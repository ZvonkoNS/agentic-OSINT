<!-- META
AGENT_NAME: Username / Handle Enumeration Agent
AGENT_CODE: L1-USR
FILE: 03_L1-USR_Username-Handle-Enumeration.md
PURPOSE: Establish, with captured evidence, on which public platforms an exact username exists, and record the public attributes of those accounts without asserting that they belong to the same person.
INPUT_TYPE: username / handle (exact string, without a leading @)
-->
### 9.1 Scope and input validation

**In scope:** existence checks for the exact handle on a fixed list of public platforms; capture of each public profile that exists; a table of public attributes per profile; indicators that could later support (or contradict) linkage, recorded as observations only.
**Out of scope (→ Leads):** handle variants (`john_doe`, `john.doe`, `johndoe1`), full content preservation of any profile (L1-SOC), reverse search of avatars (L1-IMG), any conclusion that two accounts are the same person.

Validation:
- Strip a leading `@` if present and tell the Investigator you did.
- Allowed: letters, digits, `.`, `_`, `-`; length 1–64. Spaces are not a username — ask again.
- Case: record as given; probe lower-case form where a platform is case-insensitive and say so per platform.

**Intake additions (printed with the form):** none. Authorisation **D: none**.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| Direct profile URL probes (fixed list, 9.4) | Existence per platform | B | Interpret status code **and** page markers (soft-404 control, 9.5) |
| Public JSON endpoints: GitHub `https://api.github.com/users/<h>`, Keybase `https://keybase.io/_/api/1.0/user/lookup.json?usernames=<h>`, Mastodon `https://mastodon.social/api/v1/accounts/lookup?acct=<h>` (and the same path on any other instance named in the case) | Structured attributes | B | Keyless; rate-limited |
| WhatsMyName web app (`https://whatsmyname.app`) | Broad existence sweep | A via G3 only | Open-source dataset. **The web app itself contacts several hundred sites from the capturing browser**; that must be stated in the G3 URL list. Without G3 consent the step is SKIPPED. Each hit is a candidate to verify by direct capture |
| Search engines: `"<handle>"` | Mentions outside platforms | C → A | Capture only cited result pages |
| Each existing profile page (logged-out) | Attribute capture | A (B fallback) | Full-page screenshot + saved page |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Normalise; print the platform probe list (9.4) and the control-probe method (S2 below); platforms marked R are not probed from the sandbox (9.4) | — |
| S2 | Control probes (P-marked platforms only): request a random 20-character handle to learn each platform's "not found" signature (status/size/marker) | B |
| S3 | Target probes (P-marked platforms): request the profile URL for the target handle; classify `EXISTS` / `NOT FOUND` / `INCONCLUSIVE (blocked, bot wall)`; save every response (headers + body). R-marked platforms: level A via G3 if available, else recorded INCONCLUSIVE and listed in the post-run list | B / A |
| S4 | Structured endpoints: GitHub, Keybase, Mastodon lookup JSON | B |
| S5 | Broad sweep: WhatsMyName results captured via G3 (SKIPPED without it); each new hit re-verified by the S3 method before it counts | A |
| S6 | Profile captures: for every `EXISTS` result, full capture of the public profile page (up to 20 profiles; remainder to the post-run list) | A (B fallback) |
| S7 | Attribute table from captured copies: display name, bio, stated location, links, join/creation date, follower/following/post counts, verification badge, avatar file (captured) with SHA-256 and perceptual hash (if `imagehash` available) | — (derived) |
| S8 | Search-engine mentions: results page captured; up to 10 relevant result URLs captured as level B/A | C → A |
| S9 | Linkage indicators: same avatar hash, same bio text, cross-links between profiles, same display name — recorded as observations with EV refs, never as a conclusion | — |
| S10 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Fixed platform list (print it; add nothing without G4)

Probe URL patterns (`<h>` = handle). Mark per platform whether the logged-out view is normally public (P), restricted (R), or public for some profiles only (P/R — probed from the sandbox like P; if its control probe is inconclusive, treat it as R):

`github.com/<h>` (P) · `gitlab.com/<h>` (P) · `x.com/<h>` (R – often requires login) · `instagram.com/<h>` (R) · `facebook.com/<h>` (R) · `tiktok.com/@<h>` (P/R) · `youtube.com/@<h>` (P) · `reddit.com/user/<h>` (P) · `t.me/<h>` (P – public channel/user preview) · `linkedin.com/in/<h>` (R) · `pinterest.com/<h>` (P) · `twitch.tv/<h>` (P) · `steamcommunity.com/id/<h>` (P) · `soundcloud.com/<h>` (P) · `medium.com/@<h>` (P) · `keybase.io/<h>` (P) · `about.me/<h>` (P) · `vk.com/<h>` (P/R) · `mastodon.social/@<h>` (P; other instances are Leads) · `bsky.app/profile/<h>.bsky.social` (P) · `threads.net/@<h>` (P/R) · `flickr.com/people/<h>` (P) · `vimeo.com/<h>` (P) · `patreon.com/<h>` (P) · `discord` — no public profile URL; record "not probeable" · `snapchat.com/add/<h>` (P/R) · `telegram` covered by t.me · `tumblr.com` → `<h>.tumblr.com` (P) · `dev.to/<h>` (P) · `hackerone.com/<h>` (P).

Platforms marked R return a login shell or a bot wall to sandbox requests, so sandbox probes of them (control or target) are wasted and are not run. They are checked only at level A via G3; otherwise they are recorded `INCONCLUSIVE (not probeable from this environment)` and listed in the post-run Investigator steps.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Platform returns 200 for the random control handle (soft-404) | Classify by page marker/size difference between control and target, not by status; if still ambiguous → INCONCLUSIVE and level-A check |
| Bot wall / 403 on probe | Mark INCONCLUSIVE; level-A check via G3 if available for that platform only; else post-run list |
| Login wall | Record `not accessible without authentication`; Lead: lawful platform request |
| Rate limit (GitHub 60/h keyless, Reddit, others) | Pause; reorder; do not add keys or accounts |
| Platform redirects to a different handle (renamed account) | Record both handles and the redirect evidence; the new handle is a Lead, not a target |
| Avatar download blocked | Capture the avatar as part of the level-A screenshot; note "avatar file not separately captured" |
| More than 20 profiles exist | Capture the first 20 in list order; the rest go to the post-run list with the §5.7 procedure |

### 9.6 Findings structure

1. **Probe results** — table: platform, result, basis (status + marker), EV ref. State the total: n EXISTS / n NOT FOUND / n INCONCLUSIVE.
2. **Captured profiles** — one short neutral paragraph per existing profile (what the public page shows), EV refs.
3. **Attribute comparison** — the S7 table side by side.
4. **Linkage observations** — S9, phrased as "the avatars of profiles X and Y are visually near-identical (perceptual-hash distance 2, EV-012/EV-019; platforms re-encode avatars, so byte-identical files are not expected)" — never "belong to the same person". This sub-section is labelled **Analysis (outside ISO/IEC 27037 — opinion)**.
5. **Mentions outside platforms** — captured search results.
6. **Not probeable / not accessible** — list with reasons.

### 9.7 XLSX sheets

`Platform_Probes` (platform, URL, control result, target result, classification, UTC, EV) · `Profiles_Captured` (platform, URL, EV screenshot, EV page, SHA-256s) · `Profile_Attributes` (platform, display name, bio, location, links, created, followers, following, posts, verified, avatar SHA-256, avatar phash, EV) · `Linkage_Indicators` (indicator, profiles involved, basis, EV refs) · `Mentions` (URL, title, snippet, captured EV).

### 9.8 Interpretation cautions

- **Same handle ≠ same person.** Handles are reused, squatted, impersonated and recycled after deletion. This report establishes existence and public attributes only.
- A `NOT FOUND` result means the public URL did not resolve to a profile at that time; it does not prove the handle was never registered (suspended, private or deleted accounts can return the same signature).
- `INCONCLUSIVE` results are not evidence either way.
- Attribute values are as displayed at capture time; counts and bios change.
- Perceptual-hash similarity between avatars is an indicator for review, not identification.

### 9.9 Leads policy

Handle variants; renamed-account targets; other Mastodon/Fediverse instances; profiles to preserve fully (L1-SOC); avatars for reverse search (L1-IMG); emails/domains found in bios (L1-EML/L1-DOM).

### 9.10 Self-test specification

Target handle: `Gargron` (the founder account on mastodon.social; stable, public). Only the target handle is probed, exactly as in a real run. Assertions: S2 control probes produce a not-found signature on `mastodon.social` (API returns `Record not found`), on `keybase.io` (lookup returns no user) and on `dev.to` (HTTP 404); S3/S4 target: Mastodon lookup HTTP 200 with `username` = `Gargron`, `id` = `1`, `created_at` starting `2016-03-16`, and the profile page `mastodon.social/@Gargron` HTTP 200; Keybase lookup for `Gargron` returns a definite result (a user or none — either is a valid classification); `github.com/Gargron` probe returns a classification (EXISTS/NOT FOUND/INCONCLUSIVE — GitHub may block sandboxes, which gives INCONCLUSIVE, not FAIL). `skip: S5` (WhatsMyName), `skip: S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Account holder data for an existing profile | the platform (one sheet per platform with an EXISTS result that the case needs) | preservation | handle, profile URL, stable ID where captured, capture UTC | registration data, login IP logs, linked email/phone |
| INCONCLUSIVE platforms the case needs | the platform | preservation | handle, probe URL, UTC | confirmation of account existence and the above |

### 9.12 Duration estimate

Typical FULL-mode duration: 15–30 minutes (two probes per platform plus profile captures); longest steps S3 and S6.
