# Week 2 application closeout · 19 November 2026

The offline application deliverables were reproduced from [PR #29 at `61560bd`](https://github.com/trustops-dev/trustops-ai/commit/61560bda1c13f38355a06838934e8d493587e1f5). The owner packet base for this record is [PR #27 at `14c4262`](https://github.com/trustops-dev/trustops-ai/commit/14c426261cba852c49fd441a1b0c0efc6f942bca).

## Week 2 deliverable tracker

| Owner | Scope | Status | Evidence |
|---|---|---|---|
| Nour El-Rouby | Offline Procurement and RAG scaffolds, initial retrieval index, both happy paths and one validated manual trace per application | Complete | Local reproduction at `61560bd` below and automated trace validation at `decf7cb` |

## Results on the application revision

| Check | Observed result |
|---|---|
| Initial index | Built `corpus-review-s01-fts5-bm25-v1-sqlite-3.53.1.sqlite3` using SQLite FTS5/BM25 on the seven eligible documents. The build reads the pinned manifest and source documents. |
| Indexed RAG happy path | The emergency-leave query retrieved `doc-003@review-r1:0:332` at rank 1. The answer cited `src-003:review-r1` and the test matched the selected passage, offsets and hash. Rebuilding produced identical bytes in the test environment. |
| Procurement happy path | The approved mock request reached confirmed completion. Repeating the same key produced no second effect. |
| Application tests | Both selected tests passed. The repository’s default pytest suite passed all 110 collected tests under Python 3.12.14. |

## Canonical proof fixtures

The verifier explicitly loaded these two manually authored files from [the versioned fixture directory](https://github.com/trustops-dev/trustops-ai/tree/61560bda1c13f38355a06838934e8d493587e1f5/tests/fixtures/traces/week2-v1). The RAG trace covers the laptop-request passage. The indexed emergency-leave query above is a separate test.

| File | Exact-byte SHA-256 | Assertions | Findings |
|---|---|---:|---:|
| `01-procurement-success.json` | `6a2a4340f8fa61cfe6d43ae0debacfee830cca4326bd9f22340b090672cba0b9` | 1,644 | 0 |
| `03-rag-grounded.json` | `122b8c69d7e5ba1698d62226c156ccfdab766a1f7e97a2cfd13f35f7c3896240` | 168 | 0 |

Both fixtures passed independently on the reviewed v1.16 validator at `c645cfc72ef9d718cfe326990059a5ca0a37b3a1` and on the [published validator at `8825055`](https://github.com/trustops-dev/trustops-ai/blob/882505573b3d28db362532e038100a91e9c0ea52/scripts/schema_validation/validate_s1_01_schema_v1_11.py). The published manifest retains the earlier validator hash. The verifier checks the actual Git blob for each pin. Both blob hashes and the package comparison are recorded in [validation-results.json](https://github.com/trustops-dev/trustops-ai/blob/61560bda1c13f38355a06838934e8d493587e1f5/tests/fixtures/traces/week2-v1/validation-results.json).

## Reproduce

From a clean repository checkout, use Python 3.12 with SQLite FTS5 and uv 0.13.0. Run these commands from the repository root.

```sh
git fetch origin refs/pull/29/head
git switch --detach 61560bda1c13f38355a06838934e8d493587e1f5
git fetch origin 882505573b3d28db362532e038100a91e9c0ea52
uv sync --locked --all-packages
uv run --locked --all-packages python -m trustops_rag_assistant.offline_index
uv run --locked --all-packages pytest -q tests/unit/reference_applications/test_procurement_scaffold.py::test_valid_approved_mock_path_and_same_key_no_second_effect tests/unit/reference_applications/test_rag_offline_index.py::test_persisted_search_supplies_grounded_answer
uv run --locked --all-packages python tests/fixtures/traces/week2-v1/verify.py --schema-commit 882505573b3d28db362532e038100a91e9c0ea52
uv run --locked --all-packages pytest -q
```

## Owner reviews and integration scope

- Mohamed accepted the corrected Procurement mock at `163b32f` after 42 read-only probes. His scope covers ordering, early stop, recovery evidence, effect-state vocabulary and prevention of false completion or a second effect. Durable claims, restart safety and enforcement remain open. [Governance review, §6](https://github.com/trustops-dev/trustops-ai/blob/1b7bdf40ab7ea6399119533720fbc6a9fc7db725/docs/architecture/governance/response-to-pr29-corrections.md)
- Ahmed accepted the synthetic RAG structure at `ebdefc1` and requested targeted evidence. PR #29 records the added context, conflict and sanitization tests. Semantic evaluation and integration with the canonical evaluator remain open. [Evaluator disposition and application follow-up](https://github.com/trustops-dev/trustops-ai/blob/61560bda1c13f38355a06838934e8d493587e1f5/docs/architecture/reference-applications/reviews/ahmed-pr29-rag-scaffold-2026-11-16.md)
- These reviews apply to their named revisions. The current reproduction covers offline application behavior and manual trace conformance. Live provider compatibility, runtime trace emission, operative policy release and joint integration acceptance remain open.

## Hosted checks on PR #29

GitHub returned six completed check runs for `61560bda1c13f38355a06838934e8d493587e1f5` on 19 November 2026.

| Check | Conclusion |
|---|---|
| [Dependency review](https://github.com/trustops-dev/trustops-ai/actions/runs/44464642698/job/135359375439) | PASS |
| [Frontend dependency audit](https://github.com/trustops-dev/trustops-ai/actions/runs/44464642698/job/135359375082) | PASS |
| [Secret scan](https://github.com/trustops-dev/trustops-ai/actions/runs/44464642688/job/135359374936) | PASS |
| [Python dependency audit](https://github.com/trustops-dev/trustops-ai/actions/runs/44464642698/job/135359374707) | PASS |
| [Frontend checks](https://github.com/trustops-dev/trustops-ai/actions/runs/44464642616/job/135359374160) | PASS |
| [Python checks](https://github.com/trustops-dev/trustops-ai/actions/runs/44464642555/job/135359373779) | PASS |

### Hosted follow-up on 19 November 2026

All seven hosted checks passed on [PR #29 revision `decf7cb012ceb988c051f656cbd8849af6dde58c`](https://github.com/trustops-dev/trustops-ai/commit/decf7cb012ceb988c051f656cbd8849af6dde58c), including the frontend dependency audit. The [automated Procurement and RAG proof-trace check](https://github.com/trustops-dev/trustops-ai/actions/runs/44533258923/job/135591881923) validated both application fixtures against the published schema commit `882505573b3d28db362532e038100a91e9c0ea52`. The local reproduction results and the six earlier hosted checks above apply to `61560bd`.
