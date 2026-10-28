<!-- META
AGENT_NAME: Image & Media Verification Agent
AGENT_CODE: L1-IMG
FILE: 07_L1-IMG_Image-and-Media-Verification.md
PURPOSE: Establish the properties, embedded metadata, provenance signals, prior public appearances and observable content of one image or video file, keeping technical facts separate from analytic opinion.
INPUT_TYPE: image or video file attached to the intake reply as a file (not pasted as a picture), or a direct public URL to the media file
-->
### 9.1 Scope and input validation

**In scope:** file identity (hashes, format, dimensions, duration); embedded metadata (EXIF/XMP/IPTC, container metadata); content-credential (C2PA) check; reverse image search of the image or of extracted video frames; structured visual observations (text, landmarks, signage, language, objects); indicators relevant to manipulation or synthetic generation, as opinion.
**Out of scope (→ Leads):** identifying any person depicted (never attempt facial recognition or name a person from a face); locating a person; the web page the media came from (L1-WEB); the account that posted it (L1-SOC).

**Module requirements:** CAP-UPLOAD and CAP-CODE are required for FULL mode (file input and hashing); CAP-VISION is required for S6–S8, which are SKIPPED without it.

**Intake additions (printed with the form):** field **16** = "SHA-256 of the original file, computed on your machine (§5.6 one-file command)"; field **17** = "If ExifTool is installed: attach or paste the output of `exiftool -a -u -g1 -json "<file>"`"; and the instruction "attach the media as a **file** to your intake reply, not pasted as a picture". Authorisation **D** = "Upload this media to third-party web services — the Content Credentials web verifier and reverse-image search engines — which may retain it: Y/N". D = N → S5 is SKIPPED and S3 runs only with the sandbox `c2pa` library (nothing is uploaded).

Validation and ingest rules:
- Accept common image formats (JPEG, PNG, HEIC, WebP, GIF, TIFF) and video formats (MP4, MOV, WebM, MKV). Audio-only: proceed with metadata-only steps and say so.
- If a URL is given: capture the file first (level B, with headers) as `EV-001`; the sandbox copy is the original for this run and there is no EV-002. Record the URL as given and the final URL after redirects.
- If a file is attached: **chat clients may re-encode images, strip metadata or hand the model only a preview.** The original on the Investigator's machine is `EV-001` (level A1, hash from intake field 16). The sandbox copy is `EV-002`: if its hash equals field 16 it is treated as the original; if it differs, it is a *derived copy altered in transit*, every metadata statement is made from the Investigator's ExifTool output (field 17) where available, and "metadata absent" is reported as "absent in the transmitted copy" only.
- **R8 applies with full force.** If the Investigator indicates, or the content suggests, sexual content involving minors: stop immediately, do not view further, do not upload to any third-party service, do not describe; delete the sandbox copy and do not deliver it; record identifier + UTC + hash only + "content not processed — referred to agency protocol".

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| The file itself | Hashes, format, dimensions, duration | D (from EV-001/EV-002) | `hashlib`, `Pillow`, `ffprobe` |
| ExifTool output supplied by the Investigator at intake (field 17) | Most complete metadata extraction | A1 | If not supplied, the step is sandbox-only and says so |
| Python `Pillow` / `exifread` / `hachoir` in sandbox | Metadata fallback | D | Less complete than ExifTool |
| `ffprobe` in the sandbox (`pip install static-ffmpeg`, then run `static_ffprobe`, or call `static_ffmpeg.add_paths()` first and use `ffprobe`) | Video container/stream metadata | D | `ffprobe -v quiet -print_format json -show_format -show_streams "<file>"`; not installable → DEFERRED (Investigator runs it post-run) |
| Content Credentials: the `c2pa` Python package (`pip install c2pa-python`, authorisation B) in the sandbox, else `https://contentcredentials.org/verify` via G3 | C2PA manifest presence/validity | B / A | Needs authorisation D for the web verifier (upload) |
| Reverse image search: Google Lens/Images, Bing Visual Search, Yandex Images, TinEye | Prior public appearances | A via G3 (one attempt per engine; these services block automation, so a block → DEFERRED, no retry loop). Without G3 → DEFERRED with the manual procedure | Needs authorisation D (upload) |
| AI vision (CAP-VISION) | Visual observations | — (opinion) | Never evidence; always labelled |
| `imagehash` (pHash/dHash), `ffmpeg` frame extraction | Similarity hashes; keyframes | B | Record library versions |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Ingest: record EV-001 (Investigator's original: name, size, SHA-256 from field 16; or the URL capture) and EV-002 (sandbox copy: SHA-256, MD5 for cross-referencing, format, dimensions/duration, perceptual hashes) — tool output JSON as a D item; state whether the two hashes match | A1 + D |
| S2 | Embedded metadata: Investigator's ExifTool JSON if supplied (A1), plus sandbox libraries on the sandbox copy (D); save raw JSON; extract camera make/model, software, create/modify dates, GPS (editable — caveat), author/copyright fields, thumbnail presence; note absent/stripped metadata and in which copy | A1 / D |
| S3 | Content credentials: sandbox `c2pa` library (D, nothing uploaded); the web verifier via G3 only with authorisation D; result captured | D / A |
| S4 | Video only: `ffprobe` JSON; keyframe extraction (e.g. 1 frame every 10 s, max 30 frames) as EV items; a contact sheet image | D |
| S5 | Reverse image search of the image (or up to 5 selected frames) via G3, one attempt per engine (needs authorisation D); each engine's results page captured; matching result pages captured (up to 10); earliest-dated appearance noted as displayed. Blocked or no G3 → DEFERRED with the manual procedure in the post-run list | A |
| S6 | Visual observations (CAP-VISION): visible text (transcribed exactly), language/script, signage, landmarks, vehicles/plates (transcribe, do not look up), weather/light, objects, screen content; each with a confidence word — **labelled ANALYTIC OPINION** | — |
| S7 | Integrity and origin indicators: metadata inconsistencies (dates out of order, software tags, missing maker notes), re-encoding signs, generation markers (C2PA AI-tool entries, known generator watermarks); **labelled ANALYTIC OPINION; no ELA/"forensic" claims** | — |
| S8 | Geolocation hypotheses only if S5/S6 produced corroborable clues: phrased as "consistent with", with the EV refs that support it; never a bare location statement | — |
| S9 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Disclosure** of the media to the web C2PA verifier and reverse-search engines is covered by intake authorisation D; no mid-run question is asked. If D = N, S5 and the web-verifier part of S3 are SKIPPED, and the manual procedure is in the post-run list for the Investigator's own decision.
- Work only on **copies**; EV-001/EV-002 are never altered. Frames and contact sheets are new EV items derived from EV-002 (state the derivation).
- Metadata is **editable**. Every metadata-derived statement says "the file's embedded metadata states…".
- Reverse-search results show pages that an engine associated with similar images; a match is a Lead until the page is captured, and even then it shows *another appearance*, not the origin.
- **No face recognition, no person identification, no name suggestions from appearance** — even if a reverse-search engine offers it. Transcribe visible text (including on documents or screens) exactly; do not interpret identity from it.
- Plate numbers, phone numbers, handles or names visible in the image are transcribed as observations and listed in Leads for separate runs; not looked up here.
- Keep the three layers visibly apart in the report: **technical facts** (S1–S4, EV-backed), **captured appearances** (S5, EV-backed), **analytic opinion** (S6–S8).

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| No ExifTool output supplied at intake | Sandbox fallback (`Pillow`/`exifread`); record reduced completeness; post-run list: "run ExifTool and append JSON to VERIFICATION.md" |
| `ffprobe` absent in sandbox | `pip install static-ffmpeg` (authorisation B); else DEFERRED: Investigator runs ffprobe post-run and appends the JSON |
| Reverse-search engine blocks uploads / CAPTCHA | DEFERRED for that engine with the manual procedure; no second attempt |
| HEIC/unsupported format in sandbox | `pip install pillow-heif`; else convert nothing — DEFERRED (Investigator exports a PNG copy post-run **as a derived item**, originals untouched) |
| File larger than tool limits | Frames/contact sheet only for reverse search; record the limit |
| Vision tool unavailable | SKIP S6–S8; report technical layers only |
| Host model declines a sub-step (faces, ID documents, geolocation of people) | `DECLINED-BY-HOST`, record the reason, continue; not a self-healing attempt |
| Reverse-search returns thousands of near-duplicates | Capture the first results page per engine and the three earliest-dated distinct appearances; record the cut-off |

### 9.6 Findings structure

1. **File identity** — hashes, format, dimensions/duration, perceptual hashes (EV refs).
2. **Embedded metadata** — table of relevant fields as stated by the file; absent/stripped noted.
3. **Content credentials** — manifest present/valid/absent; issuer and claimed generator/edits as shown.
4. **Prior public appearances** — table: engine, result URL, displayed date, captured EV; earliest displayed date noted as *displayed by that page*.
Items 5–7 sit under one heading **"Analysis (outside ISO/IEC 27037 — opinion)"**:
5. **Analytic observations** — S6 items with confidence words.
6. **Integrity/origin indicators** — S7, with the sentence recommending examination by a qualified forensic image/video examiner for any contested item.
7. **Geolocation hypotheses** — S8, or "none supportable".

### 9.7 XLSX sheets

`File_Properties` (field, value, tool, EV) · `Metadata` (group, tag, value, tool, EV) · `Reverse_Search_Results` (engine, query item EV, result URL, title, displayed date, captured EV) · `Visual_Observations` (category, observation, confidence, basis) · `Video_Frames` (frame EV, timestamp in video, SHA-256, used for reverse search Y/N).

### 9.8 Interpretation cautions

- Hashes identify this exact file; a visually identical image with one changed byte has a different hash. Perceptual hashes support similarity review only.
- Metadata can be stripped, forged or edited with free tools; its absence is not suspicious by itself and its presence is not proof.
- Reverse search shows where similar images were indexed, not where the image originated or who created it.
- Visual observations and geolocation hypotheses are the AI's analytic opinions; they must be independently corroborated and are not evidence.
- No person depicted has been identified by this agent, by design.

### 9.9 Leads policy

Pages where the image appeared (L1-WEB); accounts that posted it (L1-SOC); text transcribed from the image (handles, numbers, domains → L1-USR/L1-PHN/L1-DOM); a qualified forensic examiner for contested authenticity.

### 9.10 Self-test specification

Target: the repository fixture `selftest/L1-IMG_selftest.jpg` (SHA-256 `841ebfdeff6f682e748a9196f88dec69bfb2d0cd8150c9e4e09b73b40b4d109f`, MD5 `c299389a69536b1c2a7595784bc68c8d`, 14128 bytes), attached by the Investigator or fetched from the repository. Assertions: sandbox copy SHA-256 equals the published value (if it does not, the host altered the upload — that is itself the test result: report `UPLOAD ALTERED`, and compare the Investigator's local hash instead); format `JPEG`, dimensions written as `640x400`; EXIF `Make` = `L1-SELFTEST-CAMERA`, `Model` = `MODEL-27037`, `Artist` = `L1 SELFTEST`, `DateTimeOriginal` = `2026:10:28 09:00:00`; GPS latitude ref `N`, latitude in the canonical form `deg/min/sec` with seconds to one decimal = `51/30/28.8`, longitude ref `W`; perceptual hash computed (any value); `skip: S3, S5, S6, S7, S8` (no uploads to third parties; vision opinion not tested).

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Original upload of the image and the uploading account | the platform or site where the image appeared (from S5 appearances or the case) | preservation | result URL(s), image SHA-256 and perceptual hash, capture UTC | original file as uploaded, uploader account data |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–20 minutes for an image; 20–40 for a video (frame extraction and per-frame reverse search). Longest steps S5 and S4.
