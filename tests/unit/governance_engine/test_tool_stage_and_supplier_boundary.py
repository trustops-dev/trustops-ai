"""The dictionary boundary for the stage, the supplier and the check-level findings.

Unreadable input raises ``InvalidCheckInput`` and never yields a verdict. Values that are readable
but wrong are judged by the policy, not by the boundary.
"""

import json
from typing import Any

import pytest

from trustops_governance.policy import engine
from trustops_governance.policy.boundary import (
    InvalidCheckInput,
    parse_check_findings,
    parse_stage,
    parse_supplier,
)
from trustops_governance.policy.evidence import SupplierEvidence
from trustops_governance.policy.policy_schema import POLICY_SUPPLIER, POLICY_TOOL_STAGE


def check_input(**changes: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "proposal": {
            "tool": "create_purchase_order",
            "request_revision": "rev-1",
            "supplier_id": "sup-1",
            "total_amount": "1000.01",
            "currency": "USD",
        },
        "stage": "APPROVED",
        "supplier": {"lookup_outcome": "FOUND", "supplier_id": "sup-1", "status": "APPROVED"},
    }
    return {**base, **changes}


# --- evaluate_policy for the stage and supplier policies ----------------------------------


def test_the_tool_stage_policy_returns_plain_json_values(
    tool_stage_configuration: dict[str, Any],
) -> None:
    outcome = engine.evaluate_policy(POLICY_TOOL_STAGE, check_input(), tool_stage_configuration)
    assert outcome == {
        "policy_id": POLICY_TOOL_STAGE,
        "policy_version": "test-tool-stage-v1",
        "result": "PASS",
        "reason_code": "TOOL_ALLOWED_IN_STAGE",
        "basis": None,
        "observed_evidence": {
            "proposed_tool": "create_purchase_order",
            "checked_policy_stage": "APPROVED",
        },
    }
    assert json.loads(json.dumps(outcome)) == outcome


def test_the_supplier_policy_returns_plain_json_values(
    supplier_configuration: dict[str, Any],
) -> None:
    outcome = engine.evaluate_policy(POLICY_SUPPLIER, check_input(), supplier_configuration)
    assert outcome == {
        "policy_id": POLICY_SUPPLIER,
        "policy_version": "test-supplier-v1",
        "result": "PASS",
        "reason_code": "SUPPLIER_APPROVED",
        "basis": None,
        "observed_evidence": {
            "proposed_supplier_id": "sup-1",
            "supplier_id": "sup-1",
            "lookup_outcome": "FOUND",
            "supplier_status": "APPROVED",
            "eligible_status": "APPROVED",
        },
    }
    assert json.loads(json.dumps(outcome)) == outcome


def test_a_missing_stage_is_judged_by_the_policy_not_refused_by_the_boundary(
    tool_stage_configuration: dict[str, Any],
) -> None:
    without_stage = {key: value for key, value in check_input().items() if key != "stage"}
    outcome = engine.evaluate_policy(POLICY_TOOL_STAGE, without_stage, tool_stage_configuration)
    assert (outcome["result"], outcome["reason_code"]) == ("ERROR", "STAGE_UNKNOWN")


def test_a_missing_supplier_snapshot_is_judged_by_the_policy(
    supplier_configuration: dict[str, Any],
) -> None:
    outcome = engine.evaluate_policy(
        POLICY_SUPPLIER, check_input(supplier=None), supplier_configuration
    )
    assert (outcome["result"], outcome["reason_code"]) == ("ERROR", "SUPPLIER_EVIDENCE_MISSING")


# --- the stage ----------------------------------------------------------------------------


@pytest.mark.parametrize("stage", ["APPROVED", "approved", "", "anything at all"])
def test_a_stage_is_passed_on_exactly_as_given(stage: str) -> None:
    assert parse_stage({"stage": stage}) == stage


def test_an_absent_or_null_stage_is_none() -> None:
    assert parse_stage({}) is None
    assert parse_stage({"stage": None}) is None


@pytest.mark.parametrize("stage", [5, True, ["APPROVED"], {"stage": "APPROVED"}])
def test_a_stage_that_is_not_text_is_refused(stage: Any) -> None:
    with pytest.raises(InvalidCheckInput):
        parse_stage({"stage": stage})


# --- the supplier -------------------------------------------------------------------------


def test_an_absent_or_null_supplier_is_none() -> None:
    assert parse_supplier({}) is None
    assert parse_supplier({"supplier": None}) is None


def test_a_supplier_snapshot_is_read_as_given() -> None:
    parsed = parse_supplier(check_input())
    assert parsed == SupplierEvidence("FOUND", "sup-1", "APPROVED")


def test_a_snapshot_may_leave_the_id_and_the_status_null() -> None:
    parsed = parse_supplier({"supplier": {"lookup_outcome": "ERROR"}})
    assert parsed == SupplierEvidence("ERROR", None, None)


@pytest.mark.parametrize(
    "supplier",
    [
        "APPROVED",
        [],
        {},
        {"status": "APPROVED"},
        {"lookup_outcome": None},
        {"lookup_outcome": 1},
        {"lookup_outcome": "FOUND", "supplier_id": 1},
        {"lookup_outcome": "FOUND", "status": ["APPROVED"]},
    ],
    ids=repr,
)
def test_an_unreadable_supplier_snapshot_is_refused(supplier: Any) -> None:
    with pytest.raises(InvalidCheckInput):
        parse_supplier({"supplier": supplier})


# --- the check-level findings -------------------------------------------------------------


def test_findings_default_to_none_raised() -> None:
    findings = parse_check_findings({})
    assert findings.has_problem is False
    assert findings.evidence_consistency_findings == ()


def test_findings_are_read_as_given() -> None:
    findings = parse_check_findings(
        {"policy_set_version_matches": False, "evidence_consistency_findings": ["EC-03", "EC-08"]}
    )
    assert findings.policy_set_version_matches is False
    assert findings.evidence_consistency_findings == ("EC-03", "EC-08")
    assert findings.has_problem is True


@pytest.mark.parametrize(
    "key",
    [
        "policy_set_version_matches",
        "context_consistent",
        "request_well_formed",
        "evidence_unresolved",
    ],
)
@pytest.mark.parametrize("value", ["true", 1, 0, None, [True]], ids=repr)
def test_a_finding_flag_must_be_a_real_boolean(key: str, value: Any) -> None:
    with pytest.raises(InvalidCheckInput):
        parse_check_findings({key: value})


@pytest.mark.parametrize("value", ["EC-03", [3], ["EC-03", None], {"EC-03": True}], ids=repr)
def test_the_finding_list_must_be_a_list_of_text(value: Any) -> None:
    with pytest.raises(InvalidCheckInput):
        parse_check_findings({"evidence_consistency_findings": value})
