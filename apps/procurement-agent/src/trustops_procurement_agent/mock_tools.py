"""Fixed synthetic responses. These fixtures do not grant production authorization."""

from dataclasses import dataclass, field

from .workflow import (
    ApprovalResult,
    Authorization,
    CalculationResult,
    PolicyResult,
    PurchaseOrderResult,
    PurchaseRequest,
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
    dispatch_count: int = 0
    _ledger: dict[str, tuple[PurchaseRequest, PurchaseOrderResult]] = field(default_factory=dict)

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
        return self.observation

    def check_purchase_order(
        self, request: PurchaseRequest, policy: PolicyResult, supplier: SupplierResult,
        calculation: CalculationResult, approval: ApprovalResult | None,
    ) -> Authorization:
        approved = (not calculation.approval_required) or (
            approval is not None and approval.status == "APPROVED"
        )
        return Authorization(
            "ALLOW" if self.allow and approved else "BLOCK", "mock-check-01",
            request.request_revision, supplier.record_version,
            approval.record_version if approval else None,
        )

    def current_versions(self, approval_request_id: str | None) -> tuple[str, str | None]:
        return (
            self.current_supplier_version or self.supplier.record_version,
            (self.current_approval_version or self.observation.record_version)
            if approval_request_id else None,
        )

    def create_purchase_order(
        self, request: PurchaseRequest, authorization: Authorization, idempotency_key: str,
    ) -> PurchaseOrderResult:
        existing = self._ledger.get(idempotency_key)
        if existing is not None:
            old_request, result = existing
            if old_request != request:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return PurchaseOrderResult(
                "ALREADY_EXISTS", result.po_id, result.request_revision,
                result.supplier_id, result.total_amount, result.currency, True,
            )
        self.dispatch_count += 1
        result = PurchaseOrderResult(
            "CREATED", f"mock-po-{self.dispatch_count}", request.request_revision,
            request.supplier_id, request.total_amount, request.currency, True,
        )
        self._ledger[idempotency_key] = (request, result)
        return result
