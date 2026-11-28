# TrustOps AI — Reliability Engine (`trustops_reliability`) (Trace Schema v1.18 Draft Alignment)

**Canonical Path:** `packages/reliability-engine/README.md`  
**Package Namespace:** `trustops_reliability` (`packages/reliability-engine/src/trustops_reliability/`)  
**Primary Owner (R/A):** Ahmed Ragab (`AI Reliability & Machine Learning Engineer`)  
**Current Milestone:** Sprint 1, Week 1 (`Task S1-03` — Freeze Failure Taxonomy & Evaluator Contracts, `Epic TAI-EP03`)  
**Status:** **DRAFT — Awaiting Team Review** (Aligned with Trace Schema v1.18 Draft)  
**Schema & Decision Alignment:** Trace Schema v1.18 Draft (`updated_schemas_v18.md`, Package Release `v1.18.0`, Validator Component `1.11.0 (v1.18)`), Alaa's Dataset & Experiment Requirements Matrix v2.4, Mohamed's sent scoped Governance disposition (PR #28 Rev 0.6 + Nov 13 addendum), and open decisions candidate (`open-decisions.md`)  
**Specification Scope Note:** This package documentation defines the declarative Week 1 specification and cross-team integration contracts. It does **not** claim runtime implementation of Week 2+ loader, validator, evaluator, classifier, or RCA modules.

## 1. Purpose & Architectural Boundaries

`packages/reliability-engine` is the single logical home in the TrustOps AI monorepo for:

1. **Failure Taxonomy Authority (`taxonomy/`):** Declarative specification, loading, and validation of `NORMAL` plus the eight approved primary failure classes (`RETRIEVAL_FAILURE`, `HALLUCINATION`, `TOOL_SELECTION_ERROR`, `INVALID_TOOL_ARGUMENTS`, `WORKFLOW_VIOLATION`, `POLICY_VIOLATION`, `PROMPT_INJECTION`, `UNSUPPORTED_COMPLETION`) and nine fixed root-cause candidates (`prompt`, `retriever`, `retrieved_context`, `model_generation`, `tool_selection`, `tool_arguments`, `agent_workflow`, `policy_configuration`, `malicious_input`), incorporating qualitative facet sufficiency, deterministic context formatting, verifiable citation provenance, `tool_suppression`, and `recovery_check`.
   - **Dataset v1 Scope:** Dataset v1 is frozen strictly on `NORMAL` and four Sprint 3 failure classes (`WORKFLOW_VIOLATION`, `INVALID_TOOL_ARGUMENTS`, `RETRIEVAL_FAILURE`, `UNSUPPORTED_COMPLETION`). Later-version classes belong to later versioned datasets with independently frozen splits.
2. **Multi-Family Evaluation (`evaluation/` & `security/`):** Versioned deterministic, RAG, semantic/LLM-as-a-judge, security, agent/workflow, and policy-conformance evaluators.
   - Evaluator execution statuses: `COMPLETED`, `SKIPPED_NOT_APPLICABLE`, `EVALUATOR_TECHNICAL_ERROR`, `INCOMPLETE_TRACE_EVIDENCE`.
   - Traces with incomplete trace evidence map to reliability gate outcome `INCOMPLETE`, reported separately and excluded from regression-catch-rate and false-block-rate denominators.
   - Technical failures (`EVALUATOR_TECHNICAL_ERROR`) produce `INCONCLUSIVE_TECHNICAL_ERROR` results, strictly distinguished from annotator disagreement.
3. **Structured Feature Engineering (`feature_engineering/`):** Leakage-safe conversion of raw trace events and evaluator findings into versioned tabular feature vectors after stripping all ground-truth scenario metadata (`OD-13` provisional reference per Schema v1.18 §9.2, Matrix v2.4).
   - `split_group_key` is strictly excluded from inference projections and must never be used as a model feature.
4. **Failure Classification (`classification/`):** Interpretable deterministic rules (`rules.py`), multinomial Logistic Regression (`logistic_regression.py`), and `XGBoost` (`xgboost.py`).
5. **Evidence-Based Root-Cause Analysis (`rca/`):** Interpretable Top-1 and Top-3 root-cause ranking using weighted supporting and contradictory evaluator evidence (`uncalibrated_evidence_score`).
   - Normal business rejection (SC-03A) is `NORMAL` and requires no RCA.
   - Boundary fixture SC-03B RCA remains open under OD-09 and joint review.
   - A correct policy `BLOCK` or `PREVENTED` outcome is never a `policy_configuration` RCA (EC-11 affirmative re-derivation required).

### Four Distinct Data Boundaries (Alaa Matrix v2.4 Alignment)

To prevent data leakage and conflating raw telemetry with evaluation or governance records, four distinct data boundaries are strictly maintained:
1. **Raw Event Stream:** Immutable runtime telemetry emitted by application and platform SDKs.
2. **Scenario Metadata:** Scenario generation provenance and seeded failure metadata, strictly stripped before inference.
3. **`adjudication_records` (Offline Sidecar):** Offline human consensus ground-truth records, distinct from raw traces and distinct from Mohamed's production `human_review_record`.
4. **`evaluator_results` (Evaluation Run Outputs):** Outputs of active evaluator runs, scoped to `evaluation_run_id` and `trace_id`.

### Canonical Contract & Field Names (Trace Schema v1.18 Draft Alignment)

- **Approval Base Subset & Validator Profile Boundary (`week_2.md §18`):** S1-03 evaluator contracts are scoped to the exact 17 canonical base fields of `approval.attributes` (`approval_id`, `approval_request_id`, `request_id`, `bound_calculation_ref`, `bound_request_revision`, `bound_supplier_id`, `bound_amount`, `bound_currency`, `approved_amount_ceiling`, `approval_level`, `policy_id`, `policy_version`, `approval_status`, `approver_id`, `approver_role`, `approval_timestamp`, `trusted_source`). Amount ceiling constraints require `Decimal(approved_amount_ceiling) >= Decimal(bound_amount)`, while legacy `approved_amount_limit` is explicitly retired. Authorization snapshots reside exclusively on `policy_check.attributes.authorization_snapshot` (linked via `approval_evidence_ref`), never under `approval.attributes`. The four provisional OD-04 / SA-03 fields (`record_version`, `decision_record_seq`, `supersedes_approval_id`, `superseded_by_approval_id`) and supersession chains remain BLOCKED and excluded from S1-03 evaluator rules. All 17 base fields are mandatory contract members. The offline schema validator exercises this base subset under `--approval-validation-profile base_only` (verified via `POS-33`, where 14 of 17 fields trigger explicit semantic/cross-event failures upon omission, and `request_id`, `policy_id`, `approver_role` are confirmed mandatory contract fields tracked as a known v1.18 validator coverage limitation per Mohab's clarification; note that `base_only` permits optional provisional keys in its allowed-attribute definition and continues optional chronology checks if `trusted_source.verified_at` is supplied, while bypassing supersession rules). Evaluation Runtime ingestion profile wiring and SDK inference projection stripping remain pending explicit confirmation from Mohab. The full 17-field contract specifies complete event envelope syntax, whereas `POLICY_VIOLATION` classification requires only the substantive subset `{approval_status, bound_amount, approved_amount_ceiling}` (strictly conditional on the `PROC-APPROVAL-01` path).
- **Policy Check:** `policy_check.attributes.action_verdict` (`"ALLOW"`, `"BLOCK"`), `verdict_basis`, `evaluated_policies[].policy_result` and `status` (`"PASS"`, `"FAIL"`, `"NOT_APPLICABLE"`, `"ERROR"`), and `decision_config_version`. Retired legacy fields `pre_tool_verdict` and `decision_engine_version` are not used as canonical paths.
- **Distinct Version Concepts:** `policy_kb_version`/`policy_set_version` (rule definitions), `policy_bundle_version` (compiled evaluation bundle), and `decision_config_version` (gate thresholds and routing logic) remain strictly distinct.
- **Tool Lifecycle:** `tool_result.attributes.side_effect_state` (`"NONE"`, `"COMMITTED"`, `"ALREADY_EXISTING"`, `"UNKNOWN"`). Legacy `side_effect_committed` is retired.
- **RAG Provenance & Granularity:** Inspects full provenance (`retrieval_id`, `(doc_id, chunk_id, doc_version)`, `content_hash`, `canonical_chunk_slice`, `formatting_prefix_applied`, `exact_selected_text`, `rendered_context_block`, `included_in_prompt`). Citation checks prove source containment, not semantic entailment. Dataset v1 evaluation is strictly document-level (`retrieval_doc_recall_at_5`, `retrieval_doc_mrr`); chunk qrels are pending feasibility. Technical retrieval faults (`RETRIEVAL_TECHNICAL_FAULT_STATUSES`) are separated from zero hits.

### Dependency Direction (Repository Architecture Rules 1, 3, 4 & 9)

- `trustops_reliability` depends **only** on canonical cross-module contracts in `packages/contracts` (`trustops_contracts`).
- `trustops_reliability` **never** imports from `apps/` (`procurement-agent`, `rag-assistant`, `api`, `dashboard`), `packages/governance-engine`, or `packages/mlops`.
- Cross-module Pydantic contracts (`evaluations.py`, `failures.py`, `rca.py`) live in `packages/contracts/src/trustops_contracts/` (owned by Mohab Mohsen) and are proposed via cross-team review rather than duplicated or modified unilaterally.
- The `PASS / REVIEW / BLOCK` reliability decision engine lives exclusively in `packages/governance-engine/src/trustops_governance/decision/` (owned by Mohamed Elnaggar).
- **Ground-Truth Isolation Boundary (Trace Schema v1.18 Draft & Matrix v2.4):** Runtime evaluators, LLM judges, classifiers, and RCA engines consume inference projections strictly stripped of all Ground Truth evaluation-only metadata fields: `scenario_metadata.{expected_relevant_doc_ids, qrels_relevant_doc_ids, split_group_key, injected_failure_class, injected_root_cause, injection_recipe_id, is_seeded_failure, expected_critical_policy_result, is_security_subset, security_category, security_case_role, security_subset_metadata}`, `source_metadata.is_poisoned_test_doc`, `qrel_grade`, `fixture_provenance expectations`, `fixture-authored expected_* fields`, `post_run_analysis_example`, `failure_class_encoding_identifiers`, and `historical_or_prepopulated_evaluator_outputs`. Specifically:
  1. `scenario_metadata.split_group_key` must be excluded from the entire inference projection (not only classifier feature vectors) and never used as a model feature.
  2. `source_metadata.is_poisoned_test_doc`, `is_security_subset`, `security_case_role`, and `qrel_grade` must be excluded from all inference-visible runtime evaluators and LLM Judges as well as ML feature extraction.
  3. `fixture_provenance.post_run_analysis_example` must be excluded from all inference inputs.
  4. `claimed_actions.evidence_support_verdict` is not an allowed authoritative raw-trace field; raw trace capture contains only observable action and evidence linkage fields, and `deterministic_support_check` is computed post-run by the deterministic evaluator as an active evaluation-run feature.
  5. The Ground Truth field `expected_relevant_doc_ids` is removed entirely from the inference projection, while genuinely retrieved document IDs remain preserved as observable runtime evidence in `retrieval.attributes.retrieved_documents[].doc_id`. Legitimate non-evaluation provenance in `fixture_provenance` (`fixture_id`, `authored_by`, `purpose`) is preserved. Offline reference evaluation (`retrieval_doc_recall_at_5`, `retrieval_doc_mrr`) consumes ground truth post-inference only.

## 2. Canonical Package Structure

```text
packages/reliability-engine/
├── README.md
├── pyproject.toml
└── src/trustops_reliability/
    ├── __init__.py
    ├── taxonomy/
    │   ├── failure_taxonomy.yaml          # [Week 1 S1-03 Deliverable — Declarative Taxonomy & RCA Spec]
    │   ├── loader.py                      # [Week 2 S2-03 Scope — YAML loader & SHA-256 digest cache]
    │   └── validation.py                  # [Week 2 S2-03 Scope — Precedence & non-leakage validators]
    ├── evaluation/
    │   ├── engine.py                      # [Sprint 3 S3-02 Scope]
    │   ├── registry.py                    # [Sprint 3 S3-02 Scope]
    │   ├── result_aggregator.py           # [Sprint 3 S3-02 Scope]
    │   └── evaluators/
    │       ├── schema_validity.py         # [Week 2–3 Scope — Family 1: Deterministic]
    │       ├── latency_and_cost.py        # [Sprint 3 Scope — Family 1: Deterministic]
    │       ├── semantic_judge.py          # [Sprint 3 S3-02 Scope — Family 3: Semantic/LLM]
    │       ├── policy_conformance.py      # [Sprint 3 S3-02 Scope — Family 6: Policy Conformance]
    │       ├── agent/
    │       │   ├── tool_correctness.py    # [Week 3 / Sprint 3 Scope — Families 1 & 5]
    │       │   └── workflow_completion.py # [Week 3 / Sprint 3 Scope — Family 5: Agent/Workflow]
    │       └── rag/
    │           ├── groundedness.py        # [Sprint 3 S3-02 Scope — Family 2: RAG]
    │           ├── citation_correctness.py# [Sprint 3 S3-02 Scope — Family 2: RAG]
    │           └── retrieval_relevance.py # [Week 4 / Sprint 3 Scope — Family 2: RAG]
    ├── feature_engineering/               # [Sprint 4 S4-01 Scope]
    │   ├── trace_features.py
    │   ├── evaluation_features.py
    │   ├── feature_schema.py
    │   └── pipeline.py
    ├── classification/                    # [Sprint 4 S4-01 Scope]
    │   ├── interface.py
    │   ├── rules.py
    │   ├── logistic_regression.py
    │   ├── xgboost.py
    │   └── classifier_service.py
    ├── rca/                               # [Sprint 4 S4-01 Scope]
    │   ├── engine.py
    │   ├── evidence.py
    │   ├── cause_ranking.py
    │   └── explanation_builder.py
    ├── security/                          # [Sprint 3 Stub / Sprint 5 S5-01 Benchmark Scope — Family 4]
    │   ├── evaluator.py
    │   ├── metrics.py
    │   └── benchmark_runner.py
    ├── ports/
    │   ├── model_provider.py
    │   ├── evaluation_repository.py
    │   └── diagnosis_repository.py
    └── adapters/postgres/
        ├── models.py
        ├── evaluation_repository.py
        └── diagnosis_repository.py
```

## 3. Week 2 Runtime Module Design Specifications (`loader.py` & `validation.py`)

In accordance with Sprint 1 scope discipline (`S1-03`), Week 1 delivers the declarative `failure_taxonomy.yaml` specification and contract documentation, while deferring runtime Python implementation to Week 2:

| Future Runtime Module Path | Owner | Target Milestone | Intended Contract & Functional Design |
| :--- | :--- | :--- | :--- |
| `src/trustops_reliability/taxonomy/loader.py` | Ahmed Ragab | Sprint 1, Week 2 (`S1-03` / `S2-03` bridge) | • Exposes `load_failure_taxonomy(path: Path | None = None) -> FailureTaxonomySpec`.<br>• Parses `failure_taxonomy.yaml` via `yaml.safe_load`, validates against an immutable Pydantic specification, caches the parsed object with a SHA-256 content digest (`taxonomy_hash`), and provides O(1) lookup helpers (`get_class_spec(FailureClass)`, `get_rca_candidate_spec(RCACandidate)`).<br>• Pure in-memory loader with zero database or network calls. |
| `src/trustops_reliability/taxonomy/validation.py` | Ahmed Ragab | Sprint 1, Week 2 (`S1-03` / `S2-03` bridge) | • Exposes deterministic taxonomy, non-leakage, and lifecycle validators:<br>  1. `validate_primary_and_secondary_labels(primary: FailureClass, secondary: list[FailureClass]) -> ValidationResult`: Enforces that `NORMAL` has `secondary == []`, `primary not in secondary`, `secondary` has no duplicates, Precedence Tiers 1–5 are respected, and same-tier ties follow `TB-SAME-TIER-V1`.<br>  2. `validate_ground_truth_independence(label_record: dict) -> ValidationResult`: Rejects any dataset label record whose `label_provenance` cites an automated evaluator, LLM judge, or classifier output.<br>  3. `validate_inference_trace_stripped(trace_dict: dict) -> ValidationResult`: Asserts that all `scenario_metadata` ground-truth keys listed in `governance_rules.strip_ground_truth_at_inference` have been removed prior to feature extraction or security evaluation (`OD-13`).<br>  4. `validate_lifecycle_event_invariants(trace_dict: dict) -> ValidationResult`: Verifies valid lifecycle event sequencing: ensures blocked proposals emit `tool_suppression` (with canonical `suppression_source`, conditional `blocking_check_id` / `blocking_policy_ids` across all 3 cases, `execution_started: false, tool_dispatched: false, side_effect_state: "NONE"`) with no `tool_call`, allowed calls emit `tool_call` and `tool_result`, and timeouts verify `recovery_check` reconciliation semantics. |

## 4. Related Authoritative Documentation

- **Declarative Taxonomy & RCA Spec:** [`src/trustops_reliability/taxonomy/failure_taxonomy.yaml`](src/trustops_reliability/taxonomy/failure_taxonomy.yaml)
- **Evaluation Pipeline, Taxonomy, Evaluator Contracts & RCA Specification:** [`../../docs/architecture/evaluation-pipeline.md`](../../docs/architecture/evaluation-pipeline.md)
- **Annotation Guide & Worked Examples (`EX-01` to `EX-11`):** [`../../docs/architecture/annotation-guide.md`](../../docs/architecture/annotation-guide.md)
- **Trace Evidence Requirements & Teammate Interface Contracts:** [`../../docs/architecture/trace-evidence-requirements.md`](../../docs/architecture/trace-evidence-requirements.md)
- **Research Protocol (`RQ1–RQ4` & Ablations `ABL-01` to `ABL-05`):** [`../../research/README.md`](../../research/README.md)
- **Week 1 Execution Index & Handoff Package:** [`../../docs/team/week1-s1-03-index-and-handoff.md`](../../docs/team/week1-s1-03-index-and-handoff.md)
