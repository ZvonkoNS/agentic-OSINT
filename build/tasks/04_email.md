<!-- META
AGENT_NAME: Email Address Investigation Agent
AGENT_CODE: L1-EML
FILE: 04_L1-EML_Email-Address-Investigation.md
PURPOSE: Document what public sources show about one email address — its domain's mail setup, breach exposure listings, public avatar association and open-web mentions — without contacting the mailbox or probing account-recovery systems.
INPUT_TYPE: email address
-->
### 9.1 Scope and input validation

**In scope:** syntax and structure of the address; the domain's mail and registration summary; disposable/role-address classification; Gravatar association; breach-exposure listings on a public breach index; exact-match mentions on the open web and in public code/paste repositories.
**Out of scope (→ Leads):** sending anything to the address; "forgot password" or registration probes on any platform (these can notify the mailbox owner and are prohibited by R2); full domain profile (L1-DOM); accounts found by handle (L1-USR).

Validation:
- The default adapter supports a bare ASCII dot-atom or supported ASCII quoted local part and an IDNA domain; reject malformed dot-atoms and control characters. Preserve input bytes/text. Display-name forms require the bare address. Address literals and SMTPUTF8 local parts are `UNSUPPORTED_BY_ADAPTER`, not proof that the mailbox is invalid; use a tested standards-aware adapter before investigating unsupported forms. Do not validate an email by counting `@` characters alone.
- Record exactly as given; lower-case the domain for lookups; keep the local part's case as given (and note that most providers treat it case-insensitively).
- Plus-addressing (`user+tag@`) and dots in Gmail local parts: note the base form as a Lead, do not probe it.

**Intake additions (printed with the form):** none beyond authorisation C (an HIBP API key makes S5 automated). Authorisation **D: none**.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| DNS over HTTPS (MX, A/AAAA, TXT/SPF, `_dmarc`) | Advertised routing/policy, not a mailbox-existence test | B | Two resolvers; retain DNS response status and distinguish null MX, no MX, NXDOMAIN and temporary failure |
| RDAP `https://rdap.org/domain/<domain>` | Registration summary (dates, registrar) | B | Full profile is L1-DOM |
| Public disposable-domain lists (e.g. the open-source `disposable-email-domains` list on GitHub, raw file) | Disposable classification | B | Third-party list; record list version/commit |
| Gravatar `https://www.gravatar.com/avatar/<sha256>?d=404` (image) and `https://api.gravatar.com/v3/profiles/<sha256>` (public profile) | Source-reported avatar/profile for Gravatar's normalized email identifier | B | SHA-256 of the trimmed, lower-cased address is this provider's documented lookup key; the original mailbox identifier is not changed. A tested legacy MD5 avatar fallback is separate and disabled by default. Distinguish explicit 404 from blocked/auth/error responses |
| Have I Been Pwned API `https://haveibeenpwned.com/api/v3/breachedaccount/<address>?truncateResponse=false` with the agency's key (intake authorisation C) | Breach-exposure listing | B | **The website is never automated**. Without secure authorized API access, DEFERRED: an investigator-directed post-run lookup produces a new captured artifact with its digest/time in a numbered sealed addendum referencing the earlier seal; a VERIFICATION.md working note alone does not verify it |
| Search engines: `"<address>"` | Open-web mentions | C → A | Capture cited pages |
| Search-engine queries scoped to code and paste hosts (e.g. `"<address>" github`, `"<address>" pastebin`) | Public code/paste mentions | C → A/B | GitHub's own code/commit search requires sign-in and is not used (R2) |
| Paste/leak indexes via search engine | Mentions | C → A/B | Capture only; never transcribe credentials (R11); no login, no purchase |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Parse: local part, domain, plus-tag, role-address pattern (`info@`, `admin@`, `noreply@` …), free-mail provider recognition | — |
| S2 | Domain mail layer: save MX DNS status/answers, SPF, DMARC, MTA-STS and RDAP summary. A single `0 .` MX is NULL_MX_NO_SERVICE; NO_MX with successful DNS may use implicit A/AAAA routing, which is recorded without connecting to SMTP. NXDOMAIN, SERVFAIL/timeout and contradictory/mixed null-MX answers remain distinct | B |
| S3 | Disposable / temporary-mail classification against a public list (record list source and date) | B |
| S4 | Gravatar: avatar existence (status), avatar image captured if present, public profile JSON if present | B |
| S5 | Breach exposure: HIBP API with the agency key (authorisation C), raw JSON saved; list breach names, dates and data classes as returned. No key → DEFERRED (post-run website lookup by the Investigator) | B |
| S6 | Open-web exact-match sweep: search results page captured; up to 10 relevant pages captured | C → A/B |
| S7 | Code and paste mentions via search-engine queries scoped to those hosts; results pages captured; relevant public pages captured (R11 applies) | C → A/B |
| S8 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Never send mail**, never request verification codes, never use "find friends"/"import contacts" features, never run account-existence tools that hit registration or password-reset endpoints. If the Investigator asks for this, refuse under R2 and record the request.
- HIBP API responses are saved as raw JSON; breach names, dates and data classes are copied with their exact field path and EV ref. HIBP does not return the leaked data itself; do not go looking for it. The agency key is read through a named secret/environment reference supported by the host, never pasted into chat, code examples, logs, resume files or delivered artifacts. If secure input is unavailable, defer the keyed request.
- Gravatar v3 profiles use SHA-256 of the trimmed, lower-cased address. Record the provider-specific normalization, algorithm and lookup key; keep the original local-part case in the case record. A profile/ avatar result is a provider association, not proof of mailbox control or a person. Capture the API version, HTTP status and returned identifier. Do not treat a Gravatar error page as absence.
- Search queries are recorded verbatim; search result pages are captured before any result is opened.
- Disclosure: A is required for every target-bearing third-party request, including domain-bearing DNS/RDAP requests in S2 and Gravatar/HIBP/search in S4–S7. A=N means those network operations are SKIPPED; local parsing and matching against already-available, versioned lists may continue. An identifier hash is not a guarantee of anonymity. No key or provider approval overrides a denied disclosure permission.
- Paste/leak pages: capture the page as a file; the evidence record says "contains credential material — restricted" where applicable; nothing from such a page is quoted, re-typed or searched further (R11).

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| HIBP API returns 401/429 | Check the key/rate limit once; otherwise DEFERRED (Investigator's manual website lookup post-run); never automate the website |
| Successful DNS response has no MX | Record NO_MX and any captured A/AAAA fallback candidates; do not claim that no mail service or mailbox exists. A single `0 .` is NULL_MX_NO_SERVICE; NXDOMAIN, temporary failure and invalid mixed null-MX data are separate results |
| Disposable list fetch fails | Use a second public list; else SKIPPED (optional context) |
| Gravatar returns 200 for `d=404` variant anomalies | Save response headers; classify by content-type/size; re-check once |
| Search engine returns personalised/localised results | Record the engine, locale, and that results vary; capture as seen |
| Mentions page requires login | Record URL + `not accessible without authentication`; Lead |

### 9.6 Findings structure

1. **Address structure** — parse results; role/free-mail/disposable classification with basis (EV refs).
2. **Domain mail configuration** — exact DNS status and MX classification, implicit routing candidates where applicable, SPF/DMARC strings and registration summary. MX host names do not by themselves establish the responsible mailbox provider.
3. **Public avatar association** — Gravatar result (present/absent), image EV if present.
4. **Breach-exposure listings** — table from S5 as returned by HIBP, with the explicit note that these are HIBP's records of third-party breaches; or "DEFERRED — see post-run steps" when no agency key was available.
5. **Open-web mentions** — table of captured pages with context (one line each).
6. **Code/paste mentions** — same.
7. **Not performed** — list the prohibited checks (account-recovery probes, messaging-app lookups) and why.

### 9.7 XLSX sheets

`Email_Parse` (raw address, raw local part, ASCII domain, supported syntax, comparison key, adapter/version) · `Domain_Mail_Records` (record, DNS status, value, routing classification, resolver, UTC, EV) · `Gravatar` (algorithm, lookup key, endpoint/version, status, returned identifier, EV) · `Breach_Exposure` (breach name, breach date, added date, data classes, EV) · `Web_Mentions` (URL, title, context, captured EV, SHA-256) · `Code_Mentions` (repo/URL, file, line context, EV).

### 9.8 Interpretation cautions

- Presence in a breach listing shows that an address appeared in a dataset published by third parties; it does not show who used the address, that it was active, or that any password shown elsewhere is current.
- A Gravatar avatar is associated with the hash of the address, which anyone who knows the address could set up; it indicates a Gravatar account was configured for that address, nothing more.
- Open-web mentions can be scraped, spoofed or planted; each is a statement by that page at capture time.
- Absence of mentions is not evidence the address is unused.

### 9.9 Leads policy

The domain (L1-DOM); handles equal to the local part (L1-USR); base form of plus/dot variants; names or phone numbers found in mentions (separate runs); platforms where a lawful request could confirm account existence.

### 9.10 Self-test specification

The versioned `selftest/L1-EML.selftest.json` is the machine-readable assertion contract. Missing required observations, fixtures or adapters yield INCOMPLETE, never PASS. Required offline fixtures distinguish NULL_MX_NO_SERVICE (`0 .`), NO_MX with A/AAAA, NXDOMAIN, temporary failure and mixed invalid null-MX data; preserve `Alice@example.com` and `alice@example.com` as distinct by default; reject malformed dot-atoms, test supported quoted ASCII local parts, and mark SMTPUTF8 input unsupported rather than nonexistent. Gravatar request fixtures use a 64-hex SHA-256 key for v3 and distinguish 404, 401, 429 and HTML bot walls. Optional live smoke target: `selftest@example.com`; S5 is DEFERRED without secure authorized credentials. `skip: S6, S7`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Mailbox holder identity and logs | the responsible mailbox provider verified by the agency; MX operators may be filtering/relay services and registrants are not automatically mailbox custodians | preservation, then disclosure (subscriber/registration data) | address as given, domain, MX hosts, capture UTC | account registration data, login IP logs, recovery contacts |
| Accounts registered with this address on platforms named in the case | each platform | preservation | address, platform, UTC | account existence and registration data |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longest step S6.
