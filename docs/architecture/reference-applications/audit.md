# Current-state audit and source reconciliation

> Historical source-package audit: references below to attachments, hashes and the absence of a Git checkout describe the original preparation session. Those attachments and their source-hash manifest were not included in the supplied 12-file Markdown folder and were not independently inspected during this import. See the [2026-10-15 repository integration record](repository-integration.md) for current repository evidence.

## Evidence inspected

| Source | Authority and use |
|---|---|
| Project Proposal v1.1 | Scope baseline; especially I–N, Q–W, Y and Open Decisions |
| Sprint Execution Plan, supplied HTML | Execution sequence/ownership; S1-01 through S1-07, S2-01/S2-04, S3-01/S3-03, S5-02 |
| GitHub Repository Architecture, supplied DOCX | Recommended tree, module ownership and nine architecture rules |
| Figures 1–5, supplied PNGs | Visually inspected: component boundaries, pre-tool sequence, bypass graph, evaluation and gate |
| Nour 16-Week Roadmap | Supplemental planning detail only; its inferred paths and Week 2 implementation do not supersede higher sources or this task |
| Pasted text(1).txt | Original Week 1 task instructions and required deliverables |
| Pasted text(2).txt | Current targeted provider update: Google Gemini API; exact model and embeddings remain open |

The five PNGs were found and opened successfully in this session. The prior missing-file messages no longer describe their availability. Source copies are preserved. A source-hash manifest accompanies the package to identify the exact inputs read.

## Audit categories

| Category | Finding | Consequence |
|---|---|---|
| Existing | Proposal, sprint plan, repository architecture, roadmap and all five diagrams supplied | Authoritative design evidence exists; not evidence of implementation |
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
