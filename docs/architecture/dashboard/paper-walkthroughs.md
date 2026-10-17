# Paper walkthroughs and coverage check

Revision 0.2 · 2026-10-17 · DRAFT. Part of the [dashboard UX architecture](README.md).

Two checks back the architecture: a coverage check (every field or decision maps to exactly one screen and one owner) and a paper walkthrough (a reviewer can reach supporting evidence from any failed trace or blocked gate within the proposed navigation).

## Coverage check

An automated check runs in the Python CI contract tests: [test_dashboard_information_architecture.py](../../../tests/contract/test_dashboard_information_architecture.py). It reads the documents in this folder.

| Property | How it is checked |
|---|---|
| Seven screens, as the proposal names them | The screens table lists exactly the seven names of proposal section T, in order; the matrix and the wireframes each have exactly the seven `SCR-` sections |
| One screen per field | Field IDs are unique, and each ID's prefix matches the section it sits in |
| One owner per field | The owner cell holds exactly one of Nour, Ahmed, Mohab, Mohamed, Alaa; each owner owns at least one field |
| Every evidence requirement covered | All 27 rows E01 to E27 of the [trace evidence contract](../reference-applications/trace-evidence-contract.md) appear in the Source column of at least one field |
| Every field is placed | Each field has a home marker on its own screen's wireframe |
| No field has two homes | A home marker appears only on the screen that owns the field; projections only on other screens |
| No dangling references | The wireframes, journeys, story traceability and this page cite only field IDs and edge IDs that exist |
| Every story traced | Each of US-34 to US-40 has rows in the story traceability page, each citing fields or edges |
| Access table matches the source | The Manage and View table equals Appendix B.2 of the user stories, for all seven roles and seven dashboards |
| Absence states defined | Every absence code used in the matrix is defined in the status vocabulary |
| Not colour alone | Every state in the vocabulary has a text label, a glyph, an outline and a fill, and no two states share a glyph or a signature |
| Navigation reachability | Every primary screen reaches Trace Detail within two contextual links, and Release Quality Gate within one |
| Review record | All five owners are listed, and none is marked reviewed without evidence |

Result for revision 0.2: see the pull request for the exact commands and output. The check proves the documents are consistent with each other and with the transcribed Appendix B. It does not prove the design is right.

What the check does not cover, and who covers it:

| Gap | Covered by |
|---|---|
| Whether each owner agrees they own a row | Owner reviews (pending) |
| Whether a row's wording matches what the backend will serve | Mohab's S1-02 mapping, later typed contracts |
| Whether the wireframes are usable, and the US-38 task-based review | Independent walkthrough, later prototype review |
| Contrast, focus and screen reader behaviour | Accessibility review once visual design and code exist |
| The shared review checklist (Frontend README section 10) | Q-01: the document is not in the repository |

## Paper walkthrough method

The author walked each path on the wireframes in [information-architecture.md](information-architecture.md), counting one interaction per click, tap or keyboard activation, and checking that the evidence at the end is the evidence the question needs. The budgets are design targets. No interface exists to measure.

Performed by: Malak (author), on paper, against revision 0.2. **An independent walkthrough by a second person is still pending**, and is part of the S1-07 closeout.

Budgets, counted from the screen that shows the failed or blocked item:

| Starting point | Budget to the supporting event |
|---|---|
| A trace row (Trace Explorer, Failure & RCA queue) | 3 interactions or fewer; 2 from the Failure & RCA queue |
| An Overview count, class or application card | 4 interactions or fewer |
| A claim in the RAG inspector | 2 interactions or fewer to the source snapshot |
| A blocked release gate | 4 interactions or fewer |

## Walkthroughs

| # | Start | Failed or blocked item | Path | Interactions | Budget | Result |
|---|---|---|---|---|---|---|
| W1 | Failure & RCA queue (Governance Reviewer landing) | Reliability Block, approval bypass | Select the trace, follow the evidence link on the top cause (N-17) | 2 | 2 | Reaches the pre-tool verdict and dispatch status in Trace Detail |
| W2 | Trace Explorer, filtered to Block | A blocked procurement trace | Open the row (N-10), open the investigation (N-13), follow an evidence link (N-17) | 3 | 3 | Reaches the same evidence from the list |
| W3 | Overview, top failure classes tile | A workflow violation | Open the class (N-02), open a row (N-10), open the investigation (N-13), follow an evidence link (N-17) | 4 | 4 | Reaches the evidence from the glance screen |
| W4 | Applications card | Failures of one application | View failures (N-09), select a trace, follow an evidence link (N-17) | 3 | 4 | Reaches the evidence from the registry |
| W5 | RAG Diagnostics | A claim not supported by its cited source | Select the claim, open its citation source (`RAG-18`) | 2 | 2 | Reaches the immutable source text with the cited span |
| W6 | RAG Diagnostics | A failing query, to its diagnosis | Open the investigation (N-21), follow an evidence link (N-17) | 2 | 3 | Reaches the evaluator finding and the event it cites |
| W7 | Release Quality Gate, Decision | Release gate Block | Open a gate reason, open the critical scenario's candidate trace (N-24), open the investigation (N-13), follow an evidence link (N-17) | 4 | 4 | Reaches trace evidence for the regression |
| W8 | Overview evaluation tile | Evaluator failed traces | Open the Evaluator failed count (N-05), open a row (N-10), open Evaluator outputs (`TRD-61`) | 3 | 4 | Reaches the evaluator error |
| W9 | Trace Explorer | A trace with Missing evidence | Open the row (N-10), open Provenance and completeness (`TRD-82`) | 2 | 3 | Reaches the list of expected events that did not arrive |
| W10 | Release Quality Gate | A Block the LLMOps Engineer wants to override | Request override, submit reason; a Governance Reviewer opens the request, approves behind the named confirmation | 2 and 3 | none set | Both steps appear in `REL-19` and `REL-20` |

All reach their evidence within budget on paper.

## Findings raised while drafting and how the architecture handles them

Each is already reflected in revision 0.2. They are listed so reviewers can challenge the fix.

| # | Finding | Resolution |
|---|---|---|
| WF-1 | Not evaluated and Evaluator failed traces had no short path from the Overview coverage tile. | N-05 opens Trace Explorer filtered to the evaluation state. |
| WF-2 | Failure & RCA, as first drawn, showed distributions with no route to the diagnosis of one trace, which US-39 requires. | Rebuilt as a queue plus per-trace investigation with evidence links on every cause, rule and finding (N-17). |
| WF-3 | "Supporting evidence" from a blocked trace depends on each rule-path and cause item linking to an event. No source says the decision and RCA engines return such references. | `RCA-06` and `RCA-08` are defined as linked lists. Q-03, Q-06 and Q-08 ask Mohab, Mohamed and Ahmed for the reference format. |
| WF-4 | A blocked gate had no defined path to individual traces. | `REL-09` and `REL-11` carry paired trace links (N-24); the gate budget is 4. |
| WF-5 | A missing tool result could mean suppressed or unknown. | `∅ Not executed` is positive evidence; a missing result with no suppression record is ✕ Missing evidence. Rule in the vocabulary and the bypass example. |
| WF-6 | `BLOCK` and `REVIEW` name several different things. | Mandatory scope labels, distinct glyphs for machine states and plain text tags for human verdicts (DX-03). |
| WF-7 | A tool can be stopped by the agent guard (US-03) or by the pre-tool policy check (US-22), and the two must not be confused. | `TRD-44` names the layer and `TRD-47` holds the guard rejection as its own event. |
| WF-8 | A split-pane screen's narrow rule would open a second detail route. | Same route, full width, with Back (DX-04). |
| WF-9 | A review needs to be submitted from two screens, and Appendix B gives the Governance Reviewer only View on Trace Detail. | Action-level permission assumed; Q-07 asks Mohamed. |

## Known risks and what would change the design

| Risk | Effect | Owner of the answer |
|---|---|---|
| The Frontend README defines wireframes or checks that differ | Screens or checks change | Q-01 |
| The decision engine cannot return a linked rule path | Evidence budgets for blocked traces grow by a step | Q-06 |
| Execution graph is not available as nodes and edges | Timeline falls back to the ordered list, which is already primary | Q-03 |
| Ground truth must be hidden from reviewers | `RCA-11` moves behind a role or is removed | Q-11 |
| The Manage actions of Appendix B become required screens controls | Wireframes gain controls and fields | Q-13 |
| Typed contracts rename or split rows | The matrix is updated with the same IDs; the check keeps the documents aligned | Mohab, S1-02 |
