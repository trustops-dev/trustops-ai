# Ahmed's scoped PR #29 RAG scaffold review

Received from Nour as the text of Ahmed Ragab's message described as sent 2026-11-15; message ID unavailable. Reviewed commit: `ebdefc194d397804dca8238caf64842cb367ecaf`. This is an evaluator-side review of `pipeline.py`, `test_rag_scaffold.py`, and `test_rag_boundaries.py`, not acceptance of canonical emission, semantic evaluation, or a live integration.

| Area | Disposition | Scope and follow-up |
|---|---|---|
| Citation identity, version, quote and span | ACCEPT structural check; integration OPEN | Local `citation_binding` now records document/source/version/chunk/hash and selected `snapshot_ref`, correlated by query ID and matching selected context. Mohab/Ahmed must decide the canonical event mapping and whether `snapshot_ref` is required identity. |
| Insufficient and conflicting evidence | ACCEPT control flow; semantic detection OPEN | Two contradictory selected passages authored as a fixture lead to abstention without generation; a second consistent source is passed to the generator. The fixture supplies the selection judgment. Only the first source is cited; multi-claim or multi-citation semantic support is unverified. |
| Retrieval failure versus zero hits | ACCEPT locally | Typed local errors return `ERROR / RETRIEVAL_ERROR`; zero hits can produce `NO_RELEVANT_EVIDENCE` abstention. Canonical retrieval fault fields in Mohab's v1.11 draft require exact-revision consumer review and integration. |
| Raw error details | AMEND test evidence | An adapter fixture wraps a provider exception with a recognizable sensitive string. Neither events nor result contain it; unexpected programming exceptions still propagate in the existing control test. The fixture is not a production provider adapter. |
| Evaluator integration | OPEN | Obtain accepted canonical event/validator mapping, deterministic query/snapshot/source/citation identity, prompt-slice mapping if context truncation is added, human-reviewed claim/contradiction gold cases, technical retrieval failure separation, and adapter sanitization against the actual provider boundary. |

Local follow-up rerun on the code changes in this review: 39 focused reference-application tests and 74 full tests passed; Ruff check and format passed; mypy passed on 22 source files. Toolchain: pre-existing Python 3.12 virtual environment with pytest 9.1.1, Ruff 0.17.0, mypy 2.4.0. No provider, canonical validator, vector store, or semantic evaluator run. Prior 35/70 counts describe the reviewed commit and remain historical.

OD-09/GD-26 and the direct retrieval-fault amendment remain open. Ahmed's separate taxonomy reconciliation message is recorded in Nour's owner decision packet; no plan decision follows from this scaffold review.

Fresh Windows integration, 2026-11-16, Python 3.12.14 and uv 0.13.0:

- `uv sync --locked --all-packages --all-groups --no-editable --reinstall-package trustops-rag-assistant --reinstall-package trustops-procurement-agent` passed.
- `uv run --locked --all-packages pytest -q tests/unit/reference_applications` passed, 39 tests.
- `uv run --locked --all-packages pytest -q` passed, 74 tests.
- `uv run --locked ruff check .` passed.
- `uv run --locked ruff format --check .` passed, 69 files.
- `uv run --locked mypy` passed, 22 source files.
