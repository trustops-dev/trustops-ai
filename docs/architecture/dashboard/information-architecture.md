# Seven-screen information architecture

Revision 0.4 · 2026-10-19 · DRAFT. Part of the [dashboard UX architecture](README.md). Low-fidelity wireframes and a navigation model. No routing, components or code.

## Screens

The seven screens, their names and their order are those of proposal section T. Each is specified by one user story in Epic 7 (US-34 to US-40). The [story traceability](story-traceability.md) page maps every acceptance criterion to a design element.

| ID | Screen | Proposal and story | Job the user comes to do | Page pattern | Scaffold location |
|---|---|---|---|---|---|
| SCR-OVW | Reliability Overview | §T screen 1, US-34 | Glance at reliability across the platform, then leave for a module | Dashboard | `app/page.tsx`, `features/overview` |
| SCR-APP | Applications | §T screen 2, US-35 | Know which versions are deployed, the latest evaluation run and the latest gate decision | List, with application cards | `app/applications`, `features/applications` |
| SCR-TRX | Trace Explorer | §T screen 3, US-36 | Filter many traces down to the ones to investigate | List | `features/trace-explorer` |
| SCR-TRD | Trace Detail | §T screen 4, US-37 | Reconstruct one execution from its timeline, graph and evidence | Detail with sticky section navigation | `app/traces/[traceId]` |
| SCR-RAG | RAG Diagnostics | §T screen 5, US-38 | Decide whether a RAG failure came from retrieval or from ungrounded generation | Split Pane | `app/rag-diagnostics`, `features/rag-diagnostics` |
| SCR-RCA | Failure & RCA Investigation | §T screen 6, US-39 | Understand what failed, why, and what decision followed, without recomputing anything | Split Pane | `app/failure-rca`, `features/failure-rca` |
| SCR-REL | Release Quality Gate | §T screen 7, US-40 | Decide whether a candidate release is approved, reviewed or blocked | Detail with sticky section navigation | `app/release-gate`, `features/release-gate` |

There is no eighth screen. The execution graph, the review form, the override flow and the source snapshot viewer are regions or slide-overs inside these seven. The login form and Administrator account management are outside the seven (Q-14).

One screen has one job. List, board and calendar views of the same records would be a toggle on one screen.

## Design principles

| # | Principle | Consequence |
|---|---|---|
| P1 | The dashboard renders; backends decide. | No screen computes a decision, label, cause, score, graph or gate result. The Top-3 causes keep the engine's order. Release figures are those of the canonical gate artifact. |
| P2 | Separate concepts stay separate. | Outcome, run status, reliability decision, pre-tool verdict, release gate, human review and override each have their own scope label and signature. See [status vocabulary](status-vocabulary.md). |
| P3 | Evidence is never more than a few interactions away. | Reachability budgets below. |
| P4 | Missing is not zero, and pending is not a pass. | Every field has defined absence states. |
| P5 | One home per field. | The [matrix](field-owner-matrix.md) has one screen and one owner for each field. |
| P6 | Permissions are the backend's. | The UI shows what a role may do and why a control is unavailable. See [roles and access](roles-and-access.md). |
| P7 | Every number explains itself. | Meaning, unit and direction, source, and version accompany every score and badge. |

## Navigation model

```
Global navigation (persistent, all seven roles can open all of it)
  Reliability Overview · Applications · Trace Explorer · RAG Diagnostics · Failure & RCA · Release Gate

Drill-down (reached by link, not in global navigation)
  Trace Detail   ← from any trace link, with a breadcrumb back to where the user came from

After sign-in, each role lands on its default screen (Appendix B).
```

- Global navigation holds six items. Trace Detail is a drill-down that needs a trace.
- **Context travels with links.** Application, version, date, the selected baseline/candidate pair and any filter are carried in the link so the target opens already filtered. Every filtered screen shows its chips and a Clear all filters action.
- **URL state.** Filter, sort and pagination state is in the URL so a filtered view can be shared or bookmarked, and returning from Trace Detail restores the previous filters (US-36).
- **Breadcrumbs on drill-down.** Trace Detail shows `Traces › {trace}` or the origin, for example `Release Quality Gate › Critical scenarios › {scenario}`. Back returns to the origin with its filters.
- **Deep links.** Each Trace Detail section, each release gate section and each single event has a stable address, so an evidence link from Failure & RCA lands on the exact event (US-39). In the two Split Pane screens the selected trace is part of the address, so a per-trace link such as `/traces/{id}/investigation` or `/traces/{id}/rag` opens the same screen with that trace selected, not a second screen. Exact URL syntax is a Sprint 2 decision.
- **Narrow viewports** collapse global navigation behind a menu button that opens the same six destinations. No persistent rail on a phone.

### Cross-link table

Global navigation connects the six primary screens to each other and is not repeated here. These are the contextual links, and the table is the source for the paper walkthroughs and the navigation check.

| Edge | From | To | Trigger | Carries |
|---|---|---|---|---|
| N-01 | OVW | TRX | A segment of the decision tile | Decision value |
| N-02 | OVW | TRX | A failure class in the top-classes tile (US-34) | Failure class |
| N-03 | OVW | TRX | An application card (US-34) | Application |
| N-04 | OVW | REL | Release gate tile | Gate evaluation |
| N-05 | OVW | TRX | A count in the evaluation coverage tile | Evaluation state |
| N-06 | APP | TRX | View traces | Application |
| N-07 | APP | RAG | Inspect queries, RAG application only | Application |
| N-08 | APP | REL | The latest gate decision on a card (US-35) | Gate evaluation |
| N-09 | APP | RCA | View failures | Application |
| N-10 | TRX | TRD | Row | Trace |
| N-11 | TRX | RCA | Failure label link in a row | Trace |
| N-12 | TRD | TRX | More traces like this | Application, class, outcome |
| N-13 | TRD | RCA | Open investigation | Trace |
| N-14 | TRD | RAG | Open in RAG Diagnostics, RAG traces only | Trace |
| N-15 | TRD | REL | Open release gate, when the trace belongs to a gate evaluation | Gate evaluation |
| N-16 | TRD | APP | Application name in the header | Application |
| N-17 | RCA | TRD | Evidence link on a cause, rule or evaluator finding (US-39) | Trace, event |
| N-18 | RCA | TRX | View similar traces | Class or cause, application |
| N-19 | RCA | RAG | Open in RAG Diagnostics, RAG traces only | Trace |
| N-20 | RAG | TRD | Open full trace | Trace |
| N-21 | RAG | RCA | Open investigation | Trace |
| N-22 | RAG | TRX | View in explorer | Query filter |
| N-23 | REL | TRX | View traces for a regressed scenario | Gate evaluation, scenario |
| N-24 | REL | TRD | Paired baseline and candidate traces, or a critical scenario trace | Trace, event |
| N-25 | REL | RCA | A failure class change row | Class, gate evaluation |
| N-26 | REL | APP | A version row | Application |

### Evidence reachability budgets

An interaction is one click, tap or keyboard activation. Section jumps inside a screen count.

| From | To | Budget | How |
|---|---|---|---|
| A trace row (Trace Explorer, Failure & RCA queue) | The supporting event in Trace Detail | 3 interactions or fewer | Open the trace (1), open the investigation (2), follow a cause, rule or finding's evidence link (3). From the Failure & RCA queue it is 2. |
| An Overview count, failure class or application card | The supporting event in Trace Detail | 4 interactions or fewer | Open the filtered list (1), open a trace (2), open the investigation (3), follow an evidence link (4). |
| A blocked release gate | The first supporting event in Trace Detail | 4 interactions or fewer | Open a gate reason (1), open the critical scenario's trace (2), open the investigation (3), follow an evidence link (4). |
| Any claim in the RAG inspector | The source snapshot text | 2 interactions or fewer | Select the claim (1), open its citation source (2). |

## Wireframe notation

Low fidelity: boxes, labels, and field IDs. Boxes are not final layout.

| Mark | Meaning |
|---|---|
| `{TRD-60}` | The home field. Its value is defined and shown in full here. |
| `{>TRD-60}` | A read-only projection of a field homed on another screen. |
| `[Label]` | A button or link. Labels are verb first. |
| `✓ ◆ ■ ▶ ⊣ ∅ ○ ▲ ⊘ ◔ ? ✕ ▒ ▢` | State glyphs from the [vocabulary](status-vocabulary.md). |
| `…` | Content elided for the sketch. |
| `<n>`, `<id>`, `<time>` | A placeholder. Every name, count and identifier in a wireframe is layout filler, not a result or sample data. |

All wireframes are drawn at wide (1280 px). Behavior at narrow (375) and medium (768) is in each screen's notes. Only three viewport tokens are used: narrow 375, medium 768, wide 1280.

### Application shell (not a screen)

```
┌──────────────┬────────────────────────────────────────────────────────────────────────┐
│ TrustOps AI  │ [Skip to main content]      Synthetic data · mock tools   <name> · <role>│
│              ├────────────────────────────────────────────────────────────────────────┤
│ Overview     │  Page heading                                              [Header actions]
│ Applications │  One sentence describing the page                                       │
│ Traces       │  ──────────────────────────────────────────────────────────────────── │
│ RAG Diag.    │                                                                        │
│ Failure&RCA  │  main content (width capped, centered)                                  │
│ Release Gate │                                                                        │
└──────────────┴────────────────────────────────────────────────────────────────────────┘
 Shell and sidebar span the viewport. Only the main content is width-capped.
 Narrow: sidebar hidden, [Menu] button opens the same six items.
```

## SCR-OVW — Reliability Overview

Pattern: Dashboard. Read-only. At most five tiles. No date-range control and no drill inside the page; every element links out. It shows the six items US-34 requires: application cards, trace count, the decision distribution, top failure classes, recent gate status and a reliability trend.

```
Reliability Overview
Reliability across connected applications for the window shown below.
Window {OVW-01}  <label> · <start> to <end>        Data as of {OVW-03}  <time> · lag <value>
┌─ Traces ────────┐┌─ Reliability decisions ───────┐┌─ Top failure classes ┐┌─ Evaluation ───────┐┌─ Release gate ──┐
│ {OVW-02}        ││ {OVW-04}                      ││ {OVW-07}             ││ {OVW-05}           ││ {>REL-01}       │
│ <n> total       ││ ✓ Pass <n>   ◆ Review <n>    ││ 1 <class>  <n>       ││ <n> evaluated      ││ ■ Release gate  │
│ by application  ││ ■ Block <n>  ◔ No decision <n>││ 2 <class>  <n>       ││ ○ Not evaluated <n>││   Block         │
│ [View traces]   ││ [View blocked traces]         ││ 3 <class>  <n>       ││ ▲ Evaluator failed ││ [Open gate]     │
│                 ││                               ││                      ││ ⊘ Not applicable   ││                 │
└─────────────────┘└───────────────────────────────┘└──────────────────────┘└────────────────────┘└─────────────────┘
┌─ Reliability trend {OVW-06} ──────────────────────────────────────────────────────────────────────────────┐
│ Decision distribution over successive periods, with a text table alternative below the chart              │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ Applications ────────────────────────────────────────────────────────────────────────────────────────────┐
│ {>APP-01}  <name> · <kind>   {>APP-03} run status        Traces <n>   Decisions ✓ <n> ◆ <n> ■ <n>        │
│ Latest gate {>REL-01}  <decision> · <time>                                          [View traces]        │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Notes:

- The five tiles are traces, decisions, top failure classes, evaluation coverage and the release gate. The trend is the primary chart. Application cards are the supporting list.
- Clicking a failure class or an application card opens Trace Explorer already filtered (US-34, N-02, N-03). Every number is a link (N-01 to N-05). Counts in the evaluation tile open Trace Explorer filtered to that evaluation state.
- "No decision" is its own count (`PE`). It is never folded into Pass.
- All aggregates are live from the backend. No value is hardcoded.
- Narrow: tiles stack one or two per row; the chart is full width; cards keep their link visible.
- First-use empty: "No applications connected yet" with Connect an application. Error: each tile fails on its own with Retry.
- The Administrator and the Security Auditor land here after sign-in.

## SCR-APP — Applications

Pattern: List, with each application shown as a full-width card. The set is small, and a card lets all four version identifiers show in full without truncating the differentiating suffix (US-35). The card holds everything, and a Details disclosure inside the card shows the rest. No detail route or slide-over is used.

```
Applications
Connected applications: versions, the latest evaluation run and the latest gate decision.
[Search applications …]  [Filters]
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ {APP-01} <name> · <kind>     {APP-02} Synthetic data · mock tools          Last trace {APP-04} <time>    │
│ Run status {APP-03}  Active <n> · Waiting <n> · Blocked <n> · Failed <n> · Succeeded <n> …                │
│ Versions {APP-05}   application <id>  model <id>  prompt <id>  retriever <id>                            │
│ Latest evaluation run {APP-08}  <run id> · <time> · dataset <ver> · evaluator <ver> · <status>            │
│ Latest gate decision {>REL-01}  ■ Release gate Block · <candidate> vs <baseline>          [Open gate ›]   │
│ [View traces] [View failures] [Inspect queries]                                          [Details ▾]      │
│  ┌─ Details ───────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Other versions {APP-06}  Provider and model {APP-07}  Ingestion {APP-09}  Policy {APP-10}            │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
 Page <n> of <n>   [Previous] [Next]
```

Notes:

- The most recent gate decision links directly to its full Release Quality Gate record (N-08).
- Version data is exactly what the version registry holds. The screen computes nothing.
- "Inspect queries" is present only for the RAG application. Export is not required and has no field.
- No Manage controls are drawn. Appendix B gives some roles Manage here, and no story defines what it covers (Q-13).
- Narrow: cards stack; a version identifier wraps and never truncates. Search focuses with `/`.
- The AI Engineer lands here after sign-in.

## SCR-TRX — Trace Explorer

Pattern: List. One Filters control; active values appear as chips. Row activation opens Trace Detail.

```
Trace Explorer
Every ingested trace. Filter to find the ones to investigate.
[Search traces …]  [Filters]  [Columns]
Application: <app> ×   Reliability decision: Block ×   Failure label: <class> ×     [Clear all filters]
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Trace {TRX-01}  App {>APP-01}  Version {>APP-05}  Date {TRX-02}   Mode {TRX-04}    Outcome {>TRD-01}
 tr-<id> ›       <app>          <ids>              <time> · <dur>  Live model       Blocked
 …                                                      Failure label {>RCA-01}   Decision {>RCA-07}
                                                        Policy {>TRD-62}  Security {>TRD-63}
                                                        Evidence {TRX-03}   Scenario {TRX-05}   Env {TRX-06}
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Page <n> of <n>   [Previous] [Next]
```

Filters panel, all combinable: application, version, date, failure label, policy/security verdict, reliability decision (the six US-36 requires), plus execution mode and scope, execution environment, application outcome, run status, evaluation state, evidence completeness and scenario run. Each is the value set of an existing field.

Notes:

- Default sort is newest first. Rows have a resting affordance (link-colored trace ID, chevron).
- Filter, sort and pagination state live in the URL. Returning from Trace Detail restores them.
- `Evidence` shows Complete, Incomplete or Inconclusive (`TRX-03`). Incomplete traces carry the ✕ Missing evidence signature.
- Filtered empty: "No traces match your filters" with Clear all filters. First-use empty: "No traces yet" with Connect an application.
- Narrow: toolbar wraps; the table scrolls inside its region and keeps type at 12 px or larger. Search focuses with `/`.
- The Platform Engineer lands here after sign-in.

## SCR-TRD — Trace Detail

Pattern: Detail. The header carries status and metadata. Nine sections sit in a sticky section navigation, because nine is past the limit for a tab row. Each section loads independently and owns its loading, empty and error states. Event types, and proposed, blocked, failed and successful actions, are told apart in text and by signature (US-37).

```
Traces › tr-<id>                                [Record review]  [Open investigation]  [Open in RAG Diagnostics]  [⋯]
<app> · Live model · <time> · Evidence: Complete {>TRX-03}
┌─ Summary ───────────────────────────────────────────────────────────────────────────────────────┐
│ Outcome {TRD-01}  Blocked          Run {TRD-02}  BLOCKED                                          │
│ Decision {>RCA-07}  ■ Reliability Block       Failure label {>RCA-01}  Workflow violation          │
│ Policy verdict ›  Security verdict ›  Evaluator outputs ›  Review history ›                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
 Summary          │ (section content)
 Timeline         │
 Request & model  │
 Procurement ev.  │
 Tools & enforce. │
 Response         │
 Evaluator outputs│
 Review & audit   │
 Provenance       │
```

`[Record review]` is enabled for the roles that may submit one and unavailable, with the reason, for the others. The summary links open the section that holds the fact.

### Section contents

| Section | Fields | What the user must be able to tell |
|---|---|---|
| Summary | `{TRD-01}` `{TRD-02}` | Outcome and run status sit beside the decision and failure label shown from Failure & RCA. A waiting run is not a pass. |
| Timeline | `{TRD-20}` `{TRD-21}` `{TRD-22}` `{TRD-23}` | Order of events and states, which transitions were attempted versus accepted, and the backend-derived graph. The ordered list is primary and the graph is a view with the same content in text. The page does no graph derivation. |
| Request and model | `{TRD-10}` `{TRD-11}` `{TRD-12}` `{TRD-13}` `{TRD-14}` | What was asked, how it was normalized, and what the model was given and returned. A replay shows Not applicable for the model call, not an invented response. Unknown usage is Unavailable, never 0. |
| Procurement evidence | `{TRD-30}` `{TRD-31}` `{TRD-32}` `{TRD-33}` `{TRD-34}` `{TRD-35}` | Policy found, supplier status, approval required or not, and whether a valid approval was observed and bound. For a RAG trace this section is Not applicable and links to RAG Diagnostics. |
| Tools and enforcement | `{TRD-40}` `{TRD-41}` `{TRD-42}` `{TRD-43}` `{TRD-44}` `{TRD-45}` `{TRD-46}` `{TRD-47}` | The proposal, the arguments, the pre-tool verdict, which layer stopped the call if one did, whether the tool ran, and the result. Proposed, blocked, failed and successful actions are separate rows. |
| Response | `{TRD-50}` `{TRD-51}` | The raw generated text and the delivered text side by side with which one was shown, plus the evidence supporting or contradicting any completion claim. |
| Evaluator outputs | `{TRD-60}` `{TRD-61}` `{TRD-62}` `{TRD-63}` | Each evaluator as value, ○ Not evaluated, ▲ Evaluator failed or ⊘ Not applicable, each value with its metric name, unit, direction and version. The policy verdicts and the security verdict sit here. |
| Review and audit | `{TRD-70}` `{TRD-71}` | The review history, never editable, and the audit trail with actor, role, time and versions. An Administrator action carries its flag. |
| Provenance and completeness | `{TRD-80}` `{TRD-81}` `{TRD-82}` `{TRD-83}` | Exact versions used, what was redacted or unavailable, which expected events are missing, and whether the current role sees raw or redacted payloads. |

### Tools and enforcement: approval-bypass example

```
Tools and enforcement
 1  Proposal {TRD-40}      create_purchase_order · catalog v… · proposal <id>        (from model call <id>)
 2  Arguments {TRD-41}     raw · parsed · trusted context (separate)      validation: ✓ passed
 3  Agent guard {TRD-47}   ⊘ Not applicable — the agent's own stage check did not reject this call
 4  Policy request {TRD-42}   proposal <id> · stage PRE_APPROVAL · state revision … · digest …
 5  Pre-tool verdict {TRD-43}  ⊣ Pre-tool Block · basis: policy violation · checked by: real policy engine
        ✕ PROC-APPROVAL-01   approval required, none received       [View approval evidence ›]
        ✕ PROC-TOOL-STAGE-01 tool not allowed at this stage
 6  Dispatch {TRD-44}      ∅ Not executed · stopped by: pre-tool policy · execution_started: false
 7  Tool result {TRD-45}   ⊘ Not applicable — nothing ran
 8  Recovery {TRD-46}      ⊘ Not applicable
```

Notes:

- Row 7 says Not applicable because row 6 is positive evidence that nothing ran. If row 6 were absent, row 7 would read ✕ Missing evidence.
- If the verdict came from the contract stub rather than the real policy engine, row 5 says so in text (Schema v1 `check_mode`). If no verdict came back, row 5 reads as a technical check error and row 6 names a missing verdict as the layer that stopped the call.
- If the canonical schema also records a result event for a blocked call (Schema v1 §4.2 does; the S1-01 contracts do not), row 7 shows it as blocked with no side effect committed, using the Not executed signature. Q-15 asks the owners to settle which one stands.
- Row 3 shows the other possible layer. When the agent guard rejects a call first (stage not approved, US-03), row 3 holds the rejection, and rows 4 and 5 read ⊘ Not applicable because no policy request was made.
- Narrow: section navigation becomes a select at the top of the content; the summary tags wrap; wide tables scroll inside their region.
- The AI Engineer and Platform Engineer investigate here. Raw payloads show only to the Administrator.

## SCR-RAG — RAG Diagnostics

Pattern: Split Pane. A compact query list on the left. The inspector on the right holds the selected query. Selecting never changes route. A person unfamiliar with a seeded trace must be able to name its failure type from this screen alone (US-38), so the failure label sits in the inspector header.

```
RAG Diagnostics                                                                       [Open full trace]
Inspect retrieval, selected context, claims and citations for one query at a time.
[Search queries …]  [Filters]     [All] [Needs attention] [Abstained] [Errors]
┌─ Queries ───────────────────────┐ ┌─ Inspector   Failure type {>RCA-01}   [Open investigation] ───────┐
│▸ <query text>                   │ │ Query | Retrieval | Context | Answer | Abstention                  │
│   {RAG-19} Abstention  ○ …      │ │ ───────────────────────────────────────────────────────────────  │
│  <query text>                   │ │ Query                                                              │
│   Answer       …                │ │  {RAG-01} raw · effective · transformation   {RAG-02} k · filters │
│  …                              │ │  {RAG-03} retriever · corpus · index · embedding   {RAG-20} …     │
└─────────────────────────────────┘ │ Retrieval   {RAG-04} Success · <n> returned (or Error)              │
                                    │  #1 doc-<id> chunk … score … rank 1   {RAG-05} {RAG-06}            │
                                    │  Expected evidence {RAG-09}: doc-<id> — not retrieved              │
                                    │  Metrics {RAG-10}: Recall@k <value> (higher is better) · MRR …     │
                                    │ Context     {RAG-07} selected <ranks> · rejected <ranks> (reasons) │
                                    │             {RAG-08} sufficiency: Insufficient evidence            │
                                    │ Answer      {RAG-19} Answer                                        │
                                    │  {RAG-11} candidate · delivered  {RAG-12} claims                   │
                                    │  claim c1 → {RAG-13} citation → [View source ›]                    │
                                    │  {RAG-14} structural: ✓ resolves   {RAG-15} unsupported: ○ …       │
                                    │  {RAG-21} Groundedness <value> (higher is better) · Citation prec. │
                                    │ Abstention  {RAG-16} reason · missing · last stage                 │
                                    │             {RAG-17} appropriateness: ○ Not evaluated              │
                                    └────────────────────────────────────────────────────────────────────┘
┌─ Slide-over: Source snapshot {RAG-18} ──────────────────────┐
│ title · source id · version · hash                           │
│ immutable text with the cited span highlighted               │
└──────────────────────────────────────────────────────────────┘
```

Notes:

- The left pane is a compact list with no table headers and no sort controls. Arrow keys move selection; Enter moves focus to the inspector.
- Retrieved order (`RAG-05`, `RAG-06`) and selected order (`RAG-07`) are two lists, so a reader sees what was returned versus what the model saw.
- Expected evidence (`RAG-09`) is shown, labeled evaluation-side. It is never an input to the application, retrieval or classifier. Missing expected-evidence metadata shows Not evaluated, never a zero score (US-15).
- Retrieval error and an empty success differ: `RAG-04` shows "Error: {stage}" or "Success: 0 returned". An error is never shown as a zero metric.
- A structurally valid citation (`RAG-14`) and a supported claim (`RAG-15`) are separate lines. The first never implies the second.
- Groundedness and citation precision always show metric name, unit, direction and evaluator version, never a bare number (`RAG-21`, US-38).
- Narrow: the list is full width; tapping a query opens the same inspector full width on this route, with a Back to queries control. A second detail route would duplicate the inspector (DX-04).

## SCR-RCA — Failure & RCA Investigation

Pattern: Split Pane. The left queue lists traces that need investigation. The right pane investigates the selected trace: label, causes, decision. It works as a landing page for the Reliability Engineer and Governance Reviewer, who have no selected trace on arrival. Nothing is recomputed here.

```
Failure & RCA Investigation                                                             [Record review]
Traces that need investigation, with the evidence behind each diagnosis.
[Search traces …]  [Filters]     [Needs investigation] [Block] [Review] [No decision yet]
┌─ Queue ─────────────────────────┐ ┌─ Investigation: tr-<id> ──────────────────────────────────────────┐
│▸ tr-<id>                        │ │ Diagnosis | Causes | Decision | Review                              │
│   {RCA-01} · {RCA-07}           │ │ ─────────────────────────────────────────────────────────────────  │
│  tr-<id>                        │ │ Diagnosis                                                           │
│   …                             │ │  Primary label {RCA-01}  <class> · <approach> · version             │
│                                 │ │  Score {RCA-02}   <value> (rules baseline: ⊘ no score)              │
│                                 │ │  Also found {RCA-03}      Rules fired {RCA-04}                      │
│                                 │ │  Human label {RCA-10}     Violation type {RCA-09}                   │
│                                 │ │  Evaluation runs {RCA-12}                                           │
│                                 │ │ Causes                                                              │
│                                 │ │  1 <cause>   evidence score <v>   {RCA-05}  (not a probability)     │
│                                 │ │  Evidence {RCA-06}: <evaluator vN> finding › event <id>   [Open ›]  │
│                                 │ │  Evaluator findings {>TRD-60}                                       │
│                                 │ │ Decision                                                            │
│                                 │ │  ■ Reliability Block {RCA-07}   decided <time> · decision version   │
│                                 │ │  Rule path {RCA-08}:  <rule> ›   <evaluator signal> ›               │
│                                 │ │ Review                                                              │
│                                 │ │  History {>TRD-70}  ·  Audit {>TRD-71}                              │
└─────────────────────────────────┘ └─────────────────────────────────────────────────────────────────────┘
```

Notes:

- The Top-3 causes show in the order the RCA engine returned them, each with its evidence score. The screen never re-ranks. Scores are called evidence scores, not probabilities.
- Every cause, rule and evaluator finding has an evidence link that opens the specific event in Trace Detail (N-17, US-39).
- The decision always shows its rule path, not only the label. A trace with no supported cause shows that explicitly.
- `[Record review]` opens a slide-over (verdict ACCEPT, REVIEW or BLOCK plus rationale). The new entry appears in the review history immediately and cannot be edited afterwards. Only roles that may submit one see it enabled.
- A waiting run or a trace not yet decided shows Reliability: ◔ Awaiting result, never PASS.
- Narrow: the queue is full width; selecting a trace opens the investigation full width on this route with a Back to queue control.
- Queue first-use empty: "No traces need investigation" with a link to Trace Explorer.
- The Reliability Engineer and the Governance Reviewer land here after sign-in.

## SCR-REL — Release Quality Gate

Pattern: Detail. One gate evaluation: a candidate compared with the approved baseline on the same versioned dataset. Seven sections sit in a sticky section navigation. Every figure is that of the canonical gate artifact; the screen recalculates nothing (US-40).

```
Release Quality Gate › Candidate {REL-03}   vs   Baseline                  [Select evaluation ▾]  [Record review]
■ Release gate Block {REL-01}   gate policy v… · evaluated <time>     Artifact {REL-17}  <ref> · CI job <status>
Candidate: approved baseline retained {REL-18}
┌─ Decision ──────────────────────────────────────────────────────────────────────────────────────────┐
│ Why {REL-02}:  <metric> regressed ›   <n> critical failures ›   Run incomplete (<n> cases) ›          │
│ Overrides {REL-19}:  none requested · [Request override]                                             │
│ Release reviews {REL-16}:  none                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
 Decision          │ Metrics by area
 Metrics by area   │  Area      Metric {REL-05}  Baseline  Candidate  Delta   n    State {REL-04}
 Critical scenarios│  RAG       <metric>         …         …          …       …    ▲ Evaluator failed
 Version changes   │  Agent     <metric>         <value>   …          …       …    Value
 Lineage & compl.  │  Security  <metric>         …         …          …       …    Value
 Override & audit  │  Overall   <metric>         …         …          …       …    Value
 History           │  Threshold {REL-06}  ▢ Not configured (OD-15)
                   │  A metric state is a value or one of the absence states.
```

### Section contents

| Section | Fields | What the user must be able to tell |
|---|---|---|
| Decision | `{REL-01}` `{REL-02}` `{REL-03}` `{REL-17}` `{REL-18}` `{REL-16}` `{REL-19}` | The decision with its scope label, what happens to the candidate (BLOCK retains the approved baseline, REVIEW requires human action), every reason as a link, the gate artifact, and any release review or override. |
| Metrics by area | `{REL-04}` `{REL-05}` `{REL-06}` | Baseline and candidate side by side with deltas for RAG, Agent, Security and Overall, each metric with its unit and direction. A missing threshold is ▢ Not configured, not a pass. |
| Critical scenarios | `{REL-09}` `{REL-10}` `{REL-11}` `{REL-21}` | Regressed scenarios with links to the paired traces, the failure class shift, and the critical policy and security failures the candidate introduces. Scenario ground truth appears in a labeled evaluation-side panel here and nowhere else. |
| Version changes | `{REL-07}` `{REL-08}` | What changed between baseline and candidate, and which evaluation set was used. |
| Lineage and completeness | `{REL-12}` `{REL-13}` `{REL-14}` | Whether the run is complete, how to reproduce it, and whether the comparison is fixture-deterministic or live. |
| Override and audit | `{REL-19}` `{REL-20}` | Override requests and approvals with their reasons, and the audit history of this evaluation. |
| History | `{REL-15}` | Earlier gate evaluations, each opening this screen for that evaluation. |

Notes:

- Gate reasons (`REL-02`) link to the metric row, critical scenario or completeness record they cite. This is the first step of the four-interaction budget.
- A REVIEW verdict says plainly that human action is required. It is not an approval. The GitHub job fails on BLOCK and does not fail on REVIEW (US-33); the CI job status shows that.
- **Override flow.** The LLMOps Engineer requests an override with a written reason (slide-over). A Governance Reviewer or Administrator approves or rejects it behind a confirmation that names the candidate. Each step becomes an audit entry. An Administrator action is flagged.
- A gate that cannot be decided because evidence is missing shows ✕ Missing evidence under Lineage and completeness, and `◔ Awaiting result` or `▢ Not configured` as its decision, never PASS.
- Narrow: the section navigation becomes a select; tables scroll inside their region.
- The LLMOps Engineer lands here after sign-in.

## Keyboard, focus and viewport requirements

These apply to every screen. Wireframes do not repeat them.

| Area | Requirement |
|---|---|
| Skip link | First focusable element, "Skip to main content". |
| Tab order | Follows reading order. Section navigation and tab rows use arrow keys inside the group. |
| Focus ring | Visible on every interactive element: 2px offset, 3:1 contrast, in both themes. |
| Search | Present on List and Split Pane screens. `/` focuses it. |
| Overlays | Slide-overs and dialogs trap focus, close with Escape, and return focus to the element that opened them. |
| Primary actions | All reachable without hover. Hover only adds extras. |
| Hit targets | 44 by 44 px minimum. Icon-only controls get padding to meet it. |
| Page overflow | None at 375 or 1280. Tables scroll inside their own region. Type stays at 12 px or larger. |
| Graph and charts | Each has a text or table alternative with the same content. |
| Destructive actions | None in scope. An override approval is consequential and uses a named-entity confirmation with Cancel focused. |
