# Reproduce the Week 1 artifact checks

These helpers inspect authored documents and examples. They do not call Gemini, create embeddings, run a database or purchasing tool, validate canonical Trace Schema v1, establish semantic entailment, or grant team acceptance. Run them against the exact review snapshot identified by [the file manifest](../week1-review-manifest.json), retaining the repository-relative layout. A full copy without `.git` is supported for the two artifact checks.

## Prerequisites

- Python 3.12; the recorded execution used Python 3.12.14. The two newly packaged helpers use only the Python standard library. No installation, API keys or network access is required for their execution.
- The full reviewed `docs` tree, including the application contracts, fixtures, corpus, prompt assets and ADRs. A single downloaded Markdown file is insufficient.
- Git is required only for the optional `--include-git-checks` check in a real checkout.
- The existing prompt validator additionally requires Pydantic; the recorded run used `pydantic==2.14.1`. Dependency setup, if needed, is separate from offline execution and does not change the project lockfile.

## Bash: run both packaged helpers

Replace only the repository path. `REPORTS` is a fresh directory outside the inspected tree. The scripts resolve all input paths from the repository argument, not the current working directory.

```bash
set -e
REVIEW_REPO="/absolute/path/to/trustops-ai"
REVIEW_PYTHON=python3.12
REVIEW_REPORTS="$(mktemp -d)"
"$REVIEW_PYTHON" --version
"$REVIEW_PYTHON" "$REVIEW_REPO/docs/architecture/reference-applications/validation/verify_manual_fixtures.py" "$REVIEW_REPO" --output "$REVIEW_REPORTS/manual-fixtures.json"
"$REVIEW_PYTHON" "$REVIEW_REPO/docs/architecture/reference-applications/validation/verify_corpus_boundaries.py" "$REVIEW_REPO" --output "$REVIEW_REPORTS/corpus-boundaries.json"
```

Optional, only in a Git checkout for this documentation handoff:

```bash
"$REVIEW_PYTHON" "$REVIEW_REPO/docs/architecture/reference-applications/validation/verify_manual_fixtures.py" "$REVIEW_REPO" --include-git-checks --output "$REVIEW_REPORTS/manual-fixtures-with-git.json"
```

The optional check covers staged/unstaged Git whitespace and the owner-document change scope, including the three allowed offline validators. It may correctly reject a working tree containing unrelated application changes. Omit it when reviewing a copied packet; the output explicitly records `git_checks=NOT_REQUESTED`. Fixture assertions still run in full.

## PowerShell: run both packaged helpers

Python's Windows launcher must have Python 3.12 available. These commands are provided for Windows; the recorded execution used Linux.

```powershell
$reviewRepo = 'C:\path\to\trustops-ai'
$reviewReports = Join-Path ([IO.Path]::GetTempPath()) ('trustops-review-' + [guid]::NewGuid().ToString())
py -3.12 --version
py -3.12 "$reviewRepo\docs\architecture\reference-applications\validation\verify_manual_fixtures.py" $reviewRepo --output "$reviewReports\manual-fixtures.json"
if ($LASTEXITCODE -ne 0) { throw 'Manual fixture validation failed' }
py -3.12 "$reviewRepo\docs\architecture\reference-applications\validation\verify_corpus_boundaries.py" $reviewRepo --output "$reviewReports\corpus-boundaries.json"
if ($LASTEXITCODE -ne 0) { throw 'Corpus/boundary validation failed' }
```

Add `--include-git-checks` to the first helper only when inspecting the intended Git working tree.

## Existing prompt validator

[validate_prompt_pack.py](../prompt-pack/validate_prompt_pack.py) remains unchanged. It writes `prompt-pack/validation-report.json`, including Python/Pydantic versions. Run it in a disposable copy so a different environment cannot silently alter the reviewed packet or invalidate its hashes.

Using the Bash variables above, prepare an isolated environment if needed, then copy the docs and run:

```bash
"$REVIEW_PYTHON" -m venv "$REVIEW_REPORTS/prompt-env"
"$REVIEW_REPORTS/prompt-env/bin/python" -m pip install "pydantic==2.14.1"
mkdir -p "$REVIEW_REPORTS/prompt-copy"
cp -R "$REVIEW_REPO/docs" "$REVIEW_REPORTS/prompt-copy/docs"
"$REVIEW_REPORTS/prompt-env/bin/python" "$REVIEW_REPORTS/prompt-copy/docs/architecture/reference-applications/prompt-pack/validate_prompt_pack.py"
cp "$REVIEW_REPORTS/prompt-copy/docs/architecture/reference-applications/prompt-pack/validation-report.json" "$REVIEW_REPORTS/prompt-examples.json"
```

The installation may need package-index access. If Python 3.12 with Pydantic 2.14.1 is already available, use that interpreter and omit environment/install commands. No provider calls occur in the validator. On Windows use a disposable copy and `py -3.12 <copied-path>\prompt-pack\validate_prompt_pack.py` in an environment with the same Pydantic version.

## Read the results

| Helper | Report fields | What PASS means |
|---|---|---|
| [verify_manual_fixtures.py](verify_manual_fixtures.py) | `status`, `check_count`, `checks`, `fixture_event_counts`, `git_checks` | Four authored ledgers satisfy their identity/order, state/tool/approval/PO, source/citation/abstention and local-link checks |
| [verify_corpus_boundaries.py](verify_corpus_boundaries.py) | `result`, `checks` (number), `assertions`, source/snapshot/case counts | Authored source hashes/spans, source references, boundary assumptions and denial JSON are internally consistent |
| Existing prompt validator | `result`, `checks`, `assertions`, Python/Pydantic versions | The documented offline prompt/schema/binding checks pass; this is not a general semantic validator |

For the two packaged helpers: exit 0 means the checks and JSON report write succeeded; exit 1 indicates a validation/input/report-write failure; argparse usage errors exit 2. Validation failures replace a prior report at the selected output path with explicit FAIL. A report-write failure or argument error may leave an earlier file, so always use a fresh output directory and check the process exit code. The output path must be outside the inspected repository; helpers create its parent directory. Inputs are read only. Do not use a historic PASS after a failed rerun.

Check counts depend on the reviewed revision and number of documentation links. They are not quality scores or a fixed contract. Preserve the exact manifest hash, helper hashes and environment alongside reports. The earlier 755/260 counts identify earlier runs, not an assertion that future counts must be identical. See [the packaged reproduction record](reproduction-results.json) for this revision's actual results and [the overall validation record](../week1-closeout-validation.json) for prior evidence and current limits.

## Historical helper-packaging checks

The historical packaging section retained in the reproduction record covers execution from an unrelated working directory against a fresh snapshot without Git, comparison with original fixture assertions, input-file preservation, and rejection of deliberately corrupted fixture/source copies. Those corruptions exist only in temporary verification copies. The primary packet remains unchanged. No installed project dependencies, runtime application code, CI or team-owned contracts are modified by these checks.

## Current refresh — 2026-11-05

The current runs in reproduction-results.json supersede earlier counts for the final owner packet. Manual fixture/link checks, corpus/boundary checks and prompt examples run offline; prompt checks use a disposable copy. The overall report binds the results to the final manifest hash. Earlier corruption/packaging tests remain explicitly historical and are not claimed as rerun. v1.6 schema review findings are external prior review evidence, not a PASS from these owner checks. The v1.5 mapping remains historical. The separate 2026-11-06 v1.6 mapping and its rerun are described below.

## Documentation PR preparation — 2026-11-05

The three packaged Python helpers now follow the repository Ruff rules (0.17.0). Manual-fixture helper closures bind the current fixture explicitly and argument pairing checks equal lengths with strict zip; no fixture expectations or business contracts changed. The prompt helper retains a narrowly documented runtime-union exception. Current reproduction results and the manifest contain the refreshed helper hashes. The PR preparation checks do not grant shared acceptance or execute application behavior.

## v1.6 evidence mapping reproduction

The mapping checker and reports are owner review artifacts. Teammate schema/validator inputs remain external and unchanged. Obtain and extract the [exact joint-review packet](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal). Set these paths to your checkout, extracted `TrustOps_v1_6_Joint_Review` directory, and an output directory outside the checkout:

```bash
REVIEW_REPO=/absolute/path/to/trustops-ai
REVIEW_INPUT=/absolute/path/to/TrustOps_v1_6_Joint_Review
REVIEW_REPORTS=/absolute/path/to/v16-review-output
mkdir -p "$REVIEW_REPORTS"
python -S "$REVIEW_INPUT/inputs/validate_s1_01_schema_v1_6.py" "$REVIEW_INPUT/inputs/updated_schemas_v6.md"
python -S "$REVIEW_INPUT/inputs/run_s1_01_regression_suite(1).py" \
  --spec "$REVIEW_INPUT/inputs/updated_schemas_v6.md" \
  --validator "$REVIEW_INPUT/inputs/validate_s1_01_schema_v1_6.py" \
  --probes-dir "$REVIEW_REPORTS/supplied-cases" \
  --report "$REVIEW_REPORTS/supplied-report.json"
python -S "$REVIEW_INPUT/reproduce_independent.py" --output-dir "$REVIEW_REPORTS/independent"
# The independent command exits 1 while 16 expected results remain unmet.
# Run the following command separately if your shell stops on that expected nonzero exit.
python -S "$REVIEW_REPO/docs/architecture/reference-applications/validation/verify_v16_mapping.py" \
  "$REVIEW_INPUT" "$REVIEW_REPORTS/supplied-cases" \
  --output "$REVIEW_REPORTS/mapping-report.json"
```

Expected current results: baseline 2,106 assertions/0 failures; supplied suite 27/27; independent suite 19/35 expectations met, 16 unmet; mapping integrity 27 rows/69 representative paths/280 checks. See [current observations](../schema-v1.6-review-observations.json) and [mapping report](v16-mapping-report.json). Source hashes are mandatory: a corrected input is a new review, not a reason to overwrite the pinned hashes silently. Runner-generated reports may contain local paths; compare input hashes and semantic outcomes rather than entire report bytes.

These commands were rerun offline on 2026-11-06. The independent subprocess/CLI cross-check from the earlier joint review was not separately rerun. Passing the mapping checker confirms recorded evidence consistency and field presence; it does not repair validator defects or prove runtime safety. Existing provider, policy, approval and continuation gates remain open.

## Free-only and Flash Lite offline candidates

Run `python workload-review/od-llm02-v0.2/validate_workload.py` and `python workload-review/od-llm02-v0.3/validate_candidate.py` relative to the reference-applications directory, or use their repository-relative paths from the repository root. Both helpers print offline validation JSON and send zero provider requests. Redirect their output outside the checkout. Preserve prepared offline reports as historical evidence; current integration results are recorded separately in `validation/flash-lite-integration-refresh.json`. Compatibility and application regression results remain NOT_RUN until their documented private-environment prerequisites are met.
