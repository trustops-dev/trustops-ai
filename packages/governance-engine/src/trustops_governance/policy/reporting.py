"""Builds policy outcomes that carry the policy version and the values that were observed.

Every policy uses the same reporter, so a result always names the per-rule version it ran under
(or none when the configuration could not be read) and the values the policy looked at.
"""

from dataclasses import dataclass, replace
from typing import Self

from .policy_schema import ConfigErrorCode, PolicyConfigError
from .results import Evidence, OutcomeBasis, PolicyOutcome, PolicyResult, ReasonCode

_CONFIG_REASONS = {
    ConfigErrorCode.POLICY_CONFIG_MISSING: ReasonCode.POLICY_CONFIG_MISSING,
    ConfigErrorCode.POLICY_CONFIG_INVALID: ReasonCode.POLICY_CONFIG_INVALID,
}


@dataclass(frozen=True)
class Reporter:
    """The policy id, the version and the evidence known so far, ready to build an outcome."""

    policy_id: str
    version: str | None
    evidence: Evidence

    def outcome(
        self, result: PolicyResult, reason: ReasonCode, basis: OutcomeBasis | None = None
    ) -> PolicyOutcome:
        return PolicyOutcome(
            self.policy_id, result, reason, basis, self.version, dict(self.evidence)
        )

    def knowing(self, version: str | None = None, **evidence: str | None) -> Self:
        """A reporter that also knows the policy version and more observed values."""
        merged = {**self.evidence, **evidence}
        return replace(self, version=self.version if version is None else version, evidence=merged)


def config_reason(error: PolicyConfigError) -> ReasonCode:
    """The reason code of an unusable configuration. Anything unexpected is invalid."""
    return _CONFIG_REASONS.get(error.code, ReasonCode.POLICY_CONFIG_INVALID)


def text_or_none(value: object) -> str | None:
    """Evidence is recorded as text. A value that is not text is recorded as absent."""
    return value if isinstance(value, str) else None
