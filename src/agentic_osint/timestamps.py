"""Verify supplied RFC3161 proofs against an explicitly configured trust store.

No CA is downloaded or silently trusted. These helpers never obtain a timestamp,
change a proof, infer publication time, or claim the local file existed at acquisition.
"""
from pathlib import Path
import subprocess
import tempfile

from .common import bounded_bytes, digest, hash_file


def verify_rfc3161(manifest: Path, proof: Path, ca_file: Path, *, openssl: str = "openssl") -> dict:
    sources = [manifest, proof, ca_file]
    data = [bounded_bytes(path, 10_000_000) for path in sources]
    expected = [digest(raw) for raw in data]
    with tempfile.TemporaryDirectory(prefix="osint-ts-verify-") as directory:
        snapshots = [Path(directory) / name for name in ["manifest", "proof", "trust.pem"]]
        for path, raw in zip(snapshots, data):
            with path.open("xb") as stream:
                stream.write(raw)
        result = subprocess.run([openssl, "ts", "-verify", "-data", str(snapshots[0]), "-in", str(snapshots[1]),
                                 "-CAfile", str(snapshots[2])], capture_output=True, timeout=30, check=False)
        stable = all(hash_file(path)[0] == sha for path, sha in zip(snapshots, expected))
    stable = stable and all(hash_file(path)[0] == sha for path, sha in zip(sources, expected))
    passed = result.returncode == 0
    return {"result": "VALID_AGAINST_CONFIGURED_TRUST" if passed and stable else "FAIL", "manifest_sha256": expected[0],
            "proof_sha256": expected[1], "trust_store_sha256": expected[2], "inputs_unchanged": stable,
            "exit_code": result.returncode, "validation_output": (result.stdout + result.stderr).decode("utf-8", errors="replace")[:10000],
            "limitations": "Configured CA trust is an agency decision. Proof covers sealed manifest existence, not source truth or acquisition time."}
