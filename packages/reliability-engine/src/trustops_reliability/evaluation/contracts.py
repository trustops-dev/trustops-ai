"""Versioned evaluator I/O contracts, trace evidence mappings, and leakage safeguards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from trustops_reliability.taxonomy.loader import (
    ApplicationScope,
    EvaluatorFamily,
    MetricDirection,
    load_failure_taxonomy,
)


class EvaluatorResultState(StrEnum):
    """Canonical result states aligned with the dashboard status vocabulary."""

    PASS = "Pass"
    REVIEW = "Review"
    BLOCK = "Block"
    NOT_EVALUATED = "Not evaluated"
    EVALUATOR_FAILED = "Evaluator failed"
    NOT_APPLICABLE = "Not applicable"


@dataclass(frozen=True, slots=True)
class TraceEvidenceFieldSpec:
    """Mapping between reference-application evidence IDs (E01-E27) and Trace Schema v1."""

    evidence_id: str
    name: str
    schema_v1_location: str
    required_for_apps: tuple[ApplicationScope, ...]
    consumed_by_evaluators: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MetricValueOutput:
    """Single versioned metric measurement produced by an evaluator."""

    metric_name: str
    value: float | int | bool | str | None
    unit: str
    direction: MetricDirection


@dataclass(frozen=True, slots=True)
class EvaluatorFailureDetail:
    """Structured error detail when an evaluator cannot complete (TRD-61)."""

    error_category: str
    error_message: str
    evaluator_run_id: str
    occurred_at_utc: str


@dataclass(frozen=True, slots=True)
class EvaluatorInputContractV1:
    """Versioned input envelope passed to post-run or offline evaluators.

    Strictly excludes ground-truth scenario injection labels to prevent evaluation leakage.
    """

    contract_version: str
    trace_id: str
    evaluation_run_id: str
    application_id: str
    application_type: ApplicationScope
    trace_schema_version: str
    versions: dict[str, str | None]
    evidence_event_ids: tuple[str, ...]
    feature_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class EvaluatorOutputContractV1:
    """Versioned per-trace evaluator output contract (FR-06, TRD-60, TRD-61)."""

    contract_version: str
    evaluation_run_id: str
    trace_id: str
    evaluator_id: str
    evaluator_family: EvaluatorFamily
    evaluator_version: str
    result_state: EvaluatorResultState
    is_fallible_judge: bool
    can_be_ground_truth: bool
    metrics: tuple[MetricValueOutput, ...]
    supporting_event_ids: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    rationale: str | None = None
    failure_detail: EvaluatorFailureDetail | None = None


CANONICAL_TRACE_EVIDENCE_SPECS: tuple[TraceEvidenceFieldSpec, ...] = (
    TraceEvidenceFieldSpec(
        "E01",
        "User request",
        "request.user_query",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        (
            "trace_integrity_evaluator",
            "retrieval_quality_evaluator",
            "semantic_correctness_judge",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E02",
        "Model call",
        "events[event_type=model_call].attributes",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        (
            "trace_integrity_evaluator",
            "groundedness_citation_evaluator",
            "semantic_correctness_judge",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E03",
        "Procurement policy retrieval",
        "events[event_type=retrieval].attributes",
        (ApplicationScope.AGENT,),
        ("retrieval_quality_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E04",
        "RAG retrieval",
        "events[event_type=retrieval].attributes",
        (ApplicationScope.RAG,),
        ("retrieval_quality_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E05",
        "Retrieved documents",
        "events[event_type=retrieval].attributes.retrieved_documents",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        (
            "retrieval_quality_evaluator",
            "groundedness_citation_evaluator",
            "semantic_correctness_judge",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E06",
        "Retrieval scores/ranks",
        "events[event_type=retrieval].attributes.retrieved_documents[].{score,rank}",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("retrieval_quality_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E07",
        "Evidence selection",
        "events[event_type=retrieval].attributes.retrieved_documents[].content_snippet",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("retrieval_quality_evaluator", "groundedness_citation_evaluator"),
    ),
    TraceEvidenceFieldSpec(
        "E08",
        "Request normalization",
        "request.structured_input",
        (ApplicationScope.AGENT,),
        ("tool_argument_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E09",
        "Agent state transition",
        "events[event_type=agent_state].attributes.{from_stage,to_stage,transition_reason}",
        (ApplicationScope.AGENT,),
        ("workflow_trajectory_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E10",
        "Workflow stage",
        "events[event_type=agent_state].attributes.workflow_stage",
        (ApplicationScope.AGENT,),
        ("workflow_trajectory_evaluator", "policy_conformance_evaluator"),
    ),
    TraceEvidenceFieldSpec(
        "E11",
        "Supplier check",
        "events[event_type=tool_result,tool_name=get_supplier].attributes.result_payload",
        (ApplicationScope.AGENT,),
        ("policy_conformance_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E12",
        "Approval calculation",
        (
            "events[event_type=agent_state].attributes."
            "{approval_required,required_approval_level,evaluated_amount,policy_threshold}"
        ),
        (ApplicationScope.AGENT,),
        ("workflow_trajectory_evaluator", "policy_conformance_evaluator"),
    ),
    TraceEvidenceFieldSpec(
        "E13",
        "Approval submission",
        "events[event_type=tool_call,tool_name=request_approval].attributes",
        (ApplicationScope.AGENT,),
        ("workflow_trajectory_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E14",
        "Approval observation",
        "events[event_type=approval].attributes.{approval_id,approval_status}",
        (ApplicationScope.AGENT,),
        ("workflow_trajectory_evaluator", "policy_conformance_evaluator"),
    ),
    TraceEvidenceFieldSpec(
        "E15",
        "Tool proposal",
        (
            "events[event_type=tool_proposal].attributes."
            "{proposal_id,tool_name,workflow_stage_at_proposal}"
        ),
        (ApplicationScope.AGENT,),
        (
            "tool_argument_evaluator",
            "workflow_trajectory_evaluator",
            "policy_conformance_evaluator",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E16",
        "Tool arguments",
        (
            "events[event_type=tool_proposal|tool_call].attributes."
            "{proposed_arguments,arguments,argument_schema_valid}"
        ),
        (ApplicationScope.AGENT,),
        ("tool_argument_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E17",
        "Pre-execution policy request",
        "events[event_type=policy_check].attributes.{check_id,target_proposal_id,check_mode}",
        (ApplicationScope.AGENT,),
        ("policy_conformance_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E18",
        "Pre-execution policy result",
        "events[event_type=policy_check].attributes.{evaluated_policies,pre_tool_verdict}",
        (ApplicationScope.AGENT,),
        (
            "workflow_trajectory_evaluator",
            "policy_conformance_evaluator",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E19",
        "Dispatch suppression",
        "events[event_type=tool_result].attributes.{execution_status,side_effect_committed}",
        (ApplicationScope.AGENT,),
        ("workflow_trajectory_evaluator", "policy_conformance_evaluator"),
    ),
    TraceEvidenceFieldSpec(
        "E20",
        "Tool invocation/result",
        "events[event_type=tool_call|tool_result].attributes",
        (ApplicationScope.AGENT,),
        ("tool_argument_evaluator", "workflow_trajectory_evaluator"),
    ),
    TraceEvidenceFieldSpec(
        "E21",
        "Final response, Procurement",
        "events[event_type=final_response].attributes.{response_text,claimed_actions}",
        (ApplicationScope.AGENT,),
        (
            "trace_integrity_evaluator",
            "groundedness_citation_evaluator",
            "semantic_correctness_judge",
            "workflow_trajectory_evaluator",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E22",
        "Grounded answer, RAG",
        "events[event_type=final_response].attributes.response_text",
        (ApplicationScope.RAG,),
        (
            "trace_integrity_evaluator",
            "groundedness_citation_evaluator",
            "semantic_correctness_judge",
            "prompt_injection_evaluator",
        ),
    ),
    TraceEvidenceFieldSpec(
        "E23",
        "Citations",
        "events[event_type=final_response].attributes.citations",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("groundedness_citation_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E24",
        "Abstention",
        "events[event_type=final_response].attributes.{is_abstention,abstention_reason}",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("groundedness_citation_evaluator", "semantic_correctness_judge"),
    ),
    TraceEvidenceFieldSpec(
        "E25",
        "Technical failure/cancel/pending",
        "execution_status|events[event_type=error].attributes",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("trace_integrity_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E26",
        "Run/version provenance",
        (
            "versions.{application_version,prompt_version,"
            "model_version,retriever_version,policy_kb_version}"
        ),
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("trace_integrity_evaluator",),
    ),
    TraceEvidenceFieldSpec(
        "E27",
        "Controlled scenario association",
        "scenario_metadata.{scenario_id,scenario_family,question_template_id,split_group_key}",
        (ApplicationScope.RAG, ApplicationScope.AGENT),
        ("retrieval_quality_evaluator",),
    ),
)


def validate_evaluator_input_contract(
    contract: EvaluatorInputContractV1,
) -> EvaluatorInputContractV1:
    """Verify that an EvaluatorInputContractV1 carries provenance and no leaked ground truth."""
    taxonomy = load_failure_taxonomy()
    forbidden_keys = set(taxonomy.dataset_leakage_safeguards.forbidden_inference_feature_keys)
    leaked = forbidden_keys.intersection(contract.feature_payload.keys())
    if leaked:
        sorted_leaked = ", ".join(sorted(leaked))
        raise ValueError(
            "Ground-truth leakage detected in EvaluatorInputContractV1 "
            f"feature_payload: {sorted_leaked}"
        )

    required_version_keys = {
        "application_version",
        "prompt_version",
        "model_version",
        "retriever_version",
    }
    missing_versions = required_version_keys - set(contract.versions.keys())
    if missing_versions:
        sorted_missing = ", ".join(sorted(missing_versions))
        raise ValueError(f"EvaluatorInputContractV1 missing version keys: {sorted_missing}")

    if not contract.trace_id or not contract.evaluation_run_id:
        raise ValueError("trace_id and evaluation_run_id must be non-empty.")

    return contract


def validate_evaluator_output_contract(
    output: EvaluatorOutputContractV1,
) -> EvaluatorOutputContractV1:
    """Verify that an EvaluatorOutputContractV1 adheres to version, state, and evidence rules."""
    taxonomy = load_failure_taxonomy()
    ev_spec = taxonomy.evaluator_by_id(output.evaluator_id)

    if output.can_be_ground_truth:
        raise ValueError(
            f"Evaluator output '{output.evaluator_id}' must never set can_be_ground_truth=True."
        )
    if output.evaluator_family != ev_spec.family:
        raise ValueError(
            f"Evaluator '{output.evaluator_id}' family mismatch: "
            f"expected {ev_spec.family}, got {output.evaluator_family}"
        )
    if output.is_fallible_judge != ev_spec.is_fallible_judge:
        raise ValueError(
            f"Evaluator '{output.evaluator_id}' is_fallible_judge "
            f"must be {ev_spec.is_fallible_judge}."
        )
    if output.result_state == EvaluatorResultState.EVALUATOR_FAILED:
        if output.failure_detail is None:
            raise ValueError(
                "Evaluator output in state 'Evaluator failed' "
                "must populate failure_detail (TRD-61)."
            )
    elif output.result_state in (
        EvaluatorResultState.PASS,
        EvaluatorResultState.REVIEW,
        EvaluatorResultState.BLOCK,
    ):
        if not output.metrics:
            raise ValueError(
                f"Evaluated state '{output.result_state}' must include at least one metric output."
            )
        if not output.supporting_event_ids and not output.supporting_evidence_ids:
            raise ValueError(
                f"Evaluated state '{output.result_state}' must reference "
                "supporting trace events or evidence IDs."
            )

    return output


def build_split_group_key(
    scenario_family: str,
    question_template_id: str,
    injection_recipe_id: str | None,
) -> str:
    """Build the canonical leakage-safe group split key (Proposal Section L.3 & O.4)."""
    fam = scenario_family.strip()
    tpl = question_template_id.strip()
    if not fam or not tpl:
        raise ValueError("scenario_family and question_template_id must be non-empty.")
    recipe = (
        injection_recipe_id.strip()
        if injection_recipe_id and injection_recipe_id.strip()
        else "normal"
    )
    return f"{fam}::{tpl}::{recipe}"
