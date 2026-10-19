# TrustOps AI — Dashboard UX architecture

User task flows and seven-screen information architecture · Owner: Malak (dashboard) · Revision 0.3 · 2026-10-19

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

Built from the TrustOps AI project proposal v1.1 (sections K, M, N, R, S, T and V, Figures 1 to 5), the user stories and acceptance criteria v2.2 (Epic 7 and the stories it depends on, Appendices A and B), the Week 1 contracts in [reference-applications](../reference-applications/README.md) (revision 0.5), Mohamed's [governance contract register](../governance/governance-contract.md) and [decision flow](../governance/decision-flow.md) (draft v0.2), Mohab's Trace Schema v1 draft (draft v1.0, in `docs/architecture/schemas`), the dashboard scaffold under `apps/dashboard/src/`, and `ARCHITECTURE.md`. All the Week 1 contracts and both new drafts are unfrozen and unsigned. The proposal and the user stories were supplied as PDFs and are cited by section and story number; they are not stored in this repository. Status words follow the S1-01 vocabulary: **FACT** is required by a cited source, **DECISION** is a proposal for an owner to confirm, **OPEN** depends on an unresolved decision.

## Revision 0.3: alignment with the new work on `dev` (2026-10-19)

Two drafts reached `dev` after revision 0.2: Mohamed's governance contract and decision flow, and Mohab's Trace Schema v1. This revision merges `dev` and aligns the matrix with them. Where they agree with each other and with the stories, the package follows them. Where they disagree, the affected rows are marked `OPEN` and Q-15 asks the owners to settle it.

| Area | Change |
|---|---|
| Release gate owner | The governance decision flow (§2.4) runs one decision engine for a trace and a release evaluation, so `REL-01` and `REL-02` belong to Mohamed. Alaa keeps the comparison, the artifact and the candidate disposition. |
| Decision rule path and incomplete evaluations | `RCA-07` and `RCA-08` now follow the governance output: no decision while evaluation is incomplete (shown as status plus missing evidence), fired rules with reason codes and evidence references, rules not evaluated for a missing threshold. |
| Policy results | `TRD-43` and `TRD-62` now carry status (pass, fail, not applicable, error), criticality, reason code, observed versus expected evidence, the verdict basis and whether the real engine or the contract stub answered. |
| Trace events | `TRD-20` lists the ten Schema v1 event types and the sequence number. `TRD-45` and `TRD-50` show whether a side effect was committed against the claimed actions. `TRX-06` shows the execution environment. |
| Versions | `APP-06`, `APP-08` and `TRD-80` list the Schema v1 version keys (policy knowledge base, tool schema, SDK, evaluator suite, policy bundle, classifier, RCA configuration, decision engine). |
| Ground truth | Moved to `REL-21` on Release Quality Gate, where Schema v1 §5 shows it. |
| Human review | `TRD-70` records which machine decision and decision version the reviewer saw, and that a rationale is required. |
| Roles | Cross-check added to [roles and access](roles-and-access.md): the new drafts use three prototype roles, the stories use seven. |
| Open enumerations | Stage names, run and execution status, approval status, abstention reasons, per-policy status and the blocked-call result event differ between drafts. Rows that depend on them are `OPEN` (Q-15). |

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
| A-05 | ASSUMPTION | The governance contract and Trace Schema v1 are drafts. This package follows them where they agree and flags where they do not. It does not choose between conflicting drafts on the owners' behalf. | Avoids baking one draft's spelling into the matrix. Q-15. |
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
| DX-12 | DECISION | Per-policy results are plain text tags under the scope label "Policy", with no glyph. A policy Pass is never drawn like a Reliability Pass, and a Check error is neither a Fail nor a Pass. | The governance contract warns that the policy `PASS` is not a decision `PASS`. |
| DX-13 | DECISION | Procurement approval is labeled "Purchase approval" and a BLOCK override approval is labeled "Override approval". | The word means two different things in the stories and the governance contract. |

## Open questions

| ID | Owner | Question | Rows affected |
|---|---|---|---|
| Q-01 | Malak, plan owner | Share the Frontend README (sections 3.1, 3.2, 10 and its review checklist). Confirm the Jira task ID and which task ID is the evidence-model dependency. | All |
| Q-02 | Mohab | How does the canonical schema represent missing, null, not applicable, redacted, unavailable and awaiting values, and where does an evaluation state live? The dashboard needs these eight absence states to be distinguishable. | All rows with an absence state |
| Q-03 | Mohab | Schema v1 gives every event a trace-scoped event ID and a sequence number. Confirm they are the anchors for deep links, so an evidence link lands on a single event. (Node and edge types are given by US-12.) | `TRD-20`, `TRD-21`, `RCA-06`, `REL-02` |
| Q-04 | Mohab | Will `apps/api` serve the windowed aggregates and trend buckets for Overview and Release Quality Gate, computed server side? Who sets the Overview window? | `OVW-01` to `OVW-07`, `REL-04` |
| Q-05 | Mohab | Confirm ownership of volume, freshness, ingestion health, completeness, event order, execution graph and redaction markers. | `OVW-01` to `OVW-03`, `APP-04`, `APP-09`, `TRX-01` to `TRX-03`, `TRD-20`, `TRD-21`, `TRD-81`, `TRD-82` |
| Q-06 | Mohamed; Malak and Alaa | The governance contract says an incomplete evaluation has no decision and is never PASS (§6.2, decision flow §5.2), and that the rule path lists fired rules with evidence references. Confirm a reference can point at a single event. GD-13 (how an incomplete evaluation is stored and treated by the gate) names Malak and Alaa as co-owners of the answer. This package proposes the status-plus-missing-evidence display of `RCA-07`. | `RCA-07`, `RCA-08`, `OVW-04`, `OVW-06` |
| Q-07 | Mohamed, Mohab | US-25 lets a review be submitted from Trace Detail, but Appendix B gives the Governance Reviewer only View on Trace Detail. Confirm "submit a review" is an action-level permission. The governance contract (§7.3) and Schema v1 use three roles where the stories use seven. The audit action catalogue has no override request or approval. Confirm who sees review and audit history (GD-15). | `TRD-70`, `TRD-71`, `REL-16`, `REL-19` |
| Q-08 | Ahmed | Is the evaluation state (value, Not evaluated, Evaluator failed, Not applicable) a first-class result? How is a finding worded versus a metric? What reference format ties a cause to events, and how is "no cause supported" returned? How are the three classifier approaches reported for one trace? | `TRD-60` to `TRD-63`, `RCA-01` to `RCA-06` |
| Q-09 | Ahmed, Mohamed | How are attempted, prevented and realized violations returned once OD-09 is closed? | `RCA-09` |
| Q-10 | Alaa, Mohamed | The decision flow (§2.4) runs one decision engine for a trace and a release evaluation. Confirm Mohamed owns `REL-01` and `REL-02`, Alaa owns the comparison, artifact and disposition, and override requests and audit are Mohamed's. How do thresholds appear while OD-15 is open? | `REL-01`, `REL-02`, `REL-06`, `REL-18`, `REL-19` |
| Q-11 | Alaa, Ahmed | Schema v1 §5 puts scenario ground truth in the Release Quality Gate diagnostic panels, hidden from normal inference views. May reviewers see it, and under which role? Expected evidence is already shown on RAG Diagnostics as US-38 requires. | `REL-21` |
| Q-12 | Nour | Confirm the execution-mode values, that a replay has no model call, how raw and delivered text and source snapshots are exposed, and how the agent-guard rejection is emitted as its own event. | `TRX-04`, `TRD-13`, `TRD-44`, `TRD-47`, `TRD-50`, `RAG-18` |
| Q-13 | Mohamed, plan owner | Appendix B gives Manage on several dashboards, and describes actions such as configuring behavior, running evaluations, annotating results and initiating gate evaluations. Which are in the MVP, and what are their fields? | None until answered |
| Q-14 | Mohamed | Confirm the login form and Administrator account and role management are outside the seven screens. | Session context |
| Q-15 | Mohab, Nour, Mohamed, Ahmed | The three drafts name the same values differently: workflow stage names (S1-01, governance, Schema v1's nine-stage list), run status versus `execution_status`, approval status, abstention reasons, per-policy status versus a pass boolean, pre-tool verdict (ALLOW or BLOCK with a basis versus `ERROR_BLOCK`), and whether a blocked call emits a result event (Schema v1 does; S1-01 forbids a fabricated result). Which enumerations are canonical? | `TRD-01`, `TRD-02`, `TRD-22`, `TRD-23`, `TRD-43`, `TRD-45`, `TRD-62`, `RAG-16` |

## Requests the new drafts make of Malak

These are for Malak to answer. This package does not answer or acknowledge them on her behalf.

| Draft | Request | Status | Where this package stands |
|---|---|---|---|
| Governance decision flow §6 | Confirm human review and machine decision are separate, non-overwriting records, for the UI and gate | PENDING | The UI shows a human verdict beside the machine decision and its history, never in place of it (vocabulary rule 5, `TRD-70`, `TRD-71`). |
| Governance contract GD-13 | Decide with Alaa how an incomplete evaluation is stored and shown | PENDING | Proposed: no decision, an evaluation status and the missing-evidence list (`RCA-07`), and a gate that treats it as non-approving. |
| Governance contract §6 | Acknowledge the governance contract | PENDING | Not acknowledged. The contract is circulated to Malak. |
| Trace Schema v1 §9.2 | Lock answers on the ten gaps, including the three-event tool lifecycle that "maps 1:1 to Malak's Figure 3 nodes" | PENDING | The Trace Detail design shows proposal, policy check, dispatch and result as separate rows and works with either event model (Q-15). |

## Owner review record

Review requests are prepared and **not sent**. This package does not contact anyone. A PR approval does not replace these reviews, and silence is not sign-off. Each owner filters the [matrix](field-owner-matrix.md) by their name, confirms or corrects every row, and answers the listed questions.

| Owner | Review needed | Status | Revision | Evidence |
|---|---|---|---|---|
| Nour | Rows owned by Nour; Q-12, Q-15 | PENDING | 0.3 | — |
| Ahmed | Rows owned by Ahmed; Q-08, Q-09, Q-11, Q-15 | PENDING | 0.3 | — |
| Mohab | Rows owned by Mohab; Q-02 to Q-05, Q-07, Q-15 | PENDING | 0.3 | — |
| Mohamed | Rows owned by Mohamed; Q-06, Q-07, Q-09, Q-10, Q-13, Q-14, Q-15 | PENDING | 0.3 | — |
| Alaa | Rows owned by Alaa; Q-06, Q-10, Q-11 | PENDING | 0.3 | — |

Record each acknowledgement with the reviewer, date, revision reviewed, accepted rows and unresolved conditions. The task's report-back criterion (reviewed and acknowledged by all five owners) is **not met** until all five rows above show evidence.

## Checks

`tests/contract/test_dashboard_information_architecture.py` reads these documents and fails when they disagree. It is run by the Python CI workflow with the other contract tests. Locally, from the repository root:

```sh
uv run --locked --all-packages pytest tests/contract/test_dashboard_information_architecture.py
```

It checks that the seven screens match proposal section T, every field has one screen and one valid owner, every one of the 27 trace evidence requirements maps to a field, every wireframe marker resolves and every field is on its home wireframe, every navigation edge is well formed and every screen is within two links of Trace Detail, the access table matches Appendix B, every state has a distinct signature, every story US-34 to US-40 is traced, and the other documents cite only real fields and edges. See [paper-walkthroughs.md](paper-walkthroughs.md).

It cannot judge whether a design is usable, accessible or correct. That needs the owner reviews above, an independent walkthrough, and later a prototype review.
