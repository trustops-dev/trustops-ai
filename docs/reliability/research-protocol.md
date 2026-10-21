# Reliability research protocol (Week 1 draft)

## 1. Research questions and required outputs

| RQ | Comparison / question | Metrics and reporting |
|---|---|---|
| RQ1 | Rules vs. multinomial Logistic Regression vs. XGBoost for nine-class primary failure classification. | Macro-F1; per-class precision, recall and support; confusion matrix; XGBoost feature importance where applicable. Use the same group-held-out split for each model. Do not assume XGBoost wins. |
| RQ2 | Semantic/LLM evaluator alone vs. rules + semantic vs. combined evaluator signals on human-reviewed labels. | Same classification metrics where labels/outputs permit, plus agreement/disagreement and error analysis against a reviewed subset. Version judge model/rubric; never use judge outputs as gold labels. |
| RQ3 | Failure-class-only cause mapping vs. weighted evidence-based RCA. | Top-1 accuracy, Top-3 recall and MRR on cases with independently known causes. Evidence scores are not calibrated probabilities. |
| RQ4 | Whether trace-based evaluation catches seeded prompt/retrieval/agent regressions ahead of release, jointly with Alaa's gate pipeline. | Regression catch rate, false-block rate and per-category results on paired baseline/candidate runs over the same versioned scenario set. Gate `PASS`/`REVIEW`/`BLOCK` remains owned by governance. |

Supplementary outputs: RAG Recall@k and MRR; NDCG only for graded relevance; groundedness and citation support; security precision, recall, F1 and false-positive rate (FPR) with benign controls; RCA/label uncertainty, per-class support and limitations. Confidence intervals/paired bootstrap or McNemar-style tests should be used where appropriate and feasible. No experimental results are claimed by this specification.

## 2. Data and label provenance

Preserve separate fields for intended injected class/root cause, observed trace, evaluator findings, adjudicated label and model/classifier prediction. `scenario_metadata.injected_failure_class` is a candidate label, not proof of observed failure; confirm the outcome against trace evidence or human adjudication. Use `scenario_metadata.injected_root_cause` only as known cause when the planned mechanism is confirmed. Human-reviewed labels remain separate from Mohamed's decision review record.

The current dataset requirements draft proposes reviewing roughly 15–20% of records and double-annotating 100–150. Record reviewer/guideline version, conflicts, adjudication rationale and concrete trace evidence. Report support by primary class and do not fabricate duplicates to inflate rare classes.

## 3. Leakage safeguards

- Keep `injected_failure_class`, `injected_root_cause`, `primary_label`, `adjudicated_label`, `attack_present`, `is_benign_control`, evaluator outputs under test, post-run classifier predictions, and future outcomes out of classifier features.
- Split by `split_group_key` and keep the same scenario family, template, injection recipe, paraphrases, control/failure pair and other near-duplicates in one split. Freeze the test set before model selection.
- Reuse one immutable split manifest for rules, Logistic Regression and XGBoost; no preprocessing fit or feature selection may learn from held-out data.
- For RQ2, compare setups on the same reviewed subset. The LLM judge and rubric are fallible predictions, so comparison must use independent reviewed labels.
- Keep offline expected relevant IDs/reference answers in a metric-only path; never pass these references into generation or model features. Track the reference dataset version.
- Use opaque scenario identifiers during runtime where feasible so model inputs cannot trivially encode labels; keep labels and scenario design metadata in a separate dataset join path for evaluation only.
- Track label changes as versioned annotation/adjudication artifacts; do not revise labels after looking at test errors without freezing a new dataset version and recording the change.

## 4. Reproducibility metadata

At minimum record: `trace_id`, `schema_version`, `application_id`, `environment`, `versions.*`, `scenario_metadata.*`, `dataset_version`, `split_policy_version`, `code_revision`, `random_seed`, `split_group_key`, evaluator ID/version, evaluator-suite version, configuration fingerprint, dataset fingerprint, prompt/model/retriever/policy version, and metric/reference version where applicable. Missing token/latency measurements are null, not zero. Keep classifier/evaluator/RCA versions separate and freeze artifacts by the Week-12 gate, not in Week 1.

## 5. Security and interpretation limits

Security data should cover direct injection, indirect retrieved-content injection, malicious tool-use instructions, policy-bypass requests and benign look-alikes. Treat attack-present vs. detector verdict as separate variables. Report false-positive rate alongside precision/recall/F1 and inspect benign false positives. Findings from the controlled/synthetic benchmark do not support universal prompt-injection or exfiltration defense claims.

## 6. Open dependencies

- Mohab: canonical trace schema v1, evidence IDs, field aliases and evaluator persistence/run lineage.
- Nour: reproducible valid/failure/security traces, expected RAG evidence and scenario family/group keys.
- Alaa: dataset version/fingerprint, grouped-split algorithm and manifest, split ratio, experiment/run tracking and frozen test-set procedure.
- Mohamed: canonical policy evidence schema and authoritative policy truth; do not infer policy violations without it.
- Malak: required evidence and metrics for reviewer display.

Split ratio, field aliases, reviewed-label persistence, final class support and policy/workflow overlap rules remain team decisions; they must not be silently invented in the runtime integration.


## 7. Contract and trace-integration review

The approved monorepo architecture calls for Pydantic cross-module contracts. Evaluator and annotation models are implemented as Pydantic v2 models; JSON Schema files are generated from those models and supplemented with portable conditional constraints. The Python models additionally validate recursive label-leakage and cross-field evidence/identity rules that generic JSON Schema cannot fully express.

The current `dev` branch's `docs/architecture/schemas/Week 1 Execution Deliverable Trace Schema v1 (Draft) & Interface Boundaries.md` is explicitly a draft before the Week 2 contract freeze; `docs/architecture/reference-applications/trace-evidence-contract.md` says it is not Mohab's canonical schema. Therefore the evaluator contract does not yet assert full trace-payload compatibility. In particular, finalize the following before freezing evaluator contract v1:

- Align `trace_schema_version` to the trace payload's `schema_version` and require the canonical envelope identity fields.
- Agree `event_id` versus `span_id` evidence targets; resolve `document_id` versus the draft's `doc_id`; define `source_id`, `field_path`, and claim-to-source link semantics.
- Add schema-backed tests against Mohab's approved trace Pydantic model and real representative Procurement/RAG fixtures.
- Agree whether evaluator results require `evaluation_run_id` or a separately named `run_id`, and how output/result records link to the trace and run.
- Confirm the authoritative policy result fields with Mohamed; this work does not define policy truth.
