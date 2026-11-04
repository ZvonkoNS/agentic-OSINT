"""Independent mutation cases from the implementation review, all offline."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import zipfile

from agentic_osint.common import canonical, digest, hash_file, read_json, utc_now, write_json
from agentic_osint.operations import add_claim, addendum, seal
from agentic_osint.report import optional_reports
from agentic_osint.store import approve, checkpoint, event_rows, ingest, init_pack, resume
from agentic_osint.verify import verify_manifest, verify_pack


class VerificationReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / "source.json"
        self.source.write_bytes(b'{"name":"Alice"}')

    def tearDown(self):
        self.temp.cleanup()

    def case(self, name):
        root = self.base / name
        init_pack(root, case_reference="OFFLINE-REVIEW", target_type="file", target_value="source.json")
        approve(root, "Review operator", "CONFIRM")
        evidence = ingest(root, self.source)
        add_claim(root, evidence_id=evidence["id"], filename=evidence["files"][0]["path"],
                  selector={"type": "json", "pointer": "/name"}, value="Alice")
        return root

    def test_altered_addendum_fails_main_pack_verification(self):
        root = self.case("addendum")
        seal(root)
        addendum(root, self.source, actor="Review operator", note="Post-release attachment")
        (root / "addenda/0001/attachment.bin").write_bytes(b"different attachment")
        result = verify_pack(root, sealed=True)
        self.assertEqual(result["result"], "FAIL")

    def test_seal_marker_must_name_the_actual_pack(self):
        root = self.case("marker")
        seal(root)
        marker = read_json(root / "SEALED.json")
        marker["pack_id"] = str(uuid.uuid4())
        write_json(root / "SEALED.json", marker)
        self.assertEqual(verify_pack(root, sealed=True)["result"], "FAIL")

    def test_checkpoint_cannot_omit_required_evidence_bytes(self):
        root = self.case("checkpoint-source")
        path = self.base / "checkpoint.json"
        checkpoint(root, path)
        record = read_json(path)
        record["files"] = [item for item in record["files"] if not item["path"].startswith("evidence/")]
        write_json(path, record)
        destination = self.base / "resumed"
        with self.assertRaises(ValueError):
            resume(path, destination, root)
        self.assertFalse(destination.exists(), "Reject incomplete checkpoints before creating a destination")

    def test_malformed_budget_details_produce_a_structured_failure(self):
        root = self.case("bad-event")
        rows = event_rows(root)
        case = read_json(root / "case.json")
        row = {"sequence": len(rows) + 1, "time_utc": utc_now(), "action": "network_budget_reserved",
               "actor": "untrusted producer", "details": {"requests": "1", "state_sha256": digest(canonical(case))},
               "previous_hash": rows[-1]["hash"]}
        row["hash"] = digest(canonical(row))
        with (root / "events.jsonl").open("ab") as stream:
            stream.write(canonical(row) + b"\n")
        result = verify_pack(root)
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(result["failures"])

    def test_rehashed_hidden_docx_content_is_not_render_equivalence(self):
        root = self.case("hidden-report")
        seal(root, formats=["docx"])
        with zipfile.ZipFile(root / "Report.docx", "a") as archive:
            archive.writestr("word/hidden-review.xml", '<hidden>Unsupported narrative</hidden>')
        lines = []
        for line in (root / "HASHES.sha256").read_text(encoding="utf-8").splitlines():
            expected, filename = line.split("  ", 1)
            if filename == "Report.docx":
                expected = hash_file(root / filename)[0]
            lines.append(f"{expected}  {filename}\n")
        (root / "HASHES.sha256").write_bytes("".join(lines).encode())
        marker = read_json(root / "SEALED.json")
        marker["manifest_sha256"] = hash_file(root / "HASHES.sha256")[0]
        write_json(root / "SEALED.json", marker)
        # Byte consistency alone now passes; canonical rendering must still fail.
        self.assertEqual(verify_manifest(root)["result"], "PASS")
        result = verify_pack(root, sealed=True)
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(any(item["category"] == "report-equivalence" for item in result["failures"]))

    def test_pdf_long_tokens_fit_the_printable_width(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from reportlab.pdfgen.canvas import Canvas
        root = self.base / "wide-pdf"
        case = init_pack(root, case_reference="W" * 250, target_type="file", target_value="input.txt")
        original = Canvas.drawString
        drawn = []

        def draw(canvas, x, y, text, *args, **kwargs):
            drawn.append((x, stringWidth(text, canvas._fontname, canvas._fontsize), text))
            return original(canvas, x, y, text, *args, **kwargs)

        with patch.object(Canvas, "drawString", autospec=True, side_effect=draw):
            output = optional_reports(case, ["pdf"])
        self.assertTrue(output["Report.pdf"].startswith(b"%PDF"))
        self.assertTrue(drawn)
        for x, width, text in drawn:
            self.assertGreaterEqual(x, 35)
            self.assertLessEqual(x + width, 560.01, f"Clipped PDF line: {text!r}")


if __name__ == "__main__":
    unittest.main()
