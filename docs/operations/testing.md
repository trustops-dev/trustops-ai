# Python checks

Run from the repository root after installing the workspace:

```sh
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages lint-imports --no-cache
uv run --locked --all-packages pytest tests/unit tests/contract
```

The Python CI workflow runs these checks on PRs and pushes to `main` and `dev`. It installs all workspace members as wheels rather than editable packages and fails if the lockfile is missing or stale. No prerequisite-detection step skips validation.

## What is validated now

- Python linting, formatting, and strict type checking.
- Packages cannot import applications; contracts cannot import higher layers; reliability and governance cannot import each other or orchestration; instrumentation cannot import backend implementations.
- Nine packaging smoke cases verify distribution metadata and imports outside the repository working directory. These protect the initial workspace installation; they are not application behavior tests.

Import-linter analyzes static imports. Reviewers still need to check dependency declarations, dynamic imports, business-logic placement, and any architectural constraints not covered by the configured contracts.

## Add with implementation

Put actual behavior tests under the corresponding `tests/unit` directory and shared-schema tests under `tests/contract`. pytest will discover them automatically. Tests that need PostgreSQL, MLflow, a browser, or an external provider belong in their designated suites and will get separate workflows.

Coverage reporting and a meaningful coverage target will be added with the first executable domain behavior. The package shells currently contain docstrings only, so a coverage percentage would not measure application quality. The MLOps CLI smoke test will be added with the CLI implementation.

After this workflow has passed and the PR has merged, a repository owner can make `Python checks` a required status check. Enable it on `dev` only after the workflow is also merged there.
