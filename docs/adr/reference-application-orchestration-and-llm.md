# ADR — Reference application orchestration and primary LLM

Status: revision 0.4 — Google Gemini API / Gemini 3.8 Flash (`gemini-3.8-flash`) selected by the user on 2026-10-07; effective configuration, runtime validation and cross-team contract acceptance pending. Decision date: 2026-10-06; clarification date: 2026-10-07. Owner: Nour; reviewers Mohab, Mohamed, Ahmed, Alaa. Number remains unassigned: the 2026-10-15 repository inventory found no ADR index or numbering convention; see the [integration record](../architecture/reference-applications/repository-integration.md). Scope: reference application orchestration and LLM configuration only; does not supersede the backend synchronous-orchestration decision referenced by the supplied project sources; no separate backend ADR was present in the audited repository.

## Context

Proposal U permits LangGraph or an equivalent explicit Python state machine. Two reference apps, five procurement tools, a short linear workflow with approval branching, independent pre-tool enforcement and full trace evidence must fit sixteen weeks. Long-running enterprise approval infrastructure and multi-agent coordination are not required. State visibility is an evidence requirement regardless of framework.

## Alternatives considered

The comparison below is engineering judgment for this project's bounded workflow, not benchmark results.

| Criterion | LangGraph | Explicit Python state machine |
|---|---|---|
| Deterministic control | Explicit nodes/edges support constrained flow; model choice still needs guards | Small transition table and centralized dispatcher directly enforce allowed moves |
| State visibility | Graph state provides a structured representation | Typed state snapshot and transition evidence are simple and explicit |
| Tool-call interception | Put policy/validation before tool node; ensure no bypass edge | One dispatcher intercepts every proposal before body execution |
| Approval workflow | Interrupt/checkpointer facilities support pause/resume | Explicit pending outcome and trusted resume input sufficient for synthetic MVP; persistence not automatic |
| Structured tracing | Framework events still require mapping to TrustOps evidence | Emit semantic boundaries through Mohab's SDK directly |
| Controlled failure injection | Versioned graph/prompt/fixture variants, with immutable enforcement boundary | Versioned proposal/result fixtures at named boundaries, with immutable enforcement boundary |
| Debugging | Graph visualization helps, but adds framework execution semantics | Ordinary Python inspection of state/transition table and dispatch history |
| Implementation complexity | Additional framework lifecycle/checkpointer concepts | Less dependency setup; transitions, bounded retries and resume checks maintained explicitly |
| Sixteen-week feasibility | Feasible, especially if team already knows it | Selected for this small, mostly linear workflow and inspectable evidence |

Official LangGraph documentation confirms that interrupt/resume uses a checkpointer and thread ID. This is useful capability, but not a requirement to adopt the framework for the proposed synthetic approval flow. Source: [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), consulted 2026-10-06.

Provider alternative considered: **OpenAI**, including the previously proposed `gpt-4.1-mini-2025-04-14` configuration, is superseded by the user's Gemini selection. It is retained here solely as decision history, not as an active provider, runtime fallback or routing option. The orchestration comparison above is preserved from revision 0.1 and is not reopened by this provider update.

## Decision

Choose **explicit Python state machine** for Procurement and a sequential, explicitly staged Python pipeline for RAG. In the approved tree, `graph.py` may express the transition map without importing LangGraph. Keep `state.py`, `schemas.py`, `runtime.py`, workflow modules, tools and app-specific instrumentation adapters as the approved homes. No implementation is created in Week 1.

The agent remains LLM-driven where appropriate: request interpretation, policy query formulation, next-tool/argument proposal and response generation. Deterministic orchestration checks proposals, observes tool results and advances valid state. The LLM cannot edit trusted state or execute tools directly. Framework choice is independent of agentic behavior.

Use **Google Gemini API as the single primary LLM provider** for the MVP. Architecture principle: **single-provider, configuration-driven MVP**. The existing explicit Python state-machine decision remains unchanged. No technical incompatibility with this provider-neutral orchestration contract has been identified; runtime compatibility has not been tested.

**Selected model: Gemini 3.8 Flash; exact API identifier: `gemini-3.8-flash`.** User selection recorded 2026-10-07 for Procurement and RAG generation. The [official model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), checked 2026-10-07, lists this as a stable model and documents function calling and structured outputs. This establishes documented capability, not project runtime compatibility. OD-LLM-01 remains PARTIAL pending effective configuration, version-semantics review and live validation. No dated snapshot identifier is invented or immutable backend behavior assumed.

Use application-managed function calling for procurement proposals and structured final-output contracts for RAG. Google documents function calling and structured output capabilities; the selected model/API combination must still be validated against the project's contracts. Sources: [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling) and [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output), consulted 2026-10-06. These sources establish capability categories, not project-account access or measured project performance.

The eventual application runtime adapter translates provider-specific requests/responses into generic tool proposals, arguments, results and model responses. The dispatcher and governance layer retain the existing pre-execution check; Gemini never grants restricted-action authorization. No SDK automatic execution path may bypass that check. Do not introduce provider-selection services, multi-provider abstractions, fallback orchestration or adaptive routing.

## Versionable configuration strategy

| Configuration concept | Required behavior |
|---|---|
| provider | Configurable value `gemini` identifies Google Gemini API, the only active MVP LLM provider; not a routing selector |
| configured model identifier | `gemini-3.8-flash`, selected by the user; stable identifier documented by Google. Review version semantics and preserve returned version where available before reproducible runs |
| returned model identifier/version | Preserve separately when actually available; do not invent a Gemini response field or version |
| API and SDK version | Gemini API surface and SDK selection/version remain to be validated; record the chosen API and dependency lock version when implementation begins |
| model configuration version | Immutable reference including generation parameters, tool-selection configuration and output schema version |
| prompt version/hash | Independently version system/template and rendered context provenance |
| tool schema/catalog version | Model-visible schemas and descriptions frozen with run configuration |
| execution settings | Sequential tool dispatch; bounded calls/retries/timeouts specified in config before implementation; numeric values not invented here |
| credentials | Environment-injected secret, excluded from configuration manifests and traces |

Conceptual configuration only; no executable configuration or secret is created:

```text
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.8-flash
LLM_API_KEY=<environment-secret>
LLM_TEMPERATURE=<application-config>
```

These are application-facing configuration concepts, not claims about SDK environment-variable names. The future adapter may map them to verified SDK requirements. Validate parameter support for the chosen model; preserve the effective configuration. Secrets stay outside Git and trace payloads. Model changes require a new configuration/version reference for experimental comparison; configuration flexibility does not add another active provider.

No live API calls are made for Week 1. Model/account availability, budget and compatibility validation remain OPEN. Do not silently fall back to a moving alias or another provider. If unavailable, halt and revise the same single-provider configuration by reviewed decision. Deterministic mock/replay artifacts may support contract walkthroughs but must be identified as such, never represented as live model performance. Existing artifacts from a different configuration must never be relabelled as Gemini-generated traces.

## Rationale and consequences

This choice keeps tool interception, state evidence and failure injection inspectable with a small dependency footprint. It avoids a framework checkpointing commitment before the simple approval semantics are reviewed. Tradeoff: the team must implement explicit transition, continuation, retry and duplicate protections in Sprint 2 and test them there. Choosing plain Python is not evidence that LangGraph is unsuitable generally.

Gemini is selected for the planned Generative AI and tool-using scenarios, documented structured-interaction capabilities, and generation from application-supplied RAG evidence, while retaining one configurable provider. Reducing expected API operating cost is an MVP objective to assess under OD-LLM-02, not a verified saving or a free-tier entitlement. No performance superiority is claimed.

Consequences and validation gates:

- At the start of Sprint 2, before production application implementation, validate the chosen Gemini model/API behavior and schema compatibility; confirm handling of all five procurement function proposals/results and structured RAG outputs. These checks are outstanding; this documentation task performs no SDK integration or API calls.
- Validate API-project quota, rate limits and billing before workload generation, independently of any Gemini consumer Plus/Pro subscription. No consumer-plan API allowance or free tier is assumed.
- Freeze exact model identifier, effective generation configuration and version references before reproducible traces. Record provider/model/config/prompt provenance, actual response, latency and usage where available; unknown metadata stays unknown.
- Keep retrieval and evidence selection application-controlled. Gemini generates only from supplied retrieved evidence; no provider-managed retrieval replaces the existing pipeline.
- **Embedding model/provider = OPEN DECISION before RAG implementation (OD-RAG-01).** Select independently based on vector-store compatibility, dimensions, retrieval quality, API availability, reproducibility and quota/cost. Selecting Gemini for generation does not select embeddings or add another LLM generation provider.

Contract sign-off requires the exact model/configuration choice and capability review; live compatibility has a separate pre-implementation gate. The [acceptance milestones](../architecture/reference-applications/acceptance.md) define timing, owners and closure evidence. Selection evidence does not close outstanding live validation or authorize production implementation. This task performs neither.

The primary model configuration can be reused by both apps. Ahmed decides whether the same provider/model is acceptable for the fallible semantic evaluator; generator/judge configurations stay separately versioned, and self-evaluation bias must not become ground truth. This ADR does not configure Ahmed's evaluator.

## Assumptions and unresolved decisions

ASSUMPTION: synthetic approval decisions and one active request revision per sequential execution are sufficient for MVP. No long-lived workflow service is needed. Provider access and pgvector availability are unverified.

PARTIAL: OD-LLM-01 model selected; effective configuration, version-semantics review and compatibility remain pending. OPEN: OD-LLM-02 API quota/billing; OD-RAG-01 independent embeddings; four reviewer acknowledgements; calculation permission D3; approval evidence validity/resume contract; configuration budgets; precise schema field mapping and retrieval configuration. See the shared [open-decisions register](../architecture/reference-applications/open-decisions.md). Orchestration is unchanged by this provider update; do not adopt multi-agent orchestration.

## Revision 0.4 — model selection

User instruction: “i will use Gemini 3.8 Flash”. Selection date: 2026-10-07. Configuration parameters (including temperature, thinking level and output limits) have not been frozen or tested. The official model page lists thinking levels low, medium and high; minimal is unsupported. Choose supported settings during configuration review. No live API call, account-access check, team sign-off or project performance result is claimed.
