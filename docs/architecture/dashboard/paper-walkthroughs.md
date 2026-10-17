# Paper walkthroughs and coverage check

Revision 0.1 · 2026-10-17 · DRAFT. Part of the [dashboard UX architecture](README.md).

Two checks back the architecture: a coverage check (every field and decision maps to exactly one screen and one owner) and a paper walkthrough (a reviewer can reach supporting evidence from any failed trace or blocked gate within the proposed navigation).

## Coverage check

An automated check runs in the Python CI contract tests: [test_dashboard_information_architecture.py](../../../tests/contract/test_dashboard_information_architecture.py). It reads the documents in this folder.

| Property | How it is checked |
|---|---|
| Seven screens, no more | The matrix and the wireframes each have exactly the seven `SCR-` sections |
| One screen per field | Field IDs are unique, and each ID's prefix matches the section it sits in |
| One owner per field | The owner cell holds exactly one of Nour, Ahmed, Mohab, Mohamed, Alaa; each owner owns at least one field |
| Every evidence requirement covered | All 27 rows E01 to E27 of the [trace evidence contract](../reference-applications/trace-evidence-contract.md) appear in the Source column of at least one field |
| Every field is placed | Each field has a home marker on its own screen's wireframe |
| No field has two homes | A home marker appears only on the screen that owns the field; projections only on other screens |
| No dangling references | The wireframes, journeys and this page cite only field IDs and edge IDs that exist |
| Absence states defined | Every absence code used in the matrix is defined in the status vocabulary |
| Not colour alone | Every state in the vocabulary has a text label, a glyph, an outline and a fill, and no two states share a glyph or a signature |
| Navigation reachability | Every primary screen reaches Trace Detail within two contextual links, and Release Gate within one |
| Review record | All five owners are listed, and none is marked reviewed without evidence |

Result for revision 0.1: the 13 checks pass locally, and the test file is clean under the repository's pinned `ruff` (lint and format) and strict `mypy`. The check proves the documents are consistent. It does not prove the design is right.

What the check does not cover, and who covers it:

| Gap | Covered by |
|---|---|
| Whether each owner agrees they own a row | Owner reviews (pending) |
| Whether a row's wording matches what the backend will serve | Mohab's S1-02 mapping, later typed contracts |
| Whether the wireframes are usable | Independent walkthrough, later prototype review |
| Contrast, focus and screen reader behaviour | Accessibility review once visual design and code exist |

## Paper walkthrough method

The author walked each path on the wireframes in [information-architecture.md](information-architecture.md), counting one interaction per click, tap or keyboard activation, and checking that the evidence at the end is the evidence the question needs. The budgets are design targets. No interface exists to measure.

Performed by: Malak (author), on paper, against revision 0.1. **An independent walkthrough by a second person is still pending**, and is part of the S1-07 closeout.

Budgets, counted from the screen that shows the failed or blocked item:

| Starting point | Budget to the supporting event |
|---|---|
| A row showing a failed, REVIEW or Block trace | 3 interactions or fewer |
| A claim in the RAG inspector | 2 interactions or fewer to the source snapshot |
| A blocked release gate | 4 interactions or fewer |

## Walkthroughs

| # | Start | Failed or blocked item | Path | Interactions | Budget | Result |
|---|---|---|---|---|---|---|
| W1 | Overview needs-attention list | Reliability Block, approval bypass | Open the row (N-01), follow the rationale item "PROC-APPROVAL-01 failed" to Tools and enforcement, follow "View approval evidence" to `TRD-34` | 3 | 3 | Reaches the approval observation and the verdict |
| W2 | Trace Explorer, filtered to Block | A blocked procurement trace | Open the row (N-10), open a rationale item, follow its evidence link | 3 | 3 | Reaches the pre-tool verdict and dispatch status |
| W3 | Failure & RCA, Workflow violation | An exemplar (`RCA-09`) | Open the exemplar (N-18), open a rationale item, follow its evidence link | 3 | 3 | Reaches the same evidence from the pattern view |
| W4 | RAG Diagnostics | A claim not supported by its cited source | Select the claim, open its citation source (`RAG-18`) | 2 | 2 | Reaches the immutable source text with the cited span |
| W5 | RAG Diagnostics | A failing query, to its full trace | Open full trace (N-20), open the rationale item | 2 | 3 | Reaches the evaluator results and ranked causes |
| W6 | Release Gate, Decision | Release gate Block | Open a gate reason, open the candidate trace of the regressed scenario (N-24), open a rationale item, follow its evidence link | 4 | 4 | Reaches trace evidence for the regression |
| W7 | Overview evaluation tile | Evaluator failed traces | Open the Evaluator failed count (N-05), open a row (N-10), open Evaluation and diagnosis (`TRD-61`) | 3 | 3 | Reaches the evaluator error |
| W8 | Trace Explorer | A trace with Missing evidence | Open the row (N-10), open Provenance and completeness (`TRD-82`) | 2 | 3 | Reaches the list of expected events that did not arrive |

All eight reach their evidence within budget on paper.

## Findings raised while drafting and how the architecture handles them

The walkthroughs and the drafting turned up these problems. Each is already reflected in revision 0.1; they are listed so reviewers can challenge the fix.

| # | Finding | Resolution |
|---|---|---|
| WF-1 | Not evaluated and Evaluator failed traces had no short path from the Overview coverage tile, so W7 took five interactions through Failure & RCA. | N-05 now opens Trace Explorer filtered to the evaluation state. N-17 also covers evaluator health rows. |
| WF-2 | Failure & RCA showed distributions with no route to examples. | Added `RCA-09` exemplar traces and the N-18 link. |
| WF-3 | "Supporting evidence" from a blocked trace depends on each rationale item linking to an event. No source says the decision engine returns such references. | `TRD-04` is defined as a list of linked findings and marked DECISION. Q-06 and Q-03 ask Mohamed and Mohab for the reference format. |
| WF-4 | A blocked gate had no defined path to individual traces. | `REL-09` carries paired baseline and candidate trace links (N-24); the gate budget is 4. |
| WF-5 | A missing tool result could mean suppressed or unknown. | `∅ Not executed` is positive evidence; a missing result with no suppression record is ✕ Missing evidence. Rule in the vocabulary and the bypass example. |
| WF-6 | `BLOCK` names three different things. | Mandatory scope labels and distinct glyphs (DX-03). |
| WF-7 | An application detail page would have been an eighth screen. | Slide-over summary on Applications (DX-02). |
| WF-8 | The Split Pane narrow rule opens a full detail page, which would duplicate the RAG inspector in Trace Detail. | Inspector stays on the same route at narrow (DX-04). |

## Known risks and what would change the design

| Risk | Effect | Owner of the answer |
|---|---|---|
| The proposal names a different seven screens | Field homes and edges move | Q-01 |
| The decision engine cannot return linked rationale | Evidence budgets for blocked traces grow by a step | Q-06 |
| Execution graph is not available as nodes and edges | Timeline falls back to the ordered list, which is already primary | Q-03 |
| Ground truth must be hidden from reviewers | `TRD-65` and `RAG-09` move behind a role or are removed | Q-11 |
| Typed contracts rename or split rows | The matrix is updated with the same IDs; the check keeps the documents aligned | Mohab, S1-02 |
