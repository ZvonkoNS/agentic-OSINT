<!-- META
AGENT_NAME: Social Media Profile Preservation Agent
AGENT_CODE: L1-SOC
FILE: 06_L1-SOC_Social-Media-Profile-Preservation.md
PURPOSE: Preserve one public social-media profile — its attributes, platform identifiers, public posts within scope and their media — as hashed, individually cited evidence items.
INPUT_TYPE: public profile URL on a social-media platform
-->
### 9.1 Scope and input validation

**In scope:** the profile page as visible without login; profile attributes; the platform's stable account identifier where exposed; the deterministic public-post selection approved at intake (default: 25 unique original posts by this account, replies/reposts excluded); publicly downloadable media attached to selected posts; public links recorded as strings.
**Out of scope (→ Leads):** anything behind a login (followers lists, private posts, stories, DMs); other accounts of the same person; content from other platforms; interaction of any kind.

**Module requirement for FULL mode:** every required intake-selected capture must have a supported method. A rendered-view requirement needs CAP-BROWSER; a complete official public API path may support structured level-B acquisition without a browser. Test the actual environment; never infer availability from a product name or claim a sandbox always sees a login shell. Unavailable required fields/views make coverage INCOMPLETE, regardless of mode. A browser screenshot and API record remain different artifacts.

Validation:
- Must be a URL to a profile/channel/page on a recognised platform (X, Instagram, Facebook, TikTok, YouTube, Telegram public channel/user, LinkedIn, Reddit, Threads, Bluesky, Mastodon instance, VK, Twitch, Pinterest, Tumblr). Others: ask the Investigator to confirm it is a profile and proceed generically.
- Post URLs are not profile URLs: if a post permalink is given, derive the profile URL, show it, and ask which one is the target; a single post is better handled by L1-WEB.
- Record the URL exactly as given; the platform's canonical profile URL is recorded separately in S2.

**Intake additions (printed with the form):** field **16** = "Post scope: N unique original posts (default 25) or a UTC date range; include replies/reposts? (default no); chronological or served-order view?; rendered-view required?"; field **17** = "Acquisition budgets (defaults: 200 seen items, 20 pages/cursors, 25 individual post captures, 20 minutes acquisition wall time, 25 media files / 100 MB aggregate / 20 MB each)". A request for more post captures must raise the budget explicitly at intake. Authorisation **D: none**.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| Profile page, logged-out, clean profile | Primary | A (B parallel) | Scroll capture with sequential screenshots |
| Page source / embedded JSON of the profile page | Stable account ID (numeric/UUID), creation data where present | B (from captured page) | Platforms often embed `id`, `user_id`, `channelId`, `rest_id` |
| Post permalinks | Per-post evidence | A/B | Each cited post captured individually |
| Direct media URLs exposed in the page or post source | Media files | B | Only public, unauthenticated URLs |
| `yt-dlp` on the Investigator's workstation (if present) | Public video download with metadata JSON | A1, post-run (§5.8) | Public content only; never with cookies or a login (R2); record version and command |
| Platform's public "about"/transparency fields (join date, location, verification) | Attributes | A/B | As displayed |
| Platform public API where one exists without login (Bluesky `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=<handle>` and `app.bsky.feed.getAuthorFeed?actor=<handle>&limit=<n>`; Mastodon `/api/v1/accounts/lookup?acct=<h>` and `/api/v1/accounts/<id>/statuses`) | Stable ID, attributes, public posts as structured data | B | Keyless; saved verbatim as JSON |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Detect platform and adapter/version; assess actual logged-out/API visibility; freeze inclusion/order rules, desired count/date range and budgets. Prefer a supported official public API for structured collection; list any required rendered view separately | B |
| S2 | Profile capture: full-page screenshot, saved page/WARC, print-PDF; canonical profile URL; redirect chain if any | A (+B) |
| S3 | Attribute extraction from the captured copy: display name, handle, stable account ID (with the exact source element), bio, links, stated location, join/creation date, verification badge, follower/following/post counts, profile and banner images (captured as files with hashes) | — (derived) |
| S4 | Enumerate within the frozen page/seen/time budget, saving every API page/cursor or rendered timeline segment before extraction. Deduplicate by platform stable post ID (otherwise exact canonical permalink). Record pins, replies/reposts, source order, timestamps as stated and exclusions. Freeze selected IDs using 9.4 before individual captures | A / B |
| S5 | Capture every selected permalink up to the intake capture budget in the frozen order; no discretionary "most relevant" subset. Record each selected-but-missing item and why; unmet requested count or missing required captures makes coverage INCOMPLETE. An increase requires explicit scope/budget approval before new requests | A / B |
| S6 | Media: download public media of captured posts (images and video via direct public URLs, level B); media that needs `yt-dlp` is DEFERRED to the post-run list; each file an EV item | B |
| S7 | Links and mentions: outbound links in bio and captured posts; mentioned handles; hashtags — table only | — (derived) |
| S8 | Identifier cross-check: confirm that the stable account ID resolves to the same profile (platform-specific ID URL where one exists); record handle↔ID pair with UTC | A (B only where the platform serves the page without login) |
| S9 | Volatility re-check of the profile page at the end of the run (counts, bio, name) | A (B where available) |
| S10 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Clean, logged-out profile** only. Never use the Investigator's personal account; never log in with any account (R2). If a platform shows nothing without login, record that as the result for each walled element and point to a lawful platform request (preservation order) as the Lead.
- **Allowed interactions:** scroll; dismiss/reject cookie and login prompts; expand "show more"/"view replies" that reveal public content; switch tabs on the profile (Posts/Replies/Media) that are public. Log each. Nothing else — no like, follow, view-count-generating playback beyond what loading the page does, no story viewing, no "message".
- **Selection contract:** use unique original posts by the target account unless intake includes replies/reposts. Record pinned posts separately; a pin does not establish recency. When the captured API supplies exact source-stated publication times for the enumerated candidate set, sort descending by that value, breaking ties by stable post ID/permalink. If chronology cannot be established, preserve served order and label the selection `served-order sample`, never "the N most recent". For a date-range request, unknown dates remain `date inclusion unresolved`; never silently exclude them.
- **Coverage ledger:** retain every seen candidate with stable ID/permalink, source page/cursor and index, raw date, selected Y/N, exclusion/omission reason and capture result. A cursor loop, deleted/missing item, exhausted page budget or algorithmic timeline is a coverage limitation. Topic terms from intake may flag notes after collection but never replace the deterministic selection with model-ranked relevance.
- **Relative timestamps:** preserve the displayed string; capture a source-stated absolute tooltip/attribute separately when available. Derive an interval only with a documented rounding rule, viewer zone and capture-clock uncertainty; otherwise exact UTC is NOT_ESTABLISHED. Do not turn "3 hours ago" into an exact instant.
- **Time zone:** platforms render times in the viewer's locale; record the capturing environment's time zone with every displayed time.
- **Edited/deleted content:** if a post shows an "edited" marker, record it; if a post disappears between S4 and S5, record both states with EV refs.
- **Identity of the account, not the person:** the report establishes what this account displayed; it does not establish who operates it.
- **Media limits:** use the intake file/aggregate/per-file/time budgets, enforce them while streaming and record partial files as PARTIAL. A media item omitted by budget remains in the ledger with its source post. Per-platform download tools must use the bounded, single-item/no-cookie argument contract in L1-VID, never their unbounded defaults.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Login wall on the profile (common: Instagram, Facebook, X, LinkedIn) | Record what the walled view shows (often name, avatar, counts); mark elements `not accessible without authentication`; Lead: lawful platform request |
| Bot wall / rate limit during scrolling | Slow down; capture what loaded; continue later; never rotate identities |
| Stable ID not found in the page source | Record "not exposed in public page"; use the handle only; note that handles can change |
| Video download fails (DRM, signed URL expired, tool absent) | Capture the post page with the player visible; record "media not separately captured"; DEFERRED to post-run (`yt-dlp` on the workstation) or Lead for lawful request |
| Profile redirects to a different handle | Record the rename evidence; continue with the current canonical URL; old handle in Leads |
| Scope limit reached mid-thread | Stop at the limit; record extent; remainder to the post-run list |

### 9.6 Findings structure

1. **Account identity** — platform, URL as given, canonical URL, handle, stable ID with source element, verification status, join date (EV refs).
2. **Profile attributes** — table as captured; images with hashes.
3. **Public activity coverage** — requested/seen/selected/captured/omitted counts, inclusion/order rules, raw date span, cursor extent and incomplete requirements; describe only the captured set, never the account's complete history.
4. **Posts of note** — only if intake named explicit topic terms/rules; otherwise omit. Flagging notes does not alter selection. Each has the matching term/rule, permalink, displayed/source date or derived interval, EV refs and short checked excerpt.
5. **Links, mentions, hashtags** — tables.
6. **Walled elements** — what could not be seen and why.
7. **Stability** — S9 result.

### 9.7 XLSX sheets

`Profile_Attributes` (field, value, source element, EV) · `Posts` (stable ID, permalink, source page/cursor/index, pinned/reply/repost, displayed date, source timestamp/derived interval, order basis, selected Y/N, omission reason, text excerpt, media count, counts as shown, captured EV, SHA-256) · `Coverage` (requested, seen, selected, captured, omitted, limits, pagination complete Y/N, missing requirement) · `Media` (post permalink, media URL, type, capture result, file, SHA-256, EV) · `Links_and_Mentions` (type, value, where seen, EV) · `Walled_Elements` (element, platform message shown, EV).

### 9.8 Interpretation cautions

- The capture documents what the platform served to an anonymous viewer at that time; algorithms, locale, and login state change what is shown.
- Engagement counts are platform-computed and rounded; they are not independent facts.
- Account operation, authorship and impersonation cannot be determined from public pages alone.
- Platforms remove and edit content; agency-directed preservation requests may seek server-side retention but do not themselves establish that content was retained. This run records public captures only; any request and provider response are separate agency work.

### 9.9 Leads policy

Other handles seen (L1-USR); profile/post images for reverse search (L1-IMG); linked websites (L1-DOM/L1-WEB); the lawful platform request path (platform law-enforcement portal, stable ID and handle to cite).

### 9.10 Self-test specification

The versioned `selftest/L1-SOC.selftest.json` is the machine-readable assertion contract. Missing required observations, fixtures or adapters yield INCOMPLETE, never PASS. Required offline fixtures cover pinned posts, replies, reposts, duplicated pages/cursor loops, deleted selected posts, equal timestamps, unknown relative dates and more candidates than the capture budget. Repeated selection must yield the same ordered IDs and omission ledger; missing required captures must yield INCOMPLETE. Optional live smoke target: `https://bsky.app/profile/bsky.app`; use its supported public API, retain current returned identifiers and distinguish publication time in the post record from indexing time. The author feed can contain reposts of other accounts' posts: retain the original author and reposting account separately; do not require every post URI to contain the target DID or treat URI scheme validation as proof of authorship. `skip: S5, S6` means those capture paths were not tested, never that they passed.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Account holder identity, private content, deleted posts | the platform | preservation, then disclosure (subscriber/registration data) | handle, stable account ID (numeric ID / DID / channel ID), canonical profile URL, post permalinks, UTC window | registration data, login IP logs, content of listed posts, deleted content within retention |
| Media that could not be captured | the platform | preservation | post permalinks, media URLs as captured | the media files |

### 9.12 Duration estimate

Planning estimate: 15–35 minutes for 25 posts with media, plus investigator work where required. This is not a measured host benchmark; budgets cap acquisition even if the estimate is exceeded. Longest steps S4 and S5.
