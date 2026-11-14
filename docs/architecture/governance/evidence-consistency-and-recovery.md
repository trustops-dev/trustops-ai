# Evidence consistency and recovery

| | |
|---|---|
| **Status** | DRAFT v0.6 — Sprint 1 closeout (S1-04), response to review items 1 and 2 of the Trace Schema Draft v1.5 review, amended after the independent v1.6 review findings R16-01 to R16-09, Nour's owner packet 0.14 and aligned to Trace Schema Draft v1.9 names. Specification only; nothing here is implemented or verified by execution. Not acknowledged by any teammate. |
| **Owner** | Mohamed Elnaggar — `packages/governance-engine` |
| **Co-owner** | Mohab Mohsen for the schema validator and trace events; Ahmed Ragab reviews the outcome interpretation (§6) |
| **Part of** | [Governance contracts](README.md) · [contract](governance-contract.md) §4.6, §4.7, §6.3 · [decision flow](decision-flow.md) §4, §5, §6 |

## 0. Scope and source

The review of the Draft v1.5 package asks that two things be fixed, owned by Mohab and Mohamed together:

1. authorization snapshots are checked against their actual source evidence, not against copied fields;
2. recovery identity and invocation-outcome checks are complete.

This document is **governance's side**: the rules governance owns or depends on, written so Mohab's validator and the governance engine can implement the same checks and report the same finding codes. It does not replace the validator, the regression runner or the fixtures, which are Mohab's.

**Limits of this revision.** Trace Schema Draft v1.9 (specification, validator and regression runner) has now been read, and the validator was run offline on its own specification: 2,602 assertions and 0 failures, as Mohab reports. Governance did not run the 63-case regression suite and executed no runtime. Field names are now v1.9 paths. Finding codes are the `ERR_*` codes of the v1.9 validator where one exists; §7 lists the governance checks that have no dedicated code. Nothing here is a runtime verification or a teammate's acceptance.

Source tags as in the [contract](governance-contract.md): **[P]** proposal · **[R]** repository/sprint plan · **[N]** Nour's reference-application contracts · **[T]** Trace Schema draft · **[D]** governance decision or proposal.

---

## 1. Three kinds of check, and what each can and cannot do

The review asks which checks concern structure, evidence consistency and application behavior. Governance adds a fourth, the business policy outcome, because a policy violation must stay observable and must never be mistaken for a validation failure.

| Kind | Question | Examples | Implemented by | Verified by |
|---|---|---|---|---|
| **Structural validity** | Is the record well formed? | Types, required fields, enum membership, strict integers, parseable serialization | Mohab's schema validator | Validator unit tests |
| **Evidence consistency** | Do the records that reference each other agree? | Snapshot versus the supplier result it cites; recovery key versus the original key; claim id on the snapshot, the transition and the invocation | Mohab's validator (structure and trace-level agreement) and the governance consistency verifier (authorization and policy agreement), reporting the same finding codes | Contract tests built from a passing baseline and one mutation each |
| **Application behavior** | Did the runtime do what the contract says? | Dispatch claimed once, atomically; no redispatch during recovery; no verdict means no dispatch | Nour's runtime, Mohab's SDK, governance's check | Integration tests at the implementation milestone, not by fixture validation |
| **Policy outcome** | Was the business rule satisfied? | `PROC-APPROVAL-01` `FAIL` for a bypass | Governance policy engine | Truth tables ([policy-truth-tables.md](policy-truth-tables.md)) |

Rules that follow from this separation:

- **A failing trace stays capturable.** A deliberate business-policy violation (a bypass, an unapproved supplier) is a valid *failure fixture* when its evidence is consistent. It produces a policy `FAIL`, not a consistency finding.
- **Contradictory evidence is never certified.** If records disagree, an explicit finding is raised, and the fixture cannot be certified as a verified success and the authorization cannot be certified as a verified binding. A trace built on purpose to contain a contradiction is a legitimate *negative test case*, but it is never certifiable as either.
- **Failure of one kind does not hide another.** A consistency finding does not erase a policy result, and a policy `FAIL` does not excuse an inconsistency. Both are recorded.

Certification outcomes for a fixture or a recorded check:

| Outcome | Condition |
|---|---|
| `VERIFIED_SUCCESS` | Structurally valid, zero consistency findings, every applicable policy `PASS` or `NOT_APPLICABLE`, verdict `ALLOW` |
| `VERIFIED_FAILURE` | Structurally valid, zero consistency findings, at least one policy `FAIL` or the verdict `BLOCK`; the failure is the intended content |
| `NOT_CERTIFIABLE` | At least one consistency finding or an unresolved reference; recorded for analysis, never counted as success or as verified enforcement |

---

## 2. Principle: copies are claims, source records are evidence

[D] An authorization snapshot, a check request or a `binding` copies values (supplier status, approval status, amount, digests). These copies are **claims**. The **evidence** is the record they reference: the supplier result, the calculation result, the approval event and record, the normalized request, the proposal, the transition and the invocation.

1. **Policy results are computed from the resolved source evidence.** They are never computed from the copied snapshot fields.
2. **A copy that differs from its source is a finding**, and the source value is the one used.
3. **A flag asserts nothing.** `trusted_source_verified` and any similar field is a derived output. It may be `true` only when every consistency rule in §4 passed for that authorization. A `true` that contradicts a failing rule is itself a finding (`VERIFIED_FLAG_CONTRADICTED`).
4. **ALLOW needs zero findings.** A pre-tool check that has any consistency finding or unresolved reference cannot return `ALLOW`.

### 2.1 Who resolves, who compares

Governance depends only on `packages/contracts` and cannot import the platform or the reliability engine [R]. So:

| Step | Owner | Notes |
|---|---|---|
| Resolve references into actual records | Platform adapter in `packages/platform-core`, behind a port that governance defines | Looks up each referenced event or record and returns a typed `ResolvedEvidence`, or an explicit unresolved / ambiguous / duplicate marker |
| Compare claims with resolved evidence, compute policy results, raise findings | Governance engine (pure functions) | Unit-testable with no database |
| Re-run the same comparison over stored traces for post-run policy evaluation | Governance, using the same functions | Gives post-run results that do not depend on what was recorded at check time |

Proposed addition to the governance package: `ports/evidence_resolver.py` and `policy/evidence_consistency.py`. Neither is in the approved repository tree, so Mohab's agreement is needed (GD-24).

An unresolved, ambiguous or duplicated reference is a finding (`EVIDENCE_UNRESOLVED`); governance never guesses which record was meant.

---

## 3. What a check references

Each pre-tool check names its evidence by event id, in addition to any copied values:

| Reference | Evidence | Resolves to |
|---|---|---|
| Normalized request | E08 | Request id, revision, `total_amount`, `currency`, supplier, item, quantity |
| Supplier result | E11 | The `get_supplier` result for this request |
| Calculation result | E12 | The approval-requirement result |
| Approval event | E14 | The observed approval, plus governance's authoritative approval record |
| Proposal | E15, E16 | The proposed tool and parsed arguments |
| State snapshot | E09, E10 | State revision and stage |
| Authorization lifecycle | E17 to E20 | The check, the single dispatch claim, the transition and the invocation |

---

## 4. Consistency rules for authorization snapshots (review item 1)

Each rule compares a claim with resolved source evidence. "Effect" says what governance does in addition to recording the finding.

| Rule | Compares | Finding code | Effect |
|---|---|---|---|
| **EC-01** Supplier | The snapshot's supplier against the referenced supplier result: result identity, supplier id equals the proposal's, normalized eligibility, record and directory versions | `ERR_SNAPSHOT_SUPPLIER_EVIDENCE_MISMATCH` | `PROC-SUPPLIER-01` is computed from the **source** result (truth tables SU-01 to SU-07) |
| **EC-02** Calculation | The snapshot's calculation against the referenced result: result id, request revision, amount, currency, requirement, level; and the governance recomputation of the requirement (contract §5.1) against the recorded one | `CALCULATION_SNAPSHOT_MISMATCH`, `CALCULATION_RECOMPUTE_MISMATCH` | Governance's recomputed requirement is the one used (`INV-10`) |
| **EC-03** Approval | The snapshot's approval against the referenced approval event **and** governance's approval record: result identity, decision, approval-request and calculation binding, supplier, amount, currency, level, policy version; and the event against the record | `ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH`, `ERR_APPROVAL_EVIDENCE_MISMATCH` | `PROC-APPROVAL-01` is computed from the authoritative record; if event and record disagree, no valid approval can be established, so the policy is `FAIL` with `APPROVAL_EVIDENCE_CONTRADICTION` |
| **EC-04** Request and arguments | The normalized request against the authorized tool arguments and against the executed purchase order: supplier, item, quantity, `total_amount`, `currency` | `ERR_REQUEST_TOOL_ARG_MISMATCH` | Check-level `CONTEXT_MISMATCH`: `BLOCK` with basis `FAIL_CLOSED_ON_POLICY_ERROR` |
| **EC-05** Policy identities | A complete check for `create_purchase_order` has exactly one result for each of the three mandatory policy ids, and each result's applicability agrees with the recomputed requirement and the proposed tool | `ERR_POLICY_IDS_NOT_DISTINCT` | A recorded check with a duplicated or missing policy id is not certifiable; the live engine cannot emit one, so a live occurrence is an internal error and blocks |
| **EC-06** Dispatch claim | The preallocated `dispatch_claim_id` on the `binding` (authorization snapshot), on the consumption record, on the atomic transition and on the invocation: exactly equal; exactly one consumption per root; the transition links the checked state revision to the dispatch state revision | `ERR_DISPATCH_CLAIM_MISMATCH` | The authorization is not verified (see §5) |
| **EC-07** Binding | `binding` fields against the referenced records: proposal id, request revision, state revision, and the business-payload digest recomputed from the authorized arguments | `ERR_PO_BINDING_FAILED`, `ERR_ARG_DIGEST_MISMATCH` | The binding is not verified |
| **EC-08** Policy version | The binding's version, the check's version and every policy result's version agree, and equal the version active when the check ran | `POLICY_VERSION_MISMATCH` | Check-level error; blocks |
| **EC-09** Resolution | Every reference resolves to exactly one record of the expected kind | `EVIDENCE_UNRESOLVED` | Check-level error; blocks |
| **EC-10** Flag | `trusted_source_verified` against the result of EC-01 to EC-09 | `VERIFIED_FLAG_CONTRADICTED` | The flag is recomputed and the claimed value is discarded |
| **EC-11** Policy result re-derivation (post-run) | Each recorded `evaluated_policies[].policy_result` against the result governance re-derives from the **resolved source evidence** under the accepted policy bundle (truth tables) | `POLICY_RESULT_REDERIVATION_MISMATCH` | The re-derived result is the one used. A recorded `PASS` or `NOT_APPLICABLE` that re-derives to `FAIL` is a **policy-evaluation defect**: the failure is `FAIL` for `DEC-1`, the evidence is not certifiable and the finding names the policy, the recorded result and the re-derived result. Governance-only: it needs no schema field and is not in the v1.9 validator (§7.1) |

### 4.1 Effect on the verdict

| Situation | Policy results | Verdict | Basis | Certification |
|---|---|---|---|---|
| Every rule passes | Computed from source | per truth tables | per truth tables | `VERIFIED_SUCCESS` or `VERIFIED_FAILURE` |
| Finding, all policies `PASS` / `NOT_APPLICABLE` from source | Computed from source | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` | `NOT_CERTIFIABLE` |
| Finding, and at least one policy `FAIL` from source | Computed from source | `BLOCK` | `MANDATORY_POLICY_FAILED` (findings recorded too) | `NOT_CERTIFIABLE` |
| Reference unresolved | Cannot be computed for that policy: `ERROR` | `BLOCK` | `FAIL_CLOSED_ON_POLICY_ERROR` | `NOT_CERTIFIABLE` |

This follows the aggregation rules already in the truth tables (AG-02 to AG-06) and adds the cases in §7.

### 4.2 Governance-side acceptance cases (the review's five mutations)

Each case starts from the passing success baseline and changes one thing. Expected governance results:

| Case | Mutation | Findings | Policy results | Verdict / basis | Binding |
|---|---|---|---|---|---|
| **EM-01** | Supplier result becomes `NOT_APPROVED`; snapshot still says `APPROVED` | `ERR_SNAPSHOT_SUPPLIER_EVIDENCE_MISMATCH` | `PROC-SUPPLIER-01` `FAIL` (`SUPPLIER_NOT_APPROVED`) | `BLOCK` / `MANDATORY_POLICY_FAILED` | not verified |
| **EM-02a** | Approval event and record become `DENIED`; snapshot still claims approval | `ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH` | `PROC-APPROVAL-01` `FAIL` (`APPROVAL_DENIED`) | `BLOCK` / `MANDATORY_POLICY_FAILED` | not verified |
| **EM-02b** | Approval event becomes `DENIED` while governance's record says `APPROVED` | `ERR_APPROVAL_EVIDENCE_MISMATCH` | `PROC-APPROVAL-01` `FAIL` (`APPROVAL_EVIDENCE_CONTRADICTION`) | `BLOCK` / `MANDATORY_POLICY_FAILED` | not verified |
| **EM-03** | Root request amount becomes `"1.00"`; proposed and executed purchase order stay `"16000.00"` | `ERR_REQUEST_TOOL_ARG_MISMATCH` | Computed on the proposed amount | `BLOCK` / `FAIL_CLOSED_ON_POLICY_ERROR` | not verified |
| **EM-04** | All three evaluated policy results carry the same policy id | `ERR_POLICY_IDS_NOT_DISTINCT` | Recomputed from source for post-run use | recorded check `NOT_CERTIFIABLE` | not verified |
| **EM-05** | The snapshot's dispatch-claim id is changed to an unrelated value | `ERR_DISPATCH_CLAIM_MISMATCH` | unchanged | the pre-tool verdict stands; the authorization is `NOT_CERTIFIABLE` | not verified |
| **EM-00** | None (baseline) | none | `PASS` / `NOT_APPLICABLE` per source | `ALLOW` / satisfied | verified |

For EM-01 and EM-02 the business-policy failure is real and stays observable; the finding says only that the *recorded claim* was wrong. The baseline success fixture must still pass (`EM-00`).

---

## 5. Dispatch claim and authorization lifecycle

Nour's contracts make the runtime claim the dispatch atomically after an `ALLOW` [N], and her owner packet 0.14 proposes to **preallocate** an opaque claim identity before the check and consume the single allowance only after a bound `ALLOW` (OD-12-CLAIM). Governance accepts that, which also lets the `binding` carry the claim identity. The authorization is therefore two linked records plus an identity:

| Record | Written by | Content |
|---|---|---|
| Preallocated `dispatch_claim_id` | Runtime, before the check | Opaque; consumes nothing |
| Check and `binding` | Governance, at check time | `check_id`, proposal and attempt ids, request revision, state revision, business-payload digest, idempotency key, `dispatch_claim_id`, supplier / calculation / approval references with the approval and supplier `record_version`, policy-bundle version |
| Consumption record | Runtime, at claim time (one per root) | `dispatch_claim_id`, `check_id`, the authorized transition event, the invocation id, consumption time; immutable |

Governance verifies (EC-06) that the claim id is identical on the binding, the consumption record, the atomic transition and the invocation, that the consumption references an `ALLOW` whose `binding` was still current at the claim (contract §5.3 V06), and that no second consumption exists for the same root. Governance neither allocates nor consumes the claim (GD-28). Root-wide uniqueness across checks, revisions and traces is enforced by the runtime ledger; the original check and events are never edited.

**An authorization that fails EC-06 or EC-07 is not verified.** If a purchase order was nevertheless dispatched under it, post-run policy evaluation re-derives the policies from source (not from the snapshot), compares them with the recorded check and records the dispatch as executed under an unverified authorization (GD-26, contract §6.3).

---

## 6. Recovery identity and invocation-outcome checks (review item 2)

### 6.1 Posture

[N] Recovery after an unknown outcome is a read-only lookup. It grants no execution permission, never calls the creating tool again, never creates a replacement key and never reuses `ALLOW`. Governance's rules are:

- A recovery observation is **never** a new authorization, so the pre-tool policy engine is not invoked to approve it.
- A recovery observation is a **separate append-only record** linked to the original. It never replaces, edits or hides the original uncertain result.
- The original outcome stays whatever it was recorded as. The "current" outcome is derived from the original plus the latest valid recovery observation (a query, not a mutation, as with reviews).

### 6.2 Outcome combinations

For a state-mutating tool (`create_purchase_order`), the result `status`, the `execution_status` and the `side_effect_state` must form a valid combination. The effect values are the Trace Schema v1.9 `tool_result.side_effect_state` values: `NONE`, `COMMITTED`, `ALREADY_EXISTING` and `UNKNOWN`. The execution-budget ADR names the same states `NONE_CONFIRMED`, `COMMITTED_CONFIRMED` and `UNKNOWN` at its checkpoints, and Mohab's mapping puts both `COMMITTED` and `ALREADY_EXISTING` under `COMMITTED_CONFIRMED`. Read-only tools have no side effect and are outside this table.

| Case | Where it stopped | Business outcome | Transport outcome | Effect state | Valid |
|---|---|---|---|---|---|
| OC-1 | Pre-tool `BLOCK`, suppressed before dispatch | `NOT_EXECUTED` | none | `NONE` | yes |
| OC-2 | Rejected by argument validation before dispatch | `NOT_EXECUTED` (validation error) | none | `NONE` | yes |
| OC-3 | No verdict, governance error or budget exhaustion, no dispatch | `NOT_EXECUTED` | none | `NONE` | yes |
| OC-4 | Dispatched, purchase order confirmed | `CREATED` | completed | `COMMITTED` | yes |
| OC-5 | Dispatched, same-key replay | `ALREADY_EXISTS` | completed | `ALREADY_EXISTING` (earlier effect; none new; `original_result_ref` kept) | yes |
| OC-6 | Dispatched, authoritative definitive failure (no purchase order, nothing in flight) | `ERROR` | completed | `NONE` | yes, only with authoritative evidence |
| OC-7 | Dispatched, no response before the deadline | `UNKNOWN_OUTCOME` | timeout | `UNKNOWN` | yes — the only valid state |
| OC-8 | Dispatched, result malformed or lost, **or a runtime exception after the claim** | `UNKNOWN_OUTCOME` | malformed, lost or `RUNTIME_EXCEPTION` (with `transport_diagnostics`) | `UNKNOWN` | yes |
| OC-9 | `UNKNOWN_OUTCOME` or timeout with `NONE` or `COMMITTED` | — | — | — | **no** — `OUTCOME_COMBINATION_INVALID` |
| OC-10 | `CREATED` with `NONE` or `UNKNOWN` | — | — | — | **no** |
| OC-11 | `NOT_EXECUTED` with `COMMITTED` or `UNKNOWN` | — | — | — | **no** |
| OC-12 | `ERROR` after the dispatch claim without authoritative evidence, recorded as `NONE` | — | — | — | **no** — must be `UNKNOWN` until reconciled |
| OC-13 | `COMPLETION` reached while the effect is `UNKNOWN` or `STILL_UNRESOLVED` | — | — | — | **no** — `ERR_UNRESOLVED_RECOVERY_COMPLETION` |
| OC-14 | An `UNKNOWN` result whose call, proposal or claim does not match the invocation it concludes | — | — | — | **no** — `RESULT_BINDING_MISMATCH` |

**An uncertain outcome stays `UNKNOWN`** until authoritative reconciliation establishes the result. This holds for a timeout, a malformed or lost response and a runtime exception after the claim alike, and not only for a timeout. Nothing uncertain implies "no side effect". OC-8 is explicit because the independent v1.6 review found a validator that rejected a legitimate non-timeout `UNKNOWN` (case `unknown_after_runtime_exception`).

**Cross-document conflict to resolve.** Ahmed's [evaluation pipeline](../evaluation-pipeline.md) describes a mock-tool timeout as `tool_result.execution_status = "TIMEOUT"` with `side_effect_committed = false`. For a dispatched purchase order a timeout is `UNKNOWN`, so `side_effect_committed = false` would assert a certainty nobody has. Ahmed and Mohab need to align the field; until then governance treats a `false` on a dispatched timeout as `OC-9` (GD-27).

### 6.3 Recovery observation

A valid recovery observation records one of three results for the read-only ledger lookup [N]:

| Ledger observation | Recovery result | Original result event | Derived current effect |
|---|---|---|---|
| Matching confirmed purchase order exists | `RESOLVED_COMMITTED` | unchanged (`UNKNOWN`) | `COMMITTED` (outcome `CREATED`) |
| Authoritative final failure, no purchase order, nothing in flight | `RESOLVED_ABORTED` | unchanged | `NONE` (outcome `ERROR`) |
| Pending, missing, unavailable, lost or inconsistent | `STILL_UNRESOLVED` | unchanged | `UNKNOWN` |

`STILL_UNRESOLVED` is the v1.9 value; `unresolved_reason_code` carries why. Missing data alone never establishes non-execution. Each lookup attempt has its own identity and is charged to the separate recovery allowance of the execution-budget ADR; a recovery that spent no allowance, or spent another pool, is a finding (RC-11).

### 6.4 Recovery identity rules

Each rule compares the recovery observation with the original uncertain invocation.

| Rule | Compares | Finding code |
|---|---|---|
| **RC-01** | `recovery_of_result_id` belongs to `recovery_of_call_id`, and that result is the original terminal `UNKNOWN_OUTCOME` result | `ERR_RECOVERY_TARGET_UNRESOLVED`; `RECOVERY_TARGET_NOT_UNKNOWN` when the target result is not `UNKNOWN_OUTCOME` |
| **RC-02** | The recovery references the original uncertain invocation and its request id and revision | `RECOVERY_REQUEST_MISMATCH` |
| **RC-03** | The key used for the ledger query equals the original invocation's idempotency key | `ERR_RECOVERY_KEY_MISMATCH` |
| **RC-04** | The business-payload digest recorded by the recovery equals the original invocation's digest | `RECOVERY_DIGEST_MISMATCH` |
| **RC-05** | Recovered purchase-order data (supplier, item, quantity, `total_amount`, `currency`) equals the original business request | `RECOVERY_PAYLOAD_MISMATCH` |
| **RC-06** | The outcome combination is valid (§6.2) | `OUTCOME_COMBINATION_INVALID` |
| **RC-07** | The recovery did not dispatch the creating tool, create a new key or edit the original result | `RECOVERY_REDISPATCHED`, `RECOVERY_REPLACED_ORIGINAL` |
| **RC-08** | Each invocation has exactly one terminal tool result | `ERR_DUPLICATE_TERMINAL_TOOL_RESULT` |
| **RC-09** | The run does not reach `COMPLETION` while the effect is `UNKNOWN` or `STILL_UNRESOLVED` | `ERR_UNRESOLVED_RECOVERY_COMPLETION` |
| **RC-10** | An `UNKNOWN` result belongs to the exact call, proposal and claim of the invocation it concludes | `RESULT_BINDING_MISMATCH` |
| **RC-11** | Each recovery lookup attempt has its own identity and is charged to the separate recovery allowance | `RECOVERY_ATTEMPT_UNACCOUNTED` |

On `ERR_DUPLICATE_TERMINAL_TOOL_RESULT`, consumers use the earliest terminal result by sequence as the invocation's outcome and record the finding; the later one is evidence of an integrity problem, not a correction. A genuine later fact arrives as a recovery observation (§6.3), not as a second terminal result.

### 6.5 Governance-side acceptance cases

| Case | Mutation of a valid read-only recovery | Finding | Result |
|---|---|---|---|
| **RM-01** | Recovery queries with a different idempotency key | `ERR_RECOVERY_KEY_MISMATCH` | not certifiable |
| **RM-02** | Recovery records a different business-payload digest | `RECOVERY_DIGEST_MISMATCH` | not certifiable |
| **RM-03** | `recovery_of_result_id` belongs to a different call | `ERR_RECOVERY_TARGET_UNRESOLVED` | not certifiable |
| **RM-04** | An `UNKNOWN_OUTCOME` timeout records effect state `NONE` | `OUTCOME_COMBINATION_INVALID` | not certifiable |
| **RM-05** | Two terminal results for the same invocation | `ERR_DUPLICATE_TERMINAL_TOOL_RESULT` | not certifiable |
| **RM-06** | Recovered purchase order differs from the original request | `RECOVERY_PAYLOAD_MISMATCH` | not certifiable |
| **RM-07** | A non-timeout runtime exception after the claim, recorded `UNKNOWN_OUTCOME` with effect `UNKNOWN` | none | **passes** (OC-8) |
| **RM-08** | The run reaches `COMPLETION` while recovery is `STILL_UNRESOLVED` | `ERR_UNRESOLVED_RECOVERY_COMPLETION` | not certifiable |
| **RM-09** | An `UNKNOWN` result carries another proposal or another claim | `RESULT_BINDING_MISMATCH` | not certifiable |
| **RM-10** | A timeout result claims `side_effect_committed = false` (the evaluation pipeline's wording) | `OUTCOME_COMBINATION_INVALID` | not certifiable |
| **RM-00** | Valid read-only recovery; original timeout event unchanged | none | passes |

RM-07 to RM-10 come from the independent v1.6 review (`unknown_after_runtime_exception`, `unresolved_recovery_still_completed`, `unknown_result_wrong_claim`, `unknown_result_wrong_proposal`, `timeout_error_claims_no_effect`). They are governance's expected results for those inputs; the cases themselves and their execution are Mohab's.

### 6.6 What the decision layers do with an uncertain outcome

- **`enforcement_outcome`** (contract §6.3) is derived from consistent outcomes only. It is never taken from the agent's text, from a summary, or from a copied field. The authoritative evidence for each value is:

  | Value | Outcome case | Authoritative evidence (every item must be present and agree) | Not sufficient on its own |
  |---|---|---|---|
  | `PREVENTED` | `OC-1` to `OC-3` | A `tool_suppression` for the proposal (source `PRE_TOOL_POLICY_GATE`, argument validation or budget stop) with `tool_dispatched = false`, `execution_started = false`, `side_effect_state = NONE`; **no** `tool_call` and **no** `tool_result` for that proposal; **no** `dispatch_claim_consumption` for the claim; for a policy block, `claim_status_at_check = NOT_CLAIMED_BLOCKED` and `blocking_policy_ids` naming the failed policies | The final response saying it was blocked; the absence of a purchase order in the final answer |
  | `REALIZED` | `OC-4`, or a recovery `RESOLVED_COMMITTED` | A `tool_call` carrying the preallocated claim id and idempotency key; a `dispatch_claim_consumption` for that claim; a terminal `tool_result` `CREATED` with `side_effect_state = COMMITTED` and a `po_id`. After a recovery: `recovery_check` with `reconciliation_status = RESOLVED_COMMITTED`, `ledger_record_status = COMMITTED_RECORD_FOUND`, the queried key and payload digest equal to the original call's, and the recovered record matching the original request | The agent claiming "the order was created"; a tool result whose claim, proposal or digest does not match |
  | `DEFINITIVE_NO_EFFECT` | `OC-6`, or a recovery `RESOLVED_ABORTED` | The dispatch happened (a `tool_call` and a consumption record exist) **and** authoritative proof of no purchase order and nothing in flight: a terminal `ERROR` result from the authoritative source, or after a recovery `reconciliation_status = RESOLVED_ABORTED` with `ledger_record_status = EXPLICIT_ABORT_TOMBSTONE_FOUND` for the same key and digest, `resolved_side_effect_state = NONE` | `NO_LEDGER_ENTRY_FOUND` (missing, pending or unavailable data); an `ERROR` without authoritative evidence (that is `OC-12`, and stays `UNKNOWN`) |
  | `UNKNOWN` | `OC-7`, `OC-8`, `STILL_UNRESOLVED`, any invalid combination, or a duplicate terminal result | None. The evidence that is present is preserved (below); nothing is guessed in either direction | Any "probably" inference |
  | `ALREADY_EXISTING` (not a fifth value) | `OC-5` | A terminal `ALREADY_EXISTS` result with `side_effect_state = ALREADY_EXISTING` and a non-null `original_result_ref` that resolves to the earlier result. The replay itself has **no new effect** | A same-key replay with no resolvable `original_result_ref` (a consistency finding) |

  **A recovery observation** moves `UNKNOWN` to `REALIZED` or `DEFINITIVE_NO_EFFECT` in a new record and never rewrites the original result.

  **`ALREADY_EXISTING` inherits the outcome of the original call.** A replay is not itself a realized violation and not a prevented one. Governance follows `original_result_ref` to the original terminal result and applies this table to it: if the original was `COMMITTED`, the violation is `REALIZED` once, attributed to the original call; if the original is `UNKNOWN`, the outcome is `UNKNOWN`. The replay's own record adds no second effect. (Revision 0.4 to 0.6 of this document listed `OC-5` directly under `REALIZED`; that was imprecise.)

  **What is preserved when the outcome stays `UNKNOWN`** (including `STILL_UNRESOLVED`, `RUNTIME_EXCEPTION`, malformed or lost responses and timeouts): the `tool_call`, the idempotency key, the business-payload digest, the claim id and its consumption record, the original `UNKNOWN_OUTCOME` result with its transport diagnostics, every recovery attempt with its `unresolved_reason_code` and `resolved_side_effect_state = UNKNOWN`, the policy findings of the check that allowed the dispatch, and the trace status `RECOVERY_PENDING`. Nothing is inferred as "no side effect"; the run is not terminal (DC-17) and `COMPLETION` is invalid (RC-09). A critical policy `FAIL` still forces `BLOCK` through `DEC-1`.

  **A claim the evidence does not support.** A final response that says the purchase order was created while the outcome is `UNKNOWN`, `DEFINITIVE_NO_EFFECT` or `PREVENTED` is an `UNSUPPORTED_COMPLETION` finding by Ahmed's evaluators (`UNSUPPORTED_NO_MATCHING_COMMITMENT` when no committed record matches). A final response that honestly reports the pending state ("the outcome is not confirmed, a recovery check is pending") is **not** an `UNSUPPORTED_COMPLETION`; it is the correct behavior. A `COMPLETION` state with an unresolved effect is a different failure and is `ERR_UNRESOLVED_RECOVERY_COMPLETION` (RM-08).

- **Layer 2.** A run that is not terminal (for example `RECOVERY_PENDING`) is an incomplete evaluation, not `PASS`, unless a critical policy failure already forces `BLOCK` (`DEC-1` needs no other evidence). See the truth tables (§7).

### 6.7 The `enforcement_outcome` value names

Contract §6.3 began with `PREVENTED`, `REALIZED` and `UNKNOWN`. A dispatch that happened and conclusively had no effect was neither prevented (the control did not stop it) nor realized, so revision 0.4 added a fourth value, then called `NOT_REALIZED`. In the 13 November addendum that value is renamed **`DEFINITIVE_NO_EFFECT`**. `NOT_REALIZED` could be read as "the violation did not happen" and so be confused with `PREVENTED`; the new name says what is known (an authoritative conclusion that nothing was committed) and what is not (it was not stopped by the control). The rename changes no rule: it applies to `OC-6` and to a recovery with `RESOLVED_ABORTED`.

---

## 7. Ownership of the findings

All finding codes in §4 and §6.4 belong in one registry in `packages/contracts`, so the validator and the governance verifier cannot drift (GD-10, GD-24).

| Codes | Raised by |
|---|---|
| `EVIDENCE_UNRESOLVED`, `ERR_SNAPSHOT_SUPPLIER_EVIDENCE_MISMATCH`, `CALCULATION_*`, `APPROVAL_*`, `ERR_REQUEST_TOOL_ARG_MISMATCH`, `ERR_POLICY_IDS_NOT_DISTINCT`, `POLICY_VERSION_MISMATCH`, `VERIFIED_FLAG_CONTRADICTED`, `POLICY_RESULT_REDERIVATION_MISMATCH` | Governance verifier; mirrored by Mohab's validator for trace-level fixtures |
| `ERR_DISPATCH_CLAIM_MISMATCH`, `ERR_PO_BINDING_FAILED`, `ERR_ARG_DIGEST_MISMATCH` | Governance verifier and Mohab's validator; the claim itself is the runtime's |
| `RECOVERY_*`, `OUTCOME_COMBINATION_INVALID`, `ERR_DUPLICATE_TERMINAL_TOOL_RESULT` | Mohab's validator (trace events); governance applies the same rules when deriving `enforcement_outcome` |

### 7.1 Governance checks and the Trace Schema v1.9 validator codes

The v1.9 validator codes are canonical (GD-31). Where governance has a check that the v1.9 validator reports under another code, or does not report, the governance name stays as an alias and the gap is listed so Mohab can add or confirm a code.

| Governance check | v1.9 validator code | Status |
|---|---|---|
| EC-01 supplier snapshot against its source | `ERR_SNAPSHOT_SUPPLIER_EVIDENCE_MISMATCH` | Same |
| EC-03 approval snapshot against its source | `ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH` | Same |
| EC-03 approval event against governance's record | `ERR_APPROVAL_EVIDENCE_MISMATCH` | Same |
| EC-04 request against arguments | `ERR_REQUEST_TOOL_ARG_MISMATCH` | Same |
| EC-05 duplicate or missing policy ids | `ERR_POLICY_IDS_NOT_DISTINCT`, `ERR_POLICY_ENTRY_INVALID` | Same |
| EC-06 dispatch-claim identity | `ERR_DISPATCH_CLAIM_MISMATCH` | Same |
| EC-07 snapshot fields and digest | `ERR_PO_BINDING_FAILED`, `ERR_ARG_DIGEST_MISMATCH` | Same |
| EC-08 policy version | `ERR_SNAPSHOT_POLICY_VERSION` (finding); `POLICY_VERSION_MISMATCH` is the governance policy reason | Same check, two names for two purposes |
| EC-02 calculation snapshot, and the governance recomputation | none dedicated (v1.9 reports through `ERR_PO_BINDING_FAILED` and `ERR_SNAPSHOT_REQUEST_MISMATCH`) | **Gap:** `CALCULATION_SNAPSHOT_MISMATCH`, `CALCULATION_RECOMPUTE_MISMATCH` |
| EC-09 unresolved reference | per kind: `ERR_SNAPSHOT_MISSING`, `ERR_PROPOSAL_UNRESOLVED`, `ERR_AUTH_CHECK_UNRESOLVED`, `ERR_RECOVERY_TARGET_UNRESOLVED` | Umbrella alias `EVIDENCE_UNRESOLVED` |
| EC-10 flag recomputation | none (the v1.9 validator does not check `trusted_source_verified`) | **Gap:** `VERIFIED_FLAG_CONTRADICTED` |
| EC-11 policy result re-derivation | none (the validator checks the shape of `evaluated_policies`, not whether each result is right under the policy) | **Gap, governance-only:** `POLICY_RESULT_REDERIVATION_MISMATCH`; the governance verifier raises it, Mohab's validator is not asked to |
| RC-01 recovery target | `ERR_RECOVERY_TARGET_UNRESOLVED` | Same; the "target is not `UNKNOWN`" case has no dedicated code |
| RC-03 recovery key | `ERR_RECOVERY_KEY_MISMATCH` | Same |
| RC-04 recovery digest | none dedicated | **Gap:** `RECOVERY_DIGEST_MISMATCH` |
| RC-06 outcome combination | `ERR_TIMEOUT_CLAIMS_NO_EFFECT`, `ERR_TIMEOUT_SIDE_EFFECT_NOT_UNKNOWN` | Partial: the general combination has no code |
| RC-08 duplicate terminal result | `ERR_DUPLICATE_TERMINAL_TOOL_RESULT` | Same |
| RC-09 completion while unresolved | `ERR_UNRESOLVED_RECOVERY_COMPLETION` | Same |
| RC-10 `UNKNOWN` result binding | `ERR_UNKNOWN_RESULT_PROPOSAL_MISMATCH`, `ERR_UNKNOWN_RESULT_CLAIM_MISMATCH` | Same |
| Currentness at consumption | `ERR_STALE_RECORD_VERSION_AT_CLAIM` | Same; needs the SA-02 fields |
| Approval superseded by a newer record | `ERR_APPROVAL_SUPERSEDED_SEQUENCE` | Same |
| Terminal approval record reopened | none | **Gap:** proposed `ERR_APPROVAL_TERMINAL_REOPENED` (GD-32) |
| Consumption record missing or invalid | `ERR_CLAIM_CONSUMPTION_RECORD_INVALID` | Same |
| Second consumption for a root, or reused check | `ERR_PO_DUPLICATE_DISPATCH_CLAIM`, `ERR_AUTH_CHECK_REUSED` | Same |
| Original write replayed | `ERR_WRITE_RETRY_FORBIDDEN` | Same |

---

## 8. Application behavior to verify at the implementation milestone

These are not fixture-validation matters and stay open until code exists:

- The runtime claims the dispatch atomically, once per `ALLOW`, and records the claim id on the transition and the invocation (Nour, Mohab).
- No code path dispatches during recovery or issues a new key (Nour).
- "No verdict" means no dispatch (Nour, Mohab).
- The platform adapter resolves references to exactly the records governance expects (Mohab).
- The governance verifier and the schema validator report the same finding code for each mutation (Mohamed, Mohab).

---

## 9. Disposition

Nothing here is "corrected and verified" by execution: governance ran only Mohab's own validator on his own specification (2,602 assertions, 0 failures) and a probe described in the [follow-up response](response-to-owner-packet-9e6affa.md) §2. Dispositions use the review's three categories.

| Review item | Governance deliverable | Disposition |
|---|---|---|
| 1. Authorization snapshots checked against source evidence | Principle (§2), resolution split (§2.1), rules EC-01 to EC-11 (§4), acceptance cases EM-00 to EM-05 (§4.2), authorization lifecycle (§5) | **Specification corrected; awaiting implementation verification** (validator and governance verifier). **Awaiting a named decision:** GD-24 (resolver port and module additions, Mohab), GD-28 (dispatch claim records, Nour and Mohab) |
| 1. Contradictory evidence cannot establish a verified binding | Certification outcomes (§1), effect on the verdict (§4.1), `INV-11` and `INV-12` | **Specification corrected; awaiting implementation verification.** GD-25 decided on the governance side |
| 1. Executed dispatch under an unverified authorization | Treated as a critical finding (contract §6.3) | **Awaiting a named decision:** GD-26 (extends `DEC-1`; Ahmed, Alaa, plan owner) |
| 2. Recovery identity (key, digest, result ownership, request, payload) | Rules RC-01 to RC-05 (§6.4), cases RM-01 to RM-03 and RM-06 | **Specification corrected; awaiting implementation verification** |
| 2. Valid outcome combinations; uncertain timeout stays `UNKNOWN` | Outcome table (§6.2), rule RC-06, case RM-04 | **Awaiting a named decision:** GD-27 (Ahmed reviews the interpretation; Mohab confirms the `side_effect_state` values). The conflict with Ahmed's `side_effect_committed = false` on timeout is open |
| 2. One terminal result per invocation; recovery separate and append-only | Rules RC-07 and RC-08, case RM-05 | **Specification corrected; awaiting implementation verification** |
| Separation of failure capture from certification | §1 | **Specification corrected**; the fixture classes need Mohab's agreement |
| Package, hashes, report, runner (items 3 to 7 of the review) | Not governance's | Out of scope for this revision; Mohab and the other named owners |

Names that were taken from review text in earlier revisions are now confirmed against Trace Schema v1.9: `trusted_source_verified`, `recovery_of_call_id`, `recovery_of_result_id` and `side_effect_state` exist with the value sets in contract §4.5. Open with Mohab: the stub label in `check_mode`, `execution_scope`, the approval-record supersession fields and the consumption currentness fields (follow-up response §2).