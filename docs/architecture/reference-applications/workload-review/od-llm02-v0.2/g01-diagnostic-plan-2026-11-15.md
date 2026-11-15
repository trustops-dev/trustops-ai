# G01 failure preservation and bounded diagnostic plan

Status: PREPARED FOR MOHAB/ALAA REVIEW; NO THIRD LIVE CALL AUTHORIZED BY THIS DOCUMENT.
Owner: Nour. Baseline review branch: `docs/nour-week1-review-014` at `14ee4a24763ed515aeb1b0a1986893380f4f8f22` (2026-11-15 observation).

## Preserved evidence and precise finding

The [unchanged sanitized summary](bounded-live-results-2026-11-09.json) and exact
session files remain the evidence of the two 2026-11-09 operator-run sessions:

| Session | Exact result-file SHA-256 | C01 | G01 | Remote outcome |
|---|---|---|---|---|
| 01 | `9a4b17c5da09171fdfd794ce07923f93d770e40c59ef9d6d8c24477f5e3461ed` | PASS; prompt-only 6 tokens | `TIMEOUT_OUTCOME_UNKNOWN` | Provider receipt/processing unknown; charge conservatively |
| 02 | `b52e994b5bcdb1736769821626437a75fc29cca5bf0387ff90d94a9d5f8c4b20` | PASS; prompt-only 6 tokens | `PROVIDER_OR_SDK_ERROR`, HTTP status null | Cause and provider receipt unclassified; charge conservatively |

Both runs stopped at G01. G02/G03/E01/E02 were not run; there is no observed
successful generation, structured output, native tool proposal or embedding.
The 25/25 Windows offline suite is operator-supplied test evidence, not live
capability evidence. Do not overwrite either result or infer that the timeout
was rejected by the provider. Historical error labels are retained unchanged.

## Current account observation and headroom limit

On 2026-11-15 at 07:21 UTC, Nour's signed-in AI Studio project view displayed
Free tier, "Set up billing", and the limits recorded in
[the observation](free-tier-observation-2026-11-15.json). Gemini 3.8 Flash showed
5 RPM / 250K input TPM / 20 RPD. Its last-28-days **peak** row showed
1/5 RPM, 6/250K TPM and 2/20 RPD. The one-day view showed a dash for usage,
meaning no reported activity in that view. Gemini Embedding 1 showed
100 RPM / 30K input TPM / 1K RPD and zero 28-day peak activity. The display
name/API identifier relationship is still a candidate mapping.

The UI warns that usage can take 15 minutes to update and presents peak
history, not a current remaining balance. In particular **2/20 does not mean
18 requests remain today**, and a dash does not establish a full unused quota.
Other project consumers/reservations and the provider reset boundary have not
been confirmed. Headroom for a new dispatch is therefore **not established**.
This read-only observation made no API request, modified no billing setting and
retained no screenshot or credential value. Paid usage remains unauthorized
(USD 0); do not enable billing or use a different key/model to evade a limit.

## Diagnostic sequence and stop rules

1. **Mohab: offline classification first.** Review the pinned
   `google-genai==2.34.0` Interactions v1beta G01 request and local transport
   controls at the exact runner revision. Identify the possible pre-send,
   transport, HTTP and response-parse failure stages. Add narrowly typed,
   allowlisted *sanitized* stage/category evidence only if it can be tested
   with `httpx.MockTransport`; retain the historical session bytes and the
   single-request guard. Never persist raw exception text, URL query strings,
   headers, request bodies containing secrets or provider response bodies.
   Verify a timeout is still UNKNOWN and never automatically retried. Return
   the code diff, test cases and the exact safe fields to Nour.
2. **Alaa: admit or amend one diagnostic profile.** Confirm the account's
   observed free-tier limits, shared-consumer plan, conservative preflight
   bucket accounting, and a quota-day reservation. The existing complete
   runner requires operator-confirmed **at least 10 generation-bucket and 4
   embedding requests**; do not pass those flags from the historical peak
   table alone. A proposed *single G01 diagnostic* would permit at most one
   C01 count and one G01 generation attempt, conservatively reserve two
   generation-bucket debits plus a separately reviewed margin, and make **no
   embedding attempt**. This smaller mode does not exist yet; Mohab must
   implement/test it and Alaa must accept its reservation before use. It
   must inherit the 60-second G01 deadline, 900-second session ceiling,
   single in-flight request, 31-second spacing, zero SDK retries, durable
   local attempt debit and stop-on-first-failure behavior.
3. **Nour: contemporaneous admission.** Before any future call, recheck the
   same project/tier and model rows, wait beyond the UI's reporting lag for
   earlier activity to appear, obtain a written no-concurrent-consumer and
   reservation account from the team, and inspect the local durable smoke
   ledger without clearing it. Record the quota-window assumption, current
   usage evidence, unknowns, reserved debit and operator decision. If
   minimum headroom cannot be established, stop; do not invent an available
   request count for CLI admission.
4. **Only after these gates:** run the approved synthetic diagnostic once
   with the private local key; no tool execution or application traffic.
   A 401/403/model-not-found, 429, unsupported configuration, unexpected
   endpoint, timeout or uncertain receipt stops immediately. Retain the
   sanitized result, request/config hashes and local debit; do not replay
   G01 automatically. Mohab classifies the returned safe transport evidence;
   Alaa assesses quota impact. A later complete capability suite is a
   separate admission decision.

## Review replies requested

| Reviewer | Exact question | Closure evidence |
|---|---|---|
| Mohab | Can G01 failures be narrowed to safe stages/categories without exposing secrets or sending extra requests? Can an isolated single-G01 mode preserve durable accounting, one-request enforcement and fail-closed exits? | Exact runner/test revision, safe fields, positive/negative `MockTransport` cases, preservation of unknown timeout |
| Alaa | Is the proposed one-G01 quota reservation acceptable under the shared free-tier project, and what dated evidence is sufficient to attest usable headroom? | ACCEPT/AMEND with debit margin, competing-consumer coordination, model bucket/reset assumptions and stop threshold |
| Nour | Are the required current observations and reviewer responses present just before dispatch? | Dated account/consumer/ledger record and final bounded admission; sanitized post-run report only |

OD-LLM-01/02 stay OPEN. Even a G01 PASS would verify only that synthetic text
probe; G02/G03/E01/E02 and application acceptance would still be unverified.
