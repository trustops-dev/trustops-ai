"""Offline corpus/boundary review checks; not a retriever or runtime workflow validator."""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


def validate(root):
    r = root
    d = r / "docs/architecture/reference-applications"
    c = d / "corpus-review"
    b = d / "boundary-review"
    checks = []

    def check(ok, msg):
        if not ok:
            raise AssertionError(msg)
        checks.append({"check": msg, "status": "PASS"})

    def load(p):

        def unique(pairs):
            out = {}
            for k, v in pairs:
                if k in out:
                    raise ValueError("Duplicate member " + k)
                out[k] = v
            return out

        return json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=unique)

    m = load(c / "source-manifest.json")
    q = load(c / "review-cases.json")
    bc = load(b / "cases.json")
    obs = load(b / "denied-approval-observation.json")
    check(len(m["documents"]) == 8, "Eight authored sources")
    check(
        {x["domain"] for x in m["documents"]} == {"procurement", "hr", "ops", "faq"},
        "Four requested categories covered",
    )
    check(len({x["document_id"] for x in m["documents"]}) == 8, "Document IDs unique")
    check(len({x["source_id"] for x in m["documents"]}) == 8, "Source IDs unique")
    texts = {}
    records = {}
    for doc in m["documents"]:
        id = doc["document_id"]
        records[id] = doc
        p = c / doc["canonical_text_path"]
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        texts[id] = text
        check(hashlib.sha256(raw).hexdigest() == doc["content_hash"], id + ": exact UTF-8 hash")
        check(
            text == unicodedata.normalize("NFC", text) and "\r" not in text,
            id + ": NFC/LF canonical text",
        )
        check(
            doc["synthetic"] is True and doc["visibility"] == "mvp_shared",
            id + ": synthetic permitted review scope",
        )
        check(
            doc["source_version"] == "review-r1" and doc["token_counts"] is None,
            id + ": version explicit and no fabricated token count",
        )
        span = doc["locator"]["document_char_span"]
        check(span == {"start": 0, "end": len(text)}, id + ": exact Unicode span")
        check(doc["protected_units"] == [span], id + ": whole rule/exception unit retained")
        for phrase in doc["preserve_phrases"]:
            check(phrase in text, id + ": protected phrase exists: " + phrase)
        check(
            doc["effective_from"] is None and doc["effective_to"] is None,
            id + ": dates explicitly unassigned",
        )
        check(
            "review_only_relevant_documents" not in doc and "expected_outcome" not in doc,
            id + ": no review labels in source record",
        )
    check(
        m["pgvector_availability"] == "Unconfirmed — conditional on environment verification",
        "pgvector remains conditional",
    )
    snaps = {
        x["snapshot_id"]: {v["document_id"] for v in x["source_versions"]} for x in m["snapshots"]
    }
    for snap in m["snapshots"]:
        pairs = [(v["document_id"], v["source_version"]) for v in snap["source_versions"]]
        check(
            len(pairs) == len(set(x[0] for x in pairs)),
            snap["snapshot_id"] + ": one version per logical document",
        )
        check(
            all((i in records and records[i]["source_version"] == v for i, v in pairs)),
            snap["snapshot_id"] + ": manifest references resolve",
        )
    check(
        snaps["corpus-review-s02"] - snaps["corpus-review-s01"] == {"doc-007"},
        "Conflict variant changes only one document membership",
    )
    check(len(q["cases"]) == 8, "Eight review queries")
    for case in q["cases"]:
        id = case["query_id"]
        snap = snaps[case["snapshot_id"]]
        for key in [
            "authored_returned_documents",
            "authored_selected_documents",
            "review_only_relevant_documents",
            "review_only_irrelevant_documents",
            "review_only_conflicting_documents",
        ]:
            check(set(case[key]) <= snap, id + ": " + key + " resolve within snapshot")
        check(
            set(case["authored_selected_documents"]) <= set(case["authored_returned_documents"]),
            id + ": selected subset of authored returned set",
        )
        check(
            not set(case["review_only_relevant_documents"])
            & set(case["review_only_irrelevant_documents"]),
            id + ": relevance classes disjoint",
        )
        for phrase in case["required_support_phrases"]:
            check(
                any(phrase in texts[x] for x in case["authored_selected_documents"]),
                id + ": supporting phrase available",
            )
    conf = next(x for x in q["cases"] if x["query_id"] == "q-006")
    check(
        conf["expected_outcome"] == "CONFLICTING_EVIDENCE"
        and len(conf["review_only_conflicting_documents"]) == 2,
        "Conflict outcome cites two distinct sources",
    )
    check(
        "ten calendar days" in texts["doc-006"] and "fifteen calendar days" in texts["doc-007"],
        "Conflicting literal deadlines reproduced",
    )
    invalid = next(x for x in q["cases"] if x["query_id"] == "q-008")[
        "intentionally_invalid_selection"
    ]
    check(
        texts[invalid["document_id"]][invalid["start"] : invalid["end"]] == invalid["text"],
        "Rejected truncation remains an exact source slice",
    )
    check(
        "emergency" not in invalid["text"].lower() and "emergency" in texts["doc-003"].lower(),
        "Rejected slice demonstrably omits emergency exception",
    )
    check(
        {x["case_id"] for x in bc["cases"]} == {f"BC-{i:02}" for i in range(1, 11)},
        "Ten unique boundary cases",
    )
    check(all(x["runtime_executed"] is False for x in bc["cases"]), "No claimed runtime executions")
    for id in ["BC-07", "BC-08", "BC-09"]:
        case = next(x for x in bc["cases"] if x["case_id"] == id)
        check(
            "T" in case["precondition"] and (not re.search("\\d{2,}", case["precondition"])),
            id + ": symbolic threshold, no business value",
        )
    check(
        bc["symbolic_policy"]["comparator"] == ">",
        "Proposed comparison remains strict greater-than",
    )
    check(set(obs) == {"status", "data", "error"}, "Denial result uses existing tool envelope")
    check(
        obs["status"] == obs["data"]["decision_status"] == "DENIED",
        "Denial status agrees across envelope/data",
    )
    check(
        obs["data"]["approval_evidence"] is None and obs["error"] is None,
        "Denial carries no approval grant and is not technical ERROR",
    )
    check(
        all(
            isinstance(obs["data"][k], str) and obs["data"][k]
            for k in ["approval_request_id", "request_revision", "calculation_ref", "decision_ref"]
        ),
        "Denial identity/revision/calculation/decision references present",
    )
    md = (d / "manual-boundary-cases.md").read_text(encoding="utf-8")
    blocks = [json.loads(s) for s in re.findall("```json\\n(.*?)\\n```", md, re.S)]
    check(blocks[1] == obs, "Embedded denial observation equals standalone JSON")
    check(
        set(blocks[0]) == {"request_id", "justification", "approval_request_id"},
        "Observation proposal has exactly the existing three arguments",
    )
    check(
        blocks[0]["approval_request_id"] == obs["data"]["approval_request_id"],
        "Observation request/result identity matches",
    )
    check(
        "BLOCKED" in md and "No transition to APPROVED/PO_CREATION/COMPLETION" in md,
        "Denied outcome retains last state with explicit prohibited transitions",
    )
    paths = [
        d / n
        for n in [
            "rag-contract.md",
            "manual-boundary-cases.md",
            "week1-owner-closeout.md",
            "README.md",
            "acceptance.md",
            "handoffs.md",
            "open-decisions.md",
            "fixtures/README.md",
        ]
    ] + [c / "README.md"]
    for path in paths:
        for target in re.findall(
            "(?<!!)\\[[^\\]]+\\]\\(([^)]+)\\)", path.read_text(encoding="utf-8")
        ):
            target = target.split("#")[0]
            if target and (not re.match("^[a-z]+:", target)):
                check(
                    (path.parent / target).exists(), str(path.relative_to(r)) + ": link " + target
                )
    result = {
        "result": "PASS",
        "scope": "Static authored source hashes/spans, review labels/references, symbolic boundary cases, denial JSON and documentation links only",
        "checks": len(checks),
        "source_documents": 8,
        "snapshots": 2,
        "corpus_review_cases": 8,
        "boundary_cases": 10,
        "assertions": checks,
        "not_run": [
            "chunk token counts",
            "embedding API",
            "pgvector/FAISS",
            "runtime workflow",
            "canonical trace validator",
            "semantic evaluator",
            "shared acceptance",
        ],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repository",
        type=Path,
        help="Repository root, or a full copied snapshot with the same docs layout",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSON report path outside the inspected repository",
    )
    args = parser.parse_args()
    root = args.repository.resolve()
    output = args.output.resolve()
    if output.is_relative_to(root):
        parser.error(
            "--output must be outside the inspected repository to keep reviewed files unchanged"
        )
    try:
        if not (root / "docs/architecture/reference-applications").is_dir():
            raise ValueError("repository does not contain docs/architecture/reference-applications")
        report = validate(root)
        code = 0
    except Exception as exc:
        report = {
            "result": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "runtime": "NOT_RUN",
            "canonical_schema": "NOT_VALIDATED",
            "team_approvals": "PENDING",
        }
        code = 1
    report["execution_environment"] = {
        "python": sys.version.split()[0],
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Cannot write validation report: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                k: val
                for k, val in report.items()
                if k not in {"checks", "assertions"} or not isinstance(val, list)
            },
            indent=2,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
