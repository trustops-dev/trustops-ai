"""Selected-context integrity, fixture abstention and distinct retrieval errors."""

from dataclasses import replace
from hashlib import sha256
from typing import Literal
from unittest.mock import Mock

import pytest

from trustops_rag_assistant.mock_components import MockComponents, grounded_case
from trustops_rag_assistant.pipeline import Pipeline, RetrievalError, Selection
from trustops_rag_assistant.trace import RecordingSink


@pytest.mark.parametrize("reason", ["INCOMPLETE_SUPPORT", "CONFLICTING_EVIDENCE"])
def test_authored_insufficient_or_conflicting_selection_never_generates(reason: str) -> None:
    case = grounded_case()
    case = replace(
        case,
        selection=Selection(
            (case.retrieved[0].chunk_id,),
            None,
            "INSUFFICIENT_EVIDENCE",
            reason,
            "Support needed",
        ),
    )
    components = MockComponents(case)
    generator = Mock()
    result = Pipeline(components, components, generator).answer("q-abstain", case.query)
    assert (result.status, result.reason, result.citations) == ("ABSTENTION", reason, ())
    generator.generate.assert_not_called()


def test_zero_hits_are_not_a_technical_retrieval_error() -> None:
    case = grounded_case()
    case = replace(
        case,
        retrieved=(),
        selection=Selection(
            (),
            None,
            "INSUFFICIENT_EVIDENCE",
            "NO_RELEVANT_EVIDENCE",
            "No matching source",
        ),
    )
    components = MockComponents(case)
    generator = Mock()
    sink = RecordingSink()
    result = Pipeline(components, components, generator, sink).answer("q-empty", case.query)
    assert (result.status, result.reason) == ("ABSTENTION", "NO_RELEVANT_EVIDENCE")
    assert any(e.kind == "retrieval" and e.details["count"] == 0 for e in sink.events)
    assert not any(e.kind == "retrieval_error" for e in sink.events)
    generator.generate.assert_not_called()


@pytest.mark.parametrize(
    "field", ["document_id", "source_id", "source_version", "chunk_id", "content_hash"]
)
def test_candidate_citation_identity_must_match_selected_snapshot(field: str) -> None:
    case = grounded_case()
    assert case.candidate is not None
    support = case.candidate.support
    if field == "document_id":
        altered = replace(support, document_id="unselected-value")
    elif field == "source_id":
        altered = replace(support, source_id="unselected-value")
    elif field == "source_version":
        altered = replace(support, source_version="unselected-value")
    elif field == "chunk_id":
        altered = replace(support, chunk_id="unselected-value")
    else:
        altered = replace(support, content_hash="unselected-value")
    case = replace(
        case,
        candidate=replace(
            case.candidate,
            support=altered,
            citation_marker=f"[{altered.source_id}:{altered.source_version}]",
        ),
    )
    components = MockComponents(case)
    result = Pipeline(components, components, components).answer("q-identity", case.query)
    assert (result.status, result.reason, result.citations) == (
        "ABSTENTION",
        "INVALID_CITATION_BINDING",
        (),
    )


@pytest.mark.parametrize(
    "corruption", ["negative_offset", "past_end", "wrong_quote", "changed_text"]
)
def test_invalid_source_span_or_hash_is_rejected_before_generation(corruption: str) -> None:
    case = grounded_case()
    ref = case.selection.support
    assert ref is not None
    if corruption == "changed_text":
        case = replace(case, retrieved=(replace(case.retrieved[0], chunk_text="Altered text"),))
    else:
        if corruption == "negative_offset":
            ref = replace(ref, start=-1)
        elif corruption == "past_end":
            ref = replace(ref, end=len(case.retrieved[0].chunk_text) + 1)
        else:
            ref = replace(ref, quote="Invented passage")
        case = replace(case, selection=replace(case.selection, support=ref))
    components = MockComponents(case)
    generator = Mock()
    result = Pipeline(components, components, generator).answer("q-span", case.query)
    assert (result.status, result.reason) == ("ABSTENTION", "INCOMPLETE_SUPPORT")
    generator.generate.assert_not_called()


def test_retrieved_but_excluded_document_cannot_substantiate_answer() -> None:
    case = grounded_case()
    other = replace(
        case.retrieved[0], document_id="doc-other", source_id="source-other", chunk_id="chunk-other"
    )
    # The support still points to the retrieved receipt document, but it is excluded.
    case = replace(
        case,
        retrieved=(*case.retrieved, other),
        selection=replace(case.selection, selected_chunk_ids=(other.chunk_id,)),
    )
    components = MockComponents(case)
    generator = Mock()
    result = Pipeline(components, components, generator).answer("q-excluded", case.query)
    assert result.reason == "INCOMPLETE_SUPPORT"
    generator.generate.assert_not_called()


def test_generator_receives_only_exact_selected_context() -> None:
    case = grounded_case()
    other = replace(case.retrieved[0], document_id="doc-other", chunk_id="chunk-other")
    case = replace(case, retrieved=(*case.retrieved, other))
    components = MockComponents(case)
    generator = Mock(wraps=components)
    sink = RecordingSink()
    result = Pipeline(components, components, generator, sink).answer("q-context", case.query)
    assert result.status == "ANSWER"
    generator.generate.assert_called_once_with(case.query, (case.retrieved[0],))
    contexts = [e.details for e in sink.events if e.kind == "selected_context"]
    assert len(contexts) == 1
    assert contexts[0]["chunk_text"] == case.retrieved[0].chunk_text
    assert contexts[0]["content_hash"] == case.retrieved[0].content_hash


def test_citation_event_correlates_to_selected_snapshot_and_final_citation() -> None:
    case = grounded_case()
    components = MockComponents(case)
    sink = RecordingSink()
    result = Pipeline(components, components, components, sink).answer("q-binding", case.query)
    selected = next(e.details for e in sink.events if e.kind == "selected_context")
    binding = next(e.details for e in sink.events if e.kind == "citation_binding")
    assert result.status == "ANSWER"
    assert len(result.citations) == 1
    for field in ("document_id", "source_id", "source_version", "chunk_id", "content_hash"):
        assert binding[field] == selected[field] == getattr(result.citations[0], field)
    assert binding["snapshot_ref"] == selected["snapshot_ref"] == "snapshot-01"
    assert {e.query_id for e in sink.events} == {"q-binding"}


def test_two_authored_contradictory_selected_passages_abstain_without_generation() -> None:
    case = grounded_case()
    opposite = "Submit the receipt no earlier than thirty days after delivery."
    other = replace(
        case.retrieved[0],
        document_id="doc-receipt-opposite",
        source_id="source-receipt-opposite",
        chunk_id="chunk-receipt-opposite",
        chunk_text=opposite,
        content_hash=sha256(opposite.encode("utf-8")).hexdigest(),
        rank=2,
    )
    case = replace(
        case,
        retrieved=(*case.retrieved, other),
        selection=Selection(
            (case.retrieved[0].chunk_id, other.chunk_id),
            None,
            "INSUFFICIENT_EVIDENCE",
            "CONFLICTING_EVIDENCE",
            "Incompatible receipt deadlines; source precedence not established",
        ),
        candidate=None,
    )
    components = MockComponents(case)
    generator = Mock()
    sink = RecordingSink()
    result = Pipeline(components, components, generator, sink).answer("q-conflict", case.query)
    assert (result.status, result.reason, result.citations) == (
        "ABSTENTION",
        "CONFLICTING_EVIDENCE",
        (),
    )
    generator.generate.assert_not_called()
    assert [e.details["chunk_text"] for e in sink.events if e.kind == "selected_context"] == [
        case.retrieved[0].chunk_text,
        opposite,
    ]


def test_two_consistent_selected_sources_preserve_context_and_cited_identity() -> None:
    case = grounded_case()
    corroborating = "Receipts are due within ten days of delivery."
    other = replace(
        case.retrieved[0],
        document_id="doc-receipt-confirmation",
        source_id="source-receipt-confirmation",
        chunk_id="chunk-receipt-confirmation",
        chunk_text=corroborating,
        content_hash=sha256(corroborating.encode("utf-8")).hexdigest(),
        rank=2,
    )
    case = replace(
        case,
        retrieved=(*case.retrieved, other),
        selection=replace(
            case.selection, selected_chunk_ids=(case.retrieved[0].chunk_id, other.chunk_id)
        ),
    )
    components = MockComponents(case)
    generator = Mock(wraps=components)
    result = Pipeline(components, components, generator).answer("q-two-sources", case.query)
    assert result.status == "ANSWER"
    assert result.citations == (case.selection.support,)
    generator.generate.assert_called_once_with(case.query, case.retrieved)


@pytest.mark.parametrize("category", ["TIMEOUT", "PROVIDER_OR_SDK_ERROR"])
def test_retrieval_failure_is_error_not_evidence_abstention(
    category: Literal["TIMEOUT", "PROVIDER_OR_SDK_ERROR"],
) -> None:
    retriever, selector, generator = Mock(), Mock(), Mock()
    retriever.retrieve.side_effect = RetrievalError(category)
    sink = RecordingSink()
    result = Pipeline(retriever, selector, generator, sink).answer("q-fault", "Receipt deadline?")
    assert (result.status, result.reason, result.citations) == ("ERROR", "RETRIEVAL_ERROR", ())
    retriever.retrieve.assert_called_once()
    selector.select.assert_not_called()
    generator.generate.assert_not_called()
    assert [e.kind for e in sink.events] == ["user_query", "retrieval_error", "final_response"]
    assert sink.events[1].details == {"category": category}


def test_unclassified_programming_error_is_not_silently_relabelled() -> None:
    retriever = Mock()
    retriever.retrieve.side_effect = ValueError("Fixture bug")
    with pytest.raises(ValueError, match="Fixture bug"):
        Pipeline(retriever, Mock(), Mock()).answer("q-bug", "Receipt deadline?")


def test_adapter_wrapped_provider_exception_does_not_leak_raw_message() -> None:
    secret = "SENSITIVE_FIXTURE_PROVIDER_MESSAGE_do_not_emit"

    class SanitizingAdapter:
        def retrieve(self, query: str) -> tuple[()]:
            try:
                raise RuntimeError(f"Provider endpoint and token: {secret}")
            except RuntimeError as exc:
                raise RetrievalError("PROVIDER_OR_SDK_ERROR") from exc

    selector, generator = Mock(), Mock()
    sink = RecordingSink()
    result = Pipeline(SanitizingAdapter(), selector, generator, sink).answer(
        "q-provider-raw", "Receipt deadline?"
    )
    assert (result.status, result.reason) == ("ERROR", "RETRIEVAL_ERROR")
    assert sink.events[1].details == {"category": "PROVIDER_OR_SDK_ERROR"}
    assert secret not in repr(sink.events)
    assert secret not in repr(result)
    selector.select.assert_not_called()
    generator.generate.assert_not_called()
