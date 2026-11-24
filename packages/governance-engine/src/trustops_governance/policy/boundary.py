"""Plain-dictionary boundary of the policy engine.

Turns the dictionaries a caller sends into the typed inputs of the policies, and the typed
results back into dictionaries. A malformed input raises ``InvalidCheckInput``. The caller must
treat that as "no verdict, nothing dispatched" (truth tables, AG-08); it is never an ``ALLOW``.

The dictionary shape is provisional until it is agreed with the platform owner.
"""

from collections.abc import Mapping
from typing import Any

from .aggregation import CheckFindings
from .evidence import (
    ApprovalBinding,
    ApprovalEvidence,
    DecisionOrder,
    PurchaseProposal,
    SupplierEvidence,
)
from .pre_tool_check import CheckInput
from .results import AggregateOutcome, CheckOutcome, PolicyOutcome, PolicyResult


class InvalidCheckInput(ValueError):
    """The check input cannot be read. It never means that the proposal is allowed."""


def parse_proposal(check_input: Mapping[str, Any]) -> PurchaseProposal:
    proposal = _mapping(check_input.get("proposal"), "proposal")
    return PurchaseProposal(
        tool=_text(proposal, "tool", "proposal"),
        request_revision=_text(proposal, "request_revision", "proposal"),
        supplier_id=_text(proposal, "supplier_id", "proposal"),
        total_amount=proposal.get("total_amount"),
        currency=_text(proposal, "currency", "proposal"),
    )


def parse_approval(check_input: Mapping[str, Any]) -> ApprovalEvidence | None:
    raw = check_input.get("approval")
    if raw is None:
        return None
    approval = _mapping(raw, "approval")
    return ApprovalEvidence(
        status=_text(approval, "status", "approval"),
        bound=_parse_binding(approval),
        decision_order=_parse_decision_order(approval),
        record_agrees=_flag(approval, "event_agrees_with_record", "approval"),
        approver_eligible=_flag(approval, "approver_level_satisfies_required", "approval"),
    )


def _parse_binding(approval: Mapping[str, Any]) -> ApprovalBinding:
    bound = _mapping(approval.get("bound"), "approval.bound")
    return ApprovalBinding(
        request_revision=_text(bound, "request_revision", "approval.bound"),
        supplier_id=_text(bound, "supplier_id", "approval.bound"),
        total_amount=_text(bound, "total_amount", "approval.bound"),
        currency=_text(bound, "currency", "approval.bound"),
        approval_level=_text(bound, "approval_level", "approval.bound"),
    )


def _parse_decision_order(approval: Mapping[str, Any]) -> DecisionOrder | None:
    raw = approval.get("decided")
    if raw is None:
        return None
    try:
        return DecisionOrder(raw)
    except ValueError:
        raise InvalidCheckInput(f"approval.decided: unknown value {raw!r}") from None


def parse_stage(check_input: Mapping[str, Any]) -> str | None:
    """The coarse policy stage as given, or None when it is absent. Matching is the policy's job."""
    return _optional_text(check_input, "stage", "")


def parse_supplier(check_input: Mapping[str, Any]) -> SupplierEvidence | None:
    raw = check_input.get("supplier")
    if raw is None:
        return None
    supplier = _mapping(raw, "supplier")
    return SupplierEvidence(
        lookup_outcome=_text(supplier, "lookup_outcome", "supplier"),
        supplier_id=_optional_text(supplier, "supplier_id", "supplier"),
        status=_optional_text(supplier, "status", "supplier"),
    )


def parse_check_findings(check_input: Mapping[str, Any]) -> CheckFindings:
    """Findings about the check itself are optional: absent means that none was raised."""
    return CheckFindings(
        policy_set_version_matches=_flag_or(check_input, "policy_set_version_matches", True),
        context_consistent=_flag_or(check_input, "context_consistent", True),
        request_well_formed=_flag_or(check_input, "request_well_formed", True),
        evidence_consistency_findings=_findings(check_input, required=False),
        evidence_unresolved=_flag_or(check_input, "evidence_unresolved", False),
    )


def parse_check_input(check_input: Mapping[str, Any]) -> CheckInput:
    """Everything the full pre-tool check needs, read from one dictionary."""
    return CheckInput(
        proposal=parse_proposal(check_input),
        stage=parse_stage(check_input),
        approval=parse_approval(check_input),
        supplier=parse_supplier(check_input),
        findings=parse_check_findings(check_input),
    )


def parse_aggregation_input(
    data: Mapping[str, Any],
) -> tuple[dict[str, PolicyResult], CheckFindings]:
    results = _mapping(data.get("policy_results"), "policy_results")
    findings = CheckFindings(
        policy_set_version_matches=_flag(data, "policy_set_version_matches", ""),
        context_consistent=_flag(data, "context_consistent", ""),
        request_well_formed=_flag(data, "request_well_formed", ""),
        evidence_consistency_findings=_findings(data, required=True),
        evidence_unresolved=_flag(data, "evidence_unresolved", ""),
    )
    return {str(policy): _result(value, str(policy)) for policy, value in results.items()}, findings


def _findings(data: Mapping[str, Any], *, required: bool) -> tuple[str, ...]:
    raw = data.get("evidence_consistency_findings")
    if raw is None and not required:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise InvalidCheckInput("evidence_consistency_findings: must be a list of text")
    return tuple(raw)


def _result(value: object, policy: str) -> PolicyResult:
    if isinstance(value, str) and value in PolicyResult:
        return PolicyResult(value)
    raise InvalidCheckInput(f"policy_results.{policy}: unknown result {value!r}")


def outcome_to_dict(outcome: PolicyOutcome) -> dict[str, Any]:
    return {
        "policy_id": outcome.policy_id,
        "policy_version": outcome.policy_version,
        "result": outcome.result.value,
        "reason_code": outcome.reason_code.value,
        "basis": None if outcome.basis is None else outcome.basis.value,
        "observed_evidence": dict(outcome.observed_evidence),
    }


def aggregate_to_dict(outcome: AggregateOutcome) -> dict[str, Any]:
    return {"verdict": outcome.verdict.value, "verdict_basis": outcome.verdict_basis.value}


def check_outcome_to_dict(outcome: CheckOutcome) -> dict[str, Any]:
    """The full check as a dictionary: every policy result in a fixed order, then the verdict."""
    return {
        "policy_results": {item.policy_id: outcome_to_dict(item) for item in outcome.outcomes},
        **aggregate_to_dict(outcome.aggregate),
        "policy_bundle_version": outcome.policy_bundle_version,
        "check_mode": outcome.check_mode,
    }


# --- reading values -----------------------------------------------------------------------


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidCheckInput(f"{name}: must be an object")
    return value


def _text(parent: Mapping[str, Any], key: str, where: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str):
        raise InvalidCheckInput(f"{_name(where, key)}: must be text")
    return value


def _optional_text(parent: Mapping[str, Any], key: str, where: str) -> str | None:
    value = parent.get(key)
    if value is not None and not isinstance(value, str):
        raise InvalidCheckInput(f"{_name(where, key)}: must be text or null")
    return value


def _flag(parent: Mapping[str, Any], key: str, where: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise InvalidCheckInput(f"{_name(where, key)}: must be true or false")
    return value


def _flag_or(parent: Mapping[str, Any], key: str, default: bool) -> bool:
    """A flag that may be absent. A value that is present must be a real boolean."""
    value = parent.get(key, default)
    if not isinstance(value, bool):
        raise InvalidCheckInput(f"{key}: must be true or false")
    return value


def _name(where: str, key: str) -> str:
    return key if where == "" else f"{where}.{key}"
