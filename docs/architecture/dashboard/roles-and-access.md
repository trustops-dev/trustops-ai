# Roles and access

Revision 0.4 · 2026-10-19 · DRAFT. Part of the [dashboard UX architecture](README.md).

The user stories (US-27, Appendix B) define seven roles with pre-provisioned accounts. The backend enforces every permission. The dashboard reflects what the backend returns and never decides who may do what. This page records how the seven screens behave for each role.

## Roles and landing pages

Each role has a role code and a default landing screen (Appendix B.1). The first screen after sign-in is the role's landing screen.

| # | Role | Code | Default landing | What the role does |
|---|---|---|---|---|
| 1 | Administrator | ADMIN | Reliability Overview | Full visibility. Sensitive actions normally belong to the Governance Reviewer; any Administrator use of them is logged and flagged. Sees raw payloads. |
| 2 | AI Engineer | AI_ENGINEER | Applications | Investigates hallucinations, retrieval errors, wrong tool selections, invalid arguments and workflow failures. Manages application behavior configuration. Cannot approve releases. |
| 3 | Reliability Engineer | RELIABILITY_ENGINEER | Failure & RCA Investigation | Evaluator results, taxonomy, classification and root-cause analysis. Runs evaluations and annotates investigation results. |
| 4 | LLMOps Engineer | LLMOPS_ENGINEER | Release Quality Gate | Versions, datasets, baseline-versus-candidate comparisons and the quality gate. Initiates release-gate evaluations. Requests, but cannot approve, a BLOCK override. |
| 5 | Platform Engineer | PLATFORM_ENGINEER | Trace Explorer | Application registration, instrumentation, ingestion validation and schema diagnostics. Manages technical integration settings. |
| 6 | Governance Reviewer | GOVERNANCE_REVIEWER | Failure & RCA Investigation | Examines policy violations, security findings and uncertain decisions. Records human review verdicts and approves or rejects BLOCK override requests. |
| 7 | Security Auditor | SECURITY_AUDITOR | Reliability Overview | Independent and read-only. Sensitive payloads stay redacted. |

## Dashboard access by role

Dashboards: D1 Reliability Overview, D2 Applications, D3 Trace Explorer, D4 Trace Detail, D5 RAG Diagnostics, D6 Failure & RCA Investigation, D7 Release Quality Gate. Manage means the role can take the actions that role owns on that dashboard. View means read-only. Every role can open every dashboard, so global navigation shows all six destinations to everyone.

| Role | D1 | D2 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|---|
| Administrator | Manage | Manage | Manage | Manage | Manage | Manage | Manage |
| AI Engineer | View | Manage | View | View | View | View | View |
| Reliability Engineer | View | View | View | View | Manage | Manage | View |
| LLMOps Engineer | View | Manage | View | View | View | View | Manage |
| Platform Engineer | View | Manage | Manage | View | View | View | View |
| Governance Reviewer | View | View | View | View | View | Manage | Manage |
| Security Auditor | View | View | View | View | View | View | View |

## Actions the stories define

| Action | Who may do it | Where it appears | Source |
|---|---|---|---|
| Record a human review: ACCEPT, REVIEW or BLOCK verdict plus written rationale, on a trace | Governance Reviewer; Administrator, flagged as an administrator action | Header of Trace Detail and Failure & RCA Investigation | US-25, US-27 |
| Record a human review on a release evaluation | Same | Header of Release Quality Gate | US-25 |
| Request a BLOCK override with a written reason | LLMOps Engineer | Release Quality Gate | US-27 |
| Approve or reject a BLOCK override | Governance Reviewer; Administrator, flagged | Release Quality Gate | US-27 |
| See raw payloads | Administrator only; every other role sees redacted payloads | Everywhere a payload appears | US-27 |
| Any write | Not the Security Auditor. The backend rejects it | Actions are shown unavailable | US-27 |

Reviews cannot be edited after submission. A correction is a new entry (US-25). Audit records cannot be updated or deleted (US-26). Reviews and overrides appear immediately in the review history and the audit history.

## How the screens behave for permissions

| Situation | Behavior |
|---|---|
| A role cannot take an action | The control is shown unavailable with the reason in text, for example "Recording a review needs the Governance Reviewer role." It is not hidden, so the capability stays discoverable. |
| The backend rejects an action | The screen says what was refused and what to do, for example "Your role cannot approve overrides. Ask a Governance Reviewer or Administrator." No blame wording, and a retry control is not offered. |
| An Administrator takes a Governance Reviewer action | The resulting entry shows an "Administrator action" flag in the review history and the audit history. |
| Payloads | Redacted values show the Redacted state with its reason. The Administrator sees raw values. `TRD-83` tells the reader which applies. |
| Override approval | A confirmation dialog names the exact candidate, for example "Approve override of Block for candidate 'X'?", with Cancel as the default focus. |

## Cross-check with the governance contract and Trace Schema v1

The governance contract register (Mohamed, §7.3) and Trace Schema v1 (Mohab, §4.3) were drafted from the proposal's three prototype roles (Engineer, Reviewer, Admin; FR-19). The user stories v2.2 expand that to seven. This page follows the stories.

| Point | State |
|---|---|
| Role set | Governance contract §7.3 and Schema v1 `reviewer_role` use three roles. They need the seven role codes of Appendix B. Q-07. |
| Raw versus redacted content (GD-15) | US-27 answers it: raw payloads for the Administrator only. |
| Who sees review and audit history (GD-15) | Appendix B gives every role at least View on every dashboard, and the Security Auditor verifies audit history. The stories do not say whether each role sees the history itself. This package shows it to every role on the screens that carry it, pending Mohamed's confirmation. Q-07. |
| Audit action catalogue (§7.2) | It has no entries for an override request or an override approval. US-26 and US-27 require both, flagged when an Administrator acts. Q-07. |
| Word "approval" | The governance contract (§5.2) says the prototype roles are not purchase approvers. US-27 makes the Governance Reviewer the approver of a BLOCK override. These are different things, so the screens label them Purchase approval and Override approval. |

## What the stories leave open

| Gap | Question |
|---|---|
| US-25 lets a review be submitted from Trace Detail, but Appendix B gives the Governance Reviewer only View on Trace Detail (D4) and Manage on Failure & RCA (D6). | Q-07: confirm that "submit a review" is an action-level permission that does not depend on the dashboard's Manage or View level. |
| Appendix B gives Manage on Applications (AI Engineer, LLMOps Engineer, Platform Engineer), Trace Explorer (Platform Engineer) and RAG Diagnostics and Failure & RCA (Reliability Engineer), and describes actions such as configuring application behavior, running evaluations, annotating investigation results and initiating gate evaluations. No story defines what those controls are. | Q-13: list the actions, or confirm they are out of the seven screens for the MVP. The wireframes show no such controls until it is answered. |
| User accounts, role assignments and system settings are Administrator functions. | Q-14: confirm they are outside the seven screens, along with the login form. |
