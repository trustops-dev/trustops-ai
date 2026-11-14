# Policy and decision truth tables

| | |
|---|---|
| **Status** | DRAFT v0.6 — Sprint 1 closeout (S1-04). Specification only; no engine code exists. Not acknowledged by any teammate. |
| **Owner** | Mohamed Elnaggar — `packages/governance-engine` |
| **Part of** | [Governance contract](governance-contract.md) §2.3 and [decision flow](decision-flow.md) §3 |

These tables turn the rules in the [governance contract](governance-contract.md) into cases that become unit tests in Sprint 2 (`tests/unit/governance_engine/`). Every case states inputs, result state and a draft reason code.

**No value is invented.** `T` is the configured approval threshold, `C` the configured set of supported currencies, and `A[stage]` the configured allowlist, all read from versioned configuration (`policies/procurement.yaml`). The tests use clearly labelled test-fixture values. The cases are symbolic, as the reference-application contracts require [N: "boundary cases planned symbolically, not populated with invented thresholds"].

Result states: `PASS`, `FAIL`, `NOT_APPLICABLE`, `ERROR`. `ERROR` means "could not decide" and is never a violation and never a success. Reason codes are drafts for review; the final taxonomy is frozen with the contract models.

---

## 1. Notation

| Symbol | Meaning |
|---|---|
| `a`, `c` | Amount of the **proposed** purchase (exact decimal) and its currency |
| `T` | Configured approval threshold, in its own configured currency |
| `t`, `s` | Proposed tool and current coarse workflow stage |
| `A[s]` | Configured allowlist for stage `s` |
| `rev` | Request revision the evidence is bound to |
| approval record | Governance-owned record for the approval-request id; `PENDING`, `APPROVED`, `DENIED` or `CANCELLED` |

Amounts are exact decimals (decimal strings in the interface), never binary floats, so equality with `T` is decided exactly [N: Money type]. "Exceeds" is strict `>` [P §R.1].

Values match exactly and case-sensitively against the canonical enums (`APPROVED`, not `approved`). Display code may be case-insensitive; the policy engine is not.

Every input in these tables is the value **resolved from the source record the check references**, not a value copied into a request or snapshot. A copy that differs from its source is a separate evidence-consistency finding ([evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §4); it never changes the policy result.

---

## 2. `PROC-APPROVAL-01` — approval before action

Evaluated when `t = create_purchase_order`. For any other tool the result is `NOT_APPLICABLE`.

| Case | Condition | Result | Reason code |
|---|---|---|---|
| AP-01 | `a < T`, supported `c` | `NOT_APPLICABLE` (basis `NOT_REQUIRED`) | `APPROVAL_NOT_REQUIRED` |
| AP-02 | `a = T` (equality does not exceed) | `NOT_APPLICABLE` (basis `NOT_REQUIRED`) | `APPROVAL_NOT_REQUIRED` |
| AP-03 | `a > T`, no approval record | `FAIL` | `APPROVAL_MISSING` |
| AP-04 | `a > T`, record `PENDING` | `FAIL` | `APPROVAL_PENDING` |
| AP-05 | `a > T`, record `DENIED` | `FAIL` | `APPROVAL_DENIED` |
| AP-06 | `a > T`, record `CANCELLED` | `FAIL` | `APPROVAL_CANCELLED` |
| AP-07 | `a > T`, `APPROVED`, bound to a different `rev` | `FAIL` | `APPROVAL_STALE_REVISION` |
| AP-08 | `a > T`, `APPROVED`, bound amount, currency, supplier or level differs from the proposal | `FAIL` | `APPROVAL_BINDING_MISMATCH` |
| AP-09 | `a > T`, `APPROVED`, decided after the proposal event | `FAIL` | `APPROVAL_AFTER_PROPOSAL` |
| AP-10 | `a > T`, `APPROVED`, bound correctly, decided before the proposal, validity rule holds | `PASS` | `APPROVAL_VALID` |
| AP-11 | `a` missing, not a decimal, or not positive | `ERROR` | `AMOUNT_INVALID` |
| AP-12 | `c` not in `C`, or no threshold configured in `c` | `ERROR` | `CURRENCY_UNSUPPORTED` |
| AP-13 | `T` or the rule configuration missing | `ERROR` | `POLICY_CONFIG_MISSING` |
| AP-14 | `t ≠ create_purchase_order` | `NOT_APPLICABLE` | `TOOL_OUT_OF_SCOPE` |
| AP-15 | `a > T`, and the approval event and governance's approval record disagree on the decision or its binding | `FAIL` | `APPROVAL_EVIDENCE_CONTRADICTION` |
| AP-16 | `a > T`, and the approval's order relative to the proposal cannot be established (future-dated, unorderable or conflicting evidence) | `ERROR` | `APPROVAL_ORDER_UNDETERMINED` |
| AP-17 | The configuration is invalid (comparator is not `GT`, threshold or approval level missing) | `ERROR` | `POLICY_CONFIG_INVALID` |
| AP-18 | The approval-validity block is missing from the configuration (contract §5.3 V01) | `ERROR` | `POLICY_CONFIG_MISSING` |
| AP-19 | `a > T`, `APPROVED`, but the approver reference does not resolve to an approver whose level satisfies the required level | `FAIL` | `APPROVER_NOT_ELIGIBLE` |

Notes:

- **Governance derives the requirement.** Whether approval is required comes from `a`, `c` and `T`, never from the application's `approval_required` flag (`INV-10`). If the application reported `approval_required = false` while `a > T`, the case is still AP-03 to AP-10, and a diagnostic finding `REPORTED_FLAG_MISMATCH` is recorded without changing the result.
- **Approval status is authoritative.** It is read from governance's approval record, not from a status string in the request.
- **Proposal versus request mismatch.** If the amount, currency or supplier in the proposal's arguments differs from the immutable request snapshot, that is not a policy case. It is a check-level `CONTEXT_MISMATCH` (§5, case AG-06), which fails closed.
- **Validity rule.** AP-10 requires the validity rule in the policy set (contract §5.3): valid while the bound request revision is current and the record has not become `DENIED` or `CANCELLED`; no time-based expiry in the MVP.

---

## 3. `PROC-TOOL-STAGE-01` — tool permission by stage

Evaluated for **every** tool proposal. The allowlist is the one in the [governance contract](governance-contract.md) §2.1.

| Case | Condition | Result | Reason code |
|---|---|---|---|
| TS-01 | `s = PRE_APPROVAL`, `t` in {`search_policy`, `get_supplier`, `calculate_approval_level`, `request_approval`} | `PASS` | `TOOL_ALLOWED_IN_STAGE` |
| TS-02 | `s = PRE_APPROVAL`, `t = create_purchase_order` | `FAIL` | `TOOL_NOT_ALLOWED_IN_STAGE` |
| TS-03 | `s = APPROVED`, `t = create_purchase_order` | `PASS` | `TOOL_ALLOWED_IN_STAGE` |
| TS-04 | `s = APPROVED`, `t` is any read tool or `request_approval` | `FAIL` | `TOOL_NOT_ALLOWED_IN_STAGE` |
| TS-05 | `s = PO_CREATION`, any new proposal | `FAIL` | `TOOL_NOT_ALLOWED_IN_STAGE` |
| TS-06 | `s = COMPLETED`, any proposal | `FAIL` | `TOOL_NOT_ALLOWED_IN_STAGE` |
| TS-07 | `t` is not one of the five catalogued tools | `FAIL` | `TOOL_NOT_ALLOWED_IN_STAGE` |
| TS-08 | `s` missing or not a canonical stage | `ERROR` | `STAGE_UNKNOWN` |
| TS-09 | no allowlist configured for `s` | `ERROR` | `POLICY_CONFIG_MISSING` |

Notes:

- **Exact match, no normalization.** `Create_Purchase_Order` is not `create_purchase_order`. Names come from runtime code, not model text, so there is nothing to normalize and nothing to bypass by casing.
- **The stage check is coarse on purpose.** The application keeps the finer agent-state rules (for example `search_policy` only in `REQUEST_CAPTURED`). A coarse stage allowance never permits skipping a prerequisite [N].
- **TS-04 is deliberately strict.** Only the purchase-order proposal is allowed in `APPROVED`, as in the state contract [N]. If the team wants other tools there, it is a configuration change, not a code change.
- **TS-05 covers authorization reuse.** A second proposal while in `PO_CREATION` cannot borrow the first `ALLOW` (`INV-9`).

---

## 4. `PROC-SUPPLIER-01` — supplier eligibility

Evaluated when `t = create_purchase_order`. For any other tool the result is `NOT_APPLICABLE`.

| Case | Condition | Result | Reason code |
|---|---|---|---|
| SU-01 | Snapshot supplier id equals the proposal's, status `APPROVED` | `PASS` | `SUPPLIER_APPROVED` |
| SU-02 | Status `NOT_APPROVED` | `FAIL` | `SUPPLIER_NOT_APPROVED` |
| SU-03 | Status `UNKNOWN` | `FAIL` | `SUPPLIER_STATUS_UNKNOWN` |
| SU-04 | Any other non-null status string | `FAIL` | `SUPPLIER_NOT_APPROVED` |
| SU-05 | Lookup outcome `NOT_FOUND` | `FAIL` | `SUPPLIER_NOT_FOUND` |
| SU-06 | Snapshot supplier id differs from the proposal's | `FAIL` | `SUPPLIER_ID_MISMATCH` |
| SU-07 | No snapshot, lookup outcome `ERROR`, or status null | `ERROR` | `SUPPLIER_EVIDENCE_MISSING` |
| SU-08 | `t ≠ create_purchase_order` | `NOT_APPLICABLE` | `TOOL_OUT_OF_SCOPE` |

Notes:

- **Only the literal `APPROVED` passes.** Other drafts spell the non-approved status differently (`NOT_APPROVED`, `UNAPPROVED`, `SUSPENDED`); the policy needs no list of them, because every non-null value other than `APPROVED` is SU-04.
- **A snapshot from a different request revision** is a check-level `CONTEXT_MISMATCH` (§5, AG-06), not a supplier result.
- **Missing evidence is not a verdict on the supplier.** SU-07 is `ERROR`; the supplier is not declared unapproved.

---

## 5. Aggregation into the pre-tool verdict

The overall verdict is computed from the per-policy results of the applicable policies. Every applicable policy is always evaluated and recorded, even after the first `FAIL`.

| Case | Per-policy results | Verdict | Basis |
|---|---|---|---|
| AG-01 | All `PASS` / `NOT_APPLICABLE` | `ALLOW` | `ALL_APPLICABLE_PASSED` |
| AG-02 | At least one `FAIL`, no `ERROR` | `BLOCK` | `MANDATORY_POLICY_FAILED` |
| AG-03 | At least one `ERROR`, no `FAIL` | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` |
| AG-04 | At least one `FAIL` and at least one `ERROR` | `BLOCK` | `MANDATORY_POLICY_FAILED` (the `ERROR` results are still recorded) |
| AG-05 | Policy-set version reported by the application differs from the active version | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` (check-level) |
| AG-06 | Proposal, request snapshot, supplier snapshot or approval evidence disagree on request revision, amount, currency or supplier (`CONTEXT_MISMATCH`) | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` (check-level) |
| AG-07 | Request malformed or mandatory fields missing | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` (check-level) |
| AG-08 | No response (timeout, exception, unreachable) | no verdict | The caller treats it as no dispatch and records a technical check error |
| AG-09 | Replay of the same trace, proposal and attempt | the original result | — |
| AG-13 | A retry of a read-only tool, with a new attempt id | a fresh check with its own `check_id` and `authorization_snapshot` | per the evidence of that attempt |
| AG-10 | Evidence-consistency finding raised, every policy `PASS` / `NOT_APPLICABLE` on the source values | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` — contradictory evidence cannot produce `ALLOW` |
| AG-11 | Evidence-consistency finding raised, and at least one policy `FAIL` on the source values | `BLOCK` | `MANDATORY_POLICY_FAILED` (the findings are recorded too) |
| AG-12 | A referenced evidence record is unresolved, ambiguous or duplicated | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` (the affected policy is `ERROR`) |

The `ALLOW` result also carries the binding described in the contract §4.2.

### 5.1 Combined and conflicting cases

These are the cases most likely to be implemented wrongly, so each becomes its own test.

| Case | Situation | Approval | Stage | Supplier | Verdict / basis |
|---|---|---|---|---|---|
| CB-01 | Valid approved purchase, stage `APPROVED` | AP-10 `PASS` | TS-03 `PASS` | SU-01 `PASS` | `ALLOW` / satisfied |
| CB-02 | Purchase at exactly `T`, stage `APPROVED`, supplier approved | AP-02 `NOT_APPLICABLE` | TS-03 `PASS` | SU-01 `PASS` | `ALLOW` / satisfied |
| CB-03 | Approval bypass: over `T`, no approval, stage `PRE_APPROVAL` | AP-03 `FAIL` | TS-02 `FAIL` | SU-01 `PASS` | `BLOCK` / violation (both findings recorded) |
| CB-04 | Valid approval but the stage is still `PRE_APPROVAL` | AP-10 `PASS` | TS-02 `FAIL` | SU-01 `PASS` | `BLOCK` / violation — a valid approval does not override the stage rule |
| CB-05 | Over `T`, approval valid, stage `APPROVED`, supplier `NOT_APPROVED` | AP-10 `PASS` | TS-03 `PASS` | SU-02 `FAIL` | `BLOCK` / violation — one failing policy is enough |
| CB-06 | Over `T`, approval `PENDING`, supplier `NOT_APPROVED`, stage `APPROVED` | AP-04 `FAIL` | TS-03 `PASS` | SU-02 `FAIL` | `BLOCK` / violation (two findings) |
| CB-07 | Approval fails and supplier evidence is missing | AP-03 `FAIL` | TS-03 `PASS` | SU-07 `ERROR` | `BLOCK` / violation (AG-04) |
| CB-08 | Below `T`, stage `PRE_APPROVAL`, tool is `create_purchase_order` | AP-01 `NOT_APPLICABLE` | TS-02 `FAIL` | SU-01 `PASS` | `BLOCK` / violation — no approval needed does not allow the wrong stage |
| CB-09 | `get_supplier` proposed in `PRE_APPROVAL` | AP-14 `NOT_APPLICABLE` | TS-01 `PASS` | SU-08 `NOT_APPLICABLE` | `ALLOW` / satisfied |
| CB-10 | Second `create_purchase_order` proposal while in `PO_CREATION` | AP-14 or per evidence | TS-05 `FAIL` | per evidence | `BLOCK` / violation — an earlier `ALLOW` cannot be reused |
| CB-11 | Stage unknown | per evidence | TS-08 `ERROR` | per evidence | `BLOCK` / evaluation error, unless another policy already `FAIL`s (then violation) |

---

## 6. SC-03: unapproved supplier (expected behavior for Nour and Ahmed)

The reference-application contracts define two scopes [N, failure planning SC-03]. This section gives governance's full expected behavior for each, in Trace Schema v1.9 names. Both have a paired control that differs only in the supplier status.

### 6.1 Scope A and scope B

| | **SC-03A** full application, early stop | **SC-03B** isolated pre-tool boundary test |
|---|---|---|
| What it is | A real run. `get_supplier` returns `FOUND` with `supplier.status = NOT_APPROVED` and the application's own guard stops. The supplier evidence and the actual final response are preserved [N] | A synthetic fixture that sends a well-formed `create_purchase_order` proposal with a `NOT_APPROVED` supplier straight to the pre-tool interface. Marked `BOUNDARY_TEST` (SA-08) |
| Prerequisites | A valid request; `search_policy` returned `MATCHED`; the supplier record is current | A well-formed proposal; the approval prerequisite satisfied (amount not above the threshold, so `NOT_REQUIRED`, or a valid bound approval); request, amount, currency, supplier id and arguments agree (same digest); the supplier snapshot is the current record and says `NOT_APPROVED`; the active bundle is consistent. A malformed approval or argument makes this an invalid isolation pair, not proof of supplier-rule coverage |
| Policy stage | `PRE_APPROVAL` throughout (`REQUEST_CAPTURED` and `POLICY_CHECKED` are both `PRE_APPROVAL`) | `APPROVED` (`policy_stage_at_proposal` and `checked_policy_stage`) |
| Policy check executed? | **Yes, for each read-tool proposal that reached the hook** (GD-02): `search_policy` and `get_supplier` each get a `policy_check`. **No** check for `create_purchase_order`, because none is proposed | **Yes, once**, on the purchase-order proposal. Real engine (`ONLINE_PRE_TOOL`) for acceptance; the stub is a contract rehearsal only |
| Per-policy results | On the `get_supplier` check: `PROC-TOOL-STAGE-01` `PASS` (TS-01); `PROC-APPROVAL-01` and `PROC-SUPPLIER-01` `NOT_APPLICABLE` (AP-14, SU-08). **`PROC-SUPPLIER-01` is not evaluated against the supplier status here** | `PROC-TOOL-STAGE-01` `PASS` (TS-03); `PROC-APPROVAL-01` `NOT_APPLICABLE` (AP-01 or AP-02) or `PASS` (AP-10); **`PROC-SUPPLIER-01` `FAIL`** (SU-02, `SUPPLIER_NOT_APPROVED`) |
| `action_verdict` | `ALLOW` on both read checks, `ALL_APPLICABLE_PASSED`. There is no `BLOCK` in the trajectory | **`BLOCK`**, `verdict_basis = MANDATORY_POLICY_FAILED` |
| Dispatch suppressed? | Nothing to suppress: no purchase-order proposal exists, so no `tool_suppression` | **Yes.** `tool_suppression`: `suppression_source = PRE_TOOL_POLICY_GATE`, `blocking_check_id` = the check, `blocking_policy_ids = [PROC-SUPPLIER-01]`, `tool_dispatched = false`, `execution_started = false`, `side_effect_state = NONE`. No `tool_call`, no `tool_result` |
| Application state | `last_app_state = POLICY_CHECKED`; it never enters `SUPPLIER_CHECKED`. Trace `execution_status = STOPPED_BUSINESS_BLOCK` | **No application history is fabricated** [N]: the stage `APPROVED` is the proposal's policy context only, not an application state the run reached, and no prior transitions are invented. The blocked trace carries `execution_status = HALTED_POLICY_BLOCK`. The combination of stage `APPROVED` and a `NOT_APPROVED` supplier is **not reachable** in the real application and is confined to this boundary fixture |
| Side effect | None. No calculation, no approval submission, no purchase order. `po_creation_dispatch_claims.spent_count = 0` | `side_effect_state = NONE`; `claim_status_at_check = NOT_CLAIMED_BLOCKED`; no consumption record; `spent_count = 0` |
| Post-run policy evidence | No policy `FAIL` exists. The stop is an ordinary business rejection at the application guard | `PROC-SUPPLIER-01` `FAIL`, `enforcement_outcome = PREVENTED` |
| Layer 2 | No policy-driven `BLOCK`; the decision comes from the other evidence | `BLOCK` (`DEC-1`) |
| What it proves | Successful prevention at the application layer. **It is not evidence that the pre-tool purchase-order policy was exercised** | Successful enforcement by the policy gate |

**Control** (supplier `APPROVED`, everything else identical). SC-03A: the run continues past `POLICY_CHECKED`. SC-03B: `PROC-SUPPLIER-01` `PASS` (SU-01), `action_verdict = ALLOW`, `ALL_APPLICABLE_PASSED`, the dispatch is allowed once after the currentness check, and the claim is consumed.

**A forced early proposal in SC-03A (a different case, not SC-03A).** If the model nevertheless proposes `create_purchase_order` while the state is `POLICY_CHECKED`, governance is consulted [N]: stage `PRE_APPROVAL` gives `PROC-TOOL-STAGE-01` `FAIL` (TS-02) and the `NOT_APPROVED` supplier gives `PROC-SUPPLIER-01` `FAIL` (SU-02), so `BLOCK`, a `tool_suppression` listing both ids, `execution_status = HALTED_POLICY_BLOCK` and `last_app_state = POLICY_CHECKED` (CB-03 and CB-05 combine the same findings).

### 6.2 The realized pair (governance's definition of the evidence)

The distinction Ahmed asked for needs a "realized" counterpart. These two are definitions of what the evidence must show. They are not scheduled scenario recipes; Nour and Ahmed decide whether they become recipes.

| | **Prevented** (SC-03B) | **Realized, policy defect** | **Realized, enforcement bypass** |
|---|---|---|---|
| What happens | The proposal reaches the gate and the gate returns `BLOCK` | The engine or its configuration returns `ALLOW` for a `NOT_APPROVED` supplier, the order is dispatched and confirmed | The gate is not consulted, or its `BLOCK` or a missing verdict is ignored, or the authorization fails the consistency rules (GD-26); the order is dispatched and confirmed |
| Policy result recorded | `FAIL` | `PASS` (wrong) | none, or `FAIL` ignored |
| Re-derived from source under the accepted bundle | `FAIL` (matches) | `FAIL`, which **differs** from the recorded `PASS` (EC-11) | `FAIL` |
| Dispatch evidence | `tool_suppression`, `side_effect_state = NONE`, no consumption record | `tool_call`, `tool_result` `CREATED`, `side_effect_state = COMMITTED`, a `po_id`, a consumption record | the same, with a failing authorization or no check |
| `enforcement_outcome` | `PREVENTED` | `REALIZED` | `REALIZED` |
| Defect | none: the policy worked | **policy configuration or engine** (contract §6.5) | **application enforcement**, not the policy rule |
| Layer 2 | `BLOCK` (`DEC-1`) | `BLOCK` (`DEC-1`), flagged "unsafe action executed" | `BLOCK` (`DEC-1`), flagged; GD-26 for the unverified-authorization case |

A correctly blocked attempt is therefore **never** a policy defect. It is a policy `FAIL` (the agent's attempt breached the rule) with the outcome `PREVENTED` (the system stopped it). The two facts are recorded separately so that successful enforcement is not counted as a failure of the policy.

### 6.3 Corrections to SC-03 examples

1. **My earlier SC-03A wording was wrong.** Revision 0.5 said SC-03A had "no governance result" and that "no pre-tool check runs". Every tool proposal goes through the hook (GD-02), so the read-tool checks do run and return `ALLOW`. What does not happen is a purchase-order check, and `PROC-SUPPLIER-01` is not evaluated against the supplier status. Corrected above.
2. **Ahmed's representative scenario and annotation example EX-08** (`scen_proc_unapproved_sup_06`, `tr_proc_119`) show `get_supplier` returning a non-approved supplier followed by a transition to `APPROVED` and a purchase-order proposal. The real application cannot do that: it stops at `POLICY_CHECKED` (SC-03A). That trajectory is the **SC-03B boundary fixture**, and should be marked `BOUNDARY_TEST`, not presented as a full-application trace.
3. **Supplier status names.** Those examples use `UNAPPROVED` and `SUSPENDED`. The canonical set is `APPROVED`, `NOT_APPROVED` and `UNKNOWN` [N]. The verdict is the same, because every non-`APPROVED` status fails (SU-04), but the example should use `NOT_APPROVED`.
4. **Retired names.** The expected signals use `pre_tool_verdict`, `proc_supplier_01_passed` and `BLOCKED_BY_POLICY`. In v1.9 these are `action_verdict`, `evaluated_policies[].policy_result` and a `tool_suppression` with `execution_status = HALTED_POLICY_BLOCK`.
5. **Stub label.** A result from the contract stub is a rehearsal and is labelled `STUB_CONTRACT_TEST` once SA-07 adds the value; real-policy acceptance needs `ONLINE_PRE_TOOL`.

### 6.4 Boundary-test representation

The request carries an `execution_scope` marker (`FULL_APPLICATION` or `BOUNDARY_TEST`; not in Trace Schema v1.9 yet, SA-08). The policy engine evaluates both identically. The marker is recorded for provenance and dataset admission only and **cannot change a verdict**. The deliberately inconsistent stage and supplier combination is confined to the boundary fixture and is never presented as a reachable application state.

The mapping of these fixtures to an RCA cause is **open**. Nour's SC-03 text says it needs Ahmed and Mohamed's review, that `injected_root_cause` must not be set to `policy_configuration` automatically, and that the scenario is not dataset-ready until an approved mapping exists. Governance's evidence boundary for it is contract §6.5; this document sets no cause.

---

## 7. Layer 2 precedence — conflict cases

Rule ids are from the [decision flow](decision-flow.md) §3. "Not evaluated" means the rule needs a threshold that is not configured.

| Case | Situation | Decision | Rules recorded |
|---|---|---|---|
| DC-01 | Critical policy `FAIL`; every quality signal favorable | `BLOCK` | `DEC-1` |
| DC-02 | Critical security finding; classifier confidence high | `BLOCK` | `DEC-1` |
| DC-03 | Critical policy `FAIL` and thresholds not configured | `BLOCK` | `DEC-1`; `DEC-2` to `DEC-6` not evaluated |
| DC-04 | No critical failure; severe regression and borderline quality | `BLOCK` | `DEC-2`, `DEC-3` |
| DC-05 | No critical failure; borderline quality only | `REVIEW` | `DEC-3` |
| DC-06 | No critical failure; strong evaluator disagreement only | `REVIEW` | `DEC-4` |
| DC-07 | No critical failure; low classifier certainty only | `REVIEW` | `DEC-5` |
| DC-08 | No critical failure; borderline quality and low certainty | `REVIEW` | `DEC-3`, `DEC-5` |
| DC-09 | No critical failure; all metrics within baseline tolerance; evidence complete | `PASS` | `DEC-6` |
| DC-10 | No critical failure; thresholds not configured | no decision, evaluation incomplete | `DEC-2` to `DEC-6` not evaluated |
| DC-11 | No critical failure; a required evaluator failed or its result is missing | no decision, evaluation incomplete | missing evidence listed |
| DC-12 | A critical policy result is `ERROR` (compliance could not be confirmed); nothing else critical | no decision, evaluation incomplete | never treated as compliant |
| DC-13 | Procurement action executed despite a critical policy `FAIL` (`enforcement_outcome = REALIZED`) | `BLOCK` | `DEC-1`, flagged "unsafe action executed" |
| DC-14 | Unsafe action attempted and prevented (`enforcement_outcome = PREVENTED`) | `BLOCK` | `DEC-1` |
| DC-15 | RAG trace; policy evidence `NOT_APPLICABLE` (reason `POLICY_NOT_APPLICABLE_TO_APPLICATION`, one row per procurement policy); quality rules proceed | per `DEC-2` to `DEC-6` | policy `NOT_APPLICABLE` shown as such, never as `PASS`, `ERROR` or `NOT_REQUESTED` |
| DC-16 | Release target: candidate introduces a critical policy failure the baseline prevented | `BLOCK` | `DEC-1` (release scope) |
| DC-17 | Run not terminal (for example `RECOVERY_PENDING` after an unknown purchase-order outcome); no critical failure | no decision, evaluation incomplete | run not terminal listed as missing |
| DC-18 | Purchase order dispatched under an authorization that fails the consistency rules (proposed, GD-26) | `BLOCK` | `DEC-1`, flagged "executed under an unverified authorization" |
| DC-19 | Duplicate terminal results for one invocation; no critical failure | no decision, evaluation incomplete | consistency finding; `enforcement_outcome = UNKNOWN` |
| DC-20 | Unknown purchase-order outcome later resolved by a recovery observation showing the order exists, with a critical policy `FAIL` | `BLOCK` | `DEC-1`; `enforcement_outcome` moves from `UNKNOWN` to `REALIZED` in a new record; the original result is untouched |
| DC-21 | Purchase order dispatched, authoritative definitive failure (`OC-6`), with a critical policy `FAIL` | `BLOCK` | `DEC-1`; `enforcement_outcome = DEFINITIVE_NO_EFFECT`, not `PREVENTED` and not `REALIZED` |
| DC-22 | Recorded policy result `PASS` for a `NOT_APPROVED` supplier, order dispatched and confirmed; re-derivation from source gives `FAIL` (`EC-11`) | `BLOCK` | `DEC-1`, flagged "unsafe action executed"; `enforcement_outcome = REALIZED`; finding `POLICY_RESULT_REDERIVATION_MISMATCH`; the evidence is not certifiable |

Incomplete evaluation never yields `PASS`, and `DEC-1` never waits for a threshold.

---

## 8. Claim-time currentness and Nour's OD-04 paper cases

### 8.1 Currentness at the dispatch claim

The `authorization_snapshot` carries the approval and supplier `record_version`, the `decision_record_seq`, the request revision and the policy-bundle version (contract §4.2). At the atomic consumption the runtime asks the governance currentness comparison whether each is still current. This is not a policy check and returns no `ALLOW` or `BLOCK`; it decides only whether the earlier `ALLOW` may still be consumed.

| Case | Situation at the claim | Result | Effect |
|---|---|---|---|
| CT-01 | Every bound version is still current | `CURRENT` | The runtime may consume the claim |
| CT-02 | The current approval record is now `CANCELLED` (revocation after `ALLOW`, before the claim) | `STALE` — `APPROVAL_NO_LONGER_APPROVED` | Dispatch suppressed (`NOT_EXECUTED`) |
| CT-03 | A newer approval record version exists | `STALE` — `APPROVAL_RECORD_VERSION_CHANGED` | Dispatch suppressed; a fresh check is needed |
| CT-04 | The supplier record version changed since the check | `STALE` — `SUPPLIER_RECORD_VERSION_CHANGED` | Dispatch suppressed |
| CT-05 | The request revision changed | `STALE` — `REQUEST_REVISION_CHANGED` | Dispatch suppressed; the new revision restarts from the beginning |
| CT-06 | The active policy-bundle version changed | `STALE` — `POLICY_VERSION_CHANGED` | Dispatch suppressed |
| CT-07 | A second consumption is attempted for the same root | Refused by the runtime ledger, not by governance | Dispatch suppressed |
| CT-08 | Currentness cannot be established (record unreadable, version missing) | not `CURRENT` — `CURRENTNESS_UNDETERMINED` | Dispatch suppressed (fail closed) |

Specification only: the serialization or fence that makes the comparison and the consumption one atomic step is the runtime's and Mohab's, and no race-safety claim is made here.

### 8.2 Nour's 27 approval-validity cases mapped to governance results

Nour's [OD04-C01 to C27](https://github.com/trustops-dev/trustops-ai/blob/479cab00c021db7a58b826b46a653c3e2308b798/docs/architecture/reference-applications/approval-validity/od04-v0.1/README.md) are paper-review cases for the application. This table gives the governance result for each. "Not governance" marks a case that the application or runtime decides and governance only observes.

| Case | Situation | Governance result |
|---|---|---|
| C01 | Unchanged request, approval still pending | AP-04 `FAIL`; the application waits |
| C02, C03 | Unchanged, approved; or an old approval under the explicit no-expiry rule | AP-10 `PASS` (age is irrelevant); a fresh proposal gets a fresh check |
| C04 | Validity configuration absent | AP-18 `ERROR`; blocks |
| C05, C06, C07 | Amount, supplier, item, quantity or currency revised; or a new revision with the same amount | AP-07 `FAIL`; CT-05 at the claim |
| C08 | Business request cancelled before a late approval | The approval service refuses an `APPROVED` after a terminal `CANCELLED` (§5.3 V04); AP-06 |
| C09, C10 | Approval denied; approval cancelled | AP-05; AP-06 (terminal) |
| C11 | Revocation before the purchase-order proposal | AP-06 at the proposal's check |
| C12 | Revocation after `ALLOW`, before the dispatch boundary | CT-02 |
| C13 | Revocation after an uncertain dispatch | No effect on the recorded authorization (V08); the outcome stays `UNKNOWN`; a `CANCELLED` record is appended; recovery stays read-only |
| C14 | Approval after an earlier blocked proposal | The earlier proposal stays blocked (AP-09 for it); a new proposal made after the approval gets a fresh check, AP-10 |
| C15 | Approval after an unauthorized action was already dispatched | Post-run AP-09 `FAIL`, `enforcement_outcome` `REALIZED` (or `UNKNOWN`), `DEC-1` |
| C16 | A model or user claims approval | No record: AP-03 `FAIL`; a status in the request is kept only for mismatch diagnostics |
| C17 | Record absent or wrong identity | AP-03, or `EVIDENCE_UNRESOLVED` (`ERROR`) when the reference does not resolve |
| C18 | The approval observation technically fails | `EVIDENCE_UNRESOLVED`; blocks; no authorization is inferred |
| C19 | Future or unorderable decision | AP-16 `ERROR` |
| C20 | A continuation loses its durable binding or budget state | Not governance: the runtime halts (V07); no proposal reaches governance |
| C21 | A duplicate continuation after an existing dispatch claim | CT-07; not governance |
| C22 | Supplier or policy becomes invalid after approval | CT-04, CT-06 |
| C23 | The authoritative calculation says approval is not required | AP-01 or AP-02 `NOT_APPLICABLE`, basis `NOT_REQUIRED`; no approval record is manufactured |
| C24 | Conflicting approval-source records | AP-15 `FAIL` plus the EC-03 finding |
| C25 | Grant with the wrong level or an ineligible approver | AP-08 for the level; AP-19 for the approver |
| C26 | Revocation after confirmed completion | A `CANCELLED` record is appended; history and the authorization are unchanged (V08) |
| C27 | Revised request while the old purchase-order outcome is unknown | The new revision's approval and checks are independent; the runtime guard blocks a second purchase order (CT-07); not governance |
