"""Pre-tool policy engine: the public functions of the governance policy module.

Three functions take and return plain dictionaries (see ``boundary``):

* ``evaluate_policy`` evaluates one policy for one proposal;
* ``aggregate`` turns per-policy results into the verdict;
* ``check`` evaluates every mandatory policy for one proposal and aggregates the verdict. Every
  result carries the per-rule policy version and the values observed, and the check carries the
  active policy bundle version and the check mode.

All three mandatory policies are implemented: PROC-APPROVAL-01, PROC-TOOL-STAGE-01 and
PROC-SUPPLIER-01. A malformed input raises ``InvalidCheckInput``, which the caller must treat as
"no verdict, nothing dispatched".
"""

from collections.abc import Callable, Mapping
from typing import Any

from .aggregation import aggregate_results
from .approval_rule import evaluate_approval
from .boundary import (
    aggregate_to_dict,
    check_outcome_to_dict,
    outcome_to_dict,
    parse_aggregation_input,
    parse_approval,
    parse_check_input,
    parse_proposal,
    parse_stage,
    parse_supplier,
)
from .loader import Configuration
from .policy_schema import POLICY_APPROVAL, POLICY_SUPPLIER, POLICY_TOOL_STAGE
from .pre_tool_check import run_check
from .results import PolicyOutcome
from .supplier_rule import evaluate_supplier
from .tool_stage_rule import evaluate_tool_stage

Evaluator = Callable[[Mapping[str, Any], Configuration], PolicyOutcome]


class UnsupportedPolicyError(ValueError):
    """The policy id is not one of the mandatory policies. It is never treated as a pass."""


def _evaluate_approval_policy(
    check_input: Mapping[str, Any], configuration: Configuration
) -> PolicyOutcome:
    proposal, approval = parse_proposal(check_input), parse_approval(check_input)
    return evaluate_approval(proposal, approval, configuration)


def _evaluate_tool_stage_policy(
    check_input: Mapping[str, Any], configuration: Configuration
) -> PolicyOutcome:
    proposal, stage = parse_proposal(check_input), parse_stage(check_input)
    return evaluate_tool_stage(proposal.tool, stage, configuration)


def _evaluate_supplier_policy(
    check_input: Mapping[str, Any], configuration: Configuration
) -> PolicyOutcome:
    proposal, supplier = parse_proposal(check_input), parse_supplier(check_input)
    return evaluate_supplier(proposal, supplier, configuration)


_EVALUATORS: dict[str, Evaluator] = {
    POLICY_APPROVAL: _evaluate_approval_policy,
    POLICY_TOOL_STAGE: _evaluate_tool_stage_policy,
    POLICY_SUPPLIER: _evaluate_supplier_policy,
}

SUPPORTED_POLICIES = frozenset(_EVALUATORS)


def evaluate_policy(
    policy_id: str, check_input: Mapping[str, Any], configuration: Configuration
) -> dict[str, Any]:
    """Evaluate one policy. Raises ``InvalidCheckInput`` when the input cannot be read."""
    evaluator = _EVALUATORS.get(policy_id)
    if evaluator is None:
        raise UnsupportedPolicyError(f"{policy_id} is not a mandatory policy")
    return outcome_to_dict(evaluator(check_input, configuration))


def aggregate(aggregation_input: Mapping[str, Any]) -> dict[str, Any]:
    """Compute the verdict from per-policy results and the check-level findings."""
    results, findings = parse_aggregation_input(aggregation_input)
    return aggregate_to_dict(aggregate_results(results, findings))


def check(check_input: Mapping[str, Any], configuration: Configuration) -> dict[str, Any]:
    """Evaluate every mandatory policy for one proposal and aggregate the verdict."""
    return check_outcome_to_dict(run_check(parse_check_input(check_input), configuration))
