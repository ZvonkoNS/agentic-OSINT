"""Regression tests for byte integrity, build validation and transactional publishing."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_builder", ROOT / "build" / "build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
CHECK_SPEC = importlib.util.spec_from_file_location("release_checker", ROOT / "tools" / "check_release.py")
checker = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(checker)

COLLECTORS = ["WEB", "DOM", "USR", "EML", "PHN", "SOC", "IMG", "CRY", "ORG", "IPA", "TGM", "ONI", "DOC", "VID", "DSC"]


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="osint-build-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "build" / "tasks").mkdir(parents=True)
        (self.repo / "build" / "standalone").mkdir()
        (self.repo / "pyproject.toml").write_bytes(b'[project]\nname = "test"\nversion = "1.3.0"\n')
        (self.repo / "build" / "core.md").write_bytes(
            b'# {{AGENT_NAME}}\r\n**Agent code:** {{AGENT_CODE}}\r\n**Version:** {{VERSION}}\r\n{{TASK_SECTION}}\r\n')
        for index, code in enumerate(COLLECTORS, 1):
            self.write_task(index, code)
        for code, filename in [("L1-VER", "00_L1-VER_Test.md"), ("L2-ORC", "L2-ORC_Test.md")]:
            (self.repo / "build" / "standalone" / filename).write_bytes(
                f'# {code}\r\n**Agent code:** {code}\r\n**Version:** {{{{VERSION}}}}\r\n'.encode())

    def write_task(self, index, code, extra=""):
        path = self.repo / "build" / "tasks" / f"{index:02}_task.md"
        text = (f'<!-- META\nAGENT_NAME: Test {code}\nAGENT_CODE: L1-{code}\n'
                f'FILE: {index:02}_L1-{code}_Test.md\nPURPOSE: Test\nINPUT_TYPE: string\n{extra}-->\n'
                '### 9.10 Self-test\n### 9.11 Request\n### 9.12 Duration\n')
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        return path

    def staged(self, name="staged"):
        path = self.repo / name
        path.mkdir()
        builder.stage_build(path, self.repo)
        return path

    def git_fixture(self):
        def git(*args):
            return subprocess.run(["git", "-c", f"core.hooksPath={self.repo / '.git' / 'no-hooks'}",
                                   "-c", "commit.gpgsign=false", *args], cwd=self.repo,
                                  check=True, capture_output=True, text=True).stdout.strip()
        git("init", "--quiet")
        git("add", ".")
        git("-c", "user.name=Build test", "-c", "user.email=build-test@example.invalid", "commit", "-q", "-m", "fixture")
        return git

    def test_crlf_sources_generate_lf_bytes_and_matching_digests(self):
        staged = self.staged()
        for line in (staged / "AGENT_FILE_HASHES.sha256").read_text().splitlines():
            digest, filename = line.split("  ", 1)
            data = (staged / filename).read_bytes()
            self.assertNotIn(b"\r", data)
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
        builder.verify_agent_manifest(staged)
        self.assertEqual((staged / "VERSION.txt").read_text().splitlines()[0], "1.3.0")

    def test_build_is_deterministic(self):
        first, second = self.staged("first"), self.staged("second")
        self.assertEqual(builder.compare_build(first, second), [])

    def test_corruption_missing_and_stale_output_fail(self):
        expected, actual = self.staged("expected"), self.staged("actual")
        name = next(p.name for p in actual.glob("*.md"))
        (actual / name).write_bytes(b"changed")
        with self.assertRaises(builder.BuildError):
            builder.verify_agent_manifest(actual)
        self.assertIn(f"changed: {name}", builder.compare_build(expected, actual))
        (actual / name).unlink()
        (actual / "old-agent.md").write_bytes(b"stale")
        result = builder.compare_build(expected, actual)
        self.assertIn(f"missing: {name}", result)
        self.assertIn("stale: old-agent.md", result)

    def test_metadata_cannot_escape_output(self):
        path = self.write_task(1, "WEB")
        source = path.read_text().replace("01_L1-WEB_Test.md", "../outside.md")
        path.write_text(source)
        with self.assertRaisesRegex(builder.BuildError, "safe ASCII"):
            builder.build_sources(self.repo)
        self.assertFalse((self.repo / "outside.md").exists())

    def test_duplicate_unknown_and_missing_metadata_rejected(self):
        for extra in ["PURPOSE: duplicate\n", "UNKNOWN: value\n"]:
            with self.subTest(extra=extra):
                self.write_task(1, "WEB", extra)
                with self.assertRaises(builder.BuildError):
                    builder.build_sources(self.repo)
        path = self.write_task(1, "WEB")
        path.write_text(path.read_text().replace("PURPOSE: Test\n", ""))
        with self.assertRaisesRegex(builder.BuildError, "missing"):
            builder.build_sources(self.repo)

    def test_duplicate_codes_and_wrong_inventory_rejected(self):
        self.write_task(2, "WEB")
        with self.assertRaisesRegex(builder.BuildError, "duplicate code"):
            builder.build_sources(self.repo)
        self.write_task(2, "DOM")
        (self.repo / "build" / "tasks" / "15_task.md").unlink()
        with self.assertRaisesRegex(builder.BuildError, "15 collector"):
            builder.build_sources(self.repo)

    def test_missing_section_and_unexpanded_placeholder_rejected(self):
        path = self.write_task(1, "WEB")
        path.write_text(path.read_text().replace("### 9.12 Duration", "missing"))
        with self.assertRaisesRegex(builder.BuildError, "9.12"):
            builder.build_sources(self.repo)
        self.write_task(1, "WEB")
        (self.repo / "build" / "core.md").write_text("{{UNDECLARED}}")
        with self.assertRaisesRegex(builder.BuildError, "unresolved"):
            builder.build_sources(self.repo)

    def test_standalone_dependency_must_exist_and_is_expanded(self):
        path = self.repo / "build" / "standalone" / "00_L1-VER_Test.md"
        path.write_text(path.read_text() + "\n{{STANDALONE_RULES}}\n")
        with self.assertRaisesRegex(builder.BuildError, "unresolved"):
            builder.build_sources(self.repo)
        (self.repo / "build" / "standalone-core.md").write_text("Rules version {{VERSION}}\n")
        staged = self.staged()
        self.assertIn("Rules version 1.3.0", (staged / path.name).read_text())

    def test_publish_removes_stale_outputs_only_after_validation(self):
        output = self.repo / "agents"
        output.mkdir()
        (output / "stale.md").write_bytes(b"previous")
        builder.publish(self.staged(), output)
        builder.verify_agent_manifest(output)
        self.assertFalse((output / "stale.md").exists())

    def test_publish_rolls_back_if_staged_rename_fails(self):
        output = self.repo / "agents"
        output.mkdir()
        (output / "old.md").write_bytes(b"original")
        staged = self.staged()
        actual_replace = builder.os.replace
        def fail_staged(source, destination):
            if Path(source) == staged:
                raise OSError("simulated publish failure")
            return actual_replace(source, destination)
        with mock.patch.object(builder.os, "replace", side_effect=fail_staged):
            with self.assertRaises(OSError):
                builder.publish(staged, output)
        self.assertEqual((output / "old.md").read_bytes(), b"original")

    def test_failed_rollback_never_deletes_previous_output(self):
        output = self.repo / "agents"
        output.mkdir()
        (output / "old.md").write_bytes(b"original")
        staged = self.staged()
        actual_replace = builder.os.replace
        def fail_publish_and_restore(source, destination):
            if Path(source) == staged or Path(source).name.startswith(".agents-backup-"):
                raise OSError("simulated locked destination")
            return actual_replace(source, destination)
        with mock.patch.object(builder.os, "replace", side_effect=fail_publish_and_restore):
            with self.assertRaisesRegex(builder.BuildError, "previous output preserved"):
                builder.publish(staged, output)
        backups = list(self.repo.glob(".agents-backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "old.md").read_bytes(), b"original")

    def test_cli_check_does_not_modify_output(self):
        shutil.copyfile(ROOT / "build" / "build.py", self.repo / "build" / "build.py")
        script = self.repo / "build" / "build.py"
        built = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        path = next((self.repo / "agents").glob("*.md"))
        path.write_bytes(b"different")
        checked = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 1)
        self.assertEqual(path.read_bytes(), b"different")

    def test_attributes_preserve_pdf_and_markdown_under_autocrlf(self):
        shutil.copyfile(ROOT / ".gitattributes", self.repo / ".gitattributes")
        pdf, markdown = self.repo / "fixture.pdf", self.repo / "fixture.md"
        pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n")
        markdown.write_bytes(b"# Canonical\ntext\n")
        expected = pdf.read_bytes(), markdown.read_bytes()
        git = self.git_fixture()
        pdf.unlink()
        markdown.unlink()
        git("-c", "core.autocrlf=true", "checkout", "HEAD", "--", "fixture.pdf", "fixture.md")
        self.assertEqual((pdf.read_bytes(), markdown.read_bytes()), expected)

    def test_wiki_is_portable_uses_head_and_handles_detached_checkout(self):
        for filename in ("build.py", "make_wiki.py"):
            shutil.copyfile(ROOT / "build" / filename, self.repo / "build" / filename)
        git = self.git_fixture()
        commit = git("rev-parse", "HEAD")
        git("checkout", "--detach", "--quiet", "HEAD")
        output = self.repo / "nested" / "wiki.md"
        result = subprocess.run([sys.executable, "build/make_wiki.py", "--output", str(output)],
                                cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        raw = output.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertIn(commit.encode(), raw)
        self.assertNotIn(b"origin/main", raw)
        self.assertNotIn(b"reproduces the committed manifest byte for byte", raw)

    def test_release_checks_reject_fixture_changes(self):
        self.staged("agents")
        fixtures = self.repo / "selftest"
        fixtures.mkdir()
        data = b"original fixture\n"
        path = fixtures / "fixture.pdf"
        path.write_bytes(data)
        (fixtures / "FIXTURE_HASHES.json").write_text(json.dumps({"fixture.pdf": {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}}))
        self.assertEqual(checker.check(self.repo), [])
        path.write_bytes(data + b"modified")
        self.assertTrue(any("fixture byte hash/size mismatch" in error for error in checker.check(self.repo)))

    def test_release_assets_are_hashed_and_cannot_be_overwritten(self):
        assets = self.repo / "dist"
        assets.mkdir()
        (assets / "one.zip").write_bytes(b"first")
        (assets / "two.whl").write_bytes(b"second")
        checker.hash_assets(assets)
        entries = (assets / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(entries), 2)
        self.assertNotIn("SHA256SUMS", "\n".join(entries))
        with self.assertRaisesRegex(ValueError, "replace"):
            checker.hash_assets(assets)

    def test_source_archive_is_repeatable_and_rejects_modified_source(self):
        self.git_fixture()
        first, second = self.repo / "first.zip", self.repo / "second.zip"
        checker.package(self.repo, first)
        checker.package(self.repo, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with self.assertRaisesRegex(ValueError, "overwrite"):
            checker.package(self.repo, first)
        (self.repo / "pyproject.toml").write_text('[project]\nversion = "1.3.1"\n')
        with self.assertRaises(subprocess.CalledProcessError):
            checker.package(self.repo, self.repo / "third.zip")


if __name__ == "__main__":
    unittest.main()
