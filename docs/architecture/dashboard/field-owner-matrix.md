# Field and data-owner matrix

Revision 0.1 · 2026-10-17 · DRAFT for owner review. Part of the [dashboard UX architecture](README.md).

Every diagnostic field the seven screens show appears below exactly once. Each row names one **home screen** (the section it sits in) and one **data owner**. Nothing here is a canonical schema, API route or database column; Mohab maps rows to `packages/contracts` under S1-02.

## How to read this matrix

| Term | Meaning |
|---|---|
| **Home screen** | The one screen where the field is defined and shown in full. The ID prefix matches the screen: `OVW` Overview, `APP` Applications, `TRX` Trace Explorer, `TRD` Trace Detail, `RCA` Failure & RCA, `RAG` RAG Diagnostics, `REL` Release Gate. |
| **Projection** | A read-only echo of a field on another screen, such as a decision badge in a Trace Explorer row. A projection carries the same value from the same owner and is never a second field. Wireframes mark projections `{>ID}` and home fields `{ID}`. |
| **Data owner** | The backend owner accountable for the value's meaning, correctness and schema evolution. It is not the serving layer. `apps/api` serves every value; the dashboard renders it and never infers, recomputes or overrides a decision, label or cause. |
| **Aggregates** | A count or distribution belongs to the owner of the values being counted. Mohab's envelope owns only trace-level counts such as volume and completeness. |
| **Shape** | `id` identifier · `text` · `enum` · `ts` timestamp · `num` number · `count` counts or distribution · `flag` boolean · `obj` grouped record · `list` · `table` · `ref` link to another record · `ver` immutable version reference · `graph` nodes and edges. |
| **Absence** | Which no-value states can occur: `NE` Not evaluated · `EF` Evaluator failed · `NA` Not applicable · `PE` Awaiting result · `UN` Unavailable · `ME` Missing evidence · `RD` Redacted · `NC` Not configured. A dash means the field always has a value. Definitions and presentation are in the [status vocabulary](status-vocabulary.md). |
| **Basis** | `FACT`: required by the cited S1-01 source. `DECISION`: UX proposal that the owner must confirm or reject. `OPEN`: depends on an open decision or [question](README.md#open-questions). Same words as the [S1-01 status vocabulary](../reference-applications/README.md#status-vocabulary). |
| **Source** | `E01`–`E27` rows of the [trace evidence contract](../reference-applications/trace-evidence-contract.md). `SC` [state contract](../reference-applications/procurement-state-contract.md). `TC` [tool contracts](../reference-applications/procurement-tool-contracts.md). `RC` [RAG contract](../reference-applications/rag-contract.md). `FM` [failure matrix](../reference-applications/failure-planning-matrix.md). `OV` [overview](../reference-applications/overview.md). `HO` [handoffs](../reference-applications/handoffs.md). `OD-nn` [open decisions](../reference-applications/open-decisions.md). |

The five owners: **Nour** (reference applications and scenarios), **Ahmed** (evaluators, classifier, RCA), **Mohab** (trace envelope, ordering, ingestion, execution graph), **Mohamed** (policy, approvals, reliability decisions, human review), **Alaa** (versions, datasets, experiments, release gate). Malak owns the dashboard and is not a data owner.

### Rules every row follows

1. A field has one home and one owner. If two owners contribute, the row names the accountable one and the Notes below say what the other supplies.
2. The dashboard never shows a missing value as zero, blank or PASS. It shows one of the absence states.
3. `PASS`, `REVIEW`, `BLOCK` (reliability), `ALLOW`/`BLOCK` (pre-tool), application outcome and human review are separate fields with separate presentation. See [status vocabulary](status-vocabulary.md).
4. Fields tagged `OPEN` render as `Not configured` or `Awaiting result` until their owner closes the decision. The UI invents no value, threshold or default.

### UI-local state (no backend owner)

These are not diagnostic fields. They live in the browser or URL and have no data owner: sort order, column visibility, page size and page number, expanded or collapsed sections, selected tab or section, search text, applied filter chips, selected time range, selected baseline/candidate pair, graph zoom and pan, theme. The *values* offered by a filter always come from the field it filters.

## SCR-OVW — Overview

Page pattern: Dashboard. Fixed glance, at most five tiles, read-only.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| OVW-01 | Header | Reporting window: label, start and end of the period every tile covers | obj | Mohab | OV, E26 | UN | DECISION |
| OVW-02 | Tile 1 | Trace volume in window: total, and by application | count | Mohab | E01, E26 | UN | DECISION |
| OVW-03 | Tile 2 | Data freshness: time of the latest ingested trace, ingest lag | ts | Mohab | E25 | UN | DECISION |
| OVW-04 | Tile 3 and chart | Reliability decision distribution, overall and by application: PASS, REVIEW, BLOCK and "no decision yet" counts, always shown as separate numbers | count | Mohamed | OV, HO | PE | FACT |
| OVW-05 | Tile 4 | Evaluation coverage: counts of evaluated, Not evaluated, Evaluator failed and Not applicable | count | Ahmed | HO, FM | NE EF NA | FACT |

The fifth tile is the latest release gate decision, a projection of `REL-01`. The "needs attention" list under the chart shows projections of `TRX` and `TRD` fields.

## SCR-APP — Applications

Page pattern: List. A row opens a read-only slide-over summary, because an application detail route would be an eighth screen.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| APP-01 | Table | Application identity: ID, display name, kind (Procurement Agent or Enterprise RAG Assistant) | obj | Nour | E01, E26 | — | FACT |
| APP-02 | Table | Synthetic-data and mock-tool marker | flag | Nour | E01, E20 | — | FACT |
| APP-03 | Table | Run-status mix: counts of ACTIVE, WAITING_APPROVAL, RECOVERY_PENDING, BLOCKED, FAILED, CANCELLED, SUCCEEDED | count | Nour | SC | — | FACT |
| APP-04 | Table | Last trace received, per application | ts | Mohab | E25 | UN | DECISION |
| APP-05 | Slide-over | Ingestion health: events received, events rejected, incomplete traces | count | Mohab | E25, OV | UN | FACT |
| APP-06 | Slide-over | Deployed configuration versions: application, prompt, model/config, retriever, corpus/index, tool catalog, policy set, scenario/config | ver | Alaa | E26, OD-13 | UN | FACT |
| APP-07 | Slide-over | Provider and configured model identifier (`gemini`, `gemini-3.8-flash`), and returned model version when known | obj | Alaa | E26, OD-LLM-01 | UN | FACT |
| APP-08 | Slide-over | Policy applicability: which policy rules apply to this application; procurement rules are Not applicable to the RAG assistant | table | Mohamed | OD-16, SC | NA | FACT |

## SCR-TRX — Trace Explorer

Page pattern: List. Row columns are mostly projections of Trace Detail fields; only list-identity fields are homed here.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| TRX-01 | Table | Trace identifier | id | Mohab | E01, E25 | — | FACT |
| TRX-02 | Table | Trace start time and duration | ts | Mohab | E01, E25 | UN | FACT |
| TRX-03 | Table | Event count and trace completeness: complete, incomplete or inconclusive | enum | Mohab | E25, FM | ME | FACT |
| TRX-04 | Table | Execution mode and scope: live model, synthetic output replay, synthetic proposal replay, boundary fixture; full-application or boundary scope | enum | Nour | FM, E27 | NA | FACT |
| TRX-05 | Table | Scenario run reference (opaque) and linked control-pair reference | ref | Alaa | E27, FM | NA | FACT |

## SCR-TRD — Trace Detail

Page pattern: Detail with a sticky section navigation (nine sections). One trace; the primary place to verify evidence.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| TRD-01 | Summary | Application outcome. Procurement: PO created, waiting for approval, blocked, failed, recovery pending. RAG: answer, abstention, error | enum | Nour | E21, E24, E25 | — | FACT |
| TRD-02 | Summary | Run status | enum | Nour | SC | — | FACT |
| TRD-03 | Summary | Reliability decision PASS, REVIEW or BLOCK, with decision time | enum | Mohamed | OV, HO | PE | FACT |
| TRD-04 | Summary | Decision rationale: the findings and references that triggered the decision, each linking to its evidence | list | Mohamed | OV, E18 | PE | DECISION |
| TRD-05 | Summary | Primary failure class (one of eight, or NORMAL) and classifier version | enum | Ahmed | FM | NE EF | FACT |
| TRD-06 | Summary | Secondary findings, retained next to the primary class and never dropped | list | Ahmed | FM | NE EF | FACT |
| TRD-10 | Request and model | Raw request and normalized request: item, quantity, amount, currency, supplier, requester, purpose; raw-to-normalized links | obj | Nour | E01, E08, TC | UN | FACT |
| TRD-11 | Request and model | Request revision and lineage to prior attempts | list | Nour | E08, SC | — | FACT |
| TRD-12 | Request and model | Normalization and validation details, including clarification outcomes | list | Nour | E08 | NA | FACT |
| TRD-13 | Request and model | Model call: prompt or template version, rendered input reference, generation parameters, response, refusal or error | obj | Nour | E02 | UN NA | FACT |
| TRD-14 | Request and model | Model call telemetry: latency, token usage, returned model identifier and version | obj | Nour | E02 | UN NA | FACT |
| TRD-20 | Timeline | Ordered event timeline: event type, occurrence order, timestamp, parent link | list | Mohab | E09, E25 | ME | FACT |
| TRD-21 | Timeline | Execution graph: nodes, causal edges and multi-evidence references, derived by the backend | graph | Mohab | HO, E09 | ME | FACT |
| TRD-22 | Timeline | State transitions: previous and new state, reason, attempted versus accepted, state revision | list | Nour | E09 | — | FACT |
| TRD-23 | Timeline | Workflow stage at each boundary, with the state-to-stage mapping version | list | Nour | E10, SC | NA | FACT |
| TRD-30 | Procurement evidence | Policy retrieval: raw and effective query, filters, k, ranked policy matches, policy-set and retriever versions, applicability | obj | Nour | E03, TC | NA ME | FACT |
| TRD-31 | Procurement evidence | Supplier check: requested and returned supplier ID, raw and normalized status, directory and record version, lookup outcome | obj | Nour | E11, TC | NA ME | FACT |
| TRD-32 | Procurement evidence | Approval calculation: amount, currency, rule basis, threshold, comparator, policy version, required level or unresolved reason | obj | Mohamed | E12, TC | NA | FACT |
| TRD-33 | Procurement evidence | Approval submission: request ID, approval-request ID, required level, idempotency identity | obj | Mohamed | E13, TC | NA | FACT |
| TRD-34 | Procurement evidence | Approval observation: required and received flags, status, approval ID, actor, time, source | obj | Mohamed | E14, TC | NA PE | FACT |
| TRD-35 | Procurement evidence | Approval binding checks (request revision, supplier, amount, currency, level, version) and authorization basis, including NOT_REQUIRED | list | Mohamed | E14, SC | NA | FACT |
| TRD-40 | Tools and enforcement | Tool proposal: tool name, catalog version, proposal ID, originating model-call reference | obj | Nour | E15 | — | FACT |
| TRD-41 | Tools and enforcement | Tool arguments: raw serialized, parsed values, trusted runtime context kept separate, validation outcome with field errors | obj | Nour | E16 | — | FACT |
| TRD-42 | Tools and enforcement | Pre-execution policy request: proposal reference, argument digest, state revision, stage, evidence references, policy version | obj | Mohamed | E17 | NA ME | FACT |
| TRD-43 | Tools and enforcement | Pre-execution verdict ALLOW or BLOCK, per-policy findings (PROC-APPROVAL-01, PROC-TOOL-STAGE-01, PROC-SUPPLIER-01), reasons, version; timeout, error or missing verdict | obj | Mohamed | E18, SC | NA ME | FACT |
| TRD-44 | Tools and enforcement | Dispatch suppression: NOT_EXECUTED, execution_started false, blocking reference, reason | obj | Nour | E19 | NA | FACT |
| TRD-45 | Tools and enforcement | Tool invocation and result: invocation ID, start and end, mock marker, idempotency key, outcome (CREATED, ALREADY_EXISTS, UNKNOWN_OUTCOME, ERROR), PO ID only if confirmed | obj | Nour | E20, TC | NA ME | FACT |
| TRD-46 | Tools and enforcement | Recovery: RECOVERY_PENDING, read-only ledger lookup outcome, links to the original proposal, key, dispatch and result | obj | Nour | E25, SC | NA PE | FACT |
| TRD-50 | Response | Final response (procurement): raw generated text, delivered text, which was shown, supporting result references or the reason no action occurred | obj | Nour | E21 | NA | FACT |
| TRD-51 | Response | Technical failure, cancellation or pending detail: stage, known or unknown outcome, error category, retry and continuation references | obj | Nour | E25 | NA | FACT |
| TRD-60 | Evaluation and diagnosis | Evaluator results: evaluator name, family and version; result state (value, Not evaluated, Evaluator failed, Not applicable); value or finding; evidence references | table | Ahmed | HO, FM | NE EF NA | FACT |
| TRD-61 | Evaluation and diagnosis | Evaluator failure detail: error category, evaluator run ID, time | obj | Ahmed | HO | EF | DECISION |
| TRD-62 | Evaluation and diagnosis | RCA candidate causes (the fixed nine), rank, and supporting event references | list | Ahmed | FM, HO | NE EF | FACT |
| TRD-63 | Evaluation and diagnosis | Evaluation run history: each versioned re-evaluation, kept beside the original | list | Ahmed | E25, FM | — | FACT |
| TRD-64 | Evaluation and diagnosis | Prompt-injection finding: attack text, location (user input or retrieved chunk), detector outcome | obj | Ahmed | FM | NE EF NA | FACT |
| TRD-65 | Evaluation and diagnosis | Scenario ground truth, evaluation-side only: injected failure, injected root cause, expected behavior | obj | Alaa | FM, E27 | NA RD | OPEN |
| TRD-66 | Evaluation and diagnosis | Reviewer or adjudicated failure label | enum | Ahmed | FM | PE | FACT |
| TRD-70 | Human review and audit | Human review status (none, pending, completed) and review records: reviewer, outcome, rationale, time | list | Mohamed | OV, HO | NA PE | OPEN |
| TRD-71 | Human review and audit | Decision history: every machine decision with its version and time; earlier decisions are never overwritten | list | Mohamed | OV, E25 | — | FACT |
| TRD-80 | Provenance and completeness | Version snapshot for the run (application, prompt, model/config, retriever, corpus/index, tools, policy, scenario/config) and per-call exceptions | ver | Alaa | E26, OD-13 | UN ME | FACT |
| TRD-81 | Provenance and completeness | Redaction and unavailability markers: which field, which reason | list | Mohab | E25 | RD UN | FACT |
| TRD-82 | Provenance and completeness | Missing or inconclusive evidence: expected events that did not arrive | list | Mohab | E25, FM | ME | FACT |

## SCR-RCA — Failure & RCA

Page pattern: Analytics (analytical). Patterns across traces; single-trace diagnosis lives in Trace Detail.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| RCA-01 | KPI and chart | Failure class distribution for the selected range: eight classes plus NORMAL, by application | count | Ahmed | FM | NE EF | FACT |
| RCA-02 | Header | Class definitions and taxonomy version | text | Ahmed | FM, OD-09 | — | FACT |
| RCA-03 | Chart | Primary-class by secondary-finding co-occurrence | table | Ahmed | FM | NE EF | FACT |
| RCA-04 | Chart | RCA cause distribution (the fixed nine), supporting-evidence counts, and the count where no cause is supported | count | Ahmed | FM | NE EF | FACT |
| RCA-05 | Chart | Attempted, prevented and realized violation breakdown | count | Ahmed | OD-09 | NE | OPEN |
| RCA-06 | Chart | Pre-execution enforcement outcomes: ALLOW and BLOCK counts per policy rule | count | Mohamed | E18, FM | NA ME | FACT |
| RCA-07 | Chart | Reliability decisions by failure class | table | Mohamed | OV | PE | DECISION |
| RCA-08 | Chart | Evaluator health: Evaluator failed and Not evaluated rates per evaluator | table | Ahmed | HO | NE EF | FACT |
| RCA-09 | Table | Exemplar traces for each class or cause, linking to Trace Detail | list | Ahmed | HO | NE | DECISION |

## SCR-RAG — RAG Diagnostics

Page pattern: Split Pane. A compact query list on the left, the query inspector on the right. Left-list rows are projections of `RAG-01`, `RAG-19` and `RAG-10`.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| RAG-01 | Inspector: query | Query ID, raw query, effective query, transformation provenance | obj | Nour | E04, RC | UN | FACT |
| RAG-02 | Inspector: query | Retrieval settings: k and filters | obj | Nour | E04, RC | UN | FACT |
| RAG-03 | Inspector: query | Retriever, corpus, index and embedding version identifiers | ver | Alaa | E04, E26, OD-13 | UN | FACT |
| RAG-04 | Inspector: retrieval | Retrieval outcome (success, including empty; or error) and returned count | enum | Nour | RC | — | FACT |
| RAG-05 | Inspector: retrieval | Retrieved documents in returned order: document, source and chunk IDs, versions, snapshot text, content hash, locator | table | Nour | E05 | ME | FACT |
| RAG-06 | Inspector: retrieval | Scores and ranks: raw score, metric kind, direction, one-based rank, tie rule | table | Nour | E06 | UN | FACT |
| RAG-07 | Inspector: context | Selected context: selected IDs, order and spans; rejected IDs with reasons; selection version | table | Nour | E07 | NA | FACT |
| RAG-08 | Inspector: context | Sufficiency outcome and unresolved facets or conflicts | obj | Nour | E07, RC | NA | FACT |
| RAG-09 | Inspector: context | Expected relevant sources (evaluation-side reference) compared with what was retrieved | table | Ahmed | FM, HO | NA RD | OPEN |
| RAG-10 | Inspector: retrieval | Retrieval metrics for the query; unit and value per metric, each with its own state | num | Ahmed | E06, FM | NE EF NA | OPEN |
| RAG-11 | Inspector: answer | Candidate answer and delivered answer text, with the delivery flag | obj | Nour | E22 | NA | FACT |
| RAG-12 | Inspector: answer | Claims: claim ID, text, answer span | table | Nour | E22 | NA | FACT |
| RAG-13 | Inspector: answer | Citations: claim to source, chunk, version and span to visible marker; membership in selected context | table | Nour | E23 | NA | FACT |
| RAG-14 | Inspector: answer | Structural citation checks: resolves, version matches, locator valid, marker bound; cited-but-not-retrieved; uncited claims | table | Nour | E23, RC | NA | FACT |
| RAG-15 | Inspector: answer | Claim support verdict per claim from the groundedness evaluator | table | Ahmed | RC, HO | NE EF NA | FACT |
| RAG-16 | Inspector: abstention | Abstention: reason (NO_RELEVANT_EVIDENCE, INCOMPLETE_SUPPORT, CONFLICTING_EVIDENCE, INVALID_CITATION_BINDING), missing information, last stage, delivered text | obj | Nour | E24, RC | NA | FACT |
| RAG-17 | Inspector: abstention | Abstention appropriateness evaluator result | enum | Ahmed | E24, FM | NE EF NA | FACT |
| RAG-18 | Source viewer | Source snapshot: immutable text, title, hash, source ID and version | obj | Nour | E05, RC | RD ME | FACT |
| RAG-19 | Inspector: answer | RAG outcome (ANSWER, ABSTENTION, ERROR) with the error stage | enum | Nour | RC, E25 | — | FACT |
| RAG-20 | Inspector: query | Prompt-injection indicators in the query or retrieved sources: source version, location | list | Ahmed | FM | NE EF NA | FACT |

## SCR-REL — Release Gate

Page pattern: Detail with a sticky section navigation. One gate evaluation: a candidate compared with a baseline.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| REL-01 | Decision | Release gate decision PASS, REVIEW or BLOCK (release scope), with gate-policy version and evaluation time | enum | Alaa | OV, FM | PE NC | OPEN |
| REL-02 | Decision | Gate reasons: each triggering metric, regression or completeness condition, linking to its row | list | Alaa | OV | NC | DECISION |
| REL-03 | Decision | Release identities: candidate and baseline labels, IDs, creation times | obj | Alaa | OV | — | FACT |
| REL-04 | Metrics | Metric comparison: metric, baseline value, candidate value, delta, sample size, state | table | Alaa | OV, HO | NE EF NA NC | FACT |
| REL-05 | Metrics | Metric definitions: name, unit, direction, evaluator family | table | Ahmed | E06, HO | — | FACT |
| REL-06 | Metrics | Configured thresholds and tolerances with rationale and version | table | Alaa | OD-15 | NC | OPEN |
| REL-07 | Version changes | Component version differences between baseline and candidate | table | Alaa | E26, OD-13 | UN | FACT |
| REL-08 | Version changes | Evaluation set: dataset or suite version, split, case counts, paired-case grouping | obj | Alaa | FM, HO | — | FACT |
| REL-09 | Regressions | Regressed and improved scenarios: scenario reference, class, direction, links to the paired baseline and candidate traces | list | Alaa | HO, FM | NE | DECISION |
| REL-10 | Regressions | Failure class change from baseline to candidate | table | Alaa | FM | NE EF | DECISION |
| REL-11 | Regressions | Pre-execution enforcement changes per policy rule | table | Mohamed | E18 | NA | DECISION |
| REL-12 | Lineage and completeness | Run completeness: planned, executed and inconclusive cases; missing evidence | obj | Alaa | FM | ME | FACT |
| REL-13 | Lineage and completeness | Experiment lineage: run IDs, code commit, configuration hashes, manifests | list | Alaa | HO, OD-13 | UN | FACT |
| REL-14 | Lineage and completeness | Reproducibility mode: fixed-fixture or live model, with a note that live output is not deterministic | enum | Alaa | FM, HO | — | FACT |
| REL-15 | History | Previous gate evaluations: candidate, baseline, decision, time | list | Alaa | OV | — | DECISION |
| REL-16 | Decision | Release review or override record | list | Mohamed | OV | NC PE | OPEN |

## Notes on shared ownership

- **Versions (`APP-06`, `APP-07`, `RAG-03`, `TRD-80`, `REL-07`).** The applications emit version values at run time. Alaa owns the identifier and hash conventions and the lineage, so Alaa owns these rows.
- **Approvals (`TRD-32`–`TRD-35`).** Nour's tool wrappers submit and observe approvals through the governance boundary. Approval truth stays with Mohamed (`TC` request_approval).
- **Stage mapping (`TRD-23`).** Nour emits the stage snapshot. Mohamed and Mohab still have to ratify the state-to-stage names (D3).
- **Citation checks.** Structural checks (`RAG-14`) are Nour's runtime checks. Semantic support (`RAG-15`) is Ahmed's evaluator. They are separate rows so a structurally valid citation is never shown as supported.
- **Release gate versus reliability decision.** `REL-01` and `TRD-03` use the same three words at different scopes. The presentation rules in the vocabulary keep them apart. Alaa and Mohamed must confirm the split (Q-10).
- **Ground truth (`TRD-65`, `RAG-09`).** Evaluation-side labels never feed classifier or model inputs. Whether reviewers see them, and when, is open (Q-11).
