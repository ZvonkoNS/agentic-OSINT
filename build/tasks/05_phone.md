<!-- META
AGENT_NAME: Phone Number Investigation Agent
AGENT_CODE: L1-PHN
FILE: 05_L1-PHN_Phone-Number-Investigation.md
PURPOSE: Document the numbering-plan facts and public open-web footprint of one telephone number without calling, messaging, or looking the number up in any contact-based app.
INPUT_TYPE: telephone number (E.164 preferred, e.g. +38640123456; otherwise the number plus its country)
-->
### 9.1 Scope and input validation

**In scope:** parsing and normalisation; number type, region and originally assigned carrier from the public numbering plan; the regulator's numbering-plan page; exact-match mentions on the open web in all common formats; public crowd-sourced caller-reputation listings; public business-directory listings.
**Out of scope (→ Leads or prohibited):** calling or messaging the number; adding it to a contact list to see WhatsApp/Telegram/Signal/Viber presence or profile photos (prohibited — R2: it can alert the subject and uses an account); carrier-lookup services that require accounts or payment; social-media searches that require login.

Validation:
- Preserve the raw string and use a pinned `phonenumbers` adapter for parsing and formatting; do not impose an invented global minimum digit count. National numbers require an explicit ISO region; a leading `+` uses the supplied calling code without guessing a country from the investigator's location.
- Record separate parse status, `is_possible_number_with_reason`, `is_valid_number`, type and region as library-derived metadata, with library version. `valid per metadata` does not establish current allocation, reachability, operator or subscriber. A shared calling code may not identify one country.
- Reject control characters and ambiguous multiple numbers. Extensions are retained separately and are never included in an E.164 search key. Short codes/emergency/service codes and alphanumeric vanity input are `UNSUPPORTED_BY_ADAPTER` unless a dedicated adapter and scope cover them; never invent a normalized subscriber number.
- An unparseable or impossible number stops target-bearing requests and becomes NOT_INVESTIGABLE. A possible-but-not-valid number is an explicitly limited validation result: ask for confirmation/correction at intake before any open-web query, preserve the metadata caveat and never change the country silently. Without the library, return VALIDATION_NOT_PERFORMED and defer number-specific network work.

**Intake additions (printed with the form):** field **16** = "Country of the number (ISO code or name) if you did not give it in E.164 form". Authorisation **D: none**.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| `phonenumbers` Python library (port of Google libphonenumber) | Validity, type (mobile/fixed/VoIP/toll-free…), region, example formats, carrier of the original range, time zones | D (tool output) | Record library version; carrier = range holder at allocation, not current operator |
| National regulator numbering plan page (e.g. the telecoms regulator of the number's country) | Range allocation confirmation | A/B | Identify the official regulator; capture the relevant page |
| Search engines: each format variant in quotes | Open-web mentions | C → A/B | Variants generated in S3 |
| Public crowd-sourced caller-reputation sites that need no account — candidates (verify availability): tellows, shouldianswer.com, whocallsme.com | Reports by the public | B where fetchable; A via G3; else DEFERRED | Hearsay-grade; capture as shown. **Excluded**: Truecaller, GetContact, Sync.me, Eyecon and any app that requires an account or uploads contact lists (R2) |
| Public business directories / official registers that list phone numbers | Business association | A/B | Capture |
| Social platforms' public search (only where available logged-out) | Mentions | C → A | Usually not available |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Parse using the pinned library; retain raw string/extension and explicit region; output parse/possible/valid states separately, E.164/national/international forms only when established, metadata-derived type/region/range-carrier/time-zone candidates and version. Apply the intake decision for uncertain validation before network work | D |
| S2 | Numbering-plan corroboration: identify the official regulator for the country; capture the page or document that shows the range allocation; if the regulator publishes a range database, capture the matching row | A/B |
| S3 | Generate search variants: E.164, international with spaces, national with/without leading zero, grouped forms common in the country, digits only; print the list | — |
| S4 | Open-web sweep: one exact-match query per variant; capture each results page; capture up to 10 relevant result pages | C → A/B |
| S5 | Crowd-sourced reputation: lookup on the named account-free sites (9.2); capture results pages; transcribe report counts/categories as shown; blocked sites → DEFERRED | B / A |
| S6 | Business/registry listings: public directories and official registers that showed the number in S4; capture | A/B |
| S7 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **No contact of any kind** (call, SMS, WhatsApp, Telegram, Signal, Viber, iMessage, FaceTime). No "add contact". No lookups in apps bound to a phone identity. If the Investigator asks, refuse under R2 and record it; note that such checks, if lawful in the jurisdiction, must be done by the Investigator under agency procedure with a dedicated device — not by this agent.
- Record the `phonenumbers` metadata version with the parse output; carrier and time-zone mappings are static range metadata dated by that version, not current operator or a person's current location. Record empty/ambiguous values as returned.
- Number portability is **not** public in most countries: the carrier in S1/S2 is the original range holder. State this wherever a carrier is mentioned.
- Crowd-sourced reputation sites contain unverified public submissions; capture them, transcribe counts, and label them hearsay in Findings.
- Search variant queries are recorded verbatim with the engine used.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| `phonenumbers` not installed | Use the approved pinned dependency installation if permitted; otherwise VALIDATION_NOT_PERFORMED and defer number-specific network work. A digit-count guess is not a replacement validation method |
| Regulator site unknown / not in English | Search `<country> telecommunications regulator numbering plan`; verify governmental domain; if still unclear, record FAILED-DOCUMENTED |
| Reputation site shows CAPTCHA | G3 if available; else DEFERRED; never automate past it |
| Search engines return nothing for any variant | Record "no exact-match results at <UTC>" — a fact about the index, not about the number |
| Number is possible but not valid per metadata | Preserve both results and the library reason; only continue under the limited result explicitly accepted at intake. Unparseable/impossible numbers stop target-bearing requests. A new country or corrected number requires a separate intake decision, never silent normalization |

### 9.6 Findings structure

1. **Number structure and metadata** — raw input/extension, parse/possible/valid states and reasons, established formats, library-derived type/region/original-range carrier/time-zone candidates (EV: tool output + regulator capture), with explicit allocation/reachability unknowns.
2. **Open-web mentions** — table with context, which variant matched, EV refs.
3. **Crowd-sourced reports** — per site: report count, categories, latest report date as shown; labelled "public submissions, unverified".
4. **Business/registry associations** — captured listings.
5. **Not performed** — contact-based checks, with the reason.

### 9.7 XLSX sheets

`Number_Parse` (raw input, region input, extension, parse status, possible reason, valid per metadata, established format, metadata version, value, basis) · `Search_Variants` (variant, selection basis, engine, query, results page EV) · `Web_Mentions` (URL, title, variant matched, context, EV, SHA-256) · `Reputation_Reports` (site, count, categories, latest date shown, EV) · `Listings` (source, name shown, address shown, EV).

### 9.8 Interpretation cautions

- A phone number identifies a subscription at a point in time, not a person. Numbers are recycled, shared, spoofed and ported.
- Caller-reputation sites are anonymous crowd submissions; they can be malicious or mistaken.
- A mention of the number on a web page shows the page displayed it at capture time; it does not show who controls the number.
- Current operator, subscriber identity and location require a lawful request to the operator; this report provides the regulator-level facts needed to address that request (Lead).

### 9.9 Leads policy

Names, businesses, addresses and emails seen in mentions (separate runs); the original carrier and regulator contact for lawful requests; messaging-app checks to be considered under agency procedure, not by this agent.

### 9.10 Self-test specification

The versioned `selftest/L1-PHN.selftest.json` is the machine-readable assertion contract. Missing required observations, fixtures or adapters yield INCOMPLETE, never PASS. Required offline parsing fixtures cover national numbers with/without region, short valid numbering-plan examples, shared calling codes, extensions, possible-but-invalid and impossible inputs, unsupported short codes and missing-library behavior. Assert no target-bearing request for unparseable/impossible/unsupported input. Optional smoke target: `+442079460000`, the published Ofcom drama-range example, with metadata values attributed to the installed library version. No test calls or messages it. `skip: S4, S5, S6`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Subscriber identity and current operator (number portability) | the original range holder from S1/S2 (who can state the current operator), then the current operator | disclosure (subscriber/registration data) | E.164 number, original carrier, regulator range reference, UTC window from the case | subscriber data, porting history, CDRs where the legal basis allows |
| Messaging-app account on the number | the app operator | preservation | E.164 number, UTC | account existence and registration data |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longest step S4 (one search per variant).
