"""Render all views from the same record, never from an independently drafted report."""
from __future__ import annotations

import html
import datetime as dt
import io
import json
import re
import textwrap
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .common import canonical, digest


def report_lines(case: dict) -> list[str]:
    lines = ["OSINT source-value record", f"Pack: {case['pack_id']}", f"Case: {case['case_reference']}",
             f"Agent: {case['agent']['code']} {case['agent']['version']} ({case['agent']['revision']})",
             f"Target: {case['target']['type']} {case['target']['value']}",
             "Scope: " + canonical(case["scope"]).decode(), "Evidence inventory"]
    for evidence in case["evidence"]:
        lines.append(f"{evidence['id']} [{evidence['capture_level']}; {evidence['status']}]: {evidence['source']['value']}")
        lines.append(f"Capture interval: {evidence['capture_started_utc']} to {evidence['capture_finished_utc']}")
        for file in evidence["files"]:
            lines.append(f"{file['path']} | {file['size']} bytes | SHA-256 {file['sha256']}")
        if evidence["expected_sha256"]:
            lines.append("Original expected SHA-256: " + evidence["expected_sha256"])
    lines.append("Source values and analysis")
    for claim in case["claims"]:
        lines.append(f"{claim['id']}: {claim['evidence_id']} contains value {canonical(claim['value']).decode()} at {canonical(claim['selector']).decode()}")
        if claim["kind"] == "analysis":
            lines.append("ANALYSIS - HUMAN REVIEW REQUIRED: " + claim.get("text", ""))
    lines.extend(["Required and optional coverage", *[f"{s['id']}: {s['status']} (required={s['required']})" for s in case["steps"]],
                  "Limitations", "Exact source values are checked; their truth, authorship, identity and legal meaning are not established.",
                  "Local operator confirmations are recorded assertions, not authenticated proof of authority.",
                  "Times use the local system UTC clock; independent synchronization is not established.",
                  "Byte integrity and local event chains require an independently retained signature or timestamp anchor.",
                  "A hash of a screenshot or transcript does not make it a full traffic capture.",
                  "The prompts have not been benchmarked across commercial AI hosts.",
                  "Canonical case record SHA-256: " + digest(canonical(case))])
    return lines


def canonical_exports(case: dict) -> dict[str, bytes]:
    record = canonical(case) + b"\n"
    paragraphs = "\n".join("<p>" + html.escape(line) + "</p>" for line in report_lines(case))
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">' \
           '<meta name="viewport" content="width=device-width"><title>OSINT source-value record</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:36px auto;padding:20px}p{white-space:pre-wrap;overflow-wrap:anywhere}</style><main>' + paragraphs + '</main></html>\n'
    export = {"schema": "agentic-osint/import/1.3", "case": case, "source_manifest_sha256": None}
    return {"Report.json": record, "Report.html": page.encode("utf-8"), "Export.json": canonical(export) + b"\n"}


def _pdf(case: dict) -> bytes:
    import reportlab
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font = TTFont("EvidenceVera", str(Path(reportlab.__file__).parent / "fonts/Vera.ttf"))
    pdfmetrics.registerFont(font)
    lines = report_lines(case)
    unsupported = {ord(char) for line in lines for char in line if ord(char) > 31 and ord(char) not in font.face.charToGlyph}
    if unsupported:
        raise ValueError("PDF font lacks characters " + ", ".join(f"U+{n:04X}" for n in sorted(unsupported)) + "; retain the UTF-8 HTML instead of replacing glyphs")
    stream = io.BytesIO()
    doc = canvas.Canvas(stream, pagesize=(595, 842), invariant=1)
    doc.setTitle("OSINT source-value record")
    y = 800
    def wrap_width(text):
        remaining = text
        while remaining:
            end = min(len(remaining), 150)
            while end > 0 and pdfmetrics.stringWidth(remaining[:end], "EvidenceVera", 9) > 525:
                end -= 1
            if end == 0:
                raise ValueError("A glyph exceeds the printable PDF width")
            yield remaining[:end]
            remaining = remaining[end:]
    for line in lines:
        for wrapped in list(wrap_width(line)) or [""]:
            if y < 45:
                doc.showPage()
                y = 800
            doc.setFont("EvidenceVera", 9)
            doc.drawString(35, y, wrapped)
            y -= 14
        y -= 5
    doc.save()
    return stream.getvalue()


def _docx(case: dict) -> bytes:
    from docx import Document
    document = Document()
    for line in report_lines(case):
        document.add_paragraph(line)
    result = io.BytesIO()
    document.save(result)
    return _stable_zip(result.getvalue())


def _xlsx(case: dict) -> bytes:
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    sheet.title = "Source_Record"
    for row, text in enumerate(report_lines(case), 1):
        if len(text) > 32000:
            raise ValueError("A report row exceeds the XLSX text limit; use canonical JSON")
        cell = sheet.cell(row, 1, text)
        cell.data_type = "s"  # A captured '=...' value is never a formula.
    sheet.column_dimensions["A"].width = 120
    record = book.create_sheet("Canonical_Record")
    value = canonical(case).decode("utf-8")
    for row, start in enumerate(range(0, len(value), 30000), 1):
        cell = record.cell(row, 1, value[start:start + 30000])
        cell.data_type = "s"
    result = io.BytesIO()
    book.save(result)
    return _stable_zip(result.getvalue())


def _stable_zip(data: bytes) -> bytes:
    """Canonicalize our generated OOXML containers, not arbitrary evidence files."""
    result = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(result, "w", compression=zipfile.ZIP_STORED) as target:
        for name in sorted(source.namelist()):
            raw = source.read(name)
            if name == "docProps/core.xml":
                # Library defaults must not put the current rendering time into repeated views.
                raw = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:(?:created|modified)>)",
                             rb"\g<1>2000-01-01T00:00:00Z\g<2>", raw)
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o644 << 16
            target.writestr(info, raw)
    return result.getvalue()


def optional_reports(case: dict, formats: list[str]) -> dict[str, bytes]:
    renderers = {"pdf": _pdf, "docx": _docx, "xlsx": _xlsx}
    result = {}
    for format_ in formats:
        if format_ not in renderers:
            raise ValueError("Supported optional formats: pdf, docx, xlsx")
        result["Report." + format_] = renderers[format_](case)
    return result


def _normalized(lines: list[str] | str) -> str:
    return re.sub(r"\s+", "", "\n".join(lines) if isinstance(lines, list) else lines)


def verify_optional_reports(root: Path, case: dict) -> list[dict]:
    failures = []
    for format_ in ["pdf", "docx", "xlsx"]:
        path = root / ("Report." + format_)
        if not path.exists():
            continue
        try:
            if path.stat().st_size > 30_000_000:
                raise ValueError("Generated report exceeds verification budget")
            expected = optional_reports(case, [format_])[path.name]
            if path.read_bytes() != expected:
                raise ValueError("Report differs from the canonical rendering (including hidden parts); use the pinned renderer versions")
        except (ValueError, OSError, ImportError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as error:
            failures.append({"category": "report-equivalence", "file": path.name, "error": str(error)})
    return failures
