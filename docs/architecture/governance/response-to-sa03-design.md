# Governance review of the approval-record design (OD-04 / SA-03)

| | |
|---|---|
| **Status** | Governance's scoped disposition on Mohab's implementation of the approval-record design, dated 2026-11-24. It records governance's own assessment against the governance contract (§5.3, `GD-04`, `GD-32`). It is not another owner's acceptance, it does not ratify anything for Nour or Ahmed, and it does not approve or merge a pull request |
| **Reviewer** | Mohamed Elnaggar, `packages/governance-engine` |
| **Date** | 2026-11-24 |
| **Answers** | Mohab's message of 2026-11-24, which waits for governance's decision on `OD-04` / `SA-03`, and his closeout in PR #32 at `d43af58c51f5cafa96b577e354e019c21e4aa67b` |
| **Reviewed** | `week_2.md` (`41be9a32…d5c4`, sections 3.1, 3.2, 11 and 18), `updated_schemas_v18.md` (`6ad921e6…1d28`, the same hash as Mohab's manifest) and `validate_s1_01_schema_v1_11.py` (`403197a4…2e65`, the approval checks from `_validate_approval_event` to the dispatch-claim consumption check), all as downloaded from that commit |
| **What was run** | Nothing. This is a read-only comparison of documents and source. The validator and its 105 regression cases were **not** executed by governance, so the figures in Mohab's report are his |
| **Governance revision** | 0.6 with the 23 to 24 November addenda ([governance-contract.md](governance-contract.md) §5.3, [policy-truth-tables.md](policy-truth-tables.md) at baseline B2) |

Status words: **ACCEPT**, **AMEND** (a small required correction, given in §2) and **OPEN** (waiting on a named owner or a later gate).

---

## 1. Disposition by item

| # | What governance asked for (§5.3, `GD-32`) | What Mohab implemented | Disposition |
|---|---|---|---|
| 1 | Records are append-only, each with an opaque `record_version` and a monotonic `decision_record_seq`; the current record has the highest sequence | `record_version` and `decision_record_seq` on every `approval` event, repeated inside `trusted_source`, with an agreement check (`ERR_APPROVAL_EVIDENCE_MISMATCH`) | **ACCEPT** |
| 2 | Every record after the first points at the record it supersedes (`supersedes_record_version` and `supersedes_decision_record_seq`) | `supersedes_approval_id` instead. The record identity is the `approval_id`, and each record also carries its own version and sequence, so the chain can be resolved by lookup. The validator enforces the link only for a `CANCELLED` record that follows an `APPROVED` one | **ACCEPT** the representation; **AMEND** A2 |
| 3 | A terminal record does not point forward, because records are never edited | `superseded_by_approval_id` exists next to `supersedes_approval_id`. It is null in every stored event, and the `ALLOW` check refuses a non-null value | **AMEND** A3 |
| 4 | `DENIED` and `CANCELLED` are terminal; `APPROVED` may only be followed by `CANCELLED` | Any later record after a `DENIED` or `CANCELLED` record on the same approval request is refused (`ERR_APPROVAL_TERMINAL_STATUS_VIOLATION`). A `CANCELLED` record after `APPROVED` must supersede it with a higher sequence and a new version. The validator has **no rule against a `PENDING`, `DENIED` or second `APPROVED` record after an `APPROVED` one** | **ACCEPT** the terminal rule (it is stricter than the proposed wording and equals the contract's table); **AMEND** A1 |
| 5 | Record statuses are `PENDING`, `APPROVED`, `DENIED`, `CANCELLED`; `EXPIRED` is never produced | Six-value enum with `EXPIRED` and `STALE_REVISION`. Agreed on 2026-11-24 (`GD-35`): `EXPIRED` stays reserved and unused in v1.18 and is dropped in the next revision; governance reports an unexpected `EXPIRED` as `ERROR`; `STALE_REVISION` is reported as `FAIL / APPROVAL_STALE_REVISION` | **ACCEPT**, with the `GD-35` handling |
| 6 | Remove the trace-start lower bound on the decision time; keep the consistency chain; wall-clock order is informational and the order of decisions follows `decision_record_seq` and the trace `sequence_number` | The lower bound is removed. The validator keeps ISO-8601 syntax and the chain `approval_timestamp <= verified_at <= approval event timestamp`, with `verified_at` not later than the trace end. Order is decided by sequence (`ERR_APPROVAL_SUPERSEDED_SEQUENCE`) | **ACCEPT** (`SA-04` as proposed) |
| 7 | Currentness is `CURRENT`, or `STALE` with a reason, checked at the check and again at the atomic consumption | Version and sequence are compared at the check (`ERR_STALE_RECORD_VERSION_AT_CLAIM`) and at the consumption (`ERR_STALE_RECORD_VERSION_AT_CONSUMPTION`), with the observed and bound values on the consumption record (`SA-02`). **No stale reason is carried.** In the `base_only` profile the approval half of the consumption check is skipped | **ACCEPT** the checks; **AMEND** A4 |
| 8 | A revocation after dispatch does not rewrite the authorization or the outcome (`V08`) | `post_consumption_supersession` records the later `CANCELLED` record and its link; the historical action keeps its binding and stays `AUTHORIZED_AND_COMMITTED` (`POS-29`, `NEG-77`) | **ACCEPT** |
| 9 | Governance receives a resolved order signal, so it stays independent of platform storage | The platform adapter will derive the order from the current decision sequence and pass the signal. The derivation is not written down | **ACCEPT** the design; **AMEND** A5 |
| 10 | Exact binding of revision, supplier, amount, currency, level, calculation reference and policy version (`V02`) | `bound_*` fields, `bound_calculation_ref`, `approval_level` and `policy_version` on the `approval` event. `approved_amount_ceiling` is a separate field with `ceiling >= bound_amount` (`ERR_APPROVAL_CEILING_EXCEEDED`); `bound_amount` is still the exact amount that governance compares with the proposal | **ACCEPT** |

## 2. Required amendments (all small, for Mohab)

**A1. After `APPROVED`, only a revocation may follow.** For one approval request, the record after an `APPROVED` record may only be a `CANCELLED` record that supersedes it. A later `PENDING`, `DENIED` or second `APPROVED` record is refused. The contract's transition table allows exactly this (`APPROVED` to `CANCELLED`), and the validator currently checks only the `CANCELLED` case. Add the negative cases.

**A2. The supersession link on every later record.** Every record after the first for an approval request carries a non-null `supersedes_approval_id` that names the record immediately before it by sequence; the first record carries null. Today the link is checked only for a revocation.

**A3. `superseded_by_approval_id` is derived, never stored.** A stored record is never edited, so this field cannot be written back. Say that it is a read-model value, keep it null in every stored `approval` event, and refuse a non-null value there, not only at an `ALLOW`. The forward view for the dashboard comes from the registry.

**A4. A stale reason beside the code.** When a check or a consumption is stale, record why, using governance's vocabulary: `APPROVAL_RECORD_SUPERSEDED`, `APPROVAL_NO_LONGER_APPROVED`, `SUPPLIER_RECORD_SUPERSEDED`, `REQUEST_REVISION_CHANGED` and `POLICY_BUNDLE_CHANGED`. Add it to the consumption record and to the approval evidence reference, so the dashboard and the evaluators can tell the cases apart. Also state that the `base_only` profile is for the S1-03 base-evidence check only: in that profile the validator does not check the approval version or sequence at the consumption, so a revocation between the check and the dispatch is not caught. Procurement traces must use the `provisional_draft` profile, or its ratified successor, as the default.

**A5. Write down the order signal.** Document how the adapter derives the signal it passes to governance. Proposed meaning of "decided before the proposal": the observed `approval` event precedes the `tool_proposal` by trace `sequence_number`, **and** its record is the current record, the one with the highest `decision_record_seq` for the approval request. If this cannot be shown (a future-dated, conflicting or unorderable record), the signal says so. Wall-clock time never decides.

## 3. Governance's position on ratification

**Governance ratifies its side of `OD-04` / `SA-03` on the condition that A1 to A5 are applied.** Until then the fields stay provisional, as Mohab's §18 already labels them. The joint sign-off with Nour and the release of `RC-07` for Ahmed's evaluators remain theirs to give. Governance's side stops being a blocker as soon as Mohab confirms the amendments.

Mohab and governance agree to batch these into one post-review update, together with the `GD-35` `EXPIRED` cleanup and the new `enforcement_outcome` value for a confirmed no-effect after dispatch (`GD-36`).

## 4. What this response does not claim

- It does not accept PR #32, approve a merge, or accept anything for another owner.
- Nothing ran. The validator and its regression suite were read, not executed, and no probe was run.
- It does not ratify the approval fields jointly. It states governance's side, with conditions.
- The design is a specification of evidence. It authorizes no approval endpoint, no replay of a write and no change to a decision already recorded.
