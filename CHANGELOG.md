# Changelog

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
