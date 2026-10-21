"""Structural and semantic validation for the canonical failure taxonomy."""

from __future__ import annotations

import re
from collections.abc import Mapping

from trustops_contracts.failures import (
    PRIMARY_FAILURE_LABELS,
    ROOT_CAUSE_CANDIDATES,
    SECONDARY_FINDING_CODES,
)

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class TaxonomyValidationError(ValueError):
    """Raised when taxonomy content violates the v1 contract."""


def _object(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise TaxonomyValidationError(f"{path} must be an object with string keys")
    return value


def _nonempty_string(value: object, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaxonomyValidationError(f"{path} must be a non-empty string")
    return value


def _string_list(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise TaxonomyValidationError(f"{path} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise TaxonomyValidationError(f"{path} must not contain duplicates")
    return value


def _validate_semver(value: object, path: str) -> None:
    if not isinstance(value, str) or SEMVER_PATTERN.fullmatch(value) is None:
        raise TaxonomyValidationError(f"{path} must be a semantic version (MAJOR.MINOR.PATCH)")


def validate_taxonomy(payload: object) -> None:
    """Validate schema/version, all nine approved primary labels, and required semantics."""
    root = _object(payload, "taxonomy")
    required_root = {
        "schema_version",
        "taxonomy_version",
        "review_status",
        "label_policy",
        "primary_classes",
        "secondary_finding_codes",
        "root_cause_candidates",
        "evaluator_families",
    }
    missing = required_root.difference(root)
    extra = set(root).difference(required_root | {"$schema", "description"})
    if missing:
        raise TaxonomyValidationError(f"taxonomy is missing required keys: {sorted(missing)}")
    if extra:
        raise TaxonomyValidationError(f"taxonomy has unexpected keys: {sorted(extra)}")
    _validate_semver(root["schema_version"], "taxonomy.schema_version")
    _validate_semver(root["taxonomy_version"], "taxonomy.taxonomy_version")
    _nonempty_string(root["review_status"], "taxonomy.review_status")
    if root["review_status"] != "candidate_pending_cross_team_signoff":
        raise TaxonomyValidationError(
            "taxonomy review_status must not imply unrecorded team sign-off"
        )

    policy = _object(root["label_policy"], "taxonomy.label_policy")
    policy_required = {
        "one_primary_label_per_trace",
        "secondary_findings_are_orthogonal",
        "normal_requires_sufficient_evidence",
        "primary_label_selection_order",
        "ground_truth_sources",
        "forbidden_ground_truth_sources",
        "unknown_evidence_handling",
    }
    if policy_required.difference(policy) or set(policy).difference(policy_required):
        raise TaxonomyValidationError("taxonomy.label_policy has missing or unexpected keys")
    for field in (
        "one_primary_label_per_trace",
        "secondary_findings_are_orthogonal",
        "normal_requires_sufficient_evidence",
    ):
        if not isinstance(policy[field], bool) or policy[field] is not True:
            raise TaxonomyValidationError(f"taxonomy.label_policy.{field} must be true")
    selection_order = _string_list(
        policy["primary_label_selection_order"],
        "taxonomy.label_policy.primary_label_selection_order",
    )
    if set(selection_order) != set(PRIMARY_FAILURE_LABELS) or len(selection_order) != len(
        PRIMARY_FAILURE_LABELS
    ):
        raise TaxonomyValidationError(
            "primary_label_selection_order must list every primary class exactly once"
        )
    _string_list(
        policy["ground_truth_sources"],
        "taxonomy.label_policy.ground_truth_sources",
    )
    forbidden_ground_truth_sources = _string_list(
        policy["forbidden_ground_truth_sources"],
        "taxonomy.label_policy.forbidden_ground_truth_sources",
    )
    if "evaluator_predictions" not in forbidden_ground_truth_sources:
        raise TaxonomyValidationError(
            "evaluator predictions must be explicitly forbidden as ground truth"
        )
    _nonempty_string(
        policy["unknown_evidence_handling"], "taxonomy.label_policy.unknown_evidence_handling"
    )

    classes = root["primary_classes"]
    if not isinstance(classes, list) or len(classes) != len(PRIMARY_FAILURE_LABELS):
        raise TaxonomyValidationError(
            "primary_classes must contain exactly NORMAL and the eight approved failure classes"
        )
    names: list[str] = []
    class_required = {
        "name",
        "kind",
        "definition",
        "classify_when",
        "do_not_classify_when",
        "expected_trace_evidence",
        "ground_truth_sources",
        "evaluator_signals",
        "primary_metrics",
    }
    for index, raw_class in enumerate(classes):
        item = _object(raw_class, f"taxonomy.primary_classes[{index}]")
        if class_required.difference(item) or set(item).difference(
            class_required | {"boundary_note"}
        ):
            raise TaxonomyValidationError(
                f"taxonomy.primary_classes[{index}] has missing or unexpected keys"
            )
        name = _nonempty_string(item["name"], f"taxonomy.primary_classes[{index}].name")
        names.append(name)
        expected_kind = "baseline" if name == "NORMAL" else "failure"
        if item["kind"] != expected_kind:
            raise TaxonomyValidationError(f"taxonomy class {name} must have kind={expected_kind!r}")
        _nonempty_string(item["definition"], f"taxonomy.{name}.definition")
        for field in (
            "classify_when",
            "do_not_classify_when",
            "expected_trace_evidence",
            "ground_truth_sources",
            "evaluator_signals",
            "primary_metrics",
        ):
            values = _string_list(item[field], f"taxonomy.{name}.{field}")
            if not values:
                raise TaxonomyValidationError(f"taxonomy.{name}.{field} must not be empty")
        if "boundary_note" in item:
            _nonempty_string(item["boundary_note"], f"taxonomy.{name}.boundary_note")
    if tuple(names) != PRIMARY_FAILURE_LABELS:
        raise TaxonomyValidationError(
            "primary_classes must use the canonical approved labels in their declared order"
        )

    secondaries = _string_list(root["secondary_finding_codes"], "taxonomy.secondary_finding_codes")
    if tuple(secondaries) != SECONDARY_FINDING_CODES:
        raise TaxonomyValidationError(
            "secondary_finding_codes do not match the canonical contract list"
        )
    root_causes = root["root_cause_candidates"]
    if not isinstance(root_causes, list) or len(root_causes) != len(ROOT_CAUSE_CANDIDATES):
        raise TaxonomyValidationError(
            "root_cause_candidates must list the fixed nine RCA candidates"
        )
    seen_candidates: list[str] = []
    cause_required = {"name", "definition", "supporting_signals", "distinguish_from"}
    for index, raw_cause in enumerate(root_causes):
        cause = _object(raw_cause, f"taxonomy.root_cause_candidates[{index}]")
        if cause_required.difference(cause) or set(cause).difference(cause_required):
            raise TaxonomyValidationError(
                f"taxonomy.root_cause_candidates[{index}] has missing or unexpected keys"
            )
        cause_name = _nonempty_string(
            cause["name"], f"taxonomy.root_cause_candidates[{index}].name"
        )
        seen_candidates.append(cause_name)
        _nonempty_string(cause["definition"], f"taxonomy.root_cause_candidates[{index}].definition")
        _string_list(cause["supporting_signals"], f"taxonomy.{cause_name}.supporting_signals")
        _string_list(cause["distinguish_from"], f"taxonomy.{cause_name}.distinguish_from")
    if tuple(seen_candidates) != ROOT_CAUSE_CANDIDATES:
        raise TaxonomyValidationError(
            "root cause candidates must preserve the approved fixed order"
        )

    evaluator_families = root["evaluator_families"]
    family_names: list[str] = []
    required_family_keys = {"evaluator_id", "purpose", "signals", "versioning_requirements"}
    if not isinstance(evaluator_families, list) or not evaluator_families:
        raise TaxonomyValidationError("evaluator_families must be a non-empty list")
    for index, raw_family in enumerate(evaluator_families):
        family = _object(raw_family, f"taxonomy.evaluator_families[{index}]")
        if required_family_keys.difference(family) or set(family).difference(required_family_keys):
            raise TaxonomyValidationError(
                f"taxonomy.evaluator_families[{index}] has missing or unexpected keys"
            )
        family_names.append(
            _nonempty_string(
                family["evaluator_id"],
                f"taxonomy.evaluator_families[{index}].evaluator_id",
            )
        )
        _nonempty_string(family["purpose"], f"taxonomy.evaluator_families[{index}].purpose")
        _string_list(family["signals"], f"taxonomy.evaluator_families[{index}].signals")
        _string_list(
            family["versioning_requirements"],
            f"taxonomy.evaluator_families[{index}].versioning_requirements",
        )
    if len(family_names) != len(set(family_names)):
        raise TaxonomyValidationError("evaluator_families contains duplicate evaluator IDs")
