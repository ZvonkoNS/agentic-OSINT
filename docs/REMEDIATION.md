# v1.3 remediation register

This register maps all 41 findings from the review of commit
`32d699b8fca92e5daea73a492e90ecd273def406` to the v1.3 changes and checks.
It distinguishes implemented controls from procedures that require a supported
external tool. “Addressed” does not mean that every named website, AI host or
forensic parser has been implemented or operationally certified.

The local toolkit enforces its own API/CLI operations. It cannot prevent a host
or operator from bypassing it with unrelated tools. Local confirmations and
event chains do not authenticate people or resist rewriting of an entire pack
without an independently retained signature/timestamp anchor. Exact source-value
checks do not establish a source's truth or validate arbitrary semantic claims.

## Finding-by-finding changes

| Finding | Implementation or correction | Verification and remaining boundary |
|---|---|---|
| F01 Windows build byte hashes | `build/build.py` writes canonical UTF-8/LF bytes, hashes saved bytes and verifies staged output before publication. | CRLF-source, deterministic-build, corrupt-output and rollback regression tests; `build.py --check`. |
| F02 checkout conversion | `.gitattributes` fixes text EOL and marks evidence containers binary. The PDF fixture is restored to its committed 2,012 bytes. | A Windows-style autocrlf checkout fixture verifies both Markdown and PDF bytes; all fixture hashes/sizes checked. |
| F03 unenforced prompt safeguards | Added the `agentic_osint` local runtime for supported capture, policy, hashing, claims, logs, checkpoints, rendering and verification. Prompts are explicitly supervised procedures. | Offline runtime and adversarial tests. Commercial AI hosts and all provider workflows remain unbenchmarked. |
| F04 citation versus support | Claims select exact UTF-8 spans or JSON pointers and compare typed values. Free prose is analysis requiring review; source-value records cannot smuggle a `text` assertion. | Wrong values with valid EV references, boolean/number differences, duplicate JSON keys and rounded decimal selections fail. Non-integer JSON numbers require exact text spans. Semantic inference is not certified. |
| F05 corrected mismatch expectations | Store expected and observed digests separately; mismatching input goes to quarantine and prevents sealing. | Byte mutation and expected-hash tests preserve the original expectation. |
| F06 pending A1 binding | Local ingest hashes the actual copied bytes. Pending/transcribed material cannot become verified critical evidence by filename alone. | Hash comparison, provisional-T and claim-source checks. Browser-only acquisitions without available bytes remain incomplete. |
| F07 mutable continuation record | Numbered addenda preserve the original manifest and form a checked hash chain anchored to it. | Changed attachment, malformed custody fields, wrong pack ID and altered earlier record fail primary verification. Retain addendum tips outside the editable pack. |
| F08 misleading COMPLETE | Required-step coverage, byte integrity, recorded workflow and content support are separate. Missing required work cannot seal. | Required DEFERRED/FAILED, no evidence and no claims prevent a complete result. |
| F09 hostile source instructions | All source text and imported state are data. Runtime tools accept validated structured arguments; source content cannot choose destinations or execute commands. | Inert hostile-source fixtures, strict schemas and network-denial tests. This is not a guarantee that an arbitrary AI host obeys its prompt. |
| F10 destination policy | Exact URL approval, public-address validation, pinned-IP HTTPS, redirect checks and global request/byte/deadline limits. | Mock DNS/transport tests cover private/mixed answers, rebinding transitions, local/metadata addresses, redirects, TLS and deadline failures. |
| F11 hostile parsing/output | Bounded UTF-8/JSON support, bounded ZIP cataloging without extraction, no execution/viewer fetching, escaped inert HTML and text-only spreadsheet cells. | Traversal, links, malformed archives, decompression budgets, formula-looking text and hidden report-part mutations. General document/C2PA/signature parsers remain external approved tools. |
| F12 permissions and secrets | Exact initialized scope is approved before acquisition. Third-party opt-outs are enforced; raw response metadata is restricted and ordinary metadata redacted. No ordinary-chat API-key workflow is supplied. | Pre-approval and denied-lookup tests, scope-hash checks and redaction fixtures. Restricted file ingest is explicit; recognizing every secret in arbitrary content is not automated. |
| F13 time trust and precision | Separate acquisition intervals, source times and seal times; local clock synchronization is explicitly unverified. Relative-time instructions require uncertainty. | Event ordering and interval checks; no claim that an HTTP Date header is an authenticated clock. |
| F14 capture representation | Preserve HTTP entity bytes with content encoding, duplicate headers, redirect bodies and environment/TLS metadata. Different views remain separate artifacts. | Gzip, redirects, partial responses and duplicate-header tests. This is not TLS packet capture or a browser traffic archive. |
| F15 timestamp trust | `verify-timestamp` verifies an RFC3161 proof over immutable snapshots against an explicitly supplied CA trust store. Input mutation invalidates the result. | Argument/snapshot mutation regression. CA trust is an agency decision; obtaining proofs and OTS upgrade/validation are explicitly external when unavailable. |
| F16 resume and identifiers | UUID pack identities, canonical variable-length EV IDs, complete checkpoint file lists, pre/post-copy hash validation and renewed approval. | Missing/omitted files, changed bytes and resumed-session approval tests. v1.2 zero-padded labels are legacy references, not silent aliases for v1.3 records. |
| F17 moving method versions | Procedures record immutable method revision/hash; current-version notices are separate. Tagged assets receive immutable manifests and GitHub/Sigstore attestations through the release workflow. | Release version/inventory/archive tests; attestation verification applies only to assets actually produced by that workflow. A caller-supplied revision is recorded, not independently authenticated by the runtime. |
| F18 self-test specifications only | Executable typed JSON-Pointer comparator, strict observation schemas, availability states and fail-closed aggregation; all 15 specs regenerated. | Offline mutation/absence/error/regex-budget tests. DRIFT needs an explicit reviewed live-baseline change and is never PASS. The comparator does not collect/authenticate observations or benchmark a host. |
| F19 incomplete standalones | Verifier and orchestrator contain their own operating, capability, gate, error, scope and verdict rules. | Standalone dependency/placeholder checks and source review; no missing “any L1 file” dependency is required to run their procedure. |
| F20 limited verifier | Deterministic case/ledger/evidence/schema/claim/manifest/addendum checks and canonical report/export equivalence. | Rehashed hidden DOCX changes, altered PDF/XLSX views, malformed state and invented source values fail. Results explicitly distinguish recorded workflow from authenticated authority. |
| F21 identifier merging | Preserve email local-part case; namespace crypto addresses by network and handles by platform/instance; preserve raw strings separately. | Cross-chain, email-case, URL and IDNA tests. Comparison keys do not prove identity or checksum validity. |
| F22 graph provenance | Verified co-occurrence requires exact selectors in held, hash-checked artifacts. Summary assertions and lead relations have separate graph layers. | Missing/changed bytes, wrong selectors, duplicate pack IDs and resource-budget tests. A graph adds no source truth. |
| F23 unstable schemas/renderers | Versioned JSON Schemas, pinned direct dependencies and tested transitive constraints; all views derive from the same canonical case. | Schema negatives and canonical rendering tests; supported PDF glyphs and measured-width wrapping. Unsupported PDF characters fail rather than becoming replacement glyphs. Nexus/CASE receiving-tool compatibility is not claimed. |
| F24 WEB stability | Separate body/text/resource change checks and coverage-aware collection instructions. | Changed media with unchanged text is detected by the offline helper when resource maps are supplied; unobserved resources remain not checked. |
| F25 DOM parsing/history | Require a versioned Public Suffix List for registrable-domain decisions and label bounded archive/certificate queries as samples. | Module contracts remove complete-history claims from bounded queries. A live PSL/archive provider adapter is not supplied and cannot be reported as performed without a real tool result. |
| F26 USR existence | Platform-specific valid controls, positive identifiers and explicit approved destination sets replace generic size-only inference. | Corrected module contracts; platforms without tested classifiers stay inconclusive. No live all-platform existence adapter is claimed. |
| F27 EML API/MX | SHA-256 Gravatar identifier helper; domain-only email normalization; explicit null MX, no MX, NXDOMAIN and SERVFAIL states. | Offline email/MX/Gravatar vectors. Live endpoints/authentication and mailbox existence remain separate checks. |
| F28 PHN validation | Require versioned possible/valid/type library states rather than conflicting hard-coded digit rules; preserve range/portability caveats. | Module regression checks; the local toolkit does not invent a carrier result when a numbering-plan adapter is absent. |
| F29 SOC selection | Deterministic inclusion/order, pinned/repost rules, cursors, budgets and omission ledgers. | Procedure contracts; public API and browser coverage must be stated separately. No cross-platform browser automation is supplied. |
| F30 IMG provenance/opinion | Correct URL/file ingest branches; separate C2PA integrity/trust/asset coverage from visual opinion; precise uncertainty. | Module contracts and byte-preserving ingest. C2PA/OCR/vision/geolocation validation requires the named real tool and human review; absence is not fabrication evidence. |
| F31 CRY semantics | Exact native-unit conversion, UTXO target delta without invented per-party allocation, sample-coverage labels and chain/finality/validator requirements. | Synthetic multi-input/output, unresolved script, coinbase, spam/sample and exact-decimal vectors. No universal multichain tracing adapter is claimed. |
| F32 ORG authority/screening | Jurisdiction/field-specific authority, exact identifiers first, aliases/candidate review, unavailable-list coverage and recipient verification. | Corrected procedure and self-test expectations. Screening is not sanctions clearance or a legal determination. |
| F33 IPA historical precision | ExoneraTor observations retain date resolution and relay/exit distinctions; present and historical facts are separated. | Corrected procedure; a date-level relay result never establishes a particular incident's path or subscriber. |
| F34 TGM scope | Supplied post is preserved before any explicitly approved channel expansion; record stable IDs where exposed and pagination gaps. | Module scope contracts; preview omissions remain limitations. |
| F35 ONI capture | Explicit investigator-side Tor exception, isolated/inert reconstruction procedure, tested-version requirement and consistent inventory-only/hash-only limits. | Procedure review; no sandbox Tor or Tor Browser certification. Unsupported shortcuts must be tested locally or replaced with an approved capture method. |
| F36 DOC revisions/signatures | Removed EOF-count-as-fact recipes. Structural revision/signature checks require appropriate parser outputs and explicit trust/coverage states. | EOF-mutation helper remains NOT_VERIFIED. The toolkit never silently substitutes a byte count for structural document analysis. |
| F37 VID commands | Fixed argument arrays enforce single-video/no-config operations, no media in metadata/comments/captions modes, bounded retries/sizes and explicit fragment/caption choices. | Parsed module argv and adapter tests; outer aggregate quota and live platform behavior still require a supported capture environment. |
| F38 DSC identifiers/errors | Validated object types only for millisecond Snowflakes; widget identities remain anonymized; API error body required for setting conclusions. | Offline vectors reject fabricated/widget identities and retain milliseconds. Format decoding alone does not establish Discord existence. |
| F39 release controls | Windows/Linux Python 3.11/3.13 CI, strict build/fixture/schema/test checks, package creation, deterministic source ZIP, SHA256SUMS and non-overwriting tagged release. | Local regression suite and build/package checks; remote matrix and provenance results are visible in GitHub Actions. |
| F40 onboarding/claims/license | Direct downloads for all 17 agents, harmless demo/manual guide, explicit compatibility limits, optional advanced formats, MIT license and contribution/security routes. Advertising removed from gates/reports. | Documented CLI sequence and tampered-copy check run locally. Prohibited-content handling follows pre-approved agency disposition rather than improvised deletion. |
| F41 maintenance portability | Wiki output is configurable and uses checked HEAD with errors checked. One-time v1.2 migrations moved to non-executable history text. | Detached-HEAD and custom-output wiki tests; supported build command is documented. |

## Operational validation still required

The automated suite uses local synthetic fixtures and mocked transports. It is
not a test of real people, all provider endpoints, Tor Browser installations,
live C2PA/document-signature validators, receiving Nexus/CASE tools or commercial
AI-host compliance rates. The procedures require unavailable mandatory checks
to remain incomplete instead of manufacturing a result. Organizations should
evaluate their supported host/model/tool versions and case-specific method
before operational reliance.

The runtime's `PASS` is scoped to its documented byte, recorded-workflow and
exact-source-value checks. It is not a court-admissibility, source-truth,
authenticated-authorization or full-provider-coverage verdict.
