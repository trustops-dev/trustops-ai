# TrustOps AI — Research Protocol & Experimental Design (`RQ1`–`RQ4` & Ablations `ABL-01` to `ABL-05`)

**Canonical Path:** `research/README.md`  
**Owner (R/A):** Ahmed Ragab (`AI Reliability & Machine Learning Engineer`, `packages/reliability-engine/`)  
**Task / Epic:** `S1-03` — Freeze Failure Taxonomy & Evaluator Contracts (`TAI-EP03`)  

## 1. Research Questions (`RQ1`–`RQ4`) & Evaluation Metrics

* **Primary Ranking Metric (`MRR@3`):** Because `RCAResult.top_3_candidates` exposes at most $k = 3$ ranked candidates (`max_length = 3`), the primary ranking metric across `RQ3` and ablation studies `ABL-01` to `ABL-05` is **Truncated Mean Reciprocal Rank at 3 (`MRR@3`)**, where a ground-truth cause ranked at $r_i \in \{1, 2, 3\}$ contributes $1 / r_i$ and any cause absent from `top_3_candidates` (or when `insufficient_evidence_flag == True`) contributes $0$.

## 2. Related Authoritative Documentation

* **Declarative Taxonomy & RCA Spec:** [`../packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml`](../packages/reliability-engine/src/trustops_reliability/taxonomy/failure_taxonomy.yaml)
* **Evaluation Pipeline, Taxonomy, Evaluator Contracts & RCA Specification:** [`../docs/architecture/evaluation-pipeline.md`](../docs/architecture/evaluation-pipeline.md)
* **Annotation Guide & Worked Examples (`EX-01` to `EX-11`):** [`../docs/architecture/annotation-guide.md`](../docs/architecture/annotation-guide.md)
* **Trace Evidence Requirements & Teammate Interface Contracts:** [`../docs/architecture/trace-evidence-requirements.md`](../docs/architecture/trace-evidence-requirements.md)
* **Week 1 Execution Index & Handoff Package:** [`../docs/team/week1-s1-03-index-and-handoff.md`](../docs/team/week1-s1-03-index-and-handoff.md)
* **Unit Validation Tests:** [`../tests/unit/reliability_engine/test_failure_taxonomy_yaml.py`](../tests/unit/reliability_engine/test_failure_taxonomy_yaml.py)
