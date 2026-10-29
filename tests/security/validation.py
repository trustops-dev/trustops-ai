"""Validation, precedence resolution, and annotation consistency checks for Failure Taxonomy v1."""

from __future__ import annotations

import re
from dataclasses import dataclass

from trustops_reliability.taxonomy.loader import (
    ApplicationScope,
    FailureClass,
    FailureTaxonomyV1,
    GroundTruthSource,
    RootCauseCandidateId,
    ViolationDisposition,
    load_failure_taxonomy,
)

EVIDENCE_ID_PATTERN = re.compile(r"^E(?:0[1-9]|1[0-9]|2[0-7])$")
DASHBOARD_FIELD_PATTERN = re.compile(r"^(?:OVW|APP|TRX|TRD|RCA|RAG|REL)-\d{2}$")

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0.0"})
SUPPORTED_TAXONOMY_VERSIONS: frozenset[str] = frozenset({"1.0.0"})
ALLOWED_TAXONOMY_STATUSES: frozenset[str] = frozenset({"CANDIDATE_V1", "FROZEN_V1"})

APPROVED_FAILURE_CLASSES: frozenset[FailureClass] = frozenset(
    {
        FailureClass.RETRIEVAL_FAILURE,
        FailureClass.HALLUCINATION,
        FailureClass.TOOL_SELECTION_ERROR,
        FailureClass.INVALID_TOOL_ARGUMENTS,
        FailureClass.WORKFLOW_VIOLATION,
        FailureClass.POLICY_VIOLATION,
        FailureClass.PROMPT_INJECTION,
        FailureClass.UNSUPPORTED_COMPLETION,
    }
)


class TaxonomyValidationError(ValueError):
    """Raised when Failure Taxonomy v1 or trace annotation violates canonical invariants."""


@dataclass(frozen=True, slots=True)
class TraceFailureAnnotation:
    """Validated ground-truth or adjudicated failure annotation for a trace."""

    trace_id: str
    application_type: ApplicationScope
    primary_label: FailureClass
    secondary_findings: tuple[FailureClass, ...]
    violation_disposition: ViolationDisposition
    ground_truth_source: GroundTruthSource
    root_cause_ground_truth: RootCauseCandidateId | None
    evidence_ids: tuple[str, ...]
    notes: str = ""


def validate_taxonomy_v1(taxonomy: FailureTaxonomyV1 | None = None) -> FailureTaxonomyV1:
    """Validate all structural, semantic, and research-integrity invariants on Taxonomy v1."""
    tax = taxonomy if taxonomy is not None else load_failure_taxonomy()

    if (
        not isinstance(tax.schema_version, str)
        or tax.schema_version not in SUPPORTED_SCHEMA_VERSIONS
    ):
        raise TaxonomyValidationError(
            f"Unsupported taxonomy schema_version {tax.schema_version!r}; "
            f"supported versions: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    if (
        not isinstance(tax.taxonomy_version, str)
        or tax.taxonomy_version not in SUPPORTED_TAXONOMY_VERSIONS
    ):
        raise TaxonomyValidationError(
            f"Unsupported taxonomy_version {tax.taxonomy_version!r}; "
            f"supported versions: {sorted(SUPPORTED_TAXONOMY_VERSIONS)}"
        )
    if not isinstance(tax.status, str) or tax.status not in ALLOWED_TAXONOMY_STATUSES:
        raise TaxonomyValidationError(
            f"Invalid taxonomy status {tax.status!r}; "
            f"expected one of {sorted(ALLOWED_TAXONOMY_STATUSES)}"
        )

    if not tax.single_primary_label_invariant:
        raise TaxonomyValidationError("single_primary_label_invariant must be True.")
    if not tax.allow_secondary_findings:
        raise TaxonomyValidationError("allow_secondary_findings must be True.")
    if not tax.forbid_evaluator_as_ground_truth:
        raise TaxonomyValidationError("forbid_evaluator_as_ground_truth must be True.")
    if tax.rca_scores_are_calibrated_probabilities:
        raise TaxonomyValidationError(
            "rca_scores_are_calibrated_probabilities must be False in MVP v1."
        )

    # 1. Verify exact 9 classes (NORMAL + 8 primary failure classes)
    seen_classes = {spec.class_id for spec in tax.classes}
    expected_classes = APPROVED_FAILURE_CLASSES | {FailureClass.NORMAL}
    if seen_classes != expected_classes or len(tax.classes) != 9:
        raise TaxonomyValidationError(
            f"Taxonomy must contain exactly NORMAL + 8 approved classes; got {seen_classes}"
        )

    # 2. Verify precedence ranks 1..9 are contiguous and match class specs
    precedence_map = {rule.class_id: rule.rank for rule in tax.primary_label_precedence}
    if set(precedence_map.keys()) != expected_classes:
        raise TaxonomyValidationError(
            "primary_label_precedence must cover all 9 canonical classes."
        )
    if sorted(precedence_map.values()) != list(range(1, 10)):
        raise TaxonomyValidationError("Precedence ranks must be contiguous integers 1..9.")

    evaluator_ids = {ev.evaluator_id for ev in tax.evaluators}
    candidate_ids = {cand.candidate_id for cand in tax.root_cause_candidates}
    if len(candidate_ids) != 9 or candidate_ids != set(RootCauseCandidateId):
        raise TaxonomyValidationError(
            f"RCA candidate set must contain all 9 canonical candidates; got {candidate_ids}"
        )

    # 3. Verify each class specification and precedence-consistent secondary findings
    for spec in tax.classes:
        if spec.precedence_rank != precedence_map[spec.class_id]:
            raise TaxonomyValidationError(
                f"Precedence mismatch for {spec.class_id}: "
                f"class has {spec.precedence_rank}, table has {precedence_map[spec.class_id]}"
            )
        if spec.class_id == FailureClass.NORMAL:
            if spec.is_failure:
                raise TaxonomyValidationError("NORMAL must have is_failure=False.")
            if spec.allowed_secondary_findings:
                raise TaxonomyValidationError("NORMAL cannot allow secondary failure findings.")
            if spec.default_rca_candidates:
                raise TaxonomyValidationError("NORMAL cannot define default RCA candidates.")
        else:
            if not spec.is_failure:
                raise TaxonomyValidationError(f"{spec.class_id} must have is_failure=True.")
            if not spec.default_rca_candidates:
                raise TaxonomyValidationError(
                    f"Failure class {spec.class_id} must specify default_rca_candidates."
                )

        if not spec.inclusion_criteria or not spec.exclusion_criteria:
            raise TaxonomyValidationError(
                f"{spec.class_id} must define non-empty inclusion and exclusion criteria."
            )
        if not spec.primary_metrics:
            raise TaxonomyValidationError(f"{spec.class_id} must define primary_metrics.")
        if not spec.expected_evaluator_signals:
            raise TaxonomyValidationError(
                f"{spec.class_id} must define expected_evaluator_signals."
            )
        for ev_id in spec.expected_evaluator_signals:
            if ev_id not in evaluator_ids:
                raise TaxonomyValidationError(
                    f"{spec.class_id} references unknown evaluator '{ev_id}'."
                )
        for eid in spec.required_evidence_ids:
            if not EVIDENCE_ID_PATTERN.match(eid):
                raise TaxonomyValidationError(
                    f"{spec.class_id} references invalid trace evidence ID "
                    f"'{eid}' (expected E01-E27)."
                )
        if spec.class_id in spec.allowed_secondary_findings:
            raise TaxonomyValidationError(
                f"{spec.class_id} cannot list itself in allowed_secondary_findings."
            )
        if FailureClass.NORMAL in spec.allowed_secondary_findings:
            raise TaxonomyValidationError(
                f"{spec.class_id} cannot list NORMAL in allowed_secondary_findings."
            )
        for sec in spec.allowed_secondary_findings:
            if precedence_map[sec] <= spec.precedence_rank:
                raise TaxonomyValidationError(
                    f"Class {spec.class_id} (rank {spec.precedence_rank}) cannot allow "
                    f"higher-or-equal precedence class {sec} (rank {precedence_map[sec]}) "
                    "as a secondary finding."
                )

    # 4. Verify ground-truth hierarchy forbids EVALUATOR_PREDICTION
    for gt in tax.ground_truth_hierarchy:
        if gt.source_id == GroundTruthSource.EVALUATOR_PREDICTION and gt.allowed_as_ground_truth:
            raise TaxonomyValidationError(
                "EVALUATOR_PREDICTION must never have allowed_as_ground_truth=True."
            )

    # 5. Verify evaluators never claim to be ground truth and map to valid evidence/dashboard IDs
    for ev in tax.evaluators:
        if ev.can_be_ground_truth:
            raise TaxonomyValidationError(
                f"Evaluator '{ev.evaluator_id}' cannot have can_be_ground_truth=True."
            )
        if ev.family in ("SEMANTIC_LLM", "RAG_SEMANTIC", "SECURITY") and not ev.is_fallible_judge:
            raise TaxonomyValidationError(
                f"Semantic/security evaluator '{ev.evaluator_id}' must set is_fallible_judge=True."
            )
        for eid in ev.required_evidence_ids:
            if not EVIDENCE_ID_PATTERN.match(eid):
                raise TaxonomyValidationError(
                    f"Evaluator '{ev.evaluator_id}' has invalid evidence ID '{eid}'."
                )
        for fid in ev.dashboard_field_ids:
            if not DASHBOARD_FIELD_PATTERN.match(fid):
                raise TaxonomyValidationError(
                    f"Evaluator '{ev.evaluator_id}' has invalid dashboard field ID '{fid}'."
                )

    # 6. Verify RCA candidates and S1-03 policy_configuration boundary
    for cand in tax.root_cause_candidates:
        for eid in cand.required_evidence_ids:
            if not EVIDENCE_ID_PATTERN.match(eid):
                raise TaxonomyValidationError(
                    f"RCA candidate '{cand.candidate_id}' has invalid evidence ID '{eid}'."
                )
        if cand.candidate_id == RootCauseCandidateId.POLICY_CONFIGURATION:
            if "supplier" not in cand.disambiguation_note.lower():
                raise TaxonomyValidationError(
                    "policy_configuration must document the S1-03 supplier ineligibility boundary."
                )

    # 7. Verify RQ1-RQ4 and dataset leakage safeguards
    rq_ids = [rq.rq_id for rq in tax.research_questions]
    if rq_ids != ["RQ1", "RQ2", "RQ3", "RQ4"]:
        raise TaxonomyValidationError(f"Expected RQ1..RQ4 in order, got {rq_ids}")

    safeguards = tax.dataset_leakage_safeguards
    ratio_sum = safeguards.train_ratio + safeguards.validation_ratio + safeguards.test_ratio
    if abs(ratio_sum - 1.0) > 1e-6:
        raise TaxonomyValidationError(f"Dataset split ratios must sum to 1.0, got {ratio_sum}")
    if list(safeguards.required_split_group_components) != [
        "scenario_family",
        "question_template_id",
    ]:
        raise TaxonomyValidationError(
            "required_split_group_components must be ['scenario_family', 'question_template_id'] "
            "so controls and injected variants share one parent split key."
        )
    required_forbidden = {
        "injected_failure_class",
        "injected_root_cause",
        "injection_recipe_id",
        "expected_critical_policy_result",
    }
    if not required_forbidden.issubset(set(safeguards.forbidden_inference_feature_keys)):
        raise TaxonomyValidationError(
            "forbidden_inference_feature_keys is missing mandatory ground-truth keys."
        )

    return tax


def resolve_primary_and_secondary_labels(
    observed_classes: tuple[FailureClass, ...] | list[FailureClass],
    taxonomy: FailureTaxonomyV1 | None = None,
) -> tuple[FailureClass, tuple[FailureClass, ...]]:
    """Deterministically resolve one primary label and ordered secondary findings.

    Follows the canonical precedence hierarchy in Failure Taxonomy v1:
    - If no failure classes are observed (empty or only NORMAL), returns (NORMAL, ()).
    - If multiple failure classes co-occur (e.g. WORKFLOW_VIOLATION + POLICY_VIOLATION
      + UNSUPPORTED_COMPLETION in tr_proc_102, PROMPT_INJECTION + RETRIEVAL_FAILURE,
      or RETRIEVAL_FAILURE + HALLUCINATION in tr_rag_210), selects the highest-precedence
      failure class (lowest rank integer) as primary and retains all remaining unique
      failure classes in ascending precedence rank order as secondary_findings.
    """
    tax = taxonomy if taxonomy is not None else load_failure_taxonomy()
    rank_by_class = {rule.class_id: rule.rank for rule in tax.primary_label_precedence}

    normalized_classes: set[FailureClass] = set()
    for raw_cls in observed_classes:
        try:
            cls = FailureClass(raw_cls)
        except ValueError as exc:
            raise TaxonomyValidationError(f"Unrecognized failure class {raw_cls!r}") from exc
        if cls != FailureClass.NORMAL:
            normalized_classes.add(cls)

    unique_failures = sorted(normalized_classes, key=lambda cls: rank_by_class[cls])
    if not unique_failures:
        return FailureClass.NORMAL, ()

    primary = unique_failures[0]
    secondary = tuple(unique_failures[1:])
    return primary, secondary


def validate_trace_annotation(
    annotation: TraceFailureAnnotation,
    taxonomy: FailureTaxonomyV1 | None = None,
) -> TraceFailureAnnotation:
    """Validate a trace annotation against taxonomy boundaries and precedence rules."""
    if not isinstance(annotation, TraceFailureAnnotation):
        raise TaxonomyValidationError("Expected a TraceFailureAnnotation instance.")
    if not isinstance(annotation.trace_id, str) or not annotation.trace_id.strip():
        raise TaxonomyValidationError("TraceFailureAnnotation.trace_id must be a non-blank string.")

    tax = taxonomy if taxonomy is not None else load_failure_taxonomy()
    rank_by_class = {rule.class_id: rule.rank for rule in tax.primary_label_precedence}

    try:
        app_type = ApplicationScope(annotation.application_type)
    except ValueError as exc:
        raise TaxonomyValidationError(
            f"Invalid application_type {annotation.application_type!r}"
        ) from exc

    try:
        primary_label = FailureClass(annotation.primary_label)
    except ValueError as exc:
        raise TaxonomyValidationError(
            f"Invalid primary_label {annotation.primary_label!r}"
        ) from exc

    try:
        disposition = ViolationDisposition(annotation.violation_disposition)
    except ValueError as exc:
        raise TaxonomyValidationError(
            f"Invalid violation_disposition {annotation.violation_disposition!r}"
        ) from exc

    try:
        gt_source = GroundTruthSource(annotation.ground_truth_source)
    except ValueError as exc:
        raise TaxonomyValidationError(
            f"Invalid ground_truth_source {annotation.ground_truth_source!r}"
        ) from exc

    # 1. Ground truth source check (never allow evaluator predictions as ground truth)
    gt_by_id = {gt.source_id: gt for gt in tax.ground_truth_hierarchy}
    gt_spec = gt_by_id.get(gt_source)
    if gt_spec is None or not gt_spec.allowed_as_ground_truth:
        raise TaxonomyValidationError(
            f"Ground-truth source '{gt_source}' is forbidden as a label authority."
        )

    # 2. Primary class scope and disposition rules
    class_spec = tax.class_by_id(primary_label)
    if app_type not in class_spec.applicable_apps:
        raise TaxonomyValidationError(
            f"Primary label '{primary_label}' is not applicable to "
            f"application_type '{app_type}'."
        )

    if primary_label == FailureClass.NORMAL:
        if annotation.secondary_findings:
            raise TaxonomyValidationError(
                "Trace labeled NORMAL cannot have non-empty secondary_findings."
            )
        if disposition != ViolationDisposition.NOT_APPLICABLE:
            raise TaxonomyValidationError(
                "Trace labeled NORMAL must have violation_disposition=NOT_APPLICABLE; "
                "prevented violations must use their failure class with PREVENTED."
            )
        if annotation.root_cause_ground_truth is not None:
            raise TaxonomyValidationError(
                "Trace labeled NORMAL must have root_cause_ground_truth=None."
            )
    else:
        if disposition == ViolationDisposition.NOT_APPLICABLE:
            raise TaxonomyValidationError(
                f"Failure label '{primary_label}' cannot use "
                "violation_disposition=NOT_APPLICABLE."
            )
        if annotation.root_cause_ground_truth is not None:
            try:
                RootCauseCandidateId(annotation.root_cause_ground_truth)
            except ValueError as exc:
                raise TaxonomyValidationError(
                    f"Invalid root_cause_ground_truth {annotation.root_cause_ground_truth!r}"
                ) from exc

        primary_rank = rank_by_class[primary_label]
        prev_sec_rank = primary_rank
        seen_secondaries: set[FailureClass] = set()
        for raw_sec in annotation.secondary_findings:
            try:
                sec = FailureClass(raw_sec)
            except ValueError as exc:
                raise TaxonomyValidationError(
                    f"Invalid secondary finding {raw_sec!r}"
                ) from exc
            if sec == FailureClass.NORMAL:
                raise TaxonomyValidationError("NORMAL cannot appear in secondary_findings.")
            if sec == primary_label:
                raise TaxonomyValidationError(
                    f"Primary label '{primary_label}' cannot be duplicated in secondary_findings."
                )
            if sec in seen_secondaries:
                raise TaxonomyValidationError(
                    f"Duplicate secondary finding '{sec}' in secondary_findings."
                )
            seen_secondaries.add(sec)

            sec_rank = rank_by_class[sec]
            if sec_rank <= primary_rank:
                raise TaxonomyValidationError(
                    f"Secondary finding '{sec}' (precedence rank {sec_rank}) has higher "
                    f"precedence than primary label '{primary_label}' (precedence rank "
                    f"{primary_rank}); '{sec}' must be the primary label with "
                    f"'{primary_label}' as secondary."
                )
            if sec_rank < prev_sec_rank:
                raise TaxonomyValidationError(
                    "secondary_findings must be ordered by ascending precedence rank."
                )
            prev_sec_rank = sec_rank

            sec_spec = tax.class_by_id(sec)
            if app_type not in sec_spec.applicable_apps:
                raise TaxonomyValidationError(
                    f"Secondary finding '{sec}' is not applicable to "
                    f"application_type '{app_type}'."
                )
            if sec not in class_spec.allowed_secondary_findings:
                raise TaxonomyValidationError(
                    f"Secondary finding '{sec}' is not permitted under primary label "
                    f"'{primary_label}'."
                )

    # 3. Validate evidence references
    if not annotation.evidence_ids:
        raise TaxonomyValidationError("Trace annotation must cite at least one evidence ID.")
    for eid in annotation.evidence_ids:
        if not isinstance(eid, str) or not EVIDENCE_ID_PATTERN.match(eid):
            raise TaxonomyValidationError(
                f"Invalid evidence ID '{eid}' in annotation for trace '{annotation.trace_id}'."
            )

    return annotation