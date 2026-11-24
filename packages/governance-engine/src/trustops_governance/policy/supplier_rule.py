"""PROC-SUPPLIER-01: a purchase order may be proposed only for an eligible supplier.

Only the exact configured status passes (``APPROVED`` in the synthetic configuration). Every other
status string, whatever its spelling, is a failure, so no list of non-approved spellings is kept.
Missing evidence is not a verdict on the supplier: it is ERROR, never FAIL and never PASS.

Order of evaluation. The first fault found is the one reported.

1. Scope: any tool other than create_purchase_order is NOT_APPLICABLE.
2. Configuration: an unusable configuration is ERROR (POLICY_CONFIG_MISSING or _INVALID).
3. Lookup: no snapshot, or a lookup that ended in ERROR, is ERROR (SUPPLIER_EVIDENCE_MISSING);
   NOT_FOUND is FAIL (SUPPLIER_NOT_FOUND); a lookup outcome that is not recognised is ERROR
   (EVIDENCE_UNRESOLVED).
4. Status present: a found supplier whose status is null is ERROR (SUPPLIER_EVIDENCE_MISSING).
5. Identity: a snapshot for another supplier than the proposal's is FAIL (SUPPLIER_ID_MISMATCH).
6. Status: the configured status is PASS (SUPPLIER_APPROVED); UNKNOWN is FAIL
   (SUPPLIER_STATUS_UNKNOWN); any other status is FAIL (SUPPLIER_NOT_APPROVED).

Every outcome carries the per-rule policy version (none when the configuration could not be read)
and the values observed: the proposed and the snapshot supplier ids, the lookup outcome, the
status and the configured eligible status once known.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .evidence import CREATE_PURCHASE_ORDER, PurchaseProposal, SupplierEvidence, SupplierLookup
from .loader import Configuration, load_supplier_policy
from .policy_schema import POLICY_SUPPLIER, PolicyConfigError, SupplierPolicy
from .reporting import Reporter, config_reason
from .results import PolicyOutcome, PolicyResult, ReasonCode

UNKNOWN_STATUS = "UNKNOWN"


@dataclass(frozen=True)
class _Case:
    """Everything one supplier check needs. The supplier is checked present before use."""

    proposal: PurchaseProposal
    supplier: SupplierEvidence
    policy: SupplierPolicy
    reporter: Reporter


Check = Callable[[_Case], PolicyOutcome | None]


def evaluate_supplier(
    proposal: PurchaseProposal, supplier: SupplierEvidence | None, configuration: Configuration
) -> PolicyOutcome:
    """Evaluate PROC-SUPPLIER-01 for one proposal. Never raises for a bad configuration."""
    reporter = Reporter(POLICY_SUPPLIER, None, _observed(proposal, supplier))
    if proposal.tool != CREATE_PURCHASE_ORDER:
        return reporter.outcome(PolicyResult.NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)
    try:
        policy = load_supplier_policy(configuration)
    except PolicyConfigError as error:
        return reporter.outcome(PolicyResult.ERROR, config_reason(error))
    reporter = reporter.knowing(policy.version, eligible_status=policy.eligible_status)
    if supplier is None:
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)
    return _judge(_Case(proposal, supplier, policy, reporter))


def _observed(
    proposal: PurchaseProposal, supplier: SupplierEvidence | None
) -> dict[str, str | None]:
    """The values this policy looks at, as text. The eligible status is added once known."""
    return {
        "proposed_supplier_id": proposal.supplier_id,
        "supplier_id": None if supplier is None else supplier.supplier_id,
        "lookup_outcome": None if supplier is None else supplier.lookup_outcome,
        "supplier_status": None if supplier is None else supplier.status,
        "eligible_status": None,
    }


def _judge(case: _Case) -> PolicyOutcome:
    """Run the checks in the documented order. The first fault wins; the last step decides."""
    checks: tuple[Check, ...] = (_check_lookup, _check_status_present, _check_identity)
    for check in checks:
        outcome = check(case)
        if outcome is not None:
            return outcome
    return _judge_status(case)


def _check_lookup(case: _Case) -> PolicyOutcome | None:
    lookup, reporter = case.supplier.lookup_outcome, case.reporter
    if lookup == SupplierLookup.FOUND:
        return None
    if lookup == SupplierLookup.ERROR:
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)
    if lookup == SupplierLookup.NOT_FOUND:
        return reporter.outcome(PolicyResult.FAIL, ReasonCode.SUPPLIER_NOT_FOUND)
    return reporter.outcome(PolicyResult.ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


def _check_status_present(case: _Case) -> PolicyOutcome | None:
    if case.supplier.status is not None:
        return None
    return case.reporter.outcome(PolicyResult.ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)


def _check_identity(case: _Case) -> PolicyOutcome | None:
    if case.supplier.supplier_id == case.proposal.supplier_id:
        return None
    return case.reporter.outcome(PolicyResult.FAIL, ReasonCode.SUPPLIER_ID_MISMATCH)


def _judge_status(case: _Case) -> PolicyOutcome:
    """Only the exact configured status passes. Every other status is a failure."""
    status, reporter = case.supplier.status, case.reporter
    if status == case.policy.eligible_status:
        return reporter.outcome(PolicyResult.PASS, ReasonCode.SUPPLIER_APPROVED)
    if status == UNKNOWN_STATUS:
        return reporter.outcome(PolicyResult.FAIL, ReasonCode.SUPPLIER_STATUS_UNKNOWN)
    return reporter.outcome(PolicyResult.FAIL, ReasonCode.SUPPLIER_NOT_APPROVED)
