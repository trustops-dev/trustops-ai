# TrustOps AI — Dashboard UX architecture

Reviewer journeys and seven-screen information architecture · Owner: Malak (dashboard) · Revision 0.1 · 2026-10-17

**Status: draft for owner review. Not signed off.** This package is documentation only. The five backend owners have not yet reviewed or acknowledged the field matrix (see the [owner review record](#owner-review-record)). Nothing here is a canonical schema, API route, routing setup or component.

Task: *Design Reviewer Journeys & Seven-Screen Information Architecture* (Frontend, Critical). Depends on the S1-01 application flows and evidence model. Blocks S2-06. The task ID is not stated in the repository; see A-03.

## Read in order

1. [Reviewer task flows](reviewer-journeys.md): valid procurement, approval bypass, RAG failure, release regression.
2. [Seven-screen information architecture](information-architecture.md): screens, page patterns, navigation, cross-links, low-fidelity wireframes.
3. [Status vocabulary and non-colour encoding](status-vocabulary.md): how PASS, REVIEW, BLOCK, Not evaluated, Evaluator failed and Not applicable are told apart.
4. [Field and data-owner matrix](field-owner-matrix.md): every diagnostic field, each on one screen with one backend owner.
5. [Paper walkthroughs and coverage check](paper-walkthroughs.md): evidence reachability, findings, and the automated consistency check.

## What this answers

| Task scope | Where |
|---|---|
| Four reviewer task flows from Figures 2 to 5 | [reviewer-journeys.md](reviewer-journeys.md) |
| Low-fidelity wireframes and cross-link structure for seven screens | [information-architecture.md](information-architecture.md) |
| PASS, REVIEW, BLOCK, Not evaluated, Evaluator failed, Not applicable, never by colour alone | [status-vocabulary.md](status-vocabulary.md) |
| Field and data-owner matrix | [field-owner-matrix.md](field-owner-matrix.md) |
| Review with Nour, Ahmed, Mohab, Mohamed, Alaa | [Owner review record](#owner-review-record): prepared, not done |
| Coverage check and paper walkthrough | [paper-walkthroughs.md](paper-walkthroughs.md) |

Out of scope, as the task states: frontend code, routing and a component library. Export, authentication and notification features are not specified because no source requires them.

## Source basis

Built from the Week 1 contracts in [reference-applications](../reference-applications/README.md) (revision 0.5, itself a draft), the dashboard scaffold under `apps/dashboard/src/`, and the repository's `ARCHITECTURE.md`. Status words follow the S1-01 vocabulary: **FACT** is required by a cited source, **DECISION** is a proposal for an owner to confirm, **OPEN** depends on an unresolved decision.

## Assumptions and decisions

| ID | Type | Statement | Why it matters |
|---|---|---|---|
| A-01 | ASSUMPTION | The seven screens are Overview, Applications, Trace Explorer, Trace Detail, Failure & RCA, RAG Diagnostics and Release Gate. The proposal section that names them is not in the repository. The list is inferred from the dashboard route and feature folders and from the S1-01 handoffs ("Trace Explorer/Detail", "RAG Diagnostics", "No eighth screen"). | If the proposal names a different set, screens and field homes move. Confirm in Q-01. |
| A-02 | ASSUMPTION | Figures 2 to 5 and user stories US-34 to US-40 are not in the repository. Flows follow what the S1-01 documents say the figures show. | The figures must be checked before sign-off. Q-01. |
| A-03 | ASSUMPTION | The task text says it depends on "S1-04 (evidence model)". In the S1-01 handoffs, S1-04 is Mohamed's policy interaction task and S1-02 is Mohab's canonical trace schema. This package treats the evidence model as the [trace evidence contract](../reference-applications/trace-evidence-contract.md) E01 to E27. The handoffs list Malak's work as S1-06/S1-07. | Dependency traceability. Q-01. |
| A-04 | ASSUMPTION | `apps/api` serves every value shown. The dashboard calls no backend package directly and defines no endpoint here. | Keeps the dashboard a pure renderer. |
| DX-01 | DECISION | One home screen and one owner per field. A screen may show a read-only projection of a field homed elsewhere. Projections are marked in wireframes and are not fields. | Gives the "exactly one screen and one owner" check a precise meaning. |
| DX-02 | DECISION | Applications is a List whose row opens a read-only slide-over. A detail route would be an eighth screen. | Holds the count at seven. |
| DX-03 | DECISION | Every status shows its scope label and has a unique signature. `BLOCK` means three things (reliability, release gate, pre-tool), so the scope label is mandatory and the glyphs differ. | Prevents a prevented action being read as a failed release, and the reverse. |
| DX-04 | DECISION | On narrow viewports, RAG Diagnostics shows the inspector full width on the same route instead of opening Trace Detail. | Avoids duplicating the RAG inspector in a second screen and keeps one home per RAG field. |
| DX-05 | DECISION | Aggregates belong to the owner of the values counted. Mohab owns only trace-level counts such as volume, freshness and completeness. | Avoids one owner for every dashboard number. |
| DX-06 | DECISION | Eight absence states exist: Not evaluated, Evaluator failed, Not applicable, Awaiting result, Unavailable, Missing evidence, Redacted, Not configured. A real zero shows as `0`. | The four named in the task are not enough to keep unknown apart from zero. |
| DX-07 | DECISION | Page patterns: Overview is a Dashboard, Applications and Trace Explorer are Lists, Trace Detail and Release Gate are Details, Failure & RCA is Analytics, RAG Diagnostics is a Split Pane. | One job per screen. |
| DX-08 | DECISION | The execution graph is a secondary view of the ordered event list, which carries the same content in text. | Keeps the screen accessible and testable. |
| DX-09 | DECISION | Human review is shown beside the machine decision history. Whether the dashboard can write review records in the MVP is OPEN. | Q-07. |

## Open questions

| ID | Owner | Question | Rows affected |
|---|---|---|---|
| Q-01 | Malak, plan owner | Confirm the seven screens, Figures 2 to 5, US-34 to US-40 and the task and dependency IDs against the proposal and sprint plan. | All |
| Q-02 | Mohab | How does the canonical schema represent missing, null, not applicable, redacted, unavailable and awaiting values, and where does an evaluation state live in it? The dashboard needs these eight absence states to be distinguishable. | All rows with an absence state |
| Q-03 | Mohab | What node types, edge types and event anchors will the backend-derived execution graph expose, so that rationale and evidence links can point at a single event? | `TRD-20`, `TRD-21`, `TRD-04` |
| Q-04 | Mohab | Will `apps/api` serve the windowed aggregates for Overview, Failure & RCA and Release Gate, computed server side? Who sets the Overview window? | `OVW-01` to `OVW-05`, `RCA-*`, `REL-04` |
| Q-05 | Mohab | Confirm ownership of volume, freshness, ingestion health, completeness, event order, execution graph and redaction markers. | `OVW-01` to `OVW-03`, `APP-04`, `APP-05`, `TRX-01` to `TRX-03`, `TRD-20`, `TRD-21`, `TRD-81`, `TRD-82` |
| Q-06 | Mohamed | What does the decision engine return while a run is waiting, an evaluator failed or an evaluation did not run? Can a trace be PASS in those cases? What form do rationale references take, and can each point at an event? | `TRD-03`, `TRD-04`, `OVW-04` |
| Q-07 | Mohamed | Can the dashboard create human review records in the MVP? Which fields and outcome values? Is there a release-level review or override? | `TRD-70`, `REL-16` |
| Q-08 | Ahmed | Is the evaluation state (value, Not evaluated, Evaluator failed, Not applicable) a first-class result? How is a finding worded versus a metric? Does the classifier expose a score? What reference format ties a cause to events, and how is "no cause supported" returned? | `TRD-60` to `TRD-62`, `RCA-04`, `RCA-08` |
| Q-09 | Ahmed, Mohamed | How are attempted, prevented and realized violations returned once OD-09 is closed? | `RCA-05` |
| Q-10 | Alaa, Mohamed | Confirm the release gate decision is Alaa's field and a separate concept from the trace reliability decision, and how thresholds appear while OD-15 is open. | `REL-01`, `REL-06`, `TRD-03` |
| Q-11 | Alaa, Ahmed | May reviewers see evaluation-side ground truth (injected failure, expected sources)? If so, how is it separated from model and classifier inputs in the UI? | `TRD-65`, `RAG-09` |
| Q-12 | Nour | Confirm the execution-mode values, that a replay has no model call, and how raw and delivered text and source snapshots are exposed. | `TRX-04`, `TRD-13`, `TRD-50`, `RAG-18` |

## Owner review record

Review requests are prepared and **not sent**. This package does not contact anyone. A PR approval does not replace these reviews, and silence is not sign-off. Each owner filters the [matrix](field-owner-matrix.md) by their name, confirms or corrects every row, and answers the listed questions.

| Owner | Review needed | Status | Revision | Evidence |
|---|---|---|---|---|
| Nour | Rows owned by Nour; Q-12 | PENDING | 0.1 | — |
| Ahmed | Rows owned by Ahmed; Q-08, Q-09, Q-11 | PENDING | 0.1 | — |
| Mohab | Rows owned by Mohab; Q-02 to Q-05 | PENDING | 0.1 | — |
| Mohamed | Rows owned by Mohamed; Q-06, Q-07, Q-09, Q-10 | PENDING | 0.1 | — |
| Alaa | Rows owned by Alaa; Q-10, Q-11 | PENDING | 0.1 | — |

Record each acknowledgement with the reviewer, date, revision reviewed, accepted rows and unresolved conditions. The task's report-back criterion (reviewed and acknowledged by all five owners) is **not met** until all five rows above show evidence.

## Checks

`tests/contract/test_dashboard_information_architecture.py` reads these documents and fails when they disagree. It is run by the Python CI workflow with the other contract tests. Locally, from the repository root:

```sh
uv run --locked --all-packages pytest tests/contract/test_dashboard_information_architecture.py
```

It checks that every field has one screen and one valid owner, every one of the 27 trace evidence requirements maps to a field, every wireframe marker resolves and every field is on its home wireframe, every navigation edge is well formed and every screen is within two links of Trace Detail, every state has a distinct signature, and journeys cite only real fields and edges. See [paper-walkthroughs.md](paper-walkthroughs.md).

It cannot judge whether a design is usable, accessible or correct. That needs the owner reviews above, an independent walkthrough, and later a prototype review.
