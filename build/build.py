#!/usr/bin/env python3
"""Assemble standalone Level-1 OSINT agent .md files from core.md + task modules,
copy the standalone agents (Verifier, Orchestrator), and write the hash manifest.

Usage: python3 build/build.py          (from the repository root or anywhere)
"""
import hashlib
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "agents"
OUT.mkdir(exist_ok=True)

core = (ROOT / "core.md").read_text(encoding="utf-8")
meta_re = re.compile(r"<!-- META\n(.*?)\n-->\n", re.S)
CONST = {"INPUT_VALIDATION_REF": "§9.1", "PLAN_REF": "§9.3"}

manifest = []  # (filename, code, name, lines, sha)

# 1. Core + module → standalone L1 agent files
for task in sorted((ROOT / "tasks").glob("*.md")):
    text = task.read_text(encoding="utf-8")
    m = meta_re.match(text)
    if not m:
        sys.exit(f"no META block in {task}")
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    body = text[m.end():].strip() + "\n"
    meta["PURPOSE_ONE_LINER"] = meta["PURPOSE"]
    # FILE placeholder is the file name the agent is published under (used by the tamper check)
    subs = {**CONST, **meta, "TASK_SECTION": body}
    out = core
    for k, v in subs.items():
        out = out.replace("{{" + k + "}}", v)
    leftover = re.findall(r"{{[A-Z_]+}}", out)
    if leftover:
        sys.exit(f"unreplaced placeholders in {task.name}: {leftover}")
    for required in ("### 9.10", "### 9.11", "### 9.12"):
        if required not in out:
            sys.exit(f"{task.name}: missing {required}")
    dest = OUT / meta["FILE"]
    dest.write_text(out, encoding="utf-8")
    manifest.append((meta["FILE"], meta["AGENT_CODE"], meta["AGENT_NAME"], len(out.splitlines()),
                     hashlib.sha256(out.encode("utf-8")).hexdigest()))

# 2. Standalone agents (not built from the core)
for src in sorted((ROOT / "standalone").glob("*.md")):
    dest = OUT / src.name
    shutil.copyfile(src, dest)
    text = dest.read_text(encoding="utf-8")
    code = re.search(r"\*\*Agent code:\*\* (\S+)", text).group(1)
    name = text.splitlines()[0].lstrip("# ").strip()
    manifest.append((src.name, code, name, len(text.splitlines()), hashlib.sha256(text.encode("utf-8")).hexdigest()))

manifest.sort()
print(f"{'file':58} {'code':8} {'lines':>5}  sha256(first 16)")
for f, c, n, lines, sha in manifest:
    print(f"{f:58} {c:8} {lines:5}  {sha[:16]}")
(OUT / "AGENT_FILE_HASHES.sha256").write_text(
    "".join(f"{sha}  {f}\n" for f, _, _, _, sha in manifest), encoding="utf-8")
VERSION = "1.2"
(OUT / "VERSION.txt").write_text(VERSION + "\n" + "".join(f"{c} {f}\n" for f, c, _, _, _ in manifest), encoding="utf-8")
print(f"\n{len(manifest)} agent files; manifest written to agents/AGENT_FILE_HASHES.sha256; agents/VERSION.txt = {VERSION}")
