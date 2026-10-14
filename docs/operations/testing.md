# Repository checks

## Python checks

Run from the repository root after installing the workspace:

```sh
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages lint-imports --no-cache
uv run --locked --all-packages pytest tests/unit tests/contract
```

The Python CI workflow runs these checks on PRs and pushes to `main` and `dev`. It installs all workspace members as wheels rather than editable packages and fails if the lockfile is missing or stale. No prerequisite-detection step skips validation.

### What is validated now

- Python linting, formatting, and strict type checking.
- Packages cannot import applications; contracts cannot import higher layers; reliability and governance cannot import each other or orchestration; instrumentation cannot import backend implementations.
- Nine packaging smoke cases verify distribution metadata and imports outside the repository working directory. These protect the initial workspace installation; they are not application behavior tests.

Import-linter analyzes static imports. Reviewers still need to check dependency declarations, dynamic imports, business-logic placement, and any architectural constraints not covered by the configured contracts.

### Add with implementation

Put actual behavior tests under the corresponding `tests/unit` directory and shared-schema tests under `tests/contract`. pytest will discover them automatically. Tests that need PostgreSQL, MLflow, a browser, or an external provider belong in their designated suites and will get separate workflows.

Coverage reporting and a meaningful coverage target will be added with the first executable domain behavior. The package shells currently contain docstrings only, so a coverage percentage would not measure application quality. The MLOps CLI smoke test will be added with the CLI implementation.

After this workflow has passed and the PR has merged, a repository owner can make `Python checks` a required status check. Enable it on `dev` only after the workflow is also merged there.

## Frontend checks

After installing the frontend workspace, run from the repository root:

```sh
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

`Frontend checks` runs these commands on every PR and push targeting `main` or `dev`, with a frozen lockfile. ESLint checks the dashboard and TypeScript test/config files; Next.js generates route types and TypeScript checks both the application and the central test suite. Vitest and React Testing Library run tests under `tests/unit/dashboard`. The build compiles and prerenders the minimal dashboard for production.

The initial rendering smoke test verifies that the entry page mounts with an accessible heading and an empty application state. It validates the frontend harness, not application behavior, API integration, or browser flows. There is no coverage threshold until meaningful dashboard features exist. Add unit tests here as components are implemented; browser flows belong under `tests/e2e/ui` and will need a separate runner. Async Server Components should be tested through integration or browser tests rather than this synchronous rendering harness.

After a successful CI run and merge, the repository owner can add `Frontend checks` alongside `Python checks` and `Secret scan` in branch protection. First sync the workflow to `dev` before requiring it there. Keep the permanent `main` and `dev` branches.

## Remaining stages

- Database, migrations, API integration, and end-to-end tests: add with the first working API and database setup.
- Container builds and Compose validation: add with real Dockerfiles and Compose services.
- Prompt-injection, approval-bypass, and redaction tests: add with the features they exercise.
- AI quality gate: add with an executable evaluation script, versioned evaluation data, and agreed thresholds.

Do not add successful placeholder jobs for these stages. Each required check must execute real validation and fail when that validation fails.

## Dependency security

`Dependency review` checks PR dependency changes recognized by GitHub's dependency graph and fails on newly introduced high or critical vulnerabilities, including development dependencies. It is a PR-only comparison; it does not run after a push or on a schedule. The repository owner must enable Dependency graph in GitHub security settings before this check can run. The frontend uses a single-document pnpm lockfile so GitHub can read its project dependency graph. GitHub also recognized changed `uv.lock` dependencies in our verification, although its ecosystem support table does not currently list uv; the independent audits below scan the full pinned dependency inventories rather than relying only on the PR diff.

`Frontend dependency audit` independently audits the entire frontend lockfile with `pnpm audit --audit-level high`, including development dependencies. It runs on PRs, pushes, weekly on the default branch, and manual dispatch. It fails for high or critical known vulnerabilities and registry errors. Run the same command locally to reproduce it. This also detects newly disclosed vulnerabilities in existing dependencies that a PR-only comparison may not report.

`Python dependency audit` exports locked external dependencies from all Python workspace members, extras, and dependency groups, then checks them with the pinned `pip-audit` tool. Workspace packages are excluded because they are our own unpublished code. Hashes and exact versions are retained; auditing does not install application dependencies. The audit runs on PRs, pushes to `main` and `dev`, a weekly schedule on the default branch, and manual runs. It fails for any known vulnerability reported by the advisory service (including severities below high) and for collection failures. Environment markers are evaluated for the Linux/Python 3.12 CI environment.

To reproduce the Python audit after the normal workspace setup, run:

```sh
uv export --locked --all-packages --all-groups --all-extras --no-emit-workspace --format requirements-txt --output-file artifacts/python-audit-requirements.txt --quiet
uv run --locked --group audit pip-audit --requirement artifacts/python-audit-requirements.txt --require-hashes --disable-pip --strict --progress-spinner off
```

The generated export is ignored and must not be edited or committed. Dependency security checks require network access to advisory services. They detect known vulnerabilities; they do not establish that packages are trustworthy or free of unknown flaws. After the workflows pass and are merged into each protected branch, the owner can require `Dependency review`, `Frontend dependency audit`, and `Python dependency audit` alongside the other checks.
