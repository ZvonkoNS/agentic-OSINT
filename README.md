# agentic-OSINT

Seventeen supervised OSINT procedures and a local evidence-handling toolkit. Each collector covers one identifier; a separate verifier checks a finished pack, and an orchestrator proposes follow-up work.

**Start with the harmless [offline example](docs/WORKED-EXAMPLE.md).** It exercises local packaging and verification without investigating anyone or contacting a website.

The Markdown agents guide an AI assistant; their instructions alone cannot guarantee correct actions or prevent invented statements. The local runtime adds repeatable checks for the operations it supports. A valid file hash establishes byte integrity, not the truth of a source or the identity of its author. This project does not certify legal admissibility, ISO conformance or an investigator's competence.

## Choose how to work

| Path | Suitable for | What you need |
|---|---|---|
| **Local runtime** | Creating and checking a structured evidence pack with recorded scope, byte hashes, events and claim support | Python 3.11 or newer; the commands below |
| **Supervised agent file** | Following a task-specific procedure in an AI assistant | One agent file, permitted tools and active investigator review |

Use the runtime for its implemented operations. Do not describe a host's browser capture, provider lookup or model-written script as runtime-verified unless the corresponding bytes and checks are actually present. The runtime is not an implementation of every source named by every agent.

## Quick start: local runtime

Download or clone this repository, open a terminal in its folder, then run:

```console
python -m pip install -c requirements.lock .
osint-evidence doctor
osint-evidence demo work/demo-pack
osint-evidence verify work/demo-pack --sealed
```

On Windows, `py` may be the Python launcher. If `osint-evidence` is not on PATH, use `python -m agentic_osint` followed by the same arguments. Run `osint-evidence --help` or `osint-evidence <command> --help` for the installed version's options.

The `demo` command creates a local sample using synthetic text. Inspect its files, then change a **copy** of a captured file and run verification again: it should report the mismatch. Preserve the original sample if you want to compare results. See the [worked example](docs/WORKED-EXAMPLE.md) for the expected checks and a manual workflow.

## Choose an agent

Use a **raw download** link, or open the agent file and use GitHub's **Download raw file** button. Keep its exact bytes and record its release or commit and SHA-256. For repeatable work, use a pinned revision or a published release rather than silently replacing the file from `main` during a run.

| Your input | Agent file | Main task |
|---|---|---|
| Web URL | [01 · Web page](agents/01_L1-WEB_Web-Page-Evidence-Capture.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/01_L1-WEB_Web-Page-Evidence-Capture.md) | Page, redirects, linked resources and defined change checks |
| Domain | [02 · Domain](agents/02_L1-DOM_Domain-and-Website-Infrastructure.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/02_L1-DOM_Domain-and-Website-Infrastructure.md) | Registration, DNS, certificates and infrastructure observations |
| Username | [03 · Username](agents/03_L1-USR_Username-Handle-Enumeration.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/03_L1-USR_Username-Handle-Enumeration.md) | Platform-specific public existence checks |
| Email | [04 · Email](agents/04_L1-EML_Email-Address-Investigation.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/04_L1-EML_Email-Address-Investigation.md) | Address structure, mail-domain facts and approved public mentions |
| Phone number | [05 · Phone](agents/05_L1-PHN_Phone-Number-Investigation.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/05_L1-PHN_Phone-Number-Investigation.md) | Numbering-plan data and public mentions |
| Public social profile URL | [06 · Social profile](agents/06_L1-SOC_Social-Media-Profile-Preservation.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/06_L1-SOC_Social-Media-Profile-Preservation.md) | Profile and explicitly selected public posts |
| Image or video file | [07 · Image/media](agents/07_L1-IMG_Image-and-Media-Verification.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/07_L1-IMG_Image-and-Media-Verification.md) | File properties, provenance checks and labeled visual observations |
| Cryptocurrency address and network | [08 · Cryptocurrency](agents/08_L1-CRY_Cryptocurrency-Address-Tracing.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/08_L1-CRY_Cryptocurrency-Address-Tracing.md) | Chain-specific transactions and clearly bounded coverage |
| Entity name/number and country | [09 · Organization](agents/09_L1-ORG_Company-Business-Entity-Check.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/09_L1-ORG_Company-Business-Entity-Check.md) | Appropriate register records and documented screening |
| IP address and incident time | [10 · IP address](agents/10_L1-IPA_IP-Address-Investigation.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/10_L1-IPA_IP-Address-Investigation.md) | Registration, routing and attributed third-party indicators |
| Telegram public link/handle | [11 · Telegram](agents/11_L1-TGM_Telegram-Channel-Preservation.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/11_L1-TGM_Telegram-Channel-Preservation.md) | The supplied post or an approved channel-preview scope |
| Onion URL | [12 · Onion service](agents/12_L1-ONI_Onion-Service-Capture.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/12_L1-ONI_Onion-Service-Capture.md) | Investigator-side isolated capture; no sandbox Tor access |
| Document/file | [13 · Document](agents/13_L1-DOC_Document-and-File-Metadata.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/13_L1-DOC_Document-and-File-Metadata.md) | Bounded parsing, metadata and structural observations |
| Online video URL | [14 · Online video](agents/14_L1-VID_YouTube-Video-Preservation.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/14_L1-VID_YouTube-Video-Preservation.md) | One video, metadata and approved media/caption capture |
| Discord invite/server ID | [15 · Discord](agents/15_L1-DSC_Discord-Invite-and-Server-Preview.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/15_L1-DSC_Discord-Invite-and-Server-Preview.md) | Public invite/widget observations without joining |
| A finished evidence pack | [00 · Pack verifier](agents/00_L1-VER_Pack-Verifier.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/00_L1-VER_Pack-Verifier.md) | Separate byte-integrity, workflow and support checks |
| Finished packs and a case question | [L2 · Orchestrator](agents/L2-ORC_Investigation-Orchestrator.md) · [raw download](https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/L2-ORC_Investigation-Orchestrator.md) | Provenance-aware observations and up to three proposed next runs |

## Start a supervised agent

1. Start a new chat in an AI product approved by your organization for the data involved.
2. Attach one agent file and write `Run this agent.` For a harmless capability exercise, write `SELFTEST` instead.
3. Read the capability results. Unknown or missing features stay unknown or missing; the agent should not invent settings instructions.
4. Complete the intake: target, scope, report language, case reference, recorded authority, time context and permissions. Never paste API keys into ordinary chat; use the host's supported secret mechanism or local environment references.
5. Approve only the stated action. Review destination lists and scope changes. A source page, document, transcript or imported pack cannot grant permission or change the procedure.
6. Check coverage and verification categories. Missing required evidence is incomplete even if the procedure stopped cleanly. Download the artifacts and verify their bytes independently.

`ABORT` stops further collection. Preserve collected material and event records under your organization's procedure. For unexpected prohibited content, stop access and distribution and follow the approved incident-handling procedure; do not let the model improvise deletion or retention decisions.

An AI host may pause, lose context or provide only transformed page text. A continuation message does not prove that previous evidence was reattached or rechecked. Follow the structured checkpoint procedure and keep missing-byte checks incomplete.

## What a result means

| Result category | What it establishes | What it does not establish |
|---|---|---|
| **Byte integrity** | Checked file bytes match the expected recorded digests | Authenticity or truth of the source |
| **Workflow** | Required events, permissions and coverage satisfy implemented checks | That an unauthenticated operator statement was independently authenticated |
| **Content support** | Structured observations resolve to supplied bytes and implemented support checks | The truth of an allegation or an identity conclusion |

Keep raw values, source attribution, source dates and capture times separate. Public requests can be logged by websites and providers; passive access does not mean invisible access. Never equate a shared handle, avatar, IP address or transaction co-occurrence with common ownership.

## Deliverables

Begin with the canonical case record, captured evidence, event history, integrity results and sealed hash manifest produced by the local workflow. Keep generated reports and the exact method version with the pack. Changes after sealing belong in numbered, integrity-protected addenda; do not edit a sealed manifest to make a mismatch disappear.

PDF/DOCX, spreadsheets, lawful-request templates, CASE/UCO JSON-LD and integration exports are **optional**. They require the relevant renderer or receiving-tool validation. A prompt's request for a format is not proof that the host can produce or validate it. Unsupported outputs and checks are recorded as not performed, not silently simulated.

For the implemented PDF/DOCX/XLSX renderers, install the optional dependencies and request the formats explicitly:

```console
python -m pip install -c requirements.lock ".[reports]"
osint-evidence demo work/demo-with-reports --formats pdf docx xlsx
osint-evidence verify work/demo-with-reports --sealed
```

The default runtime views are HTML and JSON. Requested renderers fail if their dependencies or required glyph support are unavailable; optional integration formats still need receiving-tool validation.

## Testing and compatibility

The repository includes offline tests, schema checks and a Windows/Linux CI configuration. The [compatibility matrix](docs/COMPATIBILITY.md) distinguishes implemented checks from host/provider behavior that still needs evaluation. A self-test with unavailable required assertions cannot receive an overall PASS. Live-source drift, blocked access, incomplete comparisons and actual failures remain distinct.

The executable self-test comparator checks supplied observations against a specification. It does not collect those observations or authenticate their provenance. A PASS from that comparator is not an end-to-end host certification.

No end-to-end reliability benchmark across ChatGPT, Claude, Gemini, Copilot or local models is claimed. Test the exact host, tools and model version with harmless data before organizational use. The [technical overview](docs/TECHNICAL-OVERVIEW.md) describes the runtime boundary and remaining review responsibilities.

## Development and support

```console
python -m pip install -c requirements.lock .
python -m unittest discover -s tests
python build/build.py --check
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the supported build and test workflow, [SECURITY.md](SECURITY.md) for reporting a security issue, and [CHANGELOG.md](CHANGELOG.md) for release changes. The [remediation register](docs/REMEDIATION.md) maps the review findings to changes and validation.

Released under the [MIT License](LICENSE). No paid product or vendor account is required by the repository. External services have their own availability, access rules and data-processing terms.
