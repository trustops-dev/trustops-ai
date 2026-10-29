"""Versioned evaluator I/O contracts, trace evidence mappings, and leakage safeguards."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, is_dataclass
from enum import StrEnum

from trustops_reliability.taxonomy.loader import (
    ApplicationScope,
    EvaluatorFamily,
    MetricDirection,
    load_failure_taxonomy,
)
from trustops_reliability.taxonomy.validation import EVIDENCE_ID_PATTERN

SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({"1.0.0"})
SUPPORTED_TRACE_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0.0"})
SUPPORTED_EVALUATOR_VERSIONS: frozenset[str] = frozenset({"1.0.0"})

ADDITIONAL_FORBIDDEN_GROUND_TRUTH_KEYS: frozenset[str] = frozenset(
    {
        "scenario_metadata",
        "ground_truth",
        "ground_truth_label",
        "ground_truth_source",
        "root_cause_ground_truth",
        "adjudicated_label",
    }
)

_CAMEL_BOUNDARY_1 = re.compile(r"([a-z0-9])([A-Z])")
_CAMEL_BOUNDARY_2 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")


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


def normalize_field_name(field_name: str) -> str:
    """Normalize a field name across snake_case, camelCase, PascalCase, and separators.

    Examples:
        'injectedFailureClass' -> 'injected_failure_class'
        'Injected-Failure-Class' -> 'injected_failure_class'
        'injected.failure.class' -> 'injected_failure_class'
        'INJECTED_FAILURE_CLASS' -> 'injected_failure_class'
    """
    step1 = _CAMEL_BOUNDARY_1.sub(r"\1_\2", field_name.strip())
    step2 = _CAMEL_BOUNDARY_2.sub(r"\1_\2", step1)
    normalized = _NON_ALNUM.sub("_", step2).strip("_").lower()
    return normalized


def find_leaked_ground_truth_keys(
    payload: object,
    forbidden_normalized_keys: frozenset[str],
    path: str = "feature_payload",
) -> list[str]:
    """Recursively inspect nested mappings, sequences, sets, and objects for leaked keys."""
    violations: list[str] = []
    if isinstance(payload, Mapping):
        for raw_key, value in payload.items():
            key_str = str(raw_key)
            norm_key = normalize_field_name(key_str)
            child_path = f"{path}.{key_str}"
            if norm_key in forbidden_normalized_keys:
                violations.append(f"{child_path} (normalized='{norm_key}')")
            violations.extend(
                find_leaked_ground_truth_keys(value, forbidden_normalized_keys, child_path)
            )
    elif isinstance(payload, (Sequence, Set)) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        for idx, item in enumerate(payload):
            violations.extend(
                find_leaked_ground_truth_keys(
                    item, forbidden_normalized_keys, f"{path}[{idx}]"
                )
            )
    elif is_dataclass(payload) and not isinstance(payload, type):
        for field_key in payload.__dataclass_fields__:
            field_val = getattr(payload, field_key)
            norm_key = normalize_field_name(field_key)
            child_path = f"{path}.{field_key}"
            if norm_key in forbidden_normalized_keys:
                violations.append(f"{child_path} (normalized='{norm_key}')")
            violations.extend(
                find_leaked_ground_truth_keys(field_val, forbidden_normalized_keys, child_path)
            )
    return violations


def _require_non_blank_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{field_name}' must be a non-blank string, got {value!r}.")
    return value.strip()


def validate_evaluator_input_contract(
    contract: EvaluatorInputContractV1,
) -> EvaluatorInputContractV1:
    """Verify that an EvaluatorInputContractV1 carries valid versions, IDs, and zero leakage."""
    if not isinstance(contract, EvaluatorInputContractV1):
        raise ValueError("Expected an EvaluatorInputContractV1 instance.")

    contract_version = _require_non_blank_str(contract.contract_version, "contract_version")
    if contract_version not in SUPPORTED_CONTRACT_VERSIONS:
        raise ValueError(
            f"Unsupported EvaluatorInputContractV1 contract_version {contract.contract_version!r}; "
            f"supported versions: {sorted(SUPPORTED_CONTRACT_VERSIONS)}"
        )

    trace_schema_version = _require_non_blank_str(
        contract.trace_schema_version, "trace_schema_version"
    )
    if trace_schema_version not in SUPPORTED_TRACE_SCHEMA_VERSIONS:
        raise ValueError(
            "Unsupported EvaluatorInputContractV1 trace_schema_version "
            f"{contract.trace_schema_version!r}; "
            f"supported versions: {sorted(SUPPORTED_TRACE_SCHEMA_VERSIONS)}"
        )

    _require_non_blank_str(contract.trace_id, "trace_id")
    _require_non_blank_str(contract.evaluation_run_id, "evaluation_run_id")
    _require_non_blank_str(contract.application_id, "application_id")

    try:
        ApplicationScope(contract.application_type)
    except ValueError as exc:
        raise ValueError(
            f"Invalid application_type {contract.application_type!r}; "
            f"expected one of {[s.value for s in ApplicationScope]}"
        ) from exc

    if (
        not isinstance(contract.evidence_event_ids, (tuple, list))
        or len(contract.evidence_event_ids) == 0
    ):
        raise ValueError("EvaluatorInputContractV1.evidence_event_ids must be non-empty.")
    for idx, ev_id in enumerate(contract.evidence_event_ids):
        _require_non_blank_str(ev_id, f"evidence_event_ids[{idx}]")

    if not isinstance(contract.versions, Mapping):
        raise ValueError("EvaluatorInputContractV1.versions must be a mapping.")

    required_version_keys = (
        "application_version",
        "prompt_version",
        "model_version",
        "retriever_version",
    )
    missing_versions = [k for k in required_version_keys if k not in contract.versions]
    if missing_versions:
        sorted_missing = ", ".join(sorted(missing_versions))
        raise ValueError(f"EvaluatorInputContractV1 missing version keys: {sorted_missing}")
    for req_key in required_version_keys:
        _require_non_blank_str(contract.versions.get(req_key), f"versions.{req_key}")
    for ver_key, ver_val in contract.versions.items():
        _require_non_blank_str(ver_key, "versions.<key>")
        if ver_val is not None:
            _require_non_blank_str(ver_val, f"versions.{ver_key}")

    if not isinstance(contract.feature_payload, Mapping):
        raise ValueError("EvaluatorInputContractV1.feature_payload must be a mapping.")

    taxonomy = load_failure_taxonomy()
    forbidden_normalized = frozenset(
        normalize_field_name(k)
        for k in taxonomy.dataset_leakage_safeguards.forbidden_inference_feature_keys
    ) | ADDITIONAL_FORBIDDEN_GROUND_TRUTH_KEYS

    leaked_paths = find_leaked_ground_truth_keys(
        contract.feature_payload, forbidden_normalized, path="feature_payload"
    )
    leaked_version_paths = find_leaked_ground_truth_keys(
        contract.versions, forbidden_normalized, path="versions"
    )
    all_leaked = leaked_paths + leaked_version_paths
    if all_leaked:
        joined = ", ".join(all_leaked)
        raise ValueError(
            "Ground-truth leakage detected in EvaluatorInputContractV1: " + joined
        )

    return contract


def validate_evaluator_output_contract(
    output: EvaluatorOutputContractV1,
) -> EvaluatorOutputContractV1:
    """Verify that an EvaluatorOutputContractV1 adheres to version, state, and evidence rules."""
    if not isinstance(output, EvaluatorOutputContractV1):
        raise ValueError("Expected an EvaluatorOutputContractV1 instance.")

    contract_version = _require_non_blank_str(output.contract_version, "contract_version")
    if contract_version not in SUPPORTED_CONTRACT_VERSIONS:
        raise ValueError(
            f"Unsupported EvaluatorOutputContractV1 contract_version {output.contract_version!r}; "
            f"supported versions: {sorted(SUPPORTED_CONTRACT_VERSIONS)}"
        )

    _require_non_blank_str(output.trace_id, "trace_id")
    run_id = _require_non_blank_str(output.evaluation_run_id, "evaluation_run_id")
    evaluator_id = _require_non_blank_str(output.evaluator_id, "evaluator_id")
    evaluator_version = _require_non_blank_str(output.evaluator_version, "evaluator_version")
    if evaluator_version not in SUPPORTED_EVALUATOR_VERSIONS:
        raise ValueError(
            f"Unsupported evaluator_version {output.evaluator_version!r} for '{evaluator_id}'; "
            f"supported versions: {sorted(SUPPORTED_EVALUATOR_VERSIONS)}"
        )

    taxonomy = load_failure_taxonomy()
    try:
        ev_spec = taxonomy.evaluator_by_id(evaluator_id)
    except KeyError as exc:
        raise ValueError(f"Unrecognized evaluator_id {evaluator_id!r}.") from exc

    try:
        state = EvaluatorResultState(output.result_state)
    except ValueError as exc:
        raise ValueError(
            f"Unrecognized result_state {output.result_state!r}; "
            f"expected one of {[s.value for s in EvaluatorResultState]}"
        ) from exc

    try:
        family = EvaluatorFamily(output.evaluator_family)
    except ValueError as exc:
        raise ValueError(f"Unrecognized evaluator_family {output.evaluator_family!r}.") from exc

    if not isinstance(output.can_be_ground_truth, bool) or output.can_be_ground_truth:
        raise ValueError(
            f"Evaluator output '{evaluator_id}' must never set can_be_ground_truth=True."
        )
    if family != ev_spec.family:
        raise ValueError(
            f"Evaluator '{evaluator_id}' family mismatch: "
            f"expected {ev_spec.family}, got {family}"
        )
    if (
        not isinstance(output.is_fallible_judge, bool)
        or output.is_fallible_judge != ev_spec.is_fallible_judge
    ):
        raise ValueError(
            f"Evaluator '{evaluator_id}' is_fallible_judge "
            f"must be {ev_spec.is_fallible_judge}."
        )

    if not isinstance(output.metrics, (tuple, list)):
        raise ValueError("EvaluatorOutputContractV1.metrics must be a tuple or list.")
    if not isinstance(output.supporting_event_ids, (tuple, list)):
        raise ValueError("EvaluatorOutputContractV1.supporting_event_ids must be a tuple or list.")
    if not isinstance(output.supporting_evidence_ids, (tuple, list)):
        raise ValueError(
            "EvaluatorOutputContractV1.supporting_evidence_ids must be a tuple or list."
        )

    for idx, ev_id in enumerate(output.supporting_event_ids):
        _require_non_blank_str(ev_id, f"supporting_event_ids[{idx}]")
    for idx, eid in enumerate(output.supporting_evidence_ids):
        clean_eid = _require_non_blank_str(eid, f"supporting_evidence_ids[{idx}]")
        if not EVIDENCE_ID_PATTERN.match(clean_eid):
            raise ValueError(
                f"Invalid supporting_evidence_ids[{idx}]={eid!r}; expected E01..E27."
            )

    if state == EvaluatorResultState.EVALUATOR_FAILED:
        if output.failure_detail is None or not isinstance(
            output.failure_detail, EvaluatorFailureDetail
        ):
            raise ValueError(
                "Evaluator output in state 'Evaluator failed' "
                "must populate failure_detail (TRD-61)."
            )
        _require_non_blank_str(
            output.failure_detail.error_category, "failure_detail.error_category"
        )
        _require_non_blank_str(
            output.failure_detail.error_message, "failure_detail.error_message"
        )
        detail_run_id = _require_non_blank_str(
            output.failure_detail.evaluator_run_id, "failure_detail.evaluator_run_id"
        )
        if detail_run_id != run_id:
            raise ValueError(
                "failure_detail.evaluator_run_id must match output.evaluation_run_id."
            )
        _require_non_blank_str(
            output.failure_detail.occurred_at_utc, "failure_detail.occurred_at_utc"
        )
        if len(output.metrics) > 0:
            raise ValueError(
                "Evaluator output in state 'Evaluator failed' must have empty metrics."
            )
    elif state in (
        EvaluatorResultState.PASS,
        EvaluatorResultState.REVIEW,
        EvaluatorResultState.BLOCK,
    ):
        if output.failure_detail is not None:
            raise ValueError(
                f"Evaluated state '{state}' cannot include failure_detail."
            )
        if not output.metrics:
            raise ValueError(
                f"Evaluated state '{state}' must include at least one metric output."
            )
        if not output.supporting_event_ids or not output.supporting_evidence_ids:
            raise ValueError(
                f"Evaluated state '{state}' must reference both "
                "supporting_event_ids and supporting_evidence_ids."
            )

        allowed_metrics = {m.metric_name: m for m in ev_spec.output_metrics}
        for idx, metric in enumerate(output.metrics):
            if not isinstance(metric, MetricValueOutput):
                raise ValueError(
                    f"metrics[{idx}] must be a MetricValueOutput instance."
                )
            m_name = _require_non_blank_str(metric.metric_name, f"metrics[{idx}].metric_name")
            if m_name not in allowed_metrics:
                raise ValueError(
                    f"Metric '{m_name}' is not declared for evaluator '{evaluator_id}'."
                )
            spec_m = allowed_metrics[m_name]
            if metric.unit != spec_m.unit or metric.direction != spec_m.direction:
                raise ValueError(
                    f"Metric '{m_name}' metadata mismatch: expected "
                    f"(unit={spec_m.unit!r}, direction={spec_m.direction!r}), "
                    f"got (unit={metric.unit!r}, direction={metric.direction!r})."
                )
            if metric.value is None or (
                isinstance(metric.value, str) and not metric.value.strip()
            ):
                raise ValueError(
                    f"Metric '{m_name}' in evaluated state '{state}' must have a non-empty value."
                )
    else:
        # NOT_EVALUATED or NOT_APPLICABLE
        if output.failure_detail is not None:
            raise ValueError(f"State '{state}' cannot include failure_detail.")
        if len(output.metrics) > 0:
            raise ValueError(f"State '{state}' must have empty metrics.")

    return output


def _validate_split_component(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    cleaned = value.strip()
    if "::" in cleaned:
        raise ValueError(f"{name} cannot contain the reserved '::' delimiter.")
    return cleaned


def build_split_group_key(
    scenario_family: str,
    question_template_id: str,
    injection_recipe_id: str | None = None,
) -> str:
    """Build the canonical leakage-safe parent group split key (Proposal Section L.3 & O.4).

    Normal controls, linguistic paraphrases, and all injected failure variants derived from
    the same (scenario_family, question_template_id) share the exact same parent split group
    key so they are guaranteed to land in the same train/validation/test partition.
    The optional injection_recipe_id parameter is accepted and validated for call-site
    compatibility; use build_scenario_variant_id() when a recipe-specific identifier is needed.
    """
    fam = _validate_split_component(scenario_family, "scenario_family")
    tpl = _validate_split_component(question_template_id, "question_template_id")
    if injection_recipe_id is not None:
        _validate_split_component(injection_recipe_id, "injection_recipe_id")
    return f"{fam}::{tpl}"


def build_scenario_variant_id(
    scenario_family: str,
    question_template_id: str,
    injection_recipe_id: str | None = None,
    *,
    scenario_id: str | None = None,
) -> str:
    """Build a unique variant/example identifier within a parent split group."""
    parent_key = build_split_group_key(
        scenario_family, question_template_id, injection_recipe_id
    )
    recipe = (
        _validate_split_component(injection_recipe_id, "injection_recipe_id")
        if injection_recipe_id is not None
        else "normal"
    )
    if scenario_id is not None:
        scen = _validate_split_component(scenario_id, "scenario_id")
        return f"{parent_key}::{recipe}::{scen}"
    return f"{parent_key}::{recipe}"