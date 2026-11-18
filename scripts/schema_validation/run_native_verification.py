#!/usr/bin/env python3
"""
Cross-Platform Native Verification Launcher for TrustOps AI Package Release v1.16.0.
Double-click `run_windows_g01_verification.bat` on Windows (no terminal commands needed),
or run `python run_native_verification.py`.
Executes all 7 offline verification suites natively on the host OS (Windows msvcrt or POSIX fcntl)
and saves `native_host_verification_report.json` with exact OS, Python version, and pass/fail logs.
No live provider calls or API keys are used.
"""

import datetime
import json
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CHECKS = [
    ("baseline_validator", [sys.executable, "validate_s1_01_schema_v1_11.py"]),
    (
        "regression_suite_103",
        [
            sys.executable,
            "run_s1_01_regression_suite.py",
            "--report-out",
            "native_suite_check.json",
        ],
    ),
    ("independent_probes_6", [sys.executable, "independent_probes.py"]),
    ("reproduce_findings_10", [sys.executable, "reproduce_findings.py", "."]),
    ("probe_remaining_controls_14", [sys.executable, "probe_remaining_controls.py", "."]),
    ("g01_diagnostic_tests_33", [sys.executable, "test_g01_isolated_diagnostic.py"]),
    ("trustops_sdk_selftest", [sys.executable, "trustops_sdk.py"]),
]


def main() -> int:
    print("=" * 72)
    print("TrustOps AI v1.16.0 — Native Host Offline Verification Suite")
    print(f"OS: {platform.platform()} | Python: {sys.version.split()[0]} | os.name: {os.name}")
    print("=" * 72)

    results = []
    all_ok = True
    for name, cmd in CHECKS:
        print(f"\n>>> Running {name} ...")
        proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        passed = proc.returncode == 0
        if not passed:
            all_ok = False
        print(f"    Status: {'PASS' if passed else 'FAIL'} (exit={proc.returncode})")
        if not passed:
            print(proc.stdout[-800:])
            print(proc.stderr[-800:])
        results.append(
            {
                "check": name,
                "command": " ".join(cmd),
                "exit_code": proc.returncode,
                "passed": passed,
                "stdout_tail": proc.stdout[-1500:],
                "stderr_tail": proc.stderr[-1500:],
            }
        )

    # Clean up temporary suite check file
    tmp_suite = os.path.join(HERE, "native_suite_check.json")
    if os.path.exists(tmp_suite):
        try:
            os.remove(tmp_suite)
        except Exception:
            pass

    report = {
        "package_release_id": "v1.16.0",
        "executed_at_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": platform.platform(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "python_version": sys.version,
        "live_provider_calls": 0,
        "all_checks_passed": all_ok,
        "checks": results,
    }
    out_file = os.path.join(HERE, "native_host_verification_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 72)
    print(f"OVERALL RESULT: {'ALL 7 SUITES PASSED' if all_ok else 'SOME CHECKS FAILED'}")
    print(f"Saved report to: {out_file}")
    print("=" * 72)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
