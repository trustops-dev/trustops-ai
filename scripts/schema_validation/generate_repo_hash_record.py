#!/usr/bin/env python3
"""
Generate a separate Repository Verification Hash Record (`repo_verification_hashes.json`)
identifying the exact Git revision SHA, repository paths, byte counts, and exact-byte
SHA-256 values while preserving the original `manifest_v1_18.json` archive record untouched.

Usage (from repository root after committing PR #32 fixes):
    python path/to/generate_repo_hash_record.py --out repo_verification_hashes.json
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

TRACKED_FILENAMES = [
    "001_core.sql",
    "g01_isolated_diagnostic_runner.py",
    "independent_probes.py",
    "manifest_v1_18.json",
    "probe_remaining_controls.py",
    "reproduce_findings.py",
    "run_native_verification.py",
    "run_s1_01_regression_suite.py",
    "run_windows_g01_verification.bat",
    "s1_01_validation_report.json",
    "test_g01_isolated_diagnostic.py",
    "test_sdk_clean_install_smoke.py",
    "trustops_sdk.py",
    "updated_schemas_v18.md",
    "validate_s1_01_schema_v1_11.py",
    "week_2.md",
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
}


def git_cmd(repo_root: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "UNAVAILABLE_NOT_A_GIT_REPO"


_UTC: datetime.tzinfo = (
    datetime.UTC if sys.version_info >= (3, 11) else datetime.timezone(datetime.timedelta(0))
)


def sha256_exact(path: pathlib.Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate repo_verification_hashes.json from exact committed bytes"
    )
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--out", default="repo_verification_hashes.json", help="Output JSON path")
    args = parser.parse_args()

    repo_root = pathlib.Path(args.repo_root).resolve()
    entries = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for fname in sorted(files):
            if fname in TRACKED_FILENAMES:
                full = pathlib.Path(root) / fname
                rel = full.relative_to(repo_root).as_posix()
                size, digest = sha256_exact(full)
                entries.append(
                    {
                        "repo_path": rel,
                        "filename": fname,
                        "bytes": size,
                        "sha256": digest,
                    }
                )
    entries.sort(key=lambda x: str(x["repo_path"]))

    record = {
        "record_type": "REPOSITORY_COMMITTED_BYTE_VERIFICATION",
        "generated_at_utc": datetime.datetime.now(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_revision": git_cmd(repo_root, "rev-parse", "HEAD"),
        "git_short_sha": git_cmd(repo_root, "rev-parse", "--short", "HEAD"),
        "git_branch": git_cmd(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "git_working_tree_clean": git_cmd(repo_root, "status", "--porcelain") == "",
        "archive_manifest_preserved": "manifest_v1_18.json (historical archive snapshot, intentionally unmodified)",
        "tracked_file_count": len(entries),
        "files": entries,
    }

    out_path = pathlib.Path(args.out)
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} exact-byte repository SHA-256 entries to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
