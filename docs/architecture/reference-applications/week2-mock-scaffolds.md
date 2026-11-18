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
same-key repeated calls in one local process only. A configured non-timeout
`UNKNOWN_OUTCOME` is retained under that key; a subsequent run uses a separate
read-only recovery lookup before any new gate check or create call. `STILL_UNRESOLVED`
stays `PO_CREATION` / `RECOVERY_PENDING`; an explicit mock committed result may
complete and an explicit abort tombstone may report definitive no effect. A mere
`ERROR` or raised exception after dispatch remains `UNKNOWN`. No automatic write
replay, durable terminal-approval enforcement, cross-process deduplication, atomic
consumption or restart recovery is implemented. A small in-memory terminal-status
fixture blocks a denial/cancellation reversal while that mock object lives. The
calculation is a supplied fixture, not an app-owned
threshold rule. Workflow budgets and continuation are future integration points.

Mohamed's 18 November [review of the corrections](reviews/mohamed-pr29-corrections-followup-2026-11-18.md)
is scoped to this mock. A confirmed created effect emits `COMMITTED`; a confirmed
replay with a fixture original-result reference emits `ALREADY_EXISTING`. A replay
without a reference remains `UNKNOWN`. Read-only committed recovery requires
`COMMITTED_RECORD_FOUND` plus a matching echoed key and mock request identity;
missing proof stays pending. These comparisons do not establish an authoritative
purchase-order record or a durable claim.

## RAG

`Pipeline.answer()` performs one retrieval, explicit curated selection, mock candidate
generation and structural citation binding. A valid quote must match exact offsets in
the selected chunk, with matching document/source/chunk IDs, source version and SHA-256
content hash. The visible marker must use the selected source ID/version. Missing or
contradictory evidence and invalid citation bindings abstain. A typed local
`RetrievalError` (`TIMEOUT` or `PROVIDER_OR_SDK_ERROR`) instead returns `ERROR` /
`RETRIEVAL_ERROR`, emits only an allowlisted category, and skips selection and
generation. This is an application-local seam, not acceptance or implementation
of the proposed canonical retrieval-fault amendment. Unexpected programming
exceptions propagate; real authorization and provider adapters are not implemented. The fixture author supplies
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
uv run --locked --all-packages pytest -q tests/unit/reference_applications
uv run --locked ruff check apps/procurement-agent apps/rag-assistant tests/unit/reference_applications
uv run --locked mypy apps/procurement-agent/src apps/rag-assistant/src tests/unit/reference_applications
```

The tests use synthetic fixtures and require no API key. The current validation
record for this isolated patch is in the delivery note; it does not imply a
provider or platform integration test.

## Boundary coverage added 2026-11-15

- Procurement: happy path; missing approval record and submission ID; pending,
  denied and cancelled approval; revised request/supplier/amount/currency;
  changed supplier/approval versions and explicit policy block; non-timeout UNKNOWN
  retained on same-key repeat with one dispatch and no false completion; same-key
  payload conflict rejected. DENIED/CANCELLED tests cover stopping the current
  execution, not a durable state-transition store across separate executions.
- RAG: grounded answer; document/source/version/chunk/hash mismatch; bad offsets,
  quote and tampered chunk text; retrieved-but-excluded support; exact selected
  context passed to the generator; separate authored insufficient/conflicting
  abstention and zero-hit abstention; timeout/provider errors skip generation and
  remain errors rather than evidence insufficiency.
- Context currently consists of whole selected chunks. Span checks use Unicode
  code-point offsets in those exact chunks; sliced/truncated prompts will require
  explicit slice mapping and new tests before implementation. Structural checks
  do not establish semantic entailment. Sufficiency/conflict decisions are authored
  fixtures, not automatic contradiction detection or retrieval-quality evaluation.

Run the additional formatting check with:

```bash
uv run --locked ruff format --check apps/procurement-agent apps/rag-assistant tests/unit/reference_applications
```

See [boundary validation](week2-boundary-validation-2026-11-15.json) for actual
Linux preparation evidence and fresh Windows integration results. Live providers, canonical trace validation,
pgvector/index ingestion, governance runtime and platform integration remain
unverified. This is progress toward Week 2, not Week 2 closeout.

## Mohamed's scoped Procurement review and local follow-up

His review of PR #29 `ebdefc1` accepts the current-execution approval stops and
changed-request checks, and amends post-dispatch uncertainty and same-key rerun
behavior. The local follow-up above adds the read-only recovery seam, typed
`UNKNOWN_OUTCOME`/`RECOVERY_PENDING` for `ERROR` and caught post-dispatch
ordinary dispatch exceptions (including decoding and I/O faults), and tests with one policy check and one create call. It separately
checks the selected policy-KB release against the versioned executable bundle
pair, without requiring their IDs to be equal. Empty supplier record versions,
approval `calculation_ref` mismatch, request revision, decision sequence,
supplier/approval versions, approval status and bundle changes stop before
dispatch with distinct reasons. The local check emits `STUB_CONTRACT_TEST`;
it only simulates approval and an allow flag, not the three actual policy rules.

The mock ledger compares complete request objects rather than a canonical
business-payload digest; its root-to-key check also lives only in memory. Its terminal status memory is not durable or tied
to a versioned supersession history. The read tools still lack the full online
gate, and runtime-owned atomic claim/consumption, recovery after restart,
budget accounting and canonical side-effect/trace validation remain open with
Mohab and Mohamed. These tests are evidence for a corrected application seam,
not OD-12 runtime acceptance or policy enforcement acceptance.

## Ahmed's scoped PR #29 review and local follow-up

[The reviewer disposition and local rerun](reviews/ahmed-pr29-rag-scaffold-2026-11-16.md)
record structural acceptance and targeted test amendments. Selected context and valid
citation events now carry matching document/source/version/chunk/hash and retrieval
snapshot identity under the same query ID. Two fixture-selected contradictory passages
abstain without generation; consistent selected passages reach the generator with one
verified citation. A test adapter wraps a raw provider exception and emits only an
allowlisted retrieval error category. These cases do not establish semantic conflict
detection, full multi-source citation support or canonical event compatibility.
