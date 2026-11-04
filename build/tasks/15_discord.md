<!-- META
AGENT_NAME: Discord Invite & Server Preview Agent
AGENT_CODE: L1-DSC
FILE: 15_L1-DSC_Discord-Invite-and-Server-Preview.md
PURPOSE: Document what Discord exposes publicly about one invite link or server ID — server name, numeric ID, approximate member counts, the invite's target channel, the inviter where shown, public widget data where enabled — without joining, without an account and without the Discord client.
INPUT_TYPE: Discord invite link (discord.gg/<code>, discord.com/invite/<code>) or a numeric server (guild) ID
-->
### 9.1 Scope and input validation

**In scope:** the invite resolution as returned by Discord's public endpoint (server name, guild ID, description, icon/banner, approximate member and presence counts, the invite's target channel name and ID, inviter display data where Discord includes it, expiry if stated, vanity URL); the public widget JSON if the server enabled it (channels listed in the widget, online members as the widget shows them); the invite landing page as rendered logged-out; mentions of the invite code on the open web.
**Out of scope (→ Leads or prohibited):** joining the server or any channel; using any Discord account, bot token or the client; reading messages; member lists beyond the public widget; Discord's user lookup by ID (needs a token); any interaction (R2).

**Intake additions (printed with the form):** none beyond the core. Authorisation **D: none**.

Validation:
- Invite code: 2–32 characters `[A-Za-z0-9-]`; accept with or without the `discord.gg` / `discord.com/invite` prefix; record as given.
- Numeric input: parse as an unsigned integer within the Discord ID range, preserve the raw string, and label it `unverified candidate guild ID` until a captured Discord object confirms its ID and type. The formula `(id >> 22) + 1420070400000` yields a computed millisecond timestamp, not proof that arbitrary numeric input identifies a real object. Decode only confirmed non-anonymized guild/channel/inviter fields, naming the exact source field; retain `.mmmZ` precision.
- A user ID or message link (`discord.com/channels/<guild>/<channel>/<message>`) is not an invite: record the guild ID from it as the target if present; message content is `not accessible without authentication`.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| `https://discord.com/api/v10/invites/<code>?with_counts=true&with_expiration=true` | Invite resolution: guild name/id/description/icon/banner/features, channel name/id/type, approximate_member_count, approximate_presence_count, expires_at, inviter (where included) | B | Public, no token |
| `https://discord.com/api/guilds/<guild id>/widget.json` | Public widget: name, instant_invite, channels, anonymized display records, presence_count | B | Parse the captured Discord error JSON as well as HTTP status; generic 403 is not proof of disabled settings |
| `https://discord.gg/<code>` landing page (logged-out) | Rendered preview | B (A via G3) | Shows name and counts; nothing more without login |
| Icon/banner CDN URLs from the invite JSON (`cdn.discordapp.com/icons/<guild id>/<hash>.png`) | Images | B | Hash of the image file |
| Search engines: `"discord.gg/<code>"` and `"<guild id>"` | Where the invite is advertised | C → A/B | Capture cited pages |
| Wayback availability for the landing page | Prior snapshots | B | Context |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Parse and classify input; record candidate object type; print the source list. Defer Snowflake object-time interpretation until a captured Discord object confirms the ID/type; never decode anonymized widget-member identifiers | — |
| S2 | Invite resolution JSON captured with headers; table of fields; expiry recorded if present; inviter fields recorded exactly as returned (username, global name, ID — the ID's Snowflake timestamp is derived) | B |
| S3 | Public widget JSON: preserve channels, anonymized display records and counts exactly. A captured Discord error code `50004` means widget disabled; other errors remain their actual documented code or `HTTP 403 — cause not established`, never a guessed setting | B |
| S4 | Landing page capture (B; A via G3 where available): what an anonymous visitor sees | B / A |
| S5 | Images: server icon and banner files captured and hashed | B |
| S6 | Where it is advertised: search-engine results for the invite code and guild ID; up to 10 pages captured (these pages often show the server's purpose as its promoters describe it — captured as third-party statements) | C → A/B |
| S7 | Volatility re-check: invite JSON fetched again at the end (counts, expiry, validity) | B |
| S8 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- No joining, no account, no token, no client. Public GETs do not join a guild, but are observable to service operators; do not promise invisibility or absence of logging. Anything requiring authentication remains outside this run.
- Counts are approximate by Discord's own labelling (`approximate_member_count`); record the field name with the value.
- Inviter data, when Discord includes it, is a Discord account record as returned at that time; it is recorded verbatim and the account is a Lead, not a person.
- Widget member IDs, discriminator and avatar fields may be anonymized. Preserve them as widget display records only, with no stable-account attribution, Snowflake decoding, cross-pack identity merge or membership-roster claim.
- A Snowflake-derived timestamp is a computation from a confirmed non-anonymized object ID, with source field and formula; it is not an independently measured creation time or activity timestamp. Unconfirmed numeric candidates remain unverified.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Invite returns 404 "Unknown Invite" | Record it with UTC: the invite is invalid, expired or revoked; capture the JSON error as EV; try the landing page; Lead: lawful request with the code |
| Invite returns 429 | Pause per `retry_after`; one retry |
| Widget HTTP 403 | Preserve HTTP headers/body. Report disabled only when captured Discord JSON has documented error code `50004`; otherwise report the returned code/message or cause unknown |
| Invite requires verification/phone (`features` or landing page says so) | Record the requirement; nothing further is possible without an account |
| Guild ID given but no invite known | S2 impossible; S3 (widget) and S6 (mentions) only; say so in Findings |
| Host assistant declines (e.g. server content) | `DECLINED-BY-HOST`; JSON facts reported only |

### 9.6 Findings structure

1. **Invite / server identity** — code, confirmed guild ID or unverified candidate, name, description, features, computed ID timestamp with millisecond precision/source field, vanity URL (EV refs).
2. **Counts and target channel** — approximate member/presence counts, channel name/ID/type, expiry.
3. **Inviter record** — as returned (or "not included").
4. **Public widget** — enabled/disabled; channels and members shown if enabled.
5. **Images** — icon/banner with hashes.
6. **Where advertised** — captured third-party pages with one-line context each.
7. **Stability** — S7 drift.
8. **Not accessible** — messages, members, roles, audit logs.

### 9.7 XLSX sheets

`Invite_Resolution` (field, value, UTC, EV) · `Snowflake_Timestamps` (ID, type, derived UTC, formula) · `Widget` (field/channel/member, value, EV) · `Images` (type, URL, file, SHA-256, EV) · `Advertised_On` (URL, title, context, EV).

### 9.8 Interpretation cautions

- A server name and description are set by its owner and can change at any time; the invite code can be revoked.
- Approximate counts are Discord's estimates at the moment of the request.
- For confirmed non-anonymized objects, the timestamp encoded in the ID is a derived provider-format value; it is not an independent clock measurement or activity time. Candidate and widget IDs establish no creation fact.
- Nothing here identifies the server owner, moderators or members; that needs a lawful request to Discord.
- Error-code interpretation uses Discord's [official JSON error-code documentation](https://github.com/discord/discord-api-docs/blob/main/developers/topics/opcodes-and-status-codes.mdx); preserve the actual captured error body and provider documentation version/date used.

### 9.9 Leads policy

Inviter account and any handles in the description (lawful request / L1-USR); linked websites (L1-WEB/L1-DOM); pages advertising the invite (L1-WEB); the lawful request to Discord for owner/admin and member data.

### 9.10 Self-test specification

The versioned `selftest/L1-DSC.selftest.json` is the machine-readable assertion contract. Missing required fixtures, adapters or expected results yield INCOMPLETE, never PASS. Offline regression results and optional live-provider smoke results are reported separately.

Required offline fixtures include a confirmed guild ID `613425648685547541` whose computed time is exactly `2019-08-20T17:34:31.544Z`, arbitrary numeric input, anonymized widget member ID `0`, Discord error code `50004`, and a generic/non-Discord HTTP 403. Assert that only the confirmed non-anonymized ID receives an object-time interpretation and only `50004` receives `widget disabled`. Optional live invite smoke tests report current captured values and availability separately; a changed guild name/count does not excuse failures in these offline rules.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Server owner/admins, message content, member data, audit logs | Discord Inc. (platform) | preservation, then disclosure (subscriber/registration data) | guild ID, invite code, channel ID, inviter user ID, UTC window | registration and login data for owner/admins, content of named channels, membership records |
| Inviter account | Discord | preservation | inviter user ID and username as returned, invite code, capture UTC | account data |

### 9.12 Duration estimate

Typical FULL-mode duration: 5–12 minutes; longest step S6 (mentions).
