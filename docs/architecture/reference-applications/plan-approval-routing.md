# Team-lead plan decisions — six decision groups

**Prepared 2026-11-09 by Nour; authority corrected 2026-11-14. Status: TEAM LEAD IDENTIFIED; SIX ROW-LEVEL PLAN DECISIONS PENDING.** This packet routes the plan-impacting portions of OD-02, OD-06, OD-08, OD-16, GD-26/OD-09 and Malak's proposed UI schedule. Specialist dispositions remain separate from Nour's team-level plan decisions; the attached HTML proposal is not an approved plan.

## 1. Authority finding

| Source inspected | What it establishes | What it does not establish |
|---|---|---|
| TrustOps proposal v1.1, exact file SHA-256 `8477f21210c1ba142c7a85a59ccc1fb38eb7d991da1b012f8443812538c3f36c` | Six named subsystem owners and their workstream RACI; cover says “Prepared for: Prof. Dr. Noha Yehia.” | No RACI row or approval delegation for amendments to the 16-week sprint plan. “Prepared for” does not confer schedule-change authority. |
| Original sprint plan HTML, SHA-256 `6bbfc2eeeeedb473ad7052c0973feda04ea7cab1b5892456057320a5bf154bd1` | Sprint tasks, owners, dependencies and gates. | No named final plan approver or change-control signature. |
| UI plan snapshots dated 2026-11-07, SHA-256 `cca78edca35d450b743412a0985936a70478307ebe9426fdfc7b73ae216fbefb` and `5af1d891132436a39b566337fb753aaff0c97975c5f8c50544ba38536b4586dc` | Proposed Sprint 3–6 UI amendments and owner claims. | No signed approval. The plans describe uncommitted work and 134 passing tests, while Malak's later report says 137. |
| Current owner decisions/governance draft | Explicitly require a “plan owner” for OD-02/06/08/16 and the GD-26 extension. | No personal name or delegated authority. |

**Current finding:** The source audit above establishes only what those documents say. Nour directly confirmed on 2026-11-14 that he is the development team lead and there is no separate plan approver in the team's process. Nour owns decisions on amendments to the team's internal 16-week working plan. The proposal's academic recipient is not an additional approval gate. This role confirmation identifies the decision owner; it does **not** record acceptance of any of the six proposed changes or establish academic/institutional approval. Record each later decision against an exact plan revision.

| Authority field | Current value |
|---|---|
| Team plan decision owner | **Nour El-Rouby, development team lead** |
| Authority basis and scope | Nour's direct role/process confirmation; team's internal working-plan changes only |
| Confirmation date / reference | 2026-11-14; user confirmation in this review conversation |
| Decision evidence | Nour's dated, explicit ACCEPT/AMEND/DECLINE for each decision ID, tied to exact plan revision and affected task IDs |

### Decision ownership

Nour obtains scoped technical input from the owners named below, then records his own plan decisions. No request to identify or contact a separate approver is needed for this internal plan. Ownership does not resolve technical questions or substitute for reviewers' scoped evidence.

## 2. Review-ready plan questions

| Decision | Technical/proposal owner review first | Exact plan-level proposal to ACCEPT / AMEND / DECLINE | Plan approval evidence required |
|---|---|---|---|
| **OD-02 / GD-01** | Mohamed: governance permission and stage allowlist; Mohab: canonical tool/check representation; Nour: state fit. Mohamed's scoped email accepts the narrower read-only `calculate_approval_level` row, but does not approve a change to the proposal's tool listing. | Permit the read-only calculation in `PRE_APPROVAL` only from `SUPPLIER_CHECKED` with policy/supplier prerequisites; keep PO dispatch restricted. Confirm the corresponding scope/list/allowlist amendment without adding purchasing write authority. | Exact approved wording and affected plan/proposal row; no-prerequisite-skipping test; recorded reviewer dispositions and plan-authority acceptance. |
| **OD-06 / GD-06** | Mohamed: real-policy deliverable and stub limits; Mohab: interface/deployment; Nour: application enforcement fit. | S2-01 uses a labelled `STUB_CONTRACT_TEST`; S2-04 delivers the agreed minimum real in-process policy functions/service; Sprint 3 handles persistence and seeded end-to-end integration. State precisely when the stub ceases to qualify, preserving the Week-4 gate. | Accepted S2-01/S2-04/S3-03 task text, tests, dependencies and capacity; named plan decision. Mohamed's prior AMEND is input, not approval. |
| **OD-08** | Ahmed: labels/evaluator assertions; Alaa: grouping, split freeze, dataset order; Mohamed: SC-03 real-policy fixture; Mohab: schema/provenance; Nour: recipes. Alaa accepted grouping only. | Add SC-01 HALLUCINATION and SC-02 TOOL_SELECTION_ERROR replay recipes, plus reusable SC-03 supplier POLICY_VIOLATION control, in Week 7 via explicit S4-06 scope/dependency amendment; integrate evidence/classifier/RCA as supported in Week 8. Preserve S2 vertical slice, S3-01 four-case gate, S3-03 supplier handoff and S5 benchmark scope. | Approved S4-06 scope, work-item dependency split, capacity, dates and S3-03 fixture identity; dataset/split impact review and named plan decision. See [scenario schedule](failure-planning-matrix.md#proposed-implementation-schedule--od-08). |
| **OD-16 / GD-17** | Mohamed: governance applicability (scoped ACCEPT reported); Nour: RAG app fit; Mohab: canonical `NOT_APPLICABLE`; Ahmed/Alaa: consumer mapping. | Confirm that Procurement pre-tool policies do not run for RAG and RAG displays `NOT_APPLICABLE`, distinct from `PASS` and `ERROR`. No purchasing tool or new RAG policy is added. | Exact scope clarification, representative RAG evidence/consumer mapping and named plan acceptance if it changes the approved plan. Governance acceptance alone does not ratify scope. |
| **GD-26 / OD-09** | Ahmed and Mohamed: prevented/realized/definitively no-effect/unknown labels and critical policy outcome precedence; Alaa: dataset and gate mapping. | Decide whether the proposed DEC-1/GD-26 extension changes the approved gate scope and task dependencies. Retain independent labels and never infer a realized effect from a policy `FAIL` alone; no numeric threshold is proposed. | First receive a versioned rule/mapping with paired cases and affected card(s); then record an explicit plan-authority disposition on the scope extension and dataset/gate timing. Until then, this item is **NOT READY FOR FINAL APPROVAL**. |
| **Malak UI schedule amendment** | Malak: committed UI branch/fixtures/test reconciliation; Mohab/Mohamed/Nour/Ahmed/Alaa: affected backend, governance, app, evaluation and dataset interfaces. | Review the attached proposal for 12 new Track F tasks (S3-08–10, S4-09–12, S5-08–11, S6-08) and 12 amended existing cards. The proposal changes task count 58→70, subtasks 295→355 and Malak's count 16→28, while claiming unchanged Week-4/12/16 gates and Sprint 1–2. Evaluate capacity, overlapping screens, backend dependencies, ideal-person-day estimates and whether unsized work should remain unsized. | Approved/revised task list, owners, dependency DAG, effort convention, capacity and gate impact; Malak's pushed branch/commit, exact 134→137 test explanation, fixture index/counting rule for 11 versus 13, and plan owner decision against an exact HTML revision. UI fixture verification is not schedule approval. See [Malak review](reviews/malak-479cab0-ui-response.md). |

## 3. Routing sequence and response register

1. **Nour:** maintain the exact original/current/proposed plan revisions and the six row-level proposals. His team-lead authority for internal plan decisions is recorded above.
2. **Technical owners:** return their scoped ACCEPT/AMEND/DECLINE responses and evidence for each row above. Mohab/Mohamed/ Ahmed/Alaa/Malak do not approve another owner's plan scope by answering only their specialist question.
3. **Nour as team lead:** record a separate row-level ACCEPT/AMEND/DECLINE on OD-02, OD-06, OD-08, OD-16, GD-26 and the UI task amendments when the required evidence is available; identify affected task IDs, dates, dependencies, capacity/effort convention, accepted/rejected portions and the authoritative revised plan file/hash. A partial response leaves other rows open.
4. **Nour as document owner:** update only accepted task references and decision status; record dissent/amendments, regenerate manifest and rerun affected offline checks. No new sprint task or release gate is in force merely because it is drafted here.

### Team-lead row-level decision prompt

For each row, Nour records ACCEPT, AMEND with exact replacement wording, or DECLINE; affected task IDs, dependencies, weeks, capacity and gate impact; the evidence reviewed; the resulting authoritative plan file/revision and date. GD-26 requires Ahmed/Mohamed/Alaa's versioned outcome mapping first. The UI amendment requires Malak's committed branch and reconciliation of 134 versus 137 tests and 11 plan fixtures versus 13 reported traces. A response to one row does not decide the others.

| Item | Specialist response | Nour's plan decision | Plan revision / evidence | Current disposition |
|---|---|---|---|---|
| OD-02 | Mohamed narrower row ACCEPT reported; Mohab/interface pending | Pending | None | OPEN — TECHNICAL REVIEW AND TEAM-LEAD DECISION |
| OD-06 | Mohamed AMEND reported; interface/capacity pending | Pending | None | OPEN — TECHNICAL REVIEW AND TEAM-LEAD DECISION |
| OD-08 | Alaa grouping principle ACCEPT; Ahmed/Mohamed/Mohab/capacity pending | Pending | None | OPEN — TECHNICAL REVIEW AND TEAM-LEAD DECISION |
| OD-16 | Mohamed governance-local ACCEPT reported; canonical/consumer fit pending | Pending | None | OPEN — TECHNICAL REVIEW AND TEAM-LEAD DECISION |
| GD-26 / OD-09 | Alaa position partial; Ahmed/Mohamed exact mapping pending | Pending | None | OPEN — TECHNICAL MAPPING THEN TEAM-LEAD DECISION |
| Malak UI amendment | Nine fixture distinctions owner-reported; branch and 137/134 reconciliation pending | Pending | Proposal only | OPEN — TECHNICAL REVIEW THEN TEAM-LEAD DECISION |

**Decision record shape:** `decision_owner=Nour El-Rouby`, `role=development team lead`, `authority_reference=user confirmation 2026-11-14`, `decision_id`, `ACCEPT|AMEND|DECLINE`, `exact_plan_file_sha256`, `affected_task_ids`, `accepted_wording_or_replacement`, `capacity_and_gate_impact`, `decision_date`, `evidence_link`. Leave absent decisions explicitly pending; no inferred consent from role ownership or specialist replies.

## 4. Team-lead decision draft — 2026-11-14

The [six-row decision draft](team-lead-plan-decision-draft.md) gives Nour concrete recommended dispositions and replacement plan wording: narrow OD-02; reconcile the S2-01/S2-04 real-policy gate for OD-06; add scoped Week-7/8 recipe work under OD-08; treat OD-16 as a no-new-task clarification; hold GD-26's gate extension until the joint outcome mapping; and hold Malak's 12-task schedule package until a committed, sized and reconciled revision exists. **These are recommendations, not Nour's recorded decisions.** The response register above remains pending, and the original HTML plan remains the baseline until Nour decides and records an exact revised plan.
