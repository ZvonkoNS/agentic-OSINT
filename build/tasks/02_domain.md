<!-- META
AGENT_NAME: Domain & Website Infrastructure Agent
AGENT_CODE: L1-DOM
FILE: 02_L1-DOM_Domain-and-Website-Infrastructure.md
PURPOSE: Document the registration, DNS, certificate, hosting, mail and historical footprint of one domain name from public sources, as hashed evidence.
INPUT_TYPE: registrable domain name (e.g. example.com — not a full URL)
-->
### 9.1 Scope and input validation

**In scope:** registration data (RDAP/WHOIS), DNS records, certificate transparency, hosting (IP → network → ASN), mail configuration, the public home page, archive history, and third-party reputation listings for one domain.
**Out of scope (→ Leads):** full capture of individual pages (L1-WEB), investigation of the hosting IP beyond its registration (L1-IPA), people named in registration data (L1-USR/L1-EML), other domains found along the way.

Validation:
- Hostname syntax only: letters, digits, hyphens, dots; no scheme, path, port or `@`.
- IDN: show Unicode and punycode; use punycode for all queries.
- If a subdomain is given (e.g. `shop.example.com`), state the registrable domain (`example.com`) and ask at intake validation which one is the target. Record the answer. Registration data is always for the registrable domain; DNS/certificates/hosting can be collected for the subdomain.

**Intake additions (printed with the form):** field **16** = "If you gave a subdomain: is the target the subdomain or the registrable domain?" Authorisation **D: none**.

### 9.2 Sources (public, keyless first)

| Source | Use | Level | Notes |
|---|---|---|---|
| RDAP via bootstrap `https://rdap.org/domain/<domain>` | Registration data (registrar, dates, status, nameservers, redacted contacts) | B | Authoritative registry/registrar data in JSON |
| Registrar/registry WHOIS web page | Human-readable confirmation | A via G3; optional, SKIPPED without CAP-BROWSER | Same data, different presentation |
| DNS over HTTPS: `https://dns.google/resolve?name=<n>&type=<T>` and `https://cloudflare-dns.com/dns-query?name=<n>&type=<T>` (header `accept: application/dns-json`) | A, AAAA, CNAME, MX, NS, TXT, SOA, CAA | B | Two resolvers for cross-check |
| Certificate Transparency: `https://crt.sh/?q=%25.<domain>&output=json` | Issued certificates, SAN names → subdomain list | B | Historical and current |
| RDAP for IP: `https://rdap.org/ip/<ip>` | Netblock holder of hosting IP | B | ASN detail is L1-IPA's job; record the summary |
| RIPEstat: `https://stat.ripe.net/data/prefix-overview/data.json?resource=<ip>` | ASN and prefix | B | Keyless |
| Wayback availability `https://archive.org/wayback/available?url=<domain>` and CDX `https://web.archive.org/cdx/search/cdx?url=<domain>&output=json&limit=50` | First/last snapshot, count | B | Third-party archive |
| urlscan.io public search `https://urlscan.io/api/v1/search/?q=domain:<domain>` | Prior public scans | B | Third-party; results are scans by others |
| VirusTotal / similar reputation UI | Vendor verdicts | A via G3, or B through the vendor API with an agency key (authorisation C); otherwise SKIPPED (optional) | Opinions of vendors, not facts about the domain |
| Search engines `site:<domain>` | Indexed page count/sample | C → A | Lead first; capture the results page if cited |
| Home page `https://<domain>/`, `/robots.txt`, `/sitemap.xml`, `/.well-known/security.txt`, `https://mta-sts.<domain>/.well-known/mta-sts.txt` | Web presence; MTA-STS policy text | B (home page also A where available) | Headers saved |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Normalise input; registrable vs subdomain decision; print the query list | — |
| S2 | Registration data: RDAP JSON; extract registrar, IANA ID, creation/updated/expiry dates, statuses (EPP codes), nameservers, DNSSEC, contact fields (note redactions/privacy service); optional registrar WHOIS page capture | B (+A) |
| S3 | DNS records: A, AAAA, CNAME, MX, NS, SOA, TXT, CAA for the domain and `www`; from two resolvers; disagreements recorded | B |
| S4 | Certificates: crt.sh JSON; table of issuer, not-before/after, SAN list; derive unique subdomain list (passive only — no brute force, no zone transfer attempts) | B |
| S5 | Hosting: resolve A/AAAA → RDAP IP summary → RIPEstat prefix/ASN (facts); note CDN/proxy indicators (e.g. ASN belongs to a CDN) — the "what that means" sentence goes under the Analysis label in 9.6 | B |
| S6 | Mail: MX hosts and their providers; SPF (TXT), DMARC (`_dmarc.<domain>`), MTA-STS (the `_mta-sts.<domain>` TXT record only signals presence; the policy itself is fetched from `https://mta-sts.<domain>/.well-known/mta-sts.txt`), DKIM only if a selector is already known from the case (no guessing) | B |
| S7 | Web presence: home page capture (level A via G3 if available + level B with headers), robots.txt, sitemap.xml, security.txt; HTTP→HTTPS behaviour; server/technology headers | A + B |
| S8 | History: Wayback availability + CDX sample (first/last/count); capture the earliest and latest snapshot *index* pages as third-party items; no content analysis of old snapshots (→ Leads) | B |
| S9 | Reputation and prior scans: urlscan search JSON (B); one vendor reputation result via G3 or an agency API key (authorisation C), else SKIPPED; all labelled third-party assessment | B / A |
| S10 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- Save every JSON response verbatim as `EV-nnn_<source>.json` with its headers; derived tables cite the JSON item.
- Record query parameters exactly (type, resolver, URL) in each evidence record so the lookup is repeatable.
- DNS answers include TTLs; record the UTC time of the query — DNS is time-dependent evidence.
- Certificate data proves issuance, not that the certificate was ever deployed; say so in Findings.
- Never perform zone transfers (`AXFR`), subdomain brute-forcing, port scans, or vulnerability checks. The only permitted active requests are standard DNS queries, HTTPS GETs of public URLs and public API GETs.
- If the registrant data is redacted (common since 2018 GDPR practice), record the redaction and the privacy-service name as facts; the registrar's abuse contact is recorded as a Lead for a lawful request.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| RDAP bootstrap returns 404 / TLD has no RDAP | Try the registry's own RDAP base URL if known; else WHOIS page via G3; else DEFERRED (Investigator captures the registry WHOIS page post-run); record "RDAP unavailable for TLD" |
| Resolver answers differ (A records) | Record both with resolver identity; add a third resolver via DoH (e.g. `https://dns.quad9.net:5053/dns-query?name=<n>&type=<T>`); a workstation `nslookup`/`dig` check goes to the post-run list |
| crt.sh times out (large domains) | Retry with `&exclude=expired`; if still failing, record partial and propose a later re-run |
| Home page redirects to another domain | Capture the chain; the other domain becomes a Lead — do not profile it |
| CDN in front of origin | State that the IP/ASN describe the CDN edge, not the origin; origin is unknown without a lawful request |
| urlscan/VirusTotal rate-limited | Wait once; else SKIPPED (optional context steps) |

### 9.6 Findings structure

1. **Registration** — registrar, dates, statuses, nameservers, DNSSEC, contact visibility (EV refs).
2. **DNS** — table of records at query time; resolver agreement.
3. **Certificates and names** — issuers, validity windows, SAN-derived name list.
4. **Hosting** — IPs, netblock holder, ASN (facts, EV refs). Under the heading **Analysis (outside ISO/IEC 27037 — opinion)**: the CDN/proxy indicator and what it implies, with the explicit caveat that hosting provider ≠ site operator.
5. **Mail** — MX provider, SPF/DMARC policy strings verbatim.
6. **Web presence** — what the home page shows (neutral description), technologies from headers, robots/sitemap/security.txt existence.
7. **History** — first/last archive snapshot dates, count (third-party).
8. **Third-party assessments** — urlscan/vendor results, clearly separated from facts.
9. **Contradictions** — e.g. creation date vs first archive snapshot, registrar vs WHOIS page.

### 9.7 XLSX sheets

`Registration` (field, value, EV) · `DNS_Records` (name, type, value, TTL, resolver, UTC, EV) · `Certificates` (crt.sh id, issuer, not_before, not_after, SANs, EV) · `Subdomains` (name, first seen cert, last seen cert) · `Hosting` (IP, netblock, holder, ASN, AS name, CDN flag, EV) · `Mail` (record, value, EV) · `Archive_History` (service, first, last, count, EV) · `Reputation` (source, verdict/summary, UTC, EV).

### 9.8 Interpretation cautions

- Registration dates and nameserver changes are facts about the registry record, not about who controls the website day to day.
- Privacy/proxy registrant data is normal and not evidence of concealment intent.
- Shared hosting and CDNs mean many unrelated sites share an IP; an IP-level finding must never be attributed to the domain's operator.
- Reputation verdicts are vendor opinions with their own methodology and date; present them as such.
- DNS and hosting are volatile; everything is "as at <UTC>".

### 9.9 Leads policy

Other domains sharing nameservers, IP or certificates; registrant/admin names or emails (L1-EML/L1-USR); the hosting IP (L1-IPA); specific pages (L1-WEB); abuse contacts for lawful requests.

### 9.10 Self-test specification

Target: `example.com`. Assertions: RDAP HTTP 200 with `ldhName` = `EXAMPLE.COM`; RDAP registration event date = `1995-08-14T04:00:00Z`; RDAP nameservers list length ≥ 2 (names drift — in 2026 they are `elliott.ns.cloudflare.com` / `hera.ns.cloudflare.com`; assert the count, not the names); DoH NS answers from two resolvers agree; MX query returns the null MX `0 .` (RFC 7505) — assert that the MX answer set is either empty or exactly `0 .`; crt.sh returns ≥ 10 certificate rows; home page HTTP 200 with title `Example Domain`; `robots.txt` request returns a status (any); Wayback availability present. `skip: S9` (reputation sources not needed for the test).

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Registrant identity behind redacted RDAP data | registrar (name and IANA ID from RDAP; abuse contact as captured) | disclosure (subscriber/registration data) | domain, registrar, RDAP capture UTC, registration date | registrant contact and payment data, registration logs |
| Site operator / content | hosting provider (netblock holder from S5; abuse contact from RDAP-IP) | preservation | domain, IP(s), ASN, capture UTC | hosting account data, access logs |
| Mail account data | mail provider (MX host operator from S6) | preservation | domain, MX hosts, UTC | account data for the mailbox named in the case |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–20 minutes; longest steps S4 (crt.sh on large domains) and S8.
