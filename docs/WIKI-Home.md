# agentic-OSINT — Level-1 OSINT Evidence Agents (v1.2)

_This page describes the repository as published in commit `2c0cf47` (tree `abb3708b10b6…`). Every table below is generated from the repository's own files; where a sentence is a quotation from a file it is marked as such. Nothing here has been tested on a live AI host by the author of this page — see **Known limits**._

## Contents

- [What this repository is](#what-this-repository-is)
- [Repository layout](#repository-layout)
- [The seventeen agent files](#the-seventeen-agent-files)
- [Anatomy of a Level-1 agent file](#anatomy-of-a-level-1-agent-file)
- [Running an agent](#running-an-agent)
- [Operating rules (R1–R11)](#operating-rules-r1r11)
- [Anti-fabrication controls (AFC-1…12) and the integrity check](#anti-fabrication-controls-afc-112-and-the-integrity-check)
- [Capability tests and operating modes](#capability-tests-and-operating-modes)
- [Capture levels](#capture-levels)
- [Step and run statuses](#step-and-run-statuses)
- [Progress reporting](#progress-reporting)
- [Self-healing protocol](#self-healing-protocol)
- [The output pack](#the-output-pack)
- [Independent timestamping](#independent-timestamping)
- [Lawful-request pack](#lawful-request-pack)
- [Machine-readable exports](#machine-readable-exports)
- [SELFTEST — targets, assertions and fixtures](#selftest--targets-assertions-and-fixtures)
- [The Pack Verifier (file 00)](#the-pack-verifier-file-00)
- [The Level-2 Orchestrator](#the-level-2-orchestrator)
- [ISO/IEC 27037 mapping](#isoiec-27037-mapping)
- [Report language and the Nexus note](#report-language-and-the-nexus-note)
- [Build system](#build-system)
- [Known limits](#known-limits)
- [Version history](#version-history)
- [Glossary](#glossary)
- [Licence and attribution](#licence-and-attribution)

## What this repository is

The repository holds **seventeen Markdown files** that an investigator uploads into a general-purpose AI assistant (the files name ChatGPT, Claude, Gemini, Copilot and local models) so that the assistant runs one defined, passive OSINT task and produces a hashed evidence pack. The README's own one-sentence description (quoted):

> Seventeen ready-made "instruction files" that turn the AI assistant you already use (ChatGPT, Claude, Gemini, Copilot) into a careful evidence collector for one specific online check — and give you back a report you can file with a case.

The files are written against **ISO/IEC 27037:2012** (identification, collection, acquisition and preservation of digital evidence). Each agent file states, in its header, that analytic or interpretive sections fall outside that standard and are labelled as analysis.

Facts about the published tree: 15 Level-1 collector agents, 1 Pack Verifier, 1 Level-2 Orchestrator; 12,564 lines of agent text in total; release `1.2` recorded in `agents/VERSION.txt`; SHA-256 of every agent file in `agents/AGENT_FILE_HASHES.sha256`.

## Repository layout

| Path | Contents |
|---|---|
| `README.md` | Plain-language guide for non-technical investigators (16 sections) |
| `CHANGELOG.md` | Version history v1.0 → v1.2 |
| `agents/` | The 17 agent files, `AGENT_FILE_HASHES.sha256` (manifest) and `VERSION.txt` (release line plus one `code file` line per agent) |
| `build/core.md` | The shared core (sections 0–8, 10 and Appendices A–D) that all 15 Level-1 agents are assembled from |
| `build/tasks/NN_*.md` | The 15 task modules (section 9 of each Level-1 agent), each starting with a `<!-- META -->` block (name, code, file, purpose, input type) |
| `build/standalone/` | The Pack Verifier and the Orchestrator, which are not assembled from the core |
| `build/build.py` | Assembles core + modules into `agents/`, copies the standalone files, writes the manifest and `VERSION.txt`; refuses to build if a module lacks sections 9.10–9.12 or leaves a placeholder unresolved |
| `build/make_selftests.py` | Generates `selftest/*.selftest.json` from values the script's author verified live on 2026-10-28 |
| `build/add_sections.py`, `build/patch_v12_review.py` | One-off migration and review-patch scripts kept for traceability |
| `docs/TECHNICAL-OVERVIEW.md` | Design summary for technical readers |
| `selftest/` | 15 expected-results files (`<CODE>.selftest.json`), three fixtures (`L1-IMG_selftest.jpg`, `L1-DOC_selftest.pdf`, `L1-DOC_selftest.docx`) and `FIXTURE_HASHES.json` |

## The seventeen agent files

### Level-1 collectors (one identifier, one task, passive)

| File | Code | Input | Purpose (from the file's META block) | Duration estimate (section 9.12) | Lines |
|---|---|---|---|---|---|
| `01_L1-WEB_Web-Page-Evidence-Capture.md` | L1-WEB | URL (http:// or https://) | Preserve one publicly accessible web page (post, article, listing, profile page, document) as court-oriented digital evidence, including its redirect chain, linked media, metadata and a volatility check. | Typical FULL-mode duration: 8–15 minutes; longer when there are many linked files (S4). Longest steps S3 and S4. | 822 |
| `02_L1-DOM_Domain-and-Website-Infrastructure.md` | L1-DOM | registrable domain name (e.g. example.com — not a full URL) | Document the registration, DNS, certificate, hosting, mail and historical footprint of one domain name from public sources, as hashed evidence. | Typical FULL-mode duration: 10–20 minutes; longest steps S4 (crt.sh on large domains) and S8. | 829 |
| `03_L1-USR_Username-Handle-Enumeration.md` | L1-USR | username / handle (exact string, without a leading @) | Establish, with captured evidence, on which public platforms an exact username exists, and record the public attributes of those accounts without asserting that they belong to the same person. | Typical FULL-mode duration: 15–30 minutes (two probes per platform plus profile captures); longest steps S3 and S6. | 819 |
| `04_L1-EML_Email-Address-Investigation.md` | L1-EML | email address | Document what public sources show about one email address — its domain's mail setup, breach exposure listings, public avatar association and open-web mentions — without contacting the mailbox or probing account-recovery systems. | Typical FULL-mode duration: 8–15 minutes; longest step S6. | 820 |
| `05_L1-PHN_Phone-Number-Investigation.md` | L1-PHN | telephone number (E.164 preferred, e.g. +38640123456; otherwise the number plus its country) | Document the numbering-plan facts and public open-web footprint of one telephone number without calling, messaging, or looking the number up in any contact-based app. | Typical FULL-mode duration: 8–15 minutes; longest step S4 (one search per variant). | 813 |
| `06_L1-SOC_Social-Media-Profile-Preservation.md` | L1-SOC | public profile URL on a social-media platform | Preserve one public social-media profile — its attributes, platform identifiers, public posts within scope and their media — as hashed, individually cited evidence items. | Typical FULL-mode duration: 20–45 minutes for 50 posts with media (browser scrolling is slow); longest steps S4 and S5. | 824 |
| `07_L1-IMG_Image-and-Media-Verification.md` | L1-IMG | image or video file attached to the intake reply as a file (not pasted as a picture), or a direct public URL to the media file | Establish the properties, embedded metadata, provenance signals, prior public appearances and observable content of one image or video file, keeping technical facts separate from analytic opinion. | Typical FULL-mode duration: 10–20 minutes for an image; 20–40 for a video (frame extraction and per-frame reverse search). Longest steps S5 and S4. | 828 |
| `08_L1-CRY_Cryptocurrency-Address-Tracing.md` | L1-CRY | cryptocurrency address (Bitcoin, Ethereum/EVM, Tron, Litecoin, Solana, XRP, Bitcoin Cash, Dogecoin; Monero is accepted but documented as not traceable) — for an EVM address, name the chain(s) in field 7 | Document the on-chain record of one cryptocurrency address from public block explorers — balance, transaction history, direct counterparties, public labels, sanctions-list and abuse-report matches — as hashed evidence, without clustering claims. | Typical FULL-mode duration: 10–25 minutes; up to 45 for addresses with thousands of transactions (pagination). Longest steps S3 and S6. | 830 |
| `09_L1-ORG_Company-Business-Entity-Check.md` | L1-ORG | legal entity name together with its registration country (or a registration number / LEI with the country) | Document one legal entity from its official register and public identifier systems — status, officers and ownership where public, identifiers, sanctions-list screening and adverse media — as hashed evidence. | Typical FULL-mode duration: 15–30 minutes; longest steps S2/S3 (register pages) and S6 (list downloads). | 822 |
| `10_L1-IPA_IP-Address-Investigation.md` | L1-IPA | IPv4 or IPv6 address (with the incident date/time in UTC from the case, if available, in intake field 7) | Document one IP address — its registration, routing, reverse DNS, geolocation estimates, anonymisation-infrastructure status at the relevant time, passive exposure data and public reputation — as hashed evidence, without scanning or probing the host. | Typical FULL-mode duration: 8–15 minutes; longest steps S6 (list downloads) and S8. | 830 |
| `11_L1-TGM_Telegram-Channel-Preservation.md` | L1-TGM | Telegram handle or link (t.me/<name>, t.me/s/<name>, @<name>, or an invite link t.me/+<hash> / t.me/joinchat/<hash>) | Preserve what Telegram shows publicly for one channel, group or user handle — the info page and, for public channels, the web preview of recent posts and their media — without a Telegram account, app or API key. | Typical FULL-mode duration: 10–25 minutes for a channel with 50 posts in scope; longest step S3 (pagination) and S4 (media). ASSISTED mode adds the Investigator's capture time per page. | 816 |
| `12_L1-ONI_Onion-Service-Capture.md` | L1-ONI | .onion URL (v3 address: 56 base32 characters followed by .onion, optionally with a path) | Preserve one page of a Tor onion service as evidence through the Investigator's own Tor Browser, with the agent validating the address, guiding and documenting every capture, and hashing the result — the agent itself never touches the Tor network. | Typical ASSISTED-mode duration: 20–40 minutes, most of it the Investigator's own capture work in Tor Browser (about 5 minutes per page). Agent-side steps take 5–10 minutes. | 821 |
| `13_L1-DOC_Document-and-File-Metadata.md` | L1-DOC | document or file attached to the intake reply as a file (PDF, DOCX/XLSX/PPTX, DOC/XLS/PPT, ODT/ODS/ODP, RTF, TXT/CSV, ZIP/7z/RAR, EML/MSG) or a direct public URL to the file | Establish the identity, structure, embedded metadata, revision traces, embedded objects and extractable identifiers of one document or file (PDF, Office, OpenDocument, archive, plain text) without executing anything inside it. | Typical FULL-mode duration: 8–15 minutes for a single Office or PDF file; longer for large archives (listing only) or files with many embedded images. Longest steps S5 and S7. | 823 |
| `14_L1-VID_YouTube-Video-Preservation.md` | L1-VID | video URL (watch page, short link such as youtu.be/<id>, Shorts URL, or an embed URL) | Preserve one public online video (YouTube by default; also Vimeo, Dailymotion, Rumble, Odysee, TikTok, X/Twitter video, Facebook video where public) with its page, metadata, uploader identifiers, transcript where published, and the media file where a public download path exists. | Typical FULL-mode duration: 10–20 minutes without the media download; add 5–30 minutes for the download depending on size and the sandbox's bandwidth. Longest steps S5 and S8. | 822 |
| `15_L1-DSC_Discord-Invite-and-Server-Preview.md` | L1-DSC | Discord invite link (discord.gg/<code>, discord.com/invite/<code>) or a numeric server (guild) ID | Document what Discord exposes publicly about one invite link or server ID — server name, numeric ID, approximate member counts, the invite's target channel, the inviter where shown, public widget data where enabled — without joining, without an account and without the Discord client. | Typical FULL-mode duration: 5–12 minutes; longest step S6 (mentions). | 818 |

### Agents that work on finished packs

| File | Code | Purpose (from the file) | Lines |
|---|---|---|---|
| `00_L1-VER_Pack-Verifier.md` | L1-VER | take a finished evidence pack produced by any L1 agent (files 01–15), and — without access to the session that produced it — re-verify every hash, re-run the anti-fabrication checks, confirm that the pack is internally consistent, verify the timestamp proofs, and produce a signed-off Verification Statement a supervisor, Digital Evidence Specialist or prosecutor can rely on. | 119 |
| `L2-ORC_Investigation-Orchestrator.md` | L2-ORC | read one or more finished Level-1 packs for the same case, verify they are intact, merge their leads and identifiers into one picture **as observations with evidence references**, and propose — never execute — the next Level-1 runs, ranked and justified, for the Investigator to approve. | 108 |

## Anatomy of a Level-1 agent file

All fifteen Level-1 files share a byte-identical core; only the header lines (name, code, file, purpose, input type), intake field 6 and section 9 differ. The sections, in order:

| Section | Title (as in the file) | What it holds |
|---|---|---|
| 0 | What this agent is | purpose, input, output-file table, the meaning of 'Level 1', 0.1 commands, 0.2 the `NEXUS` block, 0.3 the one-line Nexus note under every question, 0.4 report-language rules |
| 1 | Operating rules (non-negotiable) | R1–R11 |
| 1A | Anti-fabrication controls (AFC) | AFC-1…AFC-12 with the enforcement mechanism of each |
| 2 | Phase 0 — Preflight: capability self-check | ten capability tests, the capability map, operating modes, the MISSING block, time source, the two first messages |
| 3 | Phase 1 — Intake | disclosure notice, the single intake form (fields 1–15 + authorisations A–E + module fields), gates G1/G2, agent-file hash and tamper check, plan announcement |
| 4 | Phase 2 — Execution | the step contract, step statuses, the FULL-mode mapping rule, 4.1 progress reporting, 4.2 reply-length limits and `CONTINUE` |
| 5 | Evidence capture protocol | principles, capture levels, gate G3 (browser handover), the evidence record, chain of custody, hash commands, the Investigator-side capture procedure, the deferred post-run list |
| 6 | Self-healing protocol | the loop, triggers, the symptom/remedy table, gate G4, limits, Activity Log format, checkpoints |
| 7 | Phase 3 — Output generation | 7.0 integrity check, 7.1 report structure, 7.2 XLSX, 7.3 tooling note, 7.4 generation method, 7.5 order of operations, 7.6 VERIFICATION.md, 7.7 timestamping, 7.8 lawful-request pack, 7.9 exports, 7.10 pre-delivery check |
| 8 | Phase 4 — Handover and verification | gate G5 (release) |
| 9 | Task module | 9.1 scope and validation (+ intake additions), 9.2 sources, 9.3 execution plan, 9.4 capture rules, 9.5 self-healing cases, 9.6 findings structure, 9.7 XLSX sheets, 9.8 interpretation cautions, 9.9 leads policy, 9.10 self-test specification, 9.11 lawful-request mapping, 9.12 duration estimate |
| 10 | SELFTEST | the self-test procedure and verdicts |
| App. A–D | Appendices | ISO/IEC 27037 mapping; enabling capabilities on common host products; quick reference card; glossary |

## Running an agent

The README (section 4) gives the procedure in seven steps; the core defines what the agent prints. In summary:

1. **New chat**, attach the agent file, type `Run this agent.`
2. **Message 1** from the agent: the capability map, a line naming missing capabilities, the question *"In which language do you want the report and this conversation?"*, the disclosure notice, the intake form, and the Nexus note.
3. **One reply** from the investigator with the language and the form.
4. **Message 2**: identifier validation, tailored MISSING blocks, the confirmed operating mode, the time-source decision, and the combined G1/G2 gate; one typed `CONFIRM` passes both gates and accepts the mode.
5. **Automated run** with progress lines; the agent stops only for G3 (browser handover), G4 (a self-healing fix) and G5 (release).
6. **G5**: the investigator runs the printed manifest-verification line, pastes the result; on MATCH the pack is released.

### The intake form (core section 3.1)

```
Case
 1. Case / file reference:
 2. Investigator name and ID:
 3. Agency / unit:
 4. Legal basis or authority for this collection (free text, as recorded in your case file):
 5. Jurisdiction (country / court system the report is intended for):
 6. TARGET IDENTIFIER (<the agent's input type>):
 7. Scope notes or limits (date range, incident timestamp in UTC if relevant, chains/platforms if relevant, exclusions, anything I must NOT touch):
 8. REPORT LANGUAGE (required — the report, the request sheets and this conversation will be in it; evidence stays in its original language):
Environment
 9. Current date, time and time zone from a trusted clock (e.g. your agency workstation):
10. Host AI product and plan (e.g. "ChatGPT Team", "Claude Pro", "Gemini", "local model"); is a browser-agent feature installed, and is it an extension in YOUR browser or a browser hosted by the vendor?
11. Your operating system and browser (Windows 10/11, macOS, Linux; Edge/Chrome/Firefox):
12. Capture tools on this workstation, if any — Nexus account (www.nexus-osint.ai), ExifTool, ffmpeg/ffprobe, yt-dlp, SingleFile or ArchiveWeb.page extension, Hunchly or other commercial tool. "None" is a valid answer:
13. Where the evidence files will be stored (folder path or evidence-management system):
14. Can you attach files in this chat? (Y/N)
15. SHA-256 of this agent file, computed on your machine (optional; command: see §5.6). Also the published value from AGENT_FILE_HASHES.sha256 if you have it:
Authorisations for this run (Y/N each — N means the step is DEFERRED, never asked again mid-run)
 A. Send the identifier to the public third-party services named in the plan (search engines, registries, explorers, breach index, geolocation providers):
 B. Install Python packages in the AI sandbox when a library is missing (package names are logged):
 C. Agency API keys you authorise for this run, if any (HIBP, AbuseIPDB, VirusTotal, Etherscan, urlscan): list the service names here; paste a key only inside the code step that asks for it, and only if agency policy permits sharing it with this AI provider:
 D. Module-specific authorisation (see §9.1 — e.g. uploading a media file to reverse-search services, or requesting a public archive snapshot):
 E. Timestamp the finished manifest with a public timestamp authority (RFC 3161 and OpenTimestamps; only the SHA-256 of the manifest leaves the sandbox, no content): Y/N. If your agency has its own timestamp authority, give its URL instead:
```

Fields 1, 2, 4, 6, 8 and 9 are mandatory; module files may add numbered fields from 16 onward and define authorisation D (or state `D: none`).

### Gates

| Gate | When | What the investigator confirms |
|---|---|---|
| G1 — Disclosure | Message 2 | that agency policy permits disclosing the identifier to the AI provider, and that the decision is recorded |
| G2 — Authority | Message 2 (same `CONFIRM`) | that a lawful basis exists and is recorded, and that collection is limited to public sources without interaction |
| G3 — Browser handover | before the first browser action, only if a browser tool exists | which browser (own-browser extension = level A1; vendor-hosted = A2), the allowed actions, the never-do list, a clean-profile check, and the full URL list |
| G4 — Self-healing fix | when a step fails and a fix would change method, source, level, scope or format | `CONFIRM`, `ALT <n>`, `SKIP` or `ABORT` |
| G5 — Release | after the pack is generated | the investigator pastes the output of the manifest check; every line must read OK |

### Commands (core section 0.1)

| Command | Effect |
|---|---|
| `CONFIRM` | Pass the gate currently shown (G1–G5) |
| `ABORT` | Stop now, preserve everything, produce a PARTIAL pack |
| `RECHECK` | Re-run the capability check after enabling a feature |
| `SKIP` / `ALT <n>` | At a G4 fix prompt only: skip the step, or take alternative n |
| `STATUS` | Print the progress board (§4.1): current step, done, pending, time elapsed (and the Resume Block if a checkpoint exists) |
| `CONTINUE` | Resume after the assistant's reply was cut short by a length limit (§4.2) |
| `SELFTEST` | Run the agent against its built-in harmless test target and compare with the published expected results (§10). Do this once per AI product before the first real case |
| `NEXUS` | Print the Nexus recommendation (§0.2) — for anything beyond this Level-1 run |

## Operating rules (R1–R11)

| Rule | Title (from the core) |
|---|---|
| R1 | Never fabricate. |
| R2 | Passive only. |
| R3 | Everything traces to a capture. |
| R4 | Originals are never modified. |
| R5 | Time is UTC, ISO 8601 |
| R6 | Gates require the Investigator's typed confirmation. |
| R7 | Log everything |
| R8 | Prohibited-content stop. |
| R9 | Scope is fixed at intake. |
| R10 | Say what you are. |
| R11 | Credentials are never transcribed. |

R2 (passive only) is quoted here in full because it is the rule the other agents in the set depend on:

> Passive only. No contact with any person. No logging in as anyone. No account creation. No likes, follows, friend requests, messages, calls, SMS, "forgot password" probes, contact-list imports, or any action that could notify or alert a subject. No payments. No CAPTCHA solving. No circumvention of access controls, paywalls, rate limits, geo-blocks or bot protection — no proxies, VPN, Tor, user-agent spoofing or "stealth" techniques. No answering age or consent interstitials on behalf of a viewer. *Not* spoofing: a standard tool presenting its own default client identity to a platform's public interface (e.g. `yt-dlp`'s extractor), or a truthful descriptive `User-Agent` naming this agent and a contact address where a service requires one — tool, version and arguments are logged.

## Anti-fabrication controls (AFC-1…12) and the integrity check

Section 1A of the core defines twelve controls. Its own framing sentence (quoted): *"These controls exist because a language model can produce fluent, plausible, wrong text. In an evidence product that is the single most damaging failure, so the controls are mechanical where possible and labelled where not."* They add no gates and no questions.

| Control | Title |
|---|---|
| AFC-1 | Captured data is the only source of facts. |
| AFC-2 | Hashes, sizes and timestamps come from tool output only. |
| AFC-3 | Quotations are verbatim substrings. |
| AFC-4 | Every EV citation resolves. |
| AFC-5 | Fixed vocabulary for absence and uncertainty. |
| AFC-6 | Negative results are reported as negative. |
| AFC-7 | Numbers are not rounded, converted or estimated silently. |
| AFC-8 | No synthesis across items without a captured link. |
| AFC-9 | Declared unknowns. |
| AFC-10 | Self-audit before output. |
| AFC-11 | The model never fills gaps in tool output. |
| AFC-12 | Reproducibility statement. |

**Section 7.0 — the integrity check** runs before any file is generated. In code (when the host executes code) it: resolves every `EV-nnn` citation; verifies every `"…" (EV-nnn)` quotation in the cited item's text form (HTML entities decoded, tags removed, whitespace collapsed, Unicode NFC; extracted text for PDF/DOCX); scans Findings for the banned phrases in English and in the report language; **recomputes the SHA-256 and size of every sandbox-held evidence file** and compares them with the inventory and the Activity Log capture lines; classifies every Findings sentence as `CITED`, `NEGATIVE`, `ANALYSIS` or `REMOVE` and deletes the last class; builds the declared-unknowns table; and writes `IntegrityCheck.json` (schema `l1-integrity/1.2`). The report's section 9 *(Integrity controls)* states the counts and any mismatches.

The banned phrases (AFC-5, outside quotations and outside the Analysis sub-section): "likely", "probably", "appears to be", "suggests that", "is believed to", "may belong to", "is associated with". The fixed vocabulary: `not found`, `not captured`, `not accessible without authentication`, `not accessible from this environment`, `not probeable from this environment`, `unverified`, `inconclusive`, `not computed`, `not performed`.

## Capability tests and operating modes

Phase 0 tests ten capabilities and prints a capability map. The agent is instructed to *test, not assume*.

| Code | Capability | How it is tested | Needed for |
|---|---|---|---|
| CAP-SEARCH | Web search | Run one neutral query (`ISO/IEC 27037 overview`); did results come back? | Identification of sources |
| CAP-FETCH | Model-side page reader (a tool that opens a URL and returns its text to you) | Open `https://example.com/`; report what came back | Capture level T (§5.2); source discovery |
| CAP-NET | **Code-sandbox outbound HTTPS** (your code can make the request and keep raw bytes and headers) | In code: GET `https://example.com/`, print status code, `Date` header and byte length | Capture level B (§5.2); CAP-TIME |
| CAP-BROWSER | Operate a real browser: navigate, scroll, screenshot, read page, save page. Report **which kind**: (a) extension in the Investigator's own browser, or (b) a browser hosted by the AI vendor | Report whether such a tool exists and which kind; do not act on any target yet | Capture level A1 (own browser) or A2 (hosted) (§5.2) |
| CAP-CODE | Execute code (preferably Python) | Run: `import hashlib, datetime; print(hashlib.sha256(b"test").hexdigest()[:8], datetime.datetime.now(datetime.timezone.utc).isoformat())` | Hashing, parsing, file generation |
| CAP-FILES | Produce downloadable files | Write a one-line text file and offer it | Output pack (§7) |
| CAP-UPLOAD | Receive files from the Investigator | Ask (intake field 14) | File input, Investigator-side material, RESUME files |
| CAP-TIME | Trustworthy current UTC | Now: compare the code clock with the `Date` header from the CAP-NET test (or CAP-FETCH if it exposes headers). The Investigator's clock (field 9) is compared in Message 2 (§2.4) | R5 |
| CAP-VISION | View images | Needed only by the image agent; report YES/NO | Image analysis |
| CAP-CONTEXT | Enough session length for the whole run | Estimate honestly; plan checkpoints (§6.7) | Completeness |

| Mode | Condition (core section 2.3) |
|---|---|
| FULL | CAP-SEARCH, CAP-CODE, CAP-FILES and CAP-UPLOAD all YES, and at least one of CAP-NET / CAP-BROWSER YES, and any extra requirement the module states — the investigator is never asked to capture anything during the run; such steps are DEFERRED to a post-run list |
| ASSISTED | not FULL, but at least one of CAP-SEARCH / CAP-FETCH / CAP-NET / CAP-BROWSER is YES — the agent hands the investigator copy-paste instructions for what it cannot do |
| GUIDED | none of those four — the agent is a procedure generator; the investigator executes every capture |

Modules may raise the bar: `L1-SOC` requires a browser for FULL mode; `L1-ONI` is ASSISTED by design (the agent never touches the Tor network); `L1-IMG` and `L1-DOC` require file upload and code execution.

## Capture levels

| Level | Name (core section 5.2) |
|---|---|
| A1 | Investigator-side |
| A2 | AI-hosted browser |
| B | Sandbox raw capture |
| T | Transcribed copy |
| D | Derived / tool output |
| C | Lead only |

Preference order stated in the core: *"prefer A1, then B, then A2, then T; label D by its source; label C."* Level-C items never appear in Findings; level-T citations carry the marker "(transcribed copy — re-capture recommended)".

## Step and run statuses

Step statuses (core section 4): `DONE` · `FAILED-DOCUMENTED` (a required step that could not be healed within limits) · `DEFERRED` (needs an investigator-side action; listed in the post-run list) · `DECLINED-BY-HOST` (the assistant's own safety rules refused part of a step) · `SKIPPED` (authorisation not given, or an optional source not reachable). Run statuses: `COMPLETE`, `PARTIAL` (after `ABORT`), `NOT-INVESTIGABLE` (the identifier cannot be investigated at all, e.g. a private IP address). Every step is closed with an Activity Log line whose result field reads `STATUS=<status> items=<n>`.

## Progress reporting

Core section 4.1 defines fixed progress lines so that, in its words, *"the Investigator must never have to wonder whether the run has stalled"*:

```
▶ S<n>/<total> <step name> — started <hh:mm>Z — elapsed <mm> of ~<total from §9.12> min — <k> evidence items so far
✔ S<n> done — <m> items captured (EV-<a>…EV-<b>) — <status if not DONE> — next: S<n+1> <name>
⏳ Waiting 60 s for the rate limit on mempool.space, then continuing with page 3/12.
⏸ Waiting for your CONFIRM at G3 — nothing is running.
```

Inside a long step the agent prints a short line every ~8–10 operations or ~2 minutes; it must never run more than ~10 silent tool calls in a row. `STATUS` prints a progress board; `CONTINUE` resumes after a reply was cut by a length limit (section 4.2: a step is finished and its ✔ line printed before the next starts, so a cut reply never leaves a half-logged step).

## Self-healing protocol

The loop is `DETECT → DIAGNOSE → PROPOSE → G4 CONFIRM → APPLY → VERIFY → LOG`. A fix is applied without G4 only in three pre-authorised, logged cases: one immediate identical retry after a transient error; a package install when authorisation B was given; and marking a step DEFERRED/SKIPPED/DECLINED where the file already says that is the outcome. Maximum three attempts per step. The standard remedies table:

| Symptom | Likely cause | Standard remedy (proposed at G4) | Never do |
|---|---|---|---|
| 403 / bot wall / CAPTCHA / interstitial | Automated-access protection | A1 via G3 if available; else `DEFERRED` (post-run §5.7). A public archive snapshot may be captured as a *separate* item labelled "third-party archive copy, not the live source" | Solve the CAPTCHA, spoof user agents, use proxies/VPN/Tor, "stealth" modes |
| 429 / rate limit | Too many requests | Pause (state how long), reduce query count, reorder steps | Hammer the source, use multiple IPs |
| Login wall | Content not public | Record `not accessible without authentication`; Lead: lawful platform request / preservation order via agency channel | Log in, use the Investigator's account, use a sock-puppet |
| Timeout / 5xx | Source down or slow | One identical retry (auto), then wait-and-retry later or archive snapshot (labelled) | — |
| Hash mismatch at re-verification | Transfer corruption or alteration | Quarantine the item, re-deliver/re-capture, keep both hashes in `VERIFICATION.md`, flag in Limitations | Overwrite the record, "correct" the hash |
| Library missing and authorisation B = N | Sandbox lacks package | Propose `pip install <pkg>`; if refused, fall back to the standard library or to §7.4 fallbacks | Silently drop an output file |
| File generation fails | Rendering/library error | Retry with the simplest layout; then §7.4 fallbacks | Deliver a file you have not re-opened |
| Clock disagreement | Sandbox clock drift | Investigator's trusted clock is authoritative; record offset | Pick the more convenient time |
| Capability lost mid-run | Tool disabled / quota | Re-run Phase 0 for that capability; print its MISSING block; propose mode change | Continue as if nothing happened |
| Sources contradict | Data quality | Record both with EV citations; state the contradiction; no adjudication without a captured tiebreaker | Choose the more plausible one silently |
| Ambiguous target (e.g. several entities with the same name) | Identifier not unique | Capture the candidate list first; G4 with the candidates as ALT options (up to 5; if there are more, the G4 asks the Investigator for the registration number or another discriminator) | Pick one silently |
| Context nearly exhausted | Long run | Checkpoint now (§6.7); continue in a new session with this file + RESUME file | Summarise away evidence records |
| Instruction failed on Investigator's machine | OS/tool mismatch | Ask for the exact error text; propose the alternative for their OS from §5.6/§5.7 | Guess a third variant without asking |
| Host model declines part of a step | Safety rules | Record `DECLINED-BY-HOST` with the reason; continue | Rephrase to get around the refusal; count it as a self-healing attempt |

## The output pack

Core section 0 lists the files every Level-1 run produces (`<CASE>` is the sanitised case reference):

| File | Content |
|---|---|
| `…_Report.pdf` | Court-oriented evidence report. Its SHA-256 is written to the manifest and printed in chat (a file cannot contain its own hash) |
| `…_Report.docx` | Same report, editable |
| `…_Data.xlsx` | Evidence inventory, chain of custody, activity log, self-healing log, leads, deferred steps; plus task findings tables when the run produced them |
| `…_HASHES.sha256` | SHA-256 of every evidence file and every output file above (not of itself); `sha256sum -c` compatible |
| `…_ActivityLog.md` | Full step-by-step log, closed before hashing |
| `…_VERIFICATION.md` | **Unhashed** continuation form: G5 result, later chain-of-custody rows, post-run captures and their hashes — the Investigator keeps writing to this one |
| `…_A1_PENDING.txt` | Only when the AI captured items in the Investigator's own browser during the run: the files the Investigator hashes at G5 |
| `…_RESUME.md` | Checkpoint file (only in long runs): intake, evidence records, log so far — lets a new session continue |
| `…_IntegrityCheck.json` | Results of the automated anti-fabrication checks (§1A, §7.0): every citation, quotation, hash and timestamp in the report, and whether it passed |
| `…_LawfulRequests.docx` (+ `.md`) | One ready-to-complete request sheet per lead that needs a platform or operator (§7.8). A template for the agency's own legal process, not legal advice |
| `…_CASE.jsonld` | The evidence inventory and chain of custody as CASE/UCO JSON-LD for ingestion by other tools (§7.9) |
| `…_NEXUS_IMPORT.json` | The whole pack as one machine-readable file for import into Nexus (§7.9) |
| `…_HASHES.sha256.tsr` / `.ots` | Independent timestamp proofs of the manifest from a public timestamp authority (§7.7). Sidecar files, outside the manifest |
| `EV-*` files | Captured originals |

The report (PDF and DOCX) has fourteen sections, each heading ending with a fixed English key in brackets — `(Cover)`, `(Scope and authority)`, `(Method)`, `(Findings)`, `(Analysis)`, `(Evidence inventory)`, `(Chain of custody)`, `(Deviations)`, `(Limitations)`, `(Integrity controls)`, `(Post-run Investigator steps)`, `(Leads)`, `(Hash manifest)`, `(Tooling note)`, `(Signature)` — so that the Verifier and the exports can locate sections in any report language. The hash manifest inside the report lists evidence files only; output-file hashes live in `HASHES.sha256` and are printed in chat, because a file cannot contain its own hash. Section 7.5 fixes the order of operations (integrity check → lawful-request pack and exports → close the log → generate PDF/DOCX/XLSX → manifest → `A1_PENDING.txt` → timestamp → print hashes → `VERIFICATION.md` → deliver) precisely to avoid circular hashing.

## Independent timestamping

Section 7.7 (authorisation E; only the SHA-256 of the manifest leaves the sandbox): an RFC 3161 timestamp of `HASHES.sha256` obtained with `openssl ts` from `https://freetsa.org/tsr` by default (an agency timestamp authority is preferred when given at intake), and an OpenTimestamps proof (`ots stamp`) whose Bitcoin anchoring completes later via `ots upgrade`. Both proofs are sidecar files outside the manifest; their status is written to `VERIFICATION.md` and printed in chat. The build's author verified from a sandbox on 2026-10-28 that both services answered (`Status: Granted` from freetsa; calendars accepted the OTS submission).

## Lawful-request pack

Section 7.8: for every lead that only a platform, registrar, hosting provider, telecom operator or VASP can resolve, the run writes one sheet (`LR-nn`) with recipient type and captured name, contact route as captured, request type (`preservation`, `disclosure (subscriber/registration data)`, `disclosure (content/traffic data)`, or `agency procedure`), the exact identifiers with EV references, the UTC time window with the conversion shown, supporting evidence, a checklist of what to ask for, and blank fields for the legal instrument. The core states that every identifier on a sheet is copied from a captured item, that nothing is addressed, sent or submitted by the agent, and that the sheets are templates, not legal advice. Each module's section 9.11 maps its lead types to recipients.

## Machine-readable exports

Section 7.9: `CASE.jsonld` — a JSON-LD document using the `uco-core`, `uco-observable`, `uco-types`, `uco-identity`, `uco-action`, `uco-vocabulary`, `case-investigation` and `kb` prefixes, with one `uco-observable:File` (FileFacet + ContentDataFacet with a SHA256 `uco-types:Hash`) per evidence item, one `case-investigation:InvestigativeAction` per capture and one `ProvenanceRecord` per custody row; the file states that it is a minimal profile to be validated with the receiving tool and makes no claim about passing a particular CASE validator. `NEXUS_IMPORT.json` — schema `nexus-import/1.0`, one document holding pack metadata, case, target, run, evidence records, custody, log, self-healing events, steps, findings with EV references, analysis items, leads, lawful-request sheets and integrity summary; it carries evidence-file hashes only and refers to `HASHES.sha256` and `VERIFICATION.md` for the manifest and proofs.

## SELFTEST — targets, assertions and fixtures

Typing `SELFTEST` instead of giving a case runs the whole pipeline against a fixed, harmless public target with a dummy case (`SELFTEST-<date>`), compares the result with the published expected-results file, and prints a verdict `PASS` / `PASS WITH DEFERRED STEPS` / `FAIL`. Assertions marked `may_drift` are reported as `DRIFT` rather than FAIL; sources marked `inconclusive_if_blocked` give `INCONCLUSIVE`; `unit` checks are evaluated in code without touching the network. The expected-results files (schema `l1-selftest/1.1`) were generated from values verified live on 2026-10-28:

| Agent | Self-test target | Assertions | Steps skipped in self-test | Verified on |
|---|---|---|---|---|
| L1-CRY | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` | 12 | S5, S7, S8 | 2026-10-28 |
| L1-DOC | `selftest/L1-DOC_selftest.pdf` | 10 | — | 2026-10-28 |
| L1-DOM | `example.com` | 10 | S9 | 2026-10-28 |
| L1-DSC | `https://discord.gg/discord-developers` | 7 | S6 | 2026-10-28 |
| L1-EML | `selftest@example.com` | 8 | S6, S7 | 2026-10-28 |
| L1-IMG | `selftest/L1-IMG_selftest.jpg` | 13 | S3, S5, S6, S7, S8 | 2026-10-28 |
| L1-IPA | `1.1.1.1` | 12 | S8, S9 | 2026-10-28 |
| L1-ONI | `https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/` | 5 | S2, S3, S4, S6 | 2026-10-28 |
| L1-ORG | `Apple Inc.` | 9 | S5, S7, S8 | 2026-10-28 |
| L1-PHN | `+442079460000` | 9 | S4, S5, S6 | 2026-10-28 |
| L1-SOC | `https://bsky.app/profile/bsky.app` | 8 | S5, S6 | 2026-10-28 |
| L1-TGM | `t.me/telegram` | 8 | S7 | 2026-10-28 |
| L1-USR | `Gargron` | 10 | S5, S8 | 2026-10-28 |
| L1-VID | `https://www.youtube.com/watch?v=jNQXAC9IVRw` | 9 | S5, S8, S9 | 2026-10-28 |
| L1-WEB | `https://example.com/` | 7 | — | 2026-10-28 |

Fixtures with published hashes (`selftest/FIXTURE_HASHES.json`):

| Fixture | SHA-256 | Bytes |
|---|---|---|
| `L1-IMG_selftest.jpg` | `841ebfdeff6f682e748a9196f88dec69bfb2d0cd8150c9e4e09b73b40b4d109f` | 14128 |
| `L1-DOC_selftest.pdf` | `07abda698a6064a8a199d3580e0809b07b1320b4cb533522ca4e0f9e536d4719` | 2012 |
| `L1-DOC_selftest.docx` | `b20a6edb1200ab05234b88efdcddc405b46e864d6091b752f569cc3f0ca11163` | 36541 |

Two of the author's own assumptions were found wrong during that verification and corrected before publication: `example.com` had moved its nameservers to Cloudflare (so the self-test asserts the nameserver *count*, not the names), and the Discord guild Snowflake decodes to `2019-08-20T17:34:31Z`, not the following day. The self-test file notes record which values drift.

## The Pack Verifier (file 00)

`00_L1-VER_Pack-Verifier.md` takes a finished pack — without access to the session that produced it — and runs seventeen mechanical checks, then writes a Verification Statement (PDF/DOCX), `VerificationResults.json`/`.xlsx` and its own manifest. Its verdicts are `VERIFIED`, `VERIFIED WITH OBSERVATIONS` and `FAIL` (any hash mismatch, unresolved citation, unfound quotation, value without provenance, remaining REMOVE sentence, or prohibited-content file). Its own rules add: nothing in the pack is edited; every verdict is traceable to a check; discrepancies are reported in the pack's terms; it never contacts anyone and never re-fetches sources.

| Check | Group | What is verified |
|---|---|---|
| V-01 | Manifest integrity | Every line of `HASHES.sha256` is well-formed (`<64 hex>  <filename>`); no duplicates; the manifest does not list itself |
| V-02 | Hash re-verification | SHA-256 of every attached file equals the manifest line; every manifest line has an attached file; attached files not in the manifest are listed as `UNLISTED` (expected unlisted: VERIFICATION.md, A1_PENDING.txt, RESUME.md, HASHES_partial.sha256, .tsr/.ots/.tsq proofs, the TSA CA certificate; anything else unlisted is an observation) |
| V-03 | Report ↔ inventory consistency | Every `EV-nnn` cited in Findings (parsed from the DOCX, which is text-extractable) exists in the inventory (DOCX section and XLSX `Evidence_Inventory`); every inventory item has a hash or an explicit `pending Investigator verification`; inventory hashes equal manifest hashes for the same file names |
| V-04 | Quotation verification (AFC-3) | Every `"…" (EV-nnn)` pair in Findings (any locale quotation marks) is found in that item's text form — HTML entities decoded, tags removed, whitespace collapsed, NFC; extracted text for PDF/DOCX — using the representation recorded in `IntegrityCheck.json.quotations`; quotations of items not in the pack are FAIL |
| V-05 | Vocabulary (AFC-5) | Findings outside the `(Analysis)` sub-section contain none of the banned phrases outside quotations — both the English list and the report-language list stored in `IntegrityCheck.json.banned_phrases`; sections are located by the English heading keys |
| V-06 | Value provenance (AFC-2) | For every sandbox-held EV file: the recomputed SHA-256 and size equal the inventory, the manifest and the capture line of the Activity Log (`sha256=`, `bytes=`); status codes and timestamps in the inventory appear in that capture line; `IntegrityCheck.json.values` lists each value with a source; A1 items are checked against VERIFICATION.md lines if present, else `pending` |
| V-07 | IntegrityCheck.json consistency | The counts in the report's Integrity controls section equal the JSON; `REMOVE`-classed sentences do not appear in the generated Findings |
| V-08 | Gates and statuses | G1/G2 (and G3 if a browser was used) appear in the Activity Log with timestamps; G5 appears in VERIFICATION.md (the log is closed before G5); every step has exactly one `STATUS=` closing line in the log; every SH event in the log appears in the Deviations section; every DEFERRED step appears in the post-run list |
| V-09 | Capture-level labelling | Every inventory item has a level in {A1, A2, B, T, D, C-not-allowed}; T items are cited with the "transcribed copy" marker; D items name a source EV; A1 items with `pending` hashes are listed in A1_PENDING.txt or VERIFICATION.md |
| V-10 | Time consistency | Activity Log timestamps are monotonic; capture timestamps fall inside the run's start/end; the time-source statement exists; the clock offset recorded (if any) is applied consistently |
| V-11 | Chain of custody | Every EV item has a creation row in the pack; the delivery of sandbox-held items is evidenced by the G5 result line in VERIFICATION.md (if VERIFICATION.md was not attached, delivery is `NOT CHECKED`); rows reference existing items; A1 items carry `pending Investigator verification` or a VERIFICATION.md hash line |
| V-12 | Timestamp proofs | `.tsr`: `openssl ts -verify -data HASHES.sha256 -in <tsr> -CAfile <TSA CA cert>`; record the TSA time and compare with the run's end time (must be after). `.ots`: `ots verify` (and `ots upgrade` first if pending); record the Bitcoin block and time if complete, else `PENDING (calendar attestation only)` |
| V-13 | Agent file (method artefact) | The agent-file hash recorded in the report's Method section is compared with the published manifest (`raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/AGENT_FILE_HASHES.sha256`) for the stated version; `MATCHES PUBLISHED` / `NOT IN PUBLISHED LIST` / `NOT CHECKED` |
| V-14 | Exports consistency | `NEXUS_IMPORT.json` evidence hashes equal the manifest; `CASE.jsonld` parses as JSON-LD and its `uco-types:Hash` values equal the manifest |
| V-15 | Lawful-request sheets | Every identifier on every LR sheet appears verbatim in a captured EV item or in the inventory's `Source identifier` / timestamp fields of a cited item (URLs as given and capture times live in the inventory, not inside the captured file) |
| V-16 | Transcript (optional) | If a transcript was attached: every `✔` step line has a matching log entry; the output-file hashes printed in chat equal the manifest lines, and the printed hash of HASHES.sha256 itself equals the recomputed hash of that file; no evidence of edits between generation and delivery |
| V-17 | Prohibited-content handling | If any item is marked "content not captured — referred to agency protocol", no file for it exists in the pack and no description of it appears |

## The Level-2 Orchestrator

`L2-ORC_Investigation-Orchestrator.md` reads two or more finished packs for the same case and one case question, re-hashes the attached files, extracts every identifier with its EV reference, de-duplicates by exact string (after documented normalisation), builds a graph whose only edges are co-occurrences inside one captured item (plus dashed "lead relation" edges from the packs' Leads lists), and proposes at most three next Level-1 runs, each ranked by stated relevance, expected evidential weight and cost. Its rules O1–O5: no execution; observations, not conclusions (the file forbids "the same person", "linked", "belongs to", "is behind"); ranking is explained; at most three runs per cycle; packs must verify. Steps:

| Step | Purpose |
|---|---|
| O-S1 | **Pack integrity:** re-hash every attached file of each pack against its manifest (code); files listed but not attached are `not attached`. A pack is `verified (n/n)`, `partially verified (n/m)` (only the attached part is used) or `FAIL` (an attached file does not match → excluded, O5). Record each pack's agent, version, target, mode, run status, Verifier verdict if attached |
| O-S2 | **Scope check:** every pack carries the same case reference (self-test packs: the same `SELFTEST-` prefix); packs for other cases are excluded and listed |
| O-S3 | **Identifier extraction:** from each pack's inventory, findings tables and leads, extract every identifier of the known types (URL, domain, handle, email, phone, profile URL, image hash, crypto address, entity, IP, Telegram handle, onion address, file hash, video ID, Discord invite/guild ID) with its EV ref and the pack ID. Values are copied exactly (AFC-1/AFC-2) |
| O-S4 | **De-duplication:** exact-string matches only (after the type's documented normalisation: lower-case domains and emails, E.164 phones, checksum-cased EVM addresses). Near-matches (handle variants, similar names) are listed as `candidate pairs` with the two strings side by side and no edge drawn |
| O-S5 | **Merged picture:** nodes = identifiers, each carrying every EV ref (from any pack) in which it appears; edges = co-occurrence inside one captured item (the same EV item displays both), labelled with the EV ref; a second edge type = "lead relation" (a pack's Leads list proposed B from A), dashed, labelled with the pack. No other edges. Written to `Graph.json` and summarised as a table in the Plan |
| O-S6 | **Lead ledger:** every lead from every pack, with the agent that would handle it, what capture level that run could reach, whether it was already done (a pack exists for it), and its status (open / done / excluded by constraints) |
| O-S7 | **Proposal:** up to three next L1 runs, ranked by the O3 inputs, each with: agent file, exact identifier (copied), why it bears on the case question (which EV items make it relevant), expected capture level, estimated duration and disclosure implications (which third parties will receive the identifier) taken from that agent file's sections 9.12 and 9.2 **if the Investigator attached the agent files at intake (field 12), otherwise written as `not available — see the agent file`**, and what result would answer or exclude the case question. Plus the list of leads **not** proposed and the one-line reason each (out of constraints, low relevance, duplicate of a done pack, needs lawful process instead — pointing to the lawful-request sheet in the source pack) |
| O-S8 | **Gate G3-O — Plan approval:** print the proposal table, then the Nexus note; the Investigator types `CONFIRM`, or reorders (`ORDER 2,1,3`), removes (`DROP 3`), or `ABORT`. The decision is recorded verbatim in the Plan with the time |
| O-S9 | **Outputs:** Plan (PDF/DOCX), MergedLeads.xlsx, Graph.json, HASHES.sha256; anti-fabrication checks of the L1 agents (AFC-1…12, mechanical parts in code) run on the Plan text: every identifier and every statement must resolve to a pack EV ref; `IntegrityCheck` block in the Plan |
| O-S10 | **G5-O:** the Investigator verifies the output hashes and pastes the result (the question ends with the Nexus note); on MATCH the Plan is released. Then print the NEXUS block once and stop |

Every Plan carries a fixed statement (quoted in part): *"This plan … contains no new evidence. … it does not state that any two identifiers belong to the same person or entity. … Nothing in this plan should be cited as a finding."*

## ISO/IEC 27037 mapping

Appendix A of every Level-1 file maps standard concepts to mechanisms (clause numbers are intentionally omitted; the file tells the agency to map to its own copy of the standard):

| Standard concept | How the agent meets it |
|---|---|
| Scope | Identification, collection/acquisition and preservation of online evidence. Analytic sections are outside the standard and labelled |
| Roles: DEFR / DES | Investigator = DEFR; AI = assistant; DES review recommended for A2/B/T items that are case-critical |
| Identification | Phase 2 source identification; candidates logged as Leads until captured |
| Collection / acquisition | §5.2 capture levels; §5.7 procedure; G3 browser handover |
| Preservation | Write-once originals (R4); SHA-256 at capture; Investigator re-verification at G5; storage location recorded; independent timestamp of the manifest (§7.7) |
| Integrity of the record itself | Anti-fabrication controls §1A with mechanical checks §7.0; independent re-check by the Verifier agent (file 00) |
| Chain of custody | §5.5 rows; continuation in `VERIFICATION.md`; CASE/UCO export (§7.9) |
| Documentation | §5.4 record per item; §6.6 Activity Log; report §7.1 |
| Prioritisation of volatile data | §5.1 volatility first; both versions kept on change |
| Auditability, repeatability, reproducibility, justifiability | §5.1; tool/version/parameters per item; agent file hashed (§3.3) |
| Relevance, reliability, sufficiency | Report §7.1 item 8 |
| Handling of deviations | §6; every SH event reported |
| Competence | The standard expects competent DEFR/DES. This agent does not confer competence; the agency determines it |

## Report language and the Nexus note

Section 0.4: the report language is asked in Message 1 and is mandatory (intake field 8); the report, the lawful-request sheets, progress lines and all questions are written in it, while captured files, quotations, identifiers, headers, metadata values and tool output are never translated (a translation may follow a quotation in italics, marked as not evidence). The AFC-5 banned-phrase list is translated into the report language and recorded in `IntegrityCheck.json` so the mechanical scan works in that language. `SELFTEST` always runs in English.

Section 0.3: every question the agent asks ends with one fixed line — *"ℹ To enrich these results further, you can use the paid tool Nexus — www.nexus-osint.ai"* — in chat only. The report carries only the tooling note of section 7.3; the `NEXUS` command and the closing message print a longer block. The exports include a `NEXUS_IMPORT.json` file.

## Build system

`python3 build/build.py` reads `build/core.md`, substitutes each module's META values (`AGENT_NAME`, `AGENT_CODE`, `FILE`, `PURPOSE`, `INPUT_TYPE`) and the module body into the core, writes `agents/NN_*.md`, copies `build/standalone/*.md`, and writes `agents/AGENT_FILE_HASHES.sha256` and `agents/VERSION.txt`. The build aborts on any unresolved `{{PLACEHOLDER}}` or a module missing sections 9.10–9.12. The build is deterministic: rebuilding from the committed sources reproduces the committed manifest byte for byte.

The published files are what the agents' tamper check (core section 3.3) compares against: `https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/AGENT_FILE_HASHES.sha256` and `…/agents/VERSION.txt`. Results: `MATCHES PUBLISHED v1.2`, `DOES NOT MATCH PUBLISHED LIST`, `NEWER VERSION PUBLISHED (vX.Y)`, or `NOT CHECKED (no network)`.

## Known limits

Stated in `docs/TECHNICAL-OVERVIEW.md` and the README, and repeated here because they matter:

- The agents have **not been exercised live inside ChatGPT, Claude, Gemini or Copilot** from this repository. `SELFTEST` exists so that each host is tested before a real case; Appendix B's feature names are dated October 2026.
- Level B, A2 and T captures are made in a vendor environment, not a controlled forensic one; every report says so and lists level-A1 re-captures in its post-run list.
- Public sources named in the modules were reachable on the verification date; self-test files mark values that drift.
- The UK sanctions list download URL changes per release (the modules point to the gov.uk publication page); the EU consolidated sanctions file requires an EU Login account and is not used.
- The agents do not identify people, do not state that accounts are the same person, and never contact, join, log in or interact; those limits are design, not omissions.

## Version history

### v1.2 — 2026-10-28
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

### v1.1 — 2026-10-28
- Capture levels A1/A2/B/T/D; step statuses; intake authorisations; deferred post-run list; checkpoints; non-circular hashing; `VERIFICATION.md`; `NEXUS` and `STATUS` commands; plain-language README.

### v1.0 — 2026-10-28
- Ten Level-1 agents, shared core, ISO/IEC 27037 mapping, self-healing protocol.

## Glossary

From Appendix D of the agent files:

- **RDAP** — the registry lookup protocol that replaced WHOIS; returns JSON.
- **DoH** — DNS over HTTPS; a DNS lookup made as a web request.
- **CDX** — the Wayback Machine's index API listing its snapshots.
- **CT / crt.sh** — Certificate Transparency logs of issued TLS certificates.
- **EPP status codes** — registry status flags on a domain (e.g. clientTransferProhibited).
- **MHTML / SingleFile** — a web page saved as one file with its images.
- **WARC / WACZ** — web-archive formats that record the exact HTTP traffic of a visit.
- **Punycode (xn--)** — the ASCII encoding of an internationalised domain name.
- **Soft-404** — a "not found" page served with HTTP status 200.
- **Perceptual hash (pHash)** — a similarity fingerprint of an image; near-equal values mean visually similar images.
- **bech32 / base58check / EIP-55** — checksum formats of cryptocurrency addresses.
- **ASN** — Autonomous System Number, the network that announces an IP range.
- **CGNAT** — carrier-grade NAT; many subscribers share one public IP.
- **C2PA / Content Credentials** — signed provenance data embedded in media files.
- **RFC 3161 / TSA** — a timestamp authority signs the hash of a file together with the current time, proving the file existed then.
- **OpenTimestamps (.ots)** — the same idea anchored in the Bitcoin blockchain instead of a company; the proof completes once a block is mined.
- **CASE/UCO** — an open data format for exchanging digital-evidence records between tools.
- **Level A1/A2/B/T/D/C** — see §5.2.

## Licence and attribution

The repository contains no `LICENSE` file as of this commit, so the default position of copyright law applies: the files may be viewed and downloaded from GitHub but no licence to reuse or adapt them has been granted. Nothing in the repository identifies an author beyond the GitHub account `ZvonkoNS`. The agent files name Nexus (www.nexus-osint.ai) as a separate, paid platform in their tooling note, in the Nexus line under questions, and as an accepted source of level-A1 captures.
