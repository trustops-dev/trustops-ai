"""Aggregation of per-policy results into the pre-tool verdict (truth tables, section 5).

The verdict is ``ALLOW`` only when every mandatory policy was evaluated and none failed, none
could not decide, and no check-level problem was raised. Anything else is ``BLOCK``.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from .policy_schema import POLICY_APPROVAL, POLICY_SUPPLIER, POLICY_TOOL_STAGE
from .results import AggregateOutcome, PolicyResult, Verdict, VerdictBasis

MANDATORY_POLICIES = frozenset({POLICY_APPROVAL, POLICY_TOOL_STAGE, POLICY_SUPPLIER})


@dataclass(frozen=True)
class CheckFindings:
    """Problems with the check itself, found outside any single policy."""

    policy_set_version_matches: bool
    context_consistent: bool
    request_well_formed: bool
    evidence_consistency_findings: tuple[str, ...]
    evidence_unresolved: bool

    @property
    def has_problem(self) -> bool:
        return not (
            self.policy_set_version_matches
            and self.context_consistent
            and self.request_well_formed
            and not self.evidence_consistency_findings
            and not self.evidence_unresolved
        )


def aggregate_results(
    results: Mapping[str, PolicyResult], findings: CheckFindings
) -> AggregateOutcome:
    """Compute the verdict. A failed policy outranks a policy that could not decide."""
    if PolicyResult.FAIL in results.values():
        return AggregateOutcome(Verdict.BLOCK, VerdictBasis.MANDATORY_POLICY_FAILED)
    if _cannot_allow(results, findings):
        return AggregateOutcome(Verdict.BLOCK, VerdictBasis.FAIL_CLOSED_ON_POLICY_ERROR)
    return AggregateOutcome(Verdict.ALLOW, VerdictBasis.ALL_APPLICABLE_PASSED)


def _cannot_allow(results: Mapping[str, PolicyResult], findings: CheckFindings) -> bool:
    return (
        PolicyResult.ERROR in results.values()
        or not MANDATORY_POLICIES <= results.keys()
        or findings.has_problem
    )
