# Reliability contracts (Week 1)

This directory contains the candidate v1 reliability semantics and cross-package contracts. It is a Week 1 specification: it does **not** implement the evaluator runtime, classifiers, RCA ranker, security benchmark runner, trace SDK, application behavior, governance policy engine, or quality gate.

- [Failure taxonomy v1](failure-taxonomy.md) defines primary labels, secondary findings, evidence and ambiguity handling.
- [Annotation guide](annotation-guide.md) describes how to label observed traces and adjudicate disagreements.
- [Evaluator contracts v1](evaluator-contracts-v1.md) defines versioned request/result envelopes and evidence references.
- [Research protocol](research-protocol.md) defines the research metrics, reproducibility fields and leakage safeguards.

Canonical machine-readable assets:

- `packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml`
- `packages/contracts/schemas/failure-label-v1.schema.json`
- `packages/contracts/schemas/evaluator-input-v1.schema.json`
- `packages/contracts/schemas/evaluator-output-v1.schema.json`

**Status:** taxonomy version `1.0.0`, candidate pending cross-team sign-off. Canonical cross-module contracts are implemented as **Pydantic v2 models** under `packages/contracts/src/trustops_contracts/`; models use strict validation and reject unexpected fields. `packages/contracts/scripts/export_schemas.py` deterministically generates the three Draft 2020-12 JSON Schemas from those models and adds portable structural predicates. Pydantic validators supplement the schemas for rules that require cross-field comparison, recursive traversal, or finite-number checks. JSON Schema alone cannot resolve an evidence reference against events/documents stored in a trace.

The contracts package declares `pydantic==2.13.5`. The schema regression tests use `jsonschema==4.26.0` from the root development dependency group. The root `uv.lock` has **not** yet been regenerated with the repository-pinned uv 0.13.0, so a successful clean locked installation is still a merge prerequisite; do not treat the dependency declarations alone as proof of lockfile compatibility.

The canonical taxonomy file uses the JSON-compatible subset of YAML 1.2 and is parsed with Python's standard-library JSON parser to avoid a separate YAML runtime dependency. The evaluator request's `trace_payload` intentionally remains opaque until Mohab's canonical Trace Schema v1 model and evidence-reference mapping are approved and frozen. Taxonomy/trace integration remains a candidate pending cross-team sign-off; see [contract review findings](contract-review-findings.md).
