"""PROC-APPROVAL-01: a purchase above the configured threshold needs a valid approval first.

Governance derives whether approval is required from the amount, the currency and the
configured threshold. It never takes that from the application's own flag. Exceeding the
threshold is strictly greater-than: an amount equal to it needs no approval.

Order of evaluation. The first fault found is the one reported; later checks do not run.

1. Scope: any tool other than create_purchase_order is NOT_APPLICABLE.
2. Configuration: an unusable configuration is ERROR (POLICY_CONFIG_MISSING or _INVALID).
3. Proposal amount: not a plain positive decimal string is ERROR (AMOUNT_INVALID).
4. Currency: no rule for the exact currency is ERROR (CURRENCY_UNSUPPORTED).
5. Precision: more fraction digits than the rule allows is ERROR (AMOUNT_INVALID).
6. Threshold: at or below it is NOT_APPLICABLE (APPROVAL_NOT_REQUIRED); no evidence is read.

Above the threshold the approval record is judged:

7. No record is FAIL (APPROVAL_MISSING).
8. Status: PENDING, DENIED, CANCELLED or STALE_REVISION is FAIL (STALE_REVISION reports
   APPROVAL_STALE_REVISION, as a record bound to another revision does). EXPIRED and any status
   that is not recognised is ERROR (EVIDENCE_UNRESOLVED): the MVP has no time-based expiry, so a
   record that claims to be EXPIRED is itself inconsistent evidence, never a pass.

For an APPROVED record, in this order:

9. Record and event disagree: FAIL (APPROVAL_EVIDENCE_CONTRADICTION).
10. Decision order: after the proposal is FAIL (APPROVAL_AFTER_PROPOSAL); an order that cannot be
    proved is ERROR (APPROVAL_ORDER_UNDETERMINED).
11. Request revision: bound to another revision is FAIL (APPROVAL_STALE_REVISION).
12. Bound amount: it must be read as strictly as the proposal amount (plain positive decimal
    string, configured pattern, allowed precision). Anything else, such as "+1000.01", " 1000.01",
    "1e3", "01000.01", "1000.010" or "1_000.01", is ERROR (EVIDENCE_UNRESOLVED). Malformed
    evidence can never match, and it is not reported as a mismatch because the amount that was
    approved is unknown.
13. Binding: amount (equal in value, so 1000.1 equals 1000.10), currency, supplier or approval
    level differ is FAIL (APPROVAL_BINDING_MISMATCH).
14. Approver: below the required level is FAIL (APPROVER_NOT_ELIGIBLE).

Every outcome carries the per-rule policy version (none when the configuration could not be
read) and the values observed: the tool, the amount and currency as given, the configured
threshold once known, and the approval status and decision order.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .evidence import (
    CREATE_PURCHASE_ORDER,
    ApprovalEvidence,
    ApprovalStatus,
    DecisionOrder,
    PurchaseProposal,
)
from .loader import Configuration, load_approval_policy
from .policy_schema import POLICY_APPROVAL, ApprovalPolicy, ApprovalRule, PolicyConfigError
from .reporting import Reporter, config_reason, text_or_none
from .results import OutcomeBasis, PolicyOutcome, PolicyResult, ReasonCode

# EXPIRED is deliberately absent: it has no failure reason because the MVP has no expiry.
_UNFINISHED_STATUS = {
    ApprovalStatus.PENDING: ReasonCode.APPROVAL_PENDING,
    ApprovalStatus.DENIED: ReasonCode.APPROVAL_DENIED,
    ApprovalStatus.CANCELLED: ReasonCode.APPROVAL_CANCELLED,
    ApprovalStatus.STALE_REVISION: ReasonCode.APPROVAL_STALE_REVISION,
}


@dataclass(frozen=True)
class _Scope:
    """The proposal as validated so far: its amount, its currency rule and its reporter."""

    proposal: PurchaseProposal
    amount: Decimal
    rule: ApprovalRule
    amount_pattern: str
    reporter: Reporter


@dataclass(frozen=True)
class _Case:
    """Everything one check of an APPROVED record needs."""

    scope: _Scope
    approval: ApprovalEvidence


Check = Callable[[_Case], PolicyOutcome | None]


def evaluate_approval(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence | None,
    configuration: Configuration,
) -> PolicyOutcome:
    """Evaluate PROC-APPROVAL-01 for one proposal. Never raises for a bad configuration."""
    reporter = Reporter(POLICY_APPROVAL, None, _observed(proposal, approval))
    if proposal.tool != CREATE_PURCHASE_ORDER:
        return reporter.outcome(PolicyResult.NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)
    try:
        policy = load_approval_policy(configuration)
    except PolicyConfigError as error:
        return reporter.outcome(PolicyResult.ERROR, config_reason(error))
    return _evaluate_in_scope(proposal, approval, policy, reporter.knowing(policy.version))


def _observed(
    proposal: PurchaseProposal, approval: ApprovalEvidence | None
) -> dict[str, str | None]:
    """The values this policy looks at, as text. The threshold is added once it is known."""
    order = None if approval is None else approval.decision_order
    return {
        "tool": proposal.tool,
        "total_amount": text_or_none(proposal.total_amount),
        "currency": proposal.currency,
        "configured_threshold": None,
        "approval_status": None if approval is None else approval.status,
        "decision_order": None if order is None else order.value,
    }


def _evaluate_in_scope(
    proposal: PurchaseProposal,
    approval: ApprovalEvidence | None,
    policy: ApprovalPolicy,
    reporter: Reporter,
) -> PolicyOutcome:
    amount = _parse_amount(proposal.total_amount, policy.amount_pattern)
    if amount is None:
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.AMOUNT_INVALID)
    rule = _rule_for_currency(policy, proposal.currency)
    if rule is None:
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.CURRENCY_UNSUPPORTED)
    reporter = reporter.knowing(configured_threshold=str(rule.threshold))
    if not _fits_precision(amount, rule):
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.AMOUNT_INVALID)
    if not amount > rule.threshold:
        return _not_required(reporter)
    scope = _Scope(proposal, amount, rule, policy.amount_pattern, reporter)
    return _evaluate_approval_evidence(scope, approval)


def _parse_amount(raw: object, pattern: str) -> Decimal | None:
    """A positive, finite decimal that matches the configured pattern, else None.

    The pattern is matched first, so Decimal never sees whitespace, a sign, an exponent, an
    underscore or a non-ASCII digit, all of which Decimal itself would accept.
    """
    if not isinstance(raw, str) or re.fullmatch(pattern, raw) is None:
        return None
    try:
        amount = Decimal(raw)
    except InvalidOperation:
        return None
    return amount if amount.is_finite() and amount > 0 else None


def _fits_precision(amount: Decimal, rule: ApprovalRule) -> bool:
    """No more fraction digits than the rule allows. An amount is never rounded."""
    exponent = amount.as_tuple().exponent
    return isinstance(exponent, int) and -exponent <= rule.fraction_digits


def _rule_for_currency(policy: ApprovalPolicy, currency: str) -> ApprovalRule | None:
    """Currency matching is exact and case-sensitive. No conversion is ever applied."""
    return next((rule for rule in policy.rules if rule.currency == currency), None)


def _evaluate_approval_evidence(scope: _Scope, approval: ApprovalEvidence | None) -> PolicyOutcome:
    reporter = scope.reporter
    if approval is None:
        return reporter.outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_MISSING)
    unfinished = _unfinished_status_outcome(approval.status, reporter)
    if unfinished is not None:
        return unfinished
    return _evaluate_approved(_Case(scope, approval))


def _unfinished_status_outcome(status: str, reporter: Reporter) -> PolicyOutcome | None:
    """The outcome for every status except APPROVED, or None when the record is APPROVED."""
    if status == ApprovalStatus.APPROVED:
        return None
    if status in _UNFINISHED_STATUS:
        return reporter.outcome(PolicyResult.FAIL, _UNFINISHED_STATUS[ApprovalStatus(status)])
    return reporter.outcome(PolicyResult.ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


def _evaluate_approved(case: _Case) -> PolicyOutcome:
    """Run the checks of an APPROVED record in the documented order. The first fault wins."""
    checks: tuple[Check, ...] = (
        _check_agreement,
        _check_order,
        _check_revision,
        _check_binding,
        _check_approver,
    )
    for check in checks:
        outcome = check(case)
        if outcome is not None:
            return outcome
    return case.scope.reporter.outcome(PolicyResult.PASS, ReasonCode.APPROVAL_VALID)


def _check_agreement(case: _Case) -> PolicyOutcome | None:
    if case.approval.record_agrees:
        return None
    reporter = case.scope.reporter
    return reporter.outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_EVIDENCE_CONTRADICTION)


def _check_order(case: _Case) -> PolicyOutcome | None:
    """An approval counts only when it was decided before the proposal, in a provable order."""
    order = case.approval.decision_order
    if order == DecisionOrder.BEFORE_PROPOSAL:
        return None
    reporter = case.scope.reporter
    if order == DecisionOrder.AFTER_PROPOSAL:
        return reporter.outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_AFTER_PROPOSAL)
    return reporter.outcome(PolicyResult.ERROR, ReasonCode.APPROVAL_ORDER_UNDETERMINED)


def _check_revision(case: _Case) -> PolicyOutcome | None:
    if case.approval.bound.request_revision == case.scope.proposal.request_revision:
        return None
    return case.scope.reporter.outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_STALE_REVISION)


def _check_binding(case: _Case) -> PolicyOutcome | None:
    """The bound amount is read strictly first. Evidence that cannot be read never matches."""
    reporter = case.scope.reporter
    bound_amount = _read_bound_amount(case)
    if bound_amount is None:
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.EVIDENCE_UNRESOLVED)
    if not _binding_matches(case, bound_amount):
        return reporter.outcome(PolicyResult.FAIL, ReasonCode.APPROVAL_BINDING_MISMATCH)
    return None


def _read_bound_amount(case: _Case) -> Decimal | None:
    """The approved amount, read as strictly as the proposal amount, or None if unreadable."""
    scope = case.scope
    amount = _parse_amount(case.approval.bound.total_amount, scope.amount_pattern)
    if amount is None or not _fits_precision(amount, scope.rule):
        return None
    return amount


def _binding_matches(case: _Case, bound_amount: Decimal) -> bool:
    """The approval was granted for this amount, currency, supplier and approval level."""
    bound, scope = case.approval.bound, case.scope
    return (
        bound_amount == scope.amount
        and bound.currency == scope.proposal.currency
        and bound.supplier_id == scope.proposal.supplier_id
        and bound.approval_level == scope.rule.approval_level
    )


def _check_approver(case: _Case) -> PolicyOutcome | None:
    if case.approval.approver_eligible:
        return None
    return case.scope.reporter.outcome(PolicyResult.FAIL, ReasonCode.APPROVER_NOT_ELIGIBLE)


def _not_required(reporter: Reporter) -> PolicyOutcome:
    return reporter.outcome(
        PolicyResult.NOT_APPLICABLE, ReasonCode.APPROVAL_NOT_REQUIRED, OutcomeBasis.NOT_REQUIRED
    )
