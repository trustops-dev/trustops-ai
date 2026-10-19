# Field and data-owner matrix

Revision 0.3 · 2026-10-19 · DRAFT for owner review. Part of the [dashboard UX architecture](README.md).

Every diagnostic field the seven screens show appears below exactly once. Each row names one **home screen** (the section it sits in) and one **data owner**. Nothing here is a canonical schema, API route or database column; Mohab maps rows to `packages/contracts` under S1-02.

## How to read this matrix

| Term | Meaning |
|---|---|
| **Home screen** | The one screen where the field is defined and shown in full. The ID prefix matches the screen: `OVW` Reliability Overview, `APP` Applications, `TRX` Trace Explorer, `TRD` Trace Detail, `RAG` RAG Diagnostics, `RCA` Failure & RCA Investigation, `REL` Release Quality Gate. |
| **Projection** | A read-only echo of a field on another screen, such as a decision badge in a Trace Explorer row. A projection carries the same value from the same owner and is never a second field. Wireframes mark projections `{>ID}` and home fields `{ID}`. |
| **Data owner** | The backend owner accountable for the value's meaning, correctness and schema evolution. It is not the serving layer. `apps/api` serves every value; the dashboard renders it and never infers, recomputes, re-ranks or overrides a decision, label, cause or score. |
| **Aggregates** | A count or distribution belongs to the owner of the values being counted. Mohab's envelope owns only trace-level counts such as volume, freshness and completeness. |
| **Shape** | `id` identifier · `text` · `enum` · `ts` timestamp · `num` number · `count` counts or distribution · `flag` boolean · `obj` grouped record · `list` · `table` · `ref` link to another record · `ver` immutable version reference · `graph` nodes and edges. |
| **Absence** | Which no-value states can occur: `NE` Not evaluated · `EF` Evaluator failed · `NA` Not applicable · `PE` Awaiting result · `UN` Unavailable · `ME` Missing evidence · `RD` Redacted · `NC` Not configured. A dash means the field always has a value. Definitions are in the [status vocabulary](status-vocabulary.md). |
| **Basis** | `FACT`: required by the cited source. `DECISION`: UX proposal that the owner must confirm or reject. `OPEN`: depends on an open decision or [question](README.md#open-questions). Same words as the [S1-01 status vocabulary](../reference-applications/README.md#status-vocabulary). |
| **Source** | `PR §x` the project proposal v1.1. `US-nn` the user stories v2.2. `FR-nn` proposal functional requirements. `E01`–`E27` rows of the [trace evidence contract](../reference-applications/trace-evidence-contract.md). `SC` [state contract](../reference-applications/procurement-state-contract.md). `TC` [tool contracts](../reference-applications/procurement-tool-contracts.md). `RC` [RAG contract](../reference-applications/rag-contract.md). `FM` [failure matrix](../reference-applications/failure-planning-matrix.md). `OV` [overview](../reference-applications/overview.md). `HO` [handoffs](../reference-applications/handoffs.md). `OD-nn` [open decisions](../reference-applications/open-decisions.md). `GC` the [governance contract register](../governance/governance-contract.md) (Mohamed, draft v0.2). `DF` the [governance decision flow](../governance/decision-flow.md). `TS` the Trace Schema v1 draft (Mohab, draft v1.0, section number given), in `docs/architecture/schemas`. |

The five owners: **Nour** (reference applications and scenarios), **Ahmed** (evaluators, classifier, RCA), **Mohab** (trace envelope, ordering, ingestion, execution graph), **Mohamed** (policy, approvals, reliability decisions, human review, audit, roles), **Alaa** (versions, datasets, experiments, release gate). Malak owns the dashboard and is not a data owner. These match proposal section V.

### Rules every row follows

1. A field has one home and one owner. If two owners contribute, the row names the accountable one and the notes below say what the other supplies.
2. The dashboard never shows a missing value as zero, blank or PASS. It shows one of the absence states.
3. Reliability decision, release gate decision, pre-tool verdict, application outcome and human review verdict are separate fields with separate presentation. See [status vocabulary](status-vocabulary.md).
4. Every score, status badge and finding shows its meaning, its unit and direction, its provenance and its applicable version (Epic 7 Definition of Done). The shapes below describe the value; the version and provenance travel with it.
5. Fields tagged `OPEN` render as `Not configured` or `Awaiting result` until their owner closes the decision. The UI invents no value, threshold or default.
6. Where the S1-01 contracts, the governance contract and Trace Schema v1 name the same value differently (workflow stages, run and execution status, approval status, abstention reasons, per-policy status), the row does not fix an enumeration. The dashboard renders the canonical enumeration once the owners agree one (Q-15). Row text names the concept, not one draft's spelling.

### UI-local state (no backend owner)

These are not diagnostic fields. They live in the browser or URL and have no data owner: sort order, column visibility, page size and page number, expanded or collapsed sections, selected tab or section, search text, applied filter chips, selected time range, selected baseline/candidate pair, graph zoom and pan, theme. The *values* offered by a filter always come from the field it filters. Filter and pagination state is carried in the URL (US-36).

### Session context (outside the seven screens)

The signed-in user's name, their role, and which actions that role may take come from the role service that Mohamed owns (US-27). They appear in the application shell on every screen, and the login form is not one of the seven screens. See [roles and access](roles-and-access.md).

## SCR-OVW — Reliability Overview

Page pattern: Dashboard. Fixed glance, at most five tiles, read-only. Each tile and card links out.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| OVW-01 | Header | Reporting window: label, start and end of the period every figure covers | obj | Mohab | PR §T, US-34 | UN | DECISION |
| OVW-02 | Tile: traces | Trace count in the window, total and by application | count | Mohab | US-34, E01 | UN | FACT |
| OVW-03 | Header | Data freshness: time of the latest ingested trace, ingest lag | ts | Mohab | E25 | UN | DECISION |
| OVW-04 | Tile: decisions | Reliability decision distribution, overall and by application: PASS, REVIEW, BLOCK and "no decision yet" as separate numbers | count | Mohamed | US-34, US-24 | PE | FACT |
| OVW-05 | Tile: evaluation | Evaluation coverage: counts of evaluated, Not evaluated, Evaluator failed and Not applicable | count | Ahmed | US-18, US-15 | NE EF NA | FACT |
| OVW-06 | Chart | Reliability trend: decision distribution over successive periods | count | Mohamed | US-34, PR §T | PE | FACT |
| OVW-07 | Tile: failure classes | Top failure classes: class and count, overall and by application | count | Ahmed | US-34, PR §K | NE EF | FACT |

The fifth tile is the most recent release gate decision, a projection of `REL-01`. The application cards project `APP-01`, `APP-03` and the decision and trace figures for each application.

## SCR-APP — Applications

Page pattern: List, with each record shown as a full-width application card (US-35 asks for cards). A card needs room for all four version identifiers without truncating the differentiating suffix, which a table column would cut.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| APP-01 | Card | Application identity: ID, display name, kind (Procurement Agent or Enterprise RAG Assistant) | obj | Nour | US-35, E01, E26 | — | FACT |
| APP-02 | Card | Synthetic-data and mock-tool marker | flag | Nour | E01, E20 | — | FACT |
| APP-03 | Card | Run-status mix: counts of ACTIVE, WAITING_APPROVAL, RECOVERY_PENDING, BLOCKED, FAILED, CANCELLED, SUCCEEDED | count | Nour | SC | — | FACT |
| APP-04 | Card | Last trace received | ts | Mohab | E25 | UN | DECISION |
| APP-05 | Card | Current version identifiers, all four shown in full: application, model, prompt, retriever | ver | Alaa | US-35, US-09, FR-01 | UN | FACT |
| APP-06 | Card details | Other deployed versions: policy knowledge base, tool schema, SDK, corpus and index, policy set, scenario and configuration | ver | Alaa | E26, OD-13, TS §4.6 | UN | FACT |
| APP-07 | Card details | Provider and configured model identifier, and returned model version when known | obj | Alaa | E26, OD-LLM-01 | UN | FACT |
| APP-08 | Card | Latest evaluation run: run ID, time, dataset version, evaluator suite, policy bundle, classifier, RCA configuration and decision engine versions, status | obj | Alaa | US-35, US-18, TS §4.6 | NE EF PE | FACT |
| APP-09 | Card details | Ingestion health: events received, events rejected, incomplete traces | count | Mohab | E25, OV, US-11 | UN | FACT |
| APP-10 | Card details | Policy applicability: which policy rules apply to this application; procurement rules are Not applicable to the RAG assistant | table | Mohamed | OD-16, SC | NA | FACT |

The most recent gate decision on each card projects `REL-01` and links to its Release Quality Gate record.

## SCR-TRX — Trace Explorer

Page pattern: List. Row columns are mostly projections of fields homed elsewhere; only list-identity fields are homed here.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| TRX-01 | Table | Trace identifier | id | Mohab | US-36, E01, E25 | — | FACT |
| TRX-02 | Table | Trace date and time, and total latency | ts | Mohab | US-36, E01, E25, TS §3.1 | UN | FACT |
| TRX-03 | Table | Event count and trace completeness: complete, incomplete or inconclusive | enum | Mohab | E25, FM | ME | FACT |
| TRX-04 | Table | Execution mode and scope: live model, synthetic output replay, synthetic proposal replay, boundary fixture; full-application or boundary scope | enum | Nour | FM, E27 | NA | FACT |
| TRX-05 | Table | Scenario run reference (opaque) and linked control-pair reference | ref | Alaa | E27, FM, TS §3.1 | NA | FACT |
| TRX-06 | Table | Execution environment: dev, dataset generation, CI gate or demo | enum | Mohab | TS §3.1 | — | FACT |

The six filters US-36 requires are application (`APP-01`), version (`APP-05`), date (`TRX-02`), failure label (`RCA-01`), policy/security verdict (`TRD-62`, `TRD-63`) and reliability decision (`RCA-07`).

## SCR-TRD — Trace Detail

Page pattern: Detail with a sticky section navigation (nine sections). One trace; the place to verify events and evidence.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| TRD-01 | Summary | Application outcome: what the application finally did (for example PO created, waiting for approval, blocked, failed, recovery pending, answer, abstention, error) and the response mode | enum | Nour | E21, E24, E25, TS §4.5 | — | OPEN |
| TRD-02 | Summary | Run status: the operational state of the run (S1-01 lists seven; Schema v1 lists four execution statuses) | enum | Nour | SC, TS §3.1 | — | OPEN |
| TRD-10 | Request and model | Raw request and normalized request: item, quantity, amount, currency, supplier, requester, purpose; raw-to-normalized links | obj | Nour | E01, E08, TC | UN | FACT |
| TRD-11 | Request and model | Request revision and lineage to prior attempts | list | Nour | E08, SC | — | FACT |
| TRD-12 | Request and model | Normalization and validation details, including clarification outcomes | list | Nour | E08 | NA | FACT |
| TRD-13 | Request and model | Model call: step purpose (intent parsing, tool selection, answer generation, final response), prompt or template version, rendered input reference, generation parameters, response, refusal or error | obj | Nour | E02, US-10, TS §4.5 | UN NA | FACT |
| TRD-14 | Request and model | Model call telemetry: latency, token usage, returned model identifier and version | obj | Nour | E02, US-37 | UN NA | FACT |
| TRD-20 | Timeline | Ordered event timeline: event type (retrieval, model_call, agent_state, approval, tool_proposal, policy_check, tool_call, tool_result, final_response, error), sequence number, timestamp, latency, parent link | list | Mohab | US-37, PR §J, TS §3.2 | ME | FACT |
| TRD-21 | Timeline | Execution graph derived by the backend: nodes (request, retrieval, model call, agent state, approval, tool proposal or result, final response) and edges (order, parent, policy requirement, blocked action, unsupported completion) | graph | Mohab | US-12, PR §M.3 | ME | FACT |
| TRD-22 | Timeline | State transitions: previous and new stage, reason, attempted versus accepted, state revision | list | Nour | US-02, E09, TS §4.1 | — | OPEN |
| TRD-23 | Timeline | Workflow stage at each boundary, with the state-to-stage mapping version | list | Nour | US-02, E10, SC, GC §2.1 | NA | OPEN |
| TRD-30 | Procurement evidence | Policy retrieval: raw and effective query, filters, k, ranked policy matches, policy-set and retriever versions, applicability | obj | Nour | E03, TC | NA ME | FACT |
| TRD-31 | Procurement evidence | Supplier check: requested and returned supplier ID, raw and normalized status, directory and record version, lookup outcome | obj | Nour | E11, TC | NA ME | FACT |
| TRD-32 | Procurement evidence | Approval calculation: amount, currency, rule basis, threshold, comparator, policy version, required level or unresolved reason | obj | Mohamed | E12, TC | NA | FACT |
| TRD-33 | Procurement evidence | Approval submission: request ID, approval-request ID, required level, idempotency identity | obj | Mohamed | E13, TC | NA | FACT |
| TRD-34 | Procurement evidence | Approval observation: required and received flags, status, approval ID, actor, time, source | obj | Mohamed | E14, TC | NA PE | FACT |
| TRD-35 | Procurement evidence | Approval binding checks (request revision, supplier, amount, currency, level, version) and authorization basis, including NOT_REQUIRED | list | Mohamed | E14, SC | NA | FACT |
| TRD-40 | Tools and enforcement | Tool proposal: tool name, catalog version, proposal ID, originating model-call reference | obj | Nour | E15, US-01 | — | FACT |
| TRD-41 | Tools and enforcement | Tool arguments: raw serialized, parsed values, trusted runtime context kept separate, validation outcome with field errors | obj | Nour | E16, US-01 | — | FACT |
| TRD-42 | Tools and enforcement | Pre-execution policy request: proposal reference, argument digest, state revision, stage, evidence references, policy version | obj | Mohamed | E17, US-22 | NA ME | FACT |
| TRD-43 | Tools and enforcement | Pre-execution verdict ALLOW or BLOCK with its basis (all policies satisfied, policy violation, or evaluation error), whether it came from the real policy engine or the contract stub, per-policy results (PROC-APPROVAL-01, PROC-TOOL-STAGE-01, PROC-SUPPLIER-01) each with status, criticality, reason and observed versus expected evidence, and the policy-set version; timeout, error or missing verdict | obj | Mohamed | E18, US-22, GC §4.2, TS §4.3 | NA ME | FACT |
| TRD-44 | Tools and enforcement | Dispatch suppression: NOT_EXECUTED, execution_started false, which layer stopped it (agent guard, pre-tool policy, or a missing verdict), blocking reference, reason | obj | Nour | E19, US-03, US-22, GC §5.1 | NA | FACT |
| TRD-45 | Tools and enforcement | Tool invocation and result: invocation ID, start and end, mock marker, idempotency key, outcome (CREATED, ALREADY_EXISTS, UNKNOWN_OUTCOME, ERROR), whether a side effect was committed (yes or no), PO ID only if confirmed. If the canonical schema also emits a result event for a blocked call, it shows here as blocked with no side effect | obj | Nour | E20, TC, TS §4.2 | NA ME | OPEN |
| TRD-46 | Tools and enforcement | Recovery: RECOVERY_PENDING, read-only ledger lookup outcome, links to the original proposal, key, dispatch and result | obj | Nour | E25, SC | NA PE | FACT |
| TRD-47 | Tools and enforcement | Agent-guard rejection: the rejected tool call, the workflow stage that forbade it, reason, recorded as its own event | obj | Nour | US-03 | NA | FACT |
| TRD-50 | Response | Final response (procurement): raw generated text, delivered text, which was shown, the structured claimed actions beside whether a side effect was committed, supporting result references or the reason no action occurred | obj | Nour | E21, TS §4.5 | NA | FACT |
| TRD-51 | Response | Technical failure, cancellation or pending detail: stage, known or unknown outcome, error category, retry and continuation references | obj | Nour | E25 | NA | FACT |
| TRD-60 | Evaluator outputs | Evaluator results: evaluator name, family and version; result state (value, Not evaluated, Evaluator failed, Not applicable); value or finding with metric name, unit and direction; evidence references | table | Ahmed | US-37, US-18, PR §K.1 | NE EF NA | FACT |
| TRD-61 | Evaluator outputs | Evaluator failure detail: error category, evaluator run ID, time | obj | Ahmed | US-18 | EF | DECISION |
| TRD-62 | Evaluator outputs | Policy results (post-run): per policy PROC-APPROVAL-01, PROC-TOOL-STAGE-01, PROC-SUPPLIER-01, status (pass, fail, not applicable, or error where compliance could not be decided), criticality, reason, supporting evidence | table | Mohamed | US-21, PR §R, GC §2.3, DF §5 | NA ME | FACT |
| TRD-63 | Evaluator outputs | Security verdict: attack score or verdict, attack category (direct, indirect, malicious tool use, policy bypass), semantic detector score, location of the attack text | obj | Ahmed | US-17a, PR §Q | NE EF NA | FACT |
| TRD-70 | Review and audit | Human review history: verdict ACCEPT, REVIEW or BLOCK, written rationale (required), reviewer, role, time, and which machine decision and decision version the reviewer was looking at; entries are never edited, corrections are new entries | list | Mohamed | US-25, FR-13, GC §7.1, DF INV-4 | NA PE | FACT |
| TRD-71 | Review and audit | Audit trail for this trace: policy check, approval, decision and review entries with action name, actor, role, time and the version in force, and the administrator-action flag | list | Mohamed | US-26, FR-18, GC §7.2 | — | FACT |
| TRD-80 | Provenance and completeness | Version snapshot for the run (application, prompt, model, retriever, policy knowledge base, tool schema, SDK, corpus/index, scenario/config) and per-call exceptions | ver | Alaa | E26, OD-13, US-37, TS §4.6 | UN ME | FACT |
| TRD-81 | Provenance and completeness | Redaction and unavailability markers: which field, which reason | list | Mohab | E25, US-11 | RD UN | FACT |
| TRD-82 | Provenance and completeness | Missing or inconclusive evidence: expected events that did not arrive | list | Mohab | E25, FM | ME | FACT |
| TRD-83 | Provenance and completeness | Payload visibility for the current role: raw for the Administrator, redacted for every other role | enum | Mohamed | US-27 | RD | FACT |

## SCR-RAG — RAG Diagnostics

Page pattern: Split Pane. A compact query list on the left, the query inspector on the right. Left-list rows are projections of `RAG-01`, `RAG-19` and `RCA-01`.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| RAG-01 | Inspector: query | Query ID, raw query, effective query, transformation provenance | obj | Nour | US-38, E04, RC | UN | FACT |
| RAG-02 | Inspector: query | Retrieval settings: k and filters | obj | Nour | E04, RC | UN | FACT |
| RAG-03 | Inspector: query | Retriever, corpus, index and embedding version identifiers | ver | Alaa | E04, E26, OD-13 | UN | FACT |
| RAG-04 | Inspector: retrieval | Retrieval outcome (success, including empty; or error) and returned count | enum | Nour | RC, US-07 | — | FACT |
| RAG-05 | Inspector: retrieval | Retrieved documents in returned order: document, source and chunk IDs, versions, snapshot text, content hash, locator | table | Nour | US-38, E05 | ME | FACT |
| RAG-06 | Inspector: retrieval | Scores and ranks: raw score, metric kind, direction, one-based rank, tie rule | table | Nour | US-38, E06 | UN | FACT |
| RAG-07 | Inspector: context | Selected context: selected IDs, order and spans; rejected IDs with reasons; selection version | table | Nour | E07 | NA | FACT |
| RAG-08 | Inspector: context | Sufficiency outcome and unresolved facets or conflicts | obj | Nour | E07, RC | NA | FACT |
| RAG-09 | Inspector: context | Expected evidence (evaluation-side reference) compared with what was retrieved | table | Ahmed | US-38, FM, US-15 | NE NA | FACT |
| RAG-10 | Inspector: retrieval | Retrieval metrics for the query: Recall@k and MRR (NDCG only where graded relevance exists), each with name, unit, direction and evaluator version | num | Ahmed | US-15, PR §K.1 | NE EF NA | FACT |
| RAG-11 | Inspector: answer | Candidate answer and delivered answer text, with the delivery flag | obj | Nour | E22 | NA | FACT |
| RAG-12 | Inspector: answer | Claims: claim ID, text, answer span | table | Nour | E22 | NA | FACT |
| RAG-13 | Inspector: answer | Citations: claim to source, chunk, version and span to visible marker; membership in selected context | table | Nour | US-06, E23 | NA | FACT |
| RAG-14 | Inspector: answer | Structural citation checks: resolves, version matches, locator valid, marker bound; cited-but-not-retrieved; uncited claims | table | Nour | E23, RC | NA | FACT |
| RAG-15 | Inspector: answer | Unsupported claims: per-claim support verdict from the groundedness evaluator, and which claims are unsupported | table | Ahmed | US-38, RC | NE EF NA | FACT |
| RAG-16 | Inspector: abstention | Abstention: reason code, missing information, last stage, delivered text | obj | Nour | E24, RC, TS §4.5 | NA | OPEN |
| RAG-17 | Inspector: abstention | Abstention appropriateness evaluator result | enum | Ahmed | E24, FM | NE EF NA | FACT |
| RAG-18 | Source viewer | Source snapshot: immutable text, title, hash, source ID and version | obj | Nour | E05, RC | RD ME | FACT |
| RAG-19 | Inspector: answer | RAG outcome (ANSWER, ABSTENTION, ERROR) with the error stage | enum | Nour | RC, E25 | — | FACT |
| RAG-20 | Inspector: query | Prompt-injection indicators in the query or retrieved sources: source version, location | list | Ahmed | FM, US-17a | NE EF NA | FACT |
| RAG-21 | Inspector: answer | Groundedness and citation precision for the answer, each with metric name, unit, direction and evaluator version | num | Ahmed | US-38, US-15 | NE EF NA | FACT |

## SCR-RCA — Failure & RCA Investigation

Page pattern: Split Pane. A queue of traces that need investigation on the left (failed, REVIEW, BLOCK, not yet decided), the investigation of the selected trace on the right. It works as the landing page for the Reliability Engineer and the Governance Reviewer (Appendix B).

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| RCA-01 | Diagnosis | Primary failure label (one of eight classes, or NORMAL) and the approach that produced it (rules, Logistic Regression or XGBoost) with its classifier version | enum | Ahmed | US-39, US-19, FR-08, TS §4.6 | NE EF | FACT |
| RCA-02 | Diagnosis | Classifier score or confidence indicator per ML approach; the rule baseline has none | num | Ahmed | US-39, US-19 | NE EF NA | FACT |
| RCA-03 | Diagnosis | Secondary findings, retained next to the primary label and never dropped | list | Ahmed | FM, PR §K | NE EF | FACT |
| RCA-04 | Diagnosis | Rule-based findings: which deterministic baseline rules fired, with evidence | list | Ahmed | US-39, PR §K | NE EF | FACT |
| RCA-05 | Causes | Top-3 root-cause candidates in the order the RCA engine returned them, each with its evidence score (not a probability) and the RCA configuration version; a trace with no supported cause shows that | list | Ahmed | US-39, US-20, PR §M.1, TS §4.6 | NE EF | FACT |
| RCA-06 | Causes | Supporting evidence for each cause and each evaluator finding: evaluator, version, and a link to the specific event in Trace Detail | list | Ahmed | US-39, US-20 | NE EF | FACT |
| RCA-07 | Decision | Reliability decision PASS, REVIEW or BLOCK, with decision time, decision engine version and decision configuration version. When evaluation is incomplete there is no decision: the screen shows the evaluation status and the list of missing evidence instead | enum | Mohamed | US-39, US-24, FR-12, GC §6.2, DF §5.2 | PE | FACT |
| RCA-08 | Decision | Decision rule path: every rule that fired, in order, with its reason code and the evaluator signals and evidence-run references behind it, each linked to its evidence; rules not evaluated because a threshold is not configured are listed as such | list | Mohamed | US-39, US-24, PR §K.2, GC §3.4, DF §3 | PE NC | FACT |
| RCA-09 | Diagnosis | Attempted, prevented and realized violation classification | enum | Ahmed | OD-09, FM | NE | OPEN |
| RCA-10 | Diagnosis | Human-reviewed (adjudicated) label | enum | Ahmed | PR §O.3, FM, US-31 | PE | FACT |
| RCA-12 | Diagnosis | Evaluation run history: each versioned re-evaluation and each decision record, kept beside the original | list | Ahmed | E25, FM, DF INV-6 | — | FACT |

The review action and the review history on this screen project `TRD-70` (US-25 allows submitting from here). Evaluator evidence projects `TRD-60`.

## SCR-REL — Release Quality Gate

Page pattern: Detail with a sticky section navigation. One gate evaluation: a candidate compared with the approved baseline on the same versioned dataset.

| ID | Region | Field | Shape | Data owner | Source | Absence | Basis |
|---|---|---|---|---|---|---|---|
| REL-01 | Decision | Release gate decision PASS, REVIEW or BLOCK (release scope), with decision engine version and evaluation time. It is the Layer 2 decision for a release evaluation | enum | Mohamed | US-40, PR §S, DF §2.4 | PE NC | FACT |
| REL-02 | Decision | Gate reasons: every rule that fired, with the metric, regression, critical failure or completeness condition behind it, linking to its row | list | Mohamed | US-40, PR §S.3, DF §3 | NC | DECISION |
| REL-03 | Decision | Release identities: candidate and baseline labels, IDs, creation times | obj | Alaa | US-40, US-32 | — | FACT |
| REL-04 | Metrics | Metric comparison by area (RAG, Agent, Security, Overall reliability): metric, baseline value, candidate value, delta, sample size, state | table | Alaa | US-40, US-32, PR §S.2 | NE EF NA NC | FACT |
| REL-05 | Metrics | Metric definitions: name, unit, direction, evaluator family | table | Ahmed | US-40, PR §K.1 | — | FACT |
| REL-06 | Metrics | Configured thresholds and tolerances with rationale and version | table | Alaa | OD-15, PR §S.3 | NC | OPEN |
| REL-07 | Version changes | Component version differences between baseline and candidate | table | Alaa | US-40, E26, OD-13 | UN | FACT |
| REL-08 | Version changes | Evaluation set: dataset or suite version, split, case counts, paired-case grouping | obj | Alaa | US-13, US-32, FM | — | FACT |
| REL-09 | Critical scenarios | Regressed and improved scenarios: scenario reference, class, direction, links to the paired baseline and candidate traces | list | Alaa | US-40, US-32 | NE | FACT |
| REL-10 | Critical scenarios | Failure class change from baseline to candidate | table | Alaa | FM, PR §S.2 | NE EF | DECISION |
| REL-11 | Critical scenarios | Critical policy and security failures the candidate introduces, including a seeded unsafe action the baseline prevented: scenario, policy ID, criticality | list | Mohamed | US-40, US-32, PR §S.3 | NA ME | FACT |
| REL-12 | Lineage and completeness | Run completeness: planned, executed and inconclusive cases; missing evidence | obj | Alaa | FM | ME | FACT |
| REL-13 | Lineage and completeness | Experiment lineage: run IDs, code commit, configuration hashes, manifests | list | Alaa | HO, OD-13, US-13 | UN | FACT |
| REL-14 | Lineage and completeness | Reproducibility mode: fixed-fixture or live model, with a note that live output is not deterministic | enum | Alaa | FM, HO | — | FACT |
| REL-15 | History | Previous gate evaluations: candidate, baseline, decision, time | list | Alaa | PR §S | — | DECISION |
| REL-16 | Release review | Human review verdicts attached to this release evaluation: ACCEPT, REVIEW or BLOCK, rationale, reviewer, role, time | list | Mohamed | US-25, FR-13 | NA PE | FACT |
| REL-17 | Decision | Gate artifact reference (JSON or Markdown), the evaluation run it came from and CI job status; the screen's figures are those of this artifact | ref | Alaa | US-40, US-33, TS §4.6 | UN ME | FACT |
| REL-18 | Decision | Candidate disposition: BLOCK retains the approved baseline, REVIEW requires human action, PASS leaves the candidate approvable | enum | Alaa | US-40, PR §S | PE NC | FACT |
| REL-19 | Override and audit | BLOCK override requests and approvals: requester and role, written reason, approver and role, outcome, times; administrator use is flagged | list | Mohamed | US-27, US-26 | NA PE | FACT |
| REL-20 | Override and audit | Audit history for this release evaluation: policy, gate, review and override entries with action name, actor, role, time and the version in force | list | Mohamed | US-26, FR-18, GC §7.2 | — | FACT |
| REL-21 | Critical scenarios | Scenario ground truth for the regressed scenarios, evaluation-side only: injected failure, injected root cause, expected critical policy result. Hidden from normal inference views | obj | Alaa | TS §3.1, TS §5, FM | NA RD | OPEN |

## Notes on shared ownership

- **Versions (`APP-05`, `APP-06`, `APP-07`, `RAG-03`, `TRD-80`, `REL-07`).** The applications emit version values at run time. Alaa owns the identifier and hash conventions and the lineage, so Alaa owns these rows.
- **Approvals (`TRD-32`–`TRD-35`).** Nour's tool wrappers submit and observe approvals through the governance boundary. Approval truth stays with Mohamed (`TC` request_approval).
- **Two enforcement layers (`TRD-44`, `TRD-47`).** The agent guard (US-03) is Nour's and the pre-tool policy check (US-22) is Mohamed's. Both can stop a tool; the row shows which one did. A missing verdict also stops the call (GC §5.1) and is shown as a technical check error, not a policy result.
- **Enumerations that differ between drafts (Q-15).** The stage names (S1-01 state contract, governance contract, Schema v1 nine-stage list), the run status versus Schema v1 `execution_status`, approval statuses, abstention reasons, per-policy status (pass, fail, not applicable, error versus a pass boolean), the pre-tool verdict (ALLOW or BLOCK with a basis versus ERROR_BLOCK), and whether a blocked call emits a result event all differ today. The rows marked `OPEN` above depend on them.
- **Stage mapping (`TRD-23`).** Nour emits the stage snapshot. Mohamed and Mohab still have to ratify the state-to-stage names (D3).
- **Citation checks.** Structural checks (`RAG-14`) are Nour's runtime checks. Support and groundedness (`RAG-15`, `RAG-21`) are Ahmed's evaluators. They are separate rows so a structurally valid citation is never shown as supported.
- **Release gate versus reliability decision.** The governance decision flow (§2.4) runs one decision engine for both a trace and a release evaluation, so Mohamed owns `REL-01` and `REL-02`. Alaa owns the comparison, the artifact and what happens to the candidate (`REL-04`, `REL-17`, `REL-18`). `REL-01` and `RCA-07` use the same three words at different targets, so the presentation rules in the vocabulary keep them apart (Q-10).
- **Ground truth (`REL-21`).** Evaluation-side labels never feed classifier or model inputs. Trace Schema v1 §5 puts them in the benchmark and regression diagnostic panels of the Release Quality Gate screen, hidden from normal inference views, so they are homed there. Expected evidence (`RAG-09`) is shown on RAG Diagnostics as US-38 requires. Who may see the injected labels is open (Q-11).
- **Reviews, overrides and audit (`TRD-70`, `TRD-71`, `REL-16`, `REL-19`, `REL-20`).** Mohamed owns the review workflow, the append-only audit records and role checks (proposal section V). Alaa's gate produces the decision that an override acts on.
