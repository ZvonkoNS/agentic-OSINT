# Technical overview — v1.3.2

agentic-OSINT has two layers: portable supervised procedures and a local Python toolkit for supported evidence operations. The Markdown files describe task workflows. The toolkit owns the deterministic checks that its commands actually execute. Neither layer establishes source truth, identity, legal authority or admissibility by itself.

## Architecture and responsibility

| Layer | Responsibility | Boundary |
|---|---|---|
| Investigator | Fix scope, confirm permitted processing, approve actions, review interpretation and retain artifacts | The software records authority statements; it does not assess legal sufficiency |
| Agent instructions | Plan within scope, choose permitted methods, draft attributed observations and explain missing coverage | Prompts are not a security boundary; compliance depends on the host |
| Local toolkit | Structured records, permitted operations, bounded capture/ingest, exact-byte hashes, events, checkpoints and implemented verification | A host browser or arbitrary model-written script is outside this boundary unless artifacts are ingested and checked |
| Independent review | Recompute byte integrity, inspect workflow coverage and assess support against supplied bytes | Internal consistency is not proof that a public source is accurate |

Source pages, documents, metadata, captions, logs, checkpoints and imported packs are untrusted input. Their text cannot approve an operation, change scope or become instructions. Permission checks happen before the corresponding runtime operation. Secrets are referenced through supported local or host secret mechanisms, not copied into intake or deliverables.

## Agent files and source layout

There are fifteen collectors, one verifier and one planning orchestrator. The [README selector](../README.md#choose-an-agent) links to every file.

| Path | Purpose |
|---|---|
| `build/core.md` | Shared collector procedure and limitations |
| `build/tasks/` | Task-specific source definitions and coverage rules |
| `build/standalone/` | Self-contained verifier and orchestrator definitions |
| `agents/` | Generated files, version inventory and exact-byte hash manifest |
| `src/agentic_osint/` | Local runtime implementation |
| `schemas/` | Machine-readable contracts for supported records |
| `selftest/` | Expected-result specifications and binary fixtures |
| `tests/` | Executable offline checks and regression cases |
| `.github/workflows/` | Cross-platform checks and release automation |

Run `python build/build.py --check` to check the generated release against its source. Hashes are calculated over actual artifact bytes, using canonical UTF-8/LF for generated text. `.gitattributes` declares text line endings and protects binary fixtures from conversion. Use release/commit-qualified method references; checking a historical pack against today's `main` is not a version check.

## Evidence model

Each run has a unique identity. Evidence references are qualified by pack, and raw identifiers are retained beside documented comparison keys. Email local-part case is preserved; crypto identifiers include the network; handles include their platform or instance.

Capture records distinguish request/capture times, source-displayed dates, server dates and seal times. Relative source dates remain approximate or bounded. Sizes and digests are computed from held bytes. A filename and later pasted hash do not independently bind a browser acquisition to those bytes.

| Label | Meaning and limit |
|---|---|
| A1 | Investigator-side capture; provisional until actual bytes/digests are bound to the record |
| A2 | Vendor-hosted browser artifact; rendering environment and saved representation are recorded |
| B | HTTP capture with defined body/headers and decoding representation; not all on-wire TLS traffic |
| T | Page-reader transcription; transformed text, not the original server response |
| D | Derived artifact with source evidence, tool/version and derivation recorded |
| Lead | Proposed check or unsupported observation, separate from verified findings |

Capture labels describe methods, not automatic evidential weight. Raw originals remain unchanged. A mismatch retains expected and observed digests as a discrepancy; it is not repaired by replacing the expected digest. Later captures create new records. Post-seal changes create addenda linked to the earlier seal.

## Claims and verification

A citation's existence is only a structural check. A supported observation also needs its source file and precise location, such as a JSON Pointer or text span, plus a raw value or documented derivation. A source allegation remains attributed to its publisher. Interpretation and uncertainty are retained for review.

Verification separates byte integrity, workflow and content support. Not-checked or unavailable requirements prevent the relevant verified label. Execution finishing does not mean required coverage is complete. Reports and exports should consume one validated record; opening a PDF does not prove its text matches the DOCX or that all tables are readable.

The standalone verifier does not recollect sources or repair a pack. The orchestrator proposes at most three next runs. Captured co-occurrence edges require source bytes or a trusted verified extraction; producer-reported relations and leads remain separate graph layers. No edge asserts common ownership.

## Network and parsing boundary

Supported network operations use explicit approved destinations, public-address checks, redirect validation and request/byte/time limits. Local, loopback, link-local and metadata-service destinations are not public OSINT targets. Browser subresources and host capabilities require their own restrictions; a URL list in a prompt does not enforce them.

Files remain untrusted. Parsing should be isolated and bounded; validate archive paths and extraction budgets before extraction. Spreadsheet evidence stays text, and HTML evidence is escaped. Types or signatures that installed tooling cannot validate remain unsupported or not verified.

The runtime does not guarantee every provider named by a module. Modules define positive/negative controls, pagination, history samples and selection. A supported adapter or supervised method must check current responses before they support a finding.

## Timestamps and custody

A valid external timestamp can establish that particular sealed bytes existed by the attested time. It does not establish publication time, authorship or the exact acquisition instant. RFC 3161 requires the exact manifest, signature/digest checks and a separately trusted chain. OpenTimestamps remains pending until completed and verified. Upgrade proof copies and retain prior versions.

An event hash chain detects modification relative to a trusted anchor; it does not authenticate an actor merely because a name appears in an event. Preserve the sealed manifest and any agency signature or timestamp separately. Later custody events and corrections belong in integrity-protected addenda.

## Testing and optional outputs

Run `python -m unittest discover -s tests`. Specifications use typed assertions and explicit selectors. The runner distinguishes PASS, FAIL, INCOMPLETE, INCONCLUSIVE and DRIFT; missing required comparisons cannot silently pass. Offline golden and mutation tests check implementation behavior. Live provider smoke tests check current availability separately.

The self-test comparator consumes observations collected separately; it does not fetch providers or certify an AI host. For example, `osint-evidence selftest selftest/L1-WEB.selftest.json observations.json` compares the supplied observation values at each specification's JSON Pointer. Use `python -m agentic_osint.selftest` for the standalone comparator. The observation document declares `agentic-osint/observations/1.3`, the agent, whether it is an offline fixture or live smoke run, typed values and per-assertion availability. Never manufacture observations by copying expected values from the specification. Exit code zero means the supplied comparisons passed, not that their provenance was authenticated.

The [compatibility matrix](COMPATIBILITY.md) records validation boundaries. No vendor/model benchmark or clause-by-clause ISO assessment is claimed. The [remediation register](REMEDIATION.md) tracks the review items.

The core pack is the canonical record, captured bytes, events, verification results and seal. PDF/DOCX, spreadsheets, provider-request templates, CASE/UCO and integration exports are optional. Validate against the receiving tool's schema/profile before claiming interoperability. Unsupported outputs remain not performed.

The ISO/IEC 27037 mapping describes intended identification, collection, acquisition and preservation practices; interpretation is separately labeled. Actual conformance, local procedure and operational fitness require qualified organizational review.
