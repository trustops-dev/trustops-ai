# Governance engine contracts

Sprint 1 task S1-04 · Owner: Mohamed Elnaggar · Revision 0.6 (addendum 2026-11-16) · DRAFT

This folder holds the contracts for `packages/governance-engine`: the policy engine, the approval boundary, the reliability decision engine, human review, the audit trail and role checks. Nothing here is implemented. Teammates' scoped responses are recorded in the owner review record below with exact references; none of them is a full acceptance of this folder. Sections headed with a revision number (0.3 to 0.6) describe the state at that revision's date and are historical; the current status is the owner review record.

## Documents

| Document | What it holds |
|---|---|
| [decision-flow.md](decision-flow.md) | The three verdict layers (pre-tool `ALLOW`/`BLOCK`, automated `PASS`/`REVIEW`/`BLOCK`, human `ACCEPT`/`REVIEW`/`BLOCK`), the boundary map from Figures 2–5, decision precedence, invariants and failure behavior |
| [governance-contract.md](governance-contract.md) | Policy evidence, the traceability register, the pre-tool interface, the approval boundary, the decision-engine interface, review, audit, roles and overrides, the decision log (`GD-01`–`GD-33`) and the responses to the handoff checklist and the dashboard questions |
| [policy-truth-tables.md](policy-truth-tables.md) | Case tables for `PROC-APPROVAL-01`, `PROC-TOOL-STAGE-01` and `PROC-SUPPLIER-01`, the aggregation rules, combined and conflicting cases, the SC-03 fixture pair and the decision-precedence conflict cases |
| [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) | Governance's side of the Trace Schema Draft v1.5 review items 1 and 2: checking authorization snapshots against their source evidence, recovery identity, outcome combinations, the consistency finding codes and a disposition table |
| [response-to-owner-packet-0.14.md](response-to-owner-packet-0.14.md) | Governance's ACCEPT/AMEND response to Nour's owner packet 0.14 (commit `479cab0`): OD-02, OD-03, OD-04, OD-05-MAP, OD-06, OD-09, OD-12 children and OD-16, with reviewed file hashes, exact wording, supporting cases and the split between governance-local and joint decisions. The dispositions were sent by email and Nour recorded them on 9 November (`docs/architecture/reference-applications/reviews/mohamed-479cab0-od03-response.md`, PR #27 branch `docs/nour-week1-review-014` at commit `04789d7`); this file is the written response delivered with the follow-up |
| [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md) | Governance's final, dated (14 November) disposition on Nour's follow-up (owner packet at `9e6affa`): the artifacts and the 31-case check, the OD-04 and OD-12 agreement points with Mohab against Trace Schema v1.9, the translation table, the policy-stage answer for the dashboard, the remaining wording, and the GD-26 and OD-09 coordination |
| [response-to-ahmed-evaluator-review.md](response-to-ahmed-evaluator-review.md) | Governance's reply to Ahmed's scoped evaluator review of 13 November: SC-03A and SC-03B expected behavior, prevented versus realized, authoritative outcome evidence, non-timeout `UNKNOWN`, and the evidence boundary for the RCA causes `policy_configuration` and `agent_workflow`. Sent to Ahmed with the file |
| [response-to-policy-bundle-pairing.md](response-to-policy-bundle-pairing.md) | Governance's scoped disposition (16 November) on Nour's policy bundle and corpus pairing: the new `doc-001` text and the unchanged `doc-002`, and why `PROC-TOOL-STAGE-01` needs no retrievable text |
| [response-to-pr29-review.md](response-to-pr29-review.md) | Governance's scoped assessment (16 November) of PR #29 at `ebdefc1` against the contract: approval, currentness, unknown outcome and replay, with required corrections and cases |
| [response-to-pr29-corrections.md](response-to-pr29-corrections.md) | Governance's scoped review (18 November) of the published corrections in PR #29 at `9735513` against those seven findings: ACCEPT as an isolated synthetic scaffold with small AMEND items, and the remaining conditions |
| [policy-configuration/verify_od03_independent.py](policy-configuration/verify_od03_independent.py) and [od03-independent-check-result.json](policy-configuration/od03-independent-check-result.json) | The reproducible independent check of the configuration against Nour's 31 OD-03 cases, and its result with input hashes |
| [policy-configuration/procurement-policy-set-v0.1.yaml](policy-configuration/procurement-policy-set-v0.1.yaml) | The complete synthetic configuration governance proposes for OD-03 (allowlist, supplier rule, validity rule, version identity). `runtime_enabled: false`. Its header says where the scoped acceptance and the hashes are recorded and why the three acceptance fields stay null |
| [owner-review-packet.md](owner-review-packet.md) | What each teammate is asked to review and answer, with a reply template and the record of the outreach and responses so far. The packet as a whole has not been sent as one package |

## Revision 0.3 (2026-10-21, historical)

At the time of revision 0.3, revision 0.2 had been reviewed by nobody. Malak's Sprint 1 wrap-up listed what was missing, and revision 0.3 answered it. The "Now" column is the state at that date.

| Missing | Now |
|---|---|
| Policy truth tables | Written, symbolic, with no threshold invented |
| Decisions written down: calculation tool in `PRE_APPROVAL`, when the stub is replaced, when an approval stays valid | Recorded as `GD-01`, `GD-06` and `GD-04` |
| Approval rule values | Mechanism decided (`GD-03`). **The values themselves are still open and must come from Nour's synthetic policy corpus.** Nothing here supplies them |
| Canonical names (Q-15) | Governance's position in contract §4.5; Mohab and Nour have to agree it |
| Answers to Q-06, Q-07, Q-09, Q-10, Q-13, Q-14 and a review of the 21 dashboard rows | Contract §9.2 and §9.3 |
| Contract sent to all five teammates | The packet was prepared in revision 0.3 and has not been sent as one package. The exchanges that did happen, and the responses recorded, are in the owner review record below |
| S1-01 sign-off | Given by Mohamed on 2026-11-18 with conditions; see below |

## Revision 0.4 (2026-11-05, historical): Trace Schema Draft v1.5 review (items 1 and 2)

A review of Mohab's Draft v1.5 schema package assigned two items to Mohab and Mohamed together: checking authorization snapshots against their actual source evidence, and completing recovery identity and outcome checks. This revision adds governance's side as [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md), and updates the contract (§4.6, §4.7, §6.3, §8, §9.4) and the decision flow (`INV-11` to `INV-14`, §5, §6).

What this revision does **not** do: the v1.5 package files were not available, the validator and the regression runner are Mohab's, and no check has been executed. Nothing is reported as verified. Items 3 to 7 of the review are not governance's. Five new decisions (`GD-24` to `GD-28`) are recorded; four are proposals that need Mohab, Nour, Ahmed, Alaa or the plan owner.

## Revision 0.5 (2026-11-06, historical): Nour's owner packet 0.14

Nour's commit `479cab0` asked for explicit ACCEPT or AMEND answers on seven governance decisions. [response-to-owner-packet-0.14.md](response-to-owner-packet-0.14.md) answers each one separately. This revision also changes the specification where Nour's package, the independent v1.6 review or the execution-budget ADR showed a gap: approval validity clauses V01 to V08 (contract §5.3), a preallocated claim identity with a separate consumption record (§4.7), a fresh check for every retry attempt, effect-state names aligned with the ADR, `STILL_UNRESOLVED`, a non-timeout `UNKNOWN`, claim-time currentness, and a mapping of all 27 of Nour's approval-validity cases (truth tables §8).

The dispositions in the response were sent by email and Nour recorded them on 9 November. The acceptance fields in the configuration stay null; see the header of the configuration file and the section below on where acceptance is recorded. At that date (2026-11-06) the register named no plan approver, so OD-02, OD-06, OD-16 and GD-26 stayed open. That is superseded: Nour is the internal team plan decision owner (recorded 2026-11-14 in `docs/architecture/reference-applications/plan-approval-routing.md`, PR #27 branch `docs/nour-week1-review-014` at commit `c5b2568`). Her row-level plan decisions on OD-02, OD-06 and OD-16 are pending, and the proposed amendments have not been accepted. Two new decisions are recorded (`GD-29`, `GD-30`).

## Revision 0.6 (2026-11-12, with later addenda): Trace Schema Draft v1.9 and Nour's follow-up

Mohab's Trace Schema Draft v1.9 is now the naming source for every field and enum governance shares with the trace (`GD-31`), so the governance documents no longer keep parallel names. The contract's interface sections (§4.1 to §4.8) were rewritten in v1.9 terms, the earlier governance names are listed once in §4.5, and the validator's `ERR_*` codes replace governance's own finding codes where one exists (evidence document §7.1).

Where v1.9 and governance differ, nine schema amendments `SA-01` to `SA-09` are proposed to Mohab (claim status naming, currentness at consumption, approval supersession and terminal rule, the chronology lower bound, approval status values, criticality spelling, the stub label, `execution_scope`, and where `enforcement_outcome` is stored). Two decisions were added: `GD-31` and `GD-32`. The reply to Nour's follow-up is [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md).

Checks run for this revision: the independent 31-case configuration check (31 of 31, with two deliberate negative runs), Mohab's own validator on his specification (2,602 assertions, 0 failures), and one probe showing his chronology rule rejects an approval decided before the trace starts. Nothing was run against a runtime, and the 63-case regression suite was not run by governance.

**13 November addendum (Ahmed's scoped evaluator review).** Truth tables §6 rewritten with the full SC-03A and SC-03B expected behavior (the earlier statement that SC-03A runs no pre-tool check was wrong and is corrected); `enforcement_outcome` value `NOT_REALIZED` renamed `DEFINITIVE_NO_EFFECT`; `ALREADY_EXISTING` inherits the outcome of the original call; authoritative evidence per outcome and the evidence preserved for an unresolved outcome; new governance check `EC-11` (re-derivation of recorded policy results); contract §6.3 (a correct `BLOCK` is not a policy defect) and §6.5 (RCA evidence boundary); `GD-33`; truth-table cases `DC-21` and `DC-22`. The reply is [response-to-ahmed-evaluator-review.md](response-to-ahmed-evaluator-review.md). No new execution: `EC-11` and the realized-pair cases are specification only.

## Owner review record

Status on 16 November 2026. Records are Nour's, kept in the reference-application register on PR #27 branch `docs/nour-week1-review-014` at commit `c5b2568` (not yet on `dev`). Paths below are relative to `docs/architecture/reference-applications/` unless stated. Silence is not an acknowledgement, and no response below is a full acceptance of this folder.

**Plan decisions.** Nour is the internal team plan decision owner (recorded 2026-11-14 in `docs/architecture/reference-applications/plan-approval-routing.md`, PR #27 branch `docs/nour-week1-review-014` at commit `c5b2568`). Her row-level plan decisions on OD-02, OD-06 and OD-16 are pending, and the proposed amendments have not been accepted.

| Reviewer | Outreach so far | Response recorded | Revision reviewed | Exact reference |
|---|---|---|---|---|
| Nour | Governance responses sent by email (9 November) and as files (PR #28, 14 November). Her later requests were answered by [response-to-policy-bundle-pairing.md](response-to-policy-bundle-pairing.md) (pairing proposal at PR #27 `14ee4a24763ed515aeb1b0a1986893380f4f8f22`) and [response-to-pr29-review.md](response-to-pr29-review.md) (PR #29 at `ebdefc194d397804dca8238caf64842cb367ecaf`), both dated 16 November | **Scoped.** OD-03 rows 1 to 5 accepted and row 6 amended, as recorded by her; OD-04 application position 0.2; her independent rerun of the 31-case check agrees. Corpus pairing and integration remain hers. Not a full acceptance | Governance PR #28, first at `7c26168ea47a611d233202e21f0c0b9f7a5cb3c8`; her packet at `479cab00c021db7a58b826b46a653c3e2308b798` | `reviews/mohamed-479cab0-od03-response.md` (historical, 9 November); `reviews/mohamed-7c26168-governance-response.md` (14 November, with artifact hashes); `approval-validity/od04-v0.2.md`; `validation/mohamed-7c26168-governance-refresh.json`; `corpus-review/policy-bundle-pairing-v0.1.md` |
| Mohab | None from governance as a packet. Governance reviewed his Trace Schema Draft v1.9 package (the answer to governance's revision 0.4 requests on authorization snapshots and recovery identity; package hashes in [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md) section 3.4). Nour forwards `SA-01` to `SA-09` to him | **Received:** the Draft v1.9 schema package. **No response recorded yet to these governance requests:** his dispositions of `SA-01` to `SA-09` (including `SA-09`, where `enforcement_outcome` is stored), the 19-row translation (contract §4.5, OD-05-MAP), agreement on OD-12-CLAIM, OD-12-RETRY, OD-12-OUTCOME and OD-12-BUDGET, and his review of the bundle-to-corpus pairing (transport, version, digest) | Trace Schema Draft v1.9 as received by governance | Nour's pending list for Mohab: `handoffs.md` at PR #27 branch `docs/nour-week1-review-014` at commit `c5b2568` |
| Ahmed | His scoped evaluator review of 13 November was answered by [response-to-ahmed-evaluator-review.md](response-to-ahmed-evaluator-review.md), sent to him with the file | **Received and recorded, scoped, evaluator-side.** (1) His response to owner packet `9e6affa` (recorded 15 November) accepts the SC-03A early stop, the SC-03B boundary fixture with scope separation, the four purchasing outcomes, non-timeout `UNKNOWN`, and the `DEC-1` interpretation of GD-26. (2) His taxonomy follow-up (recorded 16 November) confirms governance's sent disposition at PR #28 `ce12629` and amends the label rule to follow the failure taxonomy's tiers. **Settled on the evaluator side by his 16 November reply:** the Tier 3 versus Tier 4 label precedence. **Still open, as recorded by Nour:** the joint OD-09/GD-26 mapping (with governance and Alaa), the SC-03 injected root-cause mapping (joint with governance), implementation of governance check `EC-11` with a paired fixture, and `SA-09` storage (with Mohab and Alaa). The row-level plan decision on GD-26 is Nour's | `9e6affa` and PR #28 `ce12629659bed86c0e1316c473626e0c835a8882` | `reviews/ahmed-9e6affa-evaluator-response.md`; `reviews/ahmed-taxonomy-followup-2026-11-16.md` |
| Alaa | Her review of `479cab0` was supplied to Nour; her matrix v2-4 (14 November) lists five items open with governance, and governance gave its positions on them in the reply of 14 November (email, not a repository file) | **Partial / conditional.** On `479cab0` (recorded 6 November), and her four follow-ups (recorded 16 November): OD-13 restricted canonicalization accepted at design level, `DEC-1` interpretation of GD-26 is her technical position, `DEC-2` to `DEC-6` numeric thresholds deferred, and a G01 admission hold. Nothing in them accepts the governance folder as a whole | Nour's packet at `479cab00c021db7a58b826b46a653c3e2308b798`; Mohamed's response at PR #28 for the follow-ups | `reviews/alaa-479cab0-review.md`, `reviews/alaa-479cab0-review.json`; `reviews/alaa-four-followups-2026-11-16.md` |
| Malak | Nour forwards governance's explanation of `TRD-22` and `TRD-23` (response to `9e6affa`, section 4) | **Scoped, conditional UI acknowledgment** against `479cab0`, recorded 9 November. It is not the S1-07 closeout. **No response recorded yet to this governance request:** her confirmation that the dashboard shows the policy stage as an input label and the policy-check result as the "Policy gate" tile | Nour's handoff at `479cab00c021db7a58b826b46a653c3e2308b798` | `reviews/malak-479cab0-ui-response.md` |

### Where the scoped acceptance and the artifact hashes are recorded

| What | Where |
|---|---|
| Governance's scoped dispositions, dated 14 November | [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md) (final); the earlier email dispositions of 9 November are in [response-to-owner-packet-0.14.md](response-to-owner-packet-0.14.md) |
| Hashes of the configuration, the checker and its result | [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md) section 2, and `input_sha256_lf_normalised` in [od03-independent-check-result.json](policy-configuration/od03-independent-check-result.json) |
| Nour's exact-revision record, with hashes of the seven reviewed files and her independent rerun | `reviews/mohamed-7c26168-governance-response.md` and `validation/od03-independent-7c26168-result.json`, PR #27 branch `docs/nour-week1-review-014` at commit `04789d7` |
| Why `accepted_by`, `accepted_at` and `acceptance_evidence` are null | The header of [procurement-policy-set-v0.1.yaml](policy-configuration/procurement-policy-set-v0.1.yaml): they mean acceptance as the operative runtime configuration, which needs Mohab's transport and digest agreement, Nour's corpus pairing and integration, and Nour's row-level plan decisions on OD-02, OD-06 and OD-16 (pending; the amendments have not been accepted). A file also cannot hold the hash of its own acceptance. `runtime_enabled` stays `false` |

## S1-01 sign-off by Mohamed (given)

The [S1-01 handoff checklist](../reference-applications/handoffs.md#mohamed--s1-04-policy-interaction-and-approval-authority) asks Mohamed for a written policy-evidence sign-off. **Mohamed gave it to Nour by message on 2026-11-18**, with the conditions below. The message to Nour is the authoritative copy; the text below records it. It is a sign-off on the rows and revisions it names. It is not acceptance of the policy release, it does not set `runtime_enabled`, and it is not OD-14 acceptance.

```text
Reviewer: Mohamed Elnaggar
Date: 2026-11-18
Revision reviewed: reference-application package at commit 479cab00c021db7a58b826b46a653c3e2308b798
  (file hashes in response-to-owner-packet-0.14.md). Later material was reviewed
  separately and is not covered here: the policy bundle pairing at 14ee4a2 and
  PR #29 at ebdefc1, each with its own response file.
Governance revision: 0.6 with addenda, PR #28 at commit
  fb27a2016306eccac30e70b708b89da8c5634507
Status: GIVEN, with the conditions below
Rows accepted: the trusted-context rule, the approval boundary owned by governance,
  the proposal / check / dispatch separation, and the authorization-binding
  principle, subject to the conditions below
Conditions:
  1. calculate_approval_level may run in PRE_APPROVAL as a read-only tool; this
     extends the proposal's three-tool list (GD-01)
  2. the policy stage is the four-value coarse stage; finer state names stay with
     Nour and Mohab (GD-02)
  3. the approval threshold, currencies and level names live only in versioned
     governance configuration; the synthetic values proposed by Nour (USD 5000.00,
     manager) are accepted only as MVP configuration, per the OD-03 response (GD-03)
  4. amounts are exact decimals, not binary floats (contract §2.4)
  5. the runtime preallocates the claim identity, verifies the binding and the
     current approval and supplier versions, and consumes the single dispatch
     allowance once, atomically (GD-07, GD-28, GD-30)
  6. no verdict, timeout or error means no dispatch, covered by a test (GD-09)
  7. the application contains no policy threshold logic of its own (contract §5.1)
Not covered: this sign-off does not accept the policy release, set runtime_enabled,
  or constitute OD-14 acceptance. Nothing was run against a runtime.
```

## Revision history

| Revision | Date | Change |
|---|---|---|
| 0.1 | 2026-10-18 | Personal draft; not in the team repository |
| 0.2 | 2026-10-18 | Decision flow and contract register merged to `dev` in PR #14, reconciled with the reference-application contracts |
| 0.3 | 2026-10-21 | Policy truth tables, decision log with statuses, canonical-values proposal, approval validity, roles and overrides, review packet, responses to the wrap-up and to the dashboard questions |
| 0.6 | 2026-11-12 | Naming aligned to Trace Schema Draft v1.9 (`GD-31`); contract §4.1 to §4.8 rewritten; claim identity made root-scoped; approval-record supersession, terminal rule and chronology proposals (`GD-32`); policy stage versus policy-check result for the dashboard; RAG policy evidence aligned with Ahmed's evaluator contract; reproducible 31-case check and its result; reply to Nour's follow-up; `SA-01` to `SA-09` |
| 0.6 addendum 6 | 2026-11-18 | Nour's request of 18 November: new [response-to-pr29-corrections.md](response-to-pr29-corrections.md), governance's review of the published PR #29 corrections at `9735513` against the earlier seven findings. No change to the contract, the configuration or the check result |
| 0.6 addendum 5 | 2026-11-18 | Follow-up commit `fb27a20` (Tier 3/4 scope wording, result provenance, `.gitleaksignore` for a verified false positive) was pushed to PR #28 on 2026-11-18. This update records Mohamed's S1-01 policy-evidence sign-off, given to Nour by message on 2026-11-18 with seven conditions, covering the package at `479cab0` and governance at `fb27a20`; the sign-off block and the contract's status row are updated. Contract §6.3 and the GD-16 row now mark governance's earlier blanket `POLICY_VIOLATION` label recommendation as historical, superseded by Ahmed's tier-based rule |
| 0.6 addendum 4 | 2026-11-17 | Nour's provenance wording points: Ahmed's 16 November reply settles Tier 3 versus Tier 4 precedence on the evaluator side only (the joint OD-09/GD-26 mapping and the SC-03 root cause remain open); the check result's source note now names the exact export revision of the candidate inputs (`a62f4e7`, byte-identical at `479cab0`, `9e6affa` and `c5b2568`) instead of saying they were read from `479cab0` |
| 0.6 addendum 3 | 2026-11-16 | Nour's wording checks: Nour recorded as the internal team plan decision owner (row-level decisions on OD-02, OD-06 and OD-16 pending, amendments not accepted); every "not received" states which governance request has no response and lists the Mohab and Ahmed replies that are recorded; current-status wording no longer says nobody acknowledged the work, and older revision sections are marked historical. New governance responses to the pairing proposal and to PR #29. Contract §6.3 notes Ahmed's recorded label rule. The YAML and its hash are unchanged since the 14 November commit |
| 0.6 addendum 2 | 2026-11-14 | Nour's request of 14 November: the outreach and scoped responses received are recorded with exact references (README and owner review packet); the revision-template wording is replaced by exact commits; the configuration header is reconciled with the final dated response and explains the null acceptance fields; the configuration's hash and the check result's input hash change because only a header comment changed (canonical content, `runtime_enabled: false` and the 31-case result are unchanged) |
| 0.6 addendum | 2026-11-13 | Reply to Ahmed's scoped evaluator review: SC-03A and SC-03B behavior corrected and completed, `NOT_REALIZED` renamed `DEFINITIVE_NO_EFFECT`, `EC-11`, contract §6.5, `GD-33`, `DC-21` and `DC-22` |
| 0.5 | 2026-11-06 | Response to Nour's owner packet 0.14; synthetic policy configuration proposal; approval validity V01 to V08; preallocated claim with separate consumption record; fresh check per attempt; effect-state names aligned with the budget ADR; truth-table cases AP-16 to AP-19, AG-13, CT-01 to CT-08 and the OD-04 case mapping; `GD-29`, `GD-30` |
| 0.4 | 2026-11-05 | Evidence consistency and recovery specification (review items 1 and 2), `INV-11` to `INV-14`, `GD-24` to `GD-28`, `enforcement_outcome` gains a fourth value (named `NOT_REALIZED` then, `DEFINITIVE_NO_EFFECT` since 13 November), new truth-table cases |
