# TrustOps AI — Week 1 Reference Application Contracts

**Workload proposal prepared — 2026-11-06:** [API ownership and workload candidate 0.1](workload-review/od-llm02-v0.1/README.md) supplies execution/call/token/retry/concurrency estimates and public-price token subtotals. Actual API project/access/billing owner, account quotas and applicable charges remain unconfirmed. ALA-05/ALA-08 and OD-LLM-02/OD-12-BUDGET stay open; no live execution is authorized.

**Alaa response recorded — 2026-11-06:** [Scoped review of commit 479cab0](reviews/alaa-479cab0-review.md) received from user-supplied email text. Overall status: **PARTIAL / CONDITIONAL**. Candidate/principle acceptance and remaining conditions are recorded separately; no full specialist sign-off or joint freeze. The email date and message reference were not supplied.

**Current publication and handoff** is recorded in [the PR #27 publication record](publication-handoff.md). Earlier preparation metadata is the pre-publication snapshot.

**Current mapping — 2026-11-06:** [Draft v1.6 E01–E27 assessment](schema-v1.6-evidence-mapping.md) and [exact row evidence](schema-v1.6-evidence-mapping.json) cover all 27 requirements: **9 OK, 9 CHANGE REQUIRED, 9 OPEN**. The [rerun observations](schema-v1.6-review-observations.json) retain R16-01–09 as the current review baseline. v1.5 is historical comparison evidence. Mapping preparation is complete; corrected files, unresolved conventions and joint acceptance remain pending. OD-05 stays blocking; no new signature or runtime verification is implied.

**Reproducible review checks:** the [validation guide and packaged helpers](validation/README.md) provide repository/output arguments and exact commands for the paper fixtures, corpus/boundaries and existing prompt examples. These remain offline artifact checks; shared acceptance and runtime validation are pending.

**2026-11-02 corpus/boundary completion:** RAG revision 0.9 adds the [synthetic corpus specification](corpus-review/README.md); [ten manual boundary cases](manual-boundary-cases.md) include denied approval and symbolic below/equal/above T. These complete the remaining owner drafting items, not shared acceptance or runtime tests. See [current closeout](week1-owner-closeout.md).

**Owner closeout revision 0.13 — 2026-11-05.** References and offline validation refreshed after decision consolidation; shared acceptance remains PENDING.

Start with [Week 1 owner closeout](week1-owner-closeout.md), the [latest v1.6 joint review](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal), [20 focused decision requests](open-decisions.md#pending-decisions-and-exact-requests) and the [exact-file manifest](week1-review-manifest.json). R16-01–09 are the current review findings; disposition remains CHANGES REQUIRED. The [v1.5 review](schema-v1.5-review.md) and its row mapping are historical comparison evidence; the current v1.6 mapping is linked above; full schema acceptance remains pending. Provider ADR 0.9, tool contract 0.8, state contract 0.7, RAG contract 0.9, budget ADR 0.1 and prompt pack 1.1 remain proposed baselines. No live provider or application verification is claimed.

**Historical Sprint 1 freeze-candidate label — revision 0.6, 2026-11-01. NOT FROZEN.** Documentation and manual review evidence only; specialist approvals remain PENDING. Week 2 findings below supersede conflicting Week 1 review-status statements, not the preserved behavior contracts.

## Earlier Week 2 review context — preserved

The Week 1 contracts have been reviewed against the supplied proposal, sprint plan, repository architecture, Figures 1–5 and the available team drafts on `dev`. This revision preserves the application designs and adds actual draft-field mapping, concrete owner correction requests, four manual evidence fixtures, validation outcomes and an unsigned review matrix. It is a **review-ready freeze candidate**, not a completed freeze or permission to start production implementation.

Repository inspection on 2026-11-01 found `main` at `3ef7da1f190cd5a22efdcd6798af59199924bac3` and the newer team documentation on `dev` at `72e7975384d5e8b32d1e0e68ff4742cce96fa336`. The local task branch is based on that `dev` commit, following CONTRIBUTING. No remote branch, PR, message or approval was created by this task.

Start with the [Week 2 audit](audit.md), [27-row actual-schema mapping](trace-evidence-contract.md#week-2-mapping-to-mohabs-actual-draft), [manual fixture record](fixtures/README.md), [current decisions](open-decisions.md) and [acceptance](acceptance.md). The detailed Week 1 state/tool/RAG/scenario specifications remain the maintained contracts.

**Results:** four manual application trajectories pass their stated conceptual checks. None is certified as a canonical Trace Schema v1 trace: Mohab's current document is a draft, its enum/field gaps remain, and no frozen executable trace model is present in `packages/contracts`. The fixtures are expressly paper evidence ledgers, not an alternative shared schema. JSON and referential checks do not establish runtime behavior or schema approval.

**Retained decisions:** Google Gemini API, selected `gemini-3.8-flash`; explicit Python state machine and staged RAG pipeline. Orchestration is **APPROVED FOR SPRINT 2 IMPLEMENTATION** as the requested technical design disposition; overall S1-01 remains BLOCKED pending schema/policy/configuration alignment and named acceptance. No live provider, embedding, tool, SDK, API, evaluator or database execution was performed.

## Revision history (preserved)

Task S1-01 · Nour El-Rouby · 7 October 2026 · Revision 0.5

**Status: review-complete draft; NOT frozen or team-approved.** Documentation only. This package is ready for the freeze review, but source conflicts, canonical-schema alignment and named sign-offs remain open. No production functionality, experimental result or runtime validation is claimed.

Revision 0.2 applies the user-selected **Google Gemini API** as the single primary LLM provider. At revision 0.2, exact model selection remained OPEN before Sprint 2; embeddings remain an independent OPEN decision. The explicit Python state machine and all business behavior remain unchanged. Provider selection is confirmed by the current instruction; full contract freeze and team sign-offs remain pending.

Revision 0.3 fixes three tool-output table headers and separates contract sign-off from Gemini runtime and workload validation. Exact model selection still precedes Sprint 2 production implementation; no open decision is closed or team approval inferred. See the acceptance milestones for evidence and timing.

Revision 0.4 records the user-selected **Gemini 3.8 Flash** (`gemini-3.8-flash`) for both reference applications. Google’s official model documentation confirms this identifier, function calling and structured outputs. Model-name selection is resolved; effective configuration, team review, API access and runtime validation remain pending. Embeddings remain independent and OPEN.

Revision 0.5 completes the detailed SC-01–SC-03 scenario specifications and proposes Week 7 recipe implementation / Week 8 integration through an explicit S4-06 scope and dependency amendment. The existing S3-03 supplier-breach fixture supports that work. OD-08 now has a complete proposal awaiting review; the authoritative sprint plan and all owner approvals remain unchanged.

## Read in order

1. [Audit and source reconciliation](audit.md)
2. [Architecture overview](overview.md)
3. [Procurement behavior](procurement-state-contract.md)
4. [Five procurement tools](procurement-tool-contracts.md)
5. [Enterprise RAG](rag-contract.md)
6. [Failure matrix, detailed scenario specifications and proposed schedule](failure-planning-matrix.md)
7. [Application evidence requirements](trace-evidence-contract.md)
8. [Orchestration and provider ADR](../../adr/reference-application-orchestration-and-llm.md)
9. [Cross-team handoffs](handoffs.md)
10. [Open decisions](open-decisions.md)
11. [Acceptance and Week 2 review](acceptance.md)

The [Procurement and RAG prompt pack](prompt-pack.md) adds reusable template candidates, synthetic input/output examples, citation bindings and an offline review validator. It preserves the existing five-tool scope and pending contract gates; these assets are not live model results or canonical traces.

## Status vocabulary

- **FACT**: authoritative supplied source, identified by document and section/task.
- **DECISION**: proposed engineering contract selected in this package, pending team ratification.
- **ASSUMPTION**: unverified operating condition; not a project fact.
- **OPEN**: unresolved decision with accountable reviewer and closure evidence.
- **PLANNED**: future implementation or experiment; not completed.
- **VERIFIED DOCUMENTATION**: coverage or consistency inspection performed on these documents only.
- **VALIDATED RESULT**: runtime/experimental evidence; none produced by this task.

All newly named fields, enums, tool payloads and local status values below are DECISIONs, not pre-existing project interfaces. They describe application semantics for review; Mohab owns serialization into canonical contracts. Existing source terminology and the eight primary failure classes are preserved.

## Applying to a repository

The standalone revision 0.5 package was prepared before repository access. On 2026-10-15 it was compared with `trustops-dev/trustops-ai` and integrated for review on a task branch from `dev`. See the [repository integration record](repository-integration.md) for the audited commit, file mapping, unavailable source attachments and remaining review requirements. This import does not freeze the contracts or establish runtime compatibility. The supplied source folder remains unchanged.

This Week 1 import adds no scripts, executable tools, schemas, endpoints, indexes, SDKs or engines. The repository contains the maintained review copy of these Markdown specifications; make subsequent reviewed changes here.
