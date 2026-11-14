# Proposed OD-03 policy bundle ↔ corpus release pairing

**Owner:** Nour El-Rouby · **Date:** 2026-11-14 · **Status:** PROPOSED FOR INTEGRATION REVIEW; NOT INGESTED, INDEXED OR RUNTIME ENABLED.

## Identity and scope

| Role | Proposed identity | Exact source / SHA-256 |
|---|---|---|
| Governance bundle (`policy_bundle_version`) | `synthetic-procurement-policy-set-v0.1` | PR #28 `ce12629659bed86c0e1316c473626e0c835a8882`: `docs/architecture/governance/policy-configuration/procurement-policy-set-v0.1.yaml` · `0a585b08464e65ccb803e76238c0222a8a36d69df62c6ab75b3455f63a0f3678` |
| Approval rule within that bundle | `synthetic-procurement-approval-v0.1` / `PROC-APPROVAL-01` | Same YAML; the rule identity is distinct from the corpus source version. |
| Candidate policy knowledge-base release (`policy_kb_version`) | `synthetic-procurement-policy-kb-v0.1` | [Exact two-document membership proposal](proposed-policy-kb-v0.1.json) · SHA-256 `c81ca938c5b16f1bcee341617ffc89583919d19eb62f0024dcffc7b91f597911` |
| Approval policy source text | `synthetic-procurement-approval-text-v0.1`; stable `document_id=doc-001`, `source_id=src-001`, new `source_version=review-r2` | [doc-001-v2.txt](documents/doc-001-v2.txt) · `69e9834b728663fafb94f1731cae14d9af69eaba8988ead41a8f77343b8e1812` |
| Supplier companion | `doc-002`, `src-002`, unchanged `review-r1` | [doc-002.txt](documents/doc-002.txt) · `9e0b3f630b9c89bf76968f1506b1b9cd54369130f012dc397cb563702881a33e` |

The new release is a **procurement policy retrieval slice**, proposed for `search_policy()` and evidence binding. Its two members are exactly `doc-001@review-r2` and `doc-002@review-r1`. It is not the seven/eight-document general RAG review snapshot, a deployed `policy_kb_version`, or an index build. Keep `corpus-review-s01/s02` and their `doc-001@review-r1` symbolic A/T/C questions unchanged. Do not serve `doc-001@review-r1` and `doc-001@review-r2` together under this release. The stable document/source IDs plus new source version let citations identify the revised text without rewriting historical claims. Preserve the whole new paragraph as one protected unit (code-point span `[0,950)`); its amount condition, equality exception, supplier and urgency caveats must remain together. The configured chunker must verify actual token size before ingestion; no token count is asserted here.

The review input [policy-text.txt](../policy-candidate/od03-v0.1/policy-text.txt), SHA-256 `9132b79e4f3c68f9b6de858eeeb7994cf37b67e220bd1bc849fa3d9f12b4b578`, remains the historical paired text for Mohamed's original 31-case result. Its header says the candidate was not accepted. The new `doc-001@review-r2` is the proposed corpus-facing text for the now accepted **synthetic values**; it states the same USD-only, strict `> 5000.00`, manager-level and no-waiver rules without claiming that a release is active. The earlier [symbolic source manifest](source-manifest.json), SHA-256 `c83a2cae8315806e9b81ae561c478b3b08329632fdee64fe89cfde924004a7c2`, and `doc-001@review-r1`, SHA-256 `5e1a0e46a4df89a8e655d98e559ee814f6e59046848821f7016eb5125add0d3f`, remain historical review fixtures. No corpus membership is silently changed.

## Proposed binding at integration

1. Select the governance YAML by its pinned `policy_bundle_version` and reviewed file digest. Its `content_hash: computed-by-loader` placeholder is **not** that file digest and is not evidence of a computed runtime canonical hash. Mohab defines/validates the canonical loader digest, transport and retention convention.
2. Select this exact policy-retrieval membership by `policy_kb_version`, including both document IDs, source versions and content hashes. A missing member, duplicate active `doc-001` version, source hash mismatch or absent verified index identity must fail closed; do not fall back to the symbolic snapshot or another policy revision.
3. A `search_policy()` result carries the selected source ID/version, exact span and content hash as retrieved evidence. The application must check the pinned bundle and release identity against the trusted execution context. Model-generated text or a citation cannot authorize a purchase or alter the threshold. The governance rule calculates approval from trusted inputs and binds the result to the exact request/supplier/amount/currency under OD-04.
4. Mohab confirms how the canonical trace transports `policy_bundle_version`, `policy_kb_version`/per-policy `policy_version`, document/source versions, and any runtime content digest. The proposed release ID is never written as an observed effective index/configuration until a loader and retrieval run confirm it.
5. A changed threshold, comparator, text, membership, source version, normalization rule or document content requires a new immutable bundle and/or release version, rebuilt embeddings/index if text or membership changes, and rerun citation and boundary fixtures. No incompatible versions share the same release ID. General RAG corpus changes require their own version/snapshot review.

## Offline consistency evidence

The independent governance checker from PR #28 `ce126296` (script SHA-256 `792ae8425bb30dd9c38cf825b8a4c119d76cbd72bdea692c47b41b251130846f`) was run against its unchanged YAML, the committed 31-case `truth-table.json` (SHA-256 `94624cdb8f47223113190b6870cd0a75e1172e6479606691107701a5d6bfc86c`) and the **new** `doc-001-v2.txt`. Result: `PASS`, 31/31 cases agree, configuration valid and text consistent. This is an offline specification check; it does not validate doc-002 runtime eligibility, ingestion, retrieval, citation emission, approval validity, pgvector availability or live policy execution.

Reproduce from a checkout with PR #27's candidate inputs and PR #28's governance artifacts, writing temporary results outside the repository:

```bash
review_dir=$(mktemp -d)
git show ce12629659bed86c0e1316c473626e0c835a8882:docs/architecture/governance/policy-configuration/procurement-policy-set-v0.1.yaml > "$review_dir/procurement-policy-set-v0.1.yaml"
git show ce12629659bed86c0e1316c473626e0c835a8882:docs/architecture/governance/policy-configuration/verify_od03_independent.py > "$review_dir/verify_od03_independent.py"
python "$review_dir/verify_od03_independent.py" --config "$review_dir/procurement-policy-set-v0.1.yaml" --truth-table docs/architecture/reference-applications/policy-candidate/od03-v0.1/truth-table.json --policy-text docs/architecture/reference-applications/corpus-review/documents/doc-001-v2.txt --output "$review_dir/result.json" --source-note 'OD-03 candidate policy KB pairing, offline only'
```

## Review and activation gates

| Owner | Exact response needed |
|---|---|
| Mohamed | Confirm the new corpus-facing text remains consistent with `PROC-APPROVAL-01`, the accepted synthetic values, and supplier/urgency semantics. This does not alter his YAML or claim a runtime acceptance. |
| Mohab | ACCEPT/AMEND the release/trace field mapping, canonical digest and source/version transport, eligibility and index-version checks. Confirm that `doc-001@review-r2` cannot coexist as an eligible version with `review-r1` in the same pinned release. |
| Alaa / Ahmed | Confirm version lineage and that the new source/release receives a separate dataset/split and citation-fixture impact review; no old symbolic expected answer is silently re-labelled as USD-specific. |
| Nour | After those responses, confirm the exact release membership and corpus/index build plan, regenerate affected policy retrieval/citation examples and manifest hashes, then record any observed ingestion and application compatibility separately. |

The YAML still has `runtime_enabled: false` and null operative acceptance fields. `index_version` is null in the proposed membership. These remain so until implementation and joint integration review; an offline 31/31 result cannot enable the policy or constitute OD-14 acceptance.
