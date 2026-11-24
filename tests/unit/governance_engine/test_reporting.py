"""The reporter that every policy uses to attach its version and evidence to an outcome."""

import pytest

from trustops_governance.policy.policy_schema import (
    ConfigErrorCode,
    PolicyConfigError,
)
from trustops_governance.policy.reporting import Reporter, config_reason, text_or_none
from trustops_governance.policy.results import (
    OutcomeBasis,
    PolicyResult,
    ReasonCode,
)

POLICY = "PROC-TEST-01"


def test_an_outcome_carries_the_policy_the_version_and_the_evidence() -> None:
    reporter = Reporter(POLICY, "v1", {"tool": "search_policy"})
    outcome = reporter.outcome(PolicyResult.PASS, ReasonCode.TOOL_ALLOWED_IN_STAGE)
    assert outcome.policy_id == POLICY
    assert outcome.policy_version == "v1"
    assert outcome.observed_evidence == {"tool": "search_policy"}
    assert outcome.basis is None


def test_an_outcome_can_carry_a_basis() -> None:
    reporter = Reporter(POLICY, None, {})
    outcome = reporter.outcome(
        PolicyResult.NOT_APPLICABLE, ReasonCode.APPROVAL_NOT_REQUIRED, OutcomeBasis.NOT_REQUIRED
    )
    assert outcome.basis is OutcomeBasis.NOT_REQUIRED
    assert outcome.policy_version is None


def test_knowing_adds_the_version_and_more_evidence_without_changing_the_original() -> None:
    first = Reporter(POLICY, None, {"tool": "search_policy"})
    later = first.knowing("v2", threshold="1000.00")
    assert (first.version, dict(first.evidence)) == (None, {"tool": "search_policy"})
    assert later.version == "v2"
    assert dict(later.evidence) == {"tool": "search_policy", "threshold": "1000.00"}


def test_knowing_without_a_version_keeps_the_known_one() -> None:
    assert Reporter(POLICY, "v1", {}).knowing(extra="x").version == "v1"


def test_new_evidence_replaces_older_evidence_of_the_same_name() -> None:
    reporter = Reporter(POLICY, None, {"status": None}).knowing(status="APPROVED")
    assert dict(reporter.evidence) == {"status": "APPROVED"}


def test_every_outcome_gets_its_own_copy_of_the_evidence() -> None:
    reporter = Reporter(POLICY, "v1", {"tool": "search_policy"})
    first = reporter.outcome(PolicyResult.PASS, ReasonCode.TOOL_ALLOWED_IN_STAGE)
    second = reporter.outcome(PolicyResult.PASS, ReasonCode.TOOL_ALLOWED_IN_STAGE)
    assert first.observed_evidence is not second.observed_evidence
    assert first == second


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        (ConfigErrorCode.POLICY_CONFIG_MISSING, ReasonCode.POLICY_CONFIG_MISSING),
        (ConfigErrorCode.POLICY_CONFIG_INVALID, ReasonCode.POLICY_CONFIG_INVALID),
        (ConfigErrorCode.POLICY_CONFIG_NOT_ENABLED, ReasonCode.POLICY_CONFIG_INVALID),
    ],
)
def test_a_configuration_error_maps_to_a_reason_and_anything_unexpected_is_invalid(
    code: ConfigErrorCode, reason: ReasonCode
) -> None:
    assert config_reason(PolicyConfigError(code, "path", "detail")) is reason


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1000.01", "1000.01"), ("", ""), (None, None), (1000.01, None), (5, None), (["x"], None)],
)
def test_evidence_is_recorded_as_text_and_anything_else_as_absent(
    value: object, expected: str | None
) -> None:
    assert text_or_none(value) == expected
