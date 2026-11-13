# Governance response to Nour's follow-up (owner packet at 9e6affa)

| | |
|---|---|
| **Status** | **Final governance disposition of Mohamed Elnaggar for the items listed below, dated 2026-11-14.** It is scoped: it records governance's own dispositions only. It is not another owner's acceptance, and a general approval of this package accepts nothing that is not listed below. Items marked PENDING or **Not decided** stay open for the named people. Reissued from the draft that Nour received earlier, which lacked the repository files |
| **Reviewer** | Mohamed Elnaggar, `packages/governance-engine` |
| **Date** | 2026-11-14 (first issued 2026-11-12) |
| **Answers** | Nour's recent emails: the five numbered requests, the request for the response file, the configuration and the check together with two reconciliations against Mohab's Draft v1.8, and the 9 November email on the shared mapping and Malak's TRD-22/23 question |
| **Reviewed baseline** | Owner packet at `9e6affaa6d2f9bfca675e63e1c536d47005cd74d` (PR #27). The OD-03 candidate files are identical at `479cab0`, `9e6affa` and `a62f4e7` |
| **Schema reviewed** | Trace Schema Draft **v1.9** (Mohab; package received 12 Nov 2026), files below. Governance names now follow it (GD-31) |
| **Governance revision** | 0.6: [governance-contract.md](governance-contract.md), [decision-flow.md](decision-flow.md), [policy-truth-tables.md](policy-truth-tables.md), [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md), [policy configuration](policy-configuration/procurement-policy-set-v0.1.yaml) |

Status words: **ACCEPT**, **AMEND** (replacement wording given) and **PENDING** (waiting on a named person). "Governance-local" means this response is the disposition. "Joint" means another owner's reply is needed.

**Plan approver.** I do not name one. Nour's register records that the designated plan approver is not named, and I am not substituting for that role. Everything that needs plan approval is marked as such.

---

## 1. Summary

| ID | Disposition | Scope | Remaining dependency |
|---|---|---|---|
| Request 1: artifacts | **Provided** (§2) | Governance-local | Nour integrates the accepted values into the application examples |
| OD-03 values | ACCEPT rows 1 to 5; row 6 amended (as recorded by Nour on 9 Nov) | Governance-local | Mohab: transport and digest. Nour: fixtures |
| OD-04 V01, V02, V03, V07, V08 | ACCEPT | Governance-local | none new |
| OD-04 V04, V05 | ACCEPT amended wording; **AMEND the schema representation** (SA-03, SA-04) | Joint with Mohab | Mohab's mechanism choice (§3) |
| OD-04 V06 | AMEND mechanism (SA-02) | Joint with Mohab and Nour | Fence and atomicity: runtime and Mohab |
| OD-12-CLAIM | ACCEPT v1.9 lifecycle; **AMEND** SA-01, SA-02 | Joint with Mohab and Nour | §3 |
| OD-12-RETRY | ACCEPT: no original-write replay | Replay authority governance-local; modes joint | Mohab, Nour |
| OD-12-OUTCOME | ACCEPT in v1.9 names | Joint with Ahmed, Mohab, Nour | Ahmed's labels (OD-09) |
| OD-12-BUDGET | ACCEPT governance rows; exhaustion wording amended to `EXECUTION_BUDGET_EXHAUSTED` | Joint | Alaa's workload review |
| OD-05-MAP / R16-07 | 13 rows confirmed, 3 amended, 3 pending (§4) | Joint with Mohab | SA-05 to SA-09 |
| TRD-22 / TRD-23 | ACCEPT: policy stage and policy-check result are distinct (§4) | Governance-local; Malak confirms display | Malak |
| Cancelled approval and the actions it gates | ACCEPT `CANCELLED` as an authoritative record; link by reference (§4) | Joint with Mohab | SA-03 |
| OD-02 | ACCEPT (unchanged) | Governance-local | **Plan approver** |
| OD-06 | ACCEPT own wording (§5) | Governance-local | **Plan approver**; Mohab adds the stub label (SA-07) |
| OD-16 | ACCEPT; representation aligned with Ahmed's evaluator contract (§5) | Governance-local | **Plan approver**; Ahmed's wording |
| OD-09 and GD-26 | Governance position stated. **Not decided** | Joint | Ahmed, Alaa, **plan approver** (§6) |

---

## 2. Request 1: actual governance artifacts

I cannot give a pull-request or commit link from this file, because a file cannot contain the commit that carries it. The files are in `docs/architecture/governance/` at the head of the branch that carries this reply; the link goes in the email.

| Artifact | Path | SHA-256 (LF-normalized) |
|---|---|---|
| Governance response to owner packet 0.14 | `docs/architecture/governance/response-to-owner-packet-0.14.md` | identified by the commit |
| This follow-up | `docs/architecture/governance/response-to-owner-packet-9e6affa.md` | identified by the commit |
| Policy configuration, version `synthetic-procurement-policy-set-v0.1` | `docs/architecture/governance/policy-configuration/procurement-policy-set-v0.1.yaml` | `cde2631f8d62b6cff1240bf3b46d350805f975d2352718aac28160907707528b` |
| Independent 31-case check | `docs/architecture/governance/policy-configuration/verify_od03_independent.py` | `792ae8425bb30dd9c38cf825b8a4c119d76cbd72bdea692c47b41b251130846f` |
| Result of the check | `docs/architecture/governance/policy-configuration/od03-independent-check-result.json` | identified by the commit |
| Your `truth-table.json` (input, unchanged at `479cab0`, `9e6affa`, `a62f4e7`) | `docs/architecture/reference-applications/policy-candidate/od03-v0.1/truth-table.json` at commit `479cab0` | `94624cdb8f47223113190b6870cd0a75e1172e6479606691107701a5d6bfc86c` |
| Your `policy-text.txt` (the paired policy text used in my run; same commits) | `docs/architecture/reference-applications/policy-candidate/od03-v0.1/policy-text.txt` at commit `479cab0` | `9132b79e4f3c68f9b6de858eeeb7994cf37b67e220bd1bc849fa3d9f12b4b578` |

Hashes are of the file content with CRLF normalized to LF, so they are the same on a Windows checkout and equal the committed Git blob content. The two input hashes equal the committed-blob hashes at `479cab0`, `9e6affa` and `a62f4e7` (re-checked on 14 November). These two files are on your pull-request branch `docs/nour-week1-review-014` (PR #27); they are not on `dev` at the time of writing, so the command below runs from a checkout that contains them.

**Command** (repository root; PyYAML 6.0.3 is already a development dependency):

```bash
uv run --locked --all-packages python docs/architecture/governance/policy-configuration/verify_od03_independent.py \
  --truth-table docs/architecture/reference-applications/policy-candidate/od03-v0.1/truth-table.json \
  --policy-text docs/architecture/reference-applications/policy-candidate/od03-v0.1/policy-text.txt \
  --output od03-independent-check-result.json
```

**Result:** `PASS: 31/31 cases agree; configuration_valid=True; policy text consistent=True`. Exit code 0. Python 3.13.7, PyYAML 6.0.3. On 14 November I re-ran the script on the two inputs exactly as committed at `a62f4e7`; it passed again and produced the same result file. **The script's hash changed:** on 14 November I removed one unused `f` prefix and reformatted the file so that it passes the repository's `ruff check` and `ruff format --check` (CI runs both on the whole repository). The logic and every case result are unchanged. The hash in the table is the current file's; the earlier version you received had `d644f76c98bf5c84c91e17b35ea0e72a74095072c63ae7878a3281e4ab9a9a8e`.

What the check does: it loads the YAML, applies the governance rules (strict `>`, exact decimal strings, exact case-sensitive currency, stop on missing or invalid configuration, text or version or request-context conflict), compares every case with your expected outcome, and confirms that your paired `policy-text.txt` states the same threshold, currency, comparator wording, level, precision, no-rounding, no-conversion and no-waiver of other checks. It is independent of your `verify_candidate.py`: it shares no code with it.

It is not vacuous. I also ran it against two deliberately wrong copies of the configuration: threshold `5000.01` gave 30 of 31 and an inconsistent policy text; comparator `GTE` gave 4 of 31 with an invalid configuration. Both exit with code 1. I repeated both on 14 November with the same results.

**Identity for integration.** Policy bundle `synthetic-procurement-policy-set-v0.1` is the value of `policy_bundle_version` (contract §4.5 row 6). The approval level is `manager`, not the illustrative `MANAGER_L1` in the v1.9 fixtures. The pairing of the bundle with the corpus release (`policy_kb_version`) is assigned by you at integration, as your candidate README says; governance supplies no corpus release. The YAML is unchanged since the 9 November response.

**Limits.** This is a specification check. It is not the governance engine, not a runtime result and not an acceptance record, and the YAML still has `runtime_enabled: false` and null acceptance fields.

---

## 3. Request 2: OD-04 and OD-12 agreement with Mohab (Trace Schema v1.9)

Mohab's v1.9 already contains most of what governance asked for in rev 0.4: bound record versions, `decision_record_seq`, a separate `dispatch_claim_consumption` record and a mapping table. I read §4.4.3 and the validator, ran the validator on his specification (2,602 assertions, 0 failures, as he reports), and compared it with governance rev 0.5. Where we agree I say so. The remaining differences are listed as schema amendments **SA-01 to SA-09**.

### 3.1 The four representations you asked for

**Terminal `DENIED` and `CANCELLED`.** ACCEPT the statuses; **AMEND** the representation (SA-03). v1.9 has `approval_status` but no field saying one record replaces another, and I found no rule in the validator source that a terminal status stays terminal. Replacement: every approval record after the first carries `supersedes_record_version` and `supersedes_decision_record_seq`; after `DENIED` or `CANCELLED` for an `approval_request_id` no later record may be `PENDING` or `APPROVED` (proposed code `ERR_APPROVAL_TERMINAL_REOPENED`); a revocation is a `CANCELLED` record whose `supersedes_*` fields point at the revoked `APPROVED` record. Contract §5.3.

**Authoritative record-sequence ordering.** ACCEPT v1.9: order is `decision_record_seq` in the approval registry and the trace `sequence_number`, never wall-clock time (`ERR_APPROVAL_SUPERSEDED_SEQUENCE`). Supplier records are ordered by their own source; the two sequences are never compared with each other. One correction (SA-04, below).

**Approval and supplier version currentness at claim.** ACCEPT binding the versions at the check. **AMEND** (SA-02): v1.9 verifies currentness at the check (`currentness_verified` inside `authorization_snapshot.dispatch_claim`), but the claim is consumed later and the consumption record records only the bound versions. Replacement: add to `dispatch_claim_consumption` the versions observed **at consumption**: `latest_observed_supplier_record_version`, `latest_observed_approval_record_version`, `latest_observed_decision_record_seq`, and `currentness_at_consumption` (`CURRENT`). A consumption whose observed versions differ from the bound ones is rejected with the existing `ERR_STALE_RECORD_VERSION_AT_CLAIM`, with a reason beside it (`APPROVAL_RECORD_SUPERSEDED`, `APPROVAL_NO_LONGER_APPROVED`, `SUPPLIER_RECORD_SUPERSEDED`, `REQUEST_REVISION_CHANGED`, `POLICY_BUNDLE_CHANGED`).

**The immutable claim-consumption record.** ACCEPT v1.9's `dispatch_claim_consumption` with the answers you asked for:

| Question | Answer |
|---|---|
| Owner | The runtime (yours) emits it; the platform (Mohab) persists it. Governance neither allocates nor consumes the claim |
| Fields | Those in v1.9 §4.4.3 item 5 (`consumption_record_id`, `dispatch_claim_id`, `root_request_id`, `request_revision`, `preallocated_at_proposal_id`, `bound_authorization_check_id`, `bound_action_verdict`, `transition_state_event_id`, `resulting_state_revision_id`, `consumed_by_call_id`, `bound_supplier_record_version`, `bound_approval_record_version`, `consumption_status`, `redispatch_or_reset_permitted`) plus the SA-02 fields |
| Ordering | `policy_check` (`ALLOW`) then the `agent_state` transition into `PO_CREATION` carrying the record, then the `tool_call`. The check event is never edited |
| Uniqueness | One claim identity per root (`dclaim_<root_request_id>`), so one consumption per root across checks, revisions and traces (`ERR_PO_DUPLICATE_DISPATCH_CLAIM`), and one use of each `authorization_check_id` (`ERR_AUTH_CHECK_REUSED`) |
| Atomic relationship | The record is evidence of one runtime step: verify currentness, record the transition, consume the claim, emit the record and the `tool_call`. The serialization or fence that makes it indivisible is the runtime's and Mohab's. Governance claims no race safety, and the validator checks recorded evidence only |
| Separate record? | In v1.9 it is an object with its own id inside the transition event, mirrored in `execution_budget_telemetry.dispatch_claim_ledger`. Governance accepts that as the separate immutable record provided the original check and its events are unchanged. If you read "separate" as a separate event, say so; governance has no objection either way |

This replaces my rev 0.5 wording "one claim identity per proposal attempt" with Mohab's root-scoped identity, which makes root-wide uniqueness structural. Contract §4.7.

### 3.2 Your second reconciliation: timestamp chronology and continuation

Your question: the validator enforces timestamp chronology including approval time relative to trace start; which sequence and currentness evidence is authoritative, how is an existing approval observed across a continuation, and which timestamp checks stay informational.

I confirmed the concern by running the validator. With the approval decision moved to about one hour **before** the trace starts, everywhere it appears so that all embedded copies stay equal, the validator reports exactly one failure, `ERR_APPROVAL_CHRONOLOGY_INVALID`, on `tr_proc_101.e27`. The cause is the lower bound `trace.started_at <= approval_timestamp` in the validator source. An approval decided before a continuation trace begins is the normal case for an existing approval, so the rule would reject the continuation itself.

| Check | Class | Governance position (SA-04) |
|---|---|---|
| ISO-8601 UTC syntax of every timestamp | Structural | Keep (`ERR_TIMESTAMP`) |
| Each event inside this trace's `started_at` and `completed_at` | Structural | Keep for events produced in this trace, including `verified_at` |
| `approval_timestamp <= verified_at <= policy_check.timestamp` | Consistency | Keep (`ERR_APPROVAL_CHRONOLOGY_INVALID`) |
| `trace.started_at <= approval_timestamp` | Wrongly rejects an earlier decision | **Remove.** Lower bound is the approval request's own submission time |
| Wall-clock order of approval against proposal or revocation | Depends on clocks | **Informational only.** Order is `decision_record_seq` and trace `sequence_number` |

Observation across a continuation: the `approval` event in the continuation trace is a read-only observation (`OBSERVE_APPROVAL`) of an existing record. It carries that record's `approval_request_id`, `record_version`, `decision_record_seq` and `approval_timestamp`, plus the continuation's `verified_at`, and must resolve to the same current record in governance's registry. One trace or linked traces is Mohab's choice; governance needs the record resolvable by `approval_request_id` and `record_version` from either. Contract §5.3.

### 3.3 Your first reconciliation: OD-12-CLAIM

Specified above (§3.1, last row of the table). One naming amendment remains (SA-01): v1.9's `claim_status_at_check = AVAILABLE_CLAIMED_ON_ALLOW` reads as if the claim were taken at the check, which contradicts the agreed lifecycle in which only the runtime consumes after `ALLOW`. Rename it `AVAILABLE_AT_CHECK`; `NOT_CLAIMED_BLOCKED` stays. The validator source does not enforce this value, so the rename affects the specification and fixtures only.

### 3.4 Schema amendments and mechanism choices still open

| ID | Item | Governance position | Mechanism choice for Mohab | Evidence for closure |
|---|---|---|---|---|
| SA-01 | `claim_status_at_check` value | Rename to `AVAILABLE_AT_CHECK` | None beyond naming | Specification and fixtures updated |
| SA-02 | Currentness at consumption | Add the four fields | Where the "latest observed" values are read from (approval registry, supplier directory) | Fixture with matching versions passes; fixture where the approval was superseded between check and consumption fails with `ERR_STALE_RECORD_VERSION_AT_CLAIM` |
| SA-03 | Supersession and terminal rule | Add `supersedes_*` and a terminal rule | Field names; whether the rule is a new code | Fixture `APPROVED` then `CANCELLED` passes; `CANCELLED` then `APPROVED` fails |
| SA-04 | Chronology lower bound | Remove; wall-clock order informational | Lower bound taken from approval request submission time | The probe above passes; an approval decided after `policy_check` still fails |
| SA-05 | `approval_status` values | Four values; `EXPIRED` never produced; `STALE_REVISION` moves to the currentness result | Keep or drop the two names | Enum and fixtures updated |
| SA-06 | Criticality spelling | v1.9 text lists `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`; its fixtures use lowercase `critical` | One spelling | Specification and fixtures agree |
| SA-07 | Stub label | `check_mode` has only `ONLINE_PRE_TOOL`; GD-06 needs `STUB_CONTRACT_TEST` | Add the value | Enum updated |
| SA-08 | `execution_scope` | Recorded only; proposed `scenario_metadata.execution_scope` | Placement | Field exists and is stripped from inference inputs |
| SA-09 | Where `enforcement_outcome` is stored | Governance derives it (contract §6.3); not a trace field | Post-run analysis record | Joint with Ahmed and Alaa |

**Observation, not an amendment.** v1.9 defines `evaluated_policies[].policy_version` as the policy-corpus release, so the per-policy rule versions in the governance configuration are not separate trace fields. Governance accepts that: they are inside the bundle identified by `policy_bundle_version` and recoverable from its content hash (contract §4.5 row 6).

**Package identity, for Nour's exact-hash record.** The SHA-256 of the files as I received them is: `updated_schemas_v9.md` `a06c837b4a718562f966d34db73baee9843241955e4e6b85ce9a0352d6eb80d4`; `validate_s1_01_schema_v1_9.py` `444c8003d0040866dc443e669e7c12fb8caedbe13444f89d1168d9cdf63028a8`; `run_s1_01_regression_suite.py` `c90265aca1430eae194418cc1b58527a03283d9d2787a6fc3c1bec9475c20e7d`; `s1_01_validation_report.json` `9ec4aa676665b5403589d18350ef620e7bbeaa61aee0af7b5391298183435286`. The hashes recorded **inside** that report do not equal these. For the validator and the runner they match only after removing carriage returns and adding a final newline. For the specification I found no normalization that reproduces the recorded value (`f5929600…`). Governance reviewed the bytes received. This is for Mohab and Nour to reconcile.

---

## 4. Request 3: translation table, TRD-22/23, and the cancelled approval

**Translation table.** Governance confirmed the table against v1.9. Contract §4.5 has all 19 rows. Summary:

| Result | Rows |
|---|---|
| **Confirmed** (13) | 1 verdict, 2 verdict basis, 3 per-policy result, 4 reason and evidence, 6 policy version (with a clarification), 7 stage, 9 record order, 10 authorization binding, 12 digest, 13 effect and recovery states, 14 blocked call, 17 verified flag, 19 finding codes |
| **Amended** (3) | 5 criticality (SA-06), 8 approval statuses (SA-05), 11 claim and consumption (SA-01, SA-02) |
| **Pending** (3) | 15 stub label (SA-07), 16 execution scope (SA-08), 18 enforcement outcome (SA-09) |

**Verdict names, concretely:** `verdict` is `action_verdict`; the basis values are `ALL_APPLICABLE_PASSED`, `MANDATORY_POLICY_FAILED`, `FAIL_CLOSED_ON_POLICY_ERROR`; `results[].status` is `evaluated_policies[].policy_result`; `policy_set_version` is `policy_bundle_version`; `workflow_stage` is `policy_stage`; `binding` is `authorization_snapshot`; a missing verdict is a `tool_suppression` with `suppression_source = POLICY_CHECK_ERROR_OR_TIMEOUT`. The retired governance names (`NO_VERDICT`, `ERROR_BLOCK`, `passed`, `pre_tool_verdict`, `BLOCKED_BY_POLICY`) are not used.

**TRD-22 and TRD-23 for Malak: ACCEPT, they are two distinct things** (contract §4.8). Policy stage is an input fact: where the workflow was when the action was proposed, checked and dispatched (`policy_stage`, `policy_stage_at_proposal`, `checked_policy_stage`, `policy_stage_at_dispatch`; four values). The policy-check result is the output: `action_verdict`, `verdict_basis` and the four-valued `policy_result` of the three mandatory policies.

| Dashboard element | Shows |
|---|---|
| TRD-22 (state transitions) | Previous and new fine state and the coarse stage, accepted versus attempted |
| TRD-23 (stage at each boundary) | The stage at proposal, check and dispatch as a plain label. Never as pass or fail |
| "Policy gate" tile | The verdict pill with its basis and the three policy rows. This is what Malak's tile already shows, and it should stay so |

The state-to-stage mapping belongs to your state contract. Governance owns only the allowlist by stage, which is in the bundle named by `policy_bundle_version`. Until you and Mohab define a version for the mapping itself, the dashboard shows the stage and the bundle version and invents no mapping version.

**`CANCELLED` is an authoritative approval status, and how it links to what it gates: ACCEPT** (contract §5.3). A cancelled record cannot point forward, because records are append-only. The link runs by reference: every gated action records the approval version it was checked against (`authorization_snapshot.approval_evidence_ref.approval_record_version`, `dispatch_claim.bound_approval_record_version`, `dispatch_claim_consumption.bound_approval_record_version`). The gated set is every action whose recorded approval version equals the `supersedes_record_version` of the `CANCELLED` record for the same `approval_request_id`. A stale dispatch that was stopped appears as a `tool_suppression`. This needs SA-03.

---

## 5. Request 4: exact wording for OD-06, OD-12 and OD-16

**OD-06. ACCEPT (governance-local); plan approver pending.** Minimum real-policy deliverable at S2-04: the three policies as pure functions implementing the accepted truth tables; an in-process pre-tool service that produces the v1.9 `policy_check` attributes (`evaluated_policies`, `action_verdict`, `verdict_basis`, `authorization_snapshot`) with `check_mode = ONLINE_PRE_TOOL`, idempotent replay by attempt and fail-closed behavior; unit tests for the truth tables; and one integration test in which the approval bypass is blocked by the real engine and the mock purchase order never runs. Not required at S2-04: database persistence (S3-03) and the platform adapter to the stored trace (evidence comes from the runtime snapshot through a test resolver). **When the stub stops qualifying:** once the S2-04 service is merged and callable from the S2-01 tool hook, no enforcement-acceptance claim (the bypass test, SC-03B) may rest on the stub. The stub stays only for isolated application unit tests, labelled `STUB_CONTRACT_TEST` once SA-07 adds the value. No calendar date is invented. Evidence for closure: written milestone and task mapping, the stub limits above, the plan approver's disposition.

**OD-12-RETRY. ACCEPT.** No automatic `CREATE_APPROVAL_REQUEST` or `CREATE_PO` write retry, which matches `ERR_WRITE_RETRY_FORBIDDEN`. A retry of a read-only tool is a new `attempt_id` with a fresh, separately bound check. Same key with a different payload is `IDEMPOTENCY_CONFLICT`. Any future replay needs a separately reviewed agreement. Contract §4.1, GD-29.

**OD-12-OUTCOME. ACCEPT in v1.9 names.** `UNKNOWN`, definitive no effect (`RESOLVED_ABORTED`, authoritative proof only), `ALREADY_EXISTING` (maps to checkpoint `COMMITTED_CONFIRMED`, no new effect), `STILL_UNRESOLVED`; a `RUNTIME_EXCEPTION` after the claim is a legitimate `UNKNOWN`; `COMPLETION` is invalid while the effect is unresolved. The full matrix is [evidence-consistency-and-recovery.md](evidence-consistency-and-recovery.md) §6.2 and the validator codes are §7.1.

**OD-12-BUDGET exhaustion. ACCEPT, amended.** Exhausting any pool before a purchase-order check or dispatch is a `tool_suppression` with `suppression_source = EXECUTION_BUDGET_EXHAUSTED`, `side_effect_state = NONE`, and no policy result. It is never a policy `FAIL` or an `ALLOW`. An exhausted recovery allowance holds the effect `UNKNOWN` for manual review. Governance owns no numeric budget.

**OD-16. ACCEPT; representation aligned with Ahmed's evaluator contract (GD-17).** A RAG trace has no pre-tool check and no `policy_check` event. Its post-run policy evidence is the `policy_conformance` evaluator result with `status = NOT_APPLICABLE` and a null score. Governance reason: `POLICY_NOT_APPLICABLE_TO_APPLICATION`, basis `application_type = rag`. It is distinct from `PASS` (satisfied), from evaluator `ERROR` (could not decide) and from `NOT_REQUESTED` (an application guard stopped the action before any check). The decision engine treats it as absent evidence, never as proof of compliance. This replaces my earlier wording of one row per policy. Plan approver confirms scope.

---

## 6. Request 5: GD-26 and OD-09 coordination

My governance disposition is kept separate from Ahmed's and Alaa's acceptance and from plan approval.

**GD-26 (governance position, not a decision).** A purchase order executed under an authorization that fails the consistency rules is a critical finding and fires `DEC-1`, because the mandatory control did not demonstrably authorize the action. Alternative: record the critical finding and route to `REVIEW`, non-approving either way. I recommend the first: `REVIEW` is for borderline quality, and an unverifiable authorization is not borderline. It extends `DEC-1` beyond the proposal's wording, so it also needs the plan approver.

| Case ([truth tables §7](policy-truth-tables.md)) | What needs agreement | Who | Governance position | Evidence for closure |
|---|---|---|---|---|
| DC-13, DC-14 | How `REALIZED` and `PREVENTED` map to failure labels; whether an attempted-and-prevented violation is `POLICY_VIOLATION` | Ahmed (OD-09) | `DEC-1` fires either way; labels are Ahmed's | Labelled examples with source references |
| DC-20 and `DEFINITIVE_NO_EFFECT` (named `NOT_REALIZED` when sent) | Label for a dispatch that conclusively had no effect | Ahmed | Distinct from `PREVENTED` | Same |
| DC-17, DC-19, `UNKNOWN` | Treatment of a non-terminal run or an uncertain outcome | Ahmed, Alaa | Incomplete evaluation, never `PASS` | Gate artifact with a null decision |
| DC-12 | A critical policy `ERROR`: Alaa's requirements treat `FAIL` or `ERROR` as a critical failure; governance records it as an incomplete evaluation (compliance could not be decided, never `PASS`) | Alaa, Ahmed | Keep distinct: `ERROR` is not a violation, and counting it as one distorts the policy-failure features and RQ4 counts. At Layer 1 both already `BLOCK` | Written choice and a gate example |
| DC-16 | How the comparison identifies an unsafe action the candidate allows and the baseline prevented | Alaa | `DEC-1` at release scope | Comparison field and example |
| DC-18 | An executed dispatch under an unverified authorization | Ahmed, Alaa, plan approver | GD-26 | Decision on option A or B |
| Ahmed's `policy_conformance` inputs | His document still names `passed`, `pre_tool_verdict` and `ERROR_BLOCK`, which v1.9 retired. The equivalents are `policy_result`, `action_verdict` and a `tool_suppression` with `POLICY_CHECK_ERROR_OR_TIMEOUT`. His `POL_MISSING_MANDATORY_PRE_TOOL_CHECK` finding still applies | Ahmed | Update his input fields to v1.9 | Evaluator contract revision |

---

## 7. What this response does not claim

- No teammate has accepted anything, and I give no sign-off of another owner's scope.
- The plan approver is not named and is not substituted.
- Nothing ran against a runtime, a database, an approval service or the governance engine. The only executions are the 31-case configuration check (§2), Mohab's own validator on his specification, and the one chronology probe (§3.2).
- The v1.9 63-case regression suite was not run by governance.
- No numeric budget, threshold or tolerance is approved beyond the synthetic OD-03 values.
- Full OD-14 sign-off, adapter proof of read-only observation, atomic-claim and concurrency tests stay separate gates.
