# Owner review packet

Revision 0.4 · 2026-10-19 · Part of the [dashboard UX architecture](README.md).

This page is what each backend owner needs in order to review the dashboard field matrix. It is **prepared and not sent**. Nobody has been contacted, and no owner has acknowledged anything.

## What to send

Send each owner their section below, with the links to the [field matrix](field-owner-matrix.md) and the [information architecture](information-architecture.md). It takes three steps:

1. Open the matrix and find your rows. They are listed below, grouped by screen.
2. For each row, accept it or give the correction. Say if you are not the right owner.
3. Answer your questions, and reply with your name, the date, and the revision you reviewed (0.4).

The design does not wait for your reply. Q-10 and Q-15 keep both options in [open-decisions-both-options.md](open-decisions-both-options.md), so your answer can be as short as "keep A" or "keep B".

Row basis: `FACT` means a source requires it, `DECISION` means this package proposes it, `OPEN` means it waits on an open decision. A reply of "accepted" is only a sign-off for the rows and answers it names.

## Reply template

```text
Reviewer: <name>
Date: <date>
Revision reviewed: 0.4
Rows accepted: <ids, or 'all except the ones below'>
Rows corrected: <id: correction>
Rows I do not own: <id: who does>
Answers: <Q-number: answer>
Conditions: <anything unresolved>
```

## Nour: reference applications and scenarios

Your roadmap makes you Responsible and Accountable for the Procurement Agent, the Enterprise RAG Assistant, and failure scenarios and injection (roadmap §2.1). The rows below are the application evidence the dashboard shows: requests, model calls, state, tools, responses, retrieval, citations and scenario mode.

**Rows to confirm (37):**

- Applications: `APP-01`, `APP-02`, `APP-03`
- Trace Explorer: `TRX-04`
- Trace Detail: `TRD-01`, `TRD-02`, `TRD-10`, `TRD-11`, `TRD-12`, `TRD-13`, `TRD-14`, `TRD-22`, `TRD-23`, `TRD-30`, `TRD-31`, `TRD-40`, `TRD-41`, `TRD-44`, `TRD-45`, `TRD-46`, `TRD-47`, `TRD-50`, `TRD-51`
- RAG Diagnostics: `RAG-01`, `RAG-02`, `RAG-04`, `RAG-05`, `RAG-06`, `RAG-07`, `RAG-08`, `RAG-11`, `RAG-12`, `RAG-13`, `RAG-14`, `RAG-16`, `RAG-18`, `RAG-19`

**Questions for you:**

- **Q-12.** Confirm the execution-mode values, that a replay has no model call, how raw and delivered text and source snapshots are exposed, and how the agent-guard rejection is emitted as its own event.
- **Q-15.** The three drafts name the same values differently: workflow stage names (S1-01, governance, Schema v1's nine-stage list), run status versus `execution_status`, approval status, abstention reasons, per-policy status versus a pass boolean, pre-tool verdict (ALLOW or BLOCK with a basis versus `ERROR_BLOCK`), and whether a blocked call emits a result event (Schema v1 does; S1-01 forbids a fabricated result). Which enumerations are canonical?

## Ahmed: evaluators, classifier and RCA

Your roadmap makes you Responsible and Accountable for the evaluator library, the failure taxonomy, the rules, Logistic Regression and XGBoost classifiers, evidence-based RCA, and the security benchmark (roadmap §2.1). The rows below are the evaluator results, labels, scores, causes and metrics the dashboard shows.

**Rows to confirm (21):**

- Reliability Overview: `OVW-05`, `OVW-07`
- Trace Detail: `TRD-60`, `TRD-61`, `TRD-63`
- RAG Diagnostics: `RAG-09`, `RAG-10`, `RAG-15`, `RAG-17`, `RAG-20`, `RAG-21`
- Failure & RCA Investigation: `RCA-01`, `RCA-02`, `RCA-03`, `RCA-04`, `RCA-05`, `RCA-06`, `RCA-09`, `RCA-10`, `RCA-12`
- Release Quality Gate: `REL-05`

**Questions for you:**

- **Q-08.** Is the evaluation state (value, Not evaluated, Evaluator failed, Not applicable) a first-class result? How is a finding worded versus a metric? What reference format ties a cause to events, and how is "no cause supported" returned? How are the three classifier approaches reported for one trace?
- **Q-09.** How are attempted, prevented and realized violations returned once OD-09 is closed?
- **Q-11.** Schema v1 §5 puts scenario ground truth in the Release Quality Gate diagnostic panels, hidden from normal inference views. May reviewers see it, and under which role? Expected evidence is already shown on RAG Diagnostics as US-38 requires.
- **Q-15.** The three drafts name the same values differently: workflow stage names (S1-01, governance, Schema v1's nine-stage list), run status versus `execution_status`, approval status, abstention reasons, per-policy status versus a pass boolean, pre-tool verdict (ALLOW or BLOCK with a basis versus `ERROR_BLOCK`), and whether a blocked call emits a result event (Schema v1 does; S1-01 forbids a fabricated result). Which enumerations are canonical?

## Mohab: trace schema, ingestion and platform APIs

Your roadmap makes you Responsible and Accountable for the trace schema, instrumentation, ingestion and storage, and gives you the platform APIs and orchestration (roadmap §2.1, §2.2). The rows below are trace-level identity, order, completeness, freshness and the execution graph.

**Rows to confirm (13):**

- Reliability Overview: `OVW-01`, `OVW-02`, `OVW-03`
- Applications: `APP-04`, `APP-09`
- Trace Explorer: `TRX-01`, `TRX-02`, `TRX-03`, `TRX-06`
- Trace Detail: `TRD-20`, `TRD-21`, `TRD-81`, `TRD-82`

**Questions for you:**

- **Q-02.** How does the canonical schema represent missing, null, not applicable, redacted, unavailable and awaiting values, and where does an evaluation state live? The dashboard needs these eight absence states to be distinguishable.
- **Q-03.** Schema v1 gives every event a trace-scoped event ID and a sequence number. Confirm they are the anchors for deep links, so an evidence link lands on a single event. (Node and edge types are given by US-12.)
- **Q-04.** Will `apps/api` serve the windowed aggregates and trend buckets for Overview and Release Quality Gate, computed server side? Who sets the Overview window?
- **Q-05.** Confirm ownership of volume, freshness, ingestion health, completeness, event order, execution graph and redaction markers.
- **Q-07.** US-25 lets a review be submitted from Trace Detail, but Appendix B gives the Governance Reviewer only View on Trace Detail. Confirm "submit a review" is an action-level permission. The governance contract (§7.3) and Schema v1 use three roles where the stories use seven. The audit action catalogue has no override request or approval. Confirm who sees review and audit history (GD-15).
- **Q-15.** The three drafts name the same values differently: workflow stage names (S1-01, governance, Schema v1's nine-stage list), run status versus `execution_status`, approval status, abstention reasons, per-policy status versus a pass boolean, pre-tool verdict (ALLOW or BLOCK with a basis versus `ERROR_BLOCK`), and whether a blocked call emits a result event (Schema v1 does; S1-01 forbids a fabricated result). Which enumerations are canonical?

## Mohamed: policy, decisions, review, audit and roles

Your roadmap makes you Responsible and Accountable for the policy engine, the reliability decision logic, human review, append-only audit records and lightweight RBAC (roadmap §2.1). The rows below are policy results, approvals, decisions, review history, audit trail and payload visibility.

**Rows to confirm (21):**

- Reliability Overview: `OVW-04`, `OVW-06`
- Applications: `APP-10`
- Trace Detail: `TRD-32`, `TRD-33`, `TRD-34`, `TRD-35`, `TRD-42`, `TRD-43`, `TRD-62`, `TRD-70`, `TRD-71`, `TRD-83`
- Failure & RCA Investigation: `RCA-07`, `RCA-08`
- Release Quality Gate: `REL-01`, `REL-02`, `REL-11`, `REL-16`, `REL-19`, `REL-20`

**Questions for you:**

- **Q-06.** The governance contract says an incomplete evaluation has no decision and is never PASS (§6.2, decision flow §5.2), and that the rule path lists fired rules with evidence references. Confirm a reference can point at a single event. GD-13 (how an incomplete evaluation is stored and treated by the gate) names Malak and Alaa as co-owners of the answer. This package proposes the status-plus-missing-evidence display of `RCA-07`.
- **Q-07.** US-25 lets a review be submitted from Trace Detail, but Appendix B gives the Governance Reviewer only View on Trace Detail. Confirm "submit a review" is an action-level permission. The governance contract (§7.3) and Schema v1 use three roles where the stories use seven. The audit action catalogue has no override request or approval. Confirm who sees review and audit history (GD-15).
- **Q-09.** How are attempted, prevented and realized violations returned once OD-09 is closed?
- **Q-10.** The decision flow (§2.4) and Mohamed's roadmap give Mohamed the decision semantics and a gate decision adapter. Alaa's roadmap (§3, `gate_rules.py`) has her gate module produce the verdict. Who produces the verdict that `REL-01` shows? This package assumes Mohamed. Also confirm Alaa owns the comparison, artifact and disposition, and override requests and audit are Mohamed's. How do thresholds appear while OD-15 is open?
- **Q-13.** Appendix B gives Manage on several dashboards, and describes actions such as configuring behavior, running evaluations, annotating results and initiating gate evaluations. Which are in the MVP, and what are their fields?
- **Q-14.** Confirm the login form and Administrator account and role management are outside the seven screens.
- **Q-15.** The three drafts name the same values differently: workflow stage names (S1-01, governance, Schema v1's nine-stage list), run status versus `execution_status`, approval status, abstention reasons, per-policy status versus a pass boolean, pre-tool verdict (ALLOW or BLOCK with a basis versus `ERROR_BLOCK`), and whether a blocked call emits a result event (Schema v1 does; S1-01 forbids a fabricated result). Which enumerations are canonical?

## Alaa: versions, datasets, experiments and the release gate

Your roadmap makes you Responsible and Accountable for datasets, MLflow and reproducibility, and for the CI/CD quality gate (roadmap §2.1). The rows below are version identifiers, evaluation runs, scenario references, the gate comparison, the gate artifact and lineage.

**Rows to confirm (21):**

- Applications: `APP-05`, `APP-06`, `APP-07`, `APP-08`
- Trace Explorer: `TRX-05`
- Trace Detail: `TRD-80`
- RAG Diagnostics: `RAG-03`
- Release Quality Gate: `REL-03`, `REL-04`, `REL-06`, `REL-07`, `REL-08`, `REL-09`, `REL-10`, `REL-12`, `REL-13`, `REL-14`, `REL-15`, `REL-17`, `REL-18`, `REL-21`

**Questions for you:**

- **Q-06.** The governance contract says an incomplete evaluation has no decision and is never PASS (§6.2, decision flow §5.2), and that the rule path lists fired rules with evidence references. Confirm a reference can point at a single event. GD-13 (how an incomplete evaluation is stored and treated by the gate) names Malak and Alaa as co-owners of the answer. This package proposes the status-plus-missing-evidence display of `RCA-07`.
- **Q-10.** The decision flow (§2.4) and Mohamed's roadmap give Mohamed the decision semantics and a gate decision adapter. Alaa's roadmap (§3, `gate_rules.py`) has her gate module produce the verdict. Who produces the verdict that `REL-01` shows? This package assumes Mohamed. Also confirm Alaa owns the comparison, artifact and disposition, and override requests and audit are Mohamed's. How do thresholds appear while OD-15 is open?
- **Q-11.** Schema v1 §5 puts scenario ground truth in the Release Quality Gate diagnostic panels, hidden from normal inference views. May reviewers see it, and under which role? Expected evidence is already shown on RAG Diagnostics as US-38 requires.

