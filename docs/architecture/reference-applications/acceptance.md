# Sprint 1 acceptance and Week 2 validation

**Current mapping — 2026-11-06:** [Draft v1.6 E01–E27 assessment](schema-v1.6-evidence-mapping.md) and [exact row evidence](schema-v1.6-evidence-mapping.json) cover all 27 requirements: **9 OK, 9 CHANGE REQUIRED, 9 OPEN**. The [rerun observations](schema-v1.6-review-observations.json) retain R16-01–09 as the current review baseline. v1.5 is historical comparison evidence. Mapping preparation is complete; corrected files, unresolved conventions and joint acceptance remain pending. OD-05 stays blocking; no new signature or runtime verification is implied.

**2026-11-02 corpus/boundary completion:** RAG revision 0.9 adds the [synthetic corpus specification](corpus-review/README.md); [ten manual boundary cases](manual-boundary-cases.md) include denied approval and symbolic below/equal/above T. These complete the remaining owner drafting items, not shared acceptance or runtime tests. See [current closeout](week1-owner-closeout.md).

**Owner closeout revision 0.13 — 2026-11-05.** Decision consolidation, active review references and offline validation refreshed; shared acceptance remains PENDING.

**Historical 2026-11-05 v1.5 mapping coverage:** all original E01–E27 rows now have an explicit v1.5 representation, evidence, status and next action in the [current mapping](trace-evidence-contract.md#current-v15-application-to-schema-mapping) and [machine-readable record](schema-v1.5-evidence-mapping.json): 5 OK, 15 CHANGE REQUIRED, 7 OPEN. Coverage completion does not close any outstanding correction, decision or sign-off gate.

**Sprint 1 Contract Baseline / Freeze Candidate — revision 0.6, 2026-11-01. NOT FROZEN.** Documentation and manual review only; no teammate approval or runtime result is claimed.

PASS means documentation coverage or a specified paper check; it does not mean a live system passed, a canonical schema was frozen, or an owner approved. PARTIAL means an evidenced portion is complete with explicit alignment work remaining. BLOCKED means required acceptance evidence is absent. Review source/commit provenance is in audit.md and repository-integration.md.

| Acceptance item | Status | Evidence / precise limit |
|---|---|---|
| Procurement behavior contract complete | PASS | Eight detailed state records, entry/exit, allowed/forbidden moves, tools, policy/evidence/errors, no-approval and recovery branches retained |
| Five tool contracts complete | PASS | Typed required/optional fields, statuses, validation/pre/postconditions, mock semantics and trace/governance evidence reviewed; no implementation |
| Tool/policy-stage contract jointly reconciled | BLOCKED | OD-02/03/04/06; read-only calculation permission and authority/config/date remain unsigned |
| RAG behavior contract complete | PASS | Query→retrieval→selection→generation→binding→answer/abstention; ERROR separate |
| Grounding/citations/abstention complete at app level | PASS | Material claim→selected source span/version→visible marker, qualitative sufficiency and reasoned abstention; no invented cutoff |
| Failure-class mapping complete | PASS | Eight exact classes, mechanisms, evidence, families, fixed nine RCA causes, security/policy relationship; NORMAL distinct |
| Failure/taxonomy examples jointly accepted | BLOCKED | OD-09: supplier path, timeout, overlap and matching claim/result corrections pending Ahmed/Mohamed |
| Application-to-trace mapping documented | PASS | All 27 original requirements mapped to actual v1.6 source sections, event paths and rerun evidence with 9 OK / 9 CHANGE REQUIRED / 9 OPEN; v1.5 mapping and original requirements preserved |
| Application-to-trace mapping aligned losslessly | BLOCKED | The current mapping covers v1.6. R16-01–09 corrections, unresolved conventions and scoped acceptance remain pending |
| Successful Procurement trace validates conceptually | PASS | fixtures/01-procurement-success.json: all eight states, five tool dispatches, trusted approval, bound check, one PO, matching final claim; conditional on named proposed policy assumptions |
| Approval-bypass trace validates conceptually | PASS | fixtures/02-procurement-bypass.json: required true/missing approval, PRE_APPROVAL proposal, BLOCK, no PO dispatch/result, separate raw false candidate/delivered notice |
| Grounded RAG trace validates conceptually | PASS | fixtures/03-rag-grounded.json: complete selected source snapshot, authored generation context, exact claim/source span/version/marker and final answer |
| Insufficient-evidence RAG trace validates conceptually | PASS | fixtures/04-rag-insufficient.json: known source omission in independent sidecar, irrelevant returned source, empty support, abstention, no fabricated generation event |
| Manual traces validated against canonical Trace Schema v1 | BLOCKED | Owner paper fixtures remain non-canonical. Supplied v1.6 baseline previously passed 2106 assertions and 27 suite cases reproduced; 16 of 35 independent expectations were unmet. These external review results were not rerun in this artifact-validation refresh and do not establish schema-fit acceptance |
| Gemini/provider strategy documented | PASS | Sole Gemini provider, selected gemini-3.8-flash, provider-neutral tool contracts and planned provenance; no API execution |
| Effective generation/retrieval/embedding configuration frozen | BLOCKED | OD-LLM-01/02, OD-10 and OD-RAG-01; proposed settings now documented; account/environment verification, cross-contract acceptance and live compatibility remain pending |
| Orchestration decision documented | PASS | ADR preserves explicit Python choice and requested APPROVED FOR SPRINT 2 IMPLEMENTATION technical disposition; overall entry gates still apply |
| Every open decision closed or explicitly recorded | PASS | All 21 original decision IDs preserved; 20 focused pending request rows (including child questions) each state proposal, reviewer, question and closure evidence; existing closures/design dispositions/deferred thresholds preserved |
| Cross-team review status visible | PASS | Mohab/Ahmed/Mohamed/Alaa/Malak all PENDING; actual source review distinguished from acceptance |
| Cross-team signatures / formal freeze obtained | BLOCKED | No revision-specific owner approval received; not requested or fabricated by tool calls |
| Correct existing work preserved and docs updated in place | PASS | Existing twelve app Markdown files and combined ADR revised; original detailed state/tool/RAG/scenario design retained |
| No production implementation started | PASS | Changes confined to Markdown and four paper JSON files under documentation; no app/tool/schema/SDK/API/index/evaluator/engine code |
| No Sprint 2 scope entered Week 2 | PASS | Only source review, documentation, manual fixtures and static artifact checks performed |
| No fabricated metric/result/approval | PASS | Authored expectations, illustrative source numbers and synthetic ordering timestamps explicitly marked; live usage/latency/model responses absent; no evaluator scores generated |
| Formal S1-01 Sprint 1 exit | BLOCKED | Canonical fit, policy/config decisions, planning amendment and named acceptance remain outstanding |

## Validation evidence

The [validation guide and packaged helpers](validation/README.md), [reproduction record](validation/reproduction-results.json) and [overall report](week1-closeout-validation.json) document static artifact checks: JSON parsing, contiguous event order, parent/dependency references, state/tool/approval/PO invariants, exact source hashes/spans, citation membership, abstention and label-projection checks, relative documentation links, allowed change scope and `git diff --check`. These are **checks of authored artifacts**, not a production test suite, schema validator, evaluator or model experiment. Fixture-specific manual reasoning and original-draft reviews are in fixtures/README.md.

No CI, API, SDK, model, embedding, retrieval index, purchasing tool or policy engine was run. The two review helpers now live under `docs/architecture/reference-applications/validation/`; the existing prompt validator remains under `prompt-pack/`. They inspect authored assets only and do not alter production tests or add application functionality. Separately, the supplied v1.6 offline validator and regression runner were previously executed on review copies; their results and limitations are in the [joint review](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal). The [v1.5 review](schema-v1.5-review.md#reproduced-validation-and-limits) remains historical. This does not establish canonical contract approval or runtime correctness.

## Separate acceptance milestones

Contract approval and runtime validation require different evidence. A documentation PASS never establishes live Gemini compatibility, and contract sign-off never authorizes skipping the pre-implementation validation gate.

| Milestone | When | Required evidence / owner | Current status |
|---|---|---|---|
| Contract freeze | End of Sprint 1, before production implementation | Reviewed exact Gemini model/configuration choice with capability documentation; retrieval/embedding design decisions; resolved policy/interface blockers; manual procurement and RAG traces validated against Schema v1; written Ahmed/Mohab/Mohamed/Alaa sign-offs tied to the revision. Nour coordinates | BLOCKED; model selected and configuration proposals documented; shared alignment and exact-revision acceptance absent |
| Gemini runtime compatibility | Start of Sprint 2, before production application implementation or reproducible live traces | Controlled validation of actual API access, all five tool proposal/result mappings, structured RAG output and effective parameters; record exact model/configuration, observed responses and pass/fail evidence. Nour/Alaa, with Mohab on mapping | BLOCKED; no live validation performed |
| API workload readiness | Access review before production implementation; quota/billing validation before workload generation | Actual API-project access, quota/rate limits and billing evidence plus workload/cost assessment, independent of consumer subscriptions. Nour/Alaa | BLOCKED; OD-LLM-02 remains OPEN |
| RAG runtime readiness | During authorized RAG implementation, before accepting the runnable RAG path | Validate the selected embedding configuration against the chosen vector store, dimensions and retrieval behavior; preserve configuration/version evidence. Nour/Mohab, Ahmed/Alaa review | PENDING future implementation; no embedding calls or index built |

The model-selection portion of OD-LLM-01 can be recorded separately from its live-validation portion. Do not mark the entire item CLOSED until both have evidence. Contract freeze requires the design decisions and agreed validation plan; later runtime checks remain explicitly pending and block production implementation or workload generation at their stated gates. No unresolved policy or schema decision is waived. This clarification does not resolve the existing S2/S3 policy-engine scheduling conflict in OD-06.


## Remaining Week 2 closeout actions before coding

1. Mohab resolves R16-01–09 while retaining the verified prior fixes; Nour reviews application fit against original E01–E27/WG-01–08. Mohamed and relevant reviewers resolve the remaining policy-stage/approval/result decisions and minimal S2 real-policy scope/date with the plan owner. Encode and manually validate the four trajectories in the agreed canonical draft.
2. Nour/Mohamed freeze actual policy truth tables, approval validity/continuation, mock scope, binding/recovery and budgets. Nour/Alaa/Mohab review the completed Gemini, embedding/retrieval and execution-budget proposals, agree shared conventions and separately verify access; no live test during this task.
3. Ahmed accepts corrected failure/overlap/timeout/supplier examples and the qualitative RAG/citation rubric; Alaa agrees provenance/leakage/split conventions. Plan owner accepts or revises the proposed SC-01–03 schedule amendment without expanding S3-01 silently.
4. Obtain exact-revision Mohab/Ahmed/Mohamed/Alaa sign-offs and Malak acknowledgment/independent S1-07 closeout; then mark a genuinely frozen baseline. No owner acceptance is inferred from this local review.

After these design-entry gates, authorized Sprint 2 work begins with the separately recorded live access/compatibility validation before production application implementation. This package does not perform that work.
