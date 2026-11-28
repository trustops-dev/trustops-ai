"""Typed, immutable models of the procurement policy configuration.

These objects hold what the governance engine accepted from configuration, after the loader
validated it. They carry no evaluation logic. Thresholds are ``Decimal`` and are never floats.

The stage names and the configuration error codes are draft values. They move to the shared
contracts package once the canonical enums are frozen.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

POLICY_APPROVAL = "PROC-APPROVAL-01"
POLICY_TOOL_STAGE = "PROC-TOOL-STAGE-01"
POLICY_SUPPLIER = "PROC-SUPPLIER-01"


class PolicyStage(StrEnum):
    """Coarse workflow stages that the tool-stage policy gives an allowlist to."""

    PRE_APPROVAL = "PRE_APPROVAL"
    APPROVED = "APPROVED"
    PO_CREATION = "PO_CREATION"
    COMPLETED = "COMPLETED"


class ConfigErrorCode(StrEnum):
    """Why a configuration cannot be used. An unusable configuration never means 'allow'."""

    POLICY_CONFIG_MISSING = "POLICY_CONFIG_MISSING"
    POLICY_CONFIG_INVALID = "POLICY_CONFIG_INVALID"
    POLICY_CONFIG_NOT_ENABLED = "POLICY_CONFIG_NOT_ENABLED"


class PolicyConfigError(Exception):
    """A configuration that must stop progression. Carries a reason code and the config path."""

    def __init__(self, code: ConfigErrorCode, path: str, detail: str) -> None:
        super().__init__(f"{code.value} at {path}: {detail}")
        self.code = code
        self.path = path
        self.detail = detail


@dataclass(frozen=True)
class PolicySetInfo:
    """Identity and acceptance record of one policy set."""

    id: str
    version: str
    runtime_enabled: bool
    accepted_by: str | None
    accepted_at: str | None
    acceptance_evidence: str | None


@dataclass(frozen=True)
class ApprovalRule:
    """The approval threshold for one currency. An amount above it needs approval."""

    currency: str
    threshold: Decimal
    approval_level: str
    fraction_digits: int


@dataclass(frozen=True)
class ApprovalPolicy:
    """PROC-APPROVAL-01 configuration."""

    rules: tuple[ApprovalRule, ...]
    amount_pattern: str


@dataclass(frozen=True)
class ToolStagePolicy:
    """PROC-TOOL-STAGE-01 configuration: one tool allowlist for every stage."""

    stage_allowlist: Mapping[PolicyStage, frozenset[str]]


@dataclass(frozen=True)
class SupplierPolicy:
    """PROC-SUPPLIER-01 configuration: the one status that makes a supplier eligible."""

    eligible_status: str


@dataclass(frozen=True)
class PolicySet:
    """A fully validated procurement policy set."""

    info: PolicySetInfo
    approval: ApprovalPolicy
    tool_stage: ToolStagePolicy
    supplier: SupplierPolicy
