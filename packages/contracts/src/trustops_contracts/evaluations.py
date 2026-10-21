"""Versioned Pydantic contracts for evaluator requests, results, and trace evidence.

The evaluator envelope is owned here. ``trace_payload`` intentionally remains an opaque
object until Mohab's Trace Schema v1 is frozen and mapped to this interface.
"""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from trustops_contracts.version import EVALUATOR_CONTRACT_VERSION

NonBlankString = Annotated[str, Field(min_length=1, pattern=r"\S")]
EvaluatorStatus = Literal["pass", "fail", "inconclusive", "error"]
EvidenceTarget = Literal[
    "event_id", "span_id", "document_id", "source_id", "field_path", "claim_id"
]
MetricValue = str | int | float | bool | None


class ContractModel(BaseModel):
    """Strict base for cross-module wire contracts."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


class ContractValidationError(ValueError):
    """Raised when a payload does not comply with a versioned contract."""


class EvidenceReferenceV1(ContractModel):
    """Pointer to observed trace evidence; never an unlinked narrative assertion."""

    trace_id: NonBlankString
    event_id: NonBlankString | None = None
    span_id: NonBlankString | None = None
    document_id: NonBlankString | None = None
    source_id: NonBlankString | None = None
    field_path: NonBlankString | None = None
    claim_id: NonBlankString | None = None

    @model_validator(mode="after")
    def require_concrete_target(self) -> EvidenceReferenceV1:
        if not any(
            getattr(self, name) is not None
            for name in (
                "event_id",
                "span_id",
                "document_id",
                "source_id",
                "field_path",
                "claim_id",
            )
        ):
            raise ValueError(
                "evidence_ref must identify an event, span, document, source, field, or claim"
            )
        return self


class EvaluatorSpecV1(ContractModel):
    evaluator_id: NonBlankString
    evaluator_version: NonBlankString
    configuration_fingerprint: NonBlankString


class EvaluationReferenceDataV1(ContractModel):
    """Reference data for offline metrics only; never runtime model input."""

    mode: Literal["offline_metric_only"]
    reference_version: NonBlankString
    expected_relevant_document_ids: list[NonBlankString] = Field(default_factory=list)
    expected_citation_document_ids: list[NonBlankString] = Field(default_factory=list)
    expected_tool_sequence: list[NonBlankString] = Field(default_factory=list)
    expected_workflow_transitions: list[NonBlankString] = Field(default_factory=list)

    @field_validator("expected_relevant_document_ids", "expected_citation_document_ids")
    @classmethod
    def document_ids_are_unique(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError("expected document ID lists must not contain duplicates")
        return values


class EvaluationRunMetadataV1(ContractModel):
    dataset_version: NonBlankString | None = None
    dataset_fingerprint: NonBlankString | None = None
    split_policy_version: NonBlankString | None = None
    split: Literal["train", "validation", "test", "not_applicable"] | None = None
    split_group_key: NonBlankString | None = None
    scenario_id: NonBlankString | None = None
    scenario_family: NonBlankString | None = None
    code_revision: NonBlankString | None = None
    random_seed: int | None = None
    prompt_version: NonBlankString | None = None
    model_version: NonBlankString | None = None
    retriever_version: NonBlankString | None = None
    policy_version: NonBlankString | None = None


_FORBIDDEN_GROUND_TRUTH_KEYS = frozenset(
    "".join(character for character in key.casefold() if character.isalnum())
    for key in {
        "primary_label",
        "adjudicated_label",
        "adjudication_label",
        "intended_failure_class",
        "intended_label",
        "injected_failure_class",
        "injected_root_cause",
        "attack_present",
        "attack_label",
        "is_benign_control",
        "gold_label",
        "gold_class",
        "ground_truth",
        "ground_truth_label",
        "expected_failure_class",
        "expected_failure_label",
        "expected_label",
        "target_label",
        "target_class",
        "observed_label",
        "truth_label",
        "label_source",
        "failure_label",
        "is_seeded_failure",
        "expected_critical_policy_result",
        "injection_recipe_id",
    }
)


def _reject_ground_truth(value: object, path: str) -> None:
    """Reject nested ground-truth leakage, including case/style aliases and tuples."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = (
                "".join(character for character in key.casefold() if character.isalnum())
                if isinstance(key, str)
                else None
            )
            if normalized_key is not None and normalized_key in _FORBIDDEN_GROUND_TRUTH_KEYS:
                raise ValueError(f"{path}.{key} is ground truth and must not enter evaluator input")
            _reject_ground_truth(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_ground_truth(item, f"{path}[{index}]")


class EvaluationRequestV1(ContractModel):
    contract_version: Literal["1.0.0"]
    request_id: NonBlankString
    trace_id: NonBlankString
    trace_schema_version: NonBlankString
    application_id: NonBlankString
    trace_payload: dict[str, object] = Field(
        description=(
            "Observed trace envelope only. The canonical payload model is owned by the "
            "instrumentation/platform team and must be mapped after schema freeze."
        )
    )
    evaluator: EvaluatorSpecV1
    reference_data: EvaluationReferenceDataV1 | None = None
    run_metadata: EvaluationRunMetadataV1 | None = None

    @model_validator(mode="after")
    def validate_envelope_identity_and_prevent_target_leakage(self) -> EvaluationRequestV1:
        _reject_ground_truth(self.trace_payload, "evaluation_request.trace_payload")
        # Identity/version checks are conditional because the owning trace schema is still a
        # draft. Once schema v1 is frozen, require these fields via a typed trace-envelope model.
        for payload_key, envelope_value in (
            ("trace_id", self.trace_id),
            ("schema_version", self.trace_schema_version),
            ("application_id", self.application_id),
        ):
            payload_value = self.trace_payload.get(payload_key)
            if payload_key in self.trace_payload and payload_value != envelope_value:
                raise ValueError(
                    f"evaluation_request.trace_payload.{payload_key} "
                    "must match the evaluator envelope"
                )
        return self


def _finite_metric_values(metrics: dict[str, MetricValue]) -> dict[str, MetricValue]:
    for key, metric in metrics.items():
        if not key.strip():
            raise ValueError("evaluation_result.metrics keys must be non-empty")
        if metric is not None and type(metric) not in (str, int, float, bool):
            raise ValueError(f"evaluation_result.metrics.{key} has an unsupported value type")
        if isinstance(metric, float) and not isfinite(metric):
            raise ValueError(f"evaluation_result.metrics.{key} must be finite")
    return metrics


class EvaluationFindingV1(ContractModel):
    finding_id: NonBlankString
    code: NonBlankString
    severity: Literal["info", "low", "medium", "high", "critical"]
    message: NonBlankString
    evidence_refs: list[EvidenceReferenceV1] = Field(min_length=1)


class EvaluationExecutionV1(ContractModel):
    input_fingerprint: NonBlankString
    configuration_fingerprint: NonBlankString
    deterministic: bool
    reference_data_used: bool
    run_id: NonBlankString | None = None
    error_code: NonBlankString | None = None


class EvaluationResultV1(ContractModel):
    contract_version: Literal["1.0.0"]
    evaluator_id: NonBlankString
    evaluator_version: NonBlankString
    trace_id: NonBlankString
    status: EvaluatorStatus
    findings: list[EvaluationFindingV1]
    metrics: dict[NonBlankString, MetricValue]
    evidence_refs: list[EvidenceReferenceV1]
    execution: EvaluationExecutionV1

    @field_validator("metrics")
    @classmethod
    def validate_metrics(cls, metrics: dict[str, MetricValue]) -> dict[str, MetricValue]:
        return _finite_metric_values(metrics)

    @model_validator(mode="after")
    def validate_evidence_lineage(self) -> EvaluationResultV1:
        if self.status == "fail" and not self.findings:
            raise ValueError(
                "a failed evaluation must include at least one evidence-backed finding"
            )
        for reference in self.evidence_refs:
            if reference.trace_id != self.trace_id:
                raise ValueError("evidence_ref.trace_id must match the evaluation trace_id")
        for finding in self.findings:
            for reference in finding.evidence_refs:
                if reference.trace_id != self.trace_id:
                    raise ValueError("evidence_ref.trace_id must match the evaluation trace_id")
        return self


def _dump_model(model: BaseModel, *, exclude_unset: bool = True) -> dict[str, object]:
    """Return a wire-friendly copy while omitting absent optional fields."""
    return model.model_dump(mode="json", exclude_unset=exclude_unset)


def validate_evidence_reference(
    payload: object, *, expected_trace_id: str | None = None
) -> EvidenceReferenceV1:
    """Validate a trace pointer and optionally bind it to the evaluation trace."""
    try:
        reference = EvidenceReferenceV1.model_validate(payload)
    except ValidationError as exc:
        raise ContractValidationError(str(exc)) from exc
    if expected_trace_id is not None and reference.trace_id != expected_trace_id:
        raise ContractValidationError("evidence_ref.trace_id must match the evaluation trace_id")
    return reference


def validate_evaluation_request(payload: object) -> EvaluationRequestV1:
    """Validate evaluator request structure and prevent label leakage."""
    if (
        isinstance(payload, dict)
        and "contract_version" in payload
        and payload["contract_version"] != EVALUATOR_CONTRACT_VERSION
    ):
        raise ContractValidationError("evaluation_request.contract_version is not supported")
    try:
        return EvaluationRequestV1.model_validate(payload)
    except ValidationError as exc:
        raise ContractValidationError(str(exc)) from exc


def validate_evaluation_result(
    payload: object, *, expected_trace_id: str | None = None
) -> EvaluationResultV1:
    """Validate evaluator output shape, finite metrics, and evidence lineage."""
    if (
        isinstance(payload, dict)
        and "contract_version" in payload
        and payload["contract_version"] != EVALUATOR_CONTRACT_VERSION
    ):
        raise ContractValidationError("evaluation_result.contract_version is not supported")
    try:
        result = EvaluationResultV1.model_validate(payload)
    except ValidationError as exc:
        raise ContractValidationError(str(exc)) from exc
    if expected_trace_id is not None and result.trace_id != expected_trace_id:
        raise ContractValidationError("evaluation_result.trace_id does not match the request")
    return result
