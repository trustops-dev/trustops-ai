# Story traceability

Revision 0.3 · 2026-10-19 · DRAFT. Part of the [dashboard UX architecture](README.md).

Each acceptance criterion of the seven dashboard stories (US-34 to US-40, user stories v2.2), the Epic 7 Definition of Done, and the criteria of other stories that change what a screen shows, mapped to the design element that satisfies it. "Designed" means the wireframes, matrix and navigation cover it. It does not mean built or verified.

| Story | Criterion | Design element | Fields and links | Status |
|---|---|---|---|---|
| US-34 | All six elements (application cards, trace count, decision distribution, top failure classes, recent gate status, trend) on one screen | Overview tiles, trend chart and application cards | `OVW-02` `OVW-04` `OVW-06` `OVW-07` `APP-01` `REL-01` | Designed |
| US-34 | Clicking a failure class or an application card opens a pre-filtered Trace Explorer | Links on the failure class tile and on each card | N-02 N-03 | Designed |
| US-34 | Live aggregates for both applications, nothing hardcoded | Every aggregate is served by its owner; the page computes none | `OVW-02` `OVW-04` `OVW-05` `OVW-06` `OVW-07` | Designed |
| US-35 | Each card shows all four version identifiers without truncating the suffix | Full-width card; identifiers wrap and never truncate | `APP-05` | Designed |
| US-35 | The latest gate decision links to its full gate record, and the latest evaluation run is shown | Gate decision link and evaluation run line on each card | `APP-08` `REL-01` N-08 | Designed |
| US-35 | Version data matches the registry, with no frontend-computed values | Alaa owns version values; the page renders them | `APP-05` `APP-06` `APP-07` | Designed |
| US-36 | All six filters (application, version, date, failure label, policy/security verdict, reliability decision) available and combinable | One Filters panel with chips and Clear all filters | `APP-01` `APP-05` `TRX-02` `RCA-01` `TRD-62` `TRD-63` `RCA-07` | Designed |
| US-36 | Filter and pagination state in the URL | Navigation model, URL state | N-10 | Designed |
| US-36 | Returning from Trace Detail preserves filter and investigation context | Breadcrumb and Back restore the origin with its filters | N-10 N-12 | Designed |
| US-37 | Every event type renders in order with parent and child relationships | Ordered timeline plus the backend-derived graph | `TRD-20` `TRD-21` | Designed |
| US-37 | Proposed, blocked, failed and successful tool actions are visually and textually distinguishable | Separate rows for proposal, guard rejection, pre-tool verdict, dispatch and result, with unique signatures | `TRD-40` `TRD-43` `TRD-44` `TRD-45` `TRD-47` | Designed |
| US-37 | Missing evaluator or token data is an explicit state, never zero | Absence states on every field | `TRD-14` `TRD-60` | Designed |
| US-37 | Version context on events | Version snapshot and per-call exceptions | `TRD-80` | Designed |
| US-38 | The retrieved-document table shows document ID, score and rank for every retrieval event | Retrieved documents and scores tables | `RAG-05` `RAG-06` | Designed |
| US-38 | Groundedness and citation precision shown with metric name, direction and unit | Metric rows with name, direction, unit and evaluator version | `RAG-10` `RAG-21` | Designed |
| US-38 | A person unfamiliar with a seeded trace names its failure type from this screen alone | Failure type in the inspector header, plus query, retrieval, context, answer and abstention | `RCA-01` `RAG-04` `RAG-09` `RAG-15` | Designed; the task-based review needs the built screen |
| US-38 | The screen shows the query, expected evidence, citations and unsupported claims | Query, expected evidence, citation and unsupported-claim rows | `RAG-01` `RAG-09` `RAG-13` `RAG-14` `RAG-15` | Designed |
| US-39 | The Top-3 causes show evidence scores in the engine's order, with no frontend re-ranking | Ordered cause list labeled evidence score | `RCA-05` | Designed |
| US-39 | Every cause and every evaluator finding deep-links to its supporting event in Trace Detail | Evidence link on each item | `RCA-06` `TRD-60` N-17 | Designed |
| US-39 | The decision shows its contributing rule path, not only the label | Decision and rule path | `RCA-07` `RCA-08` | Designed |
| US-39 | The screen shows the label, classifier score, rule findings, evaluator evidence, causes and decision | Diagnosis, Causes and Decision tabs | `RCA-01` `RCA-02` `RCA-04` `RCA-05` `RCA-07` | Designed |
| US-40 | Baseline and candidate versions and deltas for RAG, Agent, Security and Overall shown side by side | Metrics by area table and release identities | `REL-03` `REL-04` `REL-07` | Designed |
| US-40 | BLOCK states the approved baseline is retained; REVIEW states human action is required | Candidate disposition line | `REL-18` | Designed |
| US-40 | Displayed metrics and verdict match the canonical gate artifact, with no frontend recalculation | Artifact reference and CI status shown with the decision | `REL-17` `REL-01` `REL-04` | Designed |
| US-40 | Critical scenarios shown | Critical scenarios section | `REL-09` `REL-11` N-24 | Designed |
| Epic 7 DoD | Not evaluated, Evaluator failed and Not applicable are always distinct, and nothing renders as zero | Eight absence states with unique signatures | `OVW-05` `TRD-60` `RAG-21` `REL-04` | Designed |
| Epic 7 DoD | Every score, badge and finding shows meaning, unit and direction, provenance and version | Matrix rule 4 and vocabulary rule 7 | `TRD-60` `RAG-10` `RAG-21` `REL-05` | Designed |
| Epic 7 DoD | PASS, REVIEW, BLOCK and severity use text or an icon, never colour alone | Signature table: label, glyph, outline and fill | `RCA-07` `REL-01` `TRD-43` | Designed |
| Epic 7 DoD | Verified against the shared review checklist (Frontend README section 10) | The checklist is not in this repository | Q-01 | Open |
| US-03 | An agent-guard rejection is its own trace event, separate from the policy check | Guard rejection row and the "stopped by" layer | `TRD-47` `TRD-44` | Designed |
| US-12 | The frontend renders the backend-derived graph and derives nothing | Graph region with a text equivalent | `TRD-21` | Designed |
| US-17a | The security verdict (score or verdict, category) is a trace signal | Security verdict row | `TRD-63` | Designed |
| US-18 | A failed evaluator run is distinguishable from a low score | Evaluator failed state and failure detail | `TRD-60` `TRD-61` | Designed |
| US-21 | Policy results are attached to the trace with verdict, evidence and criticality | Policy verdicts row | `TRD-62` | Designed |
| US-22 | The synchronous pre-tool ALLOW or BLOCK is visible, separate from post-run evaluation | Pre-tool verdict and policy request rows | `TRD-42` `TRD-43` | Designed |
| US-25 | A review can be submitted from Trace Detail or Failure & RCA, appears in the review history immediately, and is never edited | Record review action and review history | `TRD-70` `RCA-07` | Designed; permission wording open (Q-07) |
| US-26 | Audit history viewable per trace and per release evaluation, with administrator actions flagged | Audit trail rows | `TRD-71` `REL-20` | Designed |
| US-27 | Roles enforced by the backend; BLOCK override requested then approved; raw payloads for the Administrator only; the Auditor is read-only | Roles and access page, override flow, payload visibility | `TRD-83` `REL-19` | Designed; actions behind Manage unspecified (Q-13) |
