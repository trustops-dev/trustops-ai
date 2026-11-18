"""Pre-tool policy engine: the public functions of the governance policy module.

Three functions take and return plain dictionaries (see ``boundary``):

* ``evaluate_policy`` evaluates one policy for one proposal;
* ``aggregate`` turns per-policy results into the verdict;
* ``check`` evaluates every mandatory policy and aggregates. It is not available until all
  three policies exist, so that a verdict can never rest on a partial evaluation.

Implemented so far: PROC-APPROVAL-01. PROC-TOOL-STAGE-01 and PROC-SUPPLIER-01 follow.
"""

from collections.abc import Callable, Mapping
from typing import Any

from .aggregation import MANDATORY_POLICIES, aggregate_results
from .approval_rule import evaluate_approval
from .boundary import (
    aggregate_to_dict,
    outcome_to_dict,
    parse_aggregation_input,
    parse_approval,
    parse_proposal,
)
from .loader import Configuration
from .policy_schema import POLICY_APPROVAL
from .results import PolicyOutcome

Evaluator = Callable[[Mapping[str, Any], Configuration], PolicyOutcome]


class UnsupportedPolicyError(ValueError):
    """The policy has no implementation yet. It is never treated as a pass."""


def _evaluate_approval_policy(
    check_input: Mapping[str, Any], configuration: Configuration
) -> PolicyOutcome:
    return evaluate_approval(
        parse_proposal(check_input), parse_approval(check_input), configuration
    )


_EVALUATORS: dict[str, Evaluator] = {POLICY_APPROVAL: _evaluate_approval_policy}

SUPPORTED_POLICIES = frozenset(_EVALUATORS)


def evaluate_policy(
    policy_id: str, check_input: Mapping[str, Any], configuration: Configuration
) -> dict[str, Any]:
    """Evaluate one policy. Raises ``InvalidCheckInput`` when the input cannot be read."""
    evaluator = _EVALUATORS.get(policy_id)
    if evaluator is None:
        raise UnsupportedPolicyError(f"{policy_id} is not implemented yet")
    return outcome_to_dict(evaluator(check_input, configuration))


def aggregate(aggregation_input: Mapping[str, Any]) -> dict[str, Any]:
    """Compute the verdict from per-policy results and the check-level findings."""
    results, findings = parse_aggregation_input(aggregation_input)
    return aggregate_to_dict(aggregate_results(results, findings))


def check(check_input: Mapping[str, Any], configuration: Configuration) -> dict[str, Any]:
    """Evaluate every mandatory policy and aggregate. Refused until all policies exist."""
    missing = sorted(MANDATORY_POLICIES - SUPPORTED_POLICIES)
    raise NotImplementedError(f"no verdict is possible until these exist: {', '.join(missing)}")
