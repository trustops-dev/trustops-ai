# Application review of Mohab's Trace Schema Draft v1.2

**Historical review:** retained with its original findings and evidence. The latest supplied-draft disposition is the [2026-11-04 Draft v1.5 review](schema-v1.5-review.md); use its verified fixes and V15-01–07 findings for current handoffs. The v1.2 findings below are not a list of current unfixed defects.

Review date: 2026-11-02. Scope: Nour-owned application requirements. **Disposition: CHANGES REQUIRED; shared freeze remains pending.** This is an application review of an uploaded specification, not a canonical schema or implementation acceptance.

## Reviewed revision and comparison baseline

- Input: `updated_schemas_v2.md`, whose internal document status is **Draft v1.2 — S1-01 Remaining Review Corrections Applied**. The filename's v2 is not a separate schema-major version.
- Exact input: 170524 bytes; SHA-256 `ca31d98649f51a02fc92cabb586ea9772c6c8bd529cfd79869434c149f528bca`.
- Baseline: [tool contract 0.8](procurement-tool-contracts.md), [state contract 0.7](procurement-state-contract.md), [RAG contract 0.9](rag-contract.md), [application evidence requirements](trace-evidence-contract.md) and [execution-budget ADR 0.1](../../adr/application-execution-budgets.md). These retain their stated proposal and acceptance boundaries.
- The [v1.1 review](schema-v1.1-review.md) is historical. This review supersedes its current-status findings, while retaining original E01–E27 and WG-01–08 identities.
- [OD-APP-OBS-01](open-decisions.md#approval-observation-confirmation) separately records Mohamed/Mohab confirmation, reported by the user, of the distinction between trusted read-only observation and initial-submission retry. It does not accept the entire v1.2 draft or verify an adapter.
- The input hash and review files are recorded in [the current packet manifest](week1-review-manifest.json). No uploaded content was edited, and no pushed commit, live execution or additional reviewer approval is inferred.

## Corrections verified in the v1.2 specification

“Corrected” below means verified in the supplied document/examples. It does not mean implemented, jointly accepted or sufficient to close the entire related working-group item.

| Prior finding | Verified v1.2 correction | Remaining boundary |
|---|---|---|
| Fine states and PO ordering | §4.1 uses the eight application states ending in PO_CREATION then COMPLETION; WT1 and WT3 place proposal/validation/ALLOW before the dispatch transition | Coarse stages, run outcomes and immutable authorization binding still need alignment |
| Request/money types and approval outcomes | Request revisions are opaque strings; monetary examples are decimal strings; DENIED/CANCELLED are represented | Tool payload/status compatibility and approval-validity rules remain open |
| PO business arguments | §4.2.1 lists the six application arguments for create_purchase_order | The other four signatures and result contracts still differ |
| Unknown PO recovery | §4.3 prohibits SAFE_IDEMPOTENT_RETRY and PO redispatch; original timeout result is preserved and read-only recovery is separately linked; missing ledger/lookup error stays unresolved | Root-level dispatch ownership, adapter guarantees and shared recovery acceptance remain open |
| Missing prerequisite disclosure | WT2 and WT3 explicitly identify themselves as partial; WT3 restores APPROVAL_CALCULATED → APPROVED | WT1 is marked complete but still references four missing proposal events |
| Citation offset defect | WT1 clm_proc_01 uses [96,150), and that exact slice matches the claim | Prompt/source integrity and semantic grounding remain separate checks |
| Draft versus acceptance status | Header and most modified register rows distinguish draft updates from pending sign-off | Original IDs are still mislabelled; §4.6 “agreed with Alaa” must be reconciled with pending confirmation |

## Remaining findings and acceptance conditions

The V12 identifiers below are local review findings, not replacements for the original E/WG requirements.

| Finding | Evidence and required edit | Owner / acceptance condition |
|---|---|---|
| V12-01 — Tool inputs and outputs | §4.2.1 claims all five tools match, but four signatures and business-result shapes differ. Preserve the baseline arguments/statuses below; retain error, conditional data and evidence fields. Separate execution status from business outcome, or agree an explicit lossless adapter. | Mohab; Nour reviews application compatibility, Mohamed reviews authority boundaries. All five tools and examples must match the agreed contract. |
| V12-02 — Authorization and dispatch ownership | Policy-check examples contain a proposal reference and observed evidence, but no complete immutable argument/digest, source-state revision and evidence-binding contract. §4.3 limits dispatch per revision, while the budget proposal limits it per root/business request without a new-revision/key reset. | Mohab + Mohamed + Nour. Agree the snapshot/atomic-claim representation and reject changed inputs or reused authorization. Existing no-redispatch recovery remains intact. |
| V12-03 — States, permissions and unknown approval | §4.1 requires a boolean approval_required; WT1 sets true at REQUEST_CAPTURED before calculation. Coarse stages differ from the application proposal; run statuses lack clear active/cancelled/general business-block outcomes. Calculation permission and optional checks for non-risky tools are presented differently from the open application/budget proposals. | Mohab + Mohamed + Nour. Represent unknown requirement before calculation, preserve last workflow state on halt, and agree stage/status/permission mappings without treating denied approval as an automatic policy failure. |
| V12-04 — Complete walkthrough integrity | WT1 call events e2/e6/e9/e12 reference absent prop_pol_01/prop_sup_01/prop_calc_01/prop_reqapp_01. Corresponding proposal/validation and agreed policy-check evidence must be recorded. | Mohab; Nour/Ahmed review. All complete-trace references resolve to suitable preceding evidence; recheck order after inserting events. |
| V12-05 — Prompt and RAG evidence | All three model-call examples declare rendered context absent from their recorded messages; WT4 messages abbreviate context with ellipses. Five content_hash occurrences are placeholders. Score semantics, source locators, selection/exclusion reasons and selected-passage validation remain incomplete. | Mohab + Ahmed; Nour reviews retrieval requirements. Store complete exact messages/context, compute hashes, preserve versions/locators and distinguish structural citation validity from semantic support. |
| V12-06 — Malformed proposals and response provenance | §4.2.2 restricts proposed tool names to the five-tool enum and arguments to objects, losing unknown names/malformed serialization. §4.5 claimed actions lack exact result/recovery links and an explicit candidate-to-delivered-response relationship. | Mohab + Ahmed; Nour/Malak review. Retain raw name/serialization separately from parsed validation; correlate candidate, delivered text and supporting invocation/result. |
| V12-07 — Original requirement identities | §8 still relabels original E02 as states rather than model calls, WG-05 as recovery rather than RAG, and narrows WG-08. Its v1.1-to-v1.2 numbering is not a complete crosswalk from the original application requirements. | Mohab and scoped reviewers. Keep original IDs/meanings and use an explicit navigation mapping; no automatic closure from renamed rows. |
| V12-08 — Acceptance and inference projection | §4.6 claims agreement with Alaa while §8 still requests confirmation. scenario_metadata stripping alone does not specify removal of poisoned-document flags, label-rich identifiers and analysis fields elsewhere. | Mohab + Alaa + Ahmed. Reconcile acceptance claims with actual evidence and define reviewed inference projections for all relevant locations. Full specialist sign-offs remain pending. |

### Required Procurement signatures and business statuses

| Tool | Model-visible arguments in the application baseline | Business result statuses |
|---|---|---|
| search_policy | query, request_id, top_k; optional policy_ids | MATCHED / NO_MATCH / AMBIGUOUS / ERROR |
| get_supplier | supplier_id, request_id | FOUND / NOT_FOUND / ERROR |
| calculate_approval_level | request_id, total_amount, currency | CALCULATED / UNRESOLVED / ERROR |
| request_approval | request_id, justification; approval_request_id required for existing-request observation and omitted for initial submission | PENDING / APPROVED / DENIED / CANCELLED / ERROR |
| create_purchase_order | request_id, supplier_id, item_description, quantity, total_amount, currency | CREATED / ALREADY_EXISTS / UNKNOWN_OUTCOME / ERROR |

The baseline error fields are code/message/retryable/details. Normalized supplier statuses are APPROVED/NOT_APPROVED/UNKNOWN, with original values retained when mapped. ALREADY_EXISTS confirms an original effect without a new creation; UNKNOWN_OUTCOME must not fabricate a confirmed PO identity. A model-provided approval_request_id identifies a record and must be checked against trusted context; it is not an authorization token. Observation is not submission retry under OD-APP-OBS-01. Numeric budgets, approval validity and runtime guarantees retain their separate gates.

## Original requirement navigation

These are topical navigation mappings to §8 of the uploaded v1.2 draft, **not assertions of equivalence or completeness**. Keep original application IDs in fixtures and review records. Multiple original requirements may point to the same draft row.

| Original application ID / requirement | Related v1.2 table row(s) | Remaining focus |
|---|---|---|
| E01 request | E01 | Identity, normalization and request provenance |
| E02 model call | E20 | Complete messages and effective configuration |
| E03 policy retrieval | E06, E18 | Tool contract, query/filter and policy evidence |
| E04 RAG retrieval | E18, E25 | Effective query and retrieval/index/embedding configuration |
| E05 source evidence | E18 | Exact source/version/locator and real digest |
| E06 scores/ranks | E18, E26 | Score kind/direction and unavailable values |
| E07 selection/sufficiency | E19, E22 | Selected/rejected text, facets and conflict evidence |
| E08 normalization | E01, E12 | Exact money and raw/parsed values |
| E09 fine states | E02, E05 | Unknown approval and authorized transitions |
| E10 policy stage | E03 | Agreed map at proposal/check/dispatch |
| E11 supplier | E07 | Normalized eligibility and source/version evidence |
| E12 approval calculation | E08 | CALCULATED versus UNRESOLVED and rule basis |
| E13 approval submission | E09 | Initial submission distinct from observation |
| E14 approval observation | E10 | Existing request, trusted decision and validity |
| E15 proposal | E11 | Proposal distinct from actual invocation |
| E16 arguments/validation | E12, E11 | Raw malformed serialization and unknown names |
| E17 bound pre-tool request | E05, E11, E13, E14, E16 | No complete equivalent: immutable digest/state/evidence binding and atomic claim |
| E18 pre-tool result | E13, E14 | Verdict, applicability, error and binding |
| E19 suppression | E15 | Suppression without an invented tool-body result |
| E20 actual execution/result | E16, E17 | Business payload, original/new effect and unique terminal result |
| E21 Procurement final | E22 | Candidate/delivered distinction and exact result links |
| E22 RAG answer | E20, E21, E22 | Generation context and delivery correspondence |
| E23 citation | E21 | Claim → selected versioned passage → visible marker |
| E24 abstention | E22 | Evidence deficiency separate from technical error |
| E25 pending/error/recovery | E04, E17, E22 | Cancellation, waiting and immutable original outcome |
| E26 provenance | E24, E25, E26 | Effective configuration, source/code lineage and missingness |
| E27 scenario isolation | E27 | Reviewed projections remove labels/recipes/qrels/poisoned flags |

| Original working-group ID | Related v1.2 register area | Review boundary |
|---|---|---|
| WG-01 states/stages/run outcomes | WG-01 | Unknown approval and status/stage alignment remain |
| WG-02 bound authorization | WG-01/02/04 | Verdict enum fixes do not close immutable binding |
| WG-03 supplier/calculation/approval | WG-03/04 | Types improved; payloads, evidence and validity remain |
| WG-04 lifecycle/effects/recovery | WG-04/05 | Read-only PO recovery corrected; full effect/dispatch contract remains |
| WG-05 RAG evidence | WG-06 | Exact messages, hashes, selection and semantics remain |
| WG-06 provenance/missingness | WG-07 | Effective lineage and actual reviewer acceptance remain |
| WG-07 inference isolation | E27 and related projection requirements | No lossless standalone replacement WG row; projection review remains |
| WG-08 raw proposals/response provenance | WG-04/06/08 | Walkthrough edits alone do not close malformed/candidate/delivered evidence |

## Reproduced observations and limitations

The [machine-readable observation record](schema-v1.2-review-observations.json) is pinned to the input digest above. These are inspection results, not a canonical-schema validation report.

| Check | Observed result |
|---|---|
| Standalone walkthrough JSON parsing | 4 parseable traces; event counts 25, 8, 10 and 3 |
| Partial markers | WT2/WT3 true; WT1/WT4 false |
| Response substring checks | 2 of 2 exact matches: WT1 [96,150), WT4 [0,68) |
| Source quote substring checks | 2 of 2 exact matches; both quotes appear in their declared selected text |
| Complete WT1 proposal references | 4 unresolved references, listed in V12-04 |
| Declared context versus recorded messages | 3 mismatches; each declared context block is absent from recorded message strings |
| Retrieved content SHA-256 | 5 placeholder occurrences differ from SHA-256 of the exact UTF-8 content_snippet bytes |
| Configuration JSON fragment | §4.6 is a non-standalone fragment; excluded from complete-trace parse checks |

WT4 intentionally demonstrates unsupported RAG output; retain it as a negative example. Exact slices do not prove semantic support, and its negative behavior is distinct from missing or abbreviated evidence.

For reproduction, extract standalone trace objects from the supplied Markdown JSON fences. Compare each call's proposal_id with tool_proposal identities in that trace; compare response_text[start:end] to claim_text and content_snippet[start:end] to source_quote using Unicode code-point indices. Compare each declared rendered_context_block with the complete recorded message content. Compute hashlib.sha256(content_snippet.encode('utf-8')).hexdigest() and compare with content_hash after removing the sha256: prefix. The exact input digest must match before comparing counts. Finding placeholder hashes is not proof that any production store is corrupt.

## Required return and status

Mohab should return the corrected draft/examples and original-ID mapping with reviewer responses scoped to exact revisions. Nour reviews application fit; Mohamed reviews governance and authorization; Ahmed reviews failure/evidence interpretation; Alaa reviews provenance/projections; Malak reviews status and evidence presentation.

OD-05 remains BLOCKING. OD-APP-OBS-01 stays closed for observation meaning only. No runtime, SDK, policy engine, database, dashboard or repository-push validation was performed. Existing prompt/corpus validation reports retain their original scope and are not evidence that the supplied v1.2 schema is accepted.
