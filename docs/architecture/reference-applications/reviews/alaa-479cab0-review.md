# Alaa scoped owner review — commit 479cab0

**Overall status: RESPONSE RECEIVED — PARTIAL / CONDITIONAL.** No unconditional specialist sign-off, joint contract freeze or runtime verification is recorded.

| Evidence field | Recorded value |
|---|---|
| Reviewer | Alaa |
| Reviewed commit | [`479cab00c021db7a58b826b46a653c3e2308b798`](https://github.com/trustops-dev/trustops-ai/commit/479cab00c021db7a58b826b46a653c3e2308b798) |
| Record created | 2026-11-06, Africa/Cairo; documentation date only |
| Source | Email reply text supplied by Nour in this conversation |
| Email date / subject / message reference / sender address | Not supplied; no values inferred |
| Review scope | Reproducibility, dataset lineage, inference projection, embedding identity and workload accounting |
| Review provenance | User-supplied reply text; not independently retrieved mailbox evidence |
| Current editing baseline | `283fe866e3a2332409e179445a9f62c8cb876728` (publication metadata update) |

The source response states that its dispositions are owner-side review responses, not cross-team approval or runtime verification. The machine-readable [review record](alaa-479cab0-review.json) preserves the decision mapping and relevant file hashes at the reviewed commit. Acceptance is bounded by the reviewed commit and stated scope; later changes do not inherit automatic sign-off.

## Decision dispositions and conditions

ALA identifiers below are local review-item labels, not new canonical project decision IDs. Conditions are OPEN except the preserved OD-15 deferral. The evidence lists are required future closure evidence, not executed results.

### ALA-01 — OD-13

**Email disposition:** ACCEPT, subject to explicit conventions.

**Recorded status:** `ACCEPT_WITH_CONDITIONS`.

**Accepted scope / position:** Separate requested configuration, credential-free serialized provider request and observed provider metadata; reference immutable versioned app/prompt/provider-model/retriever/embedding/corpus-index/scenario artifacts. Requested values are not observed values without provider evidence.

**Remaining condition:** Explicit versioned reference-resolution and requested/serialized/observed conventions; unavailable observed metadata stays explicitly unavailable.

**Owners:** Alaa: lineage conventions; Mohab: serialization and retention; Nour: application provenance.

**Evidence to close:** Versioned convention and example provenance records.

**Verification boundary:** Design convention; runtime emission verification later.

### ALA-02 — OD-13

**Email disposition:** AMEND / JOINT AGREEMENT REQUIRED.

**Recorded status:** `AMEND_JOINT_AGREEMENT_REQUIRED`.

**Accepted scope / position:** Keep exact-file SHA-256 distinct from runtime JSON canonicalization. Proposed meanings: missing = absent field; null = present null; unavailable = could not obtain; not_applicable = does not apply; redacted = intentionally withheld.

**Remaining condition:** Jointly define runtime serialization, digest inputs, Unicode handling, numeric representation and retention/redaction rules.

**Owners:** Alaa; Mohab.

**Evidence to close:** Deterministic digest vectors covering key order, Unicode, numeric representation and missing versus null; retention/redaction table.

**Verification boundary:** Joint design agreement and offline vector verification; no convention implemented here.

### ALA-03 — OD-13, OD-05

**Email disposition:** ACCEPT WITH A REQUIRED PROJECTION CORRECTION.

**Recorded status:** `ACCEPT_WITH_REQUIRED_CORRECTION`.

**Accepted scope / position:** Exclude evaluation-only labels, injected causes, recipes, qrels, poisoned-document flags, fixture expectations and ground-truth sidecars. Preserve actual retrieved document IDs despite overlap with evaluation metadata.

**Remaining condition:** Correct R16-05 projection enforcement and distinguish runtime retrieval provenance from evaluation-only expected references.

**Owners:** Alaa: requirements; Mohab: serialization/schema enforcement; Ahmed: evaluation-side validation; Nour: application provenance.

**Evidence to close:** Positive/negative cases: injected cause/evaluation-only fields excluded; legitimate retrieved IDs retained; expected IDs supplied only through evaluation metadata excluded.

**Verification boundary:** Projection design and correction tests; runtime integration proof still pending.

### ALA-04 — OD-LLM-01

**Email disposition:** ACCEPT THE PROPOSED PROFILE; ACCESS AND COMPATIBILITY REMAIN PENDING.

**Recorded status:** `CANDIDATE_ACCEPTED_BY_ALAA`.

**Accepted scope / position:** Pinned generation profile accepted as a reproducibility candidate; requested settings, documented capabilities, actual access and executed checks remain separate.

**Remaining condition:** Provider/SDK/API and interface compatibility still require evidence and the relevant shared review.

**Owners:** Nour; Alaa; Mohab: compatibility/interface verification.

**Evidence to close:** Pinned configuration and scoped compatibility/interface results when executed.

**Verification boundary:** Candidate design only; no live compatibility verified.

### ALA-05 — OD-LLM-02

**Email disposition:** ACCESS AND COMPATIBILITY REMAIN PENDING.

**Recorded status:** `PENDING`.

**Accepted scope / position:** No project access, quota, billing or live compatibility confirmation was given.

**Remaining condition:** Identify the API project owner and supply quota and budget/workload assessment before workload generation.

**Owners:** Nour: project/access information and workload proposal; Alaa: workload/quota review; Mohab: relevant compatibility/interface evidence.

**Evidence to close:** Non-secret project/environment/owner confirmation, applicable quotas and budget/workload assessment.

**Verification boundary:** Access/workload evidence pending; no live check performed by this record.

### ALA-06 — OD-RAG-01

**Email disposition:** ACCEPT AS A CANDIDATE, NOT AS A FROZEN INDEX CONFIGURATION.

**Recorded status:** `CANDIDATE_ACCEPTED_BY_ALAA`.

**Accepted scope / position:** gemini-embedding-001, 768 dimensions, retrieval task types and client L2 normalization accepted for candidate evaluation. Model/dimensions/task/preprocessing/normalization changes create a new embedding configuration and corresponding index version; incompatible vectors must not mix.

**Remaining condition:** Complete embedding integration and configuration/index identity, compatibility and evaluation evidence before freezing.

**Owners:** Nour: embedding integration; Mohab: storage compatibility; Alaa and Ahmed: lineage/evaluation implications.

**Evidence to close:** Immutable embedding/index configuration identities and integration/compatibility/evaluation evidence when executed.

**Verification boundary:** Candidate design only; no frozen index or measured quality claimed.

### ALA-07 — OD-10

**Email disposition:** Storage/index availability remains subject to Mohab environment verification.

**Recorded status:** `PENDING_ENVIRONMENT_VERIFICATION`.

**Accepted scope / position:** Candidate acceptance does not confirm pgvector or an accepted storage/index implementation.

**Remaining condition:** Mohab verifies the target environment and storage compatibility; resolve accepted backend/index choice.

**Owners:** Mohab: environment/storage; Nour: retrieval integration; Alaa and Ahmed: relevant lineage/evaluation implications.

**Evidence to close:** Environment verification output and accepted storage/index configuration.

**Verification boundary:** Environment/design evidence pending; not run here.

### ALA-08 — OD-12-BUDGET

**Email disposition:** AMEND / CONDITIONAL ACCEPTANCE.

**Recorded status:** `AMEND_CONDITIONAL_ACCEPTANCE`.

**Accepted scope / position:** Support root-scoped accounting, shared parallel counters, no reset across retries/restarts/resumes, logical-operation versus attempt accounting, same-root retry debits, parallel reservations, root/profile identity on resume, durable counters/leases/checkpoints and fail-closed behavior if accounting is unavailable.

**Remaining condition:** Numeric limits remain proposed until workload assumptions and actual provider quotas are reviewed; implementation contract must preserve the stated accounting requirements.

**Owners:** Nour: application configuration; Mohab: ledger/persistence; Alaa: workload/experiment review; Mohamed: purchasing boundaries.

**Evidence to close:** Row-level numeric disposition, quota/workload assessment and ledger/reservation/resume/exhaustion contract; later accounting-unavailable and concurrency/restart tests.

**Verification boundary:** Design conditions and workload review now; runtime ledger verification later.

### ALA-09 — OD-08

**Email disposition:** ACCEPT THE GROUPING PRINCIPLE; PLAN APPROVAL PENDING.

**Recorded status:** `GROUPING_PRINCIPLE_ACCEPTED_SCHEDULE_PENDING`.

**Accepted scope / position:** Group scenario family/template/recipe variants/controls before split assignment. Post-freeze recipe admission requires versioned dataset/split impact review.

**Remaining condition:** Schedule and capacity require the designated plan owner; dataset/split conventions and admission evidence remain to be finalized.

**Owners:** Alaa: grouping/split review; Nour: scenario provenance and coordination; Ahmed: relevant scenario/evaluation review; Designated plan owner: schedule/capacity.

**Evidence to close:** Grouping and split/admission convention plus named plan-owner schedule/capacity disposition.

**Verification boundary:** Design/schedule decision; no dataset split or schedule amendment executed.

### ALA-10 — OD-09

**Email disposition:** PENDING JOINT MAPPING.

**Recorded status:** `PENDING_JOINT_MAPPING`.

**Accepted scope / position:** Support independent labels and distinct prevented, realized, definitively no-effect and unknown outcomes.

**Remaining condition:** Ahmed/Mohamed agree exact label precedence and policy outcome interpretation before Alaa finalizes dataset and GD-26 gate mapping.

**Owners:** Ahmed: label precedence; Mohamed: policy outcome interpretation; Alaa: dataset/gate mapping.

**Evidence to close:** Joint outcome/precedence examples and versioned GD-26 mapping; any scope extension retains its existing plan-approval gate.

**Verification boundary:** Joint design mapping only; not completed here.

### ALA-11 — OD-15

**Email disposition:** OD-15 remains deferred pending measured baselines.

**Recorded status:** `DEFERRED_PRESERVED`.

**Accepted scope / position:** No numeric reliability or regression thresholds proposed.

**Remaining condition:** Retain deferral until measured baselines and the existing designated stage.

**Owners:** Ahmed; Mohamed; Alaa.

**Evidence to close:** Measured baseline evidence and later versioned threshold proposal at the existing OD-15 stage.

**Verification boundary:** Existing deferral retained; no new Week 1/2 threshold task.

## Relevant file revisions at the reviewed commit

These are traceability references for the response scope, not individual file signatures. Exact bytes are indexed in the JSON record.

| File | Revision / historical label | SHA-256 |
|---|---|---|
| `docs/adr/reference-application-orchestration-and-llm.md` | 0.9 | `1493e2115ffa87e8548ca4adc3b49f57b376b2a1dd638ae644b82a8b56d964da` |
| `docs/adr/application-execution-budgets.md` | 0.1 | `05534790755d6f15b54586724af36e61ac1b66e6ca11b99654f8401967a60af6` |
| `docs/architecture/reference-applications/rag-contract.md` | 0.9 | `8d9d0fa056a419943a8a3cbdd28fd7885fbdcca0e925352fbf3dfd6c4c827797` |
| `docs/architecture/reference-applications/trace-evidence-contract.md` | original baseline 0.6; current v1.6 mapping addendum | `6b79c3796f5940a2bcd3eea353232220b6e844224f61368109af318fe8ce2761` |
| `docs/architecture/reference-applications/failure-planning-matrix.md` | 0.6 baseline with later schedule addenda | `bb07ac7cb96ca5d1e9ead3c7496e689bbf029d84fc42843b38039dc3324a0ae9` |
| `docs/architecture/reference-applications/schema-v1.6-evidence-mapping.json` | 1.0 | `4f76c2fc9e853b9ddf5ab586fafad28260f78fe4cd8df18fc32114815a8fb295` |
| `docs/architecture/reference-applications/open-decisions.md` | 2026-11-05 consolidation with 2026-11-06 additions | `6b645660b7ed667b4910bbe7a89976e8bcdfa421fa856aa95e78d0532096c39e` |
| `docs/architecture/reference-applications/handoffs.md` | 2026-11-05 consolidation with 2026-11-06 additions | `a1304402f847b69a6345c5ed787309220a945f37fa01bc9c9246d6baca352f04` |
| `docs/architecture/reference-applications/week1-review-manifest.json` | owner packet status-cleanup 0.14 | `7d5d678f2c8eeeca0ec63b6ec30e89b8633311837e1b866650f3ed2c4a6a9bc6` |

## Closure and follow-up

- Record evidence and the affected review-item/decision ID before closing a condition. A subsequent reply must identify its reviewed revision and exact replacement convention/configuration where amended.
- Nour supplies API-project ownership/access information and workload assumptions, and coordinates targeted follow-up.
- Mohab and Alaa agree canonicalization/missingness; Mohab returns projection/storage/accounting evidence within his scope. Ahmed reviews evaluation/projection and label meaning; Mohamed purchasing and policy meaning; the plan owner schedule/capacity.
- Do not ask Alaa to repeat already accepted candidate/grouping principles; send the missing evidence and concrete conventions.

- OD-03 and OD-04 joint acceptance remain pending and were not granted in this reply.
- OD-APP-OBS-01 semantics remain confirmed; validity, continuation and adapter proof stay separate.
- E01–E27 status remains 9 OK / 9 CHANGE REQUIRED / 9 OPEN; 16 independent unmet expectations remain.
- OD-14 receives a scoped Alaa response, not an unconditional specialist signature or shared freeze.
- Other owner responses are not inferred from this email.
