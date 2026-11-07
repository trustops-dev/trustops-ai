# API ownership, quotas and workload candidate — OD-LLM-02 / OD-12-BUDGET

Version **0.1**, prepared **2026-11-06** against PR #27 commit `d07d23338090e1106bdf55645643daa6fb62eb1c`. **PROPOSED; NOT AUTHORIZED FOR LIVE EXECUTION.** This is Nour’s workload/access preparation in response to Alaa review items ALA-04/05/06/07/08. It does not close the account, numeric-budget or compatibility gates.

## 1. Ownership and evidence status

| Role or fact | Current record | Next action |
|---|---|---|
| Application workload preparation | Nour | Own and revise the estimate; identify the actual account owner |
| API project owner | **UNCONFIRMED — name not supplied** | Nour obtains the owner’s name/role and confirmation |
| Access administrator | **UNCONFIRMED** | Actual owner identifies who grants access |
| Billing/spend approver | **UNCONFIRMED** | Identify who accepts the proposed allocation |
| Reproducibility/workload reviewer | Alaa | Review assumptions and actual quota evidence; candidate support is not quota confirmation |
| Compatibility/storage reviewer | Mohab | Verify adapter/interface and target storage within his scope; not assumed to administer Google billing |
| Project ID, environment, billing tier and access | **UNCONFIRMED** | Obtain non-secret account evidence |
| Actual RPM/TPM/RPD and shared-project headroom | **UNCONFIRMED** | Inspect the selected project/model in AI Studio with the owner |
| Actual spend / measured usage | **NOT MEASURED** | Record after an authorized bounded run |

Use [access-owner-record.json](access-owner-record.json). Unknown fields are null; neither Nour’s application role nor Alaa’s review establishes ownership of an API project. No credentials, API keys or billing-account/payment details belong in this record.

The actual owner cannot be identified from the currently available documents or email. Nour needs: owner/admin name, non-secret project/environment identifier, billing/tier status, applicable dated model quotas and approved budget. If no project exists yet, explicitly record that instead of inventing an owner or entitlement. This task creates no Google project and enables no billing.

## 2. What is confirmed, proposed or unverified

| Evidence class | Meaning |
|---|---|
| Verified document fact | Current ADR proposes Procurement 8 logical generations / 12 attempts and RAG 1 / 2. It is not an approved runtime limit. |
| Verified public documentation | Listed public prices and rate-limit semantics were retrieved on 2026-11-06; this establishes neither project entitlement nor actual billing. |
| Planning estimate | Execution counts, average native tokens, 10% retry reserve, 64-item indexing capacity and one pilot-wide concurrent attempt are assumptions for Alaa’s review. |
| Account-confirmed fact | None supplied for owner, project access, tier, quotas, billing or applicable rates. |
| Measured result | None; no provider, embedding, database, tokenization or runtime execution occurred. |

## 3. Candidate workload and per-operation assumptions

All token figures below are **estimated native provider tokens**, not measured tokens and not the `cl100k_base` chunking units. Full generation input includes instructions, schemas/tool declarations, trusted context/history and source text. Estimated billable output includes visible output plus billable thinking **once**; it is not just the visible JSON size.

| Operation | Proposed volume basis | Input tokens per attempt | Billable output tokens per attempt | Retry treatment |
|---|---|---:|---:|---|
| Procurement generation | 6 logical calls/root: 1 extraction + 5 tool proposals; optional final phrasing disabled | 4,000 average | 2,000 total | 10% aggregate planning reserve; each logical call still allows at most 1 eligible retry and root cap remains 12 attempts |
| RAG generation | 1 logical call/query; assume every query generates for planning | 8,000 | 2,000 total | 10% reserve; inherited max 2 attempts/query |
| Generation token preflight | 1 per logical generation; no preflight retry | Counts assembled input; HTTP workload shown separately | N/A | Not another generation; no duplicate token billing assumed |
| RAG query embedding | 1 item/query | 128 | N/A; embedding vector is not generated output tokens | 10% reserve; inherited max 2 attempts/query |
| Initial corpus embedding | 1 separate build, planning ceiling 64 prepared items; 1 item/request | 1,024 | N/A | 10% reserve; proposed offline cap 2 attempts/item |

There are 8 source documents in the current corpus manifest. **64 items is an illustrative pilot capacity, not a measured chunk count.** Substitute the actual chunk count and prepared native token lengths after the approved loader/chunker exists. Document input includes any title/section header. Both query/document input must pass the applicable 2,048-native-token admission limit; the query’s separate 1,024 chunker-token limit remains unchanged.

Native embedding-token validation is still an interface decision. No unsupported embedding count endpoint is invented. If admission uses extra provider calls, add their requests/quota/cost before accepting this workload. Current totals explicitly exclude that unresolved overhead.

Procurement policy lookup remains a mock read with zero embedding calls. Business tools, pre-tool authorization checks, SQL searches and trusted observation/recovery are separate non-generation operations; this calculation does not hide them inside model attempts or authorize their execution. It does not retry approval/PO creation writes. Required approval continuations share original root counters.

## 4. Execution windows

| Candidate window | Days | Procurement roots | RAG queries | Separate index builds |
|---|---:|---:|---:|---:|
| Initial bounded smoke | 1 | 2 | 5 | 1 |
| Development week | 5 | 50 (10/day) | 100 (20/day) | 1 |

These are separately costed planning scenarios, not automatic scheduled jobs. The development-week estimate excludes the separate smoke window. If both run, add their application activity and count actual index builds once where legitimately reused. No cache or deduplicated embedding reuse is introduced; repeat builds/configuration changes are additional workload.

### Daily development workload — includes 10% retry allowance

| Category | Logical operations/day | Admitted attempt estimate/day | Token input/day | Billable generation output/day |
|---|---:|---:|---:|---:|
| Procurement generation | 60 | 66 | 264,000 | 132,000 |
| RAG generation | 20 | 22 | 176,000 | 44,000 |
| Generation preflight | 80 | 80 | Counted request representation; not added again to billed generation input | N/A |
| Query embedding | 20 | 22 | 2,816 | N/A |
| Separate index build | 64 items/build | 71/build | 72,704/build | N/A |

The 10% value is a planning reserve, **not an observed retry rate or permission to force retries**. Round up separately for each operation category/day. Failures, timeouts and unknown responses do not refund root debits. Disable hidden SDK retries or include every attempt in the same accounting.

### Five-day estimate versus conditional cap exposure

| Quantity | Planning estimate with retry reserve | Exposure at inherited/proposed caps |
|---|---:|---:|
| Procurement / RAG executions | 50 / 100 | 50 / 100 |
| Logical generation operations | 400 | 500 |
| Generation attempts | 440 | 800 |
| Generation input tokens | 2,200,000 | 16,384,000 |
| Generation billable output tokens | 880,000 | 6,553,600 |
| Generation preflight requests | 400 | 500 |
| Query embedding attempts | 110 | 200 |
| Query embedding input tokens | 14,080 | 409,600 |
| Separate index embedding attempts | 71 | 128 |
| Index embedding input tokens | 72,704 | 262,144 |
| Total embedding input tokens | 86,784 | 671,744 |
| **Modeled provider HTTP attempts** | **1,021** | **1,628** |

Cap exposure uses Procurement 12 attempts × 16,384 input / at most the largest 8,192 output profile, and RAG 2 attempts × 32,768 input / 8,192 output. Applying the largest Procurement output cap to all attempts intentionally overestimates extraction (whose cap is 4,096). Runtime deadlines can prevent reaching all caps. The figures are conditional token exposure, **not an absolute invoice ceiling**: exact output/thinking-limit enforcement still needs compatibility validation and unpriced items remain outside the subtotal.

## 5. Concurrency and quota admission proposal

- Retain **1 client-owned attempt per root**. For the initial pilot, additionally propose **1 in-flight provider request across Nour’s apps and indexing job**, with no overlapping index build/application batch and no parallel fan-out.
- Request a conservative pilot pace of **at most 2 modeled provider HTTP admissions per rolling minute**, including preflight, embedding and retries. This is an application proposal, not a confirmed provider allowance or implemented limiter.
- After obtaining account evidence, the allowed request rate for each relevant quota bucket is the minimum of the proposed pace, the owner-allocated headroom, and a proposed 50% share of that bucket’s confirmed RPM. Round request capacity down; if it becomes zero, do not dispatch. The 50% share requires the project owner/Alaa agreement.
- Reserve the exact admitted request’s counted input against confirmed model/project TPM headroom before I/O; also respect RPD and any applicable daily token/spend/other quota. Do not infer requests/minute from concurrency or minimum runtime deadlines.
- At 2 generation requests/minute, illustrative input demand is up to 16,000 tokens/minute using the largest average input estimate, or 65,536 at the largest configured input cap. These are workload demands, **not confirmed TPM entitlements**. Embedding and preflight bucket accounting must be verified separately.
- Google’s documented limits are per project, not per API key, and may differ by model/tier. Other project consumers must be included; separate keys do not establish extra capacity. Check the actual AI Studio project’s limits. RPD follows midnight Pacific time, not the Cairo calendar day; enforce the provider window, including daylight-saving changes.
- The 1,021 modeled requests imply roughly 8.5 hours of rate-only allowance at 2/minute, spread across the five-day window plus the separate index job; actual latency, quota waits and extra admission work can extend this. This is not a throughput benchmark or a completion guarantee.
- Preserve root/profile identity, counters, reservations, leases and checkpoints across restarts/resumes; fail closed if required accounting is unavailable. Actual concurrency/ledger enforcement remains Mohab’s implementation contract and shared review.

No live workload is admitted while account quotas/access are unknown. A 429 does not justify raising these limits, resetting counters, switching keys/projects or replaying a purchasing write.

## 6. Public-price estimate versus actual account costs

Public **standard paid text** prices checked 2026-11-06:

| Item | Public USD / 1M tokens through 2026-12-31 | Listed generation change from 2027-01-01 |
|---|---:|---:|
| gemini-3.8-flash input | 0.75 | 1.50 |
| gemini-3.8-flash output, including thinking | 3.75 | 7.50 |
| gemini-embedding-001 input | 0.15 | Reverify; no future embedding price guarantee inferred |

Sources: [official pricing](https://aistudio.google.com/docs/pricing#gemini-3.8-flash), [embedding pricing](https://aistudio.google.com/docs/pricing#gemini-embedding), [rate limits](https://aistudio.google.com/docs/rate-limits), [token counting/usage](https://aistudio.google.com/docs/tokens). Retrieval dates/content hashes and contract input hashes are in [references.json](references.json). The web viewer could not parse the official Markdown responses; the official redirected documents were read over HTTPS. These sources do not establish our account tier or effective price.

`Modeled token subtotal = (generation_input × input_rate + billable_generation_output × output_rate + embedding_input × embedding_rate) / 1,000,000`.

| Scenario | Current public-price token subtotal | Conditional cap exposure | Generation-price-change sensitivity |
|---|---:|---:|---:|
| Smoke, including one 64-item planning build | $0.2390 | $1.6275 | $0.4670 estimate / $3.2127 cap |
| Development week, including one build | **$4.9630** | **$36.9648** | **$9.9130** estimate / **$73.8288** cap |

Future sensitivity changes only the published generation rates and holds today’s embedding rate as an explicit assumption. Reprice the actual execution dates; do not extrapolate this estimate across the full 16-week project or assume promotional prices persist.

**Budget request for review:** propose a **USD 10 development-week planning allocation** against the estimated token subtotal. This is neither authorized spend nor an implemented cap. The cap-exposure case exceeds it substantially and is not an approved execution plan. Additional runs, larger contexts, repeat index builds and quota changes require review. No live run starts until the project/billing owner confirms an allocation and the adapter’s accounting/admission controls are agreed. Provider budget notifications are not assumed to enforce a hard stop.

**Excluded or unconfirmed:** preflight fees/quota classification, any additional embedding-admission provider calls, tax, infrastructure/database/storage/network, account-specific adjustments and malformed-vector/rebuild work. No free-tier entitlement, credits, cache discount, managed tools or Batch API discount is assumed. Unknown failed-call usage remains unknown; the planning reserve conservatively charges a full estimated request per retry without asserting actual billing.

Do not sum output and thinking fields blindly: normalize returned usage according to the exact validated endpoint schema and include billable thinking once. Store missing usage explicitly unavailable, with model/config/request identity, rather than writing zero. Actual charges must be reconciled with account evidence.

## 7. Required evidence and reviewer responses

| Item | Owner | Evidence to return | Current status |
|---|---|---|---|
| Actual project/admin/billing owner | Nour obtains confirmation from the actual owner | Name/role, non-secret project/environment, access/billing/tier status | UNCONFIRMED |
| Quotas and shared headroom | Project owner + Alaa | Dated project/model RPM/TPM/RPD/other limits, other consumers and agreed allocation | UNCONFIRMED |
| Workload assumptions and numeric limits | Nour proposes; Alaa reviews; Mohamed reviews purchasing boundaries | ACCEPT/AMEND the volumes, retry allowance, concurrency/pace and numeric profiles | PROPOSED |
| Price applicability / spend authorization | Actual billing owner + Nour/Alaa | Dated applicable rates/currency, allocation and approval evidence | UNCONFIRMED |
| Token preflight / usage mapping | Mohab + Nour | Complete assembled-input coverage, correct output/thinking aggregation, endpoint/preflight quota accounting | PENDING |
| Native embedding input admission | Mohab + Nour | Verified count/admission method and any additional request/cost overhead | PENDING |
| Embedding/index compatibility | Nour integration; Mohab storage; Alaa/Ahmed lineage/evaluation | Actual item counts, prepared native token counts, compatible config/index and 768-dimensional valid vectors | PENDING |
| Ledger and exhaustion | Mohab; Nour app profile; Mohamed transaction scope | Durable attempts/reservations/resume/lease and unavailable-accounting behavior; later runtime tests | PENDING |

This prepares Nour’s workload proposal for Alaa; it **does not close ALA-05/ALA-08, OD-LLM-02, OD-12-BUDGET or other shared gates**. No review email is sent by this task.

## 8. Reproduce the offline arithmetic

From the repository root, write reports outside the checkout:

```bash
python -S docs/architecture/reference-applications/workload-review/od-llm02-v0.1/calculate_workload.py --output ../workload-estimate.json
```

Compare the results with [calculation-results.json](calculation-results.json). The [candidate JSON](workload-candidate.json) supplies all planning assumptions; `Decimal` is used for USD arithmetic and retry reserves round up per category/day. This script has no API access and grants no execution permission. After changing assumptions, regenerate results, review the effects, and refresh the packet manifest. Existing numeric runtime-budget ADRs are preserved as proposals.
