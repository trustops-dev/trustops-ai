"""PROC-APPROVAL-01: a purchase above the configured threshold needs a valid approval first.

Governance derives whether approval is required from the amount, the currency and the
configured threshold. It never takes that from the application's own flag. Exceeding the
threshold is strictly greater-than: an amount equal to it needs no approval.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .evidence import ApprovalEvidence, ApprovalStatus, DecisionOrder, PurchaseProposal
from .loader import Configuration, load_approval_policy
from .policy_schema import (
    POLICY_APPROVAL,
    ApprovalPolicy,
    ApprovalRule,
    ConfigErrorCode,
    PolicyConfigError,
)
from .results import OutcomeBasis, PolicyOutcome, PolicyResult, ReasonCode

CREATE_PURCHASE_ORDER = "create_purchase_order"

_CONFIG_REASONS = {
    ConfigErrorCode.POLICY_CONFIG_MISSING: ReasonCode.POLICY_CONFIG_MISSING,
    ConfigErrorCode.POLICY_CONFIG_INVALID: ReasonCode.POLICY_CONFIG_INVALID,
}
_UNFINISHED_STATUS = {
    ApprovalStatus.PENDING: ReasonCode.APPROVAL_PENDING,
    ApprovalStatus.DENIED: ReasonCode.APPROVAL_DENIED,
    ApprovalStatus.CANCELLED: ReasonCode.APPROVAL_CANCELLED,
}


@dataclass(frozen=True)
class _Case:
    """Everything one approval check needs, already validated up to this point."""

    proposal: PurchaseProposal
    amount: Decimal
    rule: ApprovalRule
    approval: ApprovalEvidence


Check = Callable[[_Case], PolicyOutcome | None]


def evaluate_approval(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence | None,
    configuration: Configuration,
) -> PolicyOutcome:
    """Evaluate PROC-APPROVAL-01 for one proposal. Never raises for a bad configuration."""
    if proposal.tool != CREATE_PURCHASE_ORDER:
        return _outcome(PolicyResult.NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)
    try:
        policy = load_approval_policy(configuration)
    except PolicyConfigError as error:
        reason = _CONFIG_REASONS.get(error.code, ReasonCode.POLICY_CONFIG_INVALID)
        return _outcome(PolicyResult.ERROR, reason)
    return _evaluate_in_scope(proposal, approval, policy)


def _evaluate_in_scope(
    proposal: PurchaseProposal, approval: ApprovalEvidence | None, policy: ApprovalPolicy
) -> PolicyOutcome:
    amount = _parse_amount(proposal.total_amount, policy.amount_pattern)
    if amount is None:
        return _outcome(PolicyResult.ERROR, ReasonCode.AMOUNT_INVALID)
    rule = _rule_for_currency(policy, proposal.currency)
    if rule is None:
        return _outcome(PolicyResult.ERROR, ReasonCode.CURRENCY_UNSUPPORTED)
    if not amount > rule.threshold:
        return _not_required()
    return _evaluate_approval_evidence(proposal, amount, rule, approval)


def _parse_amount(raw: object, pattern: str) -> Decimal | None:
    """A positive, finite decimal that matches the configured pattern, else None."""
    if not isinstance(raw, str) or re.fullmatch(pattern, raw) is None:
        return None
    try:
        amount = Decimal(raw)
    except InvalidOperation:
        return None
    return amount if amount.is_finite() and amount > 0 else None


def _rule_for_currency(policy: ApprovalPolicy, currency: str) -> ApprovalRule | None:
    """Currency matching is exact and case-sensitive. No conversion is ever applied."""
    return next((rule for rule in policy.rules if rule.currency == currency), None)


def _evaluate_approval_evidence(
    proposal: PurchaseProposal,
    amount: Decimal,
    rule: ApprovalRule,
    approval: ApprovalEvidence | None,
) -> PolicyOutcome:
    if approval is None:
        return _outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_MISSING)
    unfinished = _unfinished_status_outcome(approval.status)
    if unfinished is not None:
        return unfinished
    return _evaluate_approved(_Case(proposal, amount, rule, approval))


def _unfinished_status_outcome(status: str) -> PolicyOutcome | None:
    """The outcome for every status except APPROVED, or None when the record is APPROVED."""
    if status == ApprovalStatus.APPROVED:
        return None
    if status in _UNFINISHED_STATUS:
        return _outcome(PolicyResult.FAIL, _UNFINISHED_STATUS[ApprovalStatus(status)])
    return _outcome(PolicyResult.ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


def _evaluate_approved(case: _Case) -> PolicyOutcome:
    checks: tuple[Check, ...] = (_check_agreement, _check_order, _check_binding, _check_approver)
    for check in checks:
        outcome = check(case)
        if outcome is not None:
            return outcome
    return _outcome(PolicyResult.PASS, ReasonCode.APPROVAL_VALID)


def _check_agreement(case: _Case) -> PolicyOutcome | None:
    if case.approval.record_agrees:
        return None
    return _outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION)


def _check_order(case: _Case) -> PolicyOutcome | None:
    """An approval counts only when it was decided before the proposal, in a provable order."""
    order = case.approval.decision_order
    if order == DecisionOrder.BEFORE_PROPOSAL:
        return None
    if order == DecisionOrder.AFTER_PROPOSAL:
        return _outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_AFTER_PROPOSAL)
    return _outcome(PolicyResult.ERROR, ReasonCode.APPROVAL_ORDER_UNDETERMINED)


def _check_binding(case: _Case) -> PolicyOutcome | None:
    bound = case.approval.bound
    if bound.request_revision != case.proposal.request_revision:
        return _outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_STALE_REVISION)
    if not _binding_matches(case):
        return _outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_BINDING_MISMATCH)
    return None


def _binding_matches(case: _Case) -> bool:
    """The approval was granted for this amount, currency, supplier and approval level."""
    bound = case.approval.bound
    return (
        _same_amount(bound.total_amount, case.amount)
        and bound.currency == case.proposal.currency
        and bound.supplier_id == case.proposal.supplier_id
        and bound.approval_level == case.rule.approval_level
    )


def _same_amount(bound_amount: str, amount: Decimal) -> bool:
    """Equal in value, so 1000.1 and 1000.10 are the same amount. Unreadable never matches."""
    try:
        return Decimal(bound_amount) == amount
    except InvalidOperation:
        return False


def _check_approver(case: _Case) -> PolicyOutcome | None:
    if case.approval.approver_eligible:
        return None
    return _outcome(PolicyResult.FAIL, ReasonCode.APPROVER_NOT_ELIGIBLE)


def _not_required() -> PolicyOutcome:
    return PolicyOutcome(
        POLICY_APPROVAL,
        PolicyResult.NOT_APPLICABLE,
        ReasonCode.APPROVAL_NOT_REQUIRED,
        OutcomeBasis.NOT_REQUIRED,
    )


def _outcome(result: PolicyResult, reason: ReasonCode) -> PolicyOutcome:
    return PolicyOutcome(POLICY_APPROVAL, result, reason)
