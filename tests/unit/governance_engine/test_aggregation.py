"""Aggregation of policy results into the pre-tool verdict, in every state it can face.

The verdict is ALLOW only when every mandatory policy was evaluated, none failed, none could not
decide and the check itself has no problem. Every other state is BLOCK.
"""

from dataclasses import FrozenInstanceError, replace
from itertools import product

import pytest

from trustops_governance.policy.aggregation import (
    MANDATORY_POLICIES,
    CheckFindings,
    aggregate_results,
)
from trustops_governance.policy.policy_schema import (
    POLICY_APPROVAL,
    POLICY_SUPPLIER,
    POLICY_TOOL_STAGE,
)
from trustops_governance.policy.results import PolicyResult, Verdict, VerdictBasis

PASS = PolicyResult.PASS
FAIL = PolicyResult.FAIL
NOT_APPLICABLE = PolicyResult.NOT_APPLICABLE
ERROR = PolicyResult.ERROR

POLICIES = (POLICY_APPROVAL, POLICY_TOOL_STAGE, POLICY_SUPPLIER)
CLEAN = CheckFindings(
    policy_set_version_matches=True,
    context_consistent=True,
    request_well_formed=True,
    evidence_consistency_findings=(),
    evidence_unresolved=False,
)
PROBLEMS = {
    "version-mismatch": replace(CLEAN, policy_set_version_matches=False),
    "context-mismatch": replace(CLEAN, context_consistent=False),
    "malformed-request": replace(CLEAN, request_well_formed=False),
    "consistency-finding": replace(CLEAN, evidence_consistency_findings=("EC-03",)),
    "unresolved-evidence": replace(CLEAN, evidence_unresolved=True),
}
ALL_RESULT_COMBINATIONS = list(product(PolicyResult, repeat=3))

ALLOW = Verdict.ALLOW
BLOCK = Verdict.BLOCK
ALL_PASSED = VerdictBasis.ALL_APPLICABLE_PASSED
MANDATORY_FAILED = VerdictBasis.MANDATORY_POLICY_FAILED
FAIL_CLOSED = VerdictBasis.FAIL_CLOSED_ON_POLICY_ERROR


def results_of(*values: PolicyResult) -> dict[str, PolicyResult]:
    return dict(zip(POLICIES, values, strict=True))


def expected_for(values: tuple[PolicyResult, ...]) -> tuple[Verdict, VerdictBasis]:
    """The rule of the truth table, written independently of the implementation."""
    if FAIL in values:
        return BLOCK, MANDATORY_FAILED
    if ERROR in values:
        return BLOCK, FAIL_CLOSED
    return ALLOW, ALL_PASSED


# --- the policy results alone ------------------------------------------------------------


@pytest.mark.parametrize("values", ALL_RESULT_COMBINATIONS, ids=lambda v: "-".join(v))
def test_every_combination_of_the_three_results(values: tuple[PolicyResult, ...]) -> None:
    outcome = aggregate_results(results_of(*values), CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == expected_for(values)


@pytest.mark.parametrize("values", [(PASS, PASS, PASS), (NOT_APPLICABLE, PASS, NOT_APPLICABLE)])
def test_pass_and_not_applicable_allow(values: tuple[PolicyResult, ...]) -> None:
    outcome = aggregate_results(results_of(*values), CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (ALLOW, ALL_PASSED)


def test_three_not_applicable_results_allow() -> None:
    outcome = aggregate_results(results_of(NOT_APPLICABLE, NOT_APPLICABLE, NOT_APPLICABLE), CLEAN)
    assert outcome.verdict is ALLOW


def test_a_failure_outranks_a_policy_that_could_not_decide() -> None:
    outcome = aggregate_results(results_of(FAIL, PASS, ERROR), CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, MANDATORY_FAILED)


def test_a_policy_that_could_not_decide_blocks_and_is_never_a_violation() -> None:
    outcome = aggregate_results(results_of(PASS, ERROR, PASS), CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, FAIL_CLOSED)


# --- problems with the check itself ------------------------------------------------------


@pytest.mark.parametrize("findings", PROBLEMS.values(), ids=PROBLEMS.keys())
def test_a_check_level_problem_blocks_even_when_every_policy_passes(
    findings: CheckFindings,
) -> None:
    outcome = aggregate_results(results_of(PASS, PASS, PASS), findings)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, FAIL_CLOSED)


@pytest.mark.parametrize("findings", PROBLEMS.values(), ids=PROBLEMS.keys())
def test_a_failed_policy_outranks_a_check_level_problem(findings: CheckFindings) -> None:
    outcome = aggregate_results(results_of(PASS, PASS, FAIL), findings)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, MANDATORY_FAILED)


def test_a_clean_check_has_no_problem() -> None:
    assert CLEAN.has_problem is False


@pytest.mark.parametrize("findings", PROBLEMS.values(), ids=PROBLEMS.keys())
def test_each_problem_is_a_problem(findings: CheckFindings) -> None:
    assert findings.has_problem is True


# --- allow is the only way through -------------------------------------------------------


@pytest.mark.parametrize("values", ALL_RESULT_COMBINATIONS, ids=lambda v: "-".join(v))
@pytest.mark.parametrize("findings", [CLEAN, *PROBLEMS.values()], ids=["clean", *PROBLEMS.keys()])
def test_allow_only_when_nothing_failed_errored_or_went_wrong(
    values: tuple[PolicyResult, ...], findings: CheckFindings
) -> None:
    outcome = aggregate_results(results_of(*values), findings)
    nothing_wrong = not {FAIL, ERROR} & set(values) and not findings.has_problem
    assert (outcome.verdict is ALLOW) == nothing_wrong


# --- results that are missing or unknown -------------------------------------------------


@pytest.mark.parametrize("missing", POLICIES)
def test_a_missing_mandatory_policy_blocks(missing: str) -> None:
    results = {policy: PASS for policy in POLICIES if policy != missing}
    outcome = aggregate_results(results, CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, FAIL_CLOSED)


def test_no_results_at_all_blocks() -> None:
    outcome = aggregate_results({}, CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, FAIL_CLOSED)


def test_a_policy_that_is_not_mandatory_cannot_stand_in_for_a_missing_one() -> None:
    results = {POLICY_APPROVAL: PASS, POLICY_TOOL_STAGE: PASS, "PROC-OTHER-01": PASS}
    outcome = aggregate_results(results, CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, FAIL_CLOSED)


def test_an_extra_passing_policy_changes_nothing() -> None:
    results = {**results_of(PASS, PASS, PASS), "PROC-OTHER-01": PASS}
    assert aggregate_results(results, CLEAN).verdict is ALLOW


def test_an_extra_failing_policy_still_blocks() -> None:
    results = {**results_of(PASS, PASS, PASS), "PROC-OTHER-01": FAIL}
    outcome = aggregate_results(results, CLEAN)
    assert (outcome.verdict, outcome.verdict_basis) == (BLOCK, MANDATORY_FAILED)


def test_the_three_mandatory_policies_are_the_procurement_policies() -> None:
    assert MANDATORY_POLICIES == frozenset(POLICIES)


# --- safe to share -----------------------------------------------------------------------


def test_the_outcome_and_the_findings_cannot_be_changed() -> None:
    outcome = aggregate_results(results_of(PASS, PASS, PASS), CLEAN)
    with pytest.raises(FrozenInstanceError):
        outcome.__setattr__("verdict", BLOCK)
    with pytest.raises(FrozenInstanceError):
        CLEAN.__setattr__("context_consistent", False)


def test_aggregating_does_not_change_the_results_it_was_given() -> None:
    results = results_of(FAIL, PASS, ERROR)
    before = dict(results)
    aggregate_results(results, CLEAN)
    assert results == before
