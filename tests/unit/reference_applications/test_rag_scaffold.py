"""The selected snapshot alone may substantiate a synthetic final answer."""

from dataclasses import replace

from trustops_rag_assistant.mock_components import MockComponents, grounded_case
from trustops_rag_assistant.pipeline import Pipeline, Selection
from trustops_rag_assistant.trace import RecordingSink


def test_grounded_answer_cites_exact_selected_passage() -> None:
    case = grounded_case()
    sink = RecordingSink()
    result = Pipeline(MockComponents(case), MockComponents(case), MockComponents(case), sink).answer(
        "query-1", case.query
    )
    assert result.status == "ANSWER"
    assert result.text.endswith("[source-receipt:v1]")
    assert result.citations == (case.selection.support,)
    assert [event.kind for event in sink.events] == [
        "user_query", "retrieval", "evidence_selection", "selected_context", "answer_candidate",
        "citation_binding", "final_response",
    ]


def test_insufficient_or_conflicting_evidence_abstains_without_generation() -> None:
    case = grounded_case()
    case = replace(case, selection=Selection(
        ("chunk-receipt",), None, "INSUFFICIENT_EVIDENCE",
        "CONFLICTING_EVIDENCE", "Conflicting receipt deadlines",
    ), candidate=None)
    result = Pipeline(*(MockComponents(case) for _ in range(3))).answer("query-2", case.query)
    assert result.status == "ABSTENTION"
    assert result.reason == "CONFLICTING_EVIDENCE"
    assert result.citations == ()


def test_fabricated_citation_marker_is_rejected() -> None:
    case = grounded_case()
    assert case.candidate is not None
    case = replace(case, candidate=replace(case.candidate, citation_marker="[invented:v1]"))
    result = Pipeline(*(MockComponents(case) for _ in range(3))).answer("query-3", case.query)
    assert (result.status, result.reason) == ("ABSTENTION", "INVALID_CITATION_BINDING")
