"""Portable cross-platform offline mocked probes for G01 diagnostic controls (Q01..Q13).
Runs natively on BOTH Windows (msvcrt.locking) and Linux/macOS (fcntl.flock) with ZERO
unconditional `fcntl` imports.
All HTTP uses httpx.MockTransport and temporary SQLite files; no network calls are made.
Exits 0 when all 14 probes pass with defect_reproduced == False.
"""

import datetime
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import threading
import time
from collections.abc import Callable
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


ROOT = (
    pathlib.Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else _find_repo_root(pathlib.Path(__file__))
)
_g01_path = _find_repo_file("g01_isolated_diagnostic_runner.py", ROOT)
if str(_g01_path.parent) not in sys.path:
    sys.path.insert(0, str(_g01_path.parent))
import g01_isolated_diagnostic_runner as g  # noqa: E402

_UTC: datetime.tzinfo = (
    datetime.UTC if sys.version_info >= (3, 11) else datetime.timezone(datetime.timedelta(0))
)


def make_fresh_admission_record(project_id: str = "trustops-free-tier-sandbox") -> dict[str, Any]:
    now = datetime.datetime.now(_UTC)
    return {
        "project_id": project_id,
        "pre_dispatch_observations": [
            {
                "observation_id": "obs_1",
                "observed_at": (now - datetime.timedelta(minutes=20)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "project_id": project_id,
                "model_id": g.DEFAULT_MODEL_ID,
                "reported_activity_status": "ZERO_ACTIVITY",
                "observed_request_count": 0,
                "evidence_ref": "capture_quota_t0.png",
            },
            {
                "observation_id": "obs_2",
                "observed_at": (now - datetime.timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "project_id": project_id,
                "model_id": g.DEFAULT_MODEL_ID,
                "reported_activity_status": "ZERO_ACTIVITY",
                "observed_request_count": 0,
                "evidence_ref": "capture_quota_t1.png",
            },
        ],
        "consumer_pause_confirmed": True,
        "consumer_pause_evidence_ref": "pause_attestation_active",
        "consumer_pause_window": {
            "start_at": (now - datetime.timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_at": (now + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "dashboard_headroom_status": "CONFIRMED_HEADROOM_AVAILABLE",
    }


ATTESTED: dict[str, Any] = {
    "project_id": "trustops-free-tier-sandbox",
    "admission_record": make_fresh_admission_record(),
}


def ok_transport(req: httpx.Request) -> httpx.Response:
    if req.url.path.endswith(":countTokens"):
        return httpx.Response(200, json={"totalTokens": 42})
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "manager"}]}}]})


def run_case(
    name: str,
    setup: Callable[[pathlib.Path, pathlib.Path, pathlib.Path], None] | None = None,
    **kwargs: Any,
) -> tuple[str, list[str], dict[str, Any], int, bool]:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        db = root / kwargs.pop("db_name", "smoke_ledger.sqlite3")
        ledger = root / "ledger.json"
        if kwargs.pop("create_db", True):
            g.bootstrap_existing_smoke_ledger(str(db))
        if setup:
            setup(root, db, ledger)
        calls: list[str] = []
        transport_fn = kwargs.pop("transport_fn", None)

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req.url.path)
            return transport_fn(req) if transport_fn else ok_transport(req)

        opts = dict(
            api_key="synthetic-test",
            ledger_path=str(ledger),
            sqlite_smoke_ledger_path=str(db),
            transport=httpx.MockTransport(handler),
            spacing_ms=kwargs.pop("spacing_ms", 0),
        )
        on_cleanup: Callable[[], None] | None = kwargs.pop("on_cleanup", None)
        opts.update(kwargs)
        t0 = time.monotonic()
        runner = g.IsolatedG01DiagnosticRunner(**opts)
        try:
            rep = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
            elapsed_ms = int((time.monotonic() - t0) * 1000)
        finally:
            if on_cleanup is not None:
                on_cleanup()
            if runner.ledger._deferred_lock_reaper_thread is not None:
                runner.ledger._deferred_lock_reaper_thread.join(timeout=2.0)
        return name, calls, rep, elapsed_ms, db.exists()


out = []

# Q01: Omitted admission confirmation defaults must be unconfirmed (0 requests)
_name, calls, rep, _ms, _exists = run_case(
    "Q01_omitted_admission_confirmation_defaults", require_existing_ledger=True
)
ap = rep["ledger_summary"].get("admission_preconditions", {})
out.append(
    dict(
        probe="Q01_omitted_admission_confirmation_defaults",
        defect_reproduced=(
            len(calls) > 0
            or ap.get("pre_dispatch_observations_count") != 0
            or ap.get("consumer_pause_confirmed") is not False
        ),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
        admission_preconditions=ap,
    )
)


# Q02: Two existing 24h reservations in `runs` with zero `attempts` rows must block admission
def two_reservations(root: pathlib.Path, db: pathlib.Path, ledger: pathlib.Path) -> None:
    conn = sqlite3.connect(db)
    now = time.time()
    for i in range(2):
        conn.execute("INSERT INTO runs VALUES (?, ?)", (f"old-reservation-{i}", now - 7200 + i))
    conn.commit()
    conn.close()


_name, calls, rep, _ms, _exists = run_case(
    "Q02_two_existing_24h_reservations_no_attempts",
    setup=two_reservations,
    require_existing_ledger=True,
    **ATTESTED,
)
out.append(
    dict(
        probe="Q02_two_existing_24h_reservations_no_attempts",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
        active_competing_runs=rep["ledger_summary"].get("active_competing_runs_detected"),
    )
)


# Q03: 16 completed attempts in last 24h (4 debits available) -> 1 four-debit reservation acquired prior to C01
def sixteen(root: pathlib.Path, db: pathlib.Path, ledger: pathlib.Path) -> None:
    conn = sqlite3.connect(db)
    now = time.time()
    conn.execute("INSERT INTO runs VALUES (?, ?)", ("prior", now - 7200))
    for i in range(16):
        t = now - 7200 + i
        conn.execute(
            "INSERT INTO attempts VALUES (?, ?, ?, ?)", ("prior", f"uuid-{i}:G02", t, t + 1)
        )
    conn.commit()
    conn.close()


_name, calls, rep, _ms, _exists = run_case(
    "Q03_exactly_four_debits_initially_available",
    setup=sixteen,
    require_existing_ledger=True,
    **ATTESTED,
)
out.append(
    dict(
        probe="Q03_exactly_four_debits_initially_available",
        defect_reproduced=(
            len(calls) != 2 or rep["stopped_reason"] != "COMPLETED_ISOLATED_C01_AND_G01"
        ),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
        c01_status=rep["c01_result"]["execution_status"],
        g01_status=rep["g01_result"]["execution_status"] if rep["g01_result"] else None,
    )
)

# Q04: Both `missing.sqlite3` and `ordinary.sqlite3` must fail closed without creating the database
for db_name in ["missing.sqlite3", "ordinary.sqlite3"]:
    _name, calls, rep, _ms, exists = run_case(
        f"Q04_missing_path_filename_{db_name}",
        db_name=db_name,
        create_db=False,
        **ATTESTED,
    )
    out.append(
        dict(
            probe=f"Q04_missing_path_filename_{db_name}",
            defect_reproduced=(len(calls) > 0 or exists),
            mock_requests=len(calls),
            stopped_reason=rep["stopped_reason"],
            created=exists,
        )
    )


# Q05: Blocking transport (2s Event wait) under 20ms ceiling must abort preemptively before worker exits
q05_started = threading.Event()
q05_release = threading.Event()
q05_finished = threading.Event()
q05_finished_before_cleanup: dict[str, bool] = {"value": False}


def delayed(req: httpx.Request) -> httpx.Response:
    q05_started.set()
    q05_release.wait(2.0)
    q05_finished.set()
    return ok_transport(req)


def q05_cleanup() -> None:
    q05_finished_before_cleanup["value"] = q05_finished.is_set()
    q05_release.set()
    q05_finished.wait(2.0)


_name, calls, rep, elapsed_ms, _exists = run_case(
    "Q05_blocking_transport_20ms_session_ceiling",
    transport_fn=delayed,
    on_cleanup=q05_cleanup,
    session_ceiling_ms=20,
    timeout_ms=20,
    require_existing_ledger=True,
    **ATTESTED,
)
out.append(
    dict(
        probe="Q05_blocking_transport_20ms_session_ceiling",
        defect_reproduced=(
            not q05_started.is_set()
            or q05_finished_before_cleanup["value"]
            or elapsed_ms >= 1000
            or rep["c01_result"]["execution_status"] != "TIMEOUT_OUTCOME_UNKNOWN"
        ),
        mock_requests=len(calls),
        elapsed_ms=elapsed_ms,
        preempted_before_worker_exit=(
            q05_started.is_set() and not q05_finished_before_cleanup["value"]
        ),
        stopped_reason=rep["stopped_reason"],
        c01_status=rep["c01_result"]["execution_status"],
    )
)

# Q06 (Portable Windows + POSIX): Holding session.lock via CrossPlatformFileLock must block diagnostic (0 requests)
with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    db = root / "smoke_ledger.sqlite3"
    g.bootstrap_existing_smoke_ledger(str(db))
    ext_lock = g.CrossPlatformFileLock(str(root / "session.lock"), timeout_sec=0.5)
    lock_backend = ext_lock.acquire()
    try:
        calls = []

        def q06_handler(req: httpx.Request) -> httpx.Response:
            calls.append(req.url.path)
            return ok_transport(req)

        runner = g.IsolatedG01DiagnosticRunner(
            api_key="synthetic-test",
            ledger_path=str(root / "ledger.json"),
            sqlite_smoke_ledger_path=str(db),
            transport=httpx.MockTransport(q06_handler),
            spacing_ms=0,
            lock_timeout_sec=0.1,
            require_existing_ledger=True,
            **ATTESTED,
        )
        rep = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
        out.append(
            dict(
                probe="Q06_original_session_lock_held",
                defect_reproduced=(
                    len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"
                ),
                lock_backend=lock_backend,
                mock_requests=len(calls),
                stopped_reason=rep["stopped_reason"],
            )
        )
    finally:
        ext_lock.release()

# Q07 (v1.13 review finding 1): count=2 & pause=True without observation evidence must block (0 requests)
_name, calls, rep, _ms, _exists = run_case(
    "Q07_admission_count_only_no_evidence",
    require_existing_ledger=True,
    pre_dispatch_observations_count=2,
    consumer_pause_confirmed=True,
)
out.append(
    dict(
        probe="Q07_admission_count_only_no_evidence",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
        admission_attested=rep["ledger_summary"]["admission_preconditions"]["admission_attested"],
    )
)

# Q08 (v1.13 review finding 2): Timed-out uncancellable worker must NOT allow session.lock reacquisition while active
with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    db = root / "smoke_ledger.sqlite3"
    g.bootstrap_existing_smoke_ledger(str(db))
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def blocked_handler(req: httpx.Request) -> httpx.Response:
        started.set()
        release.wait(2.0)
        finished.set()
        return ok_transport(req)

    runner = g.IsolatedG01DiagnosticRunner(
        api_key="synthetic-test",
        ledger_path=str(root / "ledger.json"),
        sqlite_smoke_ledger_path=str(db),
        transport=httpx.MockTransport(blocked_handler),
        spacing_ms=0,
        timeout_ms=20,
        session_ceiling_ms=20,
        require_existing_ledger=True,
        **ATTESTED,
    )
    t0 = time.monotonic()
    rep = runner.run_isolated_diagnostic(sleep_fn=lambda _: None)
    q08_elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
    reacquired_while_active = False
    probe_lk = g.CrossPlatformFileLock(str(root / "session.lock"), timeout_sec=0.03)
    try:
        probe_lk.acquire()
        reacquired_while_active = True
        probe_lk.release()
    except RuntimeError:
        reacquired_while_active = False
    release.set()
    finished.wait(1.0)
    if runner.ledger._deferred_lock_reaper_thread is not None:
        runner.ledger._deferred_lock_reaper_thread.join(timeout=1.0)
    out.append(
        dict(
            probe="Q08_timeout_session_lock_held_until_worker_exit",
            defect_reproduced=(
                reacquired_while_active or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"
            ),
            elapsed_ms=q08_elapsed_ms,
            session_lock_reacquired_while_worker_active=reacquired_while_active,
            stopped_reason=rep["stopped_reason"],
        )
    )

# Q09 (v1.14 review): Expired 2020 observations must be rejected (0 requests)
rec_2020 = make_fresh_admission_record()
rec_2020["pre_dispatch_observations"][0]["observed_at"] = "2020-01-01T10:00:00Z"
rec_2020["pre_dispatch_observations"][1]["observed_at"] = "2020-01-01T10:20:00Z"
_name, calls, rep, _ms, _exists = run_case(
    "Q09_expired_2020_observations",
    require_existing_ledger=True,
    project_id="trustops-free-tier-sandbox",
    admission_record=rec_2020,
)
out.append(
    dict(
        probe="Q09_expired_2020_observations",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
    )
)

# Q10 (v1.14 review): Expired 2020 pause window must be rejected (0 requests)
rec_exp_pause = make_fresh_admission_record()
rec_exp_pause["consumer_pause_window"] = {
    "start_at": "2020-01-01T09:50:00Z",
    "end_at": "2020-01-01T10:50:00Z",
}
_name, calls, rep, _ms, _exists = run_case(
    "Q10_expired_pause_window",
    require_existing_ledger=True,
    project_id="trustops-free-tier-sandbox",
    admission_record=rec_exp_pause,
)
out.append(
    dict(
        probe="Q10_expired_pause_window",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
    )
)

# Q11 (v1.14 review): Missing expected project_id (--project-id=None) must be rejected (0 requests)
_name, calls, rep, _ms, _exists = run_case(
    "Q11_missing_expected_project_id",
    require_existing_ledger=True,
    project_id=None,
    admission_record=make_fresh_admission_record(project_id="arbitrary-project"),
)
out.append(
    dict(
        probe="Q11_missing_expected_project_id",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
    )
)

# Q12 (v1.14 review): Future observation timestamps must be rejected (0 requests)
rec_future = make_fresh_admission_record()
fut_now = datetime.datetime.now(_UTC)
rec_future["pre_dispatch_observations"][0]["observed_at"] = (
    fut_now + datetime.timedelta(hours=1)
).strftime("%Y-%m-%dT%H:%M:%SZ")
rec_future["pre_dispatch_observations"][1]["observed_at"] = (
    fut_now + datetime.timedelta(hours=1, minutes=20)
).strftime("%Y-%m-%dT%H:%M:%SZ")
_name, calls, rep, _ms, _exists = run_case(
    "Q12_future_observation_timestamps",
    require_existing_ledger=True,
    project_id="trustops-free-tier-sandbox",
    admission_record=rec_future,
)
out.append(
    dict(
        probe="Q12_future_observation_timestamps",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
    )
)

# Q13 (v1.15 review Amendment 1): Pause window beginning 30s in the future must be rejected (0 requests)
rec_fut_pause = make_fresh_admission_record()
_p_now = datetime.datetime.now(_UTC)
rec_fut_pause["consumer_pause_window"] = {
    "start_at": (_p_now + datetime.timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end_at": (_p_now + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
_name, calls, rep, _ms, _exists = run_case(
    "Q13_pause_window_starting_30s_in_future",
    require_existing_ledger=True,
    project_id="trustops-free-tier-sandbox",
    admission_record=rec_fut_pause,
)
out.append(
    dict(
        probe="Q13_pause_window_starting_30s_in_future",
        defect_reproduced=(len(calls) > 0 or rep["stopped_reason"] != "STOPPED_ON_C01_FAILURE"),
        mock_requests=len(calls),
        stopped_reason=rep["stopped_reason"],
    )
)

print(
    json.dumps(
        {
            "scope": "OFFLINE_MOCKED_PROBES_ONLY_CROSS_PLATFORM",
            "platform": sys.platform,
            "probes": out,
        },
        indent=2,
    )
)
sys.exit(1 if any(p["defect_reproduced"] for p in out) else 0)
