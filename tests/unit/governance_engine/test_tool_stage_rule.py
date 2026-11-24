"""PROC-TOOL-STAGE-01 in every state it can face.

The policy applies to every proposed tool. A tool passes only when the allowlist of the proposal's
stage names it exactly. The allowlists come from the configuration, never from code.
"""

import copy
from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from trustops_governance.policy.policy_schema import POLICY_TOOL_STAGE, PolicyStage
from trustops_governance.policy.results import PolicyOutcome, PolicyResult, ReasonCode
from trustops_governance.policy.tool_stage_rule import evaluate_tool_stage

TOOL_STAGE_VERSION = "test-tool-stage-v1"  # the version in the conftest configuration

PASS = PolicyResult.PASS
FAIL = PolicyResult.FAIL
ERROR = PolicyResult.ERROR

CATALOGUE = [
    "search_policy",
    "get_supplier",
    "calculate_approval_level",
    "request_approval",
    "create_purchase_order",
]
# The allowlist of each stage, written out independently of the configuration builder.
ALLOWED = {
    "PRE_APPROVAL": {
        "search_policy",
        "get_supplier",
        "calculate_approval_level",
        "request_approval",
    },
    "APPROVED": {"create_purchase_order"},
    "PO_CREATION": set(),
    "COMPLETED": set(),
}


def assert_outcome(outcome: PolicyOutcome, result: PolicyResult, reason: ReasonCode) -> None:
    assert (outcome.result, outcome.reason_code) == (result, reason)
    assert outcome.policy_id == POLICY_TOOL_STAGE


# --- every catalogued tool in every stage -------------------------------------------------


@pytest.mark.parametrize("stage", list(ALLOWED))
@pytest.mark.parametrize("tool", CATALOGUE)
def test_a_catalogued_tool_passes_only_in_a_stage_that_allows_it(
    tool: str, stage: str, tool_stage_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_tool_stage(tool, stage, tool_stage_configuration)
    if tool in ALLOWED[stage]:
        assert_outcome(outcome, PASS, ReasonCode.TOOL_ALLOWED_IN_STAGE)
    else:
        assert_outcome(outcome, FAIL, ReasonCode.TOOL_NOT_ALLOWED_IN_STAGE)


@pytest.mark.parametrize("stage", ["PO_CREATION", "COMPLETED"])
@pytest.mark.parametrize("tool", CATALOGUE)
def test_no_tool_may_be_proposed_after_the_order_is_in_progress(
    tool: str, stage: str, tool_stage_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_tool_stage(tool, stage, tool_stage_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.TOOL_NOT_ALLOWED_IN_STAGE)


# --- names match exactly ------------------------------------------------------------------


@pytest.mark.parametrize(
    "tool",
    [
        "Create_Purchase_Order",
        "CREATE_PURCHASE_ORDER",
        "create_purchase_order ",
        " create_purchase_order",
        "create-purchase-order",
        "delete_supplier",
        "",
        " ",
    ],
)
def test_a_tool_name_that_is_not_exactly_catalogued_fails(
    tool: str, tool_stage_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_tool_stage(tool, "APPROVED", tool_stage_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.TOOL_NOT_ALLOWED_IN_STAGE)


@pytest.mark.parametrize(
    "stage",
    [None, "", " ", "approved", "Approved", " APPROVED", "APPROVED ", "PRE-APPROVAL", "SHIPPED"],
    ids=lambda value: f"stage-{value!r}",
)
def test_a_stage_that_is_not_exactly_canonical_is_an_error_never_a_verdict(
    stage: str | None, tool_stage_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_tool_stage("create_purchase_order", stage, tool_stage_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.STAGE_UNKNOWN)


# --- the allowlists come from the configuration -------------------------------------------


def test_a_tool_added_to_the_configured_allowlist_is_allowed(
    tool_stage_configuration: dict[str, Any],
) -> None:
    allowlist = tool_stage_configuration["policies"][POLICY_TOOL_STAGE]["stage_allowlist"]
    assert_outcome(
        evaluate_tool_stage("get_supplier", "APPROVED", tool_stage_configuration),
        FAIL,
        ReasonCode.TOOL_NOT_ALLOWED_IN_STAGE,
    )
    allowlist["APPROVED"].append("get_supplier")
    assert_outcome(
        evaluate_tool_stage("get_supplier", "APPROVED", tool_stage_configuration),
        PASS,
        ReasonCode.TOOL_ALLOWED_IN_STAGE,
    )


def test_a_tool_removed_from_the_configured_allowlist_is_refused(
    tool_stage_configuration: dict[str, Any],
) -> None:
    allowlist = tool_stage_configuration["policies"][POLICY_TOOL_STAGE]["stage_allowlist"]
    allowlist["PRE_APPROVAL"].remove("search_policy")
    outcome = evaluate_tool_stage("search_policy", "PRE_APPROVAL", tool_stage_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.TOOL_NOT_ALLOWED_IN_STAGE)


# --- the configuration --------------------------------------------------------------------


@pytest.mark.parametrize("configuration", [None, {}, {"policies": {}}, {"policies": []}])
def test_a_missing_or_empty_configuration_is_an_error(configuration: Any) -> None:
    outcome = evaluate_tool_stage("create_purchase_order", "APPROVED", configuration)
    reasons = {ReasonCode.POLICY_CONFIG_MISSING, ReasonCode.POLICY_CONFIG_INVALID}
    assert outcome.result is ERROR
    assert outcome.reason_code in reasons


@pytest.mark.parametrize("stage", [stage.value for stage in PolicyStage])
def test_a_stage_without_an_allowlist_is_a_configuration_error_for_every_stage(
    stage: str, tool_stage_configuration: dict[str, Any]
) -> None:
    del tool_stage_configuration["policies"][POLICY_TOOL_STAGE]["stage_allowlist"][stage]
    for checked in ALLOWED:
        outcome = evaluate_tool_stage("create_purchase_order", checked, tool_stage_configuration)
        assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_MISSING)


def test_an_unknown_stage_in_the_configuration_is_invalid(
    tool_stage_configuration: dict[str, Any],
) -> None:
    allowlist = tool_stage_configuration["policies"][POLICY_TOOL_STAGE]["stage_allowlist"]
    allowlist["SHIPPED"] = ["create_purchase_order"]
    outcome = evaluate_tool_stage("create_purchase_order", "APPROVED", tool_stage_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_INVALID)


def test_a_missing_policy_version_is_invalid(tool_stage_configuration: dict[str, Any]) -> None:
    del tool_stage_configuration["policies"][POLICY_TOOL_STAGE]["version"]
    outcome = evaluate_tool_stage("create_purchase_order", "APPROVED", tool_stage_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_INVALID)
    assert outcome.policy_version is None


def test_the_configuration_is_judged_before_the_stage() -> None:
    outcome = evaluate_tool_stage("create_purchase_order", None, None)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_MISSING)


# --- what the outcome carries -------------------------------------------------------------


def test_the_outcome_carries_the_version_and_the_values_observed(
    tool_stage_configuration: dict[str, Any],
) -> None:
    outcome = evaluate_tool_stage("create_purchase_order", "APPROVED", tool_stage_configuration)
    assert outcome.policy_version == TOOL_STAGE_VERSION
    assert outcome.observed_evidence == {
        "proposed_tool": "create_purchase_order",
        "checked_policy_stage": "APPROVED",
    }


def test_an_unknown_stage_is_recorded_as_given(tool_stage_configuration: dict[str, Any]) -> None:
    outcome = evaluate_tool_stage("search_policy", "approved", tool_stage_configuration)
    assert outcome.observed_evidence["checked_policy_stage"] == "approved"
    assert outcome.policy_version == TOOL_STAGE_VERSION


def test_a_configuration_error_still_records_what_was_observed() -> None:
    outcome = evaluate_tool_stage("search_policy", "PRE_APPROVAL", None)
    assert outcome.policy_version is None
    assert outcome.observed_evidence["proposed_tool"] == "search_policy"


def test_every_outcome_has_its_own_evidence(tool_stage_configuration: dict[str, Any]) -> None:
    first = evaluate_tool_stage("search_policy", "PRE_APPROVAL", tool_stage_configuration)
    second = evaluate_tool_stage("search_policy", "PRE_APPROVAL", tool_stage_configuration)
    assert first.observed_evidence is not second.observed_evidence
    assert first == second


# --- safe to call and to share ------------------------------------------------------------


def test_evaluating_does_not_change_the_configuration(
    tool_stage_configuration: dict[str, Any],
) -> None:
    before = copy.deepcopy(tool_stage_configuration)
    evaluate_tool_stage("create_purchase_order", "APPROVED", tool_stage_configuration)
    assert tool_stage_configuration == before


def test_an_outcome_cannot_be_changed(tool_stage_configuration: dict[str, Any]) -> None:
    outcome = evaluate_tool_stage("create_purchase_order", "APPROVED", tool_stage_configuration)
    with pytest.raises(FrozenInstanceError):
        outcome.__setattr__("result", FAIL)
