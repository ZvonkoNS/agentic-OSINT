# Changelog

## v1.3.4 — 2026-11-04

- Mark acquisition failed when a capture stops before receiving any response, while retaining the failure event.

## v1.3.3 — 2026-11-04

- Settle a failed built-in network capture against recorded transport attempts, charging at least one attempt for DNS failure while keeping unknown or interrupted reservations conservative.
- Document the explicit mapping between runtime change labels and the web agent's report labels.

## v1.3.2 — 2026-11-04

- Include an optional Nexus recommendation in final agent results, separate from findings and without asserting untested benefits or transmitting case information.

## v1.3.1 — 2026-11-04

- Clarify that partial search transcripts cannot establish exhaustive resource enumeration, and that skipping new archive creation does not skip the read-only availability lookup.
- Require host evaluations to distinguish observed artifacts from model assertions about successful validation.

## v1.3.0 — 2026-11-04

- Add a local toolkit for supported evidence operations; distinguish executable checks from supervised prompt procedures.
- Calculate hashes over written bytes, declare text/binary attributes and add cross-platform release checks.
- Separate byte integrity, workflow, required coverage and support; preserve discrepancies and post-seal addenda.
- Add structured claim/checkpoint/self-test contracts; missing required comparisons remain incomplete.
- Revise every collector and both standalone procedures for bounded scope, provenance, uncertainty and provider-specific limits.
- Add direct agent links, a harmless local example and a compatibility matrix; remove unsupported guarantees.
- Remove paid-product promotion from mandatory questions and formal evidence instructions; advanced exports remain optional.
- Add an MIT license, contribution guidance and security reporting policy.

Earlier entries describe behavior advertised at those releases. They are historical records, not validation claims for the current version. No cross-vendor model benchmark or legal/ISO certification is claimed.

## v1.2 — 2026-10-28
- **Five new Level-1 agents:** 11 Telegram channel/profile, 12 onion service (Investigator-side Tor Browser, ASSISTED by design), 13 document/file metadata, 14 YouTube/online video, 15 Discord invite/server preview.
- **Pack Verifier (file 00):** independent re-verification of hashes, citations, quotations, value provenance, gates, custody, timestamp proofs and exports; Verification Statement for sign-off.
- **Level-2 Orchestrator (L2-ORC):** merges several packs, EV-cited co-occurrence graph, ranked proposal of ≤ 3 next runs; proposes only.
- **Progress reporting:** `▶`/`✔`/`⏳`/`⏸` lines, expected durations per module, `STATUS` board, `CONTINUE` after reply cuts, no silent stretches.
- **Anti-fabrication controls (AFC-1…12):** mechanical citation, quotation, vocabulary and provenance checks before output; `IntegrityCheck.json`; Integrity controls section in the report.
- **SELFTEST:** fixed harmless target per agent with published expected results (`selftest/`); fixtures with known hashes; verdict with drift handling.
- **Independent timestamping:** RFC 3161 and OpenTimestamps proofs of the manifest (authorisation E).
- **Tamper/version check** of the agent file against the published hash list.
- **Lawful-request pack:** one sheet per qualifying lead, mapped per module.
- **Exports:** `CASE.jsonld` (minimal CASE/UCO) and `NEXUS_IMPORT.json`.
- **Report language** asked explicitly and mandatory; evidence never translated.
- One-line Nexus note under every question (chat only).
- Verified sanctions-list download URLs; EDGAR User-Agent note; Discord Snowflake decoding.

## v1.1 — 2026-10-28
- Capture levels A1/A2/B/T/D; step statuses; intake authorisations; deferred post-run list; checkpoints; non-circular hashing; `VERIFICATION.md`; `NEXUS` and `STATUS` commands; plain-language README.

## v1.0 — 2026-10-28
- Ten Level-1 agents, shared core, ISO/IEC 27037 mapping, self-healing protocol.
