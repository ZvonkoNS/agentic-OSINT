<!-- META
AGENT_NAME: Document & File Metadata Agent
AGENT_CODE: L1-DOC
FILE: 13_L1-DOC_Document-and-File-Metadata.md
PURPOSE: Establish the identity, structure, embedded metadata, revision traces, embedded objects and extractable identifiers of one document or file (PDF, Office, OpenDocument, archive, plain text) without executing anything inside it.
INPUT_TYPE: document or file attached to the intake reply as a file (PDF, DOCX/XLSX/PPTX, DOC/XLS/PPT, ODT/ODS/ODP, RTF, TXT/CSV, ZIP/7z/RAR, EML/MSG) or a direct public URL to the file
-->
### 9.1 Scope and input validation

**In scope:** file identity (hashes, size, true type by signature vs extension); container structure (OOXML parts, PDF objects, archive listing); embedded metadata (core/app properties, XMP, PDF info dictionary, EXIF of embedded images); revision and history traces (Office revision count, last-modified-by, PDF incremental updates, tracked changes present, comments present); embedded objects and images (extracted as derived items); macro/script presence (detected, never executed); text extraction; identifiers found in text (URLs, emails, phone numbers, crypto addresses, handles) → Leads; digital signatures (presence and validity status as reported by the library).
**Out of scope (→ Leads or prohibited):** opening the file in any application that executes content; running macros or scripts; following links in the document; interpreting the document's meaning; authorship attribution.

**Module requirements:** CAP-UPLOAD and CAP-CODE required for FULL mode. **Intake additions (printed with the form):** field **16** = "SHA-256 of the original file, computed on your machine (§5.6)"; field **17** = "If ExifTool is installed: attach or paste `exiftool -a -u -g1 -json "<file>"` output"; the instruction "attach the file to the intake reply (do not paste its content)". Authorisation **D: none** (nothing is uploaded to third parties in this module).

Validation and ingest:
- Any file is accepted; the type is determined from the first bytes (magic numbers), never from the extension alone; a mismatch is a Finding.
- Attached file: Investigator's original = `EV-001` (A1, hash from field 16); sandbox copy = `EV-002`; hashes compared as in L1-IMG. URL input: level-B capture is `EV-001`.
- **Untrusted content rule:** the file is handled only with parsing libraries in the sandbox; never rendered by a viewer that fetches remote resources; archives are listed and selectively extracted, never run; `.exe`, scripts and installers are hashed and listed only. R8 applies to any embedded media.

### 9.2 Sources (all sandbox tools — the file never leaves the sandbox)

| Tool | Use | Level |
|---|---|---|
| `hashlib`, `python-magic` / signature table | Hashes, true type | D |
| A pinned PDF parser supporting cross-reference/trailer traversal (`pypdf` / `pikepdf` only for features the installed version exposes) | PDF info/XMP, pages, validated `startxref`/xref/trailer `/Prev` revision chain, annotations, attachments and signature fields. Raw `%%EOF` occurrence counts are not revision counts | D |
| `python-docx`, `openpyxl`, `python-pptx`, `zipfile` | OOXML core/app properties, revision, last-modified-by, template, total editing time, comments/tracked changes presence (`word/comments.xml`, `w:ins`/`w:del`), embedded media list, `vbaProject.bin` presence | D |
| `olefile` + `oletools` (`olemeta`, `olevba --decode` listing only) | Legacy OLE metadata, macro presence/listing (never executed) | D |
| `odfpy` / `zipfile` | OpenDocument `meta.xml` | D |
| `extract-msg`, `email` stdlib | EML/MSG headers (Received chain, Message-ID, From/To as written), attachments listing | D |
| `py7zr` / `rarfile` / `zipfile` | Archive listing: names, sizes, timestamps, CRCs; encrypted flag | D |
| ExifTool output from the Investigator (field 17) | Most complete metadata | A1 |
| `Pillow` | EXIF of embedded images | D |
| Text extraction (`pypdf`, `python-docx`, …) + regex | Identifier extraction | D |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Ingest: EV-001/EV-002, size, SHA-256, MD5, SHA-1 (for cross-referencing with other systems), true type vs extension, hash-match statement | A1 + D |
| S2 | Container structure: bounded part listing; PDF page/encryption/linearization fields and parsed revision-chain offsets. A single validated revision means zero incremental updates. If the parser repairs the file, omits xref-stream support or cannot validate the chain, record `revision history INCONCLUSIVE`, retaining its diagnostics | D |
| S3 | Metadata: core/app/XMP/info-dictionary fields verbatim into a table; Investigator's ExifTool JSON (A1) alongside; note which fields are absent | A1 / D |
| S4 | Revision traces: last-modified-by, revision number, total editing time, template name, creation/modification tools and versions, tracked changes present, comments present (count), PDF incremental updates with the byte offsets, prior-version text if trivially recoverable from incremental updates (recorded as separate derived items) | D |
| S5 | Embedded content: images and other embedded files extracted as derived EV items with hashes; EXIF of embedded images; macro/script presence with a listing of module names (no execution); external-link relationships (`oleObject`, `hyperlink` targets, remote templates) listed | D |
| S6 | Digital signatures: presence and claimed signer fields; use a dedicated supported validator for ByteRange/coverage, mathematical integrity, post-signature changes, certificate-chain trust, revocation status and validation time as separate results. Without that validator record presence only and `signature validation NOT CHECKED`; never infer whole-document validity from a signature field or parser success | D |
| S7 | Text extraction and identifiers: full text to `EV-nnn_text.txt`; regex extraction of URLs, emails, phone numbers (E.164-looking), crypto addresses, `@handles` → `Identifiers_Found` table; each is a Lead | D |
| S8 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- Metadata is editable; every statement reads "the file's embedded metadata states…". Absent metadata is "absent", not "stripped" (stripping is an inference, for the Analysis section only if there is a basis).
- Nothing in the document is executed, clicked, resolved or fetched. External-link targets are strings in a table.
- Identifiers found in text are transcribed exactly and go to Leads; they are not looked up here (R9).
- Prior-version text recovered from incremental PDF updates or tracked changes is a derived item; cite it as "text present in an earlier revision embedded in the file", never as "the author wrote".
- Archives: list only; extract a member only if the case names it (intake field 7); encrypted members are listed with the encrypted flag and never brute-forced.
- Run parsers offline in an isolated process with explicit input-byte, expanded-byte, member-count, nesting, memory and wall-time budgets. Reject absolute/traversal paths and link entries before any extraction; do not follow archive symlinks. Stop on budget exhaustion and retain coverage/error records. No parser may resolve document external relationships or signature-validation URLs unless a separately approved, controlled verification operation requires them.
- Derive PDF revision counts from validated structural chains, never marker searches or `%%EOF` count minus one. Repaired/malformed/hybrid structures require a supported parser and a documented completeness result. A signature authenticates only its validated covered byte ranges under the configured trust policy; record uncovered bytes and later modifications separately.
- Email files: headers are reproduced verbatim; the `Received:` chain is listed in order with the IPs transcribed (each an L1-IPA Lead); nothing is sent.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Library missing (`pikepdf`, `oletools`, `py7zr`, `extract-msg`) | `pip install` under authorisation B; else fall back to `zipfile`/`pypdf`/stdlib and record reduced completeness |
| File is encrypted / password-protected | Record `encrypted`; list what is visible without the password; the password, if the Investigator lawfully holds it, is entered only by the Investigator post-run (DEFERRED) — the agent never asks for it in chat |
| Parser raises on a malformed file | Record the error text; try a second parser; hash and structure facts still reported |
| File is an executable or script | Hash, type, size, strings count only; no further processing; recommend malware analysis under agency procedure |
| Hash mismatch between field 16 and the sandbox copy | Treat the sandbox copy as "altered in transit"; metadata statements from the Investigator's ExifTool output only |
| Host assistant declines to process the content | `DECLINED-BY-HOST`; technical layers reported only |

### 9.6 Findings structure

1. **File identity** — hashes, size, true type vs extension (EV refs).
2. **Structure** — container summary, parser diagnostics, validated revision offsets/count and completeness; do not turn marker counts or repairs into established revision history.
3. **Embedded metadata** — table verbatim; absent fields listed.
4. **Revision traces** — table; derived prior-version items referenced.
5. **Embedded content** — images/objects with hashes; macro/script presence; external-link targets.
6. **Signatures** — presence, claimed signer, covered byte ranges, integrity, later modifications, trust/revocation policy and validation time as separate fields; unperformed checks remain NOT CHECKED.
7. **Identifiers found in text** — table (Leads).
8. Under **Analysis (outside ISO/IEC 27037 — opinion)** only: consistency observations (e.g. creation tool version vs claimed date), with the recommendation of a qualified document examiner for contested items.

### 9.7 XLSX sheets

`File_Identity` (field, value, tool, EV) · `Structure` (element, value, EV) · `Metadata` (source, field, value, EV) · `Revision_Traces` (trace, value, EV) · `Embedded_Objects` (type, name, size, SHA-256, EV) · `External_Links` (relationship, target, EV) · `Signatures` (field, value, EV) · `Identifiers_Found` (type, value, location, EV) · `Email_Headers` (if EML/MSG: header, value, order, EV) · `Archive_Listing` (if archive: name, size, timestamp, CRC, encrypted, EV).

### 9.8 Interpretation cautions

- Metadata fields are set by software and can be edited with free tools; they corroborate, they do not prove authorship, time or place.
- "Last modified by" is the name configured in the editing software, not an identity.
- Identifiers found in text show that the text contains them, nothing more.
- A document examiner is the competent authority for questions of authenticity.

### 9.9 Leads policy

Every identifier in `Identifiers_Found` (L1-WEB, L1-DOM, L1-EML, L1-PHN, L1-CRY, L1-USR); IPs in email headers (L1-IPA); embedded images for verification (L1-IMG); external-link targets (L1-WEB); the lawful request to the hosting service if the file came from a URL.

### 9.10 Self-test specification

The versioned `selftest/L1-DOC.selftest.json` is the machine-readable assertion contract. Missing required fixtures, adapters or expected results yield INCOMPLETE, never PASS. Offline regression results and optional live-provider smoke results are reported separately.

The existing fixture `selftest/L1-DOC_selftest.pdf` retains its published hash, size, 2-page metadata and marker checks. Required revision/signature regressions additionally cover a normal single-revision PDF (zero incremental updates), misleading EOF text, a validated incremental update, repaired/malformed xref data and a signed file with later modifications. Missing parser/signature capabilities yield INCOMPLETE/NOT CHECKED, not a guessed count or a valid signature verdict. The DOCX fixture separately tests Office metadata; success on PDF does not certify Office, archive or signature paths.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| File obtained from a URL: who uploaded it | hosting provider / platform (via L1-DOM/L1-WEB follow-up) | preservation | URL as captured, file SHA-256, capture UTC | upload account data and logs |
| Email file: originating IPs and accounts | email provider / operator (via L1-IPA/L1-EML follow-up) | preservation | Message-ID, Received-chain IPs with UTC, sender address as written | account and connection logs |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes for a single Office or PDF file; longer for large archives (listing only) or files with many embedded images. Longest steps S5 and S7.
