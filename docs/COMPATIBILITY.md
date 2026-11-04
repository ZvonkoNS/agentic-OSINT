# Compatibility and validation status

Read CI results for the exact commit used. A configured workflow does not prove that a particular run passed, and one passing example does not establish a reliability rate.

On 2026-11-04 the v1.3.0 working tree's documented local demo and manual JSON-value workflow were exercised on Windows with Python 3.13.5. Default HTML/JSON and requested PDF/DOCX/XLSX packs completed and their sealed verification returned PASS for byte integrity and exact source-value comparisons, with workflow correctly labeled RECORDED. This is a local implementation check, not a published-release attestation or vendor-host benchmark.

| Component | Intended use | Validation boundary |
|---|---|---|
| Local toolkit | Python 3.11+; command help defines available operations | Offline unit, fixture, mutation and build checks cover implemented behavior; consult exact-commit results |
| Windows | Local Python and artifact checks | Windows CI exercises supported release checks; explicit text/binary rules protect bytes |
| Linux | Local Python and artifact checks | Linux CI exercises the same release checks; artifact equivalence is checked, not assumed |
| macOS | Python command-line use | No dedicated macOS CI or operational validation is claimed |
| ChatGPT | Supervised procedure guidance | No end-to-end host/model/version benchmark is published |
| Claude | Supervised procedure guidance | No end-to-end host/model/version benchmark is published |
| Gemini | Supervised procedure guidance | No end-to-end host/model/version benchmark is published |
| Microsoft Copilot | Supervised procedure guidance | No end-to-end host/model/version benchmark is published |
| Local/self-hosted models | Procedures with explicitly configured tools | No general compatibility or compliance guarantee |
| Browser tools | Supervised acquisition with saved artifacts | Save/download paths, logged-out state, screenshots and subresources need host-specific checks |
| Tor Browser | Investigator-side isolated capture only | No automated Tor; test the exact version's capture procedure |
| Lookup providers | Approved methods/destinations only | Availability, access rules, fields and coverage change; instructions are not a live availability claim |
| Optional formats/imports | Relevant renderer and receiving-tool checks | No general interoperability certification |

## Record a host evaluation

Use harmless data. Record date, host/product, plan, model ID where exposed, OS/browser, tool versions, capability results, exact agent commit/hash, scenario, expected result and actual artifacts. Never report a model/tool version from memory.

Exercise successful small runs, missing capabilities, blocked providers, corrupt artifacts, unsupported claims, instruction text embedded in sources, scope-expansion attempts, interruption and missing-byte resume. Required unavailable checks cannot PASS. Keep DRIFT separate from FAIL and incomplete comparisons.

For repeated evaluations report denominators for byte-integrity failures, unauthorized actions, unsupported claims, false positives/negatives, missing coverage and recovery, plus human time, request count and cost. A single trial does not generalize to every plan or model.
