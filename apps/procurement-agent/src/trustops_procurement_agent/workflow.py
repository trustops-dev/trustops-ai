"""Synchronous, synthetic Procurement vertical slice. No purchasing integration."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Protocol

from .trace import AppEvent, EventSink, NullSink


class State(StrEnum):
    REQUEST_CAPTURED = "REQUEST_CAPTURED"
    POLICY_CHECKED = "POLICY_CHECKED"
    SUPPLIER_CHECKED = "SUPPLIER_CHECKED"
    APPROVAL_CALCULATED = "APPROVAL_CALCULATED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"  # Ready; does not itself assert a human approval.
    PO_CREATION = "PO_CREATION"
    COMPLETION = "COMPLETION"


@dataclass(frozen=True)
class PurchaseRequest:
    request_id: str
    request_revision: str
    item_description: str
    quantity: int
    total_amount: str
    currency: str
    supplier_id: str
    requester_ref: str

    def __post_init__(self) -> None:
        if (
            any(
                not value
                for value in (
                    self.request_id,
                    self.request_revision,
                    self.item_description.strip(),
                    self.currency,
                    self.supplier_id,
                    self.requester_ref,
                )
            )
            or type(self.quantity) is not int
            or self.quantity <= 0
        ):
            raise ValueError("Invalid purchase request")
        if not isinstance(self.total_amount, str):
            raise ValueError("total_amount must be a decimal string")
        try:
            amount = Decimal(self.total_amount)
        except InvalidOperation as exc:
            raise ValueError("Invalid total_amount") from exc
        if not amount.is_finite() or amount <= 0:
            raise ValueError("total_amount must be a positive decimal string")


@dataclass(frozen=True)
class PolicyResult:
    status: str
    applicability: str
    policy_id: str
    policy_version: str
    evidence_ref: str


@dataclass(frozen=True)
class SupplierResult:
    status: str
    supplier_id: str
    eligibility: str
    record_version: str


@dataclass(frozen=True)
class CalculationResult:
    status: str
    request_revision: str
    approval_required: bool | None
    approval_level: str | None
    calculation_ref: str
    policy_version: str


@dataclass(frozen=True)
class ApprovalResult:
    status: str
    approval_request_id: str
    request_revision: str
    supplier_id: str
    total_amount: str
    currency: str
    approval_level: str
    record_version: str
    decision_record_seq: int
    calculation_ref: str = ""


@dataclass(frozen=True)
class Authorization:
    verdict: str
    check_ref: str
    request_revision: str
    supplier_version: str
    approval_version: str | None
    decision_record_seq: int | None
    policy_bundle_version: str


@dataclass(frozen=True)
class CurrentEvidence:
    supplier_version: str
    approval_version: str | None
    approval_status: str | None
    decision_record_seq: int | None
    request_revision: str
    policy_bundle_version: str


@dataclass(frozen=True)
class PurchaseOrderResult:
    status: str
    po_id: str | None
    request_revision: str
    supplier_id: str
    total_amount: str
    currency: str
    mock: bool


@dataclass(frozen=True)
class RecoveryResult:
    """Trusted read-only observation of a previously claimed write."""

    status: str  # STILL_UNRESOLVED, RESOLVED_COMMITTED, RESOLVED_ABORTED, IDENTITY_CONFLICT
    po_id: str | None = None
    resolution_basis: str | None = None


class ProcurementTools(Protocol):
    def recover_purchase_order(
        self, request: PurchaseRequest, idempotency_key: str
    ) -> RecoveryResult | None: ...
    def policy_pairing_valid(self, policy_kb_version: str, policy_bundle_version: str) -> bool: ...
    def search_policy(self, request: PurchaseRequest) -> PolicyResult: ...
    def get_supplier(self, request: PurchaseRequest) -> SupplierResult: ...
    def calculate_approval_level(self, request: PurchaseRequest) -> CalculationResult: ...
    def request_approval(
        self, request: PurchaseRequest, approval_request_id: str | None
    ) -> ApprovalResult: ...
    def check_purchase_order(
        self,
        request: PurchaseRequest,
        policy: PolicyResult,
        supplier: SupplierResult,
        calculation: CalculationResult,
        approval: ApprovalResult | None,
    ) -> Authorization: ...
    def current_evidence(
        self, request: PurchaseRequest, approval_request_id: str | None
    ) -> CurrentEvidence: ...
    def create_purchase_order(
        self,
        request: PurchaseRequest,
        authorization: Authorization,
        idempotency_key: str,
    ) -> PurchaseOrderResult: ...


@dataclass(frozen=True)
class RunResult:
    state: State
    status: str
    reason: str | None = None
    po_id: str | None = None


class Workflow:
    def __init__(self, tools: ProcurementTools, sink: EventSink | None = None):
        self.tools = tools
        self.sink = sink if sink is not None else NullSink()

    def run(self, request: PurchaseRequest, *, idempotency_key: str) -> RunResult:
        if not idempotency_key:
            raise ValueError("Runtime idempotency key required")
        state = State.REQUEST_CAPTURED

        def event(kind: str, **details: str | bool | int | None) -> None:
            self.sink.emit(AppEvent(kind, request.request_id, details))

        def advance(next_state: State) -> None:
            nonlocal state
            event("state_transition", from_state=state.value, to_state=next_state.value)
            state = next_state

        def halt(reason: str, status: str = "BLOCKED") -> RunResult:
            event("halt", state=state.value, reason=reason, status=status)
            return RunResult(state, status, reason)

        # The durable tool boundary owns this lookup. A resumed root must never
        # repeat the policy check or call the creating tool to discover its effect.
        recovery = self.tools.recover_purchase_order(request, idempotency_key)
        if recovery is not None:
            event(
                "recovery_check",
                operation="RECOVERY_LOOKUP",
                status=recovery.status,
                resolution_basis=recovery.resolution_basis,
                po_id=recovery.po_id,
                read_only=True,
            )
            if recovery.status == "IDENTITY_CONFLICT":
                return RunResult(State.REQUEST_CAPTURED, "BLOCKED", "IDEMPOTENCY_CONFLICT")
            if (
                recovery.status == "RESOLVED_ABORTED"
                and recovery.resolution_basis == "EXPLICIT_ABORT_TOMBSTONE_FOUND"
            ):
                return RunResult(State.PO_CREATION, "FAILED", "DEFINITIVE_NO_EFFECT")
            if recovery.status == "RESOLVED_COMMITTED" and recovery.po_id:
                event("final_response", po_id=recovery.po_id, mock=True)
                return RunResult(State.COMPLETION, "SUCCEEDED", po_id=recovery.po_id)
            return RunResult(State.PO_CREATION, "RECOVERY_PENDING", "UNKNOWN_PO_OUTCOME")

        event(
            "request_captured",
            request_revision=request.request_revision,
            supplier_id=request.supplier_id,
            total_amount=request.total_amount,
            currency=request.currency,
        )
        policy = self.tools.search_policy(request)
        event(
            "tool_result",
            tool="search_policy",
            status=policy.status,
            evidence_ref=policy.evidence_ref,
            policy_version=policy.policy_version,
        )
        if policy.status != "MATCHED" or policy.applicability != "APPLICABLE":
            return halt("POLICY_UNAVAILABLE")
        advance(State.POLICY_CHECKED)

        supplier = self.tools.get_supplier(request)
        event(
            "tool_result",
            tool="get_supplier",
            status=supplier.status,
            record_version=supplier.record_version,
        )
        if (
            supplier.status != "FOUND"
            or supplier.eligibility != "APPROVED"
            or supplier.supplier_id != request.supplier_id
            or not supplier.record_version
        ):
            return halt("SUPPLIER_INELIGIBLE")
        advance(State.SUPPLIER_CHECKED)

        calculation = self.tools.calculate_approval_level(request)
        event(
            "tool_result",
            tool="calculate_approval_level",
            status=calculation.status,
            calculation_ref=calculation.calculation_ref,
        )
        if (
            calculation.status != "CALCULATED"
            or calculation.request_revision != request.request_revision
            or not calculation.calculation_ref
            or not calculation.policy_version
            or type(calculation.approval_required) is not bool
            or (calculation.approval_required and not calculation.approval_level)
            or (not calculation.approval_required and calculation.approval_level is not None)
        ):
            return halt("CALCULATION_UNRESOLVED")
        if not self.tools.policy_pairing_valid(policy.policy_version, calculation.policy_version):
            return halt("POLICY_VERSION_MISMATCH")
        advance(State.APPROVAL_CALCULATED)

        approval = None
        if calculation.approval_required:
            submitted = self.tools.request_approval(request, None)
            event(
                "tool_result",
                tool="request_approval",
                operation="CREATE_APPROVAL_REQUEST",
                status=submitted.status,
                approval_request_id=submitted.approval_request_id,
            )
            if (
                submitted.status != "PENDING"
                or not submitted.approval_request_id
                or submitted.request_revision != request.request_revision
            ):
                return halt("APPROVAL_SUBMISSION_UNRESOLVED")
            advance(State.APPROVAL_PENDING)
            approval = self.tools.request_approval(request, submitted.approval_request_id)
            event(
                "tool_result",
                tool="request_approval",
                operation="OBSERVE_APPROVAL",
                status=approval.status,
                approval_request_id=approval.approval_request_id,
                record_version=approval.record_version,
                decision_record_seq=approval.decision_record_seq,
            )
            if approval.status == "PENDING":
                return halt("APPROVAL_PENDING", "WAITING_APPROVAL")
            if approval.status in ("DENIED", "CANCELLED"):
                return halt(
                    "APPROVAL_TERMINAL",
                    "CANCELLED" if approval.status == "CANCELLED" else "BLOCKED",
                )
            if (
                approval.status != "APPROVED"
                or approval.approval_request_id != submitted.approval_request_id
                or approval.request_revision != request.request_revision
                or approval.supplier_id != request.supplier_id
                or approval.total_amount != request.total_amount
                or approval.currency != request.currency
                or approval.approval_level != calculation.approval_level
                or not approval.calculation_ref
                or approval.calculation_ref != calculation.calculation_ref
                or not approval.record_version
                or approval.decision_record_seq <= submitted.decision_record_seq
            ):
                return halt("APPROVAL_BINDING_INVALID")
        advance(State.APPROVED)

        # The mock gate is an injected trusted boundary, never a model-provided verdict.
        event(
            "tool_proposal",
            tool="create_purchase_order",
            request_revision=request.request_revision,
            supplier_id=request.supplier_id,
            total_amount=request.total_amount,
            currency=request.currency,
        )
        authorization = self.tools.check_purchase_order(
            request, policy, supplier, calculation, approval
        )
        event(
            "policy_check",
            check_mode="STUB_CONTRACT_TEST",
            verdict=authorization.verdict,
            check_ref=authorization.check_ref,
            supplier_version=authorization.supplier_version,
            approval_version=authorization.approval_version,
            decision_record_seq=authorization.decision_record_seq,
            policy_bundle_version=authorization.policy_bundle_version,
        )
        approval_version = approval.record_version if approval else None
        if (
            authorization.verdict != "ALLOW"
            or not authorization.check_ref
            or authorization.request_revision != request.request_revision
        ):
            return halt("POLICY_CHECK_NOT_ALLOWED")
        if (
            authorization.supplier_version != supplier.record_version
            or authorization.approval_version != approval_version
            or authorization.decision_record_seq
            != (approval.decision_record_seq if approval else None)
            or authorization.policy_bundle_version != calculation.policy_version
        ):
            return halt("AUTHORIZATION_BINDING_INVALID")
        current = self.tools.current_evidence(
            request, approval.approval_request_id if approval else None
        )
        if current.request_revision != request.request_revision:
            return halt("REQUEST_REVISION_CHANGED")
        if current.policy_bundle_version != calculation.policy_version:
            return halt("POLICY_BUNDLE_CHANGED")
        if current.supplier_version != supplier.record_version:
            return halt("SUPPLIER_RECORD_SUPERSEDED")
        if approval and current.approval_status != "APPROVED":
            return halt("APPROVAL_NO_LONGER_APPROVED")
        if current.approval_version != approval_version or current.decision_record_seq != (
            approval.decision_record_seq if approval else None
        ):
            return halt("APPROVAL_RECORD_SUPERSEDED")
        # Mock boundary only; atomic claim/fencing is owned by platform integration.
        advance(State.PO_CREATION)
        try:
            po = self.tools.create_purchase_order(request, authorization, idempotency_key)
        except Exception:
            # Once dispatch starts, even decoding/adapter errors cannot prove
            # absence of an effect. Do not emit the raw exception message.
            event(
                "tool_result",
                tool="create_purchase_order",
                status="UNKNOWN_OUTCOME",
                side_effect_state="UNKNOWN",
                cause="RUNTIME_EXCEPTION",
                check_ref=authorization.check_ref,
            )
            return halt("UNKNOWN_PO_OUTCOME", "RECOVERY_PENDING")
        confirmed = (
            po.status in ("CREATED", "ALREADY_EXISTS")
            and bool(po.po_id)
            and po.mock
            and po.request_revision == request.request_revision
            and po.supplier_id == request.supplier_id
            and po.total_amount == request.total_amount
            and po.currency == request.currency
        )
        event(
            "tool_result",
            tool="create_purchase_order",
            status=po.status if confirmed else "UNKNOWN_OUTCOME",
            side_effect_state="KNOWN" if confirmed else "UNKNOWN",
            check_ref=authorization.check_ref,
            po_id=po.po_id,
            mock=po.mock,
        )
        if not confirmed:
            return halt("UNKNOWN_PO_OUTCOME", "RECOVERY_PENDING")
        advance(State.COMPLETION)
        event("final_response", po_id=po.po_id, mock=True)
        return RunResult(state, "SUCCEEDED", po_id=po.po_id)
