"""Offline additional review probes (P01..P08). Usage: python reproduce_findings.py PACKAGE_DIR.
All HTTP uses httpx.MockTransport; only temporary SQLite files are touched.
Aligned to updated_schemas_v18.md and structured 15-minute admission evidence (Package v1.18.0).
Exit status is nonzero while observed defects remain.
"""
import copy
import datetime
import json
import pathlib
import sqlite3
import sys
import tempfile
import time

import httpx

import os

_REPO_SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    "build", "dist", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "negative_and_variant_probes", ".tox", ".eggs",
}

def _find_repo_root(start: "pathlib.Path") -> "pathlib.Path":
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return start.resolve().parent if start.is_file() else start.resolve()

def _find_repo_file(filename: str, start: "pathlib.Path", prefer_in: tuple = (), avoid_in: tuple = ()) -> "pathlib.Path":
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
        dirs[:] = sorted(d for d in dirs if d not in _REPO_SKIP_DIRS and not d.endswith(".egg-info"))
        if filename in files:
            matches.append(pathlib.Path(root) / filename)
    if not matches:
        raise FileNotFoundError(f"Could not locate {filename} from {here} or repo root {repo_root}")
    def _rank(p: "pathlib.Path") -> tuple:
        parts = set(p.parts)
        pref_score = 0 if (not prefer_in or any(x in parts for x in prefer_in)) else 1
        avoid_score = 1 if any(x in parts for x in avoid_in) else 0
        return (avoid_score, pref_score, len(p.parts), str(p))
    matches.sort(key=_rank)
    return matches[0]

PKG = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _find_repo_root(pathlib.Path(__file__))
for _needed in (
    'g01_isolated_diagnostic_runner.py',
    'run_s1_01_regression_suite.py',
    'validate_s1_01_schema_v1_11.py',
):
    _p = _find_repo_file(_needed, PKG)
    if str(_p.parent) not in sys.path:
        sys.path.insert(0, str(_p.parent))
import g01_isolated_diagnostic_runner as g
import run_s1_01_regression_suite as suite
import validate_s1_01_schema_v1_11 as validator
try:
    from trustops_sdk import trustops_sdk as sdk
except ImportError:
    _sdk_p = _find_repo_file('trustops_sdk.py', PKG)
    if str(_sdk_p.parent) not in sys.path:
        sys.path.insert(0, str(_sdk_p.parent))
    import trustops_sdk as sdk

_NOW = datetime.datetime.now(datetime.timezone.utc)
ATTESTED = dict(
    project_id="trustops-free-tier-sandbox",
    admission_record={
        "project_id": "trustops-free-tier-sandbox",
        "pre_dispatch_observations": [
            {
                "observation_id": "obs_repro_1",
                "observed_at": (_NOW - datetime.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "project_id": "trustops-free-tier-sandbox",
                "model_id": g.DEFAULT_MODEL_ID,
                "reported_activity_status": "ZERO_ACTIVITY",
                "observed_request_count": 0,
                "evidence_ref": "capture_repro_t0.png",
            },
            {
                "observation_id": "obs_repro_2",
                "observed_at": (_NOW - datetime.timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "project_id": "trustops-free-tier-sandbox",
                "model_id": g.DEFAULT_MODEL_ID,
                "reported_activity_status": "ZERO_ACTIVITY",
                "observed_request_count": 0,
                "evidence_ref": "capture_repro_t1.png",
            },
        ],
        "consumer_pause_confirmed": True,
        "consumer_pause_evidence_ref": "pause_window_reproduce_findings",
        "consumer_pause_window": {
            "start_at": (_NOW - datetime.timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_at": (_NOW + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "dashboard_headroom_status": "CONFIRMED_HEADROOM_AVAILABLE",
    },
)

results = []
def record(name, defect, **data):
    results.append(dict(probe=name, defect_reproduced=defect, **data))

def success(req):
    if req.url.path.endswith(':countTokens'):
        return httpx.Response(200, json={'totalTokens': 42})
    return httpx.Response(200, json={'candidates':[{'content':{'parts':[{'text':'manager'}]}}]})

with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    dbpath = root/'legacy.sqlite3'
    db = sqlite3.connect(dbpath)
    db.executescript('CREATE TABLE runs (id TEXT PRIMARY KEY, started REAL NOT NULL); CREATE TABLE attempts (run TEXT, operation TEXT, dispatched REAL, completed REAL, PRIMARY KEY(run,operation));')
    db.execute('INSERT INTO runs VALUES (?,?)', ('historical', time.time()-8*86400))
    db.commit(); db.close()
    calls=[]
    def logged(req):
        calls.append(req.url.path)
        return success(req)
    runner=g.IsolatedG01DiagnosticRunner(api_key='synthetic-test', ledger_path=str(root/'legacy.json'),sqlite_smoke_ledger_path=str(dbpath),transport=httpx.MockTransport(logged),spacing_ms=0,**ATTESTED)
    r=runner.run_isolated_diagnostic(sleep_fn=lambda _:None)
    record('P01_actual_smoke_schema', bool(runner.ledger.initialization_error) or len(calls)!=2, error=runner.ledger.initialization_error, stopped_reason=r['stopped_reason'],mock_requests=len(calls))

    missing=root/'missing.sqlite3'
    calls.clear()
    runner=g.IsolatedG01DiagnosticRunner(api_key='synthetic-test',ledger_path=str(root/'missing.json'),sqlite_smoke_ledger_path=str(missing),transport=httpx.MockTransport(logged),spacing_ms=0,**ATTESTED)
    r=runner.run_isolated_diagnostic(sleep_fn=lambda _:None)
    record('P02_missing_existing_ledger', len(calls)>0 or missing.exists(), created_new_db=missing.exists(), mock_requests=len(calls),stopped_reason=r['stopped_reason'])

    for name,exc in [('P03_instant_read_timeout',httpx.ReadTimeout),('P04_write_error_not_timeout',httpx.WriteError)]:
        def handler(req):
            if req.url.path.endswith(':countTokens'):return success(req)
            raise exc('synthetic immediate exception',request=req)
        p_db = root/(name+'.sqlite3')
        g.bootstrap_existing_smoke_ledger(str(p_db))
        runner=g.IsolatedG01DiagnosticRunner(api_key='synthetic-test',ledger_path=str(root/(name+'.json')),sqlite_smoke_ledger_path=str(p_db),transport=httpx.MockTransport(handler),spacing_ms=0,**ATTESTED)
        start=time.monotonic();r=runner.run_isolated_diagnostic(sleep_fn=lambda _:None);wall_ms=int((time.monotonic()-start)*1000)
        f=r['g01_result']['provider_fault_details'];t=f['request_transport_evidence']
        defect=(t['elapsed_ms_at_fault']>wall_ms+1000) if exc is httpx.ReadTimeout else f['error_category']=='TIMEOUT'
        record(name,defect,wall_ms=wall_ms,reported_elapsed_ms=t['elapsed_ms_at_fault'],status=r['g01_result']['execution_status'],error_category=f['error_category'],grpc_status_code=f['grpc_status_code'])

    class BrokenStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"candidates":'
            raise httpx.ReadTimeout('synthetic body timeout')
    def stream_handler(req):
        if req.url.path.endswith(':countTokens'):return success(req)
        return httpx.Response(200,stream=BrokenStream())
    s_db = root/'stream.sqlite3'
    g.bootstrap_existing_smoke_ledger(str(s_db))
    runner=g.IsolatedG01DiagnosticRunner(api_key='synthetic-test',ledger_path=str(root/'stream.json'),sqlite_smoke_ledger_path=str(s_db),transport=httpx.MockTransport(stream_handler),spacing_ms=0,**ATTESTED)
    f=runner.run_isolated_diagnostic(sleep_fn=lambda _:None)['g01_result']['provider_fault_details']
    record('P05_body_fault_summary_contradicts_headers', 'before HTTP status headers' in f['sanitized_diagnostic_summary'], http_status=f['http_status'],http_headers_received=f['request_transport_evidence']['http_headers_received'],summary=f['sanitized_diagnostic_summary'])

    spec_file = _find_repo_file('updated_schemas_v18.md', PKG)
    s=spec_file.read_text(encoding='utf-8')
    c=next(c for c in suite.build_cases() if c['case_id']=='POS-30')
    w=copy.deepcopy(suite.extract_json_blocks(s)[8+c['wt_idx']][1]);c['mutator'](w)
    for suffix,fields in [('snapshot',['cited_snapshot_id']),('hash',['cited_content_hash']),('all',['cited_snapshot_id','cited_content_hash','cited_source_id'])]:
        m=copy.deepcopy(w);removed=0
        for e in m['events']:
            for cit in e['attributes'].get('visible_citations',[]):
                for key in fields:
                    if key in cit:removed+=1;del cit[key]
        path=root/(suffix+'.md');path.write_text(suite.rebuild_spec_with_wt(s,c['wt_idx'],m),encoding='utf-8')
        passed,codes,_=validator.SpecValidator(str(path),check_report_sync=False).validate()
        record('P06_missing_required_citation_'+suffix,passed and removed>0,removed_fields=removed,validator_passed=passed,codes=codes)

    gate=sdk.InMemoryIngestionGate()
    code,status,_=gate.ingest_trace({'trace_id':'invalid_minimal','schema_version':'1.0.0'})
    record('P07_ingestion_without_events',code==201,http_status=code,status=status)

    claimdb=root/'claims.sqlite3'
    gate=sdk.SqliteTransactionalClaimGate(str(claimdb));gate.conn.close()
    try:
        reopened=sdk.SqliteTransactionalClaimGate(str(claimdb));reopened.conn.close()
        record('P08_claim_database_reopen',False)
    except Exception as e:record('P08_claim_database_reopen',True,error=str(e))

print(json.dumps({'scope':'OFFLINE_REVIEW_ONLY_NO_LIVE_CALLS','platform':sys.platform,'results':results},indent=2))
sys.exit(1 if any(r['defect_reproduced'] for r in results) else 0)