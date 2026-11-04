<!-- META
AGENT_NAME: YouTube / Online Video Preservation Agent
AGENT_CODE: L1-VID
FILE: 14_L1-VID_YouTube-Video-Preservation.md
PURPOSE: Preserve one public online video (YouTube by default; also Vimeo, Dailymotion, Rumble, Odysee, TikTok, X/Twitter video, Facebook video where public) with its page, metadata, uploader identifiers, transcript where published, and the media file where a public download path exists.
INPUT_TYPE: video URL (watch page, short link such as youtu.be/<id>, Shorts URL, or an embed URL)
-->
### 9.1 Scope and input validation

**In scope:** the watch page as served logged-out; the platform's public metadata (oEmbed; page-embedded JSON); the video ID and the uploader's channel/account identifiers (handle, channel ID); displayed title, description, dates, counts; the public auto/creator transcript if the platform exposes it without login; thumbnails; the media file via a public download path (`yt-dlp` where installable, public content only); top-level comments only if intake field 7 asks and the page exposes them logged-out (capped).
**Out of scope (→ Leads or prohibited):** logging in; age-gated or members-only content (requires an account → `not accessible without authentication`); the uploader's other videos (L1-SOC run on the channel); any interaction (like, subscribe, comment, report); downloading with cookies or a logged-in session (R2).

**Intake additions (printed with the form):** field **16** = "Download the media file? Y/N (default Y; files can be large — the cap is 500 MB unless you raise it here)"; field **17** = "Capture comments? N / top-level only (cap 100)". Authorisation **D: none**.

Validation:
- Accept `youtube.com/watch?v=<id>`, `youtu.be/<id>`, `youtube.com/shorts/<id>`, `youtube.com/embed/<id>`, and other platforms' watch URLs. Extract and record the video ID separately; record the URL exactly as given (including `t=` timestamps and playlist parameters, which are not stripped).
- Playlist URLs without a video ID are `NOT-INVESTIGABLE` for this module (the playlist page is an L1-WEB target).

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| Watch page (logged-out) | Primary; embedded `ytInitialPlayerResponse` / `ytInitialData` JSON holds videoId, channelId, title, publishDate, uploadDate, lengthSeconds, viewCount, keywords, category | B (A via G3) | Record the environment's locale; YouTube renders dates per locale |
| oEmbed `https://www.youtube.com/oembed?url=<watch URL>&format=json` (other platforms: their oEmbed endpoint) | Title, author name, author URL, thumbnail | B | Keyless and stable |
| Version-pinned `yt-dlp` using the §9.4 argument arrays | Public metadata, media, comments and creator/automatic captions as separately approved operations | B/D as appropriate | No user config, playlist expansion, cookies, credentials or unapproved extractor options; retain argv, version, stderr and exit status |
| Channel/about page of the uploader (one page) | Channel identifiers | B (A via G3) | One capture; the channel itself is an L1-SOC Lead |
| Wayback availability for the watch URL | Prior third-party snapshots | B | Context |
| Search engines: `"<video id>"` | Mirrors and mentions | C → A/B | Capture cited pages |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Parse URL; detect platform; print the plan, the download decision (field 16) and the cap | — |
| S2 | Watch page capture: raw HTML + headers (B); full-page screenshot via G3 where available (A); extract the embedded JSON into a derived file | B / A |
| S3 | oEmbed JSON captured; cross-check title/author with S2 | B |
| S4 | Run the metadata argv with `--skip-download`; save stdout as an EV JSON item and compare returned video ID with the approved ID. A playlist/multiple-object result stops as scope mismatch | D |
| S5 | Media only if field 16 authorizes it: use the media argv, monitored hard byte/wall-time budget and approved format. Require ffmpeg before selecting separate streams; otherwise choose a documented single-file format within cap. Preserve format IDs, completion/fragment diagnostics and hashes; over-budget or missing-fragment output is PARTIAL/INCOMPLETE, never complete | B |
| S6 | Creator and automatic captions are distinct operations in separate controlled directories; use the captions/captions_automatic argv with `--skip-download` and approved languages. Save served files without correction, record language/kind/coverage, and do not overwrite one kind with the other | B |
| S7 | Uploader identifiers: channel ID, handle, channel URL, channel "about" page captured once | B / A |
| S8 | Comments only if field 17 authorizes it: use the comments argv with `--skip-download --write-info-json`; save author, text, displayed timestamp and counts as served. Enforce top-level-only selection and cap in the supported extractor, recording omitted/reply coverage; never download media for this step | B |
| S9 | Context: Wayback availability; search-engine mentions of the video ID (up to 10 pages captured) | B / C → A |
| S10 | Volatility re-check of oEmbed and view count at the end of the run | B |
| S11 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

Use these argument-list templates through `subprocess` with `shell=False`, after replacing typed placeholders; do not concatenate shell commands. `<RUN_DIR>` is the controlled per-run directory and must be created before execution. `<URL>` remains the exact recorded URL; `--no-playlist` enforces one-video scope despite `list=` parameters. These templates are regression-checked as argument contracts, not a claim that live platform access or every installed extractor is validated.

```json
{
  "metadata": ["yt-dlp", "--ignore-config", "--no-playlist", "--skip-download", "--dump-single-json", "--socket-timeout", "20", "--retries", "1", "--extractor-retries", "1", "--paths", "<RUN_DIR>/metadata", "--", "<URL>"],
  "comments": ["yt-dlp", "--ignore-config", "--no-playlist", "--skip-download", "--write-info-json", "--write-comments", "--extractor-args", "youtube:max_comments=100,all,0", "--socket-timeout", "20", "--retries", "1", "--extractor-retries", "1", "--paths", "<RUN_DIR>/comments", "--output", "EV-comments.%(ext)s", "--", "<URL>"],
  "captions": ["yt-dlp", "--ignore-config", "--no-playlist", "--skip-download", "--write-subs", "--sub-langs", "<LANGS>", "--socket-timeout", "20", "--retries", "1", "--extractor-retries", "1", "--paths", "<RUN_DIR>/captions-creator", "--output", "EV-creator.%(ext)s", "--", "<URL>"],
  "captions_automatic": ["yt-dlp", "--ignore-config", "--no-playlist", "--skip-download", "--write-auto-subs", "--sub-langs", "<LANGS>", "--socket-timeout", "20", "--retries", "1", "--extractor-retries", "1", "--paths", "<RUN_DIR>/captions-automatic", "--output", "EV-automatic.%(ext)s", "--", "<URL>"],
  "media": ["yt-dlp", "--ignore-config", "--no-playlist", "--max-downloads", "1", "--max-filesize", "500M", "--socket-timeout", "20", "--retries", "1", "--fragment-retries", "1", "--extractor-retries", "1", "--file-access-retries", "1", "--abort-on-unavailable-fragments", "--write-info-json", "--format", "bv*[height<=720]+ba/b[height<=720]", "--paths", "<RUN_DIR>/media", "--output", "EV-media.%(ext)s", "--", "<URL>"]
}
```

`--max-filesize` is an extractor filter, not a guaranteed combined-stream or unknown-size byte limit. A controlling runner must impose the approved aggregate bytes (default 500 MB), wall time (default 10 minutes per subprocess), request/process budget and directory containment, terminate on excess, and retain partials with a failure record. If the host cannot enforce these bounds, defer the download instead of running an unbounded process. All output files, including `.part`, stderr and JSON, are inventoried; only verified complete media counts as DONE. Verify the actual installed `yt-dlp` version/options and ffmpeg capability before running; unsupported options stop the operation.

- Logged-out only. Age-gated, private, unlisted-with-login, members-only or region-blocked content is recorded as `not accessible without authentication` / `not accessible from this environment` and goes to the lawful-request sheet; no VPN, no cookies, no proxies (R2).
- Dates: `publishDate`/`upload_date` are platform-stated; the capture timestamp is yours; both recorded. Platform dates are in the platform's convention (YouTube `upload_date` has no time component) — say so.
- Counts are platform-computed and change constantly; the S10 re-check shows the drift.
- The media file hash is the hash of the file as `yt-dlp` assembled it from the chosen format; a different format choice gives a different hash. Record the format ID and the command so it is reproducible; the platform's own original file is obtainable only by lawful request.
- Captions served by the platform are captured as files; the AI never produces or "corrects" a transcript (AFC-11).
- Comments are captured only as served, capped, and never replied to.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| `yt-dlp` not installable or blocked by the platform ("Sign in to confirm you're not a bot") | Record the exact message; media and metadata via `yt-dlp` become DEFERRED (Investigator runs the printed command locally without cookies); S2/S3 still stand |
| Download exceeds the cap or wall-time budget | Stop, retain partial bytes and diagnostics as PARTIAL, and propose a smaller supported format through the approved change procedure; never silently retry another format or call partial output complete |
| Video removed / private during the run | Capture the removal page as its own EV item; record the time; the lawful-request sheet gets "content removed at <UTC>" |
| oEmbed and page JSON disagree (title changed) | Keep both; state the disagreement as a fact with both EV refs |
| Platform not supported by `yt-dlp` | Page capture only; media DEFERRED with a note |
| Host assistant declines to process the video content | `DECLINED-BY-HOST`; the files remain evidence; no content description |

### 9.6 Findings structure

1. **Video identity** — platform, video ID, URL as given, canonical URL, title as displayed, uploader handle and channel ID (EV refs).
2. **Platform-stated metadata** — upload/publish date, duration, category, counts at capture, with the S10 drift.
3. **Media captured** — file(s), format, hash, duration from `ffprobe` if available; or DEFERRED note.
4. **Transcript** — languages captured as served (files); no quotation of transcript text unless intake field 7 names a passage, then verbatim with EV ref.
5. **Uploader identifiers** — table; the channel is a Lead.
6. **Comments** — count captured, file; no synthesis.
7. **Context** — archive status, mirrors/mentions captured.
8. **Not accessible** — anything gated.

### 9.7 XLSX sheets

`Video_Metadata` (field, value, source (page/oEmbed/yt-dlp), UTC, EV) · `Media_Files` (file, format id, size, SHA-256, command, EV) · `Captions` (language, kind (auto/creator), file, SHA-256, EV) · `Uploader` (field, value, EV) · `Comments` (if captured: author, text, displayed time, likes, EV) · `Mentions` (URL, title, context, EV).

### 9.8 Interpretation cautions

- The uploader's account name is not a person's identity; account holder data needs a lawful request to the platform.
- Platform dates and counts are as the platform reports them; they are not independent measurements.
- A downloaded media file is a re-encoded distribution copy, not the uploader's original; the original and the upload logs exist only at the platform.
- Automatic captions are machine-generated by the platform and may be wrong; they are captured as served, as a record of what the platform showed.
- Option semantics are documented in the [official yt-dlp README](https://github.com/yt-dlp/yt-dlp#readme); retain the installed tool version and verify its supported options rather than assuming the moving documentation describes an older executable.

### 9.9 Leads policy

The uploader's channel (L1-SOC); other channels/handles in the description or comments (L1-USR); links in the description (L1-WEB/L1-DOM); thumbnails and frames for verification (L1-IMG); the lawful request to the platform for account holder data and the original upload.

### 9.10 Self-test specification

The versioned `selftest/L1-VID.selftest.json` is the machine-readable assertion contract. Missing required fixtures, adapters or expected results yield INCOMPLETE, never PASS. Offline regression results and optional live-provider smoke results are reported separately.

Required offline checks parse the §9.4 argv contract: every operation disables user config and playlists; metadata/comments/captions skip media; media has bounded retries and aborts missing fragments; creator/automatic captions have separate paths. A URL with `list=` must retain one-video scope; a fake worker exceeding byte/time budget must terminate and remain PARTIAL. Optional live target `https://www.youtube.com/watch?v=jNQXAC9IVRw` may check oEmbed and metadata availability within budget, with media/comments downloads off unless separately approved. A successful smoke query does not certify media, captions or host compliance.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Uploader identity, upload logs, original file, removed/private content | platform (Google LLC for YouTube; the respective operator otherwise) | preservation, then disclosure (subscriber/registration data) | video ID, channel ID, handle, URL, upload date, UTC capture time | account registration data, IP logs for upload and login, original media, content as uploaded |
| Commenters named in the case | platform | preservation | comment author handle, video ID, displayed time → UTC capture | account data |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–20 minutes without the media download; add 5–30 minutes for the download depending on size and the sandbox's bandwidth. Longest steps S5 and S8.
