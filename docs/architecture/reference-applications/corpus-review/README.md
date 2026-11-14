# Synthetic corpus review specification

Version 1.0 · 2026-11-02 · PROPOSED, NOT RATIFIED. Eight authored English documents, not a complete training corpus, retrieval benchmark, live index or organizational policy. Their numbers and procedural statements are synthetic examples only. Procurement uses symbolic T and C; no production threshold/currency is assigned.

**Separate OD-03 pairing draft — 2026-11-14:** [Proposed bundle ↔ release mapping](policy-bundle-pairing-v0.1.md) and [two-document membership](proposed-policy-kb-v0.1.json) pin the accepted *synthetic* USD 5000.00 rule to new `doc-001@review-r2` text and unchanged `doc-002@review-r1`. An independent offline check passes 31/31 against Mohamed's YAML. This candidate is not part of the s01/s02 symbolic snapshots below, and has no index or runtime release acceptance.

The owning specification is [rag-contract.md](../rag-contract.md#synthetic-corpus-specification--review-v1). [Source manifest](source-manifest.json) records exact text hashes, identities, source versions, categories, visibility, spans and conditional environment status. [Review cases](review-cases.json) contains independent relevance/conflict/expected-outcome annotations; it must not enter inference or be indexed as source text.

| Document | Category | Review purpose |
|---|---|---|
| [doc-001](documents/doc-001.txt) | Procurement | Above/equal/below symbolic T, currency/config uncertainty and urgency exception |
| [doc-002](documents/doc-002.txt) | Procurement | Supplier eligibility and no override by user assertion |
| [doc-003](documents/doc-003.txt) | HR | Planned-leave notice with emergency exception and approval caveat |
| [doc-004](documents/doc-004.txt) | Internal operations (`ops`) | Maintenance-window exception with authorization condition |
| [doc-005](documents/doc-005.txt) | FAQ | Device support routing distinct from purchase authorization |
| [doc-006](documents/doc-006.txt) | HR | Ten-day receipt rule in baseline snapshot |
| [doc-007](documents/doc-007.txt) | HR | Fifteen-day receipt rule in separate conflict snapshot |
| [doc-008](documents/doc-008.txt) | FAQ | Visitor process: irrelevant evidence for device/expense queries |

Snapshot s01 contains seven documents; s02 adds doc-007. The conflicting pair comprises distinct applicable sources, not two active versions of one document. There is no verified supersession, date or authority precedence; the answer must abstain on that conflict. Snapshot membership is authored test context, not a measured retriever result.

Each short source is proposed as one protected semantic unit, including conditions, exceptions, negation and authorization caveats. Preserve source-local contiguous spans and exact text. Token counts are deliberately unavailable until the configured chunker and native provider counting are verified. If a unit exceeds the existing cap, hold it for source restructuring/review; never publish a fragment that drops its exception. q-008 deliberately illustrates that rejected fragment. Any source rewrite creates a new version, hashes, spans and dependent fixture review.

No embeddings, database writes, index construction, authorization service or model generation was executed. The manifest fields are review notation mapped to the RAG contract; Mohab/Alaa must agree canonical serialization. Existing prompt-pack sources are separate fixtures, not silently added to these snapshots. Ahmed reviews relevance/sufficiency and Alaa reviews grouping before dataset use; group variants and controls before any split assignment.
