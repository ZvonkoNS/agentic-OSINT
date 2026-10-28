<!-- META
AGENT_NAME: Social Media Profile Preservation Agent
AGENT_CODE: L1-SOC
FILE: 06_L1-SOC_Social-Media-Profile-Preservation.md
PURPOSE: Preserve one public social-media profile — its attributes, platform identifiers, public posts within scope and their media — as hashed, individually cited evidence items.
INPUT_TYPE: public profile URL on a social-media platform
-->
### 9.1 Scope and input validation

**In scope:** the profile page as visible without login; profile attributes; the platform's stable account identifier where the page exposes it; public posts within the scope limit (default: the 50 most recent, or the date range in intake field 7); publicly downloadable media attached to captured posts; public links from the profile.
**Out of scope (→ Leads):** anything behind a login (followers lists, private posts, stories, DMs); other accounts of the same person; content from other platforms; interaction of any kind.

**Module requirement for FULL mode:** CAP-BROWSER is required, kind (a) — an extension in the Investigator's own browser — preferred. Sandbox requests to X, Instagram, Facebook, LinkedIn, TikTok and Threads return login shells with no profile data or stable ID; without a browser the mode is ASSISTED and the plan announcement says that most steps will need the Investigator's browser. YouTube, Reddit, Telegram public channels, Bluesky and Mastodon are usable at level B.

Validation:
- Must be a URL to a profile/channel/page on a recognised platform (X, Instagram, Facebook, TikTok, YouTube, Telegram public channel/user, LinkedIn, Reddit, Threads, Bluesky, Mastodon instance, VK, Twitch, Pinterest, Tumblr). Others: ask the Investigator to confirm it is a profile and proceed generically.
- Post URLs are not profile URLs: if a post permalink is given, derive the profile URL, show it, and ask which one is the target; a single post is better handled by L1-WEB.
- Record the URL exactly as given; the platform's canonical profile URL is recorded separately in S2.

**Intake additions (printed with the form):** field **16** = "Scope of posts: the N most recent (default 50) or a date range". Authorisation **D: none**.

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
| S1 | Platform detection; public-visibility assessment with a logged-out level-B fetch (what is visible, what is walled); print the scope limit (N posts or date range) | B |
| S2 | Profile capture: full-page screenshot, saved page/WARC, print-PDF; canonical profile URL; redirect chain if any | A (+B) |
| S3 | Attribute extraction from the captured copy: display name, handle, stable account ID (with the exact source element), bio, links, stated location, join/creation date, verification badge, follower/following/post counts, profile and banner images (captured as files with hashes) | — (derived) |
| S4 | Post list within scope: scroll the public timeline; sequential screenshots; extract permalinks, displayed dates (relative → computed UTC), text, media presence, engagement counts as shown; build the `Posts` table | A |
| S5 | Per-post capture: open each permalink (up to 25 most relevant/recent; remainder listed; extension via G4); full capture of each | A (B fallback) |
| S6 | Media: download public media of captured posts (images and video via direct public URLs, level B); media that needs `yt-dlp` is DEFERRED to the post-run list; each file an EV item | B |
| S7 | Links and mentions: outbound links in bio and captured posts; mentioned handles; hashtags — table only | — (derived) |
| S8 | Identifier cross-check: confirm that the stable account ID resolves to the same profile (platform-specific ID URL where one exists); record handle↔ID pair with UTC | A (B only where the platform serves the page without login) |
| S9 | Volatility re-check of the profile page at the end of the run (counts, bio, name) | A (B where available) |
| S10 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Clean, logged-out profile** only. Never use the Investigator's personal account; never log in with any account (R2). If a platform shows nothing without login, record that as the result for each walled element and point to a lawful platform request (preservation order) as the Lead.
- **Allowed interactions:** scroll; dismiss/reject cookie and login prompts; expand "show more"/"view replies" that reveal public content; switch tabs on the profile (Posts/Replies/Media) that are public. Log each. Nothing else — no like, follow, view-count-generating playback beyond what loading the page does, no story viewing, no "message".
- **Relative timestamps:** capture the displayed string; hover/tooltip absolute time if the platform shows one on hover (record the hover as an allowed interaction); compute UTC from the capture timestamp otherwise and mark `computed`.
- **Time zone:** platforms render times in the viewer's locale; record the capturing environment's time zone with every displayed time.
- **Edited/deleted content:** if a post shows an "edited" marker, record it; if a post disappears between S4 and S5, record both states with EV refs.
- **Identity of the account, not the person:** the report establishes what this account displayed; it does not establish who operates it.
- **Media limits:** default 25 files / 100 MB (hosts cap downloadable output); beyond, list in the inventory and in the post-run list.

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
3. **Public activity within scope** — summary counts (posts captured, media captured), date span, and a neutral description of recurring content types; no character assessment.
4. **Posts of note** — only if intake field 7 named a topic; otherwise omit; each with permalink, displayed date, computed UTC, EV refs, short exact excerpt.
5. **Links, mentions, hashtags** — tables.
6. **Walled elements** — what could not be seen and why.
7. **Stability** — S9 result.

### 9.7 XLSX sheets

`Profile_Attributes` (field, value, source element, EV) · `Posts` (permalink, displayed date, computed UTC, text excerpt, media count, likes/replies/shares as shown, captured EV, SHA-256) · `Media` (post permalink, media URL, type, file, SHA-256, EV) · `Links_and_Mentions` (type, value, where seen, EV) · `Walled_Elements` (element, platform message shown, EV).

### 9.8 Interpretation cautions

- The capture documents what the platform served to an anonymous viewer at that time; algorithms, locale, and login state change what is shown.
- Engagement counts are platform-computed and rounded; they are not independent facts.
- Account operation, authorship and impersonation cannot be determined from public pages alone.
- Platforms remove and edit content; a lawful preservation request to the platform is the only way to freeze the account server-side (Lead).

### 9.9 Leads policy

Other handles seen (L1-USR); profile/post images for reverse search (L1-IMG); linked websites (L1-DOM/L1-WEB); the lawful platform request path (platform law-enforcement portal, stable ID and handle to cite).

### 9.10 Self-test specification

Target: `https://bsky.app/profile/bsky.app` (Bluesky's own account; public API, no login). Assertions: `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=bsky.app` HTTP 200 with `handle` = `bsky.app` and `did` = `did:plc:z72i7hdynmk6r22z27h6tvur`, `createdAt` starting `2023-04-12`; profile page HTTP 200; S4 post list: `https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=bsky.app&limit=10` returns ≥ 5 feed items, each with a `uri` starting `at://did:plc:z72i7hdynmk6r22z27h6tvur/` and an ISO `indexedAt`; stable ID (DID) recorded; `skip: S5, S6` (per-post captures and media not needed); S9 drift line printed. Without CAP-BROWSER the self-test runs in ASSISTED mode and this is expected — the verdict notes it.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Account holder identity, private content, deleted posts | the platform | preservation, then disclosure (subscriber/registration data) | handle, stable account ID (numeric ID / DID / channel ID), canonical profile URL, post permalinks, UTC window | registration data, login IP logs, content of listed posts, deleted content within retention |
| Media that could not be captured | the platform | preservation | post permalinks, media URLs as captured | the media files |

### 9.12 Duration estimate

Typical FULL-mode duration: 20–45 minutes for 50 posts with media (browser scrolling is slow); longest steps S4 and S5.
