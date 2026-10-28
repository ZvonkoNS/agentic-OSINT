<!-- META
AGENT_NAME: Telegram Channel & Public Profile Preservation Agent
AGENT_CODE: L1-TGM
FILE: 11_L1-TGM_Telegram-Channel-Preservation.md
PURPOSE: Preserve what Telegram shows publicly for one channel, group or user handle — the info page and, for public channels, the web preview of recent posts and their media — without a Telegram account, app or API key.
INPUT_TYPE: Telegram handle or link (t.me/<name>, t.me/s/<name>, @<name>, or an invite link t.me/+<hash> / t.me/joinchat/<hash>)
-->
### 9.1 Scope and input validation

**In scope:** the public info page `t.me/<name>` (title, description, subscriber/member count, photo); for public channels, the web preview `t.me/s/<name>` (recent posts, views, dates, forwarded-from labels, media); for public users and groups, whatever the info page shows; invite-link preview pages (what is visible before joining).
**Out of scope (→ Leads or prohibited):** joining anything; using a Telegram account, the official app, Telegram Desktop, Bot API or MTProto API (all require an account — R2); private channels/groups beyond the invite preview; member lists; message history older than the preview offers; "view in Telegram" buttons.

**Intake additions (printed with the form):** field **16** = "Post scope: the N most recent posts in the web preview (default 50; the preview itself caps what is public) or a date range". Authorisation **D: none**.

Validation:
- Accept `t.me/<name>`, `t.me/s/<name>`, `telegram.me/<name>`, `@<name>` (name: 5–32 chars, letters/digits/underscore), or an invite `t.me/+<hash>` / `t.me/joinchat/<hash>`. Normalise to `<name>` or `invite:<hash>`; record as given.
- `t.me/c/<id>/<n>` links point to private content and are `NOT-INVESTIGABLE` without an account; say so (core §3.1) and produce the short pack.
- A post link `t.me/<name>/<n>` is accepted: the channel is the target, the post number is recorded as the item of interest.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| `https://t.me/<name>` | Info page: title, description, counts, photo, "Preview channel" presence | B (A via G3) | Public; no account |
| `https://t.me/s/<name>` and `https://t.me/s/<name>?before=<post id>` | Web preview of a public channel: posts, text, dates, views, media, forward labels; pagination by `before` | B (A via G3) | Only public channels render here; users and groups return the info page |
| `https://t.me/+<hash>` / `joinchat` | Invite preview: title, description, member count | B | Nothing is joined |
| Media URLs in the preview page source (`cdn*.telesco.pe`, `telegram.org` CDN) | Photo/video/file downloads | B | Only what the page already exposes |
| Search engines: `"t.me/<name>"` | Mentions and mirrors | C → A/B | Capture cited pages |
| Wayback availability for `t.me/s/<name>` | Prior third-party snapshots | B | Context only |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Normalise; detect type (channel / user / group / invite / private); print the source list and the post scope | — |
| S2 | Info page capture: raw page + headers; extract title, `@name`, description, subscriber/member count (as displayed, e.g. "9 230 981 subscribers"), photo URL (captured as a file), presence of the "Preview channel" button | B (A via G3) |
| S3 | Preview capture (public channels only): page 1 of `t.me/s/<name>`; paginate with `before=` until the scope is reached; each page a separate EV item; extract per post: post number, permalink `t.me/<name>/<n>`, datetime from the `<time datetime>` attribute (UTC), text, views as displayed, forwarded-from label, reply-to, media presence | B (A via G3) |
| S4 | Media: download the media files the preview exposes for captured posts (photos; video where a direct URL is present); each an EV item; cap 25 files / 100 MB; remainder listed | B |
| S5 | Links and mentions: outbound URLs, `@handles`, hashtags, invite links in captured posts — table only | D |
| S6 | Volatility re-check: second fetch of the info page at the end of the run (count, title, description) | B |
| S7 | Mentions elsewhere: search results captured; up to 10 relevant pages captured | C → A/B |
| S8 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- No account, no app, no API. If the Investigator offers a Telegram account "to see more", refuse under R2 and record it; private content is a Lead for a lawful request to Telegram (R9).
- The web preview is served by Telegram's web server, logged-out; it reflects what Telegram chooses to show the public at that moment and may omit posts (restricted content, deleted posts). Say so in Limitations.
- Post timestamps come from the `datetime` attribute (ISO 8601, UTC) — record them as `captured`; the displayed relative form is recorded separately.
- Views are rounded by Telegram ("12.3K"); record as displayed.
- Forwarded-from labels name another channel as displayed; the other channel is a Lead, never profiled here.
- Invite links: the preview page shows the title and member count without joining; capture it and stop. Never click "Join".

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| `t.me/s/<name>` returns the info page only | The channel is not public-previewable (user, group, or restricted channel): record it; S3–S5 are `SKIPPED` with the reason `not accessible without authentication`; Lead: lawful request |
| Preview pagination stops early | Record the extent reached; note "preview limited by Telegram" |
| Media URL expires / 403 | Capture the post page with the media visible (A via G3 if available); record `media not separately captured` |
| Rate limited / 429 | Pause 60 s; reduce pagination speed |
| Channel renamed (redirect) | Record both names and the redirect; continue with the current one; old name in Leads |

### 9.6 Findings structure

1. **Target identity** — type, `@name`, title, description, counts as displayed, photo (EV refs).
2. **Public posts within scope** — count captured, date span, media count; table in the XLSX; short exact excerpts only for posts named in intake field 7.
3. **Forwards, links, mentions** — tables.
4. **Not accessible** — what Telegram did not show without an account.
5. **Stability** — S6 result.
6. **Mentions elsewhere** — captured pages.

### 9.7 XLSX sheets

`Channel_Info` (field, value, UTC, EV) · `Posts` (post no, permalink, datetime UTC, text, views shown, forwarded from, media count, EV page, media EVs) · `Media` (post no, URL, file, SHA-256, EV) · `Links_and_Mentions` (type, value, post no, EV) · `Mentions_Elsewhere` (URL, title, context, EV).

### 9.8 Interpretation cautions

- A channel's display name, description and handle are set by its operator and can change at any time; this report shows them as at the capture time.
- Subscriber counts and views are Telegram-computed, rounded and not independently verifiable.
- Nothing here identifies who operates the channel; that needs a lawful request to Telegram (see the lawful-request sheet).
- Content visible in the web preview can differ from what app users see.

### 9.9 Leads policy

Forwarded-from channels and mentioned handles (separate L1-TGM runs); outbound links (L1-WEB/L1-DOM); media for verification (L1-IMG); the lawful request to Telegram for operator/subscriber data.

### 9.10 Self-test specification

Target: `t.me/telegram` (Telegram's own official news channel). Assertions: info page HTTP 200; title displayed equals `Telegram News`; `@telegram` present; subscriber count displayed matches `\d[\d\s,.]*\s*subscribers` (value drifts — pattern only); preview `t.me/s/telegram` HTTP 200 with ≥ 10 posts on page 1; every captured post has an ISO datetime; ≥ 1 media file captured; S7 skipped (`skip: S7` — search-engine step not needed for the test).

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Channel/group operator identity, private content, member lists, deleted posts | Telegram (platform) | preservation, then disclosure (subscriber/registration data) | `@name`, numeric channel ID if captured, post permalinks, UTC window | account/registration data of the creator and admins, IP logs where retained, content of the listed posts |
| Media hosted on Telegram CDN that expired | Telegram | preservation | post permalinks, media URLs as captured | the media files |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–25 minutes for a channel with 50 posts in scope; longest step S3 (pagination) and S4 (media). ASSISTED mode adds the Investigator's capture time per page.
