# TrustOps AI — Reliability Engine (`trustops_reliability`)

**Canonical Path:** `packages/reliability-engine/README.md`  
**Package Namespace:** `trustops_reliability` (`packages/reliability-engine/src/trustops_reliability/`)  
**Primary Owner (R/A):** Ahmed Ragab (`AI Reliability & Machine Learning Engineer`)  
**Current Milestone:** Sprint 1, Week 1 (`Task S1-03` — Freeze Failure Taxonomy & Evaluator Contracts, `Epic TAI-EP03`)  
**Status:** **DRAFT — Awaiting Team Review**

## 1. Purpose & Architectural Boundaries

`packages/reliability-engine` is the single logical home in the TrustOps AI monorepo for:

1. **Failure Taxonomy Authority (`taxonomy/`):** Declarative specification, loading, and validation of `NORMAL` plus the eight approved primary failure classes and nine fixed root-cause candidates.
2. **Multi-Family Evaluation (`evaluation/` & `security/`):** Versioned deterministic, RAG, semantic/LLM-as-a-judge, security, agent/workflow, and policy-conformance evaluators.
3. **Structured Feature Engineering (`feature_engineering/`):** Leakage-safe conversion of raw trace events and evaluator findings into versioned tabular feature vectors.
4. **Failure Classification (`classification/`):** Interpretable deterministic rules (`rules.py`), multinomial Logistic Regression (`logistic_regression.py`), and `XGBoost` (`xgboost.py`).
5. **Evidence-Based Root-Cause Analysis (`rca/`):** Interpretable Top-1 and Top-3 root-cause ranking using weighted supporting and contradictory evaluator evidence (`uncalibrated_evidence_score`).

### Dependency Direction (Repository Architecture Rules 1, 3, 4 & 9)

- `trustops_reliability` depends **only** on canonical cross-module contracts in `packages/contracts` (`trustops_contracts`).
- `trustops_reliability` **never** imports from `apps/` (`procurement-agent`, `rag-assistant`, `api`, `dashboard`), `packages/governance-engine`, or `packages/mlops`.
- Cross-module Pydantic contracts (`evaluations.py`, `failures.py`, `rca.py`) live in `packages/contracts/src/trustops_contracts/` (owned by Mohab Mohsen) and are proposed via cross-team review rather than duplicated or modified unilaterally.
- The `PASS / REVIEW / BLOCK` reliability decision engine lives exclusively in `packages/governance-engine/src/trustops_governance/decision/` (owned by Mohamed Elnaggar).

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
    │       ├── semantic_judge.py          # [Sprint 3 S3-02 Scope — Family 3: Semantic/LLM (Proposed Path)]
    │       ├── policy_conformance.py      # [Sprint 3 S3-02 Scope — Family 6: Policy Conformance (Proposed Path)]
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
| `src/trustops_reliability/taxonomy/validation.py` | Ahmed Ragab | Sprint 1, Week 2 (`S1-03` / `S2-03` bridge) | • Exposes deterministic taxonomy and non-leakage validators:<br>  1. `validate_primary_and_secondary_labels(primary: FailureClass, secondary: list[FailureClass]) -> ValidationResult`: Enforces that `NORMAL` has `secondary == []`, `primary not in secondary`, and Precedence Tiers 1–5 are respected.<br>  2. `validate_ground_truth_independence(label_record: dict) -> ValidationResult`: Rejects any dataset label record whose `label_provenance` cites an automated evaluator, LLM judge, or classifier output.<br>  3. `validate_inference_trace_stripped(trace_dict: dict) -> ValidationResult`: Asserts that all `scenario_metadata` ground-truth keys listed in `governance_rules.strip_ground_truth_at_inference` have been removed prior to feature extraction or security evaluation. |

## 4. Related Authoritative Documentation

- **Declarative Taxonomy & RCA Spec:** [`../../src/trustops_reliability/taxonomy/failure_taxonomy.yaml`](../../src/trustops_reliability/taxonomy/failure_taxonomy.yaml)
- **Evaluation Pipeline, Taxonomy, Evaluator Contracts & RCA Specification:** [`../../docs/architecture/evaluation-pipeline.md`](../../docs/architecture/evaluation-pipeline.md)
- **Annotation Guide & Worked Examples (`EX-01` to `EX-11`):** [`../../docs/architecture/annotation-guide.md`](../../docs/architecture/annotation-guide.md)
- **Trace Evidence Requirements & Teammate Interface Contracts:** [`../../docs/architecture/trace-evidence-requirements.md`](../../docs/architecture/trace-evidence-requirements.md)
- **Research Protocol (`RQ1–RQ4` & Ablations `ABL-01` to `ABL-05`):** [`../../research/README.md`](../../research/README.md)
- **Week 1 Execution Index & Handoff Package:** [`../../docs/team/week1-s1-03-index-and-handoff.md`](../../docs/team/week1-s1-03-index-and-handoff.md)
- **Unit Validation Tests:** [`../../tests/unit/reliability_engine/test_failure_taxonomy_yaml.py`](../../tests/unit/reliability_engine/test_failure_taxonomy_yaml.py)
