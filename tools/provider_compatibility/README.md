# Bounded provider compatibility runner 0.1

Status: IMPLEMENTED AND OFFLINE TESTED; two operator-run bounded live sessions on 2026-11-09 stopped at G01 after C01 passed (see [sanitized owner record](../../docs/architecture/reference-applications/workload-review/od-llm02-v0.2/bounded-live-results-2026-11-09.json)). Offline Windows suite passed 25/25 per user-supplied terminal capture. This developer utility tests
synthetic provider capabilities, not application acceptance or canonical trace compliance.
It does not change the proposed primary model. Default testing targets the alternative
`gemini-3.5-flash-lite`; select `gemini-3.8-flash` explicitly to test the baseline separately.

## Setup and offline checks

Run from repository root in Python 3.12 on Linux, macOS or Windows. The live
runner uses a native nonblocking file lock (POSIX `fcntl` or Windows `msvcrt`). Install these isolated developer dependencies; no application
package or repository lockfile dependency changes are required.

```bash
python3.12 -m venv /tmp/trustops-smoke-venv
/tmp/trustops-smoke-venv/bin/python -m pip install -r tools/provider_compatibility/requirements.txt
/tmp/trustops-smoke-venv/bin/python -m pytest -q tools/provider_compatibility/test_runner.py
/tmp/trustops-smoke-venv/bin/python tools/provider_compatibility/runner.py
```

On Windows PowerShell, use `py -3.12 -m venv .venv`,
`.venv\Scripts\python.exe -m pip install -r tools/provider_compatibility/requirements.txt`,
`.venv\Scripts\python.exe -m pytest -q tools/provider_compatibility/test_runner.py`, and
`.venv\Scripts\python.exe tools/provider_compatibility/runner.py`. The Windows local suite must show
25 passing tests before attempting live execution. The last command is a dry run and requires no credential. Wire tests use `httpx.MockTransport`;
no Google request is sent. Tests cover SDK serialization, retry suppression, continuation
suppression, strict outputs, invalid vectors, durable reservations, timeout charging,
stop-on-failure and sanitized errors. SDK transitive versions are not locked by this utility;
retain the environment's package-version evidence when comparing live results.

## Run locally after verifying free-tier headroom

Use the replacement already stored privately as `GEMINI_API_KEY` in the process environment. On Windows, verify that the same PowerShell session launching the runner sees the variable without printing its value: `python -c "import os; print(bool(os.environ.get('GEMINI_API_KEY')))"`. Set it privately in that process if needed; never paste it into the review packet.
The runner does not read `.env` files, print credentials, or accept a key argument.
Confirm this key belongs to project `gen-lang-client-0848818912`, the account remains Free tier,
and at least **10 generation-bucket requests and 4 embedding requests** are available after
other consumers and reservations. These are operator attestations, not billing/quota API checks.
No paid use, billing activation, fallback, routing or application tool execution is authorized.

```bash
/tmp/trustops-smoke-venv/bin/python tools/provider_compatibility/runner.py \
  --live --model gemini-3.5-flash-lite \
  --confirm-project --confirm-free-tier --accept-smoke-scope \
  --available-generation-requests 10 --available-embedding-requests 4 \
  --output /tmp/trustops-smoke-run-001
```

Supply those headroom arguments only after checking actual availability; the numbers are
minimum admission reservations, not a claim that quota is currently available. Use a fresh
output directory. Exit 0 means all synthetic probes passed; 1 means a probe failed/stopped;
2 means local admission/ledger/setup blocked. The only result file to review is `results.json`.
Do not commit credentials, environment files or raw SDK logs. Review the sanitized result
before sharing it with Mohab/Alaa. A failed call is never automatically replayed.

## Exact scope and accounting

| Operation | Behavior | Maximum attempts |
|---|---|---:|
| C01–C03 | Native prompt-only count before each generation; require 1–256 tokens | 3 |
| G01 | Exact `READY` response | 1 |
| G02 | Native JSON response, exact object with integer quantity | 1 |
| G03 | One native `smoke_lookup` proposal; no handler/dispatch | 1 |
| E01/E02 | Retrieval document/query embeddings, 768 finite components, L2 normalization | 2 |

Eight maximum outbound attempts, zero retries, one in flight, a 31-second pause after each completed worker (therefore starts at least 31 seconds
apart). The v0.2/v0.3 smoke reservations (10 generation bucket, 4 embedding) remain conservative;
unused retry slots are not consumed or automatically released. No application runs accompany
this first smoke session. Each generation/count worker has a hard 60-second local process
deadline; embeddings have 10 seconds; session deadline is 900 seconds. Timeout cancels the
local worker but cannot prove the provider did not process the request.

`~/.trustops-compatibility/ledger.sqlite3` (or `%USERPROFILE%\.trustops-compatibility\ledger.sqlite3` on Windows) durably reserves each session before dispatch and
each attempt before its child starts. A file lock serializes local sessions. On POSIX it is inherited by the child; on Windows the lock is held by the parent process. An unfinished prior attempt incurs a conservative cooldown (last dispatch plus 60 seconds, then a 31-second spacing) before another attempt. Never retry or refund an interrupted run.
At most two reservations are admitted per rolling 24 hours (conservative 20 generation
bucket/8 embedding total, including both candidate choices). Interrupted sessions retain
charges and cannot resume or refund them. Keep this state intact across invocations; do not
remove it to recover quota. Filesystem/ledger failures stop execution. This is a **single
machine smoke ledger**, not Mohab's distributed root-budget implementation. Other machines
and project consumers still require explicit quota coordination. Wall-clock changes can
affect local rolling accounting; time-synchronized host and external headroom checks are required.

## Explicit limitations and follow-up gates

- The pinned Developer API `count_tokens` helper rejects tools, system instructions and
  generation configuration. Counts cover the fixed user prompt only, not the Interactions
  schema/tool envelope. Embedding prompts are fixed short synthetic strings and are not
  natively token-counted here. `--accept-smoke-scope` explicitly accepts these limitations
  for this isolated capability probe. This does **not** relax the production ADR's complete
  token-admission requirement; resolve that integration with Mohab before application traffic.
- The runner does not claim enforcement of the application's 125k/15k input-TPM gates from
  these partial counts. No arbitrary input, history, documents or application prompts are accepted.
- `google-genai==2.34.0` is verified locally for request serialization, not account capability.
  Unsupported model IDs/settings/endpoints fail and stop the run. There is no parameter dropping,
  model substitution, fallback or second endpoint. Safety settings are requested, not claimed effective.
- SDK retries are requested as zero; the pinned SDK normalizes attempt counts differently between API surfaces. A transport-level one-request guard is the decisive enforcement and independently blocks
  hidden retries/redirects/continuations. `automatic_continuation=False` is explicit. Direct HTTPS
  to `generativelanguage.googleapis.com` is required; environment proxies/base overrides are ignored.
- Embeddings use the SDK's synchronous `batchEmbedContents` endpoint with **one input per request**;
  this is not an asynchronous Batch API job. There is no async/background generation or server storage.
- Results persist validation outcomes and normalized-vector diagnostics, not provider-generated
  text, reasoning, headers, arbitrary metadata or vectors. Effective model metadata is unavailable
  in this minimal report; requested model identity must not be treated as observed identity.
- C01 prompt-only count was observed twice; G01 did not pass (unknown timeout and provider/SDK error).
  Model generation access, quota attribution and remaining headroom are unverified. Full Procurement/RAG fixtures, native schema acceptance,
  trace integration and regression checks are separate. A passing suite does not activate Lite.

## Evidence and official sources

Checked on 2026-11-08 against the installed official `google-genai==2.34.0` package:
`models.py` (`_CountTokensConfig_to_mldev`, embed conversion), `_api_client.py` (`retry_args`),
`_gaos/google_genai.py` (retry translation), `_gaos/types/interactions/interaction.py`
(text derived from steps), and generated Interactions request/response types.

- [Official Python SDK](https://github.com/googleapis/python-genai)
- [Pinned SDK release](https://pypi.org/project/google-genai/2.34.0/)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
- [Token counting](https://ai.google.dev/gemini-api/docs/tokens)
- [Embeddings](https://ai.google.dev/gemini-api/docs/embeddings)

Nour owns running and reporting these probes. Mohab reviews endpoint/token-admission integration;
Alaa reviews workload headroom and reproducibility evidence. Shared approval decisions remain open.
