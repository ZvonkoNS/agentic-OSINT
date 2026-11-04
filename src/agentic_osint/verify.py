"""Independent, deterministic checks of bytes, recorded workflow and selected values.

No result from this module establishes source truth, legal authority, authorship or
authenticated human approval. Unsupported document parsers are never guessed.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

from .common import canonical, digest, hash_file, json_pointer, read_json, safe_path, strict_json, validate_schema
from .store import event_rows, load_case


def selected_value(path: Path, selector: dict):
    if path.stat().st_size > 2_000_000:
        raise ValueError("Support parsing exceeds the 2 MB bounded-text limit")
    text = path.read_text(encoding="utf-8")
    if selector["type"] == "json":
        # No libraries, remote refs, embedded instructions or external resources are executed.
        value = json_pointer(strict_json(text, parse_float=Decimal), selector["pointer"])
        stack = [value]
        while stack:
            selected = stack.pop()
            if isinstance(selected, Decimal):
                raise ValueError("Selected non-integer JSON numbers require an exact text span; binary floating-point rounding is not accepted")
            if isinstance(selected, dict):
                stack.extend(selected.values())
            elif isinstance(selected, list):
                stack.extend(selected)
        return value
    if selector["type"] == "text":
        start, end = selector["start"], selector["end"]
        if isinstance(start, bool) or isinstance(end, bool) or not 0 <= start < end <= len(text):
            raise ValueError("Text selector is outside the exact UTF-8 source text")
        return text[start:end]
    raise ValueError("Unsupported selector; only exact UTF-8 text and JSON values can be checked")


def check_claim(root: Path, case: dict, claim: dict) -> dict:
    validate_schema("claim", claim)
    ev = next((e for e in case["evidence"] if e["id"] == claim["evidence_id"]), None)
    if ev is None or ev["status"] != "verified":
        raise ValueError("Claim must reference a verified byte artifact; pending/mismatching evidence is excluded")
    record = next((f for f in ev["files"] if f["path"] == claim["file"]), None)
    if record is None:
        raise ValueError("Claim file is not part of its cited evidence item")
    path = safe_path(root, record["path"])
    if hash_file(path) != (record["sha256"], record["size"]):
        raise ValueError("Claim source bytes have changed")
    observed = selected_value(path, claim["selector"])
    # JSON's true and 1 must not silently count as the same typed value.
    if canonical(observed) != canonical(claim["value"]):
        raise ValueError("The selected source value does not equal the claimed typed value")
    return {"id": claim["id"], "result": "REVIEW_REQUIRED" if claim["kind"] == "analysis" else "SUPPORTED_VALUE",
            "evidence_id": ev["id"], "file": record["path"], "selector": claim["selector"], "value": observed,
            "meaning": "Exact source-value comparison only; no semantic/identity inference validated"}


def manifest_records(root: Path) -> dict[str, str]:
    path = root / "HASHES.sha256"
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 5_000_000:
        raise ValueError("Manifest missing, linked or oversized")
    records = {}
    folded = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError("Malformed manifest line")
        sha, name = match.groups()
        safe_path(root, name)
        if name in {"HASHES.sha256", "SEALED.json", ".pack.lock"} or name.startswith("addenda/"):
            raise ValueError("Manifest contains itself or a reserved sidecar")
        if name.casefold() in folded:
            raise ValueError("Duplicate or case-colliding manifest filename")
        folded.add(name.casefold())
        records[name] = sha
    if not records:
        raise ValueError("An empty manifest never verifies")
    return records


def verify_manifest(root: Path) -> dict:
    records = manifest_records(root)
    failures = []
    for name, expected in records.items():
        try:
            observed, _ = hash_file(safe_path(root, name))
            if observed != expected:
                failures.append({"file": name, "expected": expected, "observed": observed})
        except (ValueError, OSError) as error:
            failures.append({"file": name, "error": str(error)})
    actual = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            failures.append({"file": relative, "error": "Symlink inside pack"})
        elif path.is_file() and relative not in {"HASHES.sha256", "SEALED.json", ".pack.lock"} and not relative.startswith("addenda/"):
            actual.add(relative)
    for name in sorted(actual - set(records)):
        failures.append({"file": name, "error": "Unlisted file"})
    marker = read_json(root / "SEALED.json")
    validate_schema("seal", marker)
    case = read_json(root / "case.json")
    if marker["pack_id"] != case["pack_id"]:
        failures.append({"file": "SEALED.json", "error": "Seal pack ID differs from canonical case"})
    if marker["sealed_utc"] < case["created_utc"]:
        failures.append({"file": "SEALED.json", "error": "Seal predates case creation"})
    observed_manifest = hash_file(root / "HASHES.sha256")[0]
    if marker.get("manifest_sha256") != observed_manifest:
        failures.append({"file": "HASHES.sha256", "error": "Digest differs from local seal marker"})
    return {"result": "FAIL" if failures else "PASS", "files_checked": len(records), "failures": failures,
            "manifest_sha256": observed_manifest,
            "trust": "Local digest consistency only; independently retain/sign/timestamp this manifest digest"}


def verify_pack(root: Path, *, sealed: bool = False) -> dict:
    checks, byte_failures, workflow_failures, support_failures = [], [], [], []
    try:
        case = load_case(root)
        rows = event_rows(root)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, RecursionError) as error:
        return {"schema": "agentic-osint/integrity/1.3", "pack_id": None, "result": "FAIL",
                "byte_integrity": "FAIL", "workflow": "NOT_CHECKED", "content_support": "NOT_CHECKED",
                "failures": [{"category": "state", "error": str(error)}], "claims": [],
                "limitations": ["Internal verification does not establish source truth or authenticate actors"]}
    ids, filenames = set(), set()
    for evidence in case["evidence"]:
        if evidence["id"] in ids:
            byte_failures.append({"evidence_id": evidence["id"], "error": "Duplicate evidence ID"})
        ids.add(evidence["id"])
        if evidence["status"] not in {"verified", "restricted"}:
            byte_failures.append({"evidence_id": evidence["id"], "error": evidence["status"],
                "expected": evidence["expected_sha256"], "observed": evidence["files"][0]["sha256"] if evidence["files"] else None})
        if evidence["capture_level"] == "T" and evidence["status"] == "verified":
            workflow_failures.append({"evidence_id": evidence["id"], "error": "Transcribed copies cannot be promoted to verified critical evidence"})
        if evidence["capture_level"] == "D":
            parent_id = (evidence.get("derivation") or {}).get("source_evidence")
            if not any(e["id"] == parent_id and e["status"] == "verified" for e in case["evidence"]):
                workflow_failures.append({"evidence_id": evidence["id"], "error": "Derived item lacks a verified source reference"})
        for file in evidence["files"]:
            try:
                if file["path"].casefold() in filenames:
                    raise ValueError("Duplicate or case-colliding evidence path")
                filenames.add(file["path"].casefold())
                if hash_file(safe_path(root, file["path"])) != (file["sha256"], file["size"]):
                    raise ValueError("Evidence digest or size differs from original record")
            except (ValueError, OSError) as error:
                byte_failures.append({"evidence_id": evidence["id"], "file": file["path"], "error": str(error)})
        if evidence["capture_finished_utc"] < evidence["capture_started_utc"]:
            workflow_failures.append({"evidence_id": evidence["id"], "error": "Capture interval runs backwards"})
    prior = False
    budget = 0
    for row in rows:
        if row["action"] in {"initialized", "resumed"}:
            prior = False
        if row["action"] == "approved":
            prior = row["details"].get("scope_sha256") == digest(canonical(case["scope"]))
        if row["action"] in {"ingested", "captured", "network_budget_reserved"} and not prior:
            workflow_failures.append({"sequence": row["sequence"], "error": "Acquisition precedes matching scope approval"})
        delta = row["details"].get("requests", 0)
        if isinstance(delta, bool) or not isinstance(delta, int) or delta and row["action"] not in {"network_budget_reserved", "network_budget_settled"}:
            workflow_failures.append({"sequence": row["sequence"], "error": "Invalid request accounting event"})
            delta = 0
        budget += delta
        if budget < 0 or budget > case["scope"]["max_requests"]:
            workflow_failures.append({"sequence": row["sequence"], "error": "Request budget inconsistency"})
    if not prior:
        workflow_failures.append({"error": "No current-session approval for the exact scope"})
    missing = [s["id"] for s in case["steps"] if s["required"] and s["status"] != "DONE"]
    step_ids = [s["id"] for s in case["steps"]]
    if len(set(step_ids)) != len(step_ids):
        workflow_failures.append({"error": "Duplicate step ID"})
    if not any(s["required"] for s in case["steps"]):
        missing.append("required-step-definition")
    claim_ids = set()
    for claim in case["claims"]:
        try:
            if claim["id"] in claim_ids:
                raise ValueError("Duplicate claim ID")
            claim_ids.add(claim["id"])
            checks.append(check_claim(root, case, claim))
        except (ValueError, OSError, KeyError, IndexError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
            support_failures.append({"claim_id": claim["id"], "error": str(error)})
    provisional_only = byte_failures and all(f.get("error") == "provisional" for f in byte_failures)
    byte_status = "INCOMPLETE" if provisional_only or not case["evidence"] else "FAIL" if byte_failures else "PASS"
    workflow_status = "FAIL" if workflow_failures else "INCOMPLETE" if missing else "RECORDED"
    support_status = "FAIL" if support_failures else "INCOMPLETE" if not checks else "REVIEW_REQUIRED" if any(c["result"] == "REVIEW_REQUIRED" for c in checks) else "SUPPORTED_VALUES"
    failures = [{"category": c, **f} for c, group in [("bytes", byte_failures), ("workflow", workflow_failures), ("support", support_failures)] for f in group]
    if sealed or (root / "SEALED.json").exists():
        try:
            recorded = read_json(root / "IntegrityCheck.json")
            validate_schema("integrity", recorded)
            for field, expected in {"pack_id": case["pack_id"], "byte_integrity": byte_status,
                    "workflow": workflow_status, "content_support": support_status,
                    "missing_required_steps": missing, "claims": checks, "failures": failures}.items():
                if canonical(recorded.get(field)) != canonical(expected):
                    failures.append({"category": "integrity-summary", "field": field, "error": "Recorded check differs from independent recomputation"})
                    support_status = "FAIL"
            manifest = verify_manifest(root)
            if manifest["result"] == "FAIL":
                byte_status = "FAIL"
                failures.extend({"category": "manifest", **f} for f in manifest["failures"])
            # Compare every delivered rendering/export with the canonical record and deterministic renderer.
            from .report import canonical_exports, verify_optional_reports
            for filename, expected_bytes in canonical_exports(case).items():
                if safe_path(root, filename).read_bytes() != expected_bytes:
                    failures.append({"category": "report-equivalence", "file": filename, "error": "Differs from canonical case rendering"})
                    support_status = "FAIL"
            report_failures = verify_optional_reports(root, case)
            if report_failures:
                support_status = "FAIL"
                failures.extend(report_failures)
            from .operations import verify_addenda
            addenda = verify_addenda(root)
            if addenda["result"] != "PASS":
                byte_status = "FAIL"
                failures.extend({"category": "addendum", **f} for f in addenda["failures"])
        except (ValueError, OSError, json.JSONDecodeError) as error:
            byte_status = "FAIL"
            failures.append({"category": "manifest", "error": str(error)})
    hard_failures = [f for f in failures if f.get("error") != "provisional"]
    result = "FAIL" if hard_failures else "INCOMPLETE" if "INCOMPLETE" in {byte_status, workflow_status, support_status} else "REVIEW_REQUIRED" if support_status == "REVIEW_REQUIRED" else "PASS"
    return {"schema": "agentic-osint/integrity/1.3", "pack_id": case["pack_id"], "result": result,
            "byte_integrity": byte_status, "workflow": workflow_status, "content_support": support_status,
            "missing_required_steps": missing, "failures": failures, "claims": checks,
            "limitations": ["RECORDED means locally operator-asserted workflow; actor identity/authority is not authenticated",
                "SUPPORTED_VALUES means exact source values match; source truth and arbitrary semantic claims are not verified",
                "Local event chains and hashes need an independently retained signature/timestamp anchor to resist total-pack rewriting",
                "Local UTC clock synchronization is not independently validated", "External AI hosts have not been benchmarked"]}
