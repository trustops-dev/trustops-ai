"""Plain-dictionary boundary of the policy engine.

Turns the dictionaries a caller sends into the typed inputs of the policies, and the typed
results back into dictionaries. A malformed input raises ``InvalidCheckInput``. The caller must
treat that as "no verdict, nothing dispatched" (truth tables, AG-08); it is never an ``ALLOW``.

The dictionary shape is provisional until it is agreed with the platform owner.
"""

from collections.abc import Mapping
from typing import Any

from .aggregation import CheckFindings
from .evidence import ApprovalBinding, ApprovalEvidence, DecisionOrder, PurchaseProposal
from .results import AggregateOutcome, PolicyOutcome, PolicyResult


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


def parse_aggregation_input(
    data: Mapping[str, Any],
) -> tuple[dict[str, PolicyResult], CheckFindings]:
    results = _mapping(data.get("policy_results"), "policy_results")
    findings = CheckFindings(
        policy_set_version_matches=_flag(data, "policy_set_version_matches", ""),
        context_consistent=_flag(data, "context_consistent", ""),
        request_well_formed=_flag(data, "request_well_formed", ""),
        evidence_consistency_findings=_findings(data),
        evidence_unresolved=_flag(data, "evidence_unresolved", ""),
    )
    return {str(policy): _result(value, str(policy)) for policy, value in results.items()}, findings


def _findings(data: Mapping[str, Any]) -> tuple[str, ...]:
    raw = data.get("evidence_consistency_findings")
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
        "result": outcome.result.value,
        "reason_code": outcome.reason_code.value,
        "basis": None if outcome.basis is None else outcome.basis.value,
    }


def aggregate_to_dict(outcome: AggregateOutcome) -> dict[str, Any]:
    return {"verdict": outcome.verdict.value, "verdict_basis": outcome.verdict_basis.value}


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


def _flag(parent: Mapping[str, Any], key: str, where: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise InvalidCheckInput(f"{_name(where, key)}: must be true or false")
    return value


def _name(where: str, key: str) -> str:
    return key if where == "" else f"{where}.{key}"
