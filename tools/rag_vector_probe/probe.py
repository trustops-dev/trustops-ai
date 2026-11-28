"""Prepare a read-only pgvector query and verify its result through the RAG pipeline."""

import argparse
import json
import math
import re
from collections import Counter
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from sqlite3 import Row, connect
from tempfile import TemporaryDirectory

from trustops_rag_assistant.offline_index import DEFAULT_CORPUS, SNAPSHOT, build_index
from trustops_rag_assistant.pipeline import (
    Candidate,
    EvidenceRef,
    Pipeline,
    RetrievedEvidence,
    Selection,
    valid_support,
)
from trustops_rag_assistant.trace import RecordingSink

QUESTION = (
    "Does emergency leave require five working days of notice, and is it automatically approved?"
)
INDEX_VERSION = f"{SNAPSHOT}-pgvector-fixture-termhash768-v1"
EXPECTED_HASH = "a0ddf7a477906b28bd28172850effc10d9f4eb49d04f5767d2cdb8374bcd6139"


def vector(text: str) -> list[float]:
    """Normalized deterministic token counts for the transport proof only."""
    counts = Counter(
        int.from_bytes(sha256(token.encode()).digest()[:4], "big") % 768
        for token in re.findall(r"[^\W_]+", text.casefold())
    )
    norm = math.sqrt(sum(count * count for count in counts.values()))
    return [counts[i] / norm for i in range(768)]


def members() -> dict[str, dict[str, str]]:
    # Reuse the hash-checked corpus loader. SQLite supplies source rows only.
    with TemporaryDirectory() as temp:
        index = build_index(DEFAULT_CORPUS, Path(temp))
        with closing(connect(index)) as db:
            db.row_factory = Row
            return {row["chunk_id"]: dict(row) for row in db.execute("SELECT * FROM chunks")}


def write_query(output: Path) -> None:
    docs = members()
    inputs = [
        {"id": key, "embedding": vector(row["title"] + " " + row["chunk_text"])}
        for key, row in docs.items()
    ]
    # Hex keeps arbitrary fixture bytes out of SQL syntax. The query has no table writes.
    payload = json.dumps(inputs).encode().hex()
    query = json.dumps(vector(QUESTION))
    output.write_text(
        f"""BEGIN READ ONLY;

SET LOCAL statement_timeout = '5s';

SET LOCAL search_path = pg_catalog;

DO $probe$
DECLARE ns name;
BEGIN
  SELECT n.nspname INTO ns FROM pg_catalog.pg_extension e
    JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace WHERE e.extname = 'vector';
  IF ns IS NULL THEN
    RAISE EXCEPTION 'Extension vector is not installed in this database';
  END IF;
  IF NOT has_schema_privilege(ns, 'USAGE') THEN
    RAISE EXCEPTION 'Role lacks USAGE on the vector extension schema';
  END IF;
  PERFORM pg_catalog.set_config('search_path', 'pg_catalog,' || quote_ident(ns), true);
END
$probe$;

WITH ranked AS (
  SELECT id, (embedding::text::vector(768) <=> '{query}'::vector(768)) AS distance
  FROM jsonb_to_recordset(convert_from(decode('{payload}', 'hex'), 'UTF8')::jsonb)
    AS eligible(id text, embedding jsonb)
)
SELECT json_build_object(
  'observed_utc', transaction_timestamp() AT TIME ZONE 'UTC',
  'server', current_setting('server_version'), 'extension', e.extversion, 'schema', n.nspname,
  'schema_usage', has_schema_privilege(n.oid, 'USAGE'), 'read_only', current_setting('transaction_read_only'),
  'superuser', r.rolsuper, 'bypass_rls', r.rolbypassrls,
  'index_version', '{INDEX_VERSION}', 'snapshot', '{SNAPSHOT}',
  'hits', (SELECT json_agg(json_build_array(id, distance) ORDER BY distance, id COLLATE "C") FROM ranked)
) AS proof FROM pg_extension e JOIN pg_namespace n ON n.oid = e.extnamespace
JOIN pg_roles r ON r.rolname = current_user WHERE e.extname = 'vector';

ROLLBACK;
""",
        encoding="utf-8",
    )


class RankedReceipt:
    def __init__(self, hits: tuple[RetrievedEvidence, ...]):
        self.hits = hits

    def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        if query != QUESTION:
            raise ValueError("This receipt is bound to the fixture question")
        return self.hits[:5]


class ExtractiveFixture:
    def select(self, query: str, hits: tuple[RetrievedEvidence, ...]) -> Selection:
        first = hits[0]
        quote = first.chunk_text.rstrip("\n")
        ref = EvidenceRef(
            first.document_id,
            first.source_id,
            first.source_version,
            first.chunk_id,
            first.content_hash,
            0,
            len(quote),
            quote,
        )
        return Selection((first.chunk_id,), ref, "SUFFICIENT_EVIDENCE")

    def generate(self, query: str, selected: tuple[RetrievedEvidence, ...]) -> Candidate:
        ref = self.select(query, selected).support
        if ref is None:
            raise ValueError("Missing fixture passage")
        return Candidate(ref.quote, f"[{ref.source_id}:{ref.source_version}]", ref)


def verify(path: Path) -> dict[str, object]:
    receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    docs = members()
    if (
        receipt["index_version"] != INDEX_VERSION
        or receipt["snapshot"] != SNAPSHOT
        or receipt["schema_usage"] is not True
        or receipt["read_only"] != "on"
    ):
        raise ValueError("Unexpected scope or database capability")
    pairs = receipt["hits"]
    if len(pairs) != len(docs) or {k for k, _ in pairs} != set(docs):
        raise ValueError("Returned chunk IDs differ from the pinned manifest")
    query = vector(QUESTION)
    for key, distance in pairs:
        row = docs[key]
        reference = 1 - sum(
            a * b
            for a, b in zip(query, vector(row["title"] + " " + row["chunk_text"]), strict=True)
        )
        if not math.isclose(distance, reference, abs_tol=1e-5):
            raise ValueError(f"Cosine distance differs for {key}")
    if pairs != sorted(pairs, key=lambda pair: (pair[1], pair[0])):
        raise ValueError("Rank ordering differs")
    hits = tuple(
        RetrievedEvidence(
            **docs[key],
            rank=i,
            score=distance,
            score_kind="cosine_distance",
            higher_is_better=False,
            snapshot_ref=SNAPSHOT,
            index_version=INDEX_VERSION,
        )
        for i, (key, distance) in enumerate(pairs, 1)
    )
    first = hits[0]
    if (
        first.document_id,
        first.source_id,
        first.source_version,
        first.chunk_id,
        first.content_hash,
    ) != ("doc-003", "src-003", "review-r1", "doc-003@review-r1:0:332", EXPECTED_HASH):
        raise ValueError("Unexpected provenance for the first passage")
    sink = RecordingSink()
    model = ExtractiveFixture()
    result = Pipeline(RankedReceipt(hits), model, model, sink).answer("q-002", QUESTION)
    if result.status != "ANSWER" or not result.text.endswith("[src-003:review-r1]"):
        raise ValueError("Grounded answer failed")
    (ref,) = result.citations
    context = next(e.details for e in sink.events if e.kind == "selected_context")
    binding = next(e.details for e in sink.events if e.kind == "citation_binding")
    if (
        binding["result"] != "VALID"
        or binding["snapshot_ref"] != SNAPSHOT
        or context["index_version"] != INDEX_VERSION
        or ref.quote != first.chunk_text[ref.start : ref.end]
        or not valid_support(ref, (first,))
    ):
        raise ValueError("Selected passage and citation differ")
    for changed in (
        replace(ref, document_id="other"),
        replace(ref, source_id="other"),
        replace(ref, source_version="stale"),
        replace(ref, chunk_id="other"),
        replace(ref, content_hash="0" * 64),
        replace(ref, start=ref.start + 1),
        replace(ref, quote="Different passage"),
    ):
        if valid_support(changed, (first,)):
            raise ValueError("Invalid citation accepted")
    observed = (
        "observed_utc",
        "server",
        "extension",
        "schema",
        "schema_usage",
        "read_only",
        "superuser",
        "bypass_rls",
        "index_version",
        "snapshot",
    )
    return {k: receipt[k] for k in observed} | {
        "result": "PASS",
        "verified_distances": len(pairs),
        "chunk": first.chunk_id,
        "content_hash": ref.content_hash,
        "quote_offsets": [ref.start, ref.end],
        "citation": "[src-003:review-r1]",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "verify"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.operation == "prepare":
        write_query(args.path)
    else:
        print(json.dumps(verify(args.path), indent=2))
