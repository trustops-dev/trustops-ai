"""Tests for the dependency-free Failure Taxonomy v1 loader."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from trustops_reliability.taxonomy.loader import (
    EvaluatorFamily,
    FailureClass,
    GroundTruthSource,
    MetricDirection,
    RootCauseCandidateId,
    TaxonomyLoadError,
    ViolationDisposition,
    load_failure_taxonomy,
    parse_structured_yaml,
)

TAXONOMY_PATH = (
    Path(__file__).parents[3]
    / "packages"
    / "reliability-engine"
    / "src"
    / "trustops_reliability"
    / "taxonomy"
    / "failure_taxonomy.yaml"
)


def test_default_loader_returns_typed_taxonomy() -> None:
    taxonomy = load_failure_taxonomy()

    assert taxonomy.schema_version == "1.0.0"
    assert taxonomy.taxonomy_version == "1.0.0"
    assert taxonomy.status == "FROZEN_V1"


def test_loader_exposes_exact_nine_failure_classes() -> None:
    taxonomy = load_failure_taxonomy()

    assert {item.class_id for item in taxonomy.classes} == set(FailureClass)
    assert len(taxonomy.classes) == 9


def test_precedence_is_ranked_one_through_nine() -> None:
    taxonomy = load_failure_taxonomy()

    assert [item.rank for item in taxonomy.primary_label_precedence] == list(range(1, 10))
    assert taxonomy.primary_label_precedence[0].class_id == FailureClass.PROMPT_INJECTION
    assert taxonomy.primary_label_precedence[-1].class_id == FailureClass.NORMAL


def test_precedence_table_and_class_ranks_agree() -> None:
    taxonomy = load_failure_taxonomy()
    ranks = {item.class_id: item.rank for item in taxonomy.primary_label_precedence}

    assert all(item.precedence_rank == ranks[item.class_id] for item in taxonomy.classes)


def test_all_four_violation_dispositions_are_present() -> None:
    taxonomy = load_failure_taxonomy()

    assert {item.disposition_id for item in taxonomy.violation_dispositions} == set(
        ViolationDisposition
    )


def test_evaluator_predictions_are_not_ground_truth() -> None:
    taxonomy = load_failure_taxonomy()
    evaluator_source = next(
        item
        for item in taxonomy.ground_truth_hierarchy
        if item.source_id == GroundTruthSource.EVALUATOR_PREDICTION
    )

    assert evaluator_source.allowed_as_ground_truth is False


def test_fixed_nine_root_cause_candidates_are_present() -> None:
    taxonomy = load_failure_taxonomy()

    assert {item.candidate_id for item in taxonomy.root_cause_candidates} == set(
        RootCauseCandidateId
    )
    assert len(taxonomy.root_cause_candidates) == 9


def test_eight_evaluator_families_are_defined_as_evaluators() -> None:
    taxonomy = load_failure_taxonomy()

    assert len(taxonomy.evaluators) == 8
    assert all(item.family in set(EvaluatorFamily) for item in taxonomy.evaluators)


def test_evaluators_cannot_be_ground_truth() -> None:
    taxonomy = load_failure_taxonomy()

    assert all(item.can_be_ground_truth is False for item in taxonomy.evaluators)


def test_every_metric_has_a_supported_direction() -> None:
    taxonomy = load_failure_taxonomy()

    assert all(
        metric.direction in set(MetricDirection)
        for evaluator in taxonomy.evaluators
        for metric in evaluator.output_metrics
    )


def test_leakage_safeguards_cover_injected_and_expected_truth_fields() -> None:
    taxonomy = load_failure_taxonomy()
    forbidden = set(taxonomy.dataset_leakage_safeguards.forbidden_inference_feature_keys)

    assert {
        "injected_failure_class",
        "injected_root_cause",
        "injection_recipe_id",
        "expected_critical_policy_result",
        "human_adjudicated_label",
        "is_seeded_failure",
    }.issubset(forbidden)


def test_default_split_ratios_sum_to_one() -> None:
    safeguards = load_failure_taxonomy().dataset_leakage_safeguards

    total = safeguards.train_ratio + safeguards.validation_ratio + safeguards.test_ratio
    assert total == pytest.approx(1.0)


def test_taxonomy_dataclasses_are_immutable() -> None:
    taxonomy = load_failure_taxonomy()

    with pytest.raises(FrozenInstanceError):
        taxonomy.status = "CHANGED"  # type: ignore[misc]


def test_class_by_id_returns_normal_class() -> None:
    taxonomy = load_failure_taxonomy()

    assert taxonomy.class_by_id("NORMAL").is_failure is False


def test_class_by_id_accepts_enum_value() -> None:
    taxonomy = load_failure_taxonomy()

    result = taxonomy.class_by_id(FailureClass.RETRIEVAL_FAILURE)
    assert result.class_id == FailureClass.RETRIEVAL_FAILURE


def test_class_by_id_rejects_unknown_class() -> None:
    with pytest.raises(ValueError, match="Invalid class_id"):
        load_failure_taxonomy().class_by_id("UNKNOWN_FAILURE")


def test_evaluator_by_id_returns_canonical_evaluator() -> None:
    taxonomy = load_failure_taxonomy()

    result = taxonomy.evaluator_by_id("trace_integrity_evaluator")
    assert result.family == EvaluatorFamily.DETERMINISTIC


def test_evaluator_by_id_rejects_unknown_evaluator() -> None:
    with pytest.raises(KeyError, match="Unknown evaluator ID"):
        load_failure_taxonomy().evaluator_by_id("missing_evaluator")


def test_parser_reads_nested_mappings_and_lists() -> None:
    parsed = parse_structured_yaml('root:\n  items:\n    - name: "first"\n      enabled: true\n')

    assert parsed == {"root": {"items": [{"name": "first", "enabled": True}]}}


def test_parser_reads_inline_lists_and_numbers() -> None:
    parsed = parse_structured_yaml('items: ["one", "two"]\nratio: 0.15\ncount: 9\n')

    assert parsed == {"items": ["one", "two"], "ratio": 0.15, "count": 9}


def test_parser_ignores_comments_outside_quoted_strings() -> None:
    parsed = parse_structured_yaml('value: "text # retained" # comment\n')

    assert parsed == {"value": "text # retained"}


def test_parser_rejects_duplicate_mapping_keys() -> None:
    with pytest.raises(TaxonomyLoadError, match="Duplicate key"):
        parse_structured_yaml('value: "one"\nvalue: "two"\n')


def test_parser_rejects_tab_indentation() -> None:
    with pytest.raises(TaxonomyLoadError, match="Tabs are not allowed"):
        parse_structured_yaml('root:\n\tchild: "value"\n')


def test_parser_rejects_yaml_block_scalars_explicitly() -> None:
    with pytest.raises(TaxonomyLoadError, match="Block scalar YAML is not supported"):
        parse_structured_yaml("value: |\n  content\n")


def test_explicit_taxonomy_path_loads_same_version(tmp_path: Path) -> None:
    target = tmp_path / "taxonomy.yaml"
    target.write_text(TAXONOMY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    explicit = load_failure_taxonomy(target)
    packaged = load_failure_taxonomy()
    assert explicit.taxonomy_version == packaged.taxonomy_version


def test_default_resource_loading_works_outside_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    taxonomy = load_failure_taxonomy()

    assert len(taxonomy.classes) == 9
    assert taxonomy.taxonomy_version == "1.0.0"
