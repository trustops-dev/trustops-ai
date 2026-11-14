# Week 2 isolated application scaffolds

Status: executable local mocks; no Gemini call, database, production authorization or
canonical trace serialization. The code lives in `apps/procurement-agent` and
`apps/rag-assistant`; focused tests live in `tests/unit/reference_applications`.

## Procurement

`Workflow.run()` consumes a normalized one-item request and an injected `ProcurementTools`
boundary. The fixed `MockTools` supports policy lookup, exact supplier lookup,
fixture-supplied approval calculation, initial approval submission, read-only observation,
pre-dispatch check and a single mock PO effect. The happy path traverses
`REQUEST_CAPTURED → POLICY_CHECKED → SUPPLIER_CHECKED → APPROVAL_CALCULATED →
APPROVAL_PENDING → APPROVED → PO_CREATION → COMPLETION`. Pending/invalid approval,
ineligible supplier, missing ALLOW and changed evidence stop before dispatch.

The synthetic gate response and current-version check demonstrate the integration
points. They are **not** a substitute for Mohamed's governance evaluation or Mohab's
atomic, durable authorization and consumption record. The in-memory ledger protects
same-key repeated calls in one local process only. No write replay or restart
recovery is implemented. The calculation is a supplied fixture, not an app-owned
threshold rule. Workflow budgets and continuation are future integration points.

## RAG

`Pipeline.answer()` performs one retrieval, explicit curated selection, mock candidate
generation and structural citation binding. A valid quote must match exact offsets in
the selected chunk, with matching document/source/chunk IDs, source version and SHA-256
content hash. The visible marker must use the selected source ID/version. Missing or
contradictory evidence and invalid citation bindings abstain; technical adapter
failures and real authorization are not implemented here. The fixture author supplies
the qualitative sufficiency decision; this is not an automatic semantic entailment
checker, a vector store, an embedding call or a general retrieval-quality result.

## Trace integration seam

Each app accepts an `EventSink` and emits local `AppEvent` objects. `RecordingSink`
supports test inspection; `NullSink` is the default. When Mohab's agreed schema and
transport are ready, implement an `EventSink` adapter that maps these events to
canonical records and add contract tests against the accepted schema. Local events
are diagnostic scaffolding, not schema-valid traces; they do not declare failure
classification, RCA or PASS/REVIEW/BLOCK decisions. Access-controlled content and
retention rules must be applied in that adapter before using real documents.

## Reproduction

With the repository's pinned toolchain and development environment:

```bash
uv run pytest -q tests/unit/reference_applications
uv run ruff check apps/procurement-agent apps/rag-assistant tests/unit/reference_applications
uv run mypy apps/procurement-agent/src apps/rag-assistant/src
```

The tests use synthetic fixtures and require no API key. The current validation
record for this isolated patch is in the delivery note; it does not imply a
provider or platform integration test.
