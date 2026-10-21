"""Shared contract tests for evaluator input/output and evidence lineage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator

from trustops_contracts.evaluations import (
    ContractValidationError,
    EvaluationRequestV1,
    EvaluationResultV1,
    validate_evaluation_request,
    validate_evaluation_result,
    validate_evidence_reference,
)
from trustops_contracts.failures import FailureLabelV1, validate_failure_label

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPOSITORY_ROOT / "packages/contracts/schemas"
FIXTURE_DIR = REPOSITORY_ROOT / "tests/fixtures/reliability"


def _valid_request() -> dict[str, object]:
    return {
        "contract_version": "1.0.0",
        "request_id": "eval-request-1",
        "trace_id": "trace-1",
        "trace_schema_version": "1.0.0",
        "application_id": "enterprise-rag",
        # Minimal identity stub only; this is deliberately not a schema-valid trace fixture.
        # Real Procurement/RAG traces must be added after Mohab freezes Trace Schema v1.
        "trace_payload": {
            "trace_id": "trace-1",
            "schema_version": "1.0.0",
            "application_id": "enterprise-rag",
        },
        "evaluator": {
            "evaluator_id": "rag",
            "evaluator_version": "1.0.0",
            "configuration_fingerprint": "sha256:cfg-1",
        },
        "reference_data": {
            "mode": "offline_metric_only",
            "reference_version": "rag-reference-1",
            "expected_relevant_document_ids": ["doc-1"],
        },
        "run_metadata": {
            "dataset_version": "dataset-v1",
            "dataset_fingerprint": "sha256:dataset-1",
            "split_policy_version": "group-split-v1",
            "split": "test",
            "split_group_key": "recipe-17",
            "scenario_id": "opaque-case-17",
            "scenario_family": "rag-grounding",
            "code_revision": "abc123",
            "random_seed": 17,
            "prompt_version": "prompt-v1",
            "model_version": "model-v1",
            "retriever_version": "retriever-v1",
            "policy_version": "policy-v1",
        },
    }


def _valid_result() -> dict[str, object]:
    return {
        "contract_version": "1.0.0",
        "evaluator_id": "rag",
        "evaluator_version": "1.0.0",
        "trace_id": "trace-1",
        "status": "fail",
        "findings": [
            {
                "finding_id": "finding-1",
                "code": "expected_document_not_retrieved",
                "severity": "high",
                "message": "Expected evidence was not found in the retrieved set.",
                "evidence_refs": [{"trace_id": "trace-1", "event_id": "retrieval-1"}],
            }
        ],
        "metrics": {"recall_at_5": 0.0, "mrr": 0.0, "ndcg": None},
        "evidence_refs": [{"trace_id": "trace-1", "document_id": "expected-doc-1"}],
        "execution": {
            "input_fingerprint": "sha256:input-1",
            "configuration_fingerprint": "sha256:cfg-1",
            "deterministic": True,
            "reference_data_used": True,
            "run_id": "run-1",
        },
    }


def test_valid_request_and_result_envelopes_validate() -> None:
    assert validate_evaluation_request(_valid_request()).contract_version == "1.0.0"
    result = validate_evaluation_result(_valid_result(), expected_trace_id="trace-1")
    assert result.status == "fail"


def test_request_rejects_embedded_primary_label_at_nested_level() -> None:
    payload = _valid_request()
    trace = cast(dict[str, object], payload["trace_payload"])
    trace["scenario_metadata"] = {"injected_failure_class": "NORMAL"}
    with pytest.raises(ContractValidationError, match="ground truth"):
        validate_evaluation_request(payload)


@pytest.mark.parametrize(
    "leak_key",
    [
        "goldLabel",
        "GroundTruth",
        "expected-failure-class",
        "adjudicatedLabel",
        "target_label",
        "failureLabel",
    ],
)
def test_request_rejects_normalized_ground_truth_key_aliases(leak_key: str) -> None:
    payload = _valid_request()
    trace = cast(dict[str, object], payload["trace_payload"])
    trace["scenario_metadata"] = {leak_key: "NORMAL"}
    with pytest.raises(ContractValidationError, match="ground truth"):
        validate_evaluation_request(payload)


def test_request_rejects_ground_truth_nested_in_tuple_values() -> None:
    payload = _valid_request()
    trace = cast(dict[str, object], payload["trace_payload"])
    trace["non_json_python_container"] = ({"goldLabel": "NORMAL"},)
    with pytest.raises(ContractValidationError, match="ground truth"):
        validate_evaluation_request(payload)


def test_request_requires_reference_data_to_be_metric_only() -> None:
    payload = _valid_request()
    reference = cast(dict[str, object], payload["reference_data"])
    reference["mode"] = "online_generation"
    with pytest.raises(ContractValidationError, match="offline_metric_only"):
        validate_evaluation_request(payload)


def test_result_rejects_evidence_from_another_trace() -> None:
    payload = _valid_result()
    references = cast(list[dict[str, object]], payload["evidence_refs"])
    references[0]["trace_id"] = "trace-other"
    with pytest.raises(ContractValidationError, match="match the evaluation trace_id"):
        validate_evaluation_result(payload, expected_trace_id="trace-1")


def test_result_requires_evidence_for_each_failure_finding() -> None:
    payload = _valid_result()
    findings = cast(list[dict[str, object]], payload["findings"])
    findings[0]["evidence_refs"] = []
    with pytest.raises(ContractValidationError, match="at least 1 item"):
        validate_evaluation_result(payload)


def test_evidence_reference_requires_concrete_trace_target() -> None:
    with pytest.raises(ContractValidationError, match="must identify an event"):
        validate_evidence_reference({"trace_id": "trace-1"})


def test_label_contract_schema_json_is_parseable_and_closes_unresolved_labels() -> None:
    schema = json.loads((SCHEMA_DIR / "failure-label-v1.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["contract_version"]["const"] == "1.0.0"
    unresolved_condition = next(
        clause
        for clause in schema["allOf"]
        if clause.get("if", {}).get("properties", {}).get("annotation_status", {}).get("enum")
    )
    assert unresolved_condition["then"]["properties"]["primary_label"] == {"type": "null"}
    scenario_condition = next(
        clause
        for clause in schema["allOf"]
        if clause.get("if", {}).get("properties", {}).get("label_source", {}).get("const")
        == "controlled_scenario_confirmed"
    )
    assert len(scenario_condition["then"]["oneOf"]) == 9


def test_annotation_fixtures_and_three_schemas_load_as_json() -> None:
    cases = json.loads((FIXTURE_DIR / "annotation_cases.json").read_text(encoding="utf-8"))
    assert len(cases) >= 4
    for filename in (
        "evaluator-input-v1.schema.json",
        "evaluator-output-v1.schema.json",
        "failure-label-v1.schema.json",
    ):
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        assert schema["$schema"].endswith("2020-12/schema")
    for case in cases:
        label = validate_failure_label(case["annotation"])
        assert label.trace_id


def test_json_schemas_match_typed_python_contract_field_sets() -> None:
    input_schema = json.loads(
        (SCHEMA_DIR / "evaluator-input-v1.schema.json").read_text(encoding="utf-8")
    )
    output_schema = json.loads(
        (SCHEMA_DIR / "evaluator-output-v1.schema.json").read_text(encoding="utf-8")
    )
    label_schema = json.loads(
        (SCHEMA_DIR / "failure-label-v1.schema.json").read_text(encoding="utf-8")
    )
    assert set(input_schema["properties"]) == set(EvaluationRequestV1.model_fields)
    assert set(output_schema["properties"]) == set(EvaluationResultV1.model_fields)
    assert set(label_schema["properties"]) == set(FailureLabelV1.model_fields)


def test_result_rejects_non_finite_metric_values() -> None:
    payload = _valid_result()
    metrics = cast(dict[str, object], payload["metrics"])
    metrics["unsupported_metric"] = float("nan")
    with pytest.raises(ContractValidationError, match="must be finite"):
        validate_evaluation_result(payload)


def test_request_rejects_unknown_contract_version() -> None:
    payload = _valid_request()
    payload["contract_version"] = "2.0.0"
    with pytest.raises(ContractValidationError, match="not supported"):
        validate_evaluation_request(payload)


def _valid_controlled_label() -> dict[str, object]:
    return {
        "contract_version": "1.0.0",
        "trace_id": "trace-1",
        "annotation_status": "adjudicated",
        "primary_label": "NORMAL",
        "secondary_findings": ["injection_attempt_observed"],
        "label_source": "controlled_scenario_confirmed",
        "intended_failure_class": "NORMAL",
        "evidence_refs": [{"trace_id": "trace-1", "event_id": "evt-1"}],
        "annotation_guideline_version": "1.0.0",
    }


def _schema_validator(filename: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_scenario_intent_mismatch_is_rejected() -> None:
    from trustops_contracts.failures import AnnotationContractError

    payload = _valid_controlled_label()
    payload["intended_failure_class"] = "POLICY_VIOLATION"
    with pytest.raises(AnnotationContractError, match="requires human adjudication"):
        validate_failure_label(payload)
    assert not _schema_validator("failure-label-v1.schema.json").is_valid(payload)


def test_human_adjudication_can_differ_from_intended_scenario_label() -> None:
    payload = _valid_controlled_label()
    payload["label_source"] = "human_adjudication"
    payload["primary_label"] = "NORMAL"
    payload["intended_failure_class"] = "WORKFLOW_VIOLATION"
    assert validate_failure_label(payload).primary_label == "NORMAL"
    assert _schema_validator("failure-label-v1.schema.json").is_valid(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("trace_id", "   "),
        ("annotation_guideline_version", "\t  "),
        ("adjudicated_by", "  \n"),
        ("adjudication_note", " \t "),
    ],
)
def test_whitespace_only_required_or_present_annotation_strings_rejected_by_python_and_schema(
    field: str, value: str
) -> None:
    from trustops_contracts.failures import AnnotationContractError

    payload = _valid_controlled_label()
    payload[field] = value
    with pytest.raises(AnnotationContractError):
        validate_failure_label(payload)
    assert not _schema_validator("failure-label-v1.schema.json").is_valid(payload)


def test_whitespace_label_fields_are_rejected() -> None:
    from trustops_contracts.failures import AnnotationContractError

    validator = _schema_validator("failure-label-v1.schema.json")
    for field in ("primary_label", "intended_failure_class"):
        payload = _valid_controlled_label()
        payload[field] = "   "
        with pytest.raises(AnnotationContractError):
            validate_failure_label(payload)
        assert not validator.is_valid(payload)


def test_whitespace_only_required_evaluator_fields_rejected_by_python_and_schema() -> None:
    payload = _valid_request()
    payload["request_id"] = "  \t"
    with pytest.raises(ContractValidationError):
        validate_evaluation_request(payload)
    assert not _schema_validator("evaluator-input-v1.schema.json").is_valid(payload)


def test_repeated_tool_sequence_is_allowed_but_duplicate_document_ids_are_not() -> None:
    payload = _valid_request()
    reference = cast(dict[str, object], payload["reference_data"])
    reference["expected_tool_sequence"] = ["lookup_supplier", "lookup_supplier"]
    assert validate_evaluation_request(payload).reference_data is not None
    reference["expected_relevant_document_ids"] = ["doc-1", "doc-1"]
    with pytest.raises(ContractValidationError):
        validate_evaluation_request(payload)


def test_evaluator_contract_models_round_trip_to_json_wire_format() -> None:
    request = validate_evaluation_request(_valid_request())
    result = validate_evaluation_result(_valid_result(), expected_trace_id="trace-1")
    label = validate_failure_label(_valid_controlled_label())
    request_wire = request.model_dump(mode="json", exclude_unset=True)
    result_wire = result.model_dump(mode="json", exclude_unset=True)
    label_wire = label.model_dump(mode="json", exclude_unset=True)
    assert request_wire["trace_id"] == "trace-1"
    assert result_wire["evidence_refs"][0]["trace_id"] == "trace-1"
    assert label_wire["intended_failure_class"] == "NORMAL"


def test_evidence_reference_same_trace_is_semantic_not_schema_only() -> None:
    payload = _valid_result()
    cast(list[dict[str, object]], payload["evidence_refs"])[0]["trace_id"] = "trace-other"
    with pytest.raises(ContractValidationError, match="match the evaluation trace_id"):
        validate_evaluation_result(payload)
    # JSON Schema cannot enforce equality with a sibling trace_id property.
    assert _schema_validator("evaluator-output-v1.schema.json").is_valid(payload)


def test_request_rejects_trace_payload_identity_or_schema_version_mismatch() -> None:
    conflicting_values = (
        ("trace_id", "trace-other"),
        ("schema_version", "0.0.0"),
        ("application_id", "procurement-agent"),
    )
    for key, conflicting_value in conflicting_values:
        payload = _valid_request()
        trace = cast(dict[str, object], payload["trace_payload"])
        trace[key] = conflicting_value
        with pytest.raises(ContractValidationError, match="must match the evaluator envelope"):
            validate_evaluation_request(payload)


def test_request_rejects_intended_failure_class_leakage() -> None:
    payload = _valid_request()
    trace = cast(dict[str, object], payload["trace_payload"])
    trace["scenario_metadata"] = {"intended_failure_class": "NORMAL"}
    with pytest.raises(ContractValidationError, match="ground truth"):
        validate_evaluation_request(payload)


def test_evidence_reference_requires_a_non_null_nonblank_target_in_python_and_schema() -> None:
    payload = _valid_result()
    references = cast(list[dict[str, object]], payload["evidence_refs"])
    references[0].pop("document_id")
    references[0]["event_id"] = None
    with pytest.raises(ContractValidationError, match="identify an event"):
        validate_evidence_reference(references[0])
    assert not _schema_validator("evaluator-output-v1.schema.json").is_valid(payload)


def test_adjudicated_annotation_requires_non_null_label_source_in_python_and_schema() -> None:
    from trustops_contracts.failures import AnnotationContractError

    payload = _valid_controlled_label()
    payload["label_source"] = None
    with pytest.raises(AnnotationContractError, match="ground-truth source"):
        validate_failure_label(payload)
    assert not _schema_validator("failure-label-v1.schema.json").is_valid(payload)
