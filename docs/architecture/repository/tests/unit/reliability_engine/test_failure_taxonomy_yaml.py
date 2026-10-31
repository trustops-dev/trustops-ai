"""Minimal Week 1 validation tests for declarative failure_taxonomy.yaml (Task S1-03).

Canonical Path:
    tests/unit/reliability_engine/test_failure_taxonomy_yaml.py
Owner:
    Ahmed Ragab (AI Reliability & Machine Learning Engineer)

Validates the declarative YAML specification without prematurely implementing
Week 2+ runtime loader, evaluator, classifier, or RCA modules. Compatible with
both `pytest` (in GitHub Actions `ci-python.yml`) and `python3 -m unittest`.
"""

from __future__ import annotations

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


def _resolve_taxonomy_yaml_path() -> Path:
    """Locate failure_taxonomy.yaml relative to repository root or test directory."""
    repo_root = Path(__file__).resolve().parents[3]
    canonical = (
        repo_root
        / "packages"
        / "reliability-engine"
        / "src"
        / "trustops_reliability"
        / "taxonomy"
        / "failure_taxonomy.yaml"
    )
    if canonical.is_file():
        return canonical
    pkg_root_candidate = repo_root / "packages" / "reliability-engine" / "failure_taxonomy.yaml"
    if pkg_root_candidate.is_file():
        return pkg_root_candidate
    fallback = Path(__file__).resolve().parent / "failure_taxonomy.yaml"
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(f"Could not locate failure_taxonomy.yaml at {canonical}")


class TestFailureTaxonomyYaml(unittest.TestCase):
    """Contract and structural tests for failure_taxonomy.yaml."""

    taxonomy: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        yaml_path = _resolve_taxonomy_yaml_path()
        with yaml_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        assert isinstance(loaded, dict), "failure_taxonomy.yaml root must be a mapping."
        cls.taxonomy = loaded

    def test_top_level_version_and_governance_invariants(self) -> None:
        self.assertEqual(self.taxonomy.get("schema_version"), "1.0.0")
        self.assertEqual(self.taxonomy.get("status"), "DRAFT_AWAITING_TEAM_REVIEW")
        gov = self.taxonomy.get("governance_rules", {})
        self.assertIs(gov.get("single_primary_label_per_trace"), True)
        self.assertIs(gov.get("allow_secondary_findings"), True)
        self.assertIs(gov.get("secondary_findings_never_override_primary_label"), True)
        self.assertIs(gov.get("evaluator_output_never_used_as_ground_truth"), True)
        self.assertIs(gov.get("llm_judge_is_fallible_signal_only"), True)
        strip_keys = gov.get("strip_ground_truth_at_inference", [])
        self.assertIn("scenario_metadata.injected_failure_class", strip_keys)
        self.assertIn("scenario_metadata.injected_root_cause", strip_keys)

    def test_exactly_nine_unique_primary_classes_and_numeric_codes(self) -> None:
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

    def test_nine_rca_candidates_and_referential_integrity(self) -> None:
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

    def test_conditional_tool_call_evidence_on_blocked_proposals(self) -> None:
        classes_by_id = {c["class_id"]: c for c in self.taxonomy["primary_classes"]}
        uc_evidence = " ".join(classes_by_id["UNSUPPORTED_COMPLETION"]["required_trace_evidence"])
        self.assertIn("conditional", uc_evidence)
        self.assertIn("pre_tool_verdict == 'ALLOW'", uc_evidence)

    def test_repository_markdown_links_and_review_invariants(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        md_paths = [
            repo_root / "docs/architecture/annotation-guide.md",
            repo_root / "docs/architecture/evaluation-pipeline.md",
            repo_root / "docs/architecture/trace-evidence-requirements.md",
            repo_root / "research/README.md",
            repo_root / "packages/reliability-engine/README.md",
            repo_root / "docs/team/week1-s1-03-index-and-handoff.md",
        ]
        for md_path in md_paths:
            if not md_path.is_file():
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
                self.assertTrue(
                    resolved.exists(),
                    f"Broken relative link {target!r} in {md_path.name} -> {resolved}",
                )

    def test_contract_validators_and_mrr_at_3_documented(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        eval_doc = (repo_root / "docs/architecture/evaluation-pipeline.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("FailureClass.NORMAL in self.secondary_findings", eval_doc)
        self.assertIn("len(self.secondary_findings) != len(set(self.secondary_findings))", eval_doc)
        self.assertIn("self.is_normal_trace != expected_normal", eval_doc)
        self.assertIn("expected_ranks = list(range(1, len(self.top_3_candidates) + 1))", eval_doc)
        self.assertIn("len(causes) != len(set(causes))", eval_doc)

        research_doc = (repo_root / "research/README.md").read_text(encoding="utf-8")
        self.assertIn("MRR@3", research_doc)
        self.assertIn("top_3_candidates", research_doc)

        trace_doc = (repo_root / "docs/architecture/trace-evidence-requirements.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("NEVER emitted or required on pre-execution blocked proposals", trace_doc)
        self.assertIn("14", trace_doc)

        annot_doc = (repo_root / "docs/architecture/annotation-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("TB-SAME-TIER-V1", annot_doc)
        self.assertIn("EX-11", annot_doc)
        self.assertIn("tr_proc_130", annot_doc)


if __name__ == "__main__":
    unittest.main()
