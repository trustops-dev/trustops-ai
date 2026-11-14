# Cross-team handoff checklist

**Final governance response reviewed 2026-11-14.** [Exact-revision review and artifact hashes](reviews/mohamed-7c26168-governance-response.md) record PR #28 at `7c26168ea47a611d233202e21f0c0b9f7a5cb3c8`. Mohamed accepts OD-03 synthetic values (USD only, `5000.00`, strict `>`, `manager`, decimal strings, no FX), with row 6 amended to `procurement-policy-set-v0.1.yaml`, version `synthetic-procurement-policy-set-v0.1`. The supplied checker reproduced 31/31 committed candidate cases locally. His OD-04 and OD-12 dispositions, SA-01–SA-09, stage/verdict clarification and SC-03A/SC-03B distinction are recorded with remaining owners. Mohab transport/digest and mechanism dispositions, corpus pairing, runtime verification and full cross-team acceptance remain open.

**Plan ownership corrected — 2026-11-14:** [Six decision groups](plan-approval-routing.md) route OD-02/06/08/16, GD-26/OD-09 and Malak's proposed UI schedule through their technical reviewers, then to Nour as team lead for explicit row-level decisions on the internal plan. No separate approver is part of the team's process. Neither specialist replies nor the proposed 70-task HTML plan is a plan decision.

**Malak's scoped UI response — reported 2026-11-07, recorded 2026-11-09:** [Nine fixture-based distinctions and reconciliation](reviews/malak-479cab0-ui-response.md) are received as owner verification against handoff `479cab0`: 137 tests reported, 13 traces, browser inspection. Her UI work was uncommitted; no branch or independent rerun was supplied. Both attached plan snapshots report 134 tests and 11 fixtures, with no exact test/fixture count bridge. TRD-45's tri-state presentation is acknowledged; Mohamed’s stage/verdict distinction is supplied at `7c26168`; canonical field names, cancelled/failed-invocation fixture evidence, live API and S1-07 remain open.

**Provider evidence routed — 2026-11-09:** [Two bounded sanitized sessions](workload-review/od-llm02-v0.2/bounded-live-results-2026-11-09.json) reached C01 PASS and stopped at G01 with separate timeout/unknown and provider-or-SDK errors. Windows offline tests were 25/25 per operator-supplied terminal evidence. Mohab reviews transport/error classification and full-envelope count/admission; Alaa reviews free-tier quota/headroom and workload admission; Nour retains failed-attempt accounting and coordinates any separately admitted diagnostic. No G01/G02/G03/E01/E02 live PASS or model promotion is recorded. USD 0 paid-use authorization stays in force.

**Current mapping — 2026-11-09:** [Draft v1.8 E01–E27 assessment](schema-v1.8-evidence-mapping.md) and [exact field witnesses](schema-v1.8-evidence-mapping.json) cover all 27 requirements: **11 OK, 9 CHANGE REQUIRED, 7 OPEN**. The [fresh rerun and package observations](schema-v1.8-review-observations.json) record 2,306 assertions and 52/52 cases against actual files; email/bundled-report identities disagree. OD-05 stays blocking pending corrected hashes, row fixes and scoped review. [v1.6 mapping](schema-v1.6-evidence-mapping.md) is historical; no runtime or joint sign-off is inferred.

**Credential and runner update — 2026-11-08.** Replacement `TrustOpsAI-dev` and old-key absence were observed on 2026-11-07; local storage is Nour’s confirmation. Live authentication is not verified. The [bounded compatibility runner](../../../tools/provider_compatibility/README.md) implements isolated synthetic probes with offline SDK tests. Full-envelope token admission, live results and application acceptance remain open. Nour runs the local probes and returns sanitized results; Mohab reviews interface/admission integration; Alaa reviews quota/workload evidence. No model promotion or shared approval is implied.

**Workload candidates — 2026-11-07 snapshot.** The [free-only 0.2 baseline](workload-review/od-llm02-v0.2/README.md) and [Flash Lite 0.3 alternative](workload-review/od-llm02-v0.3/README.md) supersede the earlier USD 10 allocation proposal with a USD 0 paid-spend requirement. Ownership is user-reported and free-tier quotas are screenshot-observed as recorded in the supplied update; capture times, remaining quota and runtime compatibility remain unverified. Flash remains the current proposed primary. Lite promotion requires scoped application/interface/workload review and executed evidence. Alaa’s prior response remains partial/conditional against its original revision. Credential replacement is observed and local storage is user-confirmed. Quota headroom, API execution, OD-03 integration, OD-04 acceptance and the existing schema gates remain pending. The later scoped OD-03 disposition is recorded below.

**Alaa response recorded — 2026-11-06:** [Scoped review of commit 479cab0](reviews/alaa-479cab0-review.md) received from user-supplied email text. Overall status: **PARTIAL / CONDITIONAL**. Candidate/principle acceptance and remaining conditions are recorded separately; no full specialist sign-off or joint freeze. The email date and message reference were not supplied.

**OD-03 current disposition — 2026-11-14.** Mohamed accepts synthetic review rows 1–5 and supplies the amended row-6 YAML/version at PR #28 commit `7c26168`. The independent rerun agrees on all 31 cases. Mohab transport/digest and Nour corpus pairing/integration remain open. [Final revision record](reviews/mohamed-7c26168-governance-response.md). The [earlier email record](reviews/mohamed-479cab0-od03-response.md) is historical.

**OD-04 current disposition — 2026-11-14.** [Mohamed’s final scoped response](reviews/mohamed-7c26168-governance-response.md) accepts V01/V02/V03/V07/V08 and amended V04/V05 wording, with V06 mechanism amended. [Application position 0.2](approval-validity/od04-v0.2.md) records the outstanding SA-02 consumption-time currentness/atomicity, SA-03 terminal representation, SA-04 chronology and continuation topology decisions with Mohab/Nour.


**2026-11-02 confirmation received:** Mohamed and Mohab confirmed the approval-observation distinction, as reported by the user. [OD-APP-OBS-01](open-decisions.md#approval-observation-confirmation) records trusted read-only observation of the existing approval request, distinct from retrying its initial submission. This closes that wording/interface-meaning item; full schema/governance sign-offs and implementation verification remain pending.

**2026-11-02 corpus/boundary completion:** RAG revision 0.9 adds the [synthetic corpus specification](corpus-review/README.md); [ten manual boundary cases](manual-boundary-cases.md) include denied approval and symbolic below/equal/above T. These complete the remaining owner drafting items, not shared acceptance or runtime tests. See [current closeout](week1-owner-closeout.md).

**Decision/handoff consolidation — 2026-11-05.** Owner drafting history is preserved below; current questions and routing are in the targeted review table. No new acceptance or sent message is recorded.

The current handoff is [week1-owner-closeout.md](week1-owner-closeout.md); use [week1-review-manifest.json](week1-review-manifest.json) to identify each actual file revision/hash. Do not request acceptance of every document as revision 0.6: the bundle contains independently versioned documents. The owner requests below remain valid; their old revision references are historical. Messages are prepared, not sent by this task. Scoped observation confirmation is recorded above; complete specialist acceptance has not been recorded.

**Historical freeze-candidate label — revision 0.6, 2026-11-01. NOT FROZEN.** Documentation and manual review evidence only; specialist approvals remain PENDING. Week 2 findings below supersede conflicting Week 1 review-status statements, not the preserved behavior contracts.

**Historical v1.6 supplied review — 2026-11-05:** [v1.6 schema / governance 0.4 joint review](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal), R16-01–09. Preserve verified prior fixes. The [v1.5 review](schema-v1.5-review.md) is historical; its E01–E27 mapping is retained unchanged for historical comparison; the v1.6 mapping is retained separately. The current v1.8 assessment appears above; suite reproduction does not imply acceptance.

## Week 2 cross-team review and sign-off matrix

Current routing distinguishes sent-email confirmation from received responses: Alaa’s scoped response to commit 479cab0 is recorded above; full specialist and cross-team acceptance remain pending. Earlier revision 0.6 checklists below are historical requests, not signatures. Existing imports and author checks do not establish acceptance.

| Reviewer | Review area | Status | Issues | Resolution / evidence required |
|---|---|---|---|---|
| Mohab | Trace/schema fit | PENDING — CHANGES REQUIRED | R16-01–06 and R16-09 corrections; R16-07/08 joint alignment | Correct files and return exact hashes, focused regression evidence and dispositions for reassessment; retain prior fixes. Nour has completed the v1.8 E01–E27 reassessment; Mohab must correct exact package identities and the 9 CHANGE REQUIRED rows, with 7 OPEN rows routed to named reviewers |
| Ahmed | Failure/evaluator fit | PENDING | Source/claim gaps, unknown timeout, matching action results, supplier scope, overlap, numeric examples | Accept qualitative sufficiency/citation evidence, corrected examples and independent annotation; no evaluator required |
| Mohamed | Governance fit | FINAL SCOPED RESPONSE RECEIVED — `7c26168` | OD-03 YAML and independent 31/31 result supplied; OD-04/12 governance dispositions and SA-01–SA-09 recorded | Mohab returns amendment/transport/digest dispositions; Nour integrates agreed state/corpus choices; Ahmed/Alaa resolve labels/RCA/gates. [Exact revision](reviews/mohamed-7c26168-governance-response.md) |
| Alaa | Versioning fit | RESPONSE RECEIVED — PARTIAL / CONDITIONAL | [ALA-01–11](reviews/alaa-479cab0-review.md): accepted lineage/candidate/grouping scope; hashing/projection/access/numeric-budget/joint-mapping conditions remain | Return explicit conventions with Mohab; review Nour’s access/workload evidence and dependent Ahmed/Mohamed mappings. No unconditional sign-off or frozen index inferred |
| Malak | UI evidence fit / S1-07 | RESPONSE RECEIVED — FIXTURE-BASED, CONDITIONAL | [Nine distinctions](reviews/malak-479cab0-ui-response.md) reported on uncommitted UI; TRD-22/23 display/mapping evidence, canonical fields, 137 versus 134 tests, 13 traces versus 11 plan fixtures remain open | Return branch/commit, test logs and fixture index; coordinate Mohab/Mohamed mapping; independently close S1-07 after required sign-offs |

## Targeted review routing

The [pending-decision table](open-decisions.md#pending-decisions-and-exact-requests) holds the complete proposal, responsible reviewer, exact question and closure evidence for each ID below. Use those questions verbatim or send a scoped subset; the detailed checklists later in this file are supporting acceptance criteria, not extra unassigned decisions. All requests are PREPARED; sending and reviewer acceptance are not recorded by this edit.

| Recipient / coordinator | Decision IDs to answer | Exact requested response and evidence | Nour's next action |
|---|---|---|---|
| Mohab | OD-05, OD-05-MAP, OD-12-CLAIM/RETRY/OUTCOME/BUDGET; technical parts of OD-04/10/13/LLM-01/RAG-01 | Return R16-01–09 dispositions and exact corrected files/tests; agree the canonical mapping, claim timing, attempt/outcome evidence and environment/provenance interfaces. Use each linked question's closure criteria. | Supply the current joint-review ZIP and comparison contracts; compare returned tests and E01–E27 mapping, without writing his canonical schema. |
| Mohamed | OD-02/04/06/09/16, OD-05-MAP, OD-12 children | Final governance dispositions and supplied OD-03 YAML/checker reviewed at `7c26168`; local independent result 31/31 PASS | Coordinate SA-01–SA-09 with Mohab, SA-09 also with Ahmed/Alaa; retain plan and runtime gates. [Final record](reviews/mohamed-7c26168-governance-response.md) |
| Ahmed | OD-09, interpretation portions of OD-12-OUTCOME, OD-13 and OD-05; sufficiency/metric-unit parts of OD-10 | Return outcome/label/precedence/RCA examples, source-versus-claim interpretation, relevance-unit rubric and GD-26 disposition. Identify missing evidence explicitly. | Supply candidate/delivered, supplier-boundary, unknown-effect and conflicting-RAG cases; retain qualitative sufficiency as the application design. |
| Alaa | OD-13, OD-LLM-01/02, OD-RAG-01; dataset order in OD-08; workload in OD-12-BUDGET; gate interpretation in OD-09 | Response received: retain accepted candidate/grouping principles; finalize explicit hash/missingness/projection conventions with Mohab, review supplied workload/access evidence, and complete dependent GD-26 mapping. See ALA-01–11; empirical thresholds stay deferred. | Supply API-project owner/access and quota/workload evidence; coordinate Mohab’s conventions/projection correction and Ahmed/Mohamed outcome mapping. Record closure evidence per ALA item; do not request the whole review again. |
| Malak | OD-14 UX acknowledgement; presentation consequences of OD-05-MAP/12-OUTCOME | Owner report received for all nine fixture-based distinctions; [scoped record](reviews/malak-479cab0-ui-response.md) identifies TRD-45 amendment, Mohamed’s confirmed TRD-22/23 distinction and pending canonical/display evidence. Return a committed branch, exact 137-test evidence, and reconcile plan's 134 tests and fixture counts. | Compare exact revision and fixture index when supplied, route field/stage questions to Mohab/Mohamed, then request independent S1-07 only after specialist conditions close. |
| Nour — team lead and internal plan decision owner | OD-02/06/08/16, GD-26/OD-09 and 12-task UI amendment | [Decision packet](plan-approval-routing.md) specifies proposed scope/date/dependency changes and required specialist evidence. Team-lead ownership was directly confirmed 2026-11-14; no row has been accepted by that fact alone. | Collect scoped evidence and record separate dated ACCEPT/AMEND/DECLINE per row against exact plan revision, tasks, capacity and gates. No plan change active. |
| Nour — own preparation | OD-03 integration, OD-04/12 application fit and handoff | Supplied YAML/checker and the [proposed policy-KB pairing](corpus-review/policy-bundle-pairing-v0.1.md) each pass 31/31 against their respective text; symbolic snapshots remain historical | Obtain Mohamed text, Mohab transport/digest, and Alaa/Ahmed lineage/fixture review of the exact candidate before ingestion; review SA dispositions and implement agreed atomic/currentness/continuation later. [Final governance record](reviews/mohamed-7c26168-governance-response.md) |

For final acceptance, each of Mohab, Ahmed, Mohamed and Alaa answers OD-14 for their scope. Malak's acknowledgement and later independent closeout are separate. No recipient is asked to approve an entire bundle merely because one semantic distinction was confirmed.

### Scoped response format

```text
Reviewer:
Date:
Reviewed files/revisions/hashes:
Decision IDs:
Response for each ID: ACCEPT / AMEND / DECLINE
Replacement wording or values if AMEND:
Evidence / fixture / test references:
Conditions still open and responsible person:
Scope: design / offline fixture verification / runtime verification
```

Nour records the response once in the owning decision row, links its evidence and updates the sign-off record only for the accepted scope. A runtime check cannot be marked executed from a paper fixture or validator result.

### Concrete response to Malak's 37 Nour-owned rows

| Field group | Application evidence / response | Remaining fit |
|---|---|---|
| APP-01/02/03; TRX-04 | Application identity/behavior/config refs, run state separate from reliability decision | WG-01/06; application completion never implies reliability PASS |
| TRD-01/02/10/11/12/13/14 | Run/request/model/provenance details, manual/replay/live mode, known versus absent metadata | WG-06/08; no fictitious provider response or measurement |
| TRD-22/23 | E09/E10: accepted/attempted fine transitions and separate coarse stage | WG-01; preserve pending/in-flight state and mapping version |
| TRD-30/31 | E03/E11: policy lookup and raw/normalized supplier snapshot | WG-03/05; exact source versions |
| TRD-40/41/44/45/46/47 | E15–20/E25: proposals, raw/parsed args, stop layer, calls/results, recovery | WG-02/04/08; TRD-45 tri-state effect and original-vs-recovered presentation now owner-reported on fixtures; canonical field mapping pending |
| TRD-50/51 | E21/E25: candidate/delivered response, exact supporting result, pending/error | WG-04/08; raw false claim remains visible even when corrected before delivery |
| RAG-01/02/04/05/06/07/08 | E04–07: query/config, retrieval outcome, returned docs, score semantics, selection/sufficiency | WG-05/06; empty success ≠ retrieval error; no inferred metric zero |
| RAG-11/12/13/14/16/18/19 | E22–25: answer/claims/citations/structural checks, abstention, snapshot, outcome | WG-05/08; structural citation validity ≠ semantic support |

This accounts for all 37 rows assigned to Nour in the owner packet. Mohamed continues to own approval/policy truth; Alaa version conventions; Ahmed evaluator scores. Mohab derives graph/API projections. No frontend design or implementation is added.

### Alaa configuration freeze checklist

Before implementation: agree provider/model and effective parameters/API/SDK surface, prompt/tool versions, retrieval/embedding/store/corpus/index settings, policy/approval rules, mock/continuation/idempotency budgets and their immutable references. Before dataset generation: freeze code revision, application/config/source hashes, corpus/index membership, scenario family/template/recipe versions, seed/mode, independent labels/qrels and group-split assignment; keep controls and variants in one group. Returned provider versions are recorded only if available; a stable alias is not proof of an immutable backend. API secrets are never lineage. Actual runtime compatibility, quota and workload tests remain separate future gates.

The preserved owner checklists below remain detailed acceptance requests. Use the current manifest and its SHA-256 in every new response; the original revision 0.6 references identify the earlier request only.

Historical preparation status for the checklists below: they were prepared before outreach. Current publication and Alaa’s scoped response are recorded above; no full specialist signature is inferred. S1-01 requires written acceptance from Ahmed, Mohab, Mohamed and Alaa. Malak receives application/UX evidence and performs the S1-07 independent closeout.

## Mohab — S1-02: canonical trace and interfaces

Confirmed semantic item: OD-APP-OBS-01. Remaining related work is canonical submission/observation evidence and adapter verification that observation cannot invoke the creating path; the semantics do not need to be requested again.

Provide: [E01–E27](trace-evidence-contract.md), tool proposal/check/dispatch separation, state-stage map, per-call/request versions, pending continuation semantics and four manual walkthrough scripts.

Additional provider handoff: record Google Gemini API and its exact frozen model/configuration information without making the canonical schema Gemini-specific. **Canonical TrustOps trace contract → provider-neutral; application runtime adapter → provider-specific translation.** Returned model/version and usage are recorded only when actually available; do not invent fields.

Require back:

- [ ] Disposition and closure evidence for R16-01–09 against the exact v1.6 joint-review inputs; preserve verified fixes and distinguish expected failing application traces from inconsistent claims of verified success.
- [ ] Corrected specification, validator, runner and fixtures with exact byte hashes and self-contained commands; explain optional regression cases and make reported mutations/counts match the code.
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

Confirmed semantic item: OD-APP-OBS-01. Approval validity, authoritative decision evidence, broader continuation rules and submission-replay policy retain their separate review scope.

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
| Mohab | Schema fit | PENDING | Current manifest + reviewer scope | Not received |
| Ahmed | Taxonomy/evaluation fit | PENDING | Current manifest + reviewer scope | Not received |
| Mohamed | Policy evidence fit | PENDING | Current manifest + reviewer scope | Not received |
| Alaa | Versioning fit | PENDING | Current manifest + reviewer scope | Not received |
| Malak | UX acknowledgement / later S1-07 | RECEIVED — CONDITIONAL, FIXTURE-BASED | [Scoped report](reviews/malak-479cab0-ui-response.md); no UI branch/commit | Nine distinctions reported; canonical fields, TRD-22/23 display/mapping, test/fixture reconciliation and independent S1-07 open |

Each acceptance must name exact document/config revision, accepted items, unresolved conditions, reviewer and date. Silence is not sign-off. Record changes once in the relevant contract and link the revision from this checklist.

## OD-08 schedule review — plan owner

Review the [three specifications and schedule proposal](failure-planning-matrix.md) within the [six-group decision packet](plan-approval-routing.md). Nour, as team lead, records his decision on the explicit S4-06 scope extension after reviewing Week 7 recipe dependencies, Week 8 classifier/RCA dependencies, preserved Week 4/Sprint 3 gates, S3-03 fixture handoff and capacity/dataset sequencing. He separately decides the proposed 12-task UI amendment after Malak supplies a branch and reconciles test/fixture counts. No new Jira task ID, deadline acceptance or plan edit has been assumed. Status: PENDING TECHNICAL EVIDENCE AND TEAM-LEAD DECISIONS.

## v1.8 mapping handoff — 2026-11-09

The [current 27-row mapping](schema-v1.8-evidence-mapping.md) distinguishes verified static fixes (2,306 assertions, 52/52 cases) from 9 CHANGE REQUIRED and 7 OPEN requirements. Mohab: reconcile email/report SHA-256 and assertion count to exact bytes; address E02–E04, E06–E08, E14, E17 and E25, and return corrected positive/negative examples. Mohamed + Mohab: source record-sequence ordering, approval/supplier version currentness at claim, and separate immutable consumption record. Ahmed/Alaa: metric/selection and inference/provenance conventions. Nour: reassess corrected exact revision. The supplied suite and this mapping do not constitute schema acceptance.

## v1.6 mapping handoff — 2026-11-06

Nour has completed the current row assessment. Mohab should use [the detailed mapping](schema-v1.6-evidence-mapping.md) and exact input hashes to correct E09, E13, E14, E17, E18, E20, E21, E25 and E27. Return corrected schema, validator, runner, fixtures and targeted positive/negative results. The nine OPEN rows name the responsible reviewers and exact questions; do not treat them as confirmed defects. Mohamed reviews approval/policy semantics and R16-07/08 with Mohab; Ahmed reviews evidence/failure meaning; Alaa reviews configuration/projection lineage. Nour reassesses the returned revision. OD-03 has a later scoped synthetic-value acceptance and representation amendment, with YAML and independent check supplied at `7c26168` and shared integration still open; OD-04's application response remains separately unaccepted. OD-APP-OBS-01 semantics remain closed.

## Workload/access follow-up to Alaa — prepared, not sent

**Workload proposal prepared — 2026-11-06:** [API ownership and workload candidate 0.1](workload-review/od-llm02-v0.1/README.md) supplies execution/call/token/retry/concurrency estimates and public-price token subtotals. Actual API project/access/billing owner, account quotas and applicable charges remain unconfirmed. ALA-05/ALA-08 and OD-LLM-02/OD-12-BUDGET stay open; no live execution is authorized.

Nour has prepared the estimate and explicit unknown-owner/access record. Next, obtain the actual owner/admin and project/tier/quota evidence, then ask Alaa to ACCEPT/AMEND the assumptions and allocation. Mohab confirms preflight/usage/embedding-admission and storage/accounting interfaces; Mohamed retains purchasing-boundary review. Candidate preparation is complete; account identification and execution readiness are not. Do not reopen Alaa’s accepted design principles or mark his conditions closed from this estimate.
