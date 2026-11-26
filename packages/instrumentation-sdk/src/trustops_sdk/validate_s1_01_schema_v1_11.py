#!/usr/bin/env python3
"""
Standalone Reproducible Specification & Semantic Contract Validator for S1-01 (Draft v1.11)
Target Specification: updated_schemas_v18.md
Version: 1.10.0

Enforces Three Validation Layers across all 13 JSON blocks and Specification Tables:
  - L1_STRUCTURAL_VALIDITY (cat1_envelope_and_syntax)
  - L2_EVIDENCE_CONSISTENCY (cat2_ordering_and_refs, cat3_digests_hashes_spans, cat4_contracts_snapshots_bindings)
  - L3_FIXTURE_CONSISTENCY_AND_ISOLATION (cat5_isolation_and_report)
"""

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
import pathlib
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, TypeGuard

VALIDATOR_VERSION = "1.11.0"
BARE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PREFIXED_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UNSANITIZED_FAULT_RE = re.compile(
    r"(?i)(postgresql://|postgres://|password=|api_key=|AIza[0-9A-Za-z\-_]{10,}|Traceback \(most recent call last\))"
)
DEFAULT_SPEC_FILENAME = "updated_schemas_v18.md"

PROC_APP_STATES = {
    "REQUEST_CAPTURED",
    "POLICY_CHECKED",
    "SUPPLIER_CHECKED",
    "APPROVAL_CALCULATED",
    "APPROVAL_PENDING",
    "APPROVED",
    "PO_CREATION",
    "COMPLETION",
}

PROC_POLICY_STAGES = {
    "PRE_APPROVAL",
    "APPROVED",
    "PO_CREATION",
    "COMPLETED",
}

STATE_TO_STAGE_MAP = {
    "REQUEST_CAPTURED": "PRE_APPROVAL",
    "POLICY_CHECKED": "PRE_APPROVAL",
    "SUPPLIER_CHECKED": "PRE_APPROVAL",
    "APPROVAL_CALCULATED": "PRE_APPROVAL",
    "APPROVAL_PENDING": "PRE_APPROVAL",
    "APPROVED": "APPROVED",
    "PO_CREATION": "PO_CREATION",
    "COMPLETION": "COMPLETED",
}

RAG_STAGES = {
    "USER_QUERY",
    "QUERY_RECEIVED",
    "RETRIEVAL",
    "RETRIEVAL_COMPLETED",
    "EVIDENCE_SELECTION",
    "CONTEXT_SELECTED",
    "ANSWER_GENERATION",
    "GENERATION_COMPLETED",
    "CITATION_BINDING",
    "CITATION_VALIDATED",
    "ANSWER_DELIVERED",
    "FINAL_RESPONSE",
    "ABSTENTION",
    "ERROR",
}

TRACE_EXECUTION_STATUSES = {
    "ACTIVE",
    "COMPLETED",
    "SUCCEEDED",
    "RECOVERED",
    "WAITING_APPROVAL",
    "HALTED_POLICY_BLOCK",
    "BLOCKED",
    "STOPPED_BUSINESS_BLOCK",
    "STOPPED_APPROVAL_PENDING",
    "STOPPED_APPROVAL_DENIED",
    "RECOVERY_PENDING",
    "FAILED",
    "TIMED_OUT",
    "CANCELLED",
    "ABSTAINED",
    "RUNTIME_ERROR",
}

FAILURE_CLASSES_ENUM = {
    "NORMAL",
    "RETRIEVAL_FAILURE",
    "HALLUCINATION",
    "TOOL_SELECTION_ERROR",
    "INVALID_TOOL_ARGUMENTS",
    "WORKFLOW_VIOLATION",
    "POLICY_VIOLATION",
    "PROMPT_INJECTION",
    "UNSUPPORTED_COMPLETION",
}

ROOT_CAUSES_ENUM = {
    "prompt",
    "retriever",
    "retrieved_context",
    "model_generation",
    "tool_selection",
    "tool_arguments",
    "agent_workflow",
    "policy_configuration",
    "malicious_input",
}

SECURITY_CATEGORIES_ENUM = {
    "DIRECT_USER_PROMPT_INJECTION",
    "INDIRECT_RETRIEVED_DOC_INJECTION",
    "POLICY_BYPASS_SOCIAL_ENGINEERING",
    "TOOL_ARGUMENT_INJECTION",
    "BENIGN_SECURITY_LOOKALIKE",
}

# GD-35: EXPIRED removed (MVP has no time-based expiry; unexpected EXPIRED handled fail-closed as ERROR / EVIDENCE_UNRESOLVED)
APPROVAL_STATUS_ENUM = {
    "PENDING",
    "APPROVED",
    "DENIED",
    "CANCELLED",
    "STALE_REVISION",
}

# A4: Canonical stale reason codes for approval_evidence_ref and dispatch_claim_consumption
STALE_REASON_CODES_ENUM = {
    "APPROVAL_RECORD_SUPERSEDED",
    "APPROVAL_NO_LONGER_APPROVED",
    "SUPPLIER_RECORD_SUPERSEDED",
    "REQUEST_REVISION_CHANGED",
    "POLICY_BUNDLE_CHANGED",
}

POLICY_CHECK_MODES_ENUM = {
    "ONLINE_PRE_TOOL",
    "STUB_CONTRACT_TEST",
}

RETRIEVAL_EXECUTION_STATUSES = {
    "COMPLETED",
    "COMPLETED_ZERO_HITS",
    "RETRIEVAL_TIMEOUT",
    "VECTOR_STORE_OR_SQL_ERROR",
    "EMBEDDING_PROVIDER_ERROR",
    "CORPUS_INTEGRITY_OR_PIN_MISMATCH_ERROR",
}

RETRIEVAL_TECHNICAL_FAULT_STATUSES = {
    "RETRIEVAL_TIMEOUT",
    "VECTOR_STORE_OR_SQL_ERROR",
    "EMBEDDING_PROVIDER_ERROR",
    "CORPUS_INTEGRITY_OR_PIN_MISMATCH_ERROR",
}

# GD-36: Includes AUTHORIZED_DISPATCH_RESOLVED_NO_SIDE_EFFECT (covers authoritative tool failure and recovery-to-aborted)
ENFORCEMENT_OUTCOME_ENUM = {
    "AUTHORIZED_AND_COMMITTED",
    "AUTHORIZED_DISPATCH_RESOLVED_COMMITTED_VIA_RECOVERY",
    "AUTHORIZED_DISPATCH_RESOLVED_NO_SIDE_EFFECT",
    "AUTHORIZED_DISPATCH_UNRESOLVED_HOLD",
    "UNAUTHORIZED_DISPATCH_POLICY_BYPASS",
    "BLOCKED_PRE_TOOL_NO_SIDE_EFFECT",
    "NOT_REACHED_STOPPED_BEFORE_PO_GATE",
    "NOT_APPLICABLE_RAG_WORKFLOW",
}

OPERATION_PROFILE_CONTRACTS: dict[str, dict[str, str]] = {
    "proc_agent_tool_selection_v1": {
        "step_purpose": "tool_selection",
        "structured_output_schema": "ProcurementToolProposalOrSynthesis_v1",
    },
    "proc_agent_final_synthesis_v1": {
        "step_purpose": "final_response_synthesis",
        "structured_output_schema": "ProcurementToolProposalOrSynthesis_v1",
    },
    "rag_grounded_answer_v1": {
        "step_purpose": "rag_answer_generation",
        "structured_output_schema": "RagGroundedAnswer_v1",
    },
}

CANONICAL_JSON_TEST_VECTORS: list[tuple[dict[str, Any], str, str]] = [
    (
        {"z_key": 1, "a_key": "value", "m_key": True},
        '{"a_key":"value","m_key":true,"z_key":1}',
        "sha256:6e5aaa32864f091389ecbc3adf91587a1677e1c280453416dd91b3c5b973b013",
    ),
    (
        {"supplier_id": "SUP-088", "note": "Caf\u00e9 \u2014 Cr\u00e8me", "quantity": 20},
        '{"note":"Caf\u00e9 \u2014 Cr\u00e8me","quantity":20,"supplier_id":"SUP-088"}',
        "sha256:1847323fd0c2840352ef5fa6da1bf7969a05572aa8fade6b7e16f57878095c96",
    ),
    (
        {"optional_field": None, "present_field": "ok"},
        '{"optional_field":null,"present_field":"ok"}',
        "sha256:b279c37e774c002972060d73291c77e54ee751e7a1e78b6e2458515708933e17",
    ),
]

PERMITTED_INFERENCE_TOP_KEYS = {
    "trace_id",
    "schema_version",
    "application_id",
    "application_type",
    "ingestion_mode",
    "is_partial_walkthrough",
    "environment",
    "started_at",
    "completed_at",
    "total_latency_ms",
    "execution_status",
    "last_app_state",
    "last_rag_stage",
    "versions",
    "metadata_availability",
    "request",
    "events",
    "execution_budget_telemetry",
}

FORBIDDEN_INFERENCE_TOP_KEYS = {
    "scenario_metadata",
    "fixture_provenance",
    "replay_provenance",
    "post_run_analysis_example",
    "adjudication_record",
}

ALLOWED_TRACE_TOP_KEYS = PERMITTED_INFERENCE_TOP_KEYS | FORBIDDEN_INFERENCE_TOP_KEYS

ALLOWED_EVENT_ENVELOPE_KEYS = {
    "event_id",
    "trace_id",
    "sequence_number",
    "timestamp",
    "event_type",
    "step_name",
    "actor",
    "parent_event_id",
    "span_id",
    "parent_span_id",
    "latency_ms",
    "status",
    "attributes",
}

# S1-03 Row 9 Base Approval Event attributes (17 fields; aligned to tool contract 479cab0,
# pending joint governance sign-off as Draft v1.18):
APPROVAL_BASE_ATTR_KEYS: set[str] = {
    "approval_id",
    "approval_request_id",
    "request_id",
    "bound_calculation_ref",
    "bound_request_revision",
    "bound_supplier_id",
    "bound_amount",
    "bound_currency",
    "approved_amount_ceiling",
    "approval_level",
    "policy_id",
    "policy_version",
    "approval_status",
    "approver_id",
    "approver_role",
    "approval_timestamp",
    "trusted_source",
}

# Provisional Draft OD-04 / SA-03 Approval extension attributes (4 fields; intentionally enforced
# under the default `provisional_draft` validator profile for Draft v1.18 self-validation, while
# governance acceptance remains PENDING joint sign-off and S1-03 excludes them from base Row 9
# evidence & evaluator decisions until ratified; RC-07 remains BLOCKED):
APPROVAL_PROVISIONAL_OD04_SA03_ATTR_KEYS: set[str] = {
    "record_version",
    "decision_record_seq",
    "supersedes_approval_id",
    "superseded_by_approval_id",
}

APPROVAL_VALIDATION_PROFILES = ("provisional_draft", "base_only")

ALLOWED_EVENT_ATTR_KEYS: dict[str, set[str]] = {
    "agent_state": {
        "state_revision_id",
        "from_app_state",
        "to_app_state",
        "app_state",
        "policy_stage",
        "transition_attempted",
        "transition_accepted",
        "transition_reason",
        "authorization_basis",
        "po_dispatched",
        "po_created",
        "approval_requirement_status",
        "approval_required",
        "approval_received",
        "required_approval_level",
        "calculation_ref",
        "evaluated_amount",
        "currency",
        "policy_threshold",
        "supplier_id",
        "supplier_status",
        "raw_supplier_status",
        "bound_authorization_check_id",
        "bound_dispatch_claim_id",
        "dispatch_claim_consumption",
    },
    "approval": APPROVAL_BASE_ATTR_KEYS | APPROVAL_PROVISIONAL_OD04_SA03_ATTR_KEYS,
    "argument_validation": {
        "validation_id",
        "target_proposal_id",
        "raw_proposed_tool_name",
        "tool_name",
        "tool_schema_version",
        "validation_status",
        "normalized_arguments",
        "arguments_digest",
        "validation_errors",
    },
    "final_response": {
        "generating_model_call_id",
        "raw_model_candidate_text",
        "delivered_response_text",
        "response_text",
        "runtime_modification_status",
        "runtime_correction_or_suppression_reason",
        "response_mode",
        "is_abstention",
        "abstention_details",
        "visible_citations",
        "claim_to_source_spans",
        "claimed_actions",
    },
    "model_call": {
        "model_call_id",
        "step_purpose",
        "provider",
        "model_id",
        "returned_model_version",
        "operation_profile_id",
        "effective_config_ref",
        "generation_parameters",
        "prompt_template_id",
        "selected_context_ref",
        "rendered_prompt_or_messages",
        "output_text",
        "proposed_tool_calls",
        "token_usage",
        "execution_status",
        "refusal_reason",
        "provider_fault_details",
        "retry_accounting",
    },
    "policy_check": {
        "check_id",
        "target_proposal_id",
        "policy_bundle_version",
        "check_mode",
        "evaluated_policies",
        "authorization_snapshot",
        "action_verdict",
        "verdict_basis",
    },
    "recovery_check": {
        "recovery_id",
        "recovery_of_call_id",
        "recovery_of_result_id",
        "operation_mode",
        "reconciliation_method",
        "is_read_only_observation",
        "queried_idempotency_key",
        "ledger_record_status",
        "reconciliation_status",
        "resolved_side_effect_state",
        "recovered_result_envelope",
        "recovery_session_id",
        "recovery_session_number",
        "recovery_attempt_number",
        "recovery_authorization_ref",
        "queried_business_payload_sha256",
        "unresolved_reason_code",
    },
    "retrieval": {
        "retrieval_id",
        "query_text",
        "effective_query",
        "retriever_type",
        "source_snapshot_id",
        "top_k_requested",
        "returned_count",
        "execution_status",
        "retrieval_fault_details",
        "filter_provenance",
        "score_semantics",
        "evidence_sufficiency",
        "retrieved_documents",
    },
    "tool_call": {
        "call_id",
        "proposal_id",
        "validation_id",
        "authorization_check_id",
        "tool_name",
        "arguments",
        "arguments_digest",
        "trusted_runtime_context",
        "dispatch_claim_id",
        "dispatch_claim_consumption_ref",
        "runtime_binding_verification",
        "app_state_at_dispatch",
        "policy_stage_at_dispatch",
        "checked_source_state_revision",
        "dispatch_state_revision",
        "retry_accounting",
    },
    "tool_proposal": {
        "proposal_id",
        "raw_proposed_tool_name",
        "known_tool_name",
        "app_state_at_proposal",
        "policy_stage_at_proposal",
        "is_risky_action",
        "raw_arguments_serialized",
        "arguments_parse_status",
        "proposed_arguments",
        "trusted_runtime_context",
    },
    "tool_result": {
        "result_id",
        "call_id",
        "tool_name",
        "execution_status",
        "side_effect_state",
        "result_payload",
        "transport_diagnostics",
        "linked_retrieval_id",
    },
    "tool_suppression": {
        "suppression_id",
        "target_proposal_id",
        "raw_proposed_tool_name",
        "tool_name",
        "suppression_source",
        "blocking_check_id",
        "blocking_policy_ids",
        "tool_dispatched",
        "side_effect_state",
        "validation_id",
        "suppression_reason",
        "execution_started",
    },
}

REQUIRED_SNAPSHOT_KEYS = {
    "proposal_id",
    "validation_id",
    "tool_name",
    "validated_arguments",
    "arguments_digest",
    "root_request_id",
    "request_revision",
    "checked_source_state_revision",
    "checked_app_state",
    "checked_policy_stage",
    "operation_mode",
    "supplier_evidence_ref",
    "calculation_evidence_ref",
    "approval_evidence_ref",
    "policy_id",
    "policy_version",
    "policy_bundle_version",
    "dispatch_claim",
    "resulting_dispatch_state_revision",
    "policy_id_resolution_status",
}


def validate_canonical_json_domain(obj: Any, allow_floats: bool = False) -> bool:
    """
    Validates restricted trustops-canonical-json-v1 domain (OD-13):
    - Object keys must be non-empty ASCII identifier strings (^[A-Za-z0-9_.-]+$)
    - Strings must be NFC-normalized Unicode without unpaired surrogates
    - Integers must lie within signed 64-bit integer bounds [-(2**63), 2**63 - 1]
    - Floats are forbidden in digested business/argument payloads unless allow_floats=True,
      and when allowed must be finite (math.isfinite).
    """
    if obj is None or isinstance(obj, bool):
        return True
    if isinstance(obj, int):
        return -(2**63) <= obj <= (2**63 - 1)
    if isinstance(obj, float):
        if not allow_floats:
            return False
        return math.isfinite(obj)
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj) == obj
    if isinstance(obj, list):
        return all(validate_canonical_json_domain(item, allow_floats=allow_floats) for item in obj)
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str) or not re.match(r"^[A-Za-z0-9_.-]+$", k):
                return False
            if not validate_canonical_json_domain(v, allow_floats=allow_floats):
                return False
        return True
    return False


def canonical_json_bytes(
    obj: Any, enforce_domain: bool = False, allow_floats: bool = False
) -> bytes:
    """Project-specific deterministic canonical JSON (trustops-canonical-json-v1)."""
    if enforce_domain and not validate_canonical_json_domain(obj, allow_floats=allow_floats):
        raise ValueError("ERR_CANONICAL_JSON_DOMAIN_VIOLATION")
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def compute_arguments_digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def compute_business_payload_sha256(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def compute_content_hash(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_iso8601_utc(ts: Any) -> datetime.datetime | None:
    if not isinstance(ts, str) or not ts.endswith("Z"):
        return None
    try:
        dt = datetime.datetime.fromisoformat(ts[:-1] + "+00:00")
        return dt
    except ValueError:
        return None


def is_strict_int(val: Any) -> TypeGuard[int]:
    return isinstance(val, int) and not isinstance(val, bool)


def is_money_str(val: Any) -> bool:
    return isinstance(val, str) and bool(re.match(r"^\d+\.\d{2}$", val))


def project_trace_for_inference(wt: dict[str, Any]) -> dict[str, Any]:
    """Strips all test-only ground-truth, recipe, qrel, security-subset, execution_scope, adjudication, and post-run blocks."""
    projected = {}
    for k, v in wt.items():
        if k in FORBIDDEN_INFERENCE_TOP_KEYS:
            continue
        if k in PERMITTED_INFERENCE_TOP_KEYS:
            projected[k] = copy.deepcopy(v)
    for ev in projected.get("events", []):
        if ev.get("event_type") == "retrieval":
            for doc in ev.get("attributes", {}).get("retrieved_documents", []):
                sm = doc.get("source_metadata")
                if isinstance(sm, dict):
                    sm.pop("is_poisoned_test_doc", None)
                    sm.pop("qrel_grade", None)
    return projected


class SpecValidator:
    def __init__(
        self,
        spec_path: str,
        check_report_sync: bool = True,
        approval_validation_profile: str = "provisional_draft",
    ) -> None:
        if approval_validation_profile not in APPROVAL_VALIDATION_PROFILES:
            raise ValueError(
                f"Unsupported approval_validation_profile: {approval_validation_profile!r}"
            )
        self.spec_path = spec_path
        self.check_report_sync = check_report_sync
        self.approval_validation_profile = approval_validation_profile
        self.counts: dict[str, int] = {
            "cat1_envelope_and_syntax": 0,
            "cat2_ordering_and_refs": 0,
            "cat3_digests_hashes_spans": 0,
            "cat4_contracts_snapshots_bindings": 0,
            "cat5_isolation_and_report": 0,
        }
        self.failures: list[dict[str, str]] = []
        self.failure_codes: set[str] = set()

    def check(self, cat: str, cond: bool, code: str, msg: str) -> bool:
        self.counts[cat] += 1
        if not cond:
            self.failures.append({"category": cat, "code": code, "message": msg})
            self.failure_codes.add(code)
        return cond

    def validate(self) -> tuple[bool, list[str], dict[str, int]]:
        with open(self.spec_path, encoding="utf-8") as f:
            text = f.read()

        raw_blocks = [m.group(1) for m in re.finditer(r"```json\n(.*?)\n```", text, re.DOTALL)]
        self.check(
            "cat1_envelope_and_syntax",
            len(raw_blocks) == 13,
            "ERR_JSON_BLOCK_COUNT",
            f"Expected 13 JSON blocks in {self.spec_path}, found {len(raw_blocks)}",
        )
        blocks: list[dict[str, Any]] = []
        for idx, rb in enumerate(raw_blocks):
            try:
                parsed = json.loads(rb)
                self.check(
                    "cat1_envelope_and_syntax",
                    isinstance(parsed, dict),
                    "ERR_JSON_SYNTAX",
                    f"Block {idx} is not a JSON object",
                )
                blocks.append(parsed)
            except Exception as exc:
                self.check(
                    "cat1_envelope_and_syntax",
                    False,
                    "ERR_JSON_SYNTAX",
                    f"JSON parse error in block {idx}: {exc}",
                )
                return False, sorted(self.failure_codes), self.counts

        if len(blocks) < 13:
            return False, sorted(self.failure_codes), self.counts

        walkthroughs = blocks[9:13]
        for wt_idx, wt in enumerate(walkthroughs, 1):
            self._validate_walkthrough(wt_idx, wt)

        self._validate_spec_tables_and_report(text, walkthroughs)
        return len(self.failures) == 0, sorted(self.failure_codes), self.counts

    def _validate_walkthrough(self, wt_idx: int, wt: dict[str, Any]) -> None:
        tid = str(wt.get("trace_id", f"WT{wt_idx}"))
        cat1 = "cat1_envelope_and_syntax"
        cat2 = "cat2_ordering_and_refs"

        extra_top = set(wt.keys()) - ALLOWED_TRACE_TOP_KEYS
        self.check(
            cat1,
            len(extra_top) == 0,
            "ERR_UNKNOWN_FIELD_REJECTED",
            f"{tid}: unknown top keys {extra_top}",
        )
        for req_k in PERMITTED_INFERENCE_TOP_KEYS:
            self.check(cat1, req_k in wt, "ERR_ENVELOPE_MISSING_KEY", f"{tid}: missing key {req_k}")

        app_type = wt.get("application_type")
        self.check(
            cat1,
            app_type in {"agent", "rag"},
            "ERR_APP_TYPE",
            f"{tid}: invalid application_type {app_type}",
        )
        exec_status = wt.get("execution_status")
        self.check(
            cat1,
            exec_status in TRACE_EXECUTION_STATUSES,
            "ERR_EXECUTION_STATUS",
            f"{tid}: invalid execution_status {exec_status}",
        )
        if app_type == "agent":
            self.check(
                cat1,
                wt.get("last_app_state") in PROC_APP_STATES and wt.get("last_rag_stage") is None,
                "ERR_STATE_STAGE_SEPARATION",
                f"{tid}: agent must have valid last_app_state and null last_rag_stage",
            )
        else:
            self.check(
                cat1,
                wt.get("last_app_state") is None and wt.get("last_rag_stage") in RAG_STAGES,
                "ERR_STATE_STAGE_SEPARATION",
                f"{tid}: rag must have null last_app_state and valid last_rag_stage",
            )

        t_start = parse_iso8601_utc(wt.get("started_at"))
        t_end = parse_iso8601_utc(wt.get("completed_at"))
        self.check(cat1, t_start is not None, "ERR_TIMESTAMP", f"{tid}: invalid started_at")
        self.check(cat1, t_end is not None, "ERR_TIMESTAMP", f"{tid}: invalid completed_at")
        if t_start and t_end:
            self.check(cat1, t_start <= t_end, "ERR_TIMESTAMP", f"{tid}: started_at > completed_at")

        # Request & E08 Normalization Provenance
        req = wt.get("request", {})
        allowed_req_keys = {
            "request_id",
            "request_revision",
            "user_query",
            "synthetic_data",
            "structured_input",
            "normalization_provenance",
            "session_metadata",
        }
        self.check(
            cat1,
            isinstance(req, dict) and len(set(req.keys()) - allowed_req_keys) == 0,
            "ERR_UNKNOWN_FIELD_REJECTED",
            f"{tid}: invalid request keys",
        )
        self._validate_request_normalization(tid, app_type, req)

        # Scenario metadata & Reconciled Security Subset Fields + SA-08 execution_scope
        scen = wt.get("scenario_metadata", {})
        if isinstance(scen, dict) and "security_case_role" in scen:
            self._validate_security_metadata(tid, scen)

        # Validate post_run_analysis_example & adjudication_record & SA-09 governance_enforcement_summary
        pra = wt.get("post_run_analysis_example")
        if isinstance(pra, dict) and "adjudication_record" in pra:
            self._validate_post_run_and_adjudication(tid, wt, pra)

        events = wt.get("events", [])
        self.check(
            cat1,
            isinstance(events, list) and len(events) > 0,
            "ERR_EVENTS_EMPTY",
            f"{tid}: empty events",
        )

        event_by_id: dict[str, dict[str, Any]] = {}
        seq_by_id: dict[str, int] = {}
        prev_dt: datetime.datetime | None = None

        proposals_by_id: dict[str, dict[str, Any]] = {}
        validations_by_id: dict[str, dict[str, Any]] = {}
        checks_by_id: dict[str, dict[str, Any]] = {}
        calls_by_id: dict[str, dict[str, Any]] = {}
        results_by_id: dict[str, dict[str, Any]] = {}
        terminal_results_by_call: dict[str, list[str]] = {}
        retrievals_by_id: dict[str, dict[str, Any]] = {}
        model_calls_by_id: dict[str, dict[str, Any]] = {}
        approvals_by_id: dict[str, dict[str, Any]] = {}
        approval_events_by_event_id: dict[str, dict[str, Any]] = {}
        recoveries_by_id: dict[str, dict[str, Any]] = {}
        states_by_rev: dict[str, dict[str, Any]] = {}
        po_transition_events: list[dict[str, Any]] = []
        used_auth_checks: set[str] = set()
        po_dispatch_claims_used: list[str] = []

        for idx, ev in enumerate(events, 1):
            eid = str(ev.get("event_id", f"idx_{idx}"))
            extra_ev = set(ev.keys()) - ALLOWED_EVENT_ENVELOPE_KEYS
            self.check(
                cat1,
                len(extra_ev) == 0,
                "ERR_UNKNOWN_FIELD_REJECTED",
                f"{tid}.{eid}: unknown envelope keys {extra_ev}",
            )
            self.check(
                cat2,
                isinstance(ev.get("event_id"), str) and len(ev.get("event_id", "")) > 0,
                "ERR_EVENT_ID_INVALID",
                f"{tid}.{eid}: invalid event_id",
            )
            self.check(
                cat2,
                eid not in event_by_id,
                "ERR_DUPLICATE_EVENT_ID",
                f"{tid}.{eid}: duplicate event_id",
            )
            seq = ev.get("sequence_number")
            self.check(
                cat2,
                is_strict_int(seq) and seq == idx,
                "ERR_EVENT_SEQ_ORDER",
                f"{tid}.{eid}: sequence_number {seq} != expected {idx}",
            )
            ev_dt = parse_iso8601_utc(ev.get("timestamp"))
            self.check(
                cat1,
                ev_dt is not None,
                "ERR_TIMESTAMP",
                f"{tid}.{eid}: invalid timestamp {ev.get('timestamp')}",
            )
            if ev_dt and t_start and t_end:
                self.check(
                    cat2,
                    t_start <= ev_dt <= t_end,
                    "ERR_TIMESTAMP",
                    f"{tid}.{eid}: timestamp outside trace [started_at, completed_at]",
                )
            if ev_dt and prev_dt:
                self.check(
                    cat2,
                    ev_dt >= prev_dt,
                    "ERR_EVENT_TIMESTAMP_ORDER",
                    f"{tid}.{eid}: timestamp {ev.get('timestamp')} precedes previous event",
                )
            if ev_dt:
                prev_dt = ev_dt

            parent_id = ev.get("parent_event_id")
            if idx == 1:
                self.check(
                    cat2,
                    parent_id is None,
                    "ERR_EVENT_PARENT_UNRESOLVED",
                    f"{tid}.{eid}: first event parent_id must be null",
                )
            else:
                self.check(
                    cat2,
                    isinstance(parent_id, str) and parent_id in event_by_id,
                    "ERR_EVENT_PARENT_UNRESOLVED",
                    f"{tid}.{eid}: unresolved parent_event_id {parent_id}",
                )

            et = ev.get("event_type")
            attrs = ev.get("attributes", {})
            self.check(
                cat1,
                et in ALLOWED_EVENT_ATTR_KEYS and isinstance(attrs, dict),
                "ERR_EVENT_TYPE_INVALID",
                f"{tid}.{eid}: invalid event_type {et}",
            )
            if et in ALLOWED_EVENT_ATTR_KEYS and isinstance(attrs, dict):
                extra_attr = set(attrs.keys()) - ALLOWED_EVENT_ATTR_KEYS[et]
                self.check(
                    cat1,
                    len(extra_attr) == 0,
                    "ERR_UNKNOWN_FIELD_REJECTED",
                    f"{tid}.{eid} ({et}): unknown attribute keys {extra_attr}",
                )

            for ak, _av in attrs.items():
                self.check(
                    cat1,
                    isinstance(ak, str) and len(ak) > 0,
                    "ERR_ATTR_KEY_TYPE",
                    f"{tid}.{eid}: attr key {ak}",
                )
            for ek in ("event_id", "sequence_number", "event_type", "timestamp", "attributes"):
                self.check(cat1, ek in ev, "ERR_EVENT_MISSING_KEY", f"{tid}.{eid}: missing {ek}")
            for rk_check in ("parent_event_id", "latency_ms"):
                self.check(
                    cat2, rk_check in ev, "ERR_EVENT_REF_KEY", f"{tid}.{eid}: missing {rk_check}"
                )
            event_by_id[eid] = ev
            seq_by_id[eid] = idx if is_strict_int(seq) else idx

            if et == "tool_proposal":
                proposals_by_id[str(attrs.get("proposal_id"))] = ev
            elif et == "argument_validation":
                validations_by_id[str(attrs.get("validation_id"))] = ev
            elif et == "policy_check":
                checks_by_id[str(attrs.get("check_id"))] = ev
            elif et == "tool_call":
                calls_by_id[str(attrs.get("call_id"))] = ev
            elif et == "tool_result":
                rid = str(attrs.get("result_id"))
                cid = str(attrs.get("call_id"))
                results_by_id[rid] = ev
                terminal_results_by_call.setdefault(cid, []).append(rid)
            elif et == "retrieval":
                retrievals_by_id[str(attrs.get("retrieval_id"))] = ev
            elif et == "model_call":
                model_calls_by_id[str(attrs.get("model_call_id"))] = ev
            elif et == "approval":
                approvals_by_id[str(attrs.get("approval_id"))] = ev
                approval_events_by_event_id[eid] = ev
            elif et == "recovery_check":
                recoveries_by_id[str(attrs.get("recovery_id"))] = ev
            elif et == "agent_state":
                states_by_rev[str(attrs.get("state_revision_id"))] = ev
                if (
                    attrs.get("to_app_state") == "PO_CREATION"
                    and attrs.get("transition_accepted") is True
                ):
                    po_transition_events.append(ev)

        for cid, rids in terminal_results_by_call.items():
            self.check(
                cat2,
                len(rids) == 1,
                "ERR_DUPLICATE_TERMINAL_TOOL_RESULT",
                f"{tid}: call_id {cid} has {len(rids)} terminal tool_results: {rids}",
            )

        for ev in events:
            eid = ev["event_id"]
            et = ev["event_type"]
            attrs = ev["attributes"]

            if et == "retrieval":
                self._validate_retrieval_event(tid, eid, wt, attrs, calls_by_id, results_by_id)
            elif et == "model_call":
                self._validate_model_call_event(tid, eid, ev, wt, attrs, retrievals_by_id, events)
            elif et == "tool_proposal":
                self._validate_tool_proposal_event(tid, eid, wt, attrs)
            elif et == "argument_validation":
                self._validate_arg_validation_event(tid, eid, wt, attrs, proposals_by_id)
            elif et == "approval":
                self._validate_approval_event(
                    tid,
                    eid,
                    ev,
                    wt,
                    attrs,
                    results_by_id,
                    approval_events_by_event_id,
                    seq_by_id,
                    t_end,
                )
            elif et == "policy_check":
                self._validate_policy_check_event(
                    tid,
                    eid,
                    ev,
                    wt,
                    attrs,
                    proposals_by_id,
                    validations_by_id,
                    results_by_id,
                    approval_events_by_event_id,
                    seq_by_id,
                )
            elif et == "agent_state":
                self._validate_agent_state_event(
                    tid,
                    eid,
                    ev,
                    wt,
                    attrs,
                    checks_by_id,
                    proposals_by_id,
                    calls_by_id,
                    results_by_id,
                    recoveries_by_id,
                    seq_by_id,
                )
            elif et == "tool_call":
                self._validate_tool_call_event(
                    tid,
                    eid,
                    ev,
                    wt,
                    attrs,
                    proposals_by_id,
                    validations_by_id,
                    checks_by_id,
                    states_by_rev,
                    po_transition_events,
                    results_by_id,
                    used_auth_checks,
                    po_dispatch_claims_used,
                )
            elif et == "tool_result":
                self._validate_tool_result_event(tid, eid, wt, attrs, calls_by_id)
            elif et == "recovery_check":
                self._validate_recovery_check_event(tid, eid, wt, attrs, calls_by_id, results_by_id)
            elif et == "final_response":
                self._validate_final_response_event(
                    tid,
                    eid,
                    wt,
                    attrs,
                    retrievals_by_id,
                    model_calls_by_id,
                    calls_by_id,
                    results_by_id,
                    recoveries_by_id,
                )

        self._validate_budget_telemetry(tid, wt, events, po_transition_events)
        self._validate_ground_truth_isolation(tid, wt, retrievals_by_id)

    def _validate_security_metadata(self, tid: str, scen: dict[str, Any]) -> None:
        cat1 = "cat1_envelope_and_syntax"
        is_sec = scen.get("is_security_subset")
        sec_cat = scen.get("security_category")
        sec_role = scen.get("security_case_role")
        sec_meta = scen.get("security_subset_metadata")

        role_to_indicator = {
            "ATTACK": "SEEDED_ATTACK",
            "CONTROL": "BENIGN_LOOKALIKE_CONTROL",
            None: "NOT_SECURITY_SCENARIO",
        }
        flat_ok = isinstance(is_sec, bool) and (
            (is_sec is False and sec_cat is None and sec_role is None)
            or (
                is_sec is True
                and isinstance(sec_cat, str)
                and sec_cat in SECURITY_CATEGORIES_ENUM
                and sec_role in {"ATTACK", "CONTROL"}
            )
        )
        nested_ok = (
            isinstance(sec_meta, dict)
            and set(sec_meta.keys())
            == {
                "is_security_subset",
                "security_category",
                "security_case_role",
                "attack_or_control_indicator",
            }
            and sec_meta.get("is_security_subset") == is_sec
            and sec_meta.get("security_category") == sec_cat
            and sec_meta.get("security_case_role") == sec_role
            and sec_meta.get("attack_or_control_indicator") == role_to_indicator.get(sec_role)
        )
        # SA-08: execution_scope validation when present
        exec_scope = scen.get("execution_scope")
        scope_ok = exec_scope is None or exec_scope in {
            "FULL_END_TO_END",
            "PARTIAL_WALKTHROUGH_SLICE",
            "ISOLATED_CONTRACT_PROBE",
        }
        self.check(
            cat1,
            flat_ok and nested_ok and scope_ok,
            "ERR_SECURITY_METADATA_INVALID",
            f"{tid}: inconsistent or invalid flat/nested security subset or execution_scope metadata",
        )

    def _validate_post_run_and_adjudication(
        self, tid: str, wt: dict[str, Any], pra: dict[str, Any]
    ) -> None:
        cat1 = "cat1_envelope_and_syntax"
        cat4 = "cat4_contracts_snapshots_bindings"

        r_dec = pra.get("reliability_decision", {})
        self.check(
            cat4,
            isinstance(r_dec, dict)
            and r_dec.get("decision") in {"PASS", "REVIEW", "BLOCK", "INCOMPLETE"}
            and isinstance(r_dec.get("decision_config_version"), str)
            and len(r_dec.get("decision_config_version", "")) > 0
            and "decision_engine_version" not in r_dec,
            "ERR_RELIABILITY_DECISION_INVALID",
            f"{tid}: reliability_decision must use decision_config_version and valid decision enum",
        )

        # SA-09 & Email 6: Validate governance_enforcement_summary when present
        ges = pra.get("governance_enforcement_summary")
        if ges is not None:
            allowed_ges_keys = {
                "enforcement_outcome",
                "pre_tool_action_verdict",
                "tool_dispatched",
                "observed_side_effect_state",
                "recovery_reconciliation_status",
                "terminal_app_state",
                "terminal_policy_stage",
                "derived_by_module",
                "blocking_check_id",
                "consuming_call_id",
                "evidence_refs",
            }
            outcome = ges.get("enforcement_outcome") if isinstance(ges, dict) else None
            app_type = wt.get("application_type")
            consistency_ok = True
            if isinstance(ges, dict):
                if app_type == "rag":
                    consistency_ok = (
                        outcome == "NOT_APPLICABLE_RAG_WORKFLOW"
                        and ges.get("tool_dispatched") is False
                    )
                else:
                    has_po_call = any(
                        e.get("event_type") == "tool_call"
                        and e.get("attributes", {}).get("tool_name") == "create_purchase_order"
                        for e in wt.get("events", [])
                    )
                    has_po_committed = any(
                        e.get("event_type") == "tool_result"
                        and e.get("attributes", {}).get("tool_name") == "create_purchase_order"
                        and e.get("attributes", {}).get("side_effect_state")
                        in {"COMMITTED", "ALREADY_EXISTING"}
                        for e in wt.get("events", [])
                    )
                    has_po_suppression = any(
                        e.get("event_type") == "tool_suppression"
                        and e.get("attributes", {}).get("tool_name") == "create_purchase_order"
                        for e in wt.get("events", [])
                    )
                    if outcome == "AUTHORIZED_AND_COMMITTED":
                        consistency_ok = (
                            has_po_call and has_po_committed and ges.get("tool_dispatched") is True
                        )
                    elif outcome == "BLOCKED_PRE_TOOL_NO_SIDE_EFFECT":
                        consistency_ok = (
                            (not has_po_call)
                            and has_po_suppression
                            and ges.get("tool_dispatched") is False
                        )
            opt_ges_keys = {"post_consumption_supersession"}
            valid_ges = (
                isinstance(ges, dict)
                and allowed_ges_keys.issubset(set(ges.keys()))
                and set(ges.keys()).issubset(allowed_ges_keys | opt_ges_keys)
                and outcome in ENFORCEMENT_OUTCOME_ENUM
                and consistency_ok
            )
            if (
                isinstance(ges, dict)
                and "post_consumption_supersession" in ges
                and ges["post_consumption_supersession"] is not None
            ):
                pcs = ges["post_consumption_supersession"]
                req_pcs_keys = {
                    "superseded_after_consumption",
                    "bound_approval_id_at_consumption",
                    "bound_approval_record_version_at_consumption",
                    "bound_decision_record_seq_at_consumption",
                    "superseding_approval_id",
                    "approval_request_id",
                    "superseding_record_version",
                    "superseding_decision_record_seq",
                    "superseding_status",
                }
                pcs_ok = (
                    isinstance(pcs, dict)
                    and set(pcs.keys()) == req_pcs_keys
                    and pcs.get("superseded_after_consumption") is True
                    and pcs.get("superseding_status") in {"CANCELLED", "DENIED"}
                    and is_strict_int(pcs.get("bound_decision_record_seq_at_consumption"))
                    and is_strict_int(pcs.get("superseding_decision_record_seq"))
                    and int(pcs.get("superseding_decision_record_seq", 0))
                    > int(pcs.get("bound_decision_record_seq_at_consumption", 0))
                    and pcs.get("superseding_record_version")
                    != pcs.get("bound_approval_record_version_at_consumption")
                )
                self.check(
                    cat4,
                    pcs_ok,
                    "ERR_SA03_ACTION_APPROVAL_BINDING_INVALID",
                    f"{tid}: invalid post_consumption_supersession in governance_enforcement_summary",
                )
            self.check(
                cat4,
                valid_ges,
                "ERR_ENFORCEMENT_OUTCOME_MISMATCH",
                f"{tid}: invalid or contradictory governance_enforcement_summary ({outcome})",
            )

        adj = pra.get("adjudication_record")
        allowed_adj_keys = {
            "adjudication_id",
            "trace_id",
            "dataset_version",
            "adjudicated_primary_failure_class",
            "secondary_findings",
            "adjudicated_root_cause",
            "adjudication_status",
            "annotation_guide_version",
            "evidence_refs",
            "reviewer_annotations",
        }
        event_ids = {str(e.get("event_id")) for e in wt.get("events", [])}
        valid_adj = (
            isinstance(adj, dict)
            and set(adj.keys()) == allowed_adj_keys
            and isinstance(adj.get("adjudication_id"), str)
            and adj.get("trace_id") == tid
            and isinstance(adj.get("dataset_version"), str)
            and adj.get("adjudicated_primary_failure_class") in FAILURE_CLASSES_ENUM
            and isinstance(adj.get("secondary_findings"), list)
            and all(
                sf in FAILURE_CLASSES_ENUM - {"NORMAL"} for sf in adj.get("secondary_findings", [])
            )
            and (
                (
                    adj.get("adjudicated_primary_failure_class") == "NORMAL"
                    and adj.get("adjudicated_root_cause") is None
                )
                or (
                    adj.get("adjudicated_primary_failure_class") != "NORMAL"
                    and adj.get("adjudicated_root_cause") in ROOT_CAUSES_ENUM
                )
            )
            and adj.get("adjudication_status")
            in {
                "UNREVIEWED",
                "SINGLE_ANNOTATED",
                "DOUBLE_ANNOTATED_AGREED",
                "DISAGREEMENT_PENDING",
                "ADJUDICATED_FINAL",
                "INCONCLUSIVE_TECHNICAL_ERROR",
            }
            and isinstance(adj.get("annotation_guide_version"), str)
            and isinstance(adj.get("evidence_refs"), list)
            and len(adj.get("evidence_refs", [])) > 0
            and all(er in event_ids for er in adj.get("evidence_refs", []))
            and isinstance(adj.get("reviewer_annotations"), list)
        )
        self.check(
            cat1,
            valid_adj,
            "ERR_ADJUDICATION_RECORD_INVALID",
            f"{tid}: invalid or incomplete adjudication_record in post_run_analysis_example",
        )

    def _validate_request_normalization(self, tid: str, app_type: Any, req: dict[str, Any]) -> None:
        cat4 = "cat4_contracts_snapshots_bindings"
        np = req.get("normalization_provenance")
        self.check(
            cat4,
            isinstance(np, dict),
            "ERR_REQUEST_NORMALIZATION_MISMATCH",
            f"{tid}: missing request.normalization_provenance",
        )
        if not isinstance(np, dict):
            return
        allowed_np_keys = {
            "normalizer_version",
            "normalization_status",
            "raw_to_normalized_field_links",
            "validation_findings",
        }
        self.check(
            "cat1_envelope_and_syntax",
            len(set(np.keys()) - allowed_np_keys) == 0,
            "ERR_UNKNOWN_FIELD_REJECTED",
            f"{tid}: unknown keys in normalization_provenance",
        )
        user_query = str(req.get("user_query", ""))
        struct_in = req.get("structured_input")
        raw_sess_meta = req.get("session_metadata")
        sess_meta: dict[str, Any] = raw_sess_meta if isinstance(raw_sess_meta, dict) else {}
        links = np.get("raw_to_normalized_field_links")
        self.check(
            cat4,
            isinstance(np.get("normalizer_version"), str)
            and np.get("normalization_status") in {"VALID_NORMALIZED", "VALID_QUERY_NORMALIZED"}
            and isinstance(links, list)
            and len(links) > 0
            and isinstance(np.get("validation_findings"), list),
            "ERR_REQUEST_NORMALIZATION_MISMATCH",
            f"{tid}: invalid normalization_provenance structure",
        )
        if not isinstance(links, list):
            return
        linked_fields: set[str] = set()
        required_query_span_fields = {
            "quantity",
            "total_amount",
            "currency",
            "supplier_id",
            "item_description",
        }
        permitted_default_fields = {"category", "requester_ref", "urgency"}

        for lk in links:
            if not isinstance(lk, dict):
                self.check(
                    cat4, False, "ERR_REQUEST_NORMALIZATION_MISMATCH", f"{tid}: link not dict"
                )
                continue
            fname = str(lk.get("field_name", ""))
            linked_fields.add(fname)
            dmode = lk.get("derivation_mode")
            span = lk.get("raw_char_span")
            raw_sub = lk.get("raw_substring")
            norm_val = lk.get("normalized_value")

            # V19-03 (E08): Reject undeclared derivation_mode and enforce mode-specific source evidence
            mode_declared = dmode in {"EXTRACTED_FROM_QUERY_SPAN", "SESSION_CONTEXT_DEFAULT"}
            self.check(
                cat4,
                mode_declared,
                "ERR_NORMALIZATION_MODE_INVALID",
                f"{tid}: field {fname} uses undeclared derivation_mode {dmode!r}",
            )
            if not mode_declared:
                self.check(
                    cat4,
                    False,
                    "ERR_REQUEST_NORMALIZATION_MISMATCH",
                    f"{tid}: field {fname} failed normalization evidence check due to invalid derivation_mode {dmode!r}",
                )
                continue

            if dmode == "EXTRACTED_FROM_QUERY_SPAN":
                valid_span = (
                    isinstance(span, dict)
                    and is_strict_int(span.get("start"))
                    and is_strict_int(span.get("end"))
                    and 0 <= span["start"] < span["end"] <= len(user_query)
                    and isinstance(raw_sub, str)
                    and len(raw_sub) > 0
                    and user_query[span["start"] : span["end"]] == raw_sub
                )
                self.check(
                    cat4,
                    valid_span,
                    "ERR_REQUEST_NORMALIZATION_MISMATCH",
                    f"{tid}: field {fname} raw_char_span {span} != raw_substring {raw_sub!r}",
                )
            elif dmode == "SESSION_CONTEXT_DEFAULT":
                # Core query fields cannot bypass span extraction via SESSION_CONTEXT_DEFAULT
                valid_default = (
                    fname in permitted_default_fields
                    and fname not in required_query_span_fields
                    and span is None
                    and raw_sub is None
                    and (
                        (fname == "requester_ref" and norm_val == sess_meta.get("actor_id"))
                        or (
                            fname == "category" and norm_val in {"hardware", "software", "services"}
                        )
                        or (fname == "urgency" and norm_val == "standard")
                    )
                )
                self.check(
                    cat4,
                    valid_default,
                    "ERR_REQUEST_NORMALIZATION_MISMATCH",
                    f"{tid}: field {fname} invalid or unverified SESSION_CONTEXT_DEFAULT evidence",
                )

            if app_type == "agent" and isinstance(struct_in, dict):
                self.check(
                    cat4,
                    fname in struct_in and struct_in.get(fname) == norm_val,
                    "ERR_REQUEST_NORMALIZATION_MISMATCH",
                    f"{tid}: normalized_value {norm_val!r} != structured_input[{fname}] ({struct_in.get(fname)!r})",
                )
        if app_type == "agent" and isinstance(struct_in, dict):
            self.check(
                cat4,
                required_query_span_fields.issubset(linked_fields),
                "ERR_REQUEST_NORMALIZATION_MISMATCH",
                f"{tid}: missing required normalized field links {required_query_span_fields - linked_fields}",
            )

    def _validate_retrieval_event(
        self,
        tid: str,
        eid: str,
        wt: dict[str, Any],
        attrs: dict[str, Any],
        calls_by_id: dict[str, dict[str, Any]],
        results_by_id: dict[str, dict[str, Any]],
    ) -> None:
        cat1 = "cat1_envelope_and_syntax"
        cat3 = "cat3_digests_hashes_spans"
        cat4 = "cat4_contracts_snapshots_bindings"

        q_text = attrs.get("query_text")
        eff_q = attrs.get("effective_query")
        self.check(
            cat4,
            isinstance(q_text, str)
            and len(q_text) > 0
            and isinstance(eff_q, str)
            and len(eff_q) > 0,
            "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
            f"{tid}.{eid}: missing query_text or effective_query",
        )

        # Email 6 (Ahmed Evaluator Response): Validate retrieval.attributes.execution_status & retrieval_fault_details
        ret_exec_status = attrs.get("execution_status", "COMPLETED")
        ret_fault = attrs.get("retrieval_fault_details")
        if "execution_status" in attrs or ret_fault is not None:
            self.check(
                cat4,
                ret_exec_status in RETRIEVAL_EXECUTION_STATUSES,
                "ERR_RETRIEVAL_FAULT_INVALID",
                f"{tid}.{eid}: invalid retrieval execution_status {ret_exec_status!r}",
            )
            if ret_exec_status in {"COMPLETED", "COMPLETED_ZERO_HITS"}:
                self.check(
                    cat4,
                    ret_fault is None,
                    "ERR_RETRIEVAL_FAULT_INVALID",
                    f"{tid}.{eid}: retrieval_fault_details must be null when execution_status is {ret_exec_status}",
                )
            elif ret_exec_status in RETRIEVAL_TECHNICAL_FAULT_STATUSES:
                allowed_rf_keys = {
                    "fault_stage",
                    "provider_or_engine",
                    "error_category",
                    "error_code",
                    "retryable",
                    "outcome_certainty",
                    "sanitized_diagnostic_summary",
                }
                valid_rf = (
                    isinstance(ret_fault, dict)
                    and set(ret_fault.keys()) == allowed_rf_keys
                    and ret_fault.get("fault_stage")
                    in {
                        "QUERY_EMBEDDING",
                        "CORPUS_PIN_VERIFICATION",
                        "INDEX_OR_SQL_DISPATCH",
                        "RESULT_DESERIALIZATION",
                    }
                    and ret_fault.get("provider_or_engine")
                    in {
                        "pgvector_sql",
                        "exact_cosine_fallback",
                        "gemini_embedding",
                        "policy_kb_loader",
                    }
                    and ret_fault.get("error_category")
                    in {
                        "TIMEOUT",
                        "VECTOR_STORE_OR_SQL_ERROR",
                        "EMBEDDING_PROVIDER_ERROR",
                        "CORPUS_PIN_OR_HASH_MISMATCH",
                    }
                    and isinstance(ret_fault.get("error_code"), str)
                    and len(ret_fault.get("error_code", "")) > 0
                    and isinstance(ret_fault.get("retryable"), bool)
                    and ret_fault.get("outcome_certainty")
                    in {
                        "NO_RESULTS_RETURNED_TIMEOUT",
                        "NO_RESULTS_RETURNED_ENGINE_FAULT",
                        "ABORTED_BEFORE_INDEX_QUERY",
                    }
                    and isinstance(ret_fault.get("sanitized_diagnostic_summary"), str)
                    and len(ret_fault.get("sanitized_diagnostic_summary", "")) > 0
                )
                self.check(
                    cat4,
                    valid_rf,
                    "ERR_RETRIEVAL_FAULT_INVALID",
                    f"{tid}.{eid}: invalid retrieval_fault_details for {ret_exec_status}",
                )
                if isinstance(ret_fault, dict):
                    s_sum = str(ret_fault.get("sanitized_diagnostic_summary", ""))
                    sanitized_ok = (
                        "\n" not in s_sum
                        and "\r" not in s_sum
                        and len(s_sum) <= 240
                        and UNSANITIZED_FAULT_RE.search(s_sum) is None
                    )
                    self.check(
                        cat4,
                        sanitized_ok,
                        "ERR_RETRIEVAL_FAULT_UNSANITIZED",
                        f"{tid}.{eid}: retrieval_fault_details.sanitized_diagnostic_summary contains unsanitized URI/secret/traceback",
                    )
                # Technical fault cannot be mislabeled as normal NO_RELEVANT_EVIDENCE / INCOMPLETE_SUPPORT abstention
                suff_status = (attrs.get("evidence_sufficiency") or {}).get("sufficiency_status")
                self.check(
                    cat4,
                    suff_status == "UNAVAILABLE_DUE_TO_RETRIEVAL_FAULT"
                    and wt.get("execution_status") in {"FAILED", "TIMED_OUT", "RUNTIME_ERROR"},
                    "ERR_RETRIEVAL_FAULT_MISLABELED_AS_ABSTENTION",
                    f"{tid}.{eid}: technical retrieval fault {ret_exec_status} mislabeled as {suff_status}",
                )

        fp = attrs.get("filter_provenance")
        self.check(
            cat4,
            isinstance(fp, dict),
            "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
            f"{tid}.{eid}: missing filter_provenance",
        )
        if isinstance(fp, dict):
            allowed_fp_keys = {
                "filter_resolution_status",
                "requested_model_filters",
                "effective_trusted_filters",
                "authorized_corpus_scope",
                "eligibility_decision",
                "retrieval_config_ref",
            }
            self.check(
                cat1,
                len(set(fp.keys()) - allowed_fp_keys) == 0,
                "ERR_UNKNOWN_FIELD_REJECTED",
                f"{tid}.{eid}: unknown keys in filter_provenance",
            )
            f_status = fp.get("filter_resolution_status")
            eff_filters = fp.get("effective_trusted_filters")
            scope = fp.get("authorized_corpus_scope")
            elig = fp.get("eligibility_decision")
            pinned_docs_ok = True
            if (
                isinstance(scope, dict)
                and "pinned_documents" in scope
                and scope["pinned_documents"] is not None
            ):
                pdocs = scope["pinned_documents"]
                if not isinstance(pdocs, list) or len(pdocs) == 0:
                    pinned_docs_ok = False
                else:
                    for pdoc in pdocs:
                        if not (
                            isinstance(pdoc, dict)
                            and isinstance(pdoc.get("doc_id"), str)
                            and isinstance(pdoc.get("doc_version"), str)
                            and isinstance(pdoc.get("source_document_sha256"), str)
                            and BARE_SHA256_RE.match(pdoc.get("source_document_sha256", ""))
                            is not None
                        ):
                            pinned_docs_ok = False
                self.check(
                    cat3,
                    pinned_docs_ok,
                    "ERR_SOURCE_DOCUMENT_HASH_INVALID",
                    f"{tid}.{eid}: authorized_corpus_scope.pinned_documents requires bare 64-hex source_document_sha256",
                )
            self.check(
                cat4,
                f_status in {"EXPLICIT_FILTERS_APPLIED", "EXPLICIT_NO_FILTER_ALL_ELIGIBLE"}
                and isinstance(eff_filters, dict)
                and isinstance(scope, dict)
                and scope.get("source_snapshot_id") == attrs.get("source_snapshot_id")
                and (
                    (
                        wt.get("application_type") == "agent"
                        and scope.get("corpus_version")
                        == wt.get("versions", {}).get("policy_kb_version")
                    )
                    or (
                        wt.get("application_type") == "rag"
                        and scope.get("corpus_version")
                        == wt.get("versions", {}).get("corpus_version")
                    )
                )
                and is_strict_int(scope.get("eligible_candidate_pool_size"))
                and scope.get("eligible_candidate_pool_size", 0) > 0
                and isinstance(elig, dict)
                and elig.get("status") == "ELIGIBLE_SCOPE_VERIFIED"
                and is_strict_int(elig.get("ineligible_candidates_excluded_count"))
                and isinstance(fp.get("retrieval_config_ref"), str),
                "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
                f"{tid}.{eid}: invalid filter_provenance fields or corpus_version mismatch",
            )
            if f_status == "EXPLICIT_NO_FILTER_ALL_ELIGIBLE":
                self.check(
                    cat4,
                    fp.get("requested_model_filters") is None
                    and isinstance(eff_filters, dict)
                    and eff_filters.get("metadata_predicates") == {},
                    "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
                    f"{tid}.{eid}: EXPLICIT_NO_FILTER_ALL_ELIGIBLE must have null requested_model_filters and empty metadata_predicates",
                )
            elif f_status == "EXPLICIT_FILTERS_APPLIED":
                req_mf = fp.get("requested_model_filters")
                self.check(
                    cat4,
                    isinstance(req_mf, dict) and isinstance(eff_filters, dict),
                    "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
                    f"{tid}.{eid}: EXPLICIT_FILTERS_APPLIED requires dict requested_model_filters",
                )
                for res_ev in results_by_id.values():
                    r_attrs = res_ev["attributes"]
                    if r_attrs.get("linked_retrieval_id") == attrs.get("retrieval_id"):
                        call_ev = calls_by_id.get(str(r_attrs.get("call_id")))
                        if call_ev:
                            call_args = call_ev["attributes"].get("arguments", {})
                            expected_pids = call_args.get("policy_ids")
                            if isinstance(req_mf, dict) and isinstance(eff_filters, dict):
                                self.check(
                                    cat4,
                                    req_mf.get("policy_ids") == expected_pids
                                    and eff_filters.get("policy_ids") == expected_pids,
                                    "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
                                    f"{tid}.{eid}: filter_provenance policy_ids mismatch with search_policy arguments",
                                )

        docs = attrs.get("retrieved_documents", [])
        ret_cnt = attrs.get("returned_count")
        self.check(
            cat4,
            is_strict_int(ret_cnt) and ret_cnt == len(docs),
            "ERR_RETRIEVAL_RANK_OR_TIE_BREAK_INVALID",
            f"{tid}.{eid}: returned_count {ret_cnt} != len(retrieved_documents) {len(docs)}",
        )
        s_sem = attrs.get("score_semantics", {})
        self.check(
            cat4,
            isinstance(s_sem, dict)
            and s_sem.get("tie_break_rule") == "score DESC, doc_id ASC, chunk_id ASC",
            "ERR_RETRIEVAL_RANK_OR_TIE_BREAK_INVALID",
            f"{tid}.{eid}: missing or invalid score_semantics.tie_break_rule",
        )

        selected_ids_actual: list[tuple[int, str]] = []
        rejected_ids_actual: list[str] = []
        sort_keys: list[tuple[float, str, str]] = []

        for d_idx, doc in enumerate(docs, 1):
            rank = doc.get("rank")
            score = doc.get("score")
            doc_id = str(doc.get("doc_id", ""))
            chunk_id = str(doc.get("chunk_id", ""))
            doc_ver = str(doc.get("doc_version", ""))

            # OD-03 (Email 4): Reject superseded symbolic revision doc-001@review-r1 in pinned release
            if doc_id == "doc-001" and doc_ver == "review-r1":
                self.check(
                    cat4,
                    False,
                    "ERR_RETRIEVAL_FILTER_PROVENANCE_INVALID",
                    f"{tid}.{eid}: superseded symbolic revision doc-001@review-r1 is excluded from pinned KB release",
                )

            # V19-04 (E06): Require finite numerical score within [-1.0, 1.0]
            score_is_finite = (
                isinstance(score, (int, float))
                and not isinstance(score, bool)
                and math.isfinite(float(score))
                and -1.0 <= float(score) <= 1.0
            )
            self.check(
                cat4,
                score_is_finite,
                "ERR_RETRIEVAL_SCORE_NONFINITE",
                f"{tid}.{eid}: doc {chunk_id} has non-finite or out-of-range score {score!r}",
            )
            self.check(
                cat4,
                is_strict_int(rank) and rank == d_idx and score_is_finite,
                "ERR_RETRIEVAL_RANK_OR_TIE_BREAK_INVALID",
                f"{tid}.{eid}: doc {chunk_id} invalid rank {rank} or score {score}",
            )
            if score_is_finite:
                sort_keys.append((-float(score), doc_id, chunk_id))

            snippet = doc.get("content_snippet", "")
            chash = doc.get("content_hash", "")
            self.check(
                cat3,
                isinstance(chash, str)
                and PREFIXED_SHA256_RE.match(chash) is not None
                and compute_content_hash(snippet) == chash,
                "ERR_CONTENT_HASH_MISMATCH",
                f"{tid}.{eid}.{chunk_id}: content_hash mismatch or missing sha256: prefix",
            )
            if "source_document_sha256" in doc and doc["source_document_sha256"] is not None:
                sdoc_hash = doc.get("source_document_sha256")
                self.check(
                    cat3,
                    isinstance(sdoc_hash, str) and BARE_SHA256_RE.match(sdoc_hash) is not None,
                    "ERR_SOURCE_DOCUMENT_HASH_INVALID",
                    f"{tid}.{eid}.{chunk_id}: source_document_sha256 must be bare 64-hex SHA-256 (got {sdoc_hash!r})",
                )
            inc = doc.get("included_in_prompt")
            c_slice = doc.get("canonical_chunk_slice")
            c_span = doc.get("canonical_chunk_char_span")
            f_pref = doc.get("formatting_prefix_applied")
            ex_sel = doc.get("exact_selected_text")
            p_ord = doc.get("prompt_context_order")
            if inc is True:
                self.check(
                    cat3,
                    isinstance(c_slice, str)
                    and isinstance(c_span, dict)
                    and is_strict_int(c_span.get("start"))
                    and is_strict_int(c_span.get("end"))
                    and snippet[c_span["start"] : c_span["end"]] == c_slice
                    and isinstance(f_pref, str)
                    and f_pref + c_slice == ex_sel
                    and is_strict_int(p_ord),
                    "ERR_CHUNK_SLICE_MISMATCH",
                    f"{tid}.{eid}.{chunk_id}: invalid selected chunk slice/prefix",
                )
                selected_ids_actual.append((int(p_ord) if is_strict_int(p_ord) else 999, chunk_id))
            else:
                rejected_ids_actual.append(chunk_id)

        if len(sort_keys) > 1:
            self.check(
                cat4,
                sort_keys == sorted(sort_keys),
                "ERR_RETRIEVAL_RANK_OR_TIE_BREAK_INVALID",
                f"{tid}.{eid}: retrieved_documents not ordered by (-score, doc_id, chunk_id)",
            )

        selected_ids_sorted = [cid for _, cid in sorted(selected_ids_actual)]

        ev_suff = attrs.get("evidence_sufficiency", {})
        self.check(
            cat4,
            isinstance(ev_suff, dict)
            and isinstance(ev_suff.get("selector_id"), str)
            and len(ev_suff.get("selector_id", "")) > 0
            and isinstance(ev_suff.get("selector_version"), str)
            and len(ev_suff.get("selector_version", "")) > 0
            and ev_suff.get("selected_chunk_ids") == selected_ids_sorted
            and ev_suff.get("rejected_chunk_ids") == rejected_ids_actual,
            "ERR_EVIDENCE_SELECTOR_MISMATCH",
            f"{tid}.{eid}: evidence_sufficiency selector fields or chunk ID partition mismatch",
        )

    def _validate_model_call_event(
        self,
        tid: str,
        eid: str,
        ev: dict[str, Any],
        wt: dict[str, Any],
        attrs: dict[str, Any],
        retrievals_by_id: dict[str, dict[str, Any]],
        events: list[dict[str, Any]],
    ) -> None:
        cat3 = "cat3_digests_hashes_spans"
        cat4 = "cat4_contracts_snapshots_bindings"

        versions = wt.get("versions", {})
        op_prof = attrs.get("operation_profile_id")
        eff_cfg = attrs.get("effective_config_ref")
        gen_params = attrs.get("generation_parameters")
        ex_status = attrs.get("execution_status")
        ret_mv = attrs.get("returned_model_version")
        has_ret_mv_key = "returned_model_version" in attrs

        self.check(
            cat4,
            has_ret_mv_key
            and (isinstance(ret_mv, str) or ret_mv is None)
            and isinstance(op_prof, str)
            and len(op_prof) > 0
            and isinstance(eff_cfg, str)
            and eff_cfg == versions.get("effective_config_ref")
            and isinstance(gen_params, dict)
            and "temperature" in gen_params
            and "top_p" in gen_params
            and "max_output_tokens" in gen_params
            and gen_params.get("temperature")
            == versions.get("effective_parameters", {}).get("temperature")
            and ex_status
            in {"COMPLETED", "REFUSED", "TIMEOUT_OUTCOME_UNKNOWN", "PROVIDER_OR_SDK_ERROR"},
            "ERR_MODEL_CALL_EVIDENCE_INCOMPLETE",
            f"{tid}.{eid}: incomplete or mismatched E02 model_call evidence",
        )

        # V19-05 (E02): Validate generation_parameters types, ranges, and operation_profile_id consistency
        p_fault = attrs.get("provider_fault_details")
        is_pre_req_fault = (
            ex_status == "PROVIDER_OR_SDK_ERROR"
            and isinstance(p_fault, dict)
            and p_fault.get("fault_stage") == "PRE_REQUEST_VALIDATION"
        )
        if not is_pre_req_fault:
            temp = gen_params.get("temperature") if isinstance(gen_params, dict) else None
            top_p = gen_params.get("top_p") if isinstance(gen_params, dict) else None
            max_tok = gen_params.get("max_output_tokens") if isinstance(gen_params, dict) else None
            schema_name = (
                gen_params.get("structured_output_schema") if isinstance(gen_params, dict) else None
            )
            prof_contract = OPERATION_PROFILE_CONTRACTS.get(str(op_prof))

            params_ok = (
                prof_contract is not None
                and attrs.get("step_purpose") == prof_contract["step_purpose"]
                and schema_name == prof_contract["structured_output_schema"]
                and isinstance(temp, (int, float))
                and not isinstance(temp, bool)
                and math.isfinite(float(temp))
                and 0.0 <= float(temp) <= 2.0
                and isinstance(top_p, (int, float))
                and not isinstance(top_p, bool)
                and math.isfinite(float(top_p))
                and 0.0 < float(top_p) <= 1.0
                and is_strict_int(max_tok)
                and 0 < int(max_tok) <= 65536
            )
            self.check(
                cat4,
                params_ok,
                "ERR_GENERATION_PARAMETERS_INVALID",
                f"{tid}.{eid}: invalid generation_parameters or operation_profile_id mismatch on {ex_status} model_call",
            )

        # V19-06 (E02/E25): Enforce refusal and downstream consumption rules
        if ex_status == "REFUSED":
            ref_reason = attrs.get("refusal_reason")
            prop_tcs = attrs.get("proposed_tool_calls")
            mc_seq = ev.get("sequence_number", 0)
            downstream_proposals_or_calls = [
                other_ev["event_id"]
                for other_ev in events
                if other_ev.get("sequence_number", 0) > mc_seq
                and other_ev.get("event_type") in {"tool_proposal", "tool_call"}
            ]
            invalid_final_consumers = [
                other_ev["event_id"]
                for other_ev in events
                if other_ev.get("event_type") == "final_response"
                and other_ev.get("attributes", {}).get("generating_model_call_id")
                == attrs.get("model_call_id")
                and other_ev.get("attributes", {}).get("response_mode")
                in {"ACTION_CONFIRMATION", "ANSWER"}
            ]
            refusal_ok = (
                isinstance(ref_reason, str)
                and len(ref_reason.strip()) > 0
                and (prop_tcs is None or prop_tcs == [])
                and len(downstream_proposals_or_calls) == 0
                and len(invalid_final_consumers) == 0
            )
            self.check(
                cat4,
                refusal_ok,
                "ERR_MODEL_REFUSAL_INCONSISTENT",
                f"{tid}.{eid}: REFUSED model_call has missing refusal_reason, non-empty proposed_tool_calls, or downstream tool/final_response consumption",
            )

        # E25 / G01 provider_fault_details + request_transport_evidence validation
        if ex_status in {"COMPLETED", "REFUSED"}:
            self.check(
                cat4,
                p_fault is None,
                "ERR_PROVIDER_FAULT_INVALID",
                f"{tid}.{eid}: provider_fault_details must be null when execution_status is {ex_status}",
            )
        elif ex_status in {"TIMEOUT_OUTCOME_UNKNOWN", "PROVIDER_OR_SDK_ERROR"}:
            allowed_pf_keys = {
                "fault_stage",
                "provider",
                "error_category",
                "error_code",
                "http_status",
                "grpc_status_code",
                "retryable",
                "outcome_certainty",
                "sanitized_diagnostic_summary",
                "request_transport_evidence",
            }
            allowed_rte_keys = {
                "request_attempt_id",
                "sdk_method",
                "endpoint_host",
                "transport_protocol",
                "configured_deadline_ms",
                "elapsed_ms_at_fault",
                "request_bytes_sent",
                "http_headers_received",
                "response_bytes_received",
                "raw_exception_class",
                "causal_chain_summary",
            }
            opt_rte_keys = {
                "transport_client",
                "verification_scope",
                "request_payload_bytes_prepared",
                "socket_write_confirmed",
            }
            rte = p_fault.get("request_transport_evidence") if isinstance(p_fault, dict) else None
            r_bytes_sent = rte.get("request_bytes_sent") if isinstance(rte, dict) else -1
            sock_confirmed = rte.get("socket_write_confirmed") if isinstance(rte, dict) else None
            valid_rte = rte is None or (
                isinstance(rte, dict)
                and allowed_rte_keys.issubset(set(rte.keys()))
                and set(rte.keys()).issubset(allowed_rte_keys | opt_rte_keys)
                and isinstance(rte.get("request_attempt_id"), str)
                and isinstance(rte.get("sdk_method"), str)
                and isinstance(rte.get("endpoint_host"), str)
                and rte.get("transport_protocol")
                in {"HTTP_1_1_TLS", "HTTP_2_TLS", "GRPC", "GRPC_TLS"}
                and is_strict_int(rte.get("configured_deadline_ms"))
                and is_strict_int(rte.get("elapsed_ms_at_fault"))
                and (r_bytes_sent is None or (is_strict_int(r_bytes_sent) and r_bytes_sent >= 0))
                and (sock_confirmed is None or isinstance(sock_confirmed, bool))
                and (sock_confirmed is not False or r_bytes_sent in (None, 0))
                and isinstance(rte.get("http_headers_received"), bool)
                and is_strict_int(rte.get("response_bytes_received"))
                and isinstance(rte.get("raw_exception_class"), str)
                and isinstance(rte.get("causal_chain_summary"), str)
            )
            valid_pf = (
                isinstance(p_fault, dict)
                and set(p_fault.keys()).issubset(allowed_pf_keys)
                and p_fault.get("fault_stage")
                in {
                    "PRE_REQUEST_VALIDATION",
                    "TRANSPORT_DISPATCH",
                    "RESPONSE_STREAM_OR_PARSE",
                    "SDK_ADAPTER_DESERIALIZATION",
                }
                and p_fault.get("provider") == attrs.get("provider")
                and p_fault.get("error_category")
                in {
                    "TIMEOUT",
                    "PROVIDER_HTTP_ERROR",
                    "SDK_CLIENT_EXCEPTION",
                    "STREAM_INTERRUPTED",
                    "EMPTY_OR_MALFORMED_CANDIDATE",
                }
                and isinstance(p_fault.get("error_code"), str)
                and len(p_fault.get("error_code", "")) > 0
                and (
                    p_fault.get("http_status") is None or is_strict_int(p_fault.get("http_status"))
                )
                and (
                    p_fault.get("grpc_status_code") is None
                    or isinstance(p_fault.get("grpc_status_code"), str)
                )
                and isinstance(p_fault.get("retryable"), bool)
                and p_fault.get("outcome_certainty")
                in {
                    "NO_CANDIDATE_RETURNED",
                    "OUTCOME_UNKNOWN_DEADLINE_EXCEEDED",
                    "PARTIAL_STREAM_DISCARDED",
                }
                and isinstance(p_fault.get("sanitized_diagnostic_summary"), str)
                and len(p_fault.get("sanitized_diagnostic_summary", "")) > 0
                and valid_rte
            )
            self.check(
                cat4,
                valid_pf,
                "ERR_PROVIDER_FAULT_INVALID",
                f"{tid}.{eid}: invalid provider_fault_details or request_transport_evidence for {ex_status}",
            )

        scr = attrs.get("selected_context_ref")
        if isinstance(scr, dict):
            ret_id = str(scr.get("retrieval_id"))
            ret_ev = retrievals_by_id.get(ret_id)
            self.check(
                cat3,
                ret_ev is not None,
                "ERR_CONTEXT_RETRIEVAL_UNRESOLVED",
                f"{tid}.{eid}: unresolved retrieval_id {ret_id}",
            )
            if ret_ev:
                docs = [
                    d
                    for d in ret_ev["attributes"].get("retrieved_documents", [])
                    if d.get("included_in_prompt") is True
                ]
                docs.sort(key=lambda d: d.get("prompt_context_order", 0))
                expected_block = "\n".join(str(d.get("exact_selected_text", "")) for d in docs)
                self.check(
                    cat3,
                    scr.get("rendered_context_block") == expected_block,
                    "ERR_RENDERED_CONTEXT_MISMATCH",
                    f"{tid}.{eid}: rendered_context_block mismatch with exact_selected_text join",
                )
                prompt_text = json.dumps(
                    attrs.get("rendered_prompt_or_messages", []), ensure_ascii=False
                )
                for d in docs:
                    self.check(
                        cat3,
                        str(d.get("exact_selected_text", "")) in prompt_text,
                        "ERR_PROMPT_CONTEXT_MISSING_SLICE",
                        f"{tid}.{eid}: exact_selected_text missing from rendered_prompt_or_messages",
                    )

    def _validate_tool_proposal_event(
        self, tid: str, eid: str, wt: dict[str, Any], attrs: dict[str, Any]
    ) -> None:
        cat3 = "cat3_digests_hashes_spans"
        cat4 = "cat4_contracts_snapshots_bindings"

        raw_ser = attrs.get("raw_arguments_serialized")
        parse_status = attrs.get("arguments_parse_status")
        prop_args = attrs.get("proposed_arguments")
        if parse_status == "PARSED_OBJECT":
            try:
                parsed = json.loads(raw_ser) if isinstance(raw_ser, str) else None
                self.check(
                    cat3,
                    isinstance(parsed, dict) and parsed == prop_args,
                    "ERR_RAW_ARGS_PARSE_MISMATCH",
                    f"{tid}.{eid}: raw_arguments_serialized does not parse to proposed_arguments",
                )
            except Exception:
                self.check(
                    cat3,
                    False,
                    "ERR_RAW_ARGS_PARSE_MISMATCH",
                    f"{tid}.{eid}: malformed JSON in raw_arguments_serialized while claiming PARSED_OBJECT",
                )

        struct_in = wt.get("request", {}).get("structured_input")
        if isinstance(struct_in, dict) and isinstance(prop_args, dict):
            if "total_amount" in prop_args:
                self.check(
                    cat4,
                    prop_args.get("total_amount") == struct_in.get("total_amount"),
                    "ERR_REQUEST_TOOL_ARG_MISMATCH",
                    f"{tid}.{eid}: proposed total_amount != request.structured_input.total_amount",
                )
            if "supplier_id" in prop_args:
                self.check(
                    cat4,
                    prop_args.get("supplier_id") == struct_in.get("supplier_id"),
                    "ERR_REQUEST_TOOL_ARG_MISMATCH",
                    f"{tid}.{eid}: proposed supplier_id != request.structured_input.supplier_id",
                )

        trc = attrs.get("trusted_runtime_context", {})
        b_ctx = trc.get("budget_context", {}) if isinstance(trc, dict) else {}
        trace_ft = wt.get("execution_budget_telemetry", {}).get("fencing_token")
        if isinstance(b_ctx, dict) and "fencing_token" in b_ctx:
            self.check(
                cat4,
                b_ctx.get("fencing_token") == trace_ft,
                "ERR_BUDGET_FENCING_MISMATCH",
                f"{tid}.{eid}: proposal fencing_token != trace fencing_token",
            )

    def _validate_arg_validation_event(
        self,
        tid: str,
        eid: str,
        wt: dict[str, Any],
        attrs: dict[str, Any],
        proposals_by_id: dict[str, dict[str, Any]],
    ) -> None:
        cat2 = "cat2_ordering_and_refs"
        cat3 = "cat3_digests_hashes_spans"

        t_prop = str(attrs.get("target_proposal_id"))
        self.check(
            cat2,
            t_prop in proposals_by_id,
            "ERR_PROPOSAL_UNRESOLVED",
            f"{tid}.{eid}: unresolved target_proposal_id {t_prop}",
        )
        norm_args = attrs.get("normalized_arguments")
        dig = attrs.get("arguments_digest")
        if isinstance(norm_args, dict):
            for nak, _nav in norm_args.items():
                self.check(
                    cat3,
                    isinstance(nak, str),
                    "ERR_NORM_ARG_KEY",
                    f"{tid}.{eid}: norm arg key {nak}",
                )
            domain_ok = validate_canonical_json_domain(norm_args, allow_floats=False)
            self.check(
                cat3,
                domain_ok,
                "ERR_CANONICAL_JSON_DOMAIN_VIOLATION",
                f"{tid}.{eid}: normalized_arguments violates restricted trustops-canonical-json-v1 domain",
            )
            if domain_ok:
                self.check(
                    cat3,
                    compute_arguments_digest(norm_args) == dig,
                    "ERR_ARG_DIGEST_MISMATCH",
                    f"{tid}.{eid}: arguments_digest mismatch",
                )

    def _validate_approval_event(
        self,
        tid: str,
        eid: str,
        ev: dict[str, Any],
        wt: dict[str, Any],
        attrs: dict[str, Any],
        results_by_id: dict[str, dict[str, Any]],
        approval_events_by_event_id: dict[str, dict[str, Any]],
        seq_by_id: dict[str, int],
        t_end: datetime.datetime | None,
    ) -> None:
        cat1 = "cat1_envelope_and_syntax"
        cat4 = "cat4_contracts_snapshots_bindings"

        ts_obj = attrs.get("trusted_source", {})
        is_provisional = self.approval_validation_profile == "provisional_draft"
        allowed_ts_keys = {
            "source_system",
            "source_ref",
            "verification_method",
            "verified_at",
            "record_version",
            "decision_record_seq",
        }
        self.check(
            cat1,
            isinstance(ts_obj, dict) and len(set(ts_obj.keys()) - allowed_ts_keys) == 0,
            "ERR_UNKNOWN_FIELD_REJECTED",
            f"{tid}.{eid}: invalid trusted_source keys",
        )

        # SA-05: Validate approval_status against settled 6-value enum
        ap_status = attrs.get("approval_status")
        self.check(
            cat4,
            ap_status in APPROVAL_STATUS_ENUM,
            "ERR_APPROVAL_STATUS_INVALID",
            f"{tid}.{eid}: invalid approval_status {ap_status!r}",
        )

        # SA-03 & OD-04 provisional draft checks (enforced under `provisional_draft` profile;
        # excluded under `base_only` profile for S1-03 Row 9 base Approval evidence validation only —
        # procurement traces MUST use `provisional_draft` per A4)
        if is_provisional:
            # A3: superseded_by_approval_id is a derived read-model field only and MUST be null in every stored event
            if attrs.get("superseded_by_approval_id") is not None:
                self.check(
                    cat4,
                    False,
                    "ERR_SA03_ACTION_APPROVAL_BINDING_INVALID",
                    f"{tid}.{eid}: superseded_by_approval_id must be null in stored/emitted approval events (derived read-model only)",
                )

            ap_req_id = attrs.get("approval_request_id")
            cur_seq = seq_by_id.get(eid, 0)
            sup_id = attrs.get("supersedes_approval_id")
            prior_same_req = sorted(
                [
                    (other_eid, other_ev)
                    for other_eid, other_ev in approval_events_by_event_id.items()
                    if other_eid != eid
                    and seq_by_id.get(other_eid, 0) < cur_seq
                    and other_ev["attributes"].get("approval_request_id") == ap_req_id
                ],
                key=lambda item: seq_by_id.get(item[0], 0),
            )
            if prior_same_req:
                for _, other_ev in prior_same_req:
                    other_attrs = other_ev["attributes"]
                    if other_attrs.get("approval_status") in {"DENIED", "CANCELLED"}:
                        self.check(
                            cat4,
                            False,
                            "ERR_APPROVAL_TERMINAL_STATUS_VIOLATION",
                            f"{tid}.{eid}: terminal approval status {other_attrs.get('approval_status')} on {ap_req_id} cannot transition to {ap_status}",
                        )
                    # A1: After an APPROVED record for an approval_request_id, ONLY CANCELLED is allowed next
                    if (
                        other_attrs.get("approval_status") == "APPROVED"
                        and ap_status != "CANCELLED"
                    ):
                        self.check(
                            cat4,
                            False,
                            "ERR_SA03_ACTION_APPROVAL_BINDING_INVALID",
                            f"{tid}.{eid}: after APPROVED on {ap_req_id}, only CANCELLED is allowed next (got {ap_status!r})",
                        )
                # A2: Every record after the first carries a non-null supersedes_approval_id naming the immediately preceding record
                prev_attrs = prior_same_req[-1][1]["attributes"]
                self.check(
                    cat4,
                    isinstance(sup_id, str)
                    and len(sup_id) > 0
                    and sup_id == prev_attrs.get("approval_id")
                    and is_strict_int(attrs.get("decision_record_seq"))
                    and is_strict_int(prev_attrs.get("decision_record_seq"))
                    and int(attrs.get("decision_record_seq", 0))
                    > int(prev_attrs.get("decision_record_seq", 0))
                    and attrs.get("record_version") != prev_attrs.get("record_version"),
                    "ERR_SA03_ACTION_APPROVAL_BINDING_INVALID",
                    f"{tid}.{eid}: subsequent approval record on {ap_req_id} must carry supersedes_approval_id={prev_attrs.get('approval_id')!r} with higher decision_record_seq and distinct record_version",
                )

            rec_ver = attrs.get("record_version")
            dec_seq = attrs.get("decision_record_seq")
            self.check(
                cat4,
                isinstance(rec_ver, str)
                and len(rec_ver) > 0
                and is_strict_int(dec_seq)
                and dec_seq > 0
                and ts_obj.get("record_version") == rec_ver
                and ts_obj.get("decision_record_seq") == dec_seq,
                "ERR_APPROVAL_EVIDENCE_MISMATCH",
                f"{tid}.{eid}: missing or mismatched record_version / decision_record_seq on approval event",
            )

        try:
            b_amt = Decimal(str(attrs.get("bound_amount", "0.00")))
            ceil_amt = Decimal(str(attrs.get("approved_amount_ceiling", "0.00")))
            self.check(
                cat4,
                ceil_amt >= b_amt,
                "ERR_APPROVAL_CEILING_EXCEEDED",
                f"{tid}.{eid}: approved_amount_ceiling {ceil_amt} < bound_amount {b_amt}",
            )
        except InvalidOperation:
            self.check(
                cat4,
                False,
                "ERR_APPROVAL_CEILING_EXCEEDED",
                f"{tid}.{eid}: invalid decimal in approval ceiling",
            )

        # SA-04: Remove t_start <= ap_dt requirement (existing approval can precede a continuation trace).
        # Under `provisional_draft`, require ap_dt <= ver_dt <= ev_dt <= t_end; under `base_only`,
        # require ap_dt <= ev_dt without mandating provisional trusted_source.verified_at.
        ap_dt = parse_iso8601_utc(attrs.get("approval_timestamp"))
        ver_dt = parse_iso8601_utc(ts_obj.get("verified_at")) if isinstance(ts_obj, dict) else None
        ev_dt = parse_iso8601_utc(ev.get("timestamp"))
        if is_provisional:
            chron_ok = (
                ap_dt is not None
                and ver_dt is not None
                and ev_dt is not None
                and ap_dt <= ver_dt <= ev_dt
                and (t_end is None or ver_dt <= t_end)
            )
        else:
            chron_ok = (
                ap_dt is not None
                and ev_dt is not None
                and ap_dt <= ev_dt
                and (
                    ver_dt is None
                    or (ap_dt <= ver_dt <= ev_dt and (t_end is None or ver_dt <= t_end))
                )
            )
        self.check(
            cat4,
            chron_ok,
            "ERR_APPROVAL_CHRONOLOGY_INVALID",
            f"{tid}.{eid}: invalid approval_timestamp / verified_at chronology",
        )

        for res_ev in results_by_id.values():
            r_attrs = res_ev["attributes"]
            if r_attrs.get("tool_name") == "request_approval":
                r_data = (r_attrs.get("result_payload") or {}).get("data")
                if isinstance(r_data, dict):
                    emb = r_data.get("approval_evidence")
                    if isinstance(emb, dict) and emb.get("approval_id") == attrs.get("approval_id"):
                        expected_sref_suffix = "/" + str(attrs.get("approval_id"))
                        match_ok = (
                            r_data.get("approval_request_id") == attrs.get("approval_request_id")
                            and emb.get("approval_request_id") == attrs.get("approval_request_id")
                            and emb.get("request_revision") == attrs.get("bound_request_revision")
                            and emb.get("supplier_id") == attrs.get("bound_supplier_id")
                            and emb.get("amount") == attrs.get("bound_amount")
                            and emb.get("currency") == attrs.get("bound_currency")
                            and emb.get("approval_level") == attrs.get("approval_level")
                            and emb.get("approver_ref") == attrs.get("approver_id")
                            and emb.get("decision_timestamp") == attrs.get("approval_timestamp")
                            and emb.get("policy_version") == attrs.get("policy_version")
                            and (
                                (not is_provisional)
                                or (
                                    emb.get("record_version") == attrs.get("record_version")
                                    and emb.get("decision_record_seq")
                                    == attrs.get("decision_record_seq")
                                )
                            )
                            and isinstance(emb.get("source_ref"), str)
                            and emb["source_ref"].endswith(expected_sref_suffix)
                            and emb.get("source_ref") == ts_obj.get("source_ref")
                        )
                        self.check(
                            cat4,
                            match_ok,
                            "ERR_APPROVAL_EVIDENCE_MISMATCH",
                            f"{tid}.{eid}: mismatch between request_approval result/embedded evidence and approval event",
                        )

    def _validate_policy_check_event(
        self,
        tid: str,
        eid: str,
        ev: dict[str, Any],
        wt: dict[str, Any],
        attrs: dict[str, Any],
        proposals_by_id: dict[str, dict[str, Any]],
        validations_by_id: dict[str, dict[str, Any]],
        results_by_id: dict[str, dict[str, Any]],
        approval_events_by_event_id: dict[str, dict[str, Any]],
        seq_by_id: dict[str, int],
    ) -> None:
        cat1 = "cat1_envelope_and_syntax"
        cat4 = "cat4_contracts_snapshots_bindings"

        # SA-07: Validate check_mode enum and environment restriction for STUB_CONTRACT_TEST
        chk_mode = attrs.get("check_mode")
        env = wt.get("environment")
        mode_ok = chk_mode in POLICY_CHECK_MODES_ENUM and (
            chk_mode != "STUB_CONTRACT_TEST" or env in {"dev", "test", "ci"}
        )
        self.check(
            cat4,
            mode_ok,
            "ERR_POLICY_CHECK_MODE_INVALID",
            f"{tid}.{eid}: invalid check_mode {chk_mode!r} for environment {env!r}",
        )

        snap = attrs.get("authorization_snapshot")
        self.check(
            cat4,
            isinstance(snap, dict),
            "ERR_SNAPSHOT_MISSING",
            f"{tid}.{eid}: missing authorization_snapshot",
        )
        if not isinstance(snap, dict):
            return

        for sk in REQUIRED_SNAPSHOT_KEYS:
            self.check(
                cat4, sk in snap, "ERR_SNAPSHOT_MISSING", f"{tid}.{eid}: missing snapshot key {sk}"
            )
        for ep in attrs.get("evaluated_policies", []):
            if isinstance(ep, dict):
                for epk in (
                    "policy_id",
                    "policy_version",
                    "status",
                    "policy_result",
                    "criticality",
                ):
                    self.check(
                        cat4, epk in ep, "ERR_POLICY_ENTRY_INVALID", f"{tid}.{eid}: missing {epk}"
                    )
                if "status" in ep:
                    self.check(
                        cat4,
                        ep.get("status") == ep.get("policy_result")
                        and ep.get("policy_result") in {"PASS", "FAIL", "NOT_APPLICABLE", "ERROR"},
                        "ERR_POLICY_STATUS_RESULT_MISMATCH",
                        f"{tid}.{eid}: evaluated_policies[].status ({ep.get('status')}) != policy_result ({ep.get('policy_result')})",
                    )
                # SA-06: Enforce single canonical criticality spelling ("critical")
                self.check(
                    cat4,
                    ep.get("criticality") == "critical",
                    "ERR_POLICY_CRITICALITY_INVALID",
                    f"{tid}.{eid}: evaluated_policies[].criticality must be canonical 'critical', got {ep.get('criticality')!r}",
                )
        extra_snap = set(snap.keys()) - REQUIRED_SNAPSHOT_KEYS
        missing_snap = REQUIRED_SNAPSHOT_KEYS - set(snap.keys())
        self.check(
            cat1,
            len(extra_snap) == 0 and len(missing_snap) == 0,
            "ERR_UNKNOWN_FIELD_REJECTED" if extra_snap else "ERR_SNAPSHOT_MISSING",
            f"{tid}.{eid}: snapshot key mismatch extra={extra_snap} missing={missing_snap}",
        )

        eval_pols = attrs.get("evaluated_policies", [])
        pol_ids = [p.get("policy_id") for p in eval_pols if isinstance(p, dict)]
        self.check(
            cat4,
            len(pol_ids) == 3
            and set(pol_ids) == {"PROC-APPROVAL-01", "PROC-TOOL-STAGE-01", "PROC-SUPPLIER-01"},
            "ERR_POLICY_IDS_NOT_DISTINCT",
            f"{tid}.{eid}: evaluated_policies must contain all 3 distinct mandatory policy IDs, got {pol_ids}",
        )
        versions_obj = wt.get("versions", {})
        kb_ver = versions_obj.get("policy_kb_version")
        bundle_ver = versions_obj.get("policy_bundle_version")
        rule_ver_map = versions_obj.get("policy_rule_versions")
        self.check(
            cat4,
            attrs.get("policy_bundle_version") == bundle_ver,
            "ERR_POLICY_LINEAGE_MISMATCH",
            f"{tid}.{eid}: policy_check.policy_bundle_version ({attrs.get('policy_bundle_version')}) != versions.policy_bundle_version ({bundle_ver})",
        )
        if isinstance(rule_ver_map, dict):
            expected_apr_rule_ver = rule_ver_map.get("PROC-APPROVAL-01")
            per_rule_ok = (
                set(rule_ver_map.keys())
                == {"PROC-APPROVAL-01", "PROC-TOOL-STAGE-01", "PROC-SUPPLIER-01"}
                and snap.get("policy_version") in {expected_apr_rule_ver, bundle_ver}
                and all(
                    isinstance(p, dict)
                    and p.get("policy_version") == rule_ver_map.get(str(p.get("policy_id")))
                    for p in eval_pols
                )
            )
            self.check(
                cat4,
                per_rule_ok,
                "ERR_POLICY_LINEAGE_MISMATCH",
                f"{tid}.{eid}: per-policy rule version mismatch against versions.policy_rule_versions",
            )
        else:
            self.check(
                cat4,
                snap.get("policy_version") == kb_ver
                and all(
                    p.get("policy_version") == kb_ver for p in eval_pols if isinstance(p, dict)
                ),
                "ERR_SNAPSHOT_POLICY_VERSION",
                f"{tid}.{eid}: policy_version mismatch against versions.policy_kb_version ({kb_ver})",
            )

        self.check(
            cat4,
            snap.get("request_revision") == wt.get("request", {}).get("request_revision"),
            "ERR_SNAPSHOT_REQUEST_MISMATCH",
            f"{tid}.{eid}: snapshot request_revision != request.request_revision",
        )

        sup_ref = snap.get("supplier_evidence_ref")
        if isinstance(sup_ref, dict):
            s_res_id = str(sup_ref.get("supplier_check_result_id"))
            if s_res_id in results_by_id:
                s_ev = results_by_id[s_res_id]
                s_data = (s_ev["attributes"].get("result_payload") or {}).get("data") or {}
                sup_obj = (s_data.get("supplier") or {}) if isinstance(s_data, dict) else {}
                self.check(
                    cat4,
                    sup_ref.get("supplier_status") == sup_obj.get("status")
                    and sup_ref.get("raw_supplier_status") == sup_obj.get("raw_status")
                    and sup_ref.get("supplier_id") == sup_obj.get("supplier_id")
                    and sup_ref.get("directory_version") == s_data.get("directory_version"),
                    "ERR_SNAPSHOT_SUPPLIER_EVIDENCE_MISMATCH",
                    f"{tid}.{eid}: supplier_evidence_ref contradicts get_supplier result {s_res_id}",
                )
                self.check(
                    cat4,
                    sup_ref.get("supplier_record_version") == sup_obj.get("record_version")
                    and sup_ref.get("latest_observed_supplier_record_version")
                    == sup_obj.get("record_version")
                    and sup_ref.get("is_current_at_check") is True,
                    "ERR_STALE_RECORD_VERSION_AT_CLAIM",
                    f"{tid}.{eid}: stale or mismatched supplier_record_version at check",
                )
            else:
                self.check(
                    cat4,
                    isinstance(sup_ref.get("supplier_record_version"), str)
                    and sup_ref.get("supplier_record_version")
                    == sup_ref.get("latest_observed_supplier_record_version")
                    and sup_ref.get("is_current_at_check") is True,
                    "ERR_STALE_RECORD_VERSION_AT_CLAIM",
                    f"{tid}.{eid}: stale supplier_record_version on prerequisite supplier_evidence_ref",
                )

        app_ref = snap.get("approval_evidence_ref")
        if isinstance(app_ref, dict) and "approval_event_id" in app_ref:
            ap_ev_id = str(app_ref.get("approval_event_id"))
            ap_ev = approval_events_by_event_id.get(ap_ev_id)
            self.check(
                cat4,
                ap_ev is not None and seq_by_id.get(ap_ev_id, 999999) < seq_by_id.get(eid, 0),
                "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH",
                f"{tid}.{eid}: approval_event_id {ap_ev_id} does not resolve to an earlier approval event",
            )
            if ap_ev is not None:
                ap_attrs = ap_ev["attributes"]
                ts_obj = ap_attrs.get("trusted_source", {})
                expected_suffix = "/" + str(ap_attrs.get("approval_id"))
                reqapp_matches = True
                for r_ev in results_by_id.values():
                    if r_ev["attributes"].get("tool_name") == "request_approval":
                        rd = (r_ev["attributes"].get("result_payload") or {}).get("data") or {}
                        emb = (rd.get("approval_evidence") or {}) if isinstance(rd, dict) else {}
                        if isinstance(emb, dict) and emb.get("approval_id") == ap_attrs.get(
                            "approval_id"
                        ):
                            if (
                                rd.get("approval_request_id") != ap_attrs.get("approval_request_id")
                                or emb.get("approval_level") != ap_attrs.get("approval_level")
                                or not str(emb.get("source_ref", "")).endswith(expected_suffix)
                            ):
                                reqapp_matches = False
                try:
                    ceil_ok = Decimal(str(ap_attrs.get("approved_amount_ceiling", "0"))) >= Decimal(
                        str(ap_attrs.get("bound_amount", "0"))
                    )
                except InvalidOperation:
                    ceil_ok = False

                ap_dt = parse_iso8601_utc(ap_attrs.get("approval_timestamp"))
                ver_dt = (
                    parse_iso8601_utc(ts_obj.get("verified_at"))
                    if isinstance(ts_obj, dict)
                    else None
                )
                ev_dt = parse_iso8601_utc(ev.get("timestamp"))
                if self.approval_validation_profile == "provisional_draft":
                    chron_ok = (
                        ap_dt is not None
                        and ver_dt is not None
                        and ev_dt is not None
                        and ap_dt <= ver_dt <= ev_dt
                    )
                else:
                    chron_ok = (
                        ap_dt is not None
                        and ev_dt is not None
                        and ap_dt <= ev_dt
                        and (ver_dt is None or ap_dt <= ver_dt <= ev_dt)
                    )

                snap_match = (
                    reqapp_matches
                    and ceil_ok
                    and chron_ok
                    and app_ref.get("approval_id") == ap_attrs.get("approval_id")
                    and app_ref.get("approval_request_id") == ap_attrs.get("approval_request_id")
                    and app_ref.get("decision_status") == ap_attrs.get("approval_status")
                    and app_ref.get("bound_request_revision")
                    == ap_attrs.get("bound_request_revision")
                    and app_ref.get("bound_calculation_ref")
                    == ap_attrs.get("bound_calculation_ref")
                    and app_ref.get("bound_supplier_id") == ap_attrs.get("bound_supplier_id")
                    and app_ref.get("bound_amount") == ap_attrs.get("bound_amount")
                    and app_ref.get("bound_currency") == ap_attrs.get("bound_currency")
                    and app_ref.get("approval_level") == ap_attrs.get("approval_level")
                )
                self.check(
                    cat4,
                    snap_match,
                    "ERR_SNAPSHOT_APPROVAL_EVIDENCE_MISMATCH",
                    f"{tid}.{eid}: approval_evidence_ref does not match source approval event {ap_ev_id}",
                )

                if self.approval_validation_profile == "provisional_draft":
                    self.check(
                        cat4,
                        app_ref.get("approval_record_version") == ap_attrs.get("record_version")
                        and app_ref.get("latest_observed_approval_record_version")
                        == ap_attrs.get("record_version")
                        and app_ref.get("is_current_at_check") is True,
                        "ERR_STALE_RECORD_VERSION_AT_CLAIM",
                        f"{tid}.{eid}: stale or mismatched approval_record_version at check",
                    )

                    dec_seq = app_ref.get("decision_record_seq")
                    latest_seq = app_ref.get("latest_observed_decision_record_seq")
                    later_approvals = [
                        other_ev
                        for other_id, other_ev in approval_events_by_event_id.items()
                        if other_id != ap_ev_id
                        and seq_by_id.get(other_id, 0) < seq_by_id.get(eid, 0)
                        and other_ev["attributes"].get("decision_record_seq", 0)
                        > ap_attrs.get("decision_record_seq", 0)
                    ]
                    # A4: Validate stale_reason_code on approval_evidence_ref when present
                    if "stale_reason_code" in app_ref:
                        s_code = app_ref.get("stale_reason_code")
                        stale_ok = (
                            (s_code is None)
                            if app_ref.get("is_current_at_check") is True
                            else (s_code in STALE_REASON_CODES_ENUM)
                        )
                        self.check(
                            cat4,
                            stale_ok,
                            "ERR_STALE_REASON_CODE_INVALID",
                            f"{tid}.{eid}: invalid approval_evidence_ref.stale_reason_code {s_code!r}",
                        )

                    # If action_verdict == ALLOW, approval must not be superseded
                    if attrs.get("action_verdict") == "ALLOW":
                        self.check(
                            cat4,
                            is_strict_int(dec_seq)
                            and is_strict_int(latest_seq)
                            and dec_seq == ap_attrs.get("decision_record_seq")
                            and dec_seq == latest_seq
                            and len(later_approvals) == 0
                            and ap_attrs.get("superseded_by_approval_id") is None,
                            "ERR_APPROVAL_SUPERSEDED_SEQUENCE",
                            f"{tid}.{eid}: approval decision_record_seq {dec_seq} superseded by higher sequence {latest_seq}",
                        )
                        # A5: Deterministic ordering — observed approval event MUST precede tool_proposal by trace sequence_number
                        # (wall-clock time never decides) and hold highest decision_record_seq
                        prop_ev_for_order = proposals_by_id.get(str(snap.get("proposal_id")))
                        if prop_ev_for_order is not None:
                            prop_seq_num = seq_by_id.get(prop_ev_for_order["event_id"], 0)
                            ap_seq_num = seq_by_id.get(ap_ev_id, 999999)
                            if ap_seq_num >= prop_seq_num:
                                self.check(
                                    cat4,
                                    False,
                                    "ERR_APPROVAL_ORDER_INVALID",
                                    f"{tid}.{eid}: approval event {ap_ev_id} (seq {ap_seq_num}) does not precede tool_proposal {prop_ev_for_order['event_id']} (seq {prop_seq_num})",
                                )

        dclaim = snap.get("dispatch_claim")
        if snap.get("tool_name") == "create_purchase_order":
            prop_ev = proposals_by_id.get(str(snap.get("proposal_id")))
            prop_dclaim_id = (
                prop_ev["attributes"]
                .get("trusted_runtime_context", {})
                .get("domain_context", {})
                .get("dispatch_claim_id")
                if prop_ev
                else None
            )
            self.check(
                cat4,
                isinstance(dclaim, dict)
                and dclaim.get("dispatch_claim_id") == f"dclaim_{snap.get('root_request_id')}"
                and dclaim.get("dispatch_claim_id") == prop_dclaim_id
                and dclaim.get("claim_status_at_check")
                in {"AVAILABLE_AT_CHECK", "AVAILABLE_CLAIMED_ON_ALLOW", "NOT_CLAIMED_BLOCKED"},
                "ERR_DISPATCH_CLAIM_MISMATCH",
                f"{tid}.{eid}: dispatch_claim_id or claim_status_at_check mismatch at policy_check",
            )
            if isinstance(dclaim, dict) and attrs.get("action_verdict") == "ALLOW":
                expected_sup_ver = (
                    sup_ref.get("supplier_record_version") if isinstance(sup_ref, dict) else None
                )
                expected_app_ver = (
                    app_ref.get("approval_record_version") if isinstance(app_ref, dict) else None
                )
                app_ver_ok = (
                    dclaim.get("bound_approval_record_version") == expected_app_ver
                    if self.approval_validation_profile == "provisional_draft"
                    else True
                )
                self.check(
                    cat4,
                    dclaim.get("bound_supplier_record_version") == expected_sup_ver
                    and app_ver_ok
                    and dclaim.get("currentness_verified") is True,
                    "ERR_STALE_RECORD_VERSION_AT_CLAIM",
                    f"{tid}.{eid}: dispatch_claim currentness_verified or bound record versions invalid on ALLOW",
                )

    def _validate_agent_state_event(
        self,
        tid: str,
        eid: str,
        ev: dict[str, Any],
        wt: dict[str, Any],
        attrs: dict[str, Any],
        checks_by_id: dict[str, dict[str, Any]],
        proposals_by_id: dict[str, dict[str, Any]],
        calls_by_id: dict[str, dict[str, Any]],
        results_by_id: dict[str, dict[str, Any]],
        recoveries_by_id: dict[str, dict[str, Any]],
        seq_by_id: dict[str, int],
    ) -> None:
        cat4 = "cat4_contracts_snapshots_bindings"

        to_state = attrs.get("to_app_state")
        p_stage = attrs.get("policy_stage")
        accepted = attrs.get("transition_accepted")
        dcc = attrs.get("dispatch_claim_consumption")

        expected_stage = STATE_TO_STAGE_MAP.get(str(to_state))
        self.check(
            cat4,
            to_state in PROC_APP_STATES
            and p_stage in PROC_POLICY_STAGES
            and p_stage == expected_stage,
            "ERR_STATE_STAGE_MAPPING_INVALID",
            f"{tid}.{eid}: to_app_state={to_state} must map to policy_stage={expected_stage}, got {p_stage}",
        )

        if to_state == "PO_CREATION" and accepted is True:
            chk_id = str(attrs.get("bound_authorization_check_id"))
            chk_ev = checks_by_id.get(chk_id)
            valid_po_allow = (
                chk_ev is not None
                and chk_ev["attributes"].get("action_verdict") == "ALLOW"
                and chk_ev["attributes"].get("authorization_snapshot", {}).get("tool_name")
                == "create_purchase_order"
                and chk_ev["attributes"].get("authorization_snapshot", {}).get("operation_mode")
                == "CREATE_PO"
                and chk_ev["attributes"]
                .get("authorization_snapshot", {})
                .get("resulting_dispatch_state_revision")
                == attrs.get("state_revision_id")
            )
            self.check(
                cat4,
                valid_po_allow,
                "ERR_PO_STATE_TRANSITION_INVALID",
                f"{tid}.{eid}: APPROVED -> PO_CREATION requires a bound ALLOW policy_check for create_purchase_order",
            )
            base_dcc_keys = {
                "consumption_record_id",
                "dispatch_claim_id",
                "root_request_id",
                "request_revision",
                "preallocated_at_proposal_id",
                "bound_authorization_check_id",
                "bound_action_verdict",
                "transition_state_event_id",
                "resulting_state_revision_id",
                "consumed_by_call_id",
                "bound_supplier_record_version",
                "consumption_status",
                "redispatch_or_reset_permitted",
            }
            if self.approval_validation_profile == "provisional_draft":
                base_dcc_keys.add("bound_approval_record_version")
            sa02_dcc_keys = {
                "bound_approval_record_version",
                "observed_supplier_record_version_at_consumption",
                "observed_approval_record_version_at_consumption",
                "bound_decision_record_seq",
                "observed_decision_record_seq_at_consumption",
                "currentness_verified_at_consumption",
                "stale_reason_code",
            }
            snap = chk_ev["attributes"].get("authorization_snapshot", {}) if chk_ev else {}
            dclaim = (snap.get("dispatch_claim") or {}) if isinstance(snap, dict) else {}
            call_ev = (
                calls_by_id.get(str(dcc.get("consumed_by_call_id")))
                if isinstance(dcc, dict)
                else None
            )

            # V19-02 (E17): Resolve preallocated_at_proposal_id to earlier create_purchase_order proposal
            # and require equality with snapshot.proposal_id and consuming tool_call.proposal_id
            pre_prop_id = (
                str(dcc.get("preallocated_at_proposal_id", "")) if isinstance(dcc, dict) else ""
            )
            pre_prop_ev = proposals_by_id.get(pre_prop_id)
            prop_resolved_ok = (
                pre_prop_ev is not None
                and seq_by_id.get(pre_prop_ev["event_id"], 999999) < seq_by_id.get(eid, 0)
                and pre_prop_ev["attributes"].get("known_tool_name") == "create_purchase_order"
                and pre_prop_id == snap.get("proposal_id")
                and (call_ev is None or pre_prop_id == call_ev["attributes"].get("proposal_id"))
            )
            self.check(
                cat4,
                prop_resolved_ok,
                "ERR_CLAIM_CONSUMPTION_PROPOSAL_MISMATCH",
                f"{tid}.{eid}: dispatch_claim_consumption.preallocated_at_proposal_id {pre_prop_id!r} unresolved or mismatched with PO proposal",
            )

            # SA-02: Validate consumption-time record versions & sequence currentness when present
            if isinstance(dcc, dict) and "currentness_verified_at_consumption" in dcc:
                app_ref = snap.get("approval_evidence_ref") if isinstance(snap, dict) else None
                expected_seq = (
                    app_ref.get("decision_record_seq") if isinstance(app_ref, dict) else None
                )
                if self.approval_validation_profile == "provisional_draft":
                    sa02_ok = (
                        dcc.get("observed_supplier_record_version_at_consumption")
                        == dcc.get("bound_supplier_record_version")
                        and dcc.get("observed_approval_record_version_at_consumption")
                        == dcc.get("bound_approval_record_version")
                        and dcc.get("bound_decision_record_seq") == expected_seq
                        and dcc.get("observed_decision_record_seq_at_consumption") == expected_seq
                        and dcc.get("currentness_verified_at_consumption") is True
                    )
                else:
                    sa02_ok = (
                        dcc.get("observed_supplier_record_version_at_consumption")
                        == dcc.get("bound_supplier_record_version")
                        and dcc.get("currentness_verified_at_consumption") is True
                    )
                self.check(
                    cat4,
                    sa02_ok,
                    "ERR_STALE_RECORD_VERSION_AT_CONSUMPTION",
                    f"{tid}.{eid}: stale or mismatched supplier/approval version or decision_record_seq at consumption",
                )
                if "stale_reason_code" in dcc:
                    dcc_stale = dcc.get("stale_reason_code")
                    dcc_stale_ok = (
                        (dcc_stale is None)
                        if dcc.get("currentness_verified_at_consumption") is True
                        else (dcc_stale in STALE_REASON_CODES_ENUM)
                    )
                    self.check(
                        cat4,
                        dcc_stale_ok,
                        "ERR_STALE_REASON_CODE_INVALID",
                        f"{tid}.{eid}: invalid dispatch_claim_consumption.stale_reason_code {dcc_stale!r}",
                    )

            valid_dcc = (
                isinstance(dcc, dict)
                and base_dcc_keys.issubset(set(dcc.keys()))
                and set(dcc.keys()).issubset(base_dcc_keys | sa02_dcc_keys)
                and dcc.get("dispatch_claim_id") == attrs.get("bound_dispatch_claim_id")
                and dcc.get("root_request_id") == wt.get("request", {}).get("request_id")
                and dcc.get("request_revision") == wt.get("request", {}).get("request_revision")
                and dcc.get("bound_authorization_check_id") == chk_id
                and dcc.get("bound_action_verdict") == "ALLOW"
                and dcc.get("transition_state_event_id") == eid
                and dcc.get("resulting_state_revision_id") == attrs.get("state_revision_id")
                and dcc.get("consumed_by_call_id") in calls_by_id
                and dcc.get("bound_supplier_record_version")
                == dclaim.get("bound_supplier_record_version")
                and (
                    self.approval_validation_profile != "provisional_draft"
                    or dcc.get("bound_approval_record_version")
                    == dclaim.get("bound_approval_record_version")
                )
                and dcc.get("consumption_status") == "CONSUMED_SINGLE_USE_LOCKED"
                and dcc.get("redispatch_or_reset_permitted") is False
            )
            self.check(
                cat4,
                valid_dcc,
                "ERR_CLAIM_CONSUMPTION_RECORD_INVALID",
                f"{tid}.{eid}: invalid or missing dispatch_claim_consumption on PO_CREATION transition",
            )
        else:
            self.check(
                cat4,
                dcc is None,
                "ERR_CLAIM_CONSUMPTION_RECORD_INVALID",
                f"{tid}.{eid}: dispatch_claim_consumption must be null on non-PO_CREATION transition",
            )

        if to_state == "COMPLETION" and accepted is True:
            has_confirmed_po = any(
                r["attributes"].get("tool_name") == "create_purchase_order"
                and r["attributes"].get("result_payload", {}).get("status")
                in {"CREATED", "ALREADY_EXISTS"}
                and r["attributes"].get("side_effect_state") in {"COMMITTED", "ALREADY_EXISTING"}
                for r in results_by_id.values()
            )
            has_resolved_rec = any(
                rec["attributes"].get("reconciliation_status") == "RESOLVED_COMMITTED"
                and rec["attributes"].get("resolved_side_effect_state") == "COMMITTED"
                and isinstance(rec["attributes"].get("recovered_result_envelope"), dict)
                for rec in recoveries_by_id.values()
            )
            self.check(
                cat4,
                has_confirmed_po or has_resolved_rec,
                "ERR_UNRESOLVED_RECOVERY_COMPLETION",
                f"{tid}.{eid}: transition to COMPLETION without confirmed PO result or RESOLVED_COMMITTED recovery",
            )

    def _validate_tool_call_event(
        self,
        tid: str,
        eid: str,
        ev: dict[str, Any],
        wt: dict[str, Any],
        attrs: dict[str, Any],
        proposals_by_id: dict[str, dict[str, Any]],
        validations_by_id: dict[str, dict[str, Any]],
        checks_by_id: dict[str, dict[str, Any]],
        states_by_rev: dict[str, dict[str, Any]],
        po_transition_events: list[dict[str, Any]],
        results_by_id: dict[str, dict[str, Any]],
        used_auth_checks: set[str],
        po_dispatch_claims_used: list[str],
    ) -> None:
        cat2 = "cat2_ordering_and_refs"
        cat3 = "cat3_digests_hashes_spans"
        cat4 = "cat4_contracts_snapshots_bindings"

        chk_id = str(attrs.get("authorization_check_id"))
        self.check(
            cat2,
            chk_id in checks_by_id,
            "ERR_AUTH_CHECK_UNRESOLVED",
            f"{tid}.{eid}: unresolved authorization_check_id {chk_id}",
        )
        self.check(
            cat4,
            chk_id not in used_auth_checks,
            "ERR_AUTH_CHECK_REUSED",
            f"{tid}.{eid}: reused authorization_check_id {chk_id}",
        )
        used_auth_checks.add(chk_id)

        args = attrs.get("arguments", {})
        domain_ok = validate_canonical_json_domain(args, allow_floats=False)
        self.check(
            cat3,
            domain_ok,
            "ERR_CANONICAL_JSON_DOMAIN_VIOLATION",
            f"{tid}.{eid}: tool_call arguments violate restricted trustops-canonical-json-v1 domain",
        )
        if domain_ok:
            self.check(
                cat3,
                compute_arguments_digest(args) == attrs.get("arguments_digest"),
                "ERR_ARG_DIGEST_MISMATCH",
                f"{tid}.{eid}: tool_call arguments_digest mismatch",
            )

        trc = attrs.get("trusted_runtime_context", {})
        b_ctx = trc.get("budget_context", {}) if isinstance(trc, dict) else {}
        trace_ft = wt.get("execution_budget_telemetry", {}).get("fencing_token")
        if isinstance(b_ctx, dict):
            self.check(
                cat4,
                b_ctx.get("fencing_token") == trace_ft,
                "ERR_BUDGET_FENCING_MISMATCH",
                f"{tid}.{eid}: tool_call fencing_token != trace fencing_token",
            )

        op_mode = b_ctx.get("operation_mode") if isinstance(b_ctx, dict) else None
        retry_acc = attrs.get("retry_accounting")
        if isinstance(retry_acc, dict):
            if op_mode in {"CREATE_APPROVAL_REQUEST", "CREATE_PO"}:
                self.check(
                    cat4,
                    retry_acc.get("is_retry") is False and retry_acc.get("attempt_number") == 1,
                    "ERR_WRITE_RETRY_FORBIDDEN",
                    f"{tid}.{eid}: state-changing operation_mode {op_mode} cannot retry",
                )
            if retry_acc.get("is_retry") is True or retry_acc.get("attempt_number", 1) > 1:
                prior_att = retry_acc.get("prior_attempt_id")
                has_prior_failed = any(
                    r["attributes"].get("execution_status")
                    in {"TIMEOUT", "RUNTIME_EXCEPTION", "RATE_LIMITED", "ERROR"}
                    and (r["attributes"].get("transport_diagnostics") or {}).get("retryable")
                    is True
                    for r in results_by_id.values()
                )
                self.check(
                    cat4,
                    isinstance(prior_att, str) and len(prior_att) > 0 and has_prior_failed,
                    "ERR_RETRY_PRIOR_ATTEMPT_UNRESOLVED",
                    f"{tid}.{eid}: retry lacks resolved retryable prior attempt",
                )

        if attrs.get("tool_name") == "create_purchase_order":
            dclaim_id = str(attrs.get("dispatch_claim_id"))
            self.check(
                cat4,
                dclaim_id not in po_dispatch_claims_used,
                "ERR_PO_DUPLICATE_DISPATCH_CLAIM",
                f"{tid}.{eid}: duplicate PO dispatch_claim_id {dclaim_id}",
            )
            po_dispatch_claims_used.append(dclaim_id)

            chk_ev = checks_by_id.get(chk_id)
            snap = chk_ev["attributes"].get("authorization_snapshot", {}) if chk_ev else {}
            matching_transitions = [
                st
                for st in po_transition_events
                if st["attributes"].get("bound_authorization_check_id") == chk_id
                and st["attributes"].get("bound_dispatch_claim_id") == dclaim_id
                and st["attributes"].get("state_revision_id")
                == attrs.get("dispatch_state_revision")
            ]
            sup_ok = True
            s_ref = snap.get("supplier_evidence_ref") if isinstance(snap, dict) else None
            if (
                isinstance(s_ref, dict)
                and str(s_ref.get("supplier_check_result_id")) in results_by_id
            ):
                s_ev = results_by_id[str(s_ref.get("supplier_check_result_id"))]
                sup_obj = ((s_ev["attributes"].get("result_payload") or {}).get("data") or {}).get(
                    "supplier"
                ) or {}
                if sup_obj.get("status") != "APPROVED" or s_ref.get(
                    "supplier_status"
                ) != sup_obj.get("status"):
                    sup_ok = False

            app_ok = True
            a_ref = snap.get("approval_evidence_ref") if isinstance(snap, dict) else None
            if isinstance(a_ref, dict):
                ap_ev_id = str(a_ref.get("approval_event_id", ""))
                ap_ev = next(
                    (
                        e
                        for e in wt.get("events", [])
                        if e.get("event_id") == ap_ev_id and e.get("event_type") == "approval"
                    ),
                    None,
                )
                if (
                    ap_ev is None
                    or ap_ev["attributes"].get("approval_status") != "APPROVED"
                    or (
                        self.approval_validation_profile == "provisional_draft"
                        and ap_ev["attributes"].get("superseded_by_approval_id") is not None
                    )
                ):
                    app_ok = False

            dclaim_ok = (
                isinstance(snap.get("dispatch_claim"), dict)
                and snap["dispatch_claim"].get("dispatch_claim_id") == dclaim_id
            )
            self.check(
                cat4,
                len(matching_transitions) == 1 and sup_ok and app_ok and dclaim_ok,
                "ERR_PO_BINDING_FAILED",
                f"{tid}.{eid}: create_purchase_order dispatch binding verification failed",
            )
            if len(matching_transitions) == 1:
                dcc = matching_transitions[0]["attributes"].get("dispatch_claim_consumption")
                self.check(
                    cat4,
                    isinstance(dcc, dict)
                    and attrs.get("dispatch_claim_consumption_ref")
                    == dcc.get("consumption_record_id")
                    and dcc.get("consumed_by_call_id") == attrs.get("call_id"),
                    "ERR_CLAIM_CONSUMPTION_RECORD_INVALID",
                    f"{tid}.{eid}: tool_call dispatch_claim_consumption_ref mismatch",
                )
        else:
            self.check(
                cat4,
                attrs.get("dispatch_claim_consumption_ref") is None,
                "ERR_CLAIM_CONSUMPTION_RECORD_INVALID",
                f"{tid}.{eid}: non-PO tool_call must have null dispatch_claim_consumption_ref",
            )

    def _validate_tool_result_event(
        self,
        tid: str,
        eid: str,
        wt: dict[str, Any],
        attrs: dict[str, Any],
        calls_by_id: dict[str, dict[str, Any]],
    ) -> None:
        cat1 = "cat1_envelope_and_syntax"
        cat4 = "cat4_contracts_snapshots_bindings"

        rp = attrs.get("result_payload", {})
        self.check(
            cat1,
            isinstance(rp, dict) and set(rp.keys()) == {"status", "data", "error"},
            "ERR_UNKNOWN_FIELD_REJECTED",
            f"{tid}.{eid}: result_payload must have exact keys {{status, data, error}}",
        )
        if not isinstance(rp, dict):
            return

        cat3 = "cat3_digests_hashes_spans"
        ex_status = attrs.get("execution_status")
        se_state = attrs.get("side_effect_state")
        b_status = rp.get("status")
        t_name = attrs.get("tool_name")
        call_ev = calls_by_id.get(str(attrs.get("call_id")))

        if t_name == "search_policy":
            status_ok = b_status in {"MATCHED", "NO_MATCH", "AMBIGUOUS", "ERROR"}
            self.check(
                cat4,
                status_ok,
                "ERR_SEARCH_POLICY_CONTRACT_INVALID",
                f"{tid}.{eid}: search_policy status must be in MATCHED|NO_MATCH|AMBIGUOUS|ERROR, got {b_status!r}",
            )
            if b_status in {"MATCHED", "NO_MATCH", "AMBIGUOUS"}:
                sp_data = rp.get("data")
                expected_sp_keys = {
                    "query",
                    "requested_top_k",
                    "returned_count",
                    "matches",
                    "policy_set_version",
                    "retriever_version",
                    "applicability",
                }
                sp_matches = sp_data.get("matches") if isinstance(sp_data, dict) else None
                sp_ret_cnt = sp_data.get("returned_count") if isinstance(sp_data, dict) else None
                sp_app = sp_data.get("applicability") if isinstance(sp_data, dict) else None
                sp_shape_ok = (
                    isinstance(sp_data, dict)
                    and set(sp_data.keys()) == expected_sp_keys
                    and rp.get("error") is None
                    and isinstance(sp_app, str)
                    and sp_app in {"APPLICABLE", "MISSING", "CONFLICTING"}
                    and isinstance(sp_matches, list)
                    and is_strict_int(sp_ret_cnt)
                    and sp_ret_cnt == len(sp_matches)
                )
                if sp_shape_ok and is_strict_int(sp_ret_cnt) and isinstance(sp_matches, list):
                    if b_status == "NO_MATCH":
                        sp_shape_ok = (
                            sp_ret_cnt == 0 and len(sp_matches) == 0 and sp_app == "MISSING"
                        )
                    elif b_status == "MATCHED":
                        sp_shape_ok = (
                            sp_ret_cnt > 0 and len(sp_matches) > 0 and sp_app == "APPLICABLE"
                        )
                self.check(
                    cat4,
                    sp_shape_ok,
                    "ERR_SEARCH_POLICY_CONTRACT_INVALID",
                    f"{tid}.{eid}: invalid search_policy result_payload.data contract for status={b_status!r}",
                )
                if isinstance(sp_data, dict):
                    kb_ver = wt.get("versions", {}).get("policy_kb_version")
                    self.check(
                        cat4,
                        sp_data.get("policy_set_version") == kb_ver,
                        "ERR_POLICY_LINEAGE_MISMATCH",
                        f"{tid}.{eid}: search_policy.policy_set_version ({sp_data.get('policy_set_version')}) != versions.policy_kb_version ({kb_ver})",
                    )
                    if isinstance(sp_matches, list):
                        for m_obj in sp_matches:
                            if isinstance(m_obj, dict):
                                m_chash = m_obj.get("content_hash", "")
                                m_text = m_obj.get("text", "")
                                self.check(
                                    cat3,
                                    isinstance(m_chash, str)
                                    and PREFIXED_SHA256_RE.match(m_chash) is not None
                                    and compute_content_hash(m_text) == m_chash,
                                    "ERR_CONTENT_HASH_MISMATCH",
                                    f"{tid}.{eid}: search_policy match content_hash mismatch",
                                )
                                if (
                                    "source_document_sha256" in m_obj
                                    and m_obj["source_document_sha256"] is not None
                                ):
                                    s_hash = m_obj.get("source_document_sha256")
                                    self.check(
                                        cat3,
                                        isinstance(s_hash, str)
                                        and BARE_SHA256_RE.match(s_hash) is not None,
                                        "ERR_SOURCE_DOCUMENT_HASH_INVALID",
                                        f"{tid}.{eid}: search_policy match source_document_sha256 must be bare 64-hex",
                                    )

        if t_name == "create_purchase_order" and ex_status == "TIMEOUT":
            self.check(
                cat4,
                b_status != "ERROR" and se_state != "NONE",
                "ERR_TIMEOUT_CLAIMS_NO_EFFECT",
                f"{tid}.{eid}: dispatched PO timeout cannot claim status=ERROR or side_effect_state=NONE",
            )
            self.check(
                cat4,
                b_status == "UNKNOWN_OUTCOME" and se_state == "UNKNOWN",
                "ERR_TIMEOUT_SIDE_EFFECT_NOT_UNKNOWN",
                f"{tid}.{eid}: PO timeout must record status=UNKNOWN_OUTCOME and side_effect_state=UNKNOWN",
            )

        if b_status == "UNKNOWN_OUTCOME":
            self.check(
                cat4,
                ex_status in {"TIMEOUT", "RUNTIME_EXCEPTION"} and se_state == "UNKNOWN",
                "ERR_TIMEOUT_SIDE_EFFECT_NOT_UNKNOWN",
                f"{tid}.{eid}: UNKNOWN_OUTCOME requires side_effect_state=UNKNOWN and TIMEOUT/RUNTIME_EXCEPTION",
            )
            data = rp.get("data", {})
            if isinstance(data, dict) and call_ev is not None:
                c_attrs = call_ev["attributes"]
                self.check(
                    cat4,
                    data.get("proposal_id") == c_attrs.get("proposal_id"),
                    "ERR_UNKNOWN_RESULT_PROPOSAL_MISMATCH",
                    f"{tid}.{eid}: UNKNOWN_OUTCOME proposal_id mismatch",
                )
                self.check(
                    cat4,
                    data.get("dispatch_claim_id") == c_attrs.get("dispatch_claim_id"),
                    "ERR_UNKNOWN_RESULT_CLAIM_MISMATCH",
                    f"{tid}.{eid}: UNKNOWN_OUTCOME dispatch_claim_id mismatch",
                )

    def _validate_recovery_check_event(
        self,
        tid: str,
        eid: str,
        wt: dict[str, Any],
        attrs: dict[str, Any],
        calls_by_id: dict[str, dict[str, Any]],
        results_by_id: dict[str, dict[str, Any]],
    ) -> None:
        cat4 = "cat4_contracts_snapshots_bindings"

        cid = str(attrs.get("recovery_of_call_id"))
        rid = str(attrs.get("recovery_of_result_id"))
        call_ev = calls_by_id.get(cid)
        res_ev = results_by_id.get(rid)
        self.check(
            cat4,
            call_ev is not None
            and res_ev is not None
            and res_ev["attributes"].get("call_id") == cid,
            "ERR_RECOVERY_TARGET_UNRESOLVED",
            f"{tid}.{eid}: unresolved recovery_of_call_id / recovery_of_result_id",
        )
        if call_ev is not None:
            expected_idem = (
                call_ev["attributes"]
                .get("trusted_runtime_context", {})
                .get("domain_context", {})
                .get("idempotency_key")
            )
            self.check(
                cat4,
                attrs.get("queried_idempotency_key") == expected_idem,
                "ERR_RECOVERY_KEY_MISMATCH",
                f"{tid}.{eid}: queried_idempotency_key != original tool_call idempotency_key",
            )

        rec_status = attrs.get("reconciliation_status")
        if rec_status == "RESOLVED_COMMITTED":
            env = attrs.get("recovered_result_envelope")
            struct_in = wt.get("request", {}).get("structured_input", {})
            self.check(
                cat4,
                isinstance(env, dict)
                and isinstance(env.get("data"), dict)
                and env["data"].get("total_amount") == struct_in.get("total_amount")
                and env["data"].get("supplier_id") == struct_in.get("supplier_id")
                and env["data"].get("quantity") == struct_in.get("quantity"),
                "ERR_PO_RESULT_REQUEST_MISMATCH",
                f"{tid}.{eid}: recovered PO data does not match root request structured_input",
            )
        elif rec_status == "STILL_UNRESOLVED":
            self.check(
                cat4,
                wt.get("last_app_state") == "PO_CREATION"
                and wt.get("execution_status") == "RECOVERY_PENDING",
                "ERR_UNRESOLVED_RECOVERY_COMPLETION",
                f"{tid}.{eid}: STILL_UNRESOLVED recovery requires last_app_state=PO_CREATION and execution_status=RECOVERY_PENDING",
            )

    def _validate_final_response_event(
        self,
        tid: str,
        eid: str,
        wt: dict[str, Any],
        attrs: dict[str, Any],
        retrievals_by_id: dict[str, dict[str, Any]],
        model_calls_by_id: dict[str, dict[str, Any]],
        calls_by_id: dict[str, dict[str, Any]],
        results_by_id: dict[str, dict[str, Any]],
        recoveries_by_id: dict[str, dict[str, Any]],
    ) -> None:
        cat3 = "cat3_digests_hashes_spans"
        cat4 = "cat4_contracts_snapshots_bindings"

        # Email 6: Check abstention_details against technical retrieval faults
        abs_det = attrs.get("abstention_details")
        if isinstance(abs_det, dict):
            trig_ret = retrievals_by_id.get(str(abs_det.get("triggering_retrieval_id")))
            if (
                trig_ret
                and trig_ret["attributes"].get("execution_status")
                in RETRIEVAL_TECHNICAL_FAULT_STATUSES
            ):
                self.check(
                    cat4,
                    abs_det.get("abstention_reason_code")
                    == "TECHNICAL_RETRIEVAL_OR_PROVIDER_FAULT",
                    "ERR_RETRIEVAL_FAULT_MISLABELED_AS_ABSTENTION",
                    f"{tid}.{eid}: technical retrieval fault cannot use abstention_reason_code={abs_det.get('abstention_reason_code')!r}",
                )

        gen_mc = model_calls_by_id.get(str(attrs.get("generating_model_call_id")))
        prompt_str = (
            json.dumps(
                gen_mc["attributes"].get("rendered_prompt_or_messages", []), ensure_ascii=False
            )
            if gen_mc
            else ""
        )
        selected_cids_in_mc = (
            set(
                (gen_mc["attributes"].get("selected_context_ref") or {}).get(
                    "selected_chunk_ids", []
                )
            )
            if gen_mc
            else set()
        )
        resp_text = str(attrs.get("delivered_response_text", ""))

        vis_cits = attrs.get("visible_citations", [])
        cit_by_id: dict[str, dict[str, Any]] = {}
        for cit in vis_cits:
            cid = str(cit.get("citation_id"))
            cit_by_id[cid] = cit
            matched_doc = None
            for ret_ev in retrievals_by_id.values():
                for d in ret_ev["attributes"].get("retrieved_documents", []):
                    if d.get("doc_id") == cit.get("cited_doc_id") and d.get("chunk_id") == cit.get(
                        "cited_chunk_id"
                    ):
                        matched_doc = d
                        break
            self.check(
                cat3,
                matched_doc is not None,
                "ERR_CITATION_SOURCE_UNRESOLVED",
                f"{tid}.{eid}.{cid}: cited chunk {cit.get('cited_chunk_id')} unresolved",
            )
            # R12-05: Unconditionally require cited_snapshot_id, cited_content_hash, and cited_source_id on every visible_citation
            # (never reconstruct or default missing identity fields from retrieved documents)
            c_snap = cit.get("cited_snapshot_id")
            c_hash = cit.get("cited_content_hash")
            c_src = cit.get("cited_source_id")
            identity_present_and_well_formed = (
                isinstance(c_snap, str)
                and len(c_snap.strip()) > 0
                and isinstance(c_hash, str)
                and PREFIXED_SHA256_RE.match(c_hash) is not None
                and isinstance(c_src, str)
                and len(c_src.strip()) > 0
            )
            self.check(
                cat3,
                identity_present_and_well_formed,
                "ERR_CITATION_IDENTITY_INCOMPLETE",
                f"{tid}.{eid}.{cid}: missing, null, or malformed required citation identity field(s) (cited_snapshot_id={c_snap!r}, cited_content_hash={c_hash!r}, cited_source_id={c_src!r})",
            )
            if matched_doc is not None:
                self.check(
                    cat3,
                    cit.get("cited_doc_version") == matched_doc.get("doc_version"),
                    "ERR_CITATION_VERSION_MISMATCH",
                    f"{tid}.{eid}.{cid}: cited_doc_version {cit.get('cited_doc_version')} != {matched_doc.get('doc_version')}",
                )
                expected_snap = None
                for r_ev in retrievals_by_id.values():
                    for r_d in r_ev["attributes"].get("retrieved_documents", []):
                        if r_d.get("doc_id") == cit.get("cited_doc_id") and r_d.get(
                            "chunk_id"
                        ) == cit.get("cited_chunk_id"):
                            expected_snap = r_ev["attributes"].get("source_snapshot_id")
                snap_ok = (
                    identity_present_and_well_formed
                    and c_snap == expected_snap
                    and c_hash == matched_doc.get("content_hash")
                    and c_src == matched_doc.get("source_id", cit.get("cited_doc_id"))
                )
                self.check(
                    cat3,
                    snap_ok,
                    "ERR_CITATION_SNAPSHOT_MISMATCH",
                    f"{tid}.{eid}.{cid}: citation cited_snapshot_id/content_hash/source_id mismatch against observed retrieval",
                )
                actually_selected = (
                    matched_doc.get("included_in_prompt") is True
                    and matched_doc.get("chunk_id") in selected_cids_in_mc
                )
                self.check(
                    cat3,
                    cit.get("present_in_selected_context") is True and actually_selected,
                    "ERR_CITATION_CONTEXT_FLAG_MISMATCH",
                    f"{tid}.{eid}.{cid}: cited chunk {cit.get('cited_chunk_id')} was excluded from prompt context",
                )

        for clm in attrs.get("claim_to_source_spans", []):
            r_span = clm.get("response_char_span", {})
            if (
                isinstance(r_span, dict)
                and is_strict_int(r_span.get("start"))
                and is_strict_int(r_span.get("end"))
            ):
                self.check(
                    cat3,
                    resp_text[r_span["start"] : r_span["end"]] == clm.get("claim_text"),
                    "ERR_CLAIM_SPAN_MISMATCH",
                    f"{tid}.{eid}: claim_text span mismatch",
                )
            for ses in clm.get("source_evidence_spans", []):
                matched_ret_ev = retrievals_by_id.get(str(ses.get("retrieval_id")))
                matched_doc = None
                if matched_ret_ev:
                    for d in matched_ret_ev["attributes"].get("retrieved_documents", []):
                        if d.get("chunk_id") == ses.get("chunk_id"):
                            matched_doc = d
                            break
                self.check(
                    cat3,
                    matched_doc is not None,
                    "ERR_CITATION_SOURCE_UNRESOLVED",
                    f"{tid}.{eid}: source_evidence_span chunk {ses.get('chunk_id')} unresolved",
                )
                if matched_doc is not None:
                    s_quote = str(ses.get("source_quote", ""))
                    actually_in_prompt = (
                        matched_doc.get("included_in_prompt") is True
                        and matched_doc.get("chunk_id") in selected_cids_in_mc
                    )
                    self.check(
                        cat3,
                        ses.get("in_supplied_prompt_context") == actually_in_prompt
                        and actually_in_prompt is True,
                        "ERR_CITATION_CONTEXT_FLAG_MISMATCH",
                        f"{tid}.{eid}: in_supplied_prompt_context mismatch or excluded chunk cited",
                    )
                    if ses.get("in_supplied_prompt_context") is True:
                        c_slice = str(matched_doc.get("canonical_chunk_slice") or "")
                        self.check(
                            cat3,
                            matched_doc.get("included_in_prompt") is True
                            and s_quote in c_slice
                            and s_quote in prompt_str,
                            "ERR_CITATION_OUTSIDE_SELECTED_SLICE",
                            f"{tid}.{eid}: source_quote not inside canonical_chunk_slice and supplied prompt context",
                        )

    def _validate_budget_telemetry(
        self,
        tid: str,
        wt: dict[str, Any],
        events: list[dict[str, Any]],
        po_transition_events: list[dict[str, Any]],
    ) -> None:
        cat4 = "cat4_contracts_snapshots_bindings"

        ebt = wt.get("execution_budget_telemetry", {})
        counters = ebt.get("counters", {}) if isinstance(ebt, dict) else {}

        ledger = ebt.get("dispatch_claim_ledger")
        expected_ledger = [
            st["attributes"].get("dispatch_claim_consumption")
            for st in po_transition_events
            if isinstance(st["attributes"].get("dispatch_claim_consumption"), dict)
        ]
        self.check(
            cat4,
            isinstance(ledger, list) and ledger == expected_ledger,
            "ERR_CLAIM_CONSUMPTION_RECORD_INVALID",
            f"{tid}: execution_budget_telemetry.dispatch_claim_ledger mismatch with PO_CREATION transitions",
        )

        wql = ebt.get("workload_quota_ledger")
        if wql is not None:
            allowed_wql_keys = {
                "ledger_schema_version",
                "workload_bucket_id",
                "provider",
                "model_family",
                "quota_tier_status",
                "rpm_limit_configured",
                "tpm_limit_configured",
                "rpd_limit_configured",
                "trace_requests_debited",
                "trace_prompt_tokens_debited",
                "trace_completion_tokens_debited",
                "trace_total_tokens_debited",
                "rate_limit_429_count",
                "cooldown_wait_ms_total",
                "headroom_confirmation_ref",
            }
            obs_prompt_toks = 0
            obs_comp_toks = 0
            obs_tot_toks = 0
            for e in events:
                if e.get("event_type") == "model_call":
                    tu = e["attributes"].get("token_usage")
                    if isinstance(tu, dict):
                        obs_prompt_toks += int(tu.get("prompt_tokens", 0))
                        obs_comp_toks += int(tu.get("completion_tokens", 0))
                        obs_tot_toks += int(tu.get("total_tokens", 0))

            gen_debits = (counters.get("generation_attempt_debits") or {}).get("spent_count", 0)
            emb_debits = (counters.get("embedding_attempt_debits") or {}).get("spent_count", 0)
            expected_req_debits = gen_debits + emb_debits

            valid_wql = (
                isinstance(wql, dict)
                and set(wql.keys()) == allowed_wql_keys
                and wql.get("ledger_schema_version") == "od-llm-02-v1"
                and wql.get("workload_bucket_id")
                in {
                    "ONLINE_INTERACTIVE_APP",
                    "OFFLINE_DATASET_GENERATION",
                    "CI_RELEASE_GATE_BATCH",
                    "POST_RUN_LLM_JUDGE_EVALUATION",
                }
                and wql.get("provider") == wt.get("versions", {}).get("provider")
                and wql.get("model_family") == wt.get("versions", {}).get("configured_model_id")
                and wql.get("quota_tier_status")
                in {"UNCONFIRMED_HEADROOM_PENDING_VERIFICATION", "CONFIRMED_QUOTA_TIER"}
                and is_strict_int(wql.get("trace_requests_debited"))
                and wql.get("trace_requests_debited") == expected_req_debits
                and wql.get("trace_prompt_tokens_debited") == obs_prompt_toks
                and wql.get("trace_completion_tokens_debited") == obs_comp_toks
                and wql.get("trace_total_tokens_debited") == obs_tot_toks
                and wql.get("trace_prompt_tokens_debited", 0)
                + wql.get("trace_completion_tokens_debited", 0)
                == wql.get("trace_total_tokens_debited", 0)
                and is_strict_int(wql.get("rate_limit_429_count"))
                and is_strict_int(wql.get("cooldown_wait_ms_total"))
            )
            self.check(
                cat4,
                valid_wql,
                "ERR_WORKLOAD_QUOTA_LEDGER_INVALID",
                f"{tid}: invalid or unreconciled execution_budget_telemetry.workload_quota_ledger",
            )

        obs_tool_calls = sum(1 for e in events if e.get("event_type") == "tool_call")
        obs_tool_retries = sum(
            1
            for e in events
            if e.get("event_type") == "tool_call"
            and isinstance(e["attributes"].get("retry_accounting"), dict)
            and e["attributes"]["retry_accounting"].get("is_retry") is True
        )
        obs_model_calls = sum(1 for e in events if e.get("event_type") == "model_call")
        obs_model_retries = sum(
            1
            for e in events
            if e.get("event_type") == "model_call"
            and isinstance(e["attributes"].get("retry_accounting"), dict)
            and e["attributes"]["retry_accounting"].get("is_retry") is True
        )

        for cname, cobj in counters.items():
            if not isinstance(cobj, dict):
                continue
            spent = cobj.get("spent_count")
            prereq = cobj.get("prior_prerequisite_spent_count", 0)
            slice_obs = cobj.get("slice_observed_spent_count", 0)
            res = cobj.get("reserved_count", 0)
            rem = cobj.get("remaining_count", 0)
            ceil_val = cobj.get("configured_ceiling")
            arith_ok = (
                is_strict_int(spent)
                and is_strict_int(prereq)
                and is_strict_int(slice_obs)
                and spent == prereq + slice_obs
                and (ceil_val is None or (is_strict_int(rem) and spent + res + rem == ceil_val))
            )
            if cname == "logical_tool_operations":
                arith_ok = arith_ok and (slice_obs == obs_tool_calls - obs_tool_retries)
            elif cname == "tool_attempt_debits":
                arith_ok = arith_ok and (slice_obs == obs_tool_calls)
            elif cname == "logical_generation_operations":
                arith_ok = arith_ok and (slice_obs == obs_model_calls - obs_model_retries)
            elif cname == "generation_attempt_debits":
                arith_ok = arith_ok and (slice_obs == obs_model_calls + obs_model_retries)

            self.check(
                cat4,
                arith_ok,
                "ERR_BUDGET_COUNTER_INVALID",
                f"{tid}: budget counter {cname} failed arithmetic or slice reconciliation",
            )

    def _validate_ground_truth_isolation(
        self,
        tid: str,
        wt: dict[str, Any],
        retrievals_by_id: dict[str, dict[str, Any]],
    ) -> None:
        cat5 = "cat5_isolation_and_report"

        projected = project_trace_for_inference(wt)
        for fk in FORBIDDEN_INFERENCE_TOP_KEYS:
            self.check(
                cat5,
                fk not in projected,
                "ERR_GROUND_TRUTH_LEAK",
                f"{tid}: forbidden key {fk} in projection",
            )

        scen = wt.get("scenario_metadata", {})
        if not isinstance(scen, dict):
            return

        observed_doc_ids: set[str] = set()
        for ret_ev in retrievals_by_id.values():
            for d in ret_ev["attributes"].get("retrieved_documents", []):
                if isinstance(d.get("doc_id"), str):
                    observed_doc_ids.add(d["doc_id"])

        forbidden_tokens: set[str] = set()
        for k in ("injection_recipe_id", "injected_root_cause"):
            val = scen.get(k)
            if isinstance(val, str) and len(val) > 0:
                forbidden_tokens.add(val)
        ifc = scen.get("injected_failure_class")
        if isinstance(ifc, str) and ifc != "NORMAL":
            forbidden_tokens.add(ifc)

        for doc_id in scen.get("expected_relevant_doc_ids", []) or []:
            if isinstance(doc_id, str) and doc_id not in observed_doc_ids:
                forbidden_tokens.add(doc_id)

        sc = scen.get("security_category")
        if isinstance(sc, str) and len(sc) > 0:
            forbidden_tokens.add(sc)
        srole = scen.get("security_case_role")
        if isinstance(srole, str) and len(srole) > 0:
            forbidden_tokens.add(srole)

        sec_meta = scen.get("security_subset_metadata", {})
        if isinstance(sec_meta, dict):
            aci = sec_meta.get("attack_or_control_indicator")
            if isinstance(aci, str) and aci != "NOT_SECURITY_SCENARIO":
                forbidden_tokens.add(aci)

        runtime_blob = json.dumps(projected.get("events", []), ensure_ascii=False)
        for tok in sorted(forbidden_tokens):
            pattern = r"\b" + re.escape(tok) + r"\b"
            leaked = bool(re.search(pattern, runtime_blob))
            self.check(
                cat5,
                not leaked,
                "ERR_GROUND_TRUTH_LEAK",
                f"{tid}: ground-truth token {tok!r} leaked into runtime events",
            )

    def _validate_spec_tables_and_report(
        self, text: str, walkthroughs: list[dict[str, Any]]
    ) -> None:
        cat3 = "cat3_digests_hashes_spans"
        cat5 = "cat5_isolation_and_report"

        # OD-13: Verify deterministic trustops-canonical-json-v1 test vectors
        for vec_obj, expected_ser, expected_dig in CANONICAL_JSON_TEST_VECTORS:
            ser = canonical_json_bytes(vec_obj, enforce_domain=True, allow_floats=False).decode(
                "utf-8"
            )
            dig = compute_arguments_digest(vec_obj)
            self.check(
                cat3,
                ser == expected_ser and dig == expected_dig,
                "ERR_CANONICAL_JSON_VECTOR_MISMATCH",
                f"Canonical JSON test vector mismatch: got {ser} / {dig}",
            )

        for i in range(1, 28):
            code = f"E{i:02d}"
            self.check(
                cat5, f"**`{code}`" in text, "ERR_E01_E27_MISSING", f"Missing {code} row in §8.1"
            )
        for i in range(1, 9):
            wcode = f"WG-{i:02d}"
            self.check(
                cat5, f"**`{wcode}`**" in text, "ERR_WG_MISSING", f"Missing {wcode} row in §8.2"
            )

        self.check(
            cat5,
            "\r" not in text,
            "ERR_MALFORMED_CARRIAGE_RETURN",
            "Specification contains raw \\r character (malformed arrow or CRLF)",
        )

        if self.check_report_sync:
            expected_c5 = self.counts["cat5_isolation_and_report"] + 6
            expected_total = (
                self.counts["cat1_envelope_and_syntax"]
                + self.counts["cat2_ordering_and_refs"]
                + self.counts["cat3_digests_hashes_spans"]
                + self.counts["cat4_contracts_snapshots_bindings"]
                + expected_c5
            )
            for cname in (
                "cat1_envelope_and_syntax",
                "cat2_ordering_and_refs",
                "cat3_digests_hashes_spans",
                "cat4_contracts_snapshots_bindings",
                "cat5_isolation_and_report",
            ):
                cnt = expected_c5 if cname == "cat5_isolation_and_report" else self.counts[cname]
                self.check(
                    cat5,
                    f"(`{cname}`)** | {cnt} assertions | **PASS ({cnt}/{cnt})**" in text,
                    "ERR_REPORT_COUNT_MISMATCH",
                    f"Section 9.1 table count mismatch for {cname}: expected {cnt}",
                )
            self.check(
                cat5,
                f"| **Total Automated Specification & Fixture Assertions** | **{expected_total} assertions** | **PASS ({expected_total}/{expected_total}, 0 errors)** |"
                in text,
                "ERR_REPORT_TOTAL_MISMATCH",
                f"Section 9.1 total assertions mismatch: expected {expected_total}",
            )
        else:
            for _ in range(6):
                self.check(cat5, True, "ERR_NONE", "Pad report sync assertion count")


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate S1-01 Trace Schema v1.10 Specification")
    parser.add_argument(
        "spec_path", nargs="?", default=DEFAULT_SPEC_FILENAME, help="Path to updated_schemas_v18.md"
    )
    parser.add_argument(
        "--json-out", dest="json_out", default=None, help="Optional JSON report output path"
    )
    parser.add_argument(
        "--no-report-sync", action="store_true", help="Skip §9.1 assertion count table sync check"
    )
    parser.add_argument(
        "--approval-validation-profile",
        choices=list(APPROVAL_VALIDATION_PROFILES),
        default="provisional_draft",
        help=(
            "Approval validation profile: 'provisional_draft' (default; required for all procurement traces "
            "and enforces OD-04/SA-03 A1-A5 rules) or 'base_only' (restricted strictly to S1-03 Row 9 base "
            "Approval evidence validation; skips approval version/sequence checks at consumption)"
        ),
    )
    args = parser.parse_args()

    if not os.path.exists(args.spec_path) and args.spec_path == DEFAULT_SPEC_FILENAME:
        try:
            args.spec_path = str(_find_repo_file(DEFAULT_SPEC_FILENAME, pathlib.Path(__file__)))
        except FileNotFoundError:
            pass
    if not os.path.exists(args.spec_path):
        print(f"ERROR: Specification file not found: {args.spec_path}", file=sys.stderr)
        print('FAILURE_CODES_JSON: ["ERR_SPEC_FILE_NOT_FOUND"]')
        return 2

    approval_extension_status = (
        "PROVISIONAL_DRAFT_ENFORCEMENT_PENDING_JOINT_SIGN_OFF"
        if args.approval_validation_profile == "provisional_draft"
        else "BASE_APPROVAL_ONLY_OD04_SA03_EXCLUDED"
    )
    validator = SpecValidator(
        args.spec_path,
        check_report_sync=not args.no_report_sync,
        approval_validation_profile=args.approval_validation_profile,
    )
    passed, codes, counts = validator.validate()
    total_assertions = sum(counts.values())

    print(f"Validator Version: {VALIDATOR_VERSION}")
    print(f"Target Specification: {args.spec_path}")
    print(
        f"Approval Validation Profile: {args.approval_validation_profile} ({approval_extension_status})"
    )
    for k, v in counts.items():
        print(f"  {k}: {v} assertions")
    print(f"TOTAL_ASSERTIONS: {total_assertions}")
    print(f"TOTAL_FAILURES: {len(validator.failures)}")
    for f in validator.failures:
        print(f"  [FAIL] ({f['category']}) {f['code']}: {f['message']}")
    print(f"FAILURE_CODES_JSON: {json.dumps(codes)}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as jf:
            json.dump(
                {
                    "validator_version": VALIDATOR_VERSION,
                    "target_spec": os.path.basename(args.spec_path),
                    "approval_validation_profile": args.approval_validation_profile,
                    "approval_extension_status": approval_extension_status,
                    "passed": passed,
                    "total_assertions": total_assertions,
                    "total_failures": len(validator.failures),
                    "category_assertions": counts,
                    "failure_codes": codes,
                    "failures": validator.failures,
                },
                jf,
                indent=2,
            )

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
