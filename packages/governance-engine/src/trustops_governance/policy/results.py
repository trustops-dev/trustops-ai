"""Result vocabulary of a pre-tool policy check.

The values are the draft names of the policy truth tables (governance contract section 4.2).
They move to the shared contracts package once the canonical enums are frozen.
"""

from dataclasses import dataclass
from enum import StrEnum


class PolicyResult(StrEnum):
    """What one policy decided. ``ERROR`` means "could not decide": never a pass, never a fail."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class ReasonCode(StrEnum):
    """Why a policy gave its result. Only the codes of the policies implemented so far."""

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


@dataclass(frozen=True)
class PolicyOutcome:
    """The result of one policy for one proposal."""

    policy_id: str
    result: PolicyResult
    reason_code: ReasonCode
    basis: OutcomeBasis | None = None


@dataclass(frozen=True)
class AggregateOutcome:
    """The verdict computed from the per-policy results."""

    verdict: Verdict
    verdict_basis: VerdictBasis
