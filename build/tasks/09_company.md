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
| Official entity register of the stated jurisdiction (e.g. UK Companies House, US state Secretary of State registry, Slovenia AJPES/ePRS, Germany Handelsregister or the jurisdiction's delegated registry) | Field-specific primary record | A (B where a public API exists) | Verify authority from the jurisdiction's official portal or statutory/delegation description; a government-looking domain alone is insufficient. SEC EDGAR is a securities-filing source, not a substitute for state entity registration |
| GLEIF LEI search `https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]=<name>` | LEI record, legal address, direct/ultimate parent where reported | B | Keyless |
| EU VIES REST API `https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number` (POST JSON `{"countryCode":"SI","vatNumber":"12345678"}`) or the web form via G3 | VAT number validity (EU) | B / A | A public validation, not an interaction with the entity; outside the EU use the national equivalent where public |
| OpenCorporates (web, logged-out) | Cross-check / other jurisdictions | A via G3, else B if fetchable | Aggregator — secondary to the official register |
| Sanctions: OFAC SDN list `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV` (and `https://www.treasury.gov/ofac/downloads/sdn.xml`) plus the OFAC search website; UN Security Council Consolidated List `https://scsanctions.un.org/resources/xml/en/consolidated.xml`; UK Sanctions List via the gov.uk publication page "The UK Sanctions List" (download link changes per release — capture the page, follow the current XML/CSV); EU Sanctions Map (public web). The EU consolidated file requires an EU Login account and is **not used** (R2) | Name screening | B / A | List files are level-B items; website searches via G3 |
| Search engines: `"<name>"` with neutral and adverse terms (9.4) | Adverse media | C → A | Capture cited articles |
| Entity home page | Web presence | A/B | Headers saved |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Preserve raw input; identify jurisdiction and registration ID; verify the appropriate entity register and any separate securities-filing/LEI sources; print a field-to-source authority map | — |
| S2 | Official register record: search → entity page(s) → capture; extract legal name, legal form, registration number, status, incorporation date, registered address, activity codes, share capital, filing history index as shown | A / B |
| S3 | Officers and ownership: directors/officers with appointment dates; shareholders/members; beneficial owners **only where the register publishes them**; capture each page | A / B |
| S4 | LEI: GLEIF record (if any), incl. reported parents | B |
| S5 | Identifiers: VAT/tax number validation (VIES REST API for EU; national equivalents where public); registration number cross-check | B / A |
| S6 | Sanctions screening: screen registration ID/LEI first where supported, then the raw name plus captured aliases, scripts and documented transliterations in each approved list. Record normalization/matching algorithm and version, thresholds if fuzzy matching is available, fields queried, list date/hash and unavailable lists. Classify `NO MATCH IN CHECKED DATA` / `POTENTIAL MATCH — HUMAN REVIEW` / `INCOMPLETE`; never clearance or confirmed identity from a name hit | B / A |
| S7 | Adverse media: search results captured for neutral query and for adverse-term queries; capture up to 10 relevant articles; record publication and date as displayed | C → A |
| S8 | Web presence: home page capture; stated address/contacts compared with the register | A/B |
| S9 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- **Official register first.** Aggregators are captured only as cross-checks and labelled as such. If the official register is pay-walled for documents, capture the free index/summary and record the document list as Leads with the fee notice.
- Register pages are volatile (status changes, filings added); every extract is "as at <UTC>".
- **Sanctions screening is a screening, not a determination.** Exact matching covers only the queried strings. Use fuzzy matching only through a documented, tested algorithm; if none exists, state `alias/fuzzy coverage NOT CHECKED`. Do not invent candidates or thresholds. The Investigator reviews each potential match against registration identifiers, jurisdiction and address; record their decision and unresolved differences. A no-match result names the checked lists, fields and variants and never implies sanctions clearance.
- **Recipient authority.** A hosting netblock, MX host or displayed contact is a technical lead, not proof of the correct legal recipient. Request sheets leave recipient identity/route unverified until an official provider/legal portal or agency procedure establishes that role.
- Adverse-term query set (print it before use): `fraud`, `sanction`, `investigation`, `indictment`, `lawsuit`, `bankruptcy`/`insolvency`, `money laundering`, plus two terms relevant to the case from intake field 7 if given. Localise terms to the jurisdiction's language when the Investigator provides them.
- Adverse media are reports by publishers; capture them, transcribe the headline and date, and label them "media report". No reputational summary of the entity.
- Never contact the entity, submit enquiry forms, request documents by email, or create accounts on register sites that offer them (R2). Free, logged-out access only; if a register requires a login even for search, record it and route through the Investigator under agency procedure (that is a Lead, not a level-A instruction).

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Official register not identifiable / not in English | Use the jurisdiction's official portal and documented delegation; else FAILED-DOCUMENTED with aggregator/securities-filing data labeled secondary and missing registry fields INCOMPLETE |
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

- Record the register's published verification role rather than assuming all registers operate identically. A filing, validated register field and aggregator statement have different authority; preserve their source labels and limits.
- Officer and shareholder names are as published; identity of individuals is not established here (Lead: separate runs under their own legal basis).
- Beneficial-ownership access varies by jurisdiction and changed after 2022 in the EU; "not published" is a feature of the register, not of the entity.
- Sanctions screening hits on names are frequent false positives; a `POTENTIAL MATCH` is a review task, not a finding.
- Media reports are allegations or reports by their publishers at the stated date.

### 9.9 Leads policy

Officers and owners (separate runs); parent/subsidiary entities; the entity's domain (L1-DOM); documents behind register pay-walls; registers requiring authenticated access via agency procedure.

### 9.10 Self-test specification

The versioned `selftest/L1-ORG.selftest.json` is the machine-readable assertion contract. Missing required fixtures, adapters or expected results yield INCOMPLETE, never PASS. Offline regression results and optional live-provider smoke results are reported separately.

Required offline fixtures cover two same-name entities, a delegated registry, non-Latin aliases, an unavailable sanctions list and securities-filings-only coverage. Assert that no candidate is selected without a recorded discriminator, unavailable coverage is INCOMPLETE, and an EDGAR-only record cannot satisfy state-register fields. Optional smoke target: `Apple Inc.`, US, LEI `HWUPKR0MPOU8FGXBT394`, CIK `0000320193`; GLEIF and SEC responses remain source-specific, dated observations. Do not assert that SEC EDGAR is California's entity register or that a successful name query is sanctions clearance.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Documents behind a register paywall or requiring authenticated access | the official register (name as captured) | agency procedure (not a lawful request to a private party) | registration number, legal name, document list captured | the listed filings |
| Officers/owners named in the record (persons) | — | not a lawful-request lead; a separate run under its own legal basis | — | — |
| Bank/payment relationships named in filings | the named institution | preservation | entity name, registration number, filing reference | account data (where the legal basis allows) |

### 9.12 Duration estimate

Typical FULL-mode duration: 15–30 minutes; longest steps S2/S3 (register pages) and S6 (list downloads).
