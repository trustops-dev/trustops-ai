"""PROC-SUPPLIER-01 in every state it can face.

Only the exact configured status passes. Every other status string fails. Missing evidence is an
error, never a verdict on the supplier. The policy applies to the purchase order only.
"""

import copy
from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

from trustops_governance.policy.evidence import PurchaseProposal, SupplierEvidence
from trustops_governance.policy.policy_schema import POLICY_SUPPLIER
from trustops_governance.policy.results import PolicyOutcome, PolicyResult, ReasonCode
from trustops_governance.policy.supplier_rule import evaluate_supplier

SUPPLIER_VERSION = "test-supplier-v1"  # the version in the conftest configuration

PASS = PolicyResult.PASS
FAIL = PolicyResult.FAIL
ERROR = PolicyResult.ERROR
NOT_APPLICABLE = PolicyResult.NOT_APPLICABLE


def assert_outcome(outcome: PolicyOutcome, result: PolicyResult, reason: ReasonCode) -> None:
    assert (outcome.result, outcome.reason_code) == (result, reason)
    assert outcome.policy_id == POLICY_SUPPLIER


# --- the policy applies to the purchase order only ----------------------------------------


@pytest.mark.parametrize(
    "tool", ["get_supplier", "search_policy", "request_approval", "Create_Purchase_Order", ""]
)
def test_any_other_tool_is_out_of_scope(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any], tool: str
) -> None:
    outcome = evaluate_supplier(replace(proposal, tool=tool), None, supplier_configuration)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)


def test_scope_is_decided_before_the_configuration_and_the_evidence(
    proposal: PurchaseProposal,
) -> None:
    outcome = evaluate_supplier(replace(proposal, tool="get_supplier"), None, None)
    assert_outcome(outcome, NOT_APPLICABLE, ReasonCode.TOOL_OUT_OF_SCOPE)


# --- the supplier status ------------------------------------------------------------------


def test_an_approved_supplier_passes(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(proposal, supplier, supplier_configuration)
    assert_outcome(outcome, PASS, ReasonCode.SUPPLIER_APPROVED)


@pytest.mark.parametrize(
    "status",
    [
        "NOT_APPROVED",
        "UNAPPROVED",
        "SUSPENDED",
        "BLOCKED",
        "approved",
        "Approved",
        "APPROVED ",
        " APPROVED",
        "",
        "unknown",
    ],
)
def test_every_status_other_than_the_exact_one_fails(
    proposal: PurchaseProposal,
    supplier: SupplierEvidence,
    supplier_configuration: dict[str, Any],
    status: str,
) -> None:
    outcome = evaluate_supplier(proposal, replace(supplier, status=status), supplier_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.SUPPLIER_NOT_APPROVED)


def test_the_status_unknown_is_a_failure_of_its_own(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(
        proposal, replace(supplier, status="UNKNOWN"), supplier_configuration
    )
    assert_outcome(outcome, FAIL, ReasonCode.SUPPLIER_STATUS_UNKNOWN)


def test_the_eligible_status_comes_from_the_configuration(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    supplier_configuration["policies"][POLICY_SUPPLIER]["eligible_status"] = "VERIFIED"
    approved = evaluate_supplier(proposal, supplier, supplier_configuration)
    assert_outcome(approved, FAIL, ReasonCode.SUPPLIER_NOT_APPROVED)
    verified = evaluate_supplier(
        proposal, replace(supplier, status="VERIFIED"), supplier_configuration
    )
    assert_outcome(verified, PASS, ReasonCode.SUPPLIER_APPROVED)


# --- the lookup and the evidence ----------------------------------------------------------


def test_no_snapshot_is_missing_evidence_not_a_verdict_on_the_supplier(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(proposal, None, supplier_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)


def test_a_lookup_that_ended_in_error_is_missing_evidence(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    lookup_error = SupplierEvidence(lookup_outcome="ERROR", supplier_id=None, status=None)
    outcome = evaluate_supplier(proposal, lookup_error, supplier_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)


@pytest.mark.parametrize(
    ("supplier_id", "status"), [(None, None), ("sup-1", "APPROVED"), ("sup-9", "NOT_APPROVED")]
)
def test_a_supplier_that_was_not_found_fails_whatever_else_the_snapshot_holds(
    proposal: PurchaseProposal,
    supplier_configuration: dict[str, Any],
    supplier_id: str | None,
    status: str | None,
) -> None:
    not_found = SupplierEvidence("NOT_FOUND", supplier_id, status)
    outcome = evaluate_supplier(proposal, not_found, supplier_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.SUPPLIER_NOT_FOUND)


@pytest.mark.parametrize("lookup", ["found", "Found", "TIMEOUT", "", " FOUND", "OK"])
def test_a_lookup_outcome_that_is_not_recognised_is_unresolved_evidence(
    proposal: PurchaseProposal,
    supplier: SupplierEvidence,
    supplier_configuration: dict[str, Any],
    lookup: str,
) -> None:
    outcome = evaluate_supplier(
        proposal, replace(supplier, lookup_outcome=lookup), supplier_configuration
    )
    assert_outcome(outcome, ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


def test_a_found_supplier_without_a_status_is_missing_evidence(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(proposal, replace(supplier, status=None), supplier_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)


@pytest.mark.parametrize("snapshot_id", ["sup-2", "SUP-1", "sup-1 ", "", None])
def test_a_snapshot_of_another_supplier_fails(
    proposal: PurchaseProposal,
    supplier: SupplierEvidence,
    supplier_configuration: dict[str, Any],
    snapshot_id: str | None,
) -> None:
    other = replace(supplier, supplier_id=snapshot_id)
    outcome = evaluate_supplier(proposal, other, supplier_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.SUPPLIER_ID_MISMATCH)


# --- when several things are wrong, the order is fixed ------------------------------------


def test_not_found_is_reported_before_every_other_fault(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    everything_wrong = SupplierEvidence("NOT_FOUND", "sup-9", None)
    outcome = evaluate_supplier(proposal, everything_wrong, supplier_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.SUPPLIER_NOT_FOUND)


def test_a_missing_status_is_reported_before_a_supplier_mismatch(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    both = SupplierEvidence("FOUND", "sup-9", None)
    outcome = evaluate_supplier(proposal, both, supplier_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.SUPPLIER_EVIDENCE_MISSING)


def test_a_supplier_mismatch_is_reported_before_a_status_that_fails(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    both = SupplierEvidence("FOUND", "sup-9", "NOT_APPROVED")
    outcome = evaluate_supplier(proposal, both, supplier_configuration)
    assert_outcome(outcome, FAIL, ReasonCode.SUPPLIER_ID_MISMATCH)


def test_an_unrecognised_lookup_is_reported_before_the_status(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    both = SupplierEvidence("found", "sup-1", "NOT_APPROVED")
    outcome = evaluate_supplier(proposal, both, supplier_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.EVIDENCE_UNRESOLVED)


# --- the configuration --------------------------------------------------------------------


@pytest.mark.parametrize("configuration", [None, {}, {"policies": {}}])
def test_a_missing_configuration_is_an_error_not_a_pass(
    proposal: PurchaseProposal, supplier: SupplierEvidence, configuration: Any
) -> None:
    outcome = evaluate_supplier(proposal, supplier, configuration)
    assert outcome.result is ERROR
    assert outcome.reason_code is ReasonCode.POLICY_CONFIG_MISSING
    assert outcome.policy_version is None


@pytest.mark.parametrize("field", ["eligible_status", "version"])
def test_an_unusable_field_of_the_configuration_is_invalid(
    proposal: PurchaseProposal,
    supplier: SupplierEvidence,
    supplier_configuration: dict[str, Any],
    field: str,
) -> None:
    supplier_configuration["policies"][POLICY_SUPPLIER][field] = ""
    outcome = evaluate_supplier(proposal, supplier, supplier_configuration)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_INVALID)


def test_the_configuration_is_judged_before_the_evidence(proposal: PurchaseProposal) -> None:
    outcome = evaluate_supplier(proposal, None, None)
    assert_outcome(outcome, ERROR, ReasonCode.POLICY_CONFIG_MISSING)


# --- what the outcome carries -------------------------------------------------------------


def test_the_outcome_carries_the_version_and_the_values_observed(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(proposal, supplier, supplier_configuration)
    assert outcome.policy_version == SUPPLIER_VERSION
    assert outcome.observed_evidence == {
        "proposed_supplier_id": "sup-1",
        "supplier_id": "sup-1",
        "lookup_outcome": "FOUND",
        "supplier_status": "APPROVED",
        "eligible_status": "APPROVED",
    }


def test_a_missing_snapshot_is_recorded_as_absent_values(
    proposal: PurchaseProposal, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(proposal, None, supplier_configuration)
    evidence = outcome.observed_evidence
    assert evidence["proposed_supplier_id"] == "sup-1"
    assert evidence["supplier_id"] is None
    assert evidence["supplier_status"] is None
    assert evidence["eligible_status"] == "APPROVED"


def test_a_configuration_error_records_what_was_observed_and_no_eligible_status(
    proposal: PurchaseProposal, supplier: SupplierEvidence
) -> None:
    outcome = evaluate_supplier(proposal, supplier, None)
    assert outcome.observed_evidence["supplier_status"] == "APPROVED"
    assert outcome.observed_evidence["eligible_status"] is None


# --- safe to call and to share ------------------------------------------------------------


def test_evaluating_does_not_change_its_inputs(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    before = copy.deepcopy(supplier_configuration)
    evaluate_supplier(proposal, supplier, supplier_configuration)
    assert supplier_configuration == before


def test_an_outcome_cannot_be_changed(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    outcome = evaluate_supplier(proposal, supplier, supplier_configuration)
    with pytest.raises(FrozenInstanceError):
        outcome.__setattr__("result", FAIL)


def test_the_same_input_always_gives_the_same_outcome(
    proposal: PurchaseProposal, supplier: SupplierEvidence, supplier_configuration: dict[str, Any]
) -> None:
    first = evaluate_supplier(proposal, supplier, supplier_configuration)
    assert evaluate_supplier(proposal, supplier, copy.deepcopy(supplier_configuration)) == first
