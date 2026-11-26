"""Shared builders for the governance engine tests. Test values only."""

from decimal import Decimal
from typing import Any

import pytest

from trustops_governance.policy.evidence import (
    ApprovalBinding,
    ApprovalEvidence,
    DecisionOrder,
    PurchaseProposal,
)
from trustops_governance.policy.policy_schema import POLICY_APPROVAL

THRESHOLD = Decimal("1000.00")
APPROVAL_PATTERN = r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?"


@pytest.fixture
def configuration() -> dict[str, Any]:
    """A usable approval configuration: threshold 1000.00 USD, approval level manager."""
    return {
        "policies": {
            POLICY_APPROVAL: {
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
        }
    }


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
