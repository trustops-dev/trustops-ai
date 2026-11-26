# Mohamed's Procurement correction review — application follow-up

Mohamed's scoped governance response is [PR #28 at `07fd922`](https://github.com/trustops-dev/trustops-ai/blob/07fd922dea088375b590226db7c0d859bd055708/docs/architecture/governance/response-to-pr29-corrections.md), dated 2026-11-18. It reviews PR #29 at `9735513060b3caf7ec35fb210d0489d7153895bf`. His disposition is **ACCEPT as an isolated synthetic scaffold, with AMEND items**. He reports 27 external read-only probes; he did not run our pytest suite. This document records Nour's subsequent local application changes; it is not a new governance sign-off.

| Mohamed's item | Application follow-up | Evidence boundary |
|---|---|---|
| §2.1 effect state | Confirmed `CREATED` emits `COMMITTED`; confirmed `ALREADY_EXISTS` emits `ALREADY_EXISTING`; ambiguous outcome remains `UNKNOWN`. | These are local `AppEvent` details, not validator-backed canonical traces. |
| §2.2 committed recovery | Require `COMMITTED_RECORD_FOUND`, a PO id, and echoed matching idempotency key and full mock request identity. Abort requires its explicit tombstone and the same identity. Otherwise stay `RECOVERY_PENDING`, without another check or write. | Mock lookup supplies authored evidence, not a durable authoritative ledger. |
| §2.3 gate overrides | The mock can now return different gate decision sequence and policy bundle. Both mismatch cases halt before PO dispatch, in addition to existing supplier/approval version cases. | Atomic consumption and SA-02 remain open. |
| §2.4 wording | Approved supplier with an empty record version halts as `SUPPLIER_EVIDENCE_INCOMPLETE`. | It is distinct from supplier eligibility. |
| §3 replay finding | `ALREADY_EXISTS` without an `original_result_ref` stays `UNKNOWN` / `RECOVERY_PENDING`; a fixture with an original reference shows `ALREADY_EXISTING`. | Nonempty reference is only a local mock condition; canonical resolvability and source linkage still need integration. |

Still open: SA-02 atomic/currentness proof; SA-03 durable approval terminality; OD-06 real gate and read-tool checks; business-payload digest identity; durable root claim, restart/concurrency tests, and canonical effect mapping. `None` from the mock recovery lookup is safe only in this isolated single-process fixture; a production lost-ledger condition must not be treated as a fresh claim. Policy bundle/corpus pairing remains provisional. No runtime or Gemini call is made by these changes. The frontend audit finding and G01 hold are independent gates.

## Fresh Windows integration validation

The new replay fixture exposed a same-key recovery regression: a confirmed ALREADY_EXISTS result returned to pending on resumption. The mock lookup now recognizes its stored original-result reference and the test verifies the same successful result with one check and one create call. Canonical resolvability remains an integration gate.

Python 3.12.14 and uv 0.13.0 were used after `uv sync --locked --all-packages --all-groups`. Imports resolve to this checkout.

- `uv run --locked --all-packages pytest -q tests/unit/reference_applications` passed, 72 tests.
- `uv run --locked --all-packages pytest -q tests/unit tests/contract` passed, 107 tests.
- `uv run --locked --all-packages ruff check .` passed.
- `uv run --locked --all-packages ruff format --check .` passed, 71 files.
- `uv run --locked --all-packages mypy` passed, 22 source files.
- `uv run --locked --all-packages lint-imports --no-cache` passed, all five contracts kept.
