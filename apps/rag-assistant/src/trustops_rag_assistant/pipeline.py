"""Single-pass synthetic RAG with explicit evidence selection and citation checks."""

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from .trace import AppEvent, EventSink, NullSink


@dataclass(frozen=True)
class RetrievedEvidence:
    document_id: str
    source_id: str
    source_version: str
    chunk_id: str
    chunk_text: str
    content_hash: str
    rank: int
    score: float
    score_kind: str
    higher_is_better: bool
    title: str
    domain: str
    locator: str
    snapshot_ref: str


@dataclass(frozen=True)
class EvidenceRef:
    document_id: str
    source_id: str
    source_version: str
    chunk_id: str
    content_hash: str
    start: int  # Unicode code-point offset in exact chunk_text, exclusive end.
    end: int
    quote: str


@dataclass(frozen=True)
class Selection:
    selected_chunk_ids: tuple[str, ...]
    support: EvidenceRef | None
    sufficiency: str  # SUFFICIENT_EVIDENCE or INSUFFICIENT_EVIDENCE
    reason: str | None = None
    missing_information: str | None = None


@dataclass(frozen=True)
class Candidate:
    claim: str
    citation_marker: str
    support: EvidenceRef


@dataclass(frozen=True)
class RAGResult:
    status: str
    text: str
    citations: tuple[EvidenceRef, ...] = ()
    reason: str | None = None
    missing_information: str | None = None


class Retriever(Protocol):
    def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]: ...


class Selector(Protocol):
    def select(self, query: str, retrieved: tuple[RetrievedEvidence, ...]) -> Selection: ...


class Generator(Protocol):
    def generate(self, query: str, selected: tuple[RetrievedEvidence, ...]) -> Candidate: ...


def valid_support(ref: EvidenceRef, selected: tuple[RetrievedEvidence, ...]) -> bool:
    """Structural/exact quote check; semantic entailment still requires separate review."""
    for item in selected:
        if (
            item.document_id,
            item.source_id,
            item.source_version,
            item.chunk_id,
            item.content_hash,
        ) != (ref.document_id, ref.source_id, ref.source_version, ref.chunk_id, ref.content_hash):
            continue
        if sha256(item.chunk_text.encode("utf-8")).hexdigest() != item.content_hash:
            return False
        return (
            0 <= ref.start < ref.end <= len(item.chunk_text)
            and item.chunk_text[ref.start : ref.end] == ref.quote
        )
    return False


class Pipeline:
    def __init__(
        self,
        retriever: Retriever,
        selector: Selector,
        generator: Generator,
        sink: EventSink | None = None,
    ):
        self.retriever = retriever
        self.selector = selector
        self.generator = generator
        self.sink = sink if sink is not None else NullSink()

    def answer(self, query_id: str, query: str) -> RAGResult:
        if not query_id or not query.strip():
            raise ValueError("query_id and query required")

        def event(kind: str, **details: str | int | None) -> None:
            self.sink.emit(AppEvent(kind, query_id, details))

        event("user_query", query=query)
        retrieved = self.retriever.retrieve(query)
        event("retrieval", count=len(retrieved))
        selection = self.selector.select(query, retrieved)
        selected = tuple(
            item for item in retrieved if item.chunk_id in selection.selected_chunk_ids
        )
        if len(selected) != len(selection.selected_chunk_ids) or len(
            set(selection.selected_chunk_ids)
        ) != len(selection.selected_chunk_ids):
            selection = Selection(
                (),
                None,
                "INSUFFICIENT_EVIDENCE",
                "INCOMPLETE_SUPPORT",
                "Selected source is not in retrieved results",
            )
            selected = ()
        event(
            "evidence_selection",
            sufficiency=selection.sufficiency,
            reason=selection.reason,
            selected_count=len(selected),
        )
        for item in selected:
            event(
                "selected_context",
                source_id=item.source_id,
                source_version=item.source_version,
                chunk_id=item.chunk_id,
                content_hash=item.content_hash,
                chunk_text=item.chunk_text,
            )

        def abstain(reason: str, missing: str) -> RAGResult:
            event("abstention", reason=reason, missing_information=missing)
            return RAGResult(
                "ABSTENTION",
                "The available sources do not substantiate an answer.",
                reason=reason,
                missing_information=missing,
            )

        if selection.sufficiency != "SUFFICIENT_EVIDENCE":
            return abstain(
                selection.reason or "INCOMPLETE_SUPPORT",
                selection.missing_information or "Supporting evidence",
            )
        if (
            not selected
            or selection.support is None
            or not valid_support(selection.support, selected)
        ):
            return abstain("INCOMPLETE_SUPPORT", "Verifiable selected source passage")
        candidate = self.generator.generate(query, selected)
        event("answer_candidate", claim=candidate.claim, source_id=candidate.support.source_id)
        if (
            not candidate.claim.strip()
            or candidate.citation_marker
            != (f"[{candidate.support.source_id}:{candidate.support.source_version}]")
            or candidate.support != selection.support
            or not valid_support(candidate.support, selected)
        ):
            event("citation_binding", result="INVALID")
            return abstain("INVALID_CITATION_BINDING", "A citation to the selected passage")
        event(
            "citation_binding",
            result="VALID",
            source_id=candidate.support.source_id,
            source_version=candidate.support.source_version,
            chunk_id=candidate.support.chunk_id,
            quote=candidate.support.quote,
            start=candidate.support.start,
            end=candidate.support.end,
        )
        text = f"{candidate.claim} {candidate.citation_marker}"
        event("final_response", status="ANSWER")
        return RAGResult("ANSWER", text, (candidate.support,))
