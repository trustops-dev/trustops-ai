# TrustOps AI — Dashboard UX architecture

User task flows and seven-screen information architecture · Owner: Malak (dashboard) · Revision 0.2 · 2026-10-17

**Status: draft for owner review. Not signed off.** This package is documentation only. The five backend owners have not yet reviewed or acknowledged the field matrix (see the [owner review record](#owner-review-record)). Nothing here is a canonical schema, API route, routing setup or component.

Task: *Design Reviewer Journeys & Seven-Screen Information Architecture* (Frontend, Critical). Depends on the S1-01 application flows and evidence model. Blocks S2-06. The task ID is not stated in the repository; see Q-01.

## Read in order

1. [User task flows](reviewer-journeys.md): valid procurement, approval bypass, RAG failure, release regression.
2. [Seven-screen information architecture](information-architecture.md): screens, page patterns, navigation, cross-links, low-fidelity wireframes.
3. [Roles and access](roles-and-access.md): the seven roles, landing screens, who can do what, and how screens behave for each.
4. [Status vocabulary and non-colour encoding](status-vocabulary.md): how PASS, REVIEW, BLOCK, Not evaluated, Evaluator failed and Not applicable are told apart.
5. [Field and data-owner matrix](field-owner-matrix.md): every diagnostic field, each on one screen with one backend owner.
6. [Story traceability](story-traceability.md): every acceptance criterion of US-34 to US-40 mapped to a design element.
7. [Paper walkthroughs and coverage check](paper-walkthroughs.md): evidence reachability, findings, and the automated consistency check.

## What this answers

| Task scope | Where |
|---|---|
| Four reviewer task flows from Figures 2 to 5 | [reviewer-journeys.md](reviewer-journeys.md) |
| Low-fidelity wireframes and cross-link structure for seven screens | [information-architecture.md](information-architecture.md) |
| PASS, REVIEW, BLOCK, Not evaluated, Evaluator failed, Not applicable, never by colour alone | [status-vocabulary.md](status-vocabulary.md) |
| Field and data-owner matrix | [field-owner-matrix.md](field-owner-matrix.md) |
| Match with the proposal and user stories | [story-traceability.md](story-traceability.md), [roles-and-access.md](roles-and-access.md) |
| Review with Nour, Ahmed, Mohab, Mohamed, Alaa | [Owner review record](#owner-review-record): prepared, not done |
| Coverage check and paper walkthrough | [paper-walkthroughs.md](paper-walkthroughs.md) |

Out of scope, as the task states: frontend code, routing and a component library. Export, authentication screens and account management are not specified because no story requires them on the seven screens.

## Source basis

Built from the TrustOps AI project proposal v1.1 (sections K, M, N, R, S, T and V, Figures 1 to 5), the user stories and acceptance criteria v2.2 (Epic 7 and the stories it depends on, Appendices A and B), the Week 1 contracts in [reference-applications](../reference-applications/README.md) (revision 0.5, itself a draft), the dashboard scaffold under `apps/dashboard/src/`, and `ARCHITECTURE.md`. The proposal and the user stories were supplied as PDFs and are cited by section and story number; they are not stored in this repository. Status words follow the S1-01 vocabulary: **FACT** is required by a cited source, **DECISION** is a proposal for an owner to confirm, **OPEN** depends on an unresolved decision.

## Revision 0.2: changes after checking the proposal and stories

Revision 0.1 inferred the seven screens from the dashboard scaffold. Revision 0.2 matches them to proposal section T and US-34 to US-40.

| Area | Change |
|---|---|
| Screen names and order | Reliability Overview, Applications, Trace Explorer, Trace Detail, RAG Diagnostics, Failure & RCA Investigation, Release Quality Gate, in the proposal's order. |
| Failure & RCA | Was a cross-trace statistics page. Now the per-trace investigation of US-39 (label, classifier score, rule findings, evaluator evidence, Top-3 causes, decision with rule path), as a queue plus investigation. Cross-trace statistics that no story asks for were dropped. |
| Reliability Overview | Now shows all six items of US-34: application cards, trace count, decision distribution, top failure classes, recent gate status, reliability trend. |
| Applications | Now application cards with all four versions, the latest evaluation run and the latest gate decision (US-35). The slide-over was removed. |
| Trace Explorer | The six US-36 filters are all present, including policy/security verdict. Filter state lives in the URL. |
| Trace Detail | Keeps events, graph and evaluator outputs (US-37). Adds policy verdicts, the security verdict, the agent-guard rejection and the layer that stopped a call. The decision and label moved to Failure & RCA and show here as projections. |
| RAG Diagnostics | Expected evidence is visible (US-38). Groundedness and citation precision show name, unit and direction. The failure type is in the inspector header. |
| Release Quality Gate | Metrics by area (RAG, Agent, Security, Overall), critical scenarios, candidate disposition, gate artifact and CI status, release reviews, override requests and approvals, audit history (US-40, US-25 to US-27, US-33). |
| Roles | Added the seven roles, landing screens, Manage and View table, raw versus redacted payloads, and permission behavior. See [roles and access](roles-and-access.md). |
| Human review | Resolved. The verdict is ACCEPT, REVIEW or BLOCK plus a rationale, submitted from Trace Detail or Failure & RCA, append-only (US-25). It has its own scope label. |
| Figures | Flow-to-figure mapping corrected: Figure 2 sequence, Figure 3 execution graph of the bypass, Figure 4 evaluation pipeline, Figure 5 release gate. |
| Rule added | Every score shows meaning, unit and direction, source and version. |

## Assumptions and decisions

| ID | Type | Statement | Why it matters |
|---|---|---|---|
| A-01 | FACT | The seven screens are those of proposal section T and US-34 to US-40. This replaces revision 0.1's inference from the scaffold. | Screens and field homes are settled. |
| A-02 | ASSUMPTION | The Frontend README that the stories cite (sections 3.1, 3.2 and 10, including the shared review checklist) is not in the repository and was not supplied. | It may define wireframes or checks this package should follow. Q-01. |
| A-03 | ASSUMPTION | The task text says it depends on "S1-04 (evidence model)". In the S1-01 handoffs, S1-04 is Mohamed's policy interaction task and S1-02 is Mohab's canonical trace schema. This package treats the evidence model as the [trace evidence contract](../reference-applications/trace-evidence-contract.md) E01 to E27. The handoffs list Malak's work as S1-06/S1-07. | Dependency traceability. Q-01. |
| A-04 | ASSUMPTION | `apps/api` serves every value shown. The dashboard calls no backend package directly and defines no endpoint here. | Keeps the dashboard a pure renderer. |
| DX-01 | DECISION | One home screen and one owner per field. A screen may show a read-only projection of a field homed elsewhere, marked in wireframes. | Gives the "exactly one screen and one owner" check a precise meaning. |
| DX-02 | DECISION | Applications is a List of application cards with a Details disclosure inside each card. No slide-over or detail route. | US-35 asks for cards that hold all four versions in full. |
| DX-03 | DECISION | Every status shows its scope label and has a unique signature. `BLOCK` and `REVIEW` have several meanings (reliability, release gate, pre-tool, human review). Machine states use glyphs; human review verdicts and override states are plain text tags. | A prevented action is never read as a failed release, and a reviewer's verdict is never read as a machine decision. |
| DX-04 | DECISION | On narrow viewports, RAG Diagnostics and Failure & RCA show their inspector or investigation full width on the same route with a Back control. | Avoids a second detail route that would duplicate the inspector. |
| DX-05 | DECISION | Aggregates belong to the owner of the values counted. Mohab owns only trace-level counts such as volume, freshness and completeness. | Avoids one owner for every dashboard number. |
| DX-06 | DECISION | Eight absence states exist: Not evaluated, Evaluator failed, Not applicable, Awaiting result, Unavailable, Missing evidence, Redacted, Not configured. A real zero shows as `0`. | The four named in the task are not enough to keep unknown apart from zero. |
| DX-07 | DECISION | Page patterns: Overview is a Dashboard, Applications and Trace Explorer are Lists, Trace Detail and Release Quality Gate are Details, RAG Diagnostics and Failure & RCA are Split Panes. | One job per screen. |
| DX-08 | DECISION | The execution graph is a view of the ordered event list, which carries the same content in text. The graph itself is derived by the backend (US-12). | Keeps the screen accessible and testable. |
| DX-09 | DECISION | Per-trace diagnosis lives on Failure & RCA. Trace Detail keeps events and evaluator outputs and shows the decision and label as projections. | Matches US-37 and US-39 with one home per field. |
| DX-10 | DECISION | A control the role may not use is shown unavailable with the reason, not hidden. The backend still rejects the action. | Keeps capabilities discoverable and errors explainable. |
| DX-11 | DECISION | No Manage controls are drawn beyond the actions the stories define, until Q-13 is answered. | The stories do not say what Manage covers. |

## Open questions

| ID | Owner | Question | Rows affected |
|---|---|---|---|
| Q-01 | Malak, plan owner | Share the Frontend README (sections 3.1, 3.2, 10 and its review checklist). Confirm the Jira task ID and which task ID is the evidence-model dependency. | All |
| Q-02 | Mohab | How does the canonical schema represent missing, null, not applicable, redacted, unavailable and awaiting values, and where does an evaluation state live? The dashboard needs these eight absence states to be distinguishable. | All rows with an absence state |
| Q-03 | Mohab | What event anchors will deep links use, so that evidence links land on a single event? (Node and edge types are already given by US-12.) | `TRD-20`, `TRD-21`, `RCA-06`, `REL-02` |
| Q-04 | Mohab | Will `apps/api` serve the windowed aggregates and trend buckets for Overview and Release Quality Gate, computed server side? Who sets the Overview window? | `OVW-01` to `OVW-07`, `REL-04` |
| Q-05 | Mohab | Confirm ownership of volume, freshness, ingestion health, completeness, event order, execution graph and redaction markers. | `OVW-01` to `OVW-03`, `APP-04`, `APP-09`, `TRX-01` to `TRX-03`, `TRD-20`, `TRD-21`, `TRD-81`, `TRD-82` |
| Q-06 | Mohamed | What does the decision engine return while a run is waiting, an evaluator failed or an evaluation did not run? Can a trace be PASS in those cases? In what form does the rule path return, and can each item point at an event? | `RCA-07`, `RCA-08`, `OVW-04`, `OVW-06` |
| Q-07 | Mohamed | US-25 lets a review be submitted from Trace Detail, but Appendix B gives the Governance Reviewer only View on Trace Detail. Confirm "submit a review" is an action-level permission. Confirm release reviews use the same record. | `TRD-70`, `REL-16` |
| Q-08 | Ahmed | Is the evaluation state (value, Not evaluated, Evaluator failed, Not applicable) a first-class result? How is a finding worded versus a metric? What reference format ties a cause to events, and how is "no cause supported" returned? How are the three classifier approaches reported for one trace? | `TRD-60` to `TRD-63`, `RCA-01` to `RCA-06` |
| Q-09 | Ahmed, Mohamed | How are attempted, prevented and realized violations returned once OD-09 is closed? | `RCA-09` |
| Q-10 | Alaa, Mohamed | Confirm the release gate decision and candidate disposition are Alaa's fields, a separate concept from the trace reliability decision, and that override requests and audit are Mohamed's. How do thresholds appear while OD-15 is open? | `REL-01`, `REL-06`, `REL-18`, `REL-19` |
| Q-11 | Alaa, Ahmed | May reviewers see the injected failure and root cause (evaluation-side ground truth)? Expected evidence is already shown on RAG Diagnostics as US-38 requires. | `RCA-11` |
| Q-12 | Nour | Confirm the execution-mode values, that a replay has no model call, how raw and delivered text and source snapshots are exposed, and how the agent-guard rejection is emitted as its own event. | `TRX-04`, `TRD-13`, `TRD-44`, `TRD-47`, `TRD-50`, `RAG-18` |
| Q-13 | Mohamed, plan owner | Appendix B gives Manage on several dashboards, and describes actions such as configuring behavior, running evaluations, annotating results and initiating gate evaluations. Which are in the MVP, and what are their fields? | None until answered |
| Q-14 | Mohamed | Confirm the login form and Administrator account and role management are outside the seven screens. | Session context |

## Owner review record

Review requests are prepared and **not sent**. This package does not contact anyone. A PR approval does not replace these reviews, and silence is not sign-off. Each owner filters the [matrix](field-owner-matrix.md) by their name, confirms or corrects every row, and answers the listed questions.

| Owner | Review needed | Status | Revision | Evidence |
|---|---|---|---|---|
| Nour | Rows owned by Nour; Q-12 | PENDING | 0.2 | — |
| Ahmed | Rows owned by Ahmed; Q-08, Q-09, Q-11 | PENDING | 0.2 | — |
| Mohab | Rows owned by Mohab; Q-02 to Q-05 | PENDING | 0.2 | — |
| Mohamed | Rows owned by Mohamed; Q-06, Q-07, Q-09, Q-10, Q-13, Q-14 | PENDING | 0.2 | — |
| Alaa | Rows owned by Alaa; Q-10, Q-11 | PENDING | 0.2 | — |

Record each acknowledgement with the reviewer, date, revision reviewed, accepted rows and unresolved conditions. The task's report-back criterion (reviewed and acknowledged by all five owners) is **not met** until all five rows above show evidence.

## Checks

`tests/contract/test_dashboard_information_architecture.py` reads these documents and fails when they disagree. It is run by the Python CI workflow with the other contract tests. Locally, from the repository root:

```sh
uv run --locked --all-packages pytest tests/contract/test_dashboard_information_architecture.py
```

It checks that the seven screens match proposal section T, every field has one screen and one valid owner, every one of the 27 trace evidence requirements maps to a field, every wireframe marker resolves and every field is on its home wireframe, every navigation edge is well formed and every screen is within two links of Trace Detail, the access table matches Appendix B, every state has a distinct signature, every story US-34 to US-40 is traced, and the other documents cite only real fields and edges. See [paper-walkthroughs.md](paper-walkthroughs.md).

It cannot judge whether a design is usable, accessible or correct. That needs the owner reviews above, an independent walkthrough, and later a prototype review.
