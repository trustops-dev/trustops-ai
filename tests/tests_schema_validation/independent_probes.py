#!/usr/bin/env python3
"""
Standalone 6-Case Independent Reproduction Probe Runner (Updated for S1-01 Schema v1.11)
Originally supplied in Nour El-Rouby's `TrustOps_v1.9_Review_and_Reproduction.zip`, now
bundled directly in the v1.11 deliverable archive and parameterized against:
  - Specification: updated_schemas_v18.md
  - Validator: validate_s1_01_schema_v1_11.py
  - Regression Suite: run_s1_01_regression_suite.py
Verifies that all 6 independent negative probes are deterministically REJECTED (`actual_pass: false`).
"""

import copy
import json
import os
import pathlib
import sys
import tempfile

_REPO_SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    "build", "dist", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "negative_and_variant_probes", ".tox", ".eggs",
}

def _find_repo_root(start: "pathlib.Path") -> "pathlib.Path":
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return start.resolve().parent if start.is_file() else start.resolve()

def _find_repo_file(filename: str, start: "pathlib.Path", prefer_in: tuple = (), avoid_in: tuple = ()) -> "pathlib.Path":
    here = start.resolve().parent if start.is_file() else start.resolve()
    direct = here / filename
    if direct.is_file():
        return direct
    cwd_direct = pathlib.Path.cwd() / filename
    if cwd_direct.is_file():
        return cwd_direct
    repo_root = _find_repo_root(here)
    matches = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(d for d in dirs if d not in _REPO_SKIP_DIRS and not d.endswith(".egg-info"))
        if filename in files:
            matches.append(pathlib.Path(root) / filename)
    if not matches:
        raise FileNotFoundError(f"Could not locate {filename} from {here} or repo root {repo_root}")
    def _rank(p: "pathlib.Path") -> tuple:
        parts = set(p.parts)
        pref_score = 0 if (not prefer_in or any(x in parts for x in prefer_in)) else 1
        avoid_score = 1 if any(x in parts for x in avoid_in) else 0
        return (avoid_score, pref_score, len(p.parts), str(p))
    matches.sort(key=_rank)
    return matches[0]

HERE = pathlib.Path(__file__).resolve().parent
for _needed in ('run_s1_01_regression_suite.py', 'validate_s1_01_schema_v1_11.py'):
    _p = _find_repo_file(_needed, HERE)
    if str(_p.parent) not in sys.path:
        sys.path.insert(0, str(_p.parent))

import run_s1_01_regression_suite as r
import validate_s1_01_schema_v1_11 as v


def a(w: dict, e: str) -> dict:
    return r.find_event(w, e)["attributes"]


def stale(w: dict) -> None:
    a(w, "e27")["trusted_source"]["record_version"] = "different_version"
    a(w, "e27")["trusted_source"]["decision_record_seq"] = 999
    a(w, "e25")["result_payload"]["data"]["approval_evidence"]["record_version"] = "different_version"
    a(w, "e25")["result_payload"]["data"]["approval_evidence"]["decision_record_seq"] = 999


def prop(w: dict) -> None:
    a(w, "e33")["dispatch_claim_consumption"]["preallocated_at_proposal_id"] = "NONEXISTENT"
    w["execution_budget_telemetry"]["dispatch_claim_ledger"][0]["preallocated_at_proposal_id"] = "NONEXISTENT"


def norm(w: dict) -> None:
    l = w["request"]["normalization_provenance"]["raw_to_normalized_field_links"][0]
    l.update(
        derivation_mode="INVALID_UNDECLARED_MODE",
        raw_char_span={"start": 0, "end": 3},
        raw_substring="fabricated",
    )


def score(w: dict) -> None:
    a(w, "e1")["retrieved_documents"][0]["score"] = 999999.0


def params(w: dict) -> None:
    a(w, "e29")["generation_parameters"].update(top_p=-1, max_output_tokens=-10)


def refusal(w: dict) -> None:
    a(w, "e29")["execution_status"] = "REFUSED"


def run_independent_probes(spec_path: pathlib.Path | None = None) -> list[dict]:
    target_spec = spec_path or _find_repo_file("updated_schemas_v18.md", HERE)
    s = target_spec.read_text(encoding="utf-8")
    wts = [x[1] for x in r.extract_json_blocks(s)[9:13]]

    cases = [
        ("approval_source_versions_disagree", 1, stale),
        ("consumption_proposal_unresolved", 1, prop),
        ("normalization_unknown_mode_bypasses_span", 1, norm),
        ("nonfinite_retrieval_score", 4, score),
        ("invalid_generation_parameters", 1, params),
        ("refused_model_still_supplies_tool_proposal", 1, refusal),
    ]
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        out = pathlib.Path(tmpdir)
        for name, i, mut in cases:
            w = copy.deepcopy(wts[i - 1])
            mut(w)
            txt = r.rebuild_spec_with_wt(s, i, w)
            if name == "nonfinite_retrieval_score":
                txt = txt.replace("999999.0", "1e309")
            p = out / f"{name}.md"
            p.write_text(txt, encoding="utf-8")
            valid, codes, _ = v.SpecValidator(str(p), check_report_sync=False).validate()
            results.append({"case": name, "expected": "REJECT", "actual_pass": valid, "codes": codes})
    return results


if __name__ == "__main__":
    res = run_independent_probes()
    print(json.dumps(res, indent=2))
    if any(item["actual_pass"] for item in res):
        sys.exit(1)
    sys.exit(0)