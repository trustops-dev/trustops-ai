"""The dictionary boundary and the public engine functions, in every state they can face.

A caller that sends something unreadable must get an error, never a verdict. Nothing here may
turn a malformed input into ALLOW.
"""

import copy
import json
from typing import Any

import pytest

from trustops_governance.policy import engine
from trustops_governance.policy.boundary import (
    InvalidCheckInput,
    parse_aggregation_input,
    parse_approval,
    parse_proposal,
)
from trustops_governance.policy.evidence import ApprovalEvidence, DecisionOrder
from trustops_governance.policy.policy_schema import (
    POLICY_APPROVAL,
    POLICY_SUPPLIER,
    POLICY_TOOL_STAGE,
)
from trustops_governance.policy.results import PolicyResult


def check_input() -> dict[str, Any]:
    """A valid approved purchase, in the dictionary shape of the boundary."""
    return {
        "proposal": {
            "tool": "create_purchase_order",
            "request_revision": "rev-1",
            "supplier_id": "sup-1",
            "total_amount": "1000.01",
            "currency": "USD",
        },
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
    }


def aggregation_input() -> dict[str, Any]:
    return {
        "policy_results": {
            POLICY_APPROVAL: "PASS",
            POLICY_TOOL_STAGE: "PASS",
            POLICY_SUPPLIER: "PASS",
        },
        "policy_set_version_matches": True,
        "context_consistent": True,
        "request_well_formed": True,
        "evidence_consistency_findings": [],
        "evidence_unresolved": False,
    }


def edited(base: dict[str, Any], path: str, value: object) -> dict[str, Any]:
    """A copy of ``base`` with the value at a dotted path replaced."""
    result = copy.deepcopy(base)
    *parents, last = path.split(".")
    node = result
    for part in parents:
        node = node[part]
    node[last] = value
    return result


def removed(base: dict[str, Any], path: str) -> dict[str, Any]:
    result = copy.deepcopy(base)
    *parents, last = path.split(".")
    node = result
    for part in parents:
        node = node[part]
    del node[last]
    return result


# --- evaluate_policy ---------------------------------------------------------------------


def test_the_engine_supports_only_the_approval_policy_so_far() -> None:
    assert engine.SUPPORTED_POLICIES == frozenset({POLICY_APPROVAL})


def test_evaluate_policy_returns_plain_json_values(configuration: dict[str, Any]) -> None:
    outcome = engine.evaluate_policy(POLICY_APPROVAL, check_input(), configuration)
    assert outcome == {
        "policy_id": POLICY_APPROVAL,
        "result": "PASS",
        "reason_code": "APPROVAL_VALID",
        "basis": None,
    }
    assert json.loads(json.dumps(outcome)) == outcome


def test_evaluate_policy_reports_the_basis_when_approval_is_not_required(
    configuration: dict[str, Any],
) -> None:
    below = edited(check_input(), "proposal.total_amount", "1000.00")
    outcome = engine.evaluate_policy(POLICY_APPROVAL, below, configuration)
    assert (outcome["result"], outcome["basis"]) == ("NOT_APPLICABLE", "NOT_REQUIRED")


def test_evaluate_policy_turns_a_missing_configuration_into_an_error_outcome() -> None:
    outcome = engine.evaluate_policy(POLICY_APPROVAL, check_input(), None)
    assert (outcome["result"], outcome["reason_code"]) == ("ERROR", "POLICY_CONFIG_MISSING")


def test_evaluate_policy_ignores_keys_the_policy_does_not_read(
    configuration: dict[str, Any],
) -> None:
    extra = {**check_input(), "stage": "APPROVED", "supplier": {"status": "APPROVED"}}
    outcome = engine.evaluate_policy(POLICY_APPROVAL, extra, configuration)
    assert outcome["result"] == "PASS"


@pytest.mark.parametrize("policy_id", [POLICY_TOOL_STAGE, POLICY_SUPPLIER, "PROC-OTHER-01", ""])
def test_a_policy_without_an_implementation_is_refused_not_passed(
    policy_id: str, configuration: dict[str, Any]
) -> None:
    with pytest.raises(engine.UnsupportedPolicyError):
        engine.evaluate_policy(policy_id, check_input(), configuration)


def test_evaluating_does_not_change_the_input(configuration: dict[str, Any]) -> None:
    given = check_input()
    before = copy.deepcopy(given)
    engine.evaluate_policy(POLICY_APPROVAL, given, configuration)
    assert given == before


# --- an unreadable check input is an error, never a verdict ------------------------------

UNREADABLE_INPUTS = {
    "no-proposal": lambda: removed(check_input(), "proposal"),
    "proposal-is-text": lambda: {**check_input(), "proposal": "create_purchase_order"},
    "proposal-is-null": lambda: {**check_input(), "proposal": None},
    "tool-missing": lambda: removed(check_input(), "proposal.tool"),
    "tool-not-text": lambda: edited(check_input(), "proposal.tool", 5),
    "revision-missing": lambda: removed(check_input(), "proposal.request_revision"),
    "supplier-not-text": lambda: edited(check_input(), "proposal.supplier_id", None),
    "currency-missing": lambda: removed(check_input(), "proposal.currency"),
    "currency-not-text": lambda: edited(check_input(), "proposal.currency", 840),
    "approval-is-text": lambda: edited(check_input(), "approval", "APPROVED"),
    "status-missing": lambda: removed(check_input(), "approval.status"),
    "status-not-text": lambda: edited(check_input(), "approval.status", True),
    "bound-missing": lambda: removed(check_input(), "approval.bound"),
    "bound-is-text": lambda: edited(check_input(), "approval.bound", "x"),
    "bound-revision-missing": lambda: removed(check_input(), "approval.bound.request_revision"),
    "bound-amount-not-text": lambda: edited(check_input(), "approval.bound.total_amount", 1000.01),
    "bound-level-missing": lambda: removed(check_input(), "approval.bound.approval_level"),
    "decided-unknown": lambda: edited(check_input(), "approval.decided", "YESTERDAY"),
    "decided-lowercase": lambda: edited(check_input(), "approval.decided", "before_proposal"),
    "decided-not-text": lambda: edited(check_input(), "approval.decided", 5),
    "agrees-missing": lambda: removed(check_input(), "approval.event_agrees_with_record"),
    "agrees-as-text": lambda: edited(check_input(), "approval.event_agrees_with_record", "true"),
    "agrees-as-number": lambda: edited(check_input(), "approval.event_agrees_with_record", 1),
    "eligible-missing": lambda: removed(
        check_input(), "approval.approver_level_satisfies_required"
    ),
    "eligible-null": lambda: edited(
        check_input(), "approval.approver_level_satisfies_required", None
    ),
}


@pytest.mark.parametrize("build", UNREADABLE_INPUTS.values(), ids=UNREADABLE_INPUTS.keys())
def test_an_unreadable_check_input_raises_and_never_returns_a_verdict(
    build: Any, configuration: dict[str, Any]
) -> None:
    with pytest.raises(InvalidCheckInput):
        engine.evaluate_policy(POLICY_APPROVAL, build(), configuration)


# --- parsing the proposal and the approval -----------------------------------------------


def test_the_amount_is_kept_raw_so_the_policy_can_judge_it() -> None:
    for raw in (None, 1000.5, "abc", ["x"]):
        parsed = parse_proposal(edited(check_input(), "proposal.total_amount", raw))
        assert parsed.total_amount == raw


def test_no_approval_is_none_not_an_error() -> None:
    assert parse_approval({**check_input(), "approval": None}) is None
    assert parse_approval(removed(check_input(), "approval")) is None


def test_a_pending_approval_may_have_no_decision_order() -> None:
    pending = edited(edited(check_input(), "approval.status", "PENDING"), "approval.decided", None)
    approval = parse_approval(pending)
    assert isinstance(approval, ApprovalEvidence)
    assert approval.decision_order is None


@pytest.mark.parametrize("order", list(DecisionOrder))
def test_every_decision_order_is_readable(order: DecisionOrder) -> None:
    approval = parse_approval(edited(check_input(), "approval.decided", order.value))
    assert approval is not None
    assert approval.decision_order is order


# --- aggregate ---------------------------------------------------------------------------


def test_aggregate_returns_plain_json_values() -> None:
    outcome = engine.aggregate(aggregation_input())
    assert outcome == {"verdict": "ALLOW", "verdict_basis": "ALL_APPLICABLE_PASSED"}
    assert json.loads(json.dumps(outcome)) == outcome


def test_aggregate_blocks_on_a_failed_policy() -> None:
    failed = edited(aggregation_input(), "policy_results.PROC-SUPPLIER-01", "FAIL")
    outcome = engine.aggregate(failed)
    assert outcome == {"verdict": "BLOCK", "verdict_basis": "MANDATORY_POLICY_FAILED"}


def test_aggregate_blocks_on_a_check_level_finding() -> None:
    finding = edited(aggregation_input(), "evidence_consistency_findings", ["EC-03"])
    outcome = engine.aggregate(finding)
    assert outcome == {"verdict": "BLOCK", "verdict_basis": "FAIL_CLOSED_ON_POLICY_ERROR"}


def test_aggregate_does_not_change_the_input() -> None:
    given = aggregation_input()
    before = copy.deepcopy(given)
    engine.aggregate(given)
    assert given == before


UNREADABLE_AGGREGATIONS = {
    "no-results": lambda: removed(aggregation_input(), "policy_results"),
    "results-is-a-list": lambda: {**aggregation_input(), "policy_results": ["PASS"]},
    "result-lowercase": lambda: edited(
        aggregation_input(), "policy_results.PROC-SUPPLIER-01", "pass"
    ),
    "result-unknown": lambda: edited(aggregation_input(), "policy_results.PROC-SUPPLIER-01", "OK"),
    "result-not-text": lambda: edited(aggregation_input(), "policy_results.PROC-SUPPLIER-01", 1),
    "result-null": lambda: edited(aggregation_input(), "policy_results.PROC-SUPPLIER-01", None),
    "version-flag-missing": lambda: removed(aggregation_input(), "policy_set_version_matches"),
    "context-flag-as-text": lambda: edited(aggregation_input(), "context_consistent", "true"),
    "well-formed-null": lambda: edited(aggregation_input(), "request_well_formed", None),
    "unresolved-as-number": lambda: edited(aggregation_input(), "evidence_unresolved", 0),
    "findings-missing": lambda: removed(aggregation_input(), "evidence_consistency_findings"),
    "findings-as-text": lambda: edited(
        aggregation_input(), "evidence_consistency_findings", "EC-03"
    ),
    "findings-with-number": lambda: edited(
        aggregation_input(), "evidence_consistency_findings", [3]
    ),
}


@pytest.mark.parametrize(
    "build", UNREADABLE_AGGREGATIONS.values(), ids=UNREADABLE_AGGREGATIONS.keys()
)
def test_an_unreadable_aggregation_input_raises_and_never_allows(build: Any) -> None:
    with pytest.raises(InvalidCheckInput):
        engine.aggregate(build())


def test_every_result_name_is_readable() -> None:
    for result in PolicyResult:
        given = edited(aggregation_input(), "policy_results.PROC-SUPPLIER-01", result.value)
        results, _ = parse_aggregation_input(given)
        assert results[POLICY_SUPPLIER] is result


# --- check -------------------------------------------------------------------------------


def test_check_is_refused_until_every_mandatory_policy_exists(
    configuration: dict[str, Any],
) -> None:
    with pytest.raises(NotImplementedError) as refused:
        engine.check(check_input(), configuration)
    assert POLICY_TOOL_STAGE in str(refused.value)
    assert POLICY_SUPPLIER in str(refused.value)
    assert POLICY_APPROVAL not in str(refused.value)
