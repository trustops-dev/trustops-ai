#!/usr/bin/env python3
"""Delivery-only static review. Does not execute apps or validate canonical schemas."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def digest(value):
    raw = (
        value
        if isinstance(value, str)
        else json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def validate(root, include_git_checks=False):
    folder = root / "docs/architecture/reference-applications"
    results = []

    def check(condition, label):
        results.append({"check": label, "status": "PASS" if condition else "FAIL"})
        if not condition:
            raise AssertionError(label)

    paths = sorted((folder / "fixtures").glob("*.json"))
    check(len(paths) == 4, "Exactly four authored walkthroughs")
    counts = {}
    for path in paths:
        d = json.loads(path.read_text(encoding="utf-8"))
        name = path.name
        events = d["events"]
        counts[name] = len(events)
        check(
            d["artifact_kind"] == "MANUAL_CONTRACT_WALKTHROUGH_NOT_CANONICAL_TRACE",
            name + ": manual artifact marking",
        )
        check(
            d["provenance"]["live_model_used"] is None
            and d["validation_scope"]["runtime"] == "NOT_RUN",
            name + ": no runtime claim",
        )
        seen = {}
        previous_time = None
        for n, event in enumerate(events, 1):
            label = name + ":" + event["event_id"]
            check(
                event["sequence_number"] == n and event["event_id"] not in seen,
                label + ": unique ordered ID",
            )
            check(
                event["parent_event_id"] in seen if n > 1 else event["parent_event_id"] is None,
                label + ": parent precedes child",
            )
            check(
                all(r in seen for r in event["depends_on"]), label + ": dependencies precede event"
            )
            now = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            check(
                previous_time is None or now > previous_time, label + ": synthetic timestamp order"
            )
            check(
                all(
                    re.fullmatch(r"E(0[1-9]|1[0-9]|2[0-7])", r)
                    for r in event["evidence_requirements"]
                ),
                label + ": recognized evidence IDs",
            )
            check(
                event["draft_mapping"]["status"] in {"OK", "CHANGE REQUIRED", "OPEN"},
                label + ": explicit draft fit",
            )
            previous_time = now
            seen[event["event_id"]] = event

        def rows(kind, events=events):
            return [e["paper_evidence"] for e in events if e["event_kind"] == kind]

        def evidence(ref, kind=None, seen=seen, name=name):
            e = seen[ref]
            if kind:
                check(e["event_kind"] == kind, name + ": referenced event type " + kind)
            return e["paper_evidence"]

        if d["application"] == "procurement-agent":
            request = rows("request_capture")[0]["normalized_request"]
            states = rows("state_transition")
            expected = [
                "REQUEST_CAPTURED",
                "POLICY_CHECKED",
                "SUPPLIER_CHECKED",
                "APPROVAL_CALCULATED",
                "APPROVAL_PENDING",
            ]
            if "success" in name:
                expected += ["APPROVED", "PO_CREATION", "COMPLETION"]
            check([s["to_state"] for s in states] == expected, name + ": complete state sequence")
            check(
                [s["from_state"] for s in states] == [None] + expected[:-1],
                name + ": contiguous state transitions",
            )
            proposals = rows("tool_proposal")
            tools = [
                "search_policy",
                "get_supplier",
                "calculate_approval_level",
                "request_approval",
                "create_purchase_order",
            ]
            check(
                [p["tool_name"] for p in proposals] == tools,
                name + ": five proposals in workflow order",
            )
            fields = [
                set(["query", "request_id", "top_k"]),
                set(["supplier_id", "request_id"]),
                set(["request_id", "total_amount", "currency"]),
                set(["request_id", "justification"]),
                set(
                    [
                        "request_id",
                        "supplier_id",
                        "item_description",
                        "quantity",
                        "total_amount",
                        "currency",
                    ]
                ),
            ]
            for proposal, allowed in zip(proposals, fields, strict=True):
                args = proposal["arguments"]
                check(
                    set(args) == allowed
                    and json.loads(proposal["raw_serialized_arguments"]) == args,
                    name + ": exact argument shape and serialization " + proposal["tool_name"],
                )
                check(
                    args["request_id"] == request["request_id"],
                    name + ": request binding " + proposal["tool_name"],
                )
                for key in sorted(args.keys() & request.keys()):
                    check(args[key] == request[key], name + ": normalized argument equality " + key)
                for key in ("top_k", "quantity"):
                    if key in args:
                        check(
                            type(args[key]) is int and args[key] > 0,
                            name + ": positive non-boolean " + key,
                        )
                if "total_amount" in args:
                    check(
                        isinstance(args["total_amount"], str)
                        and Decimal(args["total_amount"]).is_finite()
                        and Decimal(args["total_amount"]) > 0,
                        name + ": exact positive money",
                    )
            dispatches = rows("tool_dispatch")
            check(
                [c["tool_name"] for c in dispatches]
                == tools[: d["expected_final"]["po_dispatch_count"] + 4],
                name + ": dispatch sequence",
            )
            for call in dispatches:
                proposal = evidence(call["proposal_ref"], "tool_proposal")
                policy = evidence(call["check_ref"], "pre_tool_policy_check")
                check(
                    call["arguments"] == proposal["arguments"]
                    and call["tool_name"] == proposal["tool_name"],
                    name + ": dispatch matches proposal",
                )
                check(
                    policy["verdict"] == "ALLOW"
                    and policy["binding"]["proposal_id"] == proposal["proposal_id"]
                    and policy["binding"]["argument_sha256"] == digest(call["arguments"]),
                    name + ": bound pre-dispatch ALLOW",
                )
                check(call["live_execution_started"] is False, name + ": no live dispatch")
            observations = rows("tool_observation")
            check(
                len(observations) == len(dispatches)
                and len({o["call_ref"] for o in observations}) == len(dispatches),
                name + ": exactly one authored terminal observation per dispatch",
            )
            for observation in observations:
                call = evidence(observation["call_ref"], "tool_dispatch")
                check(call["tool_name"] == observation["tool_name"], name + ": result matches tool")
            final = rows("final_response")[0]
            if "success" in name:
                approval = rows("trusted_approval_observation")[0]
                for key in ("request_revision", "supplier_id", "currency"):
                    check(approval[key] == request[key], name + ": exact approval " + key)
                check(
                    approval["amount"] == request["total_amount"]
                    and approval["decision_status"] == "APPROVED"
                    and approval["model_can_write"] is False,
                    name + ": trusted approval amount/status",
                )
                calc = evidence(approval["calculation_ref"], "tool_observation")["outcome"]["data"]
                check(
                    approval["approval_level"] == calc["approval_level"]
                    and approval["policy_version"] == calc["policy_version"],
                    name + ": approval bound to calculation level/policy",
                )
                po = dispatches[-1]
                bound = evidence(po["check_ref"])["binding"]
                check(
                    evidence(bound["approval_ref"]) == approval
                    and bound["request_revision"] == request["request_revision"],
                    name + ": PO check binds exact approval",
                )
                check(
                    po["checked_state_revision"] == bound["state_revision"]
                    and po["dispatch_state_revision"] == bound["state_revision"] + 1
                    and po["argument_sha256"] == bound["argument_sha256"],
                    name + ": check-to-dispatch revision/digest",
                )
                check(
                    evidence(po["atomic_transition_ref"])["to_state"] == "PO_CREATION",
                    name + ": bound PO_CREATION transition",
                )
                claim = final["claimed_actions"][0]
                result = evidence(claim["supporting_result_ref"], "tool_observation")
                check(
                    result["call_ref"] == claim["supporting_call_ref"]
                    and result["outcome"]["status"] == "CREATED"
                    and result["outcome"]["data"]["po_id"] == claim["po_id"],
                    name + ": exact completion support",
                )
            else:
                suppression = rows("dispatch_suppression")[0]
                policy = evidence(suppression["check_ref"])
                check(
                    states[-1]["approval_required"] is True
                    and states[-1]["approval_received"] is False
                    and states[-1]["workflow_stage"] == "PRE_APPROVAL",
                    name + ": bypass preconditions",
                )
                check(
                    policy["verdict"] == "BLOCK"
                    and suppression["call_id"] is None
                    and suppression["tool_body_result"] is None
                    and suppression["execution_started"] is False,
                    name + ": BLOCK suppresses invocation",
                )
                check(
                    not rows("trusted_approval_observation")
                    and final["candidate_delivered"] is False
                    and final["raw_claimed_actions"][0]["supporting_result_ref"] is None,
                    name + ": unsupported candidate separated from delivered response",
                )
        else:
            retrieval = rows("retrieval_observation")[0]
            selection = rows("evidence_selection")[0]
            docs = {s["document_id"]: s for s in retrieval["documents"]}
            for source in docs.values():
                check(
                    digest(source["text"]) == source["content_hash"], name + ": exact source hash"
                )
            for selected in selection["selected_context"]:
                source = docs[selected["document_id"]]
                check(
                    source["text"][selected["start"] : selected["end"]] == selected["text"]
                    and selected["source_version"] == source["source_version"],
                    name + ": selected span/version",
                )
            if "grounded" in name:
                generation = rows("manual_generation")[0]
                binding = rows("citation_binding")[0]
                final = rows("final_response")[0]
                source = docs[binding["document_id"]]
                span = binding["source_span"]
                answer_span = binding["answer_span"]
                check(
                    binding["source_content_hash"] == source["content_hash"]
                    and binding["source_version"] == source["source_version"],
                    name + ": citation immutable source",
                )
                check(
                    source["text"][span["start"] : span["end"]] == binding["quoted_support"],
                    name + ": citation source span",
                )
                check(
                    generation["candidate_text"][answer_span["start"] : answer_span["end"]]
                    == binding["claim_text"],
                    name + ": citation answer span",
                )
                check(
                    binding["document_id"]
                    in {s["document_id"] for s in selection["selected_context"]}
                    and binding["visible_marker"] in final["delivered_text"],
                    name + ": selected citation and visible marker",
                )
                check(
                    source["text"] in generation["exact_context_text"]
                    and source["text"] in generation["rendered_prompt_or_messages"][1]["content"],
                    name + ": exact source in authored model context",
                )
                check(
                    selection["sufficiency"] == "SUFFICIENT_EVIDENCE"
                    and final["delivered_text"] == generation["candidate_text"],
                    name + ": grounded delivery path",
                )
            else:
                abstain = rows("final_abstention")[0]
                check(
                    selection["sufficiency"] == "INSUFFICIENT_EVIDENCE"
                    and not selection["selected_context"]
                    and selection["missing_facets"],
                    name + ": explicit insufficient evidence",
                )
                check(
                    not rows("manual_generation")
                    and abstain["generation_call_made"] is False
                    and not abstain["claims"]
                    and not abstain["citations"],
                    name + ": abstention without unsupported generation",
                )
                omitted = d["independent_review_annotation"]["known_in_corpus_document"][
                    "document_id"
                ]
                check(
                    omitted not in json.dumps(events),
                    name + ": omitted ground truth excluded from runtime ledger",
                )
        forbidden = {
            "primary_failure_expected",
            "root_cause_expected",
            "expected_relevant_document_ids",
            "injection_mechanism",
            "ground_truth",
        }

        def keys(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    yield k
                    yield from keys(v)
            elif isinstance(value, list):
                for v in value:
                    yield from keys(v)

        check(
            not forbidden.intersection(keys(events)),
            name + ": independent annotations outside event payload",
        )

    markdown = sorted(folder.rglob("*.md")) + [
        root / "docs/adr/reference-application-orchestration-and-llm.md"
    ]
    for path in markdown:
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            target = target.split("#")[0]
            if not target or re.match(r"^[a-z]+:", target):
                continue
            check(
                (path.parent / target).exists(),
                str(path.relative_to(root)) + ": local link " + target,
            )
    if include_git_checks:
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "--check"], capture_output=True, text=True
        )
        check(diff.returncode == 0, "git diff --check")
        staged = subprocess.run(
            ["git", "-C", str(root), "diff", "--cached", "--check"], capture_output=True, text=True
        )
        check(staged.returncode == 0, "git diff --cached --check")
        changed = subprocess.check_output(
            ["git", "-C", str(root), "diff", "--name-only"], text=True
        ).splitlines()
        changed += subprocess.check_output(
            ["git", "-C", str(root), "diff", "--cached", "--name-only"], text=True
        ).splitlines()
        changed += subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"], text=True
        ).splitlines()
        allowed_adrs = {
            "docs/adr/reference-application-orchestration-and-llm.md",
            "docs/adr/application-execution-budgets.md",
        }
        review_helpers = {
            "docs/architecture/reference-applications/prompt-pack/validate_prompt_pack.py",
            "docs/architecture/reference-applications/policy-candidate/od03-v0.1/verify_candidate.py",
            "docs/architecture/reference-applications/approval-validity/od04-v0.1/verify_review.py",
            "docs/architecture/reference-applications/validation/verify_manual_fixtures.py",
            "docs/architecture/reference-applications/validation/verify_corpus_boundaries.py",
            "docs/architecture/reference-applications/validation/verify_v16_mapping.py",
            "docs/architecture/reference-applications/workload-review/od-llm02-v0.1/calculate_workload.py",
            "docs/architecture/reference-applications/workload-review/od-llm02-v0.2/validate_workload.py",
            "docs/architecture/reference-applications/workload-review/od-llm02-v0.3/validate_candidate.py",
        }
        check(
            all(
                p in review_helpers
                or (
                    (p.startswith("docs/architecture/reference-applications/") or p in allowed_adrs)
                    and Path(p).suffix in {".md", ".json", ".txt"}
                )
                for p in changed
            ),
            "Working-tree changes confined to owner docs, paper/prompt examples and packaged offline review helpers",
        )
    return {
        "status": "PASS",
        "scope": "Static authored-artifact consistency only; not canonical schema or runtime validation",
        "canonical_schema": "BLOCKED",
        "runtime": "NOT_RUN",
        "team_approvals": "PENDING",
        "git_checks": "REQUESTED_AND_PASSED" if include_git_checks else "NOT_REQUESTED",
        "fixture_event_counts": counts,
        "check_count": len(results),
        "checks": results,
    }


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
    parser.add_argument(
        "--include-git-checks",
        action="store_true",
        help="Additionally inspect Git whitespace and owner-document change scope; requires a Git checkout",
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
        report = validate(root, args.include_git_checks)
        code = 0
    except Exception as exc:
        report = {
            "status": "FAIL",
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
