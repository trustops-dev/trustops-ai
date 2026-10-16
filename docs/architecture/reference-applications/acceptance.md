# Week 1 acceptance and Week 2 review plan

PASS below means verified documentation coverage, not runtime correctness, team sign-off or experiment success. PARTIAL means the specification is present but a substantive alignment decision remains. BLOCKED means external evidence needed for acceptance is unavailable. No automated application tests are appropriate or claimed for this documentation-only task.

| Acceptance item | Status | Evidence / reason |
|---|---|---|
| Procurement workflow completely documented | PASS | procurement-state-contract: all eight named states, valid branches and global stop/resume rules |
| Every state has entry and exit conditions | PASS | Each state has purpose, input/output, entry/exit, transitions, tools, trace/policy evidence and failure modes |
| All five tools have explicit typed contracts | PASS | procurement-tool-contracts: fields, requiredness, statuses, validation, pre/postconditions, stages, errors, governance and mock semantics |
| Tool-stage permission fully reconciled with policy | PARTIAL | Calculation tool permission D3/OD-02 requires Mohamed's ratification |
| Approval-bypass control before execution | PASS | State contract: proposal → check BLOCK → NOT_EXECUTED; no successful tool result |
| False completion preserved independently | PASS | Raw vs delivered final claims retained and linked to actual/absent result |
| Pre-execution and post-run boundaries separate | PASS | Overview, trace contract and ADR explicitly separate ALLOW/BLOCK from reliability PASS/REVIEW/BLOCK |
| RAG retrieval explicit | PASS | Query/k, IDs/text/metadata, score/rank/direction, versions and error/empty behavior documented |
| Grounding and citation explicit | PASS | Claim→retrieved span→source/version→citation mapping with snapshot requirements |
| Abstention explicit | PASS | Sufficiency branch, reasoned abstention and separate technical error |
| No unsupported numeric thresholds | PASS | Policy values, k and reliability tolerances remain owner/config or empirical decisions |
| All eight failure classes mapped | PASS | failure-planning-matrix: exact eight labels/app/mechanism/evidence/family/RCA/policy/owner/timing; NORMAL separate |
| Detailed remaining scenario specifications and proposed schedule | PASS | Revision 0.5 SC-01–SC-03 contain inputs, injection boundaries, paired controls, trace evidence, acceptance criteria, dependencies and proposed Week 7/8 work; documentation coverage only |
| Failure implementation dates approved | PARTIAL | OD-08 proposal complete; explicit S4-06 scope/dependency amendment and S3-03 fixture handoff still require review. Existing S3 four-case scope and S5 benchmark preserved |
| Significant application steps mapped to evidence | PASS | E01–E27 plus manual walkthroughs cover both applications |
| Canonical trace schema not authored for Mohab | PASS | Requirements-only matrix; no canonical schema, API or runtime class created |
| Provider/model strategy documented | PASS | ADR selects Google Gemini API and immutable configuration strategy; Gemini 3.8 Flash (`gemini-3.8-flash`) selected; remaining configuration/validation tracked under OD-LLM-01 |
| Exact Gemini model selected and recorded | PASS | User selected Gemini 3.8 Flash (`gemini-3.8-flash`) on 2026-10-07; official model page confirms identifier and documented tool/structured-output support; not a runtime result |
| Effective Gemini configuration and version semantics reviewed | BLOCKED | OD-LLM-01 remains PARTIAL: generation parameters and effective configuration still require review before contract freeze; live compatibility is a separate gate |
| Embedding model/provider and retrieval configuration selected | BLOCKED | OD-RAG-01/OD-10: independent design choice pending for Sprint 1 sign-off, as required by the RAG contract; embedding calls and index validation belong to implementation |
| Orchestration decision documented | PASS | ADR compares exactly LangGraph and explicit Python state machine across nine requested criteria |
| Team handoffs explicit | PASS | Five separate handoff checklists and unsigned review register |
| Open decisions visible | PASS | OD-01–OD-16 plus OD-LLM-01, OD-LLM-02 and OD-RAG-01; source conflicts and owners/closure criteria |
| Valid existing work preserved | PASS | Supplied sources unchanged; existing staged documentation revised in place |
| Actual repository compared/updated | PASS | [OD-01 closure evidence](repository-integration.md#od-01-closure-evidence): PR #11 merged into `dev`, PR #12 promoted to `main`; merge commits and review evidence recorded |
| Manual traces validated against Trace Schema v1 | BLOCKED | Four semantic walkthroughs prepared; actual canonical schema/fixtures not supplied |
| Four owner sign-offs obtained | BLOCKED | No written acceptance received; no teammate contacted |
| No Sprint 2 production functionality | PASS | This import contains Markdown documentation only; the original source-hash manifest was not supplied |
| No deferred technology enters MVP | PASS | Explicit scope exclusions; framework/provider selection does not add deferred infrastructure |
| No experimental/validated result fabricated | PASS | Every manual case is expected behavior, not an execution result |
| Formal S1-01 contract freeze | BLOCKED | Effective model configuration and required retrieval/embedding choices, policy/interface decisions, schema-valid manual traces and four owner sign-offs remain unresolved. Runtime validation is tracked separately below |

## Separate acceptance milestones

Contract approval and runtime validation require different evidence. A documentation PASS never establishes live Gemini compatibility, and contract sign-off never authorizes skipping the pre-implementation validation gate.

| Milestone | When | Required evidence / owner | Current status |
|---|---|---|---|
| Contract freeze | End of Sprint 1, before production implementation | Reviewed exact Gemini model/configuration choice with capability documentation; retrieval/embedding design decisions; resolved policy/interface blockers; manual procurement and RAG traces validated against Schema v1; written Ahmed/Mohab/Mohamed/Alaa sign-offs tied to the revision. Nour coordinates | BLOCKED; model selected, remaining configuration and review evidence absent |
| Gemini runtime compatibility | Start of Sprint 2, before production application implementation or reproducible live traces | Controlled validation of actual API access, all five tool proposal/result mappings, structured RAG output and effective parameters; record exact model/configuration, observed responses and pass/fail evidence. Nour/Alaa, with Mohab on mapping | BLOCKED; no live validation performed |
| API workload readiness | Access review before production implementation; quota/billing validation before workload generation | Actual API-project access, quota/rate limits and billing evidence plus workload/cost assessment, independent of consumer subscriptions. Nour/Alaa | BLOCKED; OD-LLM-02 remains OPEN |
| RAG runtime readiness | During authorized RAG implementation, before accepting the runnable RAG path | Validate the selected embedding configuration against the chosen vector store, dimensions and retrieval behavior; preserve configuration/version evidence. Nour/Mohab, Ahmed/Alaa review | PENDING future implementation; no embedding calls or index built |

The model-selection portion of OD-LLM-01 can be recorded separately from its live-validation portion. Do not mark the entire item CLOSED until both have evidence. Contract freeze requires the design decisions and agreed validation plan; later runtime checks remain explicitly pending and block production implementation or workload generation at their stated gates. No unresolved policy or schema decision is waived. This clarification does not resolve the existing S2/S3 policy-engine scheduling conflict in OD-06.

## Week 2 recommended actions — Sprint 1 only

1. **Completed ? OD-01 closed on 2026-10-16:** documentation import and promotion merged through PRs #11 and #12. See the [integration record](repository-integration.md#od-01-closure-evidence). Continue with the specialist reviews below; no runtime completion or contract freeze is implied.
2. Review with Mohamed: resolve calculation permission, coarse stage names, approval-not-required branch, currency/threshold truth table, supplier evidence, approval validity and S2/S3 integration wording.
3. Align E01–E27 with Mohab's Trace Schema v1 and governance boundary. Mohab creates canonical fixtures; walk procurement success, approval bypass, grounded RAG and RAG failure/abstention by hand. Record actual validation outcome per fixture.
4. Review with Ahmed: exact class overlap, attempted vs prevented failure semantics, independent causal metadata, citation/sufficiency rubric and RCA evidence; review SC-01–SC-03 and obtain plan-owner agreement to the proposed S4-06 scope/dependency amendment and dataset ordering; OD-08 drafting is complete, approval remains pending.
5. Review with Alaa: immutable model/prompt/retriever/corpus/scenario/config identifiers, split grouping and runtime/label separation. Review the selected `gemini-3.8-flash` model and complete its effective configuration under OD-LLM-01; review API-project access/quota/billing information under OD-LLM-02; close the independent embedding/retrieval design choices under OD-RAG-01/OD-10. Record owners and required evidence for the separate runtime gates above. No API calls, live workflow or index build in this documentation task.
6. Give Malak the state/evidence mappings for paper trace investigations and check that proposal, BLOCK, NOT_EXECUTED and false completion remain distinct.
7. Correct contracts once, update ADR/register, obtain the four named sign-offs tied to exact revision, and support Malak's S1-07 independent audit. Freeze only when required evidence exists.

Do not build runnable skeletons, tools, retrieval indexes, model workflows, SDKs, APIs, storage or other Sprint 2 functionality during Week 2. This follows the current task and Sprint 1 plan; the older roadmap's Week 2 coding recommendation is explicitly superseded for this package.

Revision 0.5 closes the Week 1 drafting action for the three remaining scenario recipes and their schedule proposal. It does not close OD-08 approval, taxonomy/root-cause adjudication, schema compatibility, owner sign-offs or runtime gates. No new production functionality is included.
