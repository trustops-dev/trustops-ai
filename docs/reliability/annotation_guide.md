# TrustOps AI — Annotation Guide v1

## 1. Annotation objective

Assign one primary reliability label to each trace while preserving secondary evaluator findings separately.

## 2. Annotation sequence

For each trace:

1. Identify the expected scenario.
2. Inspect the execution trace and available evidence.
3. Check whether required events, tools, arguments, retrieval evidence, workflow transitions, policy evidence, and final-answer evidence are present.
4. Determine the primary failure mechanism.
5. Assign exactly one primary label.
6. Record secondary findings separately.
7. Record the concrete evidence supporting the decision.
8. Record ambiguity when evidence is insufficient.

## 3. Critical distinctions

### Retrieval failure vs hallucination

- Retrieval failure: required evidence was not retrieved.
- Hallucination: the final claim is unsupported by the available evidence.

Both may appear as findings on one trace.

### Tool selection vs tool arguments

- Tool selection error: wrong tool.
- Invalid tool arguments: correct tool, invalid inputs.

### Workflow violation vs policy violation

- Workflow violation: execution order/stage/transition is wrong.
- Policy violation: an applicable policy is violated according to independent policy evidence.

### Unsupported completion

Use this when the system claims successful action without sufficient successful action evidence.

## 4. Ground-truth discipline

Never use the output of the evaluator under test as the sole ground-truth label.

## 5. Annotation record

Recommended record:

```json
{
  "trace_id": "trace-001",
  "primary_label": "NORMAL",
  "secondary_findings": [],
  "evidence": [],
  "annotator": "human",
  "ambiguity": false,
  "notes": ""
}
```
