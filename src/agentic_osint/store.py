"""Local pack acquisition and an append-only, hash-chained operator event record.

The chain detects changes relative to a retained anchor. It does not authenticate the
operator or resist rewriting by someone who controls the entire unanchored pack.
"""
from __future__ import annotations

import contextlib
import json
import mimetypes
import os
import re
import shutil
import uuid
from pathlib import Path

from . import __version__
from .common import bounded_bytes, canonical, digest, hash_file, read_json, safe_path, utc_now, validate_schema, write_json

ZERO_HASH = "0" * 64


@contextlib.contextmanager
def pack_lock(root: Path):
    lock = root / ".pack.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def event_rows(root: Path) -> list[dict]:
    path = root / "events.jsonl"
    if path.is_symlink() or path.stat().st_size > 20_000_000:
        raise ValueError("Invalid or oversized event ledger")
    rows, previous, last_time = [], ZERO_HASH, ""
    for sequence, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        row = json.loads(line)
        validate_schema("event", row)
        unsigned = {key: value for key, value in row.items() if key != "hash"}
        if row["sequence"] != sequence or row["previous_hash"] != previous or digest(canonical(unsigned)) != row["hash"]:
            raise ValueError(f"Event ledger integrity failed at sequence {sequence}")
        if row["time_utc"] < last_time:
            raise ValueError("Event clock moved backwards; do not silently rewrite times")
        previous, last_time = row["hash"], row["time_utc"]
        rows.append(row)
    if not rows:
        raise ValueError("Empty event ledger")
    return rows


def append_event(root: Path, action: str, actor: str, details: dict, *, initial: bool = False) -> dict:
    rows = [] if initial else event_rows(root)
    timestamp = utc_now()
    if rows and timestamp < rows[-1]["time_utc"]:
        raise ValueError("Clock moved backwards; stop and record an agency-approved clock resolution")
    row = {"sequence": len(rows) + 1, "time_utc": timestamp, "action": action,
           "actor": actor, "details": details, "previous_hash": rows[-1]["hash"] if rows else ZERO_HASH}
    row["hash"] = digest(canonical(row))
    validate_schema("event", row)
    with (root / "events.jsonl").open("xb" if initial else "ab") as stream:
        stream.write(canonical(row) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return row


def load_case(root: Path, *, mutable: bool = False) -> dict:
    if mutable and (root / "SEALED.json").exists():
        raise ValueError("Pack is sealed. Use a numbered addendum or create a new run")
    case = read_json(root / "case.json")
    validate_schema("case", case)
    rows = event_rows(root)
    state_events = [r for r in rows if "state_sha256" in r["details"]]
    if not state_events or state_events[-1]["details"]["state_sha256"] != digest(canonical(case)):
        raise ValueError("Case state does not match the last recorded state; preserve both for review")
    return case


def save_state(root: Path, case: dict, action: str, actor: str = "local-tool", details: dict | None = None) -> None:
    validate_schema("case", case)
    write_json(root / "case.json", case)
    append_event(root, action, actor, {**(details or {}), "state_sha256": digest(canonical(case))})


def init_pack(root: Path, *, case_reference: str, target_type: str, target_value: str,
              agent: str = "L1-WEB", allowed_urls: list[str] | None = None,
              allow_http: bool = False, third_party_lookups: bool = False,
              max_bytes: int = 10_000_000, max_requests: int = 6, revision: str = "local-unpinned") -> dict:
    if root.exists():
        raise ValueError("Choose a new pack directory; initialization never overwrites files")
    if not 1 <= max_bytes <= 1_000_000_000 or not 1 <= max_requests <= 1000:
        raise ValueError("Invalid capture budget")
    if not all(isinstance(v, str) and v.strip() for v in [case_reference, target_type, target_value, agent]):
        raise ValueError("Case, target and agent are required")
    case = {"schema": "agentic-osint/case/1.3", "pack_id": str(uuid.uuid4()),
            "case_reference": case_reference, "agent": {"code": agent, "version": __version__, "revision": revision},
            "target": {"type": target_type, "value": target_value}, "created_utc": utc_now(),
            "scope": {"allowed_urls": sorted(set(allowed_urls or [])), "allow_http": allow_http,
                      "third_party_lookups": third_party_lookups, "max_bytes": max_bytes, "max_requests": max_requests},
            "evidence": [], "claims": [], "steps": [
                {"id": "acquisition", "required": True, "status": "PENDING"},
                {"id": "support", "required": True, "status": "PENDING"}]}
    validate_schema("case", case)
    root.mkdir(parents=True)
    write_json(root / "case.json", case, exclusive=True)
    append_event(root, "initialized", "local-tool", {"state_sha256": digest(canonical(case)),
                  "tool_version": __version__, "clock": "local-system-UTC; synchronization not independently verified"}, initial=True)
    return case


def approved(root: Path) -> bool:
    rows = event_rows(root)
    case = read_json(root / "case.json")
    scope_digest = digest(canonical(case["scope"]))
    boundary = max((r["sequence"] for r in rows if r["action"] in {"initialized", "resumed"}), default=0)
    return any(r["action"] == "approved" and r["sequence"] > boundary and r["details"].get("scope_sha256") == scope_digest for r in rows)


def approve(root: Path, actor: str, confirmation: str) -> None:
    if confirmation != "CONFIRM" or not actor.strip() or len(actor) > 200:
        raise ValueError("An identified local operator must enter exactly CONFIRM")
    with pack_lock(root):
        case = load_case(root, mutable=True)
        append_event(root, "approved", actor, {"scope_sha256": digest(canonical(case["scope"])),
                     "authority": "operator-asserted; no independent identity or legal-basis validation",
                     "state_sha256": digest(canonical(case))})


def require_approval(root: Path) -> None:
    if not approved(root):
        raise ValueError("Record operator approval before acquisition; resumed sessions require new approval")


def next_evidence_id(case: dict) -> str:
    return f"EV-{max((int(e['id'][3:]) for e in case['evidence']), default=0) + 1}"


def set_step(case: dict, step_id: str, status: str, required: bool = True) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", step_id) or status not in {"PENDING", "DONE", "FAILED", "DEFERRED", "SKIPPED"}:
        raise ValueError("Invalid step ID or status")
    item = next((s for s in case["steps"] if s["id"] == step_id), None)
    if item:
        item.update(status=status, required=item["required"] or required)
    else:
        case["steps"].append({"id": step_id, "required": required, "status": status})


def _record_bytes(root: Path, case: dict, files: list[tuple[str, bytes, str]], *, source: dict,
                  level: str, started: str, expected: str | None = None) -> dict:
    ev_id = next_evidence_id(case)
    if expected is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError("Expected SHA-256 must have exactly 64 hexadecimal characters")
    observed = digest(files[0][1])
    mismatch = expected is not None and observed != expected.lower()
    prefix = "quarantine" if mismatch else "evidence"
    records = []
    for filename, data, mime in files:
        relative = f"{prefix}/{ev_id}/{filename}"
        dest = safe_path(root, relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as stream:
            stream.write(data)
        records.append({"path": relative, "size": len(data), "sha256": digest(data), "mime_type": mime})
    item = {"id": ev_id, "source": source, "files": records, "capture_level": level,
            "status": "mismatch" if mismatch else "verified", "capture_started_utc": started,
            "capture_finished_utc": utc_now(), "expected_sha256": expected.lower() if expected else None,
            "derivation": None}
    case["evidence"].append(item)
    set_step(case, "acquisition", "FAILED" if mismatch else "DONE")
    return item


def ingest(root: Path, source: Path, *, expected_sha256: str | None = None, level: str = "A1",
           source_evidence: str | None = None, tool: str | None = None, parameters: str | None = None,
           restricted: bool = False) -> dict:
    if level not in {"A1", "A2", "B", "T", "D"}:
        raise ValueError("Unknown capture level")
    with pack_lock(root):
        case = load_case(root, mutable=True)
        require_approval(root)
        if level == "D":
            parent = next((e for e in case["evidence"] if e["id"] == source_evidence and e["status"] == "verified"), None)
            if not parent or not tool or not parameters:
                raise ValueError("Derived input requires verified --source-evidence, --tool with version, and --parameters")
            for record in parent["files"]:
                if hash_file(safe_path(root, record["path"])) != (record["sha256"], record["size"]):
                    raise ValueError("Derived input parent bytes do not verify")
        started = utc_now()
        original_digest, size = hash_file(source, limit=case["scope"]["max_bytes"])
        data = bounded_bytes(source, case["scope"]["max_bytes"])
        if digest(data) != original_digest or len(data) != size or len(data) > case["scope"]["max_bytes"]:
            raise ValueError("Source changed while reading or exceeds budget")
        suffix = source.suffix.lower() if re.fullmatch(r"\.[a-zA-Z0-9]{1,10}", source.suffix) else ".bin"
        mime = mimetypes.guess_type("input" + suffix)[0] or "application/octet-stream"
        item = _record_bytes(root, case, [("input" + suffix, data, mime)], source={"kind": "file", "value": source.name},
                             level=level, started=started, expected=expected_sha256)
        if level == "D":
            item["source"]["kind"] = "derived"
            item["derivation"] = {"source_evidence": source_evidence, "tool": tool, "parameters": parameters,
                                  "basis": "operator-asserted derivation, not independently reproduced"}
        if item["status"] != "mismatch" and (restricted or level == "T"):
            item["status"] = "restricted" if restricted else "provisional"
            if level == "T":
                set_step(case, "acquisition", "DEFERRED")
        save_state(root, case, "ingested", details={"evidence_id": item["id"], "status": item["status"],
                   "observed_sha256": item["files"][0]["sha256"], "expected_sha256": item["expected_sha256"]})
        return item


def capture(root: Path, url: str, *, third_party: bool = False, fetcher=None) -> dict:
    from .network import fetch_public
    from urllib.parse import urlsplit
    with pack_lock(root):
        case = load_case(root, mutable=True)
        require_approval(root)
        policy = case["scope"]
        target = case["target"]
        target_host = urlsplit(target["value"]).hostname if target["type"] in {"url", "profile", "video"} else target["value"].lower() if target["type"] == "domain" else None
        is_lookup = third_party or target_host is None or urlsplit(url).hostname != target_host
        if is_lookup and not policy["third_party_lookups"]:
            raise ValueError("Third-party lookup authorization was denied")
        used = sum(r["details"].get("requests", 0) for r in event_rows(root))
        remaining = policy["max_requests"] - used
        if remaining <= 0:
            raise ValueError("Run request budget exhausted")
        # Reserve before network access. A failed request still consumes the budget.
        append_event(root, "network_budget_reserved", "local-tool", {"requests": remaining,
                     "destination_sha256": digest(url.encode()), "state_sha256": digest(canonical(case))})
        try:
            result = (fetcher or fetch_public)(url, policy["allowed_urls"], max_bytes=policy["max_bytes"],
                        max_requests=remaining, max_redirects=min(5, remaining - 1), allow_http=policy["allow_http"])
        except Exception as error:
            from .network import CaptureError
            if not isinstance(error, CaptureError):
                raise
            # The built-in fetcher tracks attempts before transport begins. A
            # custom fetcher or an interrupted process retains the reservation
            # because its actual network activity cannot be independently known.
            attempted = error.requests_attempted if fetcher is None else None
            if type(attempted) is int and 0 <= attempted <= remaining:
                # Charge at least one for the DNS attempt, even if no HTTP
                # transport began, to keep repeated failures bounded.
                attempted = max(1, attempted)
                append_event(root, "network_budget_settled", "local-tool", {"requests": -(remaining - attempted),
                             "requests_observed": attempted, "state_sha256": digest(canonical(case))})
            hops = getattr(error, "hops", ())
            if hops:
                partial = [(f"partial-{i + 1}.bin", hop.body, "application/octet-stream") for i, hop in enumerate(hops)]
                partial.append(("partial-response.json", canonical({"hops": [h.to_dict(redact=False) for h in hops]}) + b"\n", "application/json"))
                item = _record_bytes(root, case, partial, source={"kind": "url", "value": url}, level="B", started=hops[0].started_utc)
                item["status"] = "provisional"
                set_step(case, "acquisition", "FAILED")
                save_state(root, case, "capture_failed", details={"evidence_id": item["id"], "error_type": type(error).__name__, "partial": True})
            else:
                set_step(case, "acquisition", "FAILED")
                save_state(root, case, "capture_failed", details={"error_type": type(error).__name__, "partial": False})
            raise
        append_event(root, "network_budget_settled", "local-tool", {"requests": -(remaining - len(result.hops)),
                     "requests_observed": len(result.hops), "state_sha256": digest(canonical(case))})
        files = [("body.bin", result.body, "application/octet-stream"),
                 ("response.json", canonical(result.to_dict(redact=True)) + b"\n", "application/json")]
        # Preserve every intermediate hop body when supplied by the transport.
        for i, hop in enumerate(result.hops):
            hop_body = getattr(hop, "body", None)
            if hop_body is not None and i < len(result.hops) - 1:
                files.append((f"redirect-{i + 1}.bin", hop_body, "application/octet-stream"))
        item = _record_bytes(root, case, files, source={"kind": "url", "value": url}, level="B", started=result.hops[0].started_utc)
        raw_item = _record_bytes(root, case, [("raw-response.json", canonical(result.to_dict(redact=False)) + b"\n", "application/json")],
                      source={"kind": "url", "value": url}, level="B", started=result.hops[0].started_utc)
        raw_item["status"] = "restricted"
        save_state(root, case, "captured", details={"evidence_id": item["id"], "hops": len(result.hops),
                   "restricted_metadata_evidence": raw_item["id"],
                   "representation": "HTTP entity bytes; Content-Encoding retained; not TLS/on-wire packet capture"})
        return item


def checkpoint(root: Path, destination: Path) -> dict:
    with pack_lock(root):
        case = load_case(root)
        rows = event_rows(root)
        files = []
        for name in ["case.json", "events.jsonl", *[f["path"] for e in case["evidence"] for f in e["files"]]]:
            path = safe_path(root, name)
            sha, size = hash_file(path)
            files.append({"path": name, "sha256": sha, "size": size})
        value = {"schema": "agentic-osint/checkpoint/1.3", "pack_id": case["pack_id"], "created_utc": utc_now(),
                 "case": case, "files": files, "ledger_hash": rows[-1]["hash"]}
        validate_schema("checkpoint", value)
        write_json(destination, value, exclusive=True)
        return value


def resume(checkpoint_path: Path, destination: Path, evidence_root: Path) -> dict:
    value = read_json(checkpoint_path)
    validate_schema("checkpoint", value)
    if destination.exists():
        raise ValueError("Resume destination must be a new directory")
    if value["pack_id"] != value["case"]["pack_id"]:
        raise ValueError("Checkpoint pack identity mismatch")
    # Validate all bytes before creating a destination. Hash-only resume cannot pass.
    expected_paths = {"case.json", "events.jsonl", *[f["path"] for e in value["case"]["evidence"] for f in e["files"]]}
    supplied_paths = [f["path"] for f in value["files"]]
    if set(supplied_paths) != expected_paths or len(supplied_paths) != len(set(supplied_paths)):
        raise ValueError("Checkpoint must contain every case, ledger and evidence file exactly once")
    for f in value["files"]:
        if hash_file(safe_path(evidence_root, f["path"])) != (f["sha256"], f["size"]):
            raise ValueError(f"Checkpoint evidence missing or changed: {f['path']}")
    original = load_case(evidence_root)
    if original != value["case"] or event_rows(evidence_root)[-1]["hash"] != value["ledger_hash"]:
        raise ValueError("Checkpoint state/ledger differs from the supplied source")
    if (evidence_root / "SEALED.json").exists():
        raise ValueError("A sealed pack cannot resume; create an addendum or new run")
    destination.mkdir(parents=True)
    for f in value["files"]:
        target = safe_path(destination, f["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe_path(evidence_root, f["path"]), target)
        if hash_file(target) != (f["sha256"], f["size"]):
            raise ValueError("Evidence changed while copying; preserve incomplete destination and start a new resume")
    append_event(destination, "resumed", "local-tool", {"checkpoint_sha256": hash_file(checkpoint_path)[0],
                 "state_sha256": digest(canonical(original)), "approval": "new operator approval required"})
    return original
