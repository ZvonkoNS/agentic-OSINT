"""Deterministic checks of supplied observations against released self-test specs.

This module does not fetch providers, create observations, or certify an AI host.
Observation collection and its provenance are separate from comparison.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

SPEC_SCHEMA = "l1-selftest/1.3"
OBSERVATIONS_SCHEMA = "agentic-osint/observations/1.3"
RESULT_SCHEMA = "agentic-osint/selftest-result/1.3"
CHECKS = {"equals", "contains", "startswith", "all_startswith", "matches", "gte", "lte", "between", "in", "exists"}
_MISSING = object()


def resolve_pointer(document: Any, pointer: str) -> Any:
    """Resolve an RFC 6901 pointer without evaluation, attribute access or I/O.

    A missing member raises KeyError. Invalid pointer syntax raises ValueError.
    The empty pointer denotes the complete document.
    """
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError("JSON Pointer must be empty or start with '/'")
    current = document
    for encoded in pointer.split("/")[1:] if pointer else []:
        if re.search(r"~(?![01])", encoded):
            raise ValueError("invalid JSON Pointer escape")
        key = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if key not in current:
                raise KeyError(pointer)
            current = current[key]
        elif isinstance(current, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise KeyError(pointer)
            index = int(key)
            if index >= len(current):
                raise KeyError(pointer)
            current = current[index]
        else:
            raise KeyError(pointer)
    return current


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _same(actual: Any, expected: Any) -> bool:
    # bool is a subclass of int in Python, but true is not the JSON number 1.
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(_same(actual[k], expected[k]) for k in actual)
    return actual == expected


def validate_spec(spec: dict[str, Any]) -> None:
    """Reject invalid specs rather than quietly skipping their assertions."""
    try:
        json.dumps(spec, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("spec must contain finite JSON values") from error
    if not isinstance(spec, dict) or spec.get("schema") != SPEC_SCHEMA:
        raise ValueError(f"expected schema {SPEC_SCHEMA}")
    if not isinstance(spec.get("agent"), str) or not spec["agent"]:
        raise ValueError("spec requires an agent")
    assertions = spec.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        raise ValueError("spec must contain at least one assertion")
    ids = set()
    for assertion in assertions:
        if not isinstance(assertion, dict):
            raise ValueError("assertion must be an object")
        for key in ("id", "step", "description", "path", "required", "check", "expect"):
            if key not in assertion:
                raise ValueError(f"assertion missing {key}")
        aid = assertion["id"]
        if not isinstance(aid, str) or not aid or aid in ids:
            raise ValueError("assertion IDs must be nonempty and unique")
        ids.add(aid)
        if type(assertion["required"]) is not bool:
            raise ValueError(f"{aid}: required must be boolean")
        path = assertion["path"]
        if not isinstance(path, str) or not path.startswith("/values/") or re.search(r"~(?![01])", path):
            raise ValueError(f"{aid}: observation path must be a JSON Pointer below /values/")
        check, expected = assertion["check"], assertion["expect"]
        if check not in CHECKS:
            raise ValueError(f"{aid}: unknown check {check}")
        if check in {"gte", "lte"} and not _number(expected):
            raise ValueError(f"{aid}: numeric bound required")
        if check == "between" and (not isinstance(expected, list) or len(expected) != 2 or
                                    not all(_number(v) for v in expected) or expected[0] > expected[1]):
            raise ValueError(f"{aid}: between requires ordered numeric bounds")
        if check == "in" and (not isinstance(expected, list) or not expected):
            raise ValueError(f"{aid}: in requires a nonempty array")
        if check == "exists" and type(expected) is not bool:
            raise ValueError(f"{aid}: exists requires a boolean")
        if check in {"startswith", "all_startswith", "matches"} and not isinstance(expected, str):
            raise ValueError(f"{aid}: string expected")
        if check == "matches":
            if len(expected) > 512:
                raise ValueError(f"{aid}: regex exceeds supported length")
            try:
                re.compile(expected)
            except re.error as error:
                raise ValueError(f"{aid}: invalid regex") from error
        for flag in ("may_drift", "inconclusive_if_blocked"):
            if flag in assertion and type(assertion[flag]) is not bool:
                raise ValueError(f"{aid}: {flag} must be boolean")


def _compare(check: str, actual: Any, expected: Any) -> bool:
    if check == "equals":
        return _same(actual, expected)
    if check == "exists":
        return (actual is not _MISSING and actual is not None) == expected
    if actual is _MISSING:
        return False
    if check == "in":
        return any(_same(actual, item) for item in expected)
    if check == "contains":
        if isinstance(actual, str) and isinstance(expected, str):
            return expected in actual
        if isinstance(actual, list):
            return any(_same(item, expected) for item in actual)
        return False
    if check == "startswith":
        return isinstance(actual, str) and actual.startswith(expected)
    if check == "all_startswith":
        return isinstance(actual, list) and bool(actual) and all(isinstance(v, str) and v.startswith(expected) for v in actual)
    if check == "matches":
        if not isinstance(actual, str) or len(actual) > 4096:
            return False
        # Released specs are data too. Bound a pathological regex without
        # evaluating code or allowing one pattern to stall the parent process.
        worker = "import json,re,sys; p,v=json.load(sys.stdin); sys.exit(0 if re.fullmatch(p,v) is not None else 1)"
        try:
            result = subprocess.run([sys.executable, "-I", "-c", worker],
                                    input=json.dumps([expected, actual]), text=True,
                                    capture_output=True, timeout=1.0, check=False)
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0
    if check in {"gte", "lte", "between"}:
        if not _number(actual):
            return False
        if check == "gte":
            return actual >= expected
        if check == "lte":
            return actual <= expected
        return expected[0] <= actual <= expected[1]
    raise ValueError(f"unknown check {check}")


def evaluate_spec(spec: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    """Evaluate typed supplied values; unavailable required checks never PASS.

    Per-check statuses are PASS, FAIL, INCOMPLETE, INCONCLUSIVE or DRIFT.
    Aggregate precedence is FAIL > INCOMPLETE (including unavailable required
    checks) > DRIFT > INCONCLUSIVE > PASS. Any optional unresolved check prevents
    an unqualified PASS, but does not make required coverage incomplete.
    """
    validate_spec(spec)
    try:
        json.dumps(observations, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("observations must contain finite JSON values") from error
    if not isinstance(observations, dict) or observations.get("schema") != OBSERVATIONS_SCHEMA:
        raise ValueError(f"expected observations schema {OBSERVATIONS_SCHEMA}")
    if observations.get("agent") != spec["agent"]:
        raise ValueError("observations agent does not match specification")
    if observations.get("run_kind") not in {"offline_fixture", "live_smoke"}:
        raise ValueError("run_kind must be offline_fixture or live_smoke")
    if not isinstance(observations.get("values"), dict) or not isinstance(observations.get("availability"), dict):
        raise ValueError("observations require values and availability objects")
    checks = []
    for assertion in spec["assertions"]:
        aid = assertion["id"]
        availability = observations["availability"].get(aid, {})
        if not isinstance(availability, dict):
            raise ValueError(f"{aid}: availability must be an object")
        if not isinstance(availability.get("reason", ""), str):
            raise ValueError(f"{aid}: availability reason must be a string")
        evidence_refs = availability.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or not all(isinstance(r, str) for r in evidence_refs):
            raise ValueError(f"{aid}: evidence_refs must be an array of strings")
        state = availability.get("status", "NOT_RUN")
        if state not in {"OBSERVED", "BLOCKED", "NOT_RUN", "ERROR"}:
            raise ValueError(f"{aid}: invalid observation availability")
        try:
            actual = resolve_pointer(observations, assertion["path"])
        except KeyError:
            actual = _MISSING
        reason = availability.get("reason", "")
        if state == "ERROR":
            status, reason = "FAIL", reason or "observation collection reported an error"
        elif state == "BLOCKED":
            status = "INCONCLUSIVE" if assertion.get("inconclusive_if_blocked") else "INCOMPLETE"
            reason = reason or "source blocked; comparison not performed"
        elif state == "NOT_RUN":
            status, reason = "INCOMPLETE", reason or "observation not collected"
        elif actual is _MISSING and not (assertion["check"] == "exists" and assertion["expect"] is False):
            status, reason = "INCOMPLETE", "declared observed but pointer is missing"
        elif _compare(assertion["check"], actual, assertion["expect"]):
            status = "PASS"
        else:
            review = availability.get("baseline_change_review", {})
            reviewed_change = (isinstance(review, dict) and review.get("confirmed") is True
                               and isinstance(review.get("reviewer"), str) and bool(review["reviewer"].strip())
                               and isinstance(review.get("reason"), str) and bool(review["reason"].strip())
                               and isinstance(review.get("evidence_refs"), list) and bool(review["evidence_refs"])
                               and all(isinstance(r, str) and bool(r.strip()) for r in review["evidence_refs"]))
            status = "DRIFT" if (assertion.get("may_drift") and observations["run_kind"] == "live_smoke" and reviewed_change) else "FAIL"
            reason = ("Baseline change reviewed as a live-source change; review is operator-asserted, not authenticated"
                      if status == "DRIFT" else "comparison failed; provider drift or collector regression must be investigated, not assumed")
        checks.append({"id": aid, "step": assertion["step"], "path": assertion["path"],
                       "required": assertion["required"], "status": status,
                       "observed": None if actual is _MISSING else actual,
                       "observed_present": actual is not _MISSING, "expected": assertion["expect"],
                       "reason": reason, "evidence_refs": availability.get("evidence_refs", [])})
    if any(c["status"] == "FAIL" for c in checks):
        verdict = "FAIL"
    elif any(c["required"] and c["status"] in {"INCOMPLETE", "INCONCLUSIVE"} for c in checks):
        verdict = "INCOMPLETE"
    elif any(c["status"] == "DRIFT" for c in checks):
        verdict = "DRIFT"
    elif any(c["status"] in {"INCOMPLETE", "INCONCLUSIVE"} for c in checks):
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    return {"schema": RESULT_SCHEMA, "agent": spec["agent"], "run_kind": observations["run_kind"],
            "verdict": verdict, "release_eligible": verdict == "PASS",
            "scope": "comparison of supplied observations only; not a host or provider certification",
            "required_checked": sum(c["required"] and c["status"] in {"PASS", "FAIL", "DRIFT"} for c in checks),
            "required_total": sum(c["required"] for c in checks), "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        from .common import read_json, validate_schema
        specification, observed = read_json(args.spec), read_json(args.observations)
        validate_schema("selftest", specification)
        validate_schema("selftest-observations", observed)
        result = evaluate_spec(specification, observed)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(2, f"selftest: {error}\n")
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
