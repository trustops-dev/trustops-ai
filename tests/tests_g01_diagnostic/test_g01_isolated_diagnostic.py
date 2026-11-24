#!/usr/bin/env python3
"""
Offline Cross-Platform Test Suite for g01_isolated_diagnostic_runner.py (v0.9.0-isolated-g01).
Zero unconditional fcntl imports; runs natively on both Windows (msvcrt) and Linux/macOS (fcntl).
Covers 33 scenarios (including v1.13 review findings on admission evidence, 15-minute spacing,
cancellable shutdown, deferred session.lock reaper, and subprocess worker OS termination):
  1..16: Original R12-01..R12-04 scenarios
  17..22: RR-02..RR-06 scenarios
  23. test_23_v14_admission_count_only_and_empty_observations_rejected
  24. test_24_v14_admission_observations_five_minutes_apart_rejected_requires_15_min
  25. test_25_v14_admission_no_data_available_model_mismatch_missing_pause_ref_or_unknown_headroom_rejected
  26. test_26_v14_cancellable_transport_shuts_down_worker_completely_before_lock_release
  27. test_27_v14_uncancellable_worker_keeps_session_lock_held_until_worker_exits
  28. test_28_v14_subprocess_worker_terminated_at_deadline_before_lock_release_with_debit_retained
"""

import datetime
import json
import multiprocessing
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from collections.abc import Callable, Iterator
from typing import Any

import httpx

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


_repo_root = _find_repo_root(pathlib.Path(__file__))
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

_g01_runner_path = _find_repo_file("g01_isolated_diagnostic_runner.py", pathlib.Path(__file__))
if str(_g01_runner_path.parent) not in sys.path:
    sys.path.insert(0, str(_g01_runner_path.parent))
import g01_isolated_diagnostic_runner as g01_mod  # noqa: E402

_UTC: datetime.tzinfo = (
    datetime.UTC if sys.version_info >= (3, 11) else datetime.timezone(datetime.timedelta(0))
)


def _recording_200_transport(
    calls: list[Any], value_fn: Callable[[httpx.Request], Any] | None = None
) -> httpx.MockTransport:
    """Record intercepted requests and return HTTP 200 without invoking remote endpoints."""

    def _handler(request: httpx.Request) -> httpx.Response:
        calls.append(value_fn(request) if value_fn else request.url.path)
        return httpx.Response(200)

    return httpx.MockTransport(_handler)


def make_valid_admission_record(
    model_id: str = g01_mod.DEFAULT_MODEL_ID,
    project_id: str = "trustops-free-tier-sandbox",
) -> dict[str, Any]:
    now = datetime.datetime.now(_UTC)
    t0 = (now - datetime.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t1 = (now - datetime.timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    p_start = (now - datetime.timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
    p_end = (now + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "project_id": project_id,
        "pre_dispatch_observations": [
            {
                "observation_id": "obs_t0",
                "observed_at": t0,
                "project_id": project_id,
                "model_id": model_id,
                "reported_activity_status": "ZERO_ACTIVITY",
                "observed_request_count": 0,
                "evidence_ref": "capture_ai_studio_quota_t0.png",
            },
            {
                "observation_id": "obs_t1",
                "observed_at": t1,
                "project_id": project_id,
                "model_id": model_id,
                "reported_activity_status": "ZERO_ACTIVITY",
                "observed_request_count": 0,
                "evidence_ref": "capture_ai_studio_quota_t1.png",
            },
        ],
        "consumer_pause_confirmed": True,
        "consumer_pause_evidence_ref": "pause_attestation_team_chat_active",
        "consumer_pause_window": {
            "start_at": p_start,
            "end_at": p_end,
        },
        "dashboard_headroom_status": "CONFIRMED_HEADROOM_AVAILABLE",
    }


ATTESTED_KWARGS: dict[str, Any] = {
    "project_id": "trustops-free-tier-sandbox",
    "admission_record": make_valid_admission_record(),
}


def _competing_worker_entry(
    ledger_path: str,
    sqlite_path: str,
    run_id: str,
    barrier_file: str,
    result_file: str,
) -> None:
    def slow_handler(request: httpx.Request) -> httpx.Response:
        with open(barrier_file, "w", encoding="utf-8") as bf:
            bf.write("IN_FLIGHT")
        time.sleep(0.35)
        if request.url.path.endswith(":countTokens"):
            return httpx.Response(200, json={"totalTokens": 42})
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "manager"}]}, "finishReason": "STOP"}
                ],
                "usageMetadata": {
                    "promptTokenCount": 42,
                    "candidatesTokenCount": 2,
                    "totalTokenCount": 44,
                },
            },
        )

    runner = g01_mod.IsolatedG01DiagnosticRunner(
        api_key="test_dummy_key_not_real",
        ledger_path=ledger_path,
        sqlite_smoke_ledger_path=sqlite_path,
        run_id=run_id,
        spacing_ms=0,
        lock_timeout_sec=0.15,
        require_existing_ledger=True,
        transport=httpx.MockTransport(slow_handler),
        **ATTESTED_KWARGS,
    )
    rep = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
    with open(result_file, "w", encoding="utf-8") as rf:
        json.dump(rep, rf)


class TestIsolatedG01DiagnosticRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.tmp_dir.name, "ledger.json")
        self.sqlite_path = os.path.join(self.tmp_dir.name, "smoke_ledger.sqlite3")
        g01_mod.bootstrap_existing_smoke_ledger(self.sqlite_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_01_clean_c01_and_g01_success_with_reviewed_60s_31s_900s_defaults(self) -> None:
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {"parts": [{"text": "manager approval is required."}]},
                            "finishReason": "STOP",
                        }
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 42,
                        "candidatesTokenCount": 8,
                        "totalTokenCount": 50,
                    },
                },
            )

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_dummy_key_not_real",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        self.assertEqual(runner.timeout_ms, 60000)
        self.assertEqual(runner.spacing_ms, 31000)
        self.assertEqual(runner.session_ceiling_ms, 900000)
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)

        self.assertEqual(res["stopped_reason"], "COMPLETED_ISOLATED_C01_AND_G01")
        self.assertEqual(len(calls), 2)
        self.assertEqual(res["ledger_summary"]["sqlite_schema_flavor"], "existing_smoke_v1")

    def test_02_g01_run1_read_timeout_measured_elapsed_time_and_null_grpc_status(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            raise httpx.ReadTimeout(
                "Read timed out before response status headers", request=request
            )

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_dummy_key_not_real",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        t0 = time.monotonic()
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        wall_ms = int((time.monotonic() - t0) * 1000)

        g01 = res["g01_result"]
        self.assertEqual(g01["execution_status"], "TIMEOUT_OUTCOME_UNKNOWN")
        pf = g01["provider_fault_details"]
        self.assertIsNone(pf["grpc_status_code"])
        rte = pf["request_transport_evidence"]
        self.assertLessEqual(rte["elapsed_ms_at_fault"], wall_ms + 200)
        self.assertEqual(rte["configured_deadline_ms"], 60000)
        self.assertIsNone(rte["request_bytes_sent"])

    def test_03_g01_run2_remote_protocol_error_before_headers_unconfirmed_write_outcome_unknown(
        self,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            raise httpx.RemoteProtocolError(
                "Server disconnected without sending a response.", request=request
            )

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_dummy_key_not_real",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)

        g01 = res["g01_result"]
        pf = g01["provider_fault_details"]
        self.assertEqual(pf["outcome_certainty"], "OUTCOME_UNKNOWN_DISPATCH_UNCONFIRMED")
        self.assertIsNone(pf["grpc_status_code"])
        self.assertIsNone(pf["request_transport_evidence"]["request_bytes_sent"])

    def test_04_transport_connect_error_stage_and_stop_on_c01_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("TLS handshake failed", request=request)

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_dummy_key_not_real",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertEqual(
            res["c01_result"]["provider_fault_details"]["request_transport_evidence"][
                "request_bytes_sent"
            ],
            0,
        )

    def test_05_response_stream_or_body_parse_stage_http_200_malformed_body(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(200, content=b'{"candidates": []}')

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_dummy_key_not_real",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        pf = res["g01_result"]["provider_fault_details"]
        self.assertEqual(pf["http_status"], 200)
        self.assertIsNone(pf["request_transport_evidence"]["request_bytes_sent"])
        self.assertGreater(pf["request_transport_evidence"]["request_payload_bytes_prepared"], 0)

    def test_06_credential_header_sanitization_and_historical_file_protection(self) -> None:
        fake_secret = "AIzaSyD9999SecretKeyLeakTest123456"

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.RemoteProtocolError(f"x-goog-api-key={fake_secret}", request=request)

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key=fake_secret,
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertNotIn(fake_secret, json.dumps(res))

    def test_07_restart_persists_existing_schema_ledger_and_blocks_second_run(self) -> None:
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "manager"}]}}]},
            )

        r1 = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        ).run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(r1["stopped_reason"], "COMPLETED_ISOLATED_C01_AND_G01")

        r2 = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        ).run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(r2["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertEqual(len(calls), 2)

    def test_08_actual_existing_smoke_schema_runs_id_started_and_attempts_run_operation(
        self,
    ) -> None:
        legacy_db = os.path.join(self.tmp_dir.name, "actual_legacy.sqlite3")
        conn = sqlite3.connect(legacy_db)
        conn.executescript(
            "CREATE TABLE runs (id TEXT PRIMARY KEY, started REAL NOT NULL); "
            "CREATE TABLE attempts (run TEXT, operation TEXT, dispatched REAL, completed REAL, PRIMARY KEY(run,operation));"
        )
        now_ts = time.time()
        conn.execute("INSERT INTO runs VALUES (?, ?)", ("historical_run_8d", now_ts - 8 * 86400))
        conn.execute(
            "INSERT INTO attempts VALUES (?, ?, ?, ?)",
            ("historical_run_8d", "C01", now_ts - 8 * 86400 + 1, now_ts - 8 * 86400 + 2),
        )
        conn.commit()
        conn.close()

        calls = []

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req.url.path)
            if req.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(
                200, json={"candidates": [{"content": {"parts": [{"text": "manager"}]}}]}
            )

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=os.path.join(self.tmp_dir.name, "legacy.json"),
            sqlite_smoke_ledger_path=legacy_db,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        self.assertIsNone(runner.ledger.initialization_error)
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res["stopped_reason"], "COMPLETED_ISOLATED_C01_AND_G01")
        self.assertEqual(len(calls), 2)
        self.assertEqual(res["ledger_summary"]["historical_runs_preserved_count"], 1)
        self.assertEqual(res["ledger_summary"]["historical_attempts_preserved_count"], 1)

        conn = sqlite3.connect(legacy_db)
        conn.execute("INSERT INTO runs VALUES (?, ?)", ("unfinished_run", now_ts - 60))
        conn.execute(
            "INSERT INTO attempts VALUES (?, ?, ?, NULL)", ("unfinished_run", "G01", now_ts - 55)
        )
        conn.commit()
        conn.close()

        runner_blocked = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=os.path.join(self.tmp_dir.name, "legacy2.json"),
            sqlite_smoke_ledger_path=legacy_db,
            run_id="run_after_unfinished",
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res_blocked = runner_blocked.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res_blocked["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertEqual(len(calls), 2)

    def test_09_windows_nt_msvcrt_lock_simulation_and_no_fcntl_import(self) -> None:
        runner_dir = os.path.dirname(os.path.abspath(g01_mod.__file__))
        sub_cmd = [
            sys.executable,
            "-c",
            (
                "import sys, types, httpx; "
                "sys.modules['fcntl'] = None; "
                "m = types.ModuleType('msvcrt'); "
                "m.LK_NBLCK = 1; m.LK_UNLCK = 0; "
                "m.locking = lambda fd, mode, n: None; "
                "sys.modules['msvcrt'] = m; "
                f"sys.path.insert(0, {runner_dir!r}); "
                "import g01_isolated_diagnostic_runner as g; "
                "assert g._posix_fcntl is None and g._win_msvcrt is m; "
                "print('WINDOWS_IMPORT_AND_LOCK_SIMULATION_OK')"
            ),
        ]
        proc = subprocess.run(sub_cmd, capture_output=True, text=True, check=True)
        self.assertIn("WINDOWS_IMPORT_AND_LOCK_SIMULATION_OK", proc.stdout)

    def test_10_real_competing_processes_concurrency_guard_on_existing_schema(self) -> None:
        barrier_file = os.path.join(self.tmp_dir.name, "worker1_in_flight.flag")
        res1_file = os.path.join(self.tmp_dir.name, "worker1_res.json")
        res2_file = os.path.join(self.tmp_dir.name, "worker2_res.json")

        ctx = multiprocessing.get_context("spawn")
        p1 = ctx.Process(
            target=_competing_worker_entry,
            args=(self.ledger_path, self.sqlite_path, "run_proc_1", barrier_file, res1_file),
        )
        p1.start()
        t_wait = time.monotonic()
        while not os.path.exists(barrier_file) and (time.monotonic() - t_wait) < 3.0:
            time.sleep(0.02)

        p2 = ctx.Process(
            target=_competing_worker_entry,
            args=(self.ledger_path, self.sqlite_path, "run_proc_2", barrier_file + ".2", res2_file),
        )
        p2.start()
        p1.join(timeout=10.0)
        p2.join(timeout=10.0)

        with open(res1_file, encoding="utf-8") as f1, open(res2_file, encoding="utf-8") as f2:
            r1 = json.load(f1)
            r2 = json.load(f2)

        self.assertEqual(r1["stopped_reason"], "COMPLETED_ISOLATED_C01_AND_G01")
        self.assertEqual(r2["stopped_reason"], "STOPPED_ON_C01_FAILURE")

    def test_11_corrupt_or_unavailable_ledger_fails_closed(self) -> None:
        corrupt_sqlite = os.path.join(self.tmp_dir.name, "corrupt.sqlite3")
        with open(corrupt_sqlite, "wb") as f:
            f.write(b"NOT_SQLITE_BYTES")

        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=os.path.join(self.tmp_dir.name, "ok.json"),
            sqlite_smoke_ledger_path=corrupt_sqlite,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=_recording_200_transport(calls, lambda _req: 1),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertEqual(len(calls), 0)

    def test_12_write_error_distinguished_from_timeout_with_uncertain_outcome(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            raise httpx.WriteError("Broken pipe during request write", request=request)

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        g01 = res["g01_result"]
        self.assertEqual(g01["execution_status"], "PROVIDER_OR_SDK_ERROR")
        pf = g01["provider_fault_details"]
        self.assertEqual(pf["error_category"], "TRANSPORT_WRITE_ERROR")
        self.assertNotEqual(pf["error_category"], "TIMEOUT")
        self.assertIsNone(pf["grpc_status_code"])
        self.assertEqual(pf["outcome_certainty"], "OUTCOME_UNKNOWN_DISPATCH_UNCONFIRMED")

    def test_13_missing_existing_ledger_fails_closed_without_creating_db(self) -> None:
        missing_db = os.path.join(self.tmp_dir.name, "missing.sqlite3")
        calls = []

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req.url.path)
            return httpx.Response(200, json={"totalTokens": 42})

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=os.path.join(self.tmp_dir.name, "missing.json"),
            sqlite_smoke_ledger_path=missing_db,
            spacing_ms=0,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertEqual(len(calls), 0)
        self.assertFalse(os.path.exists(missing_db))

    def test_14_body_read_timeout_after_http_200_headers_reports_accurate_post_header_summary(
        self,
    ) -> None:
        class BrokenStream(httpx.SyncByteStream):
            def __iter__(self) -> Iterator[bytes]:
                yield b'{"candidates":'
                raise httpx.ReadTimeout("synthetic body timeout")

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(200, stream=BrokenStream())

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        pf = res["g01_result"]["provider_fault_details"]
        self.assertEqual(pf["http_status"], 200)
        self.assertTrue(pf["request_transport_evidence"]["http_headers_received"])
        self.assertNotIn("before HTTP status headers", pf["sanitized_diagnostic_summary"])
        self.assertIn("HTTP 200 status headers received", pf["sanitized_diagnostic_summary"])

    def test_15_enforced_absolute_session_ceiling_900s_and_admission_preconditions(self) -> None:
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"totalTokens": 42})

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=5000,
            session_ceiling_ms=100,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_SESSION_DEADLINE_EXCEEDED")
        self.assertIsNone(res["g01_result"])

    def test_16_four_debit_reservation_reconciled_as_capacity_not_four_dispatched_requests(
        self,
    ) -> None:
        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(
                200, json={"candidates": [{"content": {"parts": [{"text": "manager"}]}}]}
            )

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="test_key",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        fd_res = res["ledger_summary"]["four_debit_admission_reservation"]
        self.assertEqual(fd_res["required_reservation_debits"], 4)
        self.assertTrue(fd_res["session_reservation_acquired"])
        self.assertEqual(fd_res["actual_dispatched_requests_recorded"], 2)

        conn = sqlite3.connect(self.sqlite_path)
        att_cnt = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        conn.close()
        self.assertEqual(att_cnt, 2)

    def test_17_rr02_omitted_admission_confirmations_default_unconfirmed_and_fail_closed(
        self,
    ) -> None:
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        ap = res["ledger_summary"]["admission_preconditions"]
        self.assertEqual(ap["pre_dispatch_observations_count"], 0)
        self.assertFalse(ap["consumer_pause_confirmed"])
        self.assertEqual(ap["dashboard_headroom_status"], "UNKNOWN_UNCONFIRMED")
        self.assertFalse(ap["admission_attested"])

    def test_18_rr03_two_existing_24h_run_reservations_with_zero_attempts_block_admission(
        self,
    ) -> None:
        conn = sqlite3.connect(self.sqlite_path)
        now = time.time()
        for i in range(2):
            conn.execute("INSERT INTO runs VALUES (?, ?)", (f"old-reservation-{i}", now - 7200 + i))
        conn.commit()
        conn.close()

        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=_recording_200_transport(calls),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        fd_res = res["ledger_summary"]["four_debit_admission_reservation"]
        self.assertEqual(fd_res["rolling_24h_prior_run_reservations_count"], 2)
        self.assertFalse(fd_res["run_reservation_cap_satisfied"])

    def test_19_rr03_whole_session_lock_on_session_lock_blocks_startup_and_mid_session_spacing_gap(
        self,
    ) -> None:
        session_lock_file = os.path.join(self.tmp_dir.name, "session.lock")
        external_lock = g01_mod.CrossPlatformFileLock(session_lock_file, timeout_sec=0.5)
        external_lock.acquire()
        try:
            calls_a: list[Any] = []
            runner_a = g01_mod.IsolatedG01DiagnosticRunner(
                api_key="synthetic-test",
                ledger_path=self.ledger_path,
                sqlite_smoke_ledger_path=self.sqlite_path,
                spacing_ms=0,
                lock_timeout_sec=0.08,
                require_existing_ledger=True,
                transport=_recording_200_transport(calls_a),
                **ATTESTED_KWARGS,
            )
            res_a = runner_a.run_isolated_diagnostic(sleep_fn=lambda _: None)
            self.assertEqual(len(calls_a), 0)
            self.assertEqual(res_a["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        finally:
            external_lock.release()

        calls_main = []
        competing_reports = []

        def ok_handler(req: httpx.Request) -> httpx.Response:
            calls_main.append(req.url.path)
            if req.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(
                200, json={"candidates": [{"content": {"parts": [{"text": "manager"}]}}]}
            )

        def spacing_interleaving_hook(_sleep_s: float) -> None:
            sub_res_file = os.path.join(self.tmp_dir.name, "mid_spacing_competing.json")
            ctx = multiprocessing.get_context("spawn")
            p = ctx.Process(
                target=_competing_worker_entry,
                args=(
                    os.path.join(self.tmp_dir.name, "ledger_comp.json"),
                    self.sqlite_path,
                    "run_competing_mid_spacing",
                    os.path.join(self.tmp_dir.name, "comp_barrier.flag"),
                    sub_res_file,
                ),
            )
            p.start()
            p.join(timeout=10.0)
            with open(sub_res_file, encoding="utf-8") as sf:
                competing_reports.append(json.load(sf))

        runner_main = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=31000,
            lock_timeout_sec=0.5,
            require_existing_ledger=True,
            transport=httpx.MockTransport(ok_handler),
            **ATTESTED_KWARGS,
        )
        res_main = runner_main.run_isolated_diagnostic(sleep_fn=spacing_interleaving_hook)
        self.assertEqual(res_main["stopped_reason"], "COMPLETED_ISOLATED_C01_AND_G01")
        self.assertEqual(len(calls_main), 2)
        self.assertEqual(len(competing_reports), 1)
        self.assertEqual(competing_reports[0]["stopped_reason"], "STOPPED_ON_C01_FAILURE")

    def test_20_rr04_single_four_debit_session_reservation_with_16_prior_attempts_completes_c01_and_g01(
        self,
    ) -> None:
        conn = sqlite3.connect(self.sqlite_path)
        now = time.time()
        conn.execute("INSERT INTO runs VALUES (?, ?)", ("prior", now - 7200))
        for i in range(16):
            t = now - 7200 + i
            conn.execute(
                "INSERT INTO attempts VALUES (?, ?, ?, ?)", ("prior", f"uuid-{i}:G02", t, t + 1)
            )
        conn.commit()
        conn.close()

        calls = []

        def ok_handler(req: httpx.Request) -> httpx.Response:
            calls.append(req.url.path)
            if req.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 42})
            return httpx.Response(
                200, json={"candidates": [{"content": {"parts": [{"text": "manager"}]}}]}
            )

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            transport=httpx.MockTransport(ok_handler),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 2)
        self.assertEqual(res["stopped_reason"], "COMPLETED_ISOLATED_C01_AND_G01")
        fd_res = res["ledger_summary"]["four_debit_admission_reservation"]
        self.assertTrue(fd_res["session_reservation_acquired"])
        self.assertEqual(fd_res["rolling_24h_prior_attempts_count"], 16)
        self.assertEqual(fd_res["uncertainty_margin_debits_held"], 2)

    def test_21_rr05_missing_sqlite_ledger_fails_closed_for_any_filename_including_ordinary_sqlite3(
        self,
    ) -> None:
        for fname in ("missing.sqlite3", "ordinary.sqlite3"):
            target_db = os.path.join(self.tmp_dir.name, fname)
            calls: list[Any] = []
            runner = g01_mod.IsolatedG01DiagnosticRunner(
                api_key="synthetic-test",
                ledger_path=os.path.join(self.tmp_dir.name, fname + ".json"),
                sqlite_smoke_ledger_path=target_db,
                spacing_ms=0,
                transport=_recording_200_transport(calls),
                **ATTESTED_KWARGS,
            )
            res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
            self.assertEqual(len(calls), 0)
            self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
            self.assertFalse(os.path.exists(target_db))

    def test_22_rr06_preemptive_wall_clock_deadline_interrupts_blocking_transport_at_20ms_ceiling(
        self,
    ) -> None:
        calls: list[str] = []
        started = threading.Event()
        release = threading.Event()
        finished = threading.Event()

        def delayed_handler(req: httpx.Request) -> httpx.Response:
            calls.append(req.url.path)
            started.set()
            release.wait(2.0)
            finished.set()
            return httpx.Response(200, json={"totalTokens": 42})

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            timeout_ms=20,
            session_ceiling_ms=20,
            require_existing_ledger=True,
            transport=httpx.MockTransport(delayed_handler),
            **ATTESTED_KWARGS,
        )
        try:
            t0 = time.monotonic()
            res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            finished_before_release = finished.is_set()

            self.assertTrue(started.is_set())
            self.assertFalse(
                finished_before_release,
                "Caller must return preemptively before the blocked transport completes",
            )
            self.assertEqual(len(calls), 1)
            self.assertLess(elapsed_ms, 1000)
            self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
            self.assertEqual(res["c01_result"]["execution_status"], "TIMEOUT_OUTCOME_UNKNOWN")
        finally:
            release.set()
            finished.wait(2.0)
            if runner.ledger._deferred_lock_reaper_thread is not None:
                runner.ledger._deferred_lock_reaper_thread.join(timeout=2.0)

    def test_23_v14_admission_count_only_and_empty_observations_rejected(self) -> None:
        # Exact reproduction of Nour's additional_probes.py `admission_count_only_no_evidence`
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            pre_dispatch_observations_count=2,
            consumer_pause_confirmed=True,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        ap = res["ledger_summary"]["admission_preconditions"]
        self.assertFalse(ap["admission_attested"])
        self.assertGreater(len(ap["admission_validation_errors"]), 0)

    def test_24_v14_admission_observations_five_minutes_apart_rejected_requires_15_min(
        self,
    ) -> None:
        bad_rec = make_valid_admission_record()
        now = datetime.datetime.now(_UTC)
        bad_rec["pre_dispatch_observations"][0]["observed_at"] = (
            now - datetime.timedelta(minutes=10)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        bad_rec["pre_dispatch_observations"][1]["observed_at"] = (
            now - datetime.timedelta(minutes=5)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")  # only 5 min apart
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            require_existing_ledger=True,
            project_id="trustops-free-tier-sandbox",
            admission_record=bad_rec,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertIn(
            "15 minutes",
            " ".join(
                res["ledger_summary"]["admission_preconditions"]["admission_validation_errors"]
            ),
        )

    def test_25_v14_admission_no_data_available_model_mismatch_missing_pause_ref_or_unknown_headroom_rejected(
        self,
    ) -> None:
        mutations: list[Callable[[dict[str, Any]], Any]] = [
            lambda r: r["pre_dispatch_observations"][0].update(
                {"reported_activity_status": "No data available"}
            ),
            lambda r: r["pre_dispatch_observations"][1].update({"model_id": "gemini-2.5-pro"}),
            lambda r: r.update({"consumer_pause_evidence_ref": None}),
            lambda r: r.update({"dashboard_headroom_status": "UNKNOWN_UNCONFIRMED"}),
        ]
        for idx, mut in enumerate(mutations):
            rec = make_valid_admission_record()
            mut(rec)
            calls: list[Any] = []
            runner = g01_mod.IsolatedG01DiagnosticRunner(
                api_key="synthetic-only",
                ledger_path=os.path.join(self.tmp_dir.name, f"adm_{idx}.json"),
                sqlite_smoke_ledger_path=self.sqlite_path,
                run_id=f"run_adm_neg_{idx}",
                spacing_ms=0,
                require_existing_ledger=True,
                project_id="trustops-free-tier-sandbox",
                admission_record=rec,
                transport=_recording_200_transport(calls),
            )
            res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
            self.assertEqual(len(calls), 0, f"Mutation {idx} unexpectedly dispatched calls")
            self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")

    def test_26_v14_cancellable_transport_shuts_down_worker_completely_before_lock_release(
        self,
    ) -> None:
        # Cancellable transport whose close() unblocks the worker immediately on timeout
        cancelled = threading.Event()
        worker_exited = threading.Event()

        class CancellableTransport(httpx.BaseTransport):
            def handle_request(self, request: httpx.Request) -> httpx.Response:
                cancelled.wait(2.0)
                worker_exited.set()
                raise httpx.ReadTimeout("Cancelled by transport.close()", request=request)

            def close(self) -> None:
                cancelled.set()

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            timeout_ms=20,
            session_ceiling_ms=20,
            require_existing_ledger=True,
            transport=CancellableTransport(),
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertTrue(worker_exited.is_set())
        rte = res["c01_result"]["provider_fault_details"]["request_transport_evidence"]
        self.assertTrue(rte["local_worker_shutdown_verified"])
        self.assertFalse(rte["provider_remote_cancellation_inferred"])
        # Because worker exited cleanly before return, session.lock is now cleanly released and acquirable
        lk = g01_mod.CrossPlatformFileLock(
            os.path.join(self.tmp_dir.name, "session.lock"), timeout_sec=0.1
        )
        lk.acquire()
        lk.release()

    def test_27_v14_uncancellable_worker_keeps_session_lock_held_until_worker_exits(self) -> None:
        # Exact pattern of Nour's additional_probes.py `worker_survives_timeout`:
        # While worker is still blocked, session.lock MUST NOT be reacquirable!
        started = threading.Event()
        release = threading.Event()
        finished = threading.Event()

        def blocking_handler(req: httpx.Request) -> httpx.Response:
            started.set()
            release.wait(2.0)
            finished.set()
            return httpx.Response(200, json={"totalTokens": 42})

        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            timeout_ms=20,
            session_ceiling_ms=20,
            require_existing_ledger=True,
            transport=httpx.MockTransport(blocking_handler),
            **ATTESTED_KWARGS,
        )
        try:
            t0 = time.monotonic()
            res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
            elapsed_ms = (time.monotonic() - t0) * 1000
            self.assertTrue(started.is_set())
            self.assertFalse(
                finished.is_set(),
                "Caller must return preemptively while the blocked transport worker is still active",
            )
            self.assertLess(elapsed_ms, 1000)
            self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")

            # Attempt to acquire session.lock while worker is still active -> MUST FAIL!
            acquired_while_active = False
            lk_probe = g01_mod.CrossPlatformFileLock(
                os.path.join(self.tmp_dir.name, "session.lock"), timeout_sec=0.03
            )
            try:
                lk_probe.acquire()
                acquired_while_active = True
                lk_probe.release()
            except RuntimeError:
                acquired_while_active = False
            self.assertFalse(
                acquired_while_active,
                "session.lock must NOT be reacquired while worker is active!",
            )
        finally:
            # Always unblock worker and join reaper even if an assertion fails above
            release.set()
            finished.wait(2.0)
            if runner.ledger._deferred_lock_reaper_thread is not None:
                runner.ledger._deferred_lock_reaper_thread.join(timeout=2.0)
        lk_after = g01_mod.CrossPlatformFileLock(
            os.path.join(self.tmp_dir.name, "session.lock"), timeout_sec=0.2
        )
        lk_after.acquire()
        lk_after.release()

    def test_28_v14_subprocess_worker_terminated_at_deadline_before_lock_release_with_debit_retained(
        self,
    ) -> None:
        # Proves OS-level worker termination BEFORE session.lock release, retaining completed=NULL attempt debit
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            spacing_ms=0,
            timeout_ms=80,
            session_ceiling_ms=80,
            require_existing_ledger=True,
            use_subprocess_worker=True,
            _simulate_subprocess_block_seconds=2.0,
            **ATTESTED_KWARGS,
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        self.assertEqual(res["c01_result"]["execution_status"], "TIMEOUT_OUTCOME_UNKNOWN")
        rte = res["c01_result"]["provider_fault_details"]["request_transport_evidence"]
        self.assertTrue(rte["local_worker_shutdown_verified"])
        self.assertFalse(rte["provider_remote_cancellation_inferred"])

        # Verify session.lock is cleanly released now that subprocess is dead
        lk = g01_mod.CrossPlatformFileLock(
            os.path.join(self.tmp_dir.name, "session.lock"), timeout_sec=0.2
        )
        lk.acquire()
        lk.release()

        # Verify SQLite attempt debit is preserved with completed IS NULL
        conn = sqlite3.connect(self.sqlite_path)
        row = conn.execute(
            "SELECT run, operation, dispatched, completed FROM attempts WHERE operation='C01'"
        ).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertIsNotNone(row[2])
        self.assertIsNone(row[3])

    def test_29_v15_expired_2020_observations_rejected(self) -> None:
        rec = make_valid_admission_record()
        rec["pre_dispatch_observations"][0]["observed_at"] = "2020-01-01T10:00:00Z"
        rec["pre_dispatch_observations"][1]["observed_at"] = "2020-01-01T10:20:00Z"
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            project_id="trustops-free-tier-sandbox",
            spacing_ms=0,
            require_existing_ledger=True,
            admission_record=rec,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        errs = " ".join(
            res["ledger_summary"]["admission_preconditions"]["admission_validation_errors"]
        )
        self.assertIn("EXPIRED_OR_STALE_OBSERVATION", errs)

    def test_30_v15_future_observation_timestamps_rejected(self) -> None:
        rec = make_valid_admission_record()
        future_t0 = (datetime.datetime.now(_UTC) + datetime.timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        future_t1 = (
            datetime.datetime.now(_UTC) + datetime.timedelta(hours=1, minutes=20)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        rec["pre_dispatch_observations"][0]["observed_at"] = future_t0
        rec["pre_dispatch_observations"][1]["observed_at"] = future_t1
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            project_id="trustops-free-tier-sandbox",
            spacing_ms=0,
            require_existing_ledger=True,
            admission_record=rec,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        errs = " ".join(
            res["ledger_summary"]["admission_preconditions"]["admission_validation_errors"]
        )
        self.assertIn("FUTURE_OBSERVATION_TIMESTAMP", errs)

    def test_31_v15_expired_or_insufficient_pause_window_rejected(self) -> None:
        for bad_window in (
            {"start_at": "2020-01-01T09:50:00Z", "end_at": "2020-01-01T10:50:00Z"},
            {
                "start_at": (datetime.datetime.now(_UTC) - datetime.timedelta(minutes=20)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "end_at": (datetime.datetime.now(_UTC) + datetime.timedelta(minutes=5)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            },
        ):
            rec = make_valid_admission_record()
            rec["consumer_pause_window"] = bad_window
            calls: list[Any] = []
            runner = g01_mod.IsolatedG01DiagnosticRunner(
                api_key="synthetic-only",
                ledger_path=self.ledger_path,
                sqlite_smoke_ledger_path=self.sqlite_path,
                project_id="trustops-free-tier-sandbox",
                spacing_ms=0,
                session_ceiling_ms=900000,
                require_existing_ledger=True,
                admission_record=rec,
                transport=_recording_200_transport(calls),
            )
            res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
            self.assertEqual(len(calls), 0)
            self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
            errs = " ".join(
                res["ledger_summary"]["admission_preconditions"]["admission_validation_errors"]
            )
            self.assertIn("EXPIRED_OR_INSUFFICIENT_PAUSE_WINDOW", errs)

    def test_32_v15_missing_expected_project_id_rejected(self) -> None:
        rec = make_valid_admission_record(project_id="arbitrary-unapproved-project")
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            project_id=None,
            spacing_ms=0,
            require_existing_ledger=True,
            admission_record=rec,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        errs = " ".join(
            res["ledger_summary"]["admission_preconditions"]["admission_validation_errors"]
        )
        self.assertIn("MISSING_REQUIRED_PROJECT_ID", errs)

    def test_33_v16_pause_window_starting_30s_in_future_rejected(self) -> None:
        # Amendment 1: A consumer-pause window beginning 30 seconds in the future MUST be rejected (0 requests)
        rec = make_valid_admission_record()
        now = datetime.datetime.now(_UTC)
        rec["consumer_pause_window"] = {
            "start_at": (now + datetime.timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_at": (now + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        calls: list[Any] = []
        runner = g01_mod.IsolatedG01DiagnosticRunner(
            api_key="synthetic-only",
            ledger_path=self.ledger_path,
            sqlite_smoke_ledger_path=self.sqlite_path,
            project_id="trustops-free-tier-sandbox",
            spacing_ms=0,
            session_ceiling_ms=900000,
            require_existing_ledger=True,
            admission_record=rec,
            transport=_recording_200_transport(calls),
        )
        res = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        self.assertEqual(len(calls), 0)
        self.assertEqual(res["stopped_reason"], "STOPPED_ON_C01_FAILURE")
        errs = " ".join(
            res["ledger_summary"]["admission_preconditions"]["admission_validation_errors"]
        )
        self.assertIn("EXPIRED_OR_INSUFFICIENT_PAUSE_WINDOW", errs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
