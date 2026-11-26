"""PROC-APPROVAL-01 in every state it can face.

The baseline is a proposal just above the threshold (1000.00 USD) with a valid approval. Each
test changes one thing and states the result the policy must give.
"""

import copy
from collections.abc import Callable
from dataclasses import FrozenInstanceError, dataclass, replace
from itertools import combinations
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
        {"total_amount": "999.99"},
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


MALFORMED_BOUND_AMOUNTS = [
    # signs, padding, exponents and leading zeros that Decimal alone would accept
    "+1000.01",
    " 1000.01",
    "1000.01 ",
    "\t1000.01\n",
    "1.00001E3",
    "1e3",
    "1E3",
    "01000.01",
    "1000.010",
    "1000.01000",
    "1_000.01",
    "1000,01",
    # digits that are not ASCII 0-9: full-width and Arabic-Indic
    "１０００.０１",
    "١٠٠٠.٠١",
    # not finite, not positive, not a number
    "NaN",
    "nan",
    "Infinity",
    "-Infinity",
    "-1000.01",
    "0",
    "0.00",
    "",
    " ",
    "abc",
    "1000.001",
]


@pytest.mark.parametrize("granted", MALFORMED_BOUND_AMOUNTS, ids=repr)
def test_a_malformed_bound_amount_is_unresolved_evidence_and_never_matches(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    granted: str,
) -> None:
    outcome = evaluate_approval(proposal, with_bound(approval, total_amount=granted), configuration)
    assert_outcome(outcome, ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


@pytest.mark.parametrize(
    ("proposed", "granted"),
    [("1000.1", "1000.10"), ("1000.10", "1000.1"), ("1001", "1001.00"), ("1001.0", "1001")],
)
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


# --- the precision a rule allows ---------------------------------------------------------


def allow_four_fraction_digits(configuration: dict[str, Any]) -> None:
    """A pattern looser than the rule's fraction digits, so only the precision check stops it."""
    block = configuration["policies"][POLICY_APPROVAL]
    block["amount_input"]["pattern"] = r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,4})?"


def test_a_proposal_amount_with_more_digits_than_the_rule_allows_is_invalid(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    allow_four_fraction_digits(configuration)
    outcome = evaluate_approval(with_amount(proposal, "1000.001"), approval, configuration)
    assert_outcome(outcome, ERROR, ReasonCode.AMOUNT_INVALID)


def test_a_bound_amount_with_more_digits_than_the_rule_allows_is_unresolved(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    allow_four_fraction_digits(configuration)
    outcome = evaluate_approval(
        proposal, with_bound(approval, total_amount="1000.0100"), configuration
    )
    assert_outcome(outcome, ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


def test_a_rule_with_no_fraction_digits_accepts_whole_amounts_only(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    rule = configuration["policies"][POLICY_APPROVAL]["currency_rules"][0]
    rule["fraction_digits"] = 0
    fractional = evaluate_approval(with_amount(proposal, "1000.5"), approval, configuration)
    assert_outcome(fractional, ERROR, ReasonCode.AMOUNT_INVALID)
    whole = evaluate_approval(
        with_amount(proposal, "1001"), with_bound(approval, total_amount="1001"), configuration
    )
    assert_outcome(whole, PASS, ReasonCode.APPROVAL_VALID)


# --- when several things are wrong, the order is fixed ----------------------------------


@dataclass(frozen=True)
class Fault:
    """One fault of an APPROVED record and the single outcome it must produce on its own."""

    name: str
    result: PolicyResult
    reason: ReasonCode
    apply: Callable[[ApprovalEvidence], ApprovalEvidence]


# In the documented order of evaluation (see the module docstring of approval_rule).
APPROVED_RECORD_FAULTS = [
    Fault(
        "contradiction",
        FAIL,
        ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION,
        lambda approval: replace(approval, record_agrees=False),
    ),
    Fault(
        "decided-after",
        FAIL,
        ReasonCode.APPROVAL_AFTER_PROPOSAL,
        lambda approval: replace(approval, decision_order=DecisionOrder.AFTER_PROPOSAL),
    ),
    Fault(
        "stale-revision",
        FAIL,
        ReasonCode.APPROVAL_STALE_REVISION,
        lambda approval: with_bound(approval, request_revision="rev-2"),
    ),
    Fault(
        "malformed-bound-amount",
        ERROR,
        ReasonCode.EVIDENCE_UNRESOLVED,
        lambda approval: with_bound(approval, total_amount="+1000.01"),
    ),
    Fault(
        "binding-mismatch",
        FAIL,
        ReasonCode.APPROVAL_BINDING_MISMATCH,
        lambda approval: with_bound(approval, supplier_id="sup-2"),
    ),
    Fault(
        "approver-not-eligible",
        FAIL,
        ReasonCode.APPROVER_NOT_ELIGIBLE,
        lambda approval: replace(approval, approver_eligible=False),
    ),
]
FAULT_PAIRS = list(combinations(range(len(APPROVED_RECORD_FAULTS)), 2))
FAULT_NAMES = [fault.name for fault in APPROVED_RECORD_FAULTS]


@pytest.mark.parametrize("fault", APPROVED_RECORD_FAULTS, ids=FAULT_NAMES)
def test_each_fault_of_an_approved_record_is_reported_on_its_own(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    fault: Fault,
) -> None:
    outcome = evaluate_approval(proposal, fault.apply(approval), configuration)
    assert_outcome(outcome, fault.result, fault.reason)


@pytest.mark.parametrize(
    ("first", "second"),
    FAULT_PAIRS,
    ids=[f"{FAULT_NAMES[a]}+{FAULT_NAMES[b]}" for a, b in FAULT_PAIRS],
)
def test_with_two_faults_the_earlier_one_in_the_documented_order_is_reported(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    first: int,
    second: int,
) -> None:
    earlier, later = APPROVED_RECORD_FAULTS[first], APPROVED_RECORD_FAULTS[second]
    both = later.apply(earlier.apply(approval))
    outcome = evaluate_approval(proposal, both, configuration)
    assert_outcome(outcome, earlier.result, earlier.reason)


def test_with_every_fault_at_once_the_first_in_the_order_is_reported(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    everything = approval
    for fault in APPROVED_RECORD_FAULTS:
        everything = fault.apply(everything)
    outcome = evaluate_approval(proposal, everything, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION)


@pytest.mark.parametrize("later", APPROVED_RECORD_FAULTS[2:], ids=FAULT_NAMES[2:])
def test_an_order_that_cannot_be_proved_is_reported_before_the_later_faults(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    later: Fault,
) -> None:
    unprovable = replace(approval, decision_order=DecisionOrder.UNORDERABLE)
    outcome = evaluate_approval(proposal, later.apply(unprovable), configuration)
    assert_outcome(outcome, ERROR, ReasonCode.APPROVAL_ORDER_UNDETERMINED)


def test_a_contradiction_is_reported_before_an_order_that_cannot_be_proved(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    both = replace(approval, record_agrees=False, decision_order=DecisionOrder.UNORDERABLE)
    outcome = evaluate_approval(proposal, both, configuration)
    assert_outcome(outcome, FAIL, ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION)


# --- faults of the proposal and the record status come before the record's own faults ----


def faulty_record(approval: ApprovalEvidence) -> ApprovalEvidence:
    """A record with every fault of an approved record, so that none of them may be reached."""
    for fault in APPROVED_RECORD_FAULTS:
        approval = fault.apply(approval)
    return approval


@pytest.mark.parametrize(
    ("status", "result", "reason"),
    [
        ("PENDING", FAIL, ReasonCode.APPROVAL_PENDING),
        ("DENIED", FAIL, ReasonCode.APPROVAL_DENIED),
        ("CANCELLED", FAIL, ReasonCode.APPROVAL_CANCELLED),
        ("REVOKED", ERROR, ReasonCode.EVIDENCE_UNRESOLVED),
    ],
)
def test_the_status_is_reported_before_any_fault_of_an_approved_record(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence,
    configuration: dict[str, Any],
    status: str,
    result: PolicyResult,
    reason: ReasonCode,
) -> None:
    record = replace(faulty_record(approval), status=status)
    assert_outcome(evaluate_approval(proposal, record, configuration), result, reason)


def test_a_missing_record_is_reported_even_when_nothing_else_can_be_read(
    proposal: PurchaseProposal, configuration: dict[str, Any]
) -> None:
    assert_outcome(
        evaluate_approval(proposal, None, configuration), FAIL, ReasonCode.APPROVAL_MISSING
    )


def test_an_invalid_amount_is_reported_before_the_approval_record(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    outcome = evaluate_approval(
        with_amount(proposal, "abc"), faulty_record(approval), configuration
    )
    assert_outcome(outcome, ERROR, ReasonCode.AMOUNT_INVALID)
    assert_outcome(
        evaluate_approval(with_amount(proposal, None), None, configuration),
        ERROR,
        ReasonCode.AMOUNT_INVALID,
    )


def test_an_unsupported_currency_is_reported_before_the_approval_record(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    eur = replace(proposal, currency="EUR")
    outcome = evaluate_approval(eur, faulty_record(approval), configuration)
    assert_outcome(outcome, ERROR, ReasonCode.CURRENCY_UNSUPPORTED)


def test_an_invalid_amount_is_reported_before_an_unsupported_currency(
    proposal: PurchaseProposal, configuration: dict[str, Any]
) -> None:
    both = replace(with_amount(proposal, "abc"), currency="EUR")
    assert_outcome(evaluate_approval(both, None, configuration), ERROR, ReasonCode.AMOUNT_INVALID)


def test_a_broken_configuration_is_reported_before_an_invalid_amount(
    proposal: PurchaseProposal, configuration: dict[str, Any]
) -> None:
    configuration["policies"][POLICY_APPROVAL]["comparator"] = "GTE"
    outcome = evaluate_approval(with_amount(proposal, "abc"), None, configuration)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_INVALID)


def test_below_the_threshold_no_fault_of_the_record_is_reached(
    proposal: PurchaseProposal, approval: ApprovalEvidence, configuration: dict[str, Any]
) -> None:
    below = with_amount(proposal, "999.99")
    outcome = evaluate_approval(below, faulty_record(approval), configuration)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.APPROVAL_NOT_REQUIRED)


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
