# TAI-11 / S1-05 — Dataset & Experiment Requirements Matrix

**Owner:** Alaa Sayed
**Status:** DRAFT for team review.

`PENDING (owner)` marks anything not yet available or not yet agreed.

---

## 1. RQ-to-field matrix (Scope 1)

| Question | Topic | Required fields | Split | Outputs / metrics | Owner |
|---|---|---|---|---|---|
| **RQ1** | Rules vs. Logistic Regression vs. XGBoost for failure classification. Official wording: PENDING (check Proposal) | **Label:** `scenario_metadata.injected_failure_class` (NORMAL + 8 classes, see section 3). This is the intended ground truth, not a guaranteed observed label. Adjudicated label field: PENDING (Ahmed, Mohab)<br>**Features (candidates, from events):** event count, `total_latency_ms`, `application_type`, retrieval doc count and scores (`retrieved_documents[].score`, `rank`), policy results, `approval_received`, `argument_schema_valid`, `versions.*`. Final feature schema: PENDING (Ahmed)<br>**Grouping:** `split_group_key` | Same split manifest for all three models. Paired controls and variants are grouped before split assignment (Alaa). Split ratio: PENDING | Macro-F1, per-class precision/recall/support, confusion matrix | Ahmed (features, logic) + Alaa (split, runs) |
| **RQ2** | Evaluator alone vs. rules + semantic vs. full combination. Official wording: PENDING | Outputs of the 6 evaluator families (deterministic, rag, semantic_llm, security, agent_workflow, policy_conformance) from `evaluator_results` per `evaluation_run_id`; `evaluator_suite_version`. Evaluator output contracts: PENDING (Ahmed). Human-reviewed label field: PENDING (Ahmed, Mohab) | Same reviewed subset for all three setups. Subset selection: PENDING | Same metrics as RQ1, plus agreement/disagreement. Definition of "disagreement": PENDING (Ahmed) | Ahmed + Alaa |
| **RQ3** | Root-cause analysis (RCA) accuracy. Official wording: PENDING | **Ground truth:** `scenario_metadata.injected_root_cause`, restricted to the fixed nine causes: prompt, retriever, retrieved_context, model_generation, tool_selection, tool_arguments, agent_workflow, policy_configuration, malicious_input<br>**Output:** `rca_results` (ranked candidates with `supporting_events`); `rca_config_version`<br>Cause mapping for POLICY_VIOLATION and HALLUCINATION recipes: PENDING (Ahmed, Mohamed) | Cases with a known cause | Top-1, Top-3, MRR | Ahmed (RCA) + Nour (injection) |
| **RQ4** | Does the quality gate catch regressions? Official wording: PENDING | `dataset_version`, `baseline_run_id`, `candidate_run_id`, `environment = ci_gate`, `versions.*` for both, per-trace results, decision output (`decision`, `evaluation_status`, `fired_rules`, `decision_config_version`, `decision_id`), policy set version. Field names differ between Mohab and Mohamed (`policy_bundle_version` vs `policy_set_version`, `decision_engine_version` vs `decision_config_version`): PENDING (Mohab, Mohamed) | Same evaluation dataset for baseline and candidate | Regression catch rate, false-block rate, results by category, PASS/REVIEW/BLOCK. Decision thresholds: PENDING (measured baselines, Alaa, Mohamed) | Alaa + Mohamed (policy evidence) |

### Fields required for every question
`trace_id`, `schema_version`, `application_id`, `environment`, `versions.*`, `scenario_metadata.*`, `dataset_version`, `split_policy_version`, `code_revision`, `random_seed`.

## 2. Release-gate metrics and the fields that compute them

| Metric | Required fields |
|---|---|
| Critical policy failures (immediate BLOCK) | Mohab: `policy_check.evaluated_policies[].passed`, `criticality`, `pre_tool_verdict`. Mohamed: `results[].status` (PASS / FAIL / NOT_APPLICABLE / ERROR), `criticality`, `verdict` (ALLOW / BLOCK), `verdict_basis`. Names differ: PENDING (Mohab, Mohamed) |
| Reliability decision | `decision` (PASS / REVIEW / BLOCK), `evaluation_status`, `fired_rules`, `decision_config_version` |
| Incomplete evaluation | `decision` absent, `evaluation_status` incomplete, missing-evidence list. Gate treatment: PENDING (Alaa, Malak) |
| Decision thresholds | Raw metrics vs. precomputed flags: PENDING (Ahmed, Alaa). Threshold values come from measured baselines: PENDING |
| Workflow compliance | `agent_state.from_stage` / `to_stage`, `approval_required`, `approval_received`, `workflow_compliance`. Stage names (e.g. `PO_CREATED` vs `PO_CREATION`): PENDING (Mohab, Nour, Mohamed) |
| Tool-argument validity | `tool_call.argument_schema_valid`, `argument_validation_errors` |
| Unsupported completion | `final_response.claimed_actions` compared with `tool_result.side_effect_committed` |
| Groundedness / citation precision | `retrieval.retrieved_documents[].content_snippet`, `final_response.citations[]` |
| Abstention | `final_response.is_abstention`, `abstention_reason` |
| Retrieval (Recall@k, MRR, NDCG) | `top_k_requested`, `rank`, `score`, `scenario_metadata.expected_relevant_doc_ids` |
| Latency / tokens | `total_latency_ms`, `model_call.token_usage` (null when unavailable, never 0) |
| Version lineage | `versions.*` plus the `evaluation_runs` version fields |

## 3. Source mapping for each dataset group and class

### Classes (from Nour's planning matrix; all injections are planned, none implemented)

Class names are PENDING Ahmed's freeze. Scenario owner is Nour for every row.

| Class | Application | Generated by | Timing |
|---|---|---|---|
| NORMAL (baseline, not a failure class) | Both | Valid approval-required procurement, policy-confirmed no-approval procurement, grounded RAG answer, expected abstention, benign injection look-alikes | With each recipe (paired controls) |
| RETRIEVAL_FAILURE | Both | Remove the known relevant document or alter retrieval query/config | S3-01, Sprint 3 |
| HALLUCINATION | RAG | Replace the candidate answer with an unsupported claim, context held fixed | Proposed Week 7, approval PENDING |
| TOOL_SELECTION_ERROR | Procurement | Substitute a schema-valid but wrong tool for the current step | Proposed Week 7, approval PENDING |
| INVALID_TOOL_ARGUMENTS | Procurement | Corrupt quantity, type, amount or request binding in proposed arguments | S3-01, Sprint 3 |
| WORKFLOW_VIOLATION | Procurement | Propose PO creation in PRE_APPROVAL with approval required and not received | S2-01 flagship case, reused in S3-01 |
| POLICY_VIOLATION | Procurement | Unapproved supplier: full-app early-stop pair plus isolated pre-tool boundary fixture | S3-03 fixture Week 6, reusable recipe proposed Week 7, approval PENDING |
| PROMPT_INJECTION | Both | Direct user instruction or poisoned retrieved chunk, plus benign look-alikes | S5-02 benchmark (Sprint 5) |
| UNSUPPORTED_COMPLETION | Procurement | Inject a final claim of PO success after a blocked, failed or missing result | S3-01, Sprint 3 |

Rules from Nour's draft that affect the dataset: one primary class per trace with secondary findings retained (overlap rule PENDING Ahmed sign-off); expected labels, injected cause and attack/control indicators are kept out of the model and classifier inputs; runtime scenario IDs are opaque.

### Groups

| Group | Generated from | Owner |
|---|---|---|
| Procurement normal | Procurement Agent, NORMAL controls above | Nour |
| Procurement failures | Procurement Agent, the six procurement classes above | Nour |
| RAG normal | Enterprise RAG Assistant, NORMAL controls above | Nour |
| RAG failures | Enterprise RAG Assistant, RETRIEVAL_FAILURE, HALLUCINATION, PROMPT_INJECTION | Nour |
| Security subset | PROMPT_INJECTION scenarios plus benign look-alikes (S5-02). Field names for security category and attack/control flag: PENDING (Ahmed, Nour, Mohab) | Ahmed / Nour |

## 4. Dataset composition targets (Scope 2, per proposal §O.1)

| Group | Target range |
|---|---|
| Procurement normal | 300–350 |
| Procurement failures | 500–600 |
| RAG normal | 250–300 |
| RAG failures | 350–450 |
| Security subset | 150–200 (overlapping, see section 6) |
| **Total** | **1,500–1,800** (minimum acceptable ≈ 1,200) |

Per-class counts: PENDING (Ahmed, Alaa).

Class availability for Dataset v1: PENDING (Alaa, Ahmed). Only four classes are committed in Sprint 3 (workflow bypass, invalid arguments, retrieval failure, unsupported completion). HALLUCINATION, TOOL_SELECTION_ERROR and reusable POLICY_VIOLATION are proposed for Week 7, and PROMPT_INJECTION for Sprint 5. Whether the Week 7 recipes enter Dataset v1 before the split freeze, or go into a later versioned dataset, has to be decided.

## 5. Manual human-review plan (Scope 3)

- Manually review roughly **15–20%** of the dataset.
- Double-annotate **100–150** records (two reviewers) to measure agreement.
- The annotation guide comes from Ahmed. Disagreements are resolved through a documented process. Guide and reviewer assignment: PENDING (Ahmed).
- Adjudication does not overwrite the original `injected_failure_class`. Intended fault, observed behavior, evaluator findings, adjudicated label and classifier output are stored separately.
- Where adjudicated labels are stored: PENDING (Ahmed, Mohab). Mohamed's `human_review_record` covers reviews of reliability decisions (ACCEPT / REVIEW / BLOCK) and is a different record.

## 6. Security-subset overlap rule (Scope 4)

The security subset is a subset of the procurement and RAG traces, not an additional group. A trace tagged as part of the security subset is counted once in the total. Counts are reported separately (total / security subset) and never summed. The tagging field name is PENDING (Ahmed, Nour, Mohab).

## 7. Open decisions for team sign-off (Scope 5)

| # | Decision | Decided by | When |
|---|---|---|---|
| 1 | MLflow vs. PostgreSQL/JSON fallback | Team | Week 2 |
| 2 | Split ratio (current working assumption: 70/15/15) | Alaa + Ahmed | Before Week 7 |
