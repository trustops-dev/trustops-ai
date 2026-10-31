# Open decisions: both options kept

Dashboard UX architecture · Owner: Malak · Revision 0.4 · 2026-10-19

This page exists so the dashboard design does not wait for the backend owners. For each open decision it keeps **both options**, says which one the design builds on today, and says what changes if the owners pick the other. Sprint 2 can start on this page.

**This is Malak's working decision, not an owner acknowledgement.** The owners have not replied. Their rows in the [owner review record](README.md#owner-review-record) stay PENDING. When an owner decides, the cost is the small change listed under each option, not a redesign.

## Decision 1: who produces the release gate verdict (Q-10)

The verdict is the PASS, REVIEW or BLOCK shown on the Release Quality Gate screen (`REL-01`, `REL-02`).

| | Option A: Mohamed's decision engine (building on this today) | Option B: Alaa's gate module |
|---|---|---|
| Source | The governance decision flow (§2.4) runs one engine for a trace and for a release evaluation. Alaa's gate runner calls it. | Alaa's `gate_rules.py` computes the verdict, using Mohamed's decision semantics. |
| Owner of `REL-01`, `REL-02` | Mohamed | Alaa |
| Owner of comparison, artifact, disposition (`REL-04`, `REL-17`, `REL-18`) | Alaa | Alaa |
| Override requests and audit (`REL-19`, `REL-20`) | Mohamed | Mohamed |

**What stays the same on screen:** the verdict, the thresholds, the failing checks, the evidence links and the scope label "Release gate BLOCK". The screen reads one verdict value. It does not care which module wrote it.

**What changes if B wins:** the owner column of `REL-01` and `REL-02` in the [matrix](field-owner-matrix.md), and who is asked about them. No screen, no state and no wording changes.

**Thresholds while OD-15 is open:** show the threshold value next to each check when the backend sends it. When it is not sent, show "Threshold not provided" and never invent a number.

## Decision 2: which names are canonical (Q-15)

The S1-01 contracts, the governance contract and Trace Schema v1 spell the same ideas differently. The design handles all three with **one display map**: the screen shows a plain label, and the map says which raw values produce it. If an owner picks one draft, only the map is edited.

Rules that apply to every row below:

1. **Match without regard to case.** `approved` and `APPROVED` are the same value.
2. **Never drop an unknown value.** An unmapped value is shown as received, with the tag "Unmapped value", so a new backend value is visible instead of lost.
3. **Never infer a meaning that was not sent.** A missing value is "Not recorded", not Pass and not Not applicable.

### Run outcome

| Dashboard label | S1-01 run status | Schema v1 trace `execution_status` | Schema v1 tool `execution_status` |
|---|---|---|---|
| In progress | ACTIVE | — | — |
| Waiting for approval | WAITING_APPROVAL | — | — |
| Recovery pending | RECOVERY_PENDING | — | — |
| Succeeded | SUCCEEDED | completed | SUCCESS |
| Blocked by policy | BLOCKED | blocked_by_policy | BLOCKED_BY_POLICY |
| Abstained | — | abstained | — |
| Failed | FAILED | runtime_error | RUNTIME_ERROR, VALIDATION_ERROR |
| Timed out | — | — | TIMEOUT |
| Cancelled | CANCELLED | — | — |

Schema v1 uses the name `execution_status` twice, once for the trace and once for a tool call, with different values. The screen keeps them apart: the trace value goes in the trace header, the tool value on the tool row.

### Approval status

| Dashboard label | Governance contract | Schema v1 |
|---|---|---|
| Pending | PENDING | PENDING |
| Approved | APPROVED | approved |
| Denied | DENIED | not listed |
| Cancelled | CANCELLED | not listed |
| Not required | NOT_REQUIRED | not listed |

### Pre-tool verdict

| Dashboard label | Governance contract | Schema v1 |
|---|---|---|
| Pre-tool ALLOW | ALLOW | ALLOW |
| Pre-tool BLOCK | BLOCK | BLOCK |
| Pre-tool BLOCK: check error | a missing verdict also stops the call (§5.1) | ERROR_BLOCK |

The check error is never shown as a policy result.

### Per-policy result

| Governance contract | Schema v1 | Dashboard shows |
|---|---|---|
| PASS, FAIL, NOT_APPLICABLE, ERROR | a pass boolean | Pass, Fail, Not applicable, Error. From a boolean only: true is Pass, false is Fail, and Not applicable or Error are never guessed. |

### Blocked call: is there a result event?

| | Option A: Schema v1 (a result event exists) | Option B: S1-01 (no result event) |
|---|---|---|
| Row 7 of Trace Detail shows | "Blocked, no side effect committed", with the tool status BLOCKED_BY_POLICY | "Blocked before dispatch", with no result row and no invented result |

Both are already described in the [information architecture](information-architecture.md). The screen picks the wording from what the trace contains.

### Workflow stage names and abstention reasons

- **Stages.** Show the stage exactly as received, in readable form (for example `PRE_APPROVAL` as "Pre approval"). The mapping from S1-01 states to the nine Schema v1 stages is ratified by Mohamed and Mohab (GD-02, D3). Until then no screen depends on a particular set of stage names.
- **Abstention reasons.** Schema v1 lists `NO_RELEVANT_DOCUMENTS`, `INSUFFICIENT_CONTEXT_CONFIDENCE`, `OUT_OF_DOMAIN_QUERY` and `POLICY_OR_SAFETY_REFUSAL`. Show each as readable text. Any other value follows rule 2.

## Other open questions: working defaults

These do not block the design. Each has a default the design uses now, and a note on what changes if the owner answers differently.

| Question | Default used now | If the owner differs |
|---|---|---|
| Q-06 incomplete evaluation | Show "Incomplete evaluation" with the list of missing evidence. Never show PASS. | Change the wording only. |
| Q-07 who may submit a review | Treat "submit a review" as an action permission on Trace Detail. | The button is hidden for other roles. |
| Q-11 ground truth | Show injected labels only in the Release Quality Gate diagnostic panels, to roles that already see that screen. | The panels move behind a stricter role. |
| Q-13 Manage actions | None of them are in the seven screens. | Add the actions the plan owner confirms. |
| Q-14 login and account management | Outside the seven screens. | Add a separate area, not an eighth screen. |

The remaining questions (Q-01 to Q-05, Q-08, Q-09, Q-12) ask an owner to confirm fields they already own. The matrix assumes the answer is yes.
