"""Offline provenance-aware graph construction; no network or inferred identity."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Mapping

from .identifiers import normalize_identifier

MAX_ARTIFACT_BYTES = 10 * 1024 * 1024
MAX_GRAPH_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_OBSERVATIONS = 10000
MAX_EDGES = 20000
MAX_PACKS = 100


def _artifact(root: Path, filename: str) -> bytes:
    if not isinstance(filename, str) or not filename or "\\" in filename:
        raise ValueError("artifact filename must be a relative POSIX path")
    p = PurePosixPath(filename)
    if p.is_absolute() or PureWindowsPath(filename).drive or any(v in {"..", "."} for v in p.parts):
        raise ValueError("artifact path escapes pack")
    base = root.resolve(strict=True)
    path = base.joinpath(*p.parts)
    cursor = path
    while cursor != base:
        if cursor.is_symlink():
            raise ValueError("artifact links are not accepted")
        cursor = cursor.parent
    path = path.resolve(strict=True)
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError("artifact must be a regular file inside pack")
    if path.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError("artifact exceeds graph inspection limit")
    data = path.read_bytes()
    if len(data) > MAX_ARTIFACT_BYTES:
        raise ValueError("artifact exceeds graph inspection limit")
    return data


def _pointer(data: object, pointer: str) -> object:
    if not isinstance(pointer, str) or pointer and not pointer.startswith("/"):
        raise ValueError("JSON pointer must be empty or begin with /")
    for segment in pointer.split("/")[1:] if pointer else []:
        if re.search(r"~(?![01])", segment):
            raise ValueError("invalid JSON pointer escape")
        segment = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(data, list):
            if not segment.isdigit() or str(int(segment)) != segment:
                raise ValueError("invalid array index")
            data = data[int(segment)]
        elif isinstance(data, dict):
            data = data[segment]
        else:
            raise ValueError("JSON pointer does not resolve")
    return data


def _supports(data: bytes, raw: str, selector: dict) -> bool:
    if not isinstance(selector, dict):
        return False
    text = data.decode("utf-8", errors="strict")
    if selector.get("type") == "text":
        start, end = selector.get("start"), selector.get("end")
        return (type(start) is int and type(end) is int and 0 <= start <= end <= len(text)
                and text[start:end] == raw)
    if selector.get("type") in {"json", "json_pointer"}:
        def unique_members(pairs):
            value = {}
            for key, member in pairs:
                if key in value:
                    raise ValueError("ambiguous duplicate JSON member")
                value[key] = member
            return value
        def invalid_constant(_):
            raise ValueError("non-finite JSON constant")
        parsed = json.loads(text, object_pairs_hook=unique_members, parse_float=Decimal, parse_constant=invalid_constant)
        value = _pointer(parsed, selector.get("pointer"))
        # An exact scalar match is intentional. An object containing a string
        # somewhere is not a precise supporting observation.
        return isinstance(value, str) and value == raw
    return False


def build_graph(packs: list[dict], artifact_roots: Mapping[str, Path | str] | None = None) -> dict:
    """Build graph layers from explicit identifiers, never from model guesses.

    Each pack contains pack_id, evidence [{id|ev, file|filename, sha256}],
    observations [{ev, identifier:{raw,type,namespace}, selector:{type:"text",
    start,end}|{type:"json_pointer",pointer}}], and optional leads [{id,from,to}]
    whose endpoints have the same identifier shape. File hashes are checked here;
    this verifies byte binding and exact observation support, not acquisition
    authenticity, actor identity or source truth. Missing artifacts leave only a
    producer_reported layer. Callers must separately enforce case/scope policy.
    """
    artifact_roots = artifact_roots or {}
    if len(packs) > MAX_PACKS:
        raise ValueError("too many packs for graph inspection")
    if sum(len(p.get("observations", [])) + len(p.get("leads", [])) for p in packs) > MAX_OBSERVATIONS:
        raise ValueError("graph observation/lead budget exceeded")
    nodes: dict[tuple, dict] = {}
    groups = defaultdict(list)
    issues = []
    excluded_packs = []
    leads = []
    seen_packs = set()
    artifact_bytes = 0

    def node(identifier):
        item = normalize_identifier(identifier["raw"], identifier["type"], identifier.get("namespace"))
        key = tuple(item["comparison_key"])
        node_id = "id-" + sha256(json.dumps(key, ensure_ascii=False).encode()).hexdigest()
        if key not in nodes:
            nodes[key] = {"id": node_id, **item, "raw_values": [item["raw"]], "observations": []}
        elif item["raw"] not in nodes[key]["raw_values"]:
            nodes[key]["raw_values"].append(item["raw"])
        return nodes[key]

    for pack in packs:
        pack_id = pack.get("pack_id")
        if not isinstance(pack_id, str) or not pack_id or pack_id in seen_packs:
            raise ValueError("pack_id must be nonempty and unique")
        seen_packs.add(pack_id)
        evidence = {}
        for record in pack.get("evidence", []):
            ev = record.get("id", record.get("ev"))
            if not isinstance(ev, str) or not ev or ev in evidence:
                raise ValueError("evidence IDs must be nonempty and unique within pack")
            evidence[ev] = record
        cache = {}
        # A supplied digest mismatch invalidates the producing pack, rather than
        # downgrading its contents into apparently useful reported observations.
        if pack_id in artifact_roots:
            mismatch = None
            for ev, record in evidence.items():
                try:
                    data = _artifact(Path(artifact_roots[pack_id]), record.get("file", record.get("filename")))
                except (OSError, ValueError, TypeError):
                    continue  # Missing/unsupported artifacts cannot be verified.
                expected = record.get("sha256")
                if not isinstance(expected, str) or sha256(data).hexdigest() != expected.lower():
                    mismatch = {"pack_id": pack_id, "ev": ev, "reason": "supplied artifact digest mismatch or absent"}
                    break
                artifact_bytes += len(data)
                if artifact_bytes > MAX_GRAPH_ARTIFACT_BYTES:
                    raise ValueError("graph artifact-byte budget exceeded")
                cache[ev] = data
            if mismatch:
                excluded_packs.append(mismatch)
                continue
        for i, obs in enumerate(pack.get("observations", [])):
            try:
                ev = obs["ev"]
                if not isinstance(ev, str) or not ev:
                    raise ValueError("observation needs evidence ID")
                n = node(obs["identifier"])
                ref = {"pack_id": pack_id, "ev": ev}
                status = "producer_reported"
                reason = "artifact not supplied"
                record = evidence.get(ev)
                if record is None:
                    reason = "evidence record missing"
                elif pack_id in artifact_roots:
                    try:
                        if ev not in cache:
                            data = _artifact(Path(artifact_roots[pack_id]), record.get("file", record.get("filename")))
                            expected = record.get("sha256")
                            if not isinstance(expected, str) or sha256(data).hexdigest() != expected.lower():
                                raise ValueError("artifact digest mismatch or absent")
                            cache[ev] = data
                        if _supports(cache[ev], obs["identifier"]["raw"], obs.get("selector")):
                            status, reason = "artifact_bytes_checked", "exact source value located"
                        else:
                            reason = "precise selector absent or unsupported value"
                    except (OSError, ValueError, KeyError, IndexError, TypeError, UnicodeError, RecursionError) as exc:
                        reason = str(exc)
                provenance = {**ref, "status": status, "reason": reason, "observation_index": i}
                n["observations"].append(provenance)
                groups[(pack_id, ev)].append((n["id"], status))
                if status != "artifact_bytes_checked":
                    issues.append(provenance)
            except (ValueError, KeyError, TypeError) as exc:
                issues.append({"pack_id": pack_id, "observation_index": i, "reason": str(exc)})
        for lead in pack.get("leads", []):
            try:
                source, target = node(lead["from"]), node(lead["to"])
                leads.append({"type": "lead_relation", "source": source["id"], "target": target["id"],
                              "pack_id": pack_id, "lead_id": str(lead.get("id", "")), "verification": "unverified_lead"})
            except (ValueError, KeyError, TypeError) as exc:
                issues.append({"pack_id": pack_id, "lead_id": lead.get("id"), "reason": str(exc)})
    edges = []
    projected_edges = len(leads) + sum(len({v[0] for v in values}) * (len({v[0] for v in values}) - 1) // 2 for values in groups.values())
    if projected_edges > MAX_EDGES:
        raise ValueError("graph edge budget exceeded; reduce the approved observation scope")
    for (pack_id, ev), values in sorted(groups.items()):
        combined = {}
        for node_id, status in values:
            if status == "artifact_bytes_checked" or node_id not in combined:
                combined[node_id] = status
        ids = sorted(combined)
        for i, source in enumerate(ids):
            for target in ids[i+1:]:
                checked = combined[source] == combined[target] == "artifact_bytes_checked"
                edges.append({"type": "captured_cooccurrence" if checked else "producer_reported",
                              "source": source, "target": target, "pack_id": pack_id, "ev": ev,
                              "verification": "artifact_bytes_checked" if checked else "not_source_verified"})
    return {"schema": "agentic-osint/graph/1.3", "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
            "edges": edges + leads, "issues": issues,
            "excluded_packs": excluded_packs,
            "limits": {"artifact_bytes": MAX_ARTIFACT_BYTES,
                       "total_artifact_bytes": MAX_GRAPH_ARTIFACT_BYTES,
                       "observations_and_leads": MAX_OBSERVATIONS,
                       "edges": MAX_EDGES, "packs": MAX_PACKS,
                       "meaning": "co-occurrence and exact byte-backed observations; no identity or fund-flow inference"}}
