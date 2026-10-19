# Governance decision flow

| | |
|---|---|
| **Status** | DRAFT v0.2 — Sprint 1, task S1-04. Not frozen. No teammate has reviewed or signed off this document. |
| **Owner** | Mohamed Elnaggar — `packages/governance-engine` |
| **Reviewers** | Nour El-Rouby, Mohab Mohsen, Ahmed Ragab, Alaa Sayed, Malak Sayed |
| **Basis** | Proposal v1.1 §I, §K.2, §N.1, §Q, §R, §S and Figures 2–5; [repository architecture](../../../ARCHITECTURE.md); Sprint plan S1-04; the [reference-application contracts](../reference-applications/README.md) (revision 0.5) |
| **Companion** | [governance-contract.md](governance-contract.md) — field-level contracts, approval boundary, RBAC/audit register, open decisions, and the response to the S1-01 handoff checklist |

Source tags used in this document and its companion:

- **[P]** stated in the approved proposal.
- **[R]** stated in the approved repository architecture or sprint plan.
- **[N]** stated in Nour's reference-application contracts (revision 0.5). Those contracts are themselves still pending team sign-off.
- **[D]** DECISION — proposed by governance for review; not agreed until the named reviewers accept it.

Nothing described here is implemented. Sprint 1 produces contracts only; policy code starts in Sprint 2.

---

## 1. Three separate verdict layers

TrustOps produces three kinds of verdict. They answer different questions, run at different times, use different evidence and are stored separately. None can overwrite another.

| | Layer 1 — Pre-tool authorization | Layer 2 — Automated reliability decision | Layer 3 — Human review verdict |
|---|---|---|---|
| **Values** | `ALLOW`, `BLOCK` [P §I.2, §R] | `PASS`, `REVIEW`, `BLOCK` [P §K.2] | `ACCEPT`, `REVIEW`, `BLOCK` [P §R.2] |
| **Question answered** | May this proposed tool call execute now? | Is this trace (or release candidate) acceptable given all evidence? | Does a person accept, escalate or reject this result? |
| **When it runs** | Synchronously, after a tool proposal and before any tool body runs [P §I.3, N] | After the trace is stored; offline for release candidates [P §I.3] | On demand, after layer 2 [P §R.2] |
| **Target** | One tool proposal, bound to an immutable request/state snapshot [N] | A trace, or a release evaluation (baseline vs candidate) [P §S] | A trace or a release evaluation [P §R.2] |
| **Evidence it may use** | Runtime-supplied evidence, governance-owned approval records, versioned policy configuration | Policy findings, security findings, evaluator results, classifier output, RCA, baseline comparison, versioned decision configuration | The decision and its evidence as shown in the dashboard |
| **Evidence it must never use** | LLM output, semantic evaluators, classifier, RCA [P §I.3, §Q.1] | — (a critical policy/security failure always wins, §3) | — |
| **Binding** | `ALLOW` authorizes exactly one dispatch of exactly the evaluated snapshot [N] | n/a | References the decision it reviewed |
| **Module** | `trustops_governance/policy/` [R] | `trustops_governance/decision/` — "sole owner of PASS/REVIEW/BLOCK semantics" [R] | `trustops_governance/review/` [R] |
| **Stored as** | Policy check + per-policy findings | Reliability decision record | Review record |
| **Mutability** | Append-only [P §R.2] | Append-only; a re-run creates a new record [D] | Append-only [P §R.2] |

Two naming hazards to keep visible in code, API and UI:

- `BLOCK` and `REVIEW` appear in more than one layer. Every stored value must carry its layer (enum type and record type), never just a bare string. [D]
- Per-policy results use `PASS` / `FAIL` (matching the proposal's example traces, `policy_verdict.status` [P §J.1–J.2]). That `PASS` is a policy result, not a Layer 2 decision. The dashboard must label by layer; "pending approval" and "application completed" are never shown as reliability `PASS` [N]. [D]

---

## 2. Boundary map from Figures 2–5

### 2.1 Figure 2 — online pre-execution control vs post-run evaluation

```mermaid
sequenceDiagram
    participant A as Procurement Agent (runtime)
    participant I as Instrumentation SDK
    participant B as TrustOps Backend (apps/api)
    participant P as Policy Engine (governance-engine)
    participant S as PostgreSQL trace store
    participant E as Evaluators / Classifier / RCA (reliability-engine)
    participant D as Decision Engine (governance-engine)

    rect rgb(235, 245, 250)
    Note over A,P: ONLINE / PRE-EXECUTION CONTROL — Layer 1
    A->>I: emit model / retrieval / state / tool-proposal events
    I->>B: structured events + pre-tool check request (immutable snapshot)
    B->>P: evaluate(snapshot)
    P-->>B: ALLOW / BLOCK + per-policy findings + binding
    B-->>A: verdict (no verdict means no dispatch)
    Note over A: on ALLOW the runtime verifies the binding and claims dispatch once
    end

    A->>I: emit dispatch / tool result / final-response events
    I->>B: complete trace + version metadata
    B->>S: persist trace

    rect rgb(245, 240, 232)
    Note over B,D: POST-RUN RELIABILITY EVALUATION — Layer 2
    B->>E: load trace, run evaluators
    E-->>B: evaluator results, failure label + confidence, Top-1/Top-3 RCA
    B->>D: decide(evidence bundle incl. policy/security verdicts)
    D-->>B: PASS / REVIEW / BLOCK + decision path
    B->>S: persist decision (append-only)
    end
```

What this fixes for governance [P Fig. 2, §I.2; N]:

- The check happens **after** the agent proposes a tool call and **before** any tool body runs. Early or model-generated proposals are checked at whatever stage they occur, not only the valid path.
- The check evaluates one immutable snapshot of the proposal. On the valid path that is the `APPROVED` snapshot taken when `create_purchase_order` is proposed.
- Enforcement of "do not dispatch without a matching `ALLOW`" lives in Nour's runtime; correctness of the verdict lives in the governance engine.
- Policy/security verdicts flow into Layer 2 as evidence (the dashed "Policy / security verdict" flow in the figure).
- Semantic evaluators, XGBoost and RCA sit only on the post-run side. They cannot influence Layer 1.

### 2.2 Figure 3 — approval-bypass scenario (the flagship demo)

Evidence ids refer to the [application-to-trace evidence matrix](../reference-applications/trace-evidence-contract.md).

| Figure 3 element | What happens | Owner | Governance record |
|---|---|---|---|
| Policy retrieval — POL-114 | Retrieved policy text says approval is required above the threshold | Nour (E03) | Provenance only; the versioned configuration, not the text, is the authority [N] |
| Agent state | `approval_required=true`, `approval_received=false`, stage `PRE_APPROVAL` | Nour (E09, E10, E14) | Policy input |
| Proposed tool call | `create_purchase_order` proposed while in `PRE_APPROVAL` | Nour (E15) | The proposal identity keys the check |
| `PROC-APPROVAL-01` | Governance derives that approval is required and finds no valid approval | Mohamed | `FAIL`, critical |
| `PROC-TOOL-STAGE-01` | `create_purchase_order` is not on the `PRE_APPROVAL` allowlist | Mohamed | `FAIL`, critical [D] |
| `BLOCK` → "Tool execution BLOCKED" | Dispatch suppressed: `NOT_EXECUTED`, `execution_started=false`, no successful tool result (E19) | Nour obeys, Mohamed decides | Layer 1 verdict `BLOCK` |
| Final response "Purchase order was created" | Contradictory completion claim | Ahmed | **Not a policy verdict** — an `UNSUPPORTED_COMPLETION` evaluator finding that enters Layer 2 as evidence |
| Final reliability decision | `BLOCK` because of a critical policy failure | Mohamed | Rule `DEC-1` (§3) |

[D] The figure labels only `PROC-APPROVAL-01`, but §N.1 step 15 runs "`PROC-APPROVAL-01` / tool-stage policy check", and this scenario violates both rules. The engine evaluates every applicable policy and records every finding even when the first one already forces `BLOCK`, so diagnosis stays complete. Only the *side effect* is short-circuited, never the evidence.

[D] A policy `FAIL` records that an unsafe action was **attempted**. Whether it was **prevented** or **realized** is shown by the dispatch evidence (E19/E20), not by the policy result. `DEC-1` fires on the critical finding either way, which matches the figure (blocked action, final `BLOCK`). How the failure label treats attempted versus prevented violations is Ahmed's decision (GD-16).

### 2.3 Figure 4 — evidence to decision

The decision node has three exits [P Fig. 4]:

| Exit | Meaning in the figure | Layer 2 value |
|---|---|---|
| Acceptable evidence | No critical issue, within tolerance | `PASS` |
| Uncertain / borderline | Needs a human | `REVIEW` |
| Critical violation / regression | Unsafe or clearly worse | `BLOCK` |

"Critical policy/security flags" are part of the structured evidence that feeds the decision [P Fig. 4], alongside evaluator output, classifier label and RCA.

### 2.4 Figure 5 — the same decision logic at release time

| Gate verdict in figure | Layer 2 value | Behavior |
|---|---|---|
| Critical checks pass | `PASS` | Approve candidate |
| Marginal / uncertain regression | `REVIEW` | Human decision required; non-approving status [P §S.1] |
| Critical policy, security or quality regression | `BLOCK` | Reject candidate, retain approved baseline; no automatic rollback [P §S] |

The gate reuses the Layer 2 decision engine through `gate/decision_adapter.py` [R]. Alaa owns the runner and the GitHub Actions workflow; Mohamed owns the decision semantics. One versioned contract connects them, so the dashboard, backend and CI never disagree about what `BLOCK` means. [D]

### 2.5 Applicability beyond procurement

[D] The three approved policies are procurement-only [P §R]. The RAG assistant has no purchase tools or workflow stages, so it has no pre-tool check. A RAG trace's policy evidence is recorded as `NOT_APPLICABLE`, never as `PASS`, and the decision engine treats it as absent evidence, not proof of compliance. This answers the procurement-only applicability question (D5 / OD-16) and is tracked as GD-17.

---

## 3. Layer 2 precedence

The six approved conditions [P §K.2], expressed as ordered rules. Rule ids are Mohamed's labels [D].

| Rule | Condition | Decision | Needs a numeric threshold? |
|---|---|---|---|
| `DEC-1` | Any critical policy failure, or any critical security finding | `BLOCK` | No |
| `DEC-2` | No `DEC-1`, and a severe quality regression on a critical metric versus the approved baseline | `BLOCK` | Yes — pre-agreed severe-regression threshold [P §S.3] |
| `DEC-3` | No `BLOCK`, and borderline semantic quality | `REVIEW` | Yes |
| `DEC-4` | No `BLOCK`, and strong evaluator disagreement | `REVIEW` | Yes |
| `DEC-5` | No `BLOCK`, and low classifier certainty | `REVIEW` | Yes |
| `DEC-6` | No `BLOCK`, no `REVIEW` condition, and metrics within approved-baseline tolerance | `PASS` | Yes |

Notes:

- **Release target [P §S.3].** `DEC-1` also covers "a candidate introduces a critical mandatory-policy failure, or allows a seeded unsafe action that the approved baseline prevented".
- **No invented thresholds.** Exact tolerances are set only after approved-baseline distributions are measured [P §K.2, §S.3] (OD-15). They live in `config/decision_thresholds.yaml` as versioned values supplied through Alaa and Ahmed's measurements. The engine refuses to evaluate a threshold-based rule without an approved configuration version; it never falls back to a silent default.
- **`DEC-1` needs no threshold.** `BLOCK` for a critical policy/security failure is reachable from the first sprint, before any baseline exists. [D]
- **All conditions are evaluated, not just the first match.** The decision is the most severe outcome (`BLOCK` > `REVIEW` > `PASS`), and every condition that fired is recorded in order, so the decision path is explainable. [D]
- **Favorable signals cannot rescue a critical failure.** High classifier confidence, a good semantic score or a clean RCA never changes the result of `DEC-1`; an explicit conflict test covers it. [P §K.2]

---

## 4. Invariants

These hold for every downstream implementation choice. Each is a test target.

| Id | Invariant | Source |
|---|---|---|
| `INV-1` | The Layer 1 verdict is computed only from runtime-supplied evidence, governance-owned approval records and versioned policy configuration. No LLM output, semantic score, classifier or RCA result is an input. | [P §I.3, §Q.1; N] |
| `INV-2` | A critical policy or security failure yields `BLOCK` regardless of any other signal. | [P §K.2] |
| `INV-3` | Fail closed. Missing mandatory evidence, a governance error or an unknown state never yields `ALLOW` or `PASS`, and never fabricates a policy violation. It is recorded as an evaluation error. | [N] |
| `INV-4` | Human review appends a record. It never edits the machine decision or any earlier review. "Latest review" is a query, not a mutation. | [P §R.2] |
| `INV-5` | Every check, decision and review records the policy-set or decision-configuration version and references the evidence it used, so it can be reproduced. | [P §H] |
| `INV-6` | Policy, decision, review and audit records are append-only: no update or delete path exists in the repository interface. | [P §H, §R.2] |
| `INV-7` | A proposed tool call, a policy check, a dispatch suppression and an executed tool call are distinct records. A `BLOCK` leaves no successful tool result. | [N] |
| `INV-8` | The policy result is separate from the trace. Original trace events are never edited to make a run look compliant. | [D] |
| `INV-9` | An `ALLOW` is valid only for the exact snapshot it evaluated and authorizes one dispatch. Any change to the bound inputs, any other intervening state transition, or reuse of the authorization requires a fresh check. | [N] |
| `INV-10` | Governance derives the approval requirement itself from the configured rule. The application's `approval_required` flag is kept for diagnostics and is never the authority. | [D], following [N] "no independent second policy engine in the app" |

Enforcement is split: governance defines the binding and evaluates the policies; the runtime atomically verifies the binding and claims the dispatch (GD-07).

---

## 5. Failure behavior (safe by default)

Rows are [D] unless tagged otherwise. They are proposals for Nour and Mohab to ratify (GD-05, GD-09).

### 5.1 Layer 1 — pre-tool check

"Mandatory evidence" means the inputs needed to *decide* a policy. A missing approval when approval is required is a decidable fact (a violation), not missing evidence.

| Situation | Per-policy status | Overall verdict | Basis | What the caller must do |
|---|---|---|---|---|
| All applicable policies satisfied | `PASS` / `NOT_APPLICABLE` | `ALLOW` | all satisfied | May dispatch once, after verifying the binding |
| Any applicable policy violated | `FAIL` | `BLOCK` | policy violation | Must not dispatch |
| Approval required but none valid (missing, pending, denied, cancelled, bound to a different revision/amount/supplier/level, or decided after the proposal) | `FAIL` | `BLOCK` | policy violation | Must not dispatch |
| Proposed tool not on the allowlist of the current stage | `FAIL` | `BLOCK` | policy violation | Must not dispatch |
| Supplier status is not `APPROVED` (including not found) | `FAIL` | `BLOCK` | policy violation | Must not dispatch |
| Mandatory evidence missing or malformed (unparseable amount, unsupported currency, no supplier evidence, lookup error) | `ERROR` | `BLOCK` | evaluation error | Must not dispatch; this is not a policy violation |
| Stage unknown, or policy configuration missing | `ERROR` | `BLOCK` | evaluation error | Must not dispatch |
| Policy version reported by the application differs from the active version | check error | `BLOCK` | evaluation error | Must not dispatch; the application re-derives its evidence under the active version [N: "mismatched versions … cannot authorize dispatch"] |
| Governance module raises an exception | none | none returned | — | No verdict means no dispatch [N] |
| Governance call times out or is unreachable | none | none received | — | No verdict means no dispatch; recorded as a technical check error, not a policy `FAIL` or `ALLOW` [N] |
| Snapshot changed after `ALLOW` (arguments, evidence, revision, or another state transition) | — | authorization invalid | — | Must not dispatch; fresh check required [N, `INV-9`] |
| Same check request replayed (same trace and proposal) | unchanged | original verdict | — | Returns the original result; never a second authorization |
| Conflicting resubmission for the same proposal | — | rejected | — | Does not overwrite the original; mirrors the replay rule planned for trace ingestion (S2-02) |

### 5.2 Layer 2 — post-run decision

| Situation | Result |
|---|---|
| All required evidence present and a rule fires | The decision per §3 |
| Critical policy/security failure present, other evidence incomplete | `BLOCK` — `DEC-1` needs no other evidence |
| Required evaluator/classifier output missing, or an evaluator failed, and no critical failure is known | **Not `PASS`.** Recorded as an incomplete evaluation with the list of missing evidence; the gate treats it as non-approving. Stored representation is open (GD-13). |
| Threshold configuration missing or unapproved | Threshold-based rules are not evaluated; same incomplete handling |
| Critical policy result is `ERROR` (compliance could not be confirmed) | Never treated as compliant; representation is part of GD-13 |
| RAG trace (no applicable policy) | Policy evidence `NOT_APPLICABLE`; absent, not `PASS` (§2.5) |
| Re-run on the same trace | New decision record with its own evidence-run ids; earlier decisions stay intact |

---

## 6. How this document is checked (S1-04 tests)

Status: **not yet satisfied.** These are the acceptance checks from the sprint plan, to be ticked only after the reviews happen.

- [ ] **Traceability.** Every policy input and output has an identified producer and consumer — register in [governance-contract.md](governance-contract.md) §3.
- [ ] **Structural review.** The pre-tool path (§2.1, Layer 1) and the post-run path (§2.1, Layer 2) are structurally distinct, reviewed by Nour and Mohab.
- [ ] **Non-overwrite.** Human review and machine decision are separate, non-overwriting records (`INV-4`), confirmed by Malak and Alaa for the UI and gate.
- [ ] **Circulation.** Contract circulated to and acknowledged by Nour, Mohab, Ahmed, Alaa and Malak.
