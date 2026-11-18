"""PROC-APPROVAL-01 in every state it can face.

The baseline is a proposal just above the threshold (1000.00 USD) with a valid approval. Each
test changes one thing and states the result the policy must give.
"""

import copy
from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

from trustops_governance.policy.approval_rule import evaluate_approval
from trustops_governance.policy.evidence import (
    ApprovalEvidence,
    DecisionOrder,
    PurchaseProposal,
)
from trustops_governance.policy.policy_schema import POLICY_APPROVAL
from trustops_governance.policy.results import OutcomeBasis, PolicyOutcome, PolicyResult, ReasonCode

PASS = PolicyResult.PASS
FAIL = PolicyResult.FAIL
NOT_APPLICABLE = PolicyResult.NOT_APPLICABLE
ERROR = PolicyResult.ERROR


def assert_outcome(outcome: PolicyOutcome, result: PolicyResult, reason: ReasonCode) -> None:
    assert (outcome.result, outcome.reason_code) == (result, reason)
    assert outcome.policy_id == POLICY_APPROVAL


def with_amount(proposal: PurchaseProposal, amount: object) -> PurchaseProposal:
    return replace(proposal, total_amount=amount)


def with_bound(approval: ApprovalEvidence, **changes: str) -> ApprovalEvidence:
    return replace(approval, bound=replace(approval.bound, **changes))


# --- the policy applies only to the purchase order ----------------------------------------


@pytest.mark.parametrize(
    "tool",
    ["get_supplier", "search_policy", "request_approval", "Create_Purchase_Order", ""],
)
def test_any_other_tool_is_out_of_scope(
    proposal: PurchaseProposal, configuration: dict[str, Any], tool: str
) -> None:
    outcome = evaluate_approval(replace(proposal, tool=tool), None, configuration)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)
    assert outcome.basis is None


def test_scope_is_decided_before_the_configuration_and_the_amount(
    proposal: PurchaseProposal,
) -> None:
    other_tool = replace(proposal, tool="get_supplier", total_amount=None)
    outcome = evaluate_approval(other_tool, None, None)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)


# --- the configuration -------------------------------------------------------------------


def test_a_missing_configuration_is_an_error_not_a_pass(proposal: PurchaseProposal) -> None:
    outcome = evaluate_approval(proposal, None, None)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_MISSING)


def test_an_invalid_configuration_is_an_error(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    configuration["policies"][POLICY_APPROVAL]["comparator"] = "GTE"
    outcome = evaluate_approval(proposal, approval, configuration)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_INVALID)


def test_a_configuration_without_validity_is_an_error(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    del configuration["policies"][POLICY_APPROVAL]["validity"]
    outcome = evaluate_approval(proposal, approval, configuration)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_MISSING)


# --- the amount and the threshold --------------------------------------------------------


@pytest.mark.parametrize("amount", ["1000.00", "1000.0", "1000", "999.99", "0.01", "1"])
def test_an_amount_at_or_below_the_threshold_needs_no_approval(
    proposal: PurchaseProposal, configuration: dict[str, Any], amount: str
) -> None:
    outcome = evaluate_approval(with_amount(proposal, amount), None, configuration)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.APPROVAL_NOT_REQUIRED)
    assert outcome.basis is OutcomeBasis.NOT_REQUIRED


@pytest.mark.parametrize("amount", ["1000.01", "1000.1", "1001", "99999999999.99"])
def test_an_amount_above_the_threshold_needs_an_approval(
    proposal: PurchaseProposal, configuration: dict[str, Any], amount: str
) -> None:
    outcome = evaluate_approval(with_amount(proposal, amount), None, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_MISSING)


def test_a_denied_approval_does_not_matter_below_the_threshold(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    denied = replace(approval, status="DENIED")
    outcome = evaluate_approval(with_amount(proposal, "999.99"), denied, configuration)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.APPROVAL_NOT_REQUIRED)


INVALID_AMOUNTS: list[Any] = [
    # missing, empty or not text
    None,
    "",
    " ",
    1000.5,
    1001,
    True,
    ["1000.01"],
    # text that is not a plain positive decimal
    "abc",
    "1e3",
    "-1.00",
    "+5",
    "0",
    "0.00",
    "1000.001",
    " 1000.01",
    "1000.01 ",
    "1,000.00",
    "NaN",
    "Infinity",
]


@pytest.mark.parametrize("amount", INVALID_AMOUNTS, ids=lambda value: f"amount-{value!r}")
def test_an_amount_that_is_not_a_positive_decimal_string_is_an_error(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    amount: Any,
) -> None:
    outcome = evaluate_approval(with_amount(proposal, amount), approval, configuration)
    assert_outcome(outcome, ERROR, ReasonCode.AMOUNT_INVALID)


# --- the currency ------------------------------------------------------------------------


@pytest.mark.parametrize("currency", ["EUR", "usd", "Usd", "US", "", " USD"])
def test_a_currency_without_a_rule_is_an_error_and_is_never_converted(
    proposal: PurchaseProposal, configuration: dict[str, Any], currency: str
) -> None:
    outcome = evaluate_approval(replace(proposal, currency=currency), None, configuration)
    assert_outcome(outcome, ERROR, ReasonCode.CURRENCY_UNSUPPORTED)


def add_eur_rule(configuration: dict[str, Any]) -> None:
    rule: dict[str, Any] = {
        "currency": "EUR",
        "threshold": "500.00",
        "approval_level": "director",
        "fraction_digits": 2,
    }
    configuration["policies"][POLICY_APPROVAL]["currency_rules"].append(rule)


def test_each_currency_uses_its_own_threshold(
    proposal: PurchaseProposal, configuration: dict[str, Any]
) -> None:
    add_eur_rule(configuration)
    eur = replace(proposal, currency="EUR", total_amount="600.00")
    assert_outcome(evaluate_approval(eur, None, configuration), FAIL, ReasonCode.APPROVAL_MISSING)
    usd = replace(proposal, total_amount="600.00")
    outcome = evaluate_approval(usd, None, configuration)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.APPROVAL_NOT_REQUIRED)


def test_the_required_approval_level_comes_from_the_rule_of_the_currency(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    add_eur_rule(configuration)
    eur = replace(proposal, currency="EUR", total_amount="600.00")
    granted = with_bound(approval, currency="EUR", total_amount="600.00")
    wrong_level = evaluate_approval(eur, granted, configuration)
    assert_outcome(wrong_level, FAIL, ReasonCode.APPROVAL_BINDING_MISMATCH)
    right_level = evaluate_approval(
        eur, with_bound(granted, approval_level="director"), configuration
    )
    assert_outcome(right_level, PASS, ReasonCode.APPROVAL_VALID)


# --- the approval record -----------------------------------------------------------------


def test_a_valid_approval_passes(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    outcome = evaluate_approval(proposal, approval, configuration)
    assert_outcome(outcome, PASS, ReasonCode.APPROVAL_VALID)
    assert outcome.basis is None


def test_no_approval_record_fails(
    proposal: PurchaseProposal, configuration: dict[str, Any]
) -> None:
    outcome = evaluate_approval(proposal, None, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_MISSING)


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("PENDING", ReasonCode.APPROVAL_PENDING),
        ("DENIED", ReasonCode.APPROVAL_DENIED),
        ("CANCELLED", ReasonCode.APPROVAL_CANCELLED),
    ],
)
def test_an_approval_that_is_not_granted_fails(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    status: str,
    reason: ReasonCode,
) -> None:
    outcome = evaluate_approval(proposal, replace(approval, status=status), configuration)
    assert_outcome(outcome, FAIL, reason)


@pytest.mark.parametrize("status", ["approved", "Approved", "REVOKED", "EXPIRED", "", " APPROVED"])
def test_an_unrecognised_approval_status_is_an_error_never_a_pass(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    status: str,
) -> None:
    outcome = evaluate_approval(proposal, replace(approval, status=status), configuration)
    assert_outcome(outcome, ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


def test_an_approval_event_that_disagrees_with_the_record_fails(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    contradicting = replace(approval, record_agrees=False)
    outcome = evaluate_approval(proposal, contradicting, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION)


def test_an_approver_below_the_required_level_fails(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    outcome = evaluate_approval(proposal, replace(approval, approver_eligible=False), configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVER_NOT_ELIGIBLE)


# --- the order of decision and proposal --------------------------------------------------


def test_an_approval_decided_after_the_proposal_fails(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    late = replace(approval, decision_order=DecisionOrder.AFTER_PROPOSAL)
    outcome = evaluate_approval(proposal, late, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_AFTER_PROPOSAL)


@pytest.mark.parametrize(
    "order",
    [DecisionOrder.FUTURE_DATED, DecisionOrder.UNORDERABLE, DecisionOrder.CONFLICTING, None],
    ids=["future-dated", "unorderable", "conflicting", "no-order"],
)
def test_an_order_that_cannot_be_proved_is_an_error(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    order: DecisionOrder | None,
) -> None:
    outcome = evaluate_approval(proposal, replace(approval, decision_order=order), configuration)
    assert_outcome(outcome, ERROR, ReasonCode.APPROVAL_ORDER_UNDETERMINED)


# --- what the approval was granted for ---------------------------------------------------


def test_an_approval_for_another_request_revision_is_stale(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    outcome = evaluate_approval(
        proposal, with_bound(approval, request_revision="rev-2"), configuration
    )
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_STALE_REVISION)


@pytest.mark.parametrize(
    "changes",
    [
        {"total_amount": "1000.02"},
        {"total_amount": "abc"},
        {"total_amount": ""},
        {"currency": "EUR"},
        {"currency": "usd"},
        {"supplier_id": "sup-2"},
        {"approval_level": "director"},
        {"approval_level": "Manager"},
    ],
    ids=lambda changes: next(iter(changes)) + "=" + next(iter(changes.values())),
)
def test_an_approval_granted_for_something_else_is_a_binding_mismatch(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    changes: dict[str, str],
) -> None:
    outcome = evaluate_approval(proposal, with_bound(approval, **changes), configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_BINDING_MISMATCH)


@pytest.mark.parametrize(("proposed", "granted"), [("1000.1", "1000.10"), ("1000.10", "1000.1")])
def test_amounts_equal_in_value_are_the_same_amount(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    proposed: str,
    granted: str,
) -> None:
    outcome = evaluate_approval(
        with_amount(proposal, proposed), with_bound(approval, total_amount=granted), configuration
    )
    assert_outcome(outcome, PASS, ReasonCode.APPROVAL_VALID)


# --- when several things are wrong, the order is fixed ----------------------------------


def test_a_contradiction_is_reported_before_the_order(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    both = replace(approval, record_agrees=False, decision_order=DecisionOrder.AFTER_PROPOSAL)
    outcome = evaluate_approval(proposal, both, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION)


def test_the_order_is_reported_before_the_binding(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    both = replace(
        with_bound(approval, request_revision="rev-2"), decision_order=DecisionOrder.AFTER_PROPOSAL
    )
    outcome = evaluate_approval(proposal, both, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_AFTER_PROPOSAL)


def test_a_stale_revision_is_reported_before_another_binding_mismatch(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    both = with_bound(approval, request_revision="rev-2", supplier_id="sup-2")
    outcome = evaluate_approval(proposal, both, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_STALE_REVISION)


def test_the_binding_is_reported_before_the_approver(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    both = replace(with_bound(approval, supplier_id="sup-2"), approver_eligible=False)
    outcome = evaluate_approval(proposal, both, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_BINDING_MISMATCH)


# --- safe to call and to share -----------------------------------------------------------


def test_evaluating_does_not_change_its_inputs(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    before = copy.deepcopy(configuration)
    evaluate_approval(proposal, approval, configuration)
    assert configuration == before


def test_an_outcome_cannot_be_changed(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    outcome = evaluate_approval(proposal, approval, configuration)
    with pytest.raises(FrozenInstanceError):
        outcome.__setattr__("result", PolicyResult.FAIL)


def test_the_same_input_always_gives_the_same_outcome(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    first = evaluate_approval(proposal, approval, configuration)
    assert evaluate_approval(proposal, approval, copy.deepcopy(configuration)) == first
