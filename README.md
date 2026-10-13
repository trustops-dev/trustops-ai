# TrustOps AI

This repository contains the **repository base** for the TrustOps AI project, including the planned directories, contribution guidance, a Python workspace, and secret scanning. The approved repository architecture document defines the planned files, ownership, and dependency rules. `.gitkeep` files allow Git to retain empty directories.

Python packages currently provide installable shells with packaging smoke tests. Application behavior, infrastructure configuration, datasets, and scenarios have not been implemented yet. Add each file together with its feature. See [ARCHITECTURE.md](ARCHITECTURE.md) for the planned module boundaries.

The Security workflow scans Git history for secrets on pull requests and pushes to `main` and `dev`. Python CI checks linting, formatting, types, import boundaries, and package installation. Dependabot proposes weekly GitHub Actions and Python dependency updates to `main`. See [SECURITY.md](SECURITY.md) for scanner maintenance.

Start with the [local development guide](docs/operations/local-development.md) and [Python checks](docs/operations/testing.md). Other CI workflows will be added with the code they validate.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the task-branch and pull-request workflow.
