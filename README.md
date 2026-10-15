# TrustOps AI

This repository contains the **repository base** for the TrustOps AI project, including the planned directories, contribution guidance, Python and frontend workspaces, and secret scanning. The approved repository architecture document defines the planned files, ownership, and dependency rules. `.gitkeep` files allow Git to retain empty directories.

Python packages currently provide installable shells with packaging smoke tests. The dashboard has a minimal Next.js entry page and a rendering smoke test. Domain behavior, API integration, infrastructure configuration, datasets, and scenarios have not been implemented yet. Add each file together with its feature. See [ARCHITECTURE.md](ARCHITECTURE.md) for the planned module boundaries.

The Security workflow scans Git history for secrets on pull requests and pushes to `main` and `dev`. Python CI checks linting, formatting, types, import boundaries, and package installation. Frontend CI checks linting, types, rendering tests, and a production build. Dependabot proposes weekly GitHub Actions, Python, and frontend dependency updates to `main`. See [SECURITY.md](SECURITY.md) for scanner maintenance.

Dependency review checks new high/critical vulnerabilities on PRs. Separate frontend and Python audits scan the frontend lockfile and external dependencies exported from `uv.lock`. Start with the [local development guide](docs/operations/local-development.md) and [repository checks](docs/operations/testing.md). Other CI workflows will be added with the code they validate.

Team work follows **task branch → PR → `dev` → PR → `main`**. Clone the repository,
create each task branch from the latest `dev`, and open its PR against `dev`.
See [CONTRIBUTING.md](CONTRIBUTING.md) for teammate commands, review, promotion,
and synchronization instructions. Dependabot updates to `main` are synced back to `dev`.

Future checks are prepared as inactive [workflow templates](.github/workflow-templates/README.md).
Use the [activation guide](docs/operations/workflow-activation.md) to enable each
with its implementation and tests; adding these templates does not enable new checks.

## Week 1 reference application contracts

See the [S1-01 reference application contracts](docs/architecture/reference-applications/README.md)
for the procurement state machine, tool and RAG contracts, trace evidence, scenario
plans and proposed orchestration ADR. These are revision 0.5 drafts awaiting
canonical-schema alignment and named team sign-offs; they do not represent
implemented or runtime-validated application behavior.
