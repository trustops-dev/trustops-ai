"""Fixed synthetic responses. These fixtures do not grant production authorization."""

from dataclasses import dataclass, field
from typing import Literal

from .workflow import (
    ApprovalResult,
    Authorization,
    CalculationResult,
    CurrentEvidence,
    PolicyResult,
    PurchaseOrderResult,
    PurchaseRequest,
    RecoveryResult,
    SupplierResult,
)


@dataclass
class MockTools:
    policy: PolicyResult
    supplier: SupplierResult
    calculation: CalculationResult
    submission: ApprovalResult
    observation: ApprovalResult
    allow: bool = True
    current_supplier_version: str | None = None
    current_approval_version: str | None = None
    current_approval_status: str | None = None
    current_decision_record_seq: int | None = None
    current_request_revision: str | None = None
    current_policy_bundle_version: str | None = None
    gate_supplier_version: str | None = None
    gate_approval_version: str | None = None
    dispatch_count: int = 0
    po_outcome: Literal["CREATED", "UNKNOWN_OUTCOME", "ERROR"] = "CREATED"
    paired_policy_kb_version: str = "policy-kb-v1"
    paired_policy_bundle_version: str = "policy-bundle-v1"
    recovery_resolution: Literal["STILL_UNRESOLVED", "RESOLVED_COMMITTED", "RESOLVED_ABORTED"] = (
        "STILL_UNRESOLVED"
    )
    raise_after_dispatch: bool = False
    check_count: int = 0
    _ledger: dict[str, tuple[PurchaseRequest, PurchaseOrderResult]] = field(default_factory=dict)
    _root_keys: dict[str, str] = field(default_factory=dict)
    _terminal_approvals: dict[str, ApprovalResult] = field(default_factory=dict)

    def policy_pairing_valid(self, policy_kb_version: str, policy_bundle_version: str) -> bool:
        return (policy_kb_version, policy_bundle_version) == (
            self.paired_policy_kb_version,
            self.paired_policy_bundle_version,
        )

    def recover_purchase_order(
        self, request: PurchaseRequest, idempotency_key: str
    ) -> RecoveryResult | None:
        bound_key = self._root_keys.get(request.request_id)
        if bound_key is not None and bound_key != idempotency_key:
            return RecoveryResult("IDENTITY_CONFLICT")
        existing = self._ledger.get(idempotency_key)
        if existing is None:
            return None
        original_request, result = existing
        if original_request != request:
            return RecoveryResult("IDENTITY_CONFLICT")
        if result.status == "CREATED":
            return RecoveryResult("RESOLVED_COMMITTED", po_id=result.po_id)
        if self.recovery_resolution == "RESOLVED_COMMITTED":
            return RecoveryResult("RESOLVED_COMMITTED", po_id=f"recovered-{idempotency_key}")
        if self.recovery_resolution == "RESOLVED_ABORTED":
            return RecoveryResult(
                "RESOLVED_ABORTED", resolution_basis="EXPLICIT_ABORT_TOMBSTONE_FOUND"
            )
        return RecoveryResult("STILL_UNRESOLVED")

    def search_policy(self, request: PurchaseRequest) -> PolicyResult:
        return self.policy

    def get_supplier(self, request: PurchaseRequest) -> SupplierResult:
        return self.supplier

    def calculate_approval_level(self, request: PurchaseRequest) -> CalculationResult:
        return self.calculation

    def request_approval(
        self, request: PurchaseRequest, approval_request_id: str | None
    ) -> ApprovalResult:
        if approval_request_id is None:
            return self.submission
        if approval_request_id != self.submission.approval_request_id:
            raise ValueError("Unknown approval request: observation cannot submit")
        terminal = self._terminal_approvals.get(approval_request_id)
        if terminal is not None:
            return terminal
        if self.observation.status in ("DENIED", "CANCELLED"):
            self._terminal_approvals[approval_request_id] = self.observation
        return self.observation

    def check_purchase_order(
        self,
        request: PurchaseRequest,
        policy: PolicyResult,
        supplier: SupplierResult,
        calculation: CalculationResult,
        approval: ApprovalResult | None,
    ) -> Authorization:
        self.check_count += 1
        approved = (not calculation.approval_required) or (
            approval is not None and approval.status == "APPROVED"
        )
        return Authorization(
            "ALLOW" if self.allow and approved else "BLOCK",
            "mock-check-01",
            request.request_revision,
            self.gate_supplier_version
            if self.gate_supplier_version is not None
            else supplier.record_version,
            self.gate_approval_version
            if self.gate_approval_version is not None
            else (approval.record_version if approval else None),
            approval.decision_record_seq if approval else None,
            calculation.policy_version,
        )

    def current_evidence(
        self, request: PurchaseRequest, approval_request_id: str | None
    ) -> CurrentEvidence:
        return CurrentEvidence(
            self.current_supplier_version
            if self.current_supplier_version is not None
            else self.supplier.record_version,
            (
                self.current_approval_version
                if self.current_approval_version is not None
                else self.observation.record_version
            )
            if approval_request_id
            else None,
            (
                self.current_approval_status
                if self.current_approval_status is not None
                else self.observation.status
            )
            if approval_request_id
            else None,
            (
                self.current_decision_record_seq
                if self.current_decision_record_seq is not None
                else self.observation.decision_record_seq
            )
            if approval_request_id
            else None,
            self.current_request_revision
            if self.current_request_revision is not None
            else request.request_revision,
            self.current_policy_bundle_version
            if self.current_policy_bundle_version is not None
            else self.calculation.policy_version,
        )

    def create_purchase_order(
        self,
        request: PurchaseRequest,
        authorization: Authorization,
        idempotency_key: str,
    ) -> PurchaseOrderResult:
        if idempotency_key in self._ledger or request.request_id in self._root_keys:
            raise RuntimeError("ERR_WRITE_RETRY_FORBIDDEN")
        self.dispatch_count += 1
        result = PurchaseOrderResult(
            "UNKNOWN_OUTCOME" if self.raise_after_dispatch else self.po_outcome,
            f"mock-po-{self.dispatch_count}" if self.po_outcome == "CREATED" else None,
            request.request_revision,
            request.supplier_id,
            request.total_amount,
            request.currency,
            True,
        )
        self._ledger[idempotency_key] = (request, result)
        self._root_keys[request.request_id] = idempotency_key
        if self.raise_after_dispatch:
            raise RuntimeError("Synthetic failure after dispatch")
        return result
