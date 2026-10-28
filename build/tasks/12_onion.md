<!-- META
AGENT_NAME: Onion Service (Tor Hidden Service) Capture Agent
AGENT_CODE: L1-ONI
FILE: 12_L1-ONI_Onion-Service-Capture.md
PURPOSE: Preserve one page of a Tor onion service as evidence through the Investigator's own Tor Browser, with the agent validating the address, guiding and documenting every capture, and hashing the result — the agent itself never touches the Tor network.
INPUT_TYPE: .onion URL (v3 address: 56 base32 characters followed by .onion, optionally with a path)
-->
### 9.1 Scope and input validation

**In scope:** address validation; the one page given (and its directly linked resources on the same onion service, up to a small cap); its HTTP response headers as seen in Tor Browser; a clearnet-side check of where the address is mentioned (search engines, public onion directories); public archive status.
**Out of scope (→ Leads or prohibited):** logging in, registering, purchasing, messaging, posting, or interacting with any marketplace/forum function (R2); crawling beyond the given page and its direct links; de-anonymisation of the service or its users; Tor2web or any clearnet proxy to an onion address (third-party disclosure and no integrity — never used); running Tor inside the AI sandbox.

**Module requirements:** this module cannot reach its target from the sandbox by design, so the operating mode is **ASSISTED** at best: the Investigator performs the captures in Tor Browser, step by step, following the agent's instructions; the agent validates, documents, hashes, checks consistency and produces the pack. Print this at Phase 0. FULL mode is not available for this module. CAP-UPLOAD is required (the Investigator attaches the captures).

**Intake additions (printed with the form):** field **16** = "Tor Browser version installed (Help → About Tor Browser)"; field **17** = "Security Level set in Tor Browser (Standard / Safer / Safest) — Safer or Safest recommended for capture"; field **18** = "Does your agency permit visiting onion services from this workstation (dedicated/isolated machine recommended)? Y/N". Authorisation **D: none**.

Validation:
- v3 address: exactly 56 lower-case base32 characters (`a–z`, `2–7`) + `.onion`; the last byte decodes to version 3 (`0x03`) and the checksum `H(".onion checksum" || pubkey || version)[:2]` matches (compute in code if CAP-CODE; else record `format valid; checksum not verified`). v2 (16-character) addresses have been unreachable since 2021 → `NOT-INVESTIGABLE` with that explanation.
- Record the URL exactly; show the path separately; never "fix" it.
- **R8 applies with full force.** Onion services frequently host illegal content. If field 7 or the Investigator's description indicates such content, the Investigator is told not to capture beyond the page required by the case, and the agent never asks for a description of images.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| The onion page in the Investigator's Tor Browser | Primary | A1 | Screenshot, Save Page As (HTML complete), print-to-PDF; headers via Tor Browser's Network panel (F12) |
| Directly linked resources on the same service | Secondary | A1 | Up to 10, chosen by the Investigator per the agent's list |
| Clearnet search engines: `"<address>"` | Mentions on the open web | C → B | The address is sent to the search engine (authorisation A) |
| Public onion-link directories / indexes on the clearnet | Listing context | C → B | Third-party claims about the service, labelled as such |
| Ahmia-style onion search (clearnet front end) | Listing context | C → B | Shows only what that index has crawled; never relied on for content |
| Wayback availability for the clearnet mirror if one is named | Context | B | Only if a clearnet mirror URL is captured on the page itself |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Validate the address (format, version, checksum); print the Tor Browser capture procedure (9.4) and the safety reminders; confirm field 18 is Y (if N → `NOT-INVESTIGABLE` with the reason "agency policy") | — |
| S2 | Investigator capture of the target page: screenshot, HTML save, print-PDF, headers text; the Investigator attaches the files and pastes their hashes computed locally (§5.6); the agent records EV items A1 | A1 |
| S3 | Investigator capture of up to 10 directly linked resources on the same service, from the list the agent extracts from the saved HTML (same procedure) | A1 |
| S4 | Page metadata from the saved HTML: title, meta tags, visible dates, visible handles/PGP fingerprints/crypto addresses (transcribed exactly; each a Lead), external clearnet links, onion links | D |
| S5 | Clearnet context: search-engine results for the address captured (B); public directory listings captured; labelled third-party |  C → B |
| S6 | Consistency check: the agent compares the Investigator's hashes with the attached files' hashes (if the files were attached); mismatch → SH event | D |
| S7 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules — Tor Browser procedure given to the Investigator

1. Use a dedicated or isolated workstation if the agency has one. Tor Browser security level **Safer** (or **Safest** if the page works without scripts). Do not add extensions. Do not log in to anything.
2. Note the system clock (UTC) before loading. Load the exact URL. Wait for full render. Do not click anything except to scroll.
3. Screenshot: `Ctrl+Shift+S` → "Save full page" (Tor Browser is Firefox-based). Name `EV-<nnn>_onion_screenshot.png`.
4. Save page: `Ctrl+S` → "Web Page, complete". Name `EV-<nnn>_onion_page.html` (+ its `_files` folder, which is zipped as one file for hashing).
5. Print to PDF with URL and date in the header/footer. Name `EV-<nnn>_onion_print.pdf`.
6. Headers: `F12` → Network → reload → click the document request → right-click → "Copy Response Headers" → paste into `EV-<nnn>_onion_headers.txt`.
7. Hash every artefact — the page HTML, the zipped `_files` folder, the screenshot, the PDF and the headers text — with the §5.6 one-file command and paste the lines to the agent together with the UTC time of capture. Then attach the files if the host allows; otherwise the hashes alone go into the inventory with `files held by Investigator`.
8. Close the tab. Record Tor Browser version and security level in the chat (fields 16–17 already hold them).

Other rules: the agent never asks the Investigator to interact beyond scrolling; no form, button, search box or link is used except to open the listed direct links; a login wall or CAPTCHA on the onion service ends the capture of that item (`not accessible without authentication`); crypto addresses, PGP fingerprints and handles seen on the page are transcribed as Leads, not looked up here (R9).

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Service unreachable in Tor Browser ("Onionsite not found" / timeout) | Retry once after a new Tor circuit (Tor Browser menu → New Tor circuit for this site); if still unreachable, record `unreachable at <UTC>` with the error text as shown; try again later as a post-run step |
| Page requires JavaScript at Safest level | Investigator may switch to Safer for this item; the level change is recorded in the evidence record |
| Investigator's hash does not match the attached file | SH event; the Investigator re-hashes; if still different, the attached copy is quarantined and the locally held file with the Investigator's hash is the item of record |
| Page content changes between screenshot and HTML save | Keep both; note the volatility |
| Host assistant refuses to process onion content | `DECLINED-BY-HOST`; the Investigator's captures remain evidence; the pack is produced from the inventory without content description |

### 9.6 Findings structure

1. **Address** — as given, version, checksum result.
2. **Captured page** — title, what the page displays (neutral description from the saved HTML text; no description of images beyond their presence), headers of note (server, date), EV refs.
3. **Directly linked resources captured** — table.
4. **Transcribed identifiers on the page** — handles, PGP fingerprints, crypto addresses, clearnet links — as Leads.
5. **Clearnet context** — where the address is listed/mentioned (third-party).
6. **Not performed** — interaction, crawling, de-anonymisation.

### 9.7 XLSX sheets

`Address_Validation` (field, value) · `Captured_Pages` (URL, file, SHA-256 (Investigator), size, UTC, Tor Browser version, security level, EV) · `Headers` (name, value, EV) · `Identifiers_Transcribed` (type, value, where seen, EV) · `Clearnet_Context` (source, URL, what it states, EV).

### 9.8 Interpretation cautions

- An onion address identifies a service key, not a person or a server location; nothing in this report locates or identifies the operator.
- Onion services change, mirror and vanish quickly; a capture is valid for its moment only.
- Directory and index listings are claims by third parties.
- The capture reflects the Investigator's Tor Browser settings (security level) — some content may not have rendered.

### 9.9 Leads policy

Clearnet links and mirrors (L1-WEB/L1-DOM); crypto addresses (L1-CRY); handles (L1-USR); PGP fingerprints (keyserver lookup is a separate run); the service's own contact/escrow identifiers; lawful process is rarely available against an onion service itself — hosting-provider leads arise only from clearnet links.

### 9.10 Self-test specification

Target: `https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/` (DuckDuckGo's published onion service). Assertions: address format valid; version byte = 3; checksum valid (if computed); the Investigator-side capture is **optional** in self-test (`skip: S2, S3, S4, S6` unless the Investigator chooses to perform S2/S3, in which case S4/S6 run too); intake field 18 is set to `Y` for the self-test; S5 clearnet search returns ≥ 1 result page captured; validation of `http://expyuzz4wqqyqhjn.onion/` (a v2 address) returns `NOT-INVESTIGABLE`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Clearnet infrastructure referenced by the page (mirror domain, hosting) | registrar / hosting provider (from a follow-up L1-DOM/L1-IPA run) | preservation | domain/IP as captured | subscriber and access logs |
| Payment identifiers on the page | VASP/exchange (from a follow-up L1-CRY run) | preservation | address as captured | account holder data |

### 9.12 Duration estimate

Typical ASSISTED-mode duration: 20–40 minutes, most of it the Investigator's own capture work in Tor Browser (about 5 minutes per page). Agent-side steps take 5–10 minutes.
