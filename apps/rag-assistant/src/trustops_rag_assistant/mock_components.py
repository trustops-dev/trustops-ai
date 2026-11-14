"""Curated synthetic query cases. Selection is authored, not an automatic sufficiency model."""

from dataclasses import dataclass

from .pipeline import Candidate, EvidenceRef, RetrievedEvidence, Selection


@dataclass(frozen=True)
class MockCase:
    query: str
    retrieved: tuple[RetrievedEvidence, ...]
    selection: Selection
    candidate: Candidate | None


class MockComponents:
    def __init__(self, case: MockCase):
        self.case = case

    def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        if query != self.case.query:
            raise ValueError("No fixture for query")
        return self.case.retrieved

    def select(self, query: str, retrieved: tuple[RetrievedEvidence, ...]) -> Selection:
        return self.case.selection

    def generate(self, query: str, selected: tuple[RetrievedEvidence, ...]) -> Candidate:
        if self.case.candidate is None:
            raise ValueError("No candidate for abstention case")
        return self.case.candidate


def grounded_case() -> MockCase:
    """Illustrative policy with one clause, one support span, and one claim."""
    from hashlib import sha256

    query = "When is a receipt due?"
    passage = "Submit the receipt within ten days of delivery."
    digest = sha256(passage.encode("utf-8")).hexdigest()
    document = RetrievedEvidence(
        "doc-receipt", "source-receipt", "v1", "chunk-receipt", passage,
        digest, 1, 0.1, "cosine_distance", False, "Synthetic receipt rule",
        "procurement", "section 1", "snapshot-01",
    )
    ref = EvidenceRef(
        document.document_id, document.source_id, document.source_version,
        document.chunk_id, digest, 0, len(passage), passage,
    )
    return MockCase(
        query, (document,), Selection((document.chunk_id,), ref, "SUFFICIENT_EVIDENCE"),
        Candidate("The receipt is due within ten days of delivery.", "[source-receipt:v1]", ref),
    )
