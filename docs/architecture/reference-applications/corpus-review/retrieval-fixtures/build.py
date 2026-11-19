"""Build deterministic, offline authored retrieval fixtures from exact source bytes.

Inference input and evaluation-only labels are deliberately written to separate files.
No model, embedding, vector search, or native token count is performed.
"""

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def read_json(path: Path) -> dict:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def canonical_json(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def source(record: dict, corpus: Path) -> dict:
    relative = Path(record["canonical_text_path"])
    if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "documents":
        raise ValueError("source path must remain inside corpus documents")
    raw = (corpus / relative).read_bytes()
    content = raw.decode("utf-8")
    if content != unicodedata.normalize("NFC", content) or "\r" in content:
        raise ValueError(f"noncanonical source: {relative}")
    digest = hashlib.sha256(raw).hexdigest()
    span = record["locator"]["document_char_span"]
    if digest != record["content_hash"] or span != {"start": 0, "end": len(content)}:
        raise ValueError(f"source hash/span mismatch: {relative}")
    if record["protected_units"] != [span]:
        raise ValueError(f"incomplete protected source unit: {relative}")
    if record["visibility"] != "mvp_shared" or record["synthetic"] is not True:
        raise ValueError(f"source outside synthetic review scope: {relative}")
    return {
        "document_id": record["document_id"],
        "source_id": record["source_id"],
        "source_version": record["source_version"],
        "chunk_id": f"{record['document_id']}@{record['source_version']}:0:{len(content)}",
        "chunk_text": content,
        "content_hash": digest,
        "document_char_span": span,
        "title": record["title"],
        "domain": record["domain"],
        "visibility": record["visibility"],
    }


def build(corpus: Path = CORPUS, policy_root: Path = CORPUS.parents[3]) -> tuple[dict, dict, dict]:
    manifest = read_json(corpus / "source-manifest.json")
    reviews = read_json(corpus / "review-cases.json")
    authored = read_json(corpus / "retrieval-fixtures/authored-inputs.json")
    review_by_id = {r["query_id"]: r for r in reviews["cases"]}
    if len(review_by_id) != len(reviews["cases"]) or {
        r["query_id"] for r in authored["cases"]
    } != set(review_by_id):
        raise ValueError("authored/review case IDs disagree")
    records = {r["document_id"]: r for r in manifest["documents"]}
    if len(records) != len(manifest["documents"]):
        raise ValueError("duplicate document identity")
    chunks = {key: source(record, corpus) for key, record in records.items()}
    snapshots = {}
    for item in manifest["snapshots"]:
        members = item["source_versions"]
        ids = [m["document_id"] for m in members]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate active document version")
        for member in members:
            if chunks[member["document_id"]]["source_version"] != member["source_version"]:
                raise ValueError("snapshot references wrong source version")
        snapshots[item["snapshot_id"]] = ids

    inference_cases = []
    sidecar_cases = []
    for authored_case in authored["cases"]:
        review = review_by_id[authored_case["query_id"]]
        if (authored_case["snapshot_id"], authored_case["question"]) != (
            review["snapshot_id"],
            review["question"],
        ):
            raise ValueError("authored question/snapshot differs from evaluation sidecar")
        eligible = snapshots[authored_case["snapshot_id"]]
        returned = authored_case["authored_returned_documents"]
        selected = authored_case["authored_selected_documents"]
        if len(set(returned)) != len(returned) or not set(selected) <= set(returned):
            raise ValueError("invalid authored retrieval/selection")
        if not set(returned) <= set(eligible):
            raise ValueError("retrieved document not in pinned snapshot")
        for label in (
            "review_only_relevant_documents",
            "review_only_irrelevant_documents",
            "review_only_conflicting_documents",
        ):
            if not set(review[label]) <= set(eligible):
                raise ValueError("evaluation label outside pinned snapshot")
        if "intentionally_invalid_selection" in review:
            invalid = review["intentionally_invalid_selection"]
            full = chunks[invalid["document_id"]]["chunk_text"]
            if invalid["text"] != full[invalid["start"] : invalid["end"]]:
                raise ValueError(
                    "invalid-selection example is no longer the specified source slice"
                )
            if invalid["end"] >= len(full):
                raise ValueError("invalid-selection example ceased to be a partial source")
        inference_cases.append(
            {
                "query_id": authored_case["query_id"],
                "snapshot_id": authored_case["snapshot_id"],
                "question": authored_case["question"],
                "trusted_scope": "mvp_shared",
                "returned": [dict(chunks[id], rank=rank) for rank, id in enumerate(returned, 1)],
                "selected_chunk_ids": [chunks[id]["chunk_id"] for id in selected],
                "score": None,
                "score_status": "AUTHORED_ORDER_NOT_MEASURED",
            }
        )
        sidecar_cases.append(
            {
                "query_id": review["query_id"],
                "expected_outcome": review["expected_outcome"],
                "expected_response_summary": review["expected_response_summary"],
                "required_support_phrases": review["required_support_phrases"],
                "relevant_document_ids": review["review_only_relevant_documents"],
                "irrelevant_document_ids": review["review_only_irrelevant_documents"],
                "conflicting_document_ids": review["review_only_conflicting_documents"],
                **(
                    {"intentionally_invalid_selection": review["intentionally_invalid_selection"]}
                    if "intentionally_invalid_selection" in review
                    else {}
                ),
            }
        )

    pairing = read_json(corpus / "proposed-policy-kb-v0.1.json")
    proposed = []
    for record in pairing["source_membership"]:
        raw = (policy_root / record["canonical_text_path"]).read_bytes()
        content = raw.decode("utf-8")
        if hashlib.sha256(raw).hexdigest() != record["content_sha256"]:
            raise ValueError("proposed policy source hash mismatch")
        if len(content) != record["text_codepoints"] or [
            record["protected_unit_start"],
            record["protected_unit_end"],
        ] != [0, len(content)]:
            raise ValueError("proposed policy protected span mismatch")
        proposed.append(
            {
                "document_id": record["document_id"],
                "source_id": record["source_id"],
                "source_version": record["source_version"],
                "policy_id": record["policy_id"],
                "content_hash": record["content_sha256"],
                "protected_unit": [0, len(content)],
            }
        )
    if (
        pairing["index_version"] is not None
        or pairing["publication_or_runtime_activation"] != "PENDING_INTEGRATION_REVIEW"
    ):
        raise ValueError("provisional policy pairing changed status")
    return (
        {
            "artifact_kind": "OFFLINE_AUTHORED_RETRIEVAL_INPUT",
            "version": "retrieval-fixtures-v0.1",
            "source_manifest_sha256": hashlib.sha256(
                (corpus / "source-manifest.json").read_bytes()
            ).hexdigest(),
            "cases": inference_cases,
        },
        {
            "artifact_kind": "EVALUATION_ONLY_DO_NOT_LOAD_FOR_INFERENCE",
            "version": "retrieval-fixtures-v0.1",
            "review_cases_sha256": hashlib.sha256(
                (corpus / "review-cases.json").read_bytes()
            ).hexdigest(),
            "cases": sidecar_cases,
        },
        {
            "artifact_kind": "PROPOSED_POLICY_CORPUS_PAIRING_NOT_RUNTIME_INPUT",
            "policy_kb_version": pairing["policy_kb_version"],
            "policy_bundle_version": pairing["policy_bundle_version"],
            "index_version": None,
            "source_membership": proposed,
            "uncovered_rule": "PROC-TOOL-STAGE-01",
            "status": "PENDING_INTEGRATION_REVIEW",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="compare bytes with committed fixtures"
    )
    args = parser.parse_args()
    for name, value in zip(
        ("inference-inputs.json", "evaluation-sidecar.json", "proposed-policy-pairing.json"),
        build(),
        strict=True,
    ):
        path = OUT / name
        data = canonical_json(value)
        if args.check:
            if path.read_bytes() != data:
                raise SystemExit(f"fixture drift: {name}")
        else:
            path.write_bytes(data)
        print(f"{name}: {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
