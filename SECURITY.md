# Security policy

## Scope and versions

Security fixes target current `main` and the latest released version. Historical releases remain method artifacts; availability does not imply continuing fixes. Use the fixed version for new work and preserve the original method with historical packs.

Relevant issues include unauthorized requests, scope/permission bypass, source instructions triggering actions, unsafe parsing/extraction, secret disclosure, integrity-check bypass, active generated output and misleading verified statuses.

## Report an issue

Use **Report a vulnerability** on the [repository Security page](https://github.com/ZvonkoNS/agentic-OSINT/security) when private reporting is enabled. If unavailable, open an issue requesting a private channel **without** publishing exploit or sensitive details. No monitored private email or response-time commitment is claimed.

Include version/commit, environment, a minimal synthetic reproducer, expected/observed behavior, impact and a suggested mitigation. Do not include investigative data, personal data, API keys, access tokens, prohibited material or an exploit against a third-party service.

## Operational boundary

Use appropriate isolation for parsing/capture. Sources and imported packs are untrusted. Public requests may be logged; processing in an AI product discloses data to that operator under its applicable terms/configuration. Use approved destinations and secret mechanisms, with organizational retention and access rules.

For unexpected prohibited content, stop further access and distribution and follow the approved incident procedure. The model must not improvise retention, quarantine or deletion. A local hash or self-consistent event chain does not replace authenticated custody and a separately trusted seal.

Verified categories describe checks actually performed. They do not certify source truth, authority, admissibility, internet completeness or operator competence.
