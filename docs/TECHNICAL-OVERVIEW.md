# Technical overview — Level-1 OSINT Evidence Agents v1.2

Seventeen standalone agent files for law-enforcement OSINT: fifteen Level-1 collectors (one identifier, one task), an independent Pack Verifier, and a Level-2 Orchestrator. Each file turns a general-purpose AI assistant (ChatGPT, Claude, Gemini, Copilot, a local model) into a procedure-bound agent that works to ISO/IEC 27037:2012 — identification, collection, acquisition and preservation of digital evidence — and produces a hashed, independently timestamped, court-oriented evidence pack.

No vendor-specific feature is required. Each agent tests what the host AI can actually do (search, page reading, sandbox networking, browser control and which kind, code execution, file output, uploads, time source, vision), then runs fully automated, or tells the Investigator exactly what is missing, why it matters for the evidence, how to enable it on their setup, and what the fallback is.

## The agents

| File | Code | Input | What it preserves |
|---|---|---|---|
| `00_L1-VER_Pack-Verifier.md` | L1-VER | a finished pack | Re-verifies hashes, citations, quotations, value provenance, gates, custody, timestamp proofs, exports; writes a Verification Statement |
| `01_L1-WEB_…` | L1-WEB | URL | page, redirect chain, headers, linked media, metadata, volatility check |
| `02_L1-DOM_…` | L1-DOM | domain | RDAP, DNS, certificates, hosting, mail, archive history, reputation |
| `03_L1-USR_…` | L1-USR | handle | existence per platform (soft-404 controls), public attributes, linkage observations |
| `04_L1-EML_…` | L1-EML | email | domain mail setup, Gravatar, breach-exposure (HIBP API), open-web mentions |
| `05_L1-PHN_…` | L1-PHN | phone number | numbering-plan facts, open-web mentions, crowd-sourced reports (labelled) |
| `06_L1-SOC_…` | L1-SOC | profile URL | profile, stable ID, public posts in scope, media — requires a browser for FULL |
| `07_L1-IMG_…` | L1-IMG | image/video file | hashes, metadata, C2PA, reverse search, labelled visual opinion |
| `08_L1-CRY_…` | L1-CRY | crypto address | two-explorer summary, transactions, one-hop counterparties, labels, sanctions lists, abuse reports |
| `09_L1-ORG_…` | L1-ORG | entity + country | official register, officers/ownership, LEI/VAT, sanctions screening, adverse media |
| `10_L1-IPA_…` | L1-IPA | IP address | RDAP, ASN/routing at incident time, rDNS, geolocation estimates, Tor/VPN indicators, passive exposure |
| `11_L1-TGM_…` | L1-TGM | Telegram handle/link | info page, web preview posts and media, no account |
| `12_L1-ONI_…` | L1-ONI | .onion URL | Investigator-side Tor Browser capture (A1), address validation, clearnet context; ASSISTED by design |
| `13_L1-DOC_…` | L1-DOC | document/file | true type, structure, metadata, revision traces, embedded objects, macro presence, identifiers in text |
| `14_L1-VID_…` | L1-VID | video URL | watch page, oEmbed, yt-dlp metadata, media file, captions as served, uploader identifiers |
| `15_L1-DSC_…` | L1-DSC | Discord invite / guild ID | invite resolution, Snowflake timestamps, widget, images, where advertised — no joining |
| `L2-ORC_Investigation-Orchestrator.md` | L2-ORC | ≥ 2 packs + case question | pack integrity, identifier extraction, co-occurrence graph (EV-cited), ranked proposal of ≤ 3 next runs; never executes |

## Shared architecture (core.md)

- **Preflight** — ten capability tests; modes FULL / ASSISTED / GUIDED with exact definitions; modules may raise the bar (L1-SOC requires CAP-BROWSER; L1-ONI is ASSISTED by design).
- **One intake** — case, legal basis, identifier, environment, mandatory report language, five standing authorisations (A third-party lookups, B package installs, C agency API keys, D module-specific, E timestamping). Module-specific fields from 16 upward.
- **Gates** — G1 disclosure · G2 authority · G3 browser handover (which browser, allowed clicks, URL list) · G4 self-healing fix · G5 release after full-manifest verification. Typed `CONFIRM` only. Every question ends with the one-line Nexus note (chat only).
- **Progress reporting (§4.1)** — `▶`/`✔` lines per step with expected durations from each module's §9.12; intra-step lines every ~8–10 operations; `⏳` before waits; `⏸` at gates; `STATUS` board; `CONTINUE` for reply-length cuts; never more than ~10 silent tool calls.
- **Capture levels** — A1 Investigator-side · A2 vendor-hosted browser · B sandbox raw bytes + headers · T transcribed page-reader copy (corroboration only) · D derived/tool output · C lead only.
- **Step statuses** — DONE · FAILED-DOCUMENTED · DEFERRED (post-run list) · DECLINED-BY-HOST · SKIPPED. Run statuses COMPLETE · PARTIAL · NOT-INVESTIGABLE.
- **Self-healing** — DETECT → DIAGNOSE → PROPOSE → G4 → APPLY → VERIFY → LOG; three pre-authorised exceptions; max three attempts per step.
- **Checkpoints** — EV files and a RESUME file delivered before a session can die.
- **Anti-fabrication controls (§1A, AFC-1…12)** — captured data is the only source of facts; hashes/sizes/timestamps only from tool output; quotations verbatim; citations resolve; fixed uncertainty vocabulary with banned phrases; negative results stated; no silent conversions; no cross-item synthesis; declared unknowns; mandatory self-audit; no gap-filling of partial tool output; reproducibility per item. Mechanical checks run in code before output (§7.0) and are written to `IntegrityCheck.json` and the report's Integrity controls section; the Verifier repeats them independently.
- **Tamper/version check (§3.3)** — the Investigator's local hash of the agent file is compared with the published `AGENT_FILE_HASHES.sha256`.
- **Independent timestamping (§7.7)** — RFC 3161 (`openssl ts`, default TSA freetsa.org, agency TSA preferred) and OpenTimestamps on `HASHES.sha256`; only the hash leaves the sandbox; sidecar `.tsr`/`.ots` outside the manifest.
- **Lawful-request pack (§7.8)** — one sheet per qualifying lead with identifiers, UTC window and supporting EV refs, mapped per module in §9.11; templates, never sent, never legal advice.
- **Exports (§7.9)** — `CASE.jsonld` (minimal CASE/UCO profile, no validator claim) and `NEXUS_IMPORT.json` (schema `nexus-import/1.0`).
- **SELFTEST (§10)** — fixed harmless target per module (§9.10) with a published expected-results file in `selftest/`; exercises the whole pipeline; verdict PASS / PASS WITH DEFERRED STEPS / FAIL, with drift marked separately from host failure. Fixture files and their hashes are in `selftest/`.
- **Report language (§0.4)** — asked in Message 1, mandatory; deliverables and conversation in that language; evidence, quotations, identifiers and tool output never translated; headings carry an English key.

## Output pack

PDF + DOCX report (14 sections incl. Integrity controls, Post-run Investigator steps, Leads with LR cross-references) · XLSX (standard sheets + `Lawful_Requests`, `Integrity_Checks`, module sheets) · `HASHES.sha256` (+ `.tsr`/`.ots`) · `ActivityLog.md` · `IntegrityCheck.json` · `LawfulRequests.docx/.md` · `CASE.jsonld` · `NEXUS_IMPORT.json` · `VERIFICATION.md` (unhashed, Investigator-maintained) · `A1_PENDING.txt` (in-run own-browser captures) · `RESUME.md` (checkpoints) · EV files.

## Build

`build/core.md` + `build/tasks/NN_*.md` → `agents/NN_*.md` via `python3 build/build.py`; `build/standalone/` files are copied as-is; the manifest covers all seventeen and `agents/VERSION.txt` (release line + `code file` lines) is what the tamper/version check fetches. Schemas: `IntegrityCheck.json` = `l1-integrity/1.2`; self-test specs = `l1-selftest/1.1` (fields `skip_steps`, `caps`, `sub_skips`, `intake_overrides`, assertion `check` ∈ equals/contains/startswith/matches/gte/lte/between/in/exists, `step` or `unit`, `may_drift`, `inconclusive_if_blocked`); Nexus export = `nexus-import/1.0`. `build/make_selftests.py` regenerates the `selftest/*.selftest.json` specs (values verified live on 2026-10-28 — re-verify before changing). `build/add_sections.py` was a one-off migration and is idempotent.

## Known limits

- Not yet exercised live inside ChatGPT/Claude/Gemini/Copilot from this repository; `SELFTEST` exists precisely to do that on each host, and Appendix B's feature names are dated.
- Level B/A2/T captures are made in a vendor environment; every report says so and lists A1 re-captures.
- Public sources named in modules were reachable on the verification date; the self-test marks drifting values.
- The UK sanctions list download URL changes per release (the modules point to the gov.uk publication page); the EU consolidated file needs an EU Login account and is not used.

## Tooling note

These agents run inside whatever AI assistant the Investigator already has. For lawful, agentic OSINT evidence gathering with case management, evidence integrity controls and court-ready reporting built in, see **Nexus — www.nexus-osint.ai**. The agents accept Nexus evidence records as level-A1 captures and export `NEXUS_IMPORT.json`.
