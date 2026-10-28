<!-- META
AGENT_NAME: Web Page Evidence Capture Agent
AGENT_CODE: L1-WEB
FILE: 01_L1-WEB_Web-Page-Evidence-Capture.md
PURPOSE: Preserve one publicly accessible web page (post, article, listing, profile page, document) as court-oriented digital evidence, including its redirect chain, linked media, metadata and a volatility check.
INPUT_TYPE: URL (http:// or https://)
-->
### 9.1 Scope and input validation

**In scope:** one URL and what that page directly presents: the page itself, its redirect chain, HTTP headers, directly linked or embedded media and documents, page metadata, and public archive status.
**Out of scope (→ Leads):** the rest of the website, the domain's infrastructure (use L1-DOM), the author's other accounts (L1-USR / L1-SOC), anything behind a login.

Validation of the identifier:
- Scheme must be `http` or `https`. Reject `javascript:`, `data:`, `file:` and anything else.
- Reject URLs containing credentials (`user:pass@host`).
- Do **not** normalise, shorten, "clean" or strip tracking parameters. Record the URL exactly as given; a canonical URL, if the page declares one, is recorded separately in S5.
- If the host is an internationalised domain, show both the Unicode and the punycode (`xn--`) form and use the punycode form for fetching.
- If the URL is from a known link shortener or redirector, say so; the redirect chain in S2 is then a required capture, not optional.

**Intake additions (printed with the form):** authorisation **D** = "Request a *new* public archive snapshot of the target URL (Wayback/archive.today)? This creates a public, timestamped record that someone archived this URL, which can signal investigative interest. Y/N". No extra numbered fields.

### 9.2 Sources

| Source | Use | Capture level | Notes |
|---|---|---|---|
| The URL itself (live) | Primary evidence | A (preferred) + B (parallel) | Logged-out, clean profile |
| HTTP response headers at each hop | Redirect chain, server, dates, content-type | B | Save verbatim; `Date` header also serves CAP-TIME |
| Directly linked/embedded media and documents | Secondary items | B (A if the file only loads in a browser) | Same-origin or explicitly embedded only |
| Wayback Machine availability API `https://archive.org/wayback/available?url=<url>` | Existence of prior snapshots | B | Third-party; context only |
| archive.today (search by URL) | Existence of prior snapshots | A via G3; blocks automated fetch, so otherwise SKIPPED (optional) | Third-party; context only |
| DNS (DoH: `https://dns.google/resolve?name=<host>&type=A`) | Resolution at capture time | B | One query; full DNS profile is L1-DOM |

### 9.3 Execution plan (printed at §3.5)

| Step | Purpose | Level |
|---|---|---|
| S1 | URL anatomy (no network): scheme, host, punycode, path, query parameters as a table; shortener/redirector detection | — |
| S2 | Resolution and redirect chain: DNS A/AAAA of host; follow redirects hop by hop, saving status line and headers of every hop; final URL recorded | B |
| S3 | Primary capture of the final page: level A via G3 (A1 or A2 as available: full-page screenshot, saved page/print-PDF where the browser allows); plus level B raw fetch with headers as an independent parallel item. Without CAP-BROWSER: level B only, and the page is listed for post-run A1 re-capture (§5.8) | A + B |
| S4 | Linked resources: enumerate images, video, audio, documents (PDF/DOC/XLS…) referenced by the captured page; capture directly linked files up to the limit in 9.4; list the rest | B |
| S5 | Page metadata from the captured copy: `<title>`, meta description/keywords, canonical, author, `article:published_time`/`modified_time`, OpenGraph, Twitter card, JSON-LD, `lang`, visible author handle(s), visible dates (absolute and relative), comment/like counts if visible; analytics/tracking IDs → Leads | — (derived from EV) |
| S6 | Public archive status: Wayback availability JSON (B); archive.today search page (A via G3, else SKIPPED). Creation of a **new** public snapshot only with authorisation D (9.1); otherwise SKIPPED | B / A |
| S7 | Volatility check: second level-B fetch of the final URL at the end of the run (an assistant cannot idle between steps); compare visible-text hash; record STABLE / CHANGED with both items kept | B |
| S8 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Clean view.** Capture as an anonymous visitor. If the page content obviously depends on login, geography or A/B testing, state that the capture reflects the view from the capturing environment and record that environment (AI sandbox vs Investigator workstation, country if known).
- **Allowed clicks** in a level-A capture: dismissing or *rejecting* a cookie banner; expanding "read more"/"show replies" controls that reveal already-public content; scrolling. Each click is logged. **Age or consent interstitials are never answered** (R2): the item becomes `DEFERRED` for the Investigator's own decision post-run. **Nothing else.**
- **Relative dates.** "3 hours ago" is captured as shown and converted using the capture timestamp; record both the displayed string and the computed absolute UTC time, marked `computed`.
- **Infinite scroll / long pages.** Scroll to the end if the page has a natural end; otherwise capture to a stated extent (e.g. 200 items or 5 minutes of scrolling) and record the extent as a limitation.
- **Linked file limits.** Default: up to 10 files or 50 MB total (hosts cap downloadable output; the preflight CAP-FILES test should note the host's limit if known), each as its own EV item with content-type and hash. Beyond the limit, list the remaining URLs in the inventory as "not captured — limit" and in the post-run list (§5.8).
- **Embedded third-party players** (video hosted elsewhere): capture the page as rendered; the media file itself is captured only if a direct, public media URL is exposed; otherwise record the embed URL as a Lead for L1-SOC/L1-IMG.
- **Public archive creation (S6).** Only with intake authorisation D (9.1), which states the risk. If created, the snapshot is a separate level-B item labelled "third-party archive copy". archive.today itself blocks automated requests: without G3 that part is SKIPPED.
- **Documents** (PDF/Office files) found in S4 are captured as files; their own metadata extraction is a Lead for L1-IMG-style file analysis, not done here.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Page renders blank or JS-only in level B | Level A via G3 if available, else DEFERRED; keep the level-B raw HTML as a separate item ("unrendered source") |
| Redirect loop or > 10 hops | Stop following; capture the chain as is; record "redirect chain truncated at hop n" |
| Final page differs between level A and level B captures | Keep both; state in Findings which view is cited and why (usually level A); add volatility note |
| Page is geo-blocked for the AI sandbox | DEFERRED (post-run A1 from the Investigator's workstation); never a proxy/VPN from the sandbox |
| Linked media URL expires (signed URLs) | Capture immediately from within the level-A browser session; if expired, record URL + expiry evidence |
| Cookie/consent wall cannot be dismissed without accepting | Reject if possible; if only "accept" works, do not click it — DEFERRED with the note "consent wall; Investigator decides in a disposable profile and records the click" |

### 9.6 Findings structure (report §7.1 item 4)

1. **Identity of the page** — URL as given, final URL, host, resolution at capture, title (EV refs).
2. **Content summary** — what the page shows, in neutral descriptive language, citing the level-A screenshot EV and the saved page EV. Quote visible text only as short exact excerpts with EV reference; long text is in the captured files, not retyped.
3. **Authorship and timing indicators** — author name/handle as displayed, displayed publication/modification dates, metadata dates; each marked `displayed`, `metadata` or `computed`.
4. **Linked resources** — table of captured files with hashes; uncaptured list.
5. **Stability** — S7 result; both EV refs if CHANGED.
6. **Archive context** — earliest/latest known third-party snapshots (context, not evidence of content).
7. **Contradictions** — any mismatch between displayed and metadata values.

### 9.7 XLSX sheets (after the standard sheets)

`Redirect_Chain` (hop, URL, status, Location, Date header, Server, EV) · `Page_Metadata` (key, value, source element, EV) · `Linked_Resources` (URL, type, captured Y/N, EV, SHA-256, size) · `Archive_Snapshots` (service, timestamp, snapshot URL, EV) · `Visible_Dates` (displayed string, computed UTC, basis).

### 9.8 Interpretation cautions (for the Limitations section)

- A captured page proves what the capturing environment was served at that time — not what any other visitor saw, and not that the content was created by the named author.
- Server `Date` headers and metadata dates can be wrong or edited; they corroborate, they do not prove.
- Level-B captures were made in an AI sandbox that is not a controlled forensic environment; the level-A capture is the item of record where both exist.
- Third-party archive snapshots are statements by the archive, not captures by the Investigator.

### 9.9 Leads policy

Record as `L-nnn` (never act on): other pages on the same site, the domain profile (L1-DOM), author accounts (L1-USR, L1-SOC), analytics/advertising IDs seen in the source, embedded media hosted elsewhere (L1-IMG, L1-SOC), documents' internal metadata.

### 9.10 Self-test specification

Target: `https://example.com/` (IANA's reserved example domain; stable since 1999). Assertions: S2 final HTTP status `200`; redirect chain length `0`; S3 level-B capture has `<title>` = `Example Domain`; DNS A/AAAA answers for `example.com` have ≥ 1 record each (values drift); S4 linked resources count = `0` (the page has none); S6 Wayback availability returns `archived_snapshots.closest` (timestamp drifts; pattern `^\d{14}$`); S7 volatility result `STABLE`; `skip: S6 snapshot creation`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Who published the page / account that posted it | the platform or hosting provider operating the site (from the captured host and headers; registrar/host via an L1-DOM follow-up) | preservation | URL as given, final URL, capture UTC, server `Date` header, page title | account/upload data, server logs for the URL in the window |
| Removed or changed content | preservation, then disclosure (subscriber/registration data) | preservation | URL, both capture UTCs if CHANGED | content as it stood at the times cited |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longer when there are many linked files (S4). Longest steps S3 and S4.
