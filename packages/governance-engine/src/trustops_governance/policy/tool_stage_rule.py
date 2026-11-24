"""PROC-TOOL-STAGE-01: a tool may be proposed only in a stage whose allowlist names it.

The policy applies to every proposed tool, so it has no scope check. The allowlists come from the
versioned configuration. Tool and stage names match exactly and are never normalised, so
``Create_Purchase_Order`` is not ``create_purchase_order`` and ``approved`` is not ``APPROVED``.
An uncatalogued tool is simply in no allowlist.

Order of evaluation. The first fault found is the one reported.

1. Configuration: an unusable configuration is ERROR (POLICY_CONFIG_MISSING or _INVALID). The
   loader requires an allowlist for every stage, so a missing allowlist is reported here.
2. Stage: a missing stage or one that is not a canonical stage is ERROR (STAGE_UNKNOWN).
3. Tool: in the allowlist of the stage is PASS (TOOL_ALLOWED_IN_STAGE), otherwise FAIL
   (TOOL_NOT_ALLOWED_IN_STAGE).

Every outcome carries the per-rule policy version (none when the configuration could not be read)
and the values observed: the proposed tool and the stage that was checked.
"""

from .loader import Configuration, load_tool_stage_policy
from .policy_schema import POLICY_TOOL_STAGE, PolicyConfigError, PolicyStage
from .reporting import Reporter, config_reason
from .results import PolicyOutcome, PolicyResult, ReasonCode

_CANONICAL_STAGES = {stage.value: stage for stage in PolicyStage}


def evaluate_tool_stage(
    tool: str, stage: str | None, configuration: Configuration
) -> PolicyOutcome:
    """Evaluate PROC-TOOL-STAGE-01 for one proposed tool. Never raises for a bad configuration."""
    evidence = {"proposed_tool": tool, "checked_policy_stage": stage}
    reporter = Reporter(POLICY_TOOL_STAGE, None, evidence)
    try:
        policy = load_tool_stage_policy(configuration)
    except PolicyConfigError as error:
        return reporter.outcome(PolicyResult.ERROR, config_reason(error))
    reporter = reporter.knowing(policy.version)
    canonical = _canonical_stage(stage)
    if canonical is None:
        return reporter.outcome(PolicyResult.ERROR, ReasonCode.STAGE_UNKNOWN)
    return _judge_tool(tool, policy.stage_allowlist[canonical], reporter)


def _canonical_stage(stage: str | None) -> PolicyStage | None:
    """The stage when it is exactly a canonical stage name, else None."""
    return None if stage is None else _CANONICAL_STAGES.get(stage)


def _judge_tool(tool: str, allowed: frozenset[str], reporter: Reporter) -> PolicyOutcome:
    if tool in allowed:
        return reporter.outcome(PolicyResult.PASS, ReasonCode.TOOL_ALLOWED_IN_STAGE)
    return reporter.outcome(PolicyResult.FAIL, ReasonCode.TOOL_NOT_ALLOWED_IN_STAGE)
