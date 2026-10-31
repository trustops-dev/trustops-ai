# TrustOps AI — Research Protocol & Experimental Design (v1.0)

**Canonical Path:** `research/README.md`  
**Owners (R):** Ahmed Ragab (`packages/reliability-engine`, `research/` — Primary author for RQ1–RQ3, security metrics, and ablations) & Alaa Sayed (`packages/mlops`, `datasets/` — Co-owner for dataset splits, MLflow reproducibility, and RQ4 gate metrics)  
**Task / Epic:** `S1-03` — Freeze Failure Taxonomy & Evaluator Contracts (`TAI-EP03`, `TAI-EP11`)  
**Sprint / Week:** Sprint 1, Week 1  
**Status:** **DRAFT — Awaiting Team Review**  
**Authoritative Baseline:** `TrustOps_AI_Project_Proposal.docx` (v1.1, Sections L, M, O, P, Q, S)  
**Related Documents:**
- Declarative Taxonomy YAML: [`../packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml`](../packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml)
- Evaluation Pipeline & Evaluator Contracts: [`../docs/architecture/evaluation-pipeline.md`](../docs/architecture/evaluation-pipeline.md)
- Annotation Guide: [`../docs/architecture/annotation-guide.md`](../docs/architecture/annotation-guide.md)

---

## 1. Overview & Scientific Falsifiability Principle

Per Proposal `Section A`, `Section L.4`, and `Section P`, TrustOps AI frames its academic contribution as **four falsifiable empirical studies (`RQ1–RQ4`)** plus **five controlled feature/signal ablations (`P.1`)**.

1. **Falsifiable Framing:** No performance target or model superiority is assumed in advance. If interpretable deterministic rules match or outperform `XGBoost` on certain failure classes, or if removing the fallible LLM-as-a-judge improves human agreement, that finding is retained and reported transparently as a valid research conclusion.
2. **Zero Evaluator Leakage into Ground Truth:** Ground-truth labels (`primary_label`, `secondary_findings`, `ground_truth_root_cause`) are never derived from or adjudicated using the predictions of the evaluator, LLM judge, or classifier under test.
3. **Zero Fabricated Metrics:** This Week 1 protocol defines hypotheses, datasets, controls, mathematical formulas, and statistical tests only. Actual measured figures will be populated exclusively after Sprint 4–7 experiments run against frozen datasets.

---

## 2. Detailed Experimental Protocol for RQ1–RQ4

### 2.1 RQ1 — Structured-Feature Failure Classification (`research/experiments/compare_classifiers.py`)
* **Research Question:** *Can structured execution-trace features improve AI failure classification over deterministic rules alone?*
* **Hypothesis & Comparison:**
  - Compare three models trained and evaluated on the **exact same scenario-held-out test split** (`datasets/manifests/classifier-training-v1.yaml`, `~15%` of `1,500–1,800` traces):
    1. **Model 1 (`rules.py`):** Interpretable deterministic rule baseline mapping deterministic, RAG, workflow, policy, and security thresholds directly to the 9-class taxonomy using the 5-Tier Precedence Hierarchy in [`../docs/architecture/annotation-guide.md`](../docs/architecture/annotation-guide.md).
    2. **Model 2 (`logistic_regression.py`):** Multinomial Logistic Regression (`scikit-learn`, L2-regularized, `class_weight="balanced"`, split-safe `StandardScaler` / `OneHotEncoder` fitted strictly on `train`).
    3. **Model 3 (`xgboost.py`):** Multi-class Gradient Boosted Decision Trees (`XGBClassifier`, `objective="multi:softprob"`, `num_class=9`, inverse-frequency sample weights fitted strictly on `train`, hyperparameters tuned strictly on `val`).
  - **Null Hypothesis ($H_0$):** $\text{Macro-}F_1(\text{XGBoost}) \le \text{Macro-}F_1(\text{Deterministic Rules})$ on held-out scenario templates.
  - **Alternative Hypothesis ($H_1$):** Non-linear combinations of heterogeneous trace features (`retrieval` scores/spreads, `token`/`latency` ratios, `agent_state` transitions, and multi-evaluator signals) yield higher Macro-$F_1$ than deterministic rules or linear Logistic Regression, particularly on multi-symptom RAG (`RETRIEVAL_FAILURE` vs `HALLUCINATION`) and borderline agent trajectories.
* **Required Dataset & Labels:** Frozen `classifier-training-v1.yaml` (`70% train / 15% val / 15% test`), with 9-class `primary_label`.
* **Ground-Truth Source:** Independent scenario injection metadata (`Tier 1`) verified by deterministic symptom sanity checks, plus adjudicated human labels (`Tier 2`) on the `15–20%` reviewed subset. **Never** any single model's or evaluator's prediction.
* **Experimental Controls & Leakage Prevention:**
  - Grouped splitting by `split_group_key = scenario_family::question_template_id` (`tests/research/test_grouped_split_no_leakage.py`) so zero question paraphrases cross between `train`, `val`, and `test`.
  - Strip all `scenario_metadata` ground-truth keys and `is_poisoned_test_doc` flags prior to feature extraction.
  - Fit all imputers, scalers, and categorical encoders on `train` only.
* **Metrics & Mathematical Formulas:**
  - **Per-Class Precision ($P_c$), Recall ($R_c$), $F_{1,c}$, and Support ($N_c$)** for each class $c \in \{0, \dots, 8\}$:
    $$P_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}, \quad R_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}, \quad F_{1,c} = \frac{2 P_c R_c}{P_c + R_c}$$
  - **Primary Metric — Unweighted Macro-$F_1$:**
    $$\text{Macro-}F_1 = \frac{1}{9} \sum_{c=0}^{8} F_{1,c}$$
  - **$9 \times 9$ Confusion Matrix** (analyzed both overall and stratified by `application_type`: `procurement-agent` vs `enterprise-rag`).
  - **Feature Importance:** Gain-based and permutation feature importance across the 6 feature groups (`General trace`, `Retrieval`, `Answer`, `Agent`, `Policy`, `Security` per `Proposal §L.2`).
  - **Statistical Comparison:** Paired bootstrap (`B = 10,000` resamples at scenario-template cluster level) for 95% confidence intervals on $\Delta \text{Macro-}F_1$, plus Stuart-Maxwell / McNemar-style paired accuracy/error discordance tests across identical test trace IDs.
* **Interpretation, Limitations & Possible Negative Findings:**
  - Because deterministic failure classes (`INVALID_TOOL_ARGUMENTS`, `WORKFLOW_VIOLATION`, `POLICY_VIOLATION`) have strong deterministic evaluator signals, `rules.py` may match `XGBoost` on those classes. If `XGBoost` only improves on `HALLUCINATION`, `RETRIEVAL_FAILURE`, and `PROMPT_INJECTION` (or if `rules.py` matches `XGBoost` overall because synthetic scenarios are clean), we report that exact per-class breakdown rather than over-tuning `XGBoost` on the test set.

---

### 2.2 RQ2 — Multi-Evaluator Combination vs. Single Semantic Judge (`RQ2` Evaluator Agreement Study)
* **Research Question:** *Does combining deterministic, retrieval, and semantic evaluation signals agree with human-reviewed labels better than a single semantic/LLM evaluator?*
* **Hypothesis & Comparison:**
  - Evaluate three evaluator strategies on the **independently human-reviewed subset** (`15–20%` of the dataset, `~225–360` traces, including the `100–150` double-annotated adjudicated traces):
    1. **Strategy A (`Semantic / LLM Judge Alone`):** Diagnosis derived solely from `semantic_judge.py` (`sem_llm_judge_correctness_v1`).
    2. **Strategy B (`Deterministic Rules + Semantic Judge`):** Combines `deterministic`, `agent_workflow`, `policy_conformance`, and `semantic_judge` (excluding `rag` retrieval/citation metrics and `security` detectors).
    3. **Strategy C (`Full Multi-Evaluator Combination`):** Combines all 6 evaluator families (`deterministic` + `rag` + `semantic_llm` + `security` + `agent_workflow` + `policy_conformance`).
* **Required Dataset & Labels:** Human-reviewed subset (`human_adjudicated_primary_label` and binary failure/pass verdict).
* **Ground-Truth Source:** Blind human-reviewed and double-annotated adjudicated labels (`Tier 2`), recorded **without** annotators seeing any evaluator output.
* **Experimental Controls & Leakage Prevention:**
  - The LLM judge prompt and rubric (`judge_rubric_v1.0`) are frozen before running on the human-reviewed subset.
  - Human annotators are strictly blinded to the LLM judge's score and rationale.
* **Metrics & Mathematical Formulas:**
  - **Cohen's Kappa ($\kappa$) with Human Ground Truth:**
    $$\kappa_{\text{eval, human}} = \frac{p_o - p_e}{1 - p_e}$$
    computed both on binary failure detection (`NORMAL` vs `ANY_FAILURE`) and on the 9-class categorical diagnosis.
  - **Macro-$F_1$ and Per-Class $F_1$** against human labels.
  - **Evaluator-Human Disagreement Rate:**
    $$\text{Disagreement Rate} = \frac{1}{N_{\text{rev}}} \sum_{i=1}^{N_{\text{rev}}} \mathbb{I}\left(\hat{y}_{\text{strategy}, i} \neq y_{\text{human}, i}\right)$$
  - **False-Approval Rate on Critical Policy/Workflow Failures:** Fraction of human-confirmed `WORKFLOW_VIOLATION` / `POLICY_VIOLATION` / `UNSUPPORTED_COMPLETION` traces where `Semantic Judge Alone` awards a passing score because the final text sounds polite and plausible (`Proposal §B.3`).
* **Interpretation, Limitations & Possible Negative Findings:**
  - Quantifies `LLM-as-a-judge` failure modes (verbosity bias, inability to verify pre-tool state transitions or retrieval `Recall@k`). If adding the fallible LLM judge to deterministic + RAG evaluators degrades agreement on certain classes (tested via `ABL-03`), we document when the LLM judge should be down-weighted or routed to `REVIEW`.

---

### 2.3 RQ3 — Evidence-Based Root-Cause Analysis (`research/experiments/evaluate_rca_topk.py`)
* **Research Question:** *Can trace evidence provide useful root-cause ranking for intentionally seeded AI failures?*
* **Hypothesis & Comparison:**
  - Evaluate on all failed traces in the held-out test set that possess causal ground truth (`ground_truth_root_cause` $\in$ 9 fixed candidates):
    1. **Baseline (`Class-Only Cause Mapping`):** A static 1-to-1 lookup table that maps only the predicted `primary_label` to a fixed default ranking of causes without inspecting granular evaluator or trace evidence (e.g., always mapping `WORKFLOW_VIOLATION` $\rightarrow$ `[agent_workflow, prompt, model_generation]` regardless of whether `prompt_version` changed or `is_poisoned_test_doc` was present).
    2. **Primary Method (`Weighted Multi-Evaluator Evidence Ranker`):** Computes candidate `evidence_score`s directly from granular evaluator findings, version provenance deltas, retrieval score spreads, and tool/state evidence (`Proposal §M.1`).
* **Required Dataset & Labels:** Held-out failed traces (`y != NORMAL`) with verified `ground_truth_root_cause`.
* **Ground-Truth Source:** Independent scenario `injected_root_cause` metadata (`Tier 1`) plus human causal adjudication (`Tier 2`) on ambiguous semantic failures.
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
* **Interpretation, Limitations & Possible Negative Findings:**
  - Where a failure class is nearly 1-to-1 with a single root cause (e.g., `INVALID_TOOL_ARGUMENTS` $\leftrightarrow$ `tool_arguments`), the class-only baseline and weighted evidence ranker will tie on Top-1 accuracy. The weighted evidence ranker is expected to show differentiation primarily on classes with **multi-cause ambiguity** (e.g., distinguishing `prompt` vs `agent_workflow` vs `policy_configuration` in procurement failures, or `retriever` vs `retrieved_context` vs `model_generation` in RAG failures) and on **Top-2/Top-3 `MRR@3`**.

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
* **Scope Note on `calibrate_decision_thresholds.py`:** Per Proposal v1.1 (`Section E.2`, `Section K.2`, `Appendix A`), Platt/isotonic probability calibration and conformal prediction are deferred to Future Work. In the MVP, `calibrate_decision_thresholds.py` performs empirical baseline distribution percentile analysis to configure transparent numeric gate tolerances for `PASS / REVIEW / BLOCK` (`config/decision_thresholds.yaml`).
* **Required Dataset & Labels:** Versioned `regression-validation-v1.yaml` + `security-benchmark-v1.yaml` (`80–120` attacks + `80–120` benign controls).
* **Ground-Truth Source:** Known candidate configuration provenance (`is_seeded_regression: bool`, `regression_category`, `expected_gate_decision`).
* **Metrics & Mathematical Formulas:**
  - **Seeded-Regression Catch Rate (Sensitivity):**
    $$\text{Regression Catch Rate} = \frac{\text{Number of seeded regression candidates yielding REVIEW or BLOCK}}{\text{Total seeded regression candidates evaluated}}$$
  - **Critical-Regression Block Rate:** Fraction of critical policy/security regression candidates yielding `BLOCK`.
  - **False-Block Rate (on Benign Candidates / Normal Controls):**
    $$\text{False-Block Rate} = \frac{\text{Number of benign non-regression runs erroneously yielding BLOCK}}{\text{Total benign non-regression runs evaluated}}$$
  - **Candidate-vs-Baseline Metric Deltas ($\Delta M = M_{\text{candidate}} - M_{\text{baseline}}$):**
    - RAG: $\Delta \text{Recall@k}$, $\Delta \text{MRR}$, $\Delta \text{Groundedness}$, $\Delta \text{Citation Precision}$, $\Delta \text{Failure Rate}$.
    - Agent: $\Delta \text{Task Success}$, $\Delta \text{Tool Argument Validity}$, $\Delta \text{Workflow Compliance}$, $\Delta \text{Policy Violation Rate}$.
    - Security: Detector Precision, Recall, $F_1$, Benign-Control $\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$, and Critical Unsafe-Action Block Rate.

---

## 3. Five Mandatory Ablation Studies (`Proposal Section P.1`)

All five ablations from Proposal `Section P.1` are executed on the exact same held-out split in Sprint 7 (`S7-01`) and report the identical metric suite ($\Delta \text{Macro-}F_1$, per-class $\Delta F_1$, $\Delta \text{Top-1 RCA Acc}$, $\Delta \text{MRR@3}_{\text{RCA}}$, and $\Delta \kappa_{\text{human}}$):

| Ablation ID | Ablation Name | Signal / Feature Group Removed | Primary Research Insight Tested |
| :--- | :--- | :--- | :--- |
| **ABL-01** | **Remove Retrieval Features** | Drop `Recall@k`, `MRR`, `context_relevance`, document count, top-1 score, mean top-$k$ score, and score spread from classifier & RCA inputs. | Quantifies the contribution of retrieval-layer trace evidence to separating `RETRIEVAL_FAILURE` from `HALLUCINATION` (`RQ1`) and ranking `retriever` vs `model_generation` (`RQ3`). |
| **ABL-02** | **Remove Policy & Workflow Rules** | Drop deterministic `workflow_compliance`, stage-transition flags, and `policy_conformance` features (`PROC-APPROVAL-01`, `PROC-TOOL-STAGE-01`, `PROC-SUPPLIER-01`). | Quantifies the value of hard deterministic governance constraints relative to purely learned/semantic signals on agent reliability (`RQ1`, `RQ3`, `RQ4`). |
| **ABL-03** | **Remove Semantic / LLM Evaluator** | Drop `semantic_judge.py` (`semantic_correctness_score`, `query_relevance_score`) and semantic groundedness scores, retaining only deterministic, retrieval-overlap, workflow, and policy signals. | Quantifies how much `HALLUCINATION` and `RQ2` human agreement depend on LLM/semantic scoring vs deterministic trace checks. |
| **ABL-04** | **Remove Human-Reviewed Reference Evidence** | Evaluate evaluator combination tuning and agreement analysis using only unreviewed synthetic injection labels vs the adjudicated human-reviewed subset. | Quantifies the value of human calibration/adjudication reference labels for detecting ambiguous semantic failures (`RQ2`). |
| **ABL-05** | **Remove Version Metadata** | Drop `application_version`, `prompt_version`, `model_version`, `retriever_version`, and `policy_kb_version` features from classifier and RCA inputs. | Quantifies the contribution of explicit version provenance to failure diagnosis and candidate-vs-baseline regression attribution (`RQ1`, `RQ3`, `RQ4`). |

---

## 4. Controlled AI Security Benchmark Protocol (`Proposal Section Q`)

- **Benchmark Composition:** `80–120` adversarial attack traces (`DIRECT_INJECTION`, `INDIRECT_RETRIEVED_INJECTION`, `MALICIOUS_TOOL_USE`, `POLICY_BYPASS`) and `80–120` benign look-alike controls across both `procurement-agent` and `enterprise-rag` (`datasets/manifests/security-benchmark-v1.yaml`).
- **Evaluation Independence:** Attack ground truth is defined by the scenario manifest (`is_attack`, `attack_category`), never by `sec_prompt_injection_detector_v1` output. Independent deterministic pre-tool policy enforcement (`PROC-APPROVAL-01`, `PROC-TOOL-STAGE-01`, `PROC-SUPPLIER-01`) is evaluated alongside semantic detection to verify that missed semantic detections still do not authorize invalid purchase orders.
- **Reported Metrics:** Detector Precision, Recall, $F_1$, Benign-Control False-Positive Rate ($\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$), and Independent Policy Block Rate.

## Repository research conventions

Future research should use versioned dataset manifests and import production packages for feature analysis, model comparison, RCA evaluation, and threshold calibration. Write generated results under `artifacts/research/`.
