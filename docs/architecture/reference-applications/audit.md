# Current-state audit and source reconciliation

**Sprint 1 Contract Baseline / Freeze Candidate — revision 0.6, 2026-11-01. NOT FROZEN.** Documentation and manual review evidence only; specialist approvals remain PENDING. Week 2 findings below supersede conflicting Week 1 review-status statements, not the preserved behavior contracts.

## Week 2 source baseline and precedence

Review date: 2026-11-01. Priority remains Proposal → Sprint Plan → Repository Architecture → Figures → approved team artifacts → repository state; the current instruction expressly restricts Week 2 to contracts and manual validation. The team documents inspected below are **drafts**, regardless of Git merge status. Neither a merged PR nor an author's local checklist supplies a new S1-01 specialist approval.

| Source | Exact review basis / use |
|---|---|
| Project proposal v1.1 | Supplied DOCX; N/R procurement, J traces, K–M evaluation/RCA, O–S datasets/security/gates, U technology, Y milestones |
| Sprint Plan | Supplied HTML, Sprint 1/2 task details and later scope/dependency sections; S1-01/S1-02 manual reviews, S1-07 closeout, S2-01/S2-04 and S3-01/S3-03/S4-06/S5 gates |
| Repository Architecture | Supplied professional DOCX; canonical `packages/contracts`, app adapters, subsystem ownership and single-home rule |
| Figures 1–5 | Supplied images visually reviewed: system, online/post-run boundary, execution graph, evaluation pipeline, release gate |
| Nour Week 1 | Thirteen maintained Markdown files at pinned `dev`; earlier uploaded package and integration archive used only as history |
| Mohab | `docs/architecture/schemas/Week 1 Execution Deliverable Trace Schema v1 (Draft) & Interface Boundaries.md`, including all three embedded JSON examples |
| Mohamed | `docs/architecture/governance/governance-contract.md` v0.2 draft and `decision-flow.md` |
| Ahmed | `trace-evidence-requirements.md`, `annotation-guide.md`, `evaluation-pipeline.md`, taxonomy YAML and S1-03 index; draft semantics are not approvals |
| Alaa | `docs/requirements/S1-05-dataset-experiment-requirements.md`, draft versioning/dataset requirements |
| Malak | Dashboard field-owner matrix, owner-review packet and status vocabulary; Q-12/Q-15 and Nour's 37 field rows |
| Current repository | `main` 3ef7da1f190cd5a22efdcd6798af59199924bac3; latest fetched `dev` 72e7975384d5e8b32d1e0e68ff4742cce96fa336; no frozen executable trace model found |

See `repository-integration.md` and the delivery's `validation/source-manifest.json` for pins and content hashes. The separately uploaded final-integration ZIP is not proof that its repairs reached Git; only current pinned repository text is used for the schema-fit verdict.

## Week 1 artifact review — current disposition

READY means complete at application-specification level, not approved or runtime validated.

| Artifact | Status | Issue | Required Week 2 action / result |
|---|---|---|---|
| Procurement state machine | NEEDS ALIGNMENT | Draft conflates fine states, coarse stages and halt outcomes | Preserve eight states; explicit state-to-draft mismatch table added; WG-01 remains owner action |
| Five tool contracts | NEEDS ALIGNMENT | Draft examples use wrong PO argument names/types; policy transport and result semantics differ | Retain typed business contracts; add five-tool review and correction table |
| Approval-bypass trajectory | NEEDS ALIGNMENT | No actual call allowed; draft tolerates blocked `tool_call`; raw/delivered response not separately encoded | Complete paper fixture proves expected suppression and preserves false candidate separately; WG-04/08 |
| RAG flow | NEEDS ALIGNMENT | Selected context, evidence sufficiency and source-version evidence absent from schema | Preserve staged flow; map each boundary and manual sufficient/insufficient paths |
| Citation contract | NEEDS ALIGNMENT | Optional cited doc/claim does not encode exact claim→selected span→version→marker | Keep application requirement; request canonical binding in WG-05 |
| Abstention contract | NEEDS ALIGNMENT | Draft reasons do not cover incomplete/conflicting evidence or invalid binding precisely | Explicit lossless reason mapping request; no numeric confidence cutoff |
| Failure planning matrix | NEEDS CORRECTION | Current Ahmed examples imply unreachable supplier path and timeout proves no effect; fixed score examples unapproved | Application clarification added, upstream corrections requested; labels and existing recipes preserved |
| Application evidence contract | BLOCKED | Current draft cannot represent all E01–E27 losslessly | Actual paths/status per row and concrete gap register added; canonical walkthrough remains blocked |
| Provider ADR | READY | Single Gemini/model selection clear; effective config/access still open | Preserve decision and document fresh capability check; no runtime claim |
| Orchestration ADR | READY | No framework incompatibility found; enum gaps are representation issues | Explicit Python decision APPROVED FOR SPRINT 2 IMPLEMENTATION, subject to overall entry gates |
| Handoffs/sign-offs | BLOCKED | Five revision-specific acknowledgments not received | Actual team artifact review matrix prepared; every reviewer PENDING |
| Open decisions | NEEDS ALIGNMENT | Old availability statements outdated and statuses mixed | Every existing ID reclassified; no fabricated closure; owners and evidence retained |

## New source conflicts and smallest compliant corrections

| ID | Conflict / precedence | Smallest compliant correction | Owner / disposition |
|---|---|---|---|
| W2-C01 | Proposal N's fine workflow vs Mohab/Ahmed nine-stage enum; Proposal wins | Keep fine state separate from coarse policy stage; preserve APPROVAL_PENDING, PO_CREATION and COMPLETION; do not treat PO_CREATED as pre-dispatch | Mohab/Mohamed; BLOCKING |
| W2-C02 | Proposal N requires calculation but R's PRE_APPROVAL allowlist omits it; internal proposal ambiguity | Ratify read-only `calculate_approval_level` at SUPPLIER_CHECKED/PRE_APPROVAL, leaving PO restricted; Mohamed GD-01 proposes this but is unsigned | Mohamed/Nour; BLOCKING |
| W2-C03 | S2 summary/S2-01 stub vs S2-04 three real policies vs S3 persistence/integration | Agree minimum real pre-tool enforcement date and temporary stub expiry; candidate S2 in-process pure policies, S3 persistence is a proposal only | Plan owner/Mohamed/Mohab; BLOCKING |
| W2-C04 | Roadmap recommends runnable mocks in Week 2; S1 is contract-only and current task expressly prohibits implementation | Keep this revision entirely documentation/manual fixtures; implement only after Sprint 2 authorization | Resolved scope interpretation; no code introduced |
| W2-C05 | Roadmap all-class Week 6 vs S3-01 four scenarios; S4-06 fixes vs proposed Week 7 new recipes | Preserve S3 four cases and S5 security; obtain explicit S4-06 amendment for SC-01–03 and dataset sequencing | Plan owner/Nour/Ahmed/Alaa; scheduling pending |
| W2-C06 | Draft `passed:bool`/ERROR_BLOCK vs governance PASS/FAIL/NOT_APPLICABLE/ERROR and ALLOW/BLOCK+basis | Mohab/Mohamed agree lossless mapping; preserve technical error versus policy violation and non-applicability | WG-02; BLOCKING |
| W2-C07 | Schema/annotation timeout implies false side effect; app correctly preserves UNKNOWN_OUTCOME | Unknown is not false; no confirmed PO ID or replacement dispatch until read-only evidence resolves it | Mohab/Ahmed/Malak; BLOCKING |
| W2-C08 | Ahmed labels supplier breach at APPROVED as valid full-app workflow; app must stop at supplier check | Full-app early-stop control remains; isolated governance-boundary fixture explicitly declares seeded snapshot and is not reachable app execution | Ahmed/Mohamed; correction requested |
| W2-C09 | Numeric groundedness/security examples in Ahmed draft appear normative; proposal requires empirical tolerances | Treat as unapproved illustrative examples only; no app sufficiency threshold, measured score or gate configured | Ahmed/Alaa; defer numeric approval to S5 |
| W2-C10 | Schema draft recommends legacy backend schema paths and Week 2 migration | Canonical definitions belong only in `packages/contracts`; no migration/SDK/schema implementation in this task | Mohab; architecture/sprint take precedence |
| W2-C11 | Figure 3 stretch GNN and Figure 4 omitted Logistic Regression vs Proposal scope | No GNN in MVP; retain deterministic, Logistic Regression and XGBoost comparisons downstream | Scope clarified; no evaluator work |
| W2-C12 | Procurement policies mentioned alongside RAG in planning vs RAG has no purchasing tools | RAG receives NOT_APPLICABLE for procurement policy family, not a fictitious PASS or added PO capability | Mohamed/plan owner; GD-17 proposed, pending |

The remaining historical reconciliation below is retained for provenance. Its old statements that team/schema artifacts were unavailable describe the Week 1 review date only.

> Historical source-package audit: references below to attachments, hashes and the absence of a Git checkout describe the original preparation session. Those attachments and their source-hash manifest were not included in the supplied 12-file Markdown folder and were not independently inspected during this import. See the [2026-10-15 repository integration record](repository-integration.md) for current repository evidence.

## Audit categories

| Category | Finding | Consequence |
|---|---|---|
| Existing | Workspace contains source attachments; Git root detection reports no repository | No branch, commit, remote or production state can be claimed |
| Missing | `apps/procurement-agent/`, `apps/rag-assistant/`, `scenarios/`, `docs/architecture/`, `docs/adr/` absent from the supplied workspace before drafting | Missing locally only; their existence in the actual remote is unknown |
| Missing | Trace Schema v1, governance truth tables, reviewer signatures and runtime test evidence not supplied | Cannot validate against an unseen schema or declare S1-01 frozen |
| Requires Clarification | Actual repository location and existing equivalent documentation | Reconcile before merging; preserve valid existing work |
| Proposed Week 1 Artifact | Documentation under `docs/architecture/reference-applications/` and an unnumbered ADR under `docs/adr/` | Repository-ready paths within approved documentation boundaries |

## Discrepancies and smallest compliant corrections

| ID | Discrepancy | Governing source | Recommended correction; status |
|---|---|---|---|
| D1 | Roadmap Week 2 calls for executable mock tools, index and runnable apps; Sprint 1 explicitly prohibits implementation | Current task + Sprint Plan S1 scope/S1-01 | Week 2 remains manual contract/schema review; move execution work to Sprint 2. Applied to this package only |
| D2 | Roadmap uses underscore app paths and shared app helpers; approved tree uses kebab-case apps and app-specific SDK adapters | Repository Architecture rules 3, 4, 6, 9 | Use approved paths; no parallel shared SDK/schema. Applied |
| D3 | Proposal R's PRE_APPROVAL allowlist omits `calculate_approval_level`, while N requires it among five tools | Proposal N and R jointly | Mohamed must explicitly resolve the omitted permission. Recommend a read-only calculation entry in PRE_APPROVAL, restricted by app state to SUPPLIER_CHECKED; leave PO prohibition unchanged. OPEN; no silent permission grant |
| D4 | Sprint 2 overview/S2-01 describes a policy stub and Sprint 3 real-engine integration; S2-04 demands three real policies and real-engine bypass testing in Sprint 2 | Proposal W puts policy v1 in Weeks 5–6; plan is internally inconsistent | Recommend S2 minimum approval enforcement at the agreed boundary, optional early real rules, mandatory full real-policy integration in S3. Nour/Mohamed/Mohab and plan owner must reconcile wording. OPEN |
| D5 | S3-01 says three procurement policies integrated into both apps | Proposal N/R limits these rules to procurement actions | Wire procurement pre-tool enforcement only where procurement tools exist; RAG emits retrieval/security evidence and has no PO tools. Document non-applicability instead of inventing RAG purchasing stages. OPEN acknowledgement |
| D6 | Figure 3 footer describes GNNs as a stretch experiment; proposal places them in deferred work | Proposal E/AC | No current GNN work; diagram footer is not authorization. Applied |
| D7 | Figure 4 omits Logistic Regression from its simplified picture | Proposal L and Sprint S4-01 | Retain Logistic Regression in downstream requirements; no app-side classifier implementation. Applied |
| D8 | `sensitive_data_exposure.yaml` appears in recommended paths and S5-02 areas, but S5 scope excludes non-injection attacks | Proposal Q and Sprint 5 explicit scope | Do not infer a data-exfiltration benchmark from a filename. Use approved injection categories only. Applied |
| D9 | Proposal J.2's abbreviated `tool_call` example lacks an explicit blocked-execution event | Proposal N/M, Figures 2/3 and current task | Require separate proposal, check and non-execution evidence; never infer execution from `tool_call`. Mohab maps names. Applied as evidence requirement |

No repository-vs-document implementation conflict can be assessed without repository access. These are source-to-source findings, not allegations about existing code. Unrelated plan bookkeeping is outside this audit's correction scope.

## Revision 0.2 provider re-check

All supplied project-source hashes match the revision 0.1 manifest. Proposal U permits one primary LLM provider without fixing its identity; S1-01 requires provider/model selection while forbidding production implementation. Repository contract/adapter boundaries and Figures 1–5 remain applicable. The user selects Google Gemini API in this revision; the exact model remains an explicit pre-Sprint-2 blocker. No provider-driven contradiction requiring a change to business behavior, orchestration, ownership or sprint sequencing was found. Existing discrepancies D1–D9 remain unchanged. No Git checkout or remote was introduced; updates apply directly to the existing local documentation package.

## Revision 0.3 review corrections — 2026-10-07

Corrected the three-column output-table headers for calculation, approval and PO tools; field values and business semantics are unchanged. Separated contract selection/sign-off evidence from later live Gemini compatibility and workload readiness in acceptance.md, with matching ADR/open-decision references. Exact model selection remains required before production implementation; runtime validation is not claimed. Updated package/review revision references. Source documents, diagrams, procurement states, failure taxonomy, enforcement, ownership and unresolved D3/D4/D5 decisions remain unchanged. All approvals remain pending.

## Revision 0.4 — 2026-10-07

Recorded the user’s selection of Gemini 3.8 Flash (`gemini-3.8-flash`) for both reference applications. Verified the identifier, stable designation, function calling and structured outputs against [Google’s official model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash). Updated ADR, README, overview, RAG, trace provenance, decisions, acceptance and handoffs. Model-name selection is resolved; configuration, runtime compatibility, API access, embeddings and team approvals remain pending. No business contract, failure-class assignment, source document, diagram or runtime implementation changed.

## Revision 0.5 — 2026-10-07

Completed SC-01–SC-03 scenario specifications and a concrete OD-08 scheduling proposal at the user’s request. Re-read authoritative S3-01, S3-03 and S4-06 task scopes: S3-01 explicitly limits its initial recipes to four classes; S4-06 currently allows evidence/integration support only. The proposed Week 7 recipe / Week 8 integration sequence therefore requires an explicit S4-06 scope and dependency amendment, with the existing S3-03 supplier-breach fixture handed off first. Avoided a classifier dependency cycle by proposing separate construction and integration prerequisites, subject to plan-owner approval.

SC-03 distinguishes normal early rejection from an isolated pre-tool fixture instead of fabricating a reachable APPROVED/unapproved-supplier trajectory. Synthetic output/proposal origin, paired controls, independent ground truth, dataset scope and prevention-versus-detection assertions are explicit. README, acceptance, open decisions and handoffs reflect drafting completion and pending approval. No canonical schema, executable scenario, SDK call, model request, team sign-off, original source edit or runtime result was created.
