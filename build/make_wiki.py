#!/usr/bin/env python3
"""Generate a portable wiki index from checked-out metadata, not brittle prose splits."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from build import REPO, BuildError, load_version, parse_task, read_lf


def git_value(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                            text=True, encoding="utf-8")
    return result.stdout.strip()


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def generate(repo: Path = REPO) -> str:
    version = load_version(repo)
    commit = git_value(repo, "rev-parse", "HEAD")
    tree = git_value(repo, "rev-parse", "HEAD^{tree}")
    dirty = bool(git_value(repo, "status", "--porcelain"))
    base = f"https://github.com/ZvonkoNS/agentic-OSINT/blob/{commit}/"
    text = [
        f"# agentic-OSINT v{version}",
        "",
        "Portable, supervised OSINT procedures and a local evidence-handling runtime.",
        "",
        f"Generated from checked-out HEAD `{commit}` (tree `{tree}`). Working tree changes present: {'yes' if dirty else 'no'}.",
        "Links below identify the committed revision; uncommitted changes are not an immutable release.",
        "",
        "## Start here",
        "",
        f"- [Setup, agent selector and worked example]({base}README.md)",
        f"- [Technical contracts and limitations]({base}docs/TECHNICAL-OVERVIEW.md)",
        f"- [Version history]({base}CHANGELOG.md)",
        "",
        "The prompt files describe procedures; prompt compliance is not guaranteed. Use the runtime's independent checks and review evidence coverage. Hash checks establish byte consistency, not source truth, authorship, permission or legal admissibility. Consult the current documentation for tested capabilities and unsupported operations.",
        "",
        "## Collector agents",
        "",
        "| Agent | Input | Task |",
        "|---|---|---|",
    ]
    for task in sorted((repo / "build" / "tasks").glob("*.md")):
        meta, _ = parse_task(task)
        text.append(f"| [{cell(meta['AGENT_CODE'])}: {cell(meta['AGENT_NAME'])}]({base}agents/{meta['FILE']}) | {cell(meta['INPUT_TYPE'])} | {cell(meta['PURPOSE'])} |")
    text += ["", "## Verification and planning", "", "| Agent | Purpose |", "|---|---|"]
    for path in sorted((repo / "build" / "standalone").glob("*.md")):
        source = read_lf(path)
        name = source.splitlines()[0].lstrip("# ")
        purpose = re.search(r"^\*\*Purpose:\*\*\s*(.+)$", source, re.M)
        description = purpose.group(1) if purpose else "See the standalone file for its complete scope and dependencies."
        text.append(f"| [{cell(name)}]({base}agents/{path.name}) | {cell(description)} |")
    text += [
        "",
        "## Build and validation",
        "",
        "```text",
        "python build/build.py",
        "python build/build.py --check",
        "python -m unittest discover -s tests -v",
        "python tools/check_release.py",
        "python build/make_wiki.py --output docs/WIKI-Home.md",
        "```",
        "",
        "The builder writes canonical UTF-8/LF artifacts into a staging directory, hashes their actual bytes, validates the complete inventory, and only then publishes them. `--check` detects modified, missing and stale generated files without rewriting them. Cross-platform CI and tagged release artifacts provide the reproducibility evidence; a prose claim is not a substitute for passing checks.",
        "",
        "Agent method verification must use the recorded immutable release/commit, never the current main branch as a substitute for an older release. Preserve the exact method file and its SHA-256 with the case record.",
        "",
        "Live-source availability and host/model behavior are separate from offline build/runtime tests. A passing local test does not establish reliability on every AI product or validate every provider endpoint.",
        "",
        "## Contributing and support",
        "",
        f"See the [repository README]({base}README.md), [contribution guidance]({base}CONTRIBUTING.md), [security reporting policy]({base}SECURITY.md) and [license]({base}LICENSE).",
        "",
    ]
    return "\n".join(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "docs" / "WIKI-Home.md")
    args = parser.parse_args(argv)
    try:
        content = generate()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(content.encode("utf-8"))
    except (OSError, BuildError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Wiki generation failed: {exc}\n")
    print(f"Wrote {args.output} ({len(content.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
