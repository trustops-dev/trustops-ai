"""Offline SDK wire-contract and failure-boundary tests; no provider requests."""

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import httpx
import pytest
from google.genai.errors import ServerError

spec = importlib.util.spec_from_file_location(
    "compat_runner", Path(__file__).with_name("runner.py")
)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def client_for(payload, status=200):
    requests = []
    if "output_text" in payload:
        payload = {
            "status": payload["status"],
            "steps": [
                {
                    "type": "model_output",
                    "content": [{"type": "text", "text": payload["output_text"]}],
                }
            ],
        }

    def handle(request):
        requests.append(request)
        return httpx.Response(status, json=payload)

    return runner.make_client("offline-placeholder", httpx.MockTransport(handle)), requests


@pytest.mark.parametrize(
    "operation,payload",
    [
        ("G01", {"status": "completed", "output_text": "READY"}),
        ("G02", {"status": "completed", "output_text": '{"probe":"trustops-smoke","quantity":1}'}),
        (
            "G03",
            {
                "status": "requires_action",
                "steps": [
                    {
                        "id": "fc-1",
                        "type": "function_call",
                        "name": "smoke_lookup",
                        "arguments": {"item_id": "fixture-001"},
                    }
                ],
            },
        ),
    ],
)
def test_generation_wire(operation, payload):
    client, requests = client_for(payload)
    with client:
        result = runner.execute(client, operation, runner.MODELS[0])
    assert result["status"] == "PASS"
    assert len(requests) == 1
    assert requests[0].url.path == "/v1beta/interactions"
    body = json.loads(requests[0].content)
    assert body["store"] is False and body["stream"] is False
    assert body["generation_config"]["thinking_level"] == "medium"
    if operation == "G02":
        assert body["response_format"]["schema"] == runner.SCHEMA
        assert "tools" not in body
    if operation == "G03":
        assert body["tools"] == [runner.TOOL]
        assert "response_format" not in body


@pytest.mark.parametrize("operation", ["E01", "E02"])
def test_embedding_wire(operation):
    client, requests = client_for({"embeddings": [{"values": [0.5] * 768}]})
    with client:
        result = runner.execute(client, operation, runner.MODELS[0])
    assert result["status"] == "PASS"
    assert result["normalized_l2_norm"] == pytest.approx(1)
    body = json.loads(requests[0].content)
    assert body["requests"][0]["outputDimensionality"] == 768
    assert body["requests"][0]["taskType"] == (
        "RETRIEVAL_DOCUMENT" if operation == "E01" else "RETRIEVAL_QUERY"
    )


@pytest.mark.parametrize("operation", ["G01", "C01", "E01"])
def test_no_hidden_retry(operation):
    client, requests = client_for({"error": {"code": 503, "message": "temporary"}}, 503)
    with client, pytest.raises((RuntimeError, ServerError)):
        runner.execute(client, operation, runner.MODELS[0])
    assert len(requests) == 1


def test_no_automatic_continuation():
    client, requests = client_for({"status": "requires_continuation", "id": "continue-me"})
    with client:
        result = runner.execute(client, "G01", runner.MODELS[0])
    assert result["status"] == "FAIL"
    assert len(requests) == 1


@pytest.mark.parametrize("values", [[0.0] * 768, [1.0] * 767, [float("inf")] * 768])
def test_invalid_embeddings(values):
    # httpx JSON disallows infinity; construct SDK result directly for that boundary.
    from types import SimpleNamespace

    client = SimpleNamespace(
        models=SimpleNamespace(
            embed_content=lambda **kw: SimpleNamespace(embeddings=[SimpleNamespace(values=values)])
        )
    )
    assert runner.execute(client, "E01", runner.MODELS[0])["status"] == "FAIL"


@pytest.mark.parametrize(
    "text",
    [
        '{"probe":"trustops-smoke","quantity":true}',
        '{"probe":"trustops-smoke","quantity":1,"extra":2}',
        "invalid",
    ],
)
def test_strict_schema_validation(text):
    client, _ = client_for({"status": "completed", "output_text": text})
    with client:
        assert runner.execute(client, "G02", runner.MODELS[0])["status"] == "FAIL"


def test_prompt_count_bounds():
    for count in (0, 257):
        client, _ = client_for({"totalTokens": count})
        with client:
            assert runner.execute(client, "C01", runner.MODELS[0])["status"] == "FAIL"


def test_ledger_survives_reopen_and_no_refunds(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    with sqlite3.connect(path) as db:
        runner.reserve(db, "first", 100000)
    with sqlite3.connect(path) as db:
        runner.reserve(db, "second", 100001)
        with pytest.raises(RuntimeError):
            runner.reserve(db, "third", 100002)
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 2


def test_error_sanitization(monkeypatch):
    secret = "private-test-value"
    monkeypatch.setenv("GEMINI_API_KEY", secret)

    def fail(*args, **kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(runner, "make_client", fail)
    result = runner.worker("G01", runner.MODELS[0])
    assert result["status"] == "FAIL"
    assert secret not in json.dumps(result)


def test_dry_plan_has_no_provider_calls():
    assert runner.plan(runner.MODELS[0])["max_http_attempts"] == 8
    assert runner.plan(runner.MODELS[0])["tool_execution_enabled"] is False


def live_args(tmp_path):
    from types import SimpleNamespace

    return SimpleNamespace(
        confirm_free_tier=True,
        confirm_project=True,
        accept_smoke_scope=True,
        available_generation_requests=10,
        available_embedding_requests=4,
        output=str(tmp_path / "results"),
        model=runner.MODELS[0],
    )


@pytest.mark.parametrize("failure", ["timeout", "count_failure", "success"])
def test_parent_deadline_charging_and_stop(tmp_path, monkeypatch, failure):
    from types import SimpleNamespace

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "private-test-value")
    monkeypatch.setattr(runner.time, "sleep", lambda seconds: None)
    calls = []

    def child(command, **kw):
        calls.append(command)
        assert kw["timeout"] in (10, 60)
        assert "private-test-value" not in " ".join(command)
        if failure == "timeout":
            raise runner.subprocess.TimeoutExpired(command, kw["timeout"])
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {"status": "FAIL" if failure == "count_failure" else "PASS"}
            ).encode(),
        )

    monkeypatch.setattr(runner.subprocess, "run", child)
    code = runner.run_live(live_args(tmp_path))
    report = json.loads((tmp_path / "results/results.json").read_text())
    assert len(calls) == (8 if failure == "success" else 1)
    assert code == (0 if failure == "success" else 1)
    assert "private-test-value" not in json.dumps(report)
    with sqlite3.connect(tmp_path / ".trustops-compatibility/ledger.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM attempts").fetchone()[0] == len(calls)


def test_missing_attestation_blocks_before_dispatch(tmp_path):
    args = live_args(tmp_path)
    args.accept_smoke_scope = False
    with pytest.raises(RuntimeError, match="LIVE_ATTESTATIONS"):
        runner.run_live(args)
    assert not (tmp_path / "results").exists()


def test_windows_lock_and_child_without_posix_fds(tmp_path, monkeypatch):
    """Exercise the native Windows branch on a non-Windows CI host with a fake msvcrt."""
    import types

    monkeypatch.setattr(runner, "LOCK_PLATFORM", "win32")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "private-test-value")
    monkeypatch.setattr(runner.time, "sleep", lambda seconds: None)
    calls = []

    class FakeMsvcrt:
        LK_NBLCK = 1
        LK_UNLCK = 2

        @staticmethod
        def locking(fd, mode, length):
            calls.append((mode, length))
            assert length == 1

    monkeypatch.setitem(sys.modules, "msvcrt", FakeMsvcrt)

    def child(command, **kwargs):
        assert "pass_fds" not in kwargs
        return types.SimpleNamespace(returncode=0, stdout=b'{"status":"PASS"}')

    monkeypatch.setattr(runner.subprocess, "run", child)
    assert runner.run_live(live_args(tmp_path)) == 0
    assert calls == [(1, 1), (2, 1)]
    assert (tmp_path / ".trustops-compatibility/session.lock").read_bytes() == b"\0"


def test_windows_failed_attestation_never_acquires_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "LOCK_PLATFORM", "win32")
    args = live_args(tmp_path)
    args.available_generation_requests = 9
    with pytest.raises(RuntimeError, match="LIVE_ATTESTATIONS"):
        runner.run_live(args)
    assert not (tmp_path / "results").exists()
