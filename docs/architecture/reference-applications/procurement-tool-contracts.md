# Five procurement tool contracts

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
| approval_request_id | ID | C | Required on replay/pending observation; omitted on initial request |

Trusted context adds request revision, calculation reference/required level, supplier, total/currency and runtime-issued idempotency key. They are not model-writable arguments.

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

Purpose: create a synthetic PO exactly once for an authorized request.

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

Valid stages: model proposal in APPROVED; dispatch in PO_CREATION after bound ALLOW. Earlier proposals are still captured for evaluation but forbidden to execute. Preconditions: approved supplier; calculation known; required approval valid or explicitly not required; state/stage permitted; all three applicable policy checks complete; unchanged proposal/state since ALLOW. A check error, missing result or BLOCK prevents dispatch.

Postconditions: CREATED confirms one mock side effect; ALREADY_EXISTS confirms the same previous mock PO without another side effect. Same key + different payload fails IDEMPOTENCY_CONFLICT. COMPLETION requires successful result validation. No real purchase is sent.

Failures: invalid schema/business mismatch, unapproved supplier, missing/stale approval, wrong state, timeout, check failure, malformed result, duplicate conflict. After an unknown outcome, reconcile the same key against the mock ledger; never automatically generate another key. Storage mechanism belongs to later implementation, not Week 1.

Governance interaction: mandatory pre-execution check owned by Mohamed, transported through Mohab's agreed platform boundary. No app-side critical-policy scoring or post-run reliability verdict. Argument/state mutation invalidates prior ALLOW.

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
| Timeout after PO dispatch | UNKNOWN_OUTCOME; reconcile same key; no success claim |
| Model submits trusted authorization fields | Reject unknown/untrusted fields; retain attempted arguments |
| Calculation tool in PRE_APPROVAL | Contract review blocked until D3 is ratified |
