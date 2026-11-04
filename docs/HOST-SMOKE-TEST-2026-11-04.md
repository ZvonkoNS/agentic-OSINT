# Limited host and provider smoke test — 2026-11-04

Scope: one harmless L1-WEB self-test using `https://example.com/`; original agent v1.3.0, commit `f97f9a96c46b800a02f5f5ca822b52406faee065`. Windows, Brave browser; exact host model versions were not exposed. These are individual observations, not a reliability benchmark. No personal identifiers were sent in these tests.

Gemini Flash could not open the raw GitHub instruction URL. Uploading the Markdown file worked. Its run reported missing network, browser and code capabilities and an overall INCOMPLETE result. However, it marked resource enumeration done from a partial search transcript, treated the skip on creating a new archive snapshot as a skip of the archive step, and claimed workflow verification despite incomplete supporting checks. These individual claims should not be treated as verified. An attempted retest with clarified instructions returned a service error; a successful independent retest is needed before claiming the changes resolve model behavior.

ChatGPT Pro was asked to run the same original instruction and began inspecting the pinned agent and source tree. It requested access to Brave; the host run was still in progress when this note was prepared. A running or self-reported host test is not an independently verified result.

Separate, direct read-only requests from the local computer returned HTTP 200 for `https://example.com/`, Google DNS for its A records, Verisign RDAP for the domain, and the Wayback availability API for the same domain. A request to crt.sh timed out. These are one-time endpoint availability observations, not proof that a model performed the requests, that provider data is complete, or that a full agent workflow passed.

The following remain untested in this evaluation: the other 14 collectors, the verifier and orchestrator, real-case intake and evidence packs on either host, authenticated or paid provider workflows, interruptions and recovery on the hosts, and repeated adversarial trials. The v1.3.1 clarification is a prompt change, not an enforcement mechanism. Investigators must inspect actual artifacts, destinations, coverage and claim support.
