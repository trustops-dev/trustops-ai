# Plan amendment routing — authority and six decision groups

**Prepared 2026-11-09 by Nour. Status: READY FOR AUTHORITY IDENTIFICATION AND SCOPED REVIEW; NO PLAN APPROVAL RECORDED.** This packet routes the plan-impacting portions of OD-02, OD-06, OD-08, OD-16, GD-26/OD-09 and Malak's proposed UI schedule. Specialist dispositions remain separate from plan authority; the attached HTML proposal is not an approved plan.

## 1. Authority finding

| Source inspected | What it establishes | What it does not establish |
|---|---|---|
| TrustOps proposal v1.1, exact file SHA-256 `8477f21210c1ba142c7a85a59ccc1fb38eb7d991da1b012f8443812538c3f36c` | Six named subsystem owners and their workstream RACI; cover says “Prepared for: Prof. Dr. Noha Yehia.” | No RACI row or approval delegation for amendments to the 16-week sprint plan. “Prepared for” does not confer schedule-change authority. |
| Original sprint plan HTML, SHA-256 `6bbfc2eeeeedb473ad7052c0973feda04ea7cab1b5892456057320a5bf154bd1` | Sprint tasks, owners, dependencies and gates. | No named final plan approver or change-control signature. |
| UI plan snapshots dated 2026-11-07, SHA-256 `cca78edca35d450b743412a0985936a70478307ebe9426fdfc7b73ae216fbefb` and `5af1d891132436a39b566337fb753aaff0c97975c5f8c50544ba38536b4586dc` | Proposed Sprint 3–6 UI amendments and owner claims. | No signed approval. The plans describe uncommitted work and 134 passing tests, while Malak's later report says 137. |
| Current owner decisions/governance draft | Explicitly require a “plan owner” for OD-02/06/08/16 and the GD-26 extension. | No personal name or delegated authority. |

**Finding:** A final plan approver cannot be identified from the reviewed records. Nour must obtain the **person's name, role, and authority for changing scope, milestone dates, task IDs/dependencies and capacity** from the team/project coordinator or academic supervisor. Prof. Dr. Noha Yehia is a possible authority contact because the proposal was prepared for her, but her plan-approval authority is **unconfirmed**. Do not attribute approval to Nour, Mohamed, Mohab, Malak, or the professor by inference. Record the confirmation reference and date here before routing the final approval request.

| Authority field | Current value |
|---|---|
| Named plan approver | **UNCONFIRMED** |
| Authority source / delegation | **NOT SUPPLIED** |
| Confirmation date / reference | **NOT SUPPLIED** |
| Approval channel and required evidence | **TO BE CONFIRMED**; use a named, dated response tied to exact plan revision and affected decision IDs |

### Ready-to-forward authority request

> Please identify the person or body formally authorized to approve TrustOps AI 16-week sprint-plan amendments, including scope, task IDs/dependencies, capacity and milestone changes. The proposal is addressed to Prof. Dr. Noha Yehia, but it does not state that she approves these plan changes. Please provide the approver's name, role, authority/delegation reference and preferred decision channel. We have six pending decision groups (OD-02/06/08/16, GD-26 and the proposed UI schedule); no approval is being assumed from specialist replies or the proposal.

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

1. **Nour:** request and record the authorized plan approver's name, role, delegation/scope and response channel. Send this packet and the exact original/current/proposed plan revisions to that person once confirmed.
2. **Technical owners:** return their scoped ACCEPT/AMEND/DECLINE responses and evidence for each row above. Mohab/Mohamed/ Ahmed/Alaa/Malak do not approve another owner's plan scope by answering only their specialist question.
3. **Plan approver:** give a separate row-level decision on OD-02, OD-06, OD-08, OD-16, GD-26 and the UI task amendments; identify affected task IDs, dates, dependencies, capacity/effort convention, accepted/rejected portions, and the authoritative revised plan file/hash. A partial response leaves other rows open.
4. **Nour:** update only accepted task references and decision status; record dissent/amendments, regenerate manifest and rerun affected offline checks. No new sprint task or release gate is in force merely because it is drafted here.

### Ready-to-forward plan decision request, once authority is confirmed

> Please review the six rows in this packet against the identified original sprint plan and the two proposed UI plan attachments. For each row, reply ACCEPT, AMEND with exact replacement wording, or DECLINE; name the affected task IDs, dependencies, weeks, capacity and gate impact. GD-26 requires Ahmed/Mohamed/Alaa's versioned outcome mapping before final approval. The UI amendment requires Malak's committed branch and reconciliation of 134 versus 137 tests and 11 plan fixtures versus 13 reported traces. Please identify the resulting authoritative plan file/revision and date. A response to one row does not decide the others.

| Item | Specialist response | Named plan decision | Plan revision / evidence | Current disposition |
|---|---|---|---|---|
| OD-02 | Mohamed narrower row ACCEPT reported; Mohab/interface pending | None | None | OPEN — PLAN AUTHORITY |
| OD-06 | Mohamed AMEND reported; interface/capacity pending | None | None | OPEN — PLAN AUTHORITY |
| OD-08 | Alaa grouping principle ACCEPT; Ahmed/Mohamed/Mohab/capacity pending | None | None | OPEN — PLAN AUTHORITY |
| OD-16 | Mohamed governance-local ACCEPT reported; canonical/consumer fit pending | None | None | OPEN — PLAN AUTHORITY |
| GD-26 / OD-09 | Alaa position partial; Ahmed/Mohamed exact mapping pending | None | None | OPEN — TECHNICAL MAPPING THEN PLAN |
| Malak UI amendment | Nine fixture distinctions owner-reported; branch and 137/134 reconciliation pending | None | Proposal only | OPEN — TECHNICAL REVIEW THEN PLAN |

**Approval record shape:** `approver_name`, `role`, `authority_reference`, `decision_id`, `ACCEPT|AMEND|DECLINE`, `exact_plan_file_sha256`, `affected_task_ids`, `accepted_wording_or_replacement`, `capacity_and_gate_impact`, `decision_date`, `evidence_link`. Leave absent values explicitly pending; no self-attestation or inferred consent.
