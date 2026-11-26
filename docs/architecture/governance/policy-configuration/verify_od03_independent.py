#!/usr/bin/env python3
"""Independent offline check of the governance policy configuration against the
31 OD-03 boundary cases supplied by the application team.

It loads procurement-policy-set-v0.1.yaml, applies the governance rules for the
approval requirement (strict greater-than, exact decimal strings, exact currency
match, stop on missing or invalid configuration), and compares the outcome with
every expected outcome in the candidate truth table. It also checks that the paired
policy text states the same values as the configuration.

Scope: specification review only. This is not a runtime implementation, not the
governance engine and not an acceptance record. It reads files, writes only the
--output file, never calls a network or a tool, and must not be imported by an
application or governance runtime.

Dependency: PyYAML (a development dependency of this repository).

Usage, from the repository root:

    uv run --locked --all-packages python \\
        docs/architecture/governance/policy-configuration/verify_od03_independent.py \\
        --truth-table docs/architecture/reference-applications/policy-candidate/od03-v0.1/truth-table.json \\
        --policy-text docs/architecture/reference-applications/policy-candidate/od03-v0.1/policy-text.txt \\
        --output od03-independent-check-result.json

Exit code 0: every case agrees. Exit code 1: at least one disagreement or check failure.
"""

import argparse
import copy
import hashlib
import json
import platform
import re
import sys
from decimal import Decimal
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "procurement-policy-set-v0.1.yaml"

# Nour's review reason (truth-table.json) -> governance reason code.
REASON_MAP = {
    "INVALID_AMOUNT": "AMOUNT_INVALID",
    "UNSUPPORTED_CURRENCY": "CURRENCY_UNSUPPORTED",
    "MISSING_CONFIGURATION": "POLICY_CONFIG_MISSING",
    "INVALID_CONFIGURATION": "POLICY_CONFIG_INVALID",
    "TEXT_CONFIG_CONFLICT": "POLICY_TEXT_CONFIG_CONFLICT",
    "POLICY_VERSION_MISMATCH": "POLICY_VERSION_MISMATCH",
    "REQUEST_CONTEXT_MISMATCH": "CONTEXT_MISMATCH",
}


def lf_sha256(path: Path) -> str:
    """SHA-256 of the file with CRLF normalised to LF, so the value is the same on
    Windows checkouts and equals the committed Git blob content hash."""
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def validate_config(cfg):
    """Return None when the configuration may be used, else a governance reason code."""
    if cfg is None:
        return "POLICY_CONFIG_MISSING"
    try:
        policy = cfg["policies"]["PROC-APPROVAL-01"]
    except (KeyError, TypeError):
        return "POLICY_CONFIG_MISSING"
    if policy.get("comparator") != "GT":
        return "POLICY_CONFIG_INVALID"
    rules = policy.get("currency_rules") or []
    if not rules:
        return "POLICY_CONFIG_MISSING"
    for rule in rules:
        if rule.get("threshold") in (None, "") or rule.get("approval_level") in (None, ""):
            return "POLICY_CONFIG_INVALID"
    if not policy.get("validity") or policy["validity"].get("time_expiry") != "NONE":
        return "POLICY_CONFIG_MISSING"
    return None


def approval_requirement(raw_amount, currency, cfg, context):
    """Governance approval requirement. Returns (kind, payload).

    kind is CALCULATED, ERROR (malformed amount) or UNRESOLVED. Unknown never
    becomes "approval not required".
    """
    problem = validate_config(cfg)
    if problem:
        return "UNRESOLVED", problem
    policy = cfg["policies"]["PROC-APPROVAL-01"]
    pattern = policy["amount_input"]["pattern"]
    if not isinstance(raw_amount, str) or not re.fullmatch(pattern, raw_amount):
        return "ERROR", "AMOUNT_INVALID"
    amount = Decimal(raw_amount)
    if amount <= 0:
        return "ERROR", "AMOUNT_INVALID"
    rule = next((r for r in policy["currency_rules"] if r["currency"] == currency), None)
    if rule is None:
        return "UNRESOLVED", "CURRENCY_UNSUPPORTED"
    if context.get("policy_version_matches") is False:
        return "UNRESOLVED", "POLICY_VERSION_MISMATCH"
    if context.get("policy_text_matches") is False:
        return "UNRESOLVED", "POLICY_TEXT_CONFIG_CONFLICT"
    if context.get("trusted_request_matches") is False:
        return "UNRESOLVED", "CONTEXT_MISMATCH"
    required = amount > Decimal(rule["threshold"])
    return "CALCULATED", {
        "approval_required": required,
        "approval_level": rule["approval_level"] if required else None,
        "normalized_total": f"{amount:.2f}",
    }


def check_policy_text(text: str, cfg) -> list:
    """The paired text must state the same values as the configuration."""
    rule = cfg["policies"]["PROC-APPROVAL-01"]["currency_rules"][0]
    digits = {0: "no", 1: "one", 2: "two"}[rule["fraction_digits"]]
    wanted = {
        "currency": "USD" if rule["currency"] == "USD" else rule["currency"],
        "threshold": f"{rule['currency']} {rule['threshold']}",
        "strict greater-than wording": "exceeding",
        "approval level": rule["approval_level"],
        "fractional digits": f"{digits} fractional digits",
        "no rounding": "without rounding",
        "no currency conversion": "currency conversion is disabled",
        "no waiver of other checks": "urgency waives none of them",
    }
    return [{"item": k, "expected_phrase": v, "present": v in text} for k, v in wanted.items()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--truth-table", type=Path, required=True)
    ap.add_argument("--policy-text", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument(
        "--source-note",
        default="",
        help="free text recorded in the report, e.g. the commit the candidate files came from",
    )
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    table = json.loads(args.truth_table.read_text(encoding="utf-8"))
    text = args.policy_text.read_text(encoding="utf-8")

    rows, failures = [], []
    for case in table["cases"]:
        expected = case["expected"]
        working = copy.deepcopy(cfg)
        if case.get("configuration_present") is False:
            working = None
        mutation = case.get("config_mutation") or {}
        if working is not None:
            rule_block = working["policies"]["PROC-APPROVAL-01"]
            for key, value in mutation.items():
                if key == "comparator":
                    rule_block["comparator"] = value
                else:
                    rule_block["currency_rules"][0][key] = value
        context = {
            k: case[k]
            for k in ("policy_text_matches", "policy_version_matches", "trusted_request_matches")
            if k in case
        }
        kind, payload = approval_requirement(
            case["input"]["total_amount"], case["input"]["currency"], working, context
        )

        if expected["review_outcome"] == "CALCULATED":
            agree = (
                kind == "CALCULATED"
                and payload["approval_required"] == expected["approval_required"]
                and payload["approval_level"] == expected["approval_level"]
                and payload["normalized_total"] == expected["normalized_total"]
            )
            governance_result = (
                payload if kind == "CALCULATED" else {"kind": kind, "reason": payload}
            )
        else:
            wanted = REASON_MAP[expected["reason"]]
            agree = payload == wanted
            governance_result = {"kind": kind, "reason": payload}
        rows.append(
            {
                "case_id": case["case_id"],
                "input": case["input"],
                "expected_outcome": expected["review_outcome"],
                "expected_reason": expected.get("reason"),
                "governance_result": governance_result,
                "agree": agree,
            }
        )
        if not agree:
            failures.append(case["case_id"])

    text_checks = check_policy_text(text, cfg)
    text_ok = all(item["present"] for item in text_checks)
    cfg_problem = validate_config(cfg)

    result = {
        "result": "PASS" if (not failures and text_ok and cfg_problem is None) else "FAIL",
        "scope": "Offline specification check of the proposed synthetic configuration. Not runtime validation, not the governance engine, not an acceptance record.",
        "policy_set_version": cfg["policy_set"]["id"] + "-" + cfg["policy_set"]["version"],
        "cases": len(rows),
        "cases_agree": sum(r["agree"] for r in rows),
        "configuration_valid": cfg_problem is None,
        "policy_text_consistent_with_configuration": text_ok,
        "policy_text_checks": text_checks,
        "input_sha256_lf_normalised": {
            "procurement-policy-set-v0.1.yaml": lf_sha256(args.config),
            "truth-table.json": lf_sha256(args.truth_table),
            "policy-text.txt": lf_sha256(args.policy_text),
            "verify_od03_independent.py": lf_sha256(Path(__file__).resolve()),
        },
        "source_note": args.source_note,
        "python": platform.python_version(),
        "pyyaml": yaml.__version__,
        "command": "python verify_od03_independent.py --truth-table <truth-table.json> --policy-text <policy-text.txt> --output <result.json>",
        "disagreements": failures,
        "case_results": rows,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"{result['result']}: {result['cases_agree']}/{result['cases']} cases agree; "
        f"configuration_valid={result['configuration_valid']}; policy text consistent={text_ok}"
    )
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
