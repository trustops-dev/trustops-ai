# Reference application architecture overview

FACT — Proposal I/N/V and Repository Architecture ownership rules: Nour owns the two reference applications and controlled scenario inputs. The applications generate observable behavior; backend packages own interpretation, persistence and decisions.

| Responsibility | Single implementation home, planned after Sprint 1 |
|---|---|
| Procurement state, prompts, tool proposal and mock tool wrappers | `apps/procurement-agent/src/trustops_procurement_agent/` |
| RAG retrieval, grounding, citations, abstention | `apps/rag-assistant/src/trustops_rag_assistant/` |
| Attack/failure input definitions | `scenarios/`; scoring remains outside this directory |
| Canonical cross-module contracts | `packages/contracts/` — Mohab coordinates; app payload types are local until jointly standardized |
| Instrumentation and evidence delivery | `packages/instrumentation-sdk/` and `packages/platform-core/` — Mohab |
| Evaluators, classifier and RCA | `packages/reliability-engine/` — Ahmed |
| Policy truth, approvals and reliability decisions | `packages/governance-engine/` — Mohamed |
| Dataset/experiment/gate execution | `packages/mlops/`, `datasets/` — Alaa |
| Diagnostic presentation | `apps/dashboard/` — Malak |

Only `apps/api` is the FastAPI deployment/composition root. Application tools must not embed their own policy engine or backend. App-side SDK adapters translate evidence requirements to Mohab's canonical schema. No backend package imports app implementation. No database or endpoint is specified here on another owner's behalf.

## Three separate outcomes

| Outcome | Meaning | Producer |
|---|---|---|
| Tool authorization `ALLOW/BLOCK` | Permission for one proposed action against a specific state/argument snapshot, before execution | Mohamed's pre-tool interface; app obeys it |
| Application outcome | Mock PO created, waiting for approval, blocked, failed; or RAG answer/abstention/error | Nour's app, supported by actual evidence |
| Reliability `PASS/REVIEW/BLOCK` | Post-run interpretation of persisted trace, evaluator and policy/security evidence | Mohamed's decision engine, after Ahmed's evaluations and Mohab's orchestration |

Human review is a separate later record. It does not retroactively supply purchasing approval or rewrite a previous tool result. A pre-tool ALLOW is neither a successful action nor a reliability PASS. A BLOCK prevents dispatch; an already blocked trajectory may still contain a hallucinated completion claim requiring evaluation.

## Evidence boundaries

App emits request, model interaction, retrieval, state, proposal, policy interaction, dispatch/result and final-output evidence. SDK assigns canonical envelopes. Stored traces feed post-run evaluation/classification/RCA; their results must not be written back as fabricated original app events. Release comparisons reuse versioned inputs and evaluators later (Figure 5).

DECISION — synthetic, deterministic tool fixtures; sequential proposals; explicit Python state machine; Google Gemini API as the single primary configurable LLM provider; Gemini 3.8 Flash (`gemini-3.8-flash`) selected by the user; effective configuration and runtime validation pending (OD-LLM-01). The model interprets requests, forms retrieval queries, proposes tools/arguments and generates grounded text. The runtime owns state transitions and permissions. This preserves a meaningful tool-using AI agent while making unsafe proposals observable and interceptable.

ASSUMPTION — no real purchasing, supplier integration or approval notifications. Approval records are controlled synthetic fixtures consumed through the agreed governance boundary. No message is sent by this task.

Scope: specification only. No LangGraph graph, LLM call, retrieval index, embedding, tool code, FastAPI endpoint, SQL persistence, SDK, evaluator, classifier, RCA, governance implementation, benchmark or CI gate is built. Kafka, Kubernetes, graph databases/GNNs, adaptive routing, multi-agent systems, automated rollback and enterprise IAM remain excluded.
