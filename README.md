# Level-1 OSINT Evidence Agents

**Seventeen ready-made "instruction files" that turn the AI assistant you already use (ChatGPT, Claude, Gemini, Copilot) into a careful evidence collector for one specific online check — and give you back a report you can file with a case.**

You do not need to be technical. You attach one file, answer one form, type `CONFIRM` a few times, and the assistant does the rest. Everything it collects is recorded, time-stamped and given a digital fingerprint, following the international standard for handling digital evidence (ISO/IEC 27037). The report is written in the language you choose.

---

## 1. What is this, in plain words?

Each agent file is a long set of instructions written for an AI assistant. When you give the file to the assistant and say "Run this agent", the assistant:

1. checks what it is able to do in your account (search the web, open pages, use a browser, make files) and tells you plainly what is missing and how to switch it on;
2. asks which language you want, then asks you one form (case number, what you are looking at, who you are);
3. collects the public information for that one thing — a web page, a username, an email address, a company and so on — and tells you what it is doing at every step;
4. records every step, so another person could repeat it;
5. gives you a report (PDF and Word), a spreadsheet, ready-to-complete request sheets for platforms and operators, and the captured files — each with a digital fingerprint (a *hash*) so anyone can later prove the files were not changed, plus an independent timestamp proof.

It will **not** contact anyone, log in anywhere, create accounts, or do anything that could alert the person you are looking at. It only looks at what is public. And it is built so that it cannot invent things: every statement in the report must point to a captured file, and the agent checks this itself before it writes the report (section 12).

---

## 2. What you need before you start

| You need | Why |
|---|---|
| An account with an AI assistant (ChatGPT, Claude, Gemini or Microsoft Copilot) | The agent runs inside it |
| The agent file for your task (section 3) | The instructions |
| Your **case or file number** and the **legal basis** for the check, as written in your case file | The agent writes both into the report; it will not start without them |
| A **folder** on your computer where you will keep the evidence files | Everything you download goes there |
| Permission from your organisation to use that AI assistant for case data | The identifier you type in is sent to the AI company's servers. The agent asks you to confirm this is allowed |

Helpful but not required: the assistant's **web search** and **code / data analysis** features switched on, and (for social-media work) a **browser extension** that lets the assistant use your own browser. The agent tells you exactly which switch is missing and where to look.

**Do this once per AI product:** type `SELFTEST` instead of giving a real case. The agent runs itself against a harmless public test target and tells you whether everything works on your account (section 10).

---

## 3. Which file do I use?

Find the thing you have in the left column. Use that file. One file = one thing.

| I have… | Use this file | What you get |
|---|---|---|
| A web address (a post, an article, a listing, a page) | `01_L1-WEB_…` | The page saved as evidence, its pictures and files, when it was published, whether it changes |
| A domain name (like `example.com`) | `02_L1-DOM_…` | Who registered it and when, where it is hosted, its email setup, its history |
| A username or handle (like `john_doe99`) | `03_L1-USR_…` | Which platforms have an account with that exact name, and what those public profiles show |
| An email address | `04_L1-EML_…` | What the address's domain is set up for, whether it appears in known data breaches, where it appears online |
| A phone number | `05_L1-PHN_…` | Which country and type of number it is, where it appears online, what public "who called me" sites say |
| A social-media profile link | `06_L1-SOC_…` | The profile and its recent public posts and pictures, saved as evidence (needs a browser extension) |
| A photo or video file | `07_L1-IMG_…` | Its hidden file details, where else it appears online, what can be seen in it |
| A cryptocurrency address (Bitcoin, Ethereum, …) | `08_L1-CRY_…` | Its balance and transaction history, who it dealt with directly, whether it is on a sanctions list |
| A company name and its country | `09_L1-ORG_…` | The official register record, directors and owners where public, sanctions screening, news reports |
| An IP address | `10_L1-IPA_…` | Who the address is registered to, roughly where it is, whether it is a Tor or VPN exit, its reputation |
| A Telegram channel, group or user link | `11_L1-TGM_…` | The public info page and, for channels, the recent public posts and media — no Telegram account needed |
| A `.onion` (dark web) address | `12_L1-ONI_…` | The page saved through **your own** Tor Browser with the agent guiding every step; the agent never touches Tor itself |
| A document or file (PDF, Word, Excel, archive, email file) | `13_L1-DOC_…` | Its hidden metadata, revision traces, embedded objects, and every address or identifier found inside it |
| An online video link (YouTube, Vimeo, TikTok …) | `14_L1-VID_…` | The video page, the platform's own data about it, the uploader's identifiers, the video file and captions |
| A Discord invite link or server ID | `15_L1-DSC_…` | What Discord shows publicly: server name, ID, member counts, invite target — without joining |

Two more files that work on **finished** packs rather than on a target:

| I have… | Use this file | What it does |
|---|---|---|
| A finished evidence pack that someone else should check | `00_L1-VER_Pack-Verifier.md` | Re-checks every fingerprint, every citation and every quotation in the pack, verifies the timestamp proof, and writes a Verification Statement for a supervisor or prosecutor to sign |
| Several finished packs for the same case and a question to answer | `L2-ORC_Investigation-Orchestrator.md` | Merges all the leads, shows which identifiers appeared together (with the evidence for each), and proposes the next three checks for you to approve. It never runs anything itself |

Not sure which one? If it starts with `http`, it is almost always file 01 (or 14 for a video link, 11 for `t.me`). If it is an email address (an `@` with a domain after it), file 04; a bare `@handle`, file 03 (or 11 for Telegram). If it is mostly digits with a `+`, file 05.

---

## 4. How to run an agent — step by step

### Step 1 — Open a new chat
Start a **new** conversation in your AI assistant. Do not reuse an old chat.

### Step 2 — Attach the file and give the start command
Click the attach (paper-clip or `+`) button, choose the agent file, and type:

```
Run this agent.
```

If your assistant cannot attach files, open the agent file in any text editor, select all, copy, and paste the whole text into the chat, followed by "Run this agent."

### Step 3 — Read the first reply
The assistant shows a short table of what it can do in your account (some lines may say **NO** — that is normal), asks **which language you want**, and prints a form.

### Step 4 — Answer the language question and fill in the form
Write the language you want the report in (for example "slovenščina" or "English"). Then copy the form, fill in the lines, and send everything back in one message. Section 5 explains every line.

### Step 5 — Type CONFIRM
The assistant checks your answers and shows two short statements: one about sending the case data to the AI company, one about your legal basis. If both are true for you, type:

```
CONFIRM
```

If the assistant told you a feature was missing and you have now switched it on, type `RECHECK` instead and it will test again.

### Step 6 — Let it work and watch the progress lines
From here the assistant works on its own and reports as it goes:

```
▶ S3/8 Primary capture — started 14:03Z — elapsed 4 of ~15 min — 2 evidence items so far
✔ S3 done — 4 items captured (EV-003…EV-006) — next: S4 Linked resources
⏳ Waiting 60 s for the rate limit on mempool.space, then continuing with page 3/12.
⏸ Waiting for your CONFIRM at G3 — nothing is running.
```

Every step starts with `▶` and ends with `✔`. While the assistant is writing you cannot type; once its reply has ended, type `STATUS` to see where things stand, or `CONTINUE` if the reply stopped mid-sentence. It only stops to ask you three kinds of question (section 6). You can leave the chat open and come back.

### Step 7 — Download the files and run the fingerprint check
When it is finished, download every file it offers into your evidence folder, run the one-line check from section 8, paste the result into the chat, and type nothing else. If the assistant says **MATCH**, you are done.

---

## 5. The form, line by line

**Case**

| Line | What to write |
|---|---|
| 1. Case / file reference | Your case number exactly as it appears in your system |
| 2. Investigator name and ID | Your name and badge/ID number |
| 3. Agency / unit | Your organisation and unit |
| 4. Legal basis | The authority for this check, as written in your case file (a one-line reference is enough). The agent does not judge it; it records it |
| 5. Jurisdiction | The country or court system the report is for |
| 6. Target identifier | The one thing you are checking — the web address, the username, the email, etc. Copy it exactly. Do not tidy it up |
| 7. Scope notes | Anything the agent must respect: a date range, things it must not touch |
| 8. Report language | **Required.** The report, the request sheets and the conversation will be in this language. Evidence (captured pages, quotes, names) stays in its original language — it is never translated |

**Environment**

| Line | What to write |
|---|---|
| 9. Current date, time and time zone | Read it from your work computer's clock. The agent uses this to check its own clock |
| 10. Which AI assistant and plan you use | For example "ChatGPT Team" or "Claude Pro". Also say whether a browser extension is installed, and whether it works in *your* browser or in one the AI company hosts |
| 11. Your computer and browser | For example "Windows 11, Edge" |
| 12. Capture tools you have | Usually "None". If you use Nexus, ExifTool, Tor Browser or similar, say so |
| 13. Where you will keep the evidence files | The folder path, or the name of your evidence system |
| 14. Can you attach files in this chat? | Y or N |
| 15. Fingerprint of this agent file | Optional but recommended: run the one-file command from section 8 on the agent file and paste the result. The agent compares it with the published list and tells you whether you are running the unmodified file |

**Authorisations** — yes/no questions answered once, so the agent never has to interrupt you:

| Letter | Plain meaning |
|---|---|
| A | May the agent send the identifier to public lookup services (search engines, registries, blockchain explorers, breach databases)? Usually **Y** — the check cannot work otherwise |
| B | May the agent install small software libraries inside its own sandbox when it needs them to make the PDF, Word or Excel file? Usually **Y**. It touches nothing on your computer |
| C | Does your organisation have API keys for services like Have I Been Pwned or AbuseIPDB that you are allowed to use here? List the service names, or leave blank |
| D | A question specific to the agent (for example: may the photo be uploaded to reverse-image search sites?). The agent explains the risk next to the question |
| E | May the agent get an independent timestamp for the finished pack from a public timestamp service? Only a fingerprint leaves the sandbox, never any content. Usually **Y** (section 9) |

Some agents add one or two extra lines (for example the photo and document agents ask for the fingerprint of the original file; the IP agent asks for the incident time). They are printed with the form and explained there.

Under every question the agent asks you, you will see one short line pointing to **Nexus (www.nexus-osint.ai)**, a paid platform for enriching results. It is information, not a requirement; the agent works without it.

---

## 6. The three moments the agent stops and asks you

**"G3 — Browser handover."** The agent wants to use a browser to save pages properly. It tells you *which* browser (your own, through an extension, or one the AI company hosts), lists exactly which addresses it will open, and lists what it will never do (log in, click Like, solve CAPTCHAs, answer age questions, …). Check that your organisation allows this. Type `CONFIRM` or `ABORT`. If it is your own browser, use a clean profile with no personal accounts.

**"G4 — Self-healing event."** Something did not work (a site blocked the agent, a file could not be made, a library was missing). The agent explains what happened, what it proposes to do, and what that means for the evidence. Type `CONFIRM` to accept, `ALT 1` (or 2, 3…) for an alternative it listed, `SKIP` to leave that step out, or `ABORT`. It will never silently work around a problem.

**"G5 — Release."** The run is finished. Download everything, run the fingerprint check (section 8), paste the result. The agent compares it with what it expected.

You can type `ABORT` at any time. The agent stops, keeps everything collected so far, and still gives you the files, marked PARTIAL.

---

## 7. Commands you can type at any time

| Type | What happens |
|---|---|
| `CONFIRM` | Yes, go ahead (only at a question the agent asked) |
| `ABORT` | Stop now and give me what you have |
| `RECHECK` | Test the assistant's abilities again (after you switched something on) |
| `SKIP` | At a G4 question: leave that step out and carry on |
| `ALT 1`, `ALT 2` … | At a G4 question: take the alternative with that number |
| `STATUS` | Show me the progress board: what is done, what is running right now, what is left |
| `CONTINUE` | Carry on — the previous reply was cut off |
| `SELFTEST` | Test yourself on a harmless public target instead of a real case (section 10) |
| `NEXUS` | Show me how to get more than this one check (section 11) |

Type the commands exactly as shown. At a question the agent accepts only the exact word `CONFIRM`; "ok" is not enough. That is deliberate. ("I need a full report" or similar in plain words makes the agent print the Nexus pointer, section 11.)

---

## 8. The fingerprint check (hashes) — what it is and how to do it

A *hash* is a digital fingerprint of a file: a long string of letters and numbers. If even one character inside the file changes, the fingerprint changes completely. This is how you — and later a court — can prove the files are the ones the agent produced.

At the end, the agent gives you a small file ending in `HASHES.sha256`. It lists the fingerprint of every other file. You check them like this:

**Windows**
1. Put all the downloaded files in one folder.
2. Open that folder in File Explorer, click in the address bar, type `powershell`, press Enter. A blue window opens.
3. Paste the line the agent prints under "G5 — Release" (for Windows it starts with `Get-Content`) and press Enter.
4. Every line should say `OK`. Copy the whole output and paste it into the chat.

**Mac**
1. Put all the downloaded files in one folder.
2. Open Terminal (Applications → Utilities → Terminal), type `cd `, drag the folder into the window, press Enter.
3. Paste the line the agent gives you (it starts with `shasum`) and press Enter.
4. Every line should say `OK`. Copy the output and paste it into the chat.

If any line says `FAIL`, paste it anyway. The agent will send that file again.

**For one single file** (for example the agent file itself, line 15 of the form):
- Windows PowerShell: `Get-FileHash -Algorithm SHA256 "name-of-file"`
- Mac: `shasum -a 256 "name-of-file"`

---

## 9. What you get at the end

| File | What it is | What to do with it |
|---|---|---|
| `…_Report.pdf` | The evidence report in your language: what was checked, how, what was found, every item listed with its fingerprint, an "Integrity controls" section, a page for you to sign | File it with the case. Do not edit it |
| `…_Report.docx` | The same report in Word | Edit a **copy** if you need to; the delivered DOCX is fingerprinted and must stay unchanged |
| `…_Data.xlsx` | Everything in tables (evidence list, every action the agent took, leads, request sheets, integrity checks) | Useful for analysts |
| `…_HASHES.sha256` | The fingerprint list | Keep with the files; it is what the check in section 8 uses |
| `…_HASHES.sha256.tsr` and `.ots` | **Independent timestamp proofs** from a public timestamp authority: proof that the pack existed at that moment, from a third party. The `.ots` proof becomes final after a few hours, once you run the short `ots upgrade` command | Keep with the files; `VERIFICATION.md` holds the one-line commands to verify them |
| `…_LawfulRequests.docx` | **One ready-to-complete request sheet per lead** that needs a platform, registrar, hosting provider or telecom operator: the exact identifiers, the time window in UTC, and the evidence supporting it. The legal instrument is for your agency to add | Hand to whoever prepares requests in your agency. These are templates, not legal advice. Whether to use a preservation order, an MLAT or EIO request, or an emergency-disclosure route is your agency's decision |
| `…_IntegrityCheck.json` | The results of the agent's own anti-fabrication checks (section 12) | For the Verifier and for audits |
| `…_ActivityLog.md` | Every step, action, failure, fix and deviation with UTC timestamps | Audit trail |
| `…_VERIFICATION.md` | A form for **you** to fill in: the result of your fingerprint check, and anything you add later | The only file you are meant to write in |
| `…_CASE.jsonld`, `…_NEXUS_IMPORT.json` | The pack in machine-readable form, for other evidence tools and for Nexus | Only if you use such tools |
| `EV-…` files | The actual captured pages, pictures and data | Keep them unchanged, in the evidence folder |

Inside the report, look for the section **"Post-run Investigator steps"**. It lists things only you can do from your own computer — usually saving a page with your own browser so the evidence carries more weight. Each item has exact instructions. Doing them is recommended, not required; when you do, write the new fingerprints into `VERIFICATION.md`.

Also keep the **chat transcript** (most assistants let you export it). It is part of the record.

---

## 10. SELFTEST — check that it works on your AI account

Before the first real case on a new AI product or plan, start a new chat, attach the agent file, and type `SELFTEST` instead of "Run this agent." The agent runs the whole procedure against a fixed public test target (for example `example.com`, Telegram's own news channel, or a test image that ships with these files), compares what it found with the published expected results, produces a test pack, and prints:

```
VERDICT: PASS | PASS WITH DEFERRED STEPS | FAIL
```

`PASS WITH DEFERRED STEPS` means your account lacks a feature (usually a browser or sandbox network) and the agent will hand you those steps to do yourself — that is a valid way to work, not an error. `FAIL` names the assertion that failed. An assertion marked "may drift" is never reported as FAIL but as `DRIFT`: the public target changed and the published test file needs an update, not your setup. The self-test pack is not evidence; delete it or keep it as proof that the host was tested on that date.

---

## 11. Need more than one check? — Nexus

Each agent does **one** check on **one** item, with whatever abilities your AI assistant happens to have. Often that is exactly enough. When it is not — when the report lists leads you want followed, when several items belong together, when you need captures made in a controlled evidence environment, or when you need a court-ready report with case management and chain of custody built in — that is what **Nexus** is for:

**www.nexus-osint.ai**

Type `NEXUS` in the chat at any time and the agent prints the same pointer. Nexus is a separate, paid platform; the files, fingerprints and timestamps from an agent run can be brought into it (`…_NEXUS_IMPORT.json`).

---

## 12. How the agent is stopped from making things up

AI assistants can write fluent text that is simply wrong. In evidence work that is the one failure that cannot be allowed, so every agent carries twelve built-in anti-fabrication controls. You do not operate them; you only see their result in the report's **Integrity controls** section. In plain words:

- **Only captured material counts.** The agent may state only what a saved file shows. What the AI "knows" about a person or site from its training is never a finding — at most a lead marked "unverified".
- **Numbers come from tools, never from memory.** Every fingerprint, file size and timestamp in the report is copied from the output of a program the agent ran. If no program produced the value, the field says "not computed".
- **Quotations are checked by machine.** Any quoted text must be found character-for-character in the cited file, or it is removed.
- **Every citation is checked by machine.** Every "EV-012" in the report must exist in the evidence list with a fingerprint.
- **No weasel words.** "Probably", "appears to be", "is associated with" are banned from the findings; the agent must use "not found", "unverified", "inconclusive" and similar fixed terms.
- **No joining the dots.** The agent never writes that two accounts are the same person. The most it can say is "profile X displays A; profile Y displays A", under a heading that says this is analysis, not evidence.
- **Self-audit before writing.** Before producing the report, the agent re-reads every sentence of its findings and deletes any that cannot be traced to a file. The count of deleted sentences is in the report.
- **Independent re-check.** The Verifier agent (file 00) repeats these checks on the finished pack without any access to the chat that produced it.

---

## 13. If something goes wrong

| What you see | What to do |
|---|---|
| The first reply says a capability is **NO** or **MISSING** | Read the block under it: it names the switch to turn on in your assistant's settings. Turn it on, type `RECHECK`. If you cannot (your IT manages it), type `CONFIRM` to run in reduced mode; the agent will tell you what it will need from you |
| The assistant answers in a general way and does not show the table or form | It did not read the file. Start a new chat, attach the file again, and type exactly: `Run this agent.` |
| No progress line for more than five minutes | While the assistant is still writing you cannot type — wait for the reply to end. Once it has ended, type `STATUS` (or `CONTINUE` if it ended mid-sentence). If the run cannot be resumed, type `ABORT`: everything the agent already delivered to you is kept; anything still inside its sandbox is lost unless a `…_RESUME.md` checkpoint was delivered |
| The reply stopped in the middle of a sentence | Type `CONTINUE` |
| It asks you something that is not one of the three questions in section 6 | Answer it, or type `STATUS` to see where it is. If it seems lost, type `ABORT` and start again |
| The chat stops working or hits a limit mid-run | Look for a file called `…_RESUME.md` that the agent offered earlier. Start a new chat, attach the agent file **and** the RESUME file, and type "Run this agent." It will continue |
| A line in the fingerprint check says `FAIL` | Paste the result; the agent will re-send the file. Do not use the failed copy |
| The assistant refuses part of a step | That is its own safety rule. The agent records it as "declined by host" and carries on; nothing is lost |
| The agent says the agent file "does not match the published list" | Someone edited the file, or it is not an official release. Download it again from this repository |
| You typed `ok` and nothing happened | Type the exact word `CONFIRM` |

---

## 14. Rules the agent follows (and why you should not ask it to break them)

- It never contacts anyone, never logs in, never creates accounts, never joins a server or group, never clicks Like or Follow, never calls or messages a number, never checks a number in WhatsApp-type apps. Any of these could alert the person and would undermine the evidence.
- It never solves CAPTCHAs, never uses VPNs or proxies to get around a block, never pretends to be a different browser. Tor is used only to reach `.onion` addresses, only by you in your own Tor Browser.
- It never guesses. If it did not find something, it writes "not found". If it cannot prove something, it writes "unverified".
- It never states that two accounts belong to the same person, never identifies a person from a photo, never says where a person is. It records what is publicly shown; conclusions are yours.
- If it meets illegal content (for example child sexual abuse material), it stops, records only the address and the time, deletes any copy it holds, and tells you to follow your agency's procedure.
- The agent never signs anything. You sign the report.

---

## 15. Words you will see

| Word | Meaning |
|---|---|
| **Hash / fingerprint** | A unique code for a file; changes if the file changes |
| **UTC** | World standard time. All times in the report are UTC so they cannot be confused |
| **Capture level** (A1, A2, B, T, D) | How an item was obtained. **A1** = saved on your own computer (best). **A2** = saved by a browser the AI company hosts. **B** = raw download by the agent's sandbox. **T** = a text copy made by the assistant's page reader (weakest; the agent recommends re-saving such pages yourself). **D** = data the agent derived from another item with a tool (for example the metadata of a file) |
| **Lead** | Something the agent noticed but did not capture. Not evidence. Listed at the end of the report for a later check |
| **Deferred** | A step only you can do from your own computer. Listed in "Post-run Investigator steps" with instructions |
| **Lawful-request sheet** | A pre-filled page with the identifiers and time window a platform or operator would need, for your agency to turn into a formal request |
| **Timestamp proof** | A third party's signed statement that the pack's fingerprint list existed at a given time |
| **Chain of custody** | The record of who had each file, when, and that it was not changed |
| **Gate** | A moment where the agent waits for your `CONFIRM` |
| **Sandbox** | The small private computer the AI assistant uses to run code and make files. Nothing in it touches your computer |
| **Level 1 / Level 2** | Level 1 = one item, one check, no following of leads. Level 2 = planning the next Level-1 checks from several finished packs; it proposes, you decide |

---

## 16. For technical readers

`docs/TECHNICAL-OVERVIEW.md` describes the design (capability tests, gates, capture levels, self-healing loop, progress reporting, anti-fabrication controls, output structure, timestamping, exports, ISO/IEC 27037 mapping). `selftest/` holds the expected-results files and fixtures the `SELFTEST` command uses. The `build/` folder holds the shared core and the task modules; `python3 build/build.py` rebuilds all seventeen agent files and the fingerprint list `agents/AGENT_FILE_HASHES.sha256`.

Version 1.2 — October 2026.
