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
- Numeric guild ID: 17–20 digits (a Snowflake). Decode the Snowflake's creation timestamp in code (`(id >> 22) + 1420070400000` ms since epoch → UTC) and record it as a derived fact ("ID created at", which is the server's creation time for guild IDs).
- A user ID or message link (`discord.com/channels/<guild>/<channel>/<message>`) is not an invite: record the guild ID from it as the target if present; message content is `not accessible without authentication`.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| `https://discord.com/api/v10/invites/<code>?with_counts=true&with_expiration=true` | Invite resolution: guild name/id/description/icon/banner/features, channel name/id/type, approximate_member_count, approximate_presence_count, expires_at, inviter (where included) | B | Public, no token |
| `https://discord.com/api/guilds/<guild id>/widget.json` | Public widget: name, instant_invite, channels, members shown online, presence_count | B | Only if the server owner enabled the widget; 403 otherwise (a fact) |
| `https://discord.gg/<code>` landing page (logged-out) | Rendered preview | B (A via G3) | Shows name and counts; nothing more without login |
| Icon/banner CDN URLs from the invite JSON (`cdn.discordapp.com/icons/<guild id>/<hash>.png`) | Images | B | Hash of the image file |
| Search engines: `"discord.gg/<code>"` and `"<guild id>"` | Where the invite is advertised | C → A/B | Capture cited pages |
| Wayback availability for the landing page | Prior snapshots | B | Context |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Parse; classify (invite / guild ID / message link); Snowflake timestamps for every ID present (computed facts, formula shown); print the source list | — |
| S2 | Invite resolution JSON captured with headers; table of fields; expiry recorded if present; inviter fields recorded exactly as returned (username, global name, ID — the ID's Snowflake timestamp is derived) | B |
| S3 | Public widget JSON (if enabled): channels list, members shown, counts; 403 recorded as "widget disabled by server" | B |
| S4 | Landing page capture (B; A via G3 where available): what an anonymous visitor sees | B / A |
| S5 | Images: server icon and banner files captured and hashed | B |
| S6 | Where it is advertised: search-engine results for the invite code and guild ID; up to 10 pages captured (these pages often show the server's purpose as its promoters describe it — captured as third-party statements) | C → A/B |
| S7 | Volatility re-check: invite JSON fetched again at the end (counts, expiry, validity) | B |
| S8 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- No joining, no account, no token, no client. An invite JSON request does not join or notify anyone; the landing page is a public page. Anything requiring more is `not accessible without authentication` and a lawful-request lead.
- Counts are approximate by Discord's own labelling (`approximate_member_count`); record the field name with the value.
- Inviter data, when Discord includes it, is a Discord account record as returned at that time; it is recorded verbatim and the account is a Lead, not a person.
- Widget member lists show display names of members online at that moment with the widget enabled; they are recorded as a captured list, never as a membership roster.
- Snowflake-derived timestamps are computed facts (formula shown) about when an ID was issued.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Invite returns 404 "Unknown Invite" | Record it with UTC: the invite is invalid, expired or revoked; capture the JSON error as EV; try the landing page; Lead: lawful request with the code |
| Invite returns 429 | Pause per `retry_after`; one retry |
| Widget 403 | Record "widget disabled" (a fact, not an error); continue |
| Invite requires verification/phone (`features` or landing page says so) | Record the requirement; nothing further is possible without an account |
| Guild ID given but no invite known | S2 impossible; S3 (widget) and S6 (mentions) only; say so in Findings |
| Host assistant declines (e.g. server content) | `DECLINED-BY-HOST`; JSON facts reported only |

### 9.6 Findings structure

1. **Invite / server identity** — code, guild ID, name, description, features, Snowflake creation time, vanity URL (EV refs).
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
- Snowflake timestamps show when Discord issued the ID, not when any activity happened.
- Nothing here identifies the server owner, moderators or members; that needs a lawful request to Discord.

### 9.9 Leads policy

Inviter account and any handles in the description (lawful request / L1-USR); linked websites (L1-WEB/L1-DOM); pages advertising the invite (L1-WEB); the lawful request to Discord for owner/admin and member data.

### 9.10 Self-test specification

Target: `https://discord.gg/discord-developers` (Discord's official developer server). Assertions: invite JSON HTTP 200; `guild.name` = `Discord Developers`; `guild.id` = `613425648685547541`; Snowflake-derived creation time of that ID = `2019-08-20T17:34:31Z`; `approximate_member_count` ≥ 100000 (drifts upward); S3 widget returns 200 or 403 (either is a valid result); S6 `skip`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Server owner/admins, message content, member data, audit logs | Discord Inc. (platform) | preservation, then disclosure (subscriber/registration data) | guild ID, invite code, channel ID, inviter user ID, UTC window | registration and login data for owner/admins, content of named channels, membership records |
| Inviter account | Discord | preservation | inviter user ID and username as returned, invite code, capture UTC | account data |

### 9.12 Duration estimate

Typical FULL-mode duration: 5–12 minutes; longest step S6 (mentions).
