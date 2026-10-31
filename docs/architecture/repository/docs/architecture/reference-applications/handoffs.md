# Cross-team handoff checklist

Prepared for review; **not sent, acknowledged or signed**. This task does not contact teammates. S1-01 requires written acceptance from Ahmed, Mohab, Mohamed and Alaa. Malak receives application/UX evidence and performs the S1-07 independent closeout.

## Mohab — S1-02: canonical trace and interfaces

Provide: [E01–E27](trace-evidence-contract.md), tool proposal/check/dispatch separation, state-stage map, per-call/request versions, pending continuation semantics and four manual walkthrough scripts.

Additional provider handoff: record Google Gemini API and its exact frozen model/configuration information without making the canonical schema Gemini-specific. **Canonical TrustOps trace contract → provider-neutral; application runtime adapter → provider-specific translation.** Returned model/version and usage are recorded only when actually available; do not invent fields.

Require back:

- [ ] Every evidence row mapped to a canonical schema field/event in `packages/contracts`, including parent/order/evidence references.
- [ ] Distinct proposed, blocked/not-executed, executed/failed, unknown-outcome and successful actions.
- [ ] Canonical treatment of missing/null/not applicable/redacted/unavailable values; payload size and immutable source-snapshot resolution.
- [ ] Trace/continuation identity and duplicate/replay rules; confirmation required evidence can be preserved before risky dispatch.
- [ ] Manual procurement success, bypass and RAG failure fixtures aligned with S1-02; at least one procurement and one RAG schema walkthrough signed.
- [ ] Review SC-01–SC-03 replay/boundary provenance: no fictitious Gemini call, no invented app transitions, and explicit missing/not-applicable event semantics.
- [ ] Written schema-fit sign-off with contract revision and evidence references.

Nour does not define the canonical envelope, SDK, database, ingestion API or API routes.

## Ahmed — S1-03: failure/evaluator/RCA requirements

Provide: [eight-class matrix](failure-planning-matrix.md), independent ground truth requirements, normal controls, retrieval ranks/sources, claim/citation links, workflow/argument evidence and false-completion distinction.

Require back:

- [ ] Primary-label precedence for overlapping workflow/policy/injection/unsupported completion, retaining secondary findings.
- [ ] Exact class definitions and how attempted/prevented actions versus realized unsafe effects are labelled.
- [ ] Evaluator-family mapping, missing-evidence handling and fallible semantic-judge treatment.
- [ ] Fixed nine-cause RCA mapping with event evidence; supplier ineligibility must not automatically imply misconfigured policy.
- [ ] Retrieval metric unit, relevance annotations and expected-document provenance; evidence-sufficiency rubric review.
- [ ] Review SC-01 candidate-versus-delivered hallucination, SC-02 tool-selection/workflow overlap, and SC-03 early-stop versus prevented policy attempt; approve injected-cause mappings independently of evaluator output.
- [ ] Written taxonomy-fit sign-off; no observed metric or model improvement claimed without experiment evidence.

Nour does not implement the evaluator, classifier, security scorer or RCA ranking algorithm.

## Mohamed — S1-04: policy interaction and approval authority

Provide: [state contract](procurement-state-contract.md), five tool contracts, trusted context vs model arguments, request revision binding, pre-check timing, no-dispatch conditions and supplier/approval evidence.

Require back:

- [ ] Versioned truth tables for PROC-APPROVAL-01, PROC-TOOL-STAGE-01 and PROC-SUPPLIER-01, with below/equal/above configured threshold cases.
- [ ] D3 resolution for calculation tool permission; state/stage mapping and approved no-approval-required branch.
- [ ] Canonical synchronous ALLOW/BLOCK interface plus technical-error/missing-verdict semantics; no app-side policy engine.
- [ ] Approval evidence source/validity/expiry/revocation rules; stale request/supplier/amount handling and trusted resumption.
- [ ] Binding of ALLOW to proposal/state/arguments and check-to-dispatch mutation handling.
- [ ] S2/S3 integration-date reconciliation D4 and procurement-only applicability D5.
- [ ] Identify the S3-03 supplier-breach fixture for SC-03, approve isolated boundary-test scope and confirm that the real policy engine suppresses PO dispatch without bypassing application guards.
- [ ] Written policy-evidence sign-off.

Purchasing approvals, post-run reliability decisions and human trace reviews remain distinct concepts. No governance implementation is provided here.

## Alaa — S1-05: reproducibility and experiment lineage

Provide: Gemini provider identity, user-selected Gemini 3.8 Flash (`gemini-3.8-flash`), and application/prompt/model/config/retriever/corpus/index/tool/policy/scenario version requirements; scenario family/template/recipe grouping; source hashes; selected ADR; ground-truth isolation requirements.

Require back:

- [ ] Before reproducible experiments, freeze Gemini provider, exact model identifier, model configuration, prompt version, application version, retriever version and scenario version. Any model change is a configuration/version change for comparison; never relabel prior traces.
- [ ] Resolve OD-LLM-01 and validate OD-LLM-02 against the actual API project; consumer subscriptions do not establish API quota/billing entitlement. Embedding selection remains independent under OD-RAG-01.
- [ ] Version identifier and configuration-hash conventions; immutable manifests reference exact code commit when a repository is available.
- [ ] Runtime input vs injected labels/cause vs evaluator output separation, including label-encoding scenario-ID leakage checks.
- [ ] Dataset grouping, paraphrase and scenario-family split requirements with expected labels hidden from apps.
- [ ] Baseline/candidate reproducibility fields; model nondeterminism distinguished from deterministic fixture reproduction.
- [ ] Missing-provenance handling and unresolved remaining-class scheduling recorded; no synthetic metric values.
- [ ] Review proposed Week 7 recipe admission relative to dataset/split/model freezes; keep paired cases grouped and boundary-only tests distinguishable from full-app trajectories.
- [ ] Written versioning-fit sign-off.

Nour does not build datasets, split assignment, experiment tracking or the gate runner in this task.

## Malak — S1-06/S1-07: trace investigation and review

Provide: state transitions, pending/blocked/failed/succeeded outcomes; proposed versus executed tools; supplier/approval details; retrieval ranks/scores; selected context, claims/citations, abstention and version references.

Require back:

- [ ] Trace Explorer/Detail shows blocked proposal separately from executed result and false final claim.
- [ ] Execution graph requirements forwarded to Mohab for backend derivation; UI does not infer or recompute policy decisions/RCA.
- [ ] RAG Diagnostics can navigate claim→citation→source snapshot and show retrieval versus selected-context order.
- [ ] Unknown, not evaluated, evaluator failed and not applicable distinct from genuine zero/PASS.
- [ ] Pending approval and application completion are not rendered as reliability PASS.
- [ ] Acknowledgement that paper reviewer paths are understandable; independent S1-07 check after owner sign-offs.

No eighth screen, dashboard implementation or fabricated run screenshots are supplied.

## Sign-off record template

| Reviewer | Required review | Status | Contract revision | Decision/date/evidence |
|---|---|---|---|---|
| Mohab | Schema fit | PENDING | 0.5 for review | Not received |
| Ahmed | Taxonomy/evaluation fit | PENDING | 0.5 for review | Not received |
| Mohamed | Policy evidence fit | PENDING | 0.5 for review | Not received |
| Alaa | Versioning fit | PENDING | 0.5 for review | Not received |
| Malak | UX acknowledgement / later S1-07 | PENDING | 0.5 for review | Not received |

Each acceptance must name exact document/config revision, accepted items, unresolved conditions, reviewer and date. Silence is not sign-off. Record changes once in the relevant contract and link the revision from this checklist.

## OD-08 schedule review — plan owner

Provide the [three specifications and schedule proposal](failure-planning-matrix.md). Request agreement to the explicit S4-06 scope extension, separate Week 7 recipe dependencies from Week 8 classifier/RCA dependencies, and preserve the existing Week 4 and Sprint 3 gates. Identify S3-03 fixture handoff and confirm capacity/dataset sequencing. No new Jira task ID, deadline acceptance or plan edit has been assumed. Status: PENDING review.
