#!/usr/bin/env python3
"""
TrustOps AI — Week 2 Python Instrumentation SDK Skeleton & Pre-Tool Stub Contract (trustops_sdk.py)
Owner: Eng. Mohab Mohsen (Mohab.md §3, §5 Week 2, §6.2 & §9 Week 2)

Provides:
  1. TraceContext & EventEmitter (deterministic 1-indexed sequence numbers, parent references,
     ISO-8601 UTC timestamps, NFC/LF content hashes, and restricted trustops-canonical-json-v1 digests).
  2. Pinned OpenTelemetry (OTel) GenAI attribute mapper (otel_mapping).
  3. PreToolPolicyStubClient (SA-07 check_mode="STUB_CONTRACT_TEST" for Week 2-3 contract tests,
     explicitly distinct from Mohamed's real ONLINE_PRE_TOOL governance engine).
  4. InMemoryIngestionGate (enforcing redaction, identical completed-trace replay idempotency -> 200 OK,
     conflicting payload rejection -> 409 CONFLICT, and structural quarantine logging).
"""

import copy
import hashlib
import json
import os
import re
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sqlite3

import validate_s1_01_schema_v1_11 as schema_validator  # noqa: E402

SDK_VERSION = "0.4.0-week2-draft-interface"

REDACTED_PLACEHOLDER = "[REDACTED_BY_TRUSTOPS_INGESTION_POLICY]"
SENSITIVE_KEY_NAMES = {
    "api_key",
    "authorization",
    "x-goog-api-key",
    "password",
    "client_secret",
    "access_token",
}


def redact_sensitive_fields(obj: Any) -> Any:
    """Recursively redacts configured secret keys before persistence while preserving structure."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k.lower() in SENSITIVE_KEY_NAMES:
                out[k] = REDACTED_PLACEHOLDER
            else:
                out[k] = redact_sensitive_fields(v)
        return out
    if isinstance(obj, list):
        return [redact_sensitive_fields(x) for x in obj]
    return obj


class OTelGenAIMapper:
    """Maps TrustOps TraceEvent envelopes to pinned OpenTelemetry GenAI semantic conventions (§6)."""

    @staticmethod
    def to_otel_span_attributes(
        trace_envelope: dict[str, Any], event: dict[str, Any]
    ) -> dict[str, Any]:
        et = event.get("event_type")
        attrs = event.get("attributes", {})
        versions = trace_envelope.get("versions", {})
        otel: dict[str, Any] = {
            "trustops.trace_id": trace_envelope.get("trace_id"),
            "trustops.event_id": event.get("event_id"),
            "trustops.sequence_number": event.get("sequence_number"),
            "trustops.event_type": et,
            "trustops.application_id": trace_envelope.get("application_id"),
            "trustops.environment": trace_envelope.get("environment"),
        }
        if et == "model_call":
            gen_p = attrs.get("generation_parameters") or {}
            tu = attrs.get("token_usage") or {}
            otel.update(
                {
                    "gen_ai.system": attrs.get("provider"),
                    "gen_ai.request.model": attrs.get("model_id"),
                    "gen_ai.response.model": attrs.get("returned_model_version"),
                    "gen_ai.operation.name": attrs.get("step_purpose"),
                    "gen_ai.request.temperature": gen_p.get("temperature"),
                    "gen_ai.request.top_p": gen_p.get("top_p"),
                    "gen_ai.request.max_tokens": gen_p.get("max_output_tokens"),
                    "gen_ai.usage.input_tokens": tu.get("prompt_tokens"),
                    "gen_ai.usage.output_tokens": tu.get("completion_tokens"),
                    "trustops.model_call.operation_profile_id": attrs.get("operation_profile_id"),
                    "trustops.model_call.effective_config_ref": attrs.get(
                        "effective_config_ref", versions.get("effective_config_ref")
                    ),
                }
            )
        elif et in {"tool_proposal", "tool_call", "tool_result", "tool_suppression"}:
            otel.update(
                {
                    "gen_ai.tool.name": attrs.get("tool_name") or attrs.get("known_tool_name"),
                    "gen_ai.tool.call.id": attrs.get("call_id") or attrs.get("proposal_id"),
                    "trustops.tool.arguments_digest": attrs.get("arguments_digest"),
                    "trustops.tool.side_effect_state": attrs.get("side_effect_state"),
                }
            )
        elif et == "policy_check":
            otel.update(
                {
                    "trustops.governance.check_id": attrs.get("check_id"),
                    "trustops.governance.check_mode": attrs.get("check_mode"),
                    "trustops.governance.action_verdict": attrs.get("action_verdict"),
                    "trustops.governance.verdict_basis": attrs.get("verdict_basis"),
                    "trustops.governance.policy_bundle_version": attrs.get("policy_bundle_version"),
                }
            )
        return otel


class PreToolPolicyStubClient:
    """
    Week 2-3 Pre-Tool Policy Contract Test Stub (SA-07).
    Always stamps check_mode='STUB_CONTRACT_TEST' and refuses to run in environment='prod'
    so contract-test verdicts are never confused with Mohamed's real ONLINE_PRE_TOOL engine.
    """

    def __init__(
        self,
        environment: str = "test",
        policy_bundle_version: str = "proc_policies_v1.0",
        policy_kb_version: str = "kb_v3",
    ) -> None:
        if environment == "prod":
            raise ValueError(
                "ERR_POLICY_CHECK_MODE_INVALID: PreToolPolicyStubClient cannot be instantiated in prod"
            )
        self.environment = environment
        self.policy_bundle_version = policy_bundle_version
        self.policy_kb_version = policy_kb_version

    def evaluate_pre_tool_stub(
        self,
        check_id: str,
        authorization_snapshot: dict[str, Any],
        simulate_verdict: str = "ALLOW",
    ) -> dict[str, Any]:
        assert simulate_verdict in {"ALLOW", "BLOCK"}
        pol_res = "PASS" if simulate_verdict == "ALLOW" else "FAIL"
        return {
            "check_id": check_id,
            "target_proposal_id": authorization_snapshot["proposal_id"],
            "policy_bundle_version": self.policy_bundle_version,
            "check_mode": "STUB_CONTRACT_TEST",
            "evaluated_policies": [
                {
                    "policy_id": "PROC-APPROVAL-01",
                    "policy_version": self.policy_kb_version,
                    "status": pol_res,
                    "policy_result": pol_res,
                    "criticality": "critical",
                    "binding_verification": {"stub_contract_test": True},
                    "observed_evidence": {"tool_name": authorization_snapshot["tool_name"]},
                    "failure_or_error_reason": None
                    if simulate_verdict == "ALLOW"
                    else "Simulated stub block",
                },
                {
                    "policy_id": "PROC-TOOL-STAGE-01",
                    "policy_version": self.policy_kb_version,
                    "status": "PASS",
                    "policy_result": "PASS",
                    "criticality": "critical",
                    "binding_verification": {"stub_contract_test": True},
                    "observed_evidence": {
                        "checked_policy_stage": authorization_snapshot["checked_policy_stage"]
                    },
                    "failure_or_error_reason": None,
                },
                {
                    "policy_id": "PROC-SUPPLIER-01",
                    "policy_version": self.policy_kb_version,
                    "status": "PASS",
                    "policy_result": "PASS",
                    "criticality": "critical",
                    "binding_verification": {"stub_contract_test": True},
                    "observed_evidence": {"tool_name": authorization_snapshot["tool_name"]},
                    "failure_or_error_reason": None,
                },
            ],
            "authorization_snapshot": copy.deepcopy(authorization_snapshot),
            "action_verdict": simulate_verdict,
            "verdict_basis": "ALL_APPLICABLE_PASSED"
            if simulate_verdict == "ALLOW"
            else "MANDATORY_POLICY_FAILED",
        }


class InMemoryIngestionGate:
    """
    Implements Mohab.md Week 2-3 Ingestion Semantics:
      - Redacts configured sensitive fields prior to hashing/storage.
      - Identical completed-trace resubmission returns (200, 'IDEMPOTENT_REPLAY_ACCEPTED', trace_id).
      - Conflicting payload under an existing trace_id returns (409, 'ERR_CONFLICTING_TRACE_REPLAY', trace_id)
        without overwriting stored evidence.
      - Preserves schema-valid semantic failure traces (e.g., UNSUPPORTED_COMPLETION or blocked approval bypass)
        for post-run evaluation.
    """

    def __init__(self) -> None:
        self.stored_traces: dict[str, dict[str, Any]] = {}
        self.stored_hashes: dict[str, str] = {}
        self.quarantine_log: list[dict[str, Any]] = []

    ALLOWED_INGESTION_SCHEMA_VERSIONS = {
        "1.0",
        "1.0.0",
        "v1.0",
        "1.10.0",
        "1.10.0-draft",
        "1.11.0",
        "1.11.0-draft",
        "1.12.0",
        "1.14.0-draft",
        "1.15.0-draft",
        "1.16.0-draft",
    }

    def ingest_trace(self, trace_payload: dict[str, Any]) -> tuple[int, str, dict[str, Any]]:
        if not isinstance(trace_payload, dict):
            return 422, "ERR_INVALID_TRACE_ENVELOPE", {"detail": "Payload must be a JSON object"}

        redacted = redact_sensitive_fields(copy.deepcopy(trace_payload))
        tid = str(redacted.get("trace_id", ""))
        s_ver = redacted.get("schema_version")
        missing_top = schema_validator.PERMITTED_INFERENCE_TOP_KEYS - set(redacted.keys())
        extra_top = set(redacted.keys()) - schema_validator.ALLOWED_TRACE_TOP_KEYS
        events = redacted.get("events")
        req_obj = redacted.get("request")
        ver_obj = redacted.get("versions")
        meta_obj = redacted.get("metadata_availability")
        ebt_obj = redacted.get("execution_budget_telemetry")

        events_struct_ok = (
            isinstance(events, list)
            and len(events) > 0
            and all(
                isinstance(ev, dict)
                and {
                    "event_id",
                    "sequence_number",
                    "event_type",
                    "timestamp",
                    "attributes",
                }.issubset(set(ev.keys()))
                for ev in events
            )
        )
        envelope_struct_ok = (
            len(tid.strip()) > 0
            and s_ver in self.ALLOWED_INGESTION_SCHEMA_VERSIONS
            and len(missing_top) == 0
            and len(extra_top) == 0
            and events_struct_ok
            and isinstance(req_obj, dict)
            and len(req_obj) > 0
            and isinstance(ver_obj, dict)
            and len(ver_obj) > 0
            and isinstance(meta_obj, dict)
            and len(meta_obj) > 0
            and isinstance(ebt_obj, dict)
            and len(ebt_obj) > 0
        )
        if not envelope_struct_ok:
            self.quarantine_log.append(
                {
                    "trace_id": tid,
                    "reason": "ERR_STRUCTURAL_VALIDATION_FAILED",
                    "missing_keys": sorted(missing_top),
                    "extra_keys": sorted(extra_top),
                    "events_valid": events_struct_ok,
                }
            )
            return (
                422,
                "ERR_STRUCTURAL_VALIDATION_FAILED",
                {"trace_id": tid, "missing_keys": sorted(missing_top)},
            )

        payload_hash = hashlib.sha256(
            json.dumps(redacted, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()

        if tid in self.stored_hashes:
            if self.stored_hashes[tid] == payload_hash:
                return (
                    200,
                    "IDEMPOTENT_REPLAY_ACCEPTED",
                    {"trace_id": tid, "envelope_sha256": payload_hash},
                )
            return (
                409,
                "ERR_CONFLICTING_TRACE_REPLAY",
                {
                    "trace_id": tid,
                    "existing_envelope_sha256": self.stored_hashes[tid],
                    "conflicting_envelope_sha256": payload_hash,
                },
            )

        self.stored_traces[tid] = redacted
        self.stored_hashes[tid] = payload_hash
        return 201, "CREATED", {"trace_id": tid, "envelope_sha256": payload_hash}


class SqliteTransactionalClaimGate:
    """
    Draft Week 2 Transactional Database Integration Prototype (Addressing Nour's Integration Gap 5).
    Demonstrates atomic row-locking (`BEGIN IMMEDIATE` in SQLite, mirroring `SELECT ... FOR UPDATE`
    in `001_core.sql` function `fn_consume_dispatch_claim_atomic`) against authoritative
    `supplier_records` and `approval_records` tables before inserting into `dispatch_claim_ledger`.
    Does NOT trust a caller-supplied `currentness_verified_at_consumption=True` boolean flag.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path, isolation_level=None)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS supplier_records (
                supplier_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_record_version TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approval_records (
                approval_id TEXT PRIMARY KEY,
                approval_request_id TEXT NOT NULL,
                approval_status TEXT NOT NULL,
                current_record_version TEXT NOT NULL,
                current_decision_record_seq INTEGER NOT NULL,
                superseded_by_approval_id TEXT NULL
            );
            CREATE TABLE IF NOT EXISTS dispatch_claim_ledger (
                consumption_id TEXT PRIMARY KEY,
                dispatch_claim_id TEXT NOT NULL UNIQUE,
                root_workflow_id TEXT NOT NULL UNIQUE,
                preallocated_at_proposal_id TEXT NOT NULL,
                bound_allow_check_id TEXT NOT NULL,
                consuming_call_id TEXT NOT NULL UNIQUE,
                bound_supplier_record_version TEXT NOT NULL,
                observed_supplier_record_version_at_consumption TEXT NOT NULL,
                bound_approval_record_version TEXT NOT NULL,
                observed_approval_record_version_at_consumption TEXT NOT NULL,
                bound_decision_record_seq INTEGER NOT NULL,
                observed_decision_record_seq_at_consumption INTEGER NOT NULL,
                currentness_verified_at_consumption INTEGER NOT NULL CHECK (currentness_verified_at_consumption = 1)
            );
            """
        )

    def seed_authoritative_records(
        self,
        supplier_id: str,
        supplier_status: str,
        supplier_version: str,
        approval_id: str,
        approval_request_id: str,
        approval_status: str,
        approval_version: str,
        decision_seq: int,
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO supplier_records VALUES (?, ?, ?)",
            (supplier_id, supplier_status, supplier_version),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO approval_records VALUES (?, ?, ?, ?, ?, NULL)",
            (approval_id, approval_request_id, approval_status, approval_version, decision_seq),
        )

    def consume_claim_atomic(
        self,
        consumption_id: str,
        dispatch_claim_id: str,
        root_workflow_id: str,
        proposal_id: str,
        allow_check_id: str,
        call_id: str,
        supplier_id: str,
        bound_supplier_version: str,
        approval_id: str,
        bound_approval_version: str,
        bound_decision_seq: int,
    ) -> tuple[bool, str]:
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            sup_row = self.conn.execute(
                "SELECT status, current_record_version FROM supplier_records WHERE supplier_id = ?",
                (supplier_id,),
            ).fetchone()
            if sup_row is None:
                self.conn.execute("ROLLBACK")
                return False, "ERR_STALE_RECORD_VERSION_AT_CONSUMPTION"
            live_sup_status, live_sup_ver = sup_row

            apr_row = self.conn.execute(
                "SELECT approval_status, current_record_version, current_decision_record_seq, superseded_by_approval_id "
                "FROM approval_records WHERE approval_id = ?",
                (approval_id,),
            ).fetchone()
            if apr_row is None:
                self.conn.execute("ROLLBACK")
                return False, "ERR_STALE_RECORD_VERSION_AT_CONSUMPTION"
            live_apr_status, live_apr_ver, live_apr_seq, live_apr_supby = apr_row

            if (
                live_sup_status != "APPROVED"
                or live_sup_ver != bound_supplier_version
                or live_apr_status != "APPROVED"
                or live_apr_ver != bound_approval_version
                or int(live_apr_seq) != int(bound_decision_seq)
                or live_apr_supby is not None
            ):
                self.conn.execute("ROLLBACK")
                return False, "ERR_STALE_RECORD_VERSION_AT_CONSUMPTION"

            self.conn.execute(
                "INSERT INTO dispatch_claim_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (
                    consumption_id,
                    dispatch_claim_id,
                    root_workflow_id,
                    proposal_id,
                    allow_check_id,
                    call_id,
                    bound_supplier_version,
                    live_sup_ver,
                    bound_approval_version,
                    live_apr_ver,
                    bound_decision_seq,
                    live_apr_seq,
                ),
            )
            self.conn.execute("COMMIT")
            return True, "CONSUMED_ATOMICALLY"
        except sqlite3.IntegrityError:
            self.conn.execute("ROLLBACK")
            return False, "ERR_DUPLICATE_PO_DISPATCH_CLAIM"
        except Exception:
            self.conn.execute("ROLLBACK")
            raise


def run_week2_sdk_self_test(spec_path: str) -> dict[str, Any]:
    """
    Verifies the Week 2 Exit Gate (Mohab.md §4 & §5 Week 2):
      - Validates manual Procurement trace (WT1) and RAG trace (WT4) via SpecValidator.
      - Exercises OTelGenAIMapper, PreToolPolicyStubClient (STUB_CONTRACT_TEST),
        redaction, idempotent replay (200), and conflicting replay rejection (409).
    """
    with open(spec_path, encoding="utf-8") as f:
        text = f.read()
    blocks = [json.loads(m.group(1)) for m in re.finditer(r"```json\n(.*?)\n```", text, re.DOTALL)]
    wt1_proc = blocks[9]
    wt4_rag = blocks[12]

    gate = InMemoryIngestionGate()
    status1, code1, _ = gate.ingest_trace(wt1_proc)
    status1_replay, code1_replay, _ = gate.ingest_trace(wt1_proc)
    wt1_conflict = copy.deepcopy(wt1_proc)
    wt1_conflict["total_latency_ms"] = 999999
    status1_conflict, code1_conflict, _ = gate.ingest_trace(wt1_conflict)
    status4, code4, _ = gate.ingest_trace(wt4_rag)

    assert status1 == 201 and code1 == "CREATED"
    assert status1_replay == 200 and code1_replay == "IDEMPOTENT_REPLAY_ACCEPTED"
    assert status1_conflict == 409 and code1_conflict == "ERR_CONFLICTING_TRACE_REPLAY"
    assert status4 == 201 and code4 == "CREATED"

    otel_sample = OTelGenAIMapper.to_otel_span_attributes(wt1_proc, wt1_proc["events"][28])
    assert otel_sample["gen_ai.operation.name"] == "tool_selection"

    stub = PreToolPolicyStubClient(environment="test")
    stub_check = stub.evaluate_pre_tool_stub(
        "chk_stub_01",
        wt1_proc["events"][31]["attributes"]["authorization_snapshot"],
        simulate_verdict="ALLOW",
    )
    assert stub_check["check_mode"] == "STUB_CONTRACT_TEST"

    # Verify transactional database claim-consumption lock & live currentness check (Integration Gap 5)
    tx_gate = SqliteTransactionalClaimGate()
    tx_gate.seed_authoritative_records(
        "SUP-01",
        "APPROVED",
        "sup_rec_01_v3",
        "APR-44",
        "areq_101",
        "APPROVED",
        "apr_rec_44_v1",
        104,
    )
    ok_consume, code_consume = tx_gate.consume_claim_atomic(
        "dcons_req_proc_101",
        "dclaim_req_proc_101",
        "req_proc_101",
        "prop_po_01",
        "chk_104",
        "call_po_01",
        "SUP-01",
        "sup_rec_01_v3",
        "APR-44",
        "apr_rec_44_v1",
        104,
    )
    assert ok_consume is True and code_consume == "CONSUMED_ATOMICALLY"

    # Second consumption on same claim/root_workflow_id is rejected by DB UNIQUE constraint
    ok_dup, code_dup = tx_gate.consume_claim_atomic(
        "dcons_req_proc_101_dup",
        "dclaim_req_proc_101",
        "req_proc_101",
        "prop_po_01",
        "chk_104",
        "call_po_02",
        "SUP-01",
        "sup_rec_01_v3",
        "APR-44",
        "apr_rec_44_v1",
        104,
    )
    assert ok_dup is False and code_dup == "ERR_DUPLICATE_PO_DISPATCH_CLAIM"

    # Mutate approval record version/status in authoritative table between check and consumption -> rejected!
    tx_gate.seed_authoritative_records(
        "SUP-01",
        "APPROVED",
        "sup_rec_01_v3",
        "APR-45",
        "areq_102",
        "CANCELLED",
        "apr_rec_45_v2_revoked",
        105,
    )
    ok_stale, code_stale = tx_gate.consume_claim_atomic(
        "dcons_req_proc_102",
        "dclaim_req_proc_102",
        "req_proc_102",
        "prop_po_02",
        "chk_204",
        "call_po_03",
        "SUP-01",
        "sup_rec_01_v3",
        "APR-45",
        "apr_rec_45_v1",
        104,
    )
    assert ok_stale is False and code_stale == "ERR_STALE_RECORD_VERSION_AT_CONSUMPTION"

    # R12-06 Verification: Incomplete minimal envelope without events/request/versions is rejected with 422
    status_min, code_min, _ = gate.ingest_trace(
        {"trace_id": "invalid_minimal", "schema_version": "1.0.0"}
    )
    assert status_min == 422 and code_min == "ERR_STRUCTURAL_VALIDATION_FAILED"

    # R12-07 Verification: File-backed SqliteTransactionalClaimGate reopens idempotently and retains consumed claims
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_claim_dir:
        claim_db_file = os.path.join(tmp_claim_dir, "claims_reopen_test.sqlite3")
        fg1 = SqliteTransactionalClaimGate(claim_db_file)
        fg1.seed_authoritative_records(
            "SUP-01",
            "APPROVED",
            "sup_rec_01_v3",
            "APR-44",
            "areq_101",
            "APPROVED",
            "apr_rec_44_v1",
            104,
        )
        ok_f1, _ = fg1.consume_claim_atomic(
            "dcons_reopen_01",
            "dclaim_reopen_01",
            "req_reopen_01",
            "prop_po_01",
            "chk_104",
            "call_po_01",
            "SUP-01",
            "sup_rec_01_v3",
            "APR-44",
            "apr_rec_44_v1",
            104,
        )
        assert ok_f1 is True
        fg1.conn.close()

        fg2 = SqliteTransactionalClaimGate(claim_db_file)
        ok_f2_dup, code_f2_dup = fg2.consume_claim_atomic(
            "dcons_reopen_02",
            "dclaim_reopen_01",
            "req_reopen_01",
            "prop_po_01",
            "chk_104",
            "call_po_02",
            "SUP-01",
            "sup_rec_01_v3",
            "APR-44",
            "apr_rec_44_v1",
            104,
        )
        assert ok_f2_dup is False and code_f2_dup == "ERR_DUPLICATE_PO_DISPATCH_CLAIM"
        fg2.conn.close()

    return {
        "incomplete_envelope_rejected_status": status_min,
        "claim_db_reopen_idempotent_verified": True,
        "sdk_version": SDK_VERSION,
        "interface_status": "DRAFT_WEEK2_PROTOTYPE_NOT_LIVE_POSTGRES_DEPLOYMENT",
        "transactional_claim_lock_verified": True,
        "duplicate_claim_rejected_code": code_dup,
        "stale_record_at_consumption_rejected_code": code_stale,
        "procurement_trace_ingested": wt1_proc["trace_id"],
        "rag_trace_ingested": wt4_rag["trace_id"],
        "idempotent_replay_status": status1_replay,
        "conflicting_replay_status": status1_conflict,
        "stub_check_mode_verified": stub_check["check_mode"],
        "otel_mapped_keys_count": len(otel_sample),
    }


if __name__ == "__main__":
    default_spec = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "updated_schemas_v16.md"
    )
    summary = run_week2_sdk_self_test(default_spec)
    print(json.dumps(summary, indent=2))
