# Week 1 contract remediation and integration findings

**Baseline reviewed:** `dev` at `59767ba53a168c4bf39160d8a4620504852063b4` (21 October 2026 review).

**Recommendation:** **NO-GO for merge until P1 blockers are closed.** This review does not create a branch, push commits, open a PR, or claim repository CI results.

## Prioritized findings

| ID | Severity | Finding | Evidence / impact | Required action / owner |
|---|---|---|---|---|
| F-01 | P1 | Scenario-intent schema mismatch | Original Python validator rejected `label_source=controlled_scenario_confirmed` when `intended_failure_class != primary_label`; original JSON Schema accepted the same object. | Remediated in Pydantic model and generated schema: equality is required for scenario-confirmed labels; human adjudication may differ. Ahmed owns semantics. |
| F-02 | P1 | Whitespace-only non-empty strings passed JSON Schema | Original schema used `minLength: 1`, which accepts whitespace-only values; Python used `.strip()` and rejected them. Reproduced for `trace_id`, `annotation_guideline_version`, and `adjudication_note`. | Remediated with `pattern: \\S` on nonblank strings and regression tests. |
| F-03 | P1 | Canonical Pydantic contracts not implemented/dependency omitted | Approved repository architecture calls `packages/contracts` the canonical cross-module Pydantic-contract layer. Original bundle used `TypedDict` plus custom validators and had no Pydantic dependency/lock entry. | Remediated in source as Pydantic v2 models; `pydantic==2.13.5` is declared in `packages/contracts/pyproject.toml`. **Still blocked:** regenerate `uv.lock` with pinned uv 0.13.0. Current environment had uv 0.10.0 and package-index DNS failure. Do not merge with a stale lockfile. |
| F-04 | P1 | Trace-schema contract is not frozen | The `Week 1 Execution Deliverable Trace Schema v1` document describes itself as a draft before contract freeze; the application evidence document explicitly says it is not Mohab's canonical Trace Schema v1. | Mohab must publish/freeze the canonical Pydantic trace model and approve the evaluator adapter/aliases before the evaluator contract can be declared trace-compatible. |
| F-05 | P1 | Evidence target and identity link semantics remain incomplete | The draft envelope uses `event_id`, `parent_event_id`, and ordered `sequence_number`; retrieval docs use `doc_id`. The evaluator contract offers `span_id`, `document_id`, `source_id`, `field_path`, and `claim_id` without a frozen mapping/resolver. IDs can be syntactically valid but point nowhere. | Mohab defines canonical IDs/aliases and a trace evidence resolver; Ahmed writes contract tests after approval. Do not invent aliases. |
| F-06 | P1 | Lockfile and full CI not verified | Root CI requires locked installation, Ruff lint/format, strict mypy, import-linter, and full tests on Python 3.12/uv 0.13.0. Local environment is Python 3.13.5/uv 0.10.0; Ruff/mypy/import-linter are unavailable and package-index DNS fails. | Regenerate the lockfile with the pinned toolchain, then run all documented checks in the actual workspace. |
| F-07 | P2 | Expected tool/workflow sequence duplicate handling | Original Python `_string_list` rejected duplicate entries in expected sequences even though schema allowed them and valid trajectories may call the same tool repeatedly. | Remediated: expected document-ID sets remain unique; repeated tool/transition sequence entries are allowed. |
| F-08 | P2 | Recursive leakage and cross-field constraints exceed schema expressiveness | An opaque `trace_payload` makes portable JSON Schema unsuitable for prohibiting ground-truth keys at arbitrary depth or comparing nested payload IDs with envelope siblings. Evidence-reference existence also requires stored-trace access; in-memory non-finite floats are rejected by Python. | Pydantic checks recursive leakage and known identity comparisons; limits are documented. Full enforcement waits for the frozen trace model/resolver. |
| F-09 | P2 | Trace/run result link fields need owner agreement | Draft requires stored evaluator results linked to `trace_id` and `evaluation_run_id`; this evaluator output has optional `execution.run_id` and does not define an authoritative `evaluation_run_id`. | Mohab + Ahmed agree run-envelope field name; align dataset/RQ metadata with Alaa. |
| F-10 | P2 | Annotation persistence and taxonomy precedence remain unresolved | Dataset draft says adjudicated-label persistence is pending and overlap precedence needs Ahmed sign-off. Mohamed owns policy truth. | Ahmed + Mohab agree annotation storage contract; Nour signs scenario semantics; Mohamed confirms policy evidence. Keep taxonomy status as candidate. |

## Trace integration matrix

| Concern | Current evaluator contract | Trace v1 draft | Disposition |
|---|---|---|---|
| Trace identity | `trace_id` in request and evidence references | Top-level `trace_id`; `event_id` local to trace | Runtime equality check exists for known envelope keys; referenced-event existence requires resolver. |
| Schema version | Request `trace_schema_version` | Payload `schema_version` | Checked for equality when payload key is present; not required until schema freeze. Add a typed envelope when approved. |
| Application identity | Request `application_id` | Payload `application_id` and `application_type` | `application_id` checked when present; allowed values and application-type alignment await freeze. |
| Event/span refs | Evidence supports `event_id` and `span_id` | Draft event requires `event_id`, parent link and monotonic sequence; a canonical span alias is not established in the reviewed document | `span_id` mapping remains unresolved; no alias inferred. |
| Retrieval document refs | `document_id`, expected relevant/citation document IDs | Retrieved documents use `doc_id`, source metadata and explicit 1-based rank/score | Resolve `doc_id` ↔ `document_id` with Mohab before contract freeze. |
| Claim support | `claim_id`, `source_id`, `field_path` optional evidence targets | Draft requires claim → retrieved span → source/version → visible citation linkage | Target existence and semantic support require canonical linked records, not just JSON shape. |
| Ground-truth isolation | Pydantic recursively rejects forbidden label/attack keys inside trace payload | Draft puts scenario metadata in controlled dataset traces but requires it be stripped from inference inputs | Keep dataset metadata out of evaluator input; make the projection explicit in Mohab/Alaa adapter. |
| Evaluation result lineage | `trace_id`, optional `execution.run_id` | Stored evaluator results linked to `trace_id` and `evaluation_run_id` | Field name and persistence owned by Mohab; unresolved. |

## Architecture decision

Pydantic is **required by the supplied approved architecture** for canonical cross-module contracts. The remediated sources use Pydantic v2 models. The current `uv.lock` cannot safely be handcrafted: artifact hashes and the dependency graph must be generated with the required pinned uv toolchain. Tool-version mismatch and package-index access prevented that regeneration in this session. This is a real P1 release blocker.

## Required cross-team decisions

- **Mohab:** freeze trace v1 Pydantic models, canonical request/event IDs, `schema_version`, document ID alias, span support, evidence-resolution semantics and `evaluation_run_id` linkage.
- **Nour:** confirm scenario injection/normal-control semantics and realistic traces; scenario execution remains outside Ahmed's ownership.
- **Alaa:** confirm `split_group_key`, dataset/split/fingerprint/run versions, leakage exclusions, and persistence of independent intended vs adjudicated labels.
- **Mohamed:** identify authoritative policy verdict/rule/status/criticality fields and approve policy/workflow overlap handling.
- **Malak:** confirm stable result/evidence fields needed for display; do not map UI payloads onto an unapproved trace alias.
- **Ahmed:** own label definitions, annotation rules and adjudication guide; keep status at candidate until sign-offs land.

## Merge gate

All P1 items must close, with the minimum evidence below:

1. `uv.lock` regenerated under uv 0.13.0 after adding Pydantic and schema-test dependencies; locked install succeeds.
2. Contract regression tests pass in the locked Python 3.12 workspace.
3. Ruff lint/format, strict mypy, import-linter, and `pytest tests/unit tests/contract` pass exactly as documented.
4. Mohab's approved Trace Schema v1 Pydantic model is imported in a schema compatibility test, and representative Procurement and RAG traces satisfy it.
5. Cross-team owner sign-offs and outstanding field aliases/persistence fields are recorded in the PR.
