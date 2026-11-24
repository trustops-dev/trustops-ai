"""The full pre-tool check in every state it can face.

All three mandatory policies are always evaluated and recorded. The verdict is ALLOW only when
each of them passed or did not apply and the check itself has no problem. Everything else blocks.
"""

import copy
import json
from itertools import product
from pathlib import Path
from typing import Any

import pytest
import yaml

from trustops_governance.policy import engine
from trustops_governance.policy.boundary import InvalidCheckInput, parse_check_input
from trustops_governance.policy.policy_schema import (
    POLICY_APPROVAL,
    POLICY_SUPPLIER,
    POLICY_TOOL_STAGE,
)
from trustops_governance.policy.pre_tool_check import CHECK_MODE, run_check
from trustops_governance.policy.results import CheckOutcome, PolicyResult, Verdict

REPO_ROOT = Path(__file__).resolve().parents[3]
DRAFT_POLICY_SET = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "governance"
    / "policy-configuration"
    / "procurement-policy-set-v0.1.yaml"
)

ORDER = [POLICY_APPROVAL, POLICY_TOOL_STAGE, POLICY_SUPPLIER]
MANDATORY_FAILED = "MANDATORY_POLICY_FAILED"
FAIL_CLOSED = "FAIL_CLOSED_ON_POLICY_ERROR"
ALL_PASSED = "ALL_APPLICABLE_PASSED"


def request() -> dict[str, Any]:
    """A valid approved purchase above the threshold, in stage APPROVED, supplier approved."""
    return {
        "proposal": {
            "tool": "create_purchase_order",
            "request_revision": "rev-1",
            "supplier_id": "sup-1",
            "total_amount": "1000.01",
            "currency": "USD",
        },
        "stage": "APPROVED",
        "approval": {
            "status": "APPROVED",
            "bound": {
                "request_revision": "rev-1",
                "supplier_id": "sup-1",
                "total_amount": "1000.01",
                "currency": "USD",
                "approval_level": "manager",
            },
            "decided": "BEFORE_PROPOSAL",
            "event_agrees_with_record": True,
            "approver_level_satisfies_required": True,
        },
        "supplier": {"lookup_outcome": "FOUND", "supplier_id": "sup-1", "status": "APPROVED"},
    }


def with_changes(base: dict[str, Any], **changes: Any) -> dict[str, Any]:
    """A copy of the request with top-level keys replaced."""
    return {**copy.deepcopy(base), **changes}


def results_of(outcome: dict[str, Any]) -> dict[str, str]:
    return {pid: item["result"] for pid, item in outcome["policy_results"].items()}


def verdict_of(outcome: dict[str, Any]) -> tuple[str, str]:
    return outcome["verdict"], outcome["verdict_basis"]


# --- a valid purchase is allowed ----------------------------------------------------------


def test_a_valid_approved_purchase_is_allowed(full_configuration: dict[str, Any]) -> None:
    outcome = engine.check(request(), full_configuration)
    assert verdict_of(outcome) == ("ALLOW", ALL_PASSED)
    assert list(outcome["policy_results"]) == ORDER
    assert set(results_of(outcome).values()) == {"PASS"}


def test_the_check_carries_the_versions_and_the_mode(full_configuration: dict[str, Any]) -> None:
    outcome = engine.check(request(), full_configuration)
    assert outcome["check_mode"] == CHECK_MODE == "ONLINE_PRE_TOOL"
    assert outcome["policy_bundle_version"] == "test-policy-set-test"
    versions = {pid: item["policy_version"] for pid, item in outcome["policy_results"].items()}
    assert versions == {
        POLICY_APPROVAL: "test-approval-v1",
        POLICY_TOOL_STAGE: "test-tool-stage-v1",
        POLICY_SUPPLIER: "test-supplier-v1",
    }


def test_an_amount_at_the_threshold_needs_no_approval(full_configuration: dict[str, Any]) -> None:
    at_threshold = request()
    at_threshold["proposal"]["total_amount"] = "1000.00"
    at_threshold["approval"] = None
    outcome = engine.check(at_threshold, full_configuration)
    assert verdict_of(outcome) == ("ALLOW", ALL_PASSED)
    assert results_of(outcome)[POLICY_APPROVAL] == "NOT_APPLICABLE"


def test_a_read_tool_in_the_first_stage_is_allowed(full_configuration: dict[str, Any]) -> None:
    read = request()
    read["proposal"]["tool"] = "get_supplier"
    read["stage"] = "PRE_APPROVAL"
    outcome = engine.check(read, full_configuration)
    assert verdict_of(outcome) == ("ALLOW", ALL_PASSED)
    assert results_of(outcome) == {
        POLICY_APPROVAL: "NOT_APPLICABLE",
        POLICY_TOOL_STAGE: "PASS",
        POLICY_SUPPLIER: "NOT_APPLICABLE",
    }


# --- every combination of the three policies ----------------------------------------------

APPROVALS = {"valid": True, "missing": False}
STAGES = {"APPROVED": True, "PRE_APPROVAL": False}
SUPPLIERS = {"approved": "APPROVED", "not-approved": "NOT_APPROVED", "no-snapshot": None}


def combination(approval: str, stage: str, supplier: str) -> dict[str, Any]:
    case = request()
    case["stage"] = stage
    if not APPROVALS[approval]:
        case["approval"] = None
    if SUPPLIERS[supplier] is None:
        case["supplier"] = None
    else:
        case["supplier"]["status"] = SUPPLIERS[supplier]
    return case


@pytest.mark.parametrize(
    ("approval", "stage", "supplier"),
    list(product(APPROVALS, STAGES, SUPPLIERS)),
    ids=lambda value: str(value),
)
def test_every_combination_of_the_three_policies(
    approval: str, stage: str, supplier: str, full_configuration: dict[str, Any]
) -> None:
    outcome = engine.check(combination(approval, stage, supplier), full_configuration)
    results = results_of(outcome).values()
    if "FAIL" in results:
        expected = ("BLOCK", MANDATORY_FAILED)
    elif "ERROR" in results:
        expected = ("BLOCK", FAIL_CLOSED)
    else:
        expected = ("ALLOW", ALL_PASSED)
    assert verdict_of(outcome) == expected
    assert list(outcome["policy_results"]) == ORDER  # every policy recorded, even after a failure


def test_the_approval_bypass_is_blocked_with_both_findings_recorded(
    full_configuration: dict[str, Any],
) -> None:
    outcome = engine.check(combination("missing", "PRE_APPROVAL", "approved"), full_configuration)
    assert verdict_of(outcome) == ("BLOCK", MANDATORY_FAILED)
    assert results_of(outcome) == {
        POLICY_APPROVAL: "FAIL",
        POLICY_TOOL_STAGE: "FAIL",
        POLICY_SUPPLIER: "PASS",
    }


@pytest.mark.parametrize("policy_id", ORDER)
def test_each_policy_alone_can_block_the_purchase(
    policy_id: str, full_configuration: dict[str, Any]
) -> None:
    failing = {
        POLICY_APPROVAL: combination("missing", "APPROVED", "approved"),
        POLICY_TOOL_STAGE: combination("valid", "PRE_APPROVAL", "approved"),
        POLICY_SUPPLIER: combination("valid", "APPROVED", "not-approved"),
    }[policy_id]
    outcome = engine.check(failing, full_configuration)
    assert verdict_of(outcome) == ("BLOCK", MANDATORY_FAILED)
    assert results_of(outcome)[policy_id] == "FAIL"
    assert list(results_of(outcome).values()).count("FAIL") == 1


def test_a_stage_that_cannot_be_read_blocks_fail_closed(full_configuration: dict[str, Any]) -> None:
    unreadable = with_changes(request(), stage=None)
    outcome = engine.check(unreadable, full_configuration)
    assert verdict_of(outcome) == ("BLOCK", FAIL_CLOSED)
    assert results_of(outcome)[POLICY_TOOL_STAGE] == "ERROR"


# --- problems with the check itself -------------------------------------------------------

FINDINGS = {
    "version-mismatch": {"policy_set_version_matches": False},
    "context-mismatch": {"context_consistent": False},
    "malformed-request": {"request_well_formed": False},
    "consistency-finding": {"evidence_consistency_findings": ["EC-03"]},
    "unresolved-evidence": {"evidence_unresolved": True},
}


@pytest.mark.parametrize("findings", FINDINGS.values(), ids=FINDINGS.keys())
def test_a_check_level_problem_blocks_even_when_every_policy_passes(
    findings: dict[str, Any], full_configuration: dict[str, Any]
) -> None:
    outcome = engine.check({**request(), **findings}, full_configuration)
    assert set(results_of(outcome).values()) == {"PASS"}
    assert verdict_of(outcome) == ("BLOCK", FAIL_CLOSED)


@pytest.mark.parametrize("findings", FINDINGS.values(), ids=FINDINGS.keys())
def test_a_failed_policy_outranks_a_check_level_problem(
    findings: dict[str, Any], full_configuration: dict[str, Any]
) -> None:
    failing = {**combination("missing", "APPROVED", "approved"), **findings}
    assert verdict_of(engine.check(failing, full_configuration)) == ("BLOCK", MANDATORY_FAILED)


def test_findings_that_are_left_out_mean_that_none_was_raised(
    full_configuration: dict[str, Any],
) -> None:
    explicit = {
        **request(),
        "policy_set_version_matches": True,
        "context_consistent": True,
        "request_well_formed": True,
        "evidence_consistency_findings": [],
        "evidence_unresolved": False,
    }
    assert engine.check(explicit, full_configuration) == engine.check(request(), full_configuration)


# --- the policy set and the configuration -------------------------------------------------


@pytest.mark.parametrize(
    "broken",
    [{}, {"id": "test-policy-set"}, {"id": "", "version": "test"}, {"id": "x", "version": 1}],
    ids=["empty", "no-version", "blank-id", "version-not-text"],
)
def test_an_unreadable_policy_set_blocks_even_when_every_policy_passes(
    broken: dict[str, Any], full_configuration: dict[str, Any]
) -> None:
    full_configuration["policy_set"] = broken
    outcome = engine.check(request(), full_configuration)
    assert set(results_of(outcome).values()) == {"PASS"}
    assert verdict_of(outcome) == ("BLOCK", FAIL_CLOSED)
    assert outcome["policy_bundle_version"] is None


def test_a_policy_set_that_is_absent_blocks(full_configuration: dict[str, Any]) -> None:
    del full_configuration["policy_set"]
    outcome = engine.check(request(), full_configuration)
    assert verdict_of(outcome) == ("BLOCK", FAIL_CLOSED)
    assert outcome["policy_bundle_version"] is None


def test_no_configuration_blocks_and_every_policy_reports_it() -> None:
    outcome = engine.check(request(), None)
    assert verdict_of(outcome) == ("BLOCK", FAIL_CLOSED)
    assert outcome["policy_bundle_version"] is None
    assert list(outcome["policy_results"]) == ORDER
    for item in outcome["policy_results"].values():
        assert (item["result"], item["reason_code"]) == ("ERROR", "POLICY_CONFIG_MISSING")
        assert item["policy_version"] is None


def test_one_broken_policy_does_not_hide_the_others(full_configuration: dict[str, Any]) -> None:
    del full_configuration["policies"][POLICY_TOOL_STAGE]["version"]
    outcome = engine.check(request(), full_configuration)
    results = outcome["policy_results"]
    assert (results[POLICY_TOOL_STAGE]["result"], results[POLICY_TOOL_STAGE]["reason_code"]) == (
        "ERROR",
        "POLICY_CONFIG_INVALID",
    )
    assert results[POLICY_APPROVAL]["result"] == "PASS"
    assert results[POLICY_SUPPLIER]["result"] == "PASS"
    assert verdict_of(outcome) == ("BLOCK", FAIL_CLOSED)


# --- the typed check ----------------------------------------------------------------------


def test_the_typed_check_returns_every_outcome_in_the_fixed_order(
    full_configuration: dict[str, Any],
) -> None:
    outcome = run_check(parse_check_input(request()), full_configuration)
    assert isinstance(outcome, CheckOutcome)
    assert [item.policy_id for item in outcome.outcomes] == ORDER
    assert outcome.aggregate.verdict is Verdict.ALLOW
    assert outcome.check_mode == CHECK_MODE
    assert all(item.result is PolicyResult.PASS for item in outcome.outcomes)


# --- unreadable input never yields a verdict ----------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        {"evidence_consistency_findings": "EC-03"},
        {"evidence_consistency_findings": [3]},
        {"policy_set_version_matches": "true"},
        {"context_consistent": 1},
        {"request_well_formed": None},
        {"evidence_unresolved": "yes"},
        {"stage": 5},
        {"supplier": "APPROVED"},
        {"supplier": {"status": "APPROVED"}},
        {"supplier": {"lookup_outcome": 5}},
        {"supplier": {"lookup_outcome": "FOUND", "status": 5}},
        {"supplier": {"lookup_outcome": "FOUND", "supplier_id": 7}},
        {"proposal": None},
    ],
    ids=lambda value: next(iter(value)) + "=" + str(next(iter(value.values()))),
)
def test_an_unreadable_check_raises_and_never_returns_a_verdict(
    bad: dict[str, Any], full_configuration: dict[str, Any]
) -> None:
    with pytest.raises(InvalidCheckInput):
        engine.check({**request(), **bad}, full_configuration)


# --- safe to call and to share ------------------------------------------------------------


def test_checking_does_not_change_the_input_or_the_configuration(
    full_configuration: dict[str, Any],
) -> None:
    given, before = request(), copy.deepcopy(request())
    configuration_before = copy.deepcopy(full_configuration)
    engine.check(given, full_configuration)
    assert given == before
    assert full_configuration == configuration_before


def test_the_check_is_plain_json_and_deterministic(full_configuration: dict[str, Any]) -> None:
    first = engine.check(request(), full_configuration)
    assert json.loads(json.dumps(first)) == first
    assert engine.check(request(), copy.deepcopy(full_configuration)) == first


# --- the real draft configuration ---------------------------------------------------------


def test_the_check_uses_the_versions_of_the_draft_configuration() -> None:
    draft: dict[str, Any] = yaml.safe_load(DRAFT_POLICY_SET.read_text(encoding="utf-8"))
    purchase = request()
    purchase["proposal"]["total_amount"] = "5000.01"
    purchase["approval"]["bound"]["total_amount"] = "5000.01"
    outcome = engine.check(purchase, draft)
    assert verdict_of(outcome) == ("ALLOW", ALL_PASSED)
    set_info = draft["policy_set"]
    assert outcome["policy_bundle_version"] == f"{set_info['id']}-{set_info['version']}"
    for policy_id, item in outcome["policy_results"].items():
        assert item["policy_version"] == draft["policies"][policy_id]["version"]
