# Status vocabulary and non-colour encoding

Revision 0.2 · 2026-10-17 · DRAFT. Part of the [dashboard UX architecture](README.md).

The dashboard has to keep apart outcomes that look alike: a tool that was blocked, a run that is waiting, a check that never ran, a check that crashed, and a check that does not apply. This page fixes the vocabulary, the wording and a presentation signature for each state. A signature is built from a text label, a glyph, an outline and a fill. Colour is an extra cue and never the only one.

## Separate concepts

The [reference application overview](../reference-applications/overview.md#three-separate-outcomes) defines three outcomes plus a later human review. The proposal (sections K.2, R.2 and S) and the user stories (US-24, US-25, US-27, US-40) add the release gate, the human review verdict and the override. The dashboard adds evaluation states. Each concept has its own scope label, and the label is always shown with the value.

| Concept | Scope label | Values | Data owner | Fields |
|---|---|---|---|---|
| Reliability decision | Reliability | PASS, REVIEW, BLOCK | Mohamed | `RCA-07`, `OVW-04` |
| Release gate decision | Release gate | PASS, REVIEW, BLOCK | Alaa | `REL-01` |
| Candidate disposition | Candidate | Approved, baseline retained (BLOCK), human action required (REVIEW) | Alaa | `REL-18` |
| Pre-execution verdict | Pre-tool | ALLOW, BLOCK | Mohamed | `TRD-43`, `RCA-06` |
| Dispatch status | Dispatch | NOT_EXECUTED, executed (result shown separately); a suppressed call also names the layer that stopped it: agent guard or pre-tool policy | Nour | `TRD-44`, `TRD-47`, `TRD-45` |
| Application outcome | Outcome | Procurement: PO created, Waiting for approval, Blocked, Failed, Recovery pending. RAG: Answer, Abstention, Error | Nour | `TRD-01`, `RAG-19` |
| Run status | Run | ACTIVE, WAITING_APPROVAL, RECOVERY_PENDING, BLOCKED, FAILED, CANCELLED, SUCCEEDED | Nour | `TRD-02`, `APP-03` |
| Approval status | Approval | PENDING, APPROVED, DENIED, CANCELLED, NOT_REQUIRED | Mohamed | `TRD-34`, `TRD-35` |
| Evaluation state | Evaluation | value, Not evaluated, Evaluator failed, Not applicable | Ahmed | `TRD-60`, `OVW-05` |
| Human review verdict | Human review | ACCEPT, REVIEW, BLOCK, with a written rationale | Mohamed | `TRD-70`, `REL-16` |
| Override request | Override | Requested, Approved, Rejected | Mohamed | `REL-19` |

The values for each concept come from its owner. This table records what S1-01, the proposal and the user stories already name. The release gate row is a proposal until Alaa and Mohamed confirm it (Q-10). The absence states below are dashboard presentation states, not new backend enums.

### Rules that follow from the separation

1. **Scope label is mandatory.** `BLOCK` and `REVIEW` appear under several scopes. The UI always shows "Reliability BLOCK", "Release gate BLOCK", "Pre-tool BLOCK" or "Human review: Block", never a bare "BLOCK" or "REVIEW". The reliability, release gate and pre-tool states have different glyphs (table below). Human review verdicts and override states are plain text tags with no glyph, so a reviewer's verdict cannot be mistaken for a machine decision.
2. **A completed or pending run is not a PASS.** Outcome, Run and Approval tags never use the PASS badge, and nothing infers a PASS from them. A run waiting for approval shows Reliability: Awaiting result until Mohamed's engine decides.
3. **A pre-tool ALLOW is neither a success nor a PASS.** It means one proposed action could be dispatched. The invocation result is a separate field.
4. **A pre-tool BLOCK is not the end of the story.** The blocked proposal, the BLOCK verdict, `NOT_EXECUTED` and any false completion claim remain four visible, separate items. The attempt stays a finding.
5. **Human review never replaces a machine decision.** The reviewer's ACCEPT, REVIEW or BLOCK is shown next to the decision and the decision history, never in place of them. Reviews are never edited; a correction is a new entry.
6. **The UI never computes a decision.** It does not derive PASS from "no findings", REVIEW from "evaluator failed", a class from a policy result, or a cause order from its scores. Whatever the owner serves is shown, in the order served. The Top-3 causes keep the RCA engine's order, and their numbers are called "evidence scores", never probabilities.
7. **Every score says what it is.** A score, badge or finding shows its meaning, its unit and direction (higher is better, lower is better), its source and its applicable version. A bare number is never shown (Epic 7 Definition of Done, US-38).
8. **Two layers can stop a tool.** The agent guard (US-03) and the pre-tool policy check (US-22) each produce a Not executed result. The screen names the layer. A policy BLOCK is never shown for a call that only the agent guard stopped, and the reverse.

## Presentation signatures

Every reliability, enforcement, evaluation and absence state has a unique signature. Concepts that are plain text tags (Outcome, Run, Approval, Review) have no glyph, so they cannot be mistaken for the badges below. The labels are exact; the sentence-case spelling in the Label column is what users see.

| State | Scope label | Label | Glyph | Outline | Fill | Screen-reader text |
|---|---|---|---|---|---|---|
| PASS | Reliability | Pass | ✓ | solid | light | Reliability decision: pass |
| REVIEW | Reliability | Review | ◆ | double | hatch | Reliability decision: needs human review |
| BLOCK | Reliability | Block | ■ | heavy | solid | Reliability decision: block |
| ALLOW | Pre-tool | Allow | ▶ | solid | none | Pre-tool verdict: allow. The action could be dispatched |
| PRE_TOOL_BLOCK | Pre-tool | Block | ⊣ | heavy | none | Pre-tool verdict: block. The action was not dispatched |
| NOT_EXECUTED | Dispatch | Not executed | ∅ | dashed | none | Dispatch: not executed. No tool ran |
| NE | Evaluation | Not evaluated | ○ | dashed | none | Evaluation: not evaluated. No result exists |
| EF | Evaluation | Evaluator failed | ▲ | solid | hatch | Evaluation: evaluator failed. The result is unknown |
| NA | Evaluation | Not applicable | ⊘ | none | none | Not applicable. This does not apply here |
| PE | Status | Awaiting result | ◔ | solid | none | Awaiting result. It has not been produced yet |
| UN | Status | Unavailable | ? | dotted | none | Unavailable. The source did not supply it |
| ME | Status | Missing evidence | ✕ | dotted | hatch | Missing evidence. An expected event was not received |
| RD | Status | Redacted | ▒ | none | solid | Redacted. Withheld on purpose |
| NC | Status | Not configured | ▢ | dashed | light | Not configured. No value has been set |

Outline values: `solid`, `double`, `heavy`, `dashed`, `dotted`, `none`. Fill values: `none`, `light`, `hatch`, `solid`. Glyphs are placeholders that fix the silhouette family; the visual-design pass may swap an icon if its silhouette stays unique within this table. Wireframes use these glyphs.

### Which states are the four named in the task

| Task term | State | Why it needs its own signature |
|---|---|---|
| PASS / REVIEW / BLOCK | Reliability decision | Three outcomes of the post-run decision. REVIEW is not a soft pass. |
| Not evaluated | NE | No evaluator has produced a result. It is not zero, not a pass and not a failure. |
| Evaluator failed | EF | The evaluator ran and errored. The outcome is unknown, and it is not a pass or a finding. |
| Not applicable | NA | The check does not apply to this application or stage. It is expected, so it is not missing. |

## Absence states

When there is no value, the field shows exactly one of these. Each carries a reason from the owner, shown inline, and never an empty cell or a zero.

| Code | Label | Meaning | Reason shown | Next action | Counts toward a pass rate |
|---|---|---|---|---|---|
| NE | Not evaluated | No evaluator has produced a result | Which evaluator, and why not yet run | View evaluation status | No |
| EF | Evaluator failed | An evaluator ran and returned an error or timed out | Error category, evaluator run ID | View evaluator error | No |
| NA | Not applicable | The item cannot apply here (procurement rule on a RAG trace; approval not required; replay with no model call) | The rule that makes it inapplicable | See why | No |
| PE | Awaiting result | It will exist after a known event (approval decision, recovery lookup, decision engine run) | The event it waits for | Open pending step | No |
| UN | Unavailable | Applicable and expected, but the source did not supply it (provider usage, returned model version) | Source's reason | See why | No |
| ME | Missing evidence | A mandatory event is absent and the trace is incomplete or inconclusive | Which event is expected | View missing events | No |
| RD | Redacted | Withheld on purpose | Redaction reason and policy | See why | No |
| NC | Not configured | A threshold or policy value has not been set (OD-15) | What is unset and who owns it | Open thresholds | No |

Distinctions that must stay visible:

- **Not applicable versus Missing evidence.** Not applicable is expected and calm. Missing evidence is a defect in the trace and shows a count in the trace header.
- **Not executed versus Missing evidence.** `NOT_EXECUTED` is positive evidence that a call was suppressed. A missing tool-result event with no suppression record is Missing evidence. Absence of a result alone never proves non-execution (`E19`, `FM`).
- **Evaluator failed versus a finding.** A finding means the evaluator ran and found a problem. Evaluator failed means no verdict exists.
- **Genuine zero.** A real zero is shown as `0` with its unit, such as `0 findings` or `0 tokens used`. Unknown token usage is Unavailable, never `0` (`E02`).

## Rules for lists, counts and rates

1. A count shows every state separately. Not evaluated, Evaluator failed and Not applicable are never merged into an "other" bucket, and never into PASS or zero.
2. A rate shows its numerator, its denominator and what the denominator excludes, exactly as the owner serves it. The dashboard does not choose the exclusion policy.
3. Filters offer each state as its own choice, including "Awaiting result" and "Missing evidence".
4. Sorting places unknown states together and never below real zeros.
5. Charts carry a text table alternative. No chart encodes a state by colour alone.

## Accessibility requirements for the signatures

| Requirement | Rule |
|---|---|
| Not colour alone | Every state shows its text label plus a glyph, an outline style and a fill. Colour tone is an additional cue. WCAG 2.2 SC 1.4.1. |
| Contrast | Label text at least 4.5:1. Glyph and outline at least 3:1 against their surroundings, in light and dark themes. SC 1.4.3, 1.4.11. |
| Greyscale check | Reviewers can name every state when the screen is printed in greyscale. Checked on paper before visual design is signed off. |
| High-contrast and forced-colors modes | Outline style and glyph survive. Fill hatch may be dropped because label and glyph still distinguish states. |
| Screen readers | Accessible name is the screen-reader text above. Glyphs are decorative and hidden from assistive tech. |
| Keyboard | A badge that links is a real link or button, reachable by Tab, with a visible focus ring (2px offset, 3:1). A badge that does not link is not focusable. |
| Touch and pointer | A linking badge has a 44 by 44 px target. |
| Motion | No state relies on animation. Reduced-motion users get the same information. |

## Copy deck

Short, blame-free, and every message says what the state means and what to do. Verbs lead the action labels.

| State | Message | Action |
|---|---|---|
| Not evaluated | No evaluator has produced a result for this item yet. | View evaluation status |
| Evaluator failed | The evaluator did not return a result, so the outcome is unknown. This is not a pass. | View evaluator error |
| Not applicable | This check does not apply to {application or stage}. Reason: {reason}. | See why |
| Awaiting result | Waiting for {event}. This is not a pass. | Open pending step |
| Unavailable | The source did not supply this value. Reason: {reason}. | See why |
| Missing evidence | Expected evidence was not received: {event}. Whether the step ran is unknown. | View missing events |
| Redacted | Withheld by redaction policy {policy}. | See why |
| Not configured | {value} has not been set. Owner: {owner}. | Open thresholds |
| Pre-tool block with no dispatch | The proposed action was blocked before it ran. No tool executed. | View policy findings |
| Stopped by the agent guard | The agent's own workflow check rejected this call at stage {stage}. No tool executed. | View stage evidence |
| Release gate Block | The candidate is rejected and the approved baseline is retained. | View gate reasons |
| Release gate Review | A person has to decide. This is not an approval. | Record review |
| Permission refused | Your role cannot {action}. Ask a Governance Reviewer or Administrator. | View roles |

## Region states every screen defines

| State | Rule |
|---|---|
| Loading | A skeleton in the region's own footprint. No full-page spinner. Regions load independently, so a slow evaluator cannot hide the timeline. |
| First-use empty | A headline saying what belongs here, one sentence on its value, one verb-first link-out action. Inside the pattern's frame. Example: "No applications connected yet. Connect an application to see reliability decisions and evidence here." Action: Connect an application. |
| Filtered empty | "No traces match your filters" with a Clear all filters action. |
| Error | The region names what failed and offers Retry. Other regions stay usable. No blame wording. |
| Partial | Present evidence is shown; absent evidence uses an absence state. Never a blank panel. |
