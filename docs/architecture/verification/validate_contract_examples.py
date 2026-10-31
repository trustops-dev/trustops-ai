"""Temporary validation of documented specifications; no runtime implementation."""
import ast
import copy
import json
import re
import sys
import types
from pathlib import Path

from pydantic import ValidationError, __version__

root = Path(__file__).resolve().parents[1]
path = root / 'repository/docs/architecture/evaluation-pipeline.md'
source = path.read_text()
blocks = re.findall(r'```python\n(.*?)\n```', source, re.S)
assert len(blocks) == 2
# The proposed modules do not exist in dev yet. Mount the unchanged first
# documentation block under its documented module name only in this process.
parent = types.ModuleType('trustops_contracts')
parent.__path__ = []
sys.modules[parent.__name__] = parent
models = types.ModuleType('trustops_contracts.evaluations')
sys.modules[models.__name__] = models
exec(compile(blocks[0], str(path) + ':evaluations', 'exec'), models.__dict__)
rca = types.ModuleType('trustops_contracts.rca')
sys.modules[rca.__name__] = rca
exec(compile(blocks[1], str(path) + ':rca', 'exec'), rca.__dict__)
print('Runtime:', sys.version.split()[0], 'Pydantic:', __version__)
samples = [json.loads(b) for b in re.findall(r'```json\s*\n(.*?)\n```', source, re.S)]
assert len(samples) == 6
for sample in samples:
    models.EvaluatorResult.model_validate(sample)
assert {s['evaluator_family'] for s in samples} == {e.value for e in models.EvaluatorFamily}
print('PASS: all six evaluator JSON examples validate against the documented model')

count = 0
def accept(model, payload, label):
    global count
    model.model_validate(copy.deepcopy(payload))
    count += 1
    print('PASS:', label)

def reject(model, payload, label):
    global count
    try:
        model.model_validate(copy.deepcopy(payload))
    except ValidationError:
        count += 1
        print('PASS:', label)
    else:
        raise AssertionError('Accepted invalid payload: ' + label)

classification = dict(prediction_id='p1', evaluation_run_id='run1', trace_id='tr1',
    classifier_type='deterministic_rules', classifier_version='1.0.0',
    feature_schema_version='1.0.0', primary_label='WORKFLOW_VIOLATION',
    secondary_findings=['POLICY_VIOLATION'], classifier_confidence=0.8,
    created_at='2026-10-30T18:00:00Z')
C = models.FailureClassificationResult
accept(C, classification, 'valid primary and secondary labels')
reject(C, classification | {'secondary_findings':['NORMAL']}, 'reject NORMAL secondary')
reject(C, classification | {'primary_label':'NORMAL'}, 'reject NORMAL with secondary failures')
reject(C, classification | {'secondary_findings':['POLICY_VIOLATION']*2}, 'reject duplicate labels')
reject(C, classification | {'secondary_findings':['WORKFLOW_VIOLATION']}, 'reject primary repeated as secondary')
accept(C, classification | {'primary_label':'NORMAL', 'secondary_findings':[]}, 'valid NORMAL classification')

candidates = [dict(rank=i+1,cause=c,evidence_score=s,supporting_events=['e1'],
    explanation='Illustrative evidence', contributions=[]) for i,(c,s) in enumerate(
    [('agent_workflow',0.9),('prompt',0.6),('model_generation',0.3)])]
base = dict(rca_id='r1',evaluation_run_id='run1',trace_id='tr1',rca_engine_version='1.0.0',
    predicted_primary_failure='WORKFLOW_VIOLATION',is_normal_trace=False,
    top_1_cause=copy.deepcopy(candidates[0]),top_3_candidates=copy.deepcopy(candidates),
    created_at='2026-10-30T18:00:00Z')
R = rca.RCAResult
accept(R, base, 'valid evidence-ranked failure')
normal = base | {'predicted_primary_failure':'NORMAL','is_normal_trace':True,
    'top_1_cause':None,'top_3_candidates':[]}
accept(R, normal, 'valid NORMAL RCA')
missing = base | {'insufficient_evidence_flag':True,'top_1_cause':None,'top_3_candidates':[]}
accept(R, missing, 'valid insufficient evidence without fabricated cause')
reject(R, base | {'is_normal_trace':True}, 'reject inconsistent normal flag')
reject(R, normal | {'insufficient_evidence_flag':True}, 'reject NORMAL insufficient-evidence flag')
reject(R, normal | {'top_1_cause':candidates[0]}, 'reject cause on NORMAL')
reject(R, base | {'insufficient_evidence_flag':True}, 'reject ranked causes when evidence missing')
reject(R, base | {'top_1_cause':None,'top_3_candidates':[]}, 'reject empty ranking with sufficient evidence')
bad = copy.deepcopy(base);bad['top_3_candidates'][1]['rank']=3
reject(R, bad, 'reject noncontiguous ranks')
bad = copy.deepcopy(base);bad['top_3_candidates'][1]['cause']='agent_workflow'
reject(R, bad, 'reject duplicate RCA causes')
bad = copy.deepcopy(base);bad['top_3_candidates'][1]['evidence_score']=0.95
reject(R, bad, 'reject unsorted evidence scores')
bad = copy.deepcopy(base);bad['top_1_cause']['evidence_score']=0.8
reject(R, bad, 'reject top-1 score mismatch')
bad = copy.deepcopy(base);bad['top_1_cause']['supporting_events']=['other']
reject(R, bad, 'reject top-1 evidence reference mismatch')
reject(R, base | {'score_semantics':'calibrated_probability'}, 'reject probability claim')

E = models.EvaluatorResult
sample = copy.deepcopy(samples[0]);sample.update(status='COMPLETED',primary_score=0.0,verdict='FAIL',error_info=None)
accept(E, sample, 'COMPLETED failure is a valid negative finding')
reject(E, sample | {'primary_score':None}, 'reject missing completed score')
for status in ['SKIPPED_MISSING_EVIDENCE','NOT_APPLICABLE','ERROR']:
    payload = sample | {'status':status,'primary_score':None,'verdict':None}
    if status == 'ERROR':payload['error_info']={'error_code':'EXAMPLE','error_message':'Example failure'}
    accept(E, payload, status + ' accepts null score/verdict')
    reject(E, payload | {'primary_score':0.0}, status + ' rejects fabricated zero score')
    reject(E, payload | {'verdict':'PASS'}, status + ' rejects PASS verdict')
reject(E, sample | {'status':'ERROR','primary_score':None,'verdict':None}, 'ERROR requires error details')
print(f'PASS: {count} positive/negative contract cases plus six published JSON samples')
