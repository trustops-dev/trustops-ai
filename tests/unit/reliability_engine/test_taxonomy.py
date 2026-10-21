"""Unit tests for canonical taxonomy loading and annotation contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from trustops_contracts.failures import (
    PRIMARY_FAILURE_LABELS,
    ROOT_CAUSE_CANDIDATES,
    AnnotationContractError,
    validate_failure_label,
)
from trustops_reliability.taxonomy import TaxonomyValidationError, load_taxonomy, validate_taxonomy

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TAXONOMY_PATH = (
    REPOSITORY_ROOT
    / "packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml"
)
ANNOTATION_CASES = REPOSITORY_ROOT / "tests/fixtures/reliability/annotation_cases.json"


def test_taxonomy_contains_exact_approved_primary_labels_in_order() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    classes = cast(list[dict[str, object]], taxonomy["primary_classes"])
    assert tuple(item["name"] for item in classes) == PRIMARY_FAILURE_LABELS
    assert len(classes) == 9
    assert classes[0]["name"] == "NORMAL"


def test_taxonomy_fixes_root_cause_candidates_and_evaluator_families() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    causes = cast(list[dict[str, object]], taxonomy["root_cause_candidates"])
    assert tuple(item["name"] for item in causes) == ROOT_CAUSE_CANDIDATES
    families = cast(list[dict[str, object]], taxonomy["evaluator_families"])
    assert {item["evaluator_id"] for item in families} == {
        "deterministic",
        "rag",
        "semantic_llm",
        "security",
        "agent_workflow",
        "policy_conformance",
    }
    assert taxonomy["review_status"] == "candidate_pending_cross_team_signoff"


def test_taxonomy_rejects_missing_class() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    classes = cast(list[dict[str, object]], taxonomy["primary_classes"])
    taxonomy["primary_classes"] = classes[:-1]
    with pytest.raises(TaxonomyValidationError, match="exactly NORMAL"):
        validate_taxonomy(taxonomy)


def test_taxonomy_rejects_evaluator_predictions_as_ground_truth() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    policy = cast(dict[str, object], taxonomy["label_policy"])
    policy["forbidden_ground_truth_sources"] = ["classifier_predictions"]
    with pytest.raises(TaxonomyValidationError, match="evaluator predictions"):
        validate_taxonomy(taxonomy)


def test_taxonomy_loader_rejects_invalid_json_compatible_yaml(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("primary_classes: [NORMAL,", encoding="utf-8")
    with pytest.raises(TaxonomyValidationError, match="valid JSON-compatible YAML"):
        load_taxonomy(path)


def test_approved_annotation_fixtures_are_consistent() -> None:
    cases = json.loads(ANNOTATION_CASES.read_text(encoding="utf-8"))
    for case in cases:
        label = validate_failure_label(case["annotation"])
        assert label.trace_id == case["annotation"]["trace_id"]


def test_adjudicated_label_requires_evidence_and_source() -> None:
    payload = {
        "contract_version": "1.0.0",
        "trace_id": "trace-1",
        "annotation_status": "adjudicated",
        "primary_label": "NORMAL",
        "secondary_findings": [],
        "evidence_refs": [],
        "annotation_guideline_version": "1.0.0",
    }
    with pytest.raises(AnnotationContractError, match="must link to concrete trace evidence"):
        validate_failure_label(payload)


def test_scenario_intent_mismatch_requires_human_adjudication() -> None:
    payload = {
        "contract_version": "1.0.0",
        "trace_id": "trace-2",
        "annotation_status": "adjudicated",
        "primary_label": "NORMAL",
        "secondary_findings": [],
        "label_source": "controlled_scenario_confirmed",
        "intended_failure_class": "WORKFLOW_VIOLATION",
        "evidence_refs": [{"trace_id": "trace-2", "event_id": "evt-safe-refusal"}],
        "annotation_guideline_version": "1.0.0",
    }
    with pytest.raises(AnnotationContractError, match="requires human adjudication"):
        validate_failure_label(payload)


def test_evaluator_prediction_cannot_be_label_source() -> None:
    payload = {
        "contract_version": "1.0.0",
        "trace_id": "trace-3",
        "annotation_status": "adjudicated",
        "primary_label": "HALLUCINATION",
        "secondary_findings": [],
        "label_source": "llm_judge",
        "evidence_refs": [{"trace_id": "trace-3", "claim_id": "claim-1"}],
        "annotation_guideline_version": "1.0.0",
    }
    with pytest.raises(AnnotationContractError, match="independent of evaluator predictions"):
        validate_failure_label(payload)
