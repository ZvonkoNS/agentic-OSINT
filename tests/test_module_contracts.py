"""Regression checks for published task contracts and executable argv examples.

These checks do not claim live platform or AI-host certification. Runtime adapter
tests and observed self-test results are separate requirements.
"""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "build" / "tasks"


def task(name):
    return (TASKS / name).read_text(encoding="utf-8")


class ModuleContractTests(unittest.TestCase):
    def test_all_collectors_have_unique_safe_metadata_and_sections(self):
        files = sorted(TASKS.glob("*.md"))
        self.assertEqual(len(files), 15)
        codes, outputs = set(), set()
        for path in files:
            with self.subTest(module=path.name):
                text = path.read_text(encoding="utf-8")
                match = re.match(r"<!-- META\n(.*?)\n-->\n", text, re.S)
                self.assertIsNotNone(match)
                meta = dict(line.split(":", 1) for line in match.group(1).splitlines())
                meta = {key.strip(): value.strip() for key, value in meta.items()}
                self.assertTrue({"AGENT_NAME", "AGENT_CODE", "FILE", "PURPOSE", "INPUT_TYPE"} <= meta.keys())
                self.assertNotIn(meta["AGENT_CODE"], codes)
                self.assertNotIn(meta["FILE"], outputs)
                self.assertRegex(meta["FILE"], r"^[0-9]{2}_L1-[A-Z]+_[A-Za-z0-9-]+\.md$")
                codes.add(meta["AGENT_CODE"])
                outputs.add(meta["FILE"])
                for number in range(1, 13):
                    self.assertEqual(len(re.findall(rf"^### 9\.{number} [^\n]+$", text, re.M)), 1)
                self.assertIn(f"selftest/{meta['AGENT_CODE']}.selftest.json", text)
                self.assertIn("INCOMPLETE", text)
                self.assertNotRegex(text, r"\{\{[A-Z_]+\}\}")

    def test_video_templates_bound_scope_and_separate_non_media_operations(self):
        text = task("14_video.md")
        templates = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
        self.assertTrue({"metadata", "comments", "captions", "captions_automatic", "media"} <= templates.keys())
        forbidden = {"--cookies", "--cookies-from-browser", "--proxy", "--yes-playlist", "--exec", "--config-locations"}
        for operation, argv in templates.items():
            with self.subTest(operation=operation):
                self.assertIsInstance(argv, list)
                self.assertTrue(all(isinstance(arg, str) for arg in argv))
                self.assertEqual(argv[0], "yt-dlp")
                self.assertEqual(argv[-2:], ["--", "<URL>"])
                self.assertIn("--ignore-config", argv)
                self.assertIn("--no-playlist", argv)
                self.assertFalse(forbidden.intersection(argv))
                self.assertEqual(argv[argv.index("--retries") + 1], "1")
                self.assertEqual(argv[argv.index("--socket-timeout") + 1], "20")
                self.assertTrue(argv[argv.index("--paths") + 1].startswith("<RUN_DIR>/"))
                if operation != "media":
                    self.assertIn("--skip-download", argv)
                else:
                    self.assertNotIn("--skip-download", argv)
                    self.assertIn("--abort-on-unavailable-fragments", argv)
                    self.assertEqual(argv[argv.index("--max-filesize") + 1], "500M")
                    self.assertEqual(argv[argv.index("--max-downloads") + 1], "1")
        creator = templates["captions"]
        automatic = templates["captions_automatic"]
        self.assertIn("--write-subs", creator)
        self.assertNotIn("--write-auto-subs", creator)
        self.assertIn("--write-auto-subs", automatic)
        self.assertNotEqual(creator[creator.index("--paths") + 1], automatic[automatic.index("--paths") + 1])
        self.assertIn("--write-comments", templates["comments"])
        self.assertIn("--write-info-json", templates["comments"])

    def test_old_unsafe_instructions_do_not_reappear(self):
        # Exact former instructions caused material errors; prose negations are
        # allowed, but reinstating the old affirmative recipes fails release.
        removed = {
            "01_web.md": ["record STABLE / CHANGED", "computed absolute UTC time, marked `computed`"],
            "02_domain.md": ["CDX sample (first/last/count)", "assert that the MX answer set is either empty or exactly `0 .`"],
            "03_username.md": ["request a random 20-character handle", "Classify by page marker/size difference"],
            "04_email.md": ["profiles/<md5>", "lookups use an MD5", "the agency key is pasted only"],
            "05_phone.md": ["`+` followed by 8–15 digits", "fewer than 6 digits", "continue with the open-web steps"],
            "06_social.md": ["up to 25 most relevant/recent", "relative → computed UTC", "compute UTC from the capture timestamp otherwise"],
            "07_image.md": ["derived copy altered in transit", "every metadata statement", "the host altered the upload"],
            "13_document.md": ["incremental updates (count of `%%EOF`)"],
        }
        for name, phrases in removed.items():
            text = task(name)
            for phrase in phrases:
                with self.subTest(module=name, recipe=phrase):
                    self.assertNotIn(phrase.lower(), text.lower())


if __name__ == "__main__":
    unittest.main()
