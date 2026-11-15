"""Offline approval and effect boundaries using injected trusted mock records."""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from trustops_procurement_agent.trace import RecordingSink
from trustops_procurement_agent.workflow import State, Workflow

from .test_procurement_scaffold import fixtures


@pytest.mark.parametrize(
    ("approval_status", "expected_status", "reason"),
    [
        ("NOT_FOUND", "BLOCKED", "APPROVAL_BINDING_INVALID"),
        ("PENDING", "WAITING_APPROVAL", "APPROVAL_PENDING"),
        ("DENIED", "BLOCKED", "APPROVAL_TERMINAL"),
        ("CANCELLED", "CANCELLED", "APPROVAL_TERMINAL"),
    ],
)
def test_no_approved_record_never_proposes_or_dispatches_po(
    approval_status: str,
    expected_status: str,
    reason: str,
) -> None:
    request, tools = fixtures()
    tools.observation = replace(tools.observation, status=approval_status)
    observed_tools = Mock(wraps=tools)
    sink = RecordingSink()
    result = Workflow(observed_tools, sink).run(request, idempotency_key="key-approval")
    assert (result.state, result.status, result.reason) == (
        State.APPROVAL_PENDING,
        expected_status,
        reason,
    )
    observed_tools.check_purchase_order.assert_not_called()
    observed_tools.create_purchase_order.assert_not_called()
    assert tools.dispatch_count == 0
    assert not any(e.kind in ("tool_proposal", "final_response") for e in sink.events)


def test_missing_approval_submission_id_stops_before_observation() -> None:
    request, tools = fixtures()
    tools.submission = replace(tools.submission, approval_request_id="")
    observed_tools = Mock(wraps=tools)
    result = Workflow(observed_tools).run(request, idempotency_key="key-missing-id")
    assert result.reason == "APPROVAL_SUBMISSION_UNRESOLVED"
    observed_tools.request_approval.assert_called_once_with(request, None)
    observed_tools.create_purchase_order.assert_not_called()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_revision", "rev-2"),
        ("supplier_id", "sup-2"),
        ("total_amount", "7000.00"),
        ("currency", "EUR"),
    ],
)
def test_changed_request_cannot_reuse_old_approval(field: str, value: str) -> None:
    request, tools = fixtures()
    if field == "request_revision":
        request = replace(request, request_revision=value)
    elif field == "supplier_id":
        request = replace(request, supplier_id=value)
    elif field == "total_amount":
        request = replace(request, total_amount=value)
    else:
        request = replace(request, currency=value)
    # Upstream reads reflect the new request; the final approval is still for rev-1.
    tools.supplier = replace(tools.supplier, supplier_id=request.supplier_id)
    tools.calculation = replace(tools.calculation, request_revision=request.request_revision)
    tools.submission = replace(
        tools.submission,
        request_revision=request.request_revision,
        supplier_id=request.supplier_id,
        total_amount=request.total_amount,
        currency=request.currency,
    )
    observed_tools = Mock(wraps=tools)
    result = Workflow(observed_tools).run(request, idempotency_key="key-changed")
    assert (result.status, result.reason) == ("BLOCKED", "APPROVAL_BINDING_INVALID")
    observed_tools.create_purchase_order.assert_not_called()
    assert tools.dispatch_count == 0


def test_supplier_version_change_and_policy_block_prevent_dispatch() -> None:
    for stale_supplier in (True, False):
        request, tools = fixtures()
        if stale_supplier:
            tools.current_supplier_version = "supplier-v2"
        else:
            tools.allow = False
        result = Workflow(tools).run(request, idempotency_key="key-preflight")
        assert result.status == "BLOCKED"
        assert result.reason == (
            "BOUND_EVIDENCE_STALE" if stale_supplier else "POLICY_CHECK_NOT_ALLOWED"
        )
        assert tools.dispatch_count == 0


def test_non_timeout_unknown_is_retained_without_replay_or_false_completion() -> None:
    request, tools = fixtures()
    tools.po_outcome = "UNKNOWN_OUTCOME"
    sink = RecordingSink()
    workflow = Workflow(tools, sink)
    first = workflow.run(request, idempotency_key="key-uncertain")
    # Even changing the next fixture response cannot overwrite the uncertain record.
    tools.po_outcome = "CREATED"
    second = workflow.run(request, idempotency_key="key-uncertain")
    assert first == second
    assert (first.state, first.status, first.reason, first.po_id) == (
        State.PO_CREATION,
        "RECOVERY_PENDING",
        "UNKNOWN_PO_OUTCOME",
        None,
    )
    assert tools.dispatch_count == 1
    assert not any(e.kind == "final_response" for e in sink.events)
    assert not any(e.details.get("to_state") == "COMPLETION" for e in sink.events)
    po_results = [
        e.details["status"]
        for e in sink.events
        if e.kind == "tool_result" and e.details.get("tool") == "create_purchase_order"
    ]
    assert po_results == ["UNKNOWN_OUTCOME", "UNKNOWN_OUTCOME"]


def test_same_key_changed_payload_is_rejected_at_mock_ledger() -> None:
    request, tools = fixtures()
    workflow = Workflow(tools)
    assert workflow.run(request, idempotency_key="key-original").status == "SUCCEEDED"
    changed = replace(request, item_description="Changed item")
    with pytest.raises(ValueError, match="IDEMPOTENCY_CONFLICT"):
        workflow.run(changed, idempotency_key="key-original")
    assert tools.dispatch_count == 1
