# Governance response to the review of PR #29

| | |
|---|---|
| **Status** | Governance's scoped disposition on Nour's review request, dated 2026-11-16. It records governance's own assessment against the governance contract. It is not another owner's acceptance and it does not approve or merge the pull request |
| **Reviewer** | Mohamed Elnaggar, `packages/governance-engine` |
| **Date** | 2026-11-16 |
| **Answers** | Nour's request to review PR #29 at `ebdefc194d397804dca8238caf64842cb367ecaf`, focusing on `workflow.py`, `mock_tools.py` and `test_procurement_boundaries.py` |
| **Reviewed** | The three files above (and the scaffold test `test_procurement_scaffold.py` they import) at exactly that commit. Later commits on the pull request were not reviewed |
| **Governance revision** | 0.6 with the 13 and 14 November addenda: [governance-contract.md](governance-contract.md), [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md), [policy-truth-tables.md](policy-truth-tables.md) |
| **What was run** | Seven read-only probes against the code, in a scratch folder outside the repository. Nour's pytest suite was **not** run (pytest was not installed on the reviewing machine), so her validation record is not reproduced by governance |

Status words: **ACCEPT**, **AMEND** (required correction and cases given) and **OPEN** (waiting on a named owner or a later gate).

---

## 1. The three behaviors Nour asked about

| Behavior | Disposition |
|---|---|
| Missing, pending, denied or cancelled approval prevents PO dispatch | **ACCEPT** for the current execution: no proposal, check or dispatch happens, and the state stays `APPROVAL_PENDING`, as in Trace Schema v1.9. **OPEN** for durability across executions (item 3 below) |
| Changed request or mismatched approval or supplier evidence prevents continuation | **ACCEPT** for request-field mismatches and for a stale supplier or approval version at dispatch. **AMEND** for the currentness inputs and evidence completeness (items 4 to 6) |
| `UNKNOWN` PO outcome stays unresolved, no false completion, no second dispatch for the same key | **ACCEPT** for no completion and no second effect in the mock. **AMEND**: a rerun still calls the creating tool and the check again (item 2), and failures after dispatch are not recorded (item 1) |

Also consistent with the contract: an ineligible supplier stops at `POLICY_CHECKED` with no check and no purchase order (the SC-03A behavior, [policy-truth-tables.md](policy-truth-tables.md) §6), and the approval calculation is a supplied fixture with no threshold logic in the application (contract §5.1).

## 2. Required corrections and cases

**1. A failure after dispatch must become `UNKNOWN` (AMEND).** Probes: when `create_purchase_order` raises `RuntimeError`, the exception leaves `Workflow.run` with no event and no result. A result with status `ERROR` returns `FAILED` / `PO_RESULT_UNCONFIRMED`, which asserts "no effect" without authoritative proof. The contract says a non-timeout exception after the claim is `UNKNOWN_OUTCOME` / `RECOVERY_PENDING` (`OC-8`, `RM-07`), and an `ERROR` without authoritative proof stays `UNKNOWN` (`OC-12`). Cases: (a) a raised exception gives `RECOVERY_PENDING`, state `PO_CREATION`, no `final_response`; (b) status `ERROR` gives the same; (c) `FAILED` is reachable only through a recovery lookup that returns `RESOLVED_ABORTED`.

**2. A same-key rerun must not call the creating tool or consume another check (AMEND).** Probe: after an `UNKNOWN`, a second `run()` called `create_purchase_order` twice in total and `check_purchase_order` twice. `dispatch_count` stayed at 1 only because the mock ledger intercepts. With a real tool the second call is an original-write replay (GD-27, GD-29, `ERR_WRITE_RETRY_FORBIDDEN`), and a second check is a second claim on a root-wide single allowance. Needed: a read-only lookup path separate from the creating tool (`RECOVERY_LOOKUP`). Cases: `STILL_UNRESOLVED` stays `RECOVERY_PENDING`; `RESOLVED_COMMITTED` with matching key, digest and payload reaches `COMPLETION` with no new create call; `RESOLVED_ABORTED` gives `FAILED`; a lookup with a different key, digest or payload is refused (`RC-03` to `RC-05`). Assert `create_purchase_order.call_count == 1` and `check_purchase_order.call_count == 1`.

**3. Terminal approval across executions (OPEN).** Probe: `DENIED`, then `APPROVED` for the same `approval_request_id` in a separate run, ends `SUCCEEDED` with a dispatch. The scaffold documents this limit. The contract rule (V04, `SA-03`) refuses a later `PENDING` or `APPROVED` after `DENIED` or `CANCELLED`. Needed: `supersedes_record_version` and `supersedes_decision_record_seq` on the approval record. Cases: `APPROVED` then `CANCELLED` stops; `CANCELLED` then `APPROVED` is refused; a new attempt needs a new request revision and a new approval request. This stays OPEN until Mohab answers `SA-03`; a fixture-level version can be added now.

**4. Currentness at dispatch (AMEND).** `current_versions` compares only the supplier and approval record versions. `SA-02` and V06 also compare `decision_record_seq`, the request revision and the policy bundle, and they report why: `APPROVAL_RECORD_SUPERSEDED`, `APPROVAL_NO_LONGER_APPROVED`, `SUPPLIER_RECORD_SUPERSEDED`, `REQUEST_REVISION_CHANGED`, `POLICY_BUNDLE_CHANGED`. A single `BOUND_EVIDENCE_STALE` loses that. Cases: approval cancelled between check and dispatch, sequence advanced, supplier version changed, revision changed, bundle changed. Each suppresses dispatch and keeps the state `APPROVED`. Also, `MockTools.check_purchase_order` copies the versions from its inputs, so the workflow's comparison of authorization against evidence can never fail. A case needs the gate to return different versions.

**5. Policy version comparison (AMEND).** The workflow requires `calculation.policy_version == policy.policy_version`. The first is a rule or bundle identity and the second is the corpus release (`policy_kb_version`). Probe: with realistic distinct values the run halts `CALCULATION_UNRESOLVED`. Compare through the accepted bundle-to-release pairing instead. Cases: paired but different ids proceed; an unpaired release gives `POLICY_VERSION_MISMATCH`.

**6. Evidence completeness (AMEND, small).** Probe: an empty supplier `record_version` still ends `SUCCEEDED`; it should fail closed (`EC-01`). The approval record also lacks the `calculation_ref` binding that V02 requires. Cases: an empty supplier version halts; a different `calculation_ref` on the approval gives `APPROVAL_BINDING_INVALID`.

**7. Labeling and coverage (OPEN, notes).**
- The mock gate checks only approval and an allow flag, not the supplier or stage policy. Tag it `check_mode = STUB_CONTRACT_TEST` (`SA-07`) so no enforcement-acceptance claim rests on it (OD-06).
- Read tools do not pass through a gate (GD-02, S2-01).
- The ledger compares the whole request, not the business-payload digest.
- `IDEMPOTENCY_CONFLICT` is an exception and not a typed result.
- The purchase-order result has no `side_effect_state`, so combinations `OC-9` to `OC-12` cannot be checked.

## 3. Overall disposition

**AMEND, not a rejection.** Governance has no objection to merging this as an isolated scaffold if its documentation states these limits. Items 1 and 2 should be fixed before anyone cites it as evidence for OD-12-OUTCOME or OD-12-RETRY. Atomic claim, restart recovery and durable enforcement stay out of scope, as the scaffold states.

## 4. What this response does not claim

- It does not accept PR #29, and it is not an acceptance by any other owner.
- Nothing ran against a runtime, a database or the governance engine. The probes are local and read-only.
- The mocks do not establish durable enforcement, and nothing here authorizes automatic write replay.
