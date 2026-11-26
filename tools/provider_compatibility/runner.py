"""Bounded, synthetic Gemini capability probes; no application tools execute."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

LOCK_PLATFORM = sys.platform
SDK = "2.34.0"
MODELS = ("gemini-3.5-flash-lite", "gemini-3.8-flash")
EMBEDDING = "gemini-embedding-001"
PROJECT = "gen-lang-client-0848818912"
PROMPTS = {
    "G01": "Reply with exactly READY.",
    "G02": 'Return JSON with probe "trustops-smoke" and quantity 1.',
    "G03": "Propose calling smoke_lookup with item_id fixture-001. Do not execute anything.",
    "E01": "Synthetic policy: purchases require the configured approval before order creation.",
    "E02": "When is approval needed?",
}
SCHEMA = {
    "type": "object",
    "properties": {
        "probe": {"type": "string", "enum": ["trustops-smoke"]},
        "quantity": {"type": "integer", "enum": [1]},
    },
    "required": ["probe", "quantity"],
    "additionalProperties": False,
}
TOOL = {
    "type": "function",
    "name": "smoke_lookup",
    "description": "Synthetic proposal only; no execution handler exists.",
    "parameters": {
        "type": "object",
        "properties": {"item_id": {"type": "string", "enum": ["fixture-001"]}},
        "required": ["item_id"],
        "additionalProperties": False,
    },
}
OPERATIONS = ("C01", "G01", "C02", "G02", "C03", "G03", "E01", "E02")


def plan(model: str) -> dict:
    return {
        "runner_version": "0.1",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sdk": f"google-genai=={SDK}",
        "model": model,
        "embedding_model": EMBEDDING,
        "project_id_asserted_by_operator": PROJECT,
        "operations": list(OPERATIONS),
        "max_http_attempts": 8,
        "generation_bucket_reservation": 10,
        "embedding_bucket_reservation": 4,
        "automatic_retries": 0,
        "maximum_in_flight": 1,
        "minimum_start_spacing_seconds": 31,
        "session_deadline_seconds": 900,
        "tool_execution_enabled": False,
        "paid_use_authorized_usd": 0,
        "scope": "FIXED_SYNTHETIC_SMOKE_ONLY_NOT_APPLICATION_ACCEPTANCE",
        "token_admission": "PROMPT_ONLY_COUNTS; FULL_ENVELOPE_AND_EMBEDDING_COUNTS_UNVERIFIED",
        "fixtures_sha256": hashlib.sha256(
            json.dumps([PROMPTS, SCHEMA, TOOL], sort_keys=True).encode()
        ).hexdigest(),
    }


def make_client(api_key: str, transport=None):
    import httpx
    from google import genai
    from google.genai import types

    class SingleRequestTransport(httpx.BaseTransport):
        """Enforce one HTTP request even if SDK retry/continuation semantics change."""

        def __init__(self):
            self.inner = transport or httpx.HTTPTransport(retries=0, trust_env=False)
            self.attempts = 0

        def handle_request(self, request):
            if (
                request.url.scheme != "https"
                or request.url.host != "generativelanguage.googleapis.com"
            ):
                raise RuntimeError("UNEXPECTED_ENDPOINT")
            if self.attempts:
                raise RuntimeError("EXTRA_REQUEST_BLOCKED")
            self.attempts += 1
            return self.inner.handle_request(request)

        def close(self):
            self.inner.close()

    http = httpx.Client(
        transport=SingleRequestTransport(), trust_env=False, follow_redirects=False, timeout=50
    )
    return genai.Client(
        vertexai=False,
        api_key=api_key,
        http_options=types.HttpOptions(
            base_url="https://generativelanguage.googleapis.com",
            api_version="v1beta",
            httpx_client=http,
            async_client_args={"trust_env": False},
            retry_options=types.HttpRetryOptions(attempts=0),
            timeout=50000,
        ),
    )


def execute(client, operation: str, model: str) -> dict:
    from google.genai import types

    if operation.startswith("C"):
        probe = "G" + operation[1:]
        result = client.models.count_tokens(model=model, contents=PROMPTS[probe])
        count = result.total_tokens
        if type(count) is not int or not 0 < count <= 256:
            return {"status": "FAIL", "code": "PROMPT_TOKEN_LIMIT"}
        return {"status": "PASS", "prompt_tokens": count, "count_scope": "PROMPT_ONLY"}
    if operation.startswith("E"):
        result = client.models.embed_content(
            model=EMBEDDING,
            contents=PROMPTS[operation],
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="RETRIEVAL_DOCUMENT" if operation == "E01" else "RETRIEVAL_QUERY",
            ),
        )
        vectors = result.embeddings or []
        values = vectors[0].values if len(vectors) == 1 else None
        if not values or len(values) != 768 or not all(math.isfinite(v) for v in values):
            return {"status": "FAIL", "code": "INVALID_EMBEDDING"}
        norm = math.hypot(*values)
        if not math.isfinite(norm) or norm <= 0:
            return {"status": "FAIL", "code": "INVALID_EMBEDDING_NORM"}
        normalized = [v / norm for v in values]
        if abs(math.hypot(*normalized) - 1) > 1e-6:
            return {"status": "FAIL", "code": "NORMALIZATION_FAILED"}
        return {
            "status": "PASS",
            "dimensions": 768,
            "raw_l2_norm": norm,
            "normalized_l2_norm": math.hypot(*normalized),
            "input_token_admission": "UNVERIFIED_FIXED_SHORT_SYNTHETIC_TEXT",
        }
    body = {
        "model": model,
        "input": PROMPTS[operation],
        "store": False,
        "stream": False,
        "background": False,
        "generation_config": {
            "max_output_tokens": 4096 if operation != "G03" else 8192,
            "thinking_level": "medium",
            "thinking_summaries": "none",
        },
        "safety_settings": [
            dict(type=category, threshold="block_medium_and_above", method="probability")
            for category in (
                "hate_speech",
                "dangerous_content",
                "harassment",
                "sexually_explicit",
                "jailbreak",
            )
        ],
    }
    if operation == "G02":
        body["response_format"] = {
            "type": "text",
            "mime_type": "application/json",
            "schema": SCHEMA,
        }
    if operation == "G03":
        body["tools"] = [TOOL]
    result = client.interactions.create(
        **body, automatic_continuation=False, api_version="v1beta", timeout=50
    )
    passed = False
    if operation == "G01":
        passed = result.status == "completed" and (result.output_text or "").strip() == "READY"
    elif operation == "G02" and result.status == "completed":
        try:
            value = json.loads(result.output_text or "")
            passed = (
                value == {"probe": "trustops-smoke", "quantity": 1}
                and type(value["quantity"]) is int
            )
        except (ValueError, TypeError, KeyError):
            pass
    elif operation == "G03":
        calls = [step for step in (result.steps or []) if step.type == "function_call"]
        passed = (
            result.status in ("completed", "requires_action")
            and len(calls) == 1
            and calls[0].name == "smoke_lookup"
            and calls[0].arguments == {"item_id": "fixture-001"}
        )
    # Do not serialize provider text, thought steps, errors, headers or arbitrary metadata.
    return {
        "status": "PASS" if passed else "FAIL",
        "code": "EXPECTED_OUTPUT" if passed else "OUTPUT_MISMATCH",
        "provider_status": result.status
        if result.status
        in (
            "completed",
            "requires_action",
            "requires_continuation",
            "failed",
            "cancelled",
            "in_progress",
        )
        else "unavailable",
        "effective_model_metadata": "unavailable",
        "application_compatibility": "NOT_ESTABLISHED",
    }


def worker(operation: str, model: str) -> dict:
    try:
        if importlib.metadata.version("google-genai") != SDK:
            return {"status": "BLOCKED", "code": "SDK_VERSION_MISMATCH"}
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            return {"status": "BLOCKED", "code": "KEY_NOT_AVAILABLE"}
        with make_client(key) as client:
            return execute(client, operation, model)
    except Exception as exc:
        # Exception messages can contain credentials or server payloads. Never serialize them.
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        return {
            "status": "FAIL",
            "code": "PROVIDER_OR_SDK_ERROR",
            "http_status": code if type(code) is int and 100 <= code <= 599 else None,
        }


def reserve(db: sqlite3.Connection, run_id: str, now: float) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, started REAL NOT NULL)")
    db.execute(
        "CREATE TABLE IF NOT EXISTS attempts "
        "(run TEXT, operation TEXT, dispatched REAL, completed REAL, PRIMARY KEY(run, operation))"
    )
    recent = db.execute("SELECT count(*) FROM runs WHERE started > ?", (now - 86400,)).fetchone()[0]
    if recent >= 2:
        raise RuntimeError("LOCAL_ROLLING_24H_RESERVATION_EXHAUSTED")
    db.execute("INSERT INTO runs VALUES (?, ?)", (run_id, now))
    db.commit()


@contextmanager
def session_lock(lock):
    """Nonblocking, single-host lock; keep the worker handle on POSIX only."""
    if LOCK_PLATFORM == "win32":
        import msvcrt

        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield False
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield True
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def run_live(args) -> int:
    if not (
        args.confirm_free_tier
        and args.confirm_project
        and args.accept_smoke_scope
        and args.available_generation_requests >= 10
        and args.available_embedding_requests >= 4
    ):
        raise RuntimeError("LIVE_ATTESTATIONS_OR_HEADROOM_MISSING")
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("KEY_NOT_AVAILABLE")
    if importlib.metadata.version("google-genai") != SDK:
        raise RuntimeError("SDK_VERSION_MISMATCH")
    state = Path.home() / ".trustops-compatibility"
    state.mkdir(mode=0o700, exist_ok=True)
    with (state / "session.lock").open("a+b") as lock, session_lock(lock) as inherit_lock:
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=False)
        run_id = str(uuid.uuid4())
        db = sqlite3.connect(state / "ledger.sqlite3")
        db.execute("PRAGMA synchronous=FULL")
        reserve(db, run_id, time.time())
        report = {
            "plan": plan(args.model),
            "run_id": run_id,
            "status": "RUNNING",
            "started_at_unix": time.time(),
            "python_version": sys.version.split()[0],
            "package_versions": {
                package: importlib.metadata.version(package)
                for package in ("google-genai", "httpx", "pydantic")
            },
            "results": [],
            "scope_acceptance": "OPERATOR_ATTESTED_SYNTHETIC_ONLY",
            "free_tier_and_headroom": "OPERATOR_ATTESTED_NOT_API_VERIFIED",
        }

        def save():
            pending = output / "results.tmp"
            pending.write_text(json.dumps(report, indent=2) + "\n")
            pending.replace(output / "results.json")

        save()
        deadline = time.monotonic() + 900
        try:
            for operation in OPERATIONS:
                previous = db.execute(
                    "SELECT max(coalesce(completed, dispatched + 60)) FROM attempts"
                ).fetchone()[0]
                wait = max(0, 31 - (time.time() - previous)) if previous else 0
                limit = 10 if operation.startswith("E") else 60
                if time.monotonic() + wait + limit > deadline:
                    report["status"] = "DEADLINE_EXHAUSTED"
                    break
                time.sleep(wait)
                # Charge before spawning: failures, unknown outcome and interruption are not refunded.
                db.execute(
                    "INSERT INTO attempts (run, operation, dispatched) VALUES (?, ?, ?)",
                    (run_id, operation, time.time()),
                )
                db.commit()
                report["results"].append({"operation": operation, "status": "DISPATCH_RESERVED"})
                save()
                try:
                    child = subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--worker",
                            operation,
                            "--model",
                            args.model,
                        ],
                        capture_output=True,
                        **({"pass_fds": (lock.fileno(),)} if inherit_lock else {}),
                        timeout=limit,
                        check=False,
                        env={**os.environ, "TRUSTOPS_SMOKE_WORKER": "1"},
                    )
                    result = (
                        json.loads(child.stdout)
                        if child.returncode == 0
                        else {"status": "FAIL", "code": "WORKER_FAILURE"}
                    )
                except subprocess.TimeoutExpired:
                    result = {"status": "FAIL", "code": "TIMEOUT_OUTCOME_UNKNOWN"}
                except (ValueError, OSError):
                    result = {"status": "FAIL", "code": "WORKER_FAILURE"}
                db.execute(
                    "UPDATE attempts SET completed = ? WHERE run = ? AND operation = ?",
                    (time.time(), run_id, operation),
                )
                db.commit()
                report["results"][-1] = {"operation": operation, **result}
                save()
                if result.get("status") != "PASS":
                    report["status"] = "STOPPED_ON_FAILURE"
                    break
            else:
                report["status"] = "SMOKE_PASS_APPLICATION_ACCEPTANCE_PENDING"
        except BaseException:
            report["status"] = "INTERRUPTED_OR_LOCAL_FAILURE_NO_REPLAY"
            raise
        finally:
            save()
            db.close()
        print(
            json.dumps({"status": report["status"], "results_file": str(output / "results.json")})
        )
        return 0 if report["status"].startswith("SMOKE_PASS") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, default=MODELS[0])
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", default="compatibility-results-local")
    parser.add_argument("--confirm-free-tier", action="store_true")
    parser.add_argument("--confirm-project", action="store_true")
    parser.add_argument("--accept-smoke-scope", action="store_true")
    parser.add_argument("--available-generation-requests", type=int, default=0)
    parser.add_argument("--available-embedding-requests", type=int, default=0)
    parser.add_argument("--worker", choices=OPERATIONS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if os.environ.get("TRUSTOPS_SMOKE_WORKER") != "1":
            return 2
        print(json.dumps(worker(args.worker, args.model)))
        return 0
    if not args.live:
        print(json.dumps({"status": "DRY_RUN_NO_REQUESTS", "plan": plan(args.model)}, indent=2))
        return 0
    try:
        return run_live(args)
    except Exception:
        # Do not echo exception text, argv, environment or credentials.
        print(json.dumps({"status": "BLOCKED", "code": "LOCAL_PREFLIGHT_OR_LEDGER_FAILURE"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
