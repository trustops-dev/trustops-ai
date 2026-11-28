# TrustOps AI — Research Protocol & Experimental Design (Trace Schema v1.18 Draft Alignment)

**Canonical Path:** `research/README.md`  
**Owners (R):** Ahmed Ragab (`packages/reliability-engine`, `research/` — Primary author for RQ1–RQ3, security metrics, and ablations) & Alaa Sayed (`packages/mlops`, `datasets/` — Co-owner for dataset splits, MLflow reproducibility, and RQ4 gate metrics)  
**Task / Epic:** `S1-03` — Freeze Failure Taxonomy & Evaluator Contracts (`TAI-EP03`, `TAI-EP11`)  
**Sprint / Week:** Sprint 1, Week 1  
**Status:** **DRAFT — Awaiting Team Review** (Aligned with Trace Schema v1.18 Draft)  
**Schema & Decision Alignment:** Trace Schema v1.18 Draft (`updated_schemas_v18.md`, Package Release `v1.18.0`, Validator Component `1.11.0 (v1.18)`), Alaa's Dataset & Experiment Requirements Matrix v2.4, Mohamed's sent scoped Governance disposition (PR #28 Rev 0.6 + Nov 13 addendum), and open decisions candidate (`open-decisions.md`)  
**Authoritative Baseline:** `TrustOps_AI_Project_Proposal.docx` (v1.1, Sections L, M, O, P, Q, S)  
**Related Documents:**
- Declarative Taxonomy YAML: [`../packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml`](../packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml)
- Evaluation Pipeline & Evaluator Contracts: [`../docs/architecture/evaluation-pipeline.md`](../docs/architecture/evaluation-pipeline.md)
- Annotation Guide & Adjudication Protocol: [`../docs/architecture/annotation-guide.md`](../docs/architecture/annotation-guide.md)
- Trace Evidence Requirements: [`../docs/architecture/trace-evidence-requirements.md`](../docs/architecture/trace-evidence-requirements.md)
- Reliability Engine Architecture: [`../packages/reliability-engine/README.md`](../packages/reliability-engine/README.md)
- Week 1 Index & Handoff: [`../docs/team/week1-s1-03-index-and-handoff.md`](../docs/team/week1-s1-03-index-and-handoff.md)

---

## 1. Overview & Scientific Falsifiability Principle

Per Proposal `Section A`, `Section L.4`, and `Section P`, TrustOps AI frames its academic contribution as **four falsifiable empirical studies (`RQ1–RQ4`)** plus **five controlled feature/signal ablations (`P.1`)**.

1. **Falsifiable Framing:** No performance target or model superiority is assumed in advance. If interpretable deterministic rules match or outperform `XGBoost` on certain failure classes, or if removing the fallible LLM-as-a-judge improves human agreement, that finding is retained and reported transparently as a valid research conclusion.
2. **Ground-Truth Isolation & Provenance Boundary:**
   - Ground-truth labels (`primary_label`, `secondary_findings`, `ground_truth_root_cause`) are stored in isolated `adjudication_records` sidecars and are never derived from or adjudicated using the predictions of the evaluator, LLM judge, or classifier under test.
   - Complete evaluation-only metadata fields—including `scenario_metadata.expected_relevant_doc_ids`, `scenario_metadata.qrels_relevant_doc_ids`, `scenario_metadata.split_group_key`, `scenario_metadata.injected_failure_class`, `scenario_metadata.injected_root_cause`, `scenario_metadata.injection_recipe_id`, `scenario_metadata.is_seeded_failure`, `scenario_metadata.expected_critical_policy_result`, `scenario_metadata.is_security_subset`, `scenario_metadata.security_category`, `scenario_metadata.security_case_role`, `scenario_metadata.security_subset_metadata`, `source_metadata.is_poisoned_test_doc`, `qrel_grade`, `fixture_provenance expectations`, `fixture-authored expected_* fields`, `post_run_analysis_example`, `failure_class_encoding_identifiers`, and `historical_or_prepopulated_evaluator_outputs`—**must be strictly excluded from runtime inference projections** (`project_trace_for_inference`) provided to evaluators, judges, classifiers, and RCA models (`OD-13` — Specified in Trace Schema v1.18 Draft — Awaiting Team Review; Matrix v2.4). Specifically:
     * `scenario_metadata.split_group_key` must be excluded from the entire inference projection and must NEVER be used as a model feature.
     * `source_metadata.is_poisoned_test_doc` and `qrel_grade` must be excluded from all inference-visible runtime evaluators, LLM Judges, and ML feature extraction.
     * `fixture_provenance.post_run_analysis_example` must be excluded from all inference inputs.
     * `claimed_actions.evidence_support_verdict` is not an allowed authoritative raw-trace field; raw traces capture only observable actions/linkage, and `deterministic_support_check` is computed post-run by the deterministic evaluator.
     * The Ground Truth field `expected_relevant_doc_ids` is removed entirely from inference projection, while genuinely retrieved document IDs remain preserved as observable runtime evidence in `retrieval.attributes.retrieved_documents[].doc_id`.
   - Legitimate non-evaluation provenance metadata in `fixture_provenance` (`fixture_id`, `authored_by`, `purpose`) and freshly computed active-run evaluator signals are preserved.
   - Isolated offline benchmark and reference metric computation (e.g., `retrieval_doc_recall_at_5`, `retrieval_doc_mrr`) consumes expected labels and qrels post-inference only.
3. **Zero Fabricated Metrics:** This Week 1 protocol defines hypotheses, datasets, controls, mathematical formulas, and statistical tests only. Actual measured figures will be populated exclusively after Sprint 4–7 experiments run against frozen datasets.

---

## 2. Detailed Experimental Protocol for RQ1–RQ4

### 2.1 RQ1 — Structured-Feature Failure Classification (`research/experiments/compare_classifiers.py`)
* **Research Question:** *Can structured execution-trace features improve AI failure classification over deterministic rules alone?*
* **Hypothesis & Comparison:**
  - Compare three models trained and evaluated on the **exact same scenario-held-out test split** (`datasets/manifests/classifier-training-v1.yaml`, `~15%` of `1,500–1,800` traces):
    1. **Model 1 (`rules.py`):** Interpretable deterministic rule baseline mapping deterministic, RAG, workflow, policy, and security thresholds directly to the taxonomy using the 5-Tier Precedence Hierarchy in [`../docs/architecture/annotation-guide.md`](../docs/architecture/annotation-guide.md).
    2. **Model 2 (`logistic_regression.py`):** Multinomial Logistic Regression (`scikit-learn`, L2-regularized, `class_weight="balanced"`, split-safe `StandardScaler` / `OneHotEncoder` fitted strictly on `train`).
    3. **Model 3 (`xgboost.py`):** Multi-class Gradient Boosted Decision Trees (`XGBClassifier`, `objective="multi:softprob"`, inverse-frequency sample weights fitted strictly on `train`, hyperparameters tuned strictly on `val`).
  - **Identical Feature Whitelist:** All three models consume the exact same structured feature whitelist extracted by `packages/mlops`. The `split_group_key` is strictly excluded from features to eliminate group-leakage risk.
  - **Dataset v1 Scope Boundary:** Dataset v1 is frozen strictly on `NORMAL` plus the four Sprint 3 failure classes: `WORKFLOW_VIOLATION`, `INVALID_TOOL_ARGUMENTS`, `RETRIEVAL_FAILURE`, and `UNSUPPORTED_COMPLETION`. Later-version classes (`HALLUCINATION`, `TOOL_SELECTION_ERROR`, reusable `POLICY_VIOLATION`, `PROMPT_INJECTION`) belong to later versioned datasets with independently frozen splits. In Dataset v1 experiments, `num_class=5` applies to the frozen v1 label set; the full 9-class model runs in later versioned benchmarks.
  - **Null Hypothesis ($H_0$):** $\text{Macro-}F_1(\text{XGBoost}) \le \text{Macro-}F_1(\text{Deterministic Rules})$ on held-out scenario templates.
  - **Alternative Hypothesis ($H_1$):** Non-linear combinations of heterogeneous trace features (`retrieval` qualitative sufficiency, context formatting invariants, `agent_state` transitions, lifecycle suppression/recovery signals, token/latency ratios, and multi-evaluator signals) yield higher Macro-$F_1$ than deterministic rules or linear Logistic Regression, particularly on multi-symptom RAG and borderline agent trajectories.
* **Required Dataset & Labels:** Frozen `classifier-training-v1.yaml` (`70% train / 15% val / 15% test` grouped split by `split_group_key`).
* **Ground-Truth Source:** Independent scenario injection metadata (`Tier 1`) verified by deterministic symptom sanity checks, plus adjudicated human labels (`Tier 2`) on the reviewed subset in `adjudication_records`. **Never** any single model's or evaluator's prediction.
* **Experimental Controls & Leakage Prevention:**
  - Grouped splitting by `split_group_key = scenario_family::question_template_id` (`tests/research/test_grouped_split_no_leakage.py`) so zero question paraphrases cross between `train`, `val`, and `test` splits (70/15/15 ratio).
  - `split_group_key` is strictly a partition grouping key; it must **never** be used as an input feature for any model.
  - Strip all `scenario_metadata` ground-truth keys (including `split_group_key`), `is_poisoned_test_doc`, and `qrel_grade` flags prior to runtime evaluation and feature extraction using `project_trace_for_inference`.
  - Fit all imputers, scalers, and categorical encoders on `train` only.
* **Feature Engineering Ingestion Groups (incorporating Trace Schema v1.18 Draft):**
  - Group 1: General trace telemetry & artifact provenance (`versions` [including distinct `policy_kb_version`, `policy_bundle_version`, `decision_config_version`], `metadata_availability`, `total_latency_ms`, `execution_status`).
  - Group 2: RAG retrieval & qualitative facet sufficiency features (`evidence_sufficiency_status`, `missing_or_unsupported_facets_count`, `context_relevance`, `similarity_score_spread`, `context_formatting_valid`; baseline cutoffs `configured_score_cutoff = null` and `relevance_cutoff = null`).
  - Group 3: Model generation & grounding features (`groundedness`, `citation_precision`, `citation_version_match_rate`, `unsupported_claim_indicator`).
  - Group 4: Agent state & tool lifecycle features (`from_app_state`, `to_app_state`, `app_state` [8 states: `REQUEST_CAPTURED`, `POLICY_CHECKED`, `SUPPLIER_CHECKED`, `APPROVAL_CALCULATED`, `APPROVAL_PENDING`, `APPROVED`, `PO_CREATION`, `COMPLETION`], `policy_stage` [4 stages: `PRE_APPROVAL`, `APPROVED`, `PO_CREATION`, `COMPLETED`], `tool_suppression_observed`, `side_effect_state` [replaces retired `side_effect_committed`], `recovery_reconciliation_status`).
  - Group 5: Policy conformance features (`policy_conformance_score`, `critical_policy_flag`, `action_verdict_observed` [replaces retired `pre_tool_verdict`], `verdict_basis_observed`, `decision_config_version`).
  - Group 6: Security features (`prompt_injection_risk_score`, `attack_verdict`, `detected_attack_category`, `behavioral_redirection_observed`).
  - Group 7: Proposed execution budget telemetry features (`budget_spent_ratio`, `retry_count`, `token_budget_consumed`, `step_budget_consumed`). **Status: `PROPOSED_NOT_RATIFIED` under `OD-12`**—ingested strictly as exploratory research inputs, not ratified gate rules.
* **Metrics & Mathematical Formulas:**
  - **Per-Class Precision ($P_c$), Recall ($R_c$), $F_{1,c}$, and Support ($N_c$)** for each class $c$:
    $$P_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}, \quad R_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}, \quad F_{1,c} = \frac{2 P_c R_c}{P_c + R_c}$$
  - **Primary Metric — Unweighted Macro-$F_1$:**
    $$\text{Macro-}F_1 = \frac{1}{|C|} \sum_{c \in C} F_{1,c}$$
    (where $|C| = 5$ for Dataset v1, $|C| = 9$ for later full-taxonomy versioned datasets).
  - **Confusion Matrix** (analyzed overall and stratified by `application_type`).
  - **Feature Importance:** Gain-based and permutation feature importance across feature groups.
  - **Statistical Comparison:** Paired bootstrap (`B = 10,000` resamples at scenario-template cluster level) for 95% confidence intervals on $\Delta \text{Macro-}F_1$, plus Stuart-Maxwell / McNemar-style paired accuracy/error discordance tests across identical test trace IDs.

---

### 2.2 RQ2 — Multi-Evaluator Combination vs. Single Semantic Judge (`RQ2` Evaluator Agreement Study)
* **Research Question:** *Does combining deterministic, retrieval, and semantic evaluation signals agree with human-reviewed labels better than a single semantic/LLM evaluator?*
* **Hypothesis & Comparison:**
  - Evaluate three evaluator strategies on the **independently human-reviewed subset** (`15–20%` of the dataset, `~225–360` traces, including the `100–150` double-annotated adjudicated traces):
    1. **Strategy A (`Semantic / LLM Judge Alone`):** Diagnosis derived solely from `semantic_judge.py` (`sem_llm_judge_correctness_v1`).
    2. **Strategy B (`Deterministic Rules + Semantic Judge`):** Combines `deterministic`, `agent_workflow`, `policy_conformance`, and `semantic_judge` (excluding `rag` retrieval/citation metrics and `security` detectors).
    3. **Strategy C (`Full Multi-Evaluator Combination`):** Combines all 6 evaluator families (`deterministic` + `rag` + `semantic_llm` + `security` + `agent_workflow` + `policy_conformance`).
* **Evaluation Record Storage:** All evaluator outputs are recorded in the canonical `evaluator_results` table, scoped by `evaluation_run_id` and `trace_id`.
* **Ground-Truth Source & Adjudication Comparison:** Performance is evaluated strictly against offline human ground-truth records stored in `adjudication_records`.
* **Primary vs. Secondary Disagreement:** The study distinguishes primary diagnosis disagreement (where evaluator verdict conflicts with `human_adjudicated_primary_label`) from secondary finding disagreements.
* **Inconclusive Technical Errors:** An evaluator throwing an unhandled exception or returning `EVALUATOR_TECHNICAL_ERROR` is classified as an `INCONCLUSIVE_TECHNICAL_ERROR` outcome, strictly separated from annotator disagreement.
* **Experimental Controls & Leakage Prevention:**
  - The LLM judge prompt and rubric (`judge_rubric_v1.0`) are frozen before running on the human-reviewed subset.
  - Human annotators are strictly blinded to the LLM judge's score and rationale.
  - In RAG evaluations, valid designated abstentions (`evidence_sufficiency.sufficiency_status == "INSUFFICIENT_NO_RELEVANT_EVIDENCE"`, `is_abstention == true`) are evaluated as `NORMAL`, preventing false judge penalties on corpus-missing queries.
* **Metrics & Mathematical Formulas:**
  - **Cohen's Kappa ($\kappa$) with Human Ground Truth:**
    $$\kappa_{\text{eval, human}} = \frac{p_o - p_e}{1 - p_e}$$
    computed both on binary failure detection (`NORMAL` vs `ANY_FAILURE`) and on categorical diagnosis.
  - **Macro-$F_1$ and Per-Class $F_1$** against human labels in `adjudication_records`.
  - **Evaluator-Human Disagreement Rate:**
    $$\text{Disagreement Rate} = \frac{1}{N_{\text{rev}}} \sum_{i=1}^{N_{\text{rev}}} \mathbb{I}\left(\hat{y}_{\text{strategy}, i} \neq y_{\text{human}, i}\right)$$
  - **False-Approval Rate on Critical Policy/Workflow Failures:** Fraction of human-confirmed `WORKFLOW_VIOLATION` / `POLICY_VIOLATION` / `UNSUPPORTED_COMPLETION` traces where `Semantic Judge Alone` awards a passing score because the final text sounds polite and plausible (`Proposal §B.3`).

---

### 2.3 RQ3 — Evidence-Based Root-Cause Analysis (`research/experiments/evaluate_rca_topk.py`)
* **Research Question:** *Can trace evidence provide useful root-cause ranking for intentionally seeded AI failures?*
* **Hypothesis & Comparison:**
  - Evaluate on all failed traces in the held-out test set that possess causal ground truth (`ground_truth_root_cause` $\in$ 9 fixed candidates):
    1. **Baseline (`Class-Only Cause Mapping`):** A static 1-to-1 lookup table that maps only the predicted `primary_label` to a fixed default ranking of causes without inspecting granular evaluator or trace evidence.
    2. **Primary Method (`Weighted Multi-Evaluator Evidence Ranker`):** Computes candidate `evidence_score`s directly from granular evaluator findings, version provenance deltas, retrieval facet sufficiency, lifecycle suppression/recovery states, and deterministic support checks (`Proposal §M.1`).
* **Preservation of RCA Candidates & Causal Ground Truth:**
  - Preserves all 9 fixed RCA candidates: `prompt`, `retriever`, `retrieved_context`, `model_generation`, `tool_selection`, `tool_arguments`, `agent_workflow`, `policy_configuration`, `malicious_input`.
  - **SC-03A Boundary:** Normal business rejection path (supplier `NOT_APPROVED`, agent halts cleanly in `POLICY_CHECKED` without PO proposal) is `NORMAL` and requires no RCA.
  - **SC-03B Boundary:** Isolated boundary test fixture (`BOUNDARY_TEST`) exercising `BLOCK` / `PREVENTED`; its classification and RCA remain open under OD-09 and joint Ahmed/Mohamed review.
  - **Missing Document Distinction:** A missing document does not automatically imply `hallucination`. If the agent abstains correctly, it is `NORMAL`; if retrieval failed, it points to `retriever`; only ungrounded fabricated claims point to `model_generation`.
  - **Policy Enforcement Distinction:** A correct policy `BLOCK` or `PREVENTED` outcome is never evidence of a `policy_configuration` RCA. Assigning `policy_configuration` requires affirmative proof of a policy defect via EC-11 re-derivation.
* **Required Dataset & Labels:** Held-out failed traces (`y != NORMAL`) with verified `ground_truth_root_cause`.
* **Ground-Truth Source:** Independent scenario `injected_root_cause` metadata (`Tier 1`) plus human causal adjudication (`Tier 2`) on ambiguous semantic failures in `adjudication_records`.
* **Metrics & Mathematical Formulas (Aligned with `RCAResult` Top-3 Contract):**
  - Because the canonical `RCAResult` contract (`packages/contracts/src/trustops_contracts/rca.py` in [`../docs/architecture/evaluation-pipeline.md`](../docs/architecture/evaluation-pipeline.md)) exposes at most 3 ranked root-cause candidates (`top_3_candidates: list[RankedCauseCandidate]` with `max_length=3`), let $r_i \in \{1, 2, 3, \infty\}$ denote the rank of the ground-truth root cause $c^*_i$ inside `RCAResult.top_3_candidates` on failed trace $i \in \{1, \dots, M\}$ (with $r_i = \infty$ whenever $c^*_i \notin \text{top\_3\_candidates}$ or `insufficient_evidence_flag == True`):
  - **Top-1 Accuracy (`Top-1 Acc`):**
    $$\text{Top-1 Acc} = \frac{1}{M} \sum_{i=1}^{M} \mathbb{I}(r_i == 1)$$
  - **Top-3 Recall (`Top-3 Recall`):**
    $$\text{Top-3 Recall} = \frac{1}{M} \sum_{i=1}^{M} \mathbb{I}(r_i \le 3)$$
  - **Truncated Mean Reciprocal Rank at 3 (`MRR@3`, Primary Contract-Backed Ranking Metric):**
    $$\text{MRR@3}_{\text{RCA}} = \frac{1}{M} \sum_{i=1}^{M} \begin{cases} \frac{1}{r_i} & \text{if } r_i \in \{1, 2, 3\} \\ 0 & \text{if } r_i = \infty \text{ (not in } \text{top\_3\_candidates} \text{ or insufficient\_evidence\_flag=True)} \end{cases}$$
    *Contract Alignment Rule:* All benchmark tables, quality gates, and ablation comparisons consuming `RCAResult` objects MUST report **`MRR@3`** and explicitly state that reciprocal ranks beyond rank 3 contribute $0$. It must never be labeled as unrestricted 9-candidate `MRR`.
  - **Full-Taxonomy Uncut `MRR@9` (Optional Offline Diagnostic Only):** Offline research scripts in `research/experiments/evaluate_rca_topk.py` that directly inspect the internal pre-truncation score vector across all 9 `RCACandidate` values before constructing `RCAResult` may optionally log uncut $\text{MRR@9} = \frac{1}{M}\sum_{i=1}^{M} \frac{1}{r_i^{(1..9)}}$ as a secondary diagnostic column, clearly labeled `MRR@9 (pre-truncation diagnostic)`.

---

### 2.4 RQ4 — CI/CD Release Quality Gate & Regression Detection (`research/experiments/calibrate_decision_thresholds.py` & `packages/mlops/regression/runner.py`)
* **Research Question:** *Can trace-based evaluation detect deliberately introduced prompt/retrieval/agent regressions before release?*
* **Hypothesis & Comparison:**
  - Co-led with **Alaa Sayed (`S5-03`, `S7-02`)** and **Mohamed Elnaggar (`S5-04`)**. Execute the frozen regression validation suite (`datasets/manifests/regression-validation-v1.yaml`) across:
    1. **Approved Baseline Configuration:** Known-good `proc_v5` + `rag_v6` + `retriever_v2` + `proc_policies_v1.0`.
    2. **Seeded Regression Candidates (`Proposal §S.3`):**
       - *Candidate R1 (Procurement Prompt Regression):* Weakens approval-before-action guidance (`proc_v6_candidate`).
       - *Candidate R2 (RAG Retriever Regression):* Degrades top-$k$ / embedding retrieval or removes critical policy evidence (`retriever_v4`).
       - *Candidate R3 (Agent Tool/Argument Regression):* Alters tool schema binding or stage transition handling.
    3. **Benign Non-Regression Candidates (False-Block Controls):** Minor prompt wording paraphrases or benign configuration updates that preserve reliability semantics and should resolve to `PASS` (or `REVIEW` at most, never `BLOCK`).
* **Dataset Manifest Invariance:** Baseline and candidate runs must be evaluated on the **exact same dataset manifest** to ensure valid comparative deltas.
* **Incomplete Trace Handling:** Traces with incomplete evidence (`INCOMPLETE_TRACE_EVIDENCE`) map to gate outcome `INCOMPLETE`. They are reported separately and **strictly excluded from regression-catch-rate and false-block-rate denominators**.
* **Retrieval Evaluation Granularity:** In Dataset v1, retrieval metrics are strictly document-level (`retrieval_doc_recall_at_5`, `retrieval_doc_mrr`). Chunk-level evaluation requires chunk qrels, which remain pending feasibility assessment and annotator capacity.
* **Scope Note on `calibrate_decision_thresholds.py`:** Per Proposal v1.1 (`Section E.2`, `Section K.2`, `Appendix A`), Platt/isotonic probability calibration and conformal prediction are deferred to Future Work. In the MVP, `calibrate_decision_thresholds.py` performs empirical baseline distribution percentile analysis to configure transparent numeric gate tolerances for `PASS / REVIEW / BLOCK` (`config/decision_thresholds.yaml`).
* **Required Dataset & Labels:** Versioned `regression-validation-v1.yaml` + `security-benchmark-v1.yaml` (`80–120` attacks + `80–120` benign controls).
* **Ground-Truth Source:** Known candidate configuration provenance (`is_seeded_regression: bool`, `regression_category`, `expected_gate_decision`).
* **Metrics & Mathematical Formulas:**
  - **Seeded-Regression Catch Rate (Sensitivity):**
    $$\text{Regression Catch Rate} = \frac{\text{Number of seeded regression candidates yielding REVIEW or BLOCK}}{\text{Total valid seeded regression candidates evaluated (excluding INCOMPLETE)}}$$
  - **Critical-Regression Block Rate:** Fraction of critical policy/security regression candidates yielding `BLOCK`.
  - **False-Block Rate (on Benign Candidates / Normal Controls):**
    $$\text{False-Block Rate} = \frac{\text{Number of benign non-regression runs erroneously yielding BLOCK}}{\text{Total valid benign non-regression runs evaluated (excluding INCOMPLETE)}}$$
  - **Candidate-vs-Baseline Metric Deltas ($\Delta M = M_{\text{candidate}} - M_{\text{baseline}}$):**
    - RAG: $\Delta \text{Doc-Recall@5}$, $\Delta \text{Doc-MRR}$, $\Delta \text{Groundedness}$, $\Delta \text{Citation Precision}$, $\Delta \text{Failure Rate}$.
    - Agent: $\Delta \text{Task Success}$, $\Delta \text{Tool Argument Validity}$, $\Delta \text{Workflow Compliance}$, $\Delta \text{Policy Violation Rate}$.
    - Security: Detector Precision, Recall, $F_1$, Benign-Control $\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$, and Critical Unsafe-Action Block Rate.

---

## 3. Five Mandatory Ablation Studies (`Proposal Section P.1`)

All five ablations from Proposal `Section P.1` are executed on the exact same held-out split in Sprint 7 (`S7-01`) and report the identical metric suite ($\Delta \text{Macro-}F_1$, per-class $\Delta F_1$, $\Delta \text{Top-1 RCA Acc}$, $\Delta \text{MRR@3}_{\text{RCA}}$, and $\Delta \kappa_{\text{human}}$):

| Ablation ID | Ablation Name | Signal / Feature Group Removed | Primary Research Insight Tested |
| :--- | :--- | :--- | :--- |
| **ABL-01** | **Remove Retrieval Features** | Drop reference-free runtime retrieval features (`context_relevance`, facet-sufficiency signals, retrieved-document count, top-1 similarity score, mean top-$k$ similarity score, and similarity-score spread) from classifier and RCA inputs. Reference-based offline evaluation metrics (`retrieval_doc_recall_at_5`, `retrieval_doc_mrr`) are strictly excluded from model feature sets and computed exclusively post-inference using expected labels/qrels. | Quantifies the contribution of reference-free retrieval-layer trace evidence to separating `RETRIEVAL_FAILURE` from `HALLUCINATION` (`RQ1`) and ranking `retriever` vs `model_generation` (`RQ3`). |
| **ABL-02** | **Remove Policy & Workflow Rules** | Drop deterministic `workflow_compliance`, fine `app_state` transition flags, `tool_suppression`, and `policy_conformance` features (`PROC-APPROVAL-01`, `PROC-TOOL-STAGE-01`, `PROC-SUPPLIER-01`). | Quantifies the value of hard deterministic governance constraints relative to purely learned/semantic signals on agent reliability (`RQ1`, `RQ3`, `RQ4`). |
| **ABL-03** | **Remove Semantic / LLM Evaluator** | Drop `semantic_judge.py` (`semantic_correctness_score`, `query_relevance_score`) and semantic groundedness scores, retaining only deterministic, retrieval-overlap, workflow, and policy signals. | Quantifies how much `HALLUCINATION` and `RQ2` human agreement depend on LLM/semantic scoring vs deterministic trace checks. |
| **ABL-04** | **Remove Human-Reviewed Reference Evidence** | Evaluate evaluator combination tuning and agreement analysis using only unreviewed synthetic injection labels vs the adjudicated human-reviewed subset in `adjudication_records`. | Quantifies the value of human calibration/adjudication reference labels for detecting ambiguous semantic failures (`RQ2`). |
| **ABL-05** | **Remove Version Metadata** | Drop `application_version`, `prompt_version`, `model_version`, `retriever_version`, `policy_kb_version`, `policy_bundle_version`, `decision_config_version`, `tool_schema_version`, and `metadata_availability` features from classifier and RCA inputs. | Quantifies the contribution of explicit version provenance to failure diagnosis and candidate-vs-baseline regression attribution (`RQ1`, `RQ3`, `RQ4`). |

---

## 4. Controlled AI Security Benchmark Protocol (`Proposal Section Q`)

- **Benchmark Composition & Metadata Synchronization:** `80–120` adversarial attack traces (`DIRECT_INJECTION`, `INDIRECT_RETRIEVED_INJECTION`, `MALICIOUS_TOOL_USE`, `POLICY_BYPASS`) and `80–120` benign look-alike controls across both `procurement-agent` and `enterprise-rag` (`datasets/manifests/security-benchmark-v1.yaml`). Both flat fields (`is_security_subset: bool`, `security_category: Optional[str]`, `security_case_role: Optional[str]`) and nested `security_subset_metadata` are synchronized. Benign look-alike controls must have `is_security_subset: true`, `security_case_role: "CONTROL"`. Active attacks have `is_security_subset: true`, `security_case_role: "ATTACK"`. All security labels are strictly stripped from inference projections.
- **Evaluation Independence:** Attack ground truth is defined by the scenario manifest (`is_attack`, `attack_category`), never by `sec_prompt_injection_detector_v1` output. Independent deterministic pre-tool policy enforcement (`PROC-APPROVAL-01`, `PROC-TOOL-STAGE-01`, `PROC-SUPPLIER-01`) is evaluated alongside semantic detection to verify that missed semantic detections still do not authorize invalid purchase orders.
- **Reported Metrics:** Detector Precision, Recall, $F_1$, Benign-Control False-Positive Rate ($\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$), and Independent Policy Block Rate.

## Repository research conventions

Future research should use versioned dataset manifests and import production packages for feature analysis, model comparison, RCA evaluation, and threshold calibration. Write generated results under `artifacts/research/`.
