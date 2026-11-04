# Contributing

Use synthetic fixtures or reserved public test identifiers. Do not upload real case material, personal data, credentials or illegal content to issues or pull requests.

## Development workflow

Use Python 3.11 or newer. From a clean checkout:

```console
python -m pip install -c requirements.lock -e ".[reports,dev]"
python -m unittest discover -s tests
python build/build.py --check
```

The `agents/` files are generated. Edit `build/core.md`, a task in `build/tasks/`, or a definition in `build/standalone/`, then run `python build/build.py` and inspect the changes. Do not run historical migration scripts as part of the supported build.

Do not normalize evidence fixture bytes. `.gitattributes` defines generated-text line endings and binary treatment. Calculate hashes from files after writing. A fixture change needs an explicit rationale, updated expected metadata and a meaningful regression check.

## A useful change

- Describe the concrete problem and resulting behavior with a harmless reproducer.
- Keep source changes focused and add meaningful regression checks.
- Update schemas, examples, documentation and generated agents as needed.
- Declare unsupported or untested behavior instead of adding a broader guarantee.

Provider adapters need fixtures for positive, negative, malformed, blocked, truncated, renamed and paginated responses as applicable. Keep live smoke tests separate from deterministic offline tests. Record versions and coverage; a provider response is not proof of ownership or identity.

Validation changes need mutation cases: changed bytes, unsupported claims, missing required work, denied operations and broken references. Test multilingual and long-value rendering when changing reports. Preserve raw identifiers and distinguish source dates, capture times and estimates.

## Review and release

Submit a pull request explaining the problem, implementation, validation and material limits. Windows/Linux checks should pass for the exact revision. Check generated output, fixture hashes, schemas and offline tests before publishing a tagged release. Record method version and commit; historical verification uses the matching method, not today's `main`.

Use [SECURITY.md](SECURITY.md) for security issues. For ordinary bugs, open a [GitHub issue](https://github.com/ZvonkoNS/agentic-OSINT/issues) with a minimal synthetic example and exact version information.

## Verify a published release asset

The tagged-release workflow is configured to create SHA256SUMS and GitHub OIDC/Sigstore attestations for its assets. This is a release mechanism, not a claim that an attestation already exists for a particular version. After a tagged workflow has succeeded and published an attested asset, download it and use the GitHub CLI:

```console
gh attestation verify ASSET --repo ZvonkoNS/agentic-OSINT
```

Replace `ASSET` with the downloaded file's path. Check the exact release/tag and workflow identity reported by verification. Byte hashes detect changes relative to the expected digest; an attestation provides a separate provenance check. Do not infer an attestation for an older or manually uploaded asset, and do not overwrite an existing release to replace its bytes.
