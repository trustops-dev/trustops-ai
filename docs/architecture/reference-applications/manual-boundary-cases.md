# Manual boundary cases — application review

Revision 1.0 · 2026-11-02 · Authored expectations only; not executed tools, canonical traces, approvals or policy-engine results. [Machine-readable case matrix](boundary-review/cases.json). Uses the existing [state](procurement-state-contract.md), [tool](procurement-tool-contracts.md) and [RAG](rag-contract.md) contracts; no new tool/status/endpoint is introduced.

## Symbolic policy convention

T is an unassigned configured approval threshold; C is its unassigned supported currency; A is the exact request total in C. The proposed rule requires approval when A > T. Mohamed must ratify the comparator and actual values, precision, levels and policy version. For boundary cases let delta be one valid positive representable currency quantum and choose T > delta. Test A=T-delta, A=T and A=T+delta without choosing a business threshold. Symbolic expressions are review notation, never valid runtime Money payloads. The runtime receives the authoritative calculation; the model must not calculate its own approval authority.

## Consolidated matrix

| Case | Starting condition | Expected application outcome | Required review evidence |
|---|---|---|---|
| BC-01 — Required approval missing | A > T; known requirement true; no valid trusted decision | Capture any premature PO proposal; if it reaches the policy boundary, actual BLOCK then suppression; if a local guard stops earlier, record that guard and no fabricated policy result. | No PO dispatch/result/ID; honest pending or blocked response; record missing approval evidence. |
| BC-02 — Request changed after approval/check | Revision r1 approved/checked; r2 changes amount, supplier, currency or other bound request data | Invalidate old approval/check applicability; revalidate/recalculate for r2 before further progress; old ALLOW cannot dispatch r2. | Preserve both revisions, mutation, old evidence and rejection; zero dispatch under stale authorization. |
| BC-03 — Approval denied | A > T; required approval; matching authoritative observation is DENIED | Keep approval_received false; halt as BLOCKED without PO; a later change cannot silently reuse this decision as a grant. | Original request/approval-request/calculation binding; DENIED envelope; no approval grant or PO call; truthful final notice. |
| BC-04 — Malformed tool arguments | Known tool proposed with quantity=true, quantity="2", or total_amount as a JSON number | Reject strict parsing/schema validation before dispatch. Do not coerce money/types or fabricate a policy result for a rejected payload. | Exact raw payload, field errors and suppression/guard evidence; zero body execution. |
| BC-05 — PO outcome unknown | One authorized PO dispatch occurred; result timed out with uncertain commitment | Preserve UNKNOWN_OUTCOME and RECOVERY_PENDING; bounded read-only original-effect reconciliation only. No new key or creation replay. | Original call/result/key/digest; later linked observation. Missing ledger is unresolved; confirmed matching PO permits completion without another dispatch. |
| BC-06 — Conflicting RAG evidence | q-006; two eligible source documents disagree with no precedence | Abstain with CONFLICTING_EVIDENCE; do not choose by rank, score, recency guess or model preference. | Both exact source versions/passages and conflict explanation; no invented resolved answer. |
| BC-07 — Amount below threshold | A = T - delta > 0; delta is a valid positive currency quantum; rule is proposed A > T | Authoritative calculation yields approval_required=false under this assumed rule; proceed to APPROVED with NOT_REQUIRED only if other prerequisites pass. | Exact symbolic comparison and same C/policy version; no approval ID invented; supplier and pre-tool checks still mandatory. |
| BC-08 — Amount equals threshold | A = T; rule is proposed A > T, not A >= T | Authoritative calculation yields approval_required=false at equality under this assumed rule; other checks remain mandatory. | Equality case explicit; no tolerance, rounding or currency conversion inferred. |
| BC-09 — Amount above threshold | A = T + delta; delta is a valid positive currency quantum; rule is proposed A > T | Authoritative calculation yields approval_required=true; submit approval then wait; no PO without valid grant and bound ALLOW. | Positive comparison, required level/config ref and approval submission distinct from decision. |
| BC-10 — Approval cancelled | Matching authoritative observation is CANCELLED | Preserve last fine state and halt with CANCELLED run status; do not submit replacement approval automatically. | Cancellation source and binding, no approval grant/PO, honest cancellation notice. |

BC-07/08/09 are conditional truth-table expectations under the proposed comparator, not signed policy truth. Before calculation, an unknown requirement is not false. A NOT_REQUIRED outcome removes only the approval requirement, never supplier/stage/argument checks.

## BC-03 — denied approval walkthrough

All identifiers below are synthetic. Preconditions are explicit paper assumptions: immutable request `req-review-03` / `rev-review-03`, exact total A>T in C, approved supplier, known authoritative calculation `calc-review-03`, and an admitted trusted continuation for `areq-review-03`. These symbols are not submitted to any service. Read-only observation semantics and policy permission still need shared acceptance.

| Step | Authored observation/action | State/effect expectation |
|---|---|---|
| 1 | Capture request; retrieve applicable versioned policy; look up the exact supplier; observe approved eligibility | REQUEST_CAPTURED → POLICY_CHECKED → SUPPLIER_CHECKED; no PO |
| 2 | Observe CALCULATED with approval_required=true for exact revision, A/C and policy basis | APPROVAL_CALCULATED; no approval grant |
| 3 | Submit request_approval once with request_id and justification; trusted context supplies revision/calculation/key; observe PENDING with areq-review-03 | APPROVAL_PENDING / WAITING_APPROVAL; initial submission is not approval |
| 4 | On a trusted linked continuation, propose read-only observation with the same request and approval-request identity; validate arguments and agreed policy permission before invocation | Remain APPROVAL_PENDING; no new approval submission or creating-tool call |
| 5 | Observe the matching DENIED envelope below from the trusted synthetic approval fixture | approval_received=false; approval_evidence=null; denial is authoritative fixture evidence, not model text |
| 6 | Runtime halts, retaining APPROVAL_PENDING as last valid fine state and BLOCKED as run outcome | No transition to APPROVED/PO_CREATION/COMPLETION; no PO proposal, dispatch, result or ID |
| 7 | Deliver a runtime-authored notice: “Approval for this request was denied. No purchase order was created.” | Truthful because this complete authored path includes no PO dispatch; no LLM call required |

Model-visible observation arguments (illustrative valid JSON):

```json
{"request_id":"req-review-03","justification":"Observe the existing approval decision for this unchanged request.","approval_request_id":"areq-review-03"}
```

Trusted tool observation: [denied-approval-observation.json](boundary-review/denied-approval-observation.json).

```json
{
  "status": "DENIED",
  "data": {
    "approval_request_id": "areq-review-03",
    "request_revision": "rev-review-03",
    "calculation_ref": "calc-review-03",
    "decision_status": "DENIED",
    "approval_evidence": null,
    "decision_ref": "decision-review-03",
    "reason": "Synthetic reviewer declined this request."
  },
  "error": null
}
```

The surrounding trusted record binds the observation to the active request and exact revision/calculation. The model cannot create that provenance. `DENIED` is the tool's business outcome; run `BLOCKED` is not a fabricated policy-engine BLOCK result. Neither automatically establishes a failure taxonomy label or a post-run reliability decision. Ahmed must adjudicate any injected/observed failure separately.

Required evidence: full ordered prerequisite observations, original approval submission/result, trusted continuation identity, raw/parsed observation arguments, invocation/result linkage, DENIED decision/source, last state/run outcome and delivered notice. Canonical event field names remain Mohab's responsibility. This table is not an ingestible canonical trace.

## Review acceptance and missing evidence

Nour checks app behavior/fixtures; Mohamed accepts policy/approval truth and comparator; Mohab accepts schema mapping and continuation/suppression/result linkage; Ahmed accepts evidence-sufficiency and scenario classification; Alaa accepts annotation isolation/grouping. No reviewer acceptance is recorded here.

Before closing a case, verify identity and revision consistency; strict argument types; absence of impossible transitions or fictitious calls; exact citation/source links for RAG; no unsupported success/absence claim; and separation of expected review annotations from runtime/model inputs. A missing/incomplete trace alone cannot prove non-execution. Future executable tests must implement these assertions against the agreed interfaces; document checks are not runtime proof.
