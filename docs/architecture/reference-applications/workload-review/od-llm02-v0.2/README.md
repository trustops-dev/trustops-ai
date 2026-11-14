# Free-only workload candidate 0.2

Status: PROPOSED; Alaa workload acceptance and runtime compatibility pending. Prepared 2026-11-07 against the commit recorded in workload-candidate.json. On 2026-11-09, [two bounded sessions](bounded-live-results-2026-11-09.json) passed C01 prompt-only counting and stopped at G01 with distinct failures. No generation, structured output, function proposal or embedding probe passed live. This supplements the existing provider and execution-budget ADRs; it does not change their root limits, canonical schemas or selected models.

## Evidence and decisions

Nour owns project gen-lang-client-0848818912 (number 830049341899), requires free-only use and authorizes USD 0 paid spend. User-supplied screenshots show Free tier; Gemini 3.8 Flash: 5 RPM / 250,000 TPM / 20 RPD; Gemini Embedding 1: 100 RPM / 30,000 TPM / 1,000 RPD. Date is receipt date, not an independently verified capture timestamp. Displayed limits do not establish remaining quota, exact endpoint accounting or successful model access.

Keep gemini-3.8-flash, existing SDK/API candidates and gemini-embedding-001 / 768 dimensions. The embedding display-name/API-ID match remains unverified. No Flash Lite fallback, key rotation to obtain quota, paid upgrade, batch API or managed tools. The previous USD 10 allocation is superseded; historical paid-price arithmetic is retained only as historical hypothetical evidence. Runtime enforcement is NOT implemented by this document.

## Proposed admission profiles

Daily profiles are alternatives, not additive. A quota day is the provider's quota window, not an arbitrary execution or local process day; verify its reset definition before runtime use. Existing root identity, counters and effect fences persist across day boundaries. Do not reset root budgets when the provider quota resets.

| Profile | Generation attempts, including retries | Preflights | Shared reserve | Unallocated | Conservative daily debit |
|---|---:|---:|---:|---:|---:|
| Compatibility only | 5 | 3 | 2 | 10 | 10 |
| Procurement only: one root | 12 | 8 | 0 | 0 | 20 |
| RAG only: five roots | 10 | 5 | 2 | 3 | 17 |
| Mixed, conditional | 18 | 11 | 2 | 0 | 31 until preflight exemption verified; 20 after |

Compatibility has three first-attempt generation checks, two shared explicit generation retry slots, two first-attempt embedding checks and two shared embedding retry slots. Retry slots are reservations, not instructions to retry automatically. There is no application workload on that day. After compatibility passes, choose a Procurement-only or RAG-only day. Procurement-only has no spare allowance: decline if prior usage or other consumers leave less than the required reservation. No guarantee all reserved calls will be necessary or complete within existing deadlines.

The conditional mixed profile has one Procurement root (12 generation attempts), two RAG roots (4), and two diagnostic generation attempts (2). Its 11 preflights are budgeted separately and included in pacing. It is disabled until provider-specific evidence proves they do not debit generation RPD. This is not a proposal to drop preflight checks.

The earlier 2 Procurement + 5 RAG estimate is 17 calls before retries/extra logical operations. Worst-case generation reservation is 2*12 + 5*2 = 34, plus up to 21 preflights. It is not an admissible guaranteed daily plan. The previous 10 Procurement + 20 RAG/day estimate needs 80 generation calls before retries and cannot fit 20 RPD.

## Enforcement specification (proposed, not executed)

- One in-flight provider request across this pilot; at most two provider HTTP attempts per rolling minute, minimum 30 seconds between starts. Include generation, preflights, embeddings and any metadata calls in pacing. Preserve tighter root deadlines: if the wait cannot fit, terminate/defer admission rather than extend execution.
- Track RPM, input TPM and RPD separately for each actual provider bucket. Proposed pilot token caps: generation 125,000 input tokens/minute; embeddings 15,000 input tokens/minute. Native counts are required; character estimates do not establish token eligibility. Unknown embedding-native validation method remains an admission blocker, not permission to omit validation.
- Until preflight classification is verified, reserve each preflight against the generation 20/day cap conservatively. Unknown extra provider calls also need explicit admission and accounting. No automatic SDK retries. Every dispatch, failure, timeout and explicit retry debits the application's quota ledger; uncertain provider receipt is not refunded.
- Atomically reserve worst-case remaining per-root calls before admitting a root. Spend from that reservation, never debit it twice. Release only unsent capacity after definitive terminal closure. Outstanding/unknown attempts remain charged. Unknown quota-sharing/headroom or unavailable durable accounting fails closed. These are requirements for Mohab's ledger implementation, not a new implementation here.
- Overall root attempt caps remain Procurement 12 generation attempts plus 8 preflights; RAG 2 generation attempts plus 1 preflight and 2 query embedding attempts. Pacing does not refill root budgets. A day reset never authorizes replay of purchasing writes.
- On 429, record quota exhaustion, stop the batch and defer new work. Do not consume every remaining request in retries. Never switch to a paid model or enable billing. No paid authorization exists; a numeric budget field alone is not provider-side billing enforcement.
- Respect quota shared with teammates, manual experiments and any other project consumers. Dashboard historical peak zero is not a live remaining-balance guarantee. Provider refusals can occur below displayed limits; avoid claiming guaranteed throughput.

## Embedding/index allowance

Separate index day: at most 64 prepared items, at most two attempts each = 128 reserved embedding calls; proposed pilot embedding ceiling 200/day, below the observed 1,000/day. No overlap with application/smoke runs. One item per request, native input <=2,048 tokens, dimensions 768. At two requests/minute, 128 starts span at least 63.5 minutes; provider latency/validation can add time. Actual chunk count is unknown. Keep model/task/preprocessing/normalization identity and index version immutable; reuse only a valid existing index rather than rebuilding it on every query. No claim of pgvector availability is made.

## Review requests

- Alaa: ACCEPT/AMEND profiles, conservative preflight accounting, reserved headroom and smaller experiment schedule. Prior acceptance of principles does not approve these numeric rows.
- Mohab: verify quota bucket accounting, SDK retries, durable reservations, resume behavior and embedding storage/model mapping. Return evidence, not only a field mapping.
- Nour: replacement observed and private storage confirmed; identify all project consumers, run bounded compatibility checks when prerequisites are met and record actual outputs/usage.

## Reproduce offline checks

From repository root:

```sh
python docs/architecture/reference-applications/workload-review/od-llm02-v0.2/validate_workload.py
```

This validates planning arithmetic only. It does not implement a ledger or make API requests. See compatibility-tests.md and compatibility-results.json for blocked live checks. During integration refresh current decision/handoff references, affected validators and review-manifest hashes. No existing validation result is claimed to cover this new candidate.
