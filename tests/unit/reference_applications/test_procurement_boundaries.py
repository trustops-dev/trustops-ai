"""Offline approval and effect boundaries using injected trusted mock records."""

from dataclasses import replace
from typing import Any, cast
from unittest.mock import Mock

import pytest

from trustops_procurement_agent.trace import RecordingSink
from trustops_procurement_agent.workflow import RecoveryResult, State, Workflow

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
            "SUPPLIER_RECORD_SUPERSEDED" if stale_supplier else "POLICY_CHECK_NOT_ALLOWED"
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
    assert tools.check_count == 1
    assert not any(e.kind == "final_response" for e in sink.events)
    assert not any(e.details.get("to_state") == "COMPLETION" for e in sink.events)
    po_results = [
        e.details["status"]
        for e in sink.events
        if e.kind == "tool_result" and e.details.get("tool") == "create_purchase_order"
    ]
    assert po_results == ["UNKNOWN_OUTCOME"]


def test_same_key_changed_payload_is_rejected_before_check_or_write() -> None:
    request, tools = fixtures()
    workflow = Workflow(tools)
    assert workflow.run(request, idempotency_key="key-original").status == "SUCCEEDED"
    changed = replace(request, item_description="Changed item")
    result = workflow.run(changed, idempotency_key="key-original")
    assert (result.status, result.reason) == ("BLOCKED", "IDEMPOTENCY_CONFLICT")
    assert tools.dispatch_count == 1
    assert tools.check_count == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_revision", "rev-2"),
        ("supplier_id", "sup-2"),
        ("total_amount", "7000.00"),
        ("currency", "EUR"),
    ],
)
def test_recovery_refuses_changed_bound_request(field: str, value: str) -> None:
    request, tools = fixtures()
    tools.po_outcome = "UNKNOWN_OUTCOME"
    workflow = Workflow(tools)
    assert workflow.run(request, idempotency_key="key-original").status == "RECOVERY_PENDING"
    changed = replace(request, **cast(Any, {field: value}))
    second = workflow.run(changed, idempotency_key="key-original")
    assert (second.status, second.reason) == ("BLOCKED", "IDEMPOTENCY_CONFLICT")
    assert (tools.check_count, tools.dispatch_count) == (1, 1)


def test_same_root_with_different_key_is_not_an_automatic_new_write() -> None:
    request, tools = fixtures()
    tools.po_outcome = "UNKNOWN_OUTCOME"
    workflow = Workflow(tools)
    assert workflow.run(request, idempotency_key="key-original").status == "RECOVERY_PENDING"
    second = workflow.run(request, idempotency_key="key-other")
    assert (second.status, second.reason) == ("BLOCKED", "IDEMPOTENCY_CONFLICT")
    assert (tools.check_count, tools.dispatch_count) == (1, 1)


@pytest.mark.parametrize("mode", ["ERROR", "RAISE_AFTER_DISPATCH"])
def test_post_dispatch_failure_is_unknown_without_success_claim(mode: str) -> None:
    request, tools = fixtures()
    if mode == "ERROR":
        tools.po_outcome = "ERROR"
    else:
        tools.raise_after_dispatch = True
    observed = Mock(wraps=tools)
    sink = RecordingSink()
    workflow = Workflow(observed, sink)
    first = workflow.run(request, idempotency_key="key-unknown")
    assert (first.status, first.state, first.reason) == (
        "RECOVERY_PENDING",
        State.PO_CREATION,
        "UNKNOWN_PO_OUTCOME",
    )
    second = workflow.run(request, idempotency_key="key-unknown")
    assert second == first
    observed.create_purchase_order.assert_called_once()
    observed.check_purchase_order.assert_called_once()
    assert not any(event.kind == "final_response" for event in sink.events)
    assert [event.details["status"] for event in sink.events if event.kind == "recovery_check"] == [
        "STILL_UNRESOLVED"
    ]


@pytest.mark.parametrize(
    ("resolution", "status", "state"),
    [
        ("RESOLVED_COMMITTED", "SUCCEEDED", State.COMPLETION),
        ("RESOLVED_ABORTED", "FAILED", State.PO_CREATION),
    ],
)
def test_authoritative_read_only_recovery_does_not_replay(
    resolution: str, status: str, state: State
) -> None:
    request, tools = fixtures()
    tools.po_outcome = "UNKNOWN_OUTCOME"
    observed = Mock(wraps=tools)
    workflow = Workflow(observed)
    assert workflow.run(request, idempotency_key="key-recover").status == "RECOVERY_PENDING"
    tools.recovery_resolution = resolution  # type: ignore[assignment]
    resolved = workflow.run(request, idempotency_key="key-recover")
    assert (resolved.status, resolved.state) == (status, state)
    observed.create_purchase_order.assert_called_once()
    observed.check_purchase_order.assert_called_once()


def test_policy_kb_and_bundle_are_distinct_but_paired() -> None:
    request, tools = fixtures()
    assert tools.policy.policy_version != tools.calculation.policy_version
    assert Workflow(tools).run(request, idempotency_key="key-paired").status == "SUCCEEDED"
    request, tools = fixtures()
    tools.calculation = replace(tools.calculation, policy_version="unpaired-bundle")
    result = Workflow(tools).run(request, idempotency_key="key-unpaired")
    assert (result.status, result.reason, tools.dispatch_count) == (
        "BLOCKED",
        "POLICY_VERSION_MISMATCH",
        0,
    )


@pytest.mark.parametrize("exception_type", [RuntimeError, ValueError, OSError])
def test_post_dispatch_adapter_errors_are_unknown_and_sanitized(
    exception_type: type[Exception],
) -> None:
    request, tools = fixtures()
    tools.po_outcome = "UNKNOWN_OUTCOME"
    observed = Mock(wraps=tools)
    sensitive = "SYNTHETIC_PRIVATE_PROVIDER_DETAIL"

    def dispatch_then_fail(*args: object, **kwargs: object) -> None:
        tools.create_purchase_order(*cast(Any, args), **cast(Any, kwargs))
        raise exception_type(sensitive)

    observed.create_purchase_order.side_effect = dispatch_then_fail
    sink = RecordingSink()
    workflow = Workflow(observed, sink)
    result = workflow.run(request, idempotency_key="key-adapter-error")
    assert (result.state, result.status) == (State.PO_CREATION, "RECOVERY_PENDING")
    assert workflow.run(request, idempotency_key="key-adapter-error") == result
    observed.create_purchase_order.assert_called_once()
    observed.check_purchase_order.assert_called_once()
    assert sensitive not in repr(sink.events) + repr(result)
    assert not any(event.kind == "final_response" for event in sink.events)


@pytest.mark.parametrize(
    "recovery",
    [RecoveryResult("RESOLVED_ABORTED"), RecoveryResult("RESOLVED_COMMITTED")],
)
def test_incomplete_recovery_evidence_cannot_establish_success_or_no_effect(
    recovery: RecoveryResult,
) -> None:
    request, tools = fixtures()
    observed = Mock(wraps=tools)
    observed.recover_purchase_order.return_value = recovery
    sink = RecordingSink()
    result = Workflow(observed, sink).run(request, idempotency_key="key-incomplete")
    assert (result.state, result.status) == (State.PO_CREATION, "RECOVERY_PENDING")
    observed.create_purchase_order.assert_not_called()
    observed.check_purchase_order.assert_not_called()
    assert not any(event.kind == "final_response" for event in sink.events)


def test_empty_supplier_version_and_wrong_calculation_ref_fail_closed() -> None:
    request, tools = fixtures()
    tools.supplier = replace(tools.supplier, record_version="")
    result = Workflow(tools).run(request, idempotency_key="key-no-version")
    assert result.state == State.POLICY_CHECKED
    assert tools.dispatch_count == 0
    request, tools = fixtures()
    tools.observation = replace(tools.observation, calculation_ref="wrong")
    result = Workflow(tools).run(request, idempotency_key="key-wrong-calc")
    assert (result.reason, tools.dispatch_count) == ("APPROVAL_BINDING_INVALID", 0)
    request, tools = fixtures()
    tools.calculation = replace(tools.calculation, calculation_ref="")
    result = Workflow(tools).run(request, idempotency_key="key-missing-calc")
    assert (result.reason, tools.dispatch_count) == ("CALCULATION_UNRESOLVED", 0)


@pytest.mark.parametrize(
    ("changed_field", "value", "reason"),
    [
        ("current_approval_status", "CANCELLED", "APPROVAL_NO_LONGER_APPROVED"),
        ("current_approval_version", "a-v3", "APPROVAL_RECORD_SUPERSEDED"),
        ("current_decision_record_seq", 3, "APPROVAL_RECORD_SUPERSEDED"),
        ("current_supplier_version", "supplier-v2", "SUPPLIER_RECORD_SUPERSEDED"),
        ("current_request_revision", "rev-2", "REQUEST_REVISION_CHANGED"),
        ("current_policy_bundle_version", "policy-bundle-v2", "POLICY_BUNDLE_CHANGED"),
        ("gate_supplier_version", "supplier-v2", "AUTHORIZATION_BINDING_INVALID"),
        ("gate_approval_version", "a-v3", "AUTHORIZATION_BINDING_INVALID"),
    ],
)
def test_stale_or_mismatched_evidence_suppresses_dispatch(
    changed_field: str, value: str | int, reason: str
) -> None:
    request, tools = fixtures()
    setattr(tools, changed_field, value)
    observed = Mock(wraps=tools)
    result = Workflow(observed).run(request, idempotency_key=f"key-{changed_field}")
    assert (result.status, result.reason, result.state) == ("BLOCKED", reason, State.APPROVED)
    observed.create_purchase_order.assert_not_called()


@pytest.mark.parametrize("terminal_status", ["DENIED", "CANCELLED"])
def test_mock_terminal_approval_cannot_be_reused_as_approved_across_runs(
    terminal_status: str,
) -> None:
    request, tools = fixtures()
    tools.observation = replace(tools.observation, status=terminal_status)
    first = Workflow(tools).run(request, idempotency_key="key-first")
    assert first.reason == "APPROVAL_TERMINAL"
    tools.observation = replace(tools.observation, status="APPROVED", record_version="a-v3")
    second = Workflow(tools).run(request, idempotency_key="key-second")
    assert second.reason == "APPROVAL_TERMINAL"
    assert tools.dispatch_count == 0
