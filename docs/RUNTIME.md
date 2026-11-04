# Local runtime boundaries

Use `osint-evidence --help` and `osint-evidence COMMAND --help` for exact flags.
The [worked example](WORKED-EXAMPLE.md) is an executable offline starting point.
Install tested dependencies with `pip install -c requirements.lock '.[reports]'`.

## Records and supported operations

`case.json` follows the versioned [schemas](../schemas/README.md). Every mutation
is tied to an append-only `events.jsonl` state digest. The local operator approves
the exact initialized scope; a resumed session requires new approval. Evidence
files are created exclusively, never overwritten by the toolkit. A digest
mismatch preserves both expected and observed values and prevents sealing.

`capture` permits exact approved public destinations, HTTPS by default, with
validated/pinned IP connections and bounded redirects, requests, bytes and time.
Responses retain encoded HTTP entity bytes, duplicate headers and redirect bodies;
this is not on-wire TLS capture. Ordinary metadata is redacted. Raw metadata is
a separate restricted evidence item that cannot supply report quotations.
Partial responses remain provisional artifacts; failed acquisitions consume a
conservative request reservation and cannot silently become successful evidence.

`ingest` copies bounded bytes without rendering/executing/extracting the file.
Use `--expected-sha256` when an independent original hash is available. Use
`--restricted` for material that must not supply quotations. T-level transcripts
are provisional. D-level inputs require a verified `--source-evidence`, a
versioned `--tool` and exact `--parameters`; the stated derivation remains an
operator assertion unless independently reproduced.

`claim` supports exact UTF-8 text spans and JSON pointers. JSON rejects duplicate
keys, non-finite values and excessive nesting. Selected non-integer JSON numbers
must use exact text spans so binary floating-point rounding cannot silently
change evidence. A JSON pointer to an integer/string field can still be checked
when unrelated decimal fields exist elsewhere in the response. Arbitrary prose
belongs to `--analysis` and remains `REVIEW_REQUIRED`; it cannot be sealed as a
verified factual source-value claim.

`seal` requires complete required steps and passing implemented checks. HTML,
JSON and the internal import record are default views of the same canonical
record. Optional PDF/DOCX/XLSX views use pinned renderers and are independently
regenerated for equivalence. Unknown PDF glyphs fail closed; use the UTF-8 HTML
instead. Verification does not parse arbitrary received PDF content to infer
document authenticity.

`checkpoint`/`resume` require the complete earlier byte inventory and ledger;
filenames or hash-only placeholders cannot resume as verified evidence. A sealed
pack stays unchanged. `addendum` records later artifacts/custody notes in numbered,
hash-linked additions. The primary verifier also checks all addenda.

`verify-timestamp MANIFEST PROOF --ca TRUST.pem` uses OpenSSL on immutable local
snapshots and validates the proof against the explicitly selected CA. It does
not download/trust a CA, obtain a timestamp, upgrade OTS, or prove publication or
acquisition time. Keep proof/validation results through the addendum procedure.

## Offline helpers

`agentic_osint.adapters` exposes tested argument construction, email/Gravatar/MX,
separate body/text/resource changes, exact unit arithmetic, UTXO target deltas,
sample coverage, validated Snowflake decoding and bounded ZIP cataloging. ZIPs
are listed, never extracted or executed. Unsupported PDF structural checks return
`NOT_VERIFIED`. These helpers are not live provider adapters.

`graph` consumes explicitly supplied observations and artifact roots; only exact,
hash-checked source selections can produce captured co-occurrence edges.
Producer-reported and lead relations stay separate. `selftest` compares supplied
observations against a spec; it neither acquires nor authenticates them.

## Trust limits

These controls apply when operations go through this toolkit. An arbitrary shell,
browser, AI host or operator can bypass them. Local event hashes and confirmations
do not authenticate actors, establish legal authority, certify source truth or
prevent complete-pack rewriting without an external anchor. Retain the manifest
and each addendum tip independently, or use agency signatures/trusted timestamps.
Original acquisition time and clock synchronization require separate controls.

v1.3 generates canonical unpadded IDs such as `EV-1`. Legacy references such as
`EV-001` in supervised procedures are not silently aliased to another item. Import
or migrate old packs explicitly, preserving the original pack and label mapping.
