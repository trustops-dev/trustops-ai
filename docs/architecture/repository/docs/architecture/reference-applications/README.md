# TrustOps AI — Week 1 Reference Application Contracts

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
