#!/usr/bin/env python3
"""Check released method/fixture bytes and version consistency without network access."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "build"))
from build import BuildError, EXPECTED_CODES, load_version, verify_agent_manifest


def check(repo: Path = REPO) -> list[str]:
    failures: list[str] = []
    try:
        verify_agent_manifest(repo / "agents")
        version = load_version(repo)
        version_lines = (repo / "agents" / "VERSION.txt").read_text(encoding="utf-8").splitlines()
        if not version_lines or version_lines[0] != version:
            failures.append("agents/VERSION.txt does not match project.version")
        entries = [line.split(" ", 1) for line in version_lines[1:]]
        if any(len(entry) != 2 for entry in entries):
            failures.append("malformed VERSION.txt inventory entry")
            entries = []
        codes = [entry[0] for entry in entries]
        if len(codes) != len(set(codes)) or set(codes) != EXPECTED_CODES:
            failures.append("VERSION.txt agent inventory differs from the supported inventory")
        manifest_names = {line.split("  ", 1)[1] for line in (repo / "agents" / "AGENT_FILE_HASHES.sha256").read_text().splitlines()}
        if {entry[1] for entry in entries} != manifest_names:
            failures.append("VERSION.txt file inventory differs from the hash manifest")
        for code, filename in entries:
            if not re.fullmatch(r"[A-Za-z0-9_-]+\.md", filename):
                failures.append(f"unsafe VERSION.txt filename: {filename}")
                continue
            text = (repo / "agents" / filename).read_text(encoding="utf-8")
            if not re.search(rf"^\*\*Agent code:\*\* {re.escape(code)}\b", text, re.M):
                failures.append(f"agent header code mismatch: {filename}")
            if not re.search(rf"\*\*Version:\*\* {re.escape(version)}(?:\s|$)", text):
                failures.append(f"agent header version mismatch: {filename}")
        for filename, values in json.loads((repo / "selftest" / "FIXTURE_HASHES.json").read_text(encoding="utf-8")).items():
            if Path(filename).name != filename or filename in ("", ".", ".."):
                failures.append(f"unsafe fixture path: {filename}")
                continue
            path = repo / "selftest" / filename
            if path.is_symlink() or not path.is_file():
                failures.append(f"missing/unsafe fixture: {filename}")
                continue
            raw = path.read_bytes()
            if len(raw) != values["bytes"] or hashlib.sha256(raw).hexdigest() != values["sha256"]:
                failures.append(f"fixture byte hash/size mismatch: {filename}")
            if "md5" in values and hashlib.md5(raw, usedforsecurity=False).hexdigest() != values["md5"]:
                failures.append(f"fixture cross-reference MD5 mismatch: {filename}")
        for path in sorted((repo / "agents").glob("*.md")):
            if re.search(rb"\{\{[A-Z_]+\}\}", path.read_bytes()):
                failures.append(f"unexpanded placeholder: {path.name}")
    except (OSError, ValueError, KeyError, BuildError) as exc:
        failures.append(str(exc))
    return failures


def package(repo: Path, output: Path) -> None:
    """Package tracked release bytes, refusing modified tracked source or symlinks."""
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=repo, check=True)
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo).decode("utf-8").split("\0")
    output = output.absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError(f"refusing to overwrite a release archive: {output}")
    # Exclusive creation prevents accidental mutation of an existing release asset.
    # Stored entries avoid compressor-version differences across platforms.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(p for p in paths if p):
            path = repo / name
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(repo.resolve()):
                raise ValueError(f"unsafe tracked release path: {name}")
            info = zipfile.ZipInfo(f"agentic-osint-{load_version(repo)}/{name}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
        record = {
            "schema": "agentic-osint-release/1.0", "version": load_version(repo),
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
            "source_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip(),
            "method_manifest_sha256": hashlib.sha256((repo / "agents" / "AGENT_FILE_HASHES.sha256").read_bytes()).hexdigest()
                if (repo / "agents" / "AGENT_FILE_HASHES.sha256").is_file() else None,
        }
        info = zipfile.ZipInfo(f"agentic-osint-{load_version(repo)}/RELEASE.json", (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        archive.writestr(info, (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def hash_assets(directory: Path) -> None:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("asset path must be a directory")
    manifest = directory / "SHA256SUMS"
    if manifest.exists():
        raise ValueError("refusing to replace an existing release SHA256SUMS")
    lines = []
    for path in sorted(directory.iterdir()):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"release assets must be ordinary files: {path.name}")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", path.name):
            raise ValueError(f"unsupported release asset filename: {path.name}")
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    if not lines:
        raise ValueError("no release assets to hash")
    with manifest.open("xb") as target:
        target.write("".join(lines).encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument("--archive", type=Path, help="create a new canonical ZIP from clean tracked source")
    parser.add_argument("--hash-assets", type=Path, help="write SHA256SUMS for all files in an asset directory")
    args = parser.parse_args()
    failures = check(args.root)
    if failures:
        print("Release checks failed:\n" + "\n".join(failures), file=sys.stderr)
        return 1
    print("Verified method-file bytes, fixture hashes/sizes, version and inventory.")
    try:
        if args.archive:
            package(args.root, args.archive)
            print(f"Created {args.archive}")
        if args.hash_assets:
            hash_assets(args.hash_assets)
            print(f"Created {args.hash_assets / 'SHA256SUMS'}")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Release packaging failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
