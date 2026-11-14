# TrustOps UI: Verification Summary for the Nine Points

**Author:** Malak
**Date:** 2026-11-07
**Reviewed handoff commit:** 479cab0

## Result

All nine display distinctions requested in the handoff are implemented in the UI and work as intended. The type check is clean and all 137 tests pass (7 test files). The app was run in the browser and checked.

Verification was done on fixture data (13 traces). Not yet checked: live API data and mobile/tablet widths.

## Nine points

| # | Point | Result | Where in the UI |
|---|---|---|---|
| 1 | Proposed / authorized / invoked / suppressed | Met | Trace Detail, ActionLifecycle (four steps per action) |
| 2 | Known effect / no effect / UNKNOWN | Met | Trace Detail, SideEffectView (three states, no yes/no) |
| 3 | Newly created vs recovered | Met | SideEffectView ("newly created" vs "recovered" tags) |
| 4 | Approval pending / denied / cancelled / approved | Met | Trace Detail, ApprovalRecords (read from the approval record) |
| 5 | Workflow state vs policy vs execution vs PASS/REVIEW/BLOCK | Met | Trace Detail, TraceStatusPanel (four independent tiles) |
| 6 | Raw candidate vs delivered response | Met | Trace Detail, ResponseDeliveryPanel (disposition, gate intervention, per-claim consistency) |
| 7 | NOT_APPLICABLE vs unavailable/error vs PASS | Met | PolicyVerdictTag in Trace Explorer and Trace Detail header |
| 8 | Claim, source ID, version, passage, span | Met | RAG Diagnostics, ClaimExplorer (four-step trail, four claim states) |
| 9 | Abstention vs technical failure | Met | RAG Diagnostics, RagOutcomeTag and RagOutcomeNotice |

## Changes made in this round

- The Trace Detail header now shows a "Policy / security verdict" tag next to the "Reliability decision" badge. It previously appeared only in the Trace Explorer.
- New fixture `trace-a8c63e15`: the action is approved and authorized, the policy gate passed, and the gateway then refused to dispatch it (circuit breaker open). Decision is REVIEW, policy verdict PASS. The UI shows "Suppressed, not executed" with the reason "This was not a policy decision".
- New failure label `tool_not_dispatched`, shown as "Tool not dispatched".
- The new fixture is registered in the summaries, details and investigations maps.
- Tests updated: the trace list now expects 13 traces; a contract test covers the new fixture; header tests cover the verdict tag.

## Fixtures (13 traces)

| Trace | Scenario | Decision |
|---|---|---|
| trace-8f21c9a4 | PO proposed before approval, then blocked (approval pending) | BLOCK |
| trace-9a03e771 | Approved, tool ran, PO created | PASS |
| trace-b7d2e4c1 | Duplicate request, existing PO recovered | PASS |
| trace-c35e8a90 | Tool dispatched, no confirmation, effect unknown | REVIEW |
| trace-d41f6b27 | Finance denied, call suppressed, response corrected | BLOCK |
| trace-a8c63e15 (new) | Approved and authorized, gateway refused to dispatch | REVIEW |
| trace-2f88b1e0 | RAG: retrieval fine, one unsupported claim | REVIEW |
| trace-6c41d9f2 | RAG: retrieval missed the evidence, judge also failed | REVIEW |
| trace-e5a7c302 | RAG: out-of-corpus, abstained on purpose | PASS |
| trace-f9b1d7a4 | RAG: provider timeout, model never ran | REVIEW |
| trace-06b7fa21, trace-de08f31a, trace-77f120aa | Summary-only (no stored detail) | BLOCK, PASS, REVIEW |

## Rule applied throughout

Every status is read from its own record field and labelled with its source system. No status is derived from another, and a missing record is shown as "Not recorded", never as a default or a zero.

## Known limits

- Overview numbers are hand-written and do not count the new trace, so the overview total will not match the 13-trace list.
- Authorized-but-not-dispatched is stored as "suppressed", because the type has no separate "not attempted" state. The cause is given in the reason text.
- Live API data and mobile/tablet layouts are not yet verified.
- Changes are not committed yet (about 45 uncommitted files). A branch link will follow once pushed.

## Open items for other owners

- **Mohab:** canonical field names for unconfirmed and suppressed invocations, response disposition, per-claim consistency and support state, and provider-fault details (stage, provider, error code, retryable).
- **Mohamed:** whether approval status includes "cancelled" and links to the actions it gates; the meaning of "policy stage" (TRD-22/23).
