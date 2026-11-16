# Governance response to the policy bundle and corpus pairing proposal

| | |
|---|---|
| **Status** | Governance's scoped disposition on policy meaning and retrieval coverage, dated 2026-11-16. It records governance's own assessment. It is not another owner's acceptance, enables nothing and is not OD-14 acceptance |
| **Reviewer** | Mohamed Elnaggar, `packages/governance-engine` |
| **Date** | 2026-11-16 |
| **Answers** | Nour's request for a scoped ACCEPT or AMEND on two points: whether the new `doc-001` text and the unchanged `doc-002` express the accepted synthetic rule, and whether `PROC-TOOL-STAGE-01` needs retrievable text |
| **Files reviewed** | At PR #27 commit `14ee4a24763ed515aeb1b0a1986893380f4f8f22`, under `docs/architecture/reference-applications/corpus-review/`: `policy-bundle-pairing-v0.1.md`; `proposed-policy-kb-v0.1.json` (`3fd76114ee93e20271cc2ae221dc3eaecc3fe666052b34a942b70fa5ed8ba9f1`); `documents/doc-001-v2.txt` (`69e9834b728663fafb94f1731cae14d9af69eaba8988ead41a8f77343b8e1812`); `documents/doc-002.txt` (`9e0b3f630b9c89bf76968f1506b1b9cd54369130f012dc397cb563702881a33e`) |
| **Compared against** | The governance YAML at PR #28 commit `ce12629659bed86c0e1316c473626e0c835a8882`, file hash `0a585b08464e65ccb803e76238c0222a8a36d69df62c6ab75b3455f63a0f3678` |
| **What was run** | The three file hashes above were recomputed and match Nour's record. The independent checker ([policy-configuration/verify_od03_independent.py](policy-configuration/verify_od03_independent.py)) was re-run on `doc-001-v2.txt` and gave `PASS: 31/31 cases agree; configuration_valid=True; policy text consistent=True`. That check only confirms that eight phrases are present, so the rest of the wording was compared with the YAML and the truth tables by hand |

Status words: **ACCEPT**, **AMEND** and **OPEN**.

---

## 1. The text: ACCEPT both

**`doc-001@review-r2`: ACCEPT.** It expresses the accepted rule:
- USD only, strict `>` threshold `5000.00`, manager level above it (`AP-03`, `AP-10`), and equality outside the rule (`AP-02`).
- An approved supplier, the permitted workflow and the independent pre-tool check remain mandatory either way, and urgency waives none of them.
- Missing or conflicting configuration, unsupported currency, unresolved policy version and a source-versus-configuration disagreement all stop progression and never establish that approval is unnecessary.

Two optional, non-blocking clarifications for a later revision: spell out "plain-decimal" (no sign, spaces, separators, exponent or leading zeros, cases `C17` to `C22` of the OD-03 truth table), and add "and policy version" to the approval binding. The gate enforces the binding whether or not the text lists it.

**`doc-002@review-r1`: ACCEPT as the supplier companion.** Only `APPROVED` passes; `NOT_APPROVED`, `UNKNOWN` and a missing record fail (`SU-02` to `SU-05`); a user statement is not evidence; urgency does not waive it. Two non-blocking observations for a future revision, not a reason to reissue this one:
- It describes the application-level stop. `PROC-SUPPLIER-01` itself is evaluated at the purchase-order check (`SU-08` makes it `NOT_APPLICABLE` for other tools), so the text could add that the independent check also blocks the order.
- It does not mention a supplier id mismatch, unresolved supplier evidence or that the record must be the current one (`SU-06`, `SU-07`).

## 2. `PROC-TOOL-STAGE-01`: no retrievable text required

It should stay an executable governance rule without a source in this knowledge base, for three reasons:
- The gate enforces it deterministically from the allowlist in the bundle (`TS-01` to `TS-09`).
- Retrievable text would be a second source of truth that could drift from the YAML, which creates a new text-versus-configuration conflict class.
- `search_policy` exists to give applicability evidence for the request, not to carry every executable rule.

Conditions:
- The workflow must not treat the stage rule's lack of a source as `POLICY_UNAVAILABLE`.
- A request for that policy id returns "not retrievable" and never a fabricated `MATCHED`.
- Its `evaluated_policies[]` entry carries the corpus release as `policy_version` (Trace Schema v1.9: `synthetic-procurement-policy-kb-v0.1`). Its rule identity lives in the bundle.
- Human-readable explanation comes from the reason codes `TOOL_ALLOWED_IN_STAGE` and `TOOL_NOT_ALLOWED_IN_STAGE` and the allowlist.

If a requirement later needs the agent to cite the stage rule, governance will provide the wording and the rule-to-source relationship then.

## 3. A consistency note for the version mapping

The pairing proposes `search_policy`'s `policy_set_version` as an alias to `policy_bundle_version`. Governance's translation ([governance-contract.md](governance-contract.md) §4.5, row 6) and Trace Schema v1.9 treat `search_policy.data.policy_set_version` as the **corpus release**, which is `policy_kb_version`. The bundle is a separate identity. Please do not alias them; Mohab confirms the transport mapping. Governance also agrees that:
- `doc-001@review-r1` and `doc-001@review-r2` must not both be eligible in one pinned release.
- A corpus release that is not paired with the active bundle is `POLICY_VERSION_MISMATCH`.

## 4. What this response does not claim

- It does not accept the release, enable the policy or constitute OD-14 acceptance. The YAML keeps `runtime_enabled: false` and null acceptance fields.
- Ingestion, indexing, retrieval, citation emission and live policy execution were not run.
- Transport, version and digest representation are Mohab's separate review.
