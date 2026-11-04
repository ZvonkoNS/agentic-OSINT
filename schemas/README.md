# Runtime contracts (1.3)

These JSON Schemas use Draft 2020-12. The Python runtime validates them locally
with `jsonschema` and format checks. References are embedded; validation must not
download or execute remote schemas or content. Root objects reject unknown keys.

| Contract | Meaning |
|---|---|
| `case.schema.json` | Canonical case, immutable run UUID, approved destination/budget policy, evidence records, typed claims and required steps |
| `evidence.schema.json` | Captured artifact records, exact byte digests and size, capture interval and expected-digest mismatch state |
| `claim.schema.json` | A typed source value or reviewable analysis anchored to an exact text span or JSON Pointer in a captured file |
| `event.schema.json` | Sequenced, hash-chained local event; the chain requires an independently retained anchor and does not authenticate the operator |
| `checkpoint.schema.json` | Case, file inventory and ledger anchor needed to resume with the original bytes |
| `integrity.schema.json` | Separate byte, recorded-workflow and selected-source-value results; no source-truth certificate |
| `graph.schema.json` | Distinct artifact-byte-checked co-occurrences, producer-reported relations and unverified lead relations |
| `import.schema.json` | Versioned canonical export; a null manifest digest means the export precedes sealing and avoids circular hashing |
| `seal.schema.json` | Immutable pack identity and manifest digest at sealing, with an explicit independent-anchor requirement |
| `addendum.schema.json` | Numbered, hash-linked post-seal addition; actor identity remains operator-asserted |
| `selftest.schema.json` | Released test specification with a selector, required flag and typed comparison for every assertion |
| `selftest-observations.schema.json` | Separately collected values and their availability; no assertion that those observations are authentic |
| `selftest-result.schema.json` | Deterministic comparison results and explicit coverage |

## Executable self-test comparison

Run from an installed checkout:

```console
python -m agentic_osint.selftest selftest/L1-WEB.selftest.json observations.json --output result.json
```

Every assertion's `path` is an RFC 6901 JSON Pointer into the supplied document's
`values` object. These paths are a normalized collector-output contract, rather
than instructions for the model to infer a value from a description. Extracting
those values from sources and preserving their provenance is a separate step.

For example, the first WEB assertion uses:

```json
{
  "schema": "agentic-osint/observations/1.3",
  "agent": "L1-WEB",
  "run_kind": "offline_fixture",
  "values": {"S2": {"final_http_status": 200}},
  "availability": {
    "WEB-01": {"status": "OBSERVED", "evidence_refs": ["EV-1"]}
  }
}
```

This abbreviated document is intentionally incomplete for the seven-assertion
WEB spec: the missing required observations produce `INCOMPLETE`, never `PASS`.
`OBSERVED`, `BLOCKED`, `NOT_RUN` and `ERROR` describe collection availability.
An observed negative result is different from an unavailable lookup. An
`exists:false` comparison can pass only when collection explicitly reports
`OBSERVED`; an omitted availability entry is `NOT_RUN`.

Comparison is type-sensitive: `true` is not the JSON number `1`. Array indices
and escaped pointer tokens are resolved without code evaluation. Current checks
are `equals`, `contains`, `startswith`, `all_startswith`, `matches`, `gte`, `lte`,
`between`, `in` and `exists`.

Aggregate precedence is `FAIL`, `INCOMPLETE`, `DRIFT`, `INCONCLUSIVE`, `PASS`.
Missing/blocked required checks prevent a complete verdict. Optional unresolved
checks still prevent an unqualified `PASS`. Exit status is `0` only for `PASS`,
`1` for every other verdict, and `2` for invalid input. The `release_eligible`
field means only that this supplied-observation comparison passed; it does not
authorize evidence-pack release or certify an AI host.

A `may_drift` flag alone never converts a failed comparison into `DRIFT`.
Offline fixture corruption is always a failure. For a live smoke check, drift
requires an explicit `baseline_change_review` in that assertion's availability
record: `confirmed:true`, a reviewer, a reason and evidence references. This
review is operator-asserted, not authenticated by the tool, and still produces
a non-passing, non-release-eligible result. Investigate collector regressions
before recording a provider-baseline change.

## Changes to contracts

Changing a required field, its semantics or a verdict meaning requires a new
schema profile and migration notes. Keep old artifacts and their schemas; do
not rewrite a sealed pack in place. Add strict positive and negative fixtures
before accepting a new field or format. Updating a live-provider baseline does
not constitute a supported-host evaluation or benchmark.
