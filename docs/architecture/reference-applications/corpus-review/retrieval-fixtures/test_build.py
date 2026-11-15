"""Offline fixture integrity and evaluation-boundary checks."""

import json
import runpy
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

builder = runpy.run_path(str(Path(__file__).with_name("build.py")))
CORPUS = builder["CORPUS"]
OUT = builder["OUT"]
build = builder["build"]
canonical_json = builder["canonical_json"]


def test_committed_fixtures_match_source_bytes() -> None:
    for name, value in zip(
        ("inference-inputs.json", "evaluation-sidecar.json", "proposed-policy-pairing.json"),
        build(),
        strict=True,
    ):
        assert (OUT / name).read_bytes() == canonical_json(value)


def test_inference_projection_excludes_expected_labels_and_provisional_policy() -> None:
    inference, labels, pairing = build()
    assert len(inference["cases"]) == len(labels["cases"]) == 8
    assert "expected_outcome" not in json.dumps(inference)
    assert "review_only" not in json.dumps(inference)
    assert "intentionally_invalid_selection" not in json.dumps(inference)
    assert "synthetic-procurement-policy-kb-v0.1" not in json.dumps(inference)
    assert pairing["index_version"] is None
    assert pairing["status"] == "PENDING_INTEGRATION_REVIEW"
    q6 = next(c for c in inference["cases"] if c["query_id"] == "q-006")
    assert [d["document_id"] for d in q6["returned"]] == ["doc-006", "doc-007"]
    assert all(d["chunk_id"] in q6["selected_chunk_ids"] for d in q6["returned"])


def test_tampered_source_fails_closed() -> None:
    with TemporaryDirectory() as temp:
        corpus = Path(temp) / "corpus-review"
        shutil.copytree(CORPUS, corpus)
        doc = corpus / "documents/doc-003.txt"
        doc.write_bytes(doc.read_bytes().replace(b"emergency", b"routine"))
        with pytest.raises(ValueError, match="hash/span mismatch"):
            build(corpus)


def test_truncated_exception_cannot_become_a_published_unit() -> None:
    with TemporaryDirectory() as temp:
        corpus = Path(temp) / "corpus-review"
        shutil.copytree(CORPUS, corpus)
        manifest_path = corpus / "source-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"][2]["protected_units"] = [{"start": 0, "end": 118}]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="incomplete protected source unit"):
            build(corpus)


def test_snapshot_cannot_switch_to_unpinned_version() -> None:
    with TemporaryDirectory() as temp:
        corpus = Path(temp) / "corpus-review"
        shutil.copytree(CORPUS, corpus)
        manifest_path = corpus / "source-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["snapshots"][0]["source_versions"][0]["source_version"] = "review-r2"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="wrong source version"):
            build(corpus)


def test_evaluation_expectation_does_not_change_inference_input() -> None:
    original_inference, _, _ = build()
    with TemporaryDirectory() as temp:
        corpus = Path(temp) / "corpus-review"
        shutil.copytree(CORPUS, corpus)
        cases_path = corpus / "review-cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        cases["cases"][0]["expected_response_summary"] = "Different evaluation expectation"
        cases_path.write_text(json.dumps(cases), encoding="utf-8")
        inference, _, _ = build(corpus)
        assert inference["cases"] == original_inference["cases"]
