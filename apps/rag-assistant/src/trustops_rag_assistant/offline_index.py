"""Build and search the pinned synthetic s01 snapshot using SQLite FTS5."""

import argparse
import json
import re
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from .pipeline import RetrievalError, RetrievedEvidence

SNAPSHOT = "corpus-review-s01"
MANIFEST_HASH = "c83a2cae8315806e9b81ae561c478b3b08329632fdee64fe89cfde924004a7c2"
INDEX_VERSION = f"{SNAPSHOT}-fts5-bm25-v1-sqlite-{sqlite3.sqlite_version}"
DEFAULT_CORPUS = Path("docs/architecture/reference-applications/corpus-review")


def build_index(corpus: Path, output_dir: Path) -> Path:
    """Verify the pinned bytes and atomically publish a snapshot-specific database."""
    raw = (corpus / "source-manifest.json").read_bytes()
    if sha256(raw).hexdigest() != MANIFEST_HASH:
        raise ValueError("Source manifest differs from the pinned revision")
    manifest = json.loads(raw)
    snapshot = next(item for item in manifest["snapshots"] if item["snapshot_id"] == SNAPSHOT)
    records = {(r["document_id"], r["source_version"]): r for r in manifest["documents"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{INDEX_VERSION}.sqlite3"
    with TemporaryDirectory(dir=output_dir) as temporary:
        staged = Path(temporary) / "index.sqlite3"
        with closing(sqlite3.connect(staged)) as db, db:
            db.execute("CREATE TABLE metadata (snapshot_id TEXT, index_version TEXT)")
            db.execute("INSERT INTO metadata VALUES (?, ?)", (SNAPSHOT, INDEX_VERSION))
            db.execute(
                "CREATE VIRTUAL TABLE chunks USING fts5("
                "title, chunk_text, document_id UNINDEXED, source_id UNINDEXED, "
                "source_version UNINDEXED, chunk_id UNINDEXED, content_hash UNINDEXED, "
                "domain UNINDEXED, locator UNINDEXED, tokenize='unicode61')"
            )
            for member in snapshot["source_versions"]:
                doc_id, version = member["document_id"], member["source_version"]
                record = records[doc_id, version]
                source = (corpus / record["canonical_text_path"]).read_bytes()
                digest = sha256(source).hexdigest()
                if digest != record["content_hash"]:
                    raise ValueError(f"Source hash mismatch for {doc_id}")
                content = source.decode("utf-8")
                span = {"start": 0, "end": len(content)}
                if (
                    record["protected_units"] != [span]
                    or record["locator"]["document_char_span"] != span
                ):
                    raise ValueError(f"Expected one complete protected passage for {doc_id}")
                db.execute(
                    "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        record["title"],
                        content,
                        doc_id,
                        record["source_id"],
                        version,
                        f"{doc_id}@{version}:0:{len(content)}",
                        digest,
                        record["domain"],
                        record["locator"]["section"],
                    ),
                )
        staged.replace(target)
    return target


class OfflineRetriever:
    def __init__(self, index: Path, limit: int = 5):
        if limit < 1:
            raise ValueError("limit must be positive")
        self.index = index
        self.limit = limit

    def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        # Quote each literal token so punctuation and FTS operators stay user input.
        tokens = dict.fromkeys(re.findall(r"[^\W_]+", query.casefold()))
        match = " OR ".join(f'"{token}"' for token in tokens)
        try:
            uri = self.index.resolve().as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as db:
                db.row_factory = sqlite3.Row
                meta = db.execute("SELECT snapshot_id, index_version FROM metadata").fetchone()
                if meta is None or tuple(meta) != (SNAPSHOT, INDEX_VERSION):
                    raise RetrievalError("PROVIDER_OR_SDK_ERROR")
                if not match:
                    return ()
                rows = db.execute(
                    "SELECT *, bm25(chunks) AS score FROM chunks WHERE chunks MATCH ? "
                    "ORDER BY score, chunk_id COLLATE BINARY LIMIT ?",
                    (match, self.limit),
                )
                return tuple(
                    RetrievedEvidence(
                        **dict(row),
                        rank=rank,
                        score_kind="sqlite_fts5_bm25",
                        higher_is_better=False,
                        snapshot_ref=SNAPSHOT,
                        index_version=INDEX_VERSION,
                    )
                    for rank, row in enumerate(rows, start=1)
                )
        except sqlite3.Error as exc:
            raise RetrievalError("PROVIDER_OR_SDK_ERROR") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/rag-index"))
    args = parser.parse_args()
    print(build_index(args.corpus, args.output_dir))


if __name__ == "__main__":
    main()
