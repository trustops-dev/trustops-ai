"""Check that the dashboard UX architecture documents agree with each other.

The matrix, wireframes, navigation table, journeys and status vocabulary under
``docs/architecture/dashboard`` are reviewed by hand. These checks keep them from
drifting apart: every field has one screen and one owner, every evidence requirement is
covered, every wireframe marker resolves, and every state has a distinct signature.
"""

import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DOCS = REPO_ROOT / "docs" / "architecture" / "dashboard"
EVIDENCE_DOC = (
    REPO_ROOT / "docs" / "architecture" / "reference-applications" / "trace-evidence-contract.md"
)

SCREEN_BY_PREFIX = {
    "OVW": "SCR-OVW",
    "APP": "SCR-APP",
    "TRX": "SCR-TRX",
    "TRD": "SCR-TRD",
    "RCA": "SCR-RCA",
    "RAG": "SCR-RAG",
    "REL": "SCR-REL",
}
PRIMARY_SCREENS = {"OVW", "APP", "TRX", "RCA", "RAG", "REL"}
OWNERS = {"Nour", "Ahmed", "Mohab", "Mohamed", "Alaa"}
BASES = {"FACT", "DECISION", "OPEN"}
SHAPES = {
    "id",
    "text",
    "enum",
    "ts",
    "num",
    "count",
    "flag",
    "obj",
    "list",
    "table",
    "ref",
    "ver",
    "graph",
}
REQUIRED_LABELS = {"Pass", "Review", "Block", "Not evaluated", "Evaluator failed", "Not applicable"}

FIELD_ID = r"(?:OVW|APP|TRX|TRD|RCA|RAG|REL)-\d{2}"
FIELD_ID_PATTERN = re.compile(rf"\b{FIELD_ID}\b")
MARKER_PATTERN = re.compile(rf"\{{(>?)({FIELD_ID})\}}")
EDGE_ID_PATTERN = re.compile(r"\bN-\d{2}\b")


@dataclass(frozen=True)
class Field:
    field_id: str
    screen: str
    owner: str
    shape: str
    source: str
    absence: str
    basis: str


def _read(name: str) -> str:
    return (DASHBOARD_DOCS / name).read_text(encoding="utf-8")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _screen_sections(text: str) -> dict[str, str]:
    """Split a document on its ``## SCR-XXX`` headings."""
    sections: dict[str, str] = {}
    for chunk in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        heading, _, body = chunk.partition("\n")
        match = re.match(r"(SCR-[A-Z]{3})\b", heading)
        if match:
            sections[match.group(1)] = body
    return sections


def _matrix_fields() -> list[Field]:
    fields: list[Field] = []
    for screen, body in _screen_sections(_read("field-owner-matrix.md")).items():
        for line in body.splitlines():
            cells = _cells(line)
            if line.startswith("|") and re.fullmatch(FIELD_ID, cells[0]):
                fields.append(
                    Field(
                        field_id=cells[0],
                        screen=screen,
                        owner=cells[4],
                        shape=cells[3],
                        source=cells[5],
                        absence=cells[6],
                        basis=cells[7],
                    )
                )
    return fields


def _table_rows(text: str, header_start: str) -> list[list[str]]:
    """Return the data rows of the first table whose header starts with ``header_start``."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(header_start):
            rows: list[list[str]] = []
            for row in lines[index + 2 :]:
                if not row.startswith("|"):
                    break
                rows.append(_cells(row))
            return rows
    raise AssertionError(f"table starting with {header_start!r} not found")


@pytest.fixture(scope="module")
def fields() -> list[Field]:
    return _matrix_fields()


def test_matrix_covers_exactly_the_seven_screens(fields: list[Field]) -> None:
    assert {field.screen for field in fields} == set(SCREEN_BY_PREFIX.values())
    assert set(_screen_sections(_read("field-owner-matrix.md"))) == set(SCREEN_BY_PREFIX.values())


def test_every_field_has_one_screen_and_one_owner(fields: list[Field]) -> None:
    ids = [field.field_id for field in fields]
    assert len(ids) == len(set(ids)), "a field ID appears more than once"

    for field in fields:
        prefix = field.field_id.split("-")[0]
        assert SCREEN_BY_PREFIX[prefix] == field.screen, f"{field.field_id} is in the wrong section"
        assert field.owner in OWNERS, f"{field.field_id} owner {field.owner!r} is not one owner"
        assert field.shape in SHAPES, f"{field.field_id} shape {field.shape!r}"
        assert field.basis in BASES, f"{field.field_id} basis {field.basis!r}"
        assert field.source, f"{field.field_id} has no source"


def test_every_backend_owner_owns_at_least_one_field(fields: list[Field]) -> None:
    assert {field.owner for field in fields} == OWNERS


def test_every_trace_evidence_requirement_is_mapped_to_a_field(fields: list[Field]) -> None:
    required = set(re.findall(r"^\| (E\d{2}) ", EVIDENCE_DOC.read_text(encoding="utf-8"), re.M))
    assert len(required) == 27

    covered = {token for field in fields for token in re.findall(r"E\d{2}", field.source)}
    assert required - covered == set(), "evidence requirements with no field"


def test_absence_codes_are_defined_in_the_status_vocabulary(fields: list[Field]) -> None:
    signature_rows = _table_rows(_read("status-vocabulary.md"), "| State | Scope label |")
    defined = {row[0] for row in signature_rows if re.fullmatch(r"[A-Z]{2}", row[0])}
    used = {
        code
        for field in fields
        for code in field.absence.split()
        if field.absence not in {"—", "-"}
    }
    assert used <= defined, f"absence codes with no definition: {used - defined}"
    assert defined == {"NE", "EF", "NA", "PE", "UN", "ME", "RD", "NC"}


def test_every_state_has_a_distinct_non_colour_signature() -> None:
    rows = _table_rows(_read("status-vocabulary.md"), "| State | Scope label |")
    assert len(rows) >= 14

    labels = [(row[1], row[2]) for row in rows]
    glyphs = [row[3] for row in rows]
    signatures = [(row[3], row[4], row[5]) for row in rows]
    assert len(set(labels)) == len(labels), "a scope and label pair is repeated"
    assert len(set(glyphs)) == len(glyphs), "two states share a glyph"
    assert len(set(signatures)) == len(signatures), "two states share a signature"
    for row in rows:
        assert all(row), f"{row[0]} has an empty signature column"

    assert REQUIRED_LABELS <= {row[2] for row in rows}


def test_wireframes_place_every_field_once_on_its_home_screen(fields: list[Field]) -> None:
    known = {field.field_id: field.screen for field in fields}
    sections = _screen_sections(_read("information-architecture.md"))
    assert set(sections) == set(SCREEN_BY_PREFIX.values())

    placed: dict[str, set[str]] = {screen: set() for screen in sections}
    for screen, body in sections.items():
        for projection, field_id in MARKER_PATTERN.findall(body):
            assert field_id in known, f"{screen} references unknown field {field_id}"
            if projection:
                assert known[field_id] != screen, f"{field_id} is a projection of its own home"
            else:
                assert known[field_id] == screen, f"{field_id} is placed on {screen}, not its home"
                placed[screen].add(field_id)

    for field in fields:
        assert field.field_id in placed[field.screen], f"{field.field_id} is not on its wireframe"


def _contextual_edges() -> list[tuple[str, str, str]]:
    text = _read("information-architecture.md")
    rows = _table_rows(text, "| Edge | From | To |")
    return [(row[0], row[1], row[2]) for row in rows]


def test_navigation_edges_are_well_formed() -> None:
    edges = _contextual_edges()
    ids = [edge_id for edge_id, _, _ in edges]
    assert len(ids) == len(set(ids))

    screens = set(SCREEN_BY_PREFIX)
    for edge_id, origin, target in edges:
        assert origin in screens and target in screens, f"{edge_id} names an unknown screen"
        assert origin != target, f"{edge_id} links a screen to itself"


def test_every_screen_reaches_trace_detail_evidence_quickly() -> None:
    edges = _contextual_edges()
    outgoing: dict[str, set[str]] = {screen: set() for screen in SCREEN_BY_PREFIX}
    for _, origin, target in edges:
        outgoing[origin].add(target)

    def hops(start: str, goal: str) -> int:
        seen = {start}
        queue = deque([(start, 0)])
        while queue:
            screen, depth = queue.popleft()
            if screen == goal:
                return depth
            for neighbour in outgoing[screen] - seen:
                seen.add(neighbour)
                queue.append((neighbour, depth + 1))
        raise AssertionError(f"{start} cannot reach {goal}")

    for screen in PRIMARY_SCREENS:
        assert hops(screen, "TRD") <= 2, f"{screen} is too far from Trace Detail"
    assert hops("REL", "TRD") == 1, "a blocked gate must link straight to traces"
    assert {origin for _, origin, target in edges if target == "TRD"} >= PRIMARY_SCREENS - {"APP"}


def test_trace_detail_links_back_to_the_other_screens() -> None:
    targets = {target for _, origin, target in _contextual_edges() if origin == "TRD"}
    assert targets >= {"TRX", "RCA", "RAG", "REL", "APP"}


def test_journeys_and_architecture_only_cite_real_fields_and_edges(fields: list[Field]) -> None:
    known_fields = {field.field_id for field in fields}
    known_edges = {edge_id for edge_id, _, _ in _contextual_edges()}

    for name in ("reviewer-journeys.md", "information-architecture.md", "paper-walkthroughs.md"):
        text = _read(name)
        cited_fields = set(FIELD_ID_PATTERN.findall(text))
        assert cited_fields <= known_fields, (
            f"{name} cites unknown fields {cited_fields - known_fields}"
        )
        cited_edges = set(EDGE_ID_PATTERN.findall(text))
        assert cited_edges <= known_edges, f"{name} cites unknown edges {cited_edges - known_edges}"


def test_every_screen_appears_in_a_reviewer_journey() -> None:
    text = _read("reviewer-journeys.md")
    for name in (
        "Overview",
        "Trace Explorer",
        "Trace Detail",
        "Failure & RCA",
        "RAG Diagnostics",
        "Release Gate",
    ):
        assert name in text, f"no journey step uses {name}"
    assert "Applications" in text


def test_owner_review_record_lists_all_five_owners() -> None:
    rows = _table_rows(_read("README.md"), "| Owner | Review needed |")
    assert {row[0] for row in rows} == OWNERS
    for row in rows:
        status, evidence = row[2], row[4]
        assert status, f"{row[0]} has no status"
        assert status == "PENDING" or evidence not in {"", "—", "-"}, (
            f"{row[0]} is marked {status} without evidence"
        )
