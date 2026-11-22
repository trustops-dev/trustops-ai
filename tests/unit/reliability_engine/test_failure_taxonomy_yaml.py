"""Comprehensive Week 1 validation tests for declarative failure_taxonomy.yaml (Task S1-03).

Canonical Path:
    tests/unit/reliability_engine/test_failure_taxonomy_yaml.py
Owner:
    Ahmed Ragab (AI Reliability & Machine Learning Engineer)

Validates the declarative YAML specification aligned with Trace Schema v1.18 Draft,
Alaa's Dataset & Experiment Requirements Matrix v2.4, Mohamed's sent scoped
Governance disposition (PR #28 Rev 0.6 + Nov 13 addendum), and Nour's review
requests (PR #27, PR #29).

Compatible with both `pytest` and `python -m unittest`.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path
from typing import Any

import yaml

EXPECTED_CLASS_IDS: tuple[str, ...] = (
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

EXPECTED_RCA_CAUSE_IDS: tuple[str, ...] = (
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

EXPECTED_DATASET_V1_CLASSES: tuple[str, ...] = (
    "NORMAL",
    "WORKFLOW_VIOLATION",
    "INVALID_TOOL_ARGUMENTS",
    "RETRIEVAL_FAILURE",
    "UNSUPPORTED_COMPLETION",
)

EXPECTED_LATER_DATASET_CLASSES: tuple[str, ...] = (
    "HALLUCINATION",
    "TOOL_SELECTION_ERROR",
    "POLICY_VIOLATION",
    "PROMPT_INJECTION",
)

EXPECTED_EVALUATOR_FAMILIES: frozenset[str] = frozenset(
    {
        "deterministic",
        "rag",
        "semantic_llm",
        "security",
        "agent_workflow",
        "policy_conformance",
    }
)


def _resolve_target_file(canonical_rel_path: str, local_name: str) -> Path:
    """Resolve a target file either in the local outer workspace or canonical monorepo."""
    this_path = Path(__file__).resolve()

    # Strategy 1: Check sibling in local workspace directory
    sibling = this_path.parent / local_name
    if sibling.is_file():
        return sibling

    # Strategy 2: Check canonical path relative to repository root if nested
    try:
        if len(this_path.parents) > 3:
            repo_root = this_path.parents[3]
            canonical = repo_root / canonical_rel_path
            if canonical.is_file():
                return canonical
    except (IndexError, ValueError):
        pass

    raise FileNotFoundError(f"Could not locate {local_name} locally or at {canonical_rel_path}")


def _resolve_taxonomy_yaml_path() -> Path:
    """Locate failure_taxonomy.yaml relative to repository root or test directory."""
    return _resolve_target_file(
        "packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml",
        "failure_taxonomy.yaml",
    )


class TestFailureTaxonomyYaml(unittest.TestCase):
    """Contract, structural, and alignment tests for failure_taxonomy.yaml."""

    taxonomy: dict[str, Any]
    taxonomy_text: str

    @classmethod
    def setUpClass(cls) -> None:
        yaml_path = _resolve_taxonomy_yaml_path()
        cls.taxonomy_text = yaml_path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(cls.taxonomy_text)
        assert isinstance(loaded, dict), "failure_taxonomy.yaml root must be a mapping."
        cls.taxonomy = loaded

    # 1. YAML parsing and structural validity
    def test_yaml_parsing_and_structural_validity(self) -> None:
        self.assertIsInstance(self.taxonomy, dict)
        required_keys = {
            "schema_version",
            "taxonomy_version",
            "status",
            "owner",
            "last_updated",
            "governance_rules",
            "primary_classes",
            "rca_candidates",
        }
        self.assertTrue(required_keys.issubset(self.taxonomy.keys()))
        self.assertEqual(self.taxonomy.get("schema_version"), "1.0.0")
        self.assertEqual(
            self.taxonomy.get("taxonomy_version"), "taxonomy_v1.0.0_v1.18_draft_aligned"
        )
        self.assertEqual(self.taxonomy.get("status"), "DRAFT_AWAITING_TEAM_REVIEW")

    # 2. Preservation of all nine taxonomy classes
    def test_preservation_of_all_nine_taxonomy_classes(self) -> None:
        classes = self.taxonomy.get("primary_classes", [])
        self.assertEqual(len(classes), 9, "Taxonomy must define exactly 9 primary classes.")
        class_ids = [c["class_id"] for c in classes]
        numeric_codes = [c["numeric_code"] for c in classes]
        self.assertEqual(tuple(class_ids), EXPECTED_CLASS_IDS)
        self.assertEqual(len(set(class_ids)), 9)
        self.assertEqual(numeric_codes, list(range(9)))

    def test_normal_vs_failure_class_properties(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        normal = classes_by_id["NORMAL"]
        self.assertIs(normal["is_failure"], False)
        self.assertEqual(normal["precedence_tier"], 0)
        self.assertEqual(normal["likely_rca_candidates"], [])

        for class_id in EXPECTED_CLASS_IDS[1:]:
            spec = classes_by_id[class_id]
            self.assertIs(spec["is_failure"], True, f"{class_id} must have is_failure=True")
            self.assertIn(spec["precedence_tier"], {1, 2, 3, 4, 5})
            self.assertTrue(spec.get("formal_definition", "").strip())
            self.assertGreaterEqual(len(spec.get("inclusion_criteria", [])), 1)
            self.assertGreaterEqual(len(spec.get("exclusion_criteria", [])), 1)
            self.assertGreaterEqual(len(spec.get("boundary_rules", [])), 1)
            self.assertGreaterEqual(len(spec.get("required_trace_evidence", [])), 1)
            self.assertGreaterEqual(len(spec.get("ground_truth_sources", [])), 1)
            self.assertGreaterEqual(len(spec.get("likely_rca_candidates", [])), 1)

    # 3. Preservation of all nine RCA candidates
    def test_preservation_of_all_nine_rca_candidates(self) -> None:
        rca_list = self.taxonomy.get("rca_candidates", [])
        self.assertEqual(len(rca_list), 9, "Taxonomy must define exactly 9 RCA candidates.")
        cause_ids = [c["cause_id"] for c in rca_list]
        self.assertEqual(tuple(cause_ids), EXPECTED_RCA_CAUSE_IDS)
        valid_causes = set(cause_ids)
        valid_failure_classes = set(EXPECTED_CLASS_IDS[1:])

        for cls_spec in self.taxonomy["primary_classes"]:
            for candidate in cls_spec.get("likely_rca_candidates", []):
                self.assertIn(
                    candidate,
                    valid_causes,
                    f"Unknown RCA candidate '{candidate}' in {cls_spec['class_id']}",
                )

        for rca_spec in rca_list:
            self.assertTrue(rca_spec.get("description", "").strip())
            assoc = rca_spec.get("associated_failure_classes", [])
            self.assertGreaterEqual(len(assoc), 1)
            for f_cls in assoc:
                self.assertIn(
                    f_cls,
                    valid_failure_classes,
                    f"Invalid associated failure class '{f_cls}' in RCA candidate '{rca_spec['cause_id']}'",
                )

    # 4. Dataset v1 scope limited to NORMAL and the four frozen Sprint 3 failure classes
    def test_dataset_v1_scope_limited_to_normal_and_four_frozen_classes(self) -> None:
        gov = self.taxonomy.get("governance_rules", {})
        ds_v1 = gov.get("dataset_v1_scope", {})
        self.assertIsInstance(ds_v1, dict)
        frozen = ds_v1.get("frozen_classes", [])
        self.assertEqual(tuple(frozen), EXPECTED_DATASET_V1_CLASSES)
        self.assertEqual(len(frozen), 5)
        self.assertIn("TAI-11", ds_v1.get("description", ""))

    # 5. Later-version classes not incorrectly represented as part of Dataset v1
    def test_later_version_classes_excluded_from_dataset_v1(self) -> None:
        gov = self.taxonomy.get("governance_rules", {})
        later_scope = gov.get("later_versioned_datasets_scope", {})
        self.assertIsInstance(later_scope, dict)
        later_classes = later_scope.get("classes", [])
        self.assertEqual(tuple(later_classes), EXPECTED_LATER_DATASET_CLASSES)
        self.assertEqual(len(later_classes), 4)

        frozen_v1 = set(gov.get("dataset_v1_scope", {}).get("frozen_classes", []))
        for later_cls in later_classes:
            self.assertNotIn(
                later_cls,
                frozen_v1,
                f"Later-version class '{later_cls}' must NOT be in Dataset v1 scope.",
            )

    # 6. Canonical policy field names and current version terminology
    def test_canonical_policy_field_names_and_version_terminology(self) -> None:
        self.assertIn("policy_check.attributes.action_verdict", self.taxonomy_text)
        self.assertIn("verdict_basis", self.taxonomy_text)
        self.assertIn("evaluated_policies[].policy_result", self.taxonomy_text)
        self.assertTrue(re.search(r"evaluated_policies.*status", self.taxonomy_text))
        self.assertIn("decision_config_version", self.taxonomy_text)
        self.assertIn("policy_bundle_version", self.taxonomy_text)
        self.assertIn("policy_kb_version", self.taxonomy_text)

        # Retired names must not be active canonical field paths
        for match in re.finditer(r"pre_tool_verdict", self.taxonomy_text):
            line = self.taxonomy_text[
                max(0, match.start() - 60) : min(len(self.taxonomy_text), match.end() + 60)
            ]
            self.assertTrue(
                "retired" in line.lower() or "legacy" in line.lower(),
                f"Active unflagged use of retired 'pre_tool_verdict' found in: {line}",
            )

        for match in re.finditer(r"decision_engine_version", self.taxonomy_text):
            line = self.taxonomy_text[
                max(0, match.start() - 60) : min(len(self.taxonomy_text), match.end() + 60)
            ]
            self.assertTrue(
                "retired" in line.lower()
                or "legacy" in line.lower()
                or "superseded" in line.lower(),
                f"Active unflagged use of retired 'decision_engine_version' found in: {line}",
            )

    # 7. Use of side_effect_state
    def test_use_of_canonical_side_effect_state(self) -> None:
        self.assertIn("tool_result.attributes.side_effect_state", self.taxonomy_text)
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        uc_evidence = " ".join(classes_by_id["UNSUPPORTED_COMPLETION"]["required_trace_evidence"])
        wv_evidence = " ".join(classes_by_id["WORKFLOW_VIOLATION"]["required_trace_evidence"])
        self.assertIn("side_effect_state", uc_evidence)
        self.assertIn("side_effect_state", wv_evidence)

        # Retired field side_effect_committed must not be used as an active canonical requirement
        for match in re.finditer(r"side_effect_committed", self.taxonomy_text):
            line = self.taxonomy_text[
                max(0, match.start() - 60) : min(len(self.taxonomy_text), match.end() + 60)
            ]
            self.assertTrue(
                "retired" in line.lower() or "legacy" in line.lower(),
                f"Active unflagged use of retired 'side_effect_committed' found in: {line}",
            )

    # 8. Tier 3 versus Tier 4 precedence
    def test_tier3_workflow_strictly_outranks_tier4_policy(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        wv_tier = classes_by_id["WORKFLOW_VIOLATION"]["precedence_tier"]
        pv_tier = classes_by_id["POLICY_VIOLATION"]["precedence_tier"]
        self.assertEqual(wv_tier, 3)
        self.assertEqual(pv_tier, 4)
        self.assertLess(wv_tier, pv_tier, "Tier 3 numerically outranks Tier 4.")

        gov = self.taxonomy.get("governance_rules", {})
        rule = gov.get("workflow_policy_precedence_invariant", {})
        self.assertIn(
            "Tier 3 (WORKFLOW_VIOLATION) strictly outranks Tier 4 (POLICY_VIOLATION)",
            rule.get("description", ""),
        )
        self.assertIn("OD-09", rule.get("description", ""))

    # 9. SC-03A normal business rejection
    def test_sc03a_normal_business_rejection(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        normal_rules = " ".join(classes_by_id["NORMAL"]["boundary_rules"])
        self.assertIn("SC-03A", normal_rules)
        self.assertIn("NOT_APPROVED", normal_rules)
        self.assertIn("POLICY_CHECKED", normal_rules)
        self.assertIn("create_purchase_order", normal_rules)
        self.assertIn("NORMAL", normal_rules)

        pv_rules = " ".join(classes_by_id["POLICY_VIOLATION"]["boundary_rules"])
        self.assertIn("SC-03A", pv_rules)
        self.assertIn("classified as NORMAL", pv_rules)

    # 10. SC-03B isolated boundary-fixture status and unresolved classification
    def test_sc03b_boundary_fixture_and_unresolved_classification(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        normal_rules = " ".join(classes_by_id["NORMAL"]["boundary_rules"])
        self.assertIn("SC-03B", normal_rules)
        self.assertIn("BOUNDARY_TEST", normal_rules)
        self.assertIn("OD-09", normal_rules)

        pv_rules = " ".join(classes_by_id["POLICY_VIOLATION"]["boundary_rules"])
        self.assertIn("SC-03B", pv_rules)
        self.assertIn("BOUNDARY_TEST", pv_rules)
        self.assertIn("OD-09", pv_rules)
        self.assertIn("NOT evidence that the real Agent attempted a PO", pv_rules)

        # Check EC-11 Evidence Rule for policy_configuration RCA
        self.assertIn("EC-11 Evidence Rule", pv_rules)
        self.assertIn("policy_configuration", pv_rules)
        self.assertIn("correct policy BLOCK or PREVENTED outcome is NOT", pv_rules)

        # Check agent_workflow RCA candidate description
        rca_by_id = {r["cause_id"]: r for r in self.taxonomy["rca_candidates"]}
        self.assertIn("SC-03B", rca_by_id["agent_workflow"]["description"])

    # 11. Separation of human ground truth from evaluator outputs
    def test_separation_of_human_ground_truth_and_evaluator_outputs(self) -> None:
        gov = self.taxonomy.get("governance_rules", {})
        self.assertIs(gov.get("evaluator_output_never_used_as_ground_truth"), True)
        self.assertIs(gov.get("llm_judge_is_fallible_signal_only"), True)
        self.assertIs(gov.get("secondary_findings_never_override_primary_label"), True)

    # 12. Technical retrieval failure versus ordinary evidence insufficiency
    def test_technical_retrieval_failure_vs_evidence_insufficiency(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        rf_rules = " ".join(classes_by_id["RETRIEVAL_FAILURE"]["boundary_rules"])
        self.assertIn("Technical Retrieval Fault vs. Completed Retrieval with Zero Hits", rf_rules)
        self.assertIn("RETRIEVAL_TECHNICAL_FAULT_STATUSES", rf_rules)
        self.assertIn("ordinary retrieval evidence insufficiency", rf_rules)
        self.assertIn("retrieval_fault_details", rf_rules)
        self.assertIn(
            "Sensitive provider details must never be emitted into trace events", rf_rules
        )
        self.assertIn("Trace Schema v1.18 Draft", rf_rules)
        self.assertIn("UNAVAILABLE_DUE_TO_RETRIEVAL_FAULT", rf_rules)
        self.assertIn("Disposition: ACCEPT", rf_rules)

        # Verify all seven canonical retrieval_fault_details fields from week_2.md §6
        for fault_field in [
            "fault_stage",
            "provider_or_engine",
            "error_category",
            "error_code",
            "retryable",
            "outcome_certainty",
            "sanitized_diagnostic_summary",
        ]:
            self.assertIn(
                fault_field, rf_rules, f"Missing canonical retrieval fault field: {fault_field}"
            )

        # Verify expected evaluator outcomes
        self.assertIn("evaluator_execution_status = INCOMPLETE_TRACE_EVIDENCE", rf_rules)
        self.assertIn("reliability_decision.decision = INCOMPLETE", rf_rules)
        self.assertIn("adjudication_status = INCONCLUSIVE_TECHNICAL_ERROR", rf_rules)

        # Verify precise disposition from week_2.md §10.3 and adapter verification open status
        self.assertIn(
            "ACCEPT IN DRAFT v1.11 SPECIFICATION & VALIDATOR; KEEP PRODUCTION ADAPTER VERIFICATION OPEN",
            rf_rules,
        )
        self.assertIn("NEG-70", rf_rules)
        self.assertIn("NEG-76", rf_rules)
        self.assertIn(
            "PR #29 synthetic-adapter tests do not establish Production Provider Adapter verification",
            rf_rules,
        )
        self.assertIn("actual runtime production adapter verification remains OPEN", rf_rules)

    # 13. Exclusion of split_group_key from model features
    def test_exclusion_of_split_group_key_from_model_features(self) -> None:
        gov = self.taxonomy.get("governance_rules", {})
        strip_keys = gov.get("strip_ground_truth_at_inference", [])
        self.assertIn("scenario_metadata.split_group_key", strip_keys)

    # 14. Inference-safe projection and ground-truth leakage controls
    def test_inference_safe_projection_and_ground_truth_leakage_controls(self) -> None:
        gov = self.taxonomy.get("governance_rules", {})
        strip_keys = set(gov.get("strip_ground_truth_at_inference", []))
        expected_leakage_keys = {
            "scenario_metadata.injected_failure_class",
            "scenario_metadata.injected_root_cause",
            "scenario_metadata.expected_relevant_doc_ids",
            "scenario_metadata.qrels_relevant_doc_ids",
            "scenario_metadata.split_group_key",
            "scenario_metadata.is_seeded_failure",
            "scenario_metadata.expected_critical_policy_result",
            "source_metadata.is_poisoned_test_doc",
            "qrel_grade",
            "fixture_provenance expectations",
            "historical_or_prepopulated_evaluator_outputs",
        }
        self.assertTrue(
            expected_leakage_keys.issubset(strip_keys),
            f"Missing required leakage stripping keys: {expected_leakage_keys - strip_keys}",
        )

    # 15. Internal Markdown links and cross-file references
    def test_repository_markdown_links_and_review_invariants(self) -> None:
        doc_targets = [
            ("docs/architecture/annotation-guide.md", "annotation-guide.md"),
            ("docs/architecture/evaluation-pipeline.md", "evaluation-pipeline.md"),
            ("docs/architecture/trace-evidence-requirements.md", "trace-evidence-requirements.md"),
            ("research/README.md", "README (1).md"),
            ("packages/reliability-engine/README.md", "README.md"),
            ("docs/team/week1-s1-03-index-and-handoff.md", "week1-s1-03-index-and-handoff.md"),
        ]
        this_dir = Path(__file__).resolve().parent
        for can_rel, loc_name in doc_targets:
            try:
                md_path = _resolve_target_file(can_rel, loc_name)
            except FileNotFoundError:
                continue
            content = md_path.read_text(encoding="utf-8")
            self.assertNotIn("https://www.google.com/search?q=", content)
            self.assertNotIn("suspicious link removed", content)
            for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
                target = match.group(2).strip()
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                rel_file = target.split("#", 1)[0]
                resolved = (md_path.parent / rel_file).resolve()
                rel_name = Path(rel_file).name
                link_valid = resolved.exists()
                if not link_valid:
                    if (this_dir / rel_name).is_file():
                        link_valid = True
                    elif rel_name == "README.md" and (
                        (this_dir / "README.md").is_file() or (this_dir / "README (1).md").is_file()
                    ):
                        link_valid = True
                self.assertTrue(
                    link_valid,
                    f"Broken relative link {target!r} in {md_path.name} -> {resolved}",
                )

    # Additional contract checks preserved and aligned with Schema v1.18 Draft
    def test_conditional_tool_call_evidence_on_blocked_proposals(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        uc_evidence = " ".join(classes_by_id["UNSUPPORTED_COMPLETION"]["required_trace_evidence"])
        self.assertIn("conditional", uc_evidence)
        self.assertIn("action_verdict == 'ALLOW'", uc_evidence)

    def test_expected_evaluator_signals_use_canonical_family_names(self) -> None:
        for spec in self.taxonomy["primary_classes"]:
            signals = spec.get("expected_evaluator_signals", {})
            self.assertIsInstance(signals, dict)
            self.assertGreaterEqual(len(signals), 1)
            for family_key in signals:
                self.assertIn(
                    family_key,
                    EXPECTED_EVALUATOR_FAMILIES,
                    f"Invalid evaluator family key '{family_key}' in {spec['class_id']}",
                )

    def test_same_tier_tie_breaker_rule_present(self) -> None:
        gov = self.taxonomy.get("governance_rules", {})
        tie_breaker = gov.get("same_tier_tie_breaker", {})
        self.assertEqual(tie_breaker.get("rule_id"), "TB-SAME-TIER-V1")
        steps = tie_breaker.get("steps", [])
        self.assertEqual([s["step"] for s in steps], [1, 2, 3, 4])
        tiers = {t["tier"]: t["classes"] for t in gov.get("precedence_hierarchy", [])}
        self.assertEqual(
            tiers[3],
            ["TOOL_SELECTION_ERROR", "WORKFLOW_VIOLATION", "INVALID_TOOL_ARGUMENTS"],
        )
        self.assertEqual(
            tiers[5],
            ["UNSUPPORTED_COMPLETION", "HALLUCINATION"],
        )

    def test_contract_validators_and_mrr_at_3_documented(self) -> None:
        eval_doc = _resolve_target_file(
            "docs/architecture/evaluation-pipeline.md", "evaluation-pipeline.md"
        ).read_text(encoding="utf-8")
        self.assertIn("FailureClass.NORMAL in self.secondary_findings", eval_doc)
        self.assertIn("len(self.secondary_findings) != len(set(self.secondary_findings))", eval_doc)
        self.assertIn("self.is_normal_trace != expected_normal", eval_doc)
        self.assertIn("expected_ranks = list(range(1, len(self.top_3_candidates) + 1))", eval_doc)
        self.assertIn("len(causes) != len(set(causes))", eval_doc)

        research_doc = _resolve_target_file("research/README.md", "README (1).md").read_text(
            encoding="utf-8"
        )
        self.assertIn("MRR@3", research_doc)
        self.assertIn("top_3_candidates", research_doc)

        trace_doc = _resolve_target_file(
            "docs/architecture/trace-evidence-requirements.md", "trace-evidence-requirements.md"
        ).read_text(encoding="utf-8")
        self.assertIn("NEVER emitted or required on pre-execution blocked proposals", trace_doc)
        self.assertIn("14", trace_doc)

        annot_doc = _resolve_target_file(
            "docs/architecture/annotation-guide.md", "annotation-guide.md"
        ).read_text(encoding="utf-8")
        self.assertIn("TB-SAME-TIER-V1", annot_doc)
        self.assertIn("EX-11", annot_doc)
        self.assertIn("tr_proc_130", annot_doc)

    def test_schema_v1_18_taxonomy_invariants(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        uc = classes_by_id["UNSUPPORTED_COMPLETION"]
        uc_text = (
            uc["formal_definition"]
            + " "
            + " ".join(uc["inclusion_criteria"])
            + " "
            + " ".join(uc["required_trace_evidence"])
        )
        self.assertIn("side_effect_state", uc_text)
        self.assertIn("result_payload.status", uc_text)
        self.assertIn("recovery_check", uc_text)
        self.assertIn("tool_suppression", uc_text)
        self.assertIn("execution_started", uc_text)
        self.assertIn("tool_dispatched", uc_text)

        rf = classes_by_id["RETRIEVAL_FAILURE"]
        rf_text = (
            rf["formal_definition"]
            + " "
            + " ".join(rf["inclusion_criteria"])
            + " "
            + " ".join(rf["required_trace_evidence"])
        )
        self.assertIn("execution_status", rf_text)
        self.assertIn("evidence_sufficiency", rf_text)
        self.assertIn("INSUFFICIENT_MISSING_REQUIRED_FACET", rf_text)
        self.assertIn("relevance_cutoff", rf_text)
        self.assertIn("configured_score_cutoff", rf_text)

        wv = classes_by_id["WORKFLOW_VIOLATION"]
        wv_text = (
            wv["formal_definition"]
            + " "
            + " ".join(wv["inclusion_criteria"])
            + " "
            + " ".join(wv["required_trace_evidence"])
        )
        self.assertIn("app_state", wv_text)
        self.assertIn("tool_suppression", wv_text)
        self.assertIn("suppression_source", wv_text)
        self.assertIn("PRE_TOOL_POLICY_GATE", wv_text)
        self.assertIn("POLICY_CHECK_ERROR_OR_TIMEOUT", wv_text)
        self.assertIn("blocking_check_id", wv_text)
        self.assertIn("blocking_policy_ids", wv_text)
        self.assertIn("side_effect_state", wv_text)

    # 17. Schema v1.18 retrieval fault contract & Dataset v1 boundary preservation
    def test_schema_v1_18_retrieval_fault_contract(self) -> None:
        """Verify that Schema v1.18 retrieval fault semantics do not alter Dataset v1 scope or add unapproved classes."""
        gov = self.taxonomy.get("governance_rules", {})
        ds_v1 = gov.get("dataset_v1_scope", {})
        frozen = ds_v1.get("frozen_classes", [])
        self.assertEqual(tuple(frozen), EXPECTED_DATASET_V1_CLASSES)

        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        rf = classes_by_id["RETRIEVAL_FAILURE"]
        rf_text = " ".join(rf["boundary_rules"])
        self.assertIn("RETRIEVAL_TIMEOUT", rf_text)
        self.assertIn("VECTOR_STORE_OR_SQL_ERROR", rf_text)
        self.assertIn("EMBEDDING_PROVIDER_ERROR", rf_text)
        self.assertIn("CORPUS_INTEGRITY_OR_PIN_MISMATCH_ERROR", rf_text)
        self.assertIn("INCOMPLETE", rf_text)
        self.assertIn("INCONCLUSIVE_TECHNICAL_ERROR", rf_text)

        # Confirm no operational fault classes were added as primary taxonomy classes
        all_class_ids = set(c["class_id"] for c in self.taxonomy["primary_classes"])
        self.assertEqual(all_class_ids, set(EXPECTED_CLASS_IDS))

    # 18. Canonical Citation Identity, Field Paths & Alias Exclusion (Schema v1.18 §4.4.4, §4.5, week_2.md §10)
    def test_canonical_citation_identity_and_field_paths(self) -> None:
        """Verify exact canonical citation fields, six-part identity tuple, and exclusion of unsupported aliases."""
        taxonomy_text = self.taxonomy_text

        # Verify unsupported aliases are strictly excluded
        self.assertNotIn(
            "retrieval_chunk_id",
            taxonomy_text,
            "Unsupported alias 'retrieval_chunk_id' found in taxonomy.",
        )
        self.assertNotIn(
            "source_retrieval_chunk_id",
            taxonomy_text,
            "Unsupported alias 'source_retrieval_chunk_id' found in taxonomy.",
        )

        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        halluc_ev = " ".join(classes_by_id["HALLUCINATION"]["required_trace_evidence"])

        # Canonical retrieved_documents fields
        self.assertIn("doc_id", halluc_ev)
        self.assertIn("doc_version", halluc_ev)
        self.assertIn("chunk_id", halluc_ev)
        self.assertIn("content_snippet", halluc_ev)
        self.assertIn("content_hash", halluc_ev)

        # Canonical retrieval attributes
        self.assertIn("source_snapshot_id", halluc_ev)
        self.assertIn("retrieval_id", halluc_ev)

        # Canonical visible_citations fields
        for cit_field in [
            "cited_doc_id",
            "cited_doc_version",
            "cited_chunk_id",
            "cited_snapshot_id",
            "cited_content_hash",
            "cited_source_id",
            "present_in_selected_context",
        ]:
            self.assertIn(
                cit_field, halluc_ev, f"Missing canonical visible_citations field: {cit_field}"
            )

        # Canonical source_evidence_spans fields
        for span_field in [
            "retrieval_id",
            "source_snapshot_id",
            "doc_id",
            "chunk_id",
            "source_char_span",
            "slice_relative_char_span",
            "source_text_basis",
            "source_quote",
            "in_supplied_prompt_context",
        ]:
            self.assertIn(
                span_field,
                halluc_ev,
                f"Missing canonical source_evidence_spans field: {span_field}",
            )

        # Six-part canonical citation identity tuple
        self.assertIn(
            "(retrieval_id, cited_snapshot_id, cited_doc_id, cited_doc_version, cited_chunk_id, cited_content_hash)",
            halluc_ev,
        )

    # 19. Canonical Approval Base Subset (17 Fields) & Provisional Boundary Verification (week_2.md §18, Trace Schema v1.18 Draft)
    def test_approval_base_subset_and_provisional_boundary(self) -> None:
        """Verify the 17-field canonical Approval base contract on Row 9 & Family 5,

        the narrower per-class classification minimum on POLICY_VIOLATION, bound_amount vs approved_amount_ceiling,
        retirement of approved_amount_limit, placement of authorization_snapshot on policy_check,
        exclusion of provisional OD-04 / SA-03 fields from S1-03 base evidence, and Row 9 non-ratified status.
        """
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        pv = classes_by_id["POLICY_VIOLATION"]
        pv_ev = " ".join(pv["required_trace_evidence"])
        pv_rules = " ".join(pv["boundary_rules"])
        pv_criteria = " ".join(pv["inclusion_criteria"])
        self.assertTrue(
            len(pv_criteria) > 0, "POLICY_VIOLATION inclusion_criteria cannot be empty."
        )

        # 1. Per-class classification minimum on POLICY_VIOLATION required_trace_evidence
        self.assertIn(
            "approval.attributes.{approval_status, bound_amount, approved_amount_ceiling}", pv_ev
        )
        self.assertIn("bound_amount", pv_ev)
        self.assertIn("approved_amount_ceiling", pv_ev)
        self.assertIn("conditional", pv_ev.lower())

        # 2. approved_amount_limit is explicitly retired and NOT an active canonical field
        self.assertNotIn(
            "approved_amount_limit",
            pv_ev,
            "Retired 'approved_amount_limit' found in required_trace_evidence.",
        )

        # 3. authorization_snapshot is NOT on approval.attributes; it resides on policy_check.attributes
        self.assertNotIn(
            "approval.attributes.{approval_id, approval_status, approver_role, approved_amount_limit, approval_timestamp, authorization_snapshot}",
            pv_ev,
        )
        self.assertIn(
            "policy_check.attributes.{evaluated_policies, action_verdict, verdict_basis, authorization_snapshot}",
            pv_ev,
        )

        # 4. Provisional OD-04 / SA-03 fields excluded from S1-03 base evidence
        provisional_fields = [
            "record_version",
            "decision_record_seq",
            "supersedes_approval_id",
            "superseded_by_approval_id",
        ]
        for pf in provisional_fields:
            self.assertNotIn(
                pf,
                pv_ev,
                f"Provisional field '{pf}' must not appear in S1-03 base required_trace_evidence.",
            )

        # 5. Verify the intentional distinction between the 17-field Base Event Envelope Contract
        # and the narrower POLICY_VIOLATION classification minimum
        self.assertIn(
            "POLICY_VIOLATION Classification Minimum vs. 17-Field Base Event Envelope Contract",
            pv_rules,
        )

        # 6. Verify trace-evidence-requirements.md Row 9 defines all 17 base fields & remains Draft / pending sign-off
        req_doc_path = os.path.join(os.path.dirname(__file__), "trace-evidence-requirements.md")
        if not os.path.exists(req_doc_path):
            req_doc_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "docs",
                "architecture",
                "trace-evidence-requirements.md",
            )
        if os.path.exists(req_doc_path):
            with open(req_doc_path, encoding="utf-8") as f:
                doc_text = f.read()

            # Row 9 defines the exact 17 canonical base fields
            expected_17_fields = [
                "approval_id",
                "approval_request_id",
                "request_id",
                "bound_calculation_ref",
                "bound_request_revision",
                "bound_supplier_id",
                "bound_amount",
                "bound_currency",
                "approved_amount_ceiling",
                "approval_level",
                "policy_id",
                "policy_version",
                "approval_status",
                "approver_id",
                "approver_role",
                "approval_timestamp",
                "trusted_source",
            ]
            self.assertEqual(len(expected_17_fields), 17)
            for field in expected_17_fields:
                self.assertIn(field, doc_text, f"Row 9 missing canonical base field '{field}'.")

            # Row 9 must NOT claim Ratified
            self.assertNotIn("Ratified (Schema v1.10", doc_text)
            self.assertIn(
                "DRAFT / ALIGNED TO SHARED TOOL CONTRACT (479cab0) — PENDING SCOPED OWNER SIGN-OFF",
                doc_text,
            )
            self.assertIn(
                "OD-04 / SA-03 / RC-07 Approval Authority & Record Supersession remain **BLOCKED — AWAITING EXPLICIT JOINT DECISION**",
                doc_text,
            )
            self.assertIn("--approval-validation-profile base_only", doc_text)

            # Documented 14/17 validator coverage limitation without downgrading mandatory contract fields
            self.assertIn("14 of the 17 fields", doc_text)
            self.assertIn("coverage limitation", doc_text)

        # 7. Verify evaluation-pipeline.md §3.2 Family 5 preserves all 17 base fields
        eval_doc_path = os.path.join(os.path.dirname(__file__), "evaluation-pipeline.md")
        if not os.path.exists(eval_doc_path):
            eval_doc_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "docs",
                "architecture",
                "evaluation-pipeline.md",
            )
        if os.path.exists(eval_doc_path):
            with open(eval_doc_path, encoding="utf-8") as f:
                eval_text = f.read()
            for field in expected_17_fields:
                self.assertIn(
                    field,
                    eval_text,
                    f"Family 5 evaluator input missing canonical base field '{field}'.",
                )


if __name__ == "__main__":
    unittest.main()
