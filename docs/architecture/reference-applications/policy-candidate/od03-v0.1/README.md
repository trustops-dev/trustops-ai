# OD-03 — synthetic approval policy candidate 0.1

**Historical application candidate 0.1 — proposed 2026-11-05, governance values accepted 2026-11-14.** Mohamed’s final response supplies `procurement-policy-set-v0.1.yaml`, version `synthetic-procurement-policy-set-v0.1`, and accepts USD only, threshold `5000.00`, strict `>`, `manager`, positive decimal strings and no FX. [Exact-revision record and independent result](../../reviews/mohamed-7c26168-governance-response.md).

The candidate JSON, paired policy text and 31-case fixtures retain their historical input identities. The supplied governance checker at PR #28 `7c26168` agrees with all 31 committed cases. Mohab transport/digest agreement, Nour bundle/corpus pairing, source ingestion and runtime activation remain pending. The earlier [email response record](../../reviews/mohamed-479cab0-od03-response.md) is historical.

## Proposed configuration

| Parameter | Candidate | Reason / boundary |
|---|---|---|
| Policy identity | PROC-APPROVAL-01 | Existing approval-policy concept; no new policy introduced |
| Candidate policy version | synthetic-procurement-approval-v0.1-proposed | Distinct from historical demo-policy versions and any eventual accepted version |
| Supported currency | USD only | Matches existing illustrative Procurement fixtures; not a currency decision inferred from team location |
| Threshold | USD 5000.00 | Reuses the illustrative P03 policy amount to minimize example migration; the prior example is not approval of this value |
| Comparator | Strict greater than, A > T | Preserves the existing proposed “exceeds” rule |
| Required approval level | manager | Single existing baseline level; no director/finance tiers or escalation introduced |
| At or below threshold | approval_required=false; approval_level=null | No fabricated approval ID, approval record or human approval |
| Above threshold | approval_required=true; approval_level="manager" | A requirement, never an approval grant or tool authorization |
| Amount input | Positive finite plain-decimal JSON string | No JSON numeric value, bool, null, exponent, sign, separators or whitespace |
| Precision | Zero, one or two fractional digits accepted; two digits in normalized value | "5000", "5000.0" and "5000.00" represent the same exact amount |
| Rounding | None; reject more than two fractional digits | Reject "4999.999", "5000.001" and even "5000.000"; never round across the boundary |
| Currency conversion | Disabled | No implicit FX, fallback currency or case conversion; EGP and "usd" are unsupported in this candidate |
| Rule/config authority | Accepted, versioned governance configuration | Retrieved text is required evidence; a text/version/config conflict stops progression |
| Deployment | runtime_enabled=false | Review metadata is not a runtime enablement mechanism; accepted values must be integrated through governance's reviewed configuration |

The amount is the exact requested total already defined by the application contract. Do not multiply it by quantity, infer unit price, tax, freight, discounts or apply a tolerance. There is no new financial upper limit in this candidate; transport-size limits and canonical digest encoding remain shared-contract concerns. Preserve raw amount text alongside the normalized value. Numeric equality does not waive request revision, supplier or original-payload binding. Do not replace raw tool arguments or recompute canonical hashes under a new normalization rule without the accepted shared convention.

## Boundary truth table

These are conditional offline expectations for this proposal, not executed tool responses. T = 5000.00 USD; delta = 0.01 USD.

| Case | A | Relation | approval_required | approval_level | Consequence of this amount rule only |
|---|---|---|---|---|---|
| OD03-C01 | "4999.99" USD | A = T - delta | false | null | Approval not required by this rule; all other guards still apply |
| OD03-C02 | "5000.00" USD | A = T | false | null | Equality does not trigger the rule |
| OD03-C03 | "5000.01" USD | A = T + delta | true | "manager" | Await a valid, exactly bound approval; no PO on a pending/missing grant |
| OD03-C04 | "16000.00" USD | A > T | true | "manager" | Same single level; no unapproved second tier |
| OD03-C05 | "0.01" USD | 0 < A < T | false | null | Valid smallest proposed quantum |
| OD03-C06/07 | "5000" / "5000.0" USD | A = T | false | null | Exact normalized amount "5000.00"; retain original input |

The machine-readable table contains 31 cases, including invalid inputs, missing configuration, unsupported currency, policy-version mismatch, conflicting retrieved policy text, request-context mismatch, missing level and an accidental >= comparator. Invalid/unresolved cases carry no approval_required or approval_level value; unknown must not become false.

## Contract and trust boundaries

- The existing model-visible calculate_approval_level arguments remain request_id, total_amount and currency. This proposal adds no model arguments, tool endpoint, workflow state or canonical enum.
- candidate-config.json contains proposed review-file fields, not Mohab's schema or Mohamed's deployed policies/procurement.yaml format. Mohamed owns accepted rule values/calculation; Mohab owns canonical representation. The app consumes trusted calculation results rather than implementing a second policy engine.
- truth-table.json uses review_outcome and reason as offline review labels. CALCULATED refers to the documented conditional successful calculation. REJECT_BEFORE_CALCULATION means malformed input is rejected at the argument guard. UNRESOLVED means calculation cannot establish the requirement. These labels do not replace governance's ERROR, check-level CONTEXT_MISMATCH or ALLOW/BLOCK mappings; serialization remains joint work.
- Below/equal threshold does not imply a complete workflow, approved supplier, approval evidence, ALLOW, successful PO or reliability PASS. Required policy/state checks remain mandatory. Above threshold does not establish approval authority for any particular person; approver identity, validity, revocation and continuation remain OD-04.
- Invalid input, unsupported currency, missing configuration, version/text disagreement or mismatched trusted request stops progression. The illustrative matching flags in the review cases stand for conditions the trusted integration must verify; they are not model-controlled runtime fields.
- PRE_APPROVAL permission for the calculation tool remains OD-02. Budget/claim/replay decisions remain OD-12. No candidate value closes those gates.

## Corpus and version handling

policy-text.txt is the proposed matching synthetic source paragraph for this candidate. It is **not** ingested into the current corpus or substituted for corpus-review/documents/doc-001.txt. The current corpus retains symbolic A/T/C and its existing hashes. The source and configuration belong to this candidate version together; its source identifiers and runtime policy_version mapping must be assigned during accepted integration. Do not silently mix this candidate with demo-policy-v1-NOT-RATIFIED, v1.5/v1.6 review inputs or an existing index.

The supplied governance YAML at `7c26168` has been compared with the committed 31-case table through its independent checker, with 31/31 agreement. Nour next assigns the bundle/corpus pairing and updates affected examples when integration is agreed; Mohab verifies transport, digest and request binding. Update/rebuild an index only if corpus membership changes at the implementation stage. A later amendment requires a new candidate version and rerun boundary results; preserve this proposal as historical evidence.

## Historical review request to Mohamed

Please ACCEPT or AMEND candidate 0.1 for OD-03/GD-03, identifying each disputed row:

1. USD as the sole initial synthetic currency and threshold "5000.00".
2. Strict A > T, including no amount-triggered approval at equality.
3. One "manager" level above T and null below/equal; no extra tiers.
4. Positive plain-decimal strings, the stated normalization, rejection of excess precision and no FX/currency coercion.
5. Versioned governance configuration authority and stopping on missing/conflicting text, configuration, version or trusted request evidence.
6. The exact governance configuration representation and accepted version identifier to use; no assumption that this review JSON is the runtime schema.

Return reviewer, date, exact candidate file hashes, ACCEPT/AMEND for each row, replacement values/wording for amendments, and conditions still open. Do not mark approval validity, dispatch permission or runtime implementation accepted solely by accepting OD-03. The six-row request above is historical. Mohamed’s final scoped response is recorded at `7c26168`; the candidate’s original acceptance metadata remains part of the historical input.

## Offline reproduction

From the repository root, with Python 3.12:

```bash
review_reports=$(mktemp -d)
python -S docs/architecture/reference-applications/policy-candidate/od03-v0.1/verify_candidate.py --output "$review_reports/od03.json"
```

The standard-library helper checks the proposed configuration, paired policy text and all 31 expected outcomes. It writes outside the candidate folder, exits nonzero on disagreement and never loads credentials, calls tools, changes state or grants authorization. Its local arithmetic oracle is for specification review only and must not be imported by an application or governance runtime. PASS establishes internal agreement only; it is not Mohamed's acceptance or an integration result.

The candidate helper still reports its historical candidate metadata, including PENDING_MOHAMED. Current scoped acceptance is tracked in the final governance response record linked above.
