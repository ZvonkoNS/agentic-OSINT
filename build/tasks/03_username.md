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
- Preserve the complete Unicode handle and its script; reject control characters, whitespace and URL/credential forms. Each selected platform adapter validates its own supported character set, length and normalization before any request. `INVALID_FOR_PLATFORM` is not `NOT_FOUND`; unsupported internationalized handles are `UNSUPPORTED_BY_ADAPTER`, not invalid identities.
- Case and comparison keys are platform-specific; keep the raw handle and platform/instance namespace. A transformation is used only when the versioned adapter documents that service's equivalence rule. Never assume that the same handle string on two services names the same account.

**Intake additions (printed with the form):** field **16** = "Approved platform/instance list (default: select from 9.4; the exact destination list is shown before requests)". Authorisation **D** = "Optional additional enumeration: approve the explicitly listed additional platforms and target-bearing destinations? Y/N (default N)". A general web-app approval is not approval to send the handle to hundreds of unspecified sites.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| Direct profile URL probes (approved subset of 9.4) | Public existence per platform | B | Only a tested platform-specific classifier may return EXISTS/NOT_FOUND; generic HTTP/size differences remain INCONCLUSIVE |
| Public JSON endpoints: GitHub `https://api.github.com/users/<h>`, Keybase `https://keybase.io/_/api/1.0/user/lookup.json?usernames=<h>`, Mastodon `https://mastodon.social/api/v1/accounts/lookup?acct=<h>` (and the same path on any other instance named in the case) | Structured attributes | B | Keyless; rate-limited |
| WhatsMyName dataset or optional UI (`https://whatsmyname.app`) | Candidate platform discovery | C | Freeze a versioned dataset and restrict execution to the intake-approved subset. If the UI cannot demonstrably restrict target-bearing requests to that exact list, do not run its bulk sweep. Additional destinations require D and scope approval before the request; every hit remains a candidate until directly verified |
| Search engines: `"<handle>"` | Mentions outside platforms | C → A | Capture only cited result pages |
| Each existing profile page (logged-out) | Attribute capture | A (B fallback) | Full-page screenshot + saved page |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Preserve input; freeze platform/instance scope, adapter versions and per-platform validated handle; print destinations, request budget and control method. Do not run unsupported platform adapters or R-marked sandbox probes | — |
| S2 | Control probes (approved P-marked platforms with tested adapters): generate two different syntactically valid nonexistent-candidate handles under that platform's grammar, save exact values/requests, and verify the adapter's explicit not-found signature. A control that exists is replaced once within budget; conflicting/blocked controls make target classification INCONCLUSIVE | B |
| S3 | Target probes: record EXISTS only with platform-specific positive evidence (stable account ID and exact canonical handle/profile field, or another documented positive signature tested against login, reserved-route and soft-404 fixtures); NOT_FOUND only with the tested explicit negative signature. Preserve INVALID_FOR_PLATFORM, RENAMED, SUSPENDED, AUTH_REQUIRED, BLOCKED, UNSUPPORTED_BY_ADAPTER and INCONCLUSIVE separately. Save headers and bytes for all results. R-marked platforms use approved level A if available | B / A |
| S4 | Structured endpoints: GitHub, Keybase, Mastodon lookup JSON | B |
| S5 | Optional expanded sweep: only the frozen additional subset approved under D, using bounded adapters; otherwise SKIPPED. UI results are candidates and do not expand destinations or scope. Re-verify each approved candidate by S3 before it counts | A / B |
| S6 | Profile captures: for every `EXISTS` result, full capture of the public profile page (up to 20 profiles; remainder to the post-run list) | A (B fallback) |
| S7 | Attribute table from captured copies: display name, bio, stated location, links, join/creation date, follower/following/post counts, verification badge, avatar file (captured) with SHA-256 and perceptual hash (if `imagehash` available) | — (derived) |
| S8 | Search-engine mentions: results page captured; up to 10 relevant result URLs captured as level B/A | C → A |
| S9 | Linkage indicators: same avatar hash, same bio text, cross-links between profiles, same display name — recorded as observations with EV refs, never as a conclusion | — |
| S10 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Candidate platform list (select and approve before requests)

These are candidate URL patterns, not a tested compatibility matrix (`<h>` is escaped as a path component by the adapter). P/R labels are historical hints only: the actual response and installed adapter determine support. Select the required subset at intake, record exact hosts including instances, and do not add a destination merely because a search result or dataset mentions it. Without a supported classifier, preserve a page as a candidate and report INCONCLUSIVE:

`github.com/<h>` (P) · `gitlab.com/<h>` (P) · `x.com/<h>` (R – often requires login) · `instagram.com/<h>` (R) · `facebook.com/<h>` (R) · `tiktok.com/@<h>` (P/R) · `youtube.com/@<h>` (P) · `reddit.com/user/<h>` (P) · `t.me/<h>` (P – public channel/user preview) · `linkedin.com/in/<h>` (R) · `pinterest.com/<h>` (P) · `twitch.tv/<h>` (P) · `steamcommunity.com/id/<h>` (P) · `soundcloud.com/<h>` (P) · `medium.com/@<h>` (P) · `keybase.io/<h>` (P) · `about.me/<h>` (P) · `vk.com/<h>` (P/R) · `mastodon.social/@<h>` (P; other instances are Leads) · `bsky.app/profile/<h>.bsky.social` (P) · `threads.net/@<h>` (P/R) · `flickr.com/people/<h>` (P) · `vimeo.com/<h>` (P) · `patreon.com/<h>` (P) · `discord` — no public profile URL; record "not probeable" · `snapchat.com/add/<h>` (P/R) · `telegram` covered by t.me · `tumblr.com` → `<h>.tumblr.com` (P) · `dev.to/<h>` (P) · `hackerone.com/<h>` (P).

Platforms marked R return a login shell or a bot wall to sandbox requests, so sandbox probes of them (control or target) are wasted and are not run. They are checked only at level A via G3; otherwise they are recorded `INCONCLUSIVE (not probeable from this environment)` and listed in the post-run Investigator steps.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Platform returns 200 for a negative control (soft-404) | Use only the tested platform-specific explicit negative and positive signatures. Size differences alone never establish existence; login shells, reserved paths or ambiguous content → INCONCLUSIVE |
| Bot wall / 403 on probe | Mark INCONCLUSIVE; level-A check via G3 if available for that platform only; else post-run list |
| Login wall | Record `not accessible without authentication`; Lead: lawful platform request |
| Rate limit (GitHub 60/h keyless, Reddit, others) | Pause; reorder; do not add keys or accounts |
| Platform redirects to a different handle (renamed account) | Record both handles and the redirect evidence; the new handle is a Lead, not a target |
| Avatar download blocked | Capture the avatar as part of the level-A screenshot; note "avatar file not separately captured" |
| More than 20 profiles exist | Capture the first 20 in list order; the rest go to the post-run list with the §5.7 procedure |

### 9.6 Findings structure

1. **Probe results** — table: platform/instance, adapter/version, result, precise positive/negative basis, stable ID if captured and EV ref. Keep unsupported/invalid/renamed/suspended/blocked results separate; totals include approved, attempted, conclusive and omitted platforms rather than implying a complete Internet search.
2. **Captured profiles** — one short neutral paragraph per existing profile (what the public page shows), EV refs.
3. **Attribute comparison** — the S7 table side by side.
4. **Linkage observations** — S9, phrased as "the avatars of profiles X and Y are visually near-identical (perceptual-hash distance 2, EV-012/EV-019; platforms re-encode avatars, so byte-identical files are not expected)" — never "belong to the same person". This sub-section is labelled **Analysis (outside ISO/IEC 27037 — opinion)**.
5. **Mentions outside platforms** — captured search results.
6. **Not probeable / not accessible** — list with reasons.

### 9.7 XLSX sheets

`Platform_Probes` (platform, instance, adapter/version, raw handle, comparison key, URL, control values/results, target result, positive/negative field or signature, stable ID, UTC, EV) · `Scope_Coverage` (platform, approved Y/N, attempted Y/N, omitted reason) · `Profiles_Captured` (platform, URL, EV screenshot, EV page, SHA-256s) · `Profile_Attributes` (platform, display name, bio, location, links, created, followers, following, posts, verified, avatar SHA-256, avatar phash, EV) · `Linkage_Indicators` (indicator, profiles involved, basis, EV refs) · `Mentions` (URL, title, snippet, captured EV).

### 9.8 Interpretation cautions

- **Same handle ≠ same person.** Handles are reused, squatted, impersonated and recycled after deletion. This report establishes existence and public attributes only.
- A `NOT FOUND` result means the public URL did not resolve to a profile at that time; it does not prove the handle was never registered (suspended, private or deleted accounts can return the same signature).
- `INCONCLUSIVE` results are not evidence either way.
- Attribute values are as displayed at capture time; counts and bios change.
- Perceptual-hash similarity between avatars is an indicator for review, not identification.

### 9.9 Leads policy

Handle variants; renamed-account targets; other Mastodon/Fediverse instances; profiles to preserve fully (L1-SOC); avatars for reverse search (L1-IMG); emails/domains found in bios (L1-EML/L1-DOM).

### 9.10 Self-test specification

The versioned `selftest/L1-USR.selftest.json` is the machine-readable assertion contract. Missing required observations, fixtures or adapters yield INCOMPLETE, never PASS. Required offline adapter fixtures include existing, nonexistent, invalid-syntax, login-shell, soft-404, renamed, suspended, localized and blocked responses. A 200 login shell or differently sized generic page must not become EXISTS; a control outside the platform grammar must not be used. Optional live smoke target: `Gargron` on explicitly approved services only, recording current values and coverage rather than assuming IDs, dates or provider availability remain fixed. `skip: S5, S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Account holder data for an existing profile | the platform (one sheet per platform with an EXISTS result that the case needs) | preservation | handle, profile URL, stable ID where captured, capture UTC | registration data, login IP logs, linked email/phone |
| INCONCLUSIVE platforms the case needs | the platform | preservation | handle, probe URL, UTC | confirmation of account existence and the above |

### 9.12 Duration estimate

Typical FULL-mode duration: 15–30 minutes (two probes per platform plus profile captures); longest steps S3 and S6.
