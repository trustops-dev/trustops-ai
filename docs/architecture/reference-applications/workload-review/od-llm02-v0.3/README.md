# Gemini 3.5 Flash Lite development candidate 0.3

Status: CANDIDATE NOT ACTIVATED. Nour authorized evaluating a higher-quota free model, with promotion conditional on successful checks. Current proposed primary remains gemini-3.8-flash; no files here claim a live switch or successful comparison. This is an application-side ADR addendum for review, not a replacement for shared contracts.

## Context and proposed decision

Observed quota for Gemini 3.8 Flash is 20 daily requests. Gemini 3.5 Flash Lite displays 500 daily requests, 15 RPM and 250,000 TPM in the supplied account screenshot. The 25-fold RPD difference motivates evaluation; it is not evidence of equivalent answer quality, available remaining quota or runtime compatibility.

Propose gemini-3.5-flash-lite as the single development primary for both reference applications only after the promotion gate below. Keep Gemini 3.8 Flash solely as an explicitly selected comparison configuration. No automatic fallback/routing, mixed-model conversation or retry model switch. Each run records one immutable model/profile identity. A comparison is a new experiment, never a hidden retry of an uncertain purchasing operation.

Keep gemini-embedding-001 / 768 dimensions / client L2 normalization unchanged. Generation-only model changes do not require re-embedding; embedding/index identities must still be verified independently. No pgvector availability claim or new infrastructure.

## Verified capability versus candidate configuration

Official model documentation identifies gemini-3.5-flash-lite, function calling, structured outputs, a 1,048,576-token input ceiling and 65,536-token output ceiling. The thinking guide lists minimal, low, medium and high. Public capability support does not verify the pinned SDK, API version, safety controls or account access. Sources and retrieval hashes are in references.json.

For a controlled comparison retain the prior application profiles rather than simultaneously tuning prompts and thinking. Explicit medium thinking avoids accidentally using this model's documented minimal default. No latency or quality improvement is claimed.

| Operation | Thinking | App input cap | Output cap | Timeout | Mode |
|---|---|---:|---:|---:|---|
| Procurement extraction | medium | 16,384 | 4,096 | 60 s | Existing input JSON schema |
| Procurement next-tool proposal | medium | 16,384 | 8,192 | 60 s | Native function-call events, existing five tool definitions |
| Optional final candidate | low | 16,384 | 4,096 | 60 s | Existing final JSON schema; disabled by default |
| RAG answer | medium | 32,768 | 8,192 | 90 s | Existing RAG candidate JSON schema |
| Evidence-insufficient pre-abstention | N/A | N/A | 0 | N/A | Deterministic application response; no model call |

Omit temperature, top_p, top_k, seed, thinking_budget, penalties and candidate_count, preserving the previous explicit omission policy rather than inventing effective values. Retain existing safety profile, request storage disabled, no provider history IDs, no streaming/background or provider-managed tools. If a retained setting is unsupported, record incompatibility and propose a separate amendment; do not silently omit it. Root attempt/time limits, schema/ACL validation and governance dispatch boundaries are unchanged.

## Free-only workload proposals

USD 0 paid usage; billing activation and paid fallback are prohibited. Select only one profile per provider quota day. Count preflights conservatively in the generation bucket until exact endpoint accounting is verified. Every dispatched attempt, including failure, timeout and retry, consumes its application budget. Reserve before dispatch, preserve counters across restart/resume, and never reset root counters with the daily provider reset.

| Candidate profile | Generation attempts incl. retries | Preflights | Shared reserve | Total conservative debit / 500 |
|---|---:|---:|---:|---:|
| Compatibility smoke | 5 | 3 | 2 | 10 |
| Application regression: six Procurement + six RAG cases, two runs each | 168 | 108 | 20 | 296 |
| Development: ten Procurement + twenty RAG roots | 160 | 100 | 20 | 280 |

Regression reserves full root caps even if fixtures stop early. Shared reserve is not permission to exceed per-root caps or sample repeatedly until a desired answer appears. Profiles are alternatives, not cumulative. Extra SDK/metadata/token-validation calls require explicit additional debits. The 220 unused slots on a development day are not automatically allocated to other experiments. Other project consumers and provider-side headroom still need confirmation.

Retain one in-flight provider request and two total provider HTTP starts per rolling minute, including embeddings and preflights. This intentionally stays below displayed RPM and existing pilot pacing. Keep generation input TPM <=125,000 and embedding input TPM <=15,000, verified with native admission counts. Stop/defer on quota exhaustion or a wait exceeding an existing deadline. SDK automatic retries must be disabled or accounted for explicitly.

A development day reserves 280 generation-side requests plus 40 query embedding attempts: up to 320 starts, about 160 minutes at two starts/minute before latency and other delays. This is a scheduling estimate, not measured throughput. Indexing remains a separate day: 64 items * two attempts =128 embedding calls, under the existing proposed 200/day ceiling and observed 1,000 RPD. No new index is created by this review.

## Compatibility and application review

Use the existing [bounded procedure](../od-llm02-v0.2/compatibility-tests.md) under an explicit candidate configuration: replace the generation model only with gemini-3.5-flash-lite for G01–G03, retain E01/E02 unchanged. Replacement is observed and local storage is user-confirmed; confirm the local execution environment and quota headroom before running. See the [executable runner and its explicit synthetic-scope limitations](../../../../../tools/provider_compatibility/README.md). Preserve all native preflight, timeout, credential, retry and no-dispatch protections. Candidate smoke profile uses the 500/day bucket; do not overwrite the baseline Flash quota record.

Then run the 12 semantic cases in review-cases.json twice, using existing application schemas/tools and fixtures. These case descriptions are test objectives, not invented canonical payloads. Missing canonical mappings or fixture implementations block the affected case. Real purchasing side effects remain disabled. Count all failed attempts; record every result without cherry-picking. Stop a batch on auth/quota/configuration errors or a critical authorization-boundary failure.

Model-proposal correctness and runtime authorization enforcement are different observations. If the model proposes an invalid write but the application blocks it, the guard passes and the proposal-quality check fails. Do not report model correctness merely because the guard prevented harm. Evaluate groundedness and citations against the selected evidence; do not use model self-reported approval, status or confidence as truth.

Optional Flash 3.8 comparison: choose at most four matched single-call fixtures on a separate comparison day, reserving four generation attempts plus four preflights and two shared slots (10 of 20). No full Procurement root is hidden inside a single-call comparison. Hold prompt, evidence, schemas and requested thinking fixed; record model-specific observed metadata. Never pool results across models without labels. This comparison is optional; no equivalence or superior-quality claim is needed to accept a suitable development candidate.

## Promotion and rollback

All compatibility cases must actually pass; required response/tool schemas and critical authorization/citation/abstention boundaries must hold in the recorded application cases. Any failing or unimplemented case remains visible. This small suite is an engineering entry gate, not a statistical reliability baseline or OD-15 threshold.

Nour records application suitability; Mohab confirms interface, schema and SDK/accounting fit; Alaa ACCEPTs/AMENDs the workload and experiment lineage. Existing Mohamed approval/policy decisions remain unresolved where applicable; candidate review cannot close them. Promotion requires versioned profile/prompt/config references and a current quota/headroom check. Until then candidate_live_execution_enabled remains false in this proposal.

When approved, update the provider ADR's selected-model matrix and configuration example, access record, active workload, decision register, handoffs, prompt manifest model bindings and affected validation reports. Preserve the Flash baseline and earlier reviews as historical. Pin a single model per run. Rollback is an explicit configuration revision between executions after checking the baseline's 20/day allowance, not an in-flight retry or purchasing replay.

## Alternatives and tradeoffs

Remain on Flash: least configuration change but severe daily iteration constraints. Adopt Lite after evidence: more quota but possible task-quality differences and revalidation effort. Paid access conflicts with Nour's requirement. Automatic routing expands scope and undermines a simple reproducible baseline. Local model migration is outside this proposal.

## Reproduce

```sh
python docs/architecture/reference-applications/workload-review/od-llm02-v0.3/validate_candidate.py
```

Offline checks validate planning only. Live results remain NOT_RUN in results.json. No API key is included and no live requests have been sent.
