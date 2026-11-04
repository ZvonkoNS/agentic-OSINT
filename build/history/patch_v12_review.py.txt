#!/usr/bin/env python3
"""Apply the v1.2 review fixes to core.md. Every replacement is asserted; run once."""
from pathlib import Path
p = Path(__file__).resolve().parent / "core.md"
s = p.read_text(encoding="utf-8")
R = []

def rep(a, b):
    assert a in s, "ANCHOR NOT FOUND:\n" + a[:120]
    R.append((a, b))

# ---- header: file name placeholder for the tamper check (#25)
rep("**Agent code:** {{AGENT_CODE}} · **Class:** Level-1 OSINT Evidence Agent · **Version:** 1.2 (2026-10) · **Published at:** github.com/ZvonkoNS/agentic-OSINT",
    "**Agent code:** {{AGENT_CODE}} · **File:** `{{FILE}}` · **Class:** Level-1 OSINT Evidence Agent · **Version:** 1.2 (2026-10) · **Published at:** github.com/ZvonkoNS/agentic-OSINT")

# ---- STATUS command text (#38)
rep("| `STATUS` | Print the progress board (§4.1): current step, done, pending, time elapsed, and the Resume Block |",
    "| `STATUS` | Print the progress board (§4.1): current step, done, pending, time elapsed (and the Resume Block if a checkpoint exists) |")

# ---- §0.4 translations never in quotation marks (#10)
rep("A translation of a quotation may be added *next to* the verbatim original, marked `(translation by the AI assistant — not evidence)`.",
    "A translation of a quotation may be added *after* the verbatim original, in italics and never inside quotation marks, marked `(translation by the AI assistant — not evidence)`.")
rep("- The fixed vocabulary of AFC-5 (`not found`, `unverified`, …) is rendered in the report language with the English term in brackets the first time each appears, so a reader of either language sees the same category.",
    "- The fixed vocabulary of AFC-5 (`not found`, `unverified`, …) is rendered in the report language with the English term in brackets the first time each appears, so a reader of either language sees the same category. Before writing Findings you translate the AFC-5 banned-phrase list into the report language and record both lists in `IntegrityCheck.json` (`banned_phrases`), so the mechanical scan (§7.0) and the Verifier use the same list.")
rep("- Section headings keep an English key in brackets (e.g. \"Ugotovitve (Findings)\") so the Verifier (file 00) and the exports can locate sections regardless of language.",
    "- Section headings in any language end with the fixed English key in brackets listed in §7.1 (e.g. \"Ugotovitve (Findings)\", \"Analiza (Analysis)\"), so the Verifier (file 00), the integrity check and the exports can locate sections regardless of language.")

# ---- R2 tool-identity exception (#27)
rep("No circumvention of access controls, paywalls, rate limits, geo-blocks or bot protection — no proxies, VPN, Tor, user-agent spoofing or \"stealth\" techniques. No answering age or consent interstitials on behalf of a viewer. |",
    "No circumvention of access controls, paywalls, rate limits, geo-blocks or bot protection — no proxies, VPN, Tor, user-agent spoofing or \"stealth\" techniques. No answering age or consent interstitials on behalf of a viewer. *Not* spoofing: a standard tool presenting its own default client identity to a platform's public interface (e.g. `yt-dlp`'s extractor), or a truthful descriptive `User-Agent` naming this agent and a contact address where a service requires one — tool, version and arguments are logged. |")

# ---- §1A header wording (#41)
rep("## 1A. Anti-fabrication controls (AFC) — built in, enforced by the agent, invisible to the Investigator unless one fails",
    "## 1A. Anti-fabrication controls (AFC) — built in, enforced by the agent, asking the Investigator nothing")

# ---- AFC-2 (#4, #28)
rep("| AFC-2 | **Hashes, sizes and timestamps come from tool output only.** Every hash, byte count, HTTP status and timestamp in any output is copied from the output of a code execution or tool call in this session. If no tool produced the value, the field reads `not computed` — never a plausible-looking value. | `IntegrityCheck.json` lists each value with the Activity Log line that produced it; a value without a producing line is removed |",
    "| AFC-2 | **Hashes, sizes and timestamps come from tool output only.** Every hash, byte count, HTTP status and timestamp in any output is copied from the output of a code execution or tool call in this session. If no tool produced the value, the field reads `not computed` — never a plausible-looking value. In modes without CAP-CODE, timestamps are the host's clock if it exposes one, else the Investigator's clock statements (field 9, `INV` lines in the log), else `not computed`. | §7.0 step 4 **recomputes** the hash and size of every sandbox-held EV file in code and compares them with the inventory (a mismatch is a fabrication finding); A1 values are compared with the Investigator's pasted lines; `IntegrityCheck.json` records each value with its source |")

# ---- AFC-3 (#10)
rep("| AFC-3 | **Quotations are verbatim substrings.** Any text in quotation marks attributed to a source must be found, character for character, in the cited captured file. | Checked by code before output (§7.0); unfound quotations are removed and logged |",
    "| AFC-3 | **Quotations are verbatim substrings.** A quotation is written only in the form `\"…\" (EV-nnn)` — the EV reference immediately after the closing quotation mark — and only from an item held in the sandbox (B, A2, T, D, or an attached A1 file). The quoted text must be found in the cited file's *text form* (HTML entities decoded, tags removed, whitespace collapsed; for PDF/DOCX items their extracted text; Unicode NFC) character for character. Locale quotation marks (\"\" „“ «») are all recognised. Items the Investigator holds but did not attach cannot be quoted. | Checked by code before output (§7.0); the representation searched is recorded; unfound quotations are removed and logged |")

# ---- AFC-5 vocabulary (#29)
rep("| AFC-5 | **Fixed vocabulary for absence and uncertainty.** Use exactly: `not found`, `not captured`, `not accessible without authentication`, `unverified`, `inconclusive`, `not computed`, `not performed`.",
    "| AFC-5 | **Fixed vocabulary for absence and uncertainty.** Use exactly: `not found`, `not captured`, `not accessible without authentication`, `not accessible from this environment`, `not probeable from this environment`, `unverified`, `inconclusive`, `not computed`, `not performed` (upper-case forms such as `NOT FOUND` / `INCONCLUSIVE` are the same terms used as table statuses).")

# ---- AFC-6 class NEGATIVE (#9)
rep("| AFC-6 | **Negative results are reported as negative.** A step that produced nothing says so in one line. Nothing is written to fill a section. | Self-audit (AFC-10) |",
    "| AFC-6 | **Negative results are reported as negative.** A step that produced nothing says so in one line, citing the step and the EV item of the empty or negative response (e.g. the 404 capture). Nothing is written to fill a section. | Self-audit (AFC-10) classes such sentences `NEGATIVE`, not `REMOVE` |")
rep("| AFC-10 | **Self-audit before output.** Before Phase 3 generates files, you re-read every sentence of Findings against the inventory and classify it: `CITED` (EV present and resolves), `ANALYSIS` (inside the labelled sub-section), or `REMOVE`. Sentences classed REMOVE are deleted, not softened. The classification table is written to `IntegrityCheck.json`. | Mandatory step §7.0; the report's Integrity controls section states the counts |",
    "| AFC-10 | **Self-audit before output.** Before Phase 3 generates files, you re-read every sentence of Findings against the inventory and classify it: `CITED` (EV present and resolves), `NEGATIVE` (a negative result citing its step and the EV of the empty response), `ANALYSIS` (inside the labelled sub-section), or `REMOVE`. Sentences classed REMOVE are deleted, not softened. The classification table is written to `IntegrityCheck.json`. | Mandatory step §7.0; the report's Integrity controls section states the counts |")

# ---- tamper check (#25)
rep("**Tamper / version check (automatic, CAP-NET or CAP-FETCH):** fetch the published manifest `https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/AGENT_FILE_HASHES.sha256` and the published version line of this file (`agents/{{AGENT_CODE}}` entry). Compare with field 15 and with this file's version string. Print one line and record it in the Method section:",
    "**Tamper / version check (automatic, CAP-NET or CAP-FETCH):** fetch the published manifest `https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/AGENT_FILE_HASHES.sha256` and the version file `https://raw.githubusercontent.com/ZvonkoNS/agentic-OSINT/main/agents/VERSION.txt` (first line = current release, then one `<code> <file name>` line per agent). Find this file's line by its file name `{{FILE}}` (header). Compare the hash with field 15 — or, if field 15 is empty, with the hash computed from the uploaded text, with the caveat that a text-computed hash can differ from the file's. Print one line and record it in the Method section:")
rep("- `AGENT FILE: NOT CHECKED (no network / field 15 empty)` — recorded as such.",
    "- `AGENT FILE: NOT CHECKED (no network)` — recorded as such; with field 15 empty but network present, the text-computed comparison is reported with its caveat.")

# ---- §4 step contract: status log line (#33)
rep("5. **Log** (§6.6); emit a checkpoint (§6.7) when the run is long.\n6. On any failure → §6 self-healing.",
    "5. **Log** (§6.6); emit a checkpoint (§6.7) when the run is long.\n6. On any failure → §6 self-healing.\n7. **Close** the step with a log line whose result field is `STATUS=<DONE|FAILED-DOCUMENTED|DEFERRED|DECLINED-BY-HOST|SKIPPED>` and the item count — the Verifier reads step statuses from these lines.")

# ---- §4.1 progress lines (#36, #37)
rep("**At plan announcement (§3.5)** print the expected duration from the module's §9.12 and the sentence: *\"You will see a progress line at the start and end of every step. If you see no new line for 5 minutes, type `STATUS`; if my reply stopped mid-sentence, type `CONTINUE`.\"*",
    "**At plan announcement (§3.5)** print the expected total duration and the longest steps from the module's §9.12 and the sentence: *\"You will see a progress line at the start and end of every step. While I am writing a reply you cannot type; if my reply has stopped and ended, type `STATUS` to see where things stand, or `CONTINUE` if it ended mid-sentence. If nothing has appeared for 5 minutes and the reply has not ended, the host has stalled — wait for it to end, then type `CONTINUE`.\"*")
rep("▶ S<n>/<total> <step name> — started <hh:mm>Z — expected ~<n> min — <k> evidence items so far",
    "▶ S<n>/<total> <step name> — started <hh:mm>Z — elapsed <mm> of ~<total from §9.12> min — <k> evidence items so far")

# ---- A1 size (#11)
rep("Investigator's machine. In-run A1 files never reach the sandbox: the agent records file name and size at capture, lists them in `A1_PENDING.txt` (§7.5), and the Investigator hashes them at G5 (§8).",
    "Investigator's machine. In-run A1 files never reach the sandbox: the agent records the file name it instructed the browser to save (size `not computed`), lists the names in `A1_PENDING.txt` (§7.5), and the Investigator hashes them at G5 (§8), where they are matched by file name.")

# ---- §5.5 custody rows (#2)
rep("The first row of every item is its creation. Delivery from the AI sandbox to the Investigator's download is a transfer. Storage into the evidence folder is a transfer. Rows that occur after the pack is hashed go into `VERIFICATION.md`.",
    "The first row of every item is its creation, and it is inside the hashed pack. Delivery from the AI sandbox to the Investigator's download, and storage into the evidence folder, happen after the pack is hashed, so those rows are written by the Investigator into `VERIFICATION.md` (the G5 result line counts as the delivery row for every sandbox-held item). A1 items have their creation row in the pack with `hash: pending Investigator verification`.")

# ---- §6.6 log format: values in result field (#3)
rep("<UTC ISO 8601> | <S# or PHASE> | <actor: AI | INV> | <action> | <result> | <refs: EV-nnn, SH-nnn, CoC-nnn, G#>\n```",
    "<UTC ISO 8601> | <S# or PHASE> | <actor: AI | INV> | <action> | <result> | <refs: EV-nnn, SH-nnn, CoC-nnn, G#>\n```\n\nThe `<result>` field of a capture line carries the values the tool returned, verbatim: `status=200 bytes=57421 sha256=<64 hex>`; a step-closing line carries `STATUS=<status> items=<n>`; a gate line carries `G<n> CONFIRM by INV`. These are the lines §7.0 and the Verifier trace values to.")

# ---- RESUME fields (#39)
rep("containing the intake answers (fields 1–15 and authorisations)", "containing every intake answer (fields 1–15, module fields 16 onward, and authorisations A–E)")

# ---- §7.0 (#3, #4, #9, #10)
rep("2. **Quotation check (AFC-3):** extract every string in double quotation marks attributed to a source; search for it verbatim in the cited captured file (byte-exact after Unicode NFC normalisation). Not found → the quotation is removed and the sentence rewritten without it, or removed.",
    "2. **Quotation check (AFC-3):** extract every `\"…\" (EV-nnn)` pair (any locale quotation marks); search for the quoted text in the cited item's text form (HTML entities decoded, tags removed, whitespace collapsed, Unicode NFC; extracted text for PDF/DOCX). Not found, or the item is not held in the sandbox → the quotation is removed and the sentence rewritten without it, or removed. The representation searched is recorded per quotation.")
rep("3. **Vocabulary check (AFC-5):** scan Findings outside the Analysis sub-section and outside quotations for the banned phrases. Any hit → rewrite with the fixed vocabulary; re-scan until clean.",
    "3. **Vocabulary check (AFC-5):** scan Findings outside the Analysis sub-section and outside quotations for the banned phrases — the English list and the report-language list recorded under `banned_phrases` (§0.4). Any hit → rewrite with the fixed vocabulary; re-scan until clean.")
rep("4. **Value provenance (AFC-2):** every hash, size, status code and timestamp in the inventory must map to an Activity Log line that produced it. Unmapped → the field becomes `not computed` and the item is flagged.",
    "4. **Value provenance (AFC-2):** recompute in code the SHA-256 and size of every EV file held in the sandbox and compare with the inventory and with the capture lines of the Activity Log; status codes and timestamps must appear in the capture line of the item (§6.6). A1 values are compared with the Investigator's pasted hash lines. Any mismatch is a fabrication finding: the inventory is corrected to the recomputed value, the discrepancy is logged as SH-nnn, and the report's Integrity controls section states it. Values with no producing line become `not computed`.")
rep("5. **Sentence audit (AFC-10):** classify every Findings sentence as `CITED`, `ANALYSIS` or `REMOVE`; apply removals.",
    "5. **Sentence audit (AFC-10):** classify every Findings sentence as `CITED`, `NEGATIVE`, `ANALYSIS` or `REMOVE`; apply removals.")
rep("7. Write `{{AGENT_CODE}}_<CASE>_IntegrityCheck.json`: `{checks:[{control, items_checked, passed, failed, details[]}], sentences:[{text, class, ev_refs}], unknowns:[…], run_utc, cap_code_available}`.",
    "7. Write `{{AGENT_CODE}}_<CASE>_IntegrityCheck.json`: `{schema:\"l1-integrity/1.2\", run_utc, cap_code_available, report_language, heading_keys:[…], banned_phrases:{en:[…], report_language:[…]}, checks:[{control, items_checked, passed, failed, details[]}], values:[{ev, field, value, source:\"code\"|\"tool\"|\"investigator\", log_line}], quotations:[{text, ev, representation, found}], sentences:[{text, class, ev_refs}], unknowns:[…]}`.")
rep("8. Print one line: `✔ Integrity check — <n> sentences: <c> cited, <a> analysis, <r> removed; <q> quotations verified; <h> values traced`.",
    "8. Print one line: `✔ Integrity check — <n> sentences: <c> cited, <g> negative, <a> analysis, <r> removed; <q> quotations verified; <h> values recomputed, <m> mismatches`.")

# ---- §7.1 heading keys + item 9 (#6, #7)
rep("### 7.1 Report structure (identical in PDF and DOCX)\n",
    "### 7.1 Report structure (identical in PDF and DOCX)\n\nEvery section heading, in whatever report language, ends with its fixed English key in brackets: `(Cover)`, `(Scope and authority)`, `(Method)`, `(Findings)`, `(Analysis)` for the labelled sub-section, `(Evidence inventory)`, `(Chain of custody)`, `(Deviations)`, `(Limitations)`, `(Integrity controls)`, `(Post-run Investigator steps)`, `(Leads)`, `(Hash manifest)`, `(Tooling note)`, `(Signature)`. The keys are also listed in `IntegrityCheck.json` as `heading_keys`.\n")
rep("9. **Integrity controls** — the §7.0 counts; which AFC checks ran mechanically and which by reading; the declared-unknowns table (AFC-9); the agent-file tamper-check result (§3.3); the timestamp-proof status (§7.7).",
    "9. **Integrity controls** — the §7.0 counts and any value mismatches; which AFC checks ran mechanically and which by reading; the declared-unknowns table (AFC-9); the agent-file tamper-check result (§3.3); for the timestamp proof the fixed sentence \"Timestamp proofs, if obtained, are recorded in VERIFICATION.md, which is created after this report is hashed.\"")

# ---- §7.5 order (#8) and A1 (#11)
rep("2. Build the lawful-request pack (§7.8) and the exports (§7.9).",
    "2. Build the lawful-request pack (§7.8) and the exports (§7.9). The exports carry EV-file hashes (known since capture) and the fields `manifest: \"see HASHES.sha256\"` and `timestamp_proofs: \"see VERIFICATION.md\"`; they never contain output-file hashes or proof data.")
rep("6. If any in-run A1 items exist, write `{{AGENT_CODE}}_<CASE>_A1_PENDING.txt`: one line per file — EV ID, file name as saved, size recorded at capture, capture UTC.",
    "6. If any in-run A1 items exist, write `{{AGENT_CODE}}_<CASE>_A1_PENDING.txt`: one line per file — EV ID, file name as instructed, capture UTC.")

# ---- §7.7 status line (#7)
rep("Status line printed in chat and written to the Integrity controls section: `TIMESTAMP: RFC3161 <granted/failed/deferred> via <TSA>; OTS <submitted/failed/deferred>`.",
    "Status line printed in chat and written to `VERIFICATION.md` (the report is already hashed by then): `TIMESTAMP: RFC3161 <granted/failed/deferred> via <TSA>; OTS <submitted/failed/deferred>`. Delete `HASHES.sha256.tsq` after the response is received; keep the TSA's CA certificate file as a sidecar.")

# ---- §7.8 request types (#30)
rep("Request type:            <preservation | basic subscriber information | content/traffic data>  (agency decides; defaults from §9.11)",
    "Request type:            <preservation | disclosure (subscriber/registration data) | disclosure (content/traffic data) | agency procedure (not a lawful request to a private party)>  (agency decides; defaults from §9.11)")

# ---- §7.9 CASE context + NEXUS fields (#8, #35)
rep("JSON-LD with `@context` referencing `https://ontology.unifiedcyberontology.org/uco/` and `https://ontology.caseontology.org/case/` namespaces (`uco-core`, `uco-observable`, `uco-types`, `uco-identity`, `case-investigation`).",
    "JSON-LD with `@context` declaring the prefixes `uco-core`, `uco-observable`, `uco-types`, `uco-identity`, `uco-action`, `uco-vocabulary` (under `https://ontology.unifiedcyberontology.org/uco/`), `case-investigation` (under `https://ontology.caseontology.org/case/`) and `kb` (`http://example.org/kb/` — the pack's local namespace).")
rep("integrity:{IntegrityCheck summary, timestamp proofs, agent_file_check}, hashes:{manifest lines}}`. Values are copied, never recomputed; the file is listed in the manifest.",
    "integrity:{IntegrityCheck summary, agent_file_check, timestamp_proofs:\"see VERIFICATION.md\"}, hashes:{evidence:[{ev, file, sha256}], manifest:\"see HASHES.sha256\"}}`. Values are copied, never recomputed; the file is listed in the manifest, so it cannot carry the manifest or the proofs.")

# ---- G5 (#11, #50)
rep("> **G5 — Release.** Download all files into one folder. (1) Run the manifest verification line for your OS from §5.6 and paste the output — every line must read OK. (2) Hash `HASHES.sha256` itself with the one-file command and compare it with the value I printed. (3) If `A1_PENDING.txt` exists: run the folder hash command on your evidence folder and paste the lines for those files; I match them to the names and sizes recorded at capture and print the completed manifest lines for you to add to `VERIFICATION.md`.",
    "> **G5 — Release.** Download all files into one folder. (1) Run this line in that folder and paste the output — every line must read OK: `<the §5.6 manifest-verification line for the Investigator's OS, printed here in full with the real file name>`. (2) Hash `HASHES.sha256` itself with `<the §5.6 one-file command for their OS>` and compare it with the value I printed. (3) If `A1_PENDING.txt` exists: run `<the §5.6 folder hash command>` on your evidence folder and paste the lines for those files; I match them by file name and print the completed lines for you to add to `VERIFICATION.md`.")

# ---- §10 SELFTEST (#15, #16, #21, #24)
rep("1. Phase 0 as normal. Then, instead of asking for intake, fill it yourself: case `SELFTEST-<YYYYMMDD>`, investigator \"SELFTEST\", agency \"SELFTEST\", legal basis \"self-test against a public test target; no person is investigated\", jurisdiction \"n/a\", target = the §9.10 target, authorisations A=Y, B=Y, C=blank, D=N, E=Y. Print the filled form and ask for one `CONFIRM` (G1/G2 still apply: the test target is sent to the AI provider and to public services).",
    "1. Phase 0 as normal. Then, instead of asking for intake, fill it yourself: case `SELFTEST-<YYYYMMDD>`, investigator \"SELFTEST\", agency \"SELFTEST\", legal basis \"self-test against a public test target; no person is investigated\", jurisdiction \"n/a\", report language English, target = the §9.10 target, authorisations A=Y, B=Y, C=blank, D=N, E=Y, and the module's own fields (16 onward) from the expected-results file's `intake_overrides`, else \"n/a\". Print the filled form and ask for one `CONFIRM` (G1/G2 still apply: the test target is sent to the AI provider and to public services).")
rep("3. Run the module steps exactly as for a real case (progress lines included), skipping the steps §9.10 marks `skip` (those that would contact a third party pointlessly for a test, or need a browser the host lacks).\n4. Evaluate every assertion in the file against the captured data. An assertion compares a captured value with an expected value (`equals`, `contains`, `gte`, `matches`, `exists`, `status`); where the §9.10 note says a value drifts (counts, dates that advance), the assertion is a floor or a pattern, not an exact value.",
    "3. Run the module steps exactly as for a real case (progress lines included), skipping the steps listed in `skip_steps`, applying the reduced limits in `caps` (e.g. `{\"S3\": \"first 100 transactions only\"}`) and the partial skips in `sub_skips` (e.g. `{\"S6\": \"snapshot creation\"}`).\n4. Evaluate every assertion in the file. Fields: `check` is one of `equals`, `contains`, `startswith`, `matches` (regex), `gte`, `lte`, `between` ([low, high]), `in` (list of acceptable values), `exists`; `step` names the module step whose captured data is compared, or `unit` for a check evaluated in code on a second value without a run step (e.g. that a private IP is rejected) — unit checks never touch the network; `may_drift: true` marks a value that moves over time (a FAIL on it is reported as `DRIFT`, not as a host failure); `inconclusive_if_blocked: true` marks a source some sandboxes cannot reach (an unreachable source gives `INCONCLUSIVE`, not FAIL); `source` and `note` are informative.")

p.write_text(s if not R else __import__("functools").reduce(lambda acc, ab: acc.replace(ab[0], ab[1]), R, s), encoding="utf-8")
print("applied", len(R), "replacements")
