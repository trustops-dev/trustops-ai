# Owner review packet

Revision 0.6 · 2026-11-06 · Part of the [governance contracts](README.md). Nour's owner packet 0.14 has its own answer in [response-to-owner-packet-0.14.md](response-to-owner-packet-0.14.md).

This page is what each teammate needs in order to review the governance contract. It is **prepared and not sent**. Nobody has been contacted, and no owner has acknowledged anything.

## What to send

Send each owner their section below, with links to the [governance contract](governance-contract.md), the [decision flow](decision-flow.md) and the [policy truth tables](policy-truth-tables.md). It takes three steps:

1. Read the sections listed for you.
2. For each decision listed, answer "agree", "agree with a change" or "disagree", and say if you are not the right owner.
3. Reply with your name, the date and the revision you reviewed (0.5).

A decision marked DECIDED already governs the governance package. Your reply tells Mohamed whether it also works for your subsystem; it does not wait on you to start Sprint 2 work inside governance. A reply of "accepted" counts only for the items it names.

## Reply template

```text
Reviewer: <name>
Date: <date>
Revision reviewed: 0.5
Decisions agreed: <GD ids, or 'all except the ones below'>
Decisions changed: <GD id: change>
Decisions I disagree with: <GD id: reason>
Items I do not own: <id: who does>
Answers: <question: answer>
Conditions: <anything unresolved>
```

## Nour — reference applications and scenarios

Read: contract §2 (stages, applicability, evidence), §4.1–§4.2 (request and response), §5 (approval boundary), truth tables §6 (SC-03), decision flow §5.1 (failure behavior).

| Decision | Question |
|---|---|
| GD-01 | `calculate_approval_level` is allowed in `PRE_APPROVAL` as a read-only tool. This extends the proposal's three-tool list. Does that match what you proposed (D3)? |
| GD-02 | Policy keys on four coarse stages (`PRE_APPROVAL`, `APPROVED`, `PO_CREATION`, `COMPLETED`), and `APPROVED` allows only the purchase-order proposal. Does the allowlist table in §2.1 match your state machine? |
| GD-03 | **Input needed.** Please supply the approval threshold, the supported currencies and the approval-level names from your synthetic policy corpus. They live only in `policies/procurement.yaml`. Governance supplies no value |
| GD-04 | The approval validity rules in §5.3, with no time-based expiry in the MVP. Do the binding fields match your `ApprovalEvidence`? |
| GD-07, GD-08 | The runtime verifies the `authorization_snapshot` and consumes the dispatch claim once; if your reported policy version differs from the active one, the check blocks and you re-derive your evidence under the active version |
| GD-09 | The tool hook treats "no verdict" (timeout, error, unreachable) as no dispatch, and a test covers it |
| GD-17 | The RAG assistant has no pre-tool check, and its policy evidence is `NOT_APPLICABLE` |
| GD-20 | Supplier status set (governance needs only the literal `APPROVED`), and the blocked-call event: is the recommended three-event model with `execution_started = false` acceptable? |
| GD-23 | The `execution_scope` marker for SC-03B: recorded only, never changes a verdict |
| Fixture | The SC-03B control and candidate pair in truth tables §6. Does it match your S3-03 handoff? |
| GD-28 | The runtime issues one dispatch-claim id per `ALLOW`, identical on the authorization snapshot, the atomic transition and the invocation. Governance verifies equality and issues no claim id. Does that match your atomic claim? |
| GD-27 | Recovery grants no authorization, never dispatches again, uses the original idempotency key and business-payload digest, and is a separate observation that never replaces the original timeout. Outcome combinations are in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §6.2. Does your runtime follow them? |
| GD-24, GD-25 | Governance compares copied values with the records they reference and the record wins. Which of your events does the platform adapter resolve for each reference (§3 of the new document)? |

## Mohab — trace schema, ingestion and platform

Read: contract §3 (register), §4 (interface and §4.5 canonical values), §7.2 (audit), decision flow §5.

| Decision | Question |
|---|---|
| GD-05 | Governance adopts your route `POST /api/v1/policy/check` and the `tool_proposal` / `policy_check` events. Please confirm the router and the mapping of E17, E18 and E19 |
| GD-20, GD-31 | Trace Schema v1.9 is now the naming source and governance follows it. Please confirm the 19-row translation (contract §4.5) and answer the schema amendments SA-01 to SA-09 in [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md) §3.4 |
| Gap 1 (Schema v1 §8) | Governance recommends your three events, provided the blocked outcome carries `execution_started = false`. Does that fit Nour's `NOT_EXECUTED`? |
| Gap 4 (Schema v1 §8) | Policy needs only the four coarse stages, so the nine-value list does not have to cover every policy transition |
| GD-10 | Mohamed authors the governance models and enums in `packages/contracts`, and you review them |
| GD-11 | One unit of work across platform and governance repositories, so a check and its audit row commit together |
| GD-14 | **Input needed.** Which prototype identity mechanism, and who supplies it. Needed before S6-01 |
| GD-04 | How a continuation after a pending approval is represented in the trace |
| Wording | Schema v1 §4.3 states the policy as "`amount > 5000`". The proposal's number is an illustration and the threshold is configured, so the wording could say "the configured threshold" |
| GD-24 | The platform adapter resolves each reference (normalized request, supplier result, calculation result, approval event, proposal, state snapshot) to exactly one record behind a port governance defines. Governance compares and reports the findings. Governance proposes `ports/evidence_resolver.py` and `policy/evidence_consistency.py`, outside the approved tree, plus one finding-code registry in `packages/contracts`. Do you agree? |
| GD-25 | Copies are claims and source records are evidence; any finding prevents `ALLOW` and verified-binding certification, and `trusted_source_verified` is derived, never evidence. Can your validator report the same finding codes (§4 and §6.4 of the new document) for the review's mutations? |
| GD-27, GD-28 | The outcome-combination table, the single terminal result per invocation, the recovery rules RC-01 to RC-08, and the dispatch-claim record. Please confirm the value set of `side_effect_state` and the field names I took from the review text (`trusted_source_verified`, `recovery_of_call_id`, `recovery_of_result_id`), since the v1.5 package files were not available to governance |

## Ahmed — evaluators, classifier and RCA

Read: contract §3.2–§3.3, §6.3, truth tables §6–§7.

| Decision | Question |
|---|---|
| GD-16 | Each post-run policy `FAIL` carries `enforcement_outcome` (`PREVENTED`, `REALIZED`, `DEFINITIVE_NO_EFFECT` (renamed from `NOT_REALIZED` on 13 November), `UNKNOWN`). `DEC-1` fires for all four. How do you map them to labels (OD-09)? Governance's answers to your scoped review are in [response-to-ahmed-evaluator-review.md](response-to-ahmed-evaluator-review.md) |
| GD-27 | **Review requested.** The outcome interpretation in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §6.2 and §6.6: an uncertain timeout stays `UNKNOWN`. Your [evaluation pipeline](../evaluation-pipeline.md) shows a mock-tool timeout with `side_effect_committed = false`, which asserts a certainty a dispatched timeout does not have. Can you align it with Mohab? |
| GD-26 | A purchase order executed under an authorization that fails the consistency rules fires `DEC-1`. This extends `DEC-1` beyond a policy `FAIL`. Do you agree? |
| GD-12 | The decision engine takes raw metrics and compares them to thresholds in `config/decision_thresholds.yaml`. Please define "borderline", "strong disagreement" and "low certainty", and which security findings count as critical per attack category |
| Features | Policy features come from the per-policy `status` and `criticality`, as in proposal §L.2. Does your feature pipeline need anything else from governance? |
| SC-03 | Mapping the supplier fixture to an RCA cause needs your review and mine (Nour's SC-03 text); governance does not set `injected_root_cause` alone. Governance's evidence boundary for `policy_configuration` and `agent_workflow` is contract §6.5 |

## Alaa — versions, datasets, experiments and the gate

Read: contract §6.2, §6.4, §7.4, truth tables §7.

| Decision | Question |
|---|---|
| GD-22 | The governance decision engine produces the release verdict through `gate/decision_adapter.py`. You own the comparison, the gate artifact and what happens to the candidate, and your gate module calls the adapter. Do you agree? |
| GD-13 | An incomplete evaluation has no `decision`, carries `evaluation_status = INCOMPLETE`, and the gate treats it as non-approving. Does the artifact format allow a null decision? |
| GD-12 | Threshold values come from your measured baselines into `config/decision_thresholds.yaml`, versioned. Who writes the file, and when? |
| Field names | Governance uses `policy_bundle_version`, `decision_config_version` and `decision_engine_version`. Your S1-05 requirements list the names as pending |
| GD-19 | An approved override never changes the recorded `BLOCK`. What it means for the candidate is your disposition. Does the plan allow overrides? |
| DC-16 | How does your comparison identify "a candidate allows an unsafe action the baseline prevented" so `DEC-1` can use it? |
| GD-26 | A purchase order executed under an unverified authorization is a critical finding for the release gate too, and fires `DEC-1`. Does the comparison have a place to carry it? |

## Malak — dashboard

Read: contract §7 (roles, audit, overrides), §9.2 and §9.3.

| Decision | Question |
|---|---|
| GD-15 | Raw payloads for `ADMIN` only; review history and audit history read-only for every role. Does that match your screens? |
| GD-18 | Capability-based roles with the seven story role codes. Does the table in §7.3 match Appendix B? |
| GD-13 | The wording for "Incomplete evaluation" in `RCA-07` |
| GD-21 | Governance-owned actions are review, override request and override decision. Policy configuration and role assignment are API-only, and the login form and account management are outside the seven screens |
| §9.3 | Four rows changed: `TRD-43` gains `check_mode`; `TRD-71` gains `administrator_action`; `RCA-07` gains `decision_engine_version`; `RCA-08` gains `not_evaluated_rules`. Please confirm the display |
| GD-19 | The audit catalogue now has override actions. Confirm the override flow you drew |
