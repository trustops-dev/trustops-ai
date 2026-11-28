# Mohamed's scoped policy bundle ↔ corpus review

**Source:** Nour-supplied email received 2026-11-16; original send date and message ID unavailable. **Review basis:** PR #27 `14ee4a24763ed515aeb1b0a1986893380f4f8f22`, against PR #28 YAML `ce12629659bed86c0e1316c473626e0c835a8882`. This is a policy-meaning disposition, not loader, runtime, trace or OD-14 acceptance.

| Item | Mohamed's disposition | Application follow-up |
|---|---|---|
| `doc-001@review-r2` | ACCEPT; USD only, strict greater-than `5000.00`, `manager` above the threshold, equality outside the rule, no urgency waiver. Optional plain-decimal spelling and approval-policy-version text are later clarifications. | Keep the exact text/hash. No source/text change made here. |
| `doc-002@review-r1` | ACCEPT; only approved supplier passes; user assertion and urgency never substitute for verified status. Optional supplier ID/currentness and gate wording are later clarifications. | Keep the exact text/hash. |
| `PROC-TOOL-STAGE-01` | No retrievable text required. Executable allowlist rule in bundle; direct search is not retrievable, never fabricated MATCHED; lack of text does not stop normal workflow as POLICY_UNAVAILABLE. Gate entry carries corpus release `policy_version`; reason codes explain the result. | Preserve two-member KB, source-version pinning and separate executable rule identity. |
| Version mapping | AMEND proposed alias: `search_policy.data.policy_set_version` is `policy_kb_version` (corpus release), **not** `policy_bundle_version`. A non-paired release produces POLICY_VERSION_MISMATCH. | Corrected proposal and manifest metadata. Mohab still confirms the producer/trace/loader mapping. |

The source hashes recomputed locally match Mohamed's report: `doc-001-v2.txt` `69e9834b728663fafb94f1731cae14d9af69eaba8988ead41a8f77343b8e1812`; `doc-002.txt` `9e0b3f630b9c89bf76968f1506b1b9cd54369130f012dc397cb563702881a33e`. Mohamed reports the limited eight-phrase checker passed 31/31 and separately reviewed the text against YAML and truth tables. That scoped report is not a semantic proof by the checker or a runtime result.

The proposal JSON changed **only its incorrect version-mapping note**. Its exact file SHA-256 is now `5053a5593d963120b42e39c630a68e71f75f1b20ed5fc30449621b2717f74468`; membership and source files are unchanged. The previously reviewed proposal SHA-256 `3fd76114ee93e20271cc2ae221dc3eaecc3fe666052b34a942b70fa5ed8ba9f1` remains historical. Mohab's mapping, index/ingestion, Alaa/Ahmed lineage, and application runtime evidence remain open. The reviewed YAML has `runtime_enabled: false`.
