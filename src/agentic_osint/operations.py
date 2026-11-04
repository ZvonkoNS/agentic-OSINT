"""Controlled case mutations, sealing and numbered post-release addenda."""
from __future__ import annotations

import re
from pathlib import Path

from .common import bounded_bytes, canonical, digest, hash_file, read_json, safe_path, utc_now, validate_schema, write_json
from .report import canonical_exports, optional_reports
from .store import append_event, load_case, pack_lock, require_approval, save_state, set_step
from .verify import check_claim, verify_pack


def add_claim(root: Path, *, evidence_id: str, filename: str, selector: dict, value,
              analysis: str | None = None) -> dict:
    with pack_lock(root):
        case = load_case(root, mutable=True)
        require_approval(root)
        claim = {"id": f"CL-{max((int(c['id'][3:]) for c in case['claims']), default=0) + 1}",
                 "kind": "analysis" if analysis is not None else "source_value", "evidence_id": evidence_id,
                 "file": filename, "selector": selector, "value": value}
        if analysis is not None:
            claim["text"] = analysis
        result = check_claim(root, case, claim)
        case["claims"].append(claim)
        set_step(case, "support", "DONE")
        save_state(root, case, "claim_added", details={"claim_id": claim["id"], "result": result["result"]})
        return claim


def record_step(root: Path, step_id: str, status: str, required: bool = False) -> None:
    with pack_lock(root):
        case = load_case(root, mutable=True)
        require_approval(root)
        set_step(case, step_id, status, required)
        save_state(root, case, "step_recorded", details={"id": step_id, "status": status,
                   "basis": "operator-asserted coverage; not independent proof the action was performed"})


def seal(root: Path, formats: list[str] | None = None) -> dict:
    with pack_lock(root):
        case = load_case(root, mutable=True)
        require_approval(root)
        result = verify_pack(root)
        if result["result"] != "PASS":
            raise ValueError(f"Cannot seal: {result['result']}; missing required work, analysis review or integrity failures remain")
        known = {"case.json", "events.jsonl", ".pack.lock", *[f["path"] for e in case["evidence"] for f in e["files"]]}
        for path in root.rglob("*"):
            if path.is_symlink() or path.is_file() and path.relative_to(root).as_posix() not in known:
                raise ValueError("Unexpected file in working pack; preserve and resolve it before sealing")
        payloads = {**canonical_exports(case), **optional_reports(case, formats or [])}
        validate_schema("import", read_export(payloads["Export.json"]))
        payloads["IntegrityCheck.json"] = canonical(result) + b"\n"
        append_event(root, "sealed", "local-tool", {"state_sha256": digest(canonical(case)),
                     "result": result["result"], "formats": sorted(formats or []),
                     "notice": "Seal digest must be independently retained or signed/timestamped"})
        for filename, data in payloads.items():
            with safe_path(root, filename).open("xb") as stream:
                stream.write(data)
        lines = []
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name != ".pack.lock":
                relative = path.relative_to(root).as_posix()
                lines.append(f"{hash_file(path)[0]}  {relative}\n")
        with (root / "HASHES.sha256").open("xb") as stream:
            stream.write("".join(lines).encode("utf-8"))
        marker = {"schema": "agentic-osint/seal/1.3", "pack_id": case["pack_id"], "sealed_utc": utc_now(),
                  "manifest_sha256": hash_file(root / "HASHES.sha256")[0],
                  "anchor": "UNANCHORED: retain this digest outside the pack, or use agency signatures/timestamp verification"}
        write_json(root / "SEALED.json", marker, exclusive=True)
        verified = verify_pack(root, sealed=True)
        if verified["result"] != "PASS":
            raise ValueError("Post-seal verification failed; preserve this pack for review")
        return {**marker, "verification": verified}


def read_export(raw: bytes) -> dict:
    import json
    return json.loads(raw)


def verify_addenda(root: Path) -> dict:
    marker = read_json(root / "SEALED.json")
    validate_schema("seal", marker)
    if hash_file(root / "HASHES.sha256")[0] != marker["manifest_sha256"]:
        raise ValueError("Addendum anchor differs from the actual original manifest")
    previous = marker["manifest_sha256"]
    count, failures = 0, []
    directory = root / "addenda"
    if directory.exists():
        if directory.is_symlink():
            raise ValueError("Addenda must not be a symlink")
        for number, folder in enumerate(sorted(directory.iterdir()), 1):
            try:
                if folder.name != f"{number:04d}" or folder.is_symlink() or not folder.is_dir():
                    raise ValueError("Addendum numbering/path invalid")
                files = sorted(p.name for p in folder.iterdir())
                if files != ["attachment.bin", "record.json"]:
                    raise ValueError("Unexpected or missing addendum files")
                record = read_json(folder / "record.json")
                validate_schema("addendum", record)
                observed, size = hash_file(folder / "attachment.bin")
                unsigned = {k: v for k, v in record.items() if k != "hash"}
                if record["previous_hash"] != previous or record["hash"] != digest(canonical(unsigned)):
                    raise ValueError("Addendum chain changed")
                if record["pack_id"] != marker["pack_id"] or record["sequence"] != number or record["sha256"] != observed or record["size"] != size:
                    raise ValueError("Addendum identity or bytes changed")
                previous, count = record["hash"], count + 1
            except (ValueError, OSError, KeyError) as error:
                failures.append({"addendum": folder.name, "error": str(error)})
    return {"result": "FAIL" if failures else "PASS", "count": count, "tip_hash": previous,
            "failures": failures, "trust": "Retain each tip outside the editable pack; local chains do not authenticate actors"}


def addendum(root: Path, source: Path, *, actor: str, note: str) -> dict:
    with pack_lock(root):
        if not actor.strip() or not note.strip():
            raise ValueError("Actor and disposition/custody note are required")
        if verify_pack(root, sealed=True)["result"] != "PASS":
            raise ValueError("Original sealed pack must verify before adding a record")
        prior = verify_addenda(root)
        if prior["result"] != "PASS":
            raise ValueError("Earlier addenda do not verify; never rewrite them")
        sha, size = hash_file(source, limit=10_000_000)
        raw = bounded_bytes(source, 10_000_000)
        if digest(raw) != sha or len(raw) != size:
            raise ValueError("Addendum source changed during reading")
        number = prior["count"] + 1
        folder = root / "addenda" / f"{number:04d}"
        folder.mkdir(parents=True)
        with (folder / "attachment.bin").open("xb") as stream:
            stream.write(raw)
        marker = read_json(root / "SEALED.json")
        record = {"schema": "agentic-osint/addendum/1.3", "pack_id": marker["pack_id"], "sequence": number,
                  "created_utc": utc_now(), "actor": actor, "actor_authentication": "operator-asserted",
                  "note": note, "original_name": source.name, "sha256": sha, "size": size,
                  "previous_hash": prior["tip_hash"]}
        record["hash"] = digest(canonical(record))
        write_json(folder / "record.json", record, exclusive=True)
        return record
