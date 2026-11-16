# Mohamed's scoped Procurement scaffold review

**Source:** Nour-supplied email received 2026-11-16; original send date and message ID unavailable. **Reviewed revision:** PR #29 `ebdefc194d397804dca8238caf64842cb367ecaf`, `workflow.py`, `mock_tools.py`, and `test_procurement_boundaries.py`. Mohamed ran seven external read-only probes, not the repository pytest suite. This is governance review of a synthetic scaffold, not runtime or canonical schema acceptance.

| Area | Governance disposition | Application follow-up in this patch | Remaining gate |
|---|---|---|---|
| Approval and supplier early stops | ACCEPT for current execution; changed request and stale record checks accepted with amendments | Retained early stops; empty supplier version and calculation-reference binding checked | Durable terminality and supersession, SA-03 |
| Post-dispatch exception or ERROR | AMEND: unknown effect, no unsupported FAILED/completion | `UNKNOWN_OUTCOME`, `RECOVERY_PENDING`, no final response; `FAILED` only after explicit mock abort tombstone lookup | Authoritative recovery and canonical effect fields |
| Same-root rerun | AMEND: no second create or check; read-only recovery | Separate `RECOVERY_LOOKUP` seam, original key/payload binding; mock cases for unresolved, committed, aborted and conflicts | Atomic/durable root claim, digest identity, restart/concurrency tests |
| Dispatch currentness | AMEND: compare approval status/version/decision sequence, supplier version, request revision and policy bundle | Distinct stop reasons, including cancelled between check and dispatch; injected mismatched gate version test | SA-02 atomic consumption/currentness proof |
| Version identity | AMEND: policy KB release and executable bundle are distinct | Paired but different IDs proceed; unpaired bundle blocks | Mohab's exact mapping and accepted loader pairing |
| Stub policy evaluation | OPEN for actual enforcement | `check_mode=STUB_CONTRACT_TEST` local event | OD-06 full policy gate/read-tool gating and trace mapping |

The mock still compares whole request objects instead of canonical business-payload digests. Terminal approval memory and root-to-key binding last only for the current mock instance. The in-memory recovery lookup is fixture-authored; it is not authoritative purchasing evidence. No second write is authorized by this design. Mohamed's seven probes are not reproduced by his email; local tests and their execution result are recorded separately. OD-12-OUTCOME/RETRY, SA-02/03 and runtime integration remain open.

## Local validation of the revised patch

Checked 2026-11-16 against cached PR #29 base `c9aa20cb2432660eb9984e0ad0744f11f65a7845`: 100 repository unit/contract tests passed; Ruff lint and formatting passed on Procurement source and reference-application tests; mypy passed on those eight files. The existing local development environment was reused, with PYTHONPATH explicitly pointing at this worktree's Procurement and RAG source directories. No fresh locked environment installation, Windows execution or hosted CI result is claimed.

Additional cases cover RuntimeError, ValueError and OSError after a mock dispatch, raw provider-message exclusion, missing abort-tombstone proof and missing committed-result identity. The recovery event records the local RECOVERY_LOOKUP operation and supplied resolution basis. A canonical adapter still must independently validate the bound key/digest/payload and authoritative recovery evidence. Fresh GitHub access was unavailable; apply against the current branch and rerun repository checks.

## Fresh Windows integration validation

Executed 2026-11-16 with Python 3.12.14 and pinned uv 0.13.0. `uv sync --locked --all-packages --all-groups` passed; Procurement and RAG imports were asserted to resolve under this checkout.

- `uv run --locked --all-packages pytest -q tests/unit/reference_applications` passed, 65 tests.
- `uv run --locked --all-packages pytest -q tests/unit tests/contract` passed, 100 tests.
- `uv run --locked --all-packages ruff check .` passed.
- `uv run --locked --all-packages ruff format --check .` passed, 70 files.
- `uv run --locked --all-packages mypy` passed, 22 source files.
- `uv run --locked --all-packages lint-imports --no-cache` passed, all five contracts kept.

Baseline main `3ef7da1f190cd5a22efdcd6798af59199924bac3`, dev `72e7975384d5e8b32d1e0e68ff4742cce96fa336`, PR #27 `c5b256843054911b798c159ca74b9c156bb39448`, PR #29 `c9aa20cb2432660eb9984e0ad0744f11f65a7845`. No live integration or provider execution was part of these checks.
