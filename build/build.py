#!/usr/bin/env python3
"""Build canonical portable agent files; --check compares without changing output.

Usage: python build/build.py [--check] [--output PATH]
All generated text is UTF-8/LF. Digests describe bytes read back from disk.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
META_RE = re.compile(r"\A<!-- META\n(.*?)\n-->\n", re.S)
META_KEYS = {"AGENT_NAME", "AGENT_CODE", "FILE", "PURPOSE", "INPUT_TYPE"}
EXPECTED_CODES = {
    "L1-WEB", "L1-DOM", "L1-USR", "L1-EML", "L1-PHN", "L1-SOC", "L1-IMG",
    "L1-CRY", "L1-ORG", "L1-IPA", "L1-TGM", "L1-ONI", "L1-DOC", "L1-VID",
    "L1-DSC", "L1-VER", "L2-ORC",
}


class BuildError(ValueError):
    """A source or generated-artifact contract is invalid."""


def load_version(repo: Path = REPO) -> str:
    try:
        version = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise BuildError(f"cannot read project.version: {exc}") from exc
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", version):
        raise BuildError("project.version must be an explicit semantic version")
    return version


def read_lf(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def valid_filename(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+\.md", name)) and Path(name).name == name


def parse_task(path: Path) -> tuple[dict[str, str], str]:
    text = read_lf(path)
    match = META_RE.match(text)
    if not match:
        raise BuildError(f"{path.name}: missing initial META block")
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not sep or key not in META_KEYS or not value or key in meta:
            raise BuildError(f"{path.name}: invalid, unknown or duplicate META key {key!r}")
        meta[key] = value
    if set(meta) != META_KEYS:
        raise BuildError(f"{path.name}: required META keys missing: {sorted(META_KEYS-set(meta))}")
    if not re.fullmatch(r"L1-[A-Z]{3}", meta["AGENT_CODE"]):
        raise BuildError(f"{path.name}: invalid agent code")
    if not valid_filename(meta["FILE"]):
        raise BuildError(f"{path.name}: FILE must be one safe ASCII Markdown filename")
    if not re.fullmatch(r"\d{2}_[a-z]+\.md", path.name):
        raise BuildError(f"{path.name}: task filename must be NN_name.md")
    if not meta["FILE"].startswith(f"{path.name[:2]}_{meta['AGENT_CODE']}_"):
        raise BuildError(f"{path.name}: FILE prefix must match task number and code")
    body = text[match.end():].strip() + "\n"
    for required in ("### 9.10", "### 9.11", "### 9.12"):
        if not re.search(rf"^{re.escape(required)}(?:\s|$)", body, re.M):
            raise BuildError(f"{path.name}: missing {required}")
    return meta, body


def substitute(text: str, values: dict[str, str], label: str) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise BuildError(f"{label}: unresolved placeholder {key}")
        return values[key]
    text = re.sub(r"\{\{([A-Z_]+)\}\}", replace, text)
    if re.search(r"\{\{[A-Z_]+\}\}", text):
        raise BuildError(f"{label}: unresolved placeholder inside substituted content")
    return text.rstrip() + "\n"


def build_sources(repo: Path = REPO) -> tuple[str, dict[str, tuple[str, bytes]]]:
    version = load_version(repo)
    source = repo / "build"
    core = read_lf(source / "core.md")
    shared = source / "standalone-core.md"
    common = {"INPUT_VALIDATION_REF": "§9.1", "PLAN_REF": "§9.3", "VERSION": version}
    if shared.is_file():
        common["STANDALONE_RULES"] = substitute(read_lf(shared), common, shared.name)
    artifacts: dict[str, tuple[str, bytes]] = {}
    codes: set[str] = set()

    def add(filename: str, code: str, text: str) -> None:
        if not valid_filename(filename) or filename in artifacts or code in codes:
            raise BuildError(f"unsafe/duplicate filename or duplicate code: {filename}, {code}")
        artifacts[filename] = (code, text.encode("utf-8"))
        codes.add(code)

    tasks = sorted((source / "tasks").glob("*.md"))
    if len(tasks) != 15:
        raise BuildError(f"expected 15 collector modules, found {len(tasks)}")
    if [path.name[:2] for path in tasks] != [f"{index:02}" for index in range(1, 16)]:
        raise BuildError("collector module numbers must be exactly 01 through 15")
    for task in tasks:
        meta, body = parse_task(task)
        values = {**common, **meta, "PURPOSE_ONE_LINER": meta["PURPOSE"], "TASK_SECTION": body}
        add(meta["FILE"], meta["AGENT_CODE"], substitute(core, values, task.name))
    for path in sorted((source / "standalone").glob("*.md")):
        text = substitute(read_lf(path), common, path.name)
        match = re.search(r"^\*\*Agent code:\*\* (L[12]-[A-Z]{3})\b", text, re.M)
        if not match:
            raise BuildError(f"{path.name}: missing valid Agent code header")
        add(path.name, match.group(1), text)
    if codes != EXPECTED_CODES:
        raise BuildError(f"agent inventory mismatch; missing={sorted(EXPECTED_CODES-codes)}, extra={sorted(codes-EXPECTED_CODES)}")
    return version, artifacts


def stage_build(destination: Path, repo: Path = REPO) -> None:
    version, artifacts = build_sources(repo)
    manifest, inventory = [], []
    for filename, (code, data) in sorted(artifacts.items()):
        path = destination / filename
        if path.parent.resolve() != destination.resolve():
            raise BuildError(f"output escaped staging directory: {filename}")
        path.write_bytes(data)
        actual = path.read_bytes()
        if actual != data or b"\r" in actual:
            raise BuildError(f"noncanonical generated bytes: {filename}")
        digest = hashlib.sha256(actual).hexdigest()
        manifest.append(f"{digest}  {filename}\n")
        inventory.append(f"{code} {filename}\n")
    (destination / "AGENT_FILE_HASHES.sha256").write_bytes("".join(manifest).encode("utf-8"))
    (destination / "VERSION.txt").write_bytes((version + "\n" + "".join(inventory)).encode("utf-8"))
    verify_agent_manifest(destination)


def verify_agent_manifest(directory: Path) -> None:
    lines = (directory / "AGENT_FILE_HASHES.sha256").read_text(encoding="ascii").splitlines()
    seen: set[str] = set()
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_-]+\.md)", line)
        if not match or match.group(2) in seen:
            raise BuildError("malformed or duplicate agent hash entry")
        digest, filename = match.groups()
        path = directory / filename
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise BuildError(f"agent manifest mismatch: {filename}")
        seen.add(filename)
    if len(seen) != 17:
        raise BuildError(f"expected 17 manifest entries, found {len(seen)}")
    expected = seen | {"AGENT_FILE_HASHES.sha256", "VERSION.txt"}
    if {p.name for p in directory.iterdir()} != expected:
        raise BuildError("stale or missing files in generated agent directory")


def compare_build(staged: Path, output: Path) -> list[str]:
    if not output.is_dir() or output.is_symlink():
        return [f"missing or unsafe generated directory: {output}"]
    expected = {p.name for p in staged.iterdir()}
    actual = {p.name for p in output.iterdir()}
    differences = [f"missing: {n}" for n in sorted(expected-actual)]
    differences += [f"stale: {n}" for n in sorted(actual-expected)]
    for name in sorted(expected & actual):
        path = output / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != (staged / name).read_bytes():
            differences.append(f"changed: {name}")
    return differences


def publish(staged: Path, output: Path) -> None:
    """Publish only a validated directory, restoring the old build on failure.

    Each same-filesystem rename is atomic. Replacing a nonempty directory needs a
    brief rename transaction on Windows; readers should still verify manifests.
    """
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise BuildError("refusing to replace a symlink or non-directory output")
    backup = Path(tempfile.mkdtemp(prefix=".agents-backup-", dir=output.parent))
    backup.rmdir()
    had_output = output.exists()
    published = False
    try:
        if had_output:
            os.replace(output, backup)
        try:
            os.replace(staged, output)
        except BaseException as publish_error:
            if had_output:
                try:
                    os.replace(backup, output)
                except OSError as restore_error:
                    raise BuildError(f"publish failed; previous output preserved at {backup}; restore failed: {restore_error}") from publish_error
            raise
        published = True
    finally:
        if published and backup.exists():
            if backup.parent.resolve() != output.parent.resolve() or not backup.name.startswith(".agents-backup-"):
                raise BuildError("unsafe backup cleanup path")
            shutil.rmtree(backup)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare against agents without modifying output")
    parser.add_argument("--output", type=Path, default=REPO / "agents", help="dedicated generated output directory")
    args = parser.parse_args(argv)
    output = args.output.absolute()
    resolved = output.resolve()
    if output.name != "agents" or resolved == REPO or resolved in REPO.parents or resolved.is_relative_to(REPO / "build"):
        parser.error("output must be a dedicated directory named agents, outside source directories")
    try:
        if output.is_dir() and any(output.iterdir()) and not all(
                (output / name).is_file() for name in ("AGENT_FILE_HASHES.sha256", "VERSION.txt")):
            raise BuildError("existing output is not a recognized generated agent directory")
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".agents-stage-", dir=output.parent) as temp:
            staged = Path(temp) / "agents"
            staged.mkdir()
            stage_build(staged)
            if args.check:
                differences = compare_build(staged, output)
                if differences:
                    print("Build is not current:\n" + "\n".join(differences), file=sys.stderr)
                    return 1
                print("Verified 17 canonical agents, manifest bytes and generated-file inventory.")
            else:
                publish(staged, output)
                print(f"Built and verified 17 agents v{load_version()} in {output}")
        return 0
    except (OSError, BuildError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
