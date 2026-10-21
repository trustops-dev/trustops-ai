"""Canonical failure labels, root-cause candidates, and annotation-record validation."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from trustops_contracts.evaluations import ContractValidationError, EvidenceReferenceV1

PRIMARY_FAILURE_LABELS = (
    "NORMAL",
    "RETRIEVAL_FAILURE",
    "HALLUCINATION",
    "TOOL_SELECTION_ERROR",
    "INVALID_TOOL_ARGUMENTS",
    "WORKFLOW_VIOLATION",
    "POLICY_VIOLATION",
    "PROMPT_INJECTION",
    "UNSUPPORTED_COMPLETION",
)

SECONDARY_FINDING_CODES = (
    "injection_attempt_observed",
    "retrieval_miss_observed",
    "unsupported_claim_observed",
    "missing_citation",
    "tool_selection_mismatch",
    "tool_argument_constraint_failure",
    "workflow_transition_invalid",
    "approval_missing",
    "policy_rule_breach",
    "tool_result_failed_or_missing",
    "trace_evidence_incomplete",
    "semantic_judge_disagreement",
    "citation_claim_mismatch",
    "expected_document_not_retrieved",
)

ROOT_CAUSE_CANDIDATES = (
    "prompt",
    "retriever",
    "retrieved_context",
    "model_generation",
    "tool_selection",
    "tool_arguments",
    "agent_workflow",
    "policy_configuration",
    "malicious_input",
)

FailureLabel = Literal[
    "NORMAL",
    "RETRIEVAL_FAILURE",
    "HALLUCINATION",
    "TOOL_SELECTION_ERROR",
    "INVALID_TOOL_ARGUMENTS",
    "WORKFLOW_VIOLATION",
    "POLICY_VIOLATION",
    "PROMPT_INJECTION",
    "UNSUPPORTED_COMPLETION",
]
RootCauseCandidate = Literal[
    "prompt",
    "retriever",
    "retrieved_context",
    "model_generation",
    "tool_selection",
    "tool_arguments",
    "agent_workflow",
    "policy_configuration",
    "malicious_input",
]
AnnotationStatus = Literal["adjudicated", "pending", "insufficient_evidence", "needs_adjudication"]
LabelSource = Literal["human_adjudication", "controlled_scenario_confirmed"]
NonBlankString = Annotated[str, Field(min_length=1, pattern=r"\S")]


class AnnotationContractError(ContractValidationError):
    """Raised when an annotation record is internally inconsistent."""


class FailureLabelV1(BaseModel):
    """Adjudication record; intended and observed labels remain separately represented."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    contract_version: Literal["1.0.0"]
    trace_id: NonBlankString
    annotation_status: AnnotationStatus
    primary_label: FailureLabel | None
    secondary_findings: list[
        Literal[
            "injection_attempt_observed",
            "retrieval_miss_observed",
            "unsupported_claim_observed",
            "missing_citation",
            "tool_selection_mismatch",
            "tool_argument_constraint_failure",
            "workflow_transition_invalid",
            "approval_missing",
            "policy_rule_breach",
            "tool_result_failed_or_missing",
            "trace_evidence_incomplete",
            "semantic_judge_disagreement",
            "citation_claim_mismatch",
            "expected_document_not_retrieved",
        ]
    ]
    label_source: LabelSource | None = None
    intended_failure_class: FailureLabel | None = None
    injected_root_cause: RootCauseCandidate | None = None
    evidence_refs: list[EvidenceReferenceV1]
    annotation_guideline_version: NonBlankString
    adjudicated_by: NonBlankString | None = None
    adjudication_note: NonBlankString | None = None

    @field_validator("secondary_findings")
    @classmethod
    def secondary_findings_are_unique(cls, findings: list[str]) -> list[str]:
        if len(findings) != len(set(findings)):
            raise ValueError("failure_label.secondary_findings must not contain duplicates")
        return findings

    @model_validator(mode="after")
    def validate_annotation_semantics(self) -> FailureLabelV1:
        if self.annotation_status == "adjudicated":
            if self.primary_label is None:
                raise ValueError("an adjudicated record must have exactly one primary_label")
            if not self.evidence_refs:
                raise ValueError("an adjudicated label must link to concrete trace evidence")
            if self.label_source is None:
                raise ValueError("an adjudicated record must state its ground-truth source")
        elif self.primary_label is not None:
            raise ValueError("unadjudicated records must not be used as final primary labels")

        for reference in self.evidence_refs:
            if reference.trace_id != self.trace_id:
                raise ValueError("evidence_ref.trace_id must match the annotation trace_id")

        if self.label_source == "controlled_scenario_confirmed":
            if self.intended_failure_class is None:
                raise ValueError("scenario-confirmed labels must preserve intended_failure_class")
            if self.primary_label != self.intended_failure_class:
                raise ValueError(
                    "a scenario whose observed outcome differs from its intended label "
                    "requires human adjudication"
                )
        return self


def validate_failure_label(payload: object) -> FailureLabelV1:
    """Validate a human/scenario-grounded label record, never an evaluator prediction."""
    try:
        return FailureLabelV1.model_validate(payload)
    except ValidationError as exc:
        for error in exc.errors():
            if error.get("loc") == ("label_source",):
                raise AnnotationContractError(
                    "failure_label.label_source must be independent of evaluator predictions "
                    "and use an approved source"
                ) from exc
        raise AnnotationContractError(str(exc)) from exc
