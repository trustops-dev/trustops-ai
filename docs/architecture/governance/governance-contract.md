# Governance contract register

| | |
|---|---|
| **Status** | DRAFT v0.6 — Sprint 1 closeout (S1-04). Owner decisions recorded; not frozen. No teammate has acknowledged this document yet (see the [review record](README.md#owner-review-record)). |
| **Owner** | Mohamed Elnaggar — `packages/governance-engine` |
| **Reviewers** | Nour El-Rouby, Mohab Mohsen, Ahmed Ragab, Alaa Sayed, Malak Sayed |
| **Companions** | [decision-flow.md](decision-flow.md) · [policy-truth-tables.md](policy-truth-tables.md) · [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) · [response-to-owner-packet-0.14.md](response-to-owner-packet-0.14.md) · [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md) · [policy configuration](policy-configuration/procurement-policy-set-v0.1.yaml) · [owner-review-packet.md](owner-review-packet.md) |
| **Responds to** | The Mohamed section of the [S1-01 handoff checklist](../reference-applications/handoffs.md#mohamed--s1-04-policy-interaction-and-approval-authority) (§9.1), the questions addressed to Mohamed in the [dashboard owner review packet](../dashboard/owner-review-packet.md#mohamed-policy-decisions-review-audit-and-roles) (§9.2, §9.3), review items 1 and 2 of the Trace Schema Draft v1.5 review (§9.4), and Nour's owner packet 0.14 at commit `479cab0` (§9.5) |

Source tags: **[P]** approved proposal · **[R]** repository architecture or sprint plan · **[N]** Nour's [reference-application contracts](../reference-applications/README.md) rev 0.5 · **[T]** Mohab's [Trace Schema v1 draft](../schemas) · **[X]** Malak's [dashboard UX architecture](../dashboard/README.md) rev 0.4 · **[D]** governance decision or proposal.

Statuses used in §8:

- **DECIDED** — owner decision by Mohamed, recorded 2026-10-21. It governs the governance package. Where another owner is affected, that owner's acknowledgement is requested and named; until then it is not an agreed team contract.
- **PROPOSED** — needs the named owner's agreement before it binds.
- **OPEN** — waiting on an input from another owner; nothing is assumed.

Evidence ids (E01–E27) refer to the [evidence matrix](../reference-applications/trace-evidence-contract.md). Decision ids `GD-nn` are governance decisions (§8); where one matches the shared [open-decisions register](../reference-applications/open-decisions.md) the OD id is given. This document does not edit that register.

All field names, enum names and ids are drafts. They become Pydantic models in `packages/contracts` only after review (GD-10). Placeholders in angle brackets are filled by versioned configuration; no threshold, currency or approval level is invented here.

---

## 1. Scope

In scope for Sprint 1 [R, S1-04]: policy evidence requirements, the pre-tool request/response contract, the governance-owned approval boundary, the decision-engine input/output contract, the review/audit/RBAC contract, the policy truth tables, and the decisions that block Sprint 2.

Out of scope until later sprints: policy code, database tables, API endpoints (Sprint 2), decision-engine code (Sprint 4), review/audit/RBAC code (Sprint 6).

---

## 2. Stages, applicability and evidence

### 2.1 Workflow stage and tool allowlist

The application keeps a fine-grained agent **state**; governance sees a coarse **workflow stage**. Tool permission is the intersection of application state and the governance stage policy, and a coarse stage allowance never permits skipping a prerequisite [N]. The application owns the state machine; governance owns the allowlist below.

**DECIDED (GD-02):** policy keys only on the four-value `policy_stage` below. The finer state names — Nour's states and the longer lists in Trace Schema v1 — are not governance inputs; Mohab and Nour reconcile those (§4.5).

| Stage | Tool proposals permitted | Note |
|---|---|---|
| `PRE_APPROVAL` | `search_policy`, `get_supplier`, `request_approval` [P §R]; `calculate_approval_level` (GD-01) | The proposal lists the first three. Adding the read-only calculation tool is a documented extension of that list (GD-01). The application additionally restricts the calculation tool to the fine state `SUPPLIER_CHECKED` with its prerequisites; governance's coarse allowlist is the independent backstop and does not see the fine state |
| `APPROVED` | `create_purchase_order` | The proposal is checked here; dispatch happens after a bound `ALLOW` [N] |
| `PO_CREATION` | none | No new proposal; dispatch proceeds under the existing `ALLOW` binding |
| `COMPLETED` | none | Terminal |

The allowlist lives in versioned configuration (`policies/procurement.yaml`), not in code. The configuration proposed for the synthetic MVP is [policy-configuration/procurement-policy-set-v0.1.yaml](policy-configuration/procurement-policy-set-v0.1.yaml).

### 2.2 Which policies apply to which proposal

| Proposed tool | `PROC-TOOL-STAGE-01` | `PROC-APPROVAL-01` | `PROC-SUPPLIER-01` |
|---|---|---|---|
| `search_policy` | applies | not applicable | not applicable |
| `get_supplier` | applies | not applicable | not applicable |
| `calculate_approval_level` | applies | not applicable | not applicable |
| `request_approval` | applies | not applicable | not applicable |
| `create_purchase_order` | applies | applies only when approval is required, otherwise `NOT_APPLICABLE` | applies |

Basis: `PROC-APPROVAL-01` and `PROC-SUPPLIER-01` are scoped to `create_purchase_order` [P §R, §R.1 `before_tool`]; every proposed tool is checked against the stage allowlist so early or model-generated proposals are caught at any stage [N]. **DECIDED (GD-02):** every tool proposal goes through the same pre-tool hook.

### 2.3 Evidence and result states per policy

The case-by-case truth tables, with draft reason codes, are in [policy-truth-tables.md](policy-truth-tables.md). This section states the rules they implement.

Result states are `PASS`, `FAIL`, `NOT_APPLICABLE` and `ERROR`. The proposal's example traces show only `PASS` and `FAIL` [P §J]; the other two are [D]. `ERROR` represents "could not decide" without pretending it is a violation or a success (`INV-3`).

**`PROC-APPROVAL-01`** — rule: if the purchase amount exceeds the configured threshold, manager-approval evidence must exist before `create_purchase_order` [P §R].

| Aspect | Contract |
|---|---|
| Applies when | The proposal is `create_purchase_order` **and** governance derives that approval is required: `total_amount` strictly greater than the configured threshold in the same `currency` (the proposal says "exceeds", `amount_gt` [P §R.1]; equality does not trigger) |
| `PASS` | A valid approval exists (§5.3) |
| `FAIL` | Approval required and none valid: missing, pending, denied, cancelled, bound to a different request revision / amount / currency / supplier / level, or decided after the proposal |
| `NOT_APPLICABLE` | Approval not required. Recorded with the calculation evidence and the basis `NOT_REQUIRED`; no approval id is invented [N] |
| `ERROR` | `total_amount` or `currency` unparseable or unsupported, or threshold configuration missing |
| Evidence | `total_amount`, `currency`, request revision, configured threshold + currency + comparator + policy version, authoritative approval evidence, event order |

**`PROC-TOOL-STAGE-01`** — rule: `PRE_APPROVAL` allows `search_policy`, `get_supplier`, `request_approval` and forbids `create_purchase_order` [P §R].

| Aspect | Contract |
|---|---|
| `PASS` | The proposed tool is on the allowlist of the current stage |
| `FAIL` | It is not (including a purchase-order proposal outside `APPROVED`, or a tool name not on that stage's list) |
| `ERROR` | The stage is unknown or missing, or the allowlist configuration is missing |
| Evidence | Current stage, proposed tool, configured allowlist + version, trace/proposal identity; the response names the stage, tool and violated rule rather than an unexplained boolean [P §R] |

**`PROC-SUPPLIER-01`** — rule: `create_purchase_order` requires `supplier.status = APPROVED` [P §R].

| Aspect | Contract |
|---|---|
| Applies when | The proposal is `create_purchase_order` |
| `PASS` | The supplier snapshot for the **same** `supplier_id` as the proposal has status exactly `APPROVED` |
| `FAIL` | Any other non-null status, the supplier was not found, or the snapshot's supplier id differs from the proposal's |
| `NOT_APPLICABLE` | The proposal is not `create_purchase_order` |
| `ERROR` | No supplier evidence, a lookup error, or a null status (this is not a verdict on the supplier) |
| Evidence | `supplier_id`, `status`, `record_version`, `directory_version`, source, proposed tool, policy version |

Governance needs only the literal `APPROVED`. The full status set is the application's (§4.5); any non-null value other than `APPROVED` fails, so the policy does not depend on which drafts' spelling wins.

### 2.4 Trust boundary for evidence

A governance check is only as independent as its evidence. Where Nour's contracts and this contract agree, the rule is stated once:

1. **Evidence comes from runtime code, never from model text.** The model cannot set approval or supplier status, state, check verdict, idempotency key or tool result; the runtime injects trusted context separately from model arguments [N, state invariant 3]. This keeps Layer 1 independent of prompt injection [P §Q].
2. **Approval authority is governance-owned.** `request_approval` goes through the governance-owned approval boundary [N]; the check resolves approval status from governance's own approval records (§5), not from a status string in the request. A status the application reports is kept only to record a mismatch.
3. **Governance derives the approval requirement.** It does not trust the application's `approval_required` flag (`INV-10`). The app's `calculate_approval_level` tool delegates to the same governance function (§5.1), so the two cannot disagree [N].
4. **The amount that is checked is the amount of the call being proposed**, compared with the request total and the approval evidence. A disagreement between the proposal, the request snapshot, the supplier snapshot and the approval evidence on revision, amount, currency or supplier is a check-level `CONTEXT_MISMATCH` and fails closed.
5. **Policy version.** [N] has the application supply the policy-bundle version. **DECIDED (GD-08):** governance evaluates against its **active** version and fails closed on any difference, so an agent can never select a weaker policy set.
6. **Amounts are exact decimals** (decimal strings plus a currency), never binary floats, so equality with the threshold is decided exactly [N]. Trace Schema v1 currently shows numbers (§4.5).
7. **Copied values are claims, referenced records are evidence.** A supplier status, approval status or amount copied into a request, binding or snapshot never establishes agreement by itself; it is compared with the record it references, and the record wins (§4.6, `INV-11`).

---

## 3. Traceability register

Every input and output has a producer and a consumer — the S1-04 traceability check [R]. "Trust" says how a value must be sourced: **runtime** = deterministic application code, **governance** = authoritative inside governance, **platform** = trace platform, **evaluator** = produced by the reliability engine, **human**.

### 3.1 Layer 1 policy inputs

| Id | Input | Evidence | Producer | Consumer | Trust |
|---|---|---|---|---|---|
| PI-01 | `proposed_tool` | E15 | Nour — tool hook | all three policies | runtime |
| PI-02 | parsed tool arguments (supplier, item, quantity, `total_amount`, `currency`) | E16 | Nour | `PROC-APPROVAL-01`, `PROC-SUPPLIER-01` | runtime |
| PI-03 | `arguments_digest` | E17 | Nour | binding (§4.2) | runtime |
| PI-04 | `policy_stage` | E10 | Nour — state machine | `PROC-TOOL-STAGE-01` | runtime |
| PI-05 | `request_id`, `request_revision`, request `total_amount` / `currency` | E08 | Nour | consistency check, binding | runtime |
| PI-06 | source state revision | E09 | Nour | binding | runtime |
| PI-07 | calculation reference and app-reported `approval_required` | E12 | Nour | diagnostics and mismatch only | runtime, non-authoritative |
| PI-08 | approval-request id / approval id | E13, E14 | Nour (from `request_approval`) | `PROC-APPROVAL-01` → approval service lookup | runtime reference |
| PI-09 | authoritative approval evidence | E14 | governance — `approvals/approval_service.py` | `PROC-APPROVAL-01` | governance |
| PI-10 | supplier snapshot: id, status, record + directory version | E11 | Nour (`get_supplier` result) | `PROC-SUPPLIER-01` | runtime |
| PI-11 | event sequence / ordering | E09, E15 | Mohab — SDK | `PROC-APPROVAL-01` ("approval before the proposal") | platform |
| PI-12 | `trace_id`, `proposal_id`, `attempt_id` (one id per attempt of the same logical operation; a retry has a new `attempt_id`) | E15, E17 | Mohab / Nour | all policies, idempotency (a replay of the same attempt returns the original check; a new attempt needs a fresh check), audit | platform |
| PI-13 | policy-bundle version reported by the application (`authorization_snapshot.policy_bundle_version`) | E17 | Nour | compared with the active version (GD-08) | runtime |
| PI-14 | configured threshold + currency + comparator + approval level (versioned) | — | governance — `policies/procurement.yaml` | `PROC-APPROVAL-01`, §5.1 | governance |
| PI-15 | stage → tool allowlist (versioned) | — | governance — `policies/procurement.yaml` | `PROC-TOOL-STAGE-01` | governance |
| PI-16 | eligible supplier status (versioned) | — | governance — `policies/procurement.yaml` | `PROC-SUPPLIER-01` | governance |
| PI-17 | approval validity rule (versioned) | — | governance — `policies/procurement.yaml` | `PROC-APPROVAL-01` (GD-04) | governance |
| PI-18 | active `policy_bundle_version` | — | governance | all policies, every output | governance |
| PI-19 | `execution_scope` (`FULL_APPLICATION` / `BOUNDARY_TEST`) | E27 | Nour | recorded only; never affects a verdict (GD-23) | runtime |
| PI-20 | `idempotency_key` (issued by the runtime, never by governance or the model) | E20 | Nour | binding, dispatch claim, recovery identity (§4.7) | runtime |
| PI-22 | `dispatch_claim_id`: root-scoped identity `dclaim_<root_request_id>`, preallocated by the runtime **before** the check; allocating it consumes nothing | E20 | Nour | `authorization_snapshot.dispatch_claim`, then equality across the consumption record, the transition and the invocation (§4.7, GD-28) | runtime |
| PI-23 | `record_version` and `decision_record_seq` of the approval record; `record_version` of the supplier record; each append-only | E11, E14 | governance (approval), Nour (supplier directory) | `authorization_snapshot`; compared with the current versions at the consumption of the claim (§5.3, GD-30) | governance / runtime |
| PI-21 | Evidence references: normalized request, supplier result, calculation result, approval event, proposal, state snapshot | E08 to E15 | Nour / Mohab | platform adapter resolves them; governance compares them with the claimed copies (§4.6) | platform |

PI-02, PI-05, PI-07, PI-08 and PI-10 are **claims**. Their source of truth is the record each one references (PI-21). A claim that differs from its source is a finding and the source value is used (`INV-11`).

### 3.2 Layer 1 outputs

| Id | Output | Evidence | Producer | Consumer |
|---|---|---|---|---|
| PO-01 | `verdict` — `ALLOW` / `BLOCK` | E18 | governance | Nour (obeys), Mohab (persists), audit |
| PO-02 | `verdict_basis` — all satisfied / policy violation / evaluation error | E18 | governance | Nour (logging), Malak (display), audit |
| PO-03 | per-policy result: id, version, status, criticality, reason code, message, evidence refs | E18 | governance | Mohab (persist), Malak (Trace Detail), Ahmed (policy evaluator and features), Alaa (gate), Layer 2 |
| PO-04 | `policy_bundle_version`, per-policy versions | E18 | governance | Mohab, Ahmed, Alaa (provenance) |
| PO-05 | `check_id`, `evaluated_at` | E18 | governance | Mohab (trace linkage), audit |
| PO-06 | `authorization_snapshot` (§4.2) | E17, E18, E20 | governance | Nour (verify and claim), Mohab (linkage) |
| PO-07 | `check_mode` — real engine or contract stub | E18 | governance | Malak (`TRD-43`), Alaa, Mohab |

PO-03 is what feeds the proposal's policy feature group — policy failure count, critical-policy flag, tool-stage allowlist verdict, supplier eligibility [P §L.2] — so Ahmed's feature pipeline consumes it unchanged.

### 3.3 Layer 2 decision inputs

| Id | Input | Producer | Consumer | Note |
|---|---|---|---|---|
| DI-01 | policy findings (Layer 1 records, plus post-run policy evaluation with `enforcement_outcome`); `NOT_APPLICABLE` for non-procurement traces | governance | decision engine | |
| DI-02 | security findings: verdict, score, category, criticality | Ahmed — security evaluator | decision engine | which findings are critical → GD-12 |
| DI-03 | evaluator results with evaluator versions | Ahmed | decision engine | metric names → GD-12 |
| DI-04 | evaluator-disagreement indicator | Ahmed | decision engine (`DEC-4`) | definition → GD-12 |
| DI-05 | failure label, classifier confidence, classifier version | Ahmed | decision engine (`DEC-5`) | |
| DI-06 | Top-1 / Top-3 RCA with evidence scores | Ahmed | decision record (informational, linked) | never overrides `DEC-1` |
| DI-07 | baseline-vs-candidate comparison and critical cases | Alaa — regression runner | decision engine, release target only | |
| DI-08 | decision configuration and its version | governance — `config/decision_thresholds.yaml` | decision engine | values from measured baselines (OD-15) |
| DI-09 | target type and id, evidence-run ids | Mohab — orchestration | decision engine, decision record | |

### 3.4 Layer 2 outputs

| Id | Output | Producer | Consumer |
|---|---|---|---|
| DO-01 | `decision` — `PASS` / `REVIEW` / `BLOCK` (absent when evaluation is incomplete — GD-13) | governance | Malak, Alaa (gate artifact), review, audit |
| DO-02 | `evaluation_status` and the list of missing evidence | governance | Malak ("not evaluated" / "evaluator failed" / "not applicable" kept distinct from `PASS` [N]), Alaa |
| DO-03 | ordered list of fired rules (`DEC-n`) with reason codes | governance | Malak (Failure & RCA screen), reports |
| DO-04 | rules **not evaluated** and why (for example "threshold not configured") | governance | Malak (`RCA-08`), Alaa |
| DO-05 | evidence references and evidence-run ids; a reference identifies one event as `trace_id` + `event_id` | governance | Malak, audit, reproducibility |
| DO-06 | `decision_config_version` and `decision_engine_version` | governance | Alaa, Ahmed (provenance), Malak (`RCA-07`) |
| DO-07 | `decision_id`, target, `created_at` | governance | Mohab (persist), review (reference), audit |

---

## 4. Pre-tool check — draft interface

Models will live in `packages/contracts/.../governance.py` (GD-10). The service is `trustops_governance.policy.engine`. The HTTP adapter in `apps/api` serves `POST /api/v1/policy/check`, the route Trace Schema v1 already names [T] (GD-05). There is no governance microservice. Governance does not import application code or reliability implementation classes [R].

### 4.1 Check input [D]

A pre-tool check evaluates one immutable proposal snapshot. Field names are **Trace Schema v1.9 paths** [T]; governance keeps no parallel names (GD-31). Paths are relative to the `policy_check` event unless stated.

| Governance concept | Trace Schema v1.9 path | Notes |
|---|---|---|
| Proposal and attempt | `tool_proposal.attributes.proposal_id`; `trusted_runtime_context.budget_context.attempt_id` | The same attempt replayed returns the original check. A retry of a read-only tool is a new attempt with a fresh, separately bound check (GD-29) |
| Root and revision | `authorization_snapshot.root_request_id`, `request_revision` | From the immutable request snapshot |
| State and stage | `checked_source_state_revision`, `checked_app_state`, `checked_policy_stage` | Governance reads only the coarse `policy_stage`: `PRE_APPROVAL`, `APPROVED`, `PO_CREATION`, `COMPLETED` (GD-02) |
| Tool and mode | `tool_name`, `operation_mode` | An `ALLOW` authorizes only this tool in this mode |
| Arguments | `validated_arguments`, `arguments_digest` | `total_amount` is a decimal string. Digest per `trustops-canonical-json-v1` (OD-13) |
| Supplier | `supplier_evidence_ref` (`supplier_check_result_id`, `supplier_id`, `supplier_status`, `directory_version`, `supplier_record_version`, `latest_observed_supplier_record_version`, `is_current_at_check`) | A **claim** checked against the referenced `get_supplier` result (§4.6) |
| Calculation | `calculation_evidence_ref` (`calculation_result_id`, `calculation_ref`, `approval_required`, `approval_level`, `basis`) | A claim; governance recomputes the requirement itself (`INV-10`) |
| Approval | `approval_evidence_ref` (`approval_event_id`, `approval_request_id`, `decision_status`, `approval_record_version`, `decision_record_seq`, `latest_observed_*`, `is_current_at_check`) | A claim checked against the `approval` event and governance's own record |
| Policy identity | `policy_bundle_version`, `policy_version`, `policy_id_resolution_status` | `policy_bundle_version` is the executable rule bundle; `policy_version` is the policy-corpus release (§4.5 row 6) |
| Dispatch claim | `authorization_snapshot.dispatch_claim` | §4.7 |
| Evidence references | the event ids above | Resolved by a platform adapter (§4.6) |
| Execution scope | not in v1.9 | `FULL_APPLICATION` or `BOUNDARY_TEST`, recorded only and never changing a verdict (GD-23). Proposed placement `scenario_metadata.execution_scope`; open item for Mohab (§4.5 row 16) |

Deliberately **not** accepted as authority: any approval status string, any verdict, any choice of policy version, and any copied value that differs from the record it references.

### 4.2 Check output [D]

| Governance concept | Trace Schema v1.9 path | Notes |
|---|---|---|
| Pre-tool verdict | `policy_check.attributes.action_verdict` | `ALLOW` or `BLOCK` |
| Verdict basis | `verdict_basis` | `ALL_APPLICABLE_PASSED`, `MANDATORY_POLICY_FAILED` or `FAIL_CLOSED_ON_POLICY_ERROR` |
| Per-policy results | `evaluated_policies[]` (`policy_id`, `policy_version`, `policy_result`, `criticality`, `binding_verification`, `observed_evidence`, `failure_or_error_reason`) | `policy_result` is `PASS`, `FAIL`, `NOT_APPLICABLE` or `ERROR`. All three mandatory policy ids are recorded on every procurement check |
| Check identity and mode | `check_id`, `check_mode` | `ONLINE_PRE_TOOL` for the real engine. The stub label is missing in v1.9 (§4.5 row 15) |
| Rule bundle | `policy_bundle_version` | The version that actually ran |
| Authorization snapshot | `authorization_snapshot` (19 keys) | Governance's "binding": the immutable record of what was checked |
| Verification | `runtime_binding_verification` (`common_binding_verified`, `po_dispatch_binding_verified`) | Verified by comparison with the source evidence (§4.6), never trusted from the boolean alone |
| No verdict | `tool_suppression` event with `suppression_source = POLICY_CHECK_ERROR_OR_TIMEOUT` | Timeout, exception or unreachable governance: nothing is dispatched and no policy result is invented |

Only a policy whose `criticality` is critical drives `DEC-1`; the spelling question is §4.5 row 5. All three MVP policies are critical.

**Meaning of `ALLOW`** [N, authorization binding]: it authorizes the single `APPROVED → PO_CREATION` transition and the initial dispatch for exactly the checked snapshot. The runtime atomically verifies that the current snapshot still equals the `authorization_snapshot` (including that the approval and supplier `record_version`, the request revision and the policy-bundle version are still the bound ones), records the authorized transition and consumes the preallocated `dispatch_claim_id` once. Any other change to the bound inputs, any intervening transition, or a second use of the same authorization needs a fresh check. A model cannot invoke this path. Governance's part is the snapshot fields, the currentness rule (§5.3) and idempotent replay; the atomic consumption is the runtime's (GD-07, GD-28, GD-30).

### 4.3 Illustrative case: approval bypass

Values are illustrative. The complete event, with every field of the 19-key snapshot, is walkthrough 2 of Trace Schema v1.9; this shows only the governance result.

```json
{
  "check_mode": "ONLINE_PRE_TOOL",
  "policy_bundle_version": "<active bundle>",
  "evaluated_policies": [
    { "policy_id": "PROC-APPROVAL-01", "policy_result": "FAIL", "criticality": "critical",
      "failure_or_error_reason": "APPROVAL_MISSING",
      "observed_evidence": { "total_amount": "32000.00", "expected": "valid approval when amount > <configured threshold> <currency>" } },
    { "policy_id": "PROC-TOOL-STAGE-01", "policy_result": "FAIL", "criticality": "critical",
      "failure_or_error_reason": "TOOL_NOT_ALLOWED_IN_STAGE",
      "observed_evidence": { "proposed_tool": "create_purchase_order", "checked_policy_stage": "PRE_APPROVAL" } },
    { "policy_id": "PROC-SUPPLIER-01", "policy_result": "PASS", "criticality": "critical",
      "failure_or_error_reason": null,
      "observed_evidence": { "supplier_status": "APPROVED" } }
  ],
  "action_verdict": "BLOCK",
  "verdict_basis": "MANDATORY_POLICY_FAILED"
}
```

### 4.4 Outcomes

The complete case list (every approval, stage and supplier case, the aggregation rules, the combined and conflicting cases, and the SC-03 fixture pair) is in [policy-truth-tables.md](policy-truth-tables.md) §2 to §6.

### 4.5 Naming and translation (Trace Schema v1.9)

Trace Schema v1.9 (Mohab, §4.4.3 and §9.4) is the naming source for every field governance shares with the trace. This table confirms the translation of each governance concept and records where governance asks for an amendment. Earlier governance names (rev 0.5 and before) are shown only so that readers of those drafts can find the new name.

| # | Governance concept (earlier name) | Trace Schema v1.9 | Disposition |
|---|---|---|---|
| 1 | Pre-tool verdict (`verdict`) | `action_verdict`: `ALLOW`, `BLOCK` | **Confirmed**, 1:1 |
| 2 | Verdict basis | `verdict_basis`: `ALL_APPLICABLE_PASSED` (was `ALL_POLICIES_SATISFIED`), `MANDATORY_POLICY_FAILED` (was `POLICY_VIOLATION`), `FAIL_CLOSED_ON_POLICY_ERROR` (was `EVALUATION_ERROR`). The caller-written `NO_VERDICT` is retired | **Confirmed.** A missing verdict is a `tool_suppression` with `suppression_source = POLICY_CHECK_ERROR_OR_TIMEOUT` |
| 3 | Per-policy result (`results[].status`) | `evaluated_policies[].policy_result`: `PASS`, `FAIL`, `NOT_APPLICABLE`, `ERROR` | **Confirmed**, 1:1. The `passed` boolean and `pre_tool_verdict` are retired in v1.9 |
| 4 | Reason and evidence (`reason_code`, `evidence`) | `failure_or_error_reason`, `observed_evidence` | **Confirmed.** `failure_or_error_reason` carries the governance reason code from [policy-truth-tables.md](policy-truth-tables.md) |
| 5 | Criticality (`critical`, `high`, `medium`) | The v1.9 text lists `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`; the v1.9 fixtures use lowercase `critical` | **AMEND (Mohab):** use one spelling in the schema. Governance accepts either and matches case-insensitively. Governance uses only critical for the three MVP policies |
| 6 | Policy version (`policy_set_version`) | `policy_bundle_version` is the executable rule bundle (MVP value `synthetic-procurement-policy-set-v0.1`). `policy_kb_version`, `authorization_snapshot.policy_version` and `search_policy.data.policy_set_version` are the policy-corpus release. `doc_version` is a single document's revision | **Confirmed with a clarification.** `evaluated_policies[].policy_version` carries the corpus release, so per-policy rule versions (for example `synthetic-procurement-approval-v0.1`) are not separate trace fields: they are inside the bundle and recoverable from its content hash. The pairing of bundle and corpus release is assigned at integration (Nour, OD-03 candidate README); a corpus release not paired with the active bundle is `POLICY_VERSION_MISMATCH` |
| 7 | Stage (`workflow_stage`) | `policy_stage`, `policy_stage_at_proposal`, `checked_policy_stage`, `policy_stage_at_dispatch`: `PRE_APPROVAL`, `APPROVED`, `PO_CREATION`, `COMPLETED` | **Confirmed.** `PO_CREATED` is never a stage. `POST_EXECUTION` (accepted by v1.9 as a post-run alias of `COMPLETED`) is normalized by the platform; the policy engine accepts only the four values. Policy stage is not the policy-check result (§4.8) |
| 8 | Approval record status | v1.9 `approval_status`: `PENDING`, `APPROVED`, `DENIED`, `CANCELLED`, `EXPIRED`, `STALE_REVISION` | **AMEND (Mohab).** Governance records four: `PENDING`, `APPROVED`, `DENIED`, `CANCELLED` (§5.3). `EXPIRED` is never produced (no time expiry in the MVP). `STALE_REVISION` is a derived currentness result, not a record status, and belongs in the currentness fields |
| 9 | Record identity and order | `record_version`, `decision_record_seq` (approval); `record_version`, `directory_version` (supplier) | **Confirmed.** Each authority orders its own records; the two sequences are never compared with each other |
| 10 | Authorization binding (`binding`) | `authorization_snapshot` (19 keys) with `dispatch_claim` | **Confirmed.** `idempotency_key` and `attempt_id` live in `trusted_runtime_context` |
| 11 | Dispatch claim and its consumption | `dispatch_claim_id` (`dclaim_<root_request_id>`), `dispatch_claim`, `dispatch_claim_consumption` (`consumption_record_id`) | **Confirmed with two amendments** (§4.7): `claim_status_at_check` must not imply consumption, and the consumption record must record currentness at consumption |
| 12 | Digest | `arguments_digest` over `normalized_arguments`; `business_payload_sha256` over `request.structured_input`; both `trustops-canonical-json-v1` | **Confirmed.** For `create_purchase_order` the digest inputs are `currency`, `item_description`, `quantity`, `request_id`, `supplier_id`, `total_amount`; the request revision is bound separately by `authorization_snapshot.request_revision` and is not a digest input. Canonical JSON choice is OD-13 (Alaa, Mohab) |
| 13 | Effect and recovery states | `tool_result.side_effect_state`: `NONE`, `COMMITTED`, `ALREADY_EXISTING`, `UNKNOWN`. `recovery_check.reconciliation_status`: `RESOLVED_COMMITTED`, `RESOLVED_ABORTED`, `STILL_UNRESOLVED`, with `resolved_side_effect_state`. Budget checkpoint `effect_state`: `NOT_APPLICABLE`, `NONE_CONFIRMED`, `COMMITTED_CONFIRMED`, `UNKNOWN` | **Confirmed.** `ALREADY_EXISTING` maps to checkpoint `COMMITTED_CONFIRMED`; the trace keeps `ALREADY_EXISTING` and `original_result_ref` so replay stays distinguishable. A dispatched timeout is `UNKNOWN`, never `NONE` |
| 14 | Blocked call | `tool_suppression` (`suppression_source`, `blocking_check_id`, `blocking_policy_ids`, `execution_started = false`, `side_effect_state = NONE`); no `tool_call` or `tool_result` | **Confirmed.** `BLOCKED_BY_POLICY` as a `tool_result` status is retired |
| 15 | Check mode | `check_mode`: `ONLINE_PRE_TOOL` | **PENDING (Mohab).** The stub label `STUB_CONTRACT_TEST` (GD-06) is not in the v1.9 text; add it, or governance states the stub condition another way |
| 16 | Execution scope (GD-23) | not in v1.9 | **PENDING (Mohab).** Proposed `scenario_metadata.execution_scope` |
| 17 | Verified flag | `trusted_source_verified` on evidence refs; `runtime_binding_verification` | **Confirmed.** Derived output only, never evidence (`INV-12`) |
| 18 | Enforcement outcome (`enforcement_outcome`) | not a v1.9 field | **PENDING (Ahmed, Alaa, Mohab).** Governance derives it from `side_effect_state` plus the presence of a `tool_suppression` (§6.3); where the derived value is stored in post-run analysis is a joint decision |
| 19 | Finding codes | the `ERR_*` codes of the v1.9 validator | **Confirmed.** Governance adopts the validator codes; the table in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §7 lists the few governance checks with no dedicated code |

v1.9 no longer carries `reviewer_role` or `post_run_policy_verdict`. Review records, audit records and roles are governance records (§7), not trace fields, and the post-run policy aggregate is a view derived from `evaluated_policies[]`.

Not governance-owned, left to others: run status versus `execution_status`, and abstention reasons (Nour, Mohab, Ahmed).

### 4.6 Evidence resolution and consistency

[D] An authorization snapshot must be checked against its actual source evidence, not against copied fields. The full rules, finding codes and acceptance cases are in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §2 to §5. In summary:

| Principle | Contract |
|---|---|
| Copies are claims | The `authorization_snapshot` and its evidence refs copy values; the referenced records are the evidence (`INV-11`) |
| Source governs | Policy results are computed from the resolved source records; a differing copy is a finding and never changes the result |
| Resolution | A platform adapter resolves each reference to exactly one record of the expected kind, behind a port governance defines; an unresolved, ambiguous or duplicated reference is a finding |
| Comparison | Governance compares claims with the resolved records for supplier, calculation, approval, request-to-arguments agreement, mandatory policy identities, snapshot fields, policy version and the dispatch claim |
| Certification | Any finding makes the check ineligible for `ALLOW` and the authorization ineligible to be called verified (`INV-12`); a failing trace with consistent evidence is still captured as a failure fixture |
| Flags | `trusted_source_verified` and `runtime_binding_verification` are derived and never accepted as evidence |

Proposed additions to the governance package, outside the approved repository tree and so needing Mohab's agreement (GD-24): `ports/evidence_resolver.py` (the resolver port) and `policy/evidence_consistency.py` (the pure comparison functions).

### 4.7 Dispatch claim, consumption and recovery

[D] The lifecycle below is the one in Trace Schema v1.9 §4.4.3 items 3 and 5 [T], accepted by governance with two amendments (SA-01 and SA-02 in the [follow-up response](response-to-owner-packet-9e6affa.md)). It replaces the v0.5 wording "one claim identity per proposal attempt".

| Step | Trace Schema v1.9 representation | Governance rule |
|---|---|---|
| 1 Preallocation | `tool_proposal.trusted_runtime_context.domain_context.dispatch_claim_id`, value `dclaim_<root_request_id>` | The claim identity is **root-scoped**: one per root business request, so root-wide uniqueness holds by construction. Issued by the runtime, never by the model or by governance. Allocating consumes and debits nothing |
| 2 Check | `authorization_snapshot.dispatch_claim` (`dispatch_claim_id`, `claim_scope`, `claim_status_at_check`, `bound_supplier_record_version`, `bound_approval_record_version`, `currentness_verified`) | The check reads whether the claim is unconsumed and binds the record versions; it **never consumes**. **SA-01 (AMEND):** the value `AVAILABLE_CLAIMED_ON_ALLOW` reads as if the claim were taken at the check; rename it `AVAILABLE_AT_CHECK` (`NOT_CLAIMED_BLOCKED` is unchanged). `currentness_verified` here is check-time currentness only |
| 3 Consumption | `agent_state` (`PO_CREATION`) `.dispatch_claim_consumption`: `consumption_record_id`, `dispatch_claim_id`, `root_request_id`, `request_revision`, `preallocated_at_proposal_id`, `bound_authorization_check_id`, `bound_action_verdict`, `transition_state_event_id`, `resulting_state_revision_id`, `consumed_by_call_id`, `bound_supplier_record_version`, `bound_approval_record_version`, `consumption_status = CONSUMED_SINGLE_USE_LOCKED`, `redispatch_or_reset_permitted = false` | The separate immutable record. Emitted by the runtime inside the atomic `APPROVED → PO_CREATION` step, after the `ALLOW` check and before the `tool_call`; persisted by the platform. At most one consumption per root and one use of each `authorization_check_id` (`ERR_PO_DUPLICATE_DISPATCH_CLAIM`, `ERR_AUTH_CHECK_REUSED`). **SA-02 (AMEND):** add the currentness observed **at consumption**: `latest_observed_supplier_record_version`, `latest_observed_approval_record_version`, `latest_observed_decision_record_seq` and `currentness_at_consumption` (`CURRENT`). A consumption whose observed versions differ from the bound ones is rejected (`ERR_STALE_RECORD_VERSION_AT_CLAIM`) |
| 4 Dispatch | `tool_call.dispatch_claim_id`, `dispatch_claim_consumption_ref` | The identity is equal on `tool_proposal`, `authorization_snapshot.dispatch_claim`, the `agent_state` (`bound_dispatch_claim_id`), the consumption record, the `tool_call` and any `UNKNOWN_OUTCOME` result (`ERR_DISPATCH_CLAIM_MISMATCH`, `ERR_UNKNOWN_RESULT_CLAIM_MISMATCH`) |
| 5 After consumption | `execution_budget_telemetry.dispatch_claim_ledger` | A new check, revision, idempotency key or continuation trace never resets a consumed or unresolved allowance (V03) |

**What "atomic" means here.** The consumption record is evidence of one runtime step: verify that the bound versions are still current, record the transition, consume the claim, emit the consumption record and the `tool_call`. Governance defines the comparison (§5.3 V06); the serialization or fence that makes it indivisible is the runtime's and Mohab's (GD-30). The validator can check only the recorded evidence offline, and live atomicity is a Sprint 2 runtime test. Governance claims no race safety.

Recovery after an unknown outcome is read-only [N]. For governance:

- A recovery observation grants no execution permission and is never a new authorization.
- It is a separate append-only record linked to the original uncertain invocation; it never replaces the original result. Its status is `RESOLVED_COMMITTED`, `RESOLVED_ABORTED` or `STILL_UNRESOLVED`.
- It must reference the original invocation and result, use the original idempotency key and argument digest, and agree with the original business request.
- Business outcome, transport outcome and `side_effect_state` must form a valid combination; an uncertain outcome (timeout, malformed or lost response, or an exception after the claim) stays `UNKNOWN` until authoritative reconciliation.
- Each invocation has exactly one terminal result, and an `UNKNOWN` result is bound to the exact call, proposal and claim.
- A run may not reach `COMPLETION` while the purchase-order effect is `UNKNOWN` or `STILL_UNRESOLVED`.

The rules RC-01 to RC-11 and the outcome table are in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §6 (GD-27).

### 4.8 Policy stage versus policy-check result (dashboard TRD-22 and TRD-23)

**Disposition: ACCEPT, they are two distinct things.** Malak's "Policy gate" tile shows the policy-check result and must stay that way. The coarse policy stage is a separate input fact.

| | Policy stage | Policy-check result |
|---|---|---|
| What it is | Where the workflow was when the action was proposed, checked and dispatched. An **input** to `PROC-TOOL-STAGE-01` | What governance decided about that action. An **output** |
| Trace Schema v1.9 | `agent_state.policy_stage`, `policy_stage_at_proposal`, `checked_policy_stage`, `policy_stage_at_dispatch` | `policy_check.action_verdict`, `verdict_basis`, `evaluated_policies[].policy_result` |
| Values | `PRE_APPROVAL`, `APPROVED`, `PO_CREATION`, `COMPLETED` | `ALLOW` or `BLOCK`; `PASS`, `FAIL`, `NOT_APPLICABLE`, `ERROR` |
| Produced by | The application state machine (coarse view of the fine `app_state`, Trace Schema v1.9 §4.1 table) | The governance engine |
| TRD-22 (state transitions) | Show previous and new fine state and the coarse stage on each transition, with accepted versus attempted | not shown here |
| TRD-23 (stage at each boundary) | Show the stage at proposal, at check and at dispatch as a plain label. Never as pass or fail | not shown here |
| "Policy gate" tile | not this | The verdict pill with its basis, and the three mandatory policy rows with their four-valued result |

The state-to-stage mapping itself belongs to Nour's state contract; governance owns only the allowlist by stage, which lives in the bundle identified by `policy_bundle_version`. Until Nour and Mohab define a separate version for the mapping, the dashboard shows the stage and the `policy_bundle_version` and does not invent a mapping version.

---

## 5. Governance-owned approval boundary

[N] places approvals and policy truth in governance: `request_approval` is a wrapper around a governance-owned boundary, and `calculate_approval_level` delegates to governance-owned calculation. This section is governance's side of that boundary; implementation is Sprint 2 (`approvals/approval_service.py`, `approvals/workflow.py` [R]).

### 5.1 Approval requirement calculation

One pure function, used by both the application's `calculate_approval_level` wrapper and `PROC-APPROVAL-01`, so the two cannot disagree.

| | Contract |
|---|---|
| Input | `total_amount` (decimal string), `currency`, active policy-bundle version |
| Output | `required` (true / false / `UNRESOLVED`), `approval_level` (null iff not required), `policy_id`, `policy_version`, `basis` (amount, currency, configured threshold, threshold currency, comparator, rule reference) |
| Rules | Strict `>` [P §R.1]; unsupported currency, missing or invalid configuration, text/config conflict, policy-version mismatch or request-context mismatch return `UNRESOLVED`, never `false`; a malformed amount (anything but the configured decimal-string pattern, including JSON numbers, exponents, whitespace and excess precision) is rejected before calculation and, if it reaches governance, is `AMOUNT_INVALID`; no threshold or currency is hard-coded |

**Values (GD-03).** The proposal's illustrative amount (§R.1) and the `5000` in Trace Schema v1's examples are not authority. The synthetic MVP values proposed by Nour in candidate 0.1 are: USD only, threshold `5000.00`, strict `>`, one level `manager`, no required level at or below the threshold, exact decimal strings, no rounding, no implicit currency conversion. They are carried in the [configuration proposal](policy-configuration/procurement-policy-set-v0.1.yaml) and are synthetic prototype values, not a business policy. The [response](response-to-owner-packet-0.14.md) §3.1 maps all 31 of Nour's boundary cases to governance results.

### 5.2 Approval records

Governance stores approval requests and decisions as append-only records; "current status" is derived (`INV-6`).

| Operation | Contract |
|---|---|
| Create request | Binds `request_id`, `request_revision`, `calculation_ref`, supplier, `total_amount`, `currency`, required level. Idempotent on the runtime-issued key: same key + same payload returns the same approval-request id; same key + changed payload is `IDEMPOTENCY_CONFLICT` [N] |
| Record decision | `PENDING` / `APPROVED` / `DENIED` / `CANCELLED`, outside model control. In the MVP decisions come from scenario fixtures or a trusted runtime input; **no approval endpoint, reviewer UI, notification transport or IAM** is created [N] |
| Observe | Returns the authoritative status for an approval-request id |
| Evidence returned | Approval id, approval-request id, request revision, supplier, amount, currency, level, approving actor reference, decision timestamp, policy version, source reference [N, `ApprovalEvidence`] |

Manager approval in the MVP is synthetic and fixture-driven. It stays separate from human trace review and from RBAC (§7): nobody in the role set is a purchase approver.

### 5.3 Approval validity

**DECIDED (GD-04), amended in v0.5 after Nour's OD-04 draft 0.1 and in v0.6 to use the Trace Schema v1.9 representation (GD-32).** `PROC-APPROVAL-01` is satisfied only when the clauses below hold. They answer V01 to V08 one by one; the dispositions are in the [response](response-to-owner-packet-0.14.md) §3.2.

**Authoritative current record.** Governance's approval service keeps approval requests and decisions as append-only records. Each record has an opaque `record_version` (its identity, for example `apr_rec_44_v1`) and a monotonic `decision_record_seq` (its position in that approval registry). The **current record** for an approval-request id is the record with the highest `decision_record_seq`. A record is never edited or deleted. The trace's `approval` event (E14) is the application's observation of a record, not a second authority. Supplier records are ordered by their own source and are never compared with approval sequences: each authority orders only its own records.

**Status transitions** (versioned configuration, `validity.status_transitions`):

| From | Allowed to |
|---|---|
| `PENDING` | `APPROVED`, `DENIED`, `CANCELLED` |
| `APPROVED` | `CANCELLED` (revocation) |
| `DENIED`, `CANCELLED` | none (terminal for this approval-request lifecycle) |

A write that violates the table is refused and audited (`APPROVAL_DECISION_REFUSED`); it never becomes the current record.

**Representation of terminal and superseded records (proposed to Mohab, GD-32).** Trace Schema v1.9 has `approval_status`, `record_version` and `decision_record_seq` but no field that says a record replaces another, and no rule that a terminal status stays terminal. Governance asks for:

| Item | Proposed representation |
|---|---|
| Supersession | Every record after the first carries `supersedes_record_version` and `supersedes_decision_record_seq`. The first record has `null` for both. A revocation is a `CANCELLED` record whose `supersedes_*` fields point at the `APPROVED` record it revokes |
| Terminal rule | After a record with `approval_status` `DENIED` or `CANCELLED` for an `approval_request_id`, no later record for that id may have status `PENDING` or `APPROVED`. A new validator code, proposed name `ERR_APPROVAL_TERMINAL_REOPENED`, rejects it. The v1.9 validator has no such rule today |
| Status values | The record statuses are `PENDING`, `APPROVED`, `DENIED`, `CANCELLED`. `EXPIRED` is never produced (no time expiry). `STALE_REVISION` is not a record status: it is a currentness result (below) |
| Currentness result | `CURRENT`, or `STALE` with a reason: `APPROVAL_RECORD_SUPERSEDED`, `APPROVAL_NO_LONGER_APPROVED`, `SUPPLIER_RECORD_SUPERSEDED`, `REQUEST_REVISION_CHANGED`, `POLICY_BUNDLE_CHANGED`. The single v1.9 code is `ERR_STALE_RECORD_VERSION_AT_CLAIM`; the reason travels beside it |

| Clause | Rule |
|---|---|
| **V01 No time expiry** | The configuration declares `time_expiry: NONE` explicitly. A missing validity block is unresolved (`POLICY_CONFIG_MISSING`), never a forever-valid grant. Age alone never invalidates a current, correctly bound approval |
| **V02 Current evidence and exact binding** | Valid only if the current record is `APPROVED` and is bound to the proposal's request revision, supplier, `total_amount`, `currency`, required level, `calculation_ref` and policy version, and the approver reference resolves to a synthetic approver whose level satisfies the required level. A cap, a role string, a cache, model text or an id alone proves nothing. No RBAC role is a purchase approver (§5.2) |
| **V03 Revised request** | Any change to amount, currency, supplier, item or quantity, or any new request revision (even with the same total), invalidates the prior calculation, approval and `ALLOW` for that revision. The binding carries `request_revision`, so this is case AP-07. A revision never clears an existing purchase-order claim, unknown outcome or spent budget; those are runtime guards |
| **V04 Denial, cancellation, revocation** | `DENIED` and `CANCELLED` are terminal. A later "approval" for that approval request is refused, not accepted. Revocation is a new `CANCELLED` record whose `supersedes_*` fields point at the prior grant, never a `REVOKED` status. A new business attempt needs a new request revision and a new approval request. If the approval event and the governance record, or two records at the same version, disagree on the decision or binding, no valid approval is established: `FAIL` with `APPROVAL_EVIDENCE_CONTRADICTION` |
| **V05 Late decisions and order** | The approval must precede the exact proposal being checked, decided by `decision_record_seq` in the approval registry and by the trace `sequence_number`, never by wall-clock time alone. A later approval cannot repair an earlier blocked proposal or `ALLOW`; it supports only a new proposal with a fresh check. An approval after dispatch cannot retroactively authorize it (post-run `APPROVAL_AFTER_PROPOSAL`). Future-dated, conflicting or unorderable evidence is `ERROR` (`APPROVAL_ORDER_UNDETERMINED`) and blocks |
| **V06 Revocation, check and dispatch race** | The `authorization_snapshot` carries the approval and supplier `record_version`, the `decision_record_seq`, the request revision and the policy-bundle version. At the atomic consumption the runtime verifies they are still current, using the governance currentness comparison, and records the result in the consumption record (SA-02, §4.7): `CURRENT`, or `STALE` with a reason from the table above. `STALE` suppresses the dispatch (`tool_suppression`, `NOT_EXECUTED`). A snapshot or a fresh read alone is not proof that the race is solved; the serialization or fence belongs to the runtime and Mohab (GD-30), and no race-safety proof is claimed at specification stage |
| **V07 Trusted continuation** | Resume only the same active request revision through an authorized runtime continuation, with stable root and approval-request ids, the original submission key binding, linked evidence, the current-record check of V02 at resume, and retained budgets and claims. A user or model assertion, a callback payload or a trace id alone cannot resume. Observation is read-only and cannot submit, update, approve or replace a request (OD-APP-OBS-01). Whether a continuation uses one trace or linked traces is Mohab's; governance requires only that it references the original approval-request id, request revision and root id |
| **V08 Effects already dispatched** | Revocation after dispatch does not undo an order, prove no effect or rewrite the authorization; validity is judged as of the authorization boundary. The later `CANCELLED` record is appended. The original invocation and outcome stay as recorded, `UNKNOWN` stays `UNKNOWN` until read-only reconciliation, and `COMPLETION` is not rewritten. No cancellation, refund or replay capability is introduced |

**Evidence that permits each transition**

| Transition | Required evidence |
|---|---|
| `APPROVAL_PENDING` → `APPROVED` | Current record `APPROVED` at version *n*; bound to the unchanged revision, supplier, amount, currency, level, calculation and policy version; eligible approver; ordering established; the read-only observation (E14) matches the record |
| `APPROVED` → new PO proposal | A new proposal made after the approval, and a fresh check `ALLOW` bound to record version *n* |
| `APPROVED` → `PO_CREATION` | Bound `ALLOW`, currentness `CURRENT` at the claim, atomic consumption of the preallocated claim |
| any state → halt | `DENIED` or `CANCELLED`, missing or conflicting evidence, unresolved ordering, or `STALE` |

**Which time checks decide and which are informational (proposed to Mohab, GD-32).** The v1.9 validator checks the chain `trace.started_at <= approval_timestamp <= verified_at <= policy_check.timestamp`, with the lower bound taken from the trace start. That bound is wrong for an approval decided **before** this trace began, which is exactly the case when an existing approval is observed across a continuation (V07): the decision time then legitimately precedes the continuation trace's start.

| Check | Class | Governance position |
|---|---|---|
| ISO-8601 UTC syntax of every timestamp | Structural | Keep (`ERR_TIMESTAMP`) |
| Each event's timestamp inside this trace's `started_at` and `completed_at` | Structural | Keep for events produced in this trace, including `verified_at` and the `approval` event timestamp |
| `approval_timestamp <= verified_at <= policy_check.timestamp` | Consistency (a decision cannot be observed before it was made) | Keep (`ERR_APPROVAL_CHRONOLOGY_INVALID`) |
| `trace.started_at <= approval_timestamp` | Would reject an approval decided before the continuation trace started | **Remove.** The lower bound for the decision time is the approval request's own submission time, not this trace's start |
| Wall-clock order of an approval against the proposal or a revocation | Would make validity depend on clocks | **Informational only.** Order is decided by `decision_record_seq` and trace `sequence_number` (`ERR_APPROVAL_SUPERSEDED_SEQUENCE`) |

**Existing approval observed across a continuation.** In the continuation trace the `approval` event is an **observation** (`OBSERVE_APPROVAL`, read-only) of a record that already exists. It carries the record's own `approval_request_id`, `record_version`, `decision_record_seq` and `approval_timestamp`, plus the continuation's `verified_at`. It must resolve to the same current record in governance's registry. Whether the continuation is the same trace or a linked trace is Mohab's decision; governance needs only that the record is resolvable by `approval_request_id` and `record_version` independently of which trace holds the event.

**Terminal records and the actions they gate.** A `CANCELLED` (or `DENIED`) record does not point forward to the actions it blocks, because records are append-only. The link runs the other way, by reference: every action that depends on an approval records the approval version it was checked against.

| Gated action | Where it records the approval it depends on |
|---|---|
| A purchase-order `policy_check` | `authorization_snapshot.approval_evidence_ref` (`approval_event_id`, `approval_record_version`, `decision_record_seq`) |
| The dispatch claim at check | `authorization_snapshot.dispatch_claim.bound_approval_record_version` |
| The consumption of the claim | `dispatch_claim_consumption.bound_approval_record_version` and, with SA-02, the version observed at consumption |
| The dispatch itself | `tool_call.dispatch_claim_consumption_ref` |

The set of actions gated by a cancelled approval is therefore: every action whose recorded approval version equals the `supersedes_record_version` of the `CANCELLED` record, for the same `approval_request_id`. A viewer follows the chain: cancelled record, superseded record, actions that bound it, and the `tool_suppression` that stopped a stale dispatch. No stored back-link is needed or allowed.

The paper cases OD04-C01 to OD04-C27 map to governance results in the [response](response-to-owner-packet-0.14.md) §3.2 and the [truth tables](policy-truth-tables.md) §8.

---

## 6. Decision engine — draft interface

### 6.1 Input [D]

A decision input names a target (`trace` or `release_evaluation` with its id) and carries an evidence bundle made of DI-01 to DI-09. The decision configuration (thresholds and version) is loaded by the engine, not supplied by the caller.

Whether the engine receives **raw metrics and compares them to configured thresholds**, or receives **precomputed flags** such as "borderline" or "severe", is open (GD-12). Proposed default: raw metrics in, thresholds in `config/decision_thresholds.yaml`, so every threshold lives in one versioned place and the decision path can show the observed value against the threshold. While thresholds are not configured (OD-15), the output lists the threshold-based rules as not evaluated; it never invents a number.

### 6.2 Output [D]

| Field | Notes |
|---|---|
| `decision_id`, `target`, `created_at` | |
| `decision` | `PASS` / `REVIEW` / `BLOCK`, absent when evaluation is incomplete |
| `evaluation_status` | `COMPLETE`, or `INCOMPLETE` with the missing evidence listed |
| `fired_rules` | Ordered `DEC-n` ids with reason codes and the evidence behind each |
| `not_evaluated_rules` | Rules skipped, each with the reason (for example, threshold not configured) |
| `evidence_refs`, `evidence_run_ids` | References into traces, findings and evaluation runs |
| `decision_config_version`, `decision_engine_version` | |

A re-run creates a new record and leaves earlier decisions untouched (`INV-6`).

### 6.3 Post-run policy evidence: attempted, prevented, realized

**DECIDED (GD-16, amended by GD-33).** The pre-tool result records an *attempted* violation. Post-run policy evaluation adds `enforcement_outcome` to each `FAIL` finding on a tool proposal, derived from the dispatch evidence (E19, E20):

| `enforcement_outcome` | Meaning |
|---|---|
| `PREVENTED` | The dispatch was suppressed (`NOT_EXECUTED`, `execution_started = false`, `side_effect_state = NONE`) |
| `REALIZED` | The tool executed and its effect is confirmed although a critical policy `FAIL` applied. Two different causes, kept apart in the evidence: a **policy defect** (the engine returned a wrong `PASS`) and an **enforcement bypass** (the gate was not consulted or its `BLOCK` was ignored) |
| `DEFINITIVE_NO_EFFECT` | The tool was dispatched but authoritative proof shows nothing was committed and nothing is in flight. The control did not stop it, but no effect exists. Renamed from `NOT_REALIZED` on 13 November 2026 (evidence document §6.7) |
| `UNKNOWN` | No dispatch evidence either way, or the outcome is uncertain, inconsistent or duplicated |

The value is derived only from a **valid** outcome combination (`PREVENTED` from a suppression, `REALIZED` from a confirmed effect, `DEFINITIVE_NO_EFFECT` from an authoritative no-effect failure, `UNKNOWN` from an uncertain outcome of any kind, an invalid combination or a duplicate terminal result). An idempotent replay (`ALREADY_EXISTING`) inherits the outcome of the original call through `original_result_ref`. A recovery observation can move `UNKNOWN` to `REALIZED` or `DEFINITIVE_NO_EFFECT`; it never rewrites the original result. The authoritative evidence for each value, and what is preserved when the value stays `UNKNOWN`, is in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §6.6.

`DEC-1` fires for all four; `REALIZED` is flagged in the rule path as "unsafe action executed".

**A correctly blocked attempt is not a policy defect.** The policy result `FAIL` says the proposed action breached the rule. The outcome `PREVENTED` says the control stopped it. Together they describe a policy that worked. Governance never records a correct `BLOCK` as a failure of the policy, of the supplier rule or of the configuration. The Layer 2 decision is still `BLOCK` through `DEC-1`, because the evaluated agent attempted a critical breach.

**Labels (OD-09, Ahmed's decision).** Whether the failure label for an attempted-and-prevented violation is `POLICY_VIOLATION` (the class "attempts or executes" the breach) or something else is for Ahmed. Governance's recommendation: `POLICY_VIOLATION` for every critical policy `FAIL` regardless of the outcome, with `enforcement_outcome` carried next to the label so that the dashboard, the dataset and the release comparison can separate prevented from realized. That keeps the attempt visible and does not count successful enforcement as an enforcement failure.

**Executed under an unverified authorization (GD-26, proposed).** If a purchase order was dispatched under an authorization that failed the consistency rules (for example a mismatched dispatch-claim id or binding), post-run policy evaluation re-derives the policies from the source records and records the dispatch as executed under an unverified authorization. That is a critical finding and fires `DEC-1`, because the mandatory pre-tool control did not demonstrably authorize the action. This extends `DEC-1` beyond a policy `FAIL` and needs Ahmed, Alaa and the plan owner to agree.

### 6.4 Release gate verdict and incomplete evaluation

**DECIDED (GD-22).** The release verdict (`REL-01`) is the Layer 2 decision for a release evaluation, produced by the governance decision engine through `gate/decision_adapter.py` [R]. Alaa's runner supplies the comparison inputs and owns the comparison, the gate artifact and what happens to the candidate; her gate module calls the adapter and does not re-implement the precedence. This is the "Option A" assumed by [X]; Alaa's acknowledgement is requested.

**DECIDED (GD-13).** An incomplete evaluation has no `decision`. The record carries `evaluation_status = INCOMPLETE` and the missing-evidence list. The gate treats it as non-approving, like `REVIEW`, and shows it as "Incomplete evaluation", never `PASS`. A critical policy `ERROR` counts as incomplete; it is never read as compliance. Alaa and Malak's acknowledgement is requested for the gate and screen treatment.

### 6.5 Evidence boundary for the RCA causes `policy_configuration` and `agent_workflow`

Ahmed's root-cause taxonomy has nine fixed causes. Governance does not assign the cause (that is Ahmed's, and `injected_root_cause` is set by the scenario owner). What governance gives is the **evidence that must exist** before each of the two causes can be selected, so a correct block is never labelled as a configuration defect.

| Situation | Evidence | Candidate cause |
|---|---|---|
| A real agent proposes a purchase order for a `NOT_APPROVED` supplier and the gate blocks it (`PREVENTED`) | `PROC-SUPPLIER-01` `FAIL`, `tool_suppression`, `side_effect_state = NONE`, re-derivation agrees (EC-11 passes) | `agent_workflow` is the candidate (the agent attempted a step the workflow forbids). **Never** `policy_configuration`. The SC-03B boundary fixture is **not** this case: its proposal is synthetic and no agent caused it, so its cause is open (below) |
| The application guard stops at `POLICY_CHECKED` after `get_supplier` returns `NOT_APPROVED` (SC-03A) | No policy `FAIL`; read-tool checks `ALLOW` | **No RCA cause.** It is a correct business stop, not a failure |
| Recorded `PASS` for a `NOT_APPROVED` supplier, order dispatched | EC-11 finding: the recorded result differs from the re-derived result; `REALIZED` | `policy_configuration` (engine or configuration wrong). Only with the EC-11 finding |
| The active configuration differs from the accepted bundle while the evidence is valid (`policy_bundle_version` or the configuration digest does not match the accepted file) | `POLICY_VERSION_MISMATCH` (EC-08), re-derivation under the accepted bundle differs from the recorded result | `policy_configuration` |
| A seeded mutation of the configuration (threshold, stage allowlist, status set) in a candidate | The mutation is declared in the scenario and the recorded results are consistent with the mutated configuration but not with the accepted one | `policy_configuration` |
| The gate was not consulted, its `BLOCK` was ignored, or the dispatch happened with no verdict or an unverified authorization (GD-26) | No `policy_check`, or `BLOCK` followed by a `tool_call`; consumption record without a bound `ALLOW`; `REALIZED` | **No fixed cause fits** (the application's enforcement is wrong, not the policy). Ahmed to say which of the nine applies, or whether a tenth is needed. Governance does not map it to `policy_configuration` |

SC-03B's seeded cause is the deliberately inconsistent proposal-context fixture. Its mapping to the nine causes needs Ahmed and Mohamed's review [N, failure planning SC-03]; governance does not map it here.

The rule behind the table: `policy_configuration` requires proof that the configuration or the engine produced a wrong result (EC-11 or EC-08 or a declared mutation). Ineligible supplier data, a correct `BLOCK` and an application-side stop are never, on their own, evidence of a configuration defect.

---

## 7. Human review, audit, roles and overrides

### 7.1 Human review record [P §R.2, FR-13; field names D]

| Field | Producer | Consumer | Notes |
|---|---|---|---|
| `review_id` | governance | audit | |
| `target_type`, `target_id` | Reviewer via API | Malak | Trace or release evaluation |
| `verdict` | Reviewer | Malak, Alaa | `ACCEPT` / `REVIEW` / `BLOCK` |
| `rationale` | Reviewer | Malak, audit | Required and non-empty for every verdict |
| `reviewer_id`, `reviewer_role` | identity context (Mohab) | audit | Attributed server-side, never taken from the request body |
| `administrator_action` | governance | Malak | True when an Administrator acts in a reviewer capacity [X] |
| `referenced_decision_id` and its config version | governance | Malak | Records which machine decision the person was looking at |
| `created_at` | governance | audit, Malak | |

A new review is a new record; the history returns all of them and the current state is derived. A review never edits the machine decision.

### 7.2 Audit record [P §H Auditability, FR-18; field names D]

| Field | Notes |
|---|---|
| `audit_id`, `occurred_at` | |
| `actor_id`, `actor_role` | System actors use an explicit id such as `system:policy-engine` |
| `administrator_action` | Flag set when an Administrator takes an action that normally belongs to another role [X] |
| `action` | From the catalogue below |
| `target_type`, `target_id` | |
| `applicable_version` | Policy-set, decision-config or other version in force |
| `rationale` | Where the action carries one |
| `evidence_refs`, `metadata` | |

No update or delete operation exists on the audit repository interface (`INV-6`). Database-level protection is added only if it fits the shared PostgreSQL design.

Audit action catalogue [D]:

| Action | Written when |
|---|---|
| `POLICY_SET_CREATED`, `POLICY_SET_ACTIVATED` | An Administrator creates or activates a policy configuration |
| `POLICY_CHECK_COMPLETED` | A pre-tool check finishes — one row per check, system actor, referencing `check_id` and the verdict |
| `APPROVAL_REQUESTED`, `APPROVAL_DECIDED`, `APPROVAL_DECISION_REFUSED` | An approval request is created, a decision is recorded, or a decision that violates the transition table is refused (§5.3) |
| `DECISION_RECORDED` | A reliability decision is stored |
| `REVIEW_SUBMITTED` | A reviewer appends a verdict |
| `OVERRIDE_REQUESTED`, `OVERRIDE_APPROVED`, `OVERRIDE_REJECTED` | Added in this revision for US-26/US-27 [X] (GD-19) |
| `ROLE_ASSIGNED` | An Administrator assigns a role |
| `ACCESS_DENIED` | A sensitive action is rejected by RBAC |

Policy checks are stored as their own append-only evidence (PO-03) and also get an audit row so there is one chronological trail. The audit row and the record it describes should be written in the same database transaction (GD-11).

### 7.3 Roles and capabilities

**PROPOSED (GD-18).** The proposal names three prototype roles (Engineer, Reviewer, Admin; FR-19). The user stories v2.2 define seven pre-provisioned role codes with per-screen access (US-27, Appendix B) [X]. Rather than hard-code either, the backend enforces **capabilities**, and a versioned role-to-capability table decides who holds them. The three prototype roles are a grouping of the seven, so both sources are satisfied:

| Proposal role | Story roles (codes) |
|---|---|
| Engineer | `AI_ENGINEER`, `RELIABILITY_ENGINEER`, `LLMOPS_ENGINEER`, `PLATFORM_ENGINEER` |
| Reviewer | `GOVERNANCE_REVIEWER` |
| Admin | `ADMIN` |
| (read-only addition) | `SECURITY_AUDITOR` |

Backend checks are authoritative; hiding a frontend control is not enforcement.

| Capability | ADMIN | GOVERNANCE_REVIEWER | LLMOPS_ENGINEER | other Engineers | SECURITY_AUDITOR |
|---|:---:|:---:|:---:|:---:|:---:|
| `evidence.view_redacted` | yes | yes | yes | yes | yes |
| `evidence.view_raw` | yes | no | no | no | no |
| `history.view` (review and audit history, read-only) | yes | yes | yes | yes | yes |
| `review.submit` | yes (flagged) | yes | no | no | no |
| `override.request` | yes (flagged) | no | yes | no | no |
| `override.decide` | yes (flagged) | yes | no | no | no |
| `policy_config.manage` | yes | no | no | no | no |
| `roles.assign` | yes | no | no | no | no |

Notes:

- **Source of the table.** The role set, raw-payload rule (raw for the Administrator only, redacted for everyone else), flagged Administrator use and the read-only Security Auditor come from US-27 as summarised in [X]. This table follows that summary; Mohamed confirms it against the stories before it freezes.
- **`review.submit` is an action-level capability.** It does not depend on a dashboard's Manage or View level (answers Q-07).
- **Writes.** The Security Auditor holds no write capability; the backend rejects a write with `ACCESS_DENIED`, which is also audited.
- **Other Manage actions** in Appendix B (configuring application behavior, running evaluations, annotating results, initiating gate evaluations) are not governance-owned. Governance only provides the capability check; the actions belong to their owners (§9.2, Q-13).
- **Identity mechanism** is a lightweight prototype — no SSO, OAuth or enterprise IAM [P §E; R S6-01]. Which mechanism and who supplies it is open (GD-14).

### 7.4 Override requests

**PROPOSED (GD-19).** The user stories add a BLOCK-override workflow on the release gate [X]: an `LLMOPS_ENGINEER` requests it with a written reason; a `GOVERNANCE_REVIEWER` (or flagged `ADMIN`) approves or rejects it. Governance's contract for it:

| Record | Fields |
|---|---|
| Override request | `override_request_id`, release-evaluation id, referenced gate decision id and config version, requester id and role, written reason (required), `created_at` |
| Override decision | `override_request_id`, outcome `APPROVED` / `REJECTED`, approver id and role, written reason (required), `administrator_action`, `created_at` |

Both are append-only and audited (§7.2). **They never change the recorded machine decision**: the gate decision stays `BLOCK` (`INV-4`). What an approved override means for the candidate is Alaa's disposition; this contract creates no automatic promotion, rollback or release. The proposal itself says `BLOCK` retains the approved baseline and contains no override; the plan owner confirms that overrides are in the MVP scope before any code is written.

---

## 8. Decisions

"Maps to" gives the matching item in the shared open-decisions register. Status words are defined at the top of this document.

| Id | Maps to | Decision | Status | Acknowledgement needed from |
|---|---|---|---|---|
| GD-01 | OD-02 / D3 | `calculate_approval_level` is allowed in `PRE_APPROVAL` as a read-only tool, and the application permits it only in the fine state `SUPPLIER_CHECKED` with the supplier and policy prerequisites met. It extends the proposal's three-tool list and does not weaken the purchase-order restriction | DECIDED (accepts Nour's narrower row, §2.1) | Nour; plan owner (documented extension of the proposal) |
| GD-02 | — | Policy keys on the four-value coarse `policy_stage` (§2.1) and every tool proposal goes through the hook. Fine-grained state naming is not a governance input | DECIDED | Nour, Mohab |
| GD-03 | OD-03 | Strict `>`; all values only in versioned governance configuration; policy text that disagrees with configuration halts rather than being reconciled by a model [N]. Values: Nour's candidate 0.1 (USD only, `5000.00`, level `manager`, exact decimal strings, no rounding, no currency conversion) is accepted as **synthetic MVP configuration** in the form of [procurement-policy-set-v0.1.yaml](policy-configuration/procurement-policy-set-v0.1.yaml) (version `synthetic-procurement-policy-set-v0.1`). They are not a business policy and not the proposal's illustrative number | DECIDED (mechanism and values); acceptance record is Mohamed's response | Nour (updates affected source fixtures and examples on acceptance); Mohab (transport and binding) |
| GD-04 | OD-04 | Approval validity clauses V01 to V08 with the authoritative current record, terminal `DENIED`/`CANCELLED`, record-sequence ordering, currentness at the claim and the evidence for each continuation (§5.3). Amended in v0.5 after Nour's OD-04 draft 0.1 | DECIDED (governance rule); joint on the version/order binding and continuation | Mohab (field and event mapping, continuation topology, currentness mechanism), Nour (state transitions) |
| GD-05 | OD-05 | Transport: `POST /api/v1/policy/check`, events `tool_proposal` and `policy_check` [T], thin router in `apps/api`, models in `packages/contracts` | PROPOSED | Mohab |
| GD-06 | OD-06 / D4 | Sprint 2 (S2-04): real pure policies and an in-process service behind the agreed interface, replacing the stub as soon as it is callable; the S2-01 stub is labelled `STUB_CONTRACT_TEST` until then and stops qualifying for any enforcement-acceptance claim once the S2-04 service is merged. Sprint 3 (S3-03): persistence and end-to-end seeded scenarios. Real-policy acceptance requires `ONLINE_PRE_TOOL`. The Week 6 gate is unchanged. Exact S2-04 deliverable and stub limits: [response](response-to-owner-packet-0.14.md) §3.7 | DECIDED (governance side) | Plan owner (not yet named), Mohab (adds the stub label to `check_mode`, §4.5 row 15), Nour |
| GD-07 | OD-12 | `authorization_snapshot` (§4.2); runtime verifies equality and consumes the claim once, linked to `check_id`; governance replays idempotently. The claim consumption is a separate record (GD-28) | PROPOSED | Nour, Mohab |
| GD-08 | — | Governance evaluates against its active policy-bundle version and fails closed on a mismatch | DECIDED | Nour (the application re-derives evidence under the active version) |
| GD-09 | — | No verdict, timeout or technical error means no dispatch; recorded as a check error with a `NOT_EXECUTED` suppression, never as a policy `FAIL` or `ALLOW` | DECIDED | Nour, Mohab (hook and SDK behavior, plus a test) |
| GD-10 | — | Mohamed authors the governance models and enums in `packages/contracts`; Mohab reviews | PROPOSED | Mohab |
| GD-11 | — | One unit of work spans platform and governance repositories so a check and its audit row commit atomically | PROPOSED | Mohab |
| GD-12 | OD-15 (thresholds) | Raw metrics in, thresholds in `config/decision_thresholds.yaml`; Ahmed marks criticality per attack category and defines "disagreement" and "borderline" | PROPOSED | Ahmed, Alaa |
| GD-13 | — | Incomplete evaluation: no decision, status `INCOMPLETE`, gate non-approving (§6.4) | DECIDED | Alaa, Malak (gate and screen treatment) |
| GD-14 | — | Prototype identity mechanism and who supplies it | OPEN | Mohab (needed before S6-01) |
| GD-15 | — | Raw payloads for `ADMIN` only; review history and audit history are read-only visible to every role; the Security Auditor is read-only | DECIDED | Malak |
| GD-16 | OD-09 | `enforcement_outcome` on post-run policy findings (§6.3): `PREVENTED`, `REALIZED`, `DEFINITIVE_NO_EFFECT`, `UNKNOWN`; `DEC-1` fires either way. A correct `BLOCK` is not a policy defect; label mapping and the recommended `POLICY_VIOLATION` plus outcome are Ahmed's (GD-33) | DECIDED | Ahmed (label mapping) |
| GD-17 | OD-16 / D5 | RAG has no pre-tool check and no `policy_check` event. Its post-run policy evidence is the `policy_conformance` evaluator result with `status = NOT_APPLICABLE` and a null score, as in Ahmed's evaluator contract, with governance reason `POLICY_NOT_APPLICABLE_TO_APPLICATION` and basis `application_type = rag`. That is distinct from `PASS` (satisfied), from evaluator `ERROR` (could not decide) and from `NOT_REQUESTED` (an application guard stopped the action before any check). The decision engine treats it as absent evidence, never as proof of compliance. No RAG policy exists in the approved scope | DECIDED | Nour; Ahmed (evaluator wording); plan owner (scope) |
| GD-18 | — | Capability-based RBAC with the seven story role codes seeded and the proposal's three roles as a grouping (§7.3) | PROPOSED | Plan owner (stories versus proposal baseline) |
| GD-19 | — | Override request and decision records, record-only (§7.4) | PROPOSED | Plan owner (is it in the MVP), Alaa (disposition) |
| GD-20 | — | Canonical governance-owned values (§4.5) | PROPOSED | Mohab, Nour, Malak |
| GD-21 | — | Governance-owned dashboard actions are review, override request and override decision only. Policy-configuration management and role assignment are Administrator API operations; the login form and account management are outside the seven screens | DECIDED | Malak |
| GD-22 | — | Governance decision engine produces the release verdict through the gate adapter (§6.4) | DECIDED | Alaa |
| GD-23 | — | `execution_scope` is recorded for provenance and never changes a verdict; the boundary test calls the same interface as production (SC-03B). The field is not in Trace Schema v1.9 yet (§4.5 row 16) | DECIDED (governance side); placement PENDING (Mohab) | Nour, Mohab |
| GD-24 | — | Evidence resolution: a platform adapter resolves each reference to a typed record behind a port governance defines; governance compares claims with the resolved records and reports the findings. Adds `ports/evidence_resolver.py` and `policy/evidence_consistency.py`, outside the approved tree; one finding-code registry in `packages/contracts` | PROPOSED | Mohab |
| GD-25 | — | Copies are claims and source records are evidence: policy results come from resolved source evidence, any consistency finding or unresolved reference prevents `ALLOW` and verified-binding certification, and a failing trace with consistent evidence is still captured as a failure fixture | DECIDED | Mohab (validator behavior), Nour |
| GD-26 | — | A purchase order executed under an authorization that fails the consistency rules is a critical finding and fires `DEC-1` (§6.3). Extends `DEC-1` beyond a policy `FAIL` | PROPOSED | Ahmed, Alaa, plan owner |
| GD-27 | OD-12-OUTCOME | Outcome and recovery interpretation, in Trace Schema v1.9 names: valid combinations of `execution_status`, result `status` and `side_effect_state` (`NONE`, `COMMITTED`, `ALREADY_EXISTING`, `UNKNOWN`); an uncertain outcome (timeout, malformed or lost response, or a `RUNTIME_EXCEPTION` after the claim) stays `UNKNOWN`; a definitive `NONE` after dispatch needs authoritative proof (`RESOLVED_ABORTED`); `ALREADY_EXISTING` maps to the budget checkpoint state `COMMITTED_CONFIRMED` with no new effect; recovery is a separate append-only `recovery_check` (`RESOLVED_COMMITTED`, `RESOLVED_ABORTED`, `STILL_UNRESOLVED`) that grants no authorization; an `UNKNOWN` result binds to its exact call, proposal and claim; no `COMPLETION` while the effect is unresolved; one terminal result per invocation; `enforcement_outcome` gains a value for a dispatch that conclusively had no effect (`DEFINITIVE_NO_EFFECT` since GD-33). Also resolves the conflict with `side_effect_committed = false` on a timeout in the evaluation pipeline | PROPOSED | Ahmed (reviews interpretation), Mohab (event semantics), Nour (runtime state fit) |
| GD-28 | OD-12-CLAIM | Authorization lifecycle, as agreed in Trace Schema v1.9 §4.4.3: the runtime **preallocates** the root-scoped `dispatch_claim_id` (`dclaim_<root_request_id>`) before the check; the check binds it in `authorization_snapshot.dispatch_claim` and never consumes it; the single allowance is **consumed** atomically by the runtime after a bound `ALLOW`, in a separate immutable `dispatch_claim_consumption` record; the id is identical across proposal, snapshot, `agent_state`, consumption, `tool_call` and any `UNKNOWN_OUTCOME` result (§4.7). Two amendments to v1.9: SA-01 (`claim_status_at_check` must not imply consumption) and SA-02 (currentness recorded at consumption) | PROPOSED | Nour, Mohab |
| GD-29 | OD-12-RETRY, OD-12-BUDGET | A retry of a read-only tool gets a new `attempt_id` and a fresh, separately bound check; the same attempt replayed returns the original check. No original write (`CREATE_APPROVAL_REQUEST`, `CREATE_PO`) is replayed automatically. Budget exhaustion is a technical stop that blocks dispatch and is never recorded as a policy `FAIL` or `ALLOW` | DECIDED (governance side) | Mohab (mode and attempt contract), Nour (runtime), Alaa (workload) |
| GD-30 | OD-04 (V06) | The `authorization_snapshot` carries the approval and supplier `record_version`, the `decision_record_seq`, the request revision and the policy-bundle version; governance defines the currentness comparison (`CURRENT` or `STALE` with a reason) and the runtime runs it inside the atomic consumption and records the result in the consumption record (SA-02). The serialization or fence is the runtime's and Mohab's; no race safety is claimed | PROPOSED | Mohab, Nour |
| GD-31 | OD-05-MAP | Trace Schema v1.9 is the naming source for every field and enum governance shares with the trace. Governance keeps no parallel names; the earlier governance names appear only in §4.5 so readers of earlier drafts can find the new ones. Confirmed rows, amendments (SA-05 approval statuses, SA-06 criticality spelling, SA-01 and SA-02 claim and consumption) and pending rows (SA-07 stub label, SA-08 execution scope, SA-09 enforcement outcome) are in §4.5 | DECIDED (governance side); joint with Mohab for the amendments | Mohab (amendments), Nour, Malak |
| GD-32 | OD-04 | Approval-record representation proposed to Mohab: `supersedes_record_version` and `supersedes_decision_record_seq` on every record after the first; terminal `DENIED` and `CANCELLED` enforced by a new validator rule (proposed `ERR_APPROVAL_TERMINAL_REOPENED`); `EXPIRED` never produced and `STALE_REVISION` moved to the currentness result; removal of the trace-start lower bound on `approval_timestamp`; wall-clock order informational only (§5.3). These are SA-03, SA-04 and SA-05 in the [follow-up response](response-to-owner-packet-9e6affa.md) | PROPOSED | Mohab, Nour |
| GD-33 | OD-09 (Ahmed's scoped evaluator review, 13 Nov) | Prevented versus realized and the expected behavior of an ineligible supplier: (1) SC-03A (full application, early stop) runs the read-tool checks and has no purchase-order check, so it is not evidence of the pre-tool supplier rule; SC-03B (boundary test) is the case where `PROC-SUPPLIER-01` `FAIL` produces `BLOCK` and a suppression (truth tables §6); (2) a correct `BLOCK` is a policy `FAIL` with outcome `PREVENTED` and is never a policy defect (§6.3); (3) `NOT_REALIZED` is renamed `DEFINITIVE_NO_EFFECT`, and `ALREADY_EXISTING` inherits the outcome of the original call; (4) `EC-11` re-derives each recorded policy result from source evidence and is the evidence for `policy_configuration` (§6.5); (5) the `policy_configuration` and `agent_workflow` evidence boundary is §6.5. Governance does not assign labels or `injected_root_cause` | DECIDED (governance side); labels PENDING (Ahmed); RCA mapping PENDING (Ahmed and Mohamed, per Nour's SC-03 text) | Ahmed, Nour |

---

## 9. Responses

### 9.1 S1-01 handoff checklist

The [checklist](../reference-applications/handoffs.md#mohamed--s1-04-policy-interaction-and-approval-authority) lists what the reference-application contracts need back from governance. Status reflects this draft only; nothing here has been reviewed by a teammate.

| Required back | Status | Where |
|---|---|---|
| Versioned truth tables for the three policies, including below / equal / above threshold | **Written** (symbolic, no values invented); not yet reviewed | [policy-truth-tables.md](policy-truth-tables.md) |
| D3 resolution, state/stage mapping, no-approval-required branch | **Decided** on the governance side | GD-01, GD-02, §2.3 |
| Canonical synchronous `ALLOW`/`BLOCK` interface plus technical-error and missing-verdict semantics | **Drafted**; transport mapping awaits Mohab | §4, decision-flow §5.1, GD-05, GD-09 |
| Approval evidence source, validity, expiry, revocation, stale handling, trusted resumption | **Decided** (rules); resume representation is Mohab's | §5, GD-04 |
| Binding of `ALLOW` to proposal, state and arguments; check-to-dispatch mutation handling | **Proposed**; atomic claim stays with the runtime | §4.2, GD-07 |
| D4 integration-date reconciliation and D5 applicability | **Decided** | GD-06, GD-17 |
| Supplier-breach fixture for SC-03, boundary-test scope, confirmation that the real engine suppresses dispatch | **Fixture proposed** for Nour and Ahmed; real-engine confirmation needs S3-03 | [policy-truth-tables.md](policy-truth-tables.md) §6, GD-23 |
| Written policy-evidence sign-off | **Not given.** It is Mohamed's acceptance to give, naming the revision, after the reviewers respond | [README](README.md#s1-01-sign-off-by-mohamed-not-given) |

### 9.2 Questions addressed to Mohamed in the dashboard review packet

| Q | Answer | Basis |
|---|---|---|
| Q-06 | Yes: an evidence reference identifies one event as `trace_id` + `event_id` (the trace-scoped event id and sequence number in [T]). An incomplete evaluation has no decision and is never `PASS`; the rule path lists fired rules with their evidence | DO-05, §6.2, GD-13 |
| Q-07 | "Submit a review" is an action-level capability (`review.submit`), independent of a dashboard's Manage or View level. The audit catalogue now has `OVERRIDE_REQUESTED`, `OVERRIDE_APPROVED`, `OVERRIDE_REJECTED` and an `administrator_action` flag. Review and audit history are read-only visible to every role. The role set follows the seven story roles, pending the plan owner (GD-18) | §7 |
| Q-09 | `enforcement_outcome` of `PREVENTED`, `REALIZED`, `DEFINITIVE_NO_EFFECT` or `UNKNOWN` on each post-run policy `FAIL`; labels are Ahmed's | §6.3, GD-16 |
| Q-10 | The governance decision engine produces the release verdict through the gate adapter; Alaa owns the comparison, artifact and disposition; override requests and audit are governance's. Thresholds appear as "not evaluated: threshold not configured" in `not_evaluated_rules` until OD-15 is closed | §6.4, GD-22 |
| Q-13 | Governance-owned dashboard actions are review, override request and override decision. Configuring behavior, running evaluations, annotating results and initiating gate evaluations are not governance's; governance provides only the capability check | §7.3, GD-21 |
| Q-14 | Confirmed: the login form and Administrator account and role management are outside the seven screens. Role assignment is an Administrator API operation | GD-21 |
| Q-15 | Governance's position on the values it owns is in §4.5; Mohab and Nour need to agree it | §4.5, GD-20 |

### 9.3 Review of Mohamed's 21 dashboard rows

Reviewed against this contract. The result is a draft for Mohamed to confirm; the dashboard review record stays PENDING until he replies.

| Row | Result | Note |
|---|---|---|
| `OVW-04` | Accepted with a note | "No decision yet" (not evaluated) is a platform state; governance supplies only decision records and "incomplete evaluation" |
| `OVW-06` | Accepted with a note | Governance supplies timestamped decision records; windowing and trend buckets are computed by the platform (Q-04 for Mohab) |
| `APP-10` | Accepted | Applicability comes from configuration: procurement policies apply to the procurement agent, `NOT_APPLICABLE` to RAG (GD-17) |
| `TRD-32` | Accepted | Governance-owned calculation (§5.1) |
| `TRD-33` | Accepted | Approval submission is a governance record (§5.2) |
| `TRD-34` | Accepted | Authoritative status is `PENDING`/`APPROVED`/`DENIED`/`CANCELLED` (§4.5) |
| `TRD-35` | Accepted | Binding checks and the `NOT_REQUIRED` basis (§2.3, §5.3) |
| `TRD-42` | Accepted | Matches the request fields in §4.1 |
| `TRD-43` | Accepted | `check_mode` added so the screen can show real engine versus stub (§4.2); a missing verdict is a technical check error |
| `TRD-62` | Accepted | Per-policy `PASS` / `FAIL` / `NOT_APPLICABLE` / `ERROR` |
| `TRD-70` | Accepted | Review record fields in §7.1, including the decision version reviewed |
| `TRD-71` | Accepted with a change | Audit records gain the `administrator_action` flag (§7.2) |
| `TRD-83` | Accepted | The role service reports raw for `ADMIN`, redacted for every other role (§7.3). Redaction itself is applied by ingestion |
| `RCA-07` | Accepted with a change | Output adds `decision_engine_version` (§6.2) |
| `RCA-08` | Accepted with a change | Output adds `not_evaluated_rules` with reasons (§6.2) |
| `REL-01` | Accepted | Governance produces it (GD-22) |
| `REL-02` | Accepted | Gate reasons are the fired rules (§6.2) |
| `REL-11` | Accepted with a note | Policy id and criticality come from governance; the scenario list comes from Alaa's comparison |
| `REL-16` | Accepted | Same review record, release target |
| `REL-19` | Accepted, conditional | Needs GD-19 confirmed by the plan owner |
| `REL-20` | Accepted | Audit history for a release evaluation (§7.2) |

### 9.4 Draft v1.5 schema review — items 1 and 2

The review of the Trace Schema Draft v1.5 package assigns items 1 and 2 to Mohab and Mohamed together. This is governance's side. The package files themselves were not available to governance, no check has been executed, and the mutations and field names come only from the review text, so nothing is reported as verified. Details and the full disposition table are in [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §9.

| Review item | Governance deliverable | Disposition |
|---|---|---|
| 1. Authorization snapshots against actual source evidence (supplier, calculation, approval, request-to-arguments, policy identities, dispatch-claim ids) | `INV-11`, `INV-12`; contract §4.6; rules EC-01 to EC-11 and cases EM-00 to EM-05 | Specification corrected; awaiting implementation verification. Awaiting named decisions GD-24 and GD-28 (Mohab, Nour) |
| 1. Contradictory evidence cannot establish a verified binding or a verified success | Certification outcomes and the effect on the verdict | Specification corrected; awaiting implementation verification. GD-25 decided on the governance side |
| 1. Dispatch under an unverified authorization | Contract §6.3 | Awaiting a named decision: GD-26 |
| 2. Recovery identity: key, digest, result ownership, request, payload | Contract §4.7; rules RC-01 to RC-05; cases RM-01 to RM-03 and RM-06 | Specification corrected; awaiting implementation verification |
| 2. Valid outcome combinations; uncertain timeout stays `UNKNOWN` | Outcome table, rule RC-06, case RM-04 | Awaiting a named decision: GD-27 (Ahmed reviews; Mohab confirms the value set) |
| 2. One terminal result per invocation; recovery separate and append-only | Rules RC-07, RC-08; case RM-05 | Specification corrected; awaiting implementation verification |

### 9.5 Nour's owner packet 0.14 (commit `479cab0`)

Nour's packet asks for an explicit ACCEPT or AMEND on each governance decision. The full response, with exact replacement wording, the reviewed file hashes, supporting cases and the split between governance-local and joint decisions, is in [response-to-owner-packet-0.14.md](response-to-owner-packet-0.14.md). A follow-up reply to Nour's later requests, written against Trace Schema Draft v1.9, is [response-to-owner-packet-9e6affa.md](response-to-owner-packet-9e6affa.md). In summary of the first reply: OD-03 values accepted as synthetic MVP configuration (31 of 31 boundary cases reproduced offline); OD-04 clauses V01 to V08 accepted with amended wording; OD-02 accepted as the narrower state/tool row; OD-05-MAP translation table proposed for Mohab; the four OD-12 child decisions answered separately; OD-16 accepted; OD-06 milestone defined; GD-26 left to the named plan approver, who is not yet identified. Nothing there is a teammate's acceptance.

---

## 10. Remaining work

| Item | Owner | Blocks |
|---|---|---|
| Mohamed's dated acceptance or amendment of the synthetic configuration (`procurement-policy-set-v0.1.yaml`), recorded with the file hashes | Mohamed | S2-04; Nour updates affected fixtures after it |
| Name of the plan approver for OD-02, OD-06, OD-08, OD-16 and the GD-26 extension | Nour (records it) | Plan-owner acceptance |
| Acknowledgements from Nour, Mohab, Ahmed, Alaa, Malak | each | Contract freeze |
| Canonical value choices (§4.5) | Mohab, Nour | `contracts/governance.py` |
| Evidence resolver port, finding-code registry, dispatch-claim record (GD-24, GD-28) | Mohab, Nour | Consistency verifier and the recovery events |
| Outcome interpretation, `side_effect_state` value set, the timeout conflict with `side_effect_committed` (GD-27) | Ahmed, Mohab | Post-run `enforcement_outcome` |
| Whether an executed dispatch under an unverified authorization fires `DEC-1` (GD-26) | Ahmed, Alaa, plan owner | Decision engine rules |
| Prototype identity mechanism | Mohab | S6-01 |
| Plan-owner confirmation of the role baseline and override scope | plan owner | S6-01 |
| Pydantic models in `contracts/governance.py`, `policies/procurement.yaml`, sample requests and responses | Mohamed | Sprint 2, after the items above |
