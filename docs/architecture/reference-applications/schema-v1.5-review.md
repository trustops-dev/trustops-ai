# Application review of Mohab's Trace Schema Draft v1.5

**Current review pointer — 2026-11-05:** [v1.6 schema / governance 0.4 joint review](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal) is the latest supplied review (R16-01–09; CHANGES REQUIRED). The maintained row-by-row E01–E27 mapping below remains a v1.5 assessment, not a v1.6 acceptance. Its original requirement identities, field evidence and findings are preserved for comparison; a v1.6 mapping update is a separate pending task. Current decision questions are in [open-decisions.md](open-decisions.md).

Review date: 2026-11-04. Scope: Nour-owned application requirements, the supplied specification, fixtures and offline validator. **Disposition: CHANGES REQUIRED; OD-05 and shared freeze remain pending.**

This is the historical supplied-draft review for v1.5. It supersedes current-status statements in the [historical v1.2 review](schema-v1.2-review.md) and [v1.1 review](schema-v1.1-review.md). It does not certify a pushed schema, backend implementation, runtime enforcement or stakeholder acceptance. The original E01–E27 and WG-01–08 requirement identities remain unchanged. The [v1.5 row-by-row mapping](trace-evidence-contract.md#current-v15-application-to-schema-mapping) is now documented by the 2026-11-05 addendum below; the older repository-draft table is historical. Mapping coverage does not establish acceptance.

## Exact inputs and comparison baseline

The uploaded originals were read without modification. Filename suffixes are not authoritative version identifiers: the specification internally says **Draft v1.5**, and the supplied validator reports **1.5.0** despite its v1_4 filename.

| Reviewed filename | Bytes | SHA-256 of exact received bytes |
|---|---:|---|
| `updated_schemas_v5.md` | 296719 | `41292bd17ff225977b6c9c6c52b6247f7b223b00798b2a21638caa6a7d5d4321` |
| `validate_s1_01_schema_v1_4(1).py` | 99387 | `5c4dbaa3f4ba457f855445e055032b0362003c57048202c4d79d897abbfc169c` |
| `run_s1_01_regression_suite.py` | 11891 | `e90eb47584d720fa132bfcee2688a72ce82b9c710b2b1ab2defb7e075578e8a0` |
| `s1_01_validation_report.json` | 122193 | `c1d9b7d2e8e32473e802c585ccf876f556ba5c85fa876af9e9ac7737666763ae` |

Comparison contracts: [Procurement tools 0.8](procurement-tool-contracts.md), [Procurement states 0.7](procurement-state-contract.md), [RAG 0.9](rag-contract.md), [application trace evidence](trace-evidence-contract.md) and [execution budgets 0.1, proposed](../../adr/application-execution-budgets.md). Their exact comparison hashes at the 2026-11-04 review are retained in the [observation record](schema-v1.5-review-observations.json); current packet hashes are in the [manifest](week1-review-manifest.json). The 2026-11-05 mapping addendum changes the trace-evidence review section while preserving its minimum requirements and historical mapping; the earlier observation record is not rewritten as if those later bytes were reviewed on 2026-11-04.

Latest GitHub `main` was rechecked as `3ef7da1f190cd5a22efdcd6798af59199924bac3` using read-only Git after the web viewer failed. Relevant main-branch documentation remains an earlier review package. The supplied v1.5 files are external review inputs, not evidence of that revision being committed or deployed. The existing local task branch and unrelated working changes were preserved.

## Application evidence mapping addendum — 2026-11-05

All original **E01–E27** requirements now have a current v1.5 representation, cited specification section/walkthrough, status, owner and next action in [the maintained evidence contract](trace-evidence-contract.md#current-v15-application-to-schema-mapping). The [machine-readable review mapping](schema-v1.5-evidence-mapping.json) preserves each original minimum-evidence requirement and records concrete representative fixture paths.

| Mapping status | Count | Requirement IDs |
|---|---:|---|
| OK — structural evidence representable in the stated scope | 5 | E01, E05, E09, E15, E19 |
| CHANGE REQUIRED — linked to reproduced V15 findings | 15 | E04, E08, E11, E12, E14, E16, E17, E18, E20, E21, E22, E23, E24, E25, E27 |
| OPEN — exact convention or owner decision still needed | 7 | E02, E03, E06, E07, E10, E13, E26 |

OPEN rows identify the remaining mapping questions: model failure/per-call provenance; effective policy-query/filter evidence; score tie/count conventions; selector version and sufficiency interpretation; state/stage-map identity and permissions; approval-submission replay/continuation; and immutable configuration/lineage/missingness conventions. These are explicit review questions, not invented canonical fields or new runtime defect claims. V15-07 regression packaging remains cross-cutting.

**Coverage is complete; acceptance is pending.** An OK row does not establish runtime behavior, semantic correctness, policy authorization or team approval. Intentional bad-answer/bypass traces remain useful failure evidence. WT4 is not a positive grounded-answer or abstention demonstration. OD-05 remains BLOCKING; OD-APP-OBS-01 remains CLOSED — SEMANTICS ONLY.

## Verified fixes to retain

“Verified” here means observed in the supplied document/fixtures or reproduced with the offline validator. It does not close the whole related E/WG requirement or grant approval.

| Area | Verified improvement | Remaining boundary |
|---|---|---|
| Snapshot representation | Walkthroughs include required authorization-snapshot keys, dependency references and explicit unresolved policy identity before `search_policy` | Actual source evidence must still be compared with copied snapshots: V15-01 |
| PO state revisions | Checked source revision and resulting dispatch revision are separate; the bound atomic `APPROVED → PO_CREATION` transition is represented and a broken-transition probe is rejected | Claim identity, source truth and shared transaction agreement remain open |
| Business payloads and errors | Trace-only diagnostics are outside strict business payloads; `UNKNOWN_OUTCOME` keeps a null business error; ERROR/null-data and UNRESOLVED branches execute without the earlier null-object failure | Result/outcome consistency and fixture counters remain V15-02/03 |
| Lifecycle definitions | Proposal, validation, suppression, invocation, result and recovery definitions are restored; raw/malformed fields are represented; `UNRESOLVED_TIMEOUT` is a recovery reason under `RECOVERY_PENDING` | Representation alone does not validate raw JSON or replay identity: V15-02/06 |
| Source provenance and rendered context | Canonical chunk slices, source spans and formatting prefixes are present; recorded context assembly is explicit; WT4's runtime `POL-119` leakage was removed | Citation version/selected-slice checks and leakage false positives remain V15-04/05 |
| Budget mapping | Proposed budget context and telemetry are mapped outside model-visible arguments; values remain `PROPOSED_NOT_RATIFIED` | Counter arithmetic, fencing consistency, retry fields and fixture accounting remain V15-03/06 |
| Previously weak validation rules | Fresh mutations for corrupt digests, missing authorization references, invalid ordering/parents, missing snapshots and nonexistent citation chunks are rejected | These checks do not establish complete evidence consistency; independent probes below expose remaining gaps |
| Requirement/status records | Original E/WG requirement names are represented in the draft; full signatures remain pending and approval-observation semantics remain separately confirmed | Nour's complete application-fit acceptance and named specialist approvals are still pending |

Do not resend superseded v1.2 findings as though all remain unchanged. Preserve these fixes while closing the narrower remaining defects.

## Remaining findings and required return

V15 IDs identify this review's findings, not new canonical schema requirements. Owners below identify correction/review responsibility, not accepted commitments.

| ID | Observed issue and required correction | Owner / closure evidence |
|---|---|---|
| **V15-01 — Source-backed authorization** | WT1 still passes after changing the supplier result to NOT_APPROVED, the approval event to DENIED, or root request amount to `1.00` while later snapshots/PO arguments retain the original successful values. Duplicate policy IDs can replace the required policy set, and the snapshot's dispatch-claim ID can disagree with dispatch. Resolve real supplier/calculation/approval records and compare exact request revision, supplier, amount, currency, policy/version and dispatch identity; enforce required policy identities and uniqueness. Copied booleans are not proof. | **Mohab** corrects validator/fixtures; **Mohamed** confirms authority/binding rules; **Nour** reviews application fit. Contradictory bindings must produce explicit consistency findings and cannot be certified as verified success. E08/E11–18/E20; WG-02/03. |
| **V15-02 — Recovery and terminal outcomes** | WT3 passes when the recovery lookup uses another idempotency key or business-payload digest, and when a TIMEOUT/UNKNOWN_OUTCOME result is changed to side-effect NONE. WT1 also passes with a second terminal result for the same invocation. Bind recovery to the original call/request/key/digest, compare recovered evidence, enforce compatible execution/business/effect states, and allow only one terminal result per invocation. Reconciliation is a separate append-only event. | **Mohab** corrects representation checks/fixtures; **Mohamed + Ahmed** review recovery and outcome meaning; **Nour** verifies application behavior. Matching recovery must pass; mismatches must be identified; no automatic PO redispatch is introduced. E20/E21/E25; WG-04/08. |
| **V15-03 — Budget consistency and fixture accounting** | Negative spent counters, missing counters and a changed dispatch fencing token without matching context still pass. WT2 declares prior tool work but reports zero tool attempts. POS-11/POS-12 retain full-success counters despite fewer calls; POS-12's explanation also says EUR while its request/basis uses USD. Validate required integer counters, nonnegative values, ceiling/spent/reserved/remaining arithmetic, root/lease/fencing identity and consumed attempts. Clarify cumulative versus segment-local counters and identify any prior snapshot in partial traces; correct fixture accounting and currency prose. | **Mohab** updates validator/fixtures; **Nour** checks budget-contract fit; **Mohamed/Alaa** review transaction/workload proposals. Numeric limits remain proposed under OD-12; no durable-ledger implementation is claimed. E20/E25/E26; WG-04/06. |
| **V15-04 — Legitimate retrieval versus label leakage** | Adding already-retrieved `POL-114` to WT1's expected-relevant-document sidecar causes rejection solely because the same ID exists in runtime evidence. A global string blacklist confuses real retrieval with ground-truth leakage. Validate provenance and inference projection boundaries: prohibit copying labels/qrels/recipes into inference inputs while allowing identifiers independently returned by retrieval. | **Mohab + Alaa**, with **Ahmed** on annotation semantics and **Nour** on retrieval behavior. Add paired tests for legitimate identifier overlap and actual sidecar-to-prompt/rationale leakage. E27; WG-07. |
| **V15-05 — Citation version and selected-passage containment** | WT4 passes with visible citation version `v999`. It also passes after the selected FAQ slice and rendered context are shortened consistently while the final source quote remains outside the supplied slice and still claims `in_supplied_prompt_context: true`. Resolve exact retrieval/document/chunk/version identities, enforce valid span bounds and containment within the context supplied to the generating call, and recompute membership flags. | **Mohab** implements structural checks; **Nour** reviews the RAG contract; **Ahmed** owns semantic support interpretation. Both mutations must produce citation-consistency findings. Structural validity remains distinct from entailment. E05/E07/E22/E23; WG-05/08. |
| **V15-06 — Raw arguments, empty retrieval and retry fields** | Malformed raw JSON can pass while marked PARSED_OBJECT/VALID. A zero-document retrieval is rejected by a hardcoded nonempty-list rule. The documented optional `retry_accounting` object on a tool call is rejected as an unknown key. Parse raw input and compare it with parsed/normalized values under the documented rules; allow successful empty retrieval and represent abstention separately from technical error; align allowed fields and retry accounting with §4.7. | **Mohab** corrects definitions/validator/fixtures; **Nour** reviews app behavior; **Ahmed** reviews abstention/failure meaning. Include malformed and non-object JSON, legitimate empty retrieval plus a complete abstention fixture, and documented retry metadata. The existing empty-retrieval probe is an active retrieval-stage fragment, not a full validated abstention trajectory. E04/E16/E24/E25; WG-04/05/08. |
| **V15-07 — Reproducible regression package and accurate claims** | The runner hardcodes old filenames and an optional machine-specific path. Its self-contained execution has 13 cases; the supplied report has 18 including five optional old probes. NEG-10's table describes a duplicate PO call/claim, but the code mutates a supplier call's authorization-check reference. Checking a substring does not establish the claim of zero unrelated failures. Accept explicit input paths or bundle exact inputs; disclose optional cases; align descriptions with actual mutations; check failure sets or narrow the claims. | **Mohab** returns a self-contained corrected package with exact hashes, commands and results; **Nour** verifies reproduction. Preserve expected failure traces and report scope accurately. Supports OD-05/13/14. |

These are consistency/certification requirements. Intentionally failing or contradictory application traces must remain available to evaluation. A business-policy failure is not by itself a reason to discard a trace at ingestion; the validator must distinguish representable failure evidence from assertions that incorrectly certify its bindings or outcome as valid.

## Reproduced validation and limits

The [observation record](schema-v1.5-review-observations.json) contains exact input and comparison hashes, category counts, probe mutations, probe hashes and observed errors. Offline checks were rerun on 2026-11-04 without modifying the supplied inputs.

| Check | Observed result | Interpretation |
|---|---|---|
| Supplied validator against unmodified v1.5 Markdown | **2023 assertions, 0 failures**: envelope 167; ordering/references 1064; hashes/spans 198; contracts/bindings 550; isolation/report 44 | Baseline passes this validator; not complete semantic verification |
| Self-contained supplied regression runner | **13 cases match its expectations**: baseline, 10 negative mutations, 2 positive variants; zero uncaught exceptions | Reproduced with byte-identical copies under the runner's required filenames |
| Additional independent checks | **20 cases:** 2 unchanged controls pass; 15 inconsistent mutations pass unexpectedly; 3 targeted permitted-shape/provenance checks are rejected | Demonstrates remaining validation gaps; not a production defect count or acceptance result |
| Walkthrough bundle digest | `907aea127e57f71b12496b1b6cb46e8319b95a564f306659ff7fc2ab740a58fe` | Exact digest from the supplied validator; no cross-language canonicalization guarantee |

The supplied report's validator SHA-256 (`39a71e9e9741275a701d2bc80cb86bc6a4abf29ffc02f57d2da48afada935bea`) differs from the received file only by one final LF byte: adding that byte exactly reproduces the reported hash. Record both byte identities; this is a packaging difference, not evidence of a different algorithm.

### Reproduction of the supplied baseline and suite

Use the exact received inputs in an isolated directory. The runner writes its report and probes beside itself; do not run it where it could overwrite the supplied report. These commands assume the three executable/specification inputs named in the table are in the current directory:

```bash
python3 'validate_s1_01_schema_v1_4(1).py' updated_schemas_v5.md
REVIEW_RUN_DIR="$(mktemp -d)"
cp updated_schemas_v5.md "$REVIEW_RUN_DIR/updated_schemas_v4.md"
cp 'validate_s1_01_schema_v1_4(1).py' "$REVIEW_RUN_DIR/validate_s1_01_schema_v1_4.py"
cp run_s1_01_regression_suite.py "$REVIEW_RUN_DIR/run_s1_01_regression_suite.py"
python3 "$REVIEW_RUN_DIR/run_s1_01_regression_suite.py"
```

The 13-case result assumes the runner's optional `/tmp/review_v1_4/TrustOps_Mohab_v1_4_Review_Attachments/negative-probes` directory is absent. If present, report those extra inputs separately with their hashes. Rejection of old-schema probes alone is not proof of each newly added rule. The independent checks in the observation record use `Validator.validate_trace` on copies of the indicated walkthrough, applying only the recorded mutation (or its explicitly described consistent multi-field updates). Their payloads remain review evidence; this update records them and does not claim the supplied runner includes them.

## Required handoff and unchanged gates

- Mohab returns the corrected specification, validator, runner and fixtures with a disposition for **V15-01–07**, exact hashes and reproducible results. Nour reviews application compatibility; the canonical schema and validator remain Mohab's responsibility.
- Mohamed reviews authorization, validity, transaction and replay/recovery decisions; Ahmed reviews evidence/failure interpretation; Alaa reviews provenance/projections; Malak reviews outcome/evidence presentation.
- **OD-05 remains BLOCKING; full specialist sign-offs and formal freeze remain PENDING.** A baseline validator PASS is not specialist approval.
- **OD-APP-OBS-01 remains CLOSED — SEMANTICS ONLY.** Trusted read-only observation is distinct from initial submission. Adapter proof, approval validity/expiry/revocation, broader continuation and numeric budgets remain separate pending gates.
- No backend, SDK, purchasing tool, provider API, embedding/index, policy engine or dashboard was executed. No code was pushed, no message was sent and no new approval was recorded. Existing prompt/corpus reports retain their original scope.
