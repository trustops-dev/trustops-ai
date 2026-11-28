"""Typed inputs of a pre-tool check: the proposal and the evidence already resolved from source.

Every value here is what governance read from the record a check references, not a value copied
into the request (truth tables, section 1). The shape is provisional until the input boundary is
agreed with the platform owner.
"""

from dataclasses import dataclass
from enum import StrEnum


class ApprovalStatus(StrEnum):
    """The statuses an approval record can carry, as the trace schema lists them (SA-05)."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CANCELLED = "CANCELLED"
    STALE_REVISION = "STALE_REVISION"
    EXPIRED = "EXPIRED"


class DecisionOrder(StrEnum):
    """Where the approval decision sits in time relative to the proposal."""

    BEFORE_PROPOSAL = "BEFORE_PROPOSAL"
    AFTER_PROPOSAL = "AFTER_PROPOSAL"
    FUTURE_DATED = "FUTURE_DATED"
    UNORDERABLE = "UNORDERABLE"
    CONFLICTING = "CONFLICTING"


@dataclass(frozen=True)
class PurchaseProposal:
    """The proposed tool call. ``total_amount`` stays raw: judging it is the policy's job."""

    tool: str
    request_revision: str
    supplier_id: str
    total_amount: object
    currency: str


@dataclass(frozen=True)
class ApprovalBinding:
    """What an approval was granted for."""

    request_revision: str
    supplier_id: str
    total_amount: str
    currency: str
    approval_level: str


@dataclass(frozen=True)
class ApprovalEvidence:
    """Governance's approval record for the proposal.

    ``status`` stays text so that an unrecognised status can be refused, not mistaken.
    """

    status: str
    bound: ApprovalBinding
    decision_order: DecisionOrder | None
    record_agrees: bool
    approver_eligible: bool
