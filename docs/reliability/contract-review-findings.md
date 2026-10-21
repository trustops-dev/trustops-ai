# Week 1 contract remediation and integration findings

**Baseline reviewed:** `dev` at `59767ba53a168c4bf39160d8a4620504852063b4` (21 October 2026 review).

**Recommendation:** **NO-GO for merge until P1 blockers are closed.** This review does not create a branch, push commits, open a PR, or claim repository CI results.

## Prioritized findings

| ID | Severity | Finding | Evidence / impact | Required action / owner |
|---|---|---|---|---|
| F-01 | P1 | Scenario-intent schema mismatch | Original Python validator rejected `label_source=controlled_scenario_confirmed` when `intended_failure_class != primary_label`; original JSON Schema accepted the same object. | Remediated in Pydantic model and generated schema: equality is required for scenario-confirmed labels; human adjudication may differ. Ahmed owns semantics. |
| F-02 | P1 | Whitespace-only non-empty strings passed JSON Schema | Original schema used `minLength: 1`, which accepts whitespace-only values; Python used `.strip()` and rejected them. Reproduced for `trace_id`, `annotation_guideline_version`, and `adjudication_note`. | Remediated with `pattern: \\S` on nonblank strings and regression tests. |
| F-03 | RESOLVED (P1) | Canonical Pydantic contracts not implemented/dependency omitted | The original bundle used `TypedDict` plus custom validators and omitted the Pydantic dependency. | The PR now declares `pydantic==2.13.5` in `packages/contracts/pyproject.toml`; the reviewed lockfile includes the contract/test dependencies and the local locked Python checks passed under Python 3.12.15 / uv 0.13.0. The separate inherited `certifi` audit issue is tracked in F-11. |
| F-04 | P1 | Trace-schema contract is not frozen | The `Week 1 Execution Deliverable Trace Schema v1` document describes itself as a draft before contract freeze; the application evidence document explicitly says it is not Mohab's canonical Trace Schema v1. | Mohab must publish/freeze the canonical Pydantic trace model and approve the evaluator adapter/aliases before the evaluator contract can be declared trace-compatible. |
| F-05 | P1 | Evidence target and identity link semantics remain incomplete | The draft envelope uses `event_id`, `parent_event_id`, and ordered `sequence_number`; retrieval docs use `doc_id`. The evaluator contract offers `span_id`, `document_id`, `source_id`, `field_path`, and `claim_id` without a frozen mapping/resolver. IDs can be syntactically valid but point nowhere. | Mohab defines canonical IDs/aliases and a trace evidence resolver; Ahmed writes contract tests after approval. Do not invent aliases. |
| F-06 | P1 | Required CI status is not yet fully green | For PR #19 run `39607792479`, Python CI, Frontend CI, Security, Dependency review, and Frontend dependency audit passed; the Python dependency audit failed on the pre-existing `certifi` pin recorded in F-11. Local validation under Python 3.12.15 / uv 0.13.0 passed after remediation: locked installation, Ruff, format, strict mypy, five import-linter contracts, 84 unit/contract tests, and hash-verified `pip-audit` with no known vulnerabilities found. | The local checks are green. An authorized follow-up commit must trigger GitHub's required checks again; do not mark the remote dependency audit as passed until its result is confirmed. Trace mapping and evidence resolution remain separately documented as pending. |
| F-07 | P2 | Expected tool/workflow sequence duplicate handling | Original Python `_string_list` rejected duplicate entries in expected sequences even though schema allowed them and valid trajectories may call the same tool repeatedly. | Remediated: expected document-ID sets remain unique; repeated tool/transition sequence entries are allowed. |
| F-08 | P2 | Recursive leakage and cross-field constraints exceed schema expressiveness | An opaque `trace_payload` makes portable JSON Schema unsuitable for prohibiting ground-truth keys at arbitrary depth or comparing nested payload IDs with envelope siblings. Evidence-reference existence also requires stored-trace access; in-memory non-finite floats are rejected by Python. | Pydantic checks recursive leakage and known identity comparisons; limits are documented. Full enforcement waits for the frozen trace model/resolver. |
| F-09 | P2 | Trace/run result link fields need owner agreement | Draft requires stored evaluator results linked to `trace_id` and `evaluation_run_id`; this evaluator output has optional `execution.run_id` and does not define an authoritative `evaluation_run_id`. | Mohab + Ahmed agree run-envelope field name; align dataset/RQ metadata with Alaa. |
| F-10 | P2 | Annotation persistence and taxonomy precedence remain unresolved | Dataset draft says adjudicated-label persistence is pending and overlap precedence needs Ahmed sign-off. Mohamed owns policy truth. | Ahmed + Mohab agree annotation storage contract; Nour signs scenario semantics; Mohamed confirms policy evidence. Keep taxonomy status as candidate. |
| F-11 | P1 | Python dependency audit failed on a vulnerable inherited certifi pin | Run `39607792479`, job `119248414957`, reported `certifi==2026.7.22` / `PYSEC-2026-4320`, fixed in `2026.10.19`. The same `2026.7.22` pin exists in base `dev` at `59767ba53a168c4bf39160d8a4620504852063b4`, so this vulnerability predates Ahmed's PR; the PR did not introduce it. | Remediated in this local follow-up: uv 0.13.0 resolves `certifi==2026.10.19`; locked workspace installation and the repository's hash-verified `pip-audit` command passed with no known vulnerabilities found. GitHub's Python dependency audit still must rerun on the follow-up commit; do not represent that remote check as passed before it runs. |

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

Pydantic is **required by the supplied approved architecture** for canonical cross-module contracts. The remediated sources use Pydantic v2 models. Under Python 3.12.15 / uv 0.13.0, the locked workspace installation passed, `certifi` resolves to `2026.10.19`, and the hash-verified local `pip-audit` reported no known vulnerabilities. GitHub's required Python dependency audit must still rerun on the follow-up commit; its remote result is pending. **PENDING:** canonical Trace Schema v1 mapping and evidence-reference resolution remain unimplemented and unapproved. The responsible owners must resolve the outstanding cross-team decisions and confirm the applicable merge gates. Do not claim trace compatibility or full merge readiness before the required checks and decisions are complete.

## Required cross-team decisions

- **Mohab:** freeze trace v1 Pydantic models, canonical request/event IDs, `schema_version`, document ID alias, span support, evidence-resolution semantics and `evaluation_run_id` linkage.
- **Nour:** confirm scenario injection/normal-control semantics and realistic traces; scenario execution remains outside Ahmed's ownership.
- **Alaa:** confirm `split_group_key`, dataset/split/fingerprint/run versions, leakage exclusions, and persistence of independent intended vs adjudicated labels.
- **Mohamed:** identify authoritative policy verdict/rule/status/criticality fields and approve policy/workflow overlap handling.
- **Malak:** confirm stable result/evidence fields needed for display; do not map UI payloads onto an unapproved trace alias.
- **Ahmed:** own label definitions, annotation rules and adjudication guide; keep status at candidate until sign-offs land.

## Merge gate

All P1 items must close, with the minimum evidence below:

1. The local lock refresh is complete under uv 0.13.0: `certifi==2026.10.19`, locked installation, and the hash-verified local dependency audit passed. The GitHub Python dependency audit must rerun after an authorized follow-up commit before this gate is considered closed.
2. Contract regression tests pass in the locked Python 3.12 workspace.
3. Ruff lint/format, strict mypy, import-linter, and `pytest tests/unit tests/contract` pass exactly as documented.
4. **PENDING — trace mapping and evidence resolver:** Mohab's canonical Trace Schema v1 model, field/ID mapping (including document aliases), and resolver for event/span/document/claim existence have not been delivered or approved here. Do not claim trace compatibility; the owners must explicitly decide whether this remains a pre-merge gate or is tracked as a separately owned follow-up before merge.
5. Cross-team owner sign-offs and outstanding field aliases/persistence fields are recorded in the PR.
