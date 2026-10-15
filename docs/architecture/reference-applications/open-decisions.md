# Open decisions and blockers

No numeric policy, retrieval confidence or reliability threshold is invented. A selected design is not a validated implementation. All entries are OPEN unless explicitly marked below. Owners indicate proposed accountable reviewers within approved subsystem ownership, not evidence that they accepted work.

| ID | Decision / current proposal | Owner(s) | Closure evidence | When / effect |
|---|---|---|---|---|
| OD-01 | PARTIAL: repository and duplicate-doc inventory inspected; import awaits PR review and merge | Nour / repository maintainer | [Audited commit and file mapping](repository-integration.md); approved import PR and merge commit still required | Before completing repository integration; contract freeze and owner sign-offs remain separate |
| OD-02 | Calculation tool missing from PRE_APPROVAL policy list (D3) | Mohamed + Nour | Reviewed allowlist/state mapping explicitly permits read-only calculation without weakening PO restriction | Week 2 before freeze; blocks executable procurement contract |
| OD-03 | Approval rule values/currencies/levels, policy text/config authority and equality semantics | Mohamed | Versioned truth table, fixture IDs and rule-to-source mapping; proposal says `>` | Week 2 before implementation; no value assumed |
| OD-04 | Approval record validity, amount/supplier/revision binding, denial, expiry/revocation and resume authority | Mohamed + Mohab + Nour | Approved evidence and continuation contract, manual stale-approval case | Week 2; freeze blocker |
| OD-05 | Canonical Trace Schema v1 and pre-tool transport/object mapping | Mohab + Mohamed | E01–E27 mapping, valid manual fixtures, verdict/error types | Week 2; freeze blocker |
| OD-06 | S2-04 real policies vs S2-01 stub/S3 integration ambiguity (D4) | Mohamed + Mohab + Nour / plan owner | Written minimal S2 enforcement commitment and S3 full-integration date | Week 2; integration planning blocker |
| OD-07 | Provider selection resolved to Google Gemini API by current user instruction; Gemini 3.8 Flash (`gemini-3.8-flash`) selected by the user; configuration/validation/access work tracked in OD-LLM-01 and OD-LLM-02 | Nour + Alaa; Mohab consulted | Close the referenced items; freeze effective configuration and SDK/API choice | Provider selected; linked validation gates remain OPEN; no Week 1 API execution |
| OD-08 | OPEN — SC-01–SC-03 specifications and schedule proposal complete in revision 0.5; authoritative assignments still require approval | Nour + Ahmed + plan owner; Mohamed consulted for supplier fixture, Mohab/Alaa for evidence and dataset order | Approve the explicit S4-06 recipe-scope/dependency amendment: Week 7 construction, Week 8 integration; identify S3-03 Week 6 supplier fixture handoff; record capacity, dataset sequencing and reviewers. See [detailed proposal](failure-planning-matrix.md) | Week 2 review; no coding or plan amendment executed; S3-01 four-case scope and S5 benchmark retained |
| OD-09 | Overlapping primary/secondary labels and attempted vs prevented vs realized violation semantics | Ahmed + Mohamed | Annotation examples for bypass with/without false completion and missed injection detector | Week 2; taxonomy-fit blocker |
| OD-10 | pgvector selected primary; availability, chunking/index config, k and corpus membership unverified; embedding selection tracked separately in OD-RAG-01 | Nour + Mohab; Alaa versioning | Environment decision and retrieval/config specification without invented score threshold | Week 2; architecture/config freeze needed |
| OD-11 | Sufficiency rubric, document/chunk relevance unit and citation semantic checks | Nour + Ahmed | Reviewed answer/abstention examples and evidence mapping | Week 2 qualitative contract; numeric tuning only after empirical evidence |
| OD-12 | Retry/time budgets, idempotency scope and one-item mock scope; draft PO recovery is read-only with RECOVERY_PENDING and no redispatch. Ratify atomic authorization/transition binding, trusted continuation and ledger evidence semantics; any creation retry requires a separately reviewed contract | Nour + Mohamed + Mohab | Reviewed deterministic mock/replay examples and configuration decisions | Week 2 contract; implementation Sprint 2 |
| OD-13 | Immutable IDs/config hashes and source snapshot retention/redaction | Alaa + Mohab + Nour | Versioning convention; synthetic payload retention and missing-metadata handling | Week 2; reproducibility sign-off |
| OD-14 | Four S1-01 written owner sign-offs and Malak acknowledgement absent | Ahmed, Mohab, Mohamed, Alaa; Malak | Signed revision references and conditions closed | End Sprint 1; formal freeze BLOCKED |
| OD-15 | Numeric reliability/regression thresholds | Mohamed + Alaa + Ahmed | Approved-baseline distributions, chosen tolerances and versioned rationale | S5-03/S5-04; deliberately deferred, not a Week 1 omission |
| OD-16 | Procurement-only rule applicability to RAG wording (D5) | Mohamed + Nour + plan owner | Acknowledge no PO tools/stages in RAG; use not-applicable evidence | Week 2; avoid accidental app scope expansion |

## Provider-change decisions

| ID | Status | Criteria and closure evidence | Owner / deadline |
|---|---|---|---|
| OD-LLM-01 — Gemini model/configuration and compatibility | PARTIAL — model selected; configuration and validation pending | User selected Gemini 3.8 Flash (`gemini-3.8-flash`) on 2026-10-07. Official model documentation confirms the stable identifier, function calling and structured outputs; see ADR. Still required: effective configuration, version-semantics review, actual API access and compatibility checks for all five tool mappings and structured RAG output. No live validation or measured performance claimed | Nour + Alaa; Mohab consulted. Before Sprint 2 production implementation and reproducible application traces |
| OD-LLM-02 — Gemini API quota/billing validation | OPEN | Validate the actual Developer API project, permitted quota/rate limits, billing and any applicable free-tier eligibility independently from Gemini consumer Plus/Pro subscriptions. No free usage, subscription benefit or cost saving is assumed. Record a workload/cost assessment and effective limits | Nour + Alaa. Access review before production implementation; quota/billing validated before workload generation |
| OD-RAG-01 — Embedding model/provider | OPEN — before RAG implementation | Independent selection based on selected vector store, dimensions, retrieval quality, API availability, reproducibility and quota/cost. No automatic coupling to Gemini generation; retain existing Sprint 1 retrieval/config review target | Nour + Mohab; Ahmed retrieval review and Alaa versioning. Before RAG implementation |

Track OD-LLM-01 selection approval and live compatibility validation separately, each with date, reviewer and evidence. Contract freeze requires exact model/configuration selection; the item stays PARTIAL until remaining configuration review and live validation also pass before production implementation. OD-LLM-02 retains its access-review and pre-workload quota/billing deadlines. OD-RAG-01 retains the Sprint 1 design-review target and must be resolved before RAG implementation; implementation tests are separate. See [acceptance milestones](acceptance.md). Revision 0.4 adds the user’s model selection and official capability documentation. No team sign-off or runtime evidence has been received.

These entries refine OD-07/OD-10 without changing their owners or the sprint sequence. Gemini integration, API calls and embedding/index implementation remain outside this documentation task.

## Decisions made for this draft

Explicit Python state machine unchanged; user-selected Google Gemini API as single primary LLM provider, Gemini 3.8 Flash (`gemini-3.8-flash`) selected; configuration and runtime validation pending under OD-LLM-01; embeddings independently OPEN under OD-RAG-01; pgvector primary conditional on availability; no multi-provider layer; state/stage separation; proposal/check/execution distinction; no invented approval on the no-approval branch; preserve raw and delivered outputs separately. The provider change is explicitly user-directed; other decisions retain their existing review status. Model selection is recorded; no runtime validation is implied.

## Change-control rule

Close decisions in their owning specification, then update this register with reviewer/date/revision. If sources disagree, record source and precedence; do not rewrite the proposal to fit an implementation. Freeze only after the schema walkthroughs and four sign-offs exist. Later empirical thresholds must not be backfilled into this Week 1 package as though they were known now.

## Revision 0.5 — OD-08 preparation completed

The three scenario specifications, paired controls, evidence/acceptance requirements and task-amendment proposal are documented in [failure planning](failure-planning-matrix.md). The Week 1 drafting action is complete. OD-08 remains OPEN solely for review and agreed scheduling; label/cause mapping under OD-09, schema fit and formal sign-offs remain separate dependencies. No implementation result or owner acceptance is implied.
