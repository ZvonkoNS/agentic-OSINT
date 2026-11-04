"""Strict serialization, bounded reads and path rules shared by the local tools."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath

MAX_METADATA = 20_000_000
EV_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])EV-[1-9][0-9]*(?![A-Za-z0-9_-])")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path, *, limit: int = 1_000_000_000) -> tuple[str, int]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Not a regular, non-symlink file: {path.name}")
    result, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise ValueError("File exceeds byte budget")
            result.update(chunk)
    return result.hexdigest(), size


def safe_path(root: Path, relative: str) -> Path:
    """Pack paths are portable POSIX relative paths; no links or platform aliases."""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or any(ord(c) < 32 or ord(c) == 127 for c in relative):
        raise ValueError("Invalid relative pack path")
    parts = PurePosixPath(relative).parts
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if relative.startswith("/") or any(p in {".", ".."} or p.endswith((".", " ")) or p.split(".")[0].upper() in reserved for p in parts):
        raise ValueError("Path leaves the pack or uses a reserved name")
    if "/".join(parts) != relative:
        raise ValueError("Pack paths must be canonical")
    base = root.resolve()
    candidate = base.joinpath(*parts)
    for part in [candidate, *candidate.parents]:
        if part == base:
            break
        if part.is_symlink():
            raise ValueError("Symlinks are not permitted inside packs")
    if not candidate.resolve().is_relative_to(base):
        raise ValueError("Path leaves the pack")
    return candidate


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Metadata must be a regular non-symlink file")
    if path.stat().st_size > MAX_METADATA:
        raise ValueError("Metadata exceeds size limit")
    value = strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def strict_json(text: str, *, parse_float=float):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    value = json.loads(text, object_pairs_hook=no_duplicates, parse_float=parse_float,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > 100:
            raise ValueError("JSON nesting limit exceeded")
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
    return value


def bounded_bytes(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Input must be a regular non-symlink file")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Input exceeds byte budget")
    return data


def write_json(path: Path, value: object, *, exclusive: bool = False) -> None:
    data = canonical(value) + b"\n"
    if exclusive:
        with path.open("xb") as stream:
            stream.write(data)
    else:
        temp = path.with_name(path.name + ".tmp")
        with temp.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)


def schema_path(name: str) -> Path:
    candidates = [Path(__file__).resolve().parents[2] / "schemas", Path(sys.prefix) / "share/agentic-osint/schemas"]
    for directory in candidates:
        path = directory / f"{name}.schema.json"
        if path.is_file():
            return path
    raise ValueError(f"Installed schema missing: {name}; reinstall the package")


def validate_schema(name: str, value: object) -> None:
    from jsonschema import ValidationError, SchemaError
    path = schema_path(name)
    stat = path.stat()
    try:
        _schema_validator(str(path), stat.st_mtime_ns, stat.st_size).validate(value)
    except (ValidationError, SchemaError) as error:
        raise ValueError(f"{name} schema validation failed at {list(error.path)}: {error.message}") from error


@lru_cache(maxsize=64)
def _schema_validator(path: str, mtime_ns: int, size: int):
    from jsonschema import Draft202012Validator, FormatChecker
    schema = read_json(Path(path))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def json_pointer(value: object, pointer: str) -> object:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise ValueError("JSON Pointer must be empty or start with /")
    for token in pointer.split("/")[1:]:
        if re.search(r"~(?![01])", token):
            raise ValueError("Invalid JSON Pointer escape")
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise ValueError("Invalid JSON array index")
            value = value[int(key)]
        elif isinstance(value, dict):
            value = value[key]
        else:
            raise ValueError("JSON Pointer traverses a scalar")
    return value
