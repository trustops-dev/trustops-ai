# Verify pgvector for the RAG integration environment

**Decision as of 19 November 2026.** Keep pgvector as the preferred integration backend. Its exact cosine search passed a local capability test. Availability under the shared application role is pending Mohab’s observation. FAISS remains a proposed fallback requiring explicit team selection. The Week 2 SQLite FTS5 proof remains reproducible independently.

## What was verified

Application base: PR #29 at `40327ab91a94413af77313f9fa7d0e0de9f2e1df`. Contract: [PR #27 at cc99324](https://github.com/trustops-dev/trustops-ai/blob/cc9932440853fe418f588209649f7ff9c0667880/docs/architecture/reference-applications/rag-contract.md).

An isolated PostgreSQL 17.11 installation with pgvector 0.8.0 (extension schema `public`) executed the generated query in a read-only transaction on 19 November. The local run used PostgreSQL's standalone backend with `SET ROLE` to a test role without superuser or BYPASSRLS privileges. This tests SQL execution and ranking. Network connectivity, application authentication, persistent vector tables and grants in the shared deployment still require integration evidence.

The script loads seven eligible chunks using the existing pinned corpus loader. The fixture represents query and document tokens with deterministic normalized 768-dimensional vectors. PostgreSQL ranks them by exact cosine distance, with a bytewise chunk-ID tie break. Python verifies all seven distances and resolves the returned IDs to the original source bytes. The existing application pipeline selects, answers and binds the citation using an extractive test double.

The emergency-leave query ranked `doc-003@review-r1:0:332` first. Citation `[src-003:review-r1]` matched the selected source at Unicode offsets [0, 331). The verifier also rejects changes to the document, source, revision, chunk, digest, start offset and quote. A database without the extension returned an explicit missing-extension error. The result covers vector transport and structural evidence binding. Live Gemini embeddings, semantic quality, authorization of stored rows and deployment performance remain open.

## Reproduce or run in the shared target

From the application checkout with Python 3.12 and uv 0.13.0:

```sh
uv run --locked --all-packages python tools/rag_vector_probe/probe.py verify tools/rag_vector_probe/isolated-pg17-result.json
uv run --locked --all-packages python tools/rag_vector_probe/probe.py prepare rag-pgvector-probe.sql
```

Mohab can run the generated SQL directly from the handoff ZIP. Select the intended integration database using the application's ordinary PostgreSQL role and the operator's existing connection method. With libpq configured for that target, run this one command from the directory containing the SQL:

```sh
psql -X -qAt -w -v ON_ERROR_STOP=1 -f rag-pgvector-probe.sql -o rag-pgvector-result.json
```

On exit 0, return the resulting JSON and a non-sensitive environment label to Nour. On failure, return the observation time and error category (connection/authentication, missing extension, schema/operator permission, or query failure). Keep credentials and connection strings private. The SQL uses catalog reads and inline fixture vectors. It creates no tables or extensions and finishes with ROLLBACK.

Nour verifies the returned JSON from the application checkout:

```sh
uv run --locked --all-packages python tools/rag_vector_probe/probe.py verify rag-pgvector-result.json
```

Record the target label, UTC time, PostgreSQL/extension version, schema, role flags, fixture identity and result with the application commit. A passing run under the intended role establishes exact vector search for that environment. Treat a run under an administrative role as diagnostic only. If the extension is missing, agree with Mohab on enabling it or reviewing FAISS. Connectivity or permission errors leave availability unconfirmed.
