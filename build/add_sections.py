#!/usr/bin/env python3
"""Append §9.10 (self-test), §9.11 (lawful-request mapping) and §9.12 (duration) to the ten original modules.
Idempotent: skips a module that already has '### 9.10'."""
from pathlib import Path

T = Path(__file__).resolve().parent / "tasks"

ADD = {
"01_web.md": """
### 9.10 Self-test specification

Target: `https://example.com/` (IANA's reserved example domain; stable since 1999). Assertions: S2 final HTTP status `200`; redirect chain length `0`; S3 level-B capture has `<title>` = `Example Domain`; DNS A/AAAA answers for `example.com` have ≥ 1 record each (values drift); S4 linked resources count = `0` (the page has none); S6 Wayback availability returns `archived_snapshots.closest` (timestamp drifts; pattern `^\\d{14}$`); S7 volatility result `STABLE`; `skip: S6 snapshot creation`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Who published the page / account that posted it | the platform or hosting provider operating the site (from the captured host and headers; registrar/host via an L1-DOM follow-up) | preservation | URL as given, final URL, capture UTC, server `Date` header, page title | account/upload data, server logs for the URL in the window |
| Removed or changed content | the same | preservation | URL, both capture UTCs if CHANGED | content as it stood at the times cited |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longer when there are many linked files (S4). Longest steps S3 and S4.
""",
"02_domain.md": """
### 9.10 Self-test specification

Target: `example.com`. Assertions: RDAP HTTP 200 with `ldhName` = `EXAMPLE.COM`; RDAP registration event date = `1995-08-14T04:00:00Z`; RDAP nameservers list length ≥ 2 (names drift — in 2026 they are `elliott.ns.cloudflare.com` / `hera.ns.cloudflare.com`; assert the count, not the names); DoH NS answers from two resolvers agree; MX query returns the null MX `0 .` (RFC 7505) — assert that the MX answer set is either empty or exactly `0 .`; crt.sh returns ≥ 10 certificate rows; home page HTTP 200 with title `Example Domain`; `robots.txt` request returns a status (any); Wayback availability present. `skip: S9` (reputation sources not needed for the test).

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Registrant identity behind redacted RDAP data | registrar (name and IANA ID from RDAP; abuse contact as captured) | disclosure via lawful process | domain, registrar, RDAP capture UTC, registration date | registrant contact and payment data, registration logs |
| Site operator / content | hosting provider (netblock holder from S5; abuse contact from RDAP-IP) | preservation | domain, IP(s), ASN, capture UTC | hosting account data, access logs |
| Mail account data | mail provider (MX host operator from S6) | preservation | domain, MX hosts, UTC | account data for the mailbox named in the case |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–20 minutes; longest steps S4 (crt.sh on large domains) and S8.
""",
"03_username.md": """
### 9.10 Self-test specification

Target handle: `Gargron` (the founder account on mastodon.social; stable, public). Assertions: control probe on `mastodon.social` for a random handle returns `Record not found` (API) / NOT FOUND signature; target probe via `https://mastodon.social/api/v1/accounts/lookup?acct=Gargron` returns HTTP 200 with `username` = `Gargron`, `id` = `1`, `created_at` starting `2016-03-16`; Keybase lookup `https://keybase.io/_/api/1.0/user/lookup.json?usernames=chris` returns a user with `basics.username` = `chris` and the random-handle control returns no user; `dev.to/ben` returns HTTP 200 and `dev.to/<random>` returns 404; GitHub REST may be rate-limited or blocked from some sandboxes — if `api.github.com/users/octocat` is not reachable the assertion is `INCONCLUSIVE`, not FAIL. `skip: S5` (WhatsMyName), `skip: S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Account holder data for an existing profile | the platform (one sheet per platform with an EXISTS result that the case needs) | preservation | handle, profile URL, stable ID where captured, capture UTC | registration data, login IP logs, linked email/phone |
| INCONCLUSIVE platforms the case needs | the platform | preservation | handle, probe URL, UTC | confirmation of account existence and the above |

### 9.12 Duration estimate

Typical FULL-mode duration: 15–30 minutes (two probes per platform plus profile captures); longest steps S3 and S6.
""",
"04_email.md": """
### 9.10 Self-test specification

Target: `selftest@example.com`. Assertions: parse gives local part `selftest`, domain `example.com`, no plus-tag, not a role address; MX for `example.com` is the null MX `0 .` or empty → classification "domain does not advertise mail servers"; SPF TXT present or absent recorded (either is valid; drifts); RDAP summary registration date `1995-08-14T04:00:00Z`; disposable-list classification = not disposable; Gravatar avatar request for the MD5 of `selftest@example.com` returns HTTP 404; S5 is DEFERRED (no key) unless authorisation C provides one — with a key, the HIBP test address `account-exists@hibp-integration-tests.com` may be used instead and must return ≥ 1 breach; `skip: S6, S7`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Mailbox holder identity and logs | the mail provider (MX host operator for the domain; the domain's registrant for custom domains) | preservation, then disclosure | address as given, domain, MX hosts, capture UTC | account registration data, login IP logs, recovery contacts |
| Accounts registered with this address on platforms named in the case | each platform | preservation | address, platform, UTC | account existence and registration data |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longest step S6.
""",
"05_phone.md": """
### 9.10 Self-test specification

Target: `+442079460000` (a UK number in the Ofcom range reserved for drama use — it is assigned to nobody). Assertions: `phonenumbers` parse: valid = `True`, region `GB`, type `FIXED_LINE`, E.164 `+442079460000`, geocoder description `London`, time zone `Europe/London`; library version recorded; S2 regulator identified as Ofcom (gov/regulator domain `ofcom.org.uk`); S3 produces ≥ 5 search variants; `skip: S4, S5, S6` (no open-web sweep for a reserved number).

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Subscriber identity and current operator (number portability) | the original range holder from S1/S2 (who can state the current operator), then the current operator | disclosure via lawful process | E.164 number, original carrier, regulator range reference, UTC window from the case | subscriber data, porting history, CDRs where the legal basis allows |
| Messaging-app account on the number | the app operator | preservation | E.164 number, UTC | account existence and registration data |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longest step S4 (one search per variant).
""",
"06_social.md": """
### 9.10 Self-test specification

Target: `https://bsky.app/profile/bsky.app` (Bluesky's own account; public API, no login). Assertions: `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=bsky.app` HTTP 200 with `handle` = `bsky.app` and `did` = `did:plc:z72i7hdynmk6r22z27h6tvur`, `createdAt` starting `2023-04-12`; profile page HTTP 200; S4 post list: `https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=bsky.app&limit=10` returns ≥ 5 feed items, each with a `uri` starting `at://did:plc:z72i7hdynmk6r22z27h6tvur/` and an ISO `indexedAt`; stable ID (DID) recorded; `skip: S5, S6` (per-post captures and media not needed); S9 drift line printed. Without CAP-BROWSER the self-test runs in ASSISTED mode and this is expected — the verdict notes it.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Account holder identity, private content, deleted posts | the platform | preservation, then disclosure | handle, stable account ID (numeric ID / DID / channel ID), canonical profile URL, post permalinks, UTC window | registration data, login IP logs, content of listed posts, deleted content within retention |
| Media that could not be captured | the platform | preservation | post permalinks, media URLs as captured | the media files |

### 9.12 Duration estimate

Typical FULL-mode duration: 20–45 minutes for 50 posts with media (browser scrolling is slow); longest steps S4 and S5.
""",
"07_image.md": """
### 9.10 Self-test specification

Target: the repository fixture `selftest/L1-IMG_selftest.jpg` (SHA-256 `841ebfdeff6f682e748a9196f88dec69bfb2d0cd8150c9e4e09b73b40b4d109f`, MD5 `c299389a69536b1c2a7595784bc68c8d`, 14128 bytes), attached by the Investigator or fetched from the repository. Assertions: sandbox copy SHA-256 equals the published value (if it does not, the host altered the upload — that is itself the test result: report `UPLOAD ALTERED`, and compare the Investigator's local hash instead); format JPEG, dimensions `640×400`; EXIF `Make` = `L1-SELFTEST-CAMERA`, `Model` = `MODEL-27037`, `Artist` = `L1 SELFTEST`, `DateTimeOriginal` = `2026:10:28 09:00:00`; GPS latitude ref `N`, latitude `51° 30' 28.80"`, longitude ref `W`; perceptual hash computed (any value); `skip: S3, S5, S6, S7, S8` (no uploads to third parties; vision opinion not tested).

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Original upload of the image and the uploading account | the platform or site where the image appeared (from S5 appearances or the case) | preservation | result URL(s), image SHA-256 and perceptual hash, capture UTC | original file as uploaded, uploader account data |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–20 minutes for an image; 20–40 for a video (frame extraction and per-frame reverse search). Longest steps S5 and S4.
""",
"08_crypto.md": """
### 9.10 Self-test specification

Target: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` (the Bitcoin genesis-block coinbase address). Assertions: chain `BTC`, format P2PKH, base58check valid; mempool.space summary HTTP 200 with `chain_stats.spent_txo_count` = `0` and `chain_stats.funded_txo_count` ≥ `80000` and `chain_stats.tx_count` ≥ `60000` (values only grow); second explorer (blockchain.info `rawaddr`) HTTP 200 with `n_tx` ≥ `60000`; earliest transaction in the export is in block `0` with timestamp `2009-01-03T18:15:05Z`; OFAC SDN list file downloaded (HTTP 200) and the address string not found in it → `NO MATCH`; `skip: S3 beyond the first 100 transactions, S5, S7, S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Owner of a counterparty address labelled as an exchange/service | the labelled VASP (name as captured from the explorer label — the agency verifies the entity) | preservation, then disclosure | the labelled address, the transaction IDs linking it to the target, UTC block times, amounts in native units | KYC data of the account that controls the address, deposit/withdrawal records for the listed transactions |
| Target address controlled by a service (label on the target itself) | that VASP | the same | target address, label EV, tx IDs | the same |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–25 minutes; up to 45 for addresses with thousands of transactions (pagination). Longest steps S3 and S6.
""",
"09_company.md": """
### 9.10 Self-test specification

Target: `Apple Inc.`, country `US` (field 16), LEI `HWUPKR0MPOU8FGXBT394` (field 17). Assertions: GLEIF record HTTP 200 with `attributes.lei` = `HWUPKR0MPOU8FGXBT394`, `entity.legalName.name` = `Apple Inc.`, `entity.jurisdiction` = `US-CA`, `registration.status` = `ISSUED`; official register identified as SEC EDGAR for a US listed company with CIK `0000320193` (EDGAR company page HTTP 200 via `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193` — EDGAR requires a descriptive `User-Agent` header with contact email; the self-test uses `agentic-OSINT selftest (selftest@example.com)`); OFAC, UN and UK list files downloaded and the exact string `APPLE INC` screened → `NO MATCH` or `POTENTIAL MATCH (requires human review)` both acceptable (false positives on common words are expected and are the point of the review rule); `skip: S5 (VIES; not an EU entity), S7, S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Documents behind a register paywall or requiring authenticated access | the official register (name as captured) | documents request under agency procedure (not a lawful request to a private party) | registration number, legal name, document list captured | the listed filings |
| Officers/owners named in the record (persons) | — | not a lawful-request lead; a separate run under its own legal basis | — | — |
| Bank/payment relationships named in filings | the named institution | preservation | entity name, registration number, filing reference | account data (where the legal basis allows) |

### 9.12 Duration estimate

Typical FULL-mode duration: 15–30 minutes; longest steps S2/S3 (register pages) and S6 (list downloads).
""",
"10_ip.md": """
### 9.10 Self-test specification

Target: `1.1.1.1` with incident timestamp `2026-01-01T00:00:00Z` (field 16). Assertions: classification public/global; RDAP (rdap.org → APNIC) HTTP 200 with `name` = `APNIC-LABS` and range `1.1.1.0`–`1.1.1.255`; RIPEstat prefix-overview `asns[0].asn` = `13335` and prefix `1.1.1.0/24`; routing history at the incident timestamp shows AS `13335`; PTR = `one.one.one.one` from DoH and RIPEstat; two geolocation providers return HTTP 200 (values not asserted — they differ by design); Tor bulk exit list downloaded (HTTP 200) and `1.1.1.1` not in it; ExoneraTor page for the date captured (any result); Shodan InternetDB HTTP 200 with `hostnames` containing `one.one.one.one`; validation of `192.168.1.1` → `NOT-INVESTIGABLE`; `skip: S8, S9`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Subscriber assigned the IP at the incident time | the operator (netblock holder / ASN holder; abuse contact as captured from RDAP) | preservation, then disclosure | IP, incident timestamp in UTC with the conversion shown, source port if the case has it (CGNAT), ASN, netblock | subscriber identity for the IP(:port) at that time, session logs |
| VPN/hosting provider egress | the provider named in RDAP/ASN | preservation | IP, UTC window | account that used the egress at that time |

### 9.12 Duration estimate

Typical FULL-mode duration: 8–15 minutes; longest steps S6 (list downloads) and S8.
""",
}

for name, text in ADD.items():
    p = T / name
    s = p.read_text(encoding="utf-8")
    if "### 9.10" in s:
        print("skip (already has 9.10):", name); continue
    s = s.rstrip() + "\n" + text
    p.write_text(s, encoding="utf-8")
    print("added:", name)
