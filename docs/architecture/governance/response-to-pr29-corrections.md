# Governance review of the PR #29 Procurement corrections

| | |
|---|---|
| **Status** | Governance's scoped disposition on the published corrections, dated 2026-11-18. It records governance's own assessment against the governance contract. It is not another owner's acceptance and it does not approve or merge the pull request |
| **Reviewer** | Mohamed Elnaggar, `packages/governance-engine` |
| **Date** | 2026-11-18 |
| **Answers** | Nour's request to review the published Procurement corrections in PR #29 at `9735513060b3caf7ec35fb210d0489d7153895bf` against governance's earlier seven findings, with ACCEPT or AMEND and remaining conditions |
| **Earlier findings** | [response-to-pr29-review.md](response-to-pr29-review.md), made at `ebdefc194d397804dca8238caf64842cb367ecaf` |
| **Reviewed** | `workflow.py` (`44f759eb…309f`), `mock_tools.py` (`b63c621d…1bd3`), `test_procurement_boundaries.py` (`37353c56…7a62`), `test_procurement_scaffold.py` (`647029c2…cf7c`) and Nour's record `reviews/mohamed-pr29-procurement-2026-11-16.md` (`c2e5aa98…ba8a`), all at exactly that commit. The RAG files in the same commit are Ahmed's review and were not reviewed here |
| **What was run** | A read-only probe script against the extracted source, in a scratch folder outside the repository: 27 cases covering the seven findings, the restart case and an `ALREADY_EXISTS` replay. The repository pytest suite was **not** run by governance, so the validation record in Nour's file (100 tests, Ruff, mypy, import contracts) is hers and is not reproduced here |
| **Governance revision** | 0.6 with the 13 to 18 November addenda ([governance-contract.md](governance-contract.md), [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md), [policy-truth-tables.md](policy-truth-tables.md)) |

Status words: **ACCEPT**, **AMEND** (a small required correction, given below) and **OPEN** (waiting on a named owner or a later gate).

---

## 1. Disposition of the seven findings

| # | Earlier finding | Disposition | What the probes showed |
|---|---|---|---|
| 1 | A failure after dispatch must become `UNKNOWN` | **ACCEPT** | A raised exception and a result with status `ERROR` both end in state `PO_CREATION`, status `RECOVERY_PENDING`, reason `UNKNOWN_PO_OUTCOME`, with no `final_response` event. `FAILED` is reachable only through the read-only recovery lookup with `RESOLVED_ABORTED` and an explicit abort tombstone (`OC-8`, `OC-12`, `RM-07`) |
| 2 | A same-key rerun must not call the creating tool or consume another check | **ACCEPT** for the mock, with two **AMEND** items (§2.1, §2.2) and an **OPEN** durability item | After an `UNKNOWN`, a rerun leaves the counts at one create and one check. `STILL_UNRESOLVED` stays `RECOVERY_PENDING`; `RESOLVED_COMMITTED` completes with the recovered purchase order id and no new create; `RESOLVED_ABORTED` gives `FAILED` / `DEFINITIVE_NO_EFFECT`. A different key for the same request, or a changed payload under the same key, is a typed `BLOCKED` / `IDEMPOTENCY_CONFLICT` before any check or write. A rerun after a success returns the same purchase order id with no second effect |
| 3 | Terminal approval across executions | **ACCEPT** at fixture level, **OPEN** for durability | `DENIED` and then `APPROVED` for the same approval request id in a later run stays `APPROVAL_TERMINAL`, with no check and no dispatch. The memory lives in the mock instance only, as the scaffold states. The `supersedes_*` fields are still not on the approval record; `SA-03` is Mohab's |
| 4 | Currentness at dispatch | **ACCEPT**, with one **AMEND** (§2.3) | Six distinct stop reasons, each with state `APPROVED`, no create call and the single check already spent: approval cancelled (`APPROVAL_NO_LONGER_APPROVED`), sequence advanced and approval version changed (`APPROVAL_RECORD_SUPERSEDED`), `SUPPLIER_RECORD_SUPERSEDED`, `REQUEST_REVISION_CHANGED`, `POLICY_BUNDLE_CHANGED`. A gate that returns different supplier or approval versions gives `AUTHORIZATION_BINDING_INVALID`. The gate-versus-evidence comparison can now fail |
| 5 | Policy version comparison | **ACCEPT** with a condition (§3) | Paired but different ids proceed; an unpaired bundle halts `POLICY_VERSION_MISMATCH` before any check or dispatch |
| 6 | Evidence completeness | **ACCEPT**, with a non-blocking wording note (§2.4) | An empty supplier record version halts with no check and no dispatch. An approval with a different `calculation_ref` gives `APPROVAL_BINDING_INVALID` |
| 7 | Labeling and coverage | **ACCEPT** for the label and the typed conflict, **AMEND** for the effect-state values (§2.1), **OPEN** for the rest | The policy-check event carries `check_mode = STUB_CONTRACT_TEST` (`SA-07`), so no enforcement acceptance rests on the stub (`OD-06`). `IDEMPOTENCY_CONFLICT` is now a typed result on the recovery path. Read tools still have no gate (`GD-02`, `S2-01`), and the mock still compares whole requests rather than business-payload digests; the scaffold documents both |

## 2. Required corrections (small)

**2.1 Effect-state values on the purchase-order event (AMEND).** The success path emits `side_effect_state = "KNOWN"`. That is not a Trace Schema v1.9 value. The set is `NONE`, `COMMITTED`, `ALREADY_EXISTING` and `UNKNOWN` (contract §4.5). Emit `COMMITTED` for a confirmed `CREATED` and `ALREADY_EXISTING` for a confirmed replay, and keep `UNKNOWN` as is. Add the value to a test so the application event keeps its meaning when the adapter maps it.

**2.2 Committed recovery without evidence (AMEND).** A `RESOLVED_ABORTED` is accepted only with `EXPLICIT_ABORT_TOMBSTONE_FOUND`, but a `RESOLVED_COMMITTED` is accepted with a purchase order id and no resolution basis (the mock's committed recovery sets none). The same strictness should apply both ways: require `COMMITTED_RECORD_FOUND` (`RC-03` to `RC-05`) before completing, and have the recovery result echo the bound idempotency key and request or payload identity so the workflow can verify the binding and not only trust the lookup. Missing evidence stays `RECOVERY_PENDING`. The scaffold's own test for incomplete recovery evidence covers an aborted result without the tombstone and a committed result with no purchase order id. Add a committed result that has an id but no `COMMITTED_RECORD_FOUND` basis, which the probes show completes the run today.

**2.3 Gate-side overrides (AMEND, test coverage).** The mock can make the gate return a different supplier or approval version, but not a different `decision_record_seq` or policy bundle. The workflow does compare both and returns `AUTHORIZATION_BINDING_INVALID` (probed with a gate that returns them), so this is a coverage gap in the mock and tests, not a code defect. Add the two overrides and two cases.

**2.4 Wording (non-blocking).** An empty supplier record version halts as `SUPPLIER_INELIGIBLE`, but the supplier may be `APPROVED`. A separate reason such as `SUPPLIER_EVIDENCE_INCOMPLETE` would keep the dashboard and the evaluator from reading it as an eligibility failure.

## 3. Remaining conditions and open items

- **Version pairing (finding 5).** `policy_pairing_valid` is a fixture. The real pairing must come from the accepted bundle-to-corpus pairing, not from an alias of `policy_set_version` to `policy_bundle_version` ([response-to-policy-bundle-pairing.md](response-to-policy-bundle-pairing.md) §3). Transport, version and digest representation are Mohab's.
- **What `None` from the recovery lookup means (OPEN, durability).** The workflow treats `None` as "no claim for this root" and reruns the whole path. If the ledger is lost (probed by clearing the mock's ledger and root keys, which simulates a restart with no durable store), the same key reaches a second create and a second check, and the run completes with a second purchase order. The scaffold states it has no durable or atomic claim, so this is not a defect of the scaffold. It is the condition for citing it: a consumed claim with no outcome record must return `STILL_UNRESOLVED` and never `None`. That belongs to the atomic claim and restart tests (`OD-12-CLAIM`, `OD-12-OUTCOME`, `SA-02`).
- **A new observation: a replay without an original reference.** A purchase-order result with status `ALREADY_EXISTS` completes the run even though it carries no `original_result_ref`. The evidence document (`OC-5`, §6.6) says a replay with no resolvable original reference is a consistency finding. Add the reference to the purchase-order result, and treat a replay without it as `UNKNOWN`. Probed with a creating tool that returns `ALREADY_EXISTS` and no reference: the run ended `SUCCEEDED`.
- **Still open, as the scaffold states:** terminal approval and supersession across executions (`SA-03`); atomic consumption and currentness proof (`SA-02`); read-tool gating and the real policy gate (`OD-06`, `S2-01`); business-payload digest identity; restart and concurrency tests; the canonical effect fields.

## 4. Overall disposition

**ACCEPT as an isolated, synthetic scaffold, with the AMEND items in §2.** My earlier condition was that items 1 and 2 be fixed before anyone cites the scaffold as evidence for `OD-12-OUTCOME` or `OD-12-RETRY`. They are fixed at mock level. The scaffold may now be cited as evidence for the mock's ordering, early-stop, no-false-completion and no-second-effect behavior only, and only after §2.1 and §2.2 are made. It may not be cited as evidence for durable terminality, atomic claim, restart recovery, enforcement or any runtime behavior.

## 5. What this response does not claim

- It does not accept PR #29, approve a merge, or accept anything for another owner.
- Nothing ran against a runtime, a database or the governance engine. The probes are local and read-only, against the code as extracted from the commit.
- The repository tests were not run by governance. Nour's validation record is hers.
- The mocks do not establish durable enforcement, and nothing here authorizes automatic write replay.
