"""Offline search-to-citation proof for the pinned synthetic HR snapshot."""

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from trustops_rag_assistant.offline_index import (
    DEFAULT_CORPUS,
    INDEX_VERSION,
    SNAPSHOT,
    OfflineRetriever,
    build_index,
)
from trustops_rag_assistant.pipeline import (
    Candidate,
    EvidenceRef,
    Pipeline,
    RetrievalError,
    RetrievedEvidence,
    Selection,
)
from trustops_rag_assistant.trace import RecordingSink

CORPUS = Path(__file__).resolve().parents[3] / DEFAULT_CORPUS
QUESTION = (
    "Does emergency leave require five working days of notice, and is it automatically approved?"
)


class FirstPassage:
    """Extractive test double. Both calls take their text from the pipeline arguments."""

    @staticmethod
    def ref(hit: RetrievedEvidence) -> EvidenceRef:
        quote = hit.chunk_text.rstrip("\n")
        return EvidenceRef(
            hit.document_id,
            hit.source_id,
            hit.source_version,
            hit.chunk_id,
            hit.content_hash,
            0,
            len(quote),
            quote,
        )

    def select(self, query: str, retrieved: tuple[RetrievedEvidence, ...]) -> Selection:
        first = retrieved[0]
        return Selection((first.chunk_id,), self.ref(first), "SUFFICIENT_EVIDENCE")

    def generate(self, query: str, selected: tuple[RetrievedEvidence, ...]) -> Candidate:
        (hit,) = selected
        ref = self.ref(hit)
        return Candidate(ref.quote, f"[{hit.source_id}:{hit.source_version}]", ref)


def test_persisted_search_supplies_grounded_answer(tmp_path: Path) -> None:
    # Prove the build can run with only the manifest and eligible source bytes.
    corpus = tmp_path / "corpus"
    (corpus / "documents").mkdir(parents=True)
    shutil.copyfile(CORPUS / "source-manifest.json", corpus / "source-manifest.json")
    for n in (1, 2, 3, 4, 5, 6, 8):
        rel = Path("documents") / f"doc-{n:03d}.txt"
        shutil.copyfile(CORPUS / rel, corpus / rel)
    path = build_index(corpus, tmp_path / "first")
    rebuilt = build_index(corpus, tmp_path / "second")
    assert rebuilt.read_bytes() == path.read_bytes()
    shutil.rmtree(corpus)
    retriever = OfflineRetriever(path)
    hits = retriever.retrieve(QUESTION)
    first = hits[0]
    assert (first.rank, first.document_id, first.source_id, first.source_version) == (
        1,
        "doc-003",
        "src-003",
        "review-r1",
    )
    assert first.chunk_id == "doc-003@review-r1:0:332"
    assert first.content_hash == "a0ddf7a477906b28bd28172850effc10d9f4eb49d04f5767d2cdb8374bcd6139"
    assert (first.score_kind, first.higher_is_better) == ("sqlite_fts5_bm25", False)
    assert [h.score for h in hits] == sorted(h.score for h in hits)
    assert retriever.retrieve("zznohitszz") == ()
    sink = RecordingSink()
    extract = FirstPassage()
    result = Pipeline(retriever, extract, extract, sink).answer("q-002", QUESTION)
    assert result.status == "ANSWER"
    assert "Unplanned emergency leave is exempt" in result.text
    assert "does not establish approval" in result.text
    assert result.text.endswith("[src-003:review-r1]")
    (ref,) = result.citations
    assert ref.chunk_id == first.chunk_id and ref.content_hash == first.content_hash
    assert ref.quote == first.chunk_text[ref.start : ref.end]
    context = next(e.details for e in sink.events if e.kind == "selected_context")
    assert (context["snapshot_ref"], context["index_version"]) == (SNAPSHOT, INDEX_VERSION)
    binding = next(e.details for e in sink.events if e.kind == "citation_binding")
    assert binding["result"] == "VALID" and binding["quote"] == ref.quote
    with closing(sqlite3.connect(path)) as db:
        ids = {row[0] for row in db.execute("SELECT document_id FROM chunks")}
    assert ids == {f"doc-{n:03d}" for n in (1, 2, 3, 4, 5, 6, 8)}


def test_modified_source_cannot_replace_valid_index(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    shutil.copytree(CORPUS, corpus)
    index = build_index(corpus, tmp_path)
    original = index.read_bytes()
    (corpus / "documents/doc-003.txt").write_bytes(b"Changed source")
    with pytest.raises(ValueError, match="Source hash mismatch for doc-003"):
        build_index(corpus, tmp_path)
    assert index.read_bytes() == original


def test_missing_index_is_a_retrieval_error(tmp_path: Path) -> None:
    path = tmp_path / "absent.sqlite3"
    with pytest.raises(RetrievalError, match="PROVIDER_OR_SDK_ERROR"):
        OfflineRetriever(path).retrieve(QUESTION)
    assert not path.exists()
