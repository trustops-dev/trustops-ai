# Five procurement tool contracts

**OD-04 draft response — 2026-11-06:** [Nour application-side position 0.1](approval-validity/od04-v0.1/README.md) proposes scoped ACCEPT/AMEND dispositions, affected transitions and paper examples. Approval validity remains OPEN pending Mohamed/Mohab agreement; this pointer does not ratify the proposed amendments or change the behavior contract below.

**2026-11-02 review supplement:** [Consolidated manual boundary cases](manual-boundary-cases.md) add the denied-approval walkthrough and symbolic below/equal/above T review cases. Existing contract semantics and pending approvals remain unchanged.

**Sprint 1 Contract Baseline / Freeze Candidate — tool-contract revision 0.8, 2026-11-02. NOT FROZEN.** Approval-observation semantics are confirmed by Mohamed and Mohab as reported by the user on 2026-11-02; see [OD-APP-OBS-01](open-decisions.md#approval-observation-confirmation). Other specialist approvals remain PENDING. Week 2 findings below supersede conflicting Week 1 review-status statements, not the preserved behavior contracts.

## Week 2 five-tool review

The detailed records below were reviewed for purpose, required/optional input fields and types, output fields/statuses, validation, pre/postconditions, stages, deterministic fixture behavior, errors, trace evidence and governance interaction. All five have complete **application-level** coverage and remain provider-neutral. Owner-dependent policy/serialization choices prevent claiming cross-module implementation readiness.

| Tool | Existing contract verified | Actual draft/example mismatch / closure |
|---|---|---|
| search_policy | Nonblank query, matching request_id, positive integer top_k, optional policy_ids; MATCHED/NO_MATCH/AMBIGUOUS/ERROR; full ranked evidence | `retrieval` can hold query/docs/ranks but not full versions/hash/selection; original success example omits proposal/check/call linkage for this tool |
| get_supplier | Exact supplier/request IDs; FOUND/NOT_FOUND/ERROR; raw status retained and APPROVED/NOT_APPROVED/UNKNOWN normalization | Draft UNAPPROVED/SUSPENDED require lossless raw→normalized mapping; original examples lack directory/record provenance |
| calculate_approval_level | Exact decimal total/currency/revision; CALCULATED/UNRESOLVED/ERROR; governance-owned rule and comparator | Original success omits tool/calculation; PRE_APPROVAL permission unsigned; numeric schema amount conflicts with exact decimal-string requirement |
| request_approval | Initial-submission/read-only-observation requiredness, trusted calculation/revision/key; PENDING/APPROVED/DENIED/CANCELLED/ERROR; separate observation | Draft REJECTED/BYPASSED cannot silently replace DENIED/CANCELLED; approval cap/role does not prove request binding or authority |
| create_purchase_order | Six model-visible arguments; trusted binding/key separate; CREATED/ALREADY_EXISTS/UNKNOWN_OUTCOME/ERROR; single confirmed mock effect | Draft example `item`/`estimated_cost` differ from `item_description`/`total_amount`; missing request_id/currency and wrong amount representation; timeout boolean loses uncertainty |

The manual fixtures use the actual application argument names and decimal strings. They do not backfill or edit Mohab's original examples. Non-PO tools also record the proposed pre-tool check boundary and per-policy applicability for review; these are authored expected observations, not implemented governance.

**Clarification for all tools:** unknown/malformed raw JSON must survive capture even when it cannot fit the draft `proposed_arguments:object`. Parsed values and field errors must be separate from raw bytes/text. Invalid arguments never dispatch. A blocked envelope event, if Mohab elects to retain one, is runtime-produced suppression evidence with `call_id=null`, no tool-body payload and explicit `execution_started=false`; it is not an invocation outcome.

`CALCULATED` boolean is mandatory only after successful calculation; prior states and UNRESOLVED carry unknown applicability rather than false. Proposed execution/retry/time limits are now specified in the linked execution-budget ADR and the section below. They remain subject to review; business thresholds, approval validity and currency tables are not inferred from those technical limits. Numerical examples in manual fixtures are explicitly inherited proposal examples, not production defaults.

DECISION — proposed application-side types for later Pydantic implementation. Not executable schemas, canonical trace objects, governance APIs or existing repository interfaces. Basis: Proposal N/R; see [state contract](procurement-state-contract.md) for dispatch states and [evidence contract](trace-evidence-contract.md) for event requirements.

Provider boundary: these business contracts remain provider-neutral. The planned Gemini application adapter translates provider-specific payloads into generic `tool_call`, `tool_name`, `tool_arguments`, `tool_result` and `model_response` concepts; these names are descriptive, not Mohab's canonical schema. No provider-specific response object or ID is required here. Tool semantics, stages, validation and approval-bypass enforcement are unchanged; Mohamed's policy layer remains the authorization authority.

## Common conventions

R = required; O = optional; C = conditionally required. ID means nonempty opaque string; Version means immutable ID/content reference; Money means positive finite decimal encoded as a string, never binary floating point. `currency` is a supported three-letter currency code from the versioned synthetic policy configuration; no currency conversion is assumed. Positive integer fields reject booleans and strings. Unknown fields are rejected; no silent coercion of malformed amounts or missing approval flags.

Business scope is one item type and one supplier per request for the MVP (DECISION, not an approved business policy). `PurchaseRequest` fields: `request_id:ID` R, `request_revision:ID` R, `item_description:string` R nonblank, `quantity:integer` R >0, `total_amount:Money` R, `currency:string` R, `supplier_id:ID` R, `requester_ref:ID` R, `purpose:string` O. Amount is the synthetic requested total; unit prices, tax and freight are not inferred. Changes create a new revision. Multi-line allocation and tax accounting are outside this contract.

Tool-visible arguments below exclude authorization context. The application supplies a **trusted context** separately: request snapshot/revision, active state/stage, tool catalog version, policy set version, fixture/directory versions, trace/proposal/invocation linkage, approval references and check outcome where required. The model cannot supply or override trusted context. IDs the model supplies are resolved and checked against it.

Every invocation outcome has `status` (tool-specific enum), `data` (success payload or null), `error` (null or `code:string`, `message:string`, `retryable:boolean`, `details:object`), and runtime-owned evidence/version references. For ERROR, data is null and error is required. For success/domain-negative outcomes, error is null and data contains the applicable fields below. Common proposed error codes: INVALID_ARGUMENTS, WRONG_STATE, CONTEXT_MISMATCH, TIMEOUT, UNAVAILABLE, MALFORMED_RESULT, VERSION_CONFLICT. They describe technical handling, not primary failure labels.

Record raw proposed arguments, parsed/validated arguments, field-level validation failures, expected tool schema version, invocation identity, result/error and start/end/NOT_EXECUTED evidence. Rejected arguments never execute. No mock determinism is claimed for live LLM output: only fixed tool inputs plus fixed fixture versions yield deterministic mock behavior.

## 1. search_policy()

Purpose: retrieve applicable synthetic purchasing policy evidence, without granting authorization.

| Input | Type | Required | Validation/source |
|---|---|---|---|
| query | string | R | Nonblank, derived from request; preserved verbatim |
| request_id | ID | R | Must match active request |
| top_k | integer | R | >0; runtime-configured limit; no default numeric k prescribed |
| policy_ids | list[ID] | O | Optional filter; IDs must exist in the selected policy set |

| Output data | Type / condition |
|---|---|
| query, requested_top_k, returned_count | string, integer, integer; always |
| matches | list[PolicyEvidence]; empty only for NO_MATCH |
| policy_set_version, retriever_version | Version; always |
| applicability | APPLICABLE / MISSING / CONFLICTING |

`PolicyEvidence`: `policy_id:ID`, `document_id:ID`, `source_id:ID`, `source_version:Version`, `chunk_id:ID`, `text:string`, `content_hash:string`, `locator:string`, `rank:integer` starting at 1, `score:number` finite, `score_kind:string`, `higher_is_better:boolean`, `metadata:object` containing title and applicable domain. No score is a probability unless the retriever explicitly defines it so. All fields required; policy_id may match a rule while document_id identifies its textual evidence.

Statuses: MATCHED, NO_MATCH, AMBIGUOUS, ERROR. MATCHED requires nonempty usable applicable evidence; conflicting applicable rules → AMBIGUOUS, never an arbitrary selection. Fewer than k results is allowed; do not pad.

Preconditions: REQUEST_CAPTURED/PRE_APPROVAL; complete normalized request; pinned synthetic policy set. Postconditions: returns evidence, does not change approvals/suppliers or create PO. POLICY_CHECKED only on MATCHED with applicability APPLICABLE.

Failure conditions: empty query, invalid k/filter, absent relevant policy, conflicting versions/rules, unavailable corpus, malformed result. Missing retrieval evidence stops progression even if the model remembers a threshold.

Governance interaction: retrieved prose supports provenance; Mohamed's versioned executable policy configuration remains the authorization authority. Text/config disagreement is reported and halts; it is not silently reconciled by the model.

Mock behavior, PLANNED Sprint 2: fixture lookup keyed by normalized query/domain with stable ordering and fixture-defined score semantics. No embeddings needed for the procurement mock. Record lookup configuration, evidence content and versions. Full RAG retrieval is a separate application concern.

Required extra trace evidence: original and effective query, filters/k, full ranked returned evidence, applicability, selected policy references, mismatch reason.

## 2. get_supplier()

Purpose: resolve the exact supplier in the synthetic directory.

| Input | Type | Required | Validation |
|---|---|---|---|
| supplier_id | ID | R | Exact request supplier; no fuzzy substitution |
| request_id | ID | R | Active request identity |

| Output data | Type / condition |
|---|---|
| requested_supplier_id | ID; always |
| supplier | Supplier or null; required field, null only for NOT_FOUND |
| directory_version | Version; always |

`Supplier`: `supplier_id:ID`, `display_name:string`, `status:APPROVED/NOT_APPROVED/UNKNOWN`, `record_version:Version`, `source_ref:ID`, `observed_at:timestamp`. Required fields. These are proposed normalized statuses; original fixture status is also preserved when mapped.

Statuses: FOUND, NOT_FOUND, ERROR. FOUND does not imply APPROVED. Preconditions: POLICY_CHECKED/PRE_APPROVAL with accepted policy evidence. Postconditions: read-only supplier snapshot; proceed to SUPPLIER_CHECKED only for APPROVED. NOT_APPROVED/UNKNOWN/NOT_FOUND halts the workflow with no PO.

Failure conditions: supplier mismatch, absent ID, unknown status, timeout, malformed directory output or version mismatch. No invented supplier is returned.

Governance interaction: supplies authoritative synthetic status/version for PROC-SUPPLIER-01; the app's early stop does not replace Mohamed's mandatory check before PO dispatch.

Mock behavior, PLANNED Sprint 2: exact-ID lookup in an immutable directory fixture. Unknown ID → NOT_FOUND. Fixed fixture/ID yields the same business result; observation time can differ and is not the deterministic business payload.

Required extra trace evidence: requested and returned IDs, raw and normalized status, directory/record versions, source, read outcome and eligibility branch.

## 3. calculate_approval_level()

Purpose: obtain a deterministic approval requirement from Mohamed's versioned policy definition; no independent second policy engine in the app.

| Input | Type | Required | Validation |
|---|---|---|---|
| request_id | ID | R | Active identity |
| total_amount | Money | R | Exactly equals trusted request total |
| currency | string | R | Equals request and supported policy currency |

| Output data | Type | Condition |
|---|---|---|
| calculation_ref | ID | Always for CALCULATED |
| request_revision | ID | Always; runtime-bound |
| approval_required | boolean | Always for CALCULATED; missing/unknown is error |
| approval_level | string or null | Required field; null iff not required; otherwise configured level (manager per baseline rule) |
| policy_id, policy_version | ID, Version | Always |
| basis | object | Required: amount/currency, configured threshold/currency, comparator, rule reference |

Statuses: CALCULATED, UNRESOLVED, ERROR. UNRESOLVED returns explanation/rule references, with no approval_required value that could be mistaken for false. The structured payload must discriminate CALCULATED from UNRESOLVED explicitly in future schemas.

Preconditions: SUPPLIER_CHECKED/PRE_APPROVAL, approved supplier, configured rule. **Permission unresolved:** proposal R omits this tool from PRE_APPROVAL. D3 must be closed before any implementation dispatch. This document proposes the read-only permission; it does not grant it.

Postconditions: deterministic requirement evidence only; no approval is granted. Proposal R uses amount **exceeds** threshold, so equality does not trigger that amount condition; final configuration and currency precision require Mohamed's truth table. The proposal's example amount is not a default adopted here.

Failures: absent threshold/currency/rule, differing request total, invalid decimal, conflicting policy versions, unknown level, unavailable calculation boundary. UNRESOLVED prevents progression.

Governance interaction: app wrapper delegates to governance-owned policy calculation or uses a jointly reviewed fixed response fixture for early integration. No app-specific threshold logic that could disagree with PROC-APPROVAL-01. Canonical transport/function signature remains OPEN.

Mock behavior, PLANNED Sprint 2: deterministic fixture keyed by request revision + policy version, approved by Mohamed; boundary cases below/equal/above configured T planned symbolically, not populated with invented thresholds.

Required extra trace evidence: exact calculation basis, rule/version, output flags and whether fixture/delegated mode was used.

## 4. request_approval()

Purpose: create/observe a mock approval request through the governance-owned approval boundary, never self-authorize.

| Input | Type | Required | Validation |
|---|---|---|---|
| request_id | ID | R | Active request identity |
| justification | string | R | Nonblank; untrusted prose cannot change amount or level |
| approval_request_id | ID | C | Required for trusted read-only observation of the existing approval request; omitted on initial submission |

Trusted context adds request revision, calculation reference/required level, supplier, total/currency and runtime-issued idempotency key. They are not model-writable arguments.

**Confirmed interface semantics — OD-APP-OBS-01:** The trusted runtime distinguishes `CREATE_APPROVAL_REQUEST` (initial submission) from `OBSERVE_APPROVAL` (read-only observation). Observation uses the existing approval-request identity, unchanged request revision and original trusted binding; it cannot create, update, resubmit or approve a request, rotate its key, or fall back to submission when the record is absent or mismatched. The existing `request_approval` tool remains the application boundary; this clarification adds no model-visible mode argument or sixth tool. Submission and observation retain distinct operation/invocation evidence. Confirmation covers this semantic distinction; adapter read-only behavior, exact serialization, approval validity and budget values still require their separate verification/acceptance.

| Output data | Type | Condition |
|---|---|---|
| approval_request_id | ID | All non-error outcomes |
| request_revision, calculation_ref | ID | All non-error outcomes |
| decision_status | PENDING/APPROVED/DENIED/CANCELLED | Always; outside model control |
| approval_evidence | ApprovalEvidence or null | Required field; nonnull only for APPROVED |
| decision_ref, reason | ID or null, string or null | Decision details where available; pending may be null |

`ApprovalEvidence`: approval ID, approval-request ID, request revision, supplier ID, amount, currency, approval level, approving actor reference, decision timestamp, policy version, authoritative fixture/service source reference. All required. Expiry/revocation semantics are OPEN; absence of a configured validity policy is not proof that any historic approval is valid.

Statuses: PENDING, APPROVED, DENIED, CANCELLED, ERROR, matching decision_status when non-error. Preconditions: APPROVAL_CALCULATED or APPROVAL_PENDING/PRE_APPROVAL; requirement true; supplier approved. An initial pre-approved fixture result is still recorded through APPROVAL_PENDING followed by an observed approval transition, preserving chronology.

Postconditions: initial submission produces an approval request; no PO. Approved result sets approval_received only after binding validation. Denied/cancelled halts. Same key + same business request returns same approval-request identity; same key + changed payload → IDEMPOTENCY_CONFLICT error.

Failures: stale/mismatched approval, wrong level, wrong request revision, missing trusted evidence, user/model claiming approval, unavailable service, denied decision. Requested is not approved; sending a request is not a grant.

Governance interaction: approvals and policy truth remain Mohamed's ownership. App is a wrapper/consumer. No reviewer UI, notification transport, IAM or approval endpoint is implemented or invented here.

Mock behavior, PLANNED Sprint 2: immutable scenario fixtures determine pending/approved/denied observations; no email/Slack or purchasing-system integration. Runtime can accept a separately supplied synthetic approval decision; never derive it from the model saying yes.

Required extra trace evidence: submission vs observation, request/approval identities, idempotency identity, binding checks, actor/time/source, status and transition. Approval denied is a business outcome, not automatically one of the eight failures.

## 5. create_purchase_order()

Purpose: create one authorized synthetic PO under a single initial dispatch claim, with evidence-backed effect observation. No general external exactly-once guarantee is claimed.

| Input | Type | Required | Validation |
|---|---|---|---|
| request_id | ID | R | Active identity |
| supplier_id | ID | R | Same supplier as approved snapshot |
| item_description | string | R | Exact normalized description |
| quantity | integer | R | >0 and identical to request |
| total_amount | Money | R | Identical to calculated/approved amount |
| currency | string | R | Identical to request/calculation/approval |

Trusted context adds request revision, supplier/policy/approval evidence, proposal and pre-tool check references, argument digest, authorization basis and runtime idempotency key. An approval ID from model arguments is never an authorization token.

| Output data | Type | Condition |
|---|---|---|
| po_id | ID | CREATED or ALREADY_EXISTS only |
| request_revision, supplier_id | ID | All confirmed outcomes |
| quantity, total_amount, currency | integer, Money, string | Confirmed PO snapshot |
| mock | literal true | Always for created/existing PO |
| created_at, idempotency_key, result_ref | timestamp, ID, ID | Confirmed outcomes |
| original_result_ref | ID | Required for ALREADY_EXISTS |

Statuses: CREATED, ALREADY_EXISTS, UNKNOWN_OUTCOME, ERROR. UNKNOWN_OUTCOME carries request/proposal/idempotency linkage and explanation, but no asserted PO identity unless independently confirmed. Pre-tool BLOCK is **not** a tool-return status: the tool body was never called; the runtime emits NOT_EXECUTED separately.

Valid stages: model proposal in APPROVED; dispatch in PO_CREATION after bound ALLOW. Earlier proposals are still captured for evaluation but forbidden to execute. Preconditions: approved supplier; calculation known; required approval valid or explicitly not required; state/stage permitted; all three applicable policy checks complete; unchanged checked inputs, with only the runtime-owned APPROVED-to-PO_CREATION transition permitted under the [authorization binding rule](procurement-state-contract.md#authorization-binding-across-the-dispatch-transition). A check error, missing result or BLOCK prevents dispatch.

Postconditions: CREATED confirms one mock side effect; ALREADY_EXISTS confirms the same previous mock PO without another side effect. Same key + different payload fails IDEMPOTENCY_CONFLICT. COMPLETION requires successful result validation. No real purchase is sent.

Failures: invalid schema/business mismatch, unapproved supplier, missing/stale approval, wrong state, timeout, check failure, malformed result, duplicate conflict. After an unknown outcome, enter RECOVERY_PENDING and use only the trusted, read-only same-key ledger lookup defined in the [recovery contract](procurement-state-contract.md#unknown-po-outcome-and-recovery). Recovery never redispatches this tool, even if the ledger has no record; never generate a replacement key for an unresolved business request. Storage mechanism belongs to later implementation, not Week 1. An unavailable or lost ledger leaves the outcome unresolved; in-memory storage does not promise recovery across restarts.

Governance interaction: mandatory pre-execution check owned by Mohamed, transported through Mohab's agreed platform boundary. No app-side critical-policy scoring or post-run reliability verdict. Any mutation of the checked arguments, request, evidence or policy inputs, and any state transition other than the bound APPROVED-to-PO_CREATION transition, invalidates prior ALLOW before dispatch. That authorized transition and the initial dispatch claim must be atomic; the check cannot authorize another dispatch. Recovery records an observation of the original effect and does not reuse ALLOW as execution permission.

Mock behavior, PLANNED Sprint 2: controlled in-memory or fixture-backed ledger with deterministic identity from fixture/request/key; storage choice reviewed before implementation. Concurrent duplicate handling must be serialized/atomic in that ledger; no enterprise distributed transaction design.

Required extra trace evidence: proposal→check→dispatch→result linkage, immutable payload binding, actual execution start, observed outcome, mock marker, PO identity, duplicate status, and final claim's supporting result.

## Manual contract review cases (not executed tests)

| Case | Expected contract outcome |
|---|---|
| Valid request + approved supplier + valid required approval | PO proposal checked; ALLOW can dispatch; success can reach COMPLETION |
| Same request, required approval absent | BLOCK; no dispatch; no PO |
| Approval unnecessary under configured rule | NOT_REQUIRED basis; no invented approval_received or approval ID |
| Amount exactly configured T | Apply approved `>` rule at equality; no invented tolerance |
| Supplier NOT_APPROVED | Stop early; any forced PO proposal independently blocked |
| Same idempotency key/payload repeated | Same approval/PO identity; no duplicate effect |
| Same key/different payload | Error; no new effect |
| ALLOW followed only by the bound APPROVED-to-PO_CREATION transition | Initial dispatch may proceed once; trace links the checked and dispatch state revisions |
| Bound arguments/evidence change after ALLOW, or another transition occurs | Invalidate ALLOW; no dispatch until fresh validation and policy check |
| Duplicate use of the same authorization | No second dispatch; retain original claim/result references |
| Timeout after PO dispatch | UNKNOWN_OUTCOME; PO_CREATION with RECOVERY_PENDING; stop execution and retain the original key |
| Recovery finds the matching confirmed PO | Read-only observation; report existing result and reach COMPLETION; zero additional tool dispatches |
| Recovery proves final failure with no PO or in-flight operation | Halt as FAILED; zero additional tool dispatches |
| Recovery sees missing, pending, lost or conflicting ledger data | Remain RECOVERY_PENDING; bounded lookup stops without retrying creation or claiming non-execution |
| Request revision/new key proposed while prior effect is unresolved | Reject replacement dispatch for the same business request |
| Model submits trusted authorization fields | Reject unknown/untrusted fields; retain attempted arguments |
| Calculation tool in PRE_APPROVAL | Contract review blocked until D3 is ratified |


## Execution-budget and retry contract — revision 0.7

The [execution-budget ADR](../../adr/application-execution-budgets.md) is the authoritative proposed budget definition. All defaults below are **PROPOSED / NOT RATIFIED** under OD-12; no real tool, ledger or stakeholder acceptance is implied.

| Operation | Mode | Attempt timeout | Operation/stage deadline | Maximum attempts | Retry/replay rule |
|---|---|---|---|---|---|
| search_policy | READ_ONLY | 3 s | 6 s | 2 | Transient read failures only; same query/config; separate attempt identities |
| get_supplier | READ_ONLY | 2 s | 5 s | 2 | Transient read failures only; exact supplier and pinned directory rules |
| calculate_approval_level | READ_ONLY | 1 s | 1 s | 1 | No automatic retry; unresolved configuration is not transient |
| request_approval — initial submission | CREATE_APPROVAL_REQUEST | 5 s | 5 s | 1 | No automatic write retry; same-key replay requires accepted idempotency contract |
| request_approval — observation | OBSERVE_APPROVAL | 2 s | 5 s | 2 | Only if adapter proves read-only observation; PENDING is not a retryable failure |
| create_purchase_order | CREATE_PO | 5 s | 5 s | 1 | One initial creation claim; no automatic replay after any uncertain dispatch |
| pre-tool policy check | READ_ONLY | 2 s | 2 s | 1 | No automatic check retry; no verdict means no dispatch |
| internal original-PO ledger lookup | RECOVERY_LOOKUP | 2 s | 5 s | 2 | Trusted recovery session only; never invokes creating tool |


### Fields added outside model-visible arguments

| Contract field group | Required semantics |
|---|---|
| Root/segment/operation identity | Stable root business lifecycle, request revision, segment/parent scope, logical operation and distinct attempt/reservation IDs |
| Profile and counters | Immutable execution-budget-v1-proposed reference, authoritative snapshot/version, cumulative spent/reserved values and remaining limits |
| Deadline | Remaining duration and clamped effective timeout; raw process monotonic values do not travel across restart/hosts |
| Ownership | Current lease/fencing token; concurrent replays cannot each claim a dispatch |
| Operation mode | READ_ONLY, CREATE_APPROVAL_REQUEST, OBSERVE_APPROVAL, CREATE_PO or RECOVERY_LOOKUP; trusted runtime sets mode |
| Retry policy | Logical/attempt cap, retry class, classifier/backoff and actual wait; no independent hidden tool/SDK retry loop |
| Idempotency | Runtime-issued key and immutable normalized business-payload digest for approval/PO/recovery; volatile attempt/deadline fields excluded |
| Authorization | Exact check/state/request/argument/evidence binding for dispatch; key possession is not approval |
| Joint agreement | Accepted contract/profile reference and incident-specific recovery grant when required; no model-created permission |
| Outcome/effect | Business status separate from runtime suppression, actual execution start, effect certainty and later recovery observation |
| Error | Structured budget/error code, stage, last confirmed state, current-execution retryable=false, budget dimension and checkpoint reference |

The ADR includes JSON Schema and authored examples for trusted RuntimeBudgetContext and ExhaustionError. These schemas are review proposals, not canonical contracts. Mohab owns their shared placement/mapping. Existing six PO business arguments and the other four tools’ input signatures remain unchanged.

### Tool-specific enforceable changes

1. **search_policy:** 3 s attempt, 6 s operation, at most two transient read attempts; same request/query/config and full evidence capture. NO_MATCH/AMBIGUOUS are results, not retry triggers. There is no hidden embedding/model call in this mock tool.
2. **get_supplier:** 2 s attempt, 5 s operation, at most two transient read attempts. NOT_FOUND/NOT_APPROVED/UNKNOWN eligibility stops progression; do not retry in search of a favorable supplier result.
3. **calculate_approval_level:** one 1 s attempt. UNRESOLVED/missing threshold/currency/policy inconsistency is not a transient retry. The read-only calculation permission still needs Mohamed’s ratification.
4. **request_approval:** confirmed distinct trusted modes under OD-APP-OBS-01. Initial CREATE_APPROVAL_REQUEST has one proposed 5 s attempt and no automatic write replay. OBSERVE_APPROVAL uses the existing approval-request identity and unchanged trusted request/key binding; the approval decision may still be PENDING. The adapter must be verified read-only before the proposed two-attempt/5 s observation policy is enabled. An approval_request_id alone does not establish read-only behavior or approval. PENDING/DENIED/CANCELLED do not trigger retry; absent/mismatched records never trigger submission. Initial-submission replay safety, approval validity, broader trusted continuation and numeric budgets remain separate open decisions; model/user claims cannot grant approval.
5. **create_purchase_order:** one 5 s initial dispatch attempt/claim. Any ambiguous post-dispatch timeout, cancellation or lost response stops creation and retains the original key/digest. No automatic write replay and no replacement key under an unresolved business request. ALREADY_EXISTS describes a confirmed original effect; runtime read-only duplicate resolution must not fabricate a newly executed tool body or another committed PO.
6. **Pre-tool policy:** one 2 s attempt per check, at most 12 checks per root; every business-tool attempt, including a transient read retry, needs a fresh bound check under the original proposal/operation. A parseable stage-invalid proposal reaches the check for observable BLOCK, while malformed input/invalid runtime state may stop at the guard without a fabricated check. No verdict/error means suppression, not ALLOW or a fake substantive FAIL. There is no automatic retry of the check itself.
7. **Original-PO ledger lookup:** runtime-internal read-only operation, not a sixth model tool. Proposed recovery pool is 2 trusted sessions, 5 s each/10 s cumulative, two 2 s attempts each/four total. Missing/PENDING data never triggers an unbounded poll or creation replay. Contract/case authorization and original identity remain required.

### Exhaustion, cancellation and evidence

Reserve capacity before I/O through the root ledger. Count failed/timed-out/abandoned attempts, keep actual execution starts distinct, and never refill counters on a new trace, request revision or resume. Retry only the accepted safe class; business state wins over diagnostic retryable flags.

Before dispatch, budget exhaustion emits runtime suppression with no tool-body result. After a confirmed effect, preserve that effect even if later processing fails. After an uncertain PO dispatch, retain PO_CREATION/RECOVERY_PENDING and UNKNOWN; no success claim or inferred non-execution. Later lookup findings are append-only recovery observations, not a second contradictory terminal result for the original call.

Codes include BUDGET_LOGICAL_CALL_LIMIT, BUDGET_TOOL_ATTEMPT_LIMIT, BUDGET_POLICY_ATTEMPT_LIMIT, BUDGET_DEADLINE_EXCEEDED, BUDGET_SEGMENT_LIMIT, RETRY_LIMIT_EXCEEDED, RETRY_AFTER_EXCEEDS_BUDGET, BUDGET_STATE_UNAVAILABLE, STALE_EXECUTION_LEASE, IDEMPOTENCY_CONFLICT, JOINT_AGREEMENT_REQUIRED and RECOVERY_BUDGET_EXHAUSTED. The ADR lists remaining generation/embedding/depth codes and precise accounting. Shared names remain pending owner mapping.

At a durable checkpoint preserve root/profile/counters, current request/state, key/digest, authorization, original dispatch/outcome and recovery references. Lost state cannot become a fresh write allowance. Unresolved effect guards outlive ordinary trace TTL; expiry never authorizes replay.

### Purchasing agreement boundary

The ADR contains a separate purchasing-action matrix. Only synthetic approval/PO operations and their bounded original-effect observations belong to these five contracts. Real order submission/amendment, payment authorization, capture, refunds, cancellations/voids/reversals are **outside MVP and disabled**. Business process/integration owners are unassigned. Their replay or compensation requires new explicit joint business/engineering agreement; no tool or authorization is added by listing them.

### Acceptance criteria for implementation

- Race the final root slot: one winner, one denial, no duplicate I/O or negative counters.
- Inject retryable read/provider failures: one logical operation, separately charged attempts, one retry owner and parent-clamped timing.
- Resume/restart/revise the same request: no budget or idempotency reset; lost state blocks risky work.
- Exhaust before dispatch: no tool call/body result; exhaust after uncertain PO dispatch: no creation replay and no false failure/success claim.
- Observe matching/missing/conflicting original ledger outcomes: linked append-only evidence, bounded sessions, unchanged original terminal observation.
- Cancel a blocked worker: remote uncertainty remains explicit; late response cannot dispatch or overwrite the accepted outcome.
- Reuse a key with a changed business payload: conflict, no effect.
- Request payment/refund/cancellation: disabled or joint-agreement-required response; no financial tool is implemented.

These are acceptance requirements, not claimed runtime results. The authored offline review covers the specification’s arithmetic, example schemas and accounting cases only.
