"""Check pinned review inputs and authored mapping structure, not schema acceptance."""

import argparse
import collections
import hashlib
import json
import pathlib
import re


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_dir", type=pathlib.Path)
    parser.add_argument("supplied_cases", type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    doc = pathlib.Path(__file__).resolve().parents[1]
    mapping = read(doc / "schema-v1.6-evidence-mapping.json")
    old = read(doc / "schema-v1.5-evidence-mapping.json")
    observations = read(doc / "schema-v1.6-review-observations.json")
    checks = []

    def check(condition, label):
        checks.append({"check": label, "status": "PASS" if condition else "FAIL"})

    for name, expected in observations["input_hashes"].items():
        path = args.review_dir / "inputs" / name
        check(path.is_file() and digest(path) == expected, "Pinned input: " + name)
    check(
        digest(doc / mapping["historical_mapping"]) == mapping["historical_mapping_sha256"],
        "Historical mapping unchanged",
    )
    spec_path = args.review_dir / "inputs" / mapping["source_file"]
    check(digest(spec_path) == mapping["source_sha256"], "Mapped specification hash")
    check(
        digest(args.review_dir / "inputs" / mapping["validator_filename"])
        == mapping["validator_sha256"],
        "Mapped validator hash",
    )
    fixtures = {}
    spec = spec_path.read_text()
    for block in re.findall(r"```json\n(.*?)\n```", spec, re.S):
        obj = json.loads(block)
        if (
            isinstance(obj, dict)
            and "events" in obj
            and str(obj.get("trace_id", "")).startswith("tr_")
        ):
            fixtures[f"WT{len(fixtures) + 1}"] = obj
    check(len(fixtures) == 4, "Four canonical walkthroughs extracted")
    pos_path = args.supplied_cases / "pos_13_valid_empty_retrieval_abstention.json"
    fixtures["POS-13"] = read(pos_path)
    pos_record = next(
        x for x in observations["supplied_suite"]["results"] if x["case_id"] == "POS-13"
    )
    check(digest(pos_path) == pos_record["fixture_sha256"], "Pinned generated POS-13 fixture")
    rows = mapping["rows"]
    check([x["id"] for x in rows] == [f"E{i:02}" for i in range(1, 28)], "Exactly E01–E27 in order")
    counts = dict(collections.Counter(x["status"] for x in rows))
    check(counts == mapping["status_counts"], "Status counts agree")
    source_lines = spec.splitlines()
    independent = {x["case"]: x for x in observations["independent_suite"]["results"]}
    supplied = {x["case_id"]: x for x in observations["supplied_suite"]["results"]}
    paths_checked = 0
    for row, prior in zip(rows, old["rows"], strict=True):
        key = row["id"]
        check(
            all(row[k] == prior[k] for k in ("id", "application_step", "minimum_evidence")),
            key + " original requirement preserved",
        )
        check(row["status"] in mapping["status_definitions"], key + " valid status")
        check(
            all(
                row.get(k)
                for k in (
                    "assessment",
                    "next_action_or_question",
                    "owners_and_reviewers",
                    "v1_6_representation",
                    "validation_evidence",
                    "representative_field_checks",
                )
            ),
            key + " complete evidence/action fields",
        )
        ref = row["source_reference"]
        check(
            ref["sha256"] == mapping["source_sha256"]
            and 1 <= ref["line_start"] <= ref["line_end"] <= len(source_lines),
            key + " source locator",
        )
        check(
            row["status"] != "CHANGE REQUIRED" or bool(row["finding_ids"]),
            key + " change has finding reference",
        )
        for entry in row["representative_field_checks"]:
            try:
                obj = fixtures[entry["walkthrough"]]
                if entry["event_id"] is not None:
                    matches = [e for e in obj["events"] if e["event_id"] == entry["event_id"]]
                    assert len(matches) == 1
                    obj = matches[0]
                for part in entry["path"].split("."):
                    obj = obj[int(part)] if isinstance(obj, list) else obj[part]
                found = True
            except (KeyError, IndexError, ValueError, AssertionError):
                found = False
            check(
                found,
                key
                + " path "
                + entry["walkthrough"]
                + "/"
                + str(entry["event_id"])
                + "/"
                + entry["path"],
            )
            paths_checked += 1
        for entry in row["validation_evidence"]:
            if entry["suite"] == "independent":
                source = independent[entry["case"]]
                check(
                    all(entry[k] == source[k] for k in ("expected", "observed", "codes")),
                    key + " independent case " + entry["case"],
                )
            elif entry["suite"] == "supplied":
                source = supplied[entry["case"]]
                check(
                    all(entry[k] == source[k] for k in ("expected_exit_code", "observed_exit_code"))
                    and entry["codes"] == source["observed_failure_codes"],
                    key + " supplied case " + entry["case"],
                )
        if row["status"] == "CHANGE REQUIRED":
            check(
                any(x.get("expectation_met") is False for x in row["validation_evidence"]),
                key + " reproduced unmet expectation",
            )
    check(
        mapping["full_schema_acceptance"] == "PENDING_CORRECTIONS_AND_JOINT_REVIEW"
        and not mapping["new_signoff"]
        and mapping["runtime_verification"] == "NOT_RUN",
        "No fabricated acceptance/runtime claim",
    )
    check(
        sum(x["expected"] != x["observed"] for x in independent.values()) == 16,
        "16 independent unmet expectations retained",
    )
    report = {
        "date": "2026-11-06",
        "result": "PASS" if all(x["status"] == "PASS" for x in checks) else "FAIL",
        "scope": "Static mapping integrity, pinned inputs, recorded evidence and representative path presence only; not semantic completeness or runtime acceptance",
        "mapping_sha256": digest(doc / "schema-v1.6-evidence-mapping.json"),
        "rows": len(rows),
        "status_counts": counts,
        "representative_paths_checked": paths_checked,
        "check_count": len(checks),
        "checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}))
    raise SystemExit(0 if report["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
