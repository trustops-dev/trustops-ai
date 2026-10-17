# Architecture

The planned `packages/contracts` layer will define canonical cross-module data. The instrumentation SDK and reference applications will emit traces. `platform-core` will store traces and synchronously invoke reliability evaluation and governance decisions. `mlops` will own datasets, experiments, and the release quality gate. `apps/api` will wire the FastAPI HTTP boundary, while `apps/dashboard` will present results.

Packages must never import from apps. Reliability and governance will depend on contracts, and governance must not import reliability implementation classes. The directories are reserved; implementation files will be added as the project progresses.

## Week 1 reference application contracts

See the [S1-01 reference application contracts](docs/architecture/reference-applications/README.md)
for the procurement state machine, tool and RAG contracts, trace evidence, scenario
plans and proposed orchestration ADR. These are revision 0.5 drafts awaiting
canonical-schema alignment and named team sign-offs; they do not represent
implemented or runtime-validated application behavior.

## Dashboard UX architecture

See the [dashboard UX architecture](docs/architecture/dashboard/README.md) for the
reviewer task flows, the seven-screen information architecture, the status vocabulary and
the field and data-owner matrix. It is a revision 0.1 draft awaiting backend-owner review;
it adds no routes, components or code.
