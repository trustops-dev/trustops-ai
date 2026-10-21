# Evaluator input/output contract v1

**Contract version:** `1.0.0`
**Status:** candidate interface specification; fields requiring platform-team mapping are not a frozen trace schema.

## 1. Boundary

An evaluator consumes observed trace payload plus optional versioned reference data for offline metrics and emits findings linked to concrete evidence. It does not write the primary failure label, alter the trace, select `PASS`/`REVIEW`/`BLOCK`, or define policy truth. Runtime evaluation, evaluator registry/orchestration, persistence and APIs are deferred beyond Week 1.

Cross-module objects belong in `packages/contracts`. Reliability may depend on those contracts; reliability/governance independence and package import boundaries remain unchanged. The `trace_payload` stays owned by Mohab's canonical trace contract; these request envelopes must be reconciled with schema v1 before Week 2.

## 2. Input envelope (`evaluator-input-v1.schema.json`)

Required fields:

| Field | Meaning |
|---|---|
| `contract_version` | Exact supported evaluator contract version (`1.0.0`). |
| `request_id` | Unique evaluation-request ID, distinct from `trace_id`. |
| `trace_id` | Stable trace identity and evidence-reference anchor. |
| `trace_schema_version` | Version of the producer's canonical trace schema. |
| `application_id` | Application producing the observed trace. |
| `trace_payload` | Observed trace only; application trace schema remains canonical elsewhere. |
| `evaluator.evaluator_id` / `evaluator_version` | Stable evaluator identity and implementation/rubric version. |
| `evaluator.configuration_fingerprint` | Fingerprint of all behavior-affecting config/rubric inputs. |

Optional `reference_data` has `mode: offline_metric_only` and a `reference_version`, plus expected relevant/citation document IDs and expected tool/workflow trajectory. Reference values must not be exposed to online generation or included in classifier features. Optional `run_metadata` captures `dataset_version`, `dataset_fingerprint`, `split_policy_version`, split, `split_group_key`, opaque scenario ID/family, `code_revision`, `random_seed`, and prompt/model/retriever/policy versions.

Forbidden in `trace_payload`: `primary_label`, `adjudicated_label`, `injected_failure_class`, `injected_root_cause`, `attack_present`, `is_benign_control`, `gold_label`, `ground_truth`, `expected_failure_class`, and `label_source`. These belong in separate reference/label records. Evaluator results are not themselves inserted as truth.

## 3. Output envelope (`evaluator-output-v1.schema.json`)

Required fields: `contract_version`, `evaluator_id`, `evaluator_version`, `trace_id`, `status`, `findings`, `metrics`, `evidence_refs`, `execution`.

- `status`: `pass`, `fail`, `inconclusive`, or `error`; `inconclusive` is not equivalent to pass.
- Each finding includes stable `finding_id`, `code`, severity (`info`, `low`, `medium`, `high`, `critical`), human-readable message and at least one evidence reference.
- Evidence reference: same `trace_id` plus at least one of `event_id`, `span_id`, `document_id`, `source_id`, `field_path`, `claim_id`. Concrete targets are required; references cannot point to a different trace.
- Metrics are scalar (`string`, `integer`, finite `number`, `boolean`, or `null`) and metric name definitions remain evaluator-specific/versioned. Missing/unavailable values use `null`, not zero.
- `execution` captures `input_fingerprint`, `configuration_fingerprint`, `deterministic`, `reference_data_used`, and optional `run_id`/`error_code`. Record run/dataset/version lineage for reproducibility.
- A `fail` result must include one or more evidence-backed findings; individual findings may not be unreferenced.

## 4. Evaluator family identifiers

The taxonomy v1 declares six families; this names the interface only, it does not claim implementations exist:

| Family (`evaluator_id`) | Responsibility | Examples of outputs/signals |
|---|---|---|
| `deterministic` | Trace integrity, schema/business rules and provenance. | Missing required event, argument errors, invalid transition. |
| `rag` | Retrieval relevance, groundedness and citation support. | Recall@k/MRR against reference IDs; citation/claim support. |
| `semantic_llm` | Rubric-based correctness/relevance/claim evaluation. | Verdict/score/rationale plus judge-model/rubric versions. Fallible only. |
| `security` | Injection/malicious tool-use/policy-bypass attack benchmark signals. | Attack category and detector verdict; precision/recall/F1/FPR measured against independent labels. |
| `agent_workflow` | Tool selection/arguments, workflow transitions, approval and successful-action evidence. | Expected-vs-observed trajectory, approval or action-result mismatch. |
| `policy_conformance` | Consume policy results from the governance owner. | Policy-rule IDs/status/criticality/verdict-basis references. Must not recreate policy truth. |

## 5. Metadata and evidence expectations

For a reproducible research case, required shared fields are `trace_id`, `schema_version`, `application_id`, `environment`, `versions.*`, `scenario_metadata.*`, `dataset_version`, `split_policy_version`, `code_revision`, and `random_seed`. Explicitly retain `split_group_key`, `scenario_family`, opaque scenario IDs, evaluator suite version, dataset fingerprint and configuration fingerprint in run metadata.

Application evidence needed for evaluation should include, where applicable:

- **Agent:** tool call name and ID, redacted arguments, schema/business validation, state from/to stage, approval-required/received evidence, tool result status and side-effect commitment, final response/claimed actions, policy result references.
- **RAG:** query/query version, retrieved document and source IDs, ranks/scores, relevant-document reference version, final answer/claims, citation target IDs, available source snippets under the source owner's redaction rules.
- **All traces:** stable IDs, schema version, timestamps/duration when measured, application/environment, prompt/model/retriever/policy versions, event provenance and safe redaction. Missing values remain missing rather than being fabricated as zero/success.

These are Week 1 required-evidence requests, not additions to Mohab's trace payload contract. Names such as policy version, decision-config version, and workflow stage need owner agreement where the current drafts conflict.

## 6. Version compatibility and implementation note

Taxonomy, annotation guide, evaluator request/output schema and feature schema are versioned independently; major contract changes are incompatible, and unrecognized versions fail clearly. Evaluator output links to the request trace ID, evaluator version, input/configuration fingerprints and source evidence.

The approved architecture specifies Pydantic for canonical cross-module contracts. The remediated implementation defines Pydantic v2 models in `packages/contracts` and generates the JSON Schema wire files from those models. `pydantic==2.13.5` is declared as a runtime dependency. `jsonschema==4.26.0` is added as a development dependency for contract tests. The lockfile must be regenerated by the pinned uv toolchain before merge; this session could not do so because it has uv 0.10.0 rather than the required 0.13.0 and package-index DNS resolution failed.

The evaluator request intentionally keeps `trace_payload` opaque until Mohab's canonical Trace Schema v1 is frozen and mapped. The current `dev` branch has a Trace Schema v1 draft, not a frozen canonical Pydantic trace model. The request model checks `trace_id`, `schema_version`, and `application_id` consistency when those keys are present, but it does not require them until the owning schema is approved. This is temporary behavior and must not be described as full trace-schema compatibility.

## 7. JSON Schema semantic limits

The JSON Schema files are generated from the Pydantic models and include portable structural/cross-field constraints where possible. Some semantics still require Python-side validation or a canonical trace lookup:

- Recursive ground-truth leakage checks inspect arbitrary nested `trace_payload` keys. The runtime normalizes key casing and separators (for example `goldLabel` and `expected-failure-class`) and traverses mappings, lists, and tuples. A portable schema cannot prohibit a set of keys at arbitrary depth without constraining the still-opaque trace object shape; Pydantic performs this recursive check.
- Envelope-to-payload equality for `trace_id`, `schema_version`, and `application_id` is checked by Pydantic when those keys are present. The generic JSON Schema cannot express arbitrary sibling-value equality.
- `EvidenceReferenceV1.trace_id` must match the annotation/evaluation trace ID at runtime. JSON Schema can require its shape and a concrete target, but cannot compare the referenced ID to a sibling property.
- An `event_id`, `span_id`, `document_id`, `source_id`, `field_path`, or `claim_id` being syntactically present does not prove the target exists in the stored trace. Existence and target semantics require the frozen trace contract and a platform-owned resolver.
- `controlled_scenario_confirmed` requires `intended_failure_class == primary_label`. The schema uses an enumerated `oneOf` to align this v1 finite label set with Python validation. `human_adjudication` may legitimately differ from scenario intent when the intended behavior did not manifest.

These limits and the draft trace schema are integration gates, not permission to infer unknown field aliases.
