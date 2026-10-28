#!/usr/bin/env python3
"""Write selftest/<CODE>.selftest.json for every agent. Values verified live on 2026-10-28 from a sandbox."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "selftest"
OUT.mkdir(exist_ok=True)
VERIFIED = "2026-10-28"

def spec(code, target, assertions, skip, notes, extra=None):
    d = {"schema": "l1-selftest/1.1", "agent": code, "agent_version": "1.2", "verified_on": VERIFIED,
         "target": target, "skip_steps": skip, "caps": {}, "sub_skips": {}, "intake_overrides": {}, "notes": notes, "assertions": assertions}
    if extra: d.update(extra)
    return d

def A(id_, step, desc, check, expect, drift=False, **kw):
    a = {"id": id_, "step": step, "description": desc, "check": check, "expect": expect}
    if drift: a["may_drift"] = True
    a.update(kw); return a

S = {}
S["L1-WEB"] = spec("L1-WEB", "https://example.com/", [
    A("WEB-01","S2","final HTTP status","equals",200),
    A("WEB-02","S2","redirect hops","equals",0),
    A("WEB-03","S3","page title","equals","Example Domain"),
    A("WEB-04","S2","DNS A answers for example.com","gte",1,drift=True),
    A("WEB-05","S4","directly linked resources","equals",0),
    A("WEB-06","S6","Wayback closest snapshot timestamp","matches","^\\d{14}$",drift=True),
    A("WEB-07","S7","volatility result","equals","STABLE"),
], [], "example.com is IANA's reserved domain. Its DNS/hosting change occasionally; only counts and patterns are asserted for those.", {"sub_skips": {"S6": "creation of a new public snapshot"}})

S["L1-DOM"] = spec("L1-DOM", "example.com", [
    A("DOM-01","S2","RDAP HTTP status","equals",200),
    A("DOM-02","S2","RDAP ldhName","equals","EXAMPLE.COM"),
    A("DOM-03","S2","RDAP registration event date","equals","1995-08-14T04:00:00Z"),
    A("DOM-04","S2","RDAP nameserver count","gte",2,drift=True,note="names were elliott/hera.ns.cloudflare.com on the verification date"),
    A("DOM-05","S3","NS answers agree between two DoH resolvers","equals",True),
    A("DOM-06","S6","MX answer is empty or the null MX '0 .'","in",[[],["0 ."]]),
    A("DOM-07","S4","crt.sh certificate rows","gte",10,drift=True),
    A("DOM-08","S7","home page HTTP status","equals",200),
    A("DOM-09","S7","home page title","equals","Example Domain"),
    A("DOM-10","S8","Wayback availability present","exists",True),
], ["S9"], "Nameserver names drift; count only.", {"intake_overrides": {"16": "registrable domain"}})

S["L1-USR"] = spec("L1-USR", "Gargron", [
    A("USR-01","S2","mastodon.social control probe (random handle) returns not-found signature","equals",True, source="https://mastodon.social/api/v1/accounts/lookup?acct=<random>"),
    A("USR-02","S2","keybase.io control probe (random handle) returns no user","equals",True),
    A("USR-03","S2","dev.to control probe (random handle) HTTP status","equals",404),
    A("USR-04","S4","mastodon.social lookup HTTP status for Gargron","equals",200, source="https://mastodon.social/api/v1/accounts/lookup?acct=Gargron"),
    A("USR-05","S4","mastodon.social username","equals","Gargron"),
    A("USR-06","S4","mastodon.social account id","equals","1"),
    A("USR-07","S4","mastodon.social created_at starts with","startswith","2016-03-16"),
    A("USR-08","S3","mastodon.social/@Gargron profile page HTTP status","equals",200),
    A("USR-09","S4","Keybase lookup for Gargron returns a definite classification","in",["EXISTS","NOT FOUND"]),
    A("USR-10","S3","github.com/Gargron probe classification","in",["EXISTS","NOT FOUND","INCONCLUSIVE"], inconclusive_if_blocked=True, note="GitHub blocks some sandboxes; INCONCLUSIVE is a valid result"),
], ["S5","S8"], "Only the target handle is probed, as in a real run; control probes use a random handle per the S2 method.")

S["L1-EML"] = spec("L1-EML", "selftest@example.com", [
    A("EML-01","S1","local part","equals","selftest"),
    A("EML-02","S1","domain","equals","example.com"),
    A("EML-03","S1","role address","equals",False),
    A("EML-04","S2","MX answer is empty or null MX '0 .'","in",[[],["0 ."]]),
    A("EML-05","S2","RDAP registration date","equals","1995-08-14T04:00:00Z"),
    A("EML-06","S3","disposable classification","equals",False),
    A("EML-07","S4","Gravatar avatar HTTP status for md5(selftest@example.com)","equals",404),
    A("EML-08","S5","HIBP step status without key","equals","DEFERRED", note="with an agency key, use account-exists@hibp-integration-tests.com and expect >= 1 breach"),
], ["S6","S7"], "No third-party sweep for a test address.", {"intake_overrides": {}})

S["L1-PHN"] = spec("L1-PHN", "+442079460000", [
    A("PHN-01","S1","valid","equals",True),
    A("PHN-02","S1","region","equals","GB"),
    A("PHN-03","S1","number type","equals","FIXED_LINE"),
    A("PHN-04","S1","E.164","equals","+442079460000"),
    A("PHN-05","S1","geocoder description","equals","London"),
    A("PHN-06","S1","time zone","equals","Europe/London"),
    A("PHN-07","S1","phonenumbers library version recorded","exists",True),
    A("PHN-08","S2","regulator identified","contains","ofcom.org.uk"),
    A("PHN-09","S3","search variants generated","gte",5),
], ["S4","S5","S6"], "UK number range 020 7946 0xxx is reserved by Ofcom for drama use; it is assigned to nobody.", {"intake_overrides": {"16": "GB"}})

S["L1-SOC"] = spec("L1-SOC", "https://bsky.app/profile/bsky.app", [
    A("SOC-01","S1","public profile API HTTP status (platform public API source, 9.2)","equals",200, source="https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=bsky.app"),
    A("SOC-02","S3","handle","equals","bsky.app"),
    A("SOC-03","S3","stable ID (DID)","equals","did:plc:z72i7hdynmk6r22z27h6tvur"),
    A("SOC-04","S3","createdAt starts with","startswith","2023-04-12"),
    A("SOC-05","S2","profile page HTTP status","equals",200),
    A("SOC-06","S4","author feed items (limit 10)","gte",5, source="https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=bsky.app&limit=10"),
    A("SOC-07","S4","every feed item uri starts with","startswith","at://did:plc:z72i7hdynmk6r22z27h6tvur/"),
    A("SOC-08","S9","drift line printed","exists",True),
], ["S5","S6"], "Bluesky exposes a public, keyless API, so this test works without a browser; the mode will be ASSISTED on hosts without CAP-BROWSER and that is expected.", {"intake_overrides": {"16": "10 most recent"}})

S["L1-IMG"] = spec("L1-IMG", "selftest/L1-IMG_selftest.jpg", [
    A("IMG-01","S1","sandbox copy SHA-256 equals published","equals","841ebfdeff6f682e748a9196f88dec69bfb2d0cd8150c9e4e09b73b40b4d109f", note="if different, report UPLOAD ALTERED and compare the Investigator's local hash"),
    A("IMG-02","S1","MD5","equals","c299389a69536b1c2a7595784bc68c8d"),
    A("IMG-03","S1","size bytes","equals",14128),
    A("IMG-04","S1","format","equals","JPEG"),
    A("IMG-05","S1","dimensions (canonical WxH)","equals","640x400"),
    A("IMG-06","S2","EXIF Make","equals","L1-SELFTEST-CAMERA"),
    A("IMG-07","S2","EXIF Model","equals","MODEL-27037"),
    A("IMG-08","S2","EXIF Artist","equals","L1 SELFTEST"),
    A("IMG-09","S2","EXIF DateTimeOriginal","equals","2026:10:28 09:00:00"),
    A("IMG-10","S2","GPS latitude ref","equals","N"),
    A("IMG-11","S2","GPS latitude (canonical deg/min/sec, seconds to one decimal)","equals","51/30/28.8"),
    A("IMG-12","S2","GPS longitude ref","equals","W"),
    A("IMG-13","S1","perceptual hash computed","exists",True),
], ["S3","S5","S6","S7","S8"], "Fixture generated by build; hashes in selftest/FIXTURE_HASHES.json.", {"intake_overrides": {"16": "841ebfdeff6f682e748a9196f88dec69bfb2d0cd8150c9e4e09b73b40b4d109f"}})

S["L1-CRY"] = spec("L1-CRY", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", [
    A("CRY-01","S1","chain","equals","BTC"),
    A("CRY-02","S1","format","equals","P2PKH"),
    A("CRY-03","S1","base58check valid","equals",True),
    A("CRY-04","S2","mempool.space HTTP status","equals",200),
    A("CRY-05","S2","chain_stats.spent_txo_count","equals",0),
    A("CRY-06","S2","chain_stats.funded_txo_count","gte",80000,drift=True),
    A("CRY-07","S2","chain_stats.tx_count","gte",60000,drift=True),
    A("CRY-08","S2","second explorer (blockchain.info rawaddr) n_tx","gte",60000,drift=True),
    A("CRY-09","S3","earliest-100 export (fetched by offset): first transaction block height","equals",0),
    A("CRY-10","S3","earliest-100 export: first transaction block time","equals","2009-01-03T18:15:05Z"),
    A("CRY-11","S6","OFAC SDN CSV downloaded","equals",200),
    A("CRY-12","S6","sanctions result","equals","NO MATCH"),
], ["S5","S7","S8"], "Genesis coinbase address: its outputs are unspendable, so spent count is always 0; received counts only grow.", {"caps": {"S3": "most recent 100 plus earliest 100 (fetched by offset)"}})

S["L1-ORG"] = spec("L1-ORG", "Apple Inc.", [
    A("ORG-01","S4","GLEIF HTTP status","equals",200, source="https://api.gleif.org/api/v1/lei-records/HWUPKR0MPOU8FGXBT394"),
    A("ORG-02","S4","LEI","equals","HWUPKR0MPOU8FGXBT394"),
    A("ORG-03","S4","legal name","equals","Apple Inc."),
    A("ORG-04","S4","jurisdiction","equals","US-CA"),
    A("ORG-05","S4","registration status","equals","ISSUED"),
    A("ORG-06","S1","official register identified","contains","sec.gov"),
    A("ORG-07","S2","EDGAR company page HTTP status after redirect","equals",200, note="EDGAR requires a descriptive User-Agent with a contact email"),
    A("ORG-08","S6","OFAC + UN list files downloaded","equals",200),
    A("ORG-09","S6","screening result","in",["NO MATCH","POTENTIAL MATCH (requires human review)"]),
], ["S5","S7","S8"], "A large listed company with a stable LEI; name screening may produce potential matches on common words, which is acceptable.", {"intake_overrides": {"16": "US", "17": "LEI HWUPKR0MPOU8FGXBT394; CIK 0000320193"}})

S["L1-IPA"] = spec("L1-IPA", "1.1.1.1", [
    A("IPA-01","S1","classification","equals","public"),
    A("IPA-02","S2","RDAP name","equals","APNIC-LABS"),
    A("IPA-03","S2","RDAP range","equals","1.1.1.0-1.1.1.255"),
    A("IPA-04","S3","ASN","equals",13335),
    A("IPA-05","S3","prefix","equals","1.1.1.0/24"),
    A("IPA-06","S3","routing history at incident timestamp shows ASN","equals",13335),
    A("IPA-07","S4","PTR","equals","one.one.one.one"),
    A("IPA-08","S5","two geolocation providers responded","equals",True),
    A("IPA-09","S6","in Tor bulk exit list","equals",False),
    A("IPA-10","S6","ExoneraTor page captured","exists",True),
    A("IPA-11","S7","Shodan InternetDB hostnames contain","contains","one.one.one.one",drift=True),
    A("IPA-12","unit","validation routine applied to 192.168.1.1 (code only, no network)","equals","NOT-INVESTIGABLE"),
], ["S8","S9"], "Cloudflare's public resolver; registration and routing are stable.", {"intake_overrides": {"16": "2026-01-01T00:00:00Z"}})

S["L1-TGM"] = spec("L1-TGM", "t.me/telegram", [
    A("TGM-01","S2","info page HTTP status","equals",200),
    A("TGM-02","S2","title","equals","Telegram News"),
    A("TGM-03","S2","handle present","contains","@telegram"),
    A("TGM-04","S2","subscriber count displayed","matches","^\\d[\\d\\s,.]*\\s*subscribers$",drift=True),
    A("TGM-05","S3","preview page HTTP status","equals",200),
    A("TGM-06","S3","posts on preview page 1","gte",10),
    A("TGM-07","S3","every captured post has ISO datetime","equals",True),
    A("TGM-08","S4","media files captured","gte",1),
], ["S7"], "Telegram's official channel; counts drift.", {"intake_overrides": {"16": "20 most recent"}})

S["L1-ONI"] = spec("L1-ONI", "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/", [
    A("ONI-01","S1","address format valid (56 base32 + .onion)","equals",True),
    A("ONI-02","S1","version byte","equals",3),
    A("ONI-03","S1","checksum valid (if computed)","in",[True,"not verified"]),
    A("ONI-04","S5","clearnet search result page captured","gte",1),
    A("ONI-05","unit","validation routine applied to the v2 address expyuzz4wqqyqhjn.onion (code only)","equals","NOT-INVESTIGABLE"),
], ["S2","S3","S4","S6"], "The Investigator-side Tor Browser capture is optional in self-test; the agent-side validation and clearnet context are tested.", {"intake_overrides": {"16": "n/a", "17": "n/a", "18": "Y"}})

S["L1-DOC"] = spec("L1-DOC", "selftest/L1-DOC_selftest.pdf", [
    A("DOC-01","S1","SHA-256","equals","07abda698a6064a8a199d3580e0809b07b1320b4cb533522ca4e0f9e536d4719"),
    A("DOC-02","S1","size bytes","equals",2012),
    A("DOC-03","S1","true type","equals","application/pdf"),
    A("DOC-04","S2","page count","equals",2),
    A("DOC-05","S3","/Author","equals","L1 SELFTEST"),
    A("DOC-06","S3","/Title","equals","L1 SELFTEST DOCUMENT"),
    A("DOC-07","S7","extracted text contains marker","contains","ISO27037-SELFTEST-MARKER"),
    A("DOC-08","S7","Identifiers_Found contains URL","contains","https://example.com/selftest-page"),
    A("DOC-09","S7","Identifiers_Found contains email","contains","selftest@example.com"),
    A("DOC-10","S5","macros present","equals",False),
], [], "One fixture per run, as in a real case. A DOCX fixture (L1-DOC_selftest.docx, author L1 SELFTEST, revision 3) is provided for a separate manual run; hashes in selftest/FIXTURE_HASHES.json.", {"intake_overrides": {"16": "07abda698a6064a8a199d3580e0809b07b1320b4cb533522ca4e0f9e536d4719", "17": "n/a"}})

S["L1-VID"] = spec("L1-VID", "https://www.youtube.com/watch?v=jNQXAC9IVRw", [
    A("VID-01","S1","video id","equals","jNQXAC9IVRw"),
    A("VID-02","S3","oEmbed HTTP status","equals",200),
    A("VID-03","S3","oEmbed title","equals","Me at the zoo"),
    A("VID-04","S3","oEmbed author_name","equals","jawed"),
    A("VID-05","S3","oEmbed author_url","equals","https://www.youtube.com/@jawed"),
    A("VID-06","S2","watch page HTTP status","equals",200),
    A("VID-07","S4","yt-dlp upload_date (if yt-dlp ran)","equals","20050423", inconclusive_if_blocked=True),
    A("VID-08","S4","yt-dlp duration seconds (if yt-dlp ran)","between",[18,20], inconclusive_if_blocked=True),
    A("VID-09","S10","drift line printed","exists",True),
], ["S5","S8","S9"], "The first video uploaded to YouTube; public since 2005.", {"intake_overrides": {"16": "N", "17": "N"}})

S["L1-DSC"] = spec("L1-DSC", "https://discord.gg/discord-developers", [
    A("DSC-01","S2","invite JSON HTTP status","equals",200),
    A("DSC-02","S2","guild.name","equals","Discord Developers"),
    A("DSC-03","S2","guild.id","equals","613425648685547541"),
    A("DSC-04","S1","Snowflake creation time of guild id","equals","2019-08-20T17:34:31Z"),
    A("DSC-05","S2","approximate_member_count","gte",100000,drift=True),
    A("DSC-06","S3","widget HTTP status","in",[200,403]),
    A("DSC-07","S7","drift line printed","exists",True),
], ["S6"], "Discord's official developer server.")

for code, d in S.items():
    (OUT / f"{code}.selftest.json").write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", code, len(d["assertions"]), "assertions")
