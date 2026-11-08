# Week 1 — Nour's owner-side closeout and review packet

**Credential and runner update — 2026-11-08.** Replacement `TrustOpsAI-dev` and old-key absence were observed on 2026-11-07; local storage is Nour’s confirmation. Live authentication is not verified. The [bounded compatibility runner](../../../tools/provider_compatibility/README.md) implements isolated synthetic probes with offline SDK tests. Full-envelope token admission, live results and application acceptance remain open. Nour runs the local probes and returns sanitized results; Mohab reviews interface/admission integration; Alaa reviews quota/workload evidence. No model promotion or shared approval is implied.

**Current workload candidates — 2026-11-07.** The [free-only 0.2 baseline](workload-review/od-llm02-v0.2/README.md) and [Flash Lite 0.3 alternative](workload-review/od-llm02-v0.3/README.md) supersede the earlier USD 10 allocation proposal with a USD 0 paid-spend requirement. Ownership is user-reported and free-tier quotas are screenshot-observed as recorded in the supplied update; capture times, remaining quota and runtime compatibility remain unverified. Flash remains the current proposed primary. Lite promotion requires scoped application/interface/workload review and executed evidence. Alaa’s prior response remains partial/conditional against its original revision. Credential replacement is observed and local storage is user-confirmed. Quota headroom, API execution, OD-03/OD-04 acceptance and the existing schema gates remain pending.

**Workload proposal prepared — 2026-11-06:** [API ownership and workload candidate 0.1](workload-review/od-llm02-v0.1/README.md) supplies execution/call/token/retry/concurrency estimates and public-price token subtotals. Actual API project/access/billing owner, account quotas and applicable charges remain unconfirmed. ALA-05/ALA-08 and OD-LLM-02/OD-12-BUDGET stay open; no live execution is authorized.

**Alaa response recorded — 2026-11-06:** [Scoped review of commit 479cab0](reviews/alaa-479cab0-review.md) received from user-supplied email text. Overall status: **PARTIAL / CONDITIONAL**. Candidate/principle acceptance and remaining conditions are recorded separately; no full specialist sign-off or joint freeze. The email date and message reference were not supplied.

**Current publication and handoff** is recorded in [the PR #27 publication record](publication-handoff.md). Earlier preparation metadata is the pre-publication snapshot.

**Current mapping — 2026-11-06:** [Draft v1.6 E01–E27 assessment](schema-v1.6-evidence-mapping.md) and [exact row evidence](schema-v1.6-evidence-mapping.json) cover all 27 requirements: **9 OK, 9 CHANGE REQUIRED, 9 OPEN**. The [rerun observations](schema-v1.6-review-observations.json) retain R16-01–09 as the current review baseline. v1.5 is historical comparison evidence. Mapping preparation is complete; corrected files, unresolved conventions and joint acceptance remain pending. OD-05 stays blocking; no new signature or runtime verification is implied.

**Reproducible review checks:** the [validation guide and packaged helpers](validation/README.md) provide repository/output arguments and exact commands for the paper fixtures, corpus/boundaries and existing prompt examples. These remain offline artifact checks; shared acceptance and runtime validation are pending.

**Revision 0.8 completion:** items 5 (corpus specification) and 6 (boundary cases) are now explicitly delivered. Revision 0.7 had not fully consolidated those two items; this update closes that drafting gap only. Shared approvals and runtime gates remain open.

Revision 0.14 · 2026-11-06 · Task S1-01 · Status: **OWNER DRAFTING COMPLETE FOR REVIEW; SHARED FREEZE PENDING**.

**Revision 0.9 scoped confirmation:** [OD-APP-OBS-01](open-decisions.md#approval-observation-confirmation) records Mohamed/Mohab agreement, reported by the user, that approval observation is trusted read-only observation of an existing request, distinct from retrying initial submission. State contract 0.7 and tool contract 0.8 apply this wording. Full specialist sign-offs, adapter verification, approval validity, continuation and numeric budgets retain their separate gates.

This packet completes the identified documentation work that Nour can perform independently. It does not mark Week 1 jointly accepted, execute Sprint 2 applications, send messages or grant approvals. The maintained application contracts remain proposals until accepted by their reviewers.

**Current revision 0.14 — v1.6 mapping and validation status:** all E01–E27 requirements are assessed against the pinned v1.6 draft: 9 OK, 9 CHANGE REQUIRED and 9 OPEN. During the 2026-11-06 mapping update, the external validator baseline, supplied suite and independent helper were rerun offline: 2,106 baseline assertions with no failures, 27/27 supplied expectations met, and 19/35 independent expectations met (16 unmet). The [recorded observations](schema-v1.6-review-observations.json) preserve these results. The separate earlier independent CLI cross-check was not rerun. This wording cleanup does not rerun or repair the schema validator; it refreshes affected owner-document checks and packet hashes. Full schema acceptance, specialist sign-offs and runtime verification remain pending.

**Historical revision 0.13 — 2026-11-05:** the decision/reference refresh used the existing [v1.6 joint review](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal), labelled v1.5 evidence as historical, and routed 20 focused requests through the decision register and handoffs. That earlier refresh reran owner artifact checks only; it did not rerun Mohab's validator. The later v1.6 mapping rerun is recorded above.

## Completed owner work

**Historical revision 0.12 evidence mapping — superseded by the separate v1.6 assessment:** [E01–E27 now map to the supplied v1.5 draft](trace-evidence-contract.md#current-v15-application-to-schema-mapping), with [machine-readable row evidence](schema-v1.5-evidence-mapping.json): 5 OK, 15 CHANGE REQUIRED and 7 OPEN. Every row has existing field paths, specification/walkthrough references, owners and next actions. Original evidence requirements and the historical mapping are preserved. Mapping coverage is complete; schema corrections, unresolved conventions and specialist acceptance remain pending.

| Work | Deliverable / evidence | Result and boundary |
|---|---|---|
| Procurement behavior and tool definitions | [State](procurement-state-contract.md), [tools](procurement-tool-contracts.md) | Drafted; exact money, trusted context, state/dispatch and unknown-outcome rules explicit |
| Provider/configuration proposal | [Provider ADR 0.9](../../adr/reference-application-orchestration-and-llm.md) | API/SDK/profile/context/prompt/schema proposals present; live compatibility pending |
| Retrieval proposal | [RAG 0.9](rag-contract.md) | Embeddings, chunks, k, filtering, citations, abstention and conditional store explicit |
| Execution limits | [Budget ADR 0.1](../../adr/application-execution-budgets.md) | Proposed counters/deadlines/retries/recovery rules; shared acceptance pending |
| Prompt/example preparation | [Prompt pack 1.1](prompt-pack.md) | Nine templates, 12 Procurement and 10 RAG illustrations; offline review only |
| Failure coverage and scheduling request | [Failure matrix](failure-planning-matrix.md) | SC-01–03 specifications and Week 7 build / Week 8 integration proposal complete; plan amendment not approved |
| Trace-fit review and historical mapping | [v1.5 review](schema-v1.5-review.md), [E01–E27 mapping](trace-evidence-contract.md#current-v15-application-to-schema-mapping), [row evidence](schema-v1.5-evidence-mapping.json) | 27 v1.5 rows: 5 OK / 15 CHANGE REQUIRED / 7 OPEN; historical V15-01–07 dispositions; v1.6 findings and the completed current mapping are recorded separately; original IDs preserved; full application-to-schema acceptance remains pending |
| Corpus specification and samples | [Corpus review](corpus-review/README.md), [RAG specification](rag-contract.md#synthetic-corpus-specification--review-v1) | Eight source samples, metadata, two snapshots and eight relevance/conflict cases; no index built |
| Boundary cases | [Consolidated matrix](manual-boundary-cases.md) | Ten manual cases including denied approval and symbolic below/equal/above T; no runtime execution |
| Paper walkthroughs | [Four application fixtures](fixtures/README.md) | Existing authored fixtures retained; no invented canonical conversion |
| Decision/status cleanup | [Decisions](open-decisions.md), [acceptance](acceptance.md) | Drafted proposals separated from verification and team acceptance |
| Exact-version handoff | [Manifest](week1-review-manifest.json), [handoffs](handoffs.md) | Paths, byte hashes, document revision markers and review scope; nothing sent |

## Proposed configuration handoff

These values are inherited from the owning documents, not new production defaults. Follow the linked contract for complete limits and overrides.

| Area | Proposed baseline | What remains external or future |
|---|---|---|
| Generation | Gemini Developer API, gemini-3.8-flash, candidate google-genai 2.34.0; Interactions v1beta; explicit Python orchestration | API account, exact SDK/wire compatibility and shared acceptance |
| Sampling/context | Omit temperature/top_p/top_k for the selected generation profile; operation-specific thinking/output/input caps in ADR §4 | Live parameter and context-protocol checks |
| Embeddings | gemini-embedding-001, 768 dimensions; document/query task modes; client L2 normalization | Access, exact provider response, dimension/norm and quality checks |
| Chunking | Section-aware; target 512, maximum 640, overlap up to 64 chunker tokens | Loader/tokenizer and native-provider token-limit verification |
| Retrieval | One eligible-set exact cosine search; up to 20 candidates and 5 returned chunks; no numeric relevance cutoff | Actual backend, ACL/filter mapping, corpus/index and development evaluation |
| Vector store | PostgreSQL + pgvector | **Unconfirmed — conditional on environment verification**; fallback requires explicit review |
| Runtime budgets | Procurement 8 logical generations/12 attempts; RAG 1/2; foreground 300 s / 120 s; one original PO creation dispatch claim | Mohamed/Mohab transaction agreement and Alaa workload review |

Official model documentation was rechecked on 2026-11-02: [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) documents the selected identifier, function calling and structured outputs. This confirms documentation availability only, not this project's entitlement, SDK installation or runtime behavior. No new provider design was selected during this closeout.

## Requests ready for owner review — not sent

| Reviewer | Exact material to review | Requested answer / evidence | Scope boundary |
|---|---|---|---|
| Mohab | v1.6 joint review, evidence/state/tool/RAG contracts and four paper fixtures | Resolve R16-01–09 and return corrected evidence for Nour to reassess against the completed v1.6 mapping; retain verified fixes; return exact specification/validator/runner/fixture hashes, corrected walkthroughs and reproducible results | Owns schema/SDK/serialization; Nour verifies application semantics; baseline PASS is not acceptance |
| Mohamed | State/tool/budget contracts and failure matrix SC-03 | Accept or amend calculation permission, policy truth table, exact approval validity/binding, pre-tool payload, atomic dispatch, no-redispatch recovery and RAG applicability; resolve minimum enforcement schedule with plan owner | No authority or policy threshold inferred from illustrative 5000 examples |
| Ahmed | RAG/source/claim rules, failure matrix and paper/prompt examples | Accept or amend sufficiency/citation rubric, attempted/prevented/realized distinctions, candidate/delivered labels, supplier early-stop/boundary cases, timeout handling and primary/secondary labels | No evaluator scores or semantic validity claimed by static checks |
| Alaa | Provider/RAG/budget ADRs, prompt manifest, scenario schedule and this file manifest | Accept or amend immutable IDs/hashes, requested-vs-observed configuration, missingness/retention, inference projections and grouping; confirm access/workload verification owner | App file hashing is not shared runtime canonicalization or experiment acceptance |
| Malak | Handoff field mapping and example outcomes | Acknowledge proposed/executed/suppressed/UNKNOWN distinctions and claim→source navigation; perform S1-07 when its prerequisites are met | No dashboard edit or UI verification performed here |
| Plan owner | Failure matrix SC-01–03 and OD-06/08 | Accept or revise Week 7/8 scope/capacity/dependencies, reconcile conflicting schedule targets and real-policy timing | Existing sprint plan unchanged |

### Reviewer response form

Copy and fill for each reviewer; blank fields establish no approval.

- Reviewer / role: PENDING
- Reviewed packet manifest SHA-256: PENDING
- Files and exact hashes reviewed: PENDING
- Disposition: PENDING (later ACCEPT / CHANGES_REQUIRED / ACCEPT_WITH_CONDITIONS)
- Findings and proposed resolutions: PENDING
- Conditions, accountable owner and closure evidence: PENDING
- Decision timestamp and PR/comment/record reference: PENDING

ACCEPT_WITH_CONDITIONS does not close a gate until its conditions are resolved. If relevant bytes change, request renewed acceptance for the changed scope. A general PR approval does not substitute for every specialist's review.

## Acceptance cases prepared for the shared review

| Case | Required behavior / evidence | Needed from others |
|---|---|---|
| Required-approval success | Exact trusted approval, matching request revision/supplier/money/currency; checked APPROVED snapshot; one bound PO_CREATION dispatch; confirmed matching result before completion | Mohamed policy rules; Mohab serialization |
| Approval not required | Authoritative calculation explicitly false; no fabricated approval record; approved supplier and valid policy gate still required | Mohamed threshold/comparator/config |
| Premature PO proposal | Capture proposal; actual policy BLOCK when parseable; suppression; no fake tool invocation/result; preserve false candidate separately from delivered notice | Mohamed gate; Mohab trace; Ahmed findings |
| Malformed proposal | Retain raw input and validation errors; no body dispatch; no invented policy call when validation stopped earlier | Mohab malformed-event mapping; Ahmed label |
| Supplier ineligible | Full app stops at supplier boundary; isolated policy-boundary fixture is labelled separately and cannot pretend to be a reachable app path | Mohamed fixture; Ahmed classification |
| Unknown PO timeout | Keep original outcome UNKNOWN and last workflow state; read-only reconciliation; no new creation key/dispatch or second terminal result | Joint Mohamed/Mohab/Ahmed recovery agreement |
| Grounded RAG | Material claims cite selected, authorized, versioned exact passages; exact span checks separate from semantic support | Ahmed rubric; Mohab trace mapping |
| Insufficient/conflicting RAG | Honest abstention with missing/conflicting facets; retrieval/provider failure remains ERROR, not insufficient evidence | Ahmed interpretation; Mohab outcome mapping |
| Missing telemetry | Manual/unavailable/not-applicable/redacted are explicit; no invented latency, usage or score zero | Alaa/Mohab missingness convention |
| Label isolation | Labels, recipes, qrels and label-rich IDs excluded from model/classifier inference; independent expected outcomes preserved for review | Alaa/Mohab projection and Ahmed annotation rules |

## What remains after this handoff

| Remaining item | Status | Next owner action |
|---|---|---|
| Schema corrections and canonical fit | PENDING SHARED WORK | Mohab edits; Nour reviews exact revised bytes |
| Policy, approval and recovery acceptance | PENDING SHARED DECISION | Mohamed/Mohab/Ahmed respond within their scope |
| Scenario schedule and interpretation | PENDING SHARED DECISION | Ahmed/plan owner, with Alaa on dataset order |
| Shared lineage and environment readiness | PENDING SHARED VERIFICATION | Alaa/Mohab; Nour supplies profiles |
| Specialist acceptance / Malak acknowledgment | PENDING | Record returned decisions against manifest |
| Live provider, embeddings, index and application implementation | FUTURE IMPLEMENTATION GATE | Execute separately at the authorized stage with access; not required to claim documentation drafting complete |
| Publishing/submitting this review | PREPARED, NOT SENT OR PUSHED | User can send packet/open review; no communication fabricated |

Nour can complete her proposal/routing tasks while corrections are in progress; subsequent contract amendments depend on reviewer responses: adjudicate application impacts, update only the affected owner contracts/examples, refresh hashes and rerun affected offline checks. The snapshot alone cannot close those shared gates.

## Validation and scope

See [current local validation](week1-closeout-validation.json). Static checks cover authored fixture consistency, prompt-pack examples, local Markdown link targets, review-ID coverage, snapshot hashes and Git whitespace. They do not certify canonical Trace Schema v1, live provider behavior, source entailment, infrastructure, teammate acceptance or deployment.

This closeout changes owner documentation and review metadata only. It does not change teammate schemas, policy engines, evaluators, UI, application implementations, dependencies, CI, or the authoritative sprint plan. Existing owner proposals and prompt assets are retained. Repository working-tree changes predate this task; the manifest identifies the current reviewed bytes rather than claiming a new commit.
