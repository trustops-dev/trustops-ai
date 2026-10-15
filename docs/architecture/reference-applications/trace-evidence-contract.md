# Application-to-trace evidence requirements

**This is not Mohab's Trace Schema v1.** Rows name semantic evidence requirements and suggested event boundaries, not canonical JSON keys, event enums, API routes, database columns or Pydantic classes. Mohab maps each requirement to `packages/contracts` under S1-02. Canonical-schema fit is pending.

FACT — Proposal J requires stable trace/event IDs, parent relationships, sequence/timestamps and version provenance. DECISION — the apps require unambiguous linkage and the evidence below. Preserve occurrence order as well as reception time; a parent's identity alone does not express all causal dependencies. Multi-evidence references are requirements for review, not a new graph storage design.

## Evidence matrix

| ID / application step | Minimum app-provided evidence | Proposed boundary / linkage | Consumer and reason |
|---|---|---|---|
| E01 User request, both | Raw request, normalized fields/query, revision, application identity, synthetic-data marker | Request accepted/rejected; root of interaction | All: reconstruct intent and normalization |
| E02 Model call, both | Prompt/template version, actual rendered input/context reference, selected provider, configured model identifier, returned model identifier/version when available, model/configuration version, generation parameters, model response/refusal/error, latency and token/usage metadata when available | Start/end; links to triggering state/retrieval and produced proposal/text | Ahmed: semantic/tool analysis; Alaa: provenance |
| E03 Procurement policy retrieval | Raw/effective query, filters/k, policy set and retriever versions | Search proposal, start/result or error linked to E01/E02 | Ahmed/Mohamed: retrieval and policy applicability |
| E04 RAG retrieval | Query, effective query, k, filters, corpus/index/embedding/retriever configuration | Retrieval start/result or error linked to query | Ahmed: retrieval metrics, failure diagnosis |
| E05 Retrieved documents | Full ordered returned list; document/source/chunk IDs, versions, text/snapshot, hashes and locators | Children/references of retrieval result | Ahmed: independently inspect source relevance/support |
| E06 Retrieval scores/ranks | Raw finite score, metric kind/direction, returned rank, tie rule, returned count | Per retrieved result, not a model confidence score | Ahmed/Alaa: comparable retrieval metrics |
| E07 Evidence selection | Selected IDs/order/text spans, rejected IDs/reasons, sufficiency outcome, unresolved facets/conflicts, selection version | After retrieval, before generation | Groundedness/abstention review |
| E08 Request normalization | Raw-to-normalized field links, validation details, amount/currency/request revision | Before REQUEST_CAPTURED or clarification outcome | Argument and policy-consistency checks |
| E09 Agent state transition | Previous/new state, reason, input/result references, transition attempted vs accepted, state revision | Every entry/exit including no-op wait and rejected transition | Ahmed/Malak: trajectory and execution graph |
| E10 Workflow stage | Coarse stage at proposal/check/dispatch, state-to-stage mapping version | Snapshot at each relevant boundary | Mohamed: tool-stage permission |
| E11 Supplier check | Requested/returned ID, status, source/directory/record version, lookup outcome | Tool result plus state transition linkage | Supplier policy and RCA |
| E12 Approval calculation | Amount/currency, configured rule basis, threshold/comparator/version, requirement/level or unresolved reason | Calculation result tied to exact request revision | Policy reconstruction and threshold boundary review |
| E13 Approval submission | Request and approval-request IDs, calculation ref, required level, idempotency identity | Submission distinct from granting; link to active state | Governance and UI waiting state |
| E14 Approval observation | Required/received flags, status, approval ID, actor/time/source, request/supplier/amount/currency/level/version binding | Separate observation/resume event linked to submitted request | Detect stale, forged, missing or unrelated approval |
| E15 Tool proposal | Exact proposed tool, tool catalog/schema version, model call ref, proposal identity | Exists before validation/authorization; is NOT execution | Selection errors and bypass evidence |
| E16 Tool arguments | Raw serialized arguments, parsed values, trusted runtime context separately, validation outcome/field errors | Validation result links to proposal and request | Invalid arguments and tampering evidence |
| E17 Pre-execution policy request | Proposal/tool, argument digest, request/state revision, stage, supplier/approval/calculation evidence refs, policy version | After proposal, before any tool body dispatch | Mohamed owns request/result schema; app supplies trustworthy evidence |
| E18 Pre-execution policy result | ALLOW/BLOCK, per-policy findings/reasons/version, referenced inputs; explicit timeout/error/missing result | Bound to E17/proposal; separate from post-run decision | Enforce and explain refusal to dispatch |
| E19 Dispatch suppression | NOT_EXECUTED, execution_started=false, blocking/check-error reference, reason | In place of invocation; never fake successful tool result | Prove prevention; distinguish blocked and failed execution |
| E20 Tool invocation/result | Invocation identity, proposal/check refs, start/end, mock marker, idempotency key, outcome/result/error, PO ID only if confirmed | ALLOW → dispatch → observed result; unknown outcome explicit | Unsupported completion, duplicate and task success analysis |
| E21 Final response, Procurement | Exact raw generated text and delivered text, which was shown, final app outcome/state, supporting successful action references or reason for no action | Final model output/formatting linked to result or suppression | Identify independent unsupported-completion claim |
| E22 Grounded answer, RAG | Candidate and final text, exact generation context, claim IDs/text/answer spans | Generation → citation binding → final output | Groundedness review independent of generator |
| E23 Citations | Claim→retrieved source/chunk/version/span→visible marker; validation findings; selected-context membership | Binding records refer to E05/E07/E22 | Citation support and nonexistent-source checks |
| E24 Abstention | Reason, missing facets/conflicts, available/selected evidence, last stage, delivery text | Terminal ABSTENTION, separate from ERROR | Evaluate appropriate/over-abstention without a new class |
| E25 Technical failure/cancel/pending | Stage, known/unknown outcome, error category, retry/replay/continuation references | Preserve partial trace, no fabricated completion | All: missing evidence must remain visible |
| E26 Run/version provenance | Provider, exact configured model identifier and available version, application, prompt, model/config, retriever, corpus/index, tools, policy, scenario/config references | Request-level snapshot plus per-call exceptions when changed | Reproducible datasets and baseline/candidate comparison |
| E27 Controlled scenario association | Opaque scenario/version/run reference; independent label/cause/recipe records kept outside runtime inference input | Joined later by Alaa's dataset projection | Labels independent of evaluator output; leakage prevention |

Unavailable latency/token/provider metadata is unknown/null with reason, never fabricated zero. Exact canonical representations, redaction placeholders and size limits require Mohab's approval. Use synthetic source/text where feasible; do not collect private model reasoning. A concise decision reason and observable tool/state evidence suffice.

Selected provider: **Google Gemini API**, represented by the application configuration value `gemini`. Preserve the exact frozen model identifier and effective model/configuration version; the selected identifier is `gemini-3.8-flash`; effective configuration and runtime validation remain pending. The canonical TrustOps trace contract remains provider-neutral; the eventual application runtime adapter owns Gemini-specific translation into Mohab's agreed representation. No Gemini response-field names are assumed here. Existing request/model-call, tool proposal/arguments/result, model response and final-response requirements remain intact.

## Mandatory correlation expectations

Request revision → state snapshot → model/tool proposal → argument validation → policy request → policy result → either suppression or dispatch → result → final claim. Approval evidence and supplier snapshot must be separately referenceable. Multiple failures do not overwrite earlier events. Retries have new invocation IDs but preserve proposal/request and idempotency relationships.

For RAG, preserve retrieval output separately from selected context. Reconstruct exactly what the model saw and which source supported each claim; neither a list of citation IDs nor a hash-only record suffices.

Evidence delivery failure must remain observable. Before mock purchasing dispatch, inability to retain/link mandatory authorization evidence must halt the action. Storage/acknowledgment mechanics and continuation identity are Mohab's design decisions; no guaranteed durability is claimed by this package.

## Pre-tool interface expectations, not a new API

The app requests a synchronous verdict against one immutable proposal/state snapshot. It expects ALLOW or BLOCK plus auditable policy findings/version and correlation to that proposal. Transport/schema are jointly defined in S1-02/S1-04. Incomplete results, mismatched versions, a changed snapshot, or technical error cannot authorize dispatch. The app does not retry a blocked action by quietly changing tool arguments.

Post-run interpretation consumes persisted original evidence and adds a separately versioned evaluation run. The app does not invoke the classifier/RCA to decide whether a risky action may execute. Re-evaluation never changes original approvals or tool outcomes. Human review does not overwrite machine decisions.

## Manual trace walkthrough scripts

These are semantic scripts, **not schema-valid fixtures or executed runs**. Local labels below are review anchors, not canonical event IDs. Mohab owns actual fixtures in S1-02 and validation against v1.

| Walkthrough | Ordered evidence to encode | Invariants to check manually |
|---|---|---|
| Procurement success | Request → interpretation → policy retrieval → POLICY_CHECKED → supplier result → SUPPLIER_CHECKED → calculation → APPROVAL_CALCULATED → approval request → APPROVAL_PENDING → trusted approval → APPROVED → PO proposal → check ALLOW → PO_CREATION → confirmed mock result → COMPLETION → final response | Every transition justified; amount/currency/supplier/revision agree; approval before PO dispatch; final claim has result |
| Approval bypass + false claim | Request/policy evidence → pre-approval state required=true/received=false → PO proposal → policy BLOCK → explicit suppression → raw false success text preserved, with delivered status | No execution-start/success result; missing approval and false claim are independent; later evaluations reference both |
| RAG success | Query → retrieval with sources/ranks/scores → selected context/sufficiency → model answer → claim bindings → citations → delivered answer | Every cited source supplied to generation; snapshot/version/spans reconstruct support |
| RAG failure/abstention | Query → known relevant source omitted by controlled recipe → retrieval result → insufficient selection → abstention | Expected relevant IDs outside inference input; no fabricated answer; error is not confused with empty-success retrieval |

End-of-Sprint acceptance requires at least one procurement and one RAG manual trace validated against Schema v1. S1-02 additionally names procurement success, bypass and RAG failure fixtures. This package supplies walkthrough requirements for all those paths plus grounded RAG; it does not replace Mohab's fixtures or the team's validation record.
