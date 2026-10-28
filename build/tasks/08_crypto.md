<!-- META
AGENT_NAME: Cryptocurrency Address Tracing Agent
AGENT_CODE: L1-CRY
FILE: 08_L1-CRY_Cryptocurrency-Address-Tracing.md
PURPOSE: Document the on-chain record of one cryptocurrency address from public block explorers — balance, transaction history, direct counterparties, public labels, sanctions-list and abuse-report matches — as hashed evidence, without clustering claims.
INPUT_TYPE: cryptocurrency address (Bitcoin, Ethereum/EVM, Tron, Litecoin, Solana, XRP, Bitcoin Cash, Dogecoin; Monero is accepted but documented as not traceable) — for an EVM address, name the chain(s) in field 7
-->
### 9.1 Scope and input validation

**In scope:** chain detection and checksum validation; address summary from at least two independent public explorers; full or capped transaction export; direct counterparties (one hop, derived from the export); public labels/tags shown by explorers; sanctions-list address matching; public abuse-report listings.
**Out of scope (→ Leads):** clustering/common-ownership heuristics, multi-hop tracing, exchange attribution beyond public labels, deanonymisation, contacting exchanges (lawful request path is a Lead), price valuation beyond a captured rate.

Validation (do in code if CAP-CODE):
- Detect format: BTC (`1…` P2PKH, `3…` P2SH, `bc1q…` bech32, `bc1p…` taproot), LTC (`L…`, `M…`, `ltc1…`), BCH (`q…`/`bitcoincash:`), DOGE (`D…`), ETH/EVM (`0x` + 40 hex; EIP-55 checksum if mixed case), TRX (`T…` base58, 34 chars), SOL (base58, 32–44 chars), XRP (`r…`), XMR (`4…`/`8…`, 95 chars).
- Validate the checksum with a proper library: `base58` (base58check), `bech32` (bech32/bech32m), and for EIP-55 a real Keccak-256 (`pycryptodome` → `Crypto.Hash.keccak`, or `eth-hash`/`eth-utils`; **`hashlib.sha3_256` is NIST SHA-3, not Keccak, and gives wrong results**). Install under authorisation B. If no library can be installed, record "checksum not verified" and continue. A checksum that a library verifies as **invalid** stops the run with an explanation (do not "correct" it).
- EVM ambiguity: an `0x` address exists on every EVM chain. If intake field 16 names the chain(s), use them. Otherwise run Ethereum mainnet only and state in Findings and Leads that other EVM chains were not checked (R9: no scope widening). Keyless Blockscout instances for named chains, where they exist: `eth.blockscout.com`, `base.blockscout.com`, `polygon.blockscout.com`, `arbitrum.blockscout.com`, `optimism.blockscout.com`, `gnosis.blockscout.com` (verify availability). BNB Smart Chain has no keyless API in this family: use the explorer web page via G3 or an Etherscan-family API key from authorisation C; otherwise DEFERRED.
- Monero: record the address format validity and the statement that public ledgers do not expose balances or transactions for XMR addresses; proceed only with S6/S7 (sanctions/abuse).
- A library-verified invalid checksum ends the run as `NOT-INVESTIGABLE` (core §3.1) with a short pack documenting the result.

**Intake additions (printed with the form):** field **16** = "For an `0x` (EVM) address: which chain(s) does the case concern? (default: Ethereum mainnet only)"; field **17** = "Valuation wanted? If yes, the date/time (UTC) for the rate (default: none)". Authorisation **D: none**.

### 9.2 Sources (public, keyless first)

| Chain | Source | Use | Level |
|---|---|---|---|
| BTC | mempool.space API `https://mempool.space/api/address/<a>` and `/address/<a>/txs` ; blockchain.info `https://blockchain.info/rawaddr/<a>` ; blockchair `https://api.blockchair.com/bitcoin/dashboards/address/<a>` | Summary + tx list (two sources for cross-check) | B |
| ETH/EVM | Blockscout `https://eth.blockscout.com/api/v2/addresses/<a>` and `/transactions`, `/token-transfers` ; Etherscan web pages (API needs key) | Summary, native tx, token transfers | B / A |
| TRX | Tronscan API `https://apilist.tronscanapi.com/api/accountv2?address=<a>` and transaction endpoints | Summary + tx | B |
| SOL | Solscan / Solana FM web; public RPC `getSignaturesForAddress` via `https://api.mainnet-beta.solana.com` | Signatures + summary | B / A |
| XRP | XRPL public API `https://s1.ripple.com:51234/` (`account_info`, `account_tx`) or livenet.xrpl.org | Summary + tx | B / A |
| LTC / BCH / DOGE | blockchair dashboards; chain-specific explorers | Summary + tx | B |
| Sanctions | OFAC SDN list file: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV` (or `https://www.treasury.gov/ofac/downloads/sdn.csv`; digital-currency addresses appear as `Digital Currency Address - XBT/ETH/…` identifiers in the SDN alternate-ID/comments data — also download `https://www.treasury.gov/ofac/downloads/sdn.xml` and search it, since the CSV omits some identifier fields) — level B; the OFAC search website via G3 as a labelled cross-check. UN consolidated list: `https://scsanctions.un.org/resources/xml/en/consolidated.xml` — level B. UK Sanctions List: the gov.uk publication page "The UK Sanctions List" (capture the page, follow the current XML/CSV link — it changes per release) — level B/A. Addresses are rare outside OFAC. The EU consolidated file requires an EU Login account and is **not used** (R2); the public EU Sanctions Map may be checked via G3 | Exact address match | B / A |
| Abuse reports | Chainabuse `https://www.chainabuse.com/address/<a>` (public web) | Public reports | A via G3, else B if fetchable, else SKIPPED (optional) |
| Labels | Explorer "tags"/"labels"/"name tag" fields as shown | Third-party attribution | A/B |
| Price (optional) | A public price page captured with date/time | Valuation at a stated time only | A |

### 9.3 Execution plan

| Step | Purpose | Level |
|---|---|---|
| S1 | Validate; detect chain; checksum; EVM chain selection; print the explorer list | — |
| S2 | Address summary from **two** independent explorers: balance, total received/sent, tx count, first/last activity (UTC, block height); record units (satoshi/wei/sun…) and the converted value; note any disagreement | B |
| S3 | Transaction export: all transactions, or the most recent 500 plus the earliest 100 if more (record the cap; explorers paginate newest-first, so the earliest block is fetched explicitly — e.g. blockchain.info `rawaddr/<a>?limit=100&offset=<n_tx-100>`, or mempool.space `/address/<a>/txs/chain/<last txid>` paging to the end); save raw JSON pages; build a normalised CSV: txid, block, UTC, direction, value (native unit + converted), counterparty address(es), fee; token transfers (EVM) in a separate table | B |
| S4 | Direct counterparties (one hop, derived): top 20 by value in and out, with counts and date spans; mark exchange/service labels only where an explorer shows one (EV ref) | — (derived) |
| S5 | Public labels: explorer tag/name fields for the target and for the top counterparties; captured as shown; **"third-party label, unverified"** | A / B |
| S6 | Sanctions screening: download the OFAC SDN (CSV and XML), UN and UK list files (B) and search them for the exact address string (and, for EVM, its lower-case form); OFAC website search via G3 as a cross-check where available; capture every file and result page with list version/date | B / A |
| S7 | Abuse reports: Chainabuse page captured (G3, or B if fetchable); report count, categories, dates as shown; otherwise SKIPPED | A / B |
| S8 | Optional valuation: only if intake field 17 asked for it; capture a public price page for the stated date/time (A via G3, else B if a public price API is reachable, else SKIPPED); compute and show the formula | A / B |
| S9 | Findings, inventory, custody, outputs (Phase 3) | — |

### 9.4 Task-specific capture rules

- Save every API response page verbatim (`EV-nnn_<explorer>_<endpoint>_<page>.json`) with headers; the CSV is a derived item citing them.
- Two-source rule for the summary: if explorers disagree beyond rounding, record both and do not pick one.
- Units: always record the raw integer unit (satoshi, wei, sun, lamports, drops) alongside the decimal value and the divisor used.
- Time: block timestamps are miner/validator-set and in UTC; state the source (explorer vs node) for each.
- Never query the address on services that require an account; never submit the address to a form that creates a public record (e.g. a public "report" form); never interact with any contract or send any transaction.
- Labels and tags are attributions by explorer operators or their communities; capture them, cite them, do not adopt them as facts.
- No clustering: do not apply common-input-ownership, change-address or any heuristic to assert that other addresses belong to the same owner. Clustering with a blockchain-analytics platform, if the agency has one, is a Lead.

### 9.5 Task-specific self-healing cases

| Symptom | Remedy to propose at G4 |
|---|---|
| Explorer API rate-limited (429) | Pause; switch to the second explorer; reduce page size |
| Explorer returns different tx counts | Record both; export from both if feasible; note pagination differences (e.g. unconfirmed txs) |
| Address has more transactions than the S3 cap (600) | Apply the cap, record it; a dedicated later run is a Lead |
| Checksum library not installable | Record "checksum not verified"; continue |
| OFAC website blocks automation | The downloadable list files (level B) are the record; the website cross-check is SKIPPED |
| EVM address shows token spam/airdrops | Keep them in the token table; flag "unsolicited transfers possible" in cautions |
| Chainabuse unavailable | SKIPPED (optional step) |

### 9.6 Findings structure

1. **Address identity** — chain(s), format, checksum validity, EVM chain presence table.
2. **Summary** — per explorer; agreement/disagreement stated.
3. **Activity timeline** — first/last activity, tx count, total in/out; monthly activity counts (derived table).
4. **Direct counterparties** — top-20 tables with any explorer labels (cited).
5. **Public labels** — for the target address, as shown.
6. **Sanctions screening** — exact-match result per list, with capture refs; "no match" is recorded as such with the list version/date.
7. **Abuse reports** — as shown, labelled public submissions.
8. **Valuation** — only if performed; formula and captured rate.
9. **Not performed** — clustering, multi-hop, exchange identification beyond labels.

### 9.7 XLSX sheets

`Address_Summary` (field, explorer 1, explorer 2, unit, EV) · `Transactions` (txid, block, UTC, direction, value raw, value decimal, counterparty, fee, EV page) · `Token_Transfers` (EVM: tx, token contract, symbol, from, to, value, EV) · `Counterparties` (address, direction, total, count, first, last, label shown, label EV) · `Labels_Attribution` (address, label, source, EV) · `Sanctions_Screening` (list, version/date, match Y/N, EV) · `Abuse_Reports` (count, categories, latest date, EV).

### 9.8 Interpretation cautions

- An address is a cryptographic identifier, not a person; control of an address is proven only by key possession or by a service's records obtained lawfully.
- Explorer labels can be wrong, stale or crowd-sourced; a "Binance" tag is a claim by the explorer.
- Receiving funds is not an action by the address owner (anyone can send to any address, including sanctioned or spam transfers).
- Transaction counts and balances are as at the block height captured; they change.
- Converted fiat values depend on the rate source and timestamp captured; different sources differ.

### 9.9 Leads policy

Top counterparties (separate L1-CRY runs); labelled services for lawful requests (exchange compliance contacts); analytics-platform clustering; related addresses named in the case; off-chain mentions of the address (L1-WEB search).

### 9.10 Self-test specification

Target: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` (the Bitcoin genesis-block coinbase address). Assertions: chain `BTC`, format P2PKH, base58check valid; mempool.space summary HTTP 200 with `chain_stats.spent_txo_count` = `0` and `chain_stats.funded_txo_count` ≥ `80000` and `chain_stats.tx_count` ≥ `60000` (values only grow); second explorer (blockchain.info `rawaddr`) HTTP 200 with `n_tx` ≥ `60000`; the earliest-100 export (fetched by offset) has its first transaction in block `0` with timestamp `2009-01-03T18:15:05Z`; OFAC SDN list file downloaded (HTTP 200) and the address string not found in it → `NO MATCH`; caps: S3 = most recent 100 plus earliest 100; `skip: S5, S7, S8`.

### 9.11 Lawful-request mapping

| Lead type | Recipient | Request type default | Identifiers to cite | Ask for |
|---|---|---|---|---|
| Owner of a counterparty address labelled as an exchange/service | the labelled VASP (name as captured from the explorer label — the agency verifies the entity) | preservation, then disclosure (subscriber/registration data) | the labelled address, the transaction IDs linking it to the target, UTC block times, amounts in native units | KYC data of the account that controls the address, deposit/withdrawal records for the listed transactions |
| Target address controlled by a service (label on the target itself) | that VASP | preservation, then disclosure (subscriber/registration data) | target address, label EV, tx IDs | preservation, then disclosure (subscriber/registration data) |

### 9.12 Duration estimate

Typical FULL-mode duration: 10–25 minutes; up to 45 for addresses with thousands of transactions (pagination). Longest steps S3 and S6.
