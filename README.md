# TrustOps AI

TrustOps AI contains two offline reference applications. The [Procurement Agent](apps/procurement-agent/) runs the approval workflow with mock tools. The [RAG Assistant](apps/rag-assistant/) retrieves passages from a pinned synthetic corpus using SQLite FTS5 and binds citations to the selected text. The [application tests](tests/unit/reference_applications/) exercise both paths.

The [Week 2 proof traces](tests/fixtures/traces/week2-v1/) are manually authored fixtures with a reproducible schema check. Runtime trace emission, shared pgvector access and live provider compatibility remain open. See [ARCHITECTURE.md](ARCHITECTURE.md) for the integration boundaries.

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

Revision 0.5 of the [Week 1 reference application contracts](docs/architecture/reference-applications/README.md)
documents the proposed Procurement state machine, tool and RAG contracts, trace evidence and scenario plans.
