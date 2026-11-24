#!/usr/bin/env python3
"""
TrustOps AI — Isolated G01 Diagnostic Runner (OD-LLM-02 v0.9 — Package Release v1.14.0)
Reference Plan: docs/architecture/reference-applications/workload-review/od-llm02-v0.2/g01-diagnostic-plan-2026-11-15.md
Historical Baseline (Read-Only / Protected): bounded-live-results-2026-11-09.json, results.json, results (1).json

OPERATIONAL NOTICE:
  G01 REMAINS ON HOLD — Do NOT run live against the Gemini API until Nour El-Rouby & Team sign off.
  Paid-use authorization remains USD 0. No model substitution or historical-result reclassification
  is performed by this runner.

v0.9.0-isolated-g01 Controls (Addressing Nour's v1.13 Review Evidence):
  1. Structured Admission Evidence Validation (RR-02):
     - Rejects count-only (`pre_dispatch_observations_count=2`) or pause-only (`consumer_pause_confirmed=True`)
       flags when structured observation evidence, pause window/reference, or confirmed headroom are absent.
     - Validates >= 2 observation records with unique `observation_id`, valid ISO-8601 `observed_at` timestamps
       separated by at least 15 minutes (>= 900 seconds), matching `project_id` and `model_id`,
       `reported_activity_status == "ZERO_ACTIVITY"` with `observed_request_count == 0` (explicitly rejecting
       `"NO_DATA_AVAILABLE"` / `"No data available"`), and non-empty `evidence_ref`.
     - Requires `consumer_pause_confirmed == True`, non-empty `consumer_pause_evidence_ref`, valid
       `consumer_pause_window.{start_at, end_at}`, and `dashboard_headroom_status == "CONFIRMED_HEADROOM_AVAILABLE"`.
     - Explicitly records `human_operator_confirmation_required: True` and `runner_verified_dashboard_truth: False`
       because schema validation cannot independently verify external dashboard truth.
     - Supports `--admission-record <path.json>` on CLI for portable Windows & Linux usage.
  2. Timeout & Whole-Session Lock Lifetime Safety (RR-06 & RR-03):
     - Live REST requests (`transport is None`) or `use_subprocess_worker=True` execute inside a terminable
       child process (`multiprocessing` spawn worker) killed via `proc.terminate()/kill()/join()` at the
       deadline BEFORE releasing `session.lock`, guaranteeing local worker and socket shutdown.
     - In-process custom transports (`httpx.MockTransport`) close `client`/`transport` on timeout; if an
       uncancellable in-process mock closure remains blocked, ownership of the held `session.lock` is
       transferred to a daemon reaper thread that holds `session.lock` until `worker_thread.join()` completes,
       so `session.lock` is NEVER reacquired while a timed-out worker is still active.
     - Always preserves the SQLite attempt debit (`completed = NULL`) and `TIMEOUT_OUTCOME_UNKNOWN`
       (`provider_remote_cancellation_inferred: False`).
  3. Cross-Platform Windows & POSIX Support:
     - Zero unconditional `fcntl` imports anywhere in the runner or bundled probes; uses `msvcrt.locking`
       on native Windows and `fcntl.flock` on POSIX.
"""

import argparse
import contextlib
import datetime
import getpass
import importlib
import json
import multiprocessing
import os
import re
import sqlite3
import sys
import threading
import time
from collections.abc import Iterator
from typing import Any

_posix_fcntl: Any = None
try:
    _posix_fcntl = importlib.import_module("fcntl")
except ImportError:
    _posix_fcntl = None

_win_msvcrt: Any = None
try:
    _win_msvcrt = importlib.import_module("msvcrt")
except ImportError:
    _win_msvcrt = None

import httpx  # noqa: E402

RUNNER_VERSION = "0.9.0-isolated-g01"
PACKAGE_RELEASE_ID = "v1.18.0"
DEFAULT_MODEL_ID = "gemini-3.8-flash"
DEFAULT_SQLITE_SMOKE_LEDGER = "smoke_ledger.sqlite3"
SESSION_LOCK_FILENAME = "session.lock"
DEFAULT_TIMEOUT_MS = 60000
DEFAULT_SPACING_MS = 31000
DEFAULT_SESSION_CEILING_MS = 900000
MIN_OBSERVATION_SPACING_SECONDS = 900.0  # 15 minutes minimum required spacing
MAX_OBSERVATION_AGE_SECONDS = 7200.0  # 2 hours max age for earliest observation
MAX_LATEST_OBSERVATION_AGE_SECONDS = 1800.0  # 30 minutes max age for latest observation
MAX_FUTURE_CLOCK_SKEW_SECONDS = 60.0  # 60s future clock skew tolerance
ROLLING_24H_WINDOW_SECONDS = 86400.0
FOUR_DEBIT_RESERVATION_REQUIRED = 4
ROLLING_24H_DEBIT_ALLOWANCE = 20
ROLLING_24H_RUN_RESERVATION_CAP = 2

G01_SYNTHETIC_PROMPT_TEXT = (
    "Context: [POL-114 v3.0] Purchases above $5,000.00 USD require manager approval. "
    "Question: What approval is required for a $16,000.00 USD laptop order?"
)

PROTECTED_HISTORICAL_FILENAMES = {
    "bounded-live-results-2026-11-09.json",
    "results.json",
    "results (1).json",
}

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z\-_]{10,}"),
    re.compile(r"(?i)(bearer\s+)[0-9A-Za-z\-_\.~+/]+=*"),
    re.compile(r"(?i)(key=)[0-9A-Za-z\-_]{8,}"),
    re.compile(r"(?i)(x-goog-api-key\s*[:=]\s*)[^\s,;\"']+"),
]


def sanitize_text(text: str) -> str:
    """Removes API keys, bearer tokens, query-string keys, and multiline tracebacks."""
    if not text:
        return ""
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    cleaned = first_line
    for pat in SECRET_PATTERNS:
        cleaned = pat.sub("[REDACTED_CREDENTIAL]", cleaned)
    return cleaned[:240]


_UTC: datetime.tzinfo = (
    datetime.UTC if sys.version_info >= (3, 11) else datetime.timezone(datetime.timedelta(0))
)


def utc_now_iso() -> str:
    return datetime.datetime.now(_UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso8601_utc(ts: Any) -> datetime.datetime | None:
    if not isinstance(ts, str) or not ts.strip():
        return None
    raw = ts.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            return None
        return dt.astimezone(_UTC)
    except ValueError:
        return None


def validate_admission_evidence(
    expected_model_id: str,
    expected_project_id: str | None,
    pre_dispatch_observations: list[dict[str, Any]] | None,
    consumer_pause_confirmed: bool,
    consumer_pause_evidence_ref: str | None,
    consumer_pause_window: dict[str, Any] | None,
    dashboard_headroom_status: str,
    now_utc: datetime.datetime | None = None,
    session_ceiling_ms: int = DEFAULT_SESSION_CEILING_MS,
    max_observation_age_seconds: float = MAX_OBSERVATION_AGE_SECONDS,
    max_latest_observation_age_seconds: float = MAX_LATEST_OBSERVATION_AGE_SECONDS,
) -> tuple[bool, list[str], float | None]:
    """
    Validates structured admission evidence against all agreed OD-LLM-02 admission conditions:
      - Exact non-empty `expected_project_id` must be explicitly provided (no arbitrary project accepted).
      - At least 2 structured observation records with unique observation_id, ISO-8601 observed_at,
        matching project_id (equal to expected_project_id) and model_id, reported_activity_status == 'ZERO_ACTIVITY',
        observed_request_count == 0, and non-empty evidence_ref.
      - Observation timestamps must be non-future (<= now_utc + 60s), fresh (earliest within
        max_observation_age_seconds and latest within max_latest_observation_age_seconds),
        and separated by at least 15 minutes (>= 900 seconds).
      - consumer_pause_confirmed == True, non-empty consumer_pause_evidence_ref, and valid
        consumer_pause_window.{start_at, end_at} that actively covers the planned diagnostic session
        (start_at <= now_utc and end_at >= now_utc + session_ceiling_ms).
      - dashboard_headroom_status == 'CONFIRMED_HEADROOM_AVAILABLE'.
    Note: Schema validation of file references cannot prove what an operator's screenshot shows;
    human verification of dashboard truth remains mandatory.
    Returns (is_valid, list_of_errors, observation_span_seconds).
    """
    ref_now = now_utc.astimezone(_UTC) if now_utc is not None else datetime.datetime.now(_UTC)
    errors: list[str] = []

    if not isinstance(expected_project_id, str) or not expected_project_id.strip():
        errors.append(
            "MISSING_REQUIRED_PROJECT_ID: Exact expected project_id (--project-id) must be explicitly provided"
        )
        norm_expected_proj: str | None = None
    else:
        norm_expected_proj = expected_project_id.strip()

    if not isinstance(pre_dispatch_observations, list) or len(pre_dispatch_observations) < 2:
        errors.append(
            "Requires at least 2 structured pre_dispatch_observations records (count-only flags are rejected)"
        )
        obs_list: list[dict[str, Any]] = []
    else:
        obs_list = pre_dispatch_observations

    seen_ids: set[str] = set()
    seen_projects: set[str] = set()
    parsed_dts: list[datetime.datetime] = []

    for idx, obs in enumerate(obs_list):
        if not isinstance(obs, dict):
            errors.append(f"pre_dispatch_observations[{idx}] must be an object")
            continue
        obs_id = obs.get("observation_id")
        if not isinstance(obs_id, str) or not obs_id.strip():
            errors.append(
                f"pre_dispatch_observations[{idx}].observation_id must be a non-empty string"
            )
        elif obs_id in seen_ids:
            errors.append(f"Duplicate observation_id {obs_id!r}")
        else:
            seen_ids.add(obs_id)

        dt = parse_iso8601_utc(obs.get("observed_at"))
        if dt is None:
            errors.append(
                f"pre_dispatch_observations[{idx}].observed_at must be a timezone-aware ISO-8601 timestamp"
            )
        else:
            if (dt - ref_now).total_seconds() > MAX_FUTURE_CLOCK_SKEW_SECONDS:
                errors.append(
                    f"FUTURE_OBSERVATION_TIMESTAMP: pre_dispatch_observations[{idx}].observed_at ({obs.get('observed_at')}) is in the future relative to {ref_now.isoformat()}"
                )
            age_sec = (ref_now - dt).total_seconds()
            if age_sec > max_observation_age_seconds:
                errors.append(
                    f"EXPIRED_OR_STALE_OBSERVATION: pre_dispatch_observations[{idx}].observed_at is {int(age_sec)}s old (max allowed {int(max_observation_age_seconds)}s)"
                )
            parsed_dts.append(dt)

        proj = obs.get("project_id")
        if not isinstance(proj, str) or not proj.strip():
            errors.append(f"pre_dispatch_observations[{idx}].project_id must be a non-empty string")
        else:
            seen_projects.add(proj.strip())
            if norm_expected_proj and proj.strip() != norm_expected_proj:
                errors.append(
                    f"PROJECT_ID_MISMATCH: pre_dispatch_observations[{idx}].project_id {proj!r} does not match expected {norm_expected_proj!r}"
                )

        mod = obs.get("model_id")
        if not isinstance(mod, str) or mod.strip() != expected_model_id:
            errors.append(
                f"pre_dispatch_observations[{idx}].model_id {mod!r} does not match target model {expected_model_id!r}"
            )

        act_status = str(obs.get("reported_activity_status") or "").strip()
        if act_status != "ZERO_ACTIVITY":
            errors.append(
                f"pre_dispatch_observations[{idx}].reported_activity_status must be 'ZERO_ACTIVITY' (got {act_status!r}; 'No data available' is rejected)"
            )

        req_cnt = obs.get("observed_request_count")
        if not isinstance(req_cnt, int) or isinstance(req_cnt, bool) or req_cnt != 0:
            errors.append(
                f"pre_dispatch_observations[{idx}].observed_request_count must be integer 0 (got {req_cnt!r})"
            )

        ev_ref = obs.get("evidence_ref")
        if not isinstance(ev_ref, str) or not ev_ref.strip():
            errors.append(
                f"pre_dispatch_observations[{idx}].evidence_ref must be a non-empty capture/evidence reference"
            )

    if len(seen_projects) > 1:
        errors.append(f"Observation records disagree on project_id: {sorted(seen_projects)}")

    span_seconds: float | None = None
    if len(parsed_dts) >= 2:
        parsed_dts.sort()
        span_seconds = (parsed_dts[-1] - parsed_dts[0]).total_seconds()
        if span_seconds < MIN_OBSERVATION_SPACING_SECONDS:
            errors.append(
                f"Observation spacing {int(span_seconds)}s is below required minimum {int(MIN_OBSERVATION_SPACING_SECONDS)}s (15 minutes)"
            )
        latest_age_sec = (ref_now - parsed_dts[-1]).total_seconds()
        if latest_age_sec > max_latest_observation_age_seconds:
            errors.append(
                f"EXPIRED_OR_STALE_OBSERVATION: Latest observation is {int(latest_age_sec)}s old (max allowed {int(max_latest_observation_age_seconds)}s)"
            )

    if consumer_pause_confirmed is not True:
        errors.append("consumer_pause_confirmed must be explicitly True")
    if not isinstance(consumer_pause_evidence_ref, str) or not consumer_pause_evidence_ref.strip():
        errors.append("consumer_pause_evidence_ref must be a non-empty string")
    if not isinstance(consumer_pause_window, dict):
        errors.append("consumer_pause_window must be an object with ISO-8601 start_at and end_at")
    else:
        w_start = parse_iso8601_utc(consumer_pause_window.get("start_at"))
        w_end = parse_iso8601_utc(consumer_pause_window.get("end_at"))
        planned_session_end = ref_now + datetime.timedelta(
            milliseconds=max(0, int(session_ceiling_ms))
        )
        if w_start is None or w_end is None or w_end <= w_start:
            errors.append("consumer_pause_window must contain valid ISO-8601 start_at < end_at")
        else:
            if w_start > ref_now:
                errors.append(
                    f"EXPIRED_OR_INSUFFICIENT_PAUSE_WINDOW: consumer_pause_window.start_at ({consumer_pause_window.get('start_at')}) has not started yet"
                )
            if w_end < planned_session_end:
                errors.append(
                    f"EXPIRED_OR_INSUFFICIENT_PAUSE_WINDOW: consumer_pause_window.end_at ({consumer_pause_window.get('end_at')}) does not cover planned diagnostic session end ({planned_session_end.isoformat()})"
                )

    if str(dashboard_headroom_status or "").strip() != "CONFIRMED_HEADROOM_AVAILABLE":
        errors.append(
            f"dashboard_headroom_status must be 'CONFIRMED_HEADROOM_AVAILABLE' (got {dashboard_headroom_status!r})"
        )

    return (len(errors) == 0), errors, span_seconds


def bootstrap_existing_smoke_ledger(sqlite_path: str) -> None:
    """
    Explicit test/fixture bootstrap helper creating the exact existing smoke-ledger schema:
      runs(id TEXT PRIMARY KEY, started REAL NOT NULL)
      attempts(run TEXT, operation TEXT, dispatched REAL, completed REAL, PRIMARY KEY(run, operation))
    Never called implicitly on a missing path when require_existing_ledger=True.
    """
    os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)) or ".", exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                started REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
                run TEXT,
                operation TEXT,
                dispatched REAL,
                completed REAL,
                PRIMARY KEY(run, operation)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _subprocess_http_worker_entry(
    url: str,
    serialized_body: bytes,
    headers: dict[str, str],
    timeout_sec: float,
    session_deadline_epoch: float,
    result_queue: Any,
    simulate_block_seconds: float = 0.0,
) -> None:
    """
    Terminable OS-process worker for live REST transport (and subprocess termination tests).
    Because this runs in a separate OS process, parent `proc.terminate()/kill()/join()` guarantees
    immediate local worker and socket shutdown prior to releasing `session.lock`.
    """
    state: dict[str, Any] = {
        "http_status": None,
        "headers_received": False,
        "resp_bytes_len": 0,
        "raw_body": b"",
        "exc_type": None,
        "exc_module": None,
        "exc_msg": None,
    }
    try:
        if simulate_block_seconds > 0.0:
            time.sleep(simulate_block_seconds)
            state["http_status"] = 200
            state["headers_received"] = True
            state["raw_body"] = b'{"totalTokens": 42}'
            state["resp_bytes_len"] = len(state["raw_body"])
            result_queue.put(state)
            return

        timeout_cfg = httpx.Timeout(
            timeout_sec,
            connect=min(10.0, timeout_sec),
            read=timeout_sec,
            write=min(10.0, timeout_sec),
        )
        with httpx.Client(timeout=timeout_cfg) as client:
            with client.stream("POST", url, content=serialized_body, headers=headers) as response:
                state["http_status"] = response.status_code
                state["headers_received"] = True
                raw_chunks: list[bytes] = []
                for chunk in response.iter_bytes():
                    if time.time() >= session_deadline_epoch:
                        raise httpx.ReadTimeout(
                            "Absolute session ceiling exceeded during body stream read"
                        )
                    raw_chunks.append(chunk)
                    state["resp_bytes_len"] += len(chunk)
                state["raw_body"] = b"".join(raw_chunks)
    except BaseException as exc:
        state["exc_type"] = type(exc).__name__
        state["exc_module"] = type(exc).__module__
        state["exc_msg"] = str(exc)
    finally:
        try:
            result_queue.put(state)
        except Exception:
            pass


class CrossPlatformFileLock:
    """
    Cross-platform OS file lock supporting Windows (`msvcrt.locking`) and POSIX (`fcntl.flock`)
    on `session.lock` in the SQLite smoke-ledger state directory.
    """

    def __init__(
        self, lock_path: str, timeout_sec: float = 5.0, force_backend: str | None = None
    ) -> None:
        self.lock_path = os.path.abspath(lock_path)
        self.timeout_sec = timeout_sec
        self.force_backend = force_backend
        self.fd: int | None = None
        self.active_backend: str = "NONE"

    def acquire(self) -> str:
        os.makedirs(os.path.dirname(self.lock_path) or ".", exist_ok=True)
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if os.path.getsize(self.lock_path) == 0:
                os.write(fd, b"L")
                os.lseek(fd, 0, os.SEEK_SET)
        except Exception:
            pass

        backend = self.force_backend
        if backend is None:
            if _win_msvcrt is not None and (os.name == "nt" or _posix_fcntl is None):
                backend = "windows_msvcrt"
            elif _posix_fcntl is not None:
                backend = "posix_fcntl"
            else:
                backend = "atomic_fallback"

        deadline = time.monotonic() + self.timeout_sec
        while True:
            try:
                if backend == "windows_msvcrt":
                    if _win_msvcrt is None:
                        raise RuntimeError("Windows msvcrt module unavailable")
                    os.lseek(fd, 0, os.SEEK_SET)
                    _win_msvcrt.locking(fd, _win_msvcrt.LK_NBLCK, 1)
                    self.fd = fd
                    self.active_backend = "windows_msvcrt"
                    return self.active_backend
                elif backend == "posix_fcntl":
                    if _posix_fcntl is None:
                        raise RuntimeError("POSIX fcntl module unavailable")
                    _posix_fcntl.flock(fd, _posix_fcntl.LOCK_EX | _posix_fcntl.LOCK_NB)
                    self.fd = fd
                    self.active_backend = "posix_fcntl"
                    return self.active_backend
                else:
                    raise RuntimeError(f"Unsupported lock backend: {backend}")
            except (OSError, RuntimeError) as exc:
                if time.monotonic() >= deadline:
                    os.close(fd)
                    raise RuntimeError(
                        f"FAIL_CLOSED_LOCK_TIMEOUT: Could not acquire {backend} lock on {os.path.basename(self.lock_path)}: {exc}"
                    ) from exc
                time.sleep(0.01)

    def release(self) -> None:
        if self.fd is None:
            return
        fd = self.fd
        self.fd = None
        try:
            if self.active_backend == "windows_msvcrt" and _win_msvcrt is not None:
                os.lseek(fd, 0, os.SEEK_SET)
                _win_msvcrt.locking(fd, _win_msvcrt.LK_UNLCK, 1)
            elif self.active_backend == "posix_fcntl" and _posix_fcntl is not None:
                _posix_fcntl.flock(fd, _posix_fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def __enter__(self) -> "CrossPlatformFileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


class DurableDiagnosticLedger:
    """
    Compatible adapter for the existing SQLite smoke ledger:
      runs(id TEXT PRIMARY KEY, started REAL NOT NULL)
      attempts(run TEXT, operation TEXT, dispatched REAL, completed REAL, PRIMARY KEY(run, operation))
    """

    def __init__(
        self,
        ledger_path: str,
        sqlite_smoke_ledger_path: str | None = None,
        run_id: str = "run_g01_isolated_2026_11_18",
        model_id: str = DEFAULT_MODEL_ID,
        project_id: str | None = None,
        session_ceiling_ms: int = DEFAULT_SESSION_CEILING_MS,
        now_utc: datetime.datetime | None = None,
        lock_timeout_sec: float = 5.0,
        force_lock_backend: str | None = None,
        require_existing_ledger: bool = True,
        allow_bootstrap_new_ledger: bool = False,
        admission_record: dict[str, Any] | None = None,
        pre_dispatch_observations_count: int = 0,
        pre_dispatch_observations: list[dict[str, Any]] | None = None,
        consumer_pause_confirmed: bool = False,
        consumer_pause_evidence_ref: str | None = None,
        consumer_pause_window: dict[str, Any] | None = None,
        dashboard_headroom_status: str = "UNKNOWN_UNCONFIRMED",
    ) -> None:
        self.ledger_path = os.path.abspath(ledger_path)
        self.sqlite_smoke_ledger_path = (
            os.path.abspath(sqlite_smoke_ledger_path)
            if sqlite_smoke_ledger_path
            else os.path.join(os.path.dirname(self.ledger_path) or ".", DEFAULT_SQLITE_SMOKE_LEDGER)
        )
        self.session_lock_path = os.path.join(
            os.path.dirname(self.sqlite_smoke_ledger_path) or ".", SESSION_LOCK_FILENAME
        )
        self.lock_path = self.session_lock_path
        self.run_id = run_id
        self.model_id = model_id
        self.project_id = project_id
        self.lock_timeout_sec = lock_timeout_sec
        self.force_lock_backend = force_lock_backend
        self.require_existing_ledger = bool(require_existing_ledger)
        self.allow_bootstrap_new_ledger = bool(allow_bootstrap_new_ledger)

        self.session_ceiling_ms = int(session_ceiling_ms)
        self.now_utc = now_utc
        self._admission_record_project_id: str | None = None
        # Merge structured admission_record if supplied (NEVER overwrite missing expected project_id!)
        if isinstance(admission_record, dict):
            if admission_record.get("project_id") is not None:
                self._admission_record_project_id = str(admission_record["project_id"])
            if (
                pre_dispatch_observations is None
                and "pre_dispatch_observations" in admission_record
            ):
                pre_dispatch_observations = admission_record.get("pre_dispatch_observations")
            if not consumer_pause_confirmed and "consumer_pause_confirmed" in admission_record:
                consumer_pause_confirmed = bool(admission_record.get("consumer_pause_confirmed"))
            if (
                consumer_pause_evidence_ref is None
                and "consumer_pause_evidence_ref" in admission_record
            ):
                consumer_pause_evidence_ref = admission_record.get("consumer_pause_evidence_ref")
            if consumer_pause_window is None and "consumer_pause_window" in admission_record:
                consumer_pause_window = admission_record.get("consumer_pause_window")
            if (
                dashboard_headroom_status == "UNKNOWN_UNCONFIRMED"
                and "dashboard_headroom_status" in admission_record
            ):
                dashboard_headroom_status = str(
                    admission_record.get("dashboard_headroom_status") or "UNKNOWN_UNCONFIRMED"
                )

        self.pre_dispatch_observations: list[dict[str, Any]] = (
            [dict(o) for o in pre_dispatch_observations if isinstance(o, dict)]
            if isinstance(pre_dispatch_observations, list)
            else []
        )
        # Actual verified count is derived strictly from provided observation records, NOT a bare integer override
        self.pre_dispatch_observations_count_requested = int(pre_dispatch_observations_count)
        self.pre_dispatch_observations_count = len(self.pre_dispatch_observations)
        self.consumer_pause_confirmed = bool(consumer_pause_confirmed)
        self.consumer_pause_evidence_ref = consumer_pause_evidence_ref
        self.consumer_pause_window = (
            dict(consumer_pause_window) if isinstance(consumer_pause_window, dict) else None
        )
        self.dashboard_headroom_status = (
            str(dashboard_headroom_status) if dashboard_headroom_status else "UNKNOWN_UNCONFIRMED"
        )

        self.admission_valid, self.admission_validation_errors, self.observation_span_seconds = (
            validate_admission_evidence(
                expected_model_id=self.model_id,
                expected_project_id=self.project_id,
                pre_dispatch_observations=self.pre_dispatch_observations,
                consumer_pause_confirmed=self.consumer_pause_confirmed,
                consumer_pause_evidence_ref=self.consumer_pause_evidence_ref,
                consumer_pause_window=self.consumer_pause_window,
                dashboard_headroom_status=self.dashboard_headroom_status,
                now_utc=self.now_utc,
                session_ceiling_ms=self.session_ceiling_ms,
            )
        )
        if (
            self._admission_record_project_id
            and self.project_id
            and self._admission_record_project_id.strip() != self.project_id.strip()
        ):
            self.admission_validation_errors.append(
                f"PROJECT_ID_MISMATCH: admission_record.project_id {self._admission_record_project_id!r} != expected {self.project_id!r}"
            )
            self.admission_valid = False

        self.last_lock_backend_used: str = "NONE"
        self.initialization_error: str | None = None
        self._held_session_lock: CrossPlatformFileLock | None = None
        self._deferred_lock_reaper_thread: threading.Thread | None = None
        self.session_reservation_acquired: bool = False
        self.session_reservation_terminated: bool = False

        os.makedirs(os.path.dirname(self.ledger_path) or ".", exist_ok=True)
        self.state: dict[str, Any] = {}

        if not os.path.exists(self.sqlite_smoke_ledger_path) and (
            self.require_existing_ledger and not self.allow_bootstrap_new_ledger
        ):
            self.initialization_error = (
                f"RuntimeError: FAIL_CLOSED_EXISTING_LEDGER_MISSING: Authoritative existing smoke ledger "
                f"does not exist at {self.sqlite_smoke_ledger_path}"
            )
            self.state = self._build_fallback_error_state()
            return

        try:
            with self._exclusive_lock() as lk:
                self.last_lock_backend_used = lk.active_backend
                self._init_or_reconcile_locked(allow_active_self=False)
        except Exception as exc:
            self.initialization_error = f"{type(exc).__name__}: {exc}"
            self.state = self._build_fallback_error_state()

    def _build_admission_preconditions_block(
        self, ledger_refreshed: bool, four_debit_ok: bool
    ) -> dict[str, Any]:
        return {
            "pre_dispatch_observations_count": self.pre_dispatch_observations_count,
            "pre_dispatch_observations_count_requested": self.pre_dispatch_observations_count_requested,
            "pre_dispatch_observations_evidence": self.pre_dispatch_observations,
            "observation_spacing_seconds": (
                int(self.observation_span_seconds)
                if self.observation_span_seconds is not None
                else None
            ),
            "min_observation_spacing_seconds_required": int(MIN_OBSERVATION_SPACING_SECONDS),
            "consumer_pause_confirmed": self.consumer_pause_confirmed,
            "consumer_pause_evidence_ref": self.consumer_pause_evidence_ref,
            "consumer_pause_window": self.consumer_pause_window,
            "dashboard_headroom_status": self.dashboard_headroom_status,
            "human_operator_confirmation_required": True,
            "runner_verified_dashboard_truth": False,
            "file_reference_alone_does_not_prove_screenshot_content": True,
            "ledger_refreshed": ledger_refreshed,
            "four_debit_admission_reconciled": four_debit_ok,
            "admission_attested": self.admission_valid,
            "admission_validation_errors": list(self.admission_validation_errors),
        }

    def _build_fallback_error_state(self) -> dict[str, Any]:
        return {
            "ledger_schema_version": "od-llm-02-v0.9-isolated",
            "sqlite_smoke_ledger_path": os.path.basename(self.sqlite_smoke_ledger_path),
            "session_lock_path": os.path.basename(self.session_lock_path),
            "sqlite_schema_flavor": "UNAVAILABLE",
            "lock_backend": self.last_lock_backend_used,
            "fail_closed_error": self.initialization_error,
            "c01_attempts_spent": 0,
            "g01_attempts_spent": 0,
            "embedding_attempts_spent": 0,
            "c01_ceiling": 1,
            "g01_ceiling": 1,
            "embedding_ceiling": 0,
            "max_retries_configured": 0,
            "historical_runs_preserved_count": 0,
            "historical_attempts_preserved_count": 0,
            "rolling_24h_attempts_count": 0,
            "four_debit_admission_reservation": {
                "required_reservation_debits": FOUR_DEBIT_RESERVATION_REQUIRED,
                "session_reservation_acquired": False,
                "c01_reserved_debits": 1,
                "g01_reserved_debits": 1,
                "safety_headroom_reserved_debits": 2,
                "consumed_probe_debits_within_reservation": 0,
                "remaining_probe_debits_within_reservation": 0,
                "uncertainty_margin_debits_held": 0,
                "rolling_24h_budget_ceiling_debits": ROLLING_24H_DEBIT_ALLOWANCE,
                "rolling_24h_prior_attempts_count": 0,
                "rolling_24h_attempts_including_current_session": 0,
                "rolling_24h_remaining_before_reservation": 0,
                "local_ledger_24h_remaining_debits_after_reservation": 0,
                "rolling_24h_prior_run_reservations_count": 0,
                "rolling_24h_run_reservation_cap": ROLLING_24H_RUN_RESERVATION_CAP,
                "run_reservation_cap_satisfied": False,
                "actual_dispatched_requests_recorded": 0,
                "admission_reservation_satisfied": False,
                "headroom_accounting_scope": "LOCAL_SQLITE_SMOKE_LEDGER_ONLY",
                "external_project_wide_headroom_status": self.dashboard_headroom_status,
            },
            "admission_preconditions": self._build_admission_preconditions_block(
                ledger_refreshed=False, four_debit_ok=False
            ),
            "unfinished_attempts_detected": [],
            "active_competing_runs_detected": [],
            "entries": [],
        }

    def defer_session_lock_release_until_worker_exits(
        self, worker_thread: threading.Thread
    ) -> bool:
        """
        RR-06 & RR-03: If an uncancellable in-process mock worker thread is still alive after a
        timeout, transfer ownership of the held `session.lock` to a daemon reaper thread that keeps
        `session.lock` locked until `worker_thread.join()` completes, preventing any competing runner
        from reacquiring `session.lock` while the timed-out worker is still active.
        """
        lk = self._held_session_lock
        if lk is None:
            return False
        self._held_session_lock = None

        def _reaper() -> None:
            try:
                worker_thread.join()
            finally:
                try:
                    lk.release()
                except Exception:
                    pass

        reaper = threading.Thread(target=_reaper, daemon=True)
        self._deferred_lock_reaper_thread = reaper
        reaper.start()
        return True

    @contextlib.contextmanager
    def hold_whole_session_lock(self) -> Iterator[CrossPlatformFileLock]:
        if self._held_session_lock is not None:
            yield self._held_session_lock
            return
        lk = CrossPlatformFileLock(
            self.session_lock_path,
            timeout_sec=self.lock_timeout_sec,
            force_backend=self.force_lock_backend,
        )
        lk.acquire()
        self._held_session_lock = lk
        self.last_lock_backend_used = lk.active_backend
        try:
            yield lk
        finally:
            # Release ONLY if ownership was NOT transferred to a deferred worker reaper
            if self._held_session_lock is lk:
                self._held_session_lock = None
                lk.release()

    @contextlib.contextmanager
    def _exclusive_lock(self) -> Iterator[CrossPlatformFileLock]:
        if self._held_session_lock is not None:
            yield self._held_session_lock
            return
        lk = CrossPlatformFileLock(
            self.session_lock_path,
            timeout_sec=self.lock_timeout_sec,
            force_backend=self.force_lock_backend,
        )
        lk.acquire()
        try:
            yield lk
        finally:
            lk.release()

    def _classify_operation_bucket(self, op_str: str) -> str:
        up = (op_str or "").upper()
        low = (op_str or "").lower()
        if up == "C01" or "count_tokens" in low or "counttokens" in low:
            return "C01"
        if up == "G01" or "generate_content" in low or "generatecontent" in low:
            return "G01"
        if up.startswith("E") or "embed" in low:
            return "EMBEDDING"
        return "OTHER"

    def _detect_sqlite_schema_flavor(self, conn: sqlite3.Connection) -> str:
        runs_cols = [r[1] for r in conn.execute("PRAGMA table_info(runs)").fetchall()]
        att_cols = [r[1] for r in conn.execute("PRAGMA table_info(attempts)").fetchall()]
        if not runs_cols and not att_cols:
            conn.execute("CREATE TABLE runs (id TEXT PRIMARY KEY, started REAL NOT NULL)")
            conn.execute(
                "CREATE TABLE attempts (run TEXT, operation TEXT, dispatched REAL, completed REAL, PRIMARY KEY(run, operation))"
            )
            return "existing_smoke_v1"
        if (
            "id" in runs_cols
            and "started" in runs_cols
            and "run" in att_cols
            and "operation" in att_cols
        ):
            return "existing_smoke_v1"
        if "run_id" in runs_cols and "attempt_id" in att_cols:
            return "extended_v04"
        raise RuntimeError(
            f"FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: Unrecognized smoke ledger table columns runs={runs_cols}, attempts={att_cols}"
        )

    def _init_or_reconcile_locked(self, allow_active_self: bool = False) -> None:
        if not os.path.exists(self.sqlite_smoke_ledger_path):
            if self.require_existing_ledger and not self.allow_bootstrap_new_ledger:
                raise RuntimeError(
                    f"FAIL_CLOSED_EXISTING_LEDGER_MISSING: Authoritative existing smoke ledger does not exist at {self.sqlite_smoke_ledger_path}"
                )
            bootstrap_existing_smoke_ledger(self.sqlite_smoke_ledger_path)
        elif os.path.getsize(self.sqlite_smoke_ledger_path) == 0:
            raise RuntimeError(
                "FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: SQLite smoke ledger file is 0 bytes"
            )

        loaded_json: dict[str, Any] = {}
        if os.path.exists(self.ledger_path):
            if os.path.getsize(self.ledger_path) == 0:
                raise RuntimeError(
                    "FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: JSON ledger file is 0 bytes (corrupt)"
                )
            try:
                with open(self.ledger_path, encoding="utf-8") as f:
                    loaded_json = json.load(f)
            except Exception as j_exc:
                raise RuntimeError(
                    f"FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: Malformed JSON ledger at {os.path.basename(self.ledger_path)}: {j_exc}"
                ) from j_exc
            if not isinstance(loaded_json, dict) or not isinstance(
                loaded_json.get("entries", []), list
            ):
                raise RuntimeError(
                    "FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: JSON ledger root/entries invalid type"
                )
            for k_cnt in ("c01_attempts_spent", "g01_attempts_spent", "embedding_attempts_spent"):
                v_cnt = loaded_json.get(k_cnt, 0)
                if not isinstance(v_cnt, int) or isinstance(v_cnt, bool) or v_cnt < 0:
                    raise RuntimeError(
                        f"FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: Invalid counter {k_cnt}={v_cnt!r}"
                    )

        now_epoch = time.time()
        window_cutoff = now_epoch - ROLLING_24H_WINDOW_SECONDS

        try:
            conn = sqlite3.connect(
                self.sqlite_smoke_ledger_path, timeout=self.lock_timeout_sec, isolation_level=None
            )
        except Exception as s_exc:
            raise RuntimeError(
                f"FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: Cannot open SQLite smoke ledger: {s_exc}"
            ) from s_exc

        try:
            conn.execute("BEGIN IMMEDIATE")
            flavor = self._detect_sqlite_schema_flavor(conn)

            historical_runs_count = 0
            historical_attempts_count = 0
            rolling_24h_prior_attempts_count = 0
            current_session_attempts_count = 0
            prior_rolling_24h_runs: list[str] = []
            active_competing_runs: list[str] = []
            unfinished_attempts: list[str] = []
            current_diag_c01_keys: set[str] = set()
            current_diag_g01_keys: set[str] = set()
            current_diag_emb_keys: set[str] = set()
            merged_entries_by_key: dict[str, dict[str, Any]] = {}

            if flavor == "existing_smoke_v1":
                run_rows = conn.execute(
                    "SELECT id, started FROM runs ORDER BY started ASC"
                ).fetchall()
                run_started_map: dict[str, float] = {}
                for r_id, r_started in run_rows:
                    r_str = str(r_id)
                    r_ts = float(r_started or 0.0)
                    run_started_map[r_str] = r_ts
                    if r_ts < window_cutoff:
                        historical_runs_count += 1
                    else:
                        if r_str != self.run_id:
                            prior_rolling_24h_runs.append(r_str)
                        elif not allow_active_self:
                            prior_rolling_24h_runs.append(r_str)

                att_rows = conn.execute(
                    "SELECT run, operation, dispatched, completed FROM attempts ORDER BY COALESCE(dispatched, 0) ASC, run ASC, operation ASC"
                ).fetchall()
                runs_with_attempts: set[str] = set()
                for a_run, a_op, a_disp, a_comp in att_rows:
                    r_str = str(a_run)
                    op_str = str(a_op)
                    runs_with_attempts.add(r_str)
                    key = f"{r_str}:{op_str}"
                    ref_ts = (
                        float(a_disp)
                        if a_disp is not None
                        else (
                            float(a_comp)
                            if a_comp is not None
                            else run_started_map.get(r_str, now_epoch)
                        )
                    )
                    is_within_24h = ref_ts >= window_cutoff
                    if not is_within_24h and a_comp is not None:
                        historical_attempts_count += 1
                    else:
                        if r_str == self.run_id and allow_active_self:
                            current_session_attempts_count += 1
                        else:
                            rolling_24h_prior_attempts_count += 1

                    if a_comp is None:
                        if not (allow_active_self and r_str == self.run_id):
                            unfinished_attempts.append(key)
                            if r_str != self.run_id:
                                active_competing_runs.append(r_str)

                    bucket = self._classify_operation_bucket(op_str)
                    if r_str == self.run_id or (is_within_24h and r_str.startswith("run_")):
                        if bucket == "C01":
                            current_diag_c01_keys.add(key)
                        elif bucket == "G01":
                            current_diag_g01_keys.add(key)
                        elif bucket == "EMBEDDING":
                            current_diag_emb_keys.add(key)

                    merged_entries_by_key[key] = {
                        "request_attempt_id": key,
                        "run_id": r_str,
                        "probe_id": bucket if bucket in {"C01", "G01"} else op_str,
                        "operation": op_str,
                        "state": "COMPLETED"
                        if a_comp is not None
                        else ("DISPATCHED" if a_disp is not None else "RESERVED"),
                        "dispatched_epoch": float(a_disp) if a_disp is not None else None,
                        "completed_epoch": float(a_comp) if a_comp is not None else None,
                        "within_rolling_24h": is_within_24h,
                    }

                for r_id, r_ts in run_started_map.items():
                    if r_ts >= window_cutoff:
                        if not (allow_active_self and r_id == self.run_id):
                            if r_id not in runs_with_attempts and r_ts >= (now_epoch - 900.0):
                                active_competing_runs.append(r_id)
                if len(prior_rolling_24h_runs) >= ROLLING_24H_RUN_RESERVATION_CAP:
                    for r_id in prior_rolling_24h_runs:
                        if r_id not in active_competing_runs:
                            active_competing_runs.append(r_id)

                for j_ent in loaded_json.get("entries", []):
                    if not isinstance(j_ent, dict) or not j_ent.get("request_attempt_id"):
                        raise RuntimeError(
                            "FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: JSON ledger entry missing request_attempt_id"
                        )
                    r_str = str(j_ent.get("run_id") or self.run_id)
                    p_str = str(j_ent.get("probe_id") or j_ent.get("operation") or "C01")
                    key = (
                        f"{r_str}:{p_str}"
                        if ":" not in str(j_ent["request_attempt_id"])
                        else str(j_ent["request_attempt_id"])
                    )
                    bucket = self._classify_operation_bucket(p_str)
                    if j_ent.get("within_rolling_24h", True) is not False:
                        if bucket == "C01":
                            current_diag_c01_keys.add(key)
                        elif bucket == "G01":
                            current_diag_g01_keys.add(key)
                        elif bucket == "EMBEDDING":
                            current_diag_emb_keys.add(key)
                    if key not in merged_entries_by_key:
                        merged_entries_by_key[key] = j_ent

            else:
                run_rows = conn.execute(
                    "SELECT run_id, status, active_reservation_count FROM runs"
                ).fetchall()
                for r_id, r_stat, r_res in run_rows:
                    if (
                        str(r_stat or "").upper() in {"RUNNING", "IN_FLIGHT", "RESERVED"}
                        or int(r_res or 0) > 0
                    ):
                        if not (allow_active_self and str(r_id) == self.run_id):
                            active_competing_runs.append(str(r_id))
                            prior_rolling_24h_runs.append(str(r_id))
                att_rows = conn.execute(
                    "SELECT attempt_id, run_id, probe_id, operation_kind, state, completed_at FROM attempts"
                ).fetchall()
                for att_id, r_id, p_id, op_k, st_v, comp_at in att_rows:
                    key = f"{r_id}:{p_id}"
                    bucket = self._classify_operation_bucket(str(p_id) or str(op_k))
                    if bucket == "C01":
                        current_diag_c01_keys.add(key)
                    elif bucket == "G01":
                        current_diag_g01_keys.add(key)
                    elif bucket == "EMBEDDING":
                        current_diag_emb_keys.add(key)
                    if (
                        str(st_v or "").upper()
                        in {"RESERVED", "DISPATCHED", "IN_FLIGHT", "UNFINISHED"}
                        or comp_at is None
                    ):
                        if not (allow_active_self and str(r_id) == self.run_id):
                            unfinished_attempts.append(str(att_id))
                    merged_entries_by_key[key] = {
                        "request_attempt_id": str(att_id),
                        "run_id": str(r_id),
                        "probe_id": str(p_id),
                        "operation": str(op_k),
                        "state": str(st_v),
                    }
                    if str(r_id) == self.run_id and allow_active_self:
                        current_session_attempts_count += 1
                    else:
                        rolling_24h_prior_attempts_count += 1

            merged_c01 = max(
                int(loaded_json.get("c01_attempts_spent", 0)), len(current_diag_c01_keys)
            )
            merged_g01 = max(
                int(loaded_json.get("g01_attempts_spent", 0)), len(current_diag_g01_keys)
            )
            merged_emb = max(
                int(loaded_json.get("embedding_attempts_spent", 0)), len(current_diag_emb_keys)
            )
            in_flight_id = loaded_json.get("in_flight_request_id")
            if in_flight_id is not None and not allow_active_self:
                unfinished_attempts.append(str(in_flight_id))

            conn.execute("COMMIT")
        except Exception as db_exc:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            if isinstance(db_exc, RuntimeError) and "FAIL_CLOSED_" in str(db_exc):
                raise
            raise RuntimeError(
                f"FAIL_CLOSED_LEDGER_CORRUPT_OR_UNAVAILABLE: SQLite smoke ledger error: {db_exc}"
            ) from db_exc
        finally:
            conn.close()

        remaining_24h_before_res = max(
            0, ROLLING_24H_DEBIT_ALLOWANCE - rolling_24h_prior_attempts_count
        )
        four_debit_ok = remaining_24h_before_res >= FOUR_DEBIT_RESERVATION_REQUIRED
        run_cap_ok = len(prior_rolling_24h_runs) < ROLLING_24H_RUN_RESERVATION_CAP
        admission_res_ok = (
            four_debit_ok and run_cap_ok and not unfinished_attempts and not active_competing_runs
        )

        actual_dispatched_in_run = sum(
            1
            for e in merged_entries_by_key.values()
            if e.get("run_id") == self.run_id and e.get("dispatched_epoch") is not None
        )
        total_rolling_24h_attempts = rolling_24h_prior_attempts_count + actual_dispatched_in_run

        self.state = {
            "ledger_schema_version": "od-llm-02-v0.9-isolated",
            "sqlite_smoke_ledger_path": os.path.basename(self.sqlite_smoke_ledger_path),
            "session_lock_path": os.path.basename(self.session_lock_path),
            "sqlite_schema_flavor": flavor,
            "lock_backend": self.last_lock_backend_used,
            "run_id": self.run_id,
            "in_flight_request_id": in_flight_id,
            "c01_attempts_spent": merged_c01,
            "g01_attempts_spent": merged_g01,
            "embedding_attempts_spent": merged_emb,
            "c01_ceiling": 1,
            "g01_ceiling": 1,
            "embedding_ceiling": 0,
            "max_retries_configured": 0,
            "historical_runs_preserved_count": historical_runs_count,
            "historical_attempts_preserved_count": historical_attempts_count,
            "rolling_24h_attempts_count": total_rolling_24h_attempts,
            "four_debit_admission_reservation": {
                "required_reservation_debits": FOUR_DEBIT_RESERVATION_REQUIRED,
                "session_reservation_acquired": self.session_reservation_acquired,
                "c01_reserved_debits": 1,
                "g01_reserved_debits": 1,
                "safety_headroom_reserved_debits": 2,
                "consumed_probe_debits_within_reservation": actual_dispatched_in_run,
                "remaining_probe_debits_within_reservation": (
                    max(0, 2 - actual_dispatched_in_run) if self.session_reservation_acquired else 0
                ),
                "uncertainty_margin_debits_held": (
                    2
                    if (
                        self.session_reservation_acquired
                        and not self.session_reservation_terminated
                    )
                    else 0
                ),
                "rolling_24h_budget_ceiling_debits": ROLLING_24H_DEBIT_ALLOWANCE,
                "rolling_24h_prior_attempts_count": rolling_24h_prior_attempts_count,
                "rolling_24h_attempts_including_current_session": total_rolling_24h_attempts,
                "rolling_24h_remaining_before_reservation": remaining_24h_before_res,
                "local_ledger_24h_remaining_debits_after_reservation": (
                    max(0, remaining_24h_before_res - FOUR_DEBIT_RESERVATION_REQUIRED)
                    if self.session_reservation_acquired
                    else remaining_24h_before_res
                ),
                "rolling_24h_prior_run_reservations_count": len(prior_rolling_24h_runs),
                "rolling_24h_run_reservation_cap": ROLLING_24H_RUN_RESERVATION_CAP,
                "run_reservation_cap_satisfied": run_cap_ok,
                "actual_dispatched_requests_recorded": actual_dispatched_in_run,
                "admission_reservation_satisfied": admission_res_ok,
                "headroom_accounting_scope": "LOCAL_SQLITE_SMOKE_LEDGER_ONLY",
                "external_project_wide_headroom_status": self.dashboard_headroom_status,
            },
            "admission_preconditions": self._build_admission_preconditions_block(
                ledger_refreshed=True, four_debit_ok=admission_res_ok
            ),
            "unfinished_attempts_detected": sorted(set(unfinished_attempts)),
            "active_competing_runs_detected": sorted(set(active_competing_runs)),
            "entries": list(merged_entries_by_key.values()),
        }
        self._flush_json_locked()

    def _flush_json_locked(self) -> None:
        tmp_path = f"{self.ledger_path}.{os.getpid()}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
        os.replace(tmp_path, self.ledger_path)

    def acquire_session_reservation(self) -> None:
        if self.initialization_error:
            raise RuntimeError(self.initialization_error)

        if not self.admission_valid:
            raise RuntimeError(
                "FAIL_CLOSED_ADMISSION_EVIDENCE_INVALID: "
                + "; ".join(self.admission_validation_errors)
            )
        # Re-verify strict pause-window start_at <= dispatch time (zero future-start tolerance)
        if isinstance(self.consumer_pause_window, dict):
            _disp_now = (
                self.now_utc.astimezone(_UTC)
                if self.now_utc is not None
                else datetime.datetime.now(_UTC)
            )
            _w_start = parse_iso8601_utc(self.consumer_pause_window.get("start_at"))
            if _w_start is None or _w_start > _disp_now:
                raise RuntimeError(
                    "FAIL_CLOSED_ADMISSION_EVIDENCE_INVALID: EXPIRED_OR_INSUFFICIENT_PAUSE_WINDOW: consumer_pause_window.start_at is later than admission/dispatch time"
                )

        with self._exclusive_lock() as lk:
            self.last_lock_backend_used = lk.active_backend
            self._init_or_reconcile_locked(allow_active_self=self.session_reservation_acquired)

            if self.session_reservation_acquired:
                return

            fd_res = self.state["four_debit_admission_reservation"]
            if not fd_res["run_reservation_cap_satisfied"]:
                raise RuntimeError(
                    f"FAIL_CLOSED_ROLLING_24H_RUN_RESERVATION_CAP_REACHED: {fd_res['rolling_24h_prior_run_reservations_count']} run reservations already exist in rolling 24h window (cap={ROLLING_24H_RUN_RESERVATION_CAP})"
                )
            if fd_res["rolling_24h_remaining_before_reservation"] < FOUR_DEBIT_RESERVATION_REQUIRED:
                raise RuntimeError(
                    f"FAIL_CLOSED_FOUR_DEBIT_RESERVATION_EXCEEDED: Insufficient rolling 24-hour capacity ({fd_res['rolling_24h_remaining_before_reservation']} < {FOUR_DEBIT_RESERVATION_REQUIRED}) for 4-debit session reservation"
                )
            if self.state["active_competing_runs_detected"]:
                raise RuntimeError(
                    f"FAIL_CLOSED_ACTIVE_RUN_OR_UNFINISHED_ATTEMPT: Active competing run(s): {self.state['active_competing_runs_detected']}"
                )
            if self.state["unfinished_attempts_detected"]:
                raise RuntimeError(
                    f"FAIL_CLOSED_ACTIVE_RUN_OR_UNFINISHED_ATTEMPT: Unfinished attempt(s): {self.state['unfinished_attempts_detected']}"
                )

            now_epoch = time.time()
            flavor = self.state.get("sqlite_schema_flavor", "existing_smoke_v1")
            conn = sqlite3.connect(
                self.sqlite_smoke_ledger_path, timeout=self.lock_timeout_sec, isolation_level=None
            )
            try:
                conn.execute("BEGIN IMMEDIATE")
                if flavor == "existing_smoke_v1":
                    conn.execute(
                        "INSERT OR IGNORE INTO runs (id, started) VALUES (?, ?)",
                        (self.run_id, now_epoch),
                    )
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO runs (run_id, started_at, completed_at, status, model_id, active_reservation_count, notes) "
                        "VALUES (?, ?, NULL, 'RUNNING', ?, 4, 'Isolated G01 4-debit session reservation')",
                        (self.run_id, utc_now_iso(), DEFAULT_MODEL_ID),
                    )
                conn.execute("COMMIT")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise RuntimeError(f"FAIL_CLOSED_SQLITE_RESERVATION_ERROR: {exc}") from exc
            finally:
                conn.close()

            self.session_reservation_acquired = True
            self._init_or_reconcile_locked(allow_active_self=True)

    def acquire_slot(self, probe_id: str, request_attempt_id: str, operation_kind: str) -> None:
        if self.initialization_error:
            raise RuntimeError(self.initialization_error)

        if not self.session_reservation_acquired:
            self.acquire_session_reservation()

        with self._exclusive_lock() as lk:
            self.last_lock_backend_used = lk.active_backend
            self._init_or_reconcile_locked(allow_active_self=True)

            if self.state["active_competing_runs_detected"]:
                raise RuntimeError(
                    f"FAIL_CLOSED_ACTIVE_RUN_OR_UNFINISHED_ATTEMPT: Active competing run(s): {self.state['active_competing_runs_detected']}"
                )
            if self.state["unfinished_attempts_detected"]:
                raise RuntimeError(
                    f"FAIL_CLOSED_ACTIVE_RUN_OR_UNFINISHED_ATTEMPT: Unfinished attempt(s): {self.state['unfinished_attempts_detected']}"
                )
            if self.state["in_flight_request_id"] is not None:
                raise RuntimeError(
                    f"SINGLE_IN_FLIGHT_GUARD_VIOLATION: request {self.state['in_flight_request_id']} is already in flight"
                )
            if self.state["embedding_attempts_spent"] > 0:
                raise RuntimeError(
                    f"LEDGER_CEILING_EXCEEDED: Embedding ceiling is 0, but ledger shows {self.state['embedding_attempts_spent']} spent"
                )

            if probe_id == "C01":
                if self.state["c01_attempts_spent"] >= self.state["c01_ceiling"]:
                    raise RuntimeError(
                        "LEDGER_CEILING_EXCEEDED: C01 limit (1) already spent in durable smoke ledger"
                    )
                self.state["c01_attempts_spent"] += 1
            elif probe_id == "G01":
                if self.state["g01_attempts_spent"] >= self.state["g01_ceiling"]:
                    raise RuntimeError(
                        "LEDGER_CEILING_EXCEEDED: G01 limit (1) already spent in durable smoke ledger"
                    )
                self.state["g01_attempts_spent"] += 1
            else:
                raise RuntimeError(
                    f"FORBIDDEN_PROBE_ID: {probe_id} is prohibited in isolated G01 diagnostic mode"
                )

            now_epoch = time.time()
            self.state["in_flight_request_id"] = request_attempt_id
            flavor = self.state.get("sqlite_schema_flavor", "existing_smoke_v1")

            conn = sqlite3.connect(
                self.sqlite_smoke_ledger_path, timeout=self.lock_timeout_sec, isolation_level=None
            )
            try:
                conn.execute("BEGIN IMMEDIATE")
                if flavor == "existing_smoke_v1":
                    conn.execute(
                        "INSERT OR IGNORE INTO runs (id, started) VALUES (?, ?)",
                        (self.run_id, now_epoch),
                    )
                    conn.execute(
                        "INSERT INTO attempts (run, operation, dispatched, completed) VALUES (?, ?, ?, NULL)",
                        (self.run_id, probe_id, now_epoch),
                    )
                else:
                    conn.execute(
                        "INSERT INTO attempts (attempt_id, run_id, probe_id, operation_kind, state, reserved_at, dispatched_at, completed_at, outcome_status, diagnostic_stage, request_payload_bytes, socket_write_confirmed) "
                        "VALUES (?, ?, ?, ?, 'DISPATCHED', ?, ?, NULL, NULL, 'IN_FLIGHT', 0, 0)",
                        (
                            request_attempt_id,
                            self.run_id,
                            probe_id,
                            operation_kind,
                            utc_now_iso(),
                            utc_now_iso(),
                        ),
                    )
                conn.execute("COMMIT")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise RuntimeError(f"FAIL_CLOSED_SQLITE_RESERVATION_ERROR: {exc}") from exc
            finally:
                conn.close()

            key = f"{self.run_id}:{probe_id}"
            self.state["entries"].append(
                {
                    "request_attempt_id": key,
                    "run_id": self.run_id,
                    "probe_id": probe_id,
                    "operation": probe_id,
                    "state": "DISPATCHED",
                    "dispatched_epoch": now_epoch,
                    "completed_epoch": None,
                    "within_rolling_24h": True,
                }
            )
            dispatched_cnt = sum(
                1
                for e in self.state["entries"]
                if e.get("run_id") == self.run_id and e.get("dispatched_epoch") is not None
            )
            fd_res = self.state["four_debit_admission_reservation"]
            fd_res["actual_dispatched_requests_recorded"] = dispatched_cnt
            fd_res["consumed_probe_debits_within_reservation"] = dispatched_cnt
            fd_res["remaining_probe_debits_within_reservation"] = max(0, 2 - dispatched_cnt)
            fd_res["rolling_24h_attempts_including_current_session"] = (
                fd_res["rolling_24h_prior_attempts_count"] + dispatched_cnt
            )
            self.state["rolling_24h_attempts_count"] = fd_res[
                "rolling_24h_attempts_including_current_session"
            ]
            self._flush_json_locked()

    def release_slot(
        self,
        probe_id: str,
        request_attempt_id: str,
        outcome_status: str,
        diagnostic_stage: str,
        mark_completed_in_db: bool,
    ) -> None:
        with self._exclusive_lock() as lk:
            self.last_lock_backend_used = lk.active_backend
            now_epoch = time.time()
            now_iso = utc_now_iso()
            flavor = self.state.get("sqlite_schema_flavor", "existing_smoke_v1")

            conn = sqlite3.connect(
                self.sqlite_smoke_ledger_path, timeout=self.lock_timeout_sec, isolation_level=None
            )
            try:
                conn.execute("BEGIN IMMEDIATE")
                if flavor == "existing_smoke_v1":
                    if mark_completed_in_db:
                        conn.execute(
                            "UPDATE attempts SET completed = ? WHERE run = ? AND operation = ?",
                            (now_epoch, self.run_id, probe_id),
                        )
                else:
                    conn.execute(
                        "UPDATE attempts SET state = ?, completed_at = ?, outcome_status = ?, diagnostic_stage = ? WHERE attempt_id = ?",
                        (
                            outcome_status,
                            now_iso if mark_completed_in_db else None,
                            outcome_status,
                            diagnostic_stage,
                            request_attempt_id,
                        ),
                    )
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            finally:
                conn.close()

            if self.state.get("in_flight_request_id") == request_attempt_id:
                self.state["in_flight_request_id"] = None
            key = f"{self.run_id}:{probe_id}"
            for ent in self.state.get("entries", []):
                if ent.get("request_attempt_id") in {key, request_attempt_id}:
                    ent["state"] = outcome_status
                    ent["completed_epoch"] = now_epoch if mark_completed_in_db else None
                    ent["outcome_status"] = outcome_status
                    ent["diagnostic_stage"] = diagnostic_stage
            self._flush_json_locked()


class IsolatedG01DiagnosticRunner:
    def __init__(
        self,
        api_key: str,
        ledger_path: str,
        model_id: str = DEFAULT_MODEL_ID,
        project_id: str | None = None,
        endpoint_host: str = "generativelanguage.googleapis.com",
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        spacing_ms: int = DEFAULT_SPACING_MS,
        session_ceiling_ms: int = DEFAULT_SESSION_CEILING_MS,
        transport: httpx.BaseTransport | None = None,
        sqlite_smoke_ledger_path: str | None = None,
        run_id: str = "run_g01_isolated_2026_11_18",
        lock_timeout_sec: float = 5.0,
        force_lock_backend: str | None = None,
        require_existing_ledger: bool = True,
        allow_bootstrap_new_ledger: bool = False,
        admission_record: dict[str, Any] | None = None,
        pre_dispatch_observations_count: int = 0,
        pre_dispatch_observations: list[dict[str, Any]] | None = None,
        consumer_pause_confirmed: bool = False,
        consumer_pause_evidence_ref: str | None = None,
        consumer_pause_window: dict[str, Any] | None = None,
        dashboard_headroom_status: str = "UNKNOWN_UNCONFIRMED",
        use_subprocess_worker: bool | None = None,
        _simulate_subprocess_block_seconds: float = 0.0,
    ) -> None:
        self.api_key = api_key
        self.model_id = model_id
        self.project_id = project_id
        self.endpoint_host = endpoint_host
        self.timeout_ms = timeout_ms
        self.spacing_ms = spacing_ms
        self.session_ceiling_ms = session_ceiling_ms
        self.transport = transport
        self.run_id = run_id
        # Default to terminable subprocess worker for live execution (`transport is None`)
        self.use_subprocess_worker = (
            (transport is None) if use_subprocess_worker is None else bool(use_subprocess_worker)
        )
        self._simulate_subprocess_block_seconds = float(_simulate_subprocess_block_seconds)

        resolved_sqlite_path = (
            os.path.abspath(sqlite_smoke_ledger_path)
            if sqlite_smoke_ledger_path
            else os.path.join(
                os.path.dirname(os.path.abspath(ledger_path)) or ".", DEFAULT_SQLITE_SMOKE_LEDGER
            )
        )

        self.ledger = DurableDiagnosticLedger(
            ledger_path,
            sqlite_smoke_ledger_path=resolved_sqlite_path,
            run_id=run_id,
            model_id=model_id,
            project_id=project_id,
            session_ceiling_ms=session_ceiling_ms,
            lock_timeout_sec=lock_timeout_sec,
            force_lock_backend=force_lock_backend,
            require_existing_ledger=bool(require_existing_ledger),
            allow_bootstrap_new_ledger=bool(allow_bootstrap_new_ledger),
            admission_record=admission_record,
            pre_dispatch_observations_count=pre_dispatch_observations_count,
            pre_dispatch_observations=pre_dispatch_observations,
            consumer_pause_confirmed=consumer_pause_confirmed,
            consumer_pause_evidence_ref=consumer_pause_evidence_ref,
            consumer_pause_window=consumer_pause_window,
            dashboard_headroom_status=dashboard_headroom_status,
        )

    def _run_transport_subprocess(
        self,
        url: str,
        serialized_body: bytes,
        headers: dict[str, str],
        timeout_sec: float,
        session_deadline_mono: float,
    ) -> tuple[int | None, bool, int, bytes, BaseException | None, bool, bool]:
        """
        Executes the HTTP request in a terminable child OS process (`spawn` context for Windows & Linux).
        On timeout, terminates/kills and joins the child process BEFORE returning so local worker
        and socket shutdown is 100% verified prior to releasing `session.lock`.
        """
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        remaining_s = max(0.001, session_deadline_mono - time.monotonic())
        deadline_epoch = time.time() + remaining_s
        proc = ctx.Process(
            target=_subprocess_http_worker_entry,
            args=(
                url,
                serialized_body,
                headers,
                timeout_sec,
                deadline_epoch,
                q,
                self._simulate_subprocess_block_seconds,
            ),
        )
        proc.start()
        proc.join(timeout=timeout_sec)

        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=0.5)
            if proc.is_alive():
                proc.kill()
                proc.join(timeout=0.5)
            worker_shutdown_ok = not proc.is_alive()
            try:
                q.close()
            except Exception:
                pass
            return (
                None,
                False,
                0,
                b"",
                httpx.ReadTimeout(
                    f"Preemptive subprocess deadline ({int(timeout_sec * 1000)}ms) exceeded; local worker terminated"
                ),
                worker_shutdown_ok,
                False,
            )

        try:
            res = q.get_nowait()
        except Exception:
            res = {
                "exc_type": "RuntimeError",
                "exc_module": "builtins",
                "exc_msg": "Worker exited without result",
            }
        finally:
            try:
                q.close()
            except Exception:
                pass

        exc_obj: BaseException | None = None
        if res.get("exc_type"):
            etype = res["exc_type"]
            emsg = res.get("exc_msg") or etype
            if etype == "ReadTimeout":
                exc_obj = httpx.ReadTimeout(emsg)
            elif etype == "WriteTimeout":
                exc_obj = httpx.WriteTimeout(emsg)
            elif etype == "ConnectTimeout":
                exc_obj = httpx.ConnectTimeout(emsg)
            elif etype == "ConnectError":
                exc_obj = httpx.ConnectError(emsg)
            elif etype == "WriteError":
                exc_obj = httpx.WriteError(emsg)
            elif etype == "RemoteProtocolError":
                exc_obj = httpx.RemoteProtocolError(emsg)
            else:
                exc_obj = RuntimeError(f"{etype}: {emsg}")

        return (
            res.get("http_status"),
            bool(res.get("headers_received")),
            int(res.get("resp_bytes_len") or 0),
            res.get("raw_body") or b"",
            exc_obj,
            True,
            False,
        )

    def _run_transport_in_process(
        self,
        url: str,
        serialized_body: bytes,
        headers: dict[str, str],
        timeout_sec: float,
        session_deadline_mono: float,
    ) -> tuple[int | None, bool, int, bytes, BaseException | None, bool, bool]:
        """
        Executes an in-process transport (e.g., `httpx.MockTransport`). On timeout:
          1. Signals `abandoned_event`, closes `httpx.Client` and `self.transport` (unblocking cancellable transports).
          2. Briefly joins `worker_thread` (`0.015s`).
          3. If `worker_thread` is STILL alive (uncancellable mock closure), transfers `session.lock` ownership
             to a daemon reaper thread so `session.lock` CANNOT be reacquired while the worker is active!
        Returns (http_status, headers_received, resp_bytes_len, raw_body, exc, local_worker_shutdown_verified, lock_deferred_to_reaper).
        """
        timeout_cfg = httpx.Timeout(
            timeout_sec,
            connect=min(10.0, timeout_sec),
            read=timeout_sec,
            write=min(10.0, timeout_sec),
        )
        worker_state: dict[str, Any] = {
            "http_status": None,
            "headers_received": False,
            "resp_bytes_len": 0,
            "raw_body": b"",
            "exception": None,
            "client": None,
        }
        done_event = threading.Event()
        abandoned_event = threading.Event()

        def _transport_worker() -> None:
            client = httpx.Client(timeout=timeout_cfg, transport=self.transport)
            worker_state["client"] = client
            try:
                with client.stream(
                    "POST", url, content=serialized_body, headers=headers
                ) as response:
                    if abandoned_event.is_set():
                        return
                    worker_state["http_status"] = response.status_code
                    worker_state["headers_received"] = True
                    raw_chunks: list[bytes] = []
                    for chunk in response.iter_bytes():
                        if abandoned_event.is_set() or time.monotonic() >= session_deadline_mono:
                            raise httpx.ReadTimeout(
                                "Absolute session ceiling exceeded during body stream read"
                            )
                        raw_chunks.append(chunk)
                        worker_state["resp_bytes_len"] += len(chunk)
                    worker_state["raw_body"] = b"".join(raw_chunks)
            except BaseException as w_exc:
                worker_state["exception"] = w_exc
            finally:
                try:
                    client.close()
                except Exception:
                    pass
                done_event.set()

        worker_thread = threading.Thread(target=_transport_worker, daemon=True)
        worker_thread.start()
        finished_in_time = done_event.wait(timeout=timeout_sec)

        lock_deferred = False
        if not finished_in_time:
            abandoned_event.set()
            # Attempt immediate local transport/client shutdown for cancellable transports
            try:
                if self.transport is not None and hasattr(self.transport, "close"):
                    self.transport.close()
            except Exception:
                pass
            try:
                if worker_state["client"] is not None:
                    worker_state["client"].close()
            except Exception:
                pass
            worker_thread.join(timeout=0.015)
            local_shutdown_verified = not worker_thread.is_alive()
            if not local_shutdown_verified:
                # CRITICAL: Never release session.lock while worker_thread is still active!
                lock_deferred = self.ledger.defer_session_lock_release_until_worker_exits(
                    worker_thread
                )
            return (
                worker_state["http_status"],
                bool(worker_state["headers_received"]),
                int(worker_state["resp_bytes_len"]),
                b"",
                httpx.ReadTimeout(
                    f"Preemptive deadline ({int(timeout_sec * 1000)}ms) exceeded before transport completed"
                ),
                local_shutdown_verified,
                lock_deferred,
            )

        worker_thread.join(timeout=0.05)
        return (
            worker_state["http_status"],
            bool(worker_state["headers_received"]),
            int(worker_state["resp_bytes_len"]),
            worker_state["raw_body"],
            worker_state["exception"],
            not worker_thread.is_alive(),
            False,
        )

    def _execute_single_http_post(
        self,
        probe_id: str,
        operation_kind: str,
        url_path: str,
        payload: dict[str, Any],
        session_deadline_mono: float,
    ) -> dict[str, Any]:
        attempt_id = f"att_{probe_id.lower()}_01"
        started_at = utc_now_iso()
        t0 = time.monotonic()
        actual_http_method_label = f"httpx.Client.stream(POST {url_path})"

        serialized_body = b""
        try:
            serialized_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
            remaining_session_ms = int((session_deadline_mono - time.monotonic()) * 1000)
            if remaining_session_ms <= 0:
                raise RuntimeError(
                    f"SESSION_CEILING_DEADLINE_EXCEEDED: Absolute {self.session_ceiling_ms}ms session ceiling expired before {probe_id}"
                )
            if (
                not self.api_key
                or not isinstance(self.api_key, str)
                or len(self.api_key.strip()) == 0
            ):
                raise ValueError("MISSING_API_KEY_PRE_SEND")
            self.ledger.acquire_slot(probe_id, attempt_id, operation_kind)
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return {
                "probe_id": probe_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "execution_status": "PROVIDER_OR_SDK_ERROR",
                "provider_fault_details": {
                    "fault_stage": "PRE_REQUEST_VALIDATION",
                    "diagnostic_substage": "PRE_SEND_VALIDATION_OR_LEDGER_GUARD",
                    "provider": "gemini",
                    "error_category": "SDK_CLIENT_EXCEPTION",
                    "error_code": (
                        "SESSION_CEILING_DEADLINE_EXCEEDED"
                        if "SESSION_CEILING_DEADLINE_EXCEEDED" in str(exc)
                        else "PRE_SEND_GUARD_REJECTED"
                    ),
                    "http_status": None,
                    "grpc_status_code": None,
                    "retryable": False,
                    "outcome_certainty": "NOT_DISPATCHED_PRE_SEND_GUARD",
                    "sanitized_diagnostic_summary": f"Pre-send validation or ledger guard failed: {sanitize_text(str(exc))}",
                    "request_transport_evidence": {
                        "request_attempt_id": attempt_id,
                        "transport_client": "raw_httpx_rest_v1beta",
                        "sdk_method": actual_http_method_label,
                        "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                        "endpoint_host": self.endpoint_host,
                        "transport_protocol": "HTTP_1_1_TLS",
                        "configured_deadline_ms": self.timeout_ms,
                        "elapsed_ms_at_fault": elapsed_ms,
                        "request_payload_bytes_prepared": len(serialized_body),
                        "socket_write_confirmed": False,
                        "request_bytes_sent": 0,
                        "http_headers_received": False,
                        "response_bytes_received": 0,
                        "local_worker_shutdown_verified": True,
                        "session_lock_held_until_worker_exit": True,
                        "provider_remote_cancellation_inferred": False,
                        "raw_exception_class": type(exc).__name__,
                        "causal_chain_summary": "Aborted by pre-send validation, admission evidence check, session ceiling, or durable smoke-ledger guard before opening HTTP socket; zero bytes transmitted.",
                    },
                },
            }

        remaining_session_ms = max(1, int((session_deadline_mono - time.monotonic()) * 1000))
        effective_timeout_ms = min(self.timeout_ms, remaining_session_ms)
        timeout_sec = effective_timeout_ms / 1000.0
        url = f"https://{self.endpoint_host}{url_path}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        if self.use_subprocess_worker:
            (
                http_status,
                headers_received,
                resp_bytes_len,
                raw_body,
                worker_exc,
                local_shutdown_verified,
                lock_deferred,
            ) = self._run_transport_subprocess(
                url, serialized_body, headers, timeout_sec, session_deadline_mono
            )
        else:
            (
                http_status,
                headers_received,
                resp_bytes_len,
                raw_body,
                worker_exc,
                local_shutdown_verified,
                lock_deferred,
            ) = self._run_transport_in_process(
                url, serialized_body, headers, timeout_sec, session_deadline_mono
            )

        try:
            if worker_exc is not None:
                raise worker_exc

            elapsed_ms = int((time.monotonic() - t0) * 1000)

            if http_status != 200:
                self.ledger.release_slot(
                    probe_id,
                    attempt_id,
                    "PROVIDER_OR_SDK_ERROR",
                    "HTTP_STATUS_OR_HEADER_WAIT",
                    mark_completed_in_db=True,
                )
                return {
                    "probe_id": probe_id,
                    "started_at": started_at,
                    "completed_at": utc_now_iso(),
                    "execution_status": "PROVIDER_OR_SDK_ERROR",
                    "provider_fault_details": {
                        "fault_stage": "TRANSPORT_DISPATCH",
                        "diagnostic_substage": "HTTP_STATUS_OR_HEADER_WAIT",
                        "provider": "gemini",
                        "error_category": "PROVIDER_HTTP_ERROR",
                        "error_code": f"HTTP_STATUS_{http_status}",
                        "http_status": http_status,
                        "grpc_status_code": None,
                        "retryable": http_status in {429, 500, 502, 503, 504},
                        "outcome_certainty": "NO_CANDIDATE_RETURNED",
                        "sanitized_diagnostic_summary": f"Provider returned non-200 HTTP status {http_status} after {elapsed_ms}ms; response body omitted by sanitization policy.",
                        "request_transport_evidence": {
                            "request_attempt_id": attempt_id,
                            "transport_client": "raw_httpx_rest_v1beta",
                            "sdk_method": actual_http_method_label,
                            "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                            "endpoint_host": self.endpoint_host,
                            "transport_protocol": "HTTP_1_1_TLS",
                            "configured_deadline_ms": self.timeout_ms,
                            "elapsed_ms_at_fault": elapsed_ms,
                            "request_payload_bytes_prepared": len(serialized_body),
                            "socket_write_confirmed": True,
                            "request_bytes_sent": None,
                            "http_headers_received": True,
                            "response_bytes_received": resp_bytes_len,
                            "local_worker_shutdown_verified": local_shutdown_verified,
                            "session_lock_held_until_worker_exit": True,
                            "provider_remote_cancellation_inferred": False,
                            "raw_exception_class": "HTTPStatusError",
                            "causal_chain_summary": f"Received HTTP {http_status} status header after {elapsed_ms}ms; exact wire socket bytes are not exposed by httpx.",
                        },
                    },
                }

            try:
                parsed = json.loads(raw_body.decode("utf-8"))
                if probe_id == "C01":
                    total_tokens = parsed.get("totalTokens")
                    if not isinstance(total_tokens, int) or isinstance(total_tokens, bool):
                        raise ValueError("Missing integer totalTokens in C01 response")
                    self.ledger.release_slot(
                        probe_id, attempt_id, "COMPLETED", "COMPLETED_OK", mark_completed_in_db=True
                    )
                    return {
                        "probe_id": "C01",
                        "started_at": started_at,
                        "completed_at": utc_now_iso(),
                        "execution_status": "COMPLETED",
                        "latency_ms": elapsed_ms,
                        "total_tokens_counted": total_tokens,
                        "provider_fault_details": None,
                    }
                else:
                    candidates = parsed.get("candidates")
                    if not isinstance(candidates, list) or len(candidates) == 0:
                        raise ValueError("Missing or empty candidates[] in G01 response")
                    usage = parsed.get("usageMetadata") or {}
                    self.ledger.release_slot(
                        probe_id, attempt_id, "COMPLETED", "COMPLETED_OK", mark_completed_in_db=True
                    )
                    return {
                        "probe_id": "G01",
                        "started_at": started_at,
                        "completed_at": utc_now_iso(),
                        "execution_status": "COMPLETED",
                        "latency_ms": elapsed_ms,
                        "finish_reason": candidates[0].get("finishReason", "STOP"),
                        "token_usage": {
                            "prompt_tokens": int(usage.get("promptTokenCount", 0)),
                            "completion_tokens": int(usage.get("candidatesTokenCount", 0)),
                            "total_tokens": int(usage.get("totalTokenCount", 0)),
                        },
                        "provider_fault_details": None,
                    }
            except Exception as parse_exc:
                self.ledger.release_slot(
                    probe_id,
                    attempt_id,
                    "PROVIDER_OR_SDK_ERROR",
                    "RESPONSE_STREAM_OR_BODY_PARSE",
                    mark_completed_in_db=True,
                )
                return {
                    "probe_id": probe_id,
                    "started_at": started_at,
                    "completed_at": utc_now_iso(),
                    "execution_status": "PROVIDER_OR_SDK_ERROR",
                    "provider_fault_details": {
                        "fault_stage": "RESPONSE_STREAM_OR_PARSE",
                        "diagnostic_substage": "RESPONSE_STREAM_OR_BODY_PARSE",
                        "provider": "gemini",
                        "error_category": "EMPTY_OR_MALFORMED_CANDIDATE",
                        "error_code": "RESPONSE_BODY_PARSE_OR_SCHEMA_ERROR",
                        "http_status": http_status,
                        "grpc_status_code": None,
                        "retryable": False,
                        "outcome_certainty": "PARTIAL_STREAM_DISCARDED",
                        "sanitized_diagnostic_summary": f"HTTP {http_status} status headers received, but response body parse failed after {resp_bytes_len} response bytes: {sanitize_text(str(parse_exc))}",
                        "request_transport_evidence": {
                            "request_attempt_id": attempt_id,
                            "transport_client": "raw_httpx_rest_v1beta",
                            "sdk_method": actual_http_method_label,
                            "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                            "endpoint_host": self.endpoint_host,
                            "transport_protocol": "HTTP_1_1_TLS",
                            "configured_deadline_ms": self.timeout_ms,
                            "elapsed_ms_at_fault": elapsed_ms,
                            "request_payload_bytes_prepared": len(serialized_body),
                            "socket_write_confirmed": True,
                            "request_bytes_sent": None,
                            "http_headers_received": True,
                            "response_bytes_received": resp_bytes_len,
                            "local_worker_shutdown_verified": local_shutdown_verified,
                            "session_lock_held_until_worker_exit": True,
                            "provider_remote_cancellation_inferred": False,
                            "raw_exception_class": f"{type(parse_exc).__module__}.{type(parse_exc).__name__}",
                            "causal_chain_summary": f"HTTP {http_status} response headers received; response body ({resp_bytes_len} bytes) failed candidate schema deserialization.",
                        },
                    },
                }

        except (httpx.ConnectError, httpx.ConnectTimeout) as conn_exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            is_conn_to = isinstance(conn_exc, httpx.ConnectTimeout)
            self.ledger.release_slot(
                probe_id,
                attempt_id,
                "TIMEOUT_OUTCOME_UNKNOWN" if is_conn_to else "PROVIDER_OR_SDK_ERROR",
                "TRANSPORT_CONNECT_OR_TLS_WRITE",
                mark_completed_in_db=True,
            )
            return {
                "probe_id": probe_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "execution_status": "TIMEOUT_OUTCOME_UNKNOWN"
                if is_conn_to
                else "PROVIDER_OR_SDK_ERROR",
                "provider_fault_details": {
                    "fault_stage": "TRANSPORT_DISPATCH",
                    "diagnostic_substage": "TRANSPORT_CONNECT_OR_TLS_WRITE",
                    "provider": "gemini",
                    "error_category": "TIMEOUT" if is_conn_to else "SDK_CLIENT_EXCEPTION",
                    "error_code": "CONNECT_TIMEOUT_PRE_WRITE"
                    if is_conn_to
                    else "TRANSPORT_CONNECT_FAILED_PRE_WRITE",
                    "http_status": None,
                    "grpc_status_code": None,
                    "retryable": False,
                    "outcome_certainty": "NO_CANDIDATE_RETURNED",
                    "sanitized_diagnostic_summary": f"Transport connection establishment failed before HTTP request write ({type(conn_exc).__name__}): {sanitize_text(str(conn_exc))}",
                    "request_transport_evidence": {
                        "request_attempt_id": attempt_id,
                        "transport_client": "raw_httpx_rest_v1beta",
                        "sdk_method": actual_http_method_label,
                        "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                        "endpoint_host": self.endpoint_host,
                        "transport_protocol": "HTTP_1_1_TLS",
                        "configured_deadline_ms": self.timeout_ms,
                        "elapsed_ms_at_fault": elapsed_ms,
                        "request_payload_bytes_prepared": len(serialized_body),
                        "socket_write_confirmed": False,
                        "request_bytes_sent": 0,
                        "http_headers_received": False,
                        "response_bytes_received": 0,
                        "local_worker_shutdown_verified": local_shutdown_verified,
                        "session_lock_held_until_worker_exit": True,
                        "provider_remote_cancellation_inferred": False,
                        "raw_exception_class": f"{type(conn_exc).__module__}.{type(conn_exc).__name__}",
                        "causal_chain_summary": "TCP/TLS connection establishment failed prior to HTTP request write; zero request bytes sent.",
                    },
                },
            }

        except httpx.WriteError as write_exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            self.ledger.release_slot(
                probe_id,
                attempt_id,
                "PROVIDER_OR_SDK_ERROR",
                "TRANSPORT_CONNECT_OR_TLS_WRITE",
                mark_completed_in_db=False,
            )
            return {
                "probe_id": probe_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "execution_status": "PROVIDER_OR_SDK_ERROR",
                "provider_fault_details": {
                    "fault_stage": "TRANSPORT_DISPATCH",
                    "diagnostic_substage": "TRANSPORT_CONNECT_OR_TLS_WRITE",
                    "provider": "gemini",
                    "error_category": "TRANSPORT_WRITE_ERROR",
                    "error_code": "SOCKET_WRITE_ERROR_OUTCOME_UNCERTAIN",
                    "http_status": http_status,
                    "grpc_status_code": None,
                    "retryable": False,
                    "outcome_certainty": "OUTCOME_UNKNOWN_DISPATCH_UNCONFIRMED",
                    "sanitized_diagnostic_summary": (
                        f"Socket write error occurred during HTTP request transmission ({type(write_exc).__name__}): "
                        f"{sanitize_text(str(write_exc))}; dispatch completion is unconfirmed."
                    ),
                    "request_transport_evidence": {
                        "request_attempt_id": attempt_id,
                        "transport_client": "raw_httpx_rest_v1beta",
                        "sdk_method": actual_http_method_label,
                        "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                        "endpoint_host": self.endpoint_host,
                        "transport_protocol": "HTTP_1_1_TLS",
                        "configured_deadline_ms": self.timeout_ms,
                        "elapsed_ms_at_fault": elapsed_ms,
                        "request_payload_bytes_prepared": len(serialized_body),
                        "socket_write_confirmed": False,
                        "request_bytes_sent": None,
                        "http_headers_received": headers_received,
                        "response_bytes_received": resp_bytes_len,
                        "local_worker_shutdown_verified": local_shutdown_verified,
                        "session_lock_held_until_worker_exit": True,
                        "provider_remote_cancellation_inferred": False,
                        "raw_exception_class": f"{type(write_exc).__module__}.{type(write_exc).__name__}",
                        "causal_chain_summary": (
                            f"Prepared {len(serialized_body)}-byte payload; non-timeout socket WriteError occurred after {elapsed_ms}ms without HTTP status headers. Dispatch outcome preserved as unconfirmed."
                        ),
                    },
                },
            }

        except (httpx.WriteTimeout, httpx.ReadTimeout) as io_exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            is_write_to = isinstance(io_exc, httpx.WriteTimeout)
            substage = (
                "TRANSPORT_CONNECT_OR_TLS_WRITE"
                if is_write_to
                else (
                    "RESPONSE_STREAM_OR_BODY_PARSE"
                    if headers_received
                    else "HTTP_STATUS_OR_HEADER_WAIT"
                )
            )
            # Only call release_slot if lock was NOT deferred (if deferred, lock is held by reaper;
            # update in-memory JSON state without reacquiring session.lock, leaving SQLite completed = NULL!)
            if not lock_deferred:
                self.ledger.release_slot(
                    probe_id,
                    attempt_id,
                    "TIMEOUT_OUTCOME_UNKNOWN",
                    substage,
                    mark_completed_in_db=False,
                )
            else:
                if self.ledger.state.get("in_flight_request_id") == attempt_id:
                    self.ledger.state["in_flight_request_id"] = None
                key = f"{self.run_id}:{probe_id}"
                for ent in self.ledger.state.get("entries", []):
                    if ent.get("request_attempt_id") in {key, attempt_id}:
                        ent["state"] = "TIMEOUT_OUTCOME_UNKNOWN"
                        ent["completed_epoch"] = None
                        ent["outcome_status"] = "TIMEOUT_OUTCOME_UNKNOWN"
                        ent["diagnostic_stage"] = substage
                self.ledger._flush_json_locked()

            if headers_received:
                summary_msg = (
                    f"HTTP {http_status} status headers received after request transmission, but response body stream "
                    f"timed out after {resp_bytes_len} response bytes ({type(io_exc).__name__}) at {elapsed_ms}ms."
                )
                causal_msg = (
                    f"HTTP {http_status} response headers arrived; response body stream read timed out at {elapsed_ms}ms "
                    f"after receiving {resp_bytes_len} bytes."
                )
            else:
                summary_msg = (
                    f"Client {'write' if is_write_to else 'read'} timeout expired after {elapsed_ms}ms "
                    f"(configured deadline {effective_timeout_ms}ms) before HTTP status headers arrived; "
                    f"local_worker_shutdown_verified={local_shutdown_verified}, session_lock_deferred_until_exit={lock_deferred}. "
                    f"Stopping local work does not cancel any request already received remotely."
                )
                causal_msg = (
                    f"Prepared {len(serialized_body)}-byte payload via raw httpx; no HTTP status header received before "
                    f"{type(io_exc).__name__} at {elapsed_ms}ms. Attempt debit retained (completed=NULL) and remote outcome preserved as UNKNOWN."
                )

            return {
                "probe_id": probe_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "execution_status": "TIMEOUT_OUTCOME_UNKNOWN",
                "provider_fault_details": {
                    "fault_stage": "RESPONSE_STREAM_OR_PARSE"
                    if headers_received
                    else "TRANSPORT_DISPATCH",
                    "diagnostic_substage": substage,
                    "provider": "gemini",
                    "error_category": "TIMEOUT",
                    "error_code": (
                        "STREAM_READ_TIMEOUT_AFTER_HTTP_HEADERS"
                        if headers_received
                        else (
                            "WRITE_TIMEOUT_NO_HTTP_STATUS"
                            if is_write_to
                            else "CLIENT_DEADLINE_EXCEEDED_NO_HTTP_STATUS"
                        )
                    ),
                    "http_status": http_status,
                    "grpc_status_code": None,
                    "retryable": False,
                    "outcome_certainty": (
                        "PARTIAL_STREAM_DISCARDED"
                        if headers_received
                        else "OUTCOME_UNKNOWN_DEADLINE_EXCEEDED"
                    ),
                    "sanitized_diagnostic_summary": summary_msg,
                    "request_transport_evidence": {
                        "request_attempt_id": attempt_id,
                        "transport_client": "raw_httpx_rest_v1beta",
                        "sdk_method": actual_http_method_label,
                        "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                        "endpoint_host": self.endpoint_host,
                        "transport_protocol": "HTTP_1_1_TLS",
                        "configured_deadline_ms": self.timeout_ms,
                        "elapsed_ms_at_fault": elapsed_ms,
                        "request_payload_bytes_prepared": len(serialized_body),
                        "socket_write_confirmed": headers_received,
                        "request_bytes_sent": None,
                        "http_headers_received": headers_received,
                        "response_bytes_received": resp_bytes_len,
                        "local_worker_shutdown_verified": local_shutdown_verified,
                        "session_lock_held_until_worker_exit": True,
                        "session_lock_deferred_to_reaper": lock_deferred,
                        "provider_remote_cancellation_inferred": False,
                        "raw_exception_class": f"{type(io_exc).__module__}.{type(io_exc).__name__}",
                        "causal_chain_summary": causal_msg,
                    },
                },
            }

        except Exception as trans_exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            substage = (
                "RESPONSE_STREAM_OR_BODY_PARSE"
                if headers_received
                else "HTTP_STATUS_OR_HEADER_WAIT"
            )
            fault_stage = (
                "RESPONSE_STREAM_OR_PARSE" if headers_received else "SDK_ADAPTER_DESERIALIZATION"
            )
            err_cat = "STREAM_INTERRUPTED" if headers_received else "SDK_CLIENT_EXCEPTION"
            err_code = (
                "STREAM_INTERRUPTED_AFTER_HEADERS"
                if headers_received
                else "SDK_CANDIDATE_STREAM_ABORTED_NO_HTTP_STATUS"
            )
            certainty = (
                "PARTIAL_STREAM_DISCARDED"
                if headers_received
                else "OUTCOME_UNKNOWN_DISPATCH_UNCONFIRMED"
            )
            self.ledger.release_slot(
                probe_id,
                attempt_id,
                "PROVIDER_OR_SDK_ERROR",
                substage,
                mark_completed_in_db=False,
            )
            if headers_received:
                summary_msg = (
                    f"HTTP {http_status} status headers received, but response body stream aborted after "
                    f"{resp_bytes_len} response bytes ({type(trans_exc).__name__}): {sanitize_text(str(trans_exc))}"
                )
                causal_msg = (
                    f"HTTP {http_status} response headers arrived; response body stream aborted at {elapsed_ms}ms "
                    f"after {resp_bytes_len} bytes."
                )
            else:
                summary_msg = (
                    f"Raw httpx REST stream aborted before HTTP status headers ({type(trans_exc).__name__}): "
                    f"{sanitize_text(str(trans_exc))}"
                )
                causal_msg = (
                    "Peer disconnected before HTTP status header; raw httpx lacks kernel socket-write confirmation, "
                    "so request_bytes_sent=None and dispatch outcome is preserved as unconfirmed."
                )

            return {
                "probe_id": probe_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "execution_status": "PROVIDER_OR_SDK_ERROR",
                "provider_fault_details": {
                    "fault_stage": fault_stage,
                    "diagnostic_substage": substage,
                    "provider": "gemini",
                    "error_category": err_cat,
                    "error_code": err_code,
                    "http_status": http_status,
                    "grpc_status_code": None,
                    "retryable": False,
                    "outcome_certainty": certainty,
                    "sanitized_diagnostic_summary": summary_msg,
                    "request_transport_evidence": {
                        "request_attempt_id": attempt_id,
                        "transport_client": "raw_httpx_rest_v1beta",
                        "sdk_method": actual_http_method_label,
                        "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
                        "endpoint_host": self.endpoint_host,
                        "transport_protocol": "HTTP_1_1_TLS",
                        "configured_deadline_ms": self.timeout_ms,
                        "elapsed_ms_at_fault": elapsed_ms,
                        "request_payload_bytes_prepared": len(serialized_body),
                        "socket_write_confirmed": headers_received,
                        "request_bytes_sent": None,
                        "http_headers_received": headers_received,
                        "response_bytes_received": resp_bytes_len,
                        "local_worker_shutdown_verified": local_shutdown_verified,
                        "session_lock_held_until_worker_exit": True,
                        "provider_remote_cancellation_inferred": False,
                        "raw_exception_class": f"{type(trans_exc).__module__}.{type(trans_exc).__name__}",
                        "causal_chain_summary": causal_msg,
                    },
                },
            }

    def _build_session_report(
        self,
        c01_res: dict[str, Any],
        g01_res: dict[str, Any] | None,
        stopped_reason: str,
    ) -> dict[str, Any]:
        return {
            "diagnostic_plan_version": "od-llm02-v0.9-2026-11-18",
            "package_release_id": PACKAGE_RELEASE_ID,
            "runner_version": RUNNER_VERSION,
            "transport_client": "raw_httpx_rest_v1beta",
            "verification_scope": "REST_TRANSPORT_COMPATIBILITY_ONLY_NOT_GOOGLE_GENAI_SDK",
            "historical_2026_11_09_results_reclassified": False,
            "model_id": self.model_id,
            "synthetic_approval_tier": "manager",
            "constraints_enforced": {
                "max_c01_requests": 1,
                "max_g01_requests": 1,
                "max_embedding_requests": 0,
                "four_debit_admission_reservation": FOUR_DEBIT_RESERVATION_REQUIRED,
                "rolling_24h_run_reservation_cap": ROLLING_24H_RUN_RESERVATION_CAP,
                "min_observation_spacing_seconds": int(MIN_OBSERVATION_SPACING_SECONDS),
                "whole_session_lock_file": SESSION_LOCK_FILENAME,
                "session_lock_held_until_worker_exit": True,
                "max_in_flight_requests": 1,
                "automatic_retries": 0,
                "spacing_ms": self.spacing_ms,
                "timeout_ms": self.timeout_ms,
                "session_ceiling_ms": self.session_ceiling_ms,
                "stop_on_failure": True,
                "free_tier_zero_paid_use_boundary": True,
            },
            "c01_result": c01_res,
            "g01_result": g01_res,
            "stopped_reason": stopped_reason,
            "ledger_summary": self.ledger.state,
        }

    def run_isolated_diagnostic(self, sleep_fn: Any = time.sleep) -> dict[str, Any]:
        session_start_mono = time.monotonic()
        session_deadline_mono = session_start_mono + (self.session_ceiling_ms / 1000.0)

        prompt_payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": G01_SYNTHETIC_PROMPT_TEXT}],
                }
            ]
        }
        g01_payload = {
            **prompt_payload,
            "generationConfig": {
                "temperature": 0.0,
                "topP": 1.0,
                "maxOutputTokens": 256,
            },
        }

        if self.ledger.initialization_error:
            c01_res = self._execute_single_http_post(
                probe_id="C01",
                operation_kind="count_tokens",
                url_path=f"/v1beta/models/{self.model_id}:countTokens",
                payload=prompt_payload,
                session_deadline_mono=session_deadline_mono,
            )
            return self._build_session_report(c01_res, None, "STOPPED_ON_C01_FAILURE")

        try:
            with self.ledger.hold_whole_session_lock():
                c01_res = self._execute_single_http_post(
                    probe_id="C01",
                    operation_kind="count_tokens",
                    url_path=f"/v1beta/models/{self.model_id}:countTokens",
                    payload=prompt_payload,
                    session_deadline_mono=session_deadline_mono,
                )

                if c01_res.get("execution_status") != "COMPLETED":
                    return self._build_session_report(c01_res, None, "STOPPED_ON_C01_FAILURE")

                if self.spacing_ms > 0:
                    remaining_before_sleep_s = session_deadline_mono - time.monotonic()
                    sleep_target_s = self.spacing_ms / 1000.0
                    if remaining_before_sleep_s <= sleep_target_s:
                        sleep_fn(max(0.0, remaining_before_sleep_s))
                        return self._build_session_report(
                            c01_res, None, "STOPPED_ON_SESSION_DEADLINE_EXCEEDED"
                        )
                    sleep_fn(sleep_target_s)

                if time.monotonic() >= session_deadline_mono:
                    return self._build_session_report(
                        c01_res, None, "STOPPED_ON_SESSION_DEADLINE_EXCEEDED"
                    )

                g01_res = self._execute_single_http_post(
                    probe_id="G01",
                    operation_kind="generate_content",
                    url_path=f"/v1beta/models/{self.model_id}:generateContent",
                    payload=g01_payload,
                    session_deadline_mono=session_deadline_mono,
                )

                stopped_reason = (
                    "COMPLETED_ISOLATED_C01_AND_G01"
                    if g01_res.get("execution_status") == "COMPLETED"
                    else f"STOPPED_ON_G01_{g01_res.get('execution_status')}"
                )
                return self._build_session_report(c01_res, g01_res, stopped_reason)
        except Exception as lock_exc:
            self.ledger.initialization_error = f"{type(lock_exc).__name__}: {lock_exc}"
            c01_res = self._execute_single_http_post(
                probe_id="C01",
                operation_kind="count_tokens",
                url_path=f"/v1beta/models/{self.model_id}:countTokens",
                payload=prompt_payload,
                session_deadline_mono=session_deadline_mono,
            )
            return self._build_session_report(c01_res, None, "STOPPED_ON_C01_FAILURE")


def validate_output_path_not_protected(output_path: str) -> None:
    base = os.path.basename(os.path.abspath(output_path))
    if base in PROTECTED_HISTORICAL_FILENAMES:
        raise ValueError(
            f"PROTECTED_HISTORICAL_RESULT_FILE: Refusing to overwrite historical result artifact {base!r}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Isolated G01 Diagnostic Runner (OD-LLM-02 v0.9 — G01 LIVE HOLD; DO NOT RUN LIVE YET)"
    )
    parser.add_argument(
        "--output",
        default="g01_isolated_diagnostic_result_2026-11-18.json",
        help="Path for sanitized diagnostic JSON output (must not overwrite historical 2026-11-09 files)",
    )
    parser.add_argument(
        "--ledger",
        default="g01_isolated_diagnostic_ledger_2026-11-18.json",
        help="Path for durable diagnostic ledger JSON",
    )
    parser.add_argument(
        "--sqlite-smoke-ledger",
        default=DEFAULT_SQLITE_SMOKE_LEDGER,
        help="Path to authoritative existing SQLite smoke ledger (runs/attempts schema; must exist)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_ID,
        help="Target Gemini model ID (default: gemini-3.8-flash)",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="Exact expected GCP/Gemini project ID (REQUIRED for admission; omitting fails closed)",
    )
    parser.add_argument(
        "--admission-record",
        default=None,
        help="Path to structured JSON admission record containing >=2 observations (>=15m apart), pause window/ref, and confirmed headroom",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        help="Per-request G01 deadline in ms (reviewed plan default: 60000)",
    )
    parser.add_argument(
        "--spacing-ms",
        type=int,
        default=DEFAULT_SPACING_MS,
        help="Spacing between C01 and G01 in ms (reviewed plan default: 31000)",
    )
    parser.add_argument(
        "--session-ceiling-ms",
        type=int,
        default=DEFAULT_SESSION_CEILING_MS,
        help="Absolute wall-clock session deadline in ms (reviewed plan default: 900000)",
    )
    parser.add_argument(
        "--prompt-key",
        action="store_true",
        help="Prompt interactively for GEMINI_API_KEY via hidden getpass prompt (never stored in shell history)",
    )
    args = parser.parse_args()

    validate_output_path_not_protected(args.output)
    admission_record: dict[str, Any] | None = None
    if args.admission_record:
        with open(args.admission_record, encoding="utf-8") as af:
            admission_record = json.load(af)

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and args.prompt_key:
        api_key = getpass.getpass(
            "Enter GEMINI_API_KEY (hidden, not saved to shell history): "
        ).strip()

    runner = IsolatedG01DiagnosticRunner(
        api_key=api_key,
        ledger_path=args.ledger,
        model_id=args.model,
        project_id=args.project_id,
        timeout_ms=args.timeout_ms,
        spacing_ms=args.spacing_ms,
        session_ceiling_ms=args.session_ceiling_ms,
        sqlite_smoke_ledger_path=args.sqlite_smoke_ledger,
        require_existing_ledger=True,
        allow_bootstrap_new_ledger=False,
        admission_record=admission_record,
    )
    report = runner.run_isolated_diagnostic()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(
        f"Isolated G01 Diagnostic Runner Version: {RUNNER_VERSION} (Package {PACKAGE_RELEASE_ID})"
    )
    print(f"Transport Client: {report['transport_client']} ({report['verification_scope']})")
    print(f"Target Model ID: {args.model}")
    print(f"Stopped Reason: {report['stopped_reason']}")
    print(f"C01 Status: {report['c01_result']['execution_status']}")
    if report["g01_result"]:
        print(f"G01 Status: {report['g01_result']['execution_status']}")
    return 0 if report["stopped_reason"] == "COMPLETED_ISOLATED_C01_AND_G01" else 1


if __name__ == "__main__":
    sys.exit(main())
