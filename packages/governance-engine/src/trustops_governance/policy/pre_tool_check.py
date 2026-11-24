"""The pre-tool check: every mandatory policy is evaluated, then the results are aggregated.

All three policies are evaluated and recorded for every proposal, even after the first failure
(truth tables, section 5). The verdict is ``ALLOW`` only when each of them passed or did not apply
and the check itself has no problem.

The active rule bundle is the policy set's id and version. If that cannot be read, the check
fails closed on the version path (AG-05): it never allows without knowing which bundle ran.
"""

from dataclasses import dataclass, replace

from .aggregation import CheckFindings, aggregate_results
from .approval_rule import evaluate_approval
from .evidence import ApprovalEvidence, PurchaseProposal, SupplierEvidence
from .loader import Configuration, load_policy_set_info
from .policy_schema import PolicyConfigError
from .results import CheckOutcome, PolicyOutcome
from .supplier_rule import evaluate_supplier
from .tool_stage_rule import evaluate_tool_stage

CHECK_MODE = "ONLINE_PRE_TOOL"


@dataclass(frozen=True)
class CheckInput:
    """One proposal with the evidence resolved for it and the findings about the check itself."""

    proposal: PurchaseProposal
    stage: str | None
    approval: ApprovalEvidence | None
    supplier: SupplierEvidence | None
    findings: CheckFindings


def run_check(check_input: CheckInput, configuration: Configuration) -> CheckOutcome:
    """Evaluate the three mandatory policies for one proposal and aggregate the verdict."""
    outcomes = _evaluate_all(check_input, configuration)
    bundle_version = _bundle_version(configuration)
    findings = _with_version_known(check_input.findings, bundle_version)
    results = {outcome.policy_id: outcome.result for outcome in outcomes}
    return CheckOutcome(
        outcomes=outcomes,
        aggregate=aggregate_results(results, findings),
        policy_bundle_version=bundle_version,
        check_mode=CHECK_MODE,
    )


def _evaluate_all(
    check_input: CheckInput, configuration: Configuration
) -> tuple[PolicyOutcome, ...]:
    """The approval, tool-stage and supplier results, always in this order."""
    proposal = check_input.proposal
    return (
        evaluate_approval(proposal, check_input.approval, configuration),
        evaluate_tool_stage(proposal.tool, check_input.stage, configuration),
        evaluate_supplier(proposal, check_input.supplier, configuration),
    )


def _bundle_version(configuration: Configuration) -> str | None:
    """The active rule bundle, or None when the policy set cannot be read."""
    try:
        return load_policy_set_info(configuration).bundle_version
    except PolicyConfigError:
        return None


def _with_version_known(findings: CheckFindings, bundle_version: str | None) -> CheckFindings:
    if bundle_version is not None:
        return findings
    return replace(findings, policy_set_version_matches=False)
