# A harmless local example

This example uses synthetic text. It needs no real subject, public lookup service, AI account or network capture. It demonstrates implemented packaging and verification, not AI-host reliability or forensic certification.

## Run the example

From the repository folder:

```console
python -m pip install -c requirements.lock .
osint-evidence doctor
osint-evidence demo work/demo-pack
osint-evidence verify work/demo-pack --sealed
```

If the executable is not on PATH, replace `osint-evidence` with `python -m agentic_osint`. Choose a new output folder for another run rather than overwriting a sealed example.

The demo creates a case, records operator approval, ingests synthetic bytes, records a supported observation and required-step status, and seals the result. Read command output for paths and verification categories. The fixture is small enough to inspect by hand.

To exercise optional PDF/DOCX/XLSX rendering, install with `python -m pip install -c requirements.lock ".[reports]"`, then run `osint-evidence demo work/demo-with-reports --formats pdf docx xlsx` and verify that new folder. The default HTML/JSON demo does not require those renderer dependencies.

| Check | Expected behavior |
|---|---|
| Scope | The target is synthetic and the case is marked as a demonstration |
| Approval | The operation and stated actor are recorded; this is not independently authenticated identity |
| Source | A held file contains the synthetic input and its expected SHA-256 is preserved |
| Observation | A precise source span/field supports the recorded value |
| Coverage | Required work is distinguished from optional and not-performed work |
| Seal | The manifest covers the actual sealed bytes |
| Verification | Each implemented category reports its own result and reasons |

## Try a failed verification

Copy the whole pack to another folder. Change one character in the copied captured text, then run `osint-evidence verify` on the **copy**. It should report expected and observed digests without replacing the expected value to make the check pass.

Do not edit the sealed original. Legitimate later information belongs in a numbered addendum linked to the earlier seal. A changed source is new evidence, not a correction of the earlier bytes.

## Build a pack manually

The basic sequence is:

```console
osint-evidence init work/manual-pack --case DEMO --agent L1-DOC --target-type file --target example-input.json
osint-evidence approve work/manual-pack --actor DEMO --confirm CONFIRM
osint-evidence ingest work/manual-pack docs/example-input.json --level A1
```

For this fresh pack, ingest returns `EV-1` and `evidence/EV-1/input.json`. Check those values in the output before using the following command; substitute the actual values if your workflow differs. The claim selects the exact JSON number at `/example_number`, so no shell-specific string escaping is needed. The acquisition and support steps are updated by the corresponding successful operations.

```console
osint-evidence claim work/manual-pack --evidence EV-1 --file evidence/EV-1/input.json --pointer /example_number --value-json 42
osint-evidence verify work/manual-pack
osint-evidence seal work/manual-pack
osint-evidence verify work/manual-pack --sealed
```

Consult `osint-evidence <command> --help` for complete installed options. For real runs, supply the exact method commit/release with `init --revision`; this local example is explicitly unpinned demonstration data. Record additional required/optional work with `step`, rather than marking work done to obtain a pass. Missing bytes, unresolved support and unfinished required work must stay visible. A self-test that cannot compare a required assertion is incomplete, not a pass.

## Move to public collection

Select the relevant [agent](../README.md#choose-an-agent), fix a narrow scope, and obtain permission for the AI processor and each necessary third-party disclosure. Public requests can be logged. Verify actual tool capabilities, constrain destinations and preserve the acquisition environment. Start with a harmless public target and inspect its results before organizational use.
