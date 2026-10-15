# Contributing to TrustOps AI

This repository contains the planned directories, Python and frontend workspace setup, and repository checks. Add application behavior, tests, and configuration with the work that needs them. Follow the [local development guide](docs/operations/local-development.md), and read [ARCHITECTURE.md](ARCHITECTURE.md) before changing module boundaries.

## Branches and pull requests

1. Start a short-lived branch from the latest `main` for one focused task. Use a descriptive name such as `feature/trace-contracts`, `fix/api-validation`, or `docs/setup-guide`. Branches belong to tasks, not to individual members.
2. Commit the files needed for that task. Remove a directory's `.gitkeep` when the directory contains another tracked file.
3. Push the task branch and open a pull request to `main`. Describe the change and list the checks you actually ran. Request review from Nour or Malak before merging.
4. Address review feedback, merge after review and relevant checks, then delete the task branch.

The repository also has a lowercase `dev` branch. Use it only when the team agrees on an integration or release check that needs a separate branch. In that case, open task pull requests to `dev` and promote reviewed, tested changes from `dev` to `main` with another pull request. Keep `dev` close to `main`.

## What to include in a change

- Keep shared contracts in `packages/contracts`. Packages must not import from apps, and FastAPI routers should only handle the HTTP boundary.
- Add or update relevant tests and tooling with the implementation they verify. Do not add empty source files or workflows that depend on commands that do not exist yet.
- Never commit credentials, real secrets, sensitive datasets, or generated artifacts. Use safe example values in `.env.example` when configuration is introduced.
- Report exact validation commands and results in the pull request. If a check does not yet exist or cannot run, say so.
- When implementing a feature covered by an inactive workflow template, follow the [activation guide](docs/operations/workflow-activation.md) and activate the relevant check in the same PR as its code and tests. Record successful execution and failure behavior before requesting a new required check.
