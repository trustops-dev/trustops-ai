"""Shared builders for the governance engine tests. Test values only."""

from decimal import Decimal
from typing import Any

import pytest

from trustops_governance.policy.evidence import (
    ApprovalBinding,
    ApprovalEvidence,
    DecisionOrder,
    PurchaseProposal,
    SupplierEvidence,
)
from trustops_governance.policy.policy_schema import (
    POLICY_APPROVAL,
    POLICY_SUPPLIER,
    POLICY_TOOL_STAGE,
)

THRESHOLD = Decimal("1000.00")
APPROVAL_PATTERN = r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?"
APPROVAL_VERSION = "test-approval-v1"
TOOL_STAGE_VERSION = "test-tool-stage-v1"
SUPPLIER_VERSION = "test-supplier-v1"
BUNDLE_VERSION = "test-policy-set-test"  # the policy set id and version of full_configuration


def approval_block() -> dict[str, Any]:
    """The approval policy: threshold 1000.00 USD, approval level manager."""
    return {
        "version": APPROVAL_VERSION,
        "criticality": "critical",
        "comparator": "GT",
        "currency_rules": [
            {
                "currency": "USD",
                "threshold": str(THRESHOLD),
                "approval_level": "manager",
                "fraction_digits": 2,
            }
        ],
        "amount_input": {"pattern": APPROVAL_PATTERN, "positive_only": True},
        "validity": {"time_expiry": "NONE", "ordering": "RECORD_SEQUENCE"},
    }


def tool_stage_block() -> dict[str, Any]:
    return {
        "version": TOOL_STAGE_VERSION,
        "criticality": "critical",
        "stage_allowlist": {
            "PRE_APPROVAL": [
                "search_policy",
                "get_supplier",
                "request_approval",
                "calculate_approval_level",
            ],
            "APPROVED": ["create_purchase_order"],
            "PO_CREATION": [],
            "COMPLETED": [],
        },
    }


def supplier_block() -> dict[str, Any]:
    return {"version": SUPPLIER_VERSION, "criticality": "critical", "eligible_status": "APPROVED"}


@pytest.fixture
def configuration() -> dict[str, Any]:
    """A usable approval configuration. Used by the tests of the approval policy alone."""
    return {"policies": {POLICY_APPROVAL: approval_block()}}


@pytest.fixture
def tool_stage_configuration() -> dict[str, Any]:
    return {"policies": {POLICY_TOOL_STAGE: tool_stage_block()}}


@pytest.fixture
def supplier_configuration() -> dict[str, Any]:
    return {"policies": {POLICY_SUPPLIER: supplier_block()}}


@pytest.fixture
def full_configuration() -> dict[str, Any]:
    """A usable configuration of all three policies, with the policy set identity."""
    return {
        "policy_set": {"id": "test-policy-set", "version": "test"},
        "policies": {
            POLICY_APPROVAL: approval_block(),
            POLICY_TOOL_STAGE: tool_stage_block(),
            POLICY_SUPPLIER: supplier_block(),
        },
    }


@pytest.fixture
def supplier() -> SupplierEvidence:
    """A found supplier that is approved and is the one that was proposed."""
    return SupplierEvidence(lookup_outcome="FOUND", supplier_id="sup-1", status="APPROVED")


@pytest.fixture
def proposal() -> PurchaseProposal:
    """A purchase order proposal just above the threshold."""
    return PurchaseProposal(
        tool="create_purchase_order",
        request_revision="rev-1",
        supplier_id="sup-1",
        total_amount="1000.01",
        currency="USD",
    )


@pytest.fixture
def approval() -> ApprovalEvidence:
    """A valid approval for the baseline proposal."""
    return ApprovalEvidence(
        status="APPROVED",
        bound=ApprovalBinding(
            request_revision="rev-1",
            supplier_id="sup-1",
            total_amount="1000.01",
            currency="USD",
            approval_level="manager",
        ),
        decision_order=DecisionOrder.BEFORE_PROPOSAL,
        record_agrees=True,
        approver_eligible=True,
    )
