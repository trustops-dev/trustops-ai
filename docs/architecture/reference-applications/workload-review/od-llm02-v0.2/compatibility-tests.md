# Bounded compatibility test procedure

Status: PREPARED PROCEDURE; TWO BOUNDED LIVE SESSIONS STOPPED AT G01 on 2026-11-09. [Sanitized evidence](bounded-live-results-2026-11-09.json) records C01 PASS twice (six prompt-only tokens each), then G01 `TIMEOUT_OUTCOME_UNKNOWN` and `PROVIDER_OR_SDK_ERROR` (HTTP status unavailable), respectively. G02/G03/E01/E02 were not run. The 25/25 offline tests are operator-supplied terminal evidence, separate from live compatibility. Credential replacement and old-key absence were observed on 2026-11-07; Nour confirmed local storage. Do not request or include key values. The [executable smoke runner](../../../../../tools/provider_compatibility/README.md) supplies bounded synthetic probes; its prompt-only count does not satisfy full-envelope production token admission. Free-only, USD 0 authorized paid usage remains in force.

## Entry requirements

1. Replacement is observed and local storage is user-confirmed. The local operator verifies the private environment is ready; no credential value in evidence.
2. Confirm selected project is the stated Free-tier project, current quota/headroom, and no concurrent consumers. Reserve the compatibility-day profile before network requests.
3. Use the existing proposed Python 3.12 / google-genai==2.34.0 / Developer API Interactions v1beta profile. Inspect the pinned SDK and official documentation before constructing calls: the existing ADR does not claim exact client retry/timeout knobs are runtime-verified. Disable implicit retries and provider tool execution; if unable to prove this, do not send.
4. Keep store=false, streaming/background disabled and existing safety/profile choices. No Vertex mode, built-in tools, cache, batch API or real Procurement tool dispatch. Use synthetic inputs only.
5. Inspect configured transport and API base/version locally without a network probe. Bound the whole compatibility session to 15 minutes; each generation attempt to the owning ADR's timeout (60 seconds for the two Procurement-style checks; 90 seconds for text/RAG), embedding attempt to 10 seconds. Pacing waits consume session time. Transport must cancel on absolute timeout; an unknown remote result remains an attempt debit.
6. Per test use one native token preflight, no preflight retry. Three generation preflights in total. If native counting for the selected model fails, stop and record a blocker. Each generation test's synthetic input must be <=256 native tokens and total rendered context below its app cap. Keep owning ADR output caps/thinking profile, and do not confuse a short requested answer with a lower provider token budget.
7. Embedding native token eligibility must use the accepted method. If it requires an extra provider call, add it to reservations before starting. Do not silently claim tokenizer counts are provider counts. Do not call a nonexistent embedding count endpoint.

## Cases

| ID | Input / configuration | Pass evidence |
|---|---|---|
| G01 text generation | gemini-3.8-flash, no tools, request `Reply with exactly READY.`; existing RAG generation profile | Successful bounded response; output string captured and checked as READY after trimming; actual returned model metadata recorded if present. Missing usage/model metadata stays unavailable. |
| G02 structured output | Same generation model; existing Procurement extraction profile; ask for object with probe=`trustops-smoke` and quantity=1. Use native JSON response format with schema: object, properties probe:string enum[trustops-smoke], quantity:integer enum[1], both required, additionalProperties=false. | Response is JSON, schema-valid and exact expected values. Unsupported schema/format is a failed compatibility check, not permission to silently relax validation. |
| G03 native function proposal | Same generation model, existing Procurement native proposal profile; expose ONLY synthetic read-only `smoke_lookup` with argument schema object {item_id:string enum[fixture-001]}, required item_id, additionalProperties=false. Prompt `Propose smoke_lookup for fixture-001. Do not claim execution.` Use the endpoint's supported native function selection controls after SDK verification. | Exactly one native function-call event for smoke_lookup with matching schema-valid arguments; no dispatch, approval claim or function result. Printed JSON pretending to be a tool call does not pass. This isolated fixture is not a new application tool or a validation of the five real tool contracts. |
| E01 document embedding | Candidate gemini-embedding-001, RETRIEVAL_DOCUMENT, output dimensionality 768; synthetic input `Synthetic policy: purchases require the configured approval before order creation.` | One finite, nonzero 768-component vector. Record raw norm, apply client L2 normalization, verify normalized norm within 1e-6 of 1. Exact model ID compatibility observed separately from the dashboard display name. |
| E02 query embedding | Same model/dimensions, RETRIEVAL_QUERY; input `When is approval needed?` | Same shape/finite/norm checks; same embedding identity except the intentionally distinct task type. No retrieval-quality or pgvector conclusion from these two vectors. |

The G02/G03 JSON shapes are isolated compatibility fixtures, not replacements for application response/tool schemas. Re-run application-specific prompt and contract checks during integration. A passing smoke suite is not full application acceptance.

## Attempts and error handling

- Initial requests: 3 generation, 3 preflight, 2 embedding. Reserve 2 additional generation and 2 embedding retry attempts, with at most 2 total attempts per individual test.
- Shared two-slot generation-side diagnostic reserve is not preauthorized extra retries. No more than profile totals may be dispatched. Maximum planned model/preflight attempts: 8 generation-side plus 4 embedding-side = 12 before any separately approved diagnostic calls.
- No automatic retries. An explicit eligible retry may be attempted only for a transient transport/server failure, with the existing bounded backoff and remaining session/root/bucket budgets. Authentication/permission/model-not-found/schema errors stop; quota errors stop the batch. Output assertion failures are reported as failures rather than repeatedly sampling until they pass.
- Do not continue dependent tests after a setup/authentication/quota failure. Record unexecuted tests as NOT_RUN, not FAIL or PASS. Timeouts and unknown remote completion remain consumed attempt debits. Retry does not establish the outcome of the first attempt.

## Evidence to return

For each test: start/end timestamps, test ID, root/attempt IDs, requested model/API/SDK/profile and prompt/schema versions, serialized request excluding secrets, actual status/error class, observed response model/usage fields, native input count, attempts/debits, latency, validation outcome, stop reason. Never serialize headers or raw SDK exceptions that might contain credentials. Record unavailable metadata explicitly. For embeddings store shape/norm evidence rather than unnecessary vector dumps.

The [compatibility result](compatibility-results.json) now records the two operator-supplied runs with exact sanitized result-file hashes. Preserve failed attempts and the local ledger; do not infer a successful response, remaining quota, model access, throughput or runtime application budget enforcement from the C01 result.

## Official references checked during preparation

- https://aistudio.google.com/docs/get-started
- https://ai.google.dev/gemini-api/docs/structured-output
- https://ai.google.dev/gemini-api/docs/function-calling
- https://ai.google.dev/gemini-api/docs/embeddings
- https://ai.google.dev/gemini-api/docs/rate-limits

Public documentation describes capabilities; exact pinned SDK call construction, account eligibility and endpoint quota attribution still require verification. No switch to newer SDK/model/API defaults is authorized by documentation drift.
