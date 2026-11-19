# Architecture

The planned `packages/contracts` layer will define canonical cross-module data. The instrumentation SDK and reference applications will emit traces. `platform-core` will store traces and synchronously invoke reliability evaluation and governance decisions. `mlops` will own datasets, experiments, and the release quality gate. `apps/api` will wire the FastAPI HTTP boundary, while `apps/dashboard` will present results.

Packages must never import from apps. Reliability and governance will depend on contracts, and governance must not import reliability implementation classes. The Week 2 application scaffolds use mock Procurement tools and an offline RAG index. SQLite FTS5 retrieval lives in the RAG application. The [pgvector probe](tools/rag_vector_probe/) tests the proposed integration backend in isolation. Access under the shared application role still requires verification.

## Week 1 reference application contracts

Revision 0.5 of the [Week 1 reference application contracts](docs/architecture/reference-applications/README.md)
documents the proposed Procurement state machine, tool and RAG contracts, trace evidence and scenario plans.

## Dashboard UX architecture

See the [dashboard UX architecture](docs/architecture/dashboard/README.md) for the
reviewer task flows, the seven-screen information architecture, the status vocabulary and
the field and data-owner matrix. It is a revision 0.1 draft awaiting backend-owner review;
it adds no routes, components or code.
