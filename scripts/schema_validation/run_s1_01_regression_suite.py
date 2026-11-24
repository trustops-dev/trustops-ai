#!/usr/bin/env python3
"""
Self-Contained 104-Case Regression Suite Runner for S1-01 (Draft v1.11)
Version: 1.11.0 (Package Release v1.12.0)
Default Target Specification: updated_schemas_v18.md
Default Validator: validate_s1_01_schema_v1_11.py

Executes 23 Positive Controls (BASE-00 + POS-11..32) and 81 Negative Probes (NEG-01..81)
and writes the byte-verified s1_01_validation_report.json.
"""

import argparse
import copy
import hashlib
import importlib
import json
import os
import pathlib
import re
import sys
import tempfile
from collections.abc import Callable
from typing import Any

_REPO_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "negative_and_variant_probes",
    ".tox",
    ".eggs",
}


def _find_repo_root(start: "pathlib.Path") -> "pathlib.Path":
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return start.resolve().parent if start.is_file() else start.resolve()


def _find_repo_file(
    filename: str,
    start: pathlib.Path,
    prefer_in: tuple[str, ...] = (),
    avoid_in: tuple[str, ...] = (),
) -> pathlib.Path:
    here = start.resolve().parent if start.is_file() else start.resolve()
    direct = here / filename
    if direct.is_file():
        return direct
    cwd_direct = pathlib.Path.cwd() / filename
    if cwd_direct.is_file():
        return cwd_direct
    repo_root = _find_repo_root(here)
    matches = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(
            d for d in dirs if d not in _REPO_SKIP_DIRS and not d.endswith(".egg-info")
        )
        if filename in files:
            matches.append(pathlib.Path(root) / filename)
    if not matches:
        raise FileNotFoundError(f"Could not locate {filename} from {here} or repo root {repo_root}")

    def _rank(p: pathlib.Path) -> tuple[int, int, int, str]:
        parts = set(p.parts)
        pref_score = 0 if (not prefer_in or any(x in parts for x in prefer_in)) else 1
        avoid_score = 1 if any(x in parts for x in avoid_in) else 0
        return (avoid_score, pref_score, len(p.parts), str(p))

    matches.sort(key=_rank)
    return matches[0]


val_mod: Any = None
for _val_mod_name in (
    "validate_s1_01_schema_v1_11",
    "trustops_sdk.validate_s1_01_schema_v1_11",
):
    try:
        val_mod = importlib.import_module(_val_mod_name)
        break
    except ImportError:
        continue

SUITE_VERSION = "1.11.0"
DEFAULT_SPEC = "updated_schemas_v18.md"
DEFAULT_VALIDATOR = "validate_s1_01_schema_v1_11.py"


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def extract_json_blocks(spec_text: str) -> list[tuple[tuple[int, int], dict[str, Any]]]:
    res = []
    for m in re.finditer(r"```json\n(.*?)\n```", spec_text, re.DOTALL):
        res.append(((m.start(1), m.end(1)), json.loads(m.group(1))))
    return res


def rebuild_spec_with_wt(spec_text: str, wt_index: int, mutated_wt: dict[str, Any]) -> str:
    matches = list(re.finditer(r"```json\n(.*?)\n```", spec_text, re.DOTALL))
    target_m = matches[8 + wt_index]
    new_json = json.dumps(mutated_wt, indent=2, ensure_ascii=False)
    return spec_text[: target_m.start(1)] + new_json + spec_text[target_m.end(1) :]


def find_event(wt: dict[str, Any], event_id: str) -> dict[str, Any]:
    for ev in wt["events"]:
        if isinstance(ev, dict) and ev["event_id"] == event_id:
            return ev
    raise KeyError(f"Event {event_id} not found")


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add_case(
        cid: str,
        kind: str,
        wt_idx: int,
        expected_codes: list[str],
        desc: str,
        mutator: Callable[[dict[str, Any]], None],
        approval_validation_profile: str = "provisional_draft",
    ) -> None:
        cases.append(
            {
                "case_id": cid,
                "kind": kind,
                "wt_idx": wt_idx,
                "expected_pass": len(expected_codes) == 0,
                "expected_codes": sorted(expected_codes),
                "description": desc,
                "approval_validation_profile": approval_validation_profile,
                "mutator": mutator,
            }
        )

    # BASE-00
    add_case(
        "BASE-00", "POSITIVE", 1, [], "Unmodified updated_schemas_v18.md baseline", lambda wt: None
    )

    # POS-11: Valid get_supplier ERROR stopping in POLICY_CHECKED
    def pos_11(wt: dict[str, Any]) -> None:
        e13 = find_event(wt, "e13")
        e13["attributes"]["execution_status"] = "ERROR"
        e13["attributes"]["result_payload"] = {
            "status": "ERROR",
            "data": None,
            "error": {
                "code": "SUPPLIER_DIRECTORY_UNAVAILABLE",
                "message": "Directory timeout",
                "retryable": False,
            },
        }
        e14 = find_event(wt, "e14")
        e14["attributes"]["to_app_state"] = "POLICY_CHECKED"
        e14["attributes"]["app_state"] = "POLICY_CHECKED"
        e14["attributes"]["policy_stage"] = "PRE_APPROVAL"
        e14["attributes"]["transition_accepted"] = False
        wt["events"] = wt["events"][:14]
        wt["last_app_state"] = "POLICY_CHECKED"
        wt["execution_status"] = "FAILED"
        if "post_run_analysis_example" in wt:
            wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = [
                "e12",
                "e13",
                "e14",
            ]
            wt["post_run_analysis_example"]["governance_enforcement_summary"][
                "enforcement_outcome"
            ] = "NOT_REACHED_STOPPED_BEFORE_PO_GATE"
            wt["post_run_analysis_example"]["governance_enforcement_summary"]["tool_dispatched"] = (
                False
            )
        ebt = wt["execution_budget_telemetry"]
        ebt["dispatch_claim_ledger"] = []
        c = ebt["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 2
        c["logical_tool_operations"]["spent_count"] = 2
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 2
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 2
        c["tool_attempt_debits"]["spent_count"] = 2
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 2
        )
        c["logical_generation_operations"]["slice_observed_spent_count"] = 0
        c["logical_generation_operations"]["spent_count"] = 0
        c["logical_generation_operations"]["remaining_count"] = c["logical_generation_operations"][
            "configured_ceiling"
        ]
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 0
        c["generation_attempt_debits"]["spent_count"] = 0
        c["generation_attempt_debits"]["remaining_count"] = c["generation_attempt_debits"][
            "configured_ceiling"
        ]
        wql = ebt["workload_quota_ledger"]
        wql["trace_requests_debited"] = 0
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-11",
        "POSITIVE",
        1,
        [],
        "Valid get_supplier status=ERROR stopping in POLICY_CHECKED",
        pos_11,
    )

    # POS-12: Valid calculate_approval_level UNRESOLVED stopping in SUPPLIER_CHECKED
    def pos_12(wt: dict[str, Any]) -> None:
        e19 = find_event(wt, "e19")
        e19["attributes"]["result_payload"] = {
            "status": "UNRESOLVED",
            "data": {
                "calculation_ref": "calc_9001_01",
                "request_revision": "rev_001",
                "policy_id": "POL-114",
                "policy_version": "kb_v3",
                "unresolved_reason": "UNSUPPORTED_CURRENCY_EUR",
                "basis": {"amount": "16000.00", "amount_currency": "EUR"},
            },
            "error": None,
        }
        e20 = find_event(wt, "e20")
        e20["attributes"]["to_app_state"] = "SUPPLIER_CHECKED"
        e20["attributes"]["app_state"] = "SUPPLIER_CHECKED"
        e20["attributes"]["policy_stage"] = "PRE_APPROVAL"
        e20["attributes"]["transition_accepted"] = False
        wt["events"] = wt["events"][:20]
        wt["last_app_state"] = "SUPPLIER_CHECKED"
        wt["execution_status"] = "STOPPED_BUSINESS_BLOCK"
        if "post_run_analysis_example" in wt:
            wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = [
                "e18",
                "e19",
                "e20",
            ]
            wt["post_run_analysis_example"]["governance_enforcement_summary"][
                "enforcement_outcome"
            ] = "NOT_REACHED_STOPPED_BEFORE_PO_GATE"
            wt["post_run_analysis_example"]["governance_enforcement_summary"]["tool_dispatched"] = (
                False
            )
        ebt = wt["execution_budget_telemetry"]
        ebt["dispatch_claim_ledger"] = []
        c = ebt["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 3
        c["logical_tool_operations"]["spent_count"] = 3
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 3
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 3
        c["tool_attempt_debits"]["spent_count"] = 3
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 3
        )
        c["logical_generation_operations"]["slice_observed_spent_count"] = 0
        c["logical_generation_operations"]["spent_count"] = 0
        c["logical_generation_operations"]["remaining_count"] = c["logical_generation_operations"][
            "configured_ceiling"
        ]
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 0
        c["generation_attempt_debits"]["spent_count"] = 0
        c["generation_attempt_debits"]["remaining_count"] = c["generation_attempt_debits"][
            "configured_ceiling"
        ]
        wql = ebt["workload_quota_ledger"]
        wql["trace_requests_debited"] = 0
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-12",
        "POSITIVE",
        1,
        [],
        "Valid calculate_approval_level UNRESOLVED stopping in SUPPLIER_CHECKED",
        pos_12,
    )

    # POS-13: Valid RAG zero-hit empty retrieval ending in ABSTENTION
    def pos_13(wt: dict[str, Any]) -> None:
        e1 = find_event(wt, "e1")
        e1["attributes"]["returned_count"] = 0
        e1["attributes"]["execution_status"] = "COMPLETED_ZERO_HITS"
        e1["attributes"]["retrieved_documents"] = []
        es = e1["attributes"]["evidence_sufficiency"]
        es["sufficiency_status"] = "INSUFFICIENT_NO_RELEVANT_EVIDENCE"
        es["selected_chunk_ids"] = []
        es["rejected_chunk_ids"] = []
        es["selected_document_count"] = 0
        e2 = find_event(wt, "e2")
        e2["attributes"]["selected_context_ref"]["selected_chunk_ids"] = []
        e2["attributes"]["selected_context_ref"]["rendered_context_block"] = ""
        e3 = find_event(wt, "e3")
        e3["attributes"]["response_mode"] = "ABSTENTION"
        e3["attributes"]["is_abstention"] = True
        e3["attributes"]["abstention_details"] = {
            "abstention_reason_code": "NO_RELEVANT_EVIDENCE",
            "abstention_explanation": "No relevant policy chunks retrieved.",
            "triggering_retrieval_id": "ret_210",
        }
        e3["attributes"]["visible_citations"] = []
        e3["attributes"]["claim_to_source_spans"] = []
        wt["last_rag_stage"] = "ABSTENTION"

    add_case(
        "POS-13",
        "POSITIVE",
        4,
        [],
        "Valid RAG zero-hit empty retrieval ending in ABSTENTION",
        pos_13,
    )

    # POS-14: Valid retry_accounting on WT1 model_call
    def pos_14(wt: dict[str, Any]) -> None:
        e29 = find_event(wt, "e29")
        e29["attributes"]["retry_accounting"] = {
            "attempt_number": 2,
            "max_attempts_configured": 2,
            "is_retry": True,
            "retry_eligibility_class": "TRANSIENT_READ_OR_GENERATION",
            "backoff_strategy": "EQUAL_JITTER",
            "backoff_delay_ms": 250,
            "prior_attempt_id": "att_mc_proc_101_01",
            "prior_attempt_error_code": "DEADLINE_EXCEEDED",
        }
        c = wt["execution_budget_telemetry"]["counters"]
        c["logical_generation_operations"]["slice_observed_spent_count"] = 1
        c["logical_generation_operations"]["spent_count"] = 1
        c["logical_generation_operations"]["remaining_count"] = (
            c["logical_generation_operations"]["configured_ceiling"] - 1
        )
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 3
        c["generation_attempt_debits"]["spent_count"] = 3
        c["generation_attempt_debits"]["remaining_count"] = (
            c["generation_attempt_debits"]["configured_ceiling"] - 3
        )
        wt["execution_budget_telemetry"]["workload_quota_ledger"]["trace_requests_debited"] = 3

    add_case(
        "POS-14",
        "POSITIVE",
        1,
        [],
        "Valid retry_accounting on WT1 model_call reconciled with budget",
        pos_14,
    )

    # POS-15: unknown_after_runtime_exception on WT3
    def pos_15(wt: dict[str, Any]) -> None:
        e7 = find_event(wt, "e7")
        e7["attributes"]["execution_status"] = "RUNTIME_EXCEPTION"
        e7["attributes"]["transport_diagnostics"]["code"] = "CONNECTION_RESET_AFTER_SEND"

    add_case(
        "POS-15",
        "POSITIVE",
        3,
        [],
        "unknown_after_runtime_exception: Dispatched PO with RUNTIME_EXCEPTION + UNKNOWN_OUTCOME + read-only recovery",
        pos_15,
    )

    # POS-16: valid_unresolved_recovery_fragment on WT3
    def pos_16(wt: dict[str, Any]) -> None:
        e8 = find_event(wt, "e8")
        e8["attributes"]["ledger_record_status"] = "NO_LEDGER_ENTRY_FOUND"
        e8["attributes"]["reconciliation_status"] = "STILL_UNRESOLVED"
        e8["attributes"]["resolved_side_effect_state"] = "UNKNOWN"
        e8["attributes"]["recovered_result_envelope"] = None
        e8["attributes"]["unresolved_reason_code"] = "UNRESOLVED_TIMEOUT"
        wt["events"] = wt["events"][:8]
        wt["last_app_state"] = "PO_CREATION"
        wt["execution_status"] = "RECOVERY_PENDING"

    add_case(
        "POS-16",
        "POSITIVE",
        3,
        [],
        "valid_unresolved_recovery_fragment: STILL_UNRESOLVED recovery retaining PO_CREATION and RECOVERY_PENDING",
        pos_16,
    )

    # POS-17: valid_observation_retry_accounted on WT1
    def pos_17(wt: dict[str, Any]) -> None:
        e13 = find_event(wt, "e13")
        e13["attributes"]["transport_diagnostics"] = {
            "code": "TRANSIENT_LOOKUP_RETRYABLE",
            "message": "Simulated prior retryable transport flag",
            "retryable": True,
        }
        e13["attributes"]["execution_status"] = "ERROR"
        e24 = find_event(wt, "e24")
        e24["attributes"]["trusted_runtime_context"]["budget_context"]["operation_mode"] = (
            "OBSERVE_APPROVAL"
        )
        e24["attributes"]["retry_accounting"] = {
            "attempt_number": 2,
            "max_attempts_configured": 2,
            "is_retry": True,
            "retry_eligibility_class": "TRANSIENT_READ_OR_GENERATION",
            "backoff_strategy": "EQUAL_JITTER",
            "backoff_delay_ms": 150,
            "prior_attempt_id": "att_reqapp_01_prior",
        }
        c = wt["execution_budget_telemetry"]["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 4
        c["logical_tool_operations"]["spent_count"] = 4
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 4
        )

    add_case(
        "POS-17",
        "POSITIVE",
        1,
        [],
        "valid_observation_retry_accounted: OBSERVE_APPROVAL retry with resolved prior attempt and reconciled debits",
        pos_17,
    )

    # POS-18: G01 Run 2 (results (1).json) PROVIDER_OR_SDK_ERROR with http_status=null and request_transport_evidence
    def pos_18(wt: dict[str, Any]) -> None:
        e2 = find_event(wt, "e2")
        e2["status"] = "ERROR"
        e2["attributes"]["execution_status"] = "PROVIDER_OR_SDK_ERROR"
        e2["attributes"]["output_text"] = None
        e2["attributes"]["token_usage"] = None
        e2["attributes"]["provider_fault_details"] = {
            "fault_stage": "SDK_ADAPTER_DESERIALIZATION",
            "provider": "gemini",
            "error_category": "SDK_CLIENT_EXCEPTION",
            "error_code": "SDK_CANDIDATE_STREAM_ABORTED_NO_HTTP_STATUS",
            "http_status": None,
            "grpc_status_code": None,
            "retryable": False,
            "outcome_certainty": "NO_CANDIDATE_RETURNED",
            "sanitized_diagnostic_summary": "Gemini SDK stream terminated before HTTP status header or candidate payload was received (G01 Run 2 results (1).json reproduction).",
            "request_transport_evidence": {
                "request_attempt_id": "att_mc_210_g01_run2",
                "sdk_method": "genai.Client.models.generate_content",
                "endpoint_host": "generativelanguage.googleapis.com",
                "transport_protocol": "HTTP_1_1_TLS",
                "configured_deadline_ms": 15000,
                "elapsed_ms_at_fault": 1840,
                "request_bytes_sent": 2148,
                "http_headers_received": False,
                "response_bytes_received": 0,
                "raw_exception_class": "httpx.RemoteProtocolError",
                "causal_chain_summary": "TLS peer closed connection after request write before sending HTTP status line; SDK raised client error with http_status=None.",
            },
        }
        wt["events"] = wt["events"][:2]
        wt["execution_status"] = "FAILED"
        wt["last_rag_stage"] = "CONTEXT_SELECTED"
        wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = ["e1", "e2"]
        wql = wt["execution_budget_telemetry"]["workload_quota_ledger"]
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-18",
        "POSITIVE",
        4,
        [],
        "valid_g01_run2_provider_or_sdk_error_no_http_status: G01 Run 2 PROVIDER_OR_SDK_ERROR with http_status=null & transport evidence",
        pos_18,
    )

    # POS-19: valid_e03_explicit_policy_ids_filter
    def pos_19(wt: dict[str, Any]) -> None:
        e2 = find_event(wt, "e2")
        e2["attributes"]["proposed_arguments"]["policy_ids"] = ["POL-114"]
        e2["attributes"]["raw_arguments_serialized"] = json.dumps(
            e2["attributes"]["proposed_arguments"]
        )
        e3 = find_event(wt, "e3")
        e3["attributes"]["normalized_arguments"]["policy_ids"] = ["POL-114"]
        new_dig = val_mod.compute_arguments_digest(e3["attributes"]["normalized_arguments"])
        e3["attributes"]["arguments_digest"] = new_dig
        e4 = find_event(wt, "e4")
        e4["attributes"]["authorization_snapshot"]["validated_arguments"]["policy_ids"] = [
            "POL-114"
        ]
        e4["attributes"]["authorization_snapshot"]["arguments_digest"] = new_dig
        e5 = find_event(wt, "e5")
        e5["attributes"]["arguments"]["policy_ids"] = ["POL-114"]
        e5["attributes"]["arguments_digest"] = new_dig
        e6 = find_event(wt, "e6")
        e6["attributes"]["filter_provenance"]["requested_model_filters"]["policy_ids"] = ["POL-114"]
        e6["attributes"]["filter_provenance"]["effective_trusted_filters"]["policy_ids"] = [
            "POL-114"
        ]

    add_case(
        "POS-19",
        "POSITIVE",
        1,
        [],
        "valid_e03_explicit_policy_ids_filter: search_policy with explicit policy_ids=['POL-114'] matched in filter_provenance",
        pos_19,
    )

    # POS-20 (New v1.10 Alaa/Nour Security Subset Control): valid_security_subset_benign_control
    def pos_20(wt: dict[str, Any]) -> None:
        sm = wt["scenario_metadata"]
        sm["is_security_subset"] = True
        sm["security_category"] = "BENIGN_SECURITY_LOOKALIKE"
        sm["security_case_role"] = "CONTROL"
        sm["security_subset_metadata"] = {
            "is_security_subset": True,
            "security_category": "BENIGN_SECURITY_LOOKALIKE",
            "security_case_role": "CONTROL",
            "attack_or_control_indicator": "BENIGN_LOOKALIKE_CONTROL",
        }

    add_case(
        "POS-20",
        "POSITIVE",
        1,
        [],
        "valid_security_subset_benign_control: Benign look-alike tagged is_security_subset=true & security_case_role='CONTROL'",
        pos_20,
    )

    # POS-21 (New v1.10 G01 Run 1 Control): valid_g01_run1_timeout_outcome_unknown_no_http_status
    def pos_21(wt: dict[str, Any]) -> None:
        e2 = find_event(wt, "e2")
        e2["status"] = "ERROR"
        e2["attributes"]["execution_status"] = "TIMEOUT_OUTCOME_UNKNOWN"
        e2["attributes"]["output_text"] = None
        e2["attributes"]["token_usage"] = None
        e2["attributes"]["provider_fault_details"] = {
            "fault_stage": "TRANSPORT_DISPATCH",
            "provider": "gemini",
            "error_category": "TIMEOUT",
            "error_code": "CLIENT_DEADLINE_EXCEEDED_NO_HTTP_STATUS",
            "http_status": None,
            "grpc_status_code": "DEADLINE_EXCEEDED",
            "retryable": True,
            "outcome_certainty": "OUTCOME_UNKNOWN_DEADLINE_EXCEEDED",
            "sanitized_diagnostic_summary": "Client read deadline expired before HTTP response headers were received from Gemini endpoint (G01 Run 1 results.json reproduction).",
            "request_transport_evidence": {
                "request_attempt_id": "att_mc_210_g01_run1",
                "sdk_method": "genai.Client.models.generate_content",
                "endpoint_host": "generativelanguage.googleapis.com",
                "transport_protocol": "HTTP_1_1_TLS",
                "configured_deadline_ms": 15000,
                "elapsed_ms_at_fault": 15004,
                "request_bytes_sent": 2148,
                "http_headers_received": False,
                "response_bytes_received": 0,
                "raw_exception_class": "httpx.ReadTimeout",
                "causal_chain_summary": "Request payload flushed over TLS socket; read timer expired at 15004ms with zero HTTP response bytes.",
            },
        }
        wt["events"] = wt["events"][:2]
        wt["execution_status"] = "TIMED_OUT"
        wt["last_rag_stage"] = "CONTEXT_SELECTED"
        wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = ["e1", "e2"]
        wql = wt["execution_budget_telemetry"]["workload_quota_ledger"]
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-21",
        "POSITIVE",
        4,
        [],
        "valid_g01_run1_timeout_outcome_unknown_no_http_status: G01 Run 1 TIMEOUT_OUTCOME_UNKNOWN with http_status=null & transport evidence",
        pos_21,
    )

    # NEG-01 .. NEG-53 (Retained from v1.9)
    add_case(
        "NEG-01",
        "NEGATIVE",
        1,
        ["ERR_ARG_DIGEST_MISMATCH"],
        "WT1 e3 arguments_digest replaced with all-zero SHA-256",
        lambda wt: find_event(wt, "e3")["attributes"].__setitem__(
            "arguments_digest", "sha256:" + "0" * 64
        ),
    )
    add_case(
        "NEG-02",
        "NEGATIVE",
        1,
        ["ERR_AUTH_CHECK_UNRESOLVED"],
        "WT1 e5 authorization_check_id set to chk_does_not_exist",
        lambda wt: find_event(wt, "e5")["attributes"].__setitem__(
            "authorization_check_id", "chk_does_not_exist"
        ),
    )

    def neg_03(wt: dict[str, Any]) -> None:
        e5 = find_event(wt, "e5")
        e5["sequence_number"] = 999
        e5["parent_event_id"] = "e_does_not_exist"

    add_case(
        "NEG-03",
        "NEGATIVE",
        1,
        ["ERR_EVENT_SEQ_ORDER", "ERR_EVENT_PARENT_UNRESOLVED"],
        "[COMPOUND] WT1 e5 sequence_number=999 and parent_event_id=e_does_not_exist",
        neg_03,
    )
    add_case(
        "NEG-04",
        "NEGATIVE",
        1,
        ["ERR_SNAPSHOT_MISSING"],
        "WT1 e4 authorization_snapshot removed from policy_check",
        lambda wt: find_event(wt, "e4")["attributes"].__setitem__("authorization_snapshot", None),
    )
    add_case(
        "NEG-05",
        "NEGATIVE",
        1,
        ["ERR_CITATION_SOURCE_UNRESOLVED"],
        "WT1 e38 citation chunk_id set to NONEXISTENT-CHUNK",
        lambda wt: find_event(wt, "e38")["attributes"]["visible_citations"][0].__setitem__(
            "cited_chunk_id", "NONEXISTENT-CHUNK"
        ),
    )
    add_case(
        "NEG-06",
        "NEGATIVE",
        1,
        ["ERR_PO_STATE_TRANSITION_INVALID", "ERR_PO_BINDING_FAILED"],
        "WT1 e33 bound_authorization_check_id mutated",
        lambda wt: find_event(wt, "e33")["attributes"].__setitem__(
            "bound_authorization_check_id", "chk_wrong"
        ),
    )
    add_case(
        "NEG-07",
        "NEGATIVE",
        1,
        ["ERR_UNKNOWN_FIELD_REJECTED"],
        "Injects trace-only business_status into WT1 e7 result_payload",
        lambda wt: find_event(wt, "e7")["attributes"]["result_payload"].__setitem__(
            "business_status", "MATCHED"
        ),
    )
    add_case(
        "NEG-08",
        "NEGATIVE",
        4,
        ["ERR_GROUND_TRUTH_LEAK"],
        "Injects unretrieved POL-119 into WT4 sufficiency_rationale",
        lambda wt: find_event(wt, "e1")["attributes"]["evidence_sufficiency"].__setitem__(
            "sufficiency_rationale", "Missing expected document POL-119."
        ),
    )
    add_case(
        "NEG-09",
        "NEGATIVE",
        1,
        ["ERR_SNAPSHOT_REQUEST_MISMATCH"],
        "Mutates WT1 e32 snapshot request_revision to rev_000_stale",
        lambda wt: find_event(wt, "e32")["attributes"]["authorization_snapshot"].__setitem__(
            "request_revision", "rev_000_stale"
        ),
    )
    add_case(
        "NEG-10",
        "NEGATIVE",
        1,
        ["ERR_SNAPSHOT_SUPPLIER_EVIDENCE_MISMATCH", "ERR_PO_BINDING_FAILED"],
        "Actual get_supplier result e13 changed to NOT_APPROVED while snapshot claims APPROVED",
        lambda wt: find_event(wt, "e13")["attributes"]["result_payload"]["data"][
            "supplier"
        ].__setitem__("status", "NOT_APPROVED"),
    )
    add_case(
        "NEG-11",
        "NEGATIVE",
        1,
        ["ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH", "ERR_PO_BINDING_FAILED"],
        "Actual approval event e27 changed to DENIED while snapshot claims APPROVED",
        lambda wt: find_event(wt, "e27")["attributes"].__setitem__("approval_status", "DENIED"),
    )

    def neg_12(wt: dict[str, Any]) -> None:
        wt["request"]["structured_input"]["total_amount"] = "1.00"
        for lk in wt["request"]["normalization_provenance"]["raw_to_normalized_field_links"]:
            if lk["field_name"] == "total_amount":
                lk["normalized_value"] = "1.00"

    add_case(
        "NEG-12",
        "NEGATIVE",
        1,
        ["ERR_REQUEST_TOOL_ARG_MISMATCH"],
        "Root request.structured_input.total_amount changed to 1.00 while PO remains 16000.00",
        neg_12,
    )

    def neg_13(wt: dict[str, Any]) -> None:
        for p in find_event(wt, "e32")["attributes"]["evaluated_policies"]:
            p["policy_id"] = "PROC-APPROVAL-01"

    add_case(
        "NEG-13",
        "NEGATIVE",
        1,
        ["ERR_POLICY_IDS_NOT_DISTINCT"],
        "All three evaluated policy IDs in WT1 e32 collapsed to PROC-APPROVAL-01",
        neg_13,
    )
    add_case(
        "NEG-14",
        "NEGATIVE",
        1,
        ["ERR_DISPATCH_CLAIM_MISMATCH", "ERR_PO_BINDING_FAILED"],
        "WT1 e32 snapshot dispatch_claim.dispatch_claim_id changed to dclaim_tampered",
        lambda wt: find_event(wt, "e32")["attributes"]["authorization_snapshot"][
            "dispatch_claim"
        ].__setitem__("dispatch_claim_id", "dclaim_tampered"),
    )
    add_case(
        "NEG-15",
        "NEGATIVE",
        3,
        ["ERR_TIMEOUT_SIDE_EFFECT_NOT_UNKNOWN", "ERR_TIMEOUT_CLAIMS_NO_EFFECT"],
        "WT3 timeout tool_result e7 sets side_effect_state=NONE under UNKNOWN_OUTCOME",
        lambda wt: find_event(wt, "e7")["attributes"].__setitem__("side_effect_state", "NONE"),
    )

    def neg_16(wt: dict[str, Any]) -> None:
        e8 = find_event(wt, "e8")
        e8["attributes"]["queried_idempotency_key"] = "idem_wrong"
        e8["attributes"]["recovered_result_envelope"]["data"]["total_amount"] = "9999.00"

    add_case(
        "NEG-16",
        "NEGATIVE",
        3,
        ["ERR_RECOVERY_KEY_MISMATCH", "ERR_PO_RESULT_REQUEST_MISMATCH"],
        "[COMPOUND] WT3 recovery_check e8 changes queried_idempotency_key and total_amount",
        neg_16,
    )

    def neg_17(wt: dict[str, Any]) -> None:
        dup = copy.deepcopy(find_event(wt, "e13"))
        dup["event_id"] = "e39"
        dup["sequence_number"] = 39
        dup["parent_event_id"] = "e38"
        dup["attributes"]["result_id"] = "res_sup_dup"
        wt["events"].append(dup)

    add_case(
        "NEG-17",
        "NEGATIVE",
        1,
        ["ERR_DUPLICATE_TERMINAL_TOOL_RESULT"],
        "Appends a second terminal tool_result for call_id=call_sup_01 in WT1",
        neg_17,
    )
    add_case(
        "NEG-18",
        "NEGATIVE",
        1,
        ["ERR_BUDGET_COUNTER_INVALID"],
        "Corrupts WT1 execution_budget_telemetry.counters.logical_tool_operations.spent_count to 99",
        lambda wt: wt["execution_budget_telemetry"]["counters"][
            "logical_tool_operations"
        ].__setitem__("spent_count", 99),
    )
    add_case(
        "NEG-19",
        "NEGATIVE",
        1,
        ["ERR_BUDGET_FENCING_MISMATCH"],
        "Mutates WT1 e34 budget_context.fencing_token to 99 while trace fencing_token is 1",
        lambda wt: find_event(wt, "e34")["attributes"]["trusted_runtime_context"][
            "budget_context"
        ].__setitem__("fencing_token", 99),
    )
    add_case(
        "NEG-20",
        "NEGATIVE",
        1,
        ["ERR_CITATION_VERSION_MISMATCH"],
        "Mutates WT1 e38 visible_citations[0].cited_doc_version to v999_wrong",
        lambda wt: find_event(wt, "e38")["attributes"]["visible_citations"][0].__setitem__(
            "cited_doc_version", "v999_wrong"
        ),
    )

    def neg_21(wt: dict[str, Any]) -> None:
        doc = find_event(wt, "e6")["attributes"]["retrieved_documents"][0]
        short_text = doc["content_snippet"][:20]
        doc["canonical_chunk_slice"] = short_text
        doc["canonical_chunk_char_span"] = {"start": 0, "end": 20}
        doc["exact_selected_text"] = short_text
        for mc_id in ("e29", "e37"):
            mc = find_event(wt, mc_id)
            mc["attributes"]["selected_context_ref"]["rendered_context_block"] = short_text
            mc["attributes"]["rendered_prompt_or_messages"][0]["content"] = (
                f"Context:\n{short_text}"
            )

    add_case(
        "NEG-21",
        "NEGATIVE",
        1,
        ["ERR_CITATION_OUTSIDE_SELECTED_SLICE"],
        "Truncates WT1 e6 canonical_chunk_slice so cited source_quote lies outside selected slice",
        neg_21,
    )

    def neg_22(wt: dict[str, Any]) -> None:
        find_event(wt, "e30")["attributes"]["raw_arguments_serialized"] = "{bad_json"
        dup_call = copy.deepcopy(find_event(wt, "e34"))
        dup_call["event_id"] = "e39"
        dup_call["sequence_number"] = 39
        dup_call["parent_event_id"] = "e38"
        dup_call["attributes"]["call_id"] = "call_po_dup"
        wt["events"].append(dup_call)
        c = wt["execution_budget_telemetry"]["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 6
        c["logical_tool_operations"]["spent_count"] = 6
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 6
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 6
        c["tool_attempt_debits"]["spent_count"] = 6
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 6
        )

    add_case(
        "NEG-22",
        "NEGATIVE",
        1,
        ["ERR_RAW_ARGS_PARSE_MISMATCH", "ERR_AUTH_CHECK_REUSED", "ERR_PO_DUPLICATE_DISPATCH_CLAIM"],
        "[COMPOUND] Corrupts e30 raw_arguments_serialized and appends duplicate PO tool_call",
        neg_22,
    )
    add_case(
        "NEG-23",
        "NEGATIVE",
        3,
        ["ERR_RECOVERY_KEY_MISMATCH"],
        "Isolated recovery_check.queried_idempotency_key mismatch in WT3 e8",
        lambda wt: find_event(wt, "e8")["attributes"].__setitem__(
            "queried_idempotency_key", "idem_wrong_only"
        ),
    )
    add_case(
        "NEG-24",
        "NEGATIVE",
        3,
        ["ERR_PO_RESULT_REQUEST_MISMATCH"],
        "Isolated recovery_check.recovered_result_envelope.data.total_amount mismatch in WT3 e8",
        lambda wt: find_event(wt, "e8")["attributes"]["recovered_result_envelope"][
            "data"
        ].__setitem__("total_amount", "9999.00"),
    )
    add_case(
        "NEG-25",
        "NEGATIVE",
        1,
        ["ERR_RAW_ARGS_PARSE_MISMATCH"],
        "Isolated malformed raw_arguments_serialized on WT1 e30",
        lambda wt: find_event(wt, "e30")["attributes"].__setitem__(
            "raw_arguments_serialized", "{bad_json"
        ),
    )

    def neg_26(wt: dict[str, Any]) -> None:
        dup_call = copy.deepcopy(find_event(wt, "e34"))
        dup_call["event_id"] = "e39"
        dup_call["sequence_number"] = 39
        dup_call["parent_event_id"] = "e38"
        dup_call["attributes"]["call_id"] = "call_po_01"
        wt["events"].append(dup_call)
        c = wt["execution_budget_telemetry"]["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 6
        c["logical_tool_operations"]["spent_count"] = 6
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 6
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 6
        c["tool_attempt_debits"]["spent_count"] = 6
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 6
        )

    add_case(
        "NEG-26",
        "NEGATIVE",
        1,
        ["ERR_AUTH_CHECK_REUSED", "ERR_PO_DUPLICATE_DISPATCH_CLAIM"],
        "Isolated duplicate create_purchase_order tool_call reusing chk_101 and dclaim_req_9001",
        neg_26,
    )
    add_case(
        "NEG-27",
        "NEGATIVE",
        1,
        ["ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH", "ERR_PO_BINDING_FAILED"],
        "approval_event_id in WT1 e32 points to nonexistent event e999_missing",
        lambda wt: find_event(wt, "e32")["attributes"]["authorization_snapshot"][
            "approval_evidence_ref"
        ].__setitem__("approval_event_id", "e999_missing"),
    )
    add_case(
        "NEG-28",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_EVIDENCE_MISMATCH", "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH"],
        "Approval submission result e25 contains different approval_request_id",
        lambda wt: find_event(wt, "e25")["attributes"]["result_payload"]["data"].__setitem__(
            "approval_request_id", "areq_different_999"
        ),
    )
    add_case(
        "NEG-29",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_EVIDENCE_MISMATCH", "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH"],
        "Embedded ApprovalEvidence.approval_level in WT1 e25 disagrees with approval event",
        lambda wt: find_event(wt, "e25")["attributes"]["result_payload"]["data"][
            "approval_evidence"
        ].__setitem__("approval_level", "DIRECTOR_L2"),
    )
    add_case(
        "NEG-30",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_EVIDENCE_MISMATCH", "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH"],
        "Embedded ApprovalEvidence.source_ref in WT1 e25 identifies a different approval decision",
        lambda wt: find_event(wt, "e25")["attributes"]["result_payload"]["data"][
            "approval_evidence"
        ].__setitem__("source_ref", "mock_approval_registry://decisions/APR-999"),
    )
    add_case(
        "NEG-31",
        "NEGATIVE",
        1,
        ["ERR_SNAPSHOT_POLICY_VERSION"],
        "An evaluated policy in WT1 e32 has a different policy_version",
        lambda wt: find_event(wt, "e32")["attributes"]["evaluated_policies"][0].__setitem__(
            "policy_version", "kb_v999_mismatch"
        ),
    )
    add_case(
        "NEG-32",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_CEILING_EXCEEDED", "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH"],
        "approved_amount_ceiling in WT1 e27 is 1.00 while bound_amount is 16000.00",
        lambda wt: find_event(wt, "e27")["attributes"].__setitem__(
            "approved_amount_ceiling", "1.00"
        ),
    )
    add_case(
        "NEG-33",
        "NEGATIVE",
        1,
        [
            "ERR_APPROVAL_CHRONOLOGY_INVALID",
            "ERR_APPROVAL_EVIDENCE_MISMATCH",
            "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH",
        ],
        "approval_timestamp in WT1 e27 is 2099-01-01T00:00:00.000Z",
        lambda wt: find_event(wt, "e27")["attributes"].__setitem__(
            "approval_timestamp", "2099-01-01T00:00:00.000Z"
        ),
    )

    def neg_34(wt: dict[str, Any]) -> None:
        e7 = find_event(wt, "e7")
        e7["attributes"]["execution_status"] = "TIMEOUT"
        e7["attributes"]["side_effect_state"] = "NONE"
        e7["attributes"]["result_payload"] = {
            "status": "ERROR",
            "data": None,
            "error": {"code": "TIMEOUT", "message": "Timed out", "retryable": False},
        }

    add_case(
        "NEG-34",
        "NEGATIVE",
        3,
        ["ERR_TIMEOUT_CLAIMS_NO_EFFECT", "ERR_TIMEOUT_SIDE_EFFECT_NOT_UNKNOWN"],
        "timeout_error_claims_no_effect: Dispatched PO timeout claims status=ERROR and side_effect_state=NONE",
        neg_34,
    )

    def neg_35(wt: dict[str, Any]) -> None:
        e8 = find_event(wt, "e8")
        e8["attributes"]["ledger_record_status"] = "NO_LEDGER_ENTRY_FOUND"
        e8["attributes"]["reconciliation_status"] = "STILL_UNRESOLVED"
        e8["attributes"]["resolved_side_effect_state"] = "UNKNOWN"
        e8["attributes"]["recovered_result_envelope"] = None
        e8["attributes"]["unresolved_reason_code"] = "UNRESOLVED_TIMEOUT"

    add_case(
        "NEG-35",
        "NEGATIVE",
        3,
        ["ERR_UNRESOLVED_RECOVERY_COMPLETION"],
        "unresolved_recovery_still_completed: recovery_check is STILL_UNRESOLVED but trace transitions to COMPLETION",
        neg_35,
    )
    add_case(
        "NEG-36",
        "NEGATIVE",
        3,
        ["ERR_UNKNOWN_RESULT_CLAIM_MISMATCH"],
        "unknown_result_wrong_claim: WT3 e7 UNKNOWN_OUTCOME references dclaim_wrong_999",
        lambda wt: find_event(wt, "e7")["attributes"]["result_payload"]["data"].__setitem__(
            "dispatch_claim_id", "dclaim_wrong_999"
        ),
    )
    add_case(
        "NEG-37",
        "NEGATIVE",
        3,
        ["ERR_UNKNOWN_RESULT_PROPOSAL_MISMATCH"],
        "unknown_result_wrong_proposal: WT3 e7 UNKNOWN_OUTCOME references prop_wrong_999",
        lambda wt: find_event(wt, "e7")["attributes"]["result_payload"]["data"].__setitem__(
            "proposal_id", "prop_wrong_999"
        ),
    )

    def neg_38(wt: dict[str, Any]) -> None:
        e24 = find_event(wt, "e24")
        e24["attributes"]["retry_accounting"] = {
            "attempt_number": 2,
            "max_attempts_configured": 2,
            "is_retry": True,
            "retry_eligibility_class": "TRANSIENT_READ_OR_GENERATION",
            "backoff_strategy": "EQUAL_JITTER",
            "backoff_delay_ms": 100,
            "prior_attempt_id": "att_missing_999",
        }

    add_case(
        "NEG-38",
        "NEGATIVE",
        1,
        [
            "ERR_WRITE_RETRY_FORBIDDEN",
            "ERR_RETRY_PRIOR_ATTEMPT_UNRESOLVED",
            "ERR_BUDGET_COUNTER_INVALID",
        ],
        "approval_submission_retry_unaccounted: CREATE_APPROVAL_REQUEST labeled as retry without prior attempt or debit",
        neg_38,
    )
    add_case(
        "NEG-39",
        "NEGATIVE",
        4,
        ["ERR_GROUND_TRUTH_LEAK"],
        "injected_root_cause_in_runtime: Copies scenario_metadata.injected_root_cause ('retriever') into WT4 runtime rationale",
        lambda wt: find_event(wt, "e1")["attributes"]["evidence_sufficiency"].__setitem__(
            "sufficiency_rationale", "Root cause is retriever failure."
        ),
    )
    add_case(
        "NEG-40",
        "NEGATIVE",
        1,
        ["ERR_UNKNOWN_FIELD_REJECTED"],
        "approval_unknown_field: Adds undeclared attribute to WT1 e27 (approval)",
        lambda wt: find_event(wt, "e27")["attributes"].__setitem__(
            "extra_undeclared_field", "unexpected"
        ),
    )
    add_case(
        "NEG-41",
        "NEGATIVE",
        1,
        ["ERR_TIMESTAMP"],
        "invalid_event_timestamps: Replaces event timestamp in WT1 e1 with not-a-time",
        lambda wt: find_event(wt, "e1").__setitem__("timestamp", "not-a-time"),
    )

    def neg_42(wt: dict[str, Any]) -> None:
        find_event(wt, "e33")["attributes"]["bound_authorization_check_id"] = "chk_pol_01"
        find_event(wt, "e33")["attributes"]["dispatch_claim_consumption"][
            "bound_authorization_check_id"
        ] = "chk_pol_01"
        wt["execution_budget_telemetry"]["dispatch_claim_ledger"][0][
            "bound_authorization_check_id"
        ] = "chk_pol_01"

    add_case(
        "NEG-42",
        "NEGATIVE",
        1,
        ["ERR_PO_STATE_TRANSITION_INVALID", "ERR_PO_BINDING_FAILED"],
        "read_allow_used_for_po_transition: Binds APPROVED -> PO_CREATION transition e33 to read-only chk_pol_01",
        neg_42,
    )
    add_case(
        "NEG-43",
        "NEGATIVE",
        1,
        ["ERR_EVENT_SEQ_ORDER"],
        "Isolated sequence_number out-of-order (999) on WT1 e5",
        lambda wt: find_event(wt, "e5").__setitem__("sequence_number", 999),
    )
    add_case(
        "NEG-44",
        "NEGATIVE",
        1,
        ["ERR_EVENT_PARENT_UNRESOLVED"],
        "Isolated unresolved parent_event_id on WT1 e5",
        lambda wt: find_event(wt, "e5").__setitem__("parent_event_id", "e_does_not_exist"),
    )
    add_case(
        "NEG-45",
        "NEGATIVE",
        1,
        ["ERR_MODEL_CALL_EVIDENCE_INCOMPLETE"],
        "E02 Negative Probe: WT1 e29 model_call effective_config_ref or generation_parameters missing/mismatched",
        lambda wt: find_event(wt, "e29")["attributes"].__setitem__(
            "effective_config_ref", "cfg_wrong_mismatch"
        ),
    )
    add_case(
        "NEG-46",
        "NEGATIVE",
        4,
        ["ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID"],
        "E03/E04 Negative Probe: WT4 e1 retrieval EXPLICIT_NO_FILTER_ALL_ELIGIBLE has non-empty metadata_predicates",
        lambda wt: find_event(wt, "e1")["attributes"]["filter_provenance"][
            "effective_trusted_filters"
        ].__setitem__("metadata_predicates", {"undeclared_filter": "secret"}),
    )
    add_case(
        "NEG-47",
        "NEGATIVE",
        4,
        ["ERR_RETRIEVAL_RANK_OR_TIE_BREAK_INVALID"],
        "E06 Negative Probe: WT4 e1 retrieved_documents rank/score ordering inverted against tie_break_rule",
        lambda wt: find_event(wt, "e1")["attributes"]["retrieved_documents"][0].__setitem__(
            "score", 0.10
        ),
    )
    add_case(
        "NEG-48",
        "NEGATIVE",
        4,
        ["ERR_EVIDENCE_SELECTOR_MISMATCH"],
        "E07 Negative Probe: WT4 e1 evidence_sufficiency.selected_chunk_ids does not match included_in_prompt chunks",
        lambda wt: find_event(wt, "e1")["attributes"]["evidence_sufficiency"].__setitem__(
            "selected_chunk_ids", ["NONEXISTENT-CHUNK"]
        ),
    )
    add_case(
        "NEG-49",
        "NEGATIVE",
        1,
        ["ERR_REQUEST_NORMALIZATION_MISMATCH"],
        "E08 Negative Probe: WT1 request.normalization_provenance raw_char_span does not match raw_substring",
        lambda wt: wt["request"]["normalization_provenance"]["raw_to_normalized_field_links"][
            0
        ].__setitem__("raw_char_span", {"start": 0, "end": 3}),
    )

    def neg_50(wt: dict[str, Any]) -> None:
        snap = find_event(wt, "e32")["attributes"]["authorization_snapshot"]
        snap["supplier_evidence_ref"]["latest_observed_supplier_record_version"] = (
            "sup_rec_88_v3_newer"
        )
        snap["supplier_evidence_ref"]["is_current_at_check"] = False
        snap["dispatch_claim"]["currentness_verified"] = False

    add_case(
        "NEG-50",
        "NEGATIVE",
        1,
        ["ERR_STALE_RECORD_VERSION_AT_CLAIM"],
        "E14/E17 & Mohamed #1 Negative Probe: Stale supplier/approval record version at dispatch claim",
        neg_50,
    )

    def neg_51(wt: dict[str, Any]) -> None:
        find_event(wt, "e33")["attributes"]["dispatch_claim_consumption"] = None

    add_case(
        "NEG-51",
        "NEGATIVE",
        1,
        ["ERR_CLAIM_CONSUMPTION_RECORD_INVALID"],
        "E17 & Mohamed #2 Negative Probe: Missing immutable dispatch_claim_consumption record on PO_CREATION transition",
        neg_51,
    )

    def neg_52(wt: dict[str, Any]) -> None:
        snap = find_event(wt, "e32")["attributes"]["authorization_snapshot"]
        snap["approval_evidence_ref"]["latest_observed_decision_record_seq"] = 105

    add_case(
        "NEG-52",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_SUPERSEDED_SEQUENCE"],
        "E14 & Mohamed #3 Negative Probe: Approval decision_record_seq (104) superseded by newer sequence (105)",
        neg_52,
    )

    def neg_53(wt: dict[str, Any]) -> None:
        e29 = find_event(wt, "e29")
        e29["attributes"]["execution_status"] = "PROVIDER_OR_SDK_ERROR"
        e29["attributes"]["provider_fault_details"] = None

    add_case(
        "NEG-53",
        "NEGATIVE",
        1,
        ["ERR_PROVIDER_FAULT_INVALID"],
        "E25/G01 Negative Probe: model_call has execution_status=PROVIDER_OR_SDK_ERROR but provider_fault_details=null",
        neg_53,
    )

    # NEW v1.10 NEGATIVE PROBES (NEG-54 .. NEG-56)
    def neg_54(wt: dict[str, Any]) -> None:
        # Flat vs nested security_case_role mismatch or invalid security tag
        wt["scenario_metadata"]["is_security_subset"] = True
        wt["scenario_metadata"]["security_category"] = "DIRECT_USER_PROMPT_INJECTION"
        wt["scenario_metadata"]["security_case_role"] = "ATTACK"
        # Leave security_subset_metadata unsynchronized
        wt["scenario_metadata"]["security_subset_metadata"]["is_security_subset"] = False

    add_case(
        "NEG-54",
        "NEGATIVE",
        1,
        ["ERR_SECURITY_METADATA_INVALID"],
        "Alaa #3 / Nour OD-13 #2 Negative Probe: Flat scenario_metadata.security_case_role disagrees with security_subset_metadata",
        neg_54,
    )

    def neg_55(wt: dict[str, Any]) -> None:
        # Alaa #4 / Nour Section 8 item 3 & 5 Closure Test Case:
        # Citing a retrieved chunk (HR-002#chunk-01, rank 3 in WT4 e1) that was excluded from the actual prompt (included_in_prompt=false)
        e3 = find_event(wt, "e3")
        e3["attributes"]["visible_citations"][0]["cited_doc_id"] = "HR-002"
        e3["attributes"]["visible_citations"][0]["cited_doc_version"] = "v1.0"
        e3["attributes"]["visible_citations"][0]["cited_chunk_id"] = "HR-002#chunk-01"
        ses = e3["attributes"]["claim_to_source_spans"][0]["source_evidence_spans"][0]
        ses["doc_id"] = "HR-002"
        ses["chunk_id"] = "HR-002#chunk-01"
        ses["source_quote"] = (
            "Annual PTO carryover is limited to 5 business days per calendar year."
        )

    add_case(
        "NEG-55",
        "NEGATIVE",
        4,
        ["ERR_CITATION_CONTEXT_FLAG_MISMATCH", "ERR_CITATION_OUTSIDE_SELECTED_SLICE"],
        "Alaa #4 / Nour Section 8 Closure Probe: Citation references retrieved chunk HR-002#chunk-01 excluded from prompt",
        neg_55,
    )

    def neg_56(wt: dict[str, Any]) -> None:
        # Alaa #1/#2/#5 Negative Probe: terminal policy_stage typo COMPLETION instead of COMPLETED,
        # corrupted adjudication_record, and unreconciled OD-LLM-02 workload_quota_ledger
        find_event(wt, "e36")["attributes"]["policy_stage"] = "COMPLETION"
        wt["post_run_analysis_example"]["adjudication_record"][
            "adjudicated_primary_failure_class"
        ] = "INVALID_CLASS"
        wt["execution_budget_telemetry"]["workload_quota_ledger"]["trace_total_tokens_debited"] = (
            999999
        )

    add_case(
        "NEG-56",
        "NEGATIVE",
        1,
        [
            "ERR_STATE_STAGE_MAPPING_INVALID",
            "ERR_ADJUDICATION_RECORD_INVALID",
            "ERR_WORKLOAD_QUOTA_LEDGER_INVALID",
        ],
        "Alaa #1/#2/#5 Probe: Terminal policy_stage typo COMPLETION, invalid adjudication_record, and OD-LLM-02 token mismatch",
        neg_56,
    )

    # POS-22 (Email 1 V19-06 Positive Control): valid_model_refusal_abstention
    def pos_22(wt: dict[str, Any]) -> None:
        e29 = find_event(wt, "e29")
        e29["attributes"]["execution_status"] = "REFUSED"
        e29["attributes"]["refusal_reason"] = (
            "Safety policy refusal: ambiguous high-value purchase instructions."
        )
        e29["attributes"]["output_text"] = None
        e29["attributes"]["proposed_tool_calls"] = None
        e38 = copy.deepcopy(find_event(wt, "e38"))
        e38["event_id"] = "e30"
        e38["sequence_number"] = 30
        e38["parent_event_id"] = "e29"
        e38["attributes"]["generating_model_call_id"] = "mc_proc_101_01"
        e38["attributes"]["response_mode"] = "REFUSAL_OR_BLOCK_NOTICE"
        e38["attributes"]["is_abstention"] = True
        e38["attributes"]["abstention_details"] = {
            "abstention_reason_code": "MODEL_REFUSAL_SAFETY_POLICY",
            "abstention_explanation": "Model refused tool selection; execution halted safely without dispatching PO.",
            "triggering_retrieval_id": "ret_proc_101",
        }
        e38["attributes"]["visible_citations"] = []
        e38["attributes"]["claim_to_source_spans"] = []
        e38["attributes"]["claimed_actions"] = []
        wt["events"] = wt["events"][:29] + [e38]
        wt["last_app_state"] = "APPROVED"
        wt["execution_status"] = "ABSTAINED"
        wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = [
            "e28",
            "e29",
            "e30",
        ]
        wt["post_run_analysis_example"]["governance_enforcement_summary"] = {
            "enforcement_outcome": "NOT_REACHED_STOPPED_BEFORE_PO_GATE",
            "pre_tool_action_verdict": None,
            "tool_dispatched": False,
            "observed_side_effect_state": "NONE",
            "recovery_reconciliation_status": None,
            "terminal_app_state": "APPROVED",
            "terminal_policy_stage": "APPROVED",
            "derived_by_module": "governance.post_run_enforcement_evaluator_v1",
            "blocking_check_id": None,
            "consuming_call_id": None,
            "evidence_refs": ["e29", "e30"],
        }
        ebt = wt["execution_budget_telemetry"]
        ebt["dispatch_claim_ledger"] = []
        c = ebt["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 4
        c["logical_tool_operations"]["spent_count"] = 4
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 4
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 4
        c["tool_attempt_debits"]["spent_count"] = 4
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 4
        )
        c["logical_generation_operations"]["slice_observed_spent_count"] = 1
        c["logical_generation_operations"]["spent_count"] = 1
        c["logical_generation_operations"]["remaining_count"] = (
            c["logical_generation_operations"]["configured_ceiling"] - 1
        )
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 1
        c["generation_attempt_debits"]["spent_count"] = 1
        c["generation_attempt_debits"]["remaining_count"] = (
            c["generation_attempt_debits"]["configured_ceiling"] - 1
        )
        wql = ebt["workload_quota_ledger"]
        tu = e29["attributes"]["token_usage"]
        wql["trace_requests_debited"] = 1
        wql["trace_prompt_tokens_debited"] = tu["prompt_tokens"]
        wql["trace_completion_tokens_debited"] = tu["completion_tokens"]
        wql["trace_total_tokens_debited"] = tu["total_tokens"]

    add_case(
        "POS-22",
        "POSITIVE",
        1,
        [],
        "valid_model_refusal_abstention: REFUSED model_call with refusal_reason, null proposed_tool_calls, and no downstream PO dispatch",
        pos_22,
    )

    # POS-23 (Email 2 SA-03 Positive Control): valid_approved_then_cancelled_revocation_blocks_po
    def pos_23(wt: dict[str, Any]) -> None:
        e27 = find_event(wt, "e27")
        e27["attributes"]["approval_status"] = "CANCELLED"
        e27["attributes"]["supersedes_approval_id"] = "APR-43"
        e27["attributes"]["superseded_by_approval_id"] = None
        e25_data = find_event(wt, "e25")["attributes"]["result_payload"]["data"]
        e25_data["decision_status"] = "CANCELLED"
        e28 = find_event(wt, "e28")
        e28["attributes"]["to_app_state"] = "APPROVAL_PENDING"
        e28["attributes"]["app_state"] = "APPROVAL_PENDING"
        e28["attributes"]["policy_stage"] = "PRE_APPROVAL"
        e28["attributes"]["transition_accepted"] = False
        wt["events"] = wt["events"][:28]
        wt["last_app_state"] = "APPROVAL_PENDING"
        wt["execution_status"] = "STOPPED_APPROVAL_DENIED"
        wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = [
            "e25",
            "e27",
            "e28",
        ]
        wt["post_run_analysis_example"]["governance_enforcement_summary"] = {
            "enforcement_outcome": "NOT_REACHED_STOPPED_BEFORE_PO_GATE",
            "pre_tool_action_verdict": None,
            "tool_dispatched": False,
            "observed_side_effect_state": "NONE",
            "recovery_reconciliation_status": None,
            "terminal_app_state": "APPROVAL_PENDING",
            "terminal_policy_stage": "PRE_APPROVAL",
            "derived_by_module": "governance.post_run_enforcement_evaluator_v1",
            "blocking_check_id": None,
            "consuming_call_id": None,
            "evidence_refs": ["e27", "e28"],
        }
        ebt = wt["execution_budget_telemetry"]
        ebt["dispatch_claim_ledger"] = []
        c = ebt["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 4
        c["logical_tool_operations"]["spent_count"] = 4
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 4
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 4
        c["tool_attempt_debits"]["spent_count"] = 4
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 4
        )
        c["logical_generation_operations"]["slice_observed_spent_count"] = 0
        c["logical_generation_operations"]["spent_count"] = 0
        c["logical_generation_operations"]["remaining_count"] = c["logical_generation_operations"][
            "configured_ceiling"
        ]
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 0
        c["generation_attempt_debits"]["spent_count"] = 0
        c["generation_attempt_debits"]["remaining_count"] = c["generation_attempt_debits"][
            "configured_ceiling"
        ]
        wql = ebt["workload_quota_ledger"]
        wql["trace_requests_debited"] = 0
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-23",
        "POSITIVE",
        1,
        [],
        "valid_approved_then_cancelled_revocation_blocks_po: Revoked/CANCELLED approval superseding APR-43 halts safely",
        pos_23,
    )

    # POS-24 (Email 2 SA-04 Positive Control): valid_pre_existing_approval_before_trace_start
    def pos_24(wt: dict[str, Any]) -> None:
        pre_ts = "2026-10-18T08:55:00.000Z"
        find_event(wt, "e27")["attributes"]["approval_timestamp"] = pre_ts
        find_event(wt, "e25")["attributes"]["result_payload"]["data"]["approval_evidence"][
            "decision_timestamp"
        ] = pre_ts

    add_case(
        "POS-24",
        "POSITIVE",
        1,
        [],
        "valid_pre_existing_approval_before_trace_start: Existing approval timestamp precedes trace.started_at while <= verified_at <= e27.timestamp",
        pos_24,
    )

    # POS-25 (Email 2 SA-07 Positive Control): valid_stub_contract_test_check_mode
    def pos_25(wt: dict[str, Any]) -> None:
        wt["environment"] = "test"
        for ev in wt["events"]:
            if ev["event_type"] == "policy_check":
                ev["attributes"]["check_mode"] = "STUB_CONTRACT_TEST"

    add_case(
        "POS-25",
        "POSITIVE",
        1,
        [],
        "valid_stub_contract_test_check_mode: Isolated Week 2-3 contract test trace in environment='test' with check_mode='STUB_CONTRACT_TEST'",
        pos_25,
    )

    # POS-26 (Blocker 2 & OD-03 Genuine Stage-Only Zero-Hit NO_MATCH Fixture): valid_od03_stage_only_proc_tool_stage_01_zero_hit_no_match
    def pos_26(wt: dict[str, Any]) -> None:
        wt["scenario_metadata"]["expected_relevant_doc_ids"] = []
        wt["scenario_metadata"]["qrels_relevant_doc_ids"] = []
        e2 = find_event(wt, "e2")
        e2["attributes"]["proposed_arguments"]["policy_ids"] = ["PROC-TOOL-STAGE-01"]
        e2["attributes"]["raw_arguments_serialized"] = json.dumps(
            e2["attributes"]["proposed_arguments"]
        )
        e3 = find_event(wt, "e3")
        e3["attributes"]["normalized_arguments"]["policy_ids"] = ["PROC-TOOL-STAGE-01"]
        stage_dig = val_mod.compute_arguments_digest(e3["attributes"]["normalized_arguments"])
        e3["attributes"]["arguments_digest"] = stage_dig
        e4 = find_event(wt, "e4")
        e4["attributes"]["authorization_snapshot"]["validated_arguments"]["policy_ids"] = [
            "PROC-TOOL-STAGE-01"
        ]
        e4["attributes"]["authorization_snapshot"]["arguments_digest"] = stage_dig
        e5 = find_event(wt, "e5")
        e5["attributes"]["arguments"]["policy_ids"] = ["PROC-TOOL-STAGE-01"]
        e5["attributes"]["arguments_digest"] = stage_dig
        e6 = find_event(wt, "e6")
        e6["attributes"]["returned_count"] = 0
        e6["attributes"]["retrieved_documents"] = []
        e6["attributes"]["execution_status"] = "COMPLETED_ZERO_HITS"
        e6["attributes"]["retrieval_fault_details"] = None
        e6["attributes"]["filter_provenance"]["filter_resolution_status"] = (
            "EXPLICIT_FILTERS_APPLIED"
        )
        e6["attributes"]["filter_provenance"]["requested_model_filters"]["policy_ids"] = [
            "PROC-TOOL-STAGE-01"
        ]
        e6["attributes"]["filter_provenance"]["effective_trusted_filters"]["policy_ids"] = [
            "PROC-TOOL-STAGE-01"
        ]
        e6["attributes"]["evidence_sufficiency"].update(
            sufficiency_status="NO_RELEVANT_EVIDENCE",
            selected_chunk_ids=[],
            rejected_chunk_ids=[],
            selected_document_count=0,
        )
        e7 = find_event(wt, "e7")
        e7["attributes"]["result_payload"] = {
            "status": "NO_MATCH",
            "data": {
                "query": e5["attributes"]["arguments"]["query"],
                "requested_top_k": 3,
                "returned_count": 0,
                "matches": [],
                "policy_set_version": "kb_v3",
                "retriever_version": "retriever_v2",
                "applicability": "MISSING",
            },
            "error": None,
        }
        e8 = find_event(wt, "e8")
        e8["attributes"]["from_app_state"] = "REQUEST_CAPTURED"
        e8["attributes"]["to_app_state"] = "REQUEST_CAPTURED"
        e8["attributes"]["app_state"] = "REQUEST_CAPTURED"
        e8["attributes"]["policy_stage"] = "PRE_APPROVAL"
        e8["attributes"]["transition_accepted"] = False
        wt["events"] = wt["events"][:8]
        wt["last_app_state"] = "REQUEST_CAPTURED"
        wt["execution_status"] = "STOPPED_BUSINESS_BLOCK"
        wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = ["e6", "e7", "e8"]
        wt["post_run_analysis_example"]["governance_enforcement_summary"] = {
            "enforcement_outcome": "NOT_REACHED_STOPPED_BEFORE_PO_GATE",
            "pre_tool_action_verdict": None,
            "tool_dispatched": False,
            "observed_side_effect_state": "NONE",
            "recovery_reconciliation_status": None,
            "terminal_app_state": "REQUEST_CAPTURED",
            "terminal_policy_stage": "PRE_APPROVAL",
            "derived_by_module": "governance.post_run_enforcement_evaluator_v1",
            "blocking_check_id": None,
            "consuming_call_id": None,
            "evidence_refs": ["e6", "e7", "e8"],
        }
        ebt = wt["execution_budget_telemetry"]
        ebt["dispatch_claim_ledger"] = []
        c = ebt["counters"]
        c["logical_tool_operations"]["slice_observed_spent_count"] = 1
        c["logical_tool_operations"]["spent_count"] = 1
        c["logical_tool_operations"]["remaining_count"] = (
            c["logical_tool_operations"]["configured_ceiling"] - 1
        )
        c["tool_attempt_debits"]["slice_observed_spent_count"] = 1
        c["tool_attempt_debits"]["spent_count"] = 1
        c["tool_attempt_debits"]["remaining_count"] = (
            c["tool_attempt_debits"]["configured_ceiling"] - 1
        )
        c["logical_generation_operations"]["slice_observed_spent_count"] = 0
        c["logical_generation_operations"]["spent_count"] = 0
        c["logical_generation_operations"]["remaining_count"] = c["logical_generation_operations"][
            "configured_ceiling"
        ]
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 0
        c["generation_attempt_debits"]["spent_count"] = 0
        c["generation_attempt_debits"]["remaining_count"] = c["generation_attempt_debits"][
            "configured_ceiling"
        ]
        wql = ebt["workload_quota_ledger"]
        wql["trace_requests_debited"] = 0
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-26",
        "POSITIVE",
        1,
        [],
        "valid_od03_stage_only_proc_tool_stage_01_zero_hit_no_match: Stage-only PROC-TOOL-STAGE-01 search_policy returns status='NO_MATCH', matches=[], applicability='MISSING' with 0-hit retrieval",
        pos_26,
    )

    # POS-27 (Email 6 Ahmed Retrieval Fault Positive Control): valid_retrieval_timeout_and_provider_fault_halt
    def pos_27(wt: dict[str, Any]) -> None:
        e1 = find_event(wt, "e1")
        e1["status"] = "ERROR"
        e1["attributes"]["returned_count"] = 0
        e1["attributes"]["retrieved_documents"] = []
        e1["attributes"]["execution_status"] = "RETRIEVAL_TIMEOUT"
        e1["attributes"]["retrieval_fault_details"] = {
            "fault_stage": "INDEX_OR_SQL_DISPATCH",
            "provider_or_engine": "pgvector_sql",
            "error_category": "TIMEOUT",
            "error_code": "PGVECTOR_QUERY_DEADLINE_EXCEEDED",
            "retryable": True,
            "outcome_certainty": "NO_RESULTS_RETURNED_TIMEOUT",
            "sanitized_diagnostic_summary": "PostgreSQL/pgvector similarity query exceeded 5000ms statement_timeout before returning candidate rows.",
        }
        es = e1["attributes"]["evidence_sufficiency"]
        es["sufficiency_status"] = "UNAVAILABLE_DUE_TO_RETRIEVAL_FAULT"
        es["selected_chunk_ids"] = []
        es["rejected_chunk_ids"] = []
        es["selected_document_count"] = 0
        wt["events"] = wt["events"][:1]
        wt["execution_status"] = "TIMED_OUT"
        wt["last_rag_stage"] = "ERROR"
        wt["post_run_analysis_example"]["reliability_decision"]["decision"] = "INCOMPLETE"
        wt["post_run_analysis_example"]["reliability_decision"]["evaluation_status"] = (
            "INCOMPLETE_TRACE_EVIDENCE"
        )
        wt["post_run_analysis_example"]["adjudication_record"]["adjudication_status"] = (
            "INCONCLUSIVE_TECHNICAL_ERROR"
        )
        wt["post_run_analysis_example"]["adjudication_record"]["evidence_refs"] = ["e1"]
        wt["post_run_analysis_example"]["governance_enforcement_summary"]["evidence_refs"] = ["e1"]
        ebt = wt["execution_budget_telemetry"]
        c = ebt["counters"]
        c["logical_generation_operations"]["slice_observed_spent_count"] = 0
        c["logical_generation_operations"]["spent_count"] = 0
        c["logical_generation_operations"]["remaining_count"] = c["logical_generation_operations"][
            "configured_ceiling"
        ]
        c["generation_attempt_debits"]["slice_observed_spent_count"] = 0
        c["generation_attempt_debits"]["spent_count"] = 0
        c["generation_attempt_debits"]["remaining_count"] = c["generation_attempt_debits"][
            "configured_ceiling"
        ]
        wql = ebt["workload_quota_ledger"]
        wql["trace_requests_debited"] = 1
        wql["trace_prompt_tokens_debited"] = 0
        wql["trace_completion_tokens_debited"] = 0
        wql["trace_total_tokens_debited"] = 0

    add_case(
        "POS-27",
        "POSITIVE",
        4,
        [],
        "valid_retrieval_timeout_and_provider_fault_halt: Retrieval timeout records retrieval_fault_details, UNAVAILABLE_DUE_TO_RETRIEVAL_FAULT, and INCOMPLETE gate decision",
        pos_27,
    )

    # NEW NEGATIVE PROBES FOR EMAILS 1-7 (NEG-57 .. NEG-70)
    def neg_57(wt: dict[str, Any]) -> None:
        find_event(wt, "e33")["attributes"]["dispatch_claim_consumption"][
            "preallocated_at_proposal_id"
        ] = "NONEXISTENT"
        wt["execution_budget_telemetry"]["dispatch_claim_ledger"][0][
            "preallocated_at_proposal_id"
        ] = "NONEXISTENT"

    add_case(
        "NEG-57",
        "NEGATIVE",
        1,
        ["ERR_CLAIM_CONSUMPTION_PROPOSAL_MISMATCH"],
        "Email 1 V19-02a Probe: WT1 e33 dispatch_claim_consumption.preallocated_at_proposal_id set to NONEXISTENT",
        neg_57,
    )

    def neg_58(wt: dict[str, Any]) -> None:
        find_event(wt, "e33")["attributes"]["dispatch_claim_consumption"][
            "preallocated_at_proposal_id"
        ] = "prop_pol_01"
        wt["execution_budget_telemetry"]["dispatch_claim_ledger"][0][
            "preallocated_at_proposal_id"
        ] = "prop_pol_01"

    add_case(
        "NEG-58",
        "NEGATIVE",
        1,
        ["ERR_CLAIM_CONSUMPTION_PROPOSAL_MISMATCH"],
        "Email 1 V19-02b Probe: WT1 e33 dispatch_claim_consumption.preallocated_at_proposal_id points to wrong existing proposal prop_pol_01",
        neg_58,
    )

    def neg_59(wt: dict[str, Any]) -> None:
        lk = wt["request"]["normalization_provenance"]["raw_to_normalized_field_links"][0]
        lk.update(
            derivation_mode="INVALID_UNDECLARED_MODE",
            raw_char_span={"start": 0, "end": 3},
            raw_substring="fabricated",
        )

    add_case(
        "NEG-59",
        "NEGATIVE",
        1,
        ["ERR_NORMALIZATION_MODE_INVALID", "ERR_REQUEST_NORMALIZATION_MISMATCH"],
        "Email 1 V19-03 Probe: Undeclared derivation_mode=INVALID_UNDECLARED_MODE attempts to bypass span verification",
        neg_59,
    )

    def neg_60(wt: dict[str, Any]) -> None:
        find_event(wt, "e1")["attributes"]["retrieved_documents"][0]["score"] = float("inf")

    add_case(
        "NEG-60",
        "NEGATIVE",
        4,
        ["ERR_RETRIEVAL_SCORE_NONFINITE"],
        "Email 1 V19-04 Probe: Non-finite retrieval score (1e309 / Infinity) in WT4 e1",
        neg_60,
    )

    def neg_61(wt: dict[str, Any]) -> None:
        find_event(wt, "e29")["attributes"]["generation_parameters"].update(
            top_p=-1, max_output_tokens=-10
        )

    add_case(
        "NEG-61",
        "NEGATIVE",
        1,
        ["ERR_GENERATION_PARAMETERS_INVALID"],
        "Email 1 V19-05a Probe: Invalid generation_parameters (top_p=-1, max_output_tokens=-10) on completed model_call",
        neg_61,
    )

    def neg_62(wt: dict[str, Any]) -> None:
        find_event(wt, "e29")["attributes"]["operation_profile_id"] = "rag_grounded_answer_v1"

    add_case(
        "NEG-62",
        "NEGATIVE",
        1,
        ["ERR_GENERATION_PARAMETERS_INVALID"],
        "Email 1 V19-05b Probe: Mismatched operation_profile_id (rag_grounded_answer_v1) on procurement tool_selection step",
        neg_62,
    )

    def neg_63(wt: dict[str, Any]) -> None:
        find_event(wt, "e29")["attributes"]["execution_status"] = "REFUSED"

    add_case(
        "NEG-63",
        "NEGATIVE",
        1,
        ["ERR_MODEL_REFUSAL_INCONSISTENT"],
        "Email 1 V19-06 Probe: Model call e29 marked REFUSED while leaving refusal_reason=null and downstream tool_proposal e30 active",
        neg_63,
    )

    def neg_64(wt: dict[str, Any]) -> None:
        find_event(wt, "e31")["attributes"]["normalized_arguments"]["invalid_float_arg"] = 16000.50

    add_case(
        "NEG-64",
        "NEGATIVE",
        1,
        ["ERR_CANONICAL_JSON_DOMAIN_VIOLATION"],
        "Email 1 OD-13 Domain Probe: Injects float value into normalized_arguments digested by trustops-canonical-json-v1",
        neg_64,
    )

    def neg_65(wt: dict[str, Any]) -> None:
        dcc = find_event(wt, "e33")["attributes"]["dispatch_claim_consumption"]
        dcc["observed_approval_record_version_at_consumption"] = "apr_rec_44_v2_stale_race"
        dcc["observed_decision_record_seq_at_consumption"] = 105
        dcc["currentness_verified_at_consumption"] = False
        wt["execution_budget_telemetry"]["dispatch_claim_ledger"][0] = copy.deepcopy(dcc)

    add_case(
        "NEG-65",
        "NEGATIVE",
        1,
        ["ERR_STALE_RECORD_VERSION_AT_CONSUMPTION"],
        "Email 2 SA-02 Probe: Approval record version/sequence changes between policy_check and dispatch_claim_consumption",
        neg_65,
    )

    def neg_66(wt: dict[str, Any]) -> None:
        # Insert an earlier CANCELLED approval event on the same approval_request_id before e27 APPROVED
        find_event(wt, "e27")["attributes"]["approval_status"] = "CANCELLED"
        find_event(wt, "e32")["attributes"]["authorization_snapshot"]["approval_evidence_ref"][
            "decision_status"
        ] = "CANCELLED"

    add_case(
        "NEG-66",
        "NEGATIVE",
        1,
        ["ERR_PO_BINDING_FAILED"],
        "Email 2 SA-03 Probe: Terminal CANCELLED approval cannot authorize create_purchase_order",
        neg_66,
    )

    def neg_67(wt: dict[str, Any]) -> None:
        find_event(wt, "e27")["attributes"]["approval_status"] = "EXPIRED"
        find_event(wt, "e32")["attributes"]["evaluated_policies"][0]["criticality"] = (
            "CRITICAL_UPPERCASE_MISMATCH"
        )

    add_case(
        "NEG-67",
        "NEGATIVE",
        1,
        ["ERR_POLICY_CRITICALITY_INVALID", "ERR_PO_BINDING_FAILED"],
        "Email 2 SA-05 & SA-06 Probe: EXPIRED approval status and non-canonical criticality spelling rejected",
        neg_67,
    )

    def neg_68(wt: dict[str, Any]) -> None:
        wt["environment"] = "prod"
        find_event(wt, "e32")["attributes"]["check_mode"] = "STUB_CONTRACT_TEST"

    add_case(
        "NEG-68",
        "NEGATIVE",
        1,
        ["ERR_POLICY_CHECK_MODE_INVALID"],
        "Email 2 SA-07 Probe: STUB_CONTRACT_TEST check_mode rejected in prod environment",
        neg_68,
    )

    def neg_69(wt: dict[str, Any]) -> None:
        doc = find_event(wt, "e6")["attributes"]["retrieved_documents"][0]
        doc["doc_id"] = "doc-001"
        doc["doc_version"] = "review-r1"

    add_case(
        "NEG-69",
        "NEGATIVE",
        1,
        ["ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID"],
        "Email 4 OD-03 Probe: Superseded symbolic revision doc-001@review-r1 in pinned KB release rejected",
        neg_69,
    )

    def neg_70(wt: dict[str, Any]) -> None:
        e1 = find_event(wt, "e1")
        e1["attributes"]["execution_status"] = "VECTOR_STORE_OR_SQL_ERROR"
        e1["attributes"]["retrieval_fault_details"] = {
            "fault_stage": "INDEX_OR_SQL_DISPATCH",
            "provider_or_engine": "pgvector_sql",
            "error_category": "VECTOR_STORE_OR_SQL_ERROR",
            "error_code": "PGVECTOR_EXTENSION_UNAVAILABLE",
            "retryable": False,
            "outcome_certainty": "NO_RESULTS_RETURNED_ENGINE_FAULT",
            "sanitized_diagnostic_summary": "Database connection or pgvector operator failure.",
        }
        # Leave sufficiency_status as normal and corrupt governance_enforcement_summary
        wt["post_run_analysis_example"]["governance_enforcement_summary"]["enforcement_outcome"] = (
            "AUTHORIZED_AND_COMMITTED"
        )

    add_case(
        "NEG-70",
        "NEGATIVE",
        4,
        ["ERR_RETRIEVAL_FAULT_MISLABELED_AS_ABSTENTION", "ERR_ENFORCEMENT_OUTCOME_MISMATCH"],
        "Email 6 Ahmed Retrieval Fault & SA-09 Probe: Technical retrieval fault mislabeled as normal sufficiency and mismatched enforcement_outcome",
        neg_70,
    )

    # POS-28 (Integration Gap 3 Positive Control): valid_four_level_policy_lineage_and_fe944cb_corpus_hashes
    def pos_28(wt: dict[str, Any]) -> None:
        wt["versions"]["policy_bundle_version"] = "synthetic-procurement-policy-set-v0.1"
        wt["versions"]["policy_kb_version"] = "synthetic-procurement-policy-kb-v0.1"
        wt["versions"]["policy_rule_versions"] = {
            "PROC-APPROVAL-01": "rule_apr_v0.2",
            "PROC-TOOL-STAGE-01": "rule_stage_v0.1",
            "PROC-SUPPLIER-01": "rule_sup_v0.1",
        }
        doc001_full_file_bare_sha = hashlib.sha256(
            b"doc-001@review-r2 full markdown source file bytes"
        ).hexdigest()
        doc004_full_file_bare_sha = hashlib.sha256(
            b"doc-004@review-r1 full markdown source file bytes"
        ).hexdigest()

        e6 = find_event(wt, "e6")
        scope = e6["attributes"]["filter_provenance"]["authorized_corpus_scope"]
        scope["corpus_version"] = "synthetic-procurement-policy-kb-v0.1"
        scope["pinned_documents"] = [
            {
                "doc_id": "doc-001",
                "doc_version": "review-r2",
                "source_document_sha256": doc001_full_file_bare_sha,
            },
            {
                "doc_id": "doc-004",
                "doc_version": "review-r1",
                "source_document_sha256": doc004_full_file_bare_sha,
            },
        ]
        r_doc = e6["attributes"]["retrieved_documents"][0]
        r_doc["doc_version"] = "review-r2"
        r_doc["source_document_sha256"] = doc001_full_file_bare_sha

        e7 = find_event(wt, "e7")
        e7["attributes"]["result_payload"]["data"]["policy_set_version"] = (
            "synthetic-procurement-policy-kb-v0.1"
        )
        e7["attributes"]["result_payload"]["data"]["matches"][0]["source_version"] = "review-r2"
        e7["attributes"]["result_payload"]["data"]["matches"][0]["source_document_sha256"] = (
            doc001_full_file_bare_sha
        )

        find_event(wt, "e19")["attributes"]["result_payload"]["data"]["policy_version"] = (
            "rule_apr_v0.2"
        )
        find_event(wt, "e25")["attributes"]["result_payload"]["data"]["approval_evidence"][
            "policy_version"
        ] = "rule_apr_v0.2"
        find_event(wt, "e27")["attributes"]["policy_version"] = "rule_apr_v0.2"
        find_event(wt, "e38")["attributes"]["visible_citations"][0]["cited_doc_version"] = (
            "review-r2"
        )

        for ev in wt["events"]:
            if ev["event_type"] == "policy_check":
                ev["attributes"]["policy_bundle_version"] = "synthetic-procurement-policy-set-v0.1"
                ev["attributes"]["authorization_snapshot"]["policy_version"] = "rule_apr_v0.2"
                for ep in ev["attributes"]["evaluated_policies"]:
                    ep["policy_version"] = wt["versions"]["policy_rule_versions"][ep["policy_id"]]

    add_case(
        "POS-28",
        "POSITIVE",
        1,
        [],
        "valid_four_level_policy_lineage_and_fe944cb_corpus_hashes: 4 distinct policy/KB/rule/source-doc versions plus bare 64-hex source_document_sha256 and sha256:-prefixed passage content_hash",
        pos_28,
    )

    # POS-29 (Emails 3 & 4 SA-03 Positive Control): valid_sa03_post_consumption_subsequent_approval_cancellation
    def pos_29(wt: dict[str, Any]) -> None:
        # Action e34 (call_po_01) was validly checked at e32 and consumed at e33 under APR-44 (areq_101, apr_rec_44_v1, seq=104).
        # Subsequently (after e36 COMPLETION), a revocation event cancels areq_101 via APR-44-REV (apr_rec_44_v2_cancelled, seq=109).
        e27_orig = find_event(wt, "e27")
        e_rev = copy.deepcopy(e27_orig)
        e_rev["event_id"] = "e37"
        e_rev["sequence_number"] = 37
        e_rev["parent_event_id"] = "e36"
        e_rev["timestamp"] = "2026-10-18T09:00:02.250Z"
        e_rev["step_name"] = "record_post_execution_approval_revocation"
        e_rev["attributes"]["approval_id"] = "APR-44-REV"
        e_rev["attributes"]["approval_request_id"] = "areq_101"
        e_rev["attributes"]["approval_status"] = "CANCELLED"
        e_rev["attributes"]["approval_timestamp"] = "2026-10-18T09:00:02.240Z"
        e_rev["attributes"]["record_version"] = "apr_rec_44_v2_cancelled"
        e_rev["attributes"]["decision_record_seq"] = 109
        e_rev["attributes"]["supersedes_approval_id"] = "APR-44"
        e_rev["attributes"]["superseded_by_approval_id"] = None
        e_rev["attributes"]["trusted_source"] = {
            "source_system": "approval_registry_db",
            "source_ref": "approval_registry://records/areq_101/APR-44-REV",
            "verification_method": "TRUSTED_TOOL_RESULT_AND_REGISTRY_READ",
            "verified_at": "2026-10-18T09:00:02.245Z",
            "record_version": "apr_rec_44_v2_cancelled",
            "decision_record_seq": 109,
        }

        e37_mc = copy.deepcopy(find_event(wt, "e37"))
        e38_fr = copy.deepcopy(find_event(wt, "e38"))

        e37_mc["event_id"] = "e38"
        e37_mc["sequence_number"] = 38
        e37_mc["parent_event_id"] = "e37"

        e38_fr["event_id"] = "e39"
        e38_fr["sequence_number"] = 39
        e38_fr["parent_event_id"] = "e38"

        wt["events"] = wt["events"][:36] + [e_rev, e37_mc, e38_fr]
        wt["post_run_analysis_example"]["governance_enforcement_summary"][
            "post_consumption_supersession"
        ] = {
            "superseded_after_consumption": True,
            "bound_approval_id_at_consumption": "APR-44",
            "bound_approval_record_version_at_consumption": "apr_rec_44_v1",
            "bound_decision_record_seq_at_consumption": 104,
            "superseding_approval_id": "APR-44-REV",
            "approval_request_id": "areq_101",
            "superseding_record_version": "apr_rec_44_v2_cancelled",
            "superseding_decision_record_seq": 109,
            "superseding_status": "CANCELLED",
        }

    add_case(
        "POS-29",
        "POSITIVE",
        1,
        [],
        "valid_sa03_post_consumption_subsequent_approval_cancellation: Action bound to APR-44 (apr_rec_44_v1, seq=104) at check/consumption remains historically valid while recording subsequent APR-44-REV (seq=109) cancellation",
        pos_29,
    )

    # POS-30 (Email 2 PR #29 c9aa20c Positive Control): valid_pr29_c9aa20c_rag_selected_context_and_citation_snapshot_binding
    def pos_30(wt: dict[str, Any]) -> None:
        e1 = find_event(wt, "e1")
        doc1 = e1["attributes"]["retrieved_documents"][1]
        doc1["source_id"] = "FAQ-018"
        e3 = find_event(wt, "e3")
        vc0 = e3["attributes"]["visible_citations"][0]
        vc0["cited_source_id"] = "FAQ-018"
        vc0["cited_content_hash"] = doc1["content_hash"]
        vc0["cited_snapshot_id"] = e1["attributes"]["source_snapshot_id"]
        ses0 = e3["attributes"]["claim_to_source_spans"][0]["source_evidence_spans"][0]
        ses0["source_snapshot_id"] = e1["attributes"]["source_snapshot_id"]
        ses0["slice_relative_char_span"] = {"start": 0, "end": 141}

    add_case(
        "POS-30",
        "POSITIVE",
        4,
        [],
        "valid_pr29_c9aa20c_rag_selected_context_and_citation_snapshot_binding: Verifies PR #29 c9aa20c identity chain (doc_id, source_id, doc_version, chunk_id, content_hash, cited_snapshot_id) and slice_relative_char_span",
        pos_30,
    )

    # NEG-71 (Blocker 2 Probe A): Invalid search_policy status='OK' and dict applicability
    def neg_71(wt: dict[str, Any]) -> None:
        e7 = find_event(wt, "e7")
        e7["attributes"]["result_payload"]["status"] = "OK"
        e7["attributes"]["result_payload"]["data"]["applicability"] = {
            "requested_policy_ids": ["PROC-TOOL-STAGE-01"],
            "non_textual_executable_policy_ids": ["PROC-TOOL-STAGE-01"],
        }

    add_case(
        "NEG-71",
        "NEGATIVE",
        1,
        ["ERR_SEARCH_POLICY_CONTRACT_INVALID"],
        "Blocker 2 Probe A: Rejects non-contract search_policy status='OK' and dict applicability object",
        neg_71,
    )

    # NEG-72 (Blocker 2 Probe B): Inconsistent search_policy status='NO_MATCH' with non-empty matches and applicability='APPLICABLE'
    def neg_72(wt: dict[str, Any]) -> None:
        e7 = find_event(wt, "e7")
        e7["attributes"]["result_payload"]["status"] = "NO_MATCH"

    add_case(
        "NEG-72",
        "NEGATIVE",
        1,
        ["ERR_SEARCH_POLICY_CONTRACT_INVALID"],
        "Blocker 2 Probe B: Rejects search_policy status='NO_MATCH' when matches is non-empty or applicability != 'MISSING'",
        neg_72,
    )

    # NEG-73 (Integration Gap 3 Probe A): Changed passage text with unchanged full-file source_document_sha256 and content_hash
    def neg_73(wt: dict[str, Any]) -> None:
        pos_28(wt)
        find_event(wt, "e6")["attributes"]["retrieved_documents"][0]["content_snippet"] += (
            " [TAMPERED PASSAGE]"
        )

    add_case(
        "NEG-73",
        "NEGATIVE",
        1,
        ["ERR_CONTENT_HASH_MISMATCH"],
        "Integration Gap 3 Probe A: Detects mutated chunk passage text even when bare 64-hex source_document_sha256 is unchanged",
        neg_73,
    )

    # NEG-74 (Integration Gap 3 Probe B): Per-policy rule version mismatch & prefixed source_document_sha256 format violation
    def neg_74(wt: dict[str, Any]) -> None:
        pos_28(wt)
        find_event(wt, "e32")["attributes"]["evaluated_policies"][0]["policy_version"] = (
            "synthetic-procurement-policy-kb-v0.1"
        )
        find_event(wt, "e6")["attributes"]["retrieved_documents"][0]["source_document_sha256"] = (
            "sha256:"
            + find_event(wt, "e6")["attributes"]["retrieved_documents"][0]["source_document_sha256"]
        )

    add_case(
        "NEG-74",
        "NEGATIVE",
        1,
        ["ERR_POLICY_LINEAGE_MISMATCH", "ERR_SOURCE_DOCUMENT_HASH_INVALID"],
        "Integration Gap 3 Probe B: Rejects conflating KB version with per-policy rule version and rejects sha256:-prefixed source_document_sha256",
        neg_74,
    )

    # NEG-75 (Email 2 PR #29 c9aa20c Snapshot Mismatch Probe): Citation binds to wrong snapshot_ref
    def neg_75(wt: dict[str, Any]) -> None:
        pos_30(wt)
        find_event(wt, "e3")["attributes"]["visible_citations"][0]["cited_snapshot_id"] = (
            "kb_snap_ent_v1_stale"
        )

    add_case(
        "NEG-75",
        "NEGATIVE",
        4,
        ["ERR_CITATION_SNAPSHOT_MISMATCH"],
        "Email 2 PR #29 c9aa20c Probe A: Rejects citation_binding whose cited_snapshot_id disagrees with observed retrieval.source_snapshot_id",
        neg_75,
    )

    # NEG-76 (Email 2 PR #29 c9aa20c Unsanitized Retrieval Fault Probe): Raw DB URI & stack traceback in retrieval_fault_details
    def neg_76(wt: dict[str, Any]) -> None:
        pos_27(wt)
        find_event(wt, "e1")["attributes"]["retrieval_fault_details"][
            "sanitized_diagnostic_summary"
        ] = "OperationalError on postgresql://postgres:supersecret@10.0.0.12:5432/trustops -- Traceback (most recent call last): File pipeline.py"

    add_case(
        "NEG-76",
        "NEGATIVE",
        4,
        ["ERR_RETRIEVAL_FAULT_UNSANITIZED"],
        "Email 2 PR #29 c9aa20c Probe B: Rejects unsanitized database URI credentials and multiline traceback in retrieval_fault_details",
        neg_76,
    )

    # NEG-77 (Emails 3 & 4 SA-03 Provisional ID-Only / Invalid Post-Consumption Supersession Probe)
    def neg_77(wt: dict[str, Any]) -> None:
        pos_29(wt)
        # Corrupt superseding_decision_record_seq so it does not advance beyond bound_decision_record_seq (104)
        # and leave record_version identical (mimicking an unversioned ID-only link)
        e37_attr = find_event(wt, "e37")["attributes"]
        e37_attr["decision_record_seq"] = 104
        e37_attr["record_version"] = "apr_rec_44_v1"
        e37_attr["trusted_source"]["decision_record_seq"] = 104
        e37_attr["trusted_source"]["record_version"] = "apr_rec_44_v1"
        wt["post_run_analysis_example"]["governance_enforcement_summary"][
            "post_consumption_supersession"
        ]["superseding_decision_record_seq"] = 104

    add_case(
        "NEG-77",
        "NEGATIVE",
        1,
        ["ERR_SA03_ACTION_APPROVAL_BINDING_INVALID"],
        "Emails 3 & 4 SA-03 Probe: Rejects unversioned/non-advancing approval cancellation link lacking distinct record_version and higher decision_record_seq",
        neg_77,
    )

    # NEG-78 (R12-05 Probe A — P06_missing_required_citation_snapshot): Remove cited_snapshot_id alone
    def neg_78(wt: dict[str, Any]) -> None:
        pos_30(wt)
        del find_event(wt, "e3")["attributes"]["visible_citations"][0]["cited_snapshot_id"]

    add_case(
        "NEG-78",
        "NEGATIVE",
        4,
        ["ERR_CITATION_IDENTITY_INCOMPLETE", "ERR_CITATION_SNAPSHOT_MISMATCH"],
        "R12-05 Probe A: Removing cited_snapshot_id alone from visible_citations is rejected without defaulting",
        neg_78,
    )

    # NEG-79 (R12-05 Probe B — P06_missing_required_citation_hash): Remove cited_content_hash alone
    def neg_79(wt: dict[str, Any]) -> None:
        pos_30(wt)
        del find_event(wt, "e3")["attributes"]["visible_citations"][0]["cited_content_hash"]

    add_case(
        "NEG-79",
        "NEGATIVE",
        4,
        ["ERR_CITATION_IDENTITY_INCOMPLETE", "ERR_CITATION_SNAPSHOT_MISMATCH"],
        "R12-05 Probe B: Removing cited_content_hash alone from visible_citations is rejected without defaulting",
        neg_79,
    )

    # NEG-80 (R12-05 Probe C — P06_missing_required_citation_all): Remove cited_snapshot_id, cited_content_hash, and cited_source_id together
    def neg_80(wt: dict[str, Any]) -> None:
        pos_30(wt)
        vc0 = find_event(wt, "e3")["attributes"]["visible_citations"][0]
        for k in ("cited_snapshot_id", "cited_content_hash", "cited_source_id"):
            vc0.pop(k, None)

    add_case(
        "NEG-80",
        "NEGATIVE",
        4,
        ["ERR_CITATION_IDENTITY_INCOMPLETE", "ERR_CITATION_SNAPSHOT_MISMATCH"],
        "R12-05 Probe C: Removing cited_snapshot_id, cited_content_hash, and cited_source_id together is rejected",
        neg_80,
    )

    # POS-31 (v1.15): Expected NO_MATCH for non-retrievable PROC-TOOL-STAGE-01 text does NOT
    # make the executable PROC-TOOL-STAGE-01 stage rule unavailable in policy_check.evaluated_policies[],
    # while preserving 4-level policy lineage (KB release on search_policy vs per-rule version on policy_check).
    def pos_31(wt: dict[str, Any]) -> None:
        pos_26(wt)
        # Attach explicit 4-level policy_rule_versions map
        wt["versions"]["policy_rule_versions"] = {
            "PROC-APPROVAL-01": "rule_apr_v0.2",
            "PROC-TOOL-STAGE-01": "rule_stage_v0.1",
            "PROC-SUPPLIER-01": "rule_sup_v0.1",
        }
        # Update policy_check (e4 & e32), calculate_approval_level, and approval to per-rule versions
        for ev in wt["events"]:
            et = ev.get("event_type")
            attrs = ev.get("attributes") or {}
            if et == "policy_check":
                for ep in attrs.get("evaluated_policies") or []:
                    pid = ep.get("policy_id")
                    if pid in wt["versions"]["policy_rule_versions"]:
                        ep["policy_version"] = wt["versions"]["policy_rule_versions"][pid]
                    if pid == "PROC-TOOL-STAGE-01":
                        # Executable stage rule remains ACTIVE & PASS despite textual NO_MATCH
                        ep["status"] = "PASS"
                        ep["policy_result"] = "PASS"
                snap = attrs.get("authorization_snapshot")
                if isinstance(snap, dict):
                    snap["policy_version"] = "rule_apr_v0.2"
            elif et == "tool_result" and attrs.get("tool_name") == "calculate_approval_level":
                data = (attrs.get("result_payload") or {}).get("data")
                if isinstance(data, dict):
                    data["policy_version"] = "rule_apr_v0.2"
            elif et == "tool_result" and attrs.get("tool_name") == "request_approval":
                ae = ((attrs.get("result_payload") or {}).get("data") or {}).get(
                    "approval_evidence"
                )
                if isinstance(ae, dict):
                    ae["policy_version"] = "rule_apr_v0.2"
            elif et == "approval":
                attrs["policy_version"] = "rule_apr_v0.2"

    add_case(
        "POS-31",
        "POSITIVE",
        1,
        [],
        "v1.16 isolated stage-only PROC-TOOL-STAGE-01 NO_MATCH lookup (stops in REQUEST_CAPTURED; does NOT replace normal policy-applicability search)",
        pos_31,
    )

    # POS-32 (v1.16 Amendment 3): Separate full-progression continuation case proving that when
    # the normal policy-applicability search returns MATCHED textual evidence (POL-114 / kb_v3),
    # non-retrievable PROC-TOOL-STAGE-01 remains active as an executable stage rule (PASS, rule_stage_v0.1)
    # under 4-level policy lineage through COMPLETED and AUTHORIZED_AND_COMMITTED.
    def pos_32(wt: dict[str, Any]) -> None:
        wt["versions"]["policy_rule_versions"] = {
            "PROC-APPROVAL-01": "rule_apr_v0.2",
            "PROC-TOOL-STAGE-01": "rule_stage_v0.1",
            "PROC-SUPPLIER-01": "rule_sup_v0.1",
        }
        for ev in wt["events"]:
            et = ev.get("event_type")
            attrs = ev.get("attributes") or {}
            if et == "policy_check":
                for ep in attrs.get("evaluated_policies") or []:
                    pid = ep.get("policy_id")
                    if pid in wt["versions"]["policy_rule_versions"]:
                        ep["policy_version"] = wt["versions"]["policy_rule_versions"][pid]
                    if pid == "PROC-TOOL-STAGE-01":
                        ep["status"] = "PASS"
                        ep["policy_result"] = "PASS"
                snap = attrs.get("authorization_snapshot")
                if isinstance(snap, dict):
                    snap["policy_version"] = "rule_apr_v0.2"
            elif et == "tool_result" and attrs.get("tool_name") == "calculate_approval_level":
                data = (attrs.get("result_payload") or {}).get("data")
                if isinstance(data, dict):
                    data["policy_version"] = "rule_apr_v0.2"
            elif et == "tool_result" and attrs.get("tool_name") == "request_approval":
                ae = ((attrs.get("result_payload") or {}).get("data") or {}).get(
                    "approval_evidence"
                )
                if isinstance(ae, dict):
                    ae["policy_version"] = "rule_apr_v0.2"
            elif et == "approval":
                attrs["policy_version"] = "rule_apr_v0.2"

    add_case(
        "POS-32",
        "POSITIVE",
        1,
        [],
        "v1.16 continuation case: normal MATCHED policy-applicability search + active executable PROC-TOOL-STAGE-01 rule (rule_stage_v0.1) progressing to COMPLETED",
        pos_32,
    )

    # NEG-81 (v1.17 — Ahmed S1-03 Row 9 Amount Field Unification):
    # Substituting the retired legacy alias `approved_amount_limit` for canonical `approved_amount_ceiling`
    # on an `approval` event MUST be rejected.
    def neg_81(wt: dict[str, Any]) -> None:
        e27_attrs = find_event(wt, "e27")["attributes"]
        val = e27_attrs.pop("approved_amount_ceiling")
        e27_attrs["approved_amount_limit"] = val

    add_case(
        "NEG-81",
        "NEGATIVE",
        1,
        [
            "ERR_APPROVAL_CEILING_EXCEEDED",
            "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH",
            "ERR_UNKNOWN_FIELD_REJECTED",
        ],
        "v1.17 S1-03 Row 9 unification: retired legacy alias approved_amount_limit in place of canonical approved_amount_ceiling is rejected",
        neg_81,
    )

    # POS-33 (v1.18 — Ahmed Row 9 Provisional Validator Boundary):
    # Strip all provisional OD-04 / SA-03 approval fields (record_version, decision_record_seq,
    # supersedes_approval_id, superseded_by_approval_id, trusted_source.verified_at, and snapshot/claim
    # approval version/sequence refs) and validate cleanly under approval_validation_profile="base_only",
    # proving the 17-field S1-03 Row 9 base Approval Event subset validates independently without
    # treating provisional Draft validator enforcement as governance ratification.
    def pos_33(wt: dict[str, Any]) -> None:
        e27_attrs = find_event(wt, "e27")["attributes"]
        for k in (
            "record_version",
            "decision_record_seq",
            "supersedes_approval_id",
            "superseded_by_approval_id",
        ):
            e27_attrs.pop(k, None)
        ts = e27_attrs.get("trusted_source")
        if isinstance(ts, dict):
            for k in ("record_version", "decision_record_seq", "verified_at"):
                ts.pop(k, None)
        for ev in wt.get("events", []):
            et = ev.get("event_type")
            attrs = ev.get("attributes", {})
            if et == "policy_check":
                snap = attrs.get("authorization_snapshot")
                if isinstance(snap, dict):
                    aref = snap.get("approval_evidence_ref")
                    if isinstance(aref, dict):
                        for k in (
                            "approval_record_version",
                            "latest_observed_approval_record_version",
                            "is_current_at_check",
                            "decision_record_seq",
                            "latest_observed_decision_record_seq",
                        ):
                            aref.pop(k, None)
                    dclaim = snap.get("dispatch_claim")
                    if isinstance(dclaim, dict):
                        dclaim.pop("bound_approval_record_version", None)
            elif et == "agent_state":
                dcc = attrs.get("dispatch_claim_consumption")
                if isinstance(dcc, dict):
                    for k in (
                        "bound_approval_record_version",
                        "observed_approval_record_version_at_consumption",
                        "bound_decision_record_seq",
                        "observed_decision_record_seq_at_consumption",
                    ):
                        dcc.pop(k, None)
        ledger = (wt.get("execution_budget_telemetry") or {}).get("dispatch_claim_ledger")
        if isinstance(ledger, list):
            for item in ledger:
                if isinstance(item, dict):
                    for k in (
                        "bound_approval_record_version",
                        "observed_approval_record_version_at_consumption",
                        "bound_decision_record_seq",
                        "observed_decision_record_seq_at_consumption",
                    ):
                        item.pop(k, None)

    add_case(
        "POS-33",
        "POSITIVE",
        1,
        [],
        "v1.18 base_only profile: 17-field S1-03 Row 9 base Approval Event subset validates cleanly with all provisional OD-04/SA-03 fields removed",
        pos_33,
        approval_validation_profile="base_only",
    )

    # POS-34 (GD-36): AUTHORIZED_DISPATCH_RESOLVED_NO_SIDE_EFFECT accepted in enforcement_outcome
    def pos_34(wt: dict[str, Any]) -> None:
        wt["post_run_analysis_example"]["governance_enforcement_summary"]["enforcement_outcome"] = (
            "AUTHORIZED_DISPATCH_RESOLVED_NO_SIDE_EFFECT"
        )

    add_case(
        "POS-34",
        "POSITIVE",
        1,
        [],
        "GD-36: AUTHORIZED_DISPATCH_RESOLVED_NO_SIDE_EFFECT accepted as canonical definitive no-effect enforcement_outcome",
        pos_34,
    )

    # POS-35 (A4): Explicit stale_reason_code=None on current approval_evidence_ref and dispatch_claim_consumption
    def pos_35(wt: dict[str, Any]) -> None:
        find_event(wt, "e32")["attributes"]["authorization_snapshot"]["approval_evidence_ref"][
            "stale_reason_code"
        ] = None
        find_event(wt, "e33")["attributes"]["dispatch_claim_consumption"]["stale_reason_code"] = (
            None
        )
        wt["execution_budget_telemetry"]["dispatch_claim_ledger"][0]["stale_reason_code"] = None

    add_case(
        "POS-35",
        "POSITIVE",
        1,
        [],
        "A4: explicit stale_reason_code=None on current approval_evidence_ref and dispatch_claim_consumption passes",
        pos_35,
    )

    # NEG-82 (GD-35): EXPIRED approval_status rejected as invalid enum value
    def neg_82(wt: dict[str, Any]) -> None:
        find_event(wt, "e27")["attributes"]["approval_status"] = "EXPIRED"

    add_case(
        "NEG-82",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_STATUS_INVALID"],
        "GD-35: dropped EXPIRED approval_status is rejected with ERR_APPROVAL_STATUS_INVALID",
        neg_82,
    )

    # NEG-83 (A1): Second APPROVED record after APPROVED on same approval_request_id rejected
    def neg_83(wt: dict[str, Any]) -> None:
        e27 = find_event(wt, "e27")
        e_dup = copy.deepcopy(e27)
        e_dup["event_id"] = "e39"
        e_dup["sequence_number"] = 39
        e_dup["parent_event_id"] = "e38"
        e_dup["timestamp"] = "2026-10-18T09:00:02.400Z"
        e_dup["attributes"]["approval_id"] = "APR-44-SECOND"
        e_dup["attributes"]["approval_status"] = "APPROVED"
        e_dup["attributes"]["record_version"] = "apr_rec_44_v2_dup"
        e_dup["attributes"]["decision_record_seq"] = 109
        e_dup["attributes"]["supersedes_approval_id"] = "APR-44"
        e_dup["attributes"]["superseded_by_approval_id"] = None
        e_dup["attributes"]["trusted_source"]["record_version"] = "apr_rec_44_v2_dup"
        e_dup["attributes"]["trusted_source"]["decision_record_seq"] = 109
        e_dup["attributes"]["trusted_source"]["source_ref"] = (
            "approval_registry://records/areq_101/APR-44-SECOND"
        )
        e_dup["attributes"]["trusted_source"]["verified_at"] = "2026-10-18T09:00:02.350Z"
        wt["events"].append(e_dup)

    add_case(
        "NEG-83",
        "NEGATIVE",
        1,
        ["ERR_SA03_ACTION_APPROVAL_BINDING_INVALID"],
        "A1: second APPROVED record after APPROVED on same approval_request_id is rejected",
        neg_83,
    )

    # NEG-84 (A2): Subsequent approval record missing supersedes_approval_id rejected
    def neg_84(wt: dict[str, Any]) -> None:
        e27 = find_event(wt, "e27")
        e_rev = copy.deepcopy(e27)
        e_rev["event_id"] = "e39"
        e_rev["sequence_number"] = 39
        e_rev["parent_event_id"] = "e38"
        e_rev["timestamp"] = "2026-10-18T09:00:02.400Z"
        e_rev["attributes"]["approval_id"] = "APR-44-REV-NOLINK"
        e_rev["attributes"]["approval_status"] = "CANCELLED"
        e_rev["attributes"]["record_version"] = "apr_rec_44_v2_nolink"
        e_rev["attributes"]["decision_record_seq"] = 109
        e_rev["attributes"]["supersedes_approval_id"] = None
        e_rev["attributes"]["superseded_by_approval_id"] = None
        e_rev["attributes"]["trusted_source"]["record_version"] = "apr_rec_44_v2_nolink"
        e_rev["attributes"]["trusted_source"]["decision_record_seq"] = 109
        e_rev["attributes"]["trusted_source"]["source_ref"] = (
            "approval_registry://records/areq_101/APR-44-REV-NOLINK"
        )
        e_rev["attributes"]["trusted_source"]["verified_at"] = "2026-10-18T09:00:02.350Z"
        wt["events"].append(e_rev)

    add_case(
        "NEG-84",
        "NEGATIVE",
        1,
        ["ERR_SA03_ACTION_APPROVAL_BINDING_INVALID"],
        "A2: subsequent approval record with null supersedes_approval_id is rejected",
        neg_84,
    )

    # NEG-85 (A3): Stored approval event with non-null superseded_by_approval_id rejected
    def neg_85(wt: dict[str, Any]) -> None:
        find_event(wt, "e27")["attributes"]["superseded_by_approval_id"] = "APR-44-REV"

    add_case(
        "NEG-85",
        "NEGATIVE",
        1,
        ["ERR_SA03_ACTION_APPROVAL_BINDING_INVALID"],
        "A3: stored approval event with non-null superseded_by_approval_id (read-model only) is rejected",
        neg_85,
    )

    # NEG-86 (A4): Invalid stale_reason_code rejected on approval_evidence_ref
    def neg_86(wt: dict[str, Any]) -> None:
        find_event(wt, "e32")["attributes"]["authorization_snapshot"]["approval_evidence_ref"][
            "stale_reason_code"
        ] = "UNKNOWN_STALE_CODE"

    add_case(
        "NEG-86",
        "NEGATIVE",
        1,
        ["ERR_STALE_REASON_CODE_INVALID"],
        "A4: unknown stale_reason_code on approval_evidence_ref is rejected",
        neg_86,
    )

    # NEG-87 (A5): Approval event sequence_number after create_purchase_order tool_proposal rejected on ALLOW
    def neg_87(wt: dict[str, Any]) -> None:
        evs = wt["events"]
        ap_idx = next(i for i, e in enumerate(evs) if e["event_id"] == "e27")
        po_prop_idx = next(
            i
            for i, e in enumerate(evs)
            if e.get("event_type") == "tool_proposal"
            and (e.get("attributes") or {}).get("known_tool_name") == "create_purchase_order"
        )
        ap_ev = evs.pop(ap_idx)
        # Insert approval right after the create_purchase_order tool_proposal (still before policy_check e32)
        evs.insert(po_prop_idx, ap_ev)
        for seq_i, e in enumerate(evs, 1):
            e["sequence_number"] = seq_i

    add_case(
        "NEG-87",
        "NEGATIVE",
        1,
        ["ERR_APPROVAL_ORDER_INVALID"],
        "A5: approval event not preceding tool_proposal by trace sequence_number is rejected on ALLOW",
        neg_87,
    )

    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Run S1-01 113-case regression suite (v1.11.0)")
    parser.add_argument("--spec", default=DEFAULT_SPEC, help="Path to updated_schemas_v18.md")
    parser.add_argument(
        "--validator", default=DEFAULT_VALIDATOR, help="Path to validate_s1_01_schema_v1_11.py"
    )
    parser.add_argument(
        "--report-out", default="s1_01_validation_report.json", help="Output JSON report path"
    )
    args = parser.parse_args()

    if not os.path.exists(args.spec) and args.spec == DEFAULT_SPEC:
        try:
            args.spec = str(_find_repo_file(DEFAULT_SPEC, pathlib.Path(__file__)))
        except FileNotFoundError:
            pass
    if not os.path.exists(args.spec):
        print(f"ERROR: Specification file not found: {args.spec}", file=sys.stderr)
        return 2
    if not os.path.exists(args.validator) and args.validator == DEFAULT_VALIDATOR:
        try:
            args.validator = str(_find_repo_file(DEFAULT_VALIDATOR, pathlib.Path(__file__)))
        except FileNotFoundError:
            pass
    if not os.path.exists(args.validator):
        print(f"ERROR: Validator module not found: {args.validator}", file=sys.stderr)
        return 2
    import importlib.util

    spec_obj = importlib.util.spec_from_file_location(
        "dynamic_validator_mod", os.path.abspath(args.validator)
    )
    if spec_obj is None or spec_obj.loader is None:
        print(f"ERROR: Could not load validator module from {args.validator}", file=sys.stderr)
        return 2
    global val_mod
    val_mod = importlib.util.module_from_spec(spec_obj)
    spec_obj.loader.exec_module(val_mod)

    with open(args.spec, encoding="utf-8") as f:
        base_spec_text = f.read()

    blocks = extract_json_blocks(base_spec_text)
    wts = [blocks[9][1], blocks[10][1], blocks[11][1], blocks[12][1]]

    cases = build_cases()
    probe_dir = tempfile.mkdtemp(prefix="trustops_s1_01_probes_")

    results = []
    passed_count = 0
    base_counts: dict[str, int] = {}

    for c in cases:
        cid = c["case_id"]
        wt_idx = c["wt_idx"]
        if cid == "BASE-00":
            validator = val_mod.SpecValidator(args.spec, check_report_sync=True)
            ok, codes, counts = validator.validate()
            base_counts = counts
        else:
            wt_copy = copy.deepcopy(wts[wt_idx - 1])
            c["mutator"](wt_copy)
            if cid == "NEG-60":
                wt_copy["events"][0]["attributes"]["retrieved_documents"][0]["score"] = 999999.0
            mut_text = rebuild_spec_with_wt(base_spec_text, wt_idx, wt_copy)
            if cid == "NEG-60":
                mut_text = mut_text.replace("999999.0", "1e309")
            probe_path = os.path.join(probe_dir, f"{cid}.md")
            with open(probe_path, "w", encoding="utf-8") as pf:
                pf.write(mut_text)
            validator = val_mod.SpecValidator(
                probe_path,
                check_report_sync=False,
                approval_validation_profile=c.get(
                    "approval_validation_profile", "provisional_draft"
                ),
            )
            ok, codes, _ = validator.validate()
            try:
                os.remove(probe_path)
            except OSError:
                pass

        exp_pass = c["expected_pass"]
        exp_codes = set(c["expected_codes"])
        actual_codes = set(codes)

        if exp_pass:
            case_ok = ok and len(actual_codes) == 0
        else:
            case_ok = (not ok) and exp_codes.issubset(actual_codes)

        if case_ok:
            passed_count += 1
        results.append(
            {
                "case_id": cid,
                "kind": c["kind"],
                "description": c["description"],
                "expected_pass": exp_pass,
                "actual_pass": ok,
                "expected_codes": sorted(exp_codes),
                "actual_codes": sorted(actual_codes),
                "case_matched_expectation": case_ok,
            }
        )

    try:
        os.rmdir(probe_dir)
    except OSError:
        pass

    wt_bundle_sha256 = hashlib.sha256(
        val_mod.canonical_json_bytes([blocks[9][1], blocks[10][1], blocks[11][1], blocks[12][1]])
    ).hexdigest()

    report = {
        "report_version": SUITE_VERSION,
        "validator_version": val_mod.VALIDATOR_VERSION,
        "comparison_baselines": {
            "application_contracts_commit": "479cab00c021db7a58b826b46a653c3e2308b798",
            "v1_8_review_baseline_commit": "9e6affaa6d2f9bfca675e63e1c536d47005cd74d",
            "experiment_requirements_baseline": "experiment_requirements_v2-4.md",
        },
        "files": {
            "specification": {
                "filename": os.path.basename(args.spec),
                "sha256": sha256_file(args.spec),
            },
            "validator": {
                "filename": os.path.basename(args.validator),
                "sha256": sha256_file(args.validator),
            },
            "regression_runner": {
                "filename": os.path.basename(__file__),
                "sha256": sha256_file(os.path.abspath(__file__)),
            },
            "walkthrough_fixtures_canonical_bundle_sha256": wt_bundle_sha256,
        },
        "baseline_validation": {
            "passed": results[0]["actual_pass"],
            "total_assertions": sum(base_counts.values()),
            "total_failures": 0 if results[0]["actual_pass"] else 1,
            "category_assertions": base_counts,
        },
        "regression_suite_summary": {
            "total_cases": len(cases),
            "positive_controls": sum(1 for c in cases if c["kind"] == "POSITIVE"),
            "negative_probes": sum(1 for c in cases if c["kind"] == "NEGATIVE"),
            "matched_expectations": passed_count,
            "unmet_expectations": len(cases) - passed_count,
            "all_expectations_met": passed_count == len(cases),
        },
        "cases": results,
    }

    if args.report_out:
        with open(args.report_out, "w", encoding="utf-8") as rf:
            json.dump(report, rf, indent=2)

    print(f"Regression Suite Version: {SUITE_VERSION}")
    print(f"Baseline Assertions: {sum(base_counts.values())} (Pass: {results[0]['actual_pass']})")
    print(f"Suite Summary: {passed_count}/{len(cases)} cases matched expectations")
    for r in results:
        if not r["case_matched_expectation"]:
            print(
                f"  [UNMET] {r['case_id']}: expected={r['expected_codes']} actual={r['actual_codes']}"
            )

    return 0 if passed_count == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
