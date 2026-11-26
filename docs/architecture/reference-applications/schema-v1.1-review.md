# Application review of Mohab's Trace Schema Draft v1.1

**Historical review:** retained for revision history and the original requirement crosswalk. Use the [Draft v1.5 review](schema-v1.5-review.md) for the latest supplied revision, verified fixes and remaining findings; the [v1.2 review](schema-v1.2-review.md) is also historical. Findings below describe v1.1 and must not be read as current unresolved defects without comparison.

Review date: 2026-11-02. Reviewer scope: Nour-owned application requirements. Status: CHANGES REQUIRED; no shared approval claimed. This is a review addendum, not a replacement canonical schema.

Reviewed input: uploaded `updated_schemas.md`, document status “Draft v1.1 — S1-01 Review Corrections Applied”; its SHA-256 is in the review manifest. This is an uploaded document, not proof of a repository commit or running implementation. Comparison baseline: current [tool](procurement-tool-contracts.md), [state](procurement-state-contract.md), [RAG](rag-contract.md) and [evidence](trace-evidence-contract.md) contracts, themselves pending shared acceptance. Resolve conflicts jointly rather than treating either draft as an approved API.

## Improvements and remaining corrections

| Review item | Observed improvement | Required resolution / acceptance check | Owner and reviewers |
|---|---|---|---|
| Tools, §4.2.1 | Five signatures and result shapes documented | Align arguments/results with application contract; decimal-string total_amount and item_description; runtime authorization context separate from model arguments; all five valid/invalid examples match agreed signatures | Mohab; Nour/Mohamed |
| State/stage, §4.1 / WT1 | Separate app_state, policy_stage and execution_status | Waiting/recovery/halt must preserve last valid workflow state; agree enum mapping; check proposal in APPROVED then atomic bound PO_CREATION transition/single dispatch; confirmed result permits COMPLETION | Mohab; Nour/Mohamed |
| Unknown outcome/recovery, §4.3 | UNKNOWN and original call/result recovery links | Prohibit SAFE_IDEMPOTENT_RETRY for this Procurement PO recovery; read-only reconciliation only, no redispatch or second terminal result; missing ledger leaves UNKNOWN | Mohab; Mohamed/Ahmed/Nour |
| Approval, §4.4.1 | Revision, supplier, amount/currency, level, policy and provenance fields | Align opaque revision IDs, exact decimal money, DENIED/CANCELLED and validity rules; verify trusted request/decision identity and immutable authorization inputs | Mohab/Mohamed; Nour |
| Walkthroughs, §7 | Four parseable JSON trace objects | WT3 starts APPROVAL_CALCULATED→PO_CREATION; restore APPROVED and supporting evidence. WT2/WT3 must include prerequisite records or explicitly identify excerpts and linked preceding evidence. Seeded failure behavior must remain labelled, not silently corrected into a positive case | Mohab; Nour/Ahmed |
| Citations, §7.1 | Exact text/version/selected context and claim spans | clm_proc_01 claim has span [96,150), not [98,152). Define zero-based Unicode code-point, end-exclusive offsets and the exact text basis for source spans. Check quote/slice/version/selected membership independently of semantic support | Mohab; Nour/Ahmed |
| Review tracking, §8 | E/WG closure table present | Preserve original IDs or accept an explicit crosswalk; distinguish drafted correction from verified fit and named acceptance. “Agreeing Owners” is not evidence that those people reviewed these exact bytes | Mohab; all scoped reviewers |

## Original E01–E27 crosswalk

The right column locates related content in v1.1's renumbered table. This is a review navigation aid, not a claim of equivalent meaning or full coverage. Keep the left IDs in application fixtures and acceptance records until a shared migration is accepted.

| Original application ID / requirement | Related v1.1 table row(s) | Remaining acceptance focus |
|---|---|---|
| E01 request | E01 | Normalized request and runtime identity |
| E02 model call | E24 | Actual rendered context/response and unavailable telemetry |
| E03 policy retrieval | E10 | Exact tool contract and source versions |
| E04 RAG retrieval | E22 | Effective query, filters and configuration |
| E05 source evidence | E22 | Immutable content/hash/version/locator |
| E06 scores/ranks | E22, E04 | Score kind/direction and missingness |
| E07 selection/sufficiency | E23, E26 | Selected/rejected evidence, facets, conflict and ordering |
| E08 normalization | E01, E16 | Raw→normalized values, exact money and revision types |
| E09 fine states | E06, E09 | Attempted vs accepted transitions and valid sequence |
| E10 policy stage | E07 | Agreed map/version at proposal/check/dispatch |
| E11 supplier | E11 | Requested vs returned ID, normalized status, provenance |
| E12 approval calculation | E12 | Known/unresolved requirement and configured threshold basis |
| E13 approval submission | E13 | Submission distinct from approval and observation |
| E14 approval observation | E14 | Exact binding/status/validity and trusted source |
| E15 proposal | E15 | Proposal distinct from invocation |
| E16 argument validation | E16 | Raw malformed payloads plus strict parsed validation |
| E17 bound pre-tool request | E15, E17, E18, E20 | No equivalent complete row: argument digest, state/request revision, evidence and atomic dispatch binding still require agreement |
| E18 policy result | E17, E18 | Per-policy applicability/error distinct from verdict |
| E19 suppression | E19 | No fabricated invocation or tool-body result |
| E20 actual execution/result | E20, E21 | Business outcomes, original/new effect, no duplicate terminal result |
| E21 Procurement final | E26 | Candidate vs delivered claim and exact supporting result |
| E22 RAG answer | E24, E25, E26 | Candidate/delivery/context correspondence |
| E23 citation | E25 | Exact claim→selected source/version/span→visible marker |
| E24 abstention | E26 | Evidence deficiency distinct from runtime failure |
| E25 pending/error/recovery | E08, E21, E26 | Orthogonal run outcome, preserved original effect |
| E26 provenance | E02, E03, E04 | Configuration/source/code lineage and explicit absence |
| E27 scenario isolation | E27 | Approved inference projections exclude labels/recipes/qrels |

Original WG-01≈v1.1 WG-01; original WG-02≈v1.1 WG-02 plus dispatch binding; original WG-03≈v1.1 WG-03 plus tool types; original WG-04 spans v1.1 WG-04/05; original WG-05 maps to v1.1 WG-06; original WG-06 maps to v1.1 WG-07; original WG-07 needs the separate E27 projection review; original WG-08 overlaps v1.1 WG-04/08 but still requires raw/candidate/delivered evidence. These are partial topical mappings, not automatic closures.

## Reproduced checks and limits

Four complete trace JSON objects parse. This checks syntax only; the §4.6 configuration fragment is a fragment, not an invalid complete trace. A direct Python text slice reproduces the WT1 claim mismatch and the corrected [96,150) slice. Canonical validation, actual tool execution, semantic retrieval quality and owner acceptance were not performed. Ahmed's supplier examples and Malak's dashboard behavior are separate deliverables and are not closed by this review.
