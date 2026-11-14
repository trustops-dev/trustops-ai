"""Synthetic vertical slice: ordering, trust boundary and mock effect evidence."""

from trustops_procurement_agent.mock_tools import MockTools
from trustops_procurement_agent.trace import RecordingSink
from trustops_procurement_agent.workflow import (
    ApprovalResult,
    CalculationResult,
    PolicyResult,
    PurchaseRequest,
    State,
    SupplierResult,
    Workflow,
)


def fixtures() -> tuple[PurchaseRequest, MockTools]:
    request = PurchaseRequest("req-1", "rev-1", "Desktop", 1, "6000.00", "USD", "sup-1", "u-1")
    pending = ApprovalResult(
        "PENDING", "approval-1", "rev-1", "sup-1", "6000.00", "USD", "manager", "a-v1", 1
    )
    approved = ApprovalResult(
        "APPROVED", "approval-1", "rev-1", "sup-1", "6000.00", "USD", "manager", "a-v2", 2
    )
    tools = MockTools(
        PolicyResult("MATCHED", "APPLICABLE", "rule-1", "policy-v1", "evidence-1"),
        SupplierResult("FOUND", "sup-1", "APPROVED", "supplier-v1"),
        CalculationResult("CALCULATED", "rev-1", True, "manager", "calc-1", "policy-v1"),
        pending, approved,
    )
    return request, tools


def test_valid_approved_mock_path_and_same_key_no_second_effect() -> None:
    request, tools = fixtures()
    sink = RecordingSink()
    first = Workflow(tools, sink).run(request, idempotency_key="runtime-key-1")
    assert (first.state, first.status, first.po_id) == (State.COMPLETION, "SUCCEEDED", "mock-po-1")
    assert tools.dispatch_count == 1
    assert [e.details["to_state"] for e in sink.events if e.kind == "state_transition"] == [
        "POLICY_CHECKED", "SUPPLIER_CHECKED", "APPROVAL_CALCULATED", "APPROVAL_PENDING",
        "APPROVED", "PO_CREATION", "COMPLETION",
    ]
    operations = [e.details["operation"] for e in sink.events if "operation" in e.details]
    assert operations == ["CREATE_APPROVAL_REQUEST", "OBSERVE_APPROVAL"]
    second = Workflow(tools).run(request, idempotency_key="runtime-key-1")
    assert second.status == "SUCCEEDED"
    assert tools.dispatch_count == 1


def test_stale_approval_at_dispatch_claim_stops_mock_purchase() -> None:
    request, tools = fixtures()
    tools.current_approval_version = "a-v3"
    result = Workflow(tools).run(request, idempotency_key="runtime-key-2")
    assert (result.state, result.reason, tools.dispatch_count) == (
        State.APPROVED, "BOUND_EVIDENCE_STALE", 0,
    )


def test_pending_approval_is_not_an_authorization() -> None:
    request, tools = fixtures()
    tools.observation = tools.submission
    result = Workflow(tools).run(request, idempotency_key="runtime-key-3")
    assert (result.status, result.state, tools.dispatch_count) == (
        "WAITING_APPROVAL", State.APPROVAL_PENDING, 0,
    )
