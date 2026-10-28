<!-- META
AGENT_NAME: Company / Business Entity Check Agent
AGENT_CODE: L1-ORG
FILE: 09_L1-ORG_Company-Business-Entity-Check.md
PURPOSE: Document one legal entity from its official register and public identifier systems — status, officers and ownership where public, identifiers, sanctions-list screening and adverse media — as hashed evidence.
INPUT_TYPE: legal entity name together with its registration country (or a registration number / LEI with the country)
-->
### 9.1 Scope and input validation

**In scope:** the official company register record for the stated jurisdiction; LEI record; officers, shareholders and beneficial owners where the register publishes them; registration/VAT identifiers; name screening against public sanctions lists; adverse-media sweep; the entity's own web presence (home page capture only).
**Out of scope (→ Leads):** group structures beyond the direct record, related entities, individuals (separate runs), credit/financial reports, non-public registers, the entity's domain profile (L1-DOM).

Validation:
- Require the registration country (ISO code or name). Without it, ask; do not infer from the name.
- Record the name exactly as given, plus a normalised form (legal-form suffix separated: `d.o.o.`, `Ltd`, `GmbH`, `LLC`, `S.A.`…) and, for non-Latin scripts, the transliteration used.
- If a registration number or LEI is given, it is the primary key; the name is confirmed against the record.

**Intake additions (printed with the form):** field **16** = "Registration country (ISO code or name) — mandatory"; field **17** = "Registration number, LEI or VAT number if known (this avoids same-name ambiguity)"; field **18** = "Local-language adverse-media terms, if you want them added to the standard set in 9.4". Authorisation **D: none**.

### 9.2 Sources

| Source | Use | Level | Notes |
|---|---|---|---|
| Official register of the stated jurisdiction (examples: UK Companies House, US SEC EDGAR + state Secretary of State registers, EU national registers reachable via the e-Justice BRIS portal, Slovenia AJPES/ePRS, Germany Handelsregister, France Infogreffe/INPI, Netherlands KVK, etc.) | Primary record | A (B where a public JSON/API exists without key) | Identify the register by searching `<country> official company register`; verify it is governmental (government domain / regulator) before using it |
| GLEIF LEI search `https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]=<name>` | LEI record, legal address, direct/ultimate parent where reported | B | Keyless |
| EU VIES REST API `https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number` (POST JSON `{"countryCode":"SI","vatNumber":"12345678"}`) or the web form via G3 | VAT number validity (EU) | B / A | A public validation, not an interaction with the entity; outside the EU use the national equivalent where public |
| OpenCorporates (web, logged-out) | Cross-check / other jurisdictions | A via G3, else B if fetchable | Aggregator — secondary to the official register |
| Sanctions: OFAC SDN list `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV` (and `https://www.treasury.gov/ofac/downloads/sdn.xml`) plus the OFAC search website; UN Security Council Consolidated List `https://scsanctions.un.org/resources/xml/en/consolidated.xml`; UK Sanctions List via the gov.uk publication page "The UK Sanctions List" (download link changes per release — capture the page, follow the current XML/CSV); EU Sanctions Map (public web). The EU consolidated file requires an EU Login account and is **not used** (R2) | Name screening | B / A | List files are level-B items; website searches via G3 |
| Search engines: `"<name>"` with neutral and adverse terms (9.4) | Adverse media | C → A | Capture cited articles |
| Entity home page | Web presence | A/B | Headers saved |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Normalise input; identify and verify the official register for the jurisdiction; print the source list | — |
| S2 | Official register record: search → entity page(s) → capture; extract legal name, legal form, registration number, status, incorporation date, registered address, activity codes, share capital, filing history index as shown | A / B |
| S3 | Officers and ownership: directors/officers with appointment dates; shareholders/members; beneficial owners **only where the register publishes them**; capture each page | A / B |
| S4 | LEI: GLEIF record (if any), incl. reported parents | B |
| S5 | Identifiers: VAT/tax number validation (VIES REST API for EU; national equivalents where public); registration number cross-check | B / A |
| S6 | Sanctions screening: exact and normalised name search in the downloaded OFAC, UN and UK list files (B), the EU Sanctions Map via G3 (A) where available; also screen the registration number and LEI where lists carry them; capture every file and result page with version/date; classify `NO MATCH` / `POTENTIAL MATCH (requires human review)` — never "match" without the Investigator's review | B / A |
| S7 | Adverse media: search results captured for neutral query and for adverse-term queries; capture up to 10 relevant articles; record publication and date as displayed | C → A |
| S8 | Web presence: home page capture; stated address/contacts compared with the register | A/B |
| S9 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Official register first.** Aggregators are captured only as cross-checks and labelled as such. If the official register is pay-walled for documents, capture the free index/summary and record the document list as Leads with the fee notice.
- Register pages are volatile (status changes, filings added); every extract is "as at <UTC>".
- **Sanctions screening is a screening, not a determination.** Fuzzy matches on common names will appear; the Investigator must review each `POTENTIAL MATCH` against identifiers (country, date of incorporation, address). Record the list version/date shown by each service.
- Adverse-term query set (print it before use): `fraud`, `sanction`, `investigation`, `indictment`, `lawsuit`, `bankruptcy`/`insolvency`, `money laundering`, plus two terms relevant to the case from intake field 7 if given. Localise terms to the jurisdiction's language when the Investigator provides them.
- Adverse media are reports by publishers; capture them, transcribe the headline and date, and label them "media report". No reputational summary of the entity.
- Never contact the entity, submit enquiry forms, request documents by email, or create accounts on register sites that offer them (R2). Free, logged-out access only; if a register requires a login even for search, record it and route through the Investigator under agency procedure (that is a Lead, not a level-A instruction).

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Official register not identifiable / not in English | Search with the local-language term provided by the Investigator; verify government domain; else FAILED-DOCUMENTED with the aggregator capture as a labelled substitute |
| Multiple entities with the same name and no field-17 identifier | Capture the candidate list; raise a G4 event with the candidates as ALT options (up to 5; more → the G4 asks for a registration number); record the selection basis |
| Register blocks automated access | G3 if available; else DEFERRED (Investigator captures the register pages post-run, §5.7) |
| VIES unavailable (frequent) | Retry later once; else FAILED-DOCUMENTED |
| Sanctions website rate-limited or blocked | The downloaded list files are the record; the website cross-check is SKIPPED |
| LEI not found | Record "no LEI record found at <UTC>" (normal for small entities) |

### 9.6 Findings structure

1. **Registered identity** — legal name, form, number, status, incorporation date, registered address, activity codes (EV refs, register named).
2. **Officers and ownership** — tables as published; note which categories the register does not publish.
3. **Identifiers** — LEI, VAT/tax numbers with validation result and date.
4. **Sanctions screening** — per list: version/date, result, EV; every POTENTIAL MATCH listed with the differentiating identifiers for review.
5. **Adverse media** — table of captured reports (publisher, headline, date displayed, EV); no synthesis of guilt or reputation.
6. **Web presence** — home page description; consistency of stated address/contacts with the register.
7. **Discrepancies** — e.g. name variants, address mismatches, status conflicts between sources.

### 9.7 XLSX sheets

`Registry_Record` (field, value, register, UTC, EV) · `Officers` (role, name as published, appointed, resigned, EV) · `Ownership` (holder as published, interest, basis, EV) · `Identifiers` (type, value, validation result, source, EV) · `Sanctions_Screening` (list, version/date, query, result, candidate shown, differentiators, EV) · `Adverse_Media` (publisher, headline, date displayed, URL, EV) · `Candidates` (if the same-name G4 event occurred: name, number, address, selected Y/N).

### 9.8 Interpretation cautions

- Register data reflects filings by the entity; it can be late, incomplete or false, and the register does not verify it.
- Officer and shareholder names are as published; identity of individuals is not established here (Lead: separate runs under their own legal basis).
- Beneficial-ownership access varies by jurisdiction and changed after 2022 in the EU; "not published" is a feature of the register, not of the entity.
- Sanctions screening hits on names are frequent false positives; a `POTENTIAL MATCH` is a review task, not a finding.
- Media reports are allegations or reports by their publishers at the stated date.

### 9.9 Leads policy

Officers and owners (separate runs); parent/subsidiary entities; the entity's domain (L1-DOM); documents behind register pay-walls; registers requiring authenticated access via agency procedure.

### 9.10 Self-test specification

Target: `Apple Inc.`, country `US` (field 16), LEI `HWUPKR0MPOU8FGXBT394` (field 17). Assertions: GLEIF record HTTP 200 with `attributes.lei` = `HWUPKR0MPOU8FGXBT394`, `entity.legalName.name` = `Apple Inc.`, `entity.jurisdiction` = `US-CA`, `registration.status` = `ISSUED`; official register identified as SEC EDGAR for a US listed company with CIK `0000320193` (EDGAR company page HTTP 200 after redirect via `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193` — EDGAR requires a descriptive `User-Agent` header with contact email; the self-test uses `agentic-OSINT selftest (selftest@example.com)`); OFAC, UN and UK list files downloaded and the exact string `APPLE INC` screened → `NO MATCH` or `POTENTIAL MATCH (requires human review)` both acceptable (false positives on common words are expected and are the point of the review rule); `skip: S5 (VIES; not an EU entity), S7, S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Documents behind a register paywall or requiring authenticated access | the official register (name as captured) | agency procedure (not a lawful request to a private party) | registration number, legal name, document list captured | the listed filings |
| Officers/owners named in the record (persons) | — | not a lawful-request lead; a separate run under its own legal basis | — | — |
| Bank/payment relationships named in filings | the named institution | preservation | entity name, registration number, filing reference | account data (where the legal basis allows) |

### 9.12 Duration estimate

Typical FULL-mode duration: 15–30 minutes; longest steps S2/S3 (register pages) and S6 (list downloads).
