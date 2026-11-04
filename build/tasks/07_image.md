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

**Module requirements:** CAP-CODE and actual byte access are required for technical verification; CAP-UPLOAD is needed for attached-file input, but not for a direct approved URL capture. CAP-VISION is optional for analytic observations only. Missing required bytes or parsers leaves the corresponding technical claim NOT_CHECKED; a preview alone never establishes original-file metadata.

**Intake additions (printed with the form):** field **16** = "SHA-256 of the original file, computed on your machine (§5.6 one-file command); not applicable to URL-only input"; field **17** = "If ExifTool is installed: attach its JSON output as a file, with its own hash and tool version"; field **18** = "Permit the listed C2PA remote-asset/revocation endpoints? Y/N (default N; exact destinations/data must be approved before requests)"; and the instruction "attach media as a **file**, not a chat picture preview". Authorisation **D** = "Upload this media to the explicitly listed web verifier/reverse-search engines, which may retain it: Y/N (default N)". D=N means no uploads; a local library is not assumed to be offline unless its external-resource fetching is disabled and tested.

Validation and ingest rules:
- Accept common image formats (JPEG, PNG, HEIC, WebP, GIF, TIFF) and video formats (MP4, MOV, WebM, MKV). Audio-only: proceed with metadata-only steps and say so.
- If a URL is given: capture the file first (level B, with headers) as `EV-001`; the sandbox copy is the original for this run and there is no EV-002. Record the URL as given and the final URL after redirects.
- If a file is attached: **chat clients may re-encode images, strip metadata or hand the model only a preview.** The investigator-held original is a provisional A1 record `EV-001` until actual bytes and capture binding are available. Hash accessible received bytes as `EV-002`. A match establishes byte equality to the investigator-reported digest, not source authenticity. A mismatch is a different-byte copy with cause UNRESOLVED; do not conclude transit alteration, replace the expected digest or silently promote the copy to the original. Attribute metadata to the exact held copy or hashed ExifTool artifact that produced it.
- **R8 applies with full force.** If prohibited content is indicated, stop viewing, analysis, uploads and distribution; record only the permitted identifier/time/hash and refer to the agency's predetermined handling procedure. Do not improvise deletion or retention decisions; do not deliver restricted content through chat.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| The file itself | Hashes, format, dimensions, duration | D (from EV-001/EV-002) | `hashlib`, `Pillow`, `ffprobe` |
| ExifTool output supplied by the Investigator at intake (field 17) | Most complete metadata extraction | A1 | If not supplied, the step is sandbox-only and says so |
| Python `Pillow` / `exifread` / `hachoir` in sandbox | Metadata fallback | D | Less complete than ExifTool |
| `ffprobe` in the sandbox (`pip install static-ffmpeg`, then run `static_ffprobe`, or call `static_ffmpeg.add_paths()` first and use `ffprobe`) | Video container/stream metadata | D | `ffprobe -v quiet -print_format json -show_format -show_streams "<file>"`; not installable → DEFERRED (Investigator runs it post-run) |
| A pinned C2PA validator with recorded version/trust-store snapshot, else an approved web verifier | Manifest, signature, trust and asset-binding results | D / A | Local validation disables external-resource fetching unless field 18 authorizes the exact endpoints/data. A web upload requires D and approved destinations. Unsupported checks are NOT_CHECKED |
| Reverse image search: Google Lens/Images, Bing Visual Search, Yandex Images, TinEye | Prior public appearances | A via G3 (one attempt per engine; these services block automation, so a block → DEFERRED, no retry loop). Without G3 → DEFERRED with the manual procedure | Needs authorisation D (upload) |
| AI vision (CAP-VISION) | Visual observations | — (opinion) | Never evidence; always labelled |
| `imagehash` (pHash/dHash), `ffmpeg` frame extraction | Similarity hashes; keyframes | B | Record library versions |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Branch ingest explicitly. URL input: one original `EV-001` level B with headers, actual bytes/digest/size; no EV-002. File input: provisional investigator original `EV-001` plus actual received bytes `EV-002`, preserving expected/observed digests and MATCH/MISMATCH/NOT_CHECKED. Technical parse output is a new D item naming the actual source EV; calculate format/dimensions/duration and optional cross-reference/perceptual hashes | B / A1 + D |
| S2 | Embedded metadata: Investigator's hashed ExifTool JSON if supplied (A1), plus sandbox libraries on the actual held copy (D); save raw JSON; extract camera make/model, software, create/modify dates, GPS (editable — caveat), author/copyright fields and thumbnail presence. Record absent fields only for the examined copy; absence alone does not establish stripping | A1 / D |
| S3 | Content credentials: validate on a copy with the pinned tool; separately record manifest presence, signature integrity, certificate trust, trust-store/version/date, current-asset hash binding, referenced-asset availability, revocation status, validation time and network actions. A cryptographic pass with untrusted signer is not TRUSTED; unavailable referenced assets/revocation checks are NOT_CHECKED. Web-verifier uploads require D | D / A |
| S4 | Video only: `ffprobe` JSON; keyframe extraction (e.g. 1 frame every 10 s, max 30 frames) as EV items; a contact sheet image | D |
| S5 | Reverse image search of the image (or up to 5 selected frames) via G3, one attempt per engine (needs authorisation D); each engine's results page captured; matching result pages captured (up to 10); earliest-dated appearance noted as displayed. Blocked or no G3 → DEFERRED with the manual procedure in the post-run list | A |
| S6 | Visual observations (CAP-VISION): observed objects/signage/script and reviewable OCR candidates with source EV, crop coordinates, OCR tool/version and uncertainty. Preserve ambiguous glyphs as ambiguous; label unconfirmed text OCR_CANDIDATE, never an exact quotation. Plate/name/handle candidates are not looked up. General vision confidence is not a calibrated probability — **labelled ANALYTIC OPINION** | — |
| S7 | Integrity and origin indicators: metadata inconsistencies (dates out of order, software tags, missing maker notes), re-encoding signs, generation markers (C2PA AI-tool entries, known generator watermarks); **labelled ANALYTIC OPINION; no ELA/"forensic" claims** | — |
| S8 | Geolocation hypotheses only if S5/S6 produced corroborable clues: phrased as "consistent with", with the EV refs that support it; never a bare location statement | — |
| S9 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Disclosure** of the media to the web C2PA verifier and reverse-search engines is covered by intake authorisation D; no mid-run question is asked. If D = N, S5 and the web-verifier part of S3 are SKIPPED, and the manual procedure is in the post-run list for the Investigator's own decision.
- Work only on **copies**; source EV bytes are never altered. Frames/contact sheets name `EV-001` for URL input or the actual received source `EV-002` for attached input, with extraction arguments and frame offsets. Never create a dangling EV-002 reference for URL input.
- C2PA establishes specified provenance/integrity assertions within the validator's coverage; it does not prove that depicted content is true. Manifest absence is not evidence of AI generation or fabrication. A signature may be mathematically valid while its signer is untrusted; source-claimed edits/generators remain attributed assertions. Preserve the complete validation output, including unsupported and failed checks.
- Metadata is **editable**. Every metadata-derived statement says "the file's embedded metadata states…".
- Reverse-search results show pages that an engine associated with similar images; a match is a Lead until the page is captured, and even then it shows *another appearance*, not the origin.
- **No face recognition, no person identification, no name suggestions from appearance** — even if a reverse-search engine offers it. Text from documents/screens remains an OCR candidate until independently checked against the source crop; do not infer identity from it or treat visual fluency as exact transcription.
- Plate numbers, phone numbers, handles or names visible in the image are reviewable text candidates listed in Leads; uncertain glyphs remain uncertain and are not normalized or looked up here. Geolocation/manipulation hypotheses require cited independent corroboration and investigator review; otherwise report NOT_ESTABLISHED.
- Keep the three layers visibly apart in the report: **technical facts** (S1–S4, EV-backed), **captured appearances** (S5, EV-backed), **analytic opinion** (S6–S8).

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| No ExifTool output supplied at intake | Sandbox fallback (`Pillow`/`exifread`); record reduced completeness. Later ExifTool JSON is a new derived artifact naming the original source digest/tool version, bound by its own digest/time in a numbered sealed addendum referencing the earlier seal; VERIFICATION.md is a working note only |
| `ffprobe` absent in sandbox | Use an approved pinned tool under authorisation B; else DEFERRED. Investigator-side post-run ffprobe JSON is a new derived artifact naming its source file/tool version, included with its digest/time in a numbered sealed addendum, never appended as if it had been part of the original sealed result |
| Reverse-search engine blocks uploads / CAPTCHA | DEFERRED for that engine with the manual procedure; no second attempt |
| HEIC/unsupported format in sandbox | `pip install pillow-heif`; else convert nothing — DEFERRED (Investigator exports a PNG copy post-run **as a derived item**, originals untouched) |
| File larger than tool limits | Frames/contact sheet only for reverse search; record the limit |
| Vision tool unavailable | SKIP S6–S8; report technical layers only |
| Host model declines a sub-step (faces, ID documents, geolocation of people) | `DECLINED-BY-HOST`, record the reason, continue; not a self-healing attempt |
| Reverse-search returns thousands of near-duplicates | Capture the first results page per engine and the three earliest-dated distinct appearances; record the cut-off |

### 9.6 Findings structure

1. **File identity** — hashes, format, dimensions/duration, perceptual hashes (EV refs).
2. **Embedded metadata** — table of relevant fields as stated by the file; absent/stripped noted.
3. **Content credentials** — separate presence, mathematical integrity, trust, asset binding, referenced-asset/revocation coverage and validation-time results, with full tool output EV; issuer and generator/edit claims attributed as shown, never content-truth certification.
4. **Prior public appearances** — table: engine, result URL, displayed date, captured EV; earliest displayed date noted as *displayed by that page*.
Items 5–7 sit under one heading **"Analysis (outside ISO/IEC 27037 — opinion)"**:
5. **Analytic observations** — S6 items with confidence words.
6. **Integrity/origin indicators** — S7, with the sentence recommending examination by a qualified forensic image/video examiner for any contested item.
7. **Geolocation hypotheses** — S8, or "none supportable".

### 9.7 XLSX sheets

`File_Properties` (field, value, tool/version, source EV, expected digest, observed digest, comparison result) · `Metadata` (group, tag, value, tool, exact source EV) · `C2PA_Checks` (check, result, trust-store/version, validation UTC, network action, output EV) · `Reverse_Search_Results` (engine, query item EV, result URL, title, displayed date, captured EV) · `Visual_Observations` (category, candidate text/observation, crop coordinates, uncertainty, reviewer status, basis EV) · `Video_Frames` (frame EV, source EV, timestamp in video, SHA-256, used for reverse search Y/N).

### 9.8 Interpretation cautions

- Hashes identify this exact file; a visually identical image with one changed byte has a different hash. Perceptual hashes support similarity review only.
- Metadata can be stripped, forged or edited with free tools; its absence is not suspicious by itself and its presence is not proof.
- Reverse search shows where similar images were indexed, not where the image originated or who created it.
- Visual observations and geolocation hypotheses are the AI's analytic opinions; they must be independently corroborated and are not evidence.
- No person depicted has been identified by this agent, by design.

### 9.9 Leads policy

Pages where the image appeared (L1-WEB); accounts that posted it (L1-SOC); text transcribed from the image (handles, numbers, domains → L1-USR/L1-PHN/L1-DOM); a qualified forensic examiner for contested authenticity.

### 9.10 Self-test specification

The versioned `selftest/L1-IMG.selftest.json` is the machine-readable assertion contract. Missing required observations, fixtures or adapters yield INCOMPLETE, never PASS. Use the repository JPEG and its published byte hash/metadata for offline ingest checks. Run URL-mode fixture input and attached-file fixture input separately: URL mode must not reference EV-002; a deliberately changed copy preserves the expected/observed mismatch without asserting its cause. Required C2PA fixtures distinguish absent, invalid, valid-but-untrusted, missing referenced asset and unavailable revocation checks; unsupported validator capabilities are NOT_CHECKED. OCR fixtures with ambiguous glyphs must remain candidates. No third-party upload occurs in default tests; `skip: S5` means reverse-search behavior is not tested. Visual opinion is not a pass/fail truth test.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Original upload of the image and the uploading account | the platform or site where the image appeared (from S5 appearances or the case) | preservation | result URL(s), image SHA-256 and perceptual hash, capture UTC | original file as uploaded, uploader account data |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–20 minutes for an image; 20–40 for a video (frame extraction and per-frame reverse search). Longest steps S5 and S4.
