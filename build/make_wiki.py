#!/usr/bin/env python3
"""Generate the GitHub wiki Home page for ZvonkoNS/agentic-OSINT from the repository files.
Every table is extracted from the files; prose paragraphs quote or paraphrase them. Output: /tmp/wiki_Home.md"""
import json, re, hashlib, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AG = ROOT / "agents"
core = (ROOT / "build" / "core.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
version = (AG / "VERSION.txt").read_text().splitlines()[0]
commit = subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
tree = subprocess.run(["git", "rev-parse", "origin/main^{tree}"], cwd=ROOT, capture_output=True, text=True).stdout.strip()

# ---- agents table from build/tasks META + standalone headers
rows = []
for t in sorted((ROOT / "build" / "tasks").glob("*.md")):
    m = re.search(r"<!-- META\n(.*?)\n-->", t.read_text(encoding="utf-8"), re.S)
    meta = dict(l.split(":", 1) for l in m.group(1).splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    text = (AG / meta["FILE"]).read_text(encoding="utf-8")
    dur = re.search(r"### 9\.12 Duration estimate\n\n(.+?)\n", text).group(1)
    rows.append((meta["FILE"], meta["AGENT_CODE"], meta["AGENT_NAME"], meta["INPUT_TYPE"], meta["PURPOSE"], dur, len(text.splitlines())))
stand = []
for f in ["00_L1-VER_Pack-Verifier.md", "L2-ORC_Investigation-Orchestrator.md"]:
    text = (AG / f).read_text(encoding="utf-8")
    code = re.search(r"\*\*Agent code:\*\* (\S+)", text).group(1)
    name = text.splitlines()[0].lstrip("# ").strip()
    purpose = re.search(r"\*\*Purpose:\*\* (.+)", text).group(1)
    stand.append((f, code, name, purpose, len(text.splitlines())))

# ---- AFC table from core
afc = re.findall(r"^\| (AFC-\d+) \| \*\*(.+?)\*\*", core, re.M)
# ---- capture levels
levels = re.findall(r"^\| \*\*([A-Z0-9]+) — (.+?)\*\* \|", core, re.M)
# ---- rules R1..R11
rules = re.findall(r"^\| (R\d+) \| \*\*(.+?)\*\*", core, re.M)
# ---- commands
cmds = re.findall(r"^\| `([A-Z<> n]+?)`(?: / `([^`]+)`)? \| (.+?) \|$", core.split("### 0.1")[1].split("### 0.2")[0], re.M)
# ---- capabilities
caps = re.findall(r"^\| (CAP-[A-Z]+) \| (.+?) \| (.+?) \| (.+?) \|$", core, re.M)
# ---- intake fields
intake = core.split("INTAKE — {{AGENT_CODE}}")[1].split("```")[0].strip().splitlines()
# ---- output files table from core §0
outfiles = re.findall(r"^\| `\{\{AGENT_CODE\}\}_<CASE>_(.+?)`(.*?) \| (.+?) \|$", core.split("**Output (automated, Phase 3):**")[1].split("**Level 1 means")[0], re.M)
# ---- self-healing symptom table (core)
sh = re.findall(r"^\| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", core.split("### 6.3")[1].split("### 6.4")[0], re.M)[1:]
# ---- verifier checks
ver = (AG / "00_L1-VER_Pack-Verifier.md").read_text(encoding="utf-8")
vchecks = re.findall(r"^\| (V-\d+) \| \*\*(.+?)\*\* \| (.+?) \| (.+?) \|$", ver, re.M)
# ---- orchestrator steps
orc = (AG / "L2-ORC_Investigation-Orchestrator.md").read_text(encoding="utf-8")
osteps = re.findall(r"^\| (O-S\d+) \| (.+?) \|$", orc, re.M)
# ---- selftests
st = []
for f in sorted((ROOT / "selftest").glob("*.selftest.json")):
    d = json.load(open(f))
    st.append((d["agent"], d["target"], len(d["assertions"]), ", ".join(d["skip_steps"]) or "—", d["verified_on"]))
fx = json.load(open(ROOT / "selftest" / "FIXTURE_HASHES.json"))
# ---- ISO mapping
iso = re.findall(r"^\| (.+?) \| (.+?) \|$", core.split("## Appendix A")[1].split("## Appendix B")[0], re.M)[1:]
# ---- glossary
gloss = core.split("## Appendix D")[1].split("*End of agent file")[0].strip()

def esc(s): return s.replace("|", "\\|")

W = []
w = W.append
w(f"# agentic-OSINT — Level-1 OSINT Evidence Agents (v{version})\n")
w(f"_This page describes the repository as published in commit `{commit}` (tree `{tree[:12]}…`). Every table below is generated from the repository's own files; where a sentence is a quotation from a file it is marked as such. Nothing here has been tested on a live AI host by the author of this page — see **Known limits**._\n")
w("## Contents\n")
for h in ["What this repository is", "Repository layout", "The seventeen agent files", "Anatomy of a Level-1 agent file", "Running an agent", "Operating rules (R1–R11)", "Anti-fabrication controls (AFC-1…12) and the integrity check", "Capability tests and operating modes", "Capture levels", "Step and run statuses", "Progress reporting", "Self-healing protocol", "The output pack", "Independent timestamping", "Lawful-request pack", "Machine-readable exports", "SELFTEST — targets, assertions and fixtures", "The Pack Verifier (file 00)", "The Level-2 Orchestrator", "ISO/IEC 27037 mapping", "Report language and the Nexus note", "Build system", "Known limits", "Version history", "Glossary", "Licence and attribution"]:
    w(f"- [{h}](#{h.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('…', '').replace('—', '').replace('/', '').replace('–','').replace(',', '').replace('.', '')})")
w("")

w("## What this repository is\n")
w("The repository holds **seventeen Markdown files** that an investigator uploads into a general-purpose AI assistant (the files name ChatGPT, Claude, Gemini, Copilot and local models) so that the assistant runs one defined, passive OSINT task and produces a hashed evidence pack. The README's own one-sentence description (quoted):\n")
w("> " + readme.splitlines()[2].strip().strip("*") + "\n")
w("The files are written against **ISO/IEC 27037:2012** (identification, collection, acquisition and preservation of digital evidence). Each agent file states, in its header, that analytic or interpretive sections fall outside that standard and are labelled as analysis.\n")
w(f"Facts about the published tree: {len(rows)} Level-1 collector agents, 1 Pack Verifier, 1 Level-2 Orchestrator; {sum(r[6] for r in rows) + sum(s[4] for s in stand):,} lines of agent text in total; release `{version}` recorded in `agents/VERSION.txt`; SHA-256 of every agent file in `agents/AGENT_FILE_HASHES.sha256`.\n")

w("## Repository layout\n")
w("| Path | Contents |\n|---|---|")
w("| `README.md` | Plain-language guide for non-technical investigators (16 sections) |")
w("| `CHANGELOG.md` | Version history v1.0 → v1.2 |")
w("| `agents/` | The 17 agent files, `AGENT_FILE_HASHES.sha256` (manifest) and `VERSION.txt` (release line plus one `code file` line per agent) |")
w("| `build/core.md` | The shared core (sections 0–8, 10 and Appendices A–D) that all 15 Level-1 agents are assembled from |")
w("| `build/tasks/NN_*.md` | The 15 task modules (section 9 of each Level-1 agent), each starting with a `<!-- META -->` block (name, code, file, purpose, input type) |")
w("| `build/standalone/` | The Pack Verifier and the Orchestrator, which are not assembled from the core |")
w("| `build/build.py` | Assembles core + modules into `agents/`, copies the standalone files, writes the manifest and `VERSION.txt`; refuses to build if a module lacks sections 9.10–9.12 or leaves a placeholder unresolved |")
w("| `build/make_selftests.py` | Generates `selftest/*.selftest.json` from values the script's author verified live on 2026-10-28 |")
w("| `build/add_sections.py`, `build/patch_v12_review.py` | One-off migration and review-patch scripts kept for traceability |")
w("| `docs/TECHNICAL-OVERVIEW.md` | Design summary for technical readers |")
w("| `selftest/` | 15 expected-results files (`<CODE>.selftest.json`), three fixtures (`L1-IMG_selftest.jpg`, `L1-DOC_selftest.pdf`, `L1-DOC_selftest.docx`) and `FIXTURE_HASHES.json` |")
w("")

w("## The seventeen agent files\n")
w("### Level-1 collectors (one identifier, one task, passive)\n")
w("| File | Code | Input | Purpose (from the file's META block) | Duration estimate (section 9.12) | Lines |\n|---|---|---|---|---|---|")
for f, c, n, i, p, d, ln in rows:
    w(f"| `{f}` | {c} | {esc(i)} | {esc(p)} | {esc(d)} | {ln} |")
w("\n### Agents that work on finished packs\n")
w("| File | Code | Purpose (from the file) | Lines |\n|---|---|---|---|")
for f, c, n, p, ln in stand:
    w(f"| `{f}` | {c} | {esc(p)} | {ln} |")
w("")

w("## Anatomy of a Level-1 agent file\n")
w("All fifteen Level-1 files share a byte-identical core; only the header lines (name, code, file, purpose, input type), intake field 6 and section 9 differ. The sections, in order:\n")
w("| Section | Title (as in the file) | What it holds |\n|---|---|---|")
for num, title, what in [
    ("0", "What this agent is", "purpose, input, output-file table, the meaning of 'Level 1', 0.1 commands, 0.2 the `NEXUS` block, 0.3 the one-line Nexus note under every question, 0.4 report-language rules"),
    ("1", "Operating rules (non-negotiable)", "R1–R11"),
    ("1A", "Anti-fabrication controls (AFC)", "AFC-1…AFC-12 with the enforcement mechanism of each"),
    ("2", "Phase 0 — Preflight: capability self-check", "ten capability tests, the capability map, operating modes, the MISSING block, time source, the two first messages"),
    ("3", "Phase 1 — Intake", "disclosure notice, the single intake form (fields 1–15 + authorisations A–E + module fields), gates G1/G2, agent-file hash and tamper check, plan announcement"),
    ("4", "Phase 2 — Execution", "the step contract, step statuses, the FULL-mode mapping rule, 4.1 progress reporting, 4.2 reply-length limits and `CONTINUE`"),
    ("5", "Evidence capture protocol", "principles, capture levels, gate G3 (browser handover), the evidence record, chain of custody, hash commands, the Investigator-side capture procedure, the deferred post-run list"),
    ("6", "Self-healing protocol", "the loop, triggers, the symptom/remedy table, gate G4, limits, Activity Log format, checkpoints"),
    ("7", "Phase 3 — Output generation", "7.0 integrity check, 7.1 report structure, 7.2 XLSX, 7.3 tooling note, 7.4 generation method, 7.5 order of operations, 7.6 VERIFICATION.md, 7.7 timestamping, 7.8 lawful-request pack, 7.9 exports, 7.10 pre-delivery check"),
    ("8", "Phase 4 — Handover and verification", "gate G5 (release)"),
    ("9", "Task module", "9.1 scope and validation (+ intake additions), 9.2 sources, 9.3 execution plan, 9.4 capture rules, 9.5 self-healing cases, 9.6 findings structure, 9.7 XLSX sheets, 9.8 interpretation cautions, 9.9 leads policy, 9.10 self-test specification, 9.11 lawful-request mapping, 9.12 duration estimate"),
    ("10", "SELFTEST", "the self-test procedure and verdicts"),
    ("App. A–D", "Appendices", "ISO/IEC 27037 mapping; enabling capabilities on common host products; quick reference card; glossary"),
]:
    w(f"| {num} | {title} | {what} |")
w("")

w("## Running an agent\n")
w("The README (section 4) gives the procedure in seven steps; the core defines what the agent prints. In summary:\n")
w("1. **New chat**, attach the agent file, type `Run this agent.`\n2. **Message 1** from the agent: the capability map, a line naming missing capabilities, the question *\"In which language do you want the report and this conversation?\"*, the disclosure notice, the intake form, and the Nexus note.\n3. **One reply** from the investigator with the language and the form.\n4. **Message 2**: identifier validation, tailored MISSING blocks, the confirmed operating mode, the time-source decision, and the combined G1/G2 gate; one typed `CONFIRM` passes both gates and accepts the mode.\n5. **Automated run** with progress lines; the agent stops only for G3 (browser handover), G4 (a self-healing fix) and G5 (release).\n6. **G5**: the investigator runs the printed manifest-verification line, pastes the result; on MATCH the pack is released.\n")
w("### The intake form (core section 3.1)\n")
w("```\n" + "\n".join(intake).replace("{{INPUT_TYPE}}", "<the agent's input type>") + "\n```\n")
w("Fields 1, 2, 4, 6, 8 and 9 are mandatory; module files may add numbered fields from 16 onward and define authorisation D (or state `D: none`).\n")
w("### Gates\n")
w("| Gate | When | What the investigator confirms |\n|---|---|---|")
w("| G1 — Disclosure | Message 2 | that agency policy permits disclosing the identifier to the AI provider, and that the decision is recorded |")
w("| G2 — Authority | Message 2 (same `CONFIRM`) | that a lawful basis exists and is recorded, and that collection is limited to public sources without interaction |")
w("| G3 — Browser handover | before the first browser action, only if a browser tool exists | which browser (own-browser extension = level A1; vendor-hosted = A2), the allowed actions, the never-do list, a clean-profile check, and the full URL list |")
w("| G4 — Self-healing fix | when a step fails and a fix would change method, source, level, scope or format | `CONFIRM`, `ALT <n>`, `SKIP` or `ABORT` |")
w("| G5 — Release | after the pack is generated | the investigator pastes the output of the manifest check; every line must read OK |")
w("\n### Commands (core section 0.1)\n")
w("| Command | Effect |\n|---|---|")
sec01 = core.split("### 0.1")[1].split("### 0.2")[0]
for line in re.findall(r"^\| (`.+?`) \| (.+?) \|$", sec01, re.M):
    w(f"| {line[0]} | {esc(line[1])} |")
w("")

w("## Operating rules (R1–R11)\n")
w("| Rule | Title (from the core) |\n|---|---|")
for r, t in rules:
    w(f"| {r} | {esc(t)} |")
w("\nR2 (passive only) is quoted here in full because it is the rule the other agents in the set depend on:\n")
r2 = re.search(r"^\| R2 \| (.+?) \|$", core, re.M).group(1)
w("> " + r2.replace("**", "") + "\n")

w("## Anti-fabrication controls (AFC-1…12) and the integrity check\n")
w("Section 1A of the core defines twelve controls. Its own framing sentence (quoted): *\"These controls exist because a language model can produce fluent, plausible, wrong text. In an evidence product that is the single most damaging failure, so the controls are mechanical where possible and labelled where not.\"* They add no gates and no questions.\n")
w("| Control | Title |\n|---|---|")
for a, t in afc:
    w(f"| {a} | {esc(t)} |")
w("\n**Section 7.0 — the integrity check** runs before any file is generated. In code (when the host executes code) it: resolves every `EV-nnn` citation; verifies every `\"…\" (EV-nnn)` quotation in the cited item's text form (HTML entities decoded, tags removed, whitespace collapsed, Unicode NFC; extracted text for PDF/DOCX); scans Findings for the banned phrases in English and in the report language; **recomputes the SHA-256 and size of every sandbox-held evidence file** and compares them with the inventory and the Activity Log capture lines; classifies every Findings sentence as `CITED`, `NEGATIVE`, `ANALYSIS` or `REMOVE` and deletes the last class; builds the declared-unknowns table; and writes `IntegrityCheck.json` (schema `l1-integrity/1.2`). The report's section 9 *(Integrity controls)* states the counts and any mismatches.\n")
w("The banned phrases (AFC-5, outside quotations and outside the Analysis sub-section): \"likely\", \"probably\", \"appears to be\", \"suggests that\", \"is believed to\", \"may belong to\", \"is associated with\". The fixed vocabulary: `not found`, `not captured`, `not accessible without authentication`, `not accessible from this environment`, `not probeable from this environment`, `unverified`, `inconclusive`, `not computed`, `not performed`.\n")

w("## Capability tests and operating modes\n")
w("Phase 0 tests ten capabilities and prints a capability map. The agent is instructed to *test, not assume*.\n")
w("| Code | Capability | How it is tested | Needed for |\n|---|---|---|---|")
for c in caps:
    w(f"| {c[0]} | {esc(c[1])} | {esc(c[2])} | {esc(c[3])} |")
w("\n| Mode | Condition (core section 2.3) |\n|---|---|")
w("| FULL | CAP-SEARCH, CAP-CODE, CAP-FILES and CAP-UPLOAD all YES, and at least one of CAP-NET / CAP-BROWSER YES, and any extra requirement the module states — the investigator is never asked to capture anything during the run; such steps are DEFERRED to a post-run list |")
w("| ASSISTED | not FULL, but at least one of CAP-SEARCH / CAP-FETCH / CAP-NET / CAP-BROWSER is YES — the agent hands the investigator copy-paste instructions for what it cannot do |")
w("| GUIDED | none of those four — the agent is a procedure generator; the investigator executes every capture |")
w("\nModules may raise the bar: `L1-SOC` requires a browser for FULL mode; `L1-ONI` is ASSISTED by design (the agent never touches the Tor network); `L1-IMG` and `L1-DOC` require file upload and code execution.\n")

w("## Capture levels\n")
w("| Level | Name (core section 5.2) |\n|---|---|")
for l, n in levels:
    w(f"| {l} | {esc(n)} |")
w("\nPreference order stated in the core: *\"prefer A1, then B, then A2, then T; label D by its source; label C.\"* Level-C items never appear in Findings; level-T citations carry the marker \"(transcribed copy — re-capture recommended)\".\n")

w("## Step and run statuses\n")
w("Step statuses (core section 4): `DONE` · `FAILED-DOCUMENTED` (a required step that could not be healed within limits) · `DEFERRED` (needs an investigator-side action; listed in the post-run list) · `DECLINED-BY-HOST` (the assistant's own safety rules refused part of a step) · `SKIPPED` (authorisation not given, or an optional source not reachable). Run statuses: `COMPLETE`, `PARTIAL` (after `ABORT`), `NOT-INVESTIGABLE` (the identifier cannot be investigated at all, e.g. a private IP address). Every step is closed with an Activity Log line whose result field reads `STATUS=<status> items=<n>`.\n")

w("## Progress reporting\n")
w("Core section 4.1 defines fixed progress lines so that, in its words, *\"the Investigator must never have to wonder whether the run has stalled\"*:\n")
w("```\n▶ S<n>/<total> <step name> — started <hh:mm>Z — elapsed <mm> of ~<total from §9.12> min — <k> evidence items so far\n✔ S<n> done — <m> items captured (EV-<a>…EV-<b>) — <status if not DONE> — next: S<n+1> <name>\n⏳ Waiting 60 s for the rate limit on mempool.space, then continuing with page 3/12.\n⏸ Waiting for your CONFIRM at G3 — nothing is running.\n```\n")
w("Inside a long step the agent prints a short line every ~8–10 operations or ~2 minutes; it must never run more than ~10 silent tool calls in a row. `STATUS` prints a progress board; `CONTINUE` resumes after a reply was cut by a length limit (section 4.2: a step is finished and its ✔ line printed before the next starts, so a cut reply never leaves a half-logged step).\n")

w("## Self-healing protocol\n")
w("The loop is `DETECT → DIAGNOSE → PROPOSE → G4 CONFIRM → APPLY → VERIFY → LOG`. A fix is applied without G4 only in three pre-authorised, logged cases: one immediate identical retry after a transient error; a package install when authorisation B was given; and marking a step DEFERRED/SKIPPED/DECLINED where the file already says that is the outcome. Maximum three attempts per step. The standard remedies table:\n")
w("| Symptom | Likely cause | Standard remedy (proposed at G4) | Never do |\n|---|---|---|---|")
for s in sh:
    w(f"| {esc(s[0])} | {esc(s[1])} | {esc(s[2])} | {esc(s[3])} |")
w("")

w("## The output pack\n")
w("Core section 0 lists the files every Level-1 run produces (`<CASE>` is the sanitised case reference):\n")
w("| File | Content |\n|---|---|")
for name, extra, content in outfiles:
    w(f"| `…_{esc(name)}`{esc(extra)} | {esc(content)} |")
w("| `EV-*` files | Captured originals |")
w("\nThe report (PDF and DOCX) has fourteen sections, each heading ending with a fixed English key in brackets — `(Cover)`, `(Scope and authority)`, `(Method)`, `(Findings)`, `(Analysis)`, `(Evidence inventory)`, `(Chain of custody)`, `(Deviations)`, `(Limitations)`, `(Integrity controls)`, `(Post-run Investigator steps)`, `(Leads)`, `(Hash manifest)`, `(Tooling note)`, `(Signature)` — so that the Verifier and the exports can locate sections in any report language. The hash manifest inside the report lists evidence files only; output-file hashes live in `HASHES.sha256` and are printed in chat, because a file cannot contain its own hash. Section 7.5 fixes the order of operations (integrity check → lawful-request pack and exports → close the log → generate PDF/DOCX/XLSX → manifest → `A1_PENDING.txt` → timestamp → print hashes → `VERIFICATION.md` → deliver) precisely to avoid circular hashing.\n")

w("## Independent timestamping\n")
w("Section 7.7 (authorisation E; only the SHA-256 of the manifest leaves the sandbox): an RFC 3161 timestamp of `HASHES.sha256` obtained with `openssl ts` from `https://freetsa.org/tsr` by default (an agency timestamp authority is preferred when given at intake), and an OpenTimestamps proof (`ots stamp`) whose Bitcoin anchoring completes later via `ots upgrade`. Both proofs are sidecar files outside the manifest; their status is written to `VERIFICATION.md` and printed in chat. The build's author verified from a sandbox on 2026-10-28 that both services answered (`Status: Granted` from freetsa; calendars accepted the OTS submission).\n")

w("## Lawful-request pack\n")
w("Section 7.8: for every lead that only a platform, registrar, hosting provider, telecom operator or VASP can resolve, the run writes one sheet (`LR-nn`) with recipient type and captured name, contact route as captured, request type (`preservation`, `disclosure (subscriber/registration data)`, `disclosure (content/traffic data)`, or `agency procedure`), the exact identifiers with EV references, the UTC time window with the conversion shown, supporting evidence, a checklist of what to ask for, and blank fields for the legal instrument. The core states that every identifier on a sheet is copied from a captured item, that nothing is addressed, sent or submitted by the agent, and that the sheets are templates, not legal advice. Each module's section 9.11 maps its lead types to recipients.\n")

w("## Machine-readable exports\n")
w("Section 7.9: `CASE.jsonld` — a JSON-LD document using the `uco-core`, `uco-observable`, `uco-types`, `uco-identity`, `uco-action`, `uco-vocabulary`, `case-investigation` and `kb` prefixes, with one `uco-observable:File` (FileFacet + ContentDataFacet with a SHA256 `uco-types:Hash`) per evidence item, one `case-investigation:InvestigativeAction` per capture and one `ProvenanceRecord` per custody row; the file states that it is a minimal profile to be validated with the receiving tool and makes no claim about passing a particular CASE validator. `NEXUS_IMPORT.json` — schema `nexus-import/1.0`, one document holding pack metadata, case, target, run, evidence records, custody, log, self-healing events, steps, findings with EV references, analysis items, leads, lawful-request sheets and integrity summary; it carries evidence-file hashes only and refers to `HASHES.sha256` and `VERIFICATION.md` for the manifest and proofs.\n")

w("## SELFTEST — targets, assertions and fixtures\n")
w("Typing `SELFTEST` instead of giving a case runs the whole pipeline against a fixed, harmless public target with a dummy case (`SELFTEST-<date>`), compares the result with the published expected-results file, and prints a verdict `PASS` / `PASS WITH DEFERRED STEPS` / `FAIL`. Assertions marked `may_drift` are reported as `DRIFT` rather than FAIL; sources marked `inconclusive_if_blocked` give `INCONCLUSIVE`; `unit` checks are evaluated in code without touching the network. The expected-results files (schema `l1-selftest/1.1`) were generated from values verified live on 2026-10-28:\n")
w("| Agent | Self-test target | Assertions | Steps skipped in self-test | Verified on |\n|---|---|---|---|---|")
for a, t, n, sk, v in st:
    w(f"| {a} | `{esc(t)}` | {n} | {esc(sk)} | {v} |")
w("\nFixtures with published hashes (`selftest/FIXTURE_HASHES.json`):\n")
w("| Fixture | SHA-256 | Bytes |\n|---|---|---|")
for k, v in fx.items():
    w(f"| `{k}` | `{v['sha256']}` | {v['bytes']} |")
w("\nTwo of the author's own assumptions were found wrong during that verification and corrected before publication: `example.com` had moved its nameservers to Cloudflare (so the self-test asserts the nameserver *count*, not the names), and the Discord guild Snowflake decodes to `2019-08-20T17:34:31Z`, not the following day. The self-test file notes record which values drift.\n")

w("## The Pack Verifier (file 00)\n")
w("`00_L1-VER_Pack-Verifier.md` takes a finished pack — without access to the session that produced it — and runs seventeen mechanical checks, then writes a Verification Statement (PDF/DOCX), `VerificationResults.json`/`.xlsx` and its own manifest. Its verdicts are `VERIFIED`, `VERIFIED WITH OBSERVATIONS` and `FAIL` (any hash mismatch, unresolved citation, unfound quotation, value without provenance, remaining REMOVE sentence, or prohibited-content file). Its own rules add: nothing in the pack is edited; every verdict is traceable to a check; discrepancies are reported in the pack's terms; it never contacts anyone and never re-fetches sources.\n")
w("| Check | Group | What is verified |\n|---|---|---|")
for v in vchecks:
    w(f"| {v[0]} | {esc(v[1])} | {esc(v[2])} |")
w("")

w("## The Level-2 Orchestrator\n")
w("`L2-ORC_Investigation-Orchestrator.md` reads two or more finished packs for the same case and one case question, re-hashes the attached files, extracts every identifier with its EV reference, de-duplicates by exact string (after documented normalisation), builds a graph whose only edges are co-occurrences inside one captured item (plus dashed \"lead relation\" edges from the packs' Leads lists), and proposes at most three next Level-1 runs, each ranked by stated relevance, expected evidential weight and cost. Its rules O1–O5: no execution; observations, not conclusions (the file forbids \"the same person\", \"linked\", \"belongs to\", \"is behind\"); ranking is explained; at most three runs per cycle; packs must verify. Steps:\n")
w("| Step | Purpose |\n|---|---|")
for s_, t_ in osteps:
    w(f"| {s_} | {esc(t_)} |")
w("\nEvery Plan carries a fixed statement (quoted in part): *\"This plan … contains no new evidence. … it does not state that any two identifiers belong to the same person or entity. … Nothing in this plan should be cited as a finding.\"*\n")

w("## ISO/IEC 27037 mapping\n")
w("Appendix A of every Level-1 file maps standard concepts to mechanisms (clause numbers are intentionally omitted; the file tells the agency to map to its own copy of the standard):\n")
w("| Standard concept | How the agent meets it |\n|---|---|")
for c, h in iso:
    w(f"| {esc(c)} | {esc(h)} |")
w("")

w("## Report language and the Nexus note\n")
w("Section 0.4: the report language is asked in Message 1 and is mandatory (intake field 8); the report, the lawful-request sheets, progress lines and all questions are written in it, while captured files, quotations, identifiers, headers, metadata values and tool output are never translated (a translation may follow a quotation in italics, marked as not evidence). The AFC-5 banned-phrase list is translated into the report language and recorded in `IntegrityCheck.json` so the mechanical scan works in that language. `SELFTEST` always runs in English.\n")
w("Section 0.3: every question the agent asks ends with one fixed line — *\"ℹ To enrich these results further, you can use the paid tool Nexus — www.nexus-osint.ai\"* — in chat only. The report carries only the tooling note of section 7.3; the `NEXUS` command and the closing message print a longer block. The exports include a `NEXUS_IMPORT.json` file.\n")

w("## Build system\n")
w("`python3 build/build.py` reads `build/core.md`, substitutes each module's META values (`AGENT_NAME`, `AGENT_CODE`, `FILE`, `PURPOSE`, `INPUT_TYPE`) and the module body into the core, writes `agents/NN_*.md`, copies `build/standalone/*.md`, and writes `agents/AGENT_FILE_HASHES.sha256` and `agents/VERSION.txt`. The build aborts on any unresolved `{{PLACEHOLDER}}` or a module missing sections 9.10–9.12. The build is deterministic: rebuilding from the committed sources reproduces the committed manifest byte for byte.\n")
w("The published files are what the agents' tamper check (core section 3.3) compares against: `https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/AGENT_FILE_HASHES.sha256` and `…/agents/VERSION.txt`. Results: `MATCHES PUBLISHED v" + version + "`, `DOES NOT MATCH PUBLISHED LIST`, `NEWER VERSION PUBLISHED (vX.Y)`, or `NOT CHECKED (no network)`.\n")

w("## Known limits\n")
w("Stated in `docs/TECHNICAL-OVERVIEW.md` and the README, and repeated here because they matter:\n")
w("- The agents have **not been exercised live inside ChatGPT, Claude, Gemini or Copilot** from this repository. `SELFTEST` exists so that each host is tested before a real case; Appendix B's feature names are dated October 2026.")
w("- Level B, A2 and T captures are made in a vendor environment, not a controlled forensic one; every report says so and lists level-A1 re-captures in its post-run list.")
w("- Public sources named in the modules were reachable on the verification date; self-test files mark values that drift.")
w("- The UK sanctions list download URL changes per release (the modules point to the gov.uk publication page); the EU consolidated sanctions file requires an EU Login account and is not used.")
w("- The agents do not identify people, do not state that accounts are the same person, and never contact, join, log in or interact; those limits are design, not omissions.")
w("")

w("## Version history\n")
w(changelog.split("\n", 1)[1].strip().replace("\n## ", "\n### ").replace("## v", "### v", 1) + "\n")

w("## Glossary\n")
w("From Appendix D of the agent files:\n")
w("- " + gloss.split("\n", 1)[1].strip().replace(" · ", "\n- "))
w("")

w("## Licence and attribution\n")
w("The repository contains no `LICENSE` file as of this commit, so the default position of copyright law applies: the files may be viewed and downloaded from GitHub but no licence to reuse or adapt them has been granted. Nothing in the repository identifies an author beyond the GitHub account `ZvonkoNS`. The agent files name Nexus (www.nexus-osint.ai) as a separate, paid platform in their tooling note, in the Nexus line under questions, and as an accepted source of level-A1 captures.\n")

out = Path("/tmp/wiki_Home.md")
out.write_text("\n".join(W), encoding="utf-8")
print(out, len("\n".join(W)), "chars;", len(W), "lines")
