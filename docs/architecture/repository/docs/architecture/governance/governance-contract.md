# Governance contract register

| | |
|---|---|
| **Status** | DRAFT v0.2 — Sprint 1, task S1-04. Not frozen. No teammate has reviewed or signed off this document. |
| **Owner** | Mohamed Elnaggar — `packages/governance-engine` |
| **Reviewers** | Nour El-Rouby, Mohab Mohsen, Ahmed Ragab, Alaa Sayed, Malak Sayed |
| **Companion** | [decision-flow.md](decision-flow.md) — the three verdict layers, precedence, invariants, failure behavior |
| **Responds to** | The Mohamed section of the [cross-team handoff checklist](../reference-applications/handoffs.md#mohamed--s1-04-policy-interaction-and-approval-authority) — see §9 |

Source tags: **[P]** approved proposal · **[R]** approved repository architecture or sprint plan · **[N]** Nour's [reference-application contracts](../reference-applications/README.md) revision 0.5, themselves pending team sign-off · **[D]** DECISION proposed by governance, pending review.

Evidence ids (E01–E27) refer to the [application-to-trace evidence matrix](../reference-applications/trace-evidence-contract.md). Decision ids prefixed `GD-` are governance decisions in §8; where one corresponds to an item in the shared [open-decisions register](../reference-applications/open-decisions.md), the OD id is given. This document does not edit that register.

All field names, enum names and ids below are drafts. They become Pydantic models in `packages/contracts` only after review (GD-10). Placeholders in angle brackets are filled by versioned configuration or by the reason-code taxonomy; no threshold, currency or approval level is invented here.

---

## 1. Scope

In scope for Sprint 1 [R, S1-04]: policy evidence requirements, the pre-tool request/response contract, the governance-owned approval boundary, the decision-engine input/output contract, the review/audit/RBAC contract, and the open decisions that block Week 2.

Out of scope until later sprints: policy code, database tables, API endpoints, truth tables and the reason-code taxonomy (Week 2), decision-engine code (Sprint 4), review/audit/RBAC code (Sprint 6).

---

## 2. Stages, applicability and evidence

### 2.1 Workflow stage and tool allowlist

The application keeps a fine-grained agent state; governance sees a coarse **workflow stage**. Tool permission is the intersection of application state and the governance stage policy, and a coarse stage allowance never permits skipping a prerequisite [N]. The application owns the state machine; governance owns the allowlist below.

Stage names are Nour's proposal, awaiting ratification by Mohamed and Mohab [N]. The allowlist is [D] except where noted.

| Stage | Tool proposals permitted | Note |
|---|---|---|
| `PRE_APPROVAL` | `search_policy`, `get_supplier`, `request_approval` [P §R]; `calculate_approval_level` [D] | The proposal lists the first three; adding the read-only calculation tool extends that list and needs explicit team approval (GD-01) |
| `APPROVED` | `create_purchase_order` | The proposal is checked here; dispatch happens after a bound `ALLOW` [N] |
| `PO_CREATION` | none | No new proposal; dispatch proceeds under the existing `ALLOW` binding |
| `COMPLETED` | none | Terminal |

The allowlist lives in versioned configuration (`policies/procurement.yaml`), not in code. Ratifying the stage names and this table is GD-02.

### 2.2 Which policies apply to which proposal

| Proposed tool | `PROC-TOOL-STAGE-01` | `PROC-APPROVAL-01` | `PROC-SUPPLIER-01` |
|---|---|---|---|
| `search_policy` | applies | not applicable | not applicable |
| `get_supplier` | applies | not applicable | not applicable |
| `calculate_approval_level` | applies | not applicable | not applicable |
| `request_approval` | applies | not applicable | not applicable |
| `create_purchase_order` | applies | applies only when approval is required, otherwise `NOT_APPLICABLE` | applies |

Basis: `PROC-APPROVAL-01` and `PROC-SUPPLIER-01` are scoped to `create_purchase_order` [P §R, §R.1 `before_tool`]; every proposed tool is checked against the stage allowlist so early or model-generated proposals are caught at any stage [N]. Every tool proposal goes through the same hook (GD-02). Policy `PROC-TOOL-STAGE-01` also covers a purchase-order proposal made outside `APPROVED`, which is the bypass case.

### 2.3 Evidence and result states per policy

Result states are `PASS`, `FAIL`, `NOT_APPLICABLE` and `ERROR`. The proposal's example traces show only `PASS` and `FAIL` [P §J]; the other two are [D]. `ERROR` represents "could not decide" without pretending it is a violation or a success (`INV-3`).

**`PROC-APPROVAL-01`** — rule: if the purchase amount exceeds the configured threshold, manager-approval evidence must exist before `create_purchase_order` [P §R].

| Aspect | Contract |
|---|---|
| Applies when | The proposal is `create_purchase_order` **and** governance derives that approval is required: `total_amount` is strictly greater than the configured threshold in the same `currency` (the proposal says "exceeds", `amount_gt` [P §R.1]; equality does not trigger) [D] |
| `PASS` | A valid approval exists (see §5.3) |
| `FAIL` | Approval required and none valid: missing, pending, denied, cancelled, bound to a different request revision / amount / currency / supplier / level, or decided after the proposal |
| `NOT_APPLICABLE` | Approval not required. Recorded with the calculation evidence and the basis `NOT_REQUIRED`; no approval id is invented [N] |
| `ERROR` | `total_amount` or `currency` unparseable or unsupported, or threshold configuration missing |
| Evidence | `total_amount`, `currency`, request revision, configured threshold + currency + comparator + policy version, authoritative approval evidence, event order |

**`PROC-TOOL-STAGE-01`** — rule: `PRE_APPROVAL` allows `search_policy`, `get_supplier`, `request_approval` and forbids `create_purchase_order` [P §R].

| Aspect | Contract |
|---|---|
| `PASS` | The proposed tool is on the allowlist of the current stage |
| `FAIL` | It is not (including a purchase-order proposal outside `APPROVED`, or any tool name not on that stage's list) |
| `ERROR` | The stage is unknown or missing, or the allowlist configuration is missing |
| Evidence | Current stage, proposed tool, configured allowlist + version, trace/proposal identity; the response names the stage, tool and violated rule rather than an unexplained boolean [P §R] |

**`PROC-SUPPLIER-01`** — rule: `create_purchase_order` requires `supplier.status = APPROVED` [P §R].

| Aspect | Contract |
|---|---|
| Applies when | The proposal is `create_purchase_order` |
| `PASS` | The supplier snapshot for the **same** `supplier_id` as the proposal has status `APPROVED` |
| `FAIL` | Status is `NOT_APPROVED` or `UNKNOWN`, the supplier was not found, or the snapshot's supplier id differs from the proposal's |
| `NOT_APPLICABLE` | The proposal is not `create_purchase_order` |
| `ERROR` | No supplier evidence, or the lookup itself errored (this is not a verdict on the supplier) |
| Evidence | `supplier_id`, `status`, `record_version`, `directory_version`, source, proposed tool, policy version |

Supplier statuses are `APPROVED` / `NOT_APPROVED` / `UNKNOWN`, and lookup outcomes `FOUND` / `NOT_FOUND` / `ERROR` [N, `get_supplier`]. This closes the supplier-status question from the first draft.

### 2.4 Trust boundary for evidence

A governance check is only as independent as its evidence. Where Nour's contracts and this draft agree, the rule is stated once:

1. **Evidence comes from runtime code, never from model text.** The model cannot set approval or supplier status, state, check verdict, idempotency key or tool result; the runtime injects trusted context separately from model arguments [N, state invariant 3]. This keeps Layer 1 independent of prompt injection [P §Q].
2. **Approval authority is governance-owned.** `request_approval` goes through the governance-owned approval boundary [N]; the check resolves approval status from governance's own approval records (§5), not from a status string in the request. A status the application reports is kept only to record a mismatch.
3. **Governance derives the approval requirement.** It does not trust the application's `approval_required` flag (`INV-10`). The app's `calculate_approval_level` tool delegates to the same governance function (§5.1), so the two cannot disagree [N].
4. **The amount that is checked is the amount of the call being proposed** (the proposal's arguments, as parsed), compared against the request total and the approval evidence; any mismatch is a finding. [D]
5. **Policy version.** [N] has the application supply the policy-set version; [D] governance evaluates against its **active** version and fails closed on any difference, so an agent can never select a weaker policy set (GD-08).

---

## 3. Traceability register

Every input and output has a producer and a consumer — the S1-04 traceability check [R]. "Trust" says how a value must be sourced: **runtime** = deterministic application code, **governance** = authoritative inside governance, **platform** = trace platform, **evaluator** = produced by the reliability engine, **human**.

### 3.1 Layer 1 policy inputs

| Id | Input | Evidence | Producer | Consumer | Trust |
|---|---|---|---|---|---|
| PI-01 | `proposed_tool` | E15 | Nour — tool hook | all three policies | runtime |
| PI-02 | parsed tool arguments (supplier, item, quantity, `total_amount`, `currency`) | E16 | Nour | `PROC-APPROVAL-01`, `PROC-SUPPLIER-01` | runtime |
| PI-03 | `arguments_digest` | E17 | Nour | binding (§4.2) | runtime |
| PI-04 | `workflow_stage` | E10 | Nour — state machine | `PROC-TOOL-STAGE-01` | runtime |
| PI-05 | `request_id`, `request_revision`, request `total_amount` / `currency` | E08 | Nour | `PROC-APPROVAL-01` (consistency), binding | runtime |
| PI-06 | source state revision | E09 | Nour | binding | runtime |
| PI-07 | calculation reference and app-reported `approval_required` | E12 | Nour | diagnostics and mismatch only | runtime, non-authoritative |
| PI-08 | approval-request id / approval id | E13, E14 | Nour (from `request_approval`) | `PROC-APPROVAL-01` → approval service lookup | runtime reference |
| PI-09 | authoritative approval evidence | E14 | governance — `approvals/approval_service.py` | `PROC-APPROVAL-01` | governance |
| PI-10 | supplier snapshot: id, status, record + directory version | E11 | Nour (`get_supplier` result) | `PROC-SUPPLIER-01` | runtime |
| PI-11 | event sequence / ordering | E09, E15 | Mohab — SDK | `PROC-APPROVAL-01` ("approval before the proposal") | platform |
| PI-12 | `trace_id`, `proposal_id` | E15, E17 | Mohab / Nour | all policies, idempotency, audit | platform |
| PI-13 | policy-set version reported by the application | E17 | Nour | compared with the active version (GD-08) | runtime |
| PI-14 | configured threshold + currency + comparator + approval level (versioned) | — | governance — `policies/procurement.yaml` | `PROC-APPROVAL-01`, §5.1 | governance |
| PI-15 | stage → tool allowlist (versioned) | — | governance — `policies/procurement.yaml` | `PROC-TOOL-STAGE-01` | governance |
| PI-16 | eligible supplier status (versioned) | — | governance — `policies/procurement.yaml` | `PROC-SUPPLIER-01` | governance |
| PI-17 | approval validity rule (versioned) | — | governance — `policies/procurement.yaml` | `PROC-APPROVAL-01` (GD-04) | governance |
| PI-18 | active `policy_set_version` | — | governance | all policies, every output | governance |

### 3.2 Layer 1 outputs

| Id | Output | Evidence | Producer | Consumer |
|---|---|---|---|---|
| PO-01 | `verdict` — `ALLOW` / `BLOCK` | E18 | governance | Nour (obeys), Mohab (persists), audit |
| PO-02 | `verdict_basis` — all satisfied / policy violation / evaluation error | E18 | governance | Nour (logging), Malak (display), audit |
| PO-03 | per-policy result: id, version, status, criticality, reason code, message, evidence refs | E18 | governance | Mohab (persist), Malak (Trace Detail), Ahmed (policy evaluator and features), Alaa (gate), Layer 2 |
| PO-04 | `policy_set_version`, per-policy versions | E18 | governance | Mohab, Ahmed, Alaa (provenance) |
| PO-05 | `check_id`, `evaluated_at` | E18 | governance | Mohab (trace linkage), audit |
| PO-06 | `binding` (§4.2) | E17, E18, E20 | governance | Nour (verify and claim), Mohab (linkage) |

PO-03 is what feeds the proposal's policy feature group — policy failure count, critical-policy flag, tool-stage allowlist verdict, supplier eligibility [P §L.2] — so Ahmed's feature pipeline consumes it unchanged.

### 3.3 Layer 2 decision inputs

| Id | Input | Producer | Consumer | Note |
|---|---|---|---|---|
| DI-01 | policy findings (Layer 1 records, plus any post-run policy evaluation); `NOT_APPLICABLE` for non-procurement traces | governance | decision engine | |
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
| DO-02 | evaluation status and the list of missing evidence | governance | Malak ("not evaluated" / "evaluator failed" / "not applicable" kept distinct from `PASS` [N]), Alaa |
| DO-03 | ordered list of fired rules (`DEC-n`) and reason codes | governance | Malak (Failure & RCA screen), reports |
| DO-04 | evidence references and evidence-run ids | governance | Malak, audit, reproducibility |
| DO-05 | `decision_config_version` | governance | Alaa, Ahmed (provenance) |
| DO-06 | `decision_id`, target, `created_at` | governance | Mohab (persist), review (reference), audit |

---

## 4. Pre-tool check — draft interface

Models will live in `packages/contracts/.../governance.py` (GD-10). The service is `trustops_governance.policy.engine`. The HTTP route in `apps/api` is only an adapter (GD-05). There is no governance microservice. Governance does not import application code or reliability implementation classes [R].

### 4.1 Request fields [D]

| Field | Notes |
|---|---|
| `trace_id`, `proposal_id` | Together the idempotency key |
| `request_id`, `request_revision` | From the immutable request snapshot |
| `state_revision` | Revision of the state that produced the proposal |
| `workflow_stage` | `PRE_APPROVAL` / `APPROVED` / `PO_CREATION` / `COMPLETED` |
| `proposed_tool` | One of the five tool names [P §N.1] |
| `tool_arguments`, `arguments_digest` | Parsed arguments (`total_amount` as a decimal string, never a binary float) and their digest |
| `supplier` | Snapshot: `supplier_id`, `status`, `record_version`, `directory_version` |
| `approval` | `approval_request_id`, `approval_id` (both nullable), optional `reported_status` for mismatch diagnostics only |
| `calculation_ref`, `reported_approval_required` | Diagnostics and mismatch only |
| `policy_set_version` | The version the application's evidence was derived under (GD-08) |
| `evidence_event_refs` | Event ids supporting reconstruction |

Deliberately **not** accepted as authority: any approval status string, any verdict, any choice of policy version.

### 4.2 Response fields [D]

| Field | Notes |
|---|---|
| `check_id`, `evaluated_at` | |
| `verdict` | `ALLOW` / `BLOCK` |
| `verdict_basis` | `ALL_POLICIES_SATISFIED`, `POLICY_VIOLATION`, `EVALUATION_ERROR` |
| `policy_set_version` | The active version that actually ran |
| `results` | One entry per applicable policy: `policy_id`, `policy_version`, `status`, `criticality`, `reason_code`, `message`, `evidence` (list of `{field, observed, expected, event_ref}`) |
| `binding` | `check_id`, `proposal_id`, `request_revision`, `state_revision`, `arguments_digest`, supplier snapshot reference, approval evidence reference or null, `policy_set_version` |

`criticality`: the proposal shows only `critical` [P §R.1] and refers to "critical" failures [P §K.2]; the full value set is open. All three MVP policies are critical. [D]

**Meaning of `ALLOW`** [N, authorization binding]: it authorizes the single `APPROVED → PO_CREATION` transition and the initial dispatch for exactly the bound snapshot. The runtime atomically verifies that the current snapshot still equals the `binding`, records the authorized transition and claims the dispatch once. Any other change to the bound inputs, any intervening transition, or a second use of the same authorization needs a fresh check. A model cannot invoke this path. Governance's part is the binding fields and idempotent replay (a replayed check returns the same result); the atomic claim is the runtime's (GD-07).

### 4.3 Illustrative case — approval bypass

Values are illustrative; placeholders are filled by configuration or the Week 2 taxonomy.

```json
{
  "request": {
    "trace_id": "tr_proc_102",
    "proposal_id": "<proposal id>",
    "request_id": "<request id>",
    "request_revision": "<revision>",
    "state_revision": "<revision>",
    "workflow_stage": "PRE_APPROVAL",
    "proposed_tool": "create_purchase_order",
    "tool_arguments": { "supplier_id": "<supplier>", "quantity": 40, "total_amount": "32000.00", "currency": "<supported code>" },
    "arguments_digest": "<digest>",
    "supplier": { "supplier_id": "<supplier>", "status": "APPROVED", "record_version": "<v>", "directory_version": "<v>" },
    "approval": { "approval_request_id": null, "approval_id": null },
    "policy_set_version": "<version the app used>"
  },
  "response": {
    "check_id": "<generated>",
    "verdict": "BLOCK",
    "verdict_basis": "POLICY_VIOLATION",
    "policy_set_version": "<active version>",
    "results": [
      { "policy_id": "PROC-APPROVAL-01", "status": "FAIL", "criticality": "critical",
        "reason_code": "<week-2 taxonomy>",
        "evidence": [ { "field": "total_amount", "observed": "32000.00", "expected": "valid approval when amount > <configured threshold> <currency>" } ] },
      { "policy_id": "PROC-TOOL-STAGE-01", "status": "FAIL", "criticality": "critical",
        "reason_code": "<week-2 taxonomy>",
        "evidence": [ { "field": "proposed_tool", "observed": "create_purchase_order", "expected": "one of <PRE_APPROVAL allowlist>" } ] },
      { "policy_id": "PROC-SUPPLIER-01", "status": "PASS", "criticality": "critical",
        "evidence": [ { "field": "supplier.status", "observed": "APPROVED", "expected": "APPROVED" } ] }
    ]
  }
}
```

### 4.4 Outcome by situation

| Situation | `PROC-APPROVAL-01` | `PROC-TOOL-STAGE-01` | `PROC-SUPPLIER-01` | Verdict | Basis |
|---|---|---|---|---|---|
| Valid approved path, stage `APPROVED` | `PASS` | `PASS` | `PASS` | `ALLOW` | all satisfied |
| Approval not required, stage `APPROVED` | `NOT_APPLICABLE` | `PASS` | `PASS` | `ALLOW` | all satisfied |
| Approval bypass, stage `PRE_APPROVAL` | `FAIL` | `FAIL` | `PASS` | `BLOCK` | policy violation |
| Approval bound to a different request revision | `FAIL` | `PASS` | `PASS` | `BLOCK` | policy violation |
| Supplier `NOT_APPROVED`, forced proposal | `PASS` | `PASS` | `FAIL` | `BLOCK` | policy violation |
| Supplier evidence missing | `PASS` | `PASS` | `ERROR` | `BLOCK` | evaluation error |
| Reported policy version differs from the active one | — | — | — | `BLOCK` | evaluation error |

---

## 5. Governance-owned approval boundary

[N] places approvals and policy truth in governance: `request_approval` is a wrapper around a governance-owned boundary, and `calculate_approval_level` delegates to governance-owned calculation. This section is governance's side of that boundary. It is a contract proposal [D]; implementation is Sprint 2 (`approvals/approval_service.py`, `approvals/workflow.py` [R]).

### 5.1 Approval requirement calculation

One pure function, used by both the application's `calculate_approval_level` wrapper and `PROC-APPROVAL-01`, so the two cannot disagree.

| | Contract |
|---|---|
| Input | `total_amount` (decimal string), `currency`, active policy-set version |
| Output | `required` (true / false / `UNRESOLVED`), `approval_level` (null iff not required), `policy_id`, `policy_version`, `basis` (amount, currency, configured threshold, threshold currency, comparator, rule reference) |
| Rules | Strict `>` [P §R.1]; unsupported currency, missing threshold or conflicting versions return `UNRESOLVED`, never `false`; no threshold or currency is hard-coded |

The example amount in the proposal (§R.1) is an illustration, not a default; the threshold and currencies come from `policies/procurement.yaml` (GD-03).

### 5.2 Approval records

Governance stores approval requests and decisions as append-only records; "current status" is derived from them (`INV-6`).

| Operation | Contract |
|---|---|
| Create request | Binds `request_id`, `request_revision`, `calculation_ref`, supplier, `total_amount`, `currency`, required level. Idempotent on the runtime-issued key: same key + same payload returns the same approval-request id; same key + changed payload is `IDEMPOTENCY_CONFLICT` [N] |
| Record decision | `PENDING` / `APPROVED` / `DENIED` / `CANCELLED`, outside model control. In the MVP decisions come from scenario fixtures or a trusted runtime input; **no approval endpoint, reviewer UI, notification transport or IAM** is created [N] |
| Observe | Returns the authoritative status for an approval-request id |
| Evidence returned | Approval id, approval-request id, request revision, supplier, amount, currency, level, approving actor reference, decision timestamp, policy version, source reference [N, `ApprovalEvidence`] |

The three prototype roles (Engineer, Reviewer, Admin) are not approvers. Manager approval in the MVP is synthetic and fixture-driven, which keeps purchasing approval separate from human trace review and from RBAC (§7).

### 5.3 What counts as a valid approval

`PROC-APPROVAL-01` is satisfied only when all of the following hold [D]:

1. The approval record exists and its status is `APPROVED`.
2. It is bound to the proposal's request revision, supplier, `total_amount`, `currency` and required level.
3. It was decided before the proposal event (event order).
4. The validity rule in the policy set (PI-17) holds.

Expiry and revocation are open in [N]; the absence of a configured validity rule is not treated as proof that an old approval is valid. Proposed MVP rule: an approval is valid while its bound request revision is current and its record has not moved to `DENIED` or `CANCELLED`; there is no time-based expiry. The rule is written explicitly in the versioned configuration rather than left implicit (GD-04).

---

## 6. Decision engine — draft interface

### 6.1 Input [D]

A decision input names a target (`trace` or `release_evaluation` with its id) and carries an evidence bundle made of DI-01 to DI-09. The decision configuration (thresholds and version) is loaded by the engine, not supplied by the caller.

Whether the engine receives **raw metrics and compares them to configured thresholds**, or receives **precomputed flags** such as "borderline" or "severe", is open (GD-12). Proposed default: raw metrics in, thresholds in `config/decision_thresholds.yaml`, so every threshold lives in one versioned place and the decision path can show the observed value against the threshold.

### 6.2 Output [D]

| Field | Notes |
|---|---|
| `decision_id`, `target`, `created_at` | |
| `decision` | `PASS` / `REVIEW` / `BLOCK`, absent when evaluation is incomplete (GD-13) |
| `evaluation_status` | Complete, or incomplete with the missing evidence listed |
| `fired_rules` | Ordered `DEC-n` ids with reason codes |
| `evidence_refs`, `evidence_run_ids` | References into traces, findings and evaluation runs |
| `decision_config_version` | |

A re-run creates a new record and leaves earlier decisions untouched (`INV-6`).

---

## 7. Human review, audit and RBAC register

### 7.1 Human review record [P §R.2, FR-13; field names D]

| Field | Producer | Consumer | Notes |
|---|---|---|---|
| `review_id` | governance | audit | |
| `target_type`, `target_id` | Reviewer via API | Malak | Trace or release evaluation |
| `verdict` | Reviewer | Malak, Alaa | `ACCEPT` / `REVIEW` / `BLOCK` |
| `rationale` | Reviewer | Malak, audit | Proposed: required and non-empty for every verdict |
| `reviewer_id` | identity context (Mohab) | audit | Attributed server-side, never taken from the request body |
| `referenced_decision_id` and its config version | governance | Malak | Records which machine decision the person was looking at |
| `created_at` | governance | audit, Malak | |

A new review is a new record. The history query returns all of them; the current review state is derived, not stored.

### 7.2 Audit record [P §H Auditability, FR-18; field names D]

| Field | Notes |
|---|---|
| `audit_id`, `occurred_at` | |
| `actor_id`, `actor_role` | System actors use an explicit id such as `system:policy-engine` |
| `action` | From the catalogue below |
| `target_type`, `target_id` | |
| `applicable_version` | Policy-set, decision-config or other version in force |
| `rationale` | Where the action carries one |
| `evidence_refs`, `metadata` | |

No update or delete operation exists on the audit repository interface (`INV-6`). Database-level protection is added only if it fits the shared PostgreSQL design.

Proposed audit action catalogue [D]:

| Action | Written when |
|---|---|
| `POLICY_SET_CREATED`, `POLICY_SET_ACTIVATED` | An Admin creates or activates a policy configuration |
| `POLICY_CHECK_COMPLETED` | A pre-tool check finishes — one row per check, system actor, referencing `check_id` and the verdict |
| `APPROVAL_REQUESTED`, `APPROVAL_DECIDED` | An approval request is created or a decision is recorded |
| `DECISION_RECORDED` | A reliability decision is stored |
| `REVIEW_SUBMITTED` | A reviewer appends a verdict |
| `ROLE_ASSIGNED` | An Admin assigns a role |
| `ACCESS_DENIED` | A sensitive action is rejected by RBAC |

Policy checks are stored as their own append-only evidence (PO-03) and also get an audit row so there is one chronological trail. The audit row and the record it describes should be written in the same database transaction (GD-11).

### 7.3 Roles and permission matrix [P FR-19; matrix D]

The proposal fixes the three roles and says permissions gate sensitive actions; the matrix is a proposal. Backend checks are authoritative — hiding a frontend control is not enforcement.

| Capability | Engineer | Reviewer | Admin |
|---|:---:|:---:|:---:|
| View permitted / redacted diagnostic evidence | yes | yes | yes |
| Trigger permitted evaluation or check operations | yes | yes | yes |
| Submit human review | no | yes | yes |
| View review and audit history | to be agreed (GD-15) | yes | yes |
| Create or activate versioned policy configuration | no | no | yes |
| Assign prototype roles | no | no | yes |
| View raw (unredacted) trace content | to be agreed (GD-15) | to be agreed (GD-15) | yes |

Raw trace access is role-gated [P §H Security]; which roles see raw versus redacted content is recorded as an open decision rather than assumed. The identity mechanism is a lightweight prototype — no SSO, OAuth or enterprise IAM [P §E; R S6-01] — and which mechanism is open (GD-14).

---

## 8. Open decisions

"Maps to" gives the matching item in the shared [open-decisions register](../reference-applications/open-decisions.md). "Proposed default" is a recommendation, not an agreement.

| Id | Maps to | Decision needed | Proposed default [D] | Resolve with | Needed by |
|---|---|---|---|---|---|
| GD-01 | OD-02 / D3 | Whether `calculate_approval_level` is allowed in `PRE_APPROVAL`. The proposal lists three tools; the approved tool set has a fourth that runs before approval | Allow it as a read-only tool, as an explicit, documented extension of the proposal's list, without weakening the purchase-order restriction | Nour, plan owner | Week 2, before freeze |
| GD-02 | — | Ratify the stage names and the stage → allowlist table (§2.1), and that every tool proposal goes through the pre-tool hook | Adopt Nour's four stage names; per-stage allowlists in versioned configuration | Nour, Mohab (E10) | Week 2 |
| GD-03 | OD-03 | Approval rule values: threshold, supported currencies, approval levels, equality semantics, and where the numbers come from | Strict `>` per the proposal; values only in `policies/procurement.yaml`; text/config disagreement halts rather than being reconciled by the model [N] | Nour (policy text), Mohamed (configuration) | Week 2 |
| GD-04 | OD-04 | Approval validity: binding fields, denial, expiry, revocation, stale evidence, trusted resume | §5.3 rule list; no time expiry in the MVP, stated explicitly in configuration; resume authority is the trusted runtime continuation, with trace continuity defined by Mohab | Mohab, Nour | Week 2 |
| GD-05 | OD-05 | Pre-tool transport and object mapping: E17/E18/E19 to `contracts/governance.py`; verdict and error types; router home | New thin router `routers/policy_checks.py` (the approved router list has none for this); models in `packages/contracts` | Mohab | Week 2 |
| GD-06 | OD-06 / D4 | Staging of the S2-01 stub, S2-04 real policies and S3-03 integration | Sprint 2: real pure policy functions and an in-process service behind the agreed interface, replacing the stub as soon as callable, stub labelled until then; Sprint 3: persistence and end-to-end seeded scenarios | Mohab, Nour, plan owner | Week 2 |
| GD-07 | OD-12 | Binding representation and atomic claim | `binding` object in §4.2; runtime verifies equality and claims dispatch once, linked to `check_id`; governance replays idempotently | Nour, Mohab | Week 2 |
| GD-08 | — | Who selects the policy version | Application reports the version its evidence used; governance evaluates against its active version and fails closed on a difference | Nour, Mohab | Week 2 |
| GD-09 | — | Caller's fail-closed obligation | No verdict, timeout or technical error means no dispatch; recorded as a check error with a `NOT_EXECUTED` suppression event, never as a policy `FAIL` or `ALLOW`. Already stated in [N]; needs ratification and a test | Nour, Mohab | Week 2 |
| GD-10 | — | Home and ownership of governance contract models | Mohamed authors `governance.py` and governance enums in `packages/contracts`; Mohab reviews | Mohab | Week 2 |
| GD-11 | — | Transaction boundary across the platform unit of work and governance repositories | One unit of work spans both, supplied by `apps/api`, so a check and its audit row commit atomically | Mohab | Week 2–3 |
| GD-12 | OD-15 (thresholds) | Decision inputs: raw metrics vs precomputed flags; metric names; definitions of "disagreement" and "borderline"; which security findings are critical | Raw metrics in, thresholds in `config/decision_thresholds.yaml`; Ahmed marks criticality per attack category | Ahmed, Alaa | Week 2 |
| GD-13 | — | How an incomplete evaluation is stored and treated by the gate, including a critical policy `ERROR` | `decision` absent + status "incomplete" + missing-evidence list; the gate treats it as non-approving | Alaa, Malak | Week 2 |
| GD-14 | — | Prototype identity mechanism and who supplies it | Decide with Mohab; keep it a lightweight prototype mechanism | Mohab | Week 2 (built in Sprint 6) |
| GD-15 | — | Raw vs redacted content per role; Engineer access to review and audit history | Record the agreed matrix in §7.3 | Whole team | Before Sprint 6 |
| GD-16 | OD-09 | How attempted, prevented and realized violations are labelled | Policy `FAIL` means attempted; prevented vs realized comes from dispatch evidence; `DEC-1` fires either way | Ahmed | Week 2 |
| GD-17 | OD-16 / D5 | Procurement-only applicability | RAG has no pre-tool check; its policy evidence is `NOT_APPLICABLE`, not `PASS`; no RAG policy exists in the approved scope | Nour, plan owner | Week 2 |

---

## 9. Response to the S1-01 handoff checklist

The [handoff checklist](../reference-applications/handoffs.md#mohamed--s1-04-policy-interaction-and-approval-authority) lists what the reference-application contracts need back from governance. Status reflects this draft only; nothing here has been reviewed by a teammate.

| Required back | Status in this draft | Where |
|---|---|---|
| Versioned truth tables for the three policies, including below / equal / above threshold | **Not done.** Result states and the strict-`>` rule are defined; the truth tables and fixtures are Week 2 | §2.3, §10 |
| D3 resolution, state/stage mapping, approved no-approval-required branch | **Proposed**: allow the read-only calculation tool; adopt the four stage names; `NOT_REQUIRED` recorded as `NOT_APPLICABLE` with the calculation evidence | §2.1, §2.3, GD-01, GD-02 |
| Canonical synchronous `ALLOW`/`BLOCK` interface plus technical-error and missing-verdict semantics | **Drafted**; the canonical mapping depends on Mohab | §4, decision-flow §5.1, GD-05, GD-09 |
| Approval evidence source, validity, expiry, revocation, stale handling, trusted resumption | **Proposed**; expiry and resume details remain open | §5, GD-04 |
| Binding of `ALLOW` to proposal, state and arguments; check-to-dispatch mutation handling | **Proposed** binding object and split of responsibility; atomic claim stays with the runtime | §4.2, GD-07 |
| D4 integration-date reconciliation and D5 applicability | **Proposed** | GD-06, GD-17 |
| Supplier-breach fixture for SC-03, boundary-test scope, confirmation that the real engine suppresses PO dispatch | **Not done.** Expected shape: supplier `NOT_APPROVED` plus a forced purchase-order proposal gives `PROC-SUPPLIER-01` `FAIL` and `BLOCK` (§4.4). The fixture handoff belongs to S3-03 | §4.4 |
| Written policy-evidence sign-off | **Not given.** This draft is not a sign-off. It needs Mohamed's explicit acceptance after the reviewers respond, naming the revision | — |

---

## 10. Hand-off to Week 2

Once the Week 2 decisions above are answered:

- Policy truth tables for all three policies, including boundary and error cases, with unit-test matrices written before any engine code.
- `policies/procurement.yaml` draft: threshold, currency set, comparator, approval levels, stage allowlists, eligible supplier status, approval validity rule, criticality, versioning.
- Reason-code taxonomy.
- Pydantic models in `contracts/governance.py` and the initial policy-version model.
- Sample requests and responses for Nour, Mohab and Malak: one success, one failure and one missing-evidence case each.
