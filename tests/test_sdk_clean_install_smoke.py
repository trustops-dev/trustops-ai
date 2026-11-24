#!/usr/bin/env python3
"""
Installed-SDK Out-of-Tree Smoke Test (PR #32 P1 Verification).

Verifies that `import trustops_sdk.trustops_sdk` succeeds from a temporary directory
OUTSIDE the repository checkout, with PYTHONPATH unset and zero manually copied files,
and that the bundled `validate_s1_01_schema_v1_11` dependency resolves cleanly.

Usage:
  - In CI (after clean non-editable install):
      pytest tests/test_sdk_clean_install_smoke.py
  - Or standalone:
      python test_sdk_clean_install_smoke.py
  - Or full end-to-end clean-venv wheel install verification:
      python test_sdk_clean_install_smoke.py --build-venv path/to/trustops_sdk_package
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

SMOKE_SNIPPET = """
import json
import trustops_sdk
import trustops_sdk.trustops_sdk as sdk_mod

gate = sdk_mod.InMemoryIngestionGate()
code, status, _ = gate.ingest_trace({"trace_id": "invalid_minimal", "schema_version": "1.18.0-draft"})
assert code == 422 and status == "ERR_STRUCTURAL_VALIDATION_FAILED", (code, status)

stub = sdk_mod.PreToolPolicyStubClient(environment="test")
assert stub.environment == "test"

tx_gate = sdk_mod.SqliteTransactionalClaimGate(":memory:")
tx_gate.seed_authoritative_records(
    "SUP-01", "APPROVED", "sup_v1", "APR-01", "areq_1", "APPROVED", "apr_v1", 1
)
ok, c_status = tx_gate.consume_claim_atomic(
    "cons_1", "claim_1", "wf_1", "prop_1", "chk_1", "call_1",
    "SUP-01", "sup_v1", "APR-01", "apr_v1", 1
)
assert ok is True and c_status == "CONSUMED_ATOMICALLY", (ok, c_status)
tx_gate.conn.close()

print(json.dumps({
    "import_ok": True,
    "sdk_version": sdk_mod.SDK_VERSION,
    "sdk_file": sdk_mod.__file__,
    "validator_file": sdk_mod.schema_validator.__file__,
    "permitted_keys_count": len(sdk_mod.schema_validator.PERMITTED_INFERENCE_TOP_KEYS),
    "allowed_keys_count": len(sdk_mod.schema_validator.ALLOWED_TRACE_TOP_KEYS),
}))
"""


def run_out_of_tree_import_check(python_executable: str = sys.executable) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    with tempfile.TemporaryDirectory(prefix="trustops_sdk_smoke_cwd_") as outside_dir:
        proc = subprocess.run(
            [python_executable, "-c", SMOKE_SNIPPET],
            cwd=outside_dir,
            env=env,
            capture_output=True,
            text=True,
        )
    if proc.returncode != 0:
        raise AssertionError(
            f"Out-of-tree SDK import failed (exit={proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return json.loads(proc.stdout.strip())


class TestInstalledSdkSmoke(unittest.TestCase):
    def test_import_trustops_sdk_from_outside_checkout_without_pythonpath(self) -> None:
        result = run_out_of_tree_import_check(sys.executable)
        self.assertTrue(result["import_ok"])
        self.assertGreater(result["permitted_keys_count"], 0)
        self.assertGreater(result["allowed_keys_count"], 0)


def verify_clean_non_editable_venv(package_dir: pathlib.Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="trustops_clean_venv_") as venv_parent:
        venv_dir = pathlib.Path(venv_parent) / "venv"
        venv_proc = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            capture_output=True,
            text=True,
        )
        if os.name == "nt":
            vpy = str(venv_dir / "Scripts" / "python.exe")
        else:
            vpy = str(venv_dir / "bin" / "python")
        if venv_proc.returncode == 0:
            subprocess.run(
                [vpy, "-m", "pip", "install", "--no-deps", "--no-build-isolation", str(package_dir.resolve())],
                check=True,
            )
        else:
            if venv_dir.exists():
                shutil.rmtree(venv_dir)
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_dir)], check=True)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "--python",
                    vpy,
                    "install",
                    "--no-deps",
                    "--no-build-isolation",
                    str(package_dir.resolve()),
                ],
                check=True,
            )
        result = run_out_of_tree_import_check(vpy)
        assert "site-packages" in result["sdk_file"].replace("\\", "/"), (
            f"Expected non-editable site-packages install, got: {result['sdk_file']}"
        )
        assert "site-packages" in result["validator_file"].replace("\\", "/"), (
            f"Expected validator packaged in site-packages, got: {result['validator_file']}"
        )
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Out-of-tree clean-install SDK smoke test")
    parser.add_argument(
        "--build-venv",
        type=str,
        default=None,
        help="Path to trustops_sdk package dir for clean non-editable venv test",
    )
    args, remaining = parser.parse_known_args()
    if args.build_venv:
        res = verify_clean_non_editable_venv(pathlib.Path(args.build_venv))
        print(json.dumps(res, indent=2))
        sys.exit(0)
    sys.argv = [sys.argv[0], *remaining]
    unittest.main(verbosity=2)
