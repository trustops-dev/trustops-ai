# Activating future repository checks

## Current status

All nine files in `.github/workflow-templates/` are **not configured / inactive**.
They do not run on pushes and do not create status checks. The six existing
required checks remain the current baseline. No application, database, container,
browser test, evaluation data, or coverage dependency is implemented by this setup.

GitHub discovers YAML workflows in `.github/workflows/`; these templates live
outside that directory and end in `.yml.template`. See the
[GitHub workflow syntax reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

Paths and script interfaces below are proposed activation contracts. If the
implementation chooses different paths, update the template and this guide in
the same PR. Do not create empty files just to satisfy prerequisite checks.

## Activation checklist for an implementation PR

1. Add the working feature, tests, fixtures, and locked dependencies first.
2. Choose only the template(s) for that feature. Move each into
   `.github/workflows/` and remove `.template` from its name. For example:

   ```sh
   git mv .github/workflow-templates/abuse-case-tests.yml.template .github/workflows/abuse-case-tests.yml
   ```

3. Replace every `REPLACE_...` value, review proposed paths, matrix entries,
   action SHAs, tool versions, timeouts, and dependency setup. Remove the inactive
   header comments. Compare shared setup with the maintained Python/frontend CI.
4. Run the workflow's commands locally. In the PR, show both a successful case
   and evidence that a relevant defect causes failure (for example, a rejected
   request becoming allowed, an unmet quality threshold, or a broken migration).
   Revert intentional defects before the final commit.
5. Keep the PR triggers for both `main` and `dev`. The new workflow will run on
   the implementation PR; it need not be merged first. Tests must execute real
   assertions, not only collect, skip, or report success. Pytest and Playwright
   must retain their failure behavior when no tests are found. Reviewers should
   also reject a suite whose relevant cases are all skipped.
6. Update the status table below, `testing.md`, and local setup instructions with
   the actual commands and scope. Include any non-secret environment example
   values needed by developers.
7. Obtain Code Owner review and merge only after existing and newly activated
   checks pass. If `dev` is used, sync the workflow and its implementation there.
8. The repository owner then adds the stable job names to branch protection on
   each branch containing the implementation. Required matrix check names must
   match the implemented rows. Keep the six baseline checks required.

Activation is explicit: pushing code into a reserved folder alone does not enable
a template. No prerequisite-detection job, `continue-on-error`, `|| true`, or
successful fallback may hide broken or missing implementation after activation.
Avoid path filters on required workflows: GitHub can leave their checks pending
when the workflow is skipped. See
[GitHub's skipped workflow behavior](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs).

## Activation map

All entries are inactive until their implementation PR updates this table.

| Template | Check name after activation | Required implementation |
| --- | --- | --- |
| `integration-tests.yml.template` | `API integration tests` | Standalone test stack, real migrations, integration and API suites |
| `compose-config.yml.template` | `Compose config` | Development and standalone test Compose files with documented interpolation values |
| `build-images.yml.template` | `Build image (component)` | Working Dockerfiles for the retained matrix rows, root `.dockerignore` |
| `ui-e2e.yml.template` | `Browser tests` | Playwright configuration, pinned runner, working UI flow and browser tests |
| `abuse-case-tests.yml.template` | `Abuse-case tests` | Actual controls and security behavior tests |
| `ai-quality-gate.yml.template` | `AI quality gate` | Evaluator, versioned cases, thresholds, and report contract |
| `python-coverage.yml.template` | `Python coverage` | Python behavior tests, coverage dependency, source configuration, agreed threshold |
| `frontend-coverage.yml.template` | `Frontend coverage` | Frontend behavior tests, matching Vitest coverage provider, source selection and threshold |
| `cli-smoke.yml.template` | `MLOps CLI smoke` | Installed console entry point with working `--help` |

## API integration and Compose

- Create root `compose.yml` for development and `compose.test.yml` as a
  **standalone** isolated test stack. The templates validate each separately.
  If the project instead chooses an override file, change every validation,
  startup, log, and teardown command to use the same ordered `-f` file list.
- The integration template expects PostgreSQL on `127.0.0.1:5432`, database/user
  `trustops_test`, and disposable password `trustops_ci_only`. Map these environment
  values into the test service. Use only ephemeral CI data and volumes. Pin the
  PostgreSQL/pgvector image to a reviewed version and digest at implementation time.
- Define real service health checks. `docker compose up --wait` is only useful
  for readiness if those health checks test the required dependencies. Do not
  use a fixed sleep as the database readiness check.
- Implement `scripts/ci/migrate-test-db.sh` to read `DATABASE_URL`, apply the real
  migration chain to the disposable database, create/verify required extensions,
  and return nonzero on any error. It must not replace migrations with test-only
  table creation. Run it without production credentials.
- Add executable tests to **both** `tests/integration` and `tests/e2e/api`. The
  two pytest commands are separate so an empty suite fails independently. Define
  cleanup/isolation between tests. If only one suite is implemented initially,
  scope and name the activated job accordingly and document the deferred suite.
- Tests should start the actual API in a fixture or the test stack and validate
  persistence, migrations, and HTTP behavior. Add any extra service variables to
  both the workflow and local development instructions.
- Failure logs and unconditional teardown are included. The job-specific Compose
  project name limits teardown to that job's disposable containers and volumes.

## Container builds

The matrix lists proposed Dockerfile paths for API, procurement agent, RAG
assistant, dashboard, and MLflow. At first activation, **remove rows for components
not implemented in that PR**. Add each row later with its real Dockerfile. Do not
silently skip missing Dockerfiles.

Use repository-root build context for workspace dependencies, a reviewed
`.dockerignore`, pinned base images, and locked dependency installation. Builds
must succeed from a clean checkout without local `.env` files, virtual environments,
`node_modules`, or secrets. The template builds locally on the CI runner and does
not publish images. Runtime health and behavior need integration tests; a successful
image build alone does not establish them.

## Browser tests

Add a pinned `@playwright/test` development dependency and regenerate `pnpm-lock.yaml`.
Implement root `playwright.config.ts` with `testDir: tests/e2e/ui`, a `chromium`
project, and `forbidOnly` enabled in CI. Use its `webServer` configuration to start
and stop the built dashboard and wait for the local URL; disable server reuse in CI.
The template builds first and runs one Chromium worker.

Add at least one real user journey with assertions. Choose either a reproducible
local backend or explicit API fixtures; document which behavior is covered. If a
backend is required, add its startup, readiness, and cleanup in the same PR.
Include browser tests/config in lint/type checking and ignore generated test reports.
See [Playwright CI](https://playwright.dev/docs/ci) and
[web server configuration](https://playwright.dev/docs/test-webserver).

## Abuse-case tests

Add tests under `tests/security` that exercise the controls actually implemented:
prompt-injection resistance, approval-bypass prevention, and/or redaction. Cover
allowed and denied behavior, including a regression case for each relevant control.
Use synthetic fixtures and local provider fakes where external services would make
the test nondeterministic. Document which controls remain unimplemented. Add service
setup and cleanup if tests require a real database or API.

Activate as `abuse-case-tests.yml`. Do **not** replace the existing
`security-tests.yml`: that active file owns the `Secret scan` baseline check.

## AI quality gate

Implement all of the following together:

- `scripts/run_quality_gate.sh`, with strict error propagation and an actual
  evaluator invocation in the locked Python environment.
- `config/quality-gate.yml`, defining metrics, directions, thresholds, minimum
  case count, and the selected dataset/version.
- `tests/fixtures/evaluation/cases.jsonl`, containing reviewed synthetic or
  redistributable cases, stable IDs, and expected outcomes. This proposed fixture
  location is tracked; generated/local dataset directories are ignored.
- `artifacts/ai-quality/report.json`, generated by each run with dataset/model or
  fixture version, per-metric scores, case counts, thresholds, and pass/fail result.

The script must fail for missing/invalid configuration or data, zero cases,
evaluator/provider errors, non-finite scores, and any breached threshold. It must
produce a fresh report rather than accept a cached successful result. The workflow
also requires that report to be nonempty; report existence does not replace metric
enforcement in the script. Include behavior tests for threshold and error handling.

The initial PR gate uses `TRUSTOPS_EVAL_MODE=offline` and must explicitly enforce
local fixtures/deterministic evaluation without production keys or paid calls.
This validates the reproducible evaluation scope documented in the implementation;
it does not establish live-provider/model quality. Live evaluations need separately
reviewed credentials, costs, repeatability criteria, and a suitable trusted trigger.

## Coverage

Coverage is a separate activation for each language, not a percentage over empty
package shells. Replace `MIN_COVERAGE` with an agreed integer from 1 through 100
based on real source and tests. The template deliberately fails for its placeholder
or a zero threshold. Explain the chosen threshold and scope in the PR.

- **Python:** add a pinned `coverage` dev dependency and regenerate `uv.lock`.
  Implement `config/coverage.ini` with branch measurement and source selection
  covering all implemented modules, including those not imported by tests. Keep
  source errors visible. Include paths for installed wheels if needed; the
  workspace is installed non-editably. Run real unit/contract behavior tests.
- **Frontend:** pin `@vitest/coverage-v8` to the same version as `vitest` and
  regenerate `pnpm-lock.yaml`. Set `coverage.include` in `vitest.config.mts` to
  include the implemented dashboard source, including unimported files. Review
  exclusions and add real component behavior tests. The template enforces the
  agreed target for lines, branches, functions, and statements.

Generated coverage outputs stay ignored. Add thresholds for new components as
they become executable; do not exclude difficult code just to achieve the target.

## MLOps CLI smoke test

Declare and implement the actual console entry point in the MLOps package and
replace `MLOPS_CLI` with that command name. `--help` must exit zero, print useful
usage, and require no credentials, running services, or writes to production data.
The template installs wheels and invokes the command outside the checkout to catch
packaging/import errors. Add CLI behavior tests separately as commands are built.

## Keeping the templates current

Templates intentionally have no active CI jobs or fake passing checks. Syntax can
be checked with a YAML parser and actionlint, but end-to-end execution is deferred
until the prerequisites exist. Review action pins and tool versions when moving
a template; do not assume Dependabot updates inactive files.

Keep each activation in one focused implementation PR. If a workflow needs a new
dependency group, script interface, fixture format, or service, include that change
and its documentation in the same PR. Successful CI plus Code Owner review is the
evidence for adding the new check to branch protection afterward.
