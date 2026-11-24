"""Result vocabulary of a pre-tool policy check.

The values are the draft names of the policy truth tables (governance contract section 4.2).
They move to the shared contracts package once the canonical enums are frozen.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class PolicyResult(StrEnum):
    """What one policy decided. ``ERROR`` means "could not decide": never a pass, never a fail."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class ReasonCode(StrEnum):
    """Why a policy gave its result: the codes of the three mandatory policies, and shared ones."""

    # PROC-APPROVAL-01
    APPROVAL_NOT_REQUIRED = "APPROVAL_NOT_REQUIRED"
    APPROVAL_MISSING = "APPROVAL_MISSING"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    APPROVAL_CANCELLED = "APPROVAL_CANCELLED"
    APPROVAL_STALE_REVISION = "APPROVAL_STALE_REVISION"
    APPROVAL_BINDING_MISMATCH = "APPROVAL_BINDING_MISMATCH"
    APPROVAL_AFTER_PROPOSAL = "APPROVAL_AFTER_PROPOSAL"
    APPROVAL_VALID = "APPROVAL_VALID"
    APPROVAL_EVIDENCE_CONTRADICTION = "APPROVAL_EVIDENCE_CONTRADICTION"
    APPROVAL_ORDER_UNDETERMINED = "APPROVAL_ORDER_UNDETERMINED"
    APPROVER_NOT_ELIGIBLE = "APPROVER_NOT_ELIGIBLE"
    AMOUNT_INVALID = "AMOUNT_INVALID"
    CURRENCY_UNSUPPORTED = "CURRENCY_UNSUPPORTED"
    # PROC-TOOL-STAGE-01
    TOOL_ALLOWED_IN_STAGE = "TOOL_ALLOWED_IN_STAGE"
    TOOL_NOT_ALLOWED_IN_STAGE = "TOOL_NOT_ALLOWED_IN_STAGE"
    STAGE_UNKNOWN = "STAGE_UNKNOWN"
    # PROC-SUPPLIER-01
    SUPPLIER_APPROVED = "SUPPLIER_APPROVED"
    SUPPLIER_NOT_APPROVED = "SUPPLIER_NOT_APPROVED"
    SUPPLIER_STATUS_UNKNOWN = "SUPPLIER_STATUS_UNKNOWN"
    SUPPLIER_NOT_FOUND = "SUPPLIER_NOT_FOUND"
    SUPPLIER_ID_MISMATCH = "SUPPLIER_ID_MISMATCH"
    SUPPLIER_EVIDENCE_MISSING = "SUPPLIER_EVIDENCE_MISSING"
    # Shared
    TOOL_OUT_OF_SCOPE = "TOOL_OUT_OF_SCOPE"
    EVIDENCE_UNRESOLVED = "EVIDENCE_UNRESOLVED"
    POLICY_CONFIG_MISSING = "POLICY_CONFIG_MISSING"
    POLICY_CONFIG_INVALID = "POLICY_CONFIG_INVALID"


class OutcomeBasis(StrEnum):
    """Extra context some results carry."""

    NOT_REQUIRED = "NOT_REQUIRED"


class Verdict(StrEnum):
    """The pre-tool decision about one proposed tool call."""

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class VerdictBasis(StrEnum):
    ALL_APPLICABLE_PASSED = "ALL_APPLICABLE_PASSED"
    MANDATORY_POLICY_FAILED = "MANDATORY_POLICY_FAILED"
    FAIL_CLOSED_ON_POLICY_ERROR = "FAIL_CLOSED_ON_POLICY_ERROR"


Evidence = Mapping[str, str | None]


@dataclass(frozen=True)
class PolicyOutcome:
    """The result of one policy for one proposal.

    ``policy_version`` is the per-rule version from the configuration, or None when the
    configuration could not be read. ``observed_evidence`` lists the values the policy looked at.
    """

    policy_id: str
    result: PolicyResult
    reason_code: ReasonCode
    basis: OutcomeBasis | None = None
    policy_version: str | None = None
    observed_evidence: Evidence = field(default_factory=dict)


@dataclass(frozen=True)
class AggregateOutcome:
    """The verdict computed from the per-policy results."""

    verdict: Verdict
    verdict_basis: VerdictBasis


@dataclass(frozen=True)
class CheckOutcome:
    """The full pre-tool check: every mandatory policy result and the verdict."""

    outcomes: tuple[PolicyOutcome, ...]
    aggregate: AggregateOutcome
    policy_bundle_version: str | None
    check_mode: str
