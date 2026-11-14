"""Offline OD-03 specification oracle. Never import into an application or policy engine."""

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parent


def outcome(config, case):
    """Return review labels only; no tool response, workflow verdict or authorization."""
    amount = case["input"]["total_amount"]
    if (
        not isinstance(amount, str)
        or re.fullmatch(config["amount_input"]["pattern"], amount) is None
    ):
        return {"review_outcome": "REJECT_BEFORE_CALCULATION", "reason": "INVALID_AMOUNT"}
    value = Decimal(amount)
    if value <= 0:
        return {"review_outcome": "REJECT_BEFORE_CALCULATION", "reason": "INVALID_AMOUNT"}
    for flag, reason in [
        ("configuration_present", "MISSING_CONFIGURATION"),
        ("policy_text_matches", "TEXT_CONFIG_CONFLICT"),
        ("policy_version_matches", "POLICY_VERSION_MISMATCH"),
        ("trusted_request_matches", "REQUEST_CONTEXT_MISMATCH"),
    ]:
        if case.get(flag) is False:
            return {"review_outcome": "UNRESOLVED", "reason": reason}
    rule = deepcopy(config["rules"][0])
    rule.update(case.get("config_mutation", {}))
    if case["input"]["currency"] != rule["currency"]:
        return {"review_outcome": "UNRESOLVED", "reason": "UNSUPPORTED_CURRENCY"}
    if (
        rule["threshold"] is None
        or rule["approval_level"] != "manager"
        or rule["comparator"] != "GT"
    ):
        return {"review_outcome": "UNRESOLVED", "reason": "INVALID_CONFIGURATION"}
    required = value > Decimal(rule["threshold"])
    return {
        "review_outcome": "CALCULATED",
        "approval_required": required,
        "approval_level": rule["approval_level"] if required else None,
        "normalized_total": format(value, ".2f"),
    }


def validate():
    config = json.loads((BASE / "candidate-config.json").read_text())
    table = json.loads((BASE / "truth-table.json").read_text())
    text = (BASE / "policy-text.txt").read_text()
    checks = []

    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append({"check": name, "result": "PASS"})

    check(
        "Review only and disabled",
        config["review_status"] == "PROPOSED_NOT_ACCEPTED" and config["runtime_enabled"] is False,
    )
    check(
        "No fabricated acceptance",
        all(
            config["authority"][k] is None
            for k in ["accepted_by", "accepted_at", "acceptance_evidence"]
        ),
    )
    check(
        "Governance owns runtime calculation", config["authority"]["runtime_owner"] == "governance"
    )
    check(
        "Version matches review cases",
        config["candidate_version"] == table["candidate_version"] == "0.1",
    )
    check(
        "One exact proposed rule",
        config["rules"]
        == [
            {
                "currency": "USD",
                "threshold": "5000.00",
                "comparator": "GT",
                "approval_level": "manager",
                "fraction_digits": 2,
                "rounding": "REJECT_EXCESS_PRECISION",
                "fx_conversion": "DISABLED",
            }
        ],
    )
    check(
        "Positive plain-decimal string rule",
        config["amount_input"]["pattern"] == r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?"
        and config["amount_input"]["positive_only"] is True,
    )
    check(
        "Matching policy paragraph",
        all(
            s in text
            for s in [
                "exceeding USD 5000.00 require manager approval",
                "at or below USD 5000.00",
                "Excess precision is rejected without rounding",
                "currency conversion is disabled",
                "prevents progression",
            ]
        ),
    )
    check(
        "All 31 unique case IDs",
        len(table["cases"]) == len({c["case_id"] for c in table["cases"]}) == 31,
    )
    for case in table["cases"]:
        actual = outcome(config, case)
        check(case["case_id"] + ": " + case["label"], actual == case["expected"])
        if actual["review_outcome"] != "CALCULATED":
            check(
                case["case_id"] + ": unresolved is not false",
                "approval_required" not in actual and "approval_level" not in actual,
            )
    return {
        "result": "PASS",
        "scope": "Offline candidate consistency; not stakeholder acceptance or runtime policy validation",
        "candidate_version": "0.1",
        "review_cases": len(table["cases"]),
        "checks": checks,
        "check_count": len(checks),
        "python": sys.version.split()[0],
        "input_hashes": {
            name: hashlib.sha256((BASE / name).read_bytes()).hexdigest()
            for name in [
                "candidate-config.json",
                "truth-table.json",
                "policy-text.txt",
                "verify_candidate.py",
            ]
        },
        "stakeholder_acceptance": "PENDING_MOHAMED",
        "runtime_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(BASE):
        parser.error("Write the review report outside the candidate folder")
    try:
        report = validate()
        code = 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report = {"result": "FAIL", "error": str(exc)}
        code = 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
