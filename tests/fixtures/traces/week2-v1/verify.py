"""Check the two application files with the v1.16 per-walkthrough validator."""

import argparse
import hashlib
import json
import runpy
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

REVIEWED_REVISION = "c645cfc72ef9d718cfe326990059a5ca0a37b3a1"
VALIDATOR_HASHES = {
    REVIEWED_REVISION: "b406f4b35949205cd90dbf19df0a333a1836a13d1cbd2f922b7c88d802a23d5b",
    "882505573b3d28db362532e038100a91e9c0ea52": (
        "c55e9c32a94cb94951f9719a713b8f055ed2c8a9eb8dc25b3d4ef49044acd458"
    ),
}
VALIDATOR = "scripts/schema_validation/validate_s1_01_schema_v1_11.py"
FIXTURES = ("01-procurement-success.json", "03-rag-grounded.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-commit", choices=VALIDATOR_HASHES, default=REVIEWED_REVISION)
    revision = parser.parse_args().schema_commit
    directory = Path(__file__).resolve().parent
    source = subprocess.check_output(["git", "show", f"{revision}:{VALIDATOR}"], cwd=directory)
    if hashlib.sha256(source).hexdigest() != VALIDATOR_HASHES[revision]:
        raise ValueError("Unexpected schema validator hash")
    with TemporaryDirectory() as temp:
        path = Path(temp) / "validator.py"
        path.write_bytes(source)
        validator = runpy.run_path(str(path))["SpecValidator"]
    failed = False
    for filename in FIXTURES:
        raw = (directory / filename).read_bytes()
        trace = json.loads(raw)
        check = validator("")
        # The package CLI validates Markdown examples. Use its actual per-trace check here.
        check._validate_walkthrough(1, trace)
        failed |= bool(check.failures)
        print(
            json.dumps(
                {
                    "fixture": filename,
                    "schema_commit": revision,
                    "finding_count": len(check.failures),
                    "trace_id": trace["trace_id"],
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "assertions": sum(check.counts.values()),
                    "findings": check.failures,
                    "status": "FAIL" if check.failures else "PASS",
                }
            )
        )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
