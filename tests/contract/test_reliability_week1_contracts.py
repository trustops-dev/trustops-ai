"""Contract-level checks for the supplied Week 1 reliability artifacts."""

from __future__ import annotations

import pytest

from trustops_reliability.evaluation.contracts import (
    CANONICAL_TRACE_EVIDENCE_SPECS,
    EvaluatorFailureDetail,
    EvaluatorInputContractV1,
    EvaluatorOutputContractV1,
    EvaluatorResultState,
    MetricValueOutput,
    build_split_group_key,
    validate_evaluator_input_contract,
    validate_evaluator_output_contract,
)
from trustops_reliability.taxonomy.loader import (
    ApplicationScope,
    EvaluatorFamily,
    FailureClass,
    GroundTruthSource,
    MetricDirection,
    RootCauseCandidateId,
    ViolationDisposition,
    load_failure_taxonomy,
)
from trustops_reliability.taxonomy.validation import (
    TaxonomyValidationError,
    TraceFailureAnnotation,
    resolve_primary_and_secondary_labels,
    validate_taxonomy_v1,
    validate_trace_annotation,
)


def _input_contract(
    *,
    features: dict[str, object] | None = None,
    versions: dict[str, str | None] | None = None,
) -> EvaluatorInputContractV1:
    return EvaluatorInputContractV1(
        contract_version="1.0.0",
        trace_id="trace-001",
        evaluation_run_id="eval-001",
        application_id="enterprise-rag",
        application_type=ApplicationScope.RAG,
        trace_schema_version="1.0.0",
        versions=versions
        or {
            "application_version": "1.0.0",
            "prompt_version": "1.0.0",
            "model_version": "model-001",
            "retriever_version": "retriever-001",
        },
        evidence_event_ids=("event-1",),
        feature_payload=features or {"token_count": 10},
    )


def _output_contract(**overrides: object) -> EvaluatorOutputContractV1:
    values: dict[str, object] = {
        "contract_version": "1.0.0",
        "evaluation_run_id": "eval-001",
        "trace_id": "trace-001",
        "evaluator_id": "trace_integrity_evaluator",
        "evaluator_family": EvaluatorFamily.DETERMINISTIC,
        "evaluator_version": "1.0.0",
        "result_state": EvaluatorResultState.PASS,
        "is_fallible_judge": False,
        "can_be_ground_truth": False,
        "metrics": (
            MetricValueOutput(
                "trace_integrity_valid", True, "boolean", MetricDirection.HIGHER_IS_BETTER
            ),
        ),
        "supporting_event_ids": ("event-1",),
        "supporting_evidence_ids": ("E01",),
    }
    values.update(overrides)
    return EvaluatorOutputContractV1(**values)  # type: ignore[arg-type]


def test_taxonomy_v1_validator_accepts_canonical_taxonomy() -> None:
    assert validate_taxonomy_v1().taxonomy_version == "1.0.0"


def test_precedence_resolver_returns_normal_for_no_failure() -> None:
    assert resolve_primary_and_secondary_labels([]) == (FailureClass.NORMAL, ())


def test_precedence_resolver_ignores_normal_when_failure_exists() -> None:
    primary, secondary = resolve_primary_and_secondary_labels(
        [FailureClass.NORMAL, FailureClass.HALLUCINATION]
    )

    assert primary == FailureClass.HALLUCINATION
    assert secondary == ()


def test_precedence_resolver_sorts_by_canonical_taxonomy_rank() -> None:
    primary, secondary = resolve_primary_and_secondary_labels(
        [
            FailureClass.UNSUPPORTED_COMPLETION,
            FailureClass.POLICY_VIOLATION,
            FailureClass.WORKFLOW_VIOLATION,
        ]
    )

    assert primary == FailureClass.WORKFLOW_VIOLATION
    assert secondary == (FailureClass.POLICY_VIOLATION, FailureClass.UNSUPPORTED_COMPLETION)


def test_precedence_resolver_deduplicates_observed_failures() -> None:
    primary, secondary = resolve_primary_and_secondary_labels(
        [FailureClass.RETRIEVAL_FAILURE, FailureClass.HALLUCINATION, FailureClass.HALLUCINATION]
    )

    assert primary == FailureClass.RETRIEVAL_FAILURE
    assert secondary == (FailureClass.HALLUCINATION,)


def test_normal_annotation_must_use_not_applicable_disposition() -> None:
    annotation = TraceFailureAnnotation(
        trace_id="trace-normal",
        application_type=ApplicationScope.RAG,
        primary_label=FailureClass.NORMAL,
        secondary_findings=(),
        violation_disposition=ViolationDisposition.NOT_APPLICABLE,
        ground_truth_source=GroundTruthSource.HUMAN_ADJUDICATED_LABEL,
        root_cause_ground_truth=None,
        evidence_ids=("E01",),
    )

    assert validate_trace_annotation(annotation) == annotation


def test_evaluator_prediction_is_rejected_as_ground_truth_source() -> None:
    annotation = TraceFailureAnnotation(
        trace_id="trace-bad-source",
        application_type=ApplicationScope.RAG,
        primary_label=FailureClass.HALLUCINATION,
        secondary_findings=(),
        violation_disposition=ViolationDisposition.NOT_APPLICABLE,
        ground_truth_source=GroundTruthSource.EVALUATOR_PREDICTION,
        root_cause_ground_truth=RootCauseCandidateId.MODEL_GENERATION,
        evidence_ids=("E01",),
    )

    with pytest.raises(TaxonomyValidationError, match="forbidden as a label authority"):
        validate_trace_annotation(annotation)


def test_normal_annotation_rejects_secondary_findings() -> None:
    annotation = TraceFailureAnnotation(
        trace_id="trace-normal-secondary",
        application_type=ApplicationScope.RAG,
        primary_label=FailureClass.NORMAL,
        secondary_findings=(FailureClass.HALLUCINATION,),
        violation_disposition=ViolationDisposition.NOT_APPLICABLE,
        ground_truth_source=GroundTruthSource.HUMAN_ADJUDICATED_LABEL,
        root_cause_ground_truth=None,
        evidence_ids=("E01",),
    )

    with pytest.raises(TaxonomyValidationError, match="cannot have non-empty secondary_findings"):
        validate_trace_annotation(annotation)


def test_invalid_evidence_id_is_rejected_for_annotation() -> None:
    annotation = TraceFailureAnnotation(
        trace_id="trace-invalid-evidence",
        application_type=ApplicationScope.RAG,
        primary_label=FailureClass.NORMAL,
        secondary_findings=(),
        violation_disposition=ViolationDisposition.NOT_APPLICABLE,
        ground_truth_source=GroundTruthSource.HUMAN_ADJUDICATED_LABEL,
        root_cause_ground_truth=None,
        evidence_ids=("E99",),
    )

    with pytest.raises(TaxonomyValidationError, match="Invalid evidence ID"):
        validate_trace_annotation(annotation)


def test_valid_evaluator_input_contract_passes() -> None:
    contract = _input_contract()

    assert validate_evaluator_input_contract(contract) == contract


@pytest.mark.parametrize(
    "leak_key",
    [
        "injected_failure_class",
        "injected_root_cause",
        "injection_recipe_id",
        "human_adjudicated_label",
    ],
)
def test_evaluator_input_rejects_ground_truth_leakage(leak_key: str) -> None:
    with pytest.raises(ValueError, match="Ground-truth leakage detected"):
        validate_evaluator_input_contract(_input_contract(features={leak_key: "leak"}))


def test_evaluator_input_requires_version_provenance() -> None:
    with pytest.raises(ValueError, match="missing version keys"):
        validate_evaluator_input_contract(
            _input_contract(versions={"application_version": "1.0.0"})
        )


def test_split_group_key_is_deterministic_and_includes_recipe() -> None:
    assert build_split_group_key("procurement", "q-007", "recipe-2") == (
        "procurement::q-007::recipe-2"
    )


def test_split_group_key_defaults_blank_recipe_to_normal() -> None:
    assert build_split_group_key("rag", "query-1", " ") == "rag::query-1::normal"


def test_split_group_key_rejects_empty_required_parts() -> None:
    with pytest.raises(ValueError, match="must be non-empty"):
        build_split_group_key(" ", "query-1", None)


def test_evidence_contracts_cover_expected_ids_without_duplicates() -> None:
    ids = [item.evidence_id for item in CANONICAL_TRACE_EVIDENCE_SPECS]

    assert len(ids) == len(set(ids))
    assert ids[0] == "E01"
    assert ids[-1] == "E27"
    assert set(ids) == {f"E{i:02d}" for i in range(1, 28)}


def test_valid_evaluator_output_contract_passes() -> None:
    output = _output_contract()

    assert validate_evaluator_output_contract(output) == output


def test_evaluator_output_cannot_be_ground_truth() -> None:
    with pytest.raises(ValueError, match="must never set can_be_ground_truth=True"):
        validate_evaluator_output_contract(_output_contract(can_be_ground_truth=True))


def test_evaluator_output_requires_metrics_for_evaluated_state() -> None:
    with pytest.raises(ValueError, match="must include at least one metric"):
        validate_evaluator_output_contract(_output_contract(metrics=()))


def test_evaluator_failed_output_requires_failure_detail() -> None:
    with pytest.raises(ValueError, match="must populate failure_detail"):
        validate_evaluator_output_contract(
            _output_contract(result_state=EvaluatorResultState.EVALUATOR_FAILED, metrics=())
        )


def test_evaluator_failed_output_accepts_failure_detail() -> None:
    detail = EvaluatorFailureDetail(
        error_category="input_invalid",
        error_message="Invalid source evidence",
        evaluator_run_id="eval-run-1",
        occurred_at_utc="2026-10-28T07:00:00Z",
    )
    output = _output_contract(
        result_state=EvaluatorResultState.EVALUATOR_FAILED,
        metrics=(),
        supporting_event_ids=(),
        supporting_evidence_ids=(),
        failure_detail=detail,
    )

    assert validate_evaluator_output_contract(output).failure_detail == detail


def test_output_contract_rejects_evaluator_family_mismatch() -> None:
    with pytest.raises(ValueError, match="family mismatch"):
        validate_evaluator_output_contract(_output_contract(evaluator_family=EvaluatorFamily.RAG))


def test_taxonomy_flags_match_required_single_label_and_leakage_policy() -> None:
    taxonomy = load_failure_taxonomy()

    assert taxonomy.single_primary_label_invariant is True
    assert taxonomy.allow_secondary_findings is True
    assert taxonomy.forbid_evaluator_as_ground_truth is True
