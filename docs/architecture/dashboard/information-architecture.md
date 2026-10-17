# Seven-screen information architecture

Revision 0.1 · 2026-10-17 · DRAFT. Part of the [dashboard UX architecture](README.md). Low-fidelity wireframes and a navigation model. No routing, components or code.

## Screens

The seven screens are inferred from the dashboard scaffold (`apps/dashboard/src/app/` and `src/features/`) and the S1-01 handoffs, because the proposal section that names them is not in the repository. See assumption A-01 in the [README](README.md#assumptions-and-decisions).

| ID | Screen | Job the reviewer comes to do | Page pattern | Scaffold location |
|---|---|---|---|---|
| SCR-OVW | Overview | Glance at fleet reliability, then leave for a module | Dashboard | `app/page.tsx`, `features/overview` |
| SCR-APP | Applications | Find an application and check its health, versions and applicable policy | List, with a read-only slide-over | `app/applications`, `features/applications` |
| SCR-TRX | Trace Explorer | Search and filter traces to find the ones to inspect | List | `features/trace-explorer` |
| SCR-TRD | Trace Detail | Verify one trace from request to decision, using its evidence | Detail with sticky section navigation | `app/traces/[traceId]` |
| SCR-RCA | Failure & RCA | See failure and cause patterns across traces and reach examples | Analytics (analytical) | `app/failure-rca`, `features/failure-rca` |
| SCR-RAG | RAG Diagnostics | Triage RAG queries and inspect retrieval, context, claims and citations | Split Pane | `app/rag-diagnostics`, `features/rag-diagnostics` |
| SCR-REL | Release Gate | Read a candidate-versus-baseline gate decision and trace it to evidence | Detail with sticky section navigation | `app/release-gate`, `features/release-gate` |

There is no eighth screen. Execution graph, human review, and the source snapshot viewer are regions or slide-overs inside these screens.

Pattern names follow the page-pattern catalog used for this design review. One screen has one job; list, board and calendar views of the same records would be a toggle on one screen.

## Design principles

| # | Principle | Consequence |
|---|---|---|
| P1 | The dashboard renders; backends decide. | No screen computes a decision, label, cause or approval. |
| P2 | Separate concepts stay separate. | Outcome, run status, reliability decision, pre-tool verdict, release gate and human review each have their own scope label and signature. See [status vocabulary](status-vocabulary.md). |
| P3 | Evidence is never more than a few interactions away. | Reachability budgets below. |
| P4 | Missing is not zero, and pending is not a pass. | Every field has defined absence states. |
| P5 | One home per field. | The [matrix](field-owner-matrix.md) has one screen and one owner for each field. |
| P6 | Read-first. | The only candidate write is a human review record (open question Q-07). No destructive actions exist. |

## Navigation model

```
Global navigation (persistent, always present)
  Overview · Applications · Traces · Failure & RCA · RAG Diagnostics · Release Gate

Drill-down (reached by link, not in global navigation)
  Trace Detail   ← from any trace link, with a breadcrumb back to where the reviewer came from
```

- Global navigation holds six items. Trace Detail is a drill-down that needs a trace.
- **Context travels with links.** Application, the selected time range, and the baseline/candidate pair are carried in the link so the target screen opens already filtered. Every filtered screen shows its chips and a Clear all filters action.
- **Breadcrumbs on drill-down.** Trace Detail shows `Traces › {trace}` or, when reached from elsewhere, the origin: `Release Gate › Regressions › {scenario}`. Back returns to the origin with its filters.
- **Deep links.** Each Trace Detail section and each release gate section has a stable address, and a link can point at a single event. Exact URL syntax is a Sprint 2 decision.
- **Narrow viewports** collapse global navigation behind a menu button that opens the same six destinations. No persistent rail on a phone.

### Cross-link table

Global navigation connects the six primary screens to each other and is not repeated here. These are the contextual links, and the table is the source for the paper walkthroughs and the navigation check.

| Edge | From | To | Trigger | Carries |
|---|---|---|---|---|
| N-01 | OVW | TRD | Row in the "needs attention" list | Trace |
| N-02 | OVW | TRX | A segment of the decision tile or chart | Decision value, application |
| N-03 | OVW | APP | Application name in the volume tile | Application |
| N-04 | OVW | REL | Release gate tile | Gate evaluation |
| N-05 | OVW | TRX | A count in the evaluation coverage tile | Evaluation state |
| N-06 | APP | TRX | View traces | Application |
| N-07 | APP | RAG | Inspect queries, RAG application only | Application |
| N-08 | APP | REL | View release gate | Application |
| N-09 | APP | RCA | View failures | Application |
| N-10 | TRX | TRD | Row | Trace |
| N-11 | TRX | RCA | Failure class link in a row | Failure class |
| N-12 | TRD | TRX | More traces like this | Application, class, outcome |
| N-13 | TRD | RCA | Failure class or cause link | Class, cause |
| N-14 | TRD | RAG | Open in RAG Diagnostics, RAG traces only | Trace |
| N-15 | TRD | REL | Open release gate, when the trace belongs to a gate evaluation | Gate evaluation |
| N-16 | TRD | APP | Application name in the header | Application |
| N-17 | RCA | TRX | View traces, from a class, a cause or an evaluator health row | Class, cause or evaluator and state; application |
| N-18 | RCA | TRD | Exemplar trace | Trace |
| N-19 | RCA | RAG | Retrieval-related classes | Class |
| N-20 | RAG | TRD | Open full trace | Trace |
| N-21 | RAG | TRX | View in explorer | Query filter |
| N-22 | RAG | RCA | Failure class link | Class |
| N-23 | REL | TRX | View traces for a regressed scenario | Gate evaluation, scenario |
| N-24 | REL | TRD | Paired baseline and candidate traces | Trace |
| N-25 | REL | RCA | Failure class change row | Class, gate evaluation |
| N-26 | REL | APP | Version row | Application |

### Evidence reachability budgets

An interaction is one click, tap or keyboard activation. Section jumps inside a screen count.

| From | To | Budget | How |
|---|---|---|---|
| Any list row showing a failed or REVIEW trace (OVW attention list, TRX, RCA exemplar, RAG query) | The supporting event in Trace Detail | 3 interactions or fewer | Open the trace (1), open the decision rationale (2), follow its evidence link (3). |
| A blocked release gate | The first supporting event in Trace Detail | 4 interactions or fewer | Open a gate reason (1), open the regressed scenario trace (2), open the decision rationale (3), follow its evidence link (4). |
| Any claim in the RAG inspector | The source snapshot text | 2 interactions or fewer | Select the claim (1), open its citation source (2). |

## Wireframe notation

Low fidelity: boxes, labels, and field IDs. Boxes are not final layout.

| Mark | Meaning |
|---|---|
| `{TRD-03}` | The home field. Its value is defined and shown in full here. |
| `{>TRD-03}` | A read-only projection of a field homed on another screen. |
| `[Label]` | A button or link. Labels are verb first. |
| `✓ ◆ ■ ▶ ⊣ ∅ ○ ▲ ⊘ ◔ ? ✕ ▒ ▢` | State glyphs from the [vocabulary](status-vocabulary.md). |
| `…` | Content elided for the sketch. |
| `<n>`, `<id>`, `<time>` | A placeholder. Every name, count and identifier in a wireframe is layout filler, not a result or sample data. |

All wireframes are drawn at wide (1280 px). Behavior at narrow (375) and medium (768) is in each screen's notes. Only three viewport tokens are used: narrow 375, medium 768, wide 1280.

### Application shell (not a screen)

```
┌──────────────┬────────────────────────────────────────────────────────────────────────┐
│ TrustOps AI  │ [Skip to main content]                    Synthetic data · mock tools   │
│              ├────────────────────────────────────────────────────────────────────────┤
│ Overview     │  Page heading                                              [Header actions]
│ Applications │  One sentence describing the page                                       │
│ Traces       │  ──────────────────────────────────────────────────────────────────── │
│ Failure&RCA  │                                                                        │
│ RAG Diag.    │  main content (width capped, centered)                                  │
│ Release Gate │                                                                        │
└──────────────┴────────────────────────────────────────────────────────────────────────┘
 Shell and sidebar span the viewport. Only the main content is width-capped.
 Narrow: sidebar hidden, [Menu] button opens the same six items.
```

## SCR-OVW — Overview

Pattern: Dashboard. Read-only. At most five tiles. No date-range control and no drill inside the page; every element links out.

```
Overview
Reliability across connected applications for the window shown below.
Window: {OVW-01}  <label> · <start> to <end>
┌─ Traces ────────┐┌─ Reliability decisions ───────┐┌─ Evaluation ───────┐┌─ Freshness ──┐┌─ Release gate ──┐
│ {OVW-02}        ││ {OVW-04}                      ││ {OVW-05}           ││ {OVW-03}     ││ {>REL-01}       │
│ <n> total       ││ ✓ Pass <n>   ◆ Review <n>    ││ <n> evaluated      ││ Latest trace ││ ■ Release gate  │
│ by application  ││ ■ Block <n>  ◔ No decision <n>││ ○ Not evaluated <n>││ <time>       ││   Block         │
│ [Open apps]     ││ [View blocked traces]         ││ ▲ Evaluator failed ││ Lag <value>  ││ [Open gate]     │
│                 ││                               ││ ⊘ Not applicable   ││              ││                 │
└─────────────────┘└───────────────────────────────┘└────────────────────┘└──────────────┘└─────────────────┘
┌─ Decisions by application ────────────────────────────────────────────────────────────────────────────────┐
│ Stacked bars from {OVW-04}, one per application; text table alternative below the chart                   │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ Needs attention ─────────────────────────────────────────────────────────────────────────────────────────┐
│ ■ Block  {>TRX-01}  {>APP-01}  {>TRD-01}  {>TRD-05}  {>TRX-02}                                   [Open ›] │
│ ◆ Review  …                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Notes:

- Tiles are fixed at five: traces, decisions, evaluation coverage, freshness, release gate. The window is set by the backend and shown, not chosen.
- Every number is a link to the filtered destination (N-01 to N-05). Counts in the evaluation tile open Trace Explorer filtered to that evaluation state, so Not evaluated and Evaluator failed traces are one step away.
- "No decision" is its own count (`PE`). It is never folded into Pass.
- Narrow: tiles stack one or two per row; the chart is full width; the attention list keeps its Open action visible.
- First-use empty: "No applications connected yet" with Connect an application. Error: each tile fails on its own with Retry.

## SCR-APP — Applications

Pattern: List. Row activation opens a read-only slide-over. A detail route would be an eighth screen, so it is not used. The slide-over is a read of under ten seconds with links out, which fits the slide-over surface.

```
Applications
Connected applications, their health, versions and the policies that apply to them.
[Search applications …]  [Filters]
────────────────────────────────────────────────────────────────────────────────────────────────────
 Application {APP-01}     Data {APP-02}   Run status mix {APP-03}                  Last trace {APP-04}
 Procurement Agent  ›     Synthetic       Active <n> · Waiting <n> · Blocked <n> … <time>
 Enterprise RAG Assistant › Synthetic     Succeeded <n> · Failed <n> …             <time>
────────────────────────────────────────────────────────────────────────────────────────────────────
 Page 1 of 1   [Previous] [Next]

┌─ Slide-over: Procurement Agent ───────────────────────────────┐
│ Ingestion  {APP-05}   received · rejected · incomplete        │
│ Versions   {APP-06}   app · prompt · model/config · retriever …│
│ Model      {APP-07}   gemini · gemini-3.8-flash · returned: ?  │
│ Policy     {APP-08}   PROC-APPROVAL-01 …  ⊘ Not applicable (RAG)│
│ [View traces] [View failures] [View release gate] [Inspect queries]│
└───────────────────────────────────────────────────────────────┘
```

Notes:

- Export is not required in Sprint 2 and has no field, so the screen has no Export control.
- The synthetic and mock marker is always visible, matching the shell banner.
- Slide-over closes with Escape and returns focus to the row. "Inspect queries" is present only for the RAG application.
- Narrow: the table scrolls inside its region; the slide-over becomes full height.
- Search focuses with `/`.

## SCR-TRX — Trace Explorer

Pattern: List. One Filters control; active values appear as chips. Row activation opens Trace Detail.

```
Traces
Every ingested trace. Filter to find the ones to inspect.
[Search traces …]  [Filters]  [Columns]
Application: Procurement ×   Reliability: Block ×   Evidence: Missing ×    [Clear all filters]
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Trace {TRX-01}  App {>APP-01}  Started {TRX-02}  Mode {TRX-04}   Outcome {>TRD-01}  Reliability {>TRD-03}
 tr-<id> ›       Procurement   <time> · <dur>    Live model       Blocked            ■ Reliability Block
 …                                                                  Class {>TRD-05}   Evidence {TRX-03}   Scenario {TRX-05}
                                                                    Workflow violation  Complete          <ref>
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Page <n> of <n>   [Previous] [Next]
```

Filters panel dimensions: application, time range, execution mode and scope, application outcome, run status, reliability decision (including No decision), failure class, evaluation state, evidence completeness, scenario run, version. Each is the value set of an existing field.

Notes:

- Default sort is newest first. Rows have a resting affordance (link-colored trace ID, chevron).
- `Evidence` shows Complete, Incomplete or Inconclusive (`TRX-03`). Incomplete traces carry the ✕ Missing evidence signature.
- Filtered empty: "No traces match your filters" with Clear all filters. First-use empty: "No traces yet" with Connect an application.
- Narrow: toolbar wraps; the table scrolls inside its region and keeps type at 12 px or larger.
- Search focuses with `/`.

## SCR-TRD — Trace Detail

Pattern: Detail. The header carries status and metadata. Nine sections sit in a sticky section navigation, because nine is past the limit for a tab row. Each section loads independently and owns its loading, empty and error states.

```
Traces › tr-<id>                                      [Record review]  [Open in RAG Diagnostics]  [⋯]
Procurement Agent · Live model · Started <time> · Evidence: Complete {>TRX-03}
┌─ Summary ───────────────────────────────────────────────────────────────────────────────────────┐
│ Outcome  {TRD-01}   Blocked            Run {TRD-02}  BLOCKED                                     │
│ ■ Reliability Block {TRD-03}  decided <time>        Class  Workflow violation {TRD-05}           │
│ Also found {TRD-06}: Unsupported completion                                                      │
│ Why {TRD-04}:  PROC-APPROVAL-01 failed ›  PROC-TOOL-STAGE-01 failed ›  False success claim ›    │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
 Summary        │ (section content)
 Timeline       │
 Request & model│
 Procurement ev.│
 Tools & enforce│
 Response       │
 Evaluation & dx│
 Human review   │
 Provenance     │
```

`[Record review]` appears only if the dashboard may write review records (Q-07). The "Why" items are links. Each opens the section that holds its evidence (see the evidence reachability budgets above).

### Section contents

| Section | Fields | What the reviewer must be able to tell |
|---|---|---|
| Summary | `{TRD-01}` `{TRD-02}` `{TRD-03}` `{TRD-04}` `{TRD-05}` `{TRD-06}` | Four separate statuses side by side: outcome, run, reliability decision, class. A waiting run is not a pass. Secondary findings sit next to the primary class. |
| Timeline | `{TRD-20}` `{TRD-21}` `{TRD-22}` `{TRD-23}` | Order of events and states, which transitions were attempted versus accepted, and the causal graph. The ordered list is primary; the graph is an optional view with the same content in text. |
| Request and model | `{TRD-10}` `{TRD-11}` `{TRD-12}` `{TRD-13}` `{TRD-14}` | What was asked, how it was normalized, and what the model was given and returned. A replay shows Not applicable for the model call, not an invented response. Unknown usage is Unavailable, never 0. |
| Procurement evidence | `{TRD-30}` `{TRD-31}` `{TRD-32}` `{TRD-33}` `{TRD-34}` `{TRD-35}` | Policy found, supplier status, approval required or not, and whether a valid approval was observed and bound. For a RAG trace this section is Not applicable and links to RAG Diagnostics. |
| Tools and enforcement | `{TRD-40}` `{TRD-41}` `{TRD-42}` `{TRD-43}` `{TRD-44}` `{TRD-45}` `{TRD-46}` | The proposal, the arguments, the pre-tool verdict, whether the tool ran, and the result. Proposal, verdict, ∅ Not executed and result are four separate rows. |
| Response | `{TRD-50}` `{TRD-51}` | The raw generated text and the delivered text side by side with which one was shown, plus the evidence supporting or contradicting any completion claim. |
| Evaluation and diagnosis | `{TRD-60}` `{TRD-61}` `{TRD-62}` `{TRD-63}` `{TRD-64}` `{TRD-65}` `{TRD-66}` | Each evaluator as value, ○ Not evaluated, ▲ Evaluator failed or ⊘ Not applicable. Ranked causes with links to events. Ground truth appears in its own collapsed, labeled block. |
| Human review and audit | `{TRD-70}` `{TRD-71}` | Machine decision history with versions, and any human review shown beside it, never over it. |
| Provenance and completeness | `{TRD-80}` `{TRD-81}` `{TRD-82}` | Exact versions used, what was redacted or unavailable, and which expected events are missing. |

### Tools and enforcement: approval-bypass example

```
Tools and enforcement
 1  Proposal {TRD-40}     create_purchase_order · catalog v… · proposal <id>        (from model call <id>)
 2  Arguments {TRD-41}    raw · parsed · trusted context (separate)      validation: ✓ passed
 3  Policy request {TRD-42}   proposal <id> · stage PRE_APPROVAL · state revision … · digest …
 4  Pre-tool verdict {TRD-43}  ⊣ Pre-tool Block
        ✕ PROC-APPROVAL-01   approval required, none received       [View approval evidence ›]
        ✕ PROC-TOOL-STAGE-01 tool not allowed at this stage
 5  Dispatch {TRD-44}     ∅ Not executed · execution_started: false      reason: blocked by 4
 6  Tool result {TRD-45}  ⊘ Not applicable — nothing ran
 7  Recovery {TRD-46}     ⊘ Not applicable
```

Notes:

- Row 6 says Not applicable because row 5 is positive evidence that nothing ran. If row 5 were absent, row 6 would read ✕ Missing evidence.
- Narrow: section navigation becomes a select at the top of the content; the summary tags wrap; wide tables scroll inside their region.

## SCR-RCA — Failure & RCA

Pattern: Analytics (analytical). The date range is first and always visible. One filter change updates every chart. At most five tiles. Single-trace diagnosis stays in Trace Detail.

```
Failure & RCA
Failure classes and root-cause patterns across traces.
[Date range ▾]  [Filters]                                                        Taxonomy {RCA-02}
┌─ Classes ─────────┐┌─ Pre-tool blocks ───┐┌─ No cause found ──┐┌─ Evaluator health ┐┌─ Decisions ──────┐
│ {RCA-01} top class││ {RCA-06}            ││ {RCA-04}          ││ {RCA-08}          ││ {RCA-07}         │
└───────────────────┘└─────────────────────┘└───────────────────┘└───────────────────┘└──────────────────┘
┌─ Failure class distribution {RCA-01} ───────────────────────────────────────────────────────────────┐
│ Eight classes plus Normal, by application. Text table alternative below.                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ Cause distribution {RCA-04} ──────────────┐ ┌─ Primary × secondary {RCA-03} ─────────────────────────┐
│ Nine fixed causes, evidence counts          │ │ co-occurrence table                                    │
└─────────────────────────────────────────────┘ └────────────────────────────────────────────────────────┘
┌─ Attempted · prevented · realized {RCA-05} ────────────────────────────────────────────────────────┐
│ ○ Not evaluated until the label semantics are agreed (OD-09)                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ Evaluator health {RCA-08} ────────────────────────────────────────────────────────────────────────┐
│ Evaluator   Evaluator failed   Not evaluated                                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ Examples {RCA-09} ────────────────────────────────────────────────────────────────────────────────┐
│ Class / cause   Trace {>TRX-01}   {>TRD-03}                                          [Open trace ›] │
│ [View traces]                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
Decisions by class {RCA-07}: table of Pass / Review / Block / No decision per class, for the Decisions tile
Class definitions {RCA-02}: glossary opened from any class label
```

Notes:

- Each tile headlines the section of the same field below it and scrolls to that section. Tiles do not leave the screen.
- Drilling into a class adds a chip and scrolls to Examples, which links on to Trace Explorer or Trace Detail (N-17, N-18).
- A cause with no supporting evidence is shown as a count of "No cause supported", not as a ranked cause.
- Narrow: filters stack; charts are full width; tables scroll inside their region.

## SCR-RAG — RAG Diagnostics

Pattern: Split Pane. A compact query list on the left. The inspector on the right holds the selected query. Selecting never changes route. Aggregate retrieval quality over time lives in Release Gate (`REL-04`), and failure patterns live in Failure & RCA.

```
RAG Diagnostics                                                                       [Open full trace]
Inspect retrieval, selected context, claims and citations for one query at a time.
[Search queries …]  [Filters]     [All] [Needs attention] [Abstained] [Errors]
┌─ Queries ───────────────────────┐ ┌─ Inspector ───────────────────────────────────────────────────────┐
│▸ <query text>                   │ │ Query | Retrieval | Context | Answer | Abstention                  │
│   {RAG-19} Abstention  ○ …      │ │ ───────────────────────────────────────────────────────────────  │
│  <query text>                   │ │ Query                                                              │
│   Answer       …                │ │  {RAG-01} raw · effective · transformation   {RAG-02} k · filters │
│  …                              │ │  {RAG-03} retriever · corpus · index · embedding   {RAG-20} …     │
└─────────────────────────────────┘ │ Retrieval   {RAG-04} Success · <n> returned (or Error)              │
                                    │  #1 doc-<id> chunk … score … rank 1   {RAG-05} {RAG-06}            │
                                    │  {RAG-09} expected: doc-<id> — not retrieved                       │
                                    │  {RAG-10} metrics: recall … ○ Not evaluated                        │
                                    │ Context     {RAG-07} selected <ranks> · rejected <ranks> (reasons) │
                                    │             {RAG-08} sufficiency: Insufficient evidence            │
                                    │ Answer      {RAG-19} Answer                                        │
                                    │  {RAG-11} candidate · delivered  {RAG-12} claims                   │
                                    │  claim c1 → {RAG-13} citation → [View source ›]                    │
                                    │  {RAG-14} structural: ✓ resolves   {RAG-15} support: ▲ Evaluator failed│
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
- Retrieved order (`RAG-05`, `RAG-06`) and selected order (`RAG-07`) are shown as two lists so a reviewer sees what was returned versus what the model saw.
- Retrieval error and an empty success are different: `RAG-04` shows "Error: {stage}" or "Success: 0 returned". An error is never shown as a zero metric.
- A structurally valid citation (`RAG-14`) and a supported claim (`RAG-15`) are shown on separate lines. The first never implies the second.
- `RAG-09` and `RAG-10` are reference and metric rows from evaluation. They are collapsed behind an "Evaluation reference" label and are never used as inputs. See Q-11.
- Narrow: the list is full width; tapping a query opens the same inspector full width on this route, with a Back to queries control. The pattern's "full Detail page" is deliberately not a second route, because that would duplicate the inspector (decision DX-04).

## SCR-REL — Release Gate

Pattern: Detail. One named gate evaluation (a candidate compared with a baseline). Six sections go in a sticky section navigation.

```
Release Gate › Candidate {REL-03}   vs   Baseline                                   [Select evaluation ▾]
■ Release gate Block {REL-01}   gate policy v… · evaluated <time>
┌─ Decision ──────────────────────────────────────────────────────────────────────────────────────────┐
│ Why {REL-02}:  <metric> regressed ›   <n> scenarios newly Block ›   Run incomplete (<n> cases) ›     │
│ Review {REL-16}: ▢ Not configured — no release review process is defined yet                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
 Decision          │ Metrics
 Metrics           │  Metric {REL-05}   Baseline   Candidate   Delta   n    State {REL-04}
 Version changes   │  <metric>          …          …           …       …    ▲ Evaluator failed
 Regressions       │  <metric>          <value>    …           …       …    Value
 Lineage & compl.  │  Threshold {REL-06}  ▢ Not configured (OD-15)
 History           │  A metric state is a value or one of the absence states.
```

Section contents:

| Section | Fields | What the reviewer must be able to tell |
|---|---|---|
| Decision | `{REL-01}` `{REL-02}` `{REL-03}` `{REL-16}` | The gate decision with its scope label, each reason as a link, and which two releases are compared. |
| Metrics | `{REL-04}` `{REL-05}` `{REL-06}` | Baseline versus candidate values with sample size and state. A missing threshold is ▢ Not configured, not a pass. |
| Version changes | `{REL-07}` `{REL-08}` | What changed between baseline and candidate, and which evaluation set was used. |
| Regressions | `{REL-09}` `{REL-10}` `{REL-11}` | Regressed and improved scenarios with links to the paired traces, the failure class shift, and enforcement changes. |
| Lineage and completeness | `{REL-12}` `{REL-13}` `{REL-14}` | Whether the run is complete, how to reproduce it, and whether the comparison is fixture-deterministic or live. |
| History | `{REL-15}` | Earlier gate evaluations, each opening this screen for that evaluation. |

Notes:

- Gate reasons (`REL-02`) link to the metric row, the regressed scenario or the completeness record they cite. This is the first step of the four-interaction budget.
- A gate that cannot be decided because required evidence is missing shows ✕ Missing evidence under Lineage and completeness and `◔ Awaiting result` or `▢ Not configured` as its decision, never a PASS.
- Narrow: the section navigation becomes a select; tables scroll inside their region.

## Keyboard, focus and viewport requirements

These apply to every screen. Wireframes do not repeat them.

| Area | Requirement |
|---|---|
| Skip link | First focusable element, "Skip to main content". |
| Tab order | Follows reading order. Section navigation and tab rows use arrow keys inside the group. |
| Focus ring | Visible on every interactive element: 2px offset, 3:1 contrast, in both themes. |
| Search | Present on List and Split Pane screens. `/` focuses it. |
| Overlays | Slide-overs trap focus, close with Escape, and return focus to the element that opened them. |
| Primary actions | All reachable without hover. Hover only adds extras. |
| Hit targets | 44 by 44 px minimum. Icon-only controls get padding to meet it. |
| Page overflow | None at 375 or 1280. Tables scroll inside their own region. Type stays at 12 px or larger. |
| Graph and charts | Each has a text or table alternative with the same content. |
| Destructive actions | None in scope. A future one needs a named-entity confirmation dialog with Cancel focused. |
