#!/usr/bin/env python3
"""
Cross-Platform Native Verification Launcher for TrustOps AI (Repository & Archive Layouts).
Resolves all 7 offline verification suites dynamically against the repository layout
(or flat archive layout when run from an unpacked archive) without custom PYTHONPATH
or manual file copies.
Saves `native_host_verification_report.json` with Python patch version, exact command,
resolved paths, and PASS/FAIL results for each of the 7 steps.
No live provider calls or API keys are used.
"""
import datetime
import json
import os
import pathlib
import platform
import subprocess
import sys
import tempfile

_REPO_SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    "build", "dist", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "negative_and_variant_probes", ".tox", ".eggs",
}


def find_repo_root(start: pathlib.Path) -> pathlib.Path:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return start.resolve().parent if start.is_file() else start.resolve()


def find_repo_file(
    filename: str,
    repo_root: pathlib.Path,
    here: pathlib.Path,
    prefer_in: tuple = (),
    avoid_in: tuple = (),
) -> pathlib.Path:
    if (here / filename).is_file() and not any(x in (here / filename).parts for x in avoid_in):
        return here / filename
    matches = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(d for d in dirs if d not in _REPO_SKIP_DIRS and not d.endswith(".egg-info"))
        if filename in files:
            matches.append(pathlib.Path(root) / filename)
    if not matches:
        raise FileNotFoundError(f"Could not locate {filename} under {repo_root}")

    def _rank(p: pathlib.Path) -> tuple:
        parts = set(p.parts)
        pref_score = 0 if (not prefer_in or any(x in parts for x in prefer_in)) else 1
        avoid_score = 1 if any(x in parts for x in avoid_in) else 0
        return (avoid_score, pref_score, len(p.parts), str(p))

    matches.sort(key=_rank)
    return matches[0]


def _rel(p: pathlib.Path, base: pathlib.Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    repo_root = find_repo_root(here)
    py_patch = platform.python_version()

    spec_path = find_repo_file("updated_schemas_v18.md", repo_root, here)
    validator_path = find_repo_file("validate_s1_01_schema_v1_11.py", repo_root, here, avoid_in=("trustops_sdk",))
    regression_path = find_repo_file("run_s1_01_regression_suite.py", repo_root, here)
    ind_probes_path = find_repo_file("independent_probes.py", repo_root, here)
    repro_path = find_repo_file("reproduce_findings.py", repo_root, here)
    controls_path = find_repo_file("probe_remaining_controls.py", repo_root, here)
    g01_test_path = find_repo_file("test_g01_isolated_diagnostic.py", repo_root, here)
    sdk_path = find_repo_file("trustops_sdk.py", repo_root, here, prefer_in=("trustops_sdk",))

    with tempfile.TemporaryDirectory(prefix="trustops_native_suite_") as tmpdir:
        tmp_report = str(pathlib.Path(tmpdir) / "native_suite_check.json")
        checks = [
            (
                "baseline_validator",
                [sys.executable, _rel(validator_path, repo_root), _rel(spec_path, repo_root)],
            ),
            (
                "regression_suite_113",
                [
                    sys.executable,
                    _rel(regression_path, repo_root),
                    "--spec",
                    _rel(spec_path, repo_root),
                    "--validator",
                    _rel(validator_path, repo_root),
                    "--report-out",
                    tmp_report,
                ],
            ),
            (
                "independent_probes_6",
                [sys.executable, _rel(ind_probes_path, repo_root)],
            ),
            (
                "reproduce_findings_10",
                [sys.executable, _rel(repro_path, repo_root), "."],
            ),
            (
                "probe_remaining_controls_14",
                [sys.executable, _rel(controls_path, repo_root), "."],
            ),
            (
                "g01_diagnostic_tests_33",
                [sys.executable, _rel(g01_test_path, repo_root)],
            ),
            (
                "trustops_sdk_selftest",
                [sys.executable, _rel(sdk_path, repo_root), _rel(spec_path, repo_root)],
            ),
        ]

        print("=" * 72)
        print("TrustOps AI v1.18.0 — Native Host Offline Verification Suite")
        print(f"OS: {platform.platform()} | Python: {py_patch} | os.name: {os.name}")
        print(f"Repo Root: {repo_root}")
        print(f"Spec Path: {_rel(spec_path, repo_root)}")
        print("=" * 72)

        results = []
        all_ok = True
        for idx, (name, cmd) in enumerate(checks, start=1):
            print(f"\n[{idx}/7] Running {name} ...")
            print(f"    Command: {' '.join(cmd)}")
            proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
            passed = proc.returncode == 0
            if not passed:
                all_ok = False
            print(f"    Status: {'PASS' if passed else 'FAIL'} (exit={proc.returncode})")
            if not passed:
                print(proc.stdout[-800:])
                print(proc.stderr[-800:])
            results.append(
                {
                    "step": idx,
                    "check": name,
                    "command": " ".join(cmd),
                    "cwd": str(repo_root),
                    "exit_code": proc.returncode,
                    "passed": passed,
                    "stdout_tail": proc.stdout[-1500:],
                    "stderr_tail": proc.stderr[-1500:],
                }
            )

    report = {
        "package_release_id": "v1.18.0",
        "executed_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": platform.platform(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "python_patch_version": py_patch,
        "python_version": sys.version,
        "repo_root": str(repo_root),
        "documented_command": f"{sys.executable} {_rel(pathlib.Path(__file__).resolve(), repo_root)}",
        "live_provider_calls": 0,
        "all_checks_passed": all_ok,
        "checks": results,
    }
    out_file = here / "native_host_verification_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"OVERALL RESULT: {'ALL 7 SUITES PASSED' if all_ok else 'SOME CHECKS FAILED'} (Python {py_patch})")
    print(f"Saved report to: {out_file}")
    print("=" * 72)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())