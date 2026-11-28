# ADR — Application execution budgets, retry accounting and purchasing recovery

**2026-11-02 scoped confirmation:** [OD-APP-OBS-01](../architecture/reference-applications/open-decisions.md#approval-observation-confirmation) records Mohamed/Mohab confirmation, reported by the user, of trusted read-only observation of the existing approval request. Observation is distinct from retrying the original submission. Numeric budgets, initial-submission replay policy and implementation verification remain proposed/open.

| Item | Value |
|---|---|
| Status / revision | **PROPOSED — engineering review candidate, revision 0.1, 2026-11-01; NOT FROZEN** |
| Owner | Nour El-Rouby — application orchestration and tool wrappers |
| Required engineering reviewers | Mohab: state/persistence/contracts; Mohamed: authorization/approval/recovery; Alaa: reproducibility/quota accounting; Ahmed: failure/evaluation semantics |
| Business stakeholders | Purchasing process owner and Finance/Treasury/payment integration owners are **unassigned**; no business authorization is inferred |
| Decision scope | Two reference apps, their existing five Procurement tools, pre-tool boundary and original-effect read-only recovery |
| Related documents | [Generation ADR](reference-application-orchestration-and-llm.md), [tool contracts](../architecture/reference-applications/procurement-tool-contracts.md), [state contract](../architecture/reference-applications/procurement-state-contract.md), [RAG contract](../architecture/reference-applications/rag-contract.md) |
| Validation status | Documentation, mathematical/accounting examples and schema checks only; no provider, database, payment or production tool execution |

All values below are **proposed configurable engineering limits**. They are not existing business policies, measured optima, SLAs, account quotas or stakeholder approvals. The compatibility mapping supersedes older retry timing where explicitly stated. Actual implementation and integration tests remain Sprint 2 work.

## 1. Context and problem

The Procurement Agent uses an explicit state machine, trusted approval evidence and a synchronous pre-tool check before a synthetic PO side effect. RAG uses one application-owned retrieval/generation pipeline. Both must stop predictably when calls or time run out, without treating a timeout as proof that a remote action did not happen.

Existing generation profiles already propose Procurement 8 logical generation operations/12 attempt debits and RAG 1 generation operation/2 attempts, with 60/90-second attempt caps. This ADR preserves those limits and adds precise hierarchy, lifetime accounting, tool/check limits, durable resume rules and recovery boundaries. RAG retains its 15-second embedding stage, 5-second SQL search and 120-second total query limit.

No model output can raise a budget, reset counters, select a new idempotency key, assert an approval or authorize a recovery write. No new queue, distributed workflow service, multi-agent system or payment integration is introduced. Shared budget/continuation representation remains Mohab’s contract responsibility; policy truth and approval authority remain Mohamed’s.

## 2. Decisions and terminology

| Term | Enforceable meaning |
|---|---|
| Root workflow | One trusted business request lifecycle, including revisions, segments, retries and linked traces; runtime-owned identity |
| Execution segment | One admitted foreground interaction; waiting for human approval ends it |
| Logical operation | One intended generation, tool, check, embedding or preflight operation; not one HTTP request |
| Attempt-budget debit | Capacity atomically charged immediately before an I/O admission/dispatch claim; may conservatively remain spent after a crash even if send cannot be proved |
| Actual dispatch/start | Separately observed I/O/tool-start evidence; never fabricated merely because capacity was charged |
| Retry | Another attempt for the same logical operation under an explicitly eligible retry policy |
| Replay/resume | A new caller/continuation delivery referring to prior work; it does not create new capacity or permission |
| Recovery | Read-only reconciliation of an original uncertain effect; not a purchasing retry or a new transaction |
| Effect state | NOT_APPLICABLE, NONE_CONFIRMED, COMMITTED_CONFIRMED or UNKNOWN, supported by evidence |

**Authoritative configuration:** `execution-budget-v1-proposed`. Valid values are finite positive integer caps for enabled operations; zero is allowed only for explicitly disabled capabilities. No null/unlimited timeout, negative counter, boolean-as-integer limit, or silent SDK default may disable enforcement. Nour owns the app profile; cap changes require a versioned reviewed configuration, with Mohamed/Mohab acceptance when transaction safety changes and Alaa acceptance for workload/experiment changes.

The table values are both the recommended starting defaults and proposed hard admission ceilings for this profile. Deployment overrides may lower a ceiling; raising it requires a new reviewed profile revision. Effective limits are the minimum of profile ceilings, deployment overrides and remaining ancestor allowances. Reaching a ceiling blocks the next admission; it is not merely a warning threshold.

## 3. Execution-budget configuration table

| Dimension | Procurement proposed limit | RAG proposed limit | Owner / enforcement boundary |
|---|---:|---:|---|
| Logical generation operations per root | 8 | 1 | Runtime admission; optional final phrasing remains disabled by default |
| Generation attempt-budget debits per root | 12 | 2 | Provider wrapper; failures/timeouts/retries consume capacity |
| Generation attempts per logical operation | 2 total | 2 total | Initial + at most one eligible retry |
| Model attempt timeout | 60 s | 90 s | Clamped to every remaining parent deadline |
| Token preflights per root | 8, one per logical generation operation | 1 | Separate provider HTTP accounting; no retry |
| Token preflight timeout | 10 s | 10 s | Within parent active deadline |
| Embedding operations / attempt debits | 0 for the mock policy lookup | 1 / 2 | RAG query wrapper; indexing is a separate offline workload |
| Query embedding stage / attempt cap | Not applicable | 15 s / 10 s | Stage deadline wins over two attempt caps |
| SQL searches / timeout | App/tool-specific below | 1 / 5 s | No automatic refill/query retry |
| Logical model-visible tool operations | 8 | 0 | Runtime operation ledger |
| Tool attempt-budget debits | 12 total | 0 | Per-tool retry policy also applies |
| Tool proposals, including rejected proposals | 8 | 0 | Capture/admission limit; do not loop around rejection |
| Pre-tool checks / attempt debits | 12 / 12; one attempt per check | 0 | Fresh bound check before each business-tool attempt; rejected proposals also consume checks when reached |
| Foreground segment deadline | 300 s | 120 s for the whole query | Supervisor and adapter parent deadlines |
| Cumulative active-time pool per root | 600 s | 120 s | No reset through revision/resume/restart |
| Maximum segment starts | 3: initial + at most 2 trusted continuations | 1 | A replayed segment returns existing status rather than charging a new segment |
| Native PO creation dispatch claims | 1 per root and business request; no refill for a new revision/key | 0 | Atomic local dispatch claim; no recovery redispatch |
| Budget-tree depth | Root=0, deepest allowed=4 | Same | Root → segment → stage → logical operation → attempt |
| Client-owned concurrent attempts per run | 1 | 1 | Sequential MVP; no parallel fan-out enabled |
| Cleanup observation window | Up to 2 s within remaining parent time | Same | No deadline extension or new business/model/recovery I/O; no remote-cancellation guarantee |

Provider request accounting is explicit: Procurement generation/preflight requests are bounded above by 12 + 8 = **20 admitted request attempts**; RAG generation/embedding/preflight requests by 2 + 2 + 1 = **5**. These are upper bounds, not expected usage or quota entitlements. Actual starts may be lower than charged admissions. Pre-tool and database calls are counted separately, not hidden inside provider totals. Aggregate quotas across different root workflows still need account-level workload planning; one run’s limits are not global rate limiting.

### Per-tool and internal-operation limits

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


Operation/stage deadlines include attempt time and retry waits; two attempts do not guarantee two full timeout windows. Underlying calls cannot reset the parent timer. Policy calls use one attempt by default, even if the underlying service is read-only: a check failure suppresses the proposed tool rather than initiating an invisible authorization loop.

A transient business-tool read retry requires a fresh bound pre-tool check before its next attempt, under the same proposal/logical operation and remaining check pool. Check calls consume their separate counters and time, not an extra tool proposal or business-tool attempt. A rejected proposal can spend a check without spending a tool attempt; therefore the 12-attempt tool allowance is an upper bound, not guaranteed usable capacity. A missing/error/BLOCK verdict ends that operation without a policy retry or dispatch. This stricter retry-to-check binding requires Mohamed/Mohab acceptance.

### Recovery-only allowance

Reserve an explicitly separate original-effect reconciliation allowance when admitting the root profile: **2 trusted recovery sessions**, **5 s per session**, **10 s cumulative active time**, at most **2 lookup attempts per session / 4 total**, each at most **2 s**. This allowance cannot fund model calls, a new approval request or a purchase dispatch. It remains available after business-work exhaustion only for a trusted, authorized original-effect lookup. It is never reset by reopening an incident or starting another trace. Exhaustion leaves the effect held for manual review; expanding it requires a new recorded agreement, not a model decision.

PENDING/missing ledger data is not a transient error inviting a poll loop. A subsequent observation requires one of the bounded trusted sessions. The allowance is a proposed design, subject to Mohamed/Mohab/Nour acceptance under OD-12. No durable ledger or notification workflow is claimed to exist.

Recovery session starts, attempt debits and active-time leases use the same durable reservation and conservative crash-charging rules as foreground work. A restart never replenishes the separate recovery pool.

## 4. Hierarchical deadlines, reservations and restart behavior

For a child attempt, compute:

`effective_timeout = min(configured_attempt_timeout, logical_operation_remaining, stage_remaining, segment_remaining, reserved_root_time_remaining)`

All quantities must be positive. Recompute after preflight, queue/wait time, policy calls and retry delay. Connect/read/SDK timeouts are subordinate transport controls, not independent extra time. Reject before I/O if no capacity remains. Admission, counters, a current fencing token and the pending dispatch claim are checked together through the agreed runtime ledger contract.

Use a monotonic clock within a live process. UTC timestamps are for audit/correlation, not arithmetic that trusts adjustable wall time. Never serialize a process’s raw monotonic deadline as a valid deadline on another host or after restart. Pass a decreasing remaining-time allowance, validate it against the authoritative root lease, and reconstruct local deadlines at the receiver without granting a fresh full interval.

At segment start, reserve an active-time allotment from the root pool, at most 300 s for Procurement and the remaining pool. Measure segment elapsed time once, including retry sleeps and internal processing. On an orderly durable close, return only the unspent time whose release is confirmed. On a crash or uncertain lease close, conservatively charge the reserved allotment until an authorized reconciliation establishes the facts; do not refund it automatically. A resumed segment consumes a segment-start slot and remaining root capacity. Human-approval waiting does not burn active execution time, but no new model loop runs while waiting.

The 600-second Procurement limit is cumulative active execution, not a calendar approval-validity period. Calendar expiry/abandonment of dormant requests and approval validity remain joint business/policy decisions; no expiry duration is invented. Persist dormant status without a worker/poll loop, and block purchasing continuation when current approval validity cannot be established. No unlimited active workflow is authorized by leaving calendar expiry open.

Logical/attempt counters survive request revisions and linked approval continuations. A revised amount or supplier invalidates authorization but does not refill budgets. A genuinely new business request can obtain a new root only through the trusted intake/admission rule; issuing new trace IDs or keys for the same unresolved transaction is not a new request. Cross-request business duplicate detection is not magically solved by this local budget ledger.

Persist the root/profile identity, active allotment lease, counters, operation/attempt records, fence and continuation checkpoint. If persistence is unavailable or an in-memory ledger was lost, **fail closed** for dispatch/resume; no fabricated fresh counters. Mohab chooses storage representation within the existing platform; this contract adds no database table or endpoint on his behalf.

## 5. Retry accounting, concurrency and partial failures

### Accounting rules

1. Validate caller input before admission. Invalid proposals consume the proposal limit, but do not fabricate model/tool attempt starts.
2. Atomically admit a logical operation once and charge its logical counter. Deduplicate a repeated operation identity; an accepted operation is not re-created under a new ID to retry.
3. Immediately before each send/dispatch, reserve its attempt capacity and claim ownership. Spent attempt capacity is not refunded after timeout, error, cancellation or ambiguous restart. A rolled-back admission transaction that never committed grants no dispatch permission.
4. Record actual I/O start separately. An admission that crashed before a proven send remains conservatively charged; this does not justify logging a tool execution that was never observed.
5. A retry consumes another attempt under the same logical operation and all applicable root limits. Model/schema repair is not a transport retry and is disabled. Do not retry at both SDK and application layers; disable SDK retries or prove every internal attempt is governed by the same ledger.
6. Business-negative results—NOT_FOUND, PENDING, DENIED, UNRESOLVED, BLOCK—and invalid arguments/citations are not transient faults. They do not trigger automatic retry.
7. Same-key writes require an accepted server/ledger idempotency contract, not merely an `Idempotency-Key` header or a `retryable=true` diagnostic flag. The more restrictive tool/business rule wins over HTTP classification.

### Backoff and error classification

For retry number `r=1` for the first retry, set `cap_r = min(10 s, 1 s * 2^(r-1))` and **equal-jitter** delay `cap_r/2 + Uniform(0, cap_r/2)`. Default two-attempt operations therefore have one delay in [0.5,1] seconds. Exponential behavior is defined for reviewed higher-attempt profiles; the default does not authorize them.

Parse Retry-After as nonnegative seconds or HTTP-date [E2]. When valid, wait at least `max(jitter_delay, retry_after_delay)`; do not shorten a server minimum to the local cap. If required wait exceeds 10 s or leaves no parent time, stop with RETRY_AFTER_EXCEEDS_BUDGET rather than retry early. Malformed Retry-After is recorded and uses the local delay only for otherwise eligible failures.

Eligible failures for **side-effect-free generation and reads**: transient connection/timeout failures and HTTP 408/429/500/502/503/504 under the adapter’s reviewed mapping, with no accepted result and remaining budgets. Authentication/permission, invalid model/schema/configuration, payload/semantic validation, refusal/safety block, budget/lease conflicts and idempotency mismatches are not auto-retryable. A 5xx or transport timeout from a write does not establish whether it committed [E1].

### Concurrent admission and partial failure

The MVP rejects parallel fan-out; client-owned concurrency is 1 per run. Two simultaneous continuations for the same root compete for one fenced segment/operation lease; only the atomic winner may perform I/O. A stale owner cannot dispatch after its lease is superseded. A database transaction cannot atomically include a remote external effect: use durable intent + local claim before I/O and separate outcome observation, without promising external exactly-once execution.

If a future reviewed profile enables parallel reads, all branches reserve from the same root counters; never clone a full budget into each child. Counters sum work across branches, while root active time measures elapsed foreground wall time once, not the sum of overlapping child durations. A failed required branch cancels unfinished siblings and prevents answer completion; completed read evidence may be retained, and any confirmed/uncertain effect remains explicitly visible. Parallel financial writes remain disabled.

## 6. Deterministic exhaustion, cancellation and error precedence

On a depleted count/deadline: reject new admissions, stop the model/tool loop, fence abandoned attempts, request cancellation of owned local work and preserve a checkpoint. The cleanup observation ceiling is `min(2 s, remaining current parent deadline)`; it never extends business or recovery time. At an already expired deadline, request cancellation/fence and return through the supervisor without a new waiting allowance. Use any remaining cleanup time only to finalize already-owned resources and record diagnostics. It grants no new model call, policy retry, purchase or read-only recovery. If cancellation does not finish, quarantine the worker/lease and return control through the supervising boundary rather than waiting indefinitely; no new execution may reuse its write claim. Durable pre-dispatch intent must allow later reconstruction even if a final checkpoint write fails.

A count cap blocks the next operation/attempt requiring that capacity; it does not discard the valid result of the final admitted attempt. Normal deterministic completion may use already accepted evidence without another model/tool call while the time deadline remains valid. A time deadline expires independently: abandon unfinished work and reject late responses even when counters remain.

Cancellation is a request, not proof a thread, driver, remote model or transaction stopped. Python `wait_for` may wait beyond its nominal timeout for cancellation [E3]. Integration must verify real transport/statement deadline behavior; an outer coroutine timeout alone is insufficient. A client may return at its deadline while the remote side still processes. This ADR establishes admission and delivery rules, not an already-validated hard real-time guarantee.

| Evidence at stop | Required behavior |
|---|---|
| No write dispatched | Return technical ERROR/FAILED, or CANCELLED for explicit caller cancellation; preserve last workflow state; effect NONE_CONFIRMED or NOT_APPLICABLE as appropriate |
| PO confirmed committed before stop | Preserve confirmed PO identity/result and report that fact; execution may have failed to finish formatting, but the purchase is not relabelled failed or undone |
| Write dispatched with unknown outcome | Keep last state PO_CREATION, mark RECOVERY_PENDING with UNKNOWN effect; no PO success claim, no new key or dispatch; hold for trusted original-effect recovery |
| Approval creation outcome unknown | Hold the same request/key; do not create another approval request or infer a grant; existing business state remains truthful |
| RAG has partial text or only part of required evidence | Preserve candidate/read evidence; deliver technical ERROR for budget failure, not a complete answer or healthy insufficient-evidence abstention |
| Pending human approval without budget failure | Normal waiting checkpoint, not a retry failure; future trusted resume uses remaining root budget |

Error precedence: uncertain side effects determine the recovery state even when the trigger is a budget deadline. Confirmed effects cannot be erased by a later error. Keep run outcome, workflow state, effect state, provider outcome and later reliability decision separate. The app does not manufacture PASS/REVIEW/BLOCK or a primary failure label.

Proposed technical codes: BUDGET_LOGICAL_CALL_LIMIT, BUDGET_GENERATION_ATTEMPT_LIMIT, BUDGET_TOOL_ATTEMPT_LIMIT, BUDGET_POLICY_ATTEMPT_LIMIT, BUDGET_EMBEDDING_ATTEMPT_LIMIT, BUDGET_PREFLIGHT_LIMIT, BUDGET_DEADLINE_EXCEEDED, BUDGET_DEPTH_LIMIT, BUDGET_SEGMENT_LIMIT, RETRY_LIMIT_EXCEEDED, RETRY_AFTER_EXCEEDS_BUDGET, PARALLEL_NOT_ENABLED, BUDGET_STATE_UNAVAILABLE, STALE_EXECUTION_LEASE, IDEMPOTENCY_CONFLICT, JOINT_AGREEMENT_REQUIRED and RECOVERY_BUDGET_EXHAUSTED. Exact shared enum placement requires Mohab’s review. Budget errors have `retryable=false` for the current execution; an authorized later workflow/recovery decision is separate.

### Example exhaustion-error schema

This is a proposed runtime error payload, not a canonical Trace Schema event or a tool-body result.

```json
{
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string"
    },
    "stage": {
      "type": "string"
    },
    "message": {
      "type": "string"
    },
    "retryable": {
      "type": "boolean",
      "enum": [
        false
      ]
    },
    "budget_dimension": {
      "type": "string"
    },
    "budget_profile_id": {
      "type": "string",
      "enum": [
        "execution-budget-v1-proposed"
      ]
    },
    "root_workflow_id": {
      "type": "string"
    },
    "execution_segment_id": {
      "type": "string"
    },
    "logical_operation_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "attempt_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "last_confirmed_state": {
      "type": "string"
    },
    "execution_started": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ]
    },
    "effect_state": {
      "enum": [
        "NOT_APPLICABLE",
        "NONE_CONFIRMED",
        "COMMITTED_CONFIRMED",
        "UNKNOWN"
      ],
      "type": "string"
    },
    "recovery_action": {
      "enum": [
        "NONE",
        "HOLD_FOR_REVIEW",
        "READ_ONLY_ORIGINAL_EFFECT"
      ],
      "type": "string"
    },
    "recovery_authorization_ref": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "checkpoint_ref": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "code",
    "stage",
    "message",
    "retryable",
    "budget_dimension",
    "budget_profile_id",
    "root_workflow_id",
    "execution_segment_id",
    "logical_operation_id",
    "attempt_id",
    "last_confirmed_state",
    "execution_started",
    "effect_state",
    "recovery_action",
    "recovery_authorization_ref",
    "checkpoint_ref"
  ],
  "type": "object"
}
```

Authored unknown-PO example (no transaction executed):

```json
{
  "code": "BUDGET_DEADLINE_EXCEEDED",
  "stage": "tool_dispatch",
  "message": "Execution stopped; the original PO outcome remains unknown.",
  "retryable": false,
  "budget_dimension": "active_deadline",
  "budget_profile_id": "execution-budget-v1-proposed",
  "root_workflow_id": "wf-paper-01",
  "execution_segment_id": "segment-paper-02",
  "logical_operation_id": "op-paper-po",
  "attempt_id": "attempt-paper-01",
  "last_confirmed_state": "PO_CREATION",
  "execution_started": true,
  "effect_state": "UNKNOWN",
  "recovery_action": "HOLD_FOR_REVIEW",
  "recovery_authorization_ref": null,
  "checkpoint_ref": "checkpoint-paper-unknown"
}
```

The absence of a recovery authorization reference means HOLD_FOR_REVIEW; it does not itself allow a reconciliation session. The user-facing response states that the outcome is unknown. Optional known PO/result fields are reported only from a confirmed observation, never inferred from this error.

`execution_started` is true only with positive original-start evidence, false only with authoritative non-execution evidence, and null when start cannot be established after a claimed dispatch/crash. UNKNOWN may therefore have true or null, never an invented true solely because an attempt debit exists. Cross-field rules require runtime validation in addition to the JSON Schema: clamped positive time, required write key/digest and PO authorization, UNKNOWN requiring HOLD or authorized read-only recovery, and COMMITTED_CONFIRMED requiring start evidence. READ_ONLY_ORIGINAL_EFFECT additionally requires a non-null trusted recovery authorization reference; a reference alone does not prove its validity.

## 7. Purchasing-action approval matrix

MVP purchasing effects are **synthetic**. The financial operations below are explicitly outside current tools and disabled; listing them is a risk/approval boundary, not permission to implement or call them.

| Action | Scope | Default replay policy | Required safeguards / evidence | Joint decision owners |
|---|---|---|---|---|
| Policy/supplier lookup | MVP read | Bounded retry allowed for transient reads | No financial effect; preserve version/eligibility evidence | Nour; data/policy owners confirm contract |
| Approval-level calculation | MVP read | One attempt by default | Same request/revision and authoritative rule; no approval granted | Nour + Mohamed |
| Approval request — initial creation | MVP synthetic write | One attempt; no automatic write replay | Same-key/payload semantics, source authority and retention must be accepted; ambiguity stops submission | Mohamed + Mohab + Nour; purchasing process owner if real integration |
| Existing approval observation | MVP read; semantics confirmed under OD-APP-OBS-01, implementation verification pending | Proposed bounded transient read retry only; never retry initial submission or create/update a request | Existing approval-request ID, unchanged trusted request binding; no fallback to creation if absent/mismatched; authoritative status preserved | Mohamed + Mohab confirmed semantics via user; Nour records; adapter/budget gates remain |
| Mock PO submission | MVP synthetic effect | One creation dispatch claim; no automatic redispatch | Valid bound ALLOW, immutable payload, stable key, atomic local claim and result correlation | Mohamed + Mohab + Nour; design acceptance pending |
| Original mock PO outcome lookup | MVP internal read | Bounded trusted read-only recovery | Original key/call; no replacement key; authoritative result or remain unresolved | Mohamed + Mohab + Nour; recovery contract acceptance pending |
| Real order submission or amendment | OUTSIDE MVP | Disabled; joint agreement required before enablement/replay | Remote idempotency scope/retention, supplier state, exact business request and incident-specific reconciliation | Purchasing process owner + integration owner (unassigned) + Mohamed/Mohab/Nour |
| Payment authorization | OUTSIDE MVP | Disabled; no automatic replay | Provider transaction identity/status, amount/currency, original authorization evidence and duplicate exposure | Finance/Treasury process owner + payment integration owner (unassigned) + governance/engineering |
| Payment capture | OUTSIDE MVP | Disabled; no automatic replay | Authorization/capture identities, partial-capture rules, authoritative amount/status and remaining capturable amount | Finance/Treasury + payment integration owner (unassigned) + governance/engineering |
| Refund | OUTSIDE MVP | Disabled; no automatic replay | Original payment/capture and refund identities, prior refunds, approved refundable amount and status | Finance/Treasury + payment integration owner (unassigned) + governance/engineering |
| Cancellation/void/reversal | OUTSIDE MVP | Disabled; joint agreement required | Exact target and operation type, downstream state, any already committed effect and cancellation authority | Purchasing owner for orders; Finance/Treasury for payments; integration owner + governance/engineering |


### What “joint agreement” must contain

There are three distinct approvals:

1. **Contract enablement:** Mohamed, Mohab and Nour accept the relevant mock operation’s retry/idempotency/recovery semantics. Real business/financial enablement also requires the designated process/integration owners; their names and authority are not supplied.
2. **Transaction authorization:** the existing trusted purchasing approval and fresh pre-tool ALLOW for the exact request/operation. A review of this ADR is not a manager’s approval to purchase.
3. **Incident recovery authorization:** a recorded case-specific permitted action after ambiguity or a request to expand a read-only recovery allowance. It references the original workflow, operation, key and effect evidence. This authorization cannot silently convert a read-only MVP recovery into write replay.

The agreement record needs: ID/revision, reviewer identities/roles, date, original root/request/operation IDs, immutable payload digest and amount/currency where relevant, original key and dispatch/result references, authoritative current state, permitted action, bounded attempts/time, evidence validity/expiry/revocation rules, conditions and closure evidence. Actual approval validity values remain owner decisions, not invented defaults.

Default permitted actions are **HOLD** or **READ_ONLY_ORIGINAL_EFFECT**. Real replay, compensation, payment capture/refund or cancellation requires an explicit separately reviewed contract and case authorization; no operation name is assumed reversible. A compensating action is a new governed transaction with its own identity/approval, not rollback of history.

## 8. Idempotency, recovery and duplicate safeguards

Issue keys in trusted runtime code and namespace them by operation/business scope; never accept a model’s replacement key as authority. Bind the key to an immutable normalized business snapshot: request/revision, supplier, item/quantity, exact decimal total and currency as applicable. Keep authorization/policy/check bindings separate from the idempotency digest; volatile attempt IDs, deadlines and timestamps must not change business-payload identity.

Use the generation ADR’s reviewed canonical JSON/hash convention after business normalization; never round money during hashing. Same key + different business digest is IDEMPOTENCY_CONFLICT. Concurrent same-key deliveries are single-flighted/fenced through a shared supported ledger. A known confirmed prior result can be returned by a runtime read-only observation referencing the original invocation; do not fabricate a second tool call/commit.

Before initial PO I/O, persist required authorization, current budget snapshot/fence, idempotency binding and dispatch claim. The local claim and authorized APPROVED→PO_CREATION transition must be atomic as agreed with Mohab/Mohamed. Do not hold a database transaction open expecting it to make remote execution atomic. A crash after claim but before provable send is ambiguous unless authoritative evidence establishes otherwise; no blind creation replay.

Recovery observes the original key only. Confirmed matching effect can lead to COMPLETION; authoritative final failure can halt as FAILED; missing, pending, conflicting or lost data remains unresolved. Missing data alone does not prove no remote/in-flight effect. Do not overwrite the original UNKNOWN_OUTCOME or add a contradictory second terminal tool result; append a typed recovery observation linked to the original call.

Retain unresolved idempotency/dispatch fences and minimal checkpoint references beyond ordinary raw-trace TTL until the case is authoritatively closed under an accepted policy. A TTL or provider-side key expiry must never silently free a business request for replay. If an in-memory ledger was lost on restart, durable recovery cannot be claimed. A new key/revision/root for the same unresolved purchase remains prohibited. Any future conclusively-failed creation retry needs separate joint agreement; the current contract grants no redispatch through recovery.

## 9. Concrete tool-contract metadata and schemas

Business tool arguments stay unchanged. The runtime adds the following **trusted context**, outside model-written arguments:

```json
{
  "additionalProperties": false,
  "properties": {
    "root_workflow_id": {
      "type": "string"
    },
    "request_revision": {
      "type": "string"
    },
    "execution_segment_id": {
      "type": "string"
    },
    "logical_operation_id": {
      "type": "string"
    },
    "attempt_id": {
      "type": "string"
    },
    "reservation_id": {
      "type": "string"
    },
    "parent_scope_id": {
      "type": "string"
    },
    "budget_profile_id": {
      "type": "string",
      "enum": [
        "execution-budget-v1-proposed"
      ]
    },
    "budget_snapshot_ref": {
      "type": "string"
    },
    "fencing_token": {
      "exclusiveMinimum": 0,
      "type": "integer"
    },
    "operation_mode": {
      "enum": [
        "READ_ONLY",
        "CREATE_APPROVAL_REQUEST",
        "OBSERVE_APPROVAL",
        "CREATE_PO",
        "RECOVERY_LOOKUP"
      ],
      "type": "string"
    },
    "deadline_remaining_ms": {
      "exclusiveMinimum": 0,
      "type": "integer"
    },
    "configured_timeout_ms": {
      "exclusiveMinimum": 0,
      "type": "integer"
    },
    "effective_timeout_ms": {
      "exclusiveMinimum": 0,
      "type": "integer"
    },
    "idempotency_key": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "business_payload_sha256": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "authorization_check_ref": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "joint_agreement_ref": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "root_workflow_id",
    "request_revision",
    "execution_segment_id",
    "logical_operation_id",
    "attempt_id",
    "reservation_id",
    "parent_scope_id",
    "budget_profile_id",
    "budget_snapshot_ref",
    "fencing_token",
    "operation_mode",
    "deadline_remaining_ms",
    "configured_timeout_ms",
    "effective_timeout_ms",
    "idempotency_key",
    "business_payload_sha256",
    "authorization_check_ref",
    "joint_agreement_ref"
  ],
  "type": "object"
}
```

Authored dispatch context example:

```json
{
  "root_workflow_id": "wf-paper-01",
  "request_revision": "request-paper-r1",
  "execution_segment_id": "segment-paper-02",
  "logical_operation_id": "op-paper-po",
  "attempt_id": "attempt-paper-01",
  "reservation_id": "reservation-paper-01",
  "parent_scope_id": "scope-paper-dispatch",
  "budget_profile_id": "execution-budget-v1-proposed",
  "budget_snapshot_ref": "budget-paper-v12",
  "fencing_token": 3,
  "operation_mode": "CREATE_PO",
  "deadline_remaining_ms": 3200,
  "configured_timeout_ms": 5000,
  "effective_timeout_ms": 3200,
  "idempotency_key": "opaque-po-key-paper",
  "business_payload_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "authorization_check_ref": "check-paper-allow",
  "joint_agreement_ref": null
}
```

This context is an audit/adapter view of an authoritative reservation, not a capability supplied by a client. Validate it against stored current ownership, counters, immutable request and authorization. Do not trust a copied timeout/fencing token from the model. `joint_agreement_ref=null` does not waive operation enablement; acceptance can be linked through the frozen profile/contract record, while an incident-specific grant is recorded when required.

Required per-attempt evidence: attempt/reservation ID; debit status; actual-send/start observation and timestamp; effective timeout; outcome/error; cancellation request/acknowledgment; effect state; final accepted versus abandoned response; original operation and recovery links. Pre-dispatch suppression has no tool-body payload and canonical call ID remains null unless actual invocation evidence exists. A reserved-but-unsent attempt may consume budget without becoming a fabricated tool call.

Runtime envelope kinds must distinguish TOOL_OBSERVATION, RUNTIME_SUPPRESSION and RECOVERY_OBSERVATION. Retain existing business statuses: CREATED, ALREADY_EXISTS, UNKNOWN_OUTCOME, ERROR, PENDING and the other tool-specific outcomes. An ALREADY_EXISTS/recovery observation is evidence of an original effect, not proof of a new commit. Shared envelope/type names remain proposals for `packages/contracts`, not app-defined competing canonical schemas.

## 10. Observability and recovery checkpoints

Record root/segment/parent/operation/attempt IDs, profile/code/config versions, ledger version/fence, limits/spent/remaining values, admission/debit/start distinctions, remaining deadlines, retry classification/backoff/Retry-After, cancellation, last confirmed state, effect state and original idempotency/approval/result references. Never log credentials, raw authorization headers or hidden model reasoning.

Suggested metric families: admission_denied_total by application/operation class/dimension; attempts_total by outcome/retry class; active execution duration; remaining-budget-at-stop; policy suppression count; unknown-effect and recovery observation counts. IDs, keys, payload digests and free-text errors belong in controlled traces, not high-cardinality metric labels. Use measured durations/counts only; no values are fabricated in this specification.

Checkpoint before side-effect claim, before ending approval wait, on effect observation/uncertainty and on exhaustion/cancellation. Persist enough to reconstruct counters and truth without rerunning model/tool work. Evidence-delivery or budget-state failure prevents new risky dispatch. A later evaluation consumes original evidence but does not reset execution or turn reviewer acceptance into purchase approval.

## 11. Alternatives, consequences and risks

| Alternative | Decision / trade-off |
|---|---|
| Fresh budgets per retry/resume | Rejected: creates unlimited work and duplicate paths |
| Per-call timeouts only | Rejected: nested stages and backoff can exceed a total budget |
| Independent SDK/application retries | Rejected unless counted by one owner; otherwise multiplicative work |
| Retry all HTTP 5xx writes | Rejected: transport failure does not determine effect state |
| Generic cancellation wrapper | Insufficient: remote/driver work can survive cancellation; preserve uncertainty |
| External exactly-once guarantee | Not claimed: atomic local intent and provider idempotency are separate contracts |
| New distributed workflow infrastructure | Not selected for MVP; existing platform ledger/continuation boundary must enforce the reviewed contract |
| No read-only recovery allowance | Rejected as too restrictive after a safe halt; instead use a separately bounded, trusted original-effect allowance |

Consequences: conservative crash charging can exhaust capacity despite fewer observed starts; finite resume slots may require operator review; bounded output delivery may leave an effect unresolved; quota limits across roots remain a deployment concern. These are deliberate proposed trade-offs. No callback, cancellation or timeout is treated as a financial reversal.

## 12. Open decisions requiring joint agreement

| Decision | Required owners | Closure evidence |
|---|---|---|
| Proposed budget values, cumulative active-time lease and fencing | Nour + Mohab; Mohamed for purchasing boundaries | Named revision acceptance and adapter tests |
| Approval submission same-key replay, validity and continuation implementation | Mohamed + Mohab + Nour | Observation semantics confirmed in OD-APP-OBS-01; remaining evidence: submission idempotency/trusted-resume contract, verified read-only adapter and stale/ambiguous examples |
| Dormant request calendar expiry and approval validity | Mohamed + business process owner when applicable; Mohab/Nour | Explicit validity/abandonment policy; idle wait is not an active budget or permission to resume |
| PO dispatch claim, ledger durability and no-redispatch recovery | Mohamed + Mohab + Nour | Original-effect observations, crash cases and exact implementation limits |
| Recovery sessions/allowance expansion and incident evidence | Mohamed + Mohab + Nour; business owner for real effects | Signed bounded permitted-action record |
| Real order/payment/refund/cancellation enablement | Assigned business process and integration owners + governance/engineering | New explicit scope/contract decision; currently disabled |
| SDK transport retries and effective cancellation behavior | Nour + Mohab | Actual attempt counts and timeout/cancellation fault injection |
| Cross-root workload/quota and reproducibility | Alaa + Nour/Mohab | Actual account quotas, frozen manifests and batch admission design |
| Error/effect/recovery schema mapping and evaluation distinctions | Mohab + Ahmed/Mohamed/Nour | Agreed canonical fields; no conflicting terminal results |

## 13. Acceptance tests and implementation checklist

The following are required tests for the later implementation, not invented results:

| Test | Required assertion |
|---|---|
| Final model slot raced by two callers | One admission wins; other makes no provider request; counters never negative |
| Initial model attempt fails then retries | One logical debit, two attempt debits; both outcomes visible |
| Timeout/cancel/crash after reservation | No refund/reset from ambiguity; actual start remains distinct from debit |
| Parent has 1.2 s but child asks for 5 s | Child effective timeout <=1.2 s; no fresh independent timer |
| Retry-After exceeds wait/parent budget | No early retry; deterministic stop code and evidence |
| SDK performs hidden retries | Test detects extra I/O; release fails until governed by the root counter |
| Approval wait then trusted resume | Same root/profile and remaining counters; no charged active time while waiting; segment cap applies |
| Changed amount/revision or new trace ID | Authorization invalidated; root counters and unresolved-effect guard preserved |
| Multiple/native parallel proposals | Preserved and rejected without partial dispatch; no fan-out in baseline |
| Policy error/missing verdict | Tool not dispatched; no fabricated policy FAIL or tool result |
| PO timeout after actual dispatch | UNKNOWN effect, RECOVERY_PENDING, zero creation replay even after missing ledger row |
| Confirmed PO followed by formatting/deadline failure | Confirmed effect retained and truthfully reported; not relabelled failed purchase |
| Same key, changed payload | IDEMPOTENCY_CONFLICT before a new effect |
| Read-only recovery finds matching effect | Linked recovery observation; no second terminal result for original call and no new creation dispatch |
| Recovery allowance exhausted or ledger lost | Hold for review; no replacement key/root or invented no-effect conclusion |
| Cancellation fails to stop remote work | Parent does not trust late output; worker fenced; no implicit remote rollback claim |
| Root state unavailable after restart | No fresh budget; new purchasing dispatch blocked |
| Financial operation requested | Disabled/JOINT_AGREEMENT_REQUIRED; no payment/refund/cancellation tool introduced |
| RAG retrieval consumes most query deadline | Generation receives smaller remaining time; no total 120-second reset |
| Counter/schema integrity | Reject negative/boolean limits, unknown metadata fields and impossible timeout/effect combinations |

- [ ] Ratify values and purchasing/recovery contracts; keep all approvals revision-specific.
- [ ] Define canonical budget/error/recovery representations with Mohab; app-local examples are not a competing schema.
- [ ] Implement one ledger/admission/retry owner and operation-specific wrappers in the existing app/platform homes.
- [ ] Disable/verify SDK automatic retries; use actual adapter timeout controls and parent clamping.
- [ ] Integrate the existing governance boundary and atomic local dispatch claim; do not implement another policy engine.
- [ ] Preserve immutable original outcomes; append recovery observations and stable same-key correlations.
- [ ] Run the negative/race/crash/timeout acceptance cases as implementation becomes available.
- [ ] Confirm actual quota/access/deployment controls before batches or real integration; real financial work remains out of scope.

## 14. Proposed configuration JSON

This is application configuration, not provider request fields or existing repository interfaces.

```json
{
  "profile_id": "execution-budget-v1-proposed",
  "status": "PROPOSED_NOT_RATIFIED",
  "nesting": {
    "maximum_depth": 4,
    "root_depth": 0,
    "parallel_execution_enabled": false,
    "max_active_attempts_per_run": 1
  },
  "procurement": {
    "max_logical_generation_calls": 8,
    "max_generation_attempt_debits": 12,
    "max_generation_attempts_per_operation": 2,
    "max_token_preflights": 8,
    "max_logical_tool_operations": 8,
    "max_tool_attempt_debits": 12,
    "max_proposals": 8,
    "max_policy_checks": 12,
    "max_policy_check_attempts": 12,
    "segment_deadline_s": 300,
    "workflow_active_time_pool_s": 600,
    "max_segment_starts": 3,
    "max_po_creation_dispatch_claims": 1
  },
  "rag": {
    "max_logical_generation_calls": 1,
    "max_generation_attempt_debits": 2,
    "max_logical_embedding_operations": 1,
    "max_embedding_attempt_debits": 2,
    "max_token_preflights": 1,
    "max_sql_searches": 1,
    "max_proposals": 0,
    "total_query_deadline_s": 120,
    "embedding_stage_deadline_s": 15,
    "embedding_attempt_timeout_s": 10,
    "sql_statement_timeout_s": 5
  },
  "generation": {
    "procurement_attempt_timeout_s": 60,
    "rag_attempt_timeout_s": 90,
    "token_preflight_timeout_s": 10,
    "max_preflight_attempts": 1,
    "max_semantic_repair_calls": 0
  },
  "retry": {
    "max_attempts_default": 2,
    "base_delay_s": 1,
    "backoff_cap_s": 10,
    "jitter": "equal_jitter",
    "max_retry_wait_s": 10,
    "retry_after_is_minimum": true
  },
  "recovery": {
    "mode": "READ_ONLY_ORIGINAL_EFFECT",
    "max_trusted_sessions": 2,
    "session_deadline_s": 5,
    "total_active_time_pool_s": 10,
    "max_attempts_per_session": 2,
    "max_attempt_debits_total": 4,
    "lookup_attempt_timeout_s": 2,
    "allow_creation_redispatch": false
  },
  "cleanup": {
    "observation_cap_s": 2,
    "may_extend_parent_deadline": false,
    "new_business_operations_allowed": false
  },
  "operations": {
    "search_policy": {
      "mode": "READ_ONLY",
      "attempt_timeout_s": 3,
      "operation_deadline_s": 6,
      "max_attempts": 2
    },
    "get_supplier": {
      "mode": "READ_ONLY",
      "attempt_timeout_s": 2,
      "operation_deadline_s": 5,
      "max_attempts": 2
    },
    "calculate_approval_level": {
      "mode": "READ_ONLY",
      "attempt_timeout_s": 1,
      "operation_deadline_s": 1,
      "max_attempts": 1
    },
    "request_approval.create": {
      "mode": "CREATE_APPROVAL_REQUEST",
      "attempt_timeout_s": 5,
      "operation_deadline_s": 5,
      "max_attempts": 1
    },
    "request_approval.observe": {
      "mode": "OBSERVE_APPROVAL",
      "attempt_timeout_s": 2,
      "operation_deadline_s": 5,
      "max_attempts": 2
    },
    "create_purchase_order": {
      "mode": "CREATE_PO",
      "attempt_timeout_s": 5,
      "operation_deadline_s": 5,
      "max_attempts": 1
    },
    "pre_tool_check": {
      "mode": "READ_ONLY",
      "attempt_timeout_s": 2,
      "operation_deadline_s": 2,
      "max_attempts": 1
    },
    "original_po_lookup": {
      "mode": "RECOVERY_LOOKUP",
      "attempt_timeout_s": 2,
      "operation_deadline_s": 5,
      "max_attempts": 2
    }
  }
}
```

## 15. References and validation

| Ref | Primary reference | Technical point |
|---|---|---|
| E1 | https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/ | Bounded retries/backoff and side-effect ambiguity |
| E2 | https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3 | Retry-After seconds/date semantics; transport rules do not grant business replay permission |
| E3 | https://docs.python.org/3.12/library/asyncio-task.html | Cancellation/timeout behavior and limits of wrapper timeouts |

Offline authored specification checks: **PASS (32 assertions)**. These validate configuration relationships, example schemas, timeout clamping and illustrative accounting cases. The final-slot example is serial arithmetic, **not a concurrent database/worker race test**. No provider/SDK timeout, actual transaction, cancellation, persistent ledger, recovery or payment was executed. All implementation acceptance tests and joint decisions remain pending.
