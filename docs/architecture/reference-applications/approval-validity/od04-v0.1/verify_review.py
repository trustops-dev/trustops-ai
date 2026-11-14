"""Check OD-04 authored review structure, not runtime approval or race safety."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATES = {
    "REQUEST_CAPTURED",
    "POLICY_CHECKED",
    "SUPPLIER_CHECKED",
    "APPROVAL_CALCULATED",
    "APPROVAL_PENDING",
    "APPROVED",
    "PO_CREATION",
    "COMPLETION",
}


def validate():
    response = json.loads((BASE / "response.json").read_text())
    table = json.loads((BASE / "cases.json").read_text())
    document = (BASE / "README.md").read_text()
    checks = []

    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append({"check": name, "status": "PASS"})

    check(
        "Draft response remains unsent and jointly unaccepted",
        response["submission_status"] == "NOT_SENT"
        and response["joint_acceptance"] == "PENDING"
        and response["signed_acceptances"] == [],
    )
    check(
        "No runtime implementation claimed",
        response["runtime_implemented"] is False and table["proposed_design_only"] is True,
    )
    check(
        "Overall amendment remains explicit",
        response["overall_draft_disposition"] == "AMEND" and "AMEND overall" in document,
    )
    check(
        "Confirmed observation semantics retained",
        response["confirmed_semantics_preserved"] == "OD-APP-OBS-01",
    )
    check("Versions agree", response["version"] == table["version"] == "0.1")
    expected_clauses = {f"V{i:02d}" for i in range(1, 9)}
    check(
        "Exactly eight unique clauses",
        len(response["clauses"]) == 8
        and {c["id"] for c in response["clauses"]} == expected_clauses,
    )
    for clause in response["clauses"]:
        check(
            clause["id"] + ": scoped disposition and reviewer",
            clause["draft_disposition"] in {"ACCEPT", "AMEND"}
            and bool(clause["required_reviewers"])
            and clause["acceptance"] == "PENDING_JOINT_REVIEW"
            and clause["id"] in document,
        )
    cases = table["cases"]
    check(
        "Exactly 27 unique paper cases",
        len(cases) == 27 and len({c["case_id"] for c in cases}) == 27,
    )
    covered = set()
    for case in cases:
        cid = case["case_id"]
        expected = case["expected"]
        covered.update(case["clauses"])
        check(
            cid + ": known states and clauses",
            case["state_before"] in STATES
            and expected["state_after"] in STATES
            and bool(case["clauses"])
            and set(case["clauses"]) <= expected_clauses,
        )
        check(
            cid + ": no example grants dispatch",
            expected["direct_dispatch_authorized_by_this_example"] is False,
        )
        check(
            cid + ": preserve history and root guards",
            expected["preserve_history"] is True
            and expected["reset_root_budget_or_claim"] is False,
        )
        check(
            cid + ": scenario and provenance requirements",
            bool(case["review_condition"]) and all(case["evidence_required"].values()),
        )
        if expected["may_prepare_new_po_proposal_after_validation"]:
            check(
                cid + ": new proposal is not dispatch",
                expected["state_after"] == "APPROVED"
                and expected["review_action"] == "PREPARE_FRESH_PROPOSAL_AND_CHECK",
            )
        if case["state_before"] == "PO_CREATION":
            check(
                cid + ": no effect rewind",
                expected["state_after"] == "PO_CREATION"
                and not expected["may_prepare_new_po_proposal_after_validation"],
            )
        if case["state_before"] == "COMPLETION":
            check(cid + ": preserve completed history", expected["state_after"] == "COMPLETION")
    check("Every clause covered", covered == expected_clauses)
    by_id = {c["case_id"]: c for c in cases}
    for cid in ["OD04-C05", "OD04-C06", "OD04-C07"]:
        check(
            cid + ": revised request starts at capture",
            by_id[cid]["expected"]["state_after"] == "REQUEST_CAPTURED",
        )
    for cid in [
        "OD04-C08",
        "OD04-C09",
        "OD04-C10",
        "OD04-C11",
        "OD04-C16",
        "OD04-C17",
        "OD04-C19",
        "OD04-C20",
        "OD04-C22",
        "OD04-C24",
        "OD04-C25",
    ]:
        check(cid + ": invalid authority halts", by_id[cid]["expected"]["review_action"] == "HALT")
    check(
        "Revocation race explicitly suppresses stale dispatch",
        by_id["OD04-C12"]["expected"]["review_action"] == "SUPPRESS_STALE_DISPATCH",
    )
    check(
        "Unknown effects and duplicate continuations stay read-only",
        all(
            by_id[cid]["expected"]["review_action"] == "READ_ONLY_RECOVERY_PENDING"
            for cid in ["OD04-C13", "OD04-C21", "OD04-C27"]
        ),
    )
    check(
        "Late approval preserves old BLOCK then new proposal",
        by_id["OD04-C14"]["authoritative_order_example"]
        == [
            "old PO proposal",
            "BLOCK and suppression",
            "APPROVED decision",
            "trusted validated continuation",
            "new PO proposal",
            "fresh policy check",
        ],
    )
    return {
        "result": "PASS",
        "scope": "Authored review structure and stated expectation consistency only; not execution or proof of approval validity, canonical schema fit, currentness or race safety",
        "cases": len(cases),
        "clause_count": 8,
        "check_count": len(checks),
        "checks": checks,
        "joint_acceptance": "PENDING",
        "runtime": "NOT_RUN",
        "python": sys.version.split()[0],
        "file_hashes": {
            n: hashlib.sha256((BASE / n).read_bytes()).hexdigest()
            for n in ["README.md", "response.json", "cases.json", "verify_review.py"]
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if output.is_relative_to(BASE):
        parser.error("Write the validation report outside the reviewed folder")
    try:
        report, code = validate(), 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report, code = {"result": "FAIL", "error": str(exc)}, 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
