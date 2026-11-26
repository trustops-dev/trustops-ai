# OD-04 — Nour's application-side approval-validity response, draft 0.1

**Prepared 2026-11-06 — AMEND overall; application-side response prepared, not sent or jointly accepted.** This records the proposed response Nour can give to Mohamed's GD-04 in governance draft 0.4, reviewed alongside Mohab's supplied schema v1.6 and the maintained application contracts. ACCEPT below is scoped to the proposed application design; it is not a fabricated personal signature, specialist sign-off, live approval or closure of OD-04. Mohamed and Mohab must return exact-revision dispositions before integration. No runtime behavior changes in this documentation update.

**Historical draft:** the later [application response 0.2](../od04-v0.2.md) records Mohamed's scoped V01–V08 reply, terminal DENIED/CANCELLED, source record-sequence ordering and approval/supplier version currentness at the dispatch claim. Statements in this 0.1 draft that OD-03 values are unaccepted or that Mohamed's response has not arrived describe its 2026-11-06 preparation state; they do not override the later scoped review records.

## Proposed response to GD-04

| Clause | Nour's draft disposition | Application-side position / required amendment |
|---|---|---|
| V01 — Explicit no time expiry | ACCEPT, subject to V02–V08 | No arbitrary TTL is added for the synthetic MVP. The accepted policy configuration must explicitly declare no time expiry. Missing validity configuration is unresolved, never an implicit forever-valid grant. Age alone does not invalidate a current, correctly bound approval under that explicit rule. |
| V02 — Current authoritative evidence and exact binding | ACCEPT, with clarification | Resolve the existing approval request through the trusted approval boundary. Require its current authoritative APPROVED record, approval/request identities, current immutable request revision, supplier, exact amount/currency, required level, actor authority, policy/calculation references and decision provenance. An approval cap, role string, stale cache, model text or ID alone does not prove validity. |
| V03 — Revised request | ACCEPT | Any changed amount, currency, supplier, item/quantity or new request revision invalidates the prior calculation/approval/ALLOW for that revision, including a revision with the same total. Start the new revision at REQUEST_CAPTURED, retaining original events and business-root identity. A revision never clears an existing PO claim, unknown outcome or spent budget. |
| V04 — Denial, cancellation and revocation | AMEND | Propose DENIED/CANCELLED as terminal for that existing approval-request lifecycle in the MVP: no automatic reopening or superseding grant from a later callback. Revocation is a new authoritative CANCELLED record linked to the prior grant, as GD-04 proposes, not a new application state or REVOKED enum. A cancelled business request cannot be revived by a late approval. Mohamed must confirm terminality and how conflicting source records are resolved. |
| V05 — Late decisions and causal order | AMEND | Approval must precede the exact PO proposal being checked. An approval arriving after an earlier blocked proposal can support only a new proposal after a trusted, valid continuation; it cannot repair the old proposal/ALLOW. Approval after dispatch cannot retroactively authorize that dispatch. Future-dated, conflicting or unorderable evidence cannot establish validity; wall-clock coincidence alone is insufficient. |
| V06 — Revocation/check/dispatch race | AMEND | Revalidate current authority at the serialized authorization/claim/dispatch boundary. If approval, request, supplier or policy changes after ALLOW but before the initial dispatch claim takes effect, suppress the stale dispatch. Mohamed and Mohab must agree a version/order binding and atomicity/fencing mechanism. Until that mechanism is defined and tested, a snapshot or fresh read alone is not proof that the race is solved. |
| V07 — Trusted continuation | ACCEPT, with prerequisites | Resume only the same active request revision through an authorized runtime continuation, with stable root/approval-request IDs, original submission/key binding, linked evidence, current source checks and retained budgets/claims. Preserve confirmed OBSERVE_APPROVAL semantics: observation cannot submit, update, approve or replace a request. A user/model assertion, callback payload or trace ID alone cannot resume execution. |
| V08 — Effects already dispatched | ACCEPT, with explicit boundary | Revocation after dispatch does not undo an order, prove no effect or rewrite the historical authorization. Preserve the original invocation/outcome and append later observations. UNKNOWN stays PO_CREATION/RECOVERY_PENDING until trusted read-only reconciliation. Existing COMPLETION is not retroactively rewritten by later revocation. No cancellation/refund/replay capability is introduced. |

The current rule requires approval before the proposal event. The proposal here preserves that rule and clarifies which proposal is eligible after a pending interaction. Approval decisions remain governance-owned, never model-written. This response does not select a TTL, grant a purchasing role to dashboard/RBAC roles, resolve OD-03 numerical values, close OD-02 calculation permission, or implement OD-12 claims/replay/budgets.

## Validity and continuation checkpoints

1. **Observe:** use trusted read-only observation of the existing approval_request_id, unchanged request revision and original binding. Preserve response provenance and its actual status. No missing record or failed observation falls back to initial submission.
2. **Validate:** require an explicit accepted validity rule, a current authoritative record, exact binding, authorized synthetic approver evidence, a current policy/calculation and supplier eligibility. No-expiry removes only a time-age test; it removes none of these conditions. A currentness mechanism/record version must be mapped by Mohamed/Mohab; it is not a new model-visible argument.
3. **Continue:** verify the business request is active and the continuation is trusted. Preserve the root, parent/continuation linkage, original approval identity/key, spent/reserved budgets and existing PO claim/outcome. Unknown prior effects and lost state prevent a fresh creation path. Do not promise restart durability for an in-memory ledger.
4. **Propose:** after APPROVAL_PENDING -> APPROVED, produce a new PO proposal when appropriate. Do not replay the previous blocked proposal or overwrite its result. Obtain a fresh policy check bound to this exact proposal, arguments, state revision and evidence.
5. **Dispatch once:** only an accepted bound ALLOW and the agreed atomic claim/transition permit APPROVED -> PO_CREATION. Recheck authority ordering at this boundary. A competing continuation cannot obtain another write allowance. Implementation and concurrency proof are later gates, not results of these paper cases.
6. **Handle late facts:** retain original evidence and classify whether the fact preceded or followed the authoritative dispatch boundary. If ordering cannot be established, withhold certification of authorization and preserve known effect evidence; do not infer NONE, success or an automatic compensation path.

## Affected state transitions

These rows reference existing application states. HALT, WAIT and invalidation are descriptive control actions, not new canonical state/run-status enums. On a halt retain the last confirmed fine state and append the stop reason; the existing APPROVED label does not keep an invalid grant usable.

| Starting state / condition | Proposed application behavior | Prohibited behavior |
|---|---|---|
| APPROVAL_PENDING; source still PENDING | Remain APPROVAL_PENDING; finish the interaction as waiting | Poll indefinitely, resubmit the original request or claim approval |
| APPROVAL_PENDING; unchanged request and current valid APPROVED evidence | Transition to APPROVED after validation; later new PO proposal + fresh check | Jump straight to PO_CREATION/COMPLETION or treat observation as ALLOW |
| APPROVAL_PENDING; DENIED/CANCELLED, missing/conflicting evidence or cancelled business request | Halt progression; retain pending state as the last confirmed fine state | Fake an APPROVED transition, reopen automatically or create a replacement identity |
| APPROVED; invalidated approval/supplier/policy before dispatch | Suppress dispatch and halt; keep invalidation visible | Execute using old ALLOW or invent an unlisted backward transition |
| Existing revision replaced, before a new creation can be considered | New revision begins at REQUEST_CAPTURED with explicit linkage and full required evidence reacquisition | Reuse old approval/ALLOW; reset root budgets or prior dispatch guards |
| APPROVED; all conditions hold at the agreed atomic boundary | APPROVED -> PO_CREATION with exactly one original dispatch claim | Duplicate creation from a second callback, check, trace or continuation |
| PO_CREATION; effect UNKNOWN, with any later approval/revocation | Retain PO_CREATION/RECOVERY_PENDING and use authorized read-only reconciliation only | Redispatch, turn uncertainty into failure/no effect, or manufacture success |
| PO_CREATION; later facts establish the original effect | Apply the existing outcome/reconciliation contract; preserve original observations | Treat a recovered original PO as a new execution or authorization |
| COMPLETION; revocation arrives later | Preserve completion/effect history and append the later approval record | Rewrite history, automatically cancel/refund or issue another PO |
| APPROVAL_CALCULATED; trusted calculation says approval not required | Existing path to APPROVED with NOT_REQUIRED; no approval record manufactured | Treat lack of a grant as evidence that approval is unnecessary when calculation is unresolved |

Policy/calculation changes require reestablishing evidence through a permitted application path. This response does not invent APPROVED -> APPROVAL_CALCULATED or another shortcut. If the same revision cannot legally re-enter that path, halt and obtain a jointly agreed continuation/revision disposition.

## Representative sequences

All identifiers below are illustrative review values, not actual approval records or canonical traces. Amounts remain symbolic A/T/C; OD-03 candidate 0.1 is still unaccepted.

**Unchanged request:** req-od04-01 / rev-1 remains active. The authoritative record for approval-request-01 becomes APPROVED and exactly matches the request. Trusted observation and validation permit APPROVAL_PENDING -> APPROVED. A newly created proposal po-proposal-02 then receives a fresh bound check. Only the later atomic single-dispatch boundary can permit the PO tool body.

**Changed request:** the same business root moves from rev-1 to rev-2, even if its total is unchanged. approval-request-01 bound to rev-1 cannot authorize rev-2. Retain the old history and restart the new revision at REQUEST_CAPTURED. If rev-1 already has an unresolved PO dispatch, preserve that guard; rev-2 is not a workaround for creating another PO.

**Late approval after BLOCK:** po-proposal-01 was blocked while approval was pending. An authentic approval decision arrives later. Keep po-proposal-01 and its BLOCK immutable. Subject to trusted continuation, current validity, remaining budgets and no existing creation claim, the app may prepare po-proposal-02 after the approval and obtain a fresh check. It may not replay proposal-01.

**Revocation race:** a bound ALLOW references authoritative approval record version v1. Before the dispatch boundary, the approval authority records a linked CANCELLED version v2. The stale v1 dispatch is suppressed under the proposed ordering rule. If reliable ordering or atomic exclusion is unavailable, the app cannot certify a dispatch as authorized. If the write was already dispatched, retain its actual/unknown outcome and route the inconsistency through the existing recovery/evaluation contracts; cancellation of the approval is not cancellation of the PO.

## Evidence and implementation ownership

| Evidence / decision | Owner and required response |
|---|---|
| Validity rule, explicit no-expiry setting, authoritative current status and approver eligibility | Mohamed: accept/amend V01/V02; specify actual configuration and source-resolution contract |
| Denial/cancellation terminality and revocation version/order | Mohamed: accept/amend V04/V06; define valid transitions and handling of conflicting records |
| Approval precedes proposal and trusted event/time semantics | Mohamed + Mohab: accept/amend V05; define ordering across traces/continuations and malformed/future timestamp handling |
| Existing record identity, source version, event references, exact request/calculation/policy binding | Mohab: map the required evidence into the corrected schema; no implicit agreement with defective v1.6 paths |
| Root/continuation/claim identity, currentness check, concurrency and dispatch boundary | Mohab + Mohamed with Nour: agree V06/V07 and OD-12 mapping; do not resolve claim timing by mutating an earlier immutable check |
| Application state and emitted evidence | Nour: implement only the accepted transitions later; retain candidate/observed/trusted values separately |
| Post-dispatch uncertainty and downstream interpretation | Ahmed/Mohamed/Mohab: retain their OD-12-OUTCOME scopes; this response does not assign final labels, scores or PASS/REVIEW/BLOCK |

## Exact response requested

Mohamed: return ACCEPT/AMEND for V01–V08, especially explicit no expiry, authoritative status resolution, terminal denial/cancellation, late-decision ordering and revocation effective order. Supply replacement wording where needed, configuration/version references and the accepted synthetic authority mechanism. Existing governance-local DECIDED status does not substitute for the cross-team response.

Mohab: return the field/event mapping for each clause and the reviewed continuation/claim/currentness design. Identify which fields or transitions remain unresolved and provide paired valid/invalid fixtures. Specify whether continuation shares one trace or uses linked traces; no trace topology is assumed here.

Each reply must name reviewer, date, clause IDs, exact reviewed files/hashes, ACCEPT/AMEND, evidence and remaining conditions. The overall response remains AMEND and OD-04 remains OPEN until the required joint dispositions are recorded. No response is sent by this edit. Full OD-14 sign-off and runtime adapter/concurrency proof remain separate gates. Do not reopen the confirmed read-only observation distinction under OD-APP-OBS-01.

## Review artifacts and verification limit

response.json records clause dispositions and ownership. cases.json provides paper-review expectations for unchanged/revised requests, denial/cancellation, revocation timing, late decisions, trusted continuation and already-dispatched effects. Their review-only field names are not proposed tool arguments, endpoints, canonical trace fields or new runtime enum values.

Validation checks file/ID consistency, permitted state names, clause coverage, required negative cases and preservation of the OD-03 candidate/confirmed semantics. It does not execute an approval service, runtime state machine, atomic dispatch, schema validator or governance engine, and does not prove approval validity or race safety.

Reproduce the structural review from the repository root (Python 3.12, standard library only):

```bash
review_reports=$(mktemp -d)
python -S docs/architecture/reference-applications/approval-validity/od04-v0.1/verify_review.py --output "$review_reports/od04.json"
```

The helper exits nonzero on structural disagreement. It is not a simulated approval authority and must not be imported into application execution.
