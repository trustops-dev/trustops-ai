# E01–E27 mapping — reviewed Draft v1.6

Review date: **2026-11-06**. Status: **mapping prepared; full schema acceptance pending**.

All 27 original requirements are retained: **9 OK, 9 CHANGE REQUIRED, 9 OPEN**. Status describes the scoped row, not the whole validator. Compared with v1.5, E04/E08/E12 move to OPEN, E11/E16/E22/E23/E24 to OK, and E09/E13 to CHANGE REQUIRED based on newly reproduced findings. The [historical mapping](schema-v1.5-evidence-mapping.json) is unchanged.

The [machine-readable mapping](schema-v1.6-evidence-mapping.json) contains exact source line ranges, event paths, owners, questions and case results. The [fresh observations](schema-v1.6-review-observations.json) record 2,106 baseline assertions, 27/27 supplied expectations and **19/35 independent expectations met** (15 false passes and one valid UNKNOWN rejected). Expected independent runner exit code is 1 while these defects remain.

Inputs are the hash-pinned external [joint-review packet](https://chatgpt.com/library?file_id=libfile_f4d5624725148191a8a7bac3df276434&account_id=personal). No canonical schema or runtime implementation was changed. Main was verified via read-only Git at `3ef7da1f190cd5a22efdcd6798af59199924bac3`; the web viewer was unavailable. This mapping assesses the supplied v1.6 draft, not an inferred pushed schema revision.

## Status summary

| ID | Requirement | v1.6 status | Current finding |
|---|---|---|---|
| E01 | User request, both | **OK** | See scoped assessment |
| E02 | Model call, both | **OPEN** | See scoped assessment |
| E03 | Procurement policy retrieval | **OPEN** | See scoped assessment |
| E04 | RAG retrieval | **OPEN** | See scoped assessment |
| E05 | Retrieved documents | **OK** | See scoped assessment |
| E06 | Retrieval scores/ranks | **OPEN** | See scoped assessment |
| E07 | Evidence selection | **OPEN** | See scoped assessment |
| E08 | Request normalization | **OPEN** | See scoped assessment |
| E09 | Agent state transition | **CHANGE REQUIRED** | R16-03 |
| E10 | Workflow stage | **OPEN** | R16-07 |
| E11 | Supplier check | **OK** | See scoped assessment |
| E12 | Approval calculation | **OPEN** | See scoped assessment |
| E13 | Approval submission | **CHANGE REQUIRED** | R16-01, R16-04 |
| E14 | Approval observation | **CHANGE REQUIRED** | R16-01, R16-06 |
| E15 | Tool proposal | **OK** | See scoped assessment |
| E16 | Tool arguments | **OK** | See scoped assessment |
| E17 | Pre-execution policy request | **CHANGE REQUIRED** | R16-01, R16-07, R16-08 |
| E18 | Pre-execution policy result | **CHANGE REQUIRED** | R16-01, R16-07 |
| E19 | Dispatch suppression | **OK** | See scoped assessment |
| E20 | Tool invocation/result | **CHANGE REQUIRED** | R16-02, R16-03 |
| E21 | Final response, Procurement | **CHANGE REQUIRED** | R16-03 |
| E22 | Grounded answer, RAG | **OK** | See scoped assessment |
| E23 | Citations | **OK** | See scoped assessment |
| E24 | Abstention | **OK** | See scoped assessment |
| E25 | Technical failure/cancel/pending | **CHANGE REQUIRED** | R16-02, R16-03, R16-04 |
| E26 | Run/version provenance | **OPEN** | See scoped assessment |
| E27 | Controlled scenario association | **CHANGE REQUIRED** | R16-05 |

## Evidence by requirement

### E01 — User request, both

**Status: OK** (v1.5: OK).

**Required evidence:** Raw request, normalized fields/query, revision, application identity, synthetic-data marker.

**v1.6 representation:** `application_id`, `application_type`; `request.{request_id,request_revision,user_query,structured_input,synthetic_data,session_metadata}`.

**Source:** `updated_schemas_v6.md`, lines 56–79; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `root` / `request.request_revision`
- `WT4` / `root` / `request.synthetic_data`

**Assessment:** Request identity, raw query, normalized input container, revision and synthetic marker are represented. Initial normalization correctness is separately E08.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Retain the envelope and trusted provenance; request/session content cannot establish authorization.

**Owners/reviewers:** Nour, Mohab. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E02 — Model call, both

**Status: OPEN** (v1.5: OPEN).

**Required evidence:** Prompt/template version, actual rendered input/context reference, selected provider, configured model identifier, returned model identifier/version when available, model/configuration version, generation parameters, model response/refusal/error, latency and token/usage metadata when available.

**v1.6 representation:** `model_call.a.{model_call_id,step_purpose,provider,model_id,prompt_template_id,selected_context_ref,rendered_prompt_or_messages,output_text,proposed_tool_calls,token_usage}`; event `timestamp`/`latency_ms`; `versions`, `metadata_availability`. §4.6 declares nullable `versions.returned_model_version`.

**Source:** `updated_schemas_v6.md`, lines 458–518; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e2` / `attributes.rendered_prompt_or_messages`
- `WT1` / `e29` / `attributes.selected_context_ref`

**Assessment:** Normal prompt/context/input/output fields are present. Complete provider refusal/error, per-call configuration overrides and returned-version missingness are not established by these fixtures.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Mohab/Alaa: identify the exact refusal/error and per-call effective-configuration paths and give one fixture for each, for Nour to compare with the provider ADR.

**Owners/reviewers:** Mohab, Alaa, Nour. **Decisions:** OD-LLM-01, OD-13. **Findings:** No unresolved reproduced row-specific finding.

### E03 — Procurement policy retrieval

**Status: OPEN** (v1.5: OPEN).

**Required evidence:** Raw/effective query, filters/k, policy set and retriever versions.

**v1.6 representation:** `search_policy` `tool_call.a.arguments.{query,request_id,top_k}` plus optional `policy_ids` (§4.2.1); `tool_result.a.linked_retrieval_id` and `result_payload.data.{query,requested_top_k,returned_count,matches,policy_set_version,retriever_version,applicability}`; `retrieval.a.{retrieval_id,query_text,source_snapshot_id}`.

**Source:** `updated_schemas_v6.md`, lines 160–299; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e5` / `attributes.arguments.query`
- `WT1` / `e7` / `attributes.linked_retrieval_id`
- `WT1` / `e7` / `attributes.result_payload.data.policy_set_version`

**Assessment:** Policy call/result/retrieval linkage and version fields are present. Raw versus effective query and a complete trusted filter/applicability snapshot still need an agreed mapping.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Mohab/Mohamed: identify the effective query and applied trusted filters or immutable resolution reference, including the no-filter case; Nour verifies policy retrieval fit.

**Owners/reviewers:** Mohab, Nour, Mohamed. **Decisions:** OD-05, OD-13. **Findings:** No unresolved reproduced row-specific finding.

### E04 — RAG retrieval

**Status: OPEN** (v1.5: CHANGE REQUIRED).

**Required evidence:** Query, effective query, k, filters, corpus/index/embedding/retriever configuration.

**v1.6 representation:** `retrieval.a.{retrieval_id,query_text,effective_query,retriever_type,source_snapshot_id,top_k_requested,retrieved_documents}`; `versions.{retriever_version,corpus_version,index_version,embedding_model_version,effective_config_ref,config_digest}`.

**Source:** `updated_schemas_v6.md`, lines 458–518; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e1` / `attributes.effective_query`
- `WT4` / `root` / `versions.index_version`

**Assessment:** POS-13 now represents a successful empty retrieval and abstention. Effective tenant/ACL/filter configuration and embedding dimensions still need agreed reference resolution.

**Validation evidence:** `POS-13` expected exit 0, observed 0.

**Action / exact question:** Mohab/Alaa/Nour: supply the filter, isolation and embedding-configuration paths or exact versioned resolution rule. Keep pgvector availability conditional.

**Owners/reviewers:** Mohab, Nour, Ahmed, Alaa. **Decisions:** OD-05, OD-10, OD-RAG-01, OD-13. **Findings:** No unresolved reproduced row-specific finding.

### E05 — Retrieved documents

**Status: OK** (v1.5: OK).

**Required evidence:** Full ordered returned list; document/source/chunk IDs, versions, text/snapshot, hashes and locators.

**v1.6 representation:** `retrieval.a.source_snapshot_id`; `retrieved_documents[].{doc_id,doc_version,chunk_id,source_locator,rank,content_snippet,content_hash,source_metadata,canonical_chunk_slice,canonical_chunk_char_span,formatting_prefix_applied,exact_selected_text}`.

**Source:** `updated_schemas_v6.md`, lines 404–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e1` / `attributes.retrieved_documents.0.content_hash`
- `WT4` / `e1` / `attributes.retrieved_documents.0.source_locator`
- `WT4` / `e1` / `attributes.retrieved_documents.0.canonical_chunk_char_span`

**Assessment:** Ordered source/chunk identity, version, text/hash, locator and source-to-prompt slices are concrete. Citation version/containment checks are now demonstrated separately in E23.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Preserve exact snapshots, source order and span conventions; storage retention remains E26.

**Owners/reviewers:** Mohab, Nour, Ahmed. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E06 — Retrieval scores/ranks

**Status: OPEN** (v1.5: OPEN).

**Required evidence:** Raw finite score, metric kind/direction, returned rank, tie rule, returned count.

**v1.6 representation:** `retrieval.a.score_semantics.{metric_type,score_direction,score_availability}` and `retrieved_documents[].{rank,score}`; `metadata_availability.retriever_scores`; policy-search result `data.returned_count`.

**Source:** `updated_schemas_v6.md`, lines 458–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e1` / `attributes.score_semantics.metric_type`
- `WT4` / `e1` / `attributes.retrieved_documents.0.rank`
- `WT1` / `e7` / `attributes.result_payload.data.returned_count`

**Assessment:** Metric kind/direction, availability and returned rank are represented. Tie-rule identity and the general RAG returned-count convention still need explicit assignment.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Ahmed/Alaa/Mohab: confirm finite/null score handling, tie-rule version and whether returned count is stored or derived from the complete ordered list.

**Owners/reviewers:** Ahmed, Alaa, Mohab, Nour. **Decisions:** OD-05, OD-13. **Findings:** No unresolved reproduced row-specific finding.

### E07 — Evidence selection

**Status: OPEN** (v1.5: OPEN).

**Required evidence:** Selected IDs/order/text spans, rejected IDs/reasons, sufficiency outcome, unresolved facets/conflicts, selection version.

**v1.6 representation:** `retrieved_documents[].{included_in_prompt,selection_or_exclusion_reason,prompt_context_order,canonical_chunk_char_span,exact_selected_text}`; `retrieval.a.evidence_sufficiency`; `model_call.a.selected_context_ref.{selected_chunk_ids,context_formatting_rule,rendered_context_block}`.

**Source:** `updated_schemas_v6.md`, lines 458–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e1` / `attributes.evidence_sufficiency.missing_or_unsupported_facets`
- `WT4` / `e2` / `attributes.selected_context_ref.selected_chunk_ids`

**Assessment:** Selected/excluded sources, exact context, missing facets and conflicts are represented. Selector-version resolution and qualitative sufficiency interpretation remain open. WT4 is an intentional bad answer.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Nour/Ahmed/Mohab/Alaa: agree the selector/configuration reference and facet/conflict rubric; return a positive grounded fixture. Scores and structural citation checks do not prove entailment.

**Owners/reviewers:** Nour, Ahmed, Mohab, Alaa. **Decisions:** OD-05, OD-11, OD-13. **Findings:** No unresolved reproduced row-specific finding.

### E08 — Request normalization

**Status: OPEN** (v1.5: CHANGE REQUIRED).

**Required evidence:** Raw-to-normalized field links, validation details, amount/currency/request revision.

**v1.6 representation:** `request.{user_query,request_revision,structured_input}`; `tool_proposal.a.{raw_arguments_serialized,arguments_parse_status,proposed_arguments}`; `argument_validation.a.{target_proposal_id,normalized_arguments,validation_errors,arguments_digest}`.

**Source:** `updated_schemas_v6.md`, lines 304–332; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `root` / `request.structured_input.total_amount`
- `WT1` / `e3` / `attributes.normalized_arguments`

**Assessment:** Root-amount disagreement and malformed raw arguments are now detected. The initial user-request-to-normalized-field audit trail and clarification linkage still lack an agreed exact representation.

**Validation evidence:** `old_request_amount` expected FINDING, observed FINDING; `old_raw_malformed` expected FINDING, observed FINDING.

**Action / exact question:** Mohab/Nour/Mohamed: identify the initial normalization and clarification references, with a changed/missing field example. Retain invalid proposals as evidence.

**Owners/reviewers:** Mohab, Nour, Mohamed. **Decisions:** OD-05. **Findings:** No unresolved reproduced row-specific finding.

### E09 — Agent state transition

**Status: CHANGE REQUIRED** (v1.5: OK).

**Required evidence:** Previous/new state, reason, input/result references, transition attempted vs accepted, state revision.

**v1.6 representation:** `agent_state.a.{state_revision_id,from_app_state,to_app_state,app_state,transition_attempted,transition_accepted,transition_reason,bound_authorization_check_id,bound_dispatch_claim_id}`; event `parent_event_id`; root `last_app_state`.

**Source:** `updated_schemas_v6.md`, lines 100–157; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e33` / `attributes.bound_authorization_check_id`
- `WT1` / `e33` / `attributes.state_revision_id`
- `WT1` / `e14` / `parent_event_id`

**Assessment:** State revisions and attempted/accepted transitions are represented, but unresolved_recovery_still_completed passes despite an unresolved purchasing outcome and a completed state.

**Validation evidence:** `unresolved_recovery_still_completed` expected FINDING, observed PASS.

**Action / exact question:** Mohab: reject unsupported completion after unresolved recovery, while accepting honest unresolved/cancelled states; Nour/Mohamed confirm affected transitions.

**Owners/reviewers:** Nour, Mohab, Mohamed, Malak. **Decisions:** OD-04, OD-05, OD-12. **Findings:** R16-03.

### E10 — Workflow stage

**Status: OPEN** (v1.5: OPEN).

**Required evidence:** Coarse stage at proposal/check/dispatch, state-to-stage mapping version.

**v1.6 representation:** `agent_state.a.policy_stage`; `tool_proposal.a.policy_stage_at_proposal`; `policy_check.a.authorization_snapshot.checked_policy_stage`; `tool_call.a.policy_stage_at_dispatch`; `policy_bundle_version`.

**Source:** `updated_schemas_v6.md`, lines 100–157; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e30` / `attributes.policy_stage_at_proposal`
- `WT1` / `e32` / `attributes.authorization_snapshot.checked_policy_stage`
- `WT1` / `e34` / `attributes.policy_stage_at_dispatch`

**Assessment:** Proposal/check/dispatch stages exist. Calculation permission, coarse-stage aliases and the authoritative state-to-stage mapping version still need joint agreement.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Mohamed/Mohab/Nour: ratify permission and lossless state/stage translation with its version reference (R16-07); do not infer it from policy_bundle_version alone.

**Owners/reviewers:** Mohamed, Mohab, Nour. **Decisions:** OD-02, OD-05. **Findings:** R16-07.

### E11 — Supplier check

**Status: OK** (v1.5: CHANGE REQUIRED).

**Required evidence:** Requested/returned ID, status, source/directory/record version, lookup outcome.

**v1.6 representation:** `get_supplier` `tool_call.a.arguments.supplier_id`; `tool_result.a.result_payload.data.{requested_supplier_id,supplier,directory_version}`; `supplier.{supplier_id,status,raw_status,record_version,source_ref,observed_at}`; snapshot `supplier_evidence_ref`.

**Source:** `updated_schemas_v6.md`, lines 432–448; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e13` / `attributes.result_payload.data.supplier.status`
- `WT1` / `e32` / `attributes.authorization_snapshot.supplier_evidence_ref`

**Assessment:** Requested/returned supplier identity, status and source/version references are represented. The old source-versus-snapshot supplier contradiction is now detected.

**Validation evidence:** `old_supplier_contradiction` expected FINDING, observed FINDING; `NEG-10` expected exit 1, observed 1.

**Action / exact question:** Retain source-backed comparison and negative regression. This row does not certify live directory authenticity or all possible supplier transitions.

**Owners/reviewers:** Mohab, Mohamed, Nour. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E12 — Approval calculation

**Status: OPEN** (v1.5: CHANGE REQUIRED).

**Required evidence:** Amount/currency, configured rule basis, threshold/comparator/version, requirement/level or unresolved reason.

**v1.6 representation:** `calculate_approval_level` result `data.{calculation_ref,request_revision,approval_required,approval_level,policy_id,policy_version,basis}`; `basis.{amount,amount_currency,threshold,threshold_currency,comparator,rule_ref}`; snapshot `calculation_evidence_ref`.

**Source:** `updated_schemas_v6.md`, lines 160–299; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e19` / `attributes.result_payload.data.basis`
- `WT1` / `e20` / `attributes.approval_required`

**Assessment:** Calculation basis, required level and CALCULATED/UNRESOLVED outcomes are represented. Root amount disagreement is now detected. OD-03 candidate values and OD-02 calculation permission remain unaccepted.

**Validation evidence:** `old_request_amount` expected FINDING, observed FINDING; `POS-12` expected exit 0, observed 0.

**Action / exact question:** Mohamed: ACCEPT/AMEND the OD-03 candidate and below/equal/above-T behavior, plus calculation permission; Mohab confirms mapped evidence. Existing examples remain symbolic.

**Owners/reviewers:** Mohab, Mohamed, Nour. **Decisions:** OD-02, OD-03, OD-05. **Findings:** No unresolved reproduced row-specific finding.

### E13 — Approval submission

**Status: CHANGE REQUIRED** (v1.5: OPEN).

**Required evidence:** Request and approval-request IDs, calculation ref, required level, idempotency identity.

**v1.6 representation:** `request_approval` call `a.trusted_runtime_context.domain_context.operation_mode`, domain request/calculation/level/idempotency bindings; result `data.{approval_request_id,request_revision,calculation_ref,decision_status,approval_evidence,decision_ref,reason}`.

**Source:** `updated_schemas_v6.md`, lines 160–299; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e25` / `attributes.result_payload.data.approval_request_id`
- `WT1` / `e25` / `attributes.result_payload.data.calculation_ref`

**Assessment:** Submission/observation modes and IDs exist, but approval_submission_request_disagrees passes; approval_submission_retry_unaccounted accepts an unaccounted submission write as a transient read retry.

**Validation evidence:** `approval_submission_request_disagrees` expected FINDING, observed PASS; `approval_submission_retry_unaccounted` expected FINDING, observed PASS.

**Action / exact question:** Mohab: bind submission to the exact request/calculation and enforce write retry accounting. Mohamed confirms replay/continuation rules. Keep OD-APP-OBS-01 semantics closed.

**Owners/reviewers:** Mohamed, Mohab, Nour. **Decisions:** OD-04, OD-05, OD-12. **Findings:** R16-01, R16-04.

### E14 — Approval observation

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** Required/received flags, status, approval ID, actor/time/source, request/supplier/amount/currency/level/version binding.

**v1.6 representation:** `approval.a.{approval_id,approval_request_id,request_id,bound_calculation_ref,bound_request_revision,bound_supplier_id,bound_amount,bound_currency,approval_level,policy_version,approval_status,approver_id,approver_role,approval_timestamp,trusted_source}`; request_approval result `decision_ref` and snapshot `approval_evidence_ref`.

**Source:** `updated_schemas_v6.md`, lines 100–157; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e27` / `attributes.approval_status`
- `WT1` / `e27` / `attributes.bound_request_revision`
- `WT1` / `e32` / `attributes.authorization_snapshot.approval_evidence_ref`

**Assessment:** Denied-source contradictions are detected, but nonexistent approval references, inadequate ceiling, mismatched level/record/policy and future approval timestamps still pass. Approval unknown fields also pass.

**Validation evidence:** `old_approval_denied` expected FINDING, observed FINDING; `approval_event_reference_nonexistent` expected FINDING, observed PASS; `approval_ceiling_below_request` expected FINDING, observed PASS; `approval_source_level_disagrees` expected FINDING, observed PASS; `approval_source_record_disagrees` expected FINDING, observed PASS; `approval_policy_version_disagrees` expected FINDING, observed PASS; `approval_future_timestamp` expected FINDING, observed PASS; `approval_unknown_field` expected FINDING, observed PASS.

**Action / exact question:** Mohab: resolve and compare the exact trusted approval source and enforce declared field/time rules. Mohamed/Mohab review Nour’s OD-04 response before joint acceptance.

**Owners/reviewers:** Mohab, Mohamed, Nour. **Decisions:** OD-04, OD-05. **Findings:** R16-01, R16-06.

### E15 — Tool proposal

**Status: OK** (v1.5: OK).

**Required evidence:** Exact proposed tool, tool catalog/schema version, model call ref, proposal identity.

**v1.6 representation:** `tool_proposal.a.{proposal_id,raw_proposed_tool_name,known_tool_name,app_state_at_proposal,policy_stage_at_proposal,is_risky_action}`; `parent_event_id` to generating model event when applicable; `versions.tool_schema_version` and linked `argument_validation.a.tool_schema_version`.

**Source:** `updated_schemas_v6.md`, lines 304–332; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e30` / `attributes.proposal_id`
- `WT1` / `e30` / `parent_event_id`
- `WT1` / `e31` / `attributes.tool_schema_version`

**Assessment:** Tool proposal identity, exact raw/known tool name, model parent reference and catalog/schema version are represented separately from execution.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Retain proposal-to-model and validation version links; a proposal is not an authorized or completed action.

**Owners/reviewers:** Nour, Mohab, Ahmed. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E16 — Tool arguments

**Status: OK** (v1.5: CHANGE REQUIRED).

**Required evidence:** Raw serialized arguments, parsed values, trusted runtime context separately, validation outcome/field errors.

**v1.6 representation:** `tool_proposal.a.{raw_arguments_serialized,arguments_parse_status,proposed_arguments,trusted_runtime_context}`; `argument_validation.a.{validation_id,target_proposal_id,validation_status,normalized_arguments,arguments_digest,validation_errors}`.

**Source:** `updated_schemas_v6.md`, lines 304–332; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e2` / `attributes.raw_arguments_serialized`
- `WT1` / `e3` / `attributes.validation_errors`

**Assessment:** Raw serialized, parsed and normalized arguments, validation findings and trusted runtime context are separate. Malformed raw JSON is now detected by an independent single-purpose probe.

**Validation evidence:** `old_raw_malformed` expected FINDING, observed FINDING.

**Action / exact question:** Keep raw invalid arguments and errors; preserve trusted/model separation. Initial request normalization remains E08.

**Owners/reviewers:** Mohab, Nour, Ahmed. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E17 — Pre-execution policy request

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** Proposal/tool, argument digest, request/state revision, stage, supplier/approval/calculation evidence refs, policy version.

**v1.6 representation:** `policy_check.a.{check_id,target_proposal_id,authorization_snapshot}`; snapshot request/proposal/validation/digest/state/policy/evidence fields and `dispatch_claim`; `tool_call.a.{checked_source_state_revision,dispatch_state_revision,dispatch_claim_id,runtime_binding_verification}`.

**Source:** `updated_schemas_v6.md`, lines 350–373; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e32` / `attributes.authorization_snapshot`
- `WT1` / `e34` / `attributes.dispatch_claim_id`

**Assessment:** Authorization snapshot and checked/dispatch revisions exist; supplier, amount, duplicate policy and claim discrepancies are better checked. Approval source binding still permits false verification.

**Validation evidence:** `old_supplier_contradiction` expected FINDING, observed FINDING; `old_request_amount` expected FINDING, observed FINDING; `old_claim_mismatch` expected FINDING, observed FINDING; `approval_event_reference_nonexistent` expected FINDING, observed PASS; `approval_ceiling_below_request` expected FINDING, observed PASS.

**Action / exact question:** Mohab: fix R16-01 source resolution and approval comparisons. Mohamed/Mohab agree the R16-07 interface and R16-08 claim allocation/consumption lifecycle before acceptance.

**Owners/reviewers:** Mohab, Mohamed, Nour. **Decisions:** OD-04, OD-05, OD-12. **Findings:** R16-01, R16-07, R16-08.

### E18 — Pre-execution policy result

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** ALLOW/BLOCK, per-policy findings/reasons/version, referenced inputs; explicit timeout/error/missing result.

**v1.6 representation:** `policy_check.a.{check_id,check_mode,policy_bundle_version,evaluated_policies,action_verdict,verdict_basis}`; each policy includes `policy_id`, `policy_version`, `policy_result`, `binding_verification`, `observed_evidence`, `failure_or_error_reason`.

**Source:** `updated_schemas_v6.md`, lines 432–457; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e32` / `attributes.evaluated_policies.0.policy_result`
- `WT2` / `e6` / `attributes.action_verdict`

**Assessment:** Per-policy verdicts/reasons and unique IDs are represented and duplicate IDs now fail. Approval contradictions can still support a false verified policy result; governance mapping remains pending.

**Validation evidence:** `old_duplicate_policy_ids` expected FINDING, observed FINDING; `approval_source_level_disagrees` expected FINDING, observed PASS; `approval_policy_version_disagrees` expected FINDING, observed PASS.

**Action / exact question:** Mohab: derive approval verification from resolved source data and retain failed consistency evidence. Mohamed agrees canonical names/translations, reasons and certification semantics (R16-07).

**Owners/reviewers:** Mohab, Mohamed, Nour, Ahmed. **Decisions:** OD-05, OD-16. **Findings:** R16-01, R16-07.

### E19 — Dispatch suppression

**Status: OK** (v1.5: OK).

**Required evidence:** NOT_EXECUTED, execution_started=false, blocking/check-error reference, reason.

**v1.6 representation:** `tool_suppression.a.{suppression_id,target_proposal_id,validation_id,suppression_source,blocking_check_id,blocking_policy_ids,suppression_reason,execution_started,tool_dispatched,side_effect_state}`.

**Source:** `updated_schemas_v6.md`, lines 333–349; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT2` / `e7` / `attributes.execution_started`
- `WT2` / `e7` / `attributes.blocking_check_id`
- `WT2` / `e7` / `attributes.tool_dispatched`

**Assessment:** Suppression carries proposal/validation/check linkage, reason and false execution_started/tool_dispatched flags, with no execution effect.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Keep suppression distinct from a dispatched call with UNKNOWN effect; do not reuse this no-dispatch representation for transport failure.

**Owners/reviewers:** Nour, Mohab, Mohamed, Malak. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E20 — Tool invocation/result

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** Invocation identity, proposal/check refs, start/end, mock marker, idempotency key, outcome/result/error, PO ID only if confirmed.

**v1.6 representation:** `tool_call.a.{call_id,proposal_id,validation_id,authorization_check_id,arguments,arguments_digest,trusted_runtime_context,dispatch_claim_id}`; `tool_result.a.{result_id,call_id,execution_status,side_effect_state,result_payload,transport_diagnostics}`; event timing; PO data `mock`, `idempotency_key`, `result_ref`.

**Source:** `updated_schemas_v6.md`, lines 350–429; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e35` / `attributes.result_payload.data.result_ref`
- `WT3` / `e7` / `attributes.side_effect_state`

**Assessment:** One-terminal-result and timeout/recovery identity checks improved, but timeout_error_claims_no_effect still passes, valid non-timeout UNKNOWN is rejected, and UNKNOWN results can carry wrong proposal/claim links.

**Validation evidence:** `NEG-17` expected exit 1, observed 1; `old_timeout_none` expected FINDING, observed FINDING; `timeout_error_claims_no_effect` expected FINDING, observed PASS; `unknown_after_runtime_exception` expected PASS, observed FINDING; `unknown_result_wrong_claim` expected FINDING, observed PASS; `unknown_result_wrong_proposal` expected FINDING, observed PASS.

**Action / exact question:** Mohab: validate uncertainty across execution-status branches; accept legitimate non-timeout UNKNOWN and bind every result to its exact call/proposal/claim. Reconciliation remains a separate observation.

**Owners/reviewers:** Mohab, Nour, Mohamed, Ahmed. **Decisions:** OD-05, OD-12. **Findings:** R16-02, R16-03.

### E21 — Final response, Procurement

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** Exact raw generated text and delivered text, which was shown, final app outcome/state, supporting successful action references or reason for no action.

**v1.6 representation:** `final_response.a.{generating_model_call_id,raw_model_candidate_text,delivered_response_text,response_text,runtime_modification_status,runtime_correction_or_suppression_reason,response_mode,claimed_actions}`; action `supporting_call_id`, `supporting_result_id`, `supporting_recovery_id`.

**Source:** `updated_schemas_v6.md`, lines 458–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT1` / `e38` / `attributes.claimed_actions.0.supporting_result_id`
- `WT2` / `e8` / `attributes.raw_model_candidate_text`
- `WT2` / `e8` / `attributes.delivered_response_text`

**Assessment:** Raw/delivered output and supporting action references exist. An unresolved recovery can still coexist with COMPLETED; loose UNKNOWN result linkage prevents reliable supporting-action certification.

**Validation evidence:** `unresolved_recovery_still_completed` expected FINDING, observed PASS; `unknown_result_wrong_claim` expected FINDING, observed PASS; `unknown_result_wrong_proposal` expected FINDING, observed PASS.

**Action / exact question:** Mohab/Ahmed: bind delivered success claims and terminal completion to resolved matching action evidence, with a negative unresolved-completion fixture. Preserve unsupported model text for evaluation.

**Owners/reviewers:** Mohab, Ahmed, Nour, Malak. **Decisions:** OD-05, OD-09. **Findings:** R16-03.

### E22 — Grounded answer, RAG

**Status: OK** (v1.5: CHANGE REQUIRED).

**Required evidence:** Candidate and final text, exact generation context, claim IDs/text/answer spans.

**v1.6 representation:** `model_call.a.{model_call_id,selected_context_ref,rendered_prompt_or_messages,output_text}`; `final_response.a.{generating_model_call_id,raw_model_candidate_text,delivered_response_text,claim_to_source_spans}`; claim `claim_id`, `claim_text`, `response_char_span`.

**Source:** `updated_schemas_v6.md`, lines 458–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e3` / `attributes.generating_model_call_id`
- `WT4` / `e3` / `attributes.claim_to_source_spans.0.response_char_span`

**Assessment:** Generation context, model-call linkage, raw/delivered answer and claim spans are represented. NEG-21 now rejects quotation outside the selected passage. This is structural capture, not a general grounding verdict.

**Validation evidence:** `NEG-21` expected exit 1, observed 1.

**Action / exact question:** Retain exact generating context; Nour/Ahmed still need a positive grounded canonical fixture and semantic-support review. WT4 intentionally contains unsupported content.

**Owners/reviewers:** Mohab, Nour, Ahmed. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E23 — Citations

**Status: OK** (v1.5: CHANGE REQUIRED).

**Required evidence:** Claim→retrieved source/chunk/version/span→visible marker; validation findings; selected-context membership.

**v1.6 representation:** `final_response.a.visible_citations[].{citation_id,visible_citation_label,cited_doc_id,cited_doc_version,cited_chunk_id,present_in_selected_context}`; `claim_to_source_spans[].{linked_citation_ids,source_evidence_spans}`; source `retrieval_id`, `doc_id`, `chunk_id`, `source_text_basis`, `source_char_span`, `source_quote`, `in_supplied_prompt_context`.

**Source:** `updated_schemas_v6.md`, lines 458–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e3` / `attributes.visible_citations.0.cited_doc_version`
- `WT4` / `e3` / `attributes.claim_to_source_spans.0.source_evidence_spans.0.source_char_span`

**Assessment:** Visible citations and claim/source/version/span links are represented. Wrong document version and passage outside the selected slice are now detected. Structural membership does not prove entailment.

**Validation evidence:** `old_citation_version` expected FINDING, observed FINDING; `NEG-20` expected exit 1, observed 1; `NEG-21` expected exit 1, observed 1.

**Action / exact question:** Keep version and containment regressions, exact span conventions and independent semantic-support evaluation.

**Owners/reviewers:** Mohab, Nour, Ahmed. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E24 — Abstention

**Status: OK** (v1.5: CHANGE REQUIRED).

**Required evidence:** Reason, missing facets/conflicts, available/selected evidence, last stage, delivery text.

**v1.6 representation:** `retrieval.a.evidence_sufficiency.{sufficiency_status,missing_or_unsupported_facets,unresolved_conflicts}`; `final_response.a.{response_mode,is_abstention,abstention_details,delivered_response_text}`; §4.5 declares `abstention_details.abstention_reason_code`; root `last_rag_stage`, `execution_status`.

**Source:** `updated_schemas_v6.md`, lines 458–500; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `e1` / `attributes.evidence_sufficiency.sufficiency_status`
- `WT4` / `e3` / `attributes.abstention_details`
- `WT4` / `root` / `last_rag_stage`
- `POS-13` / `e3` / `attributes.abstention_details.abstention_reason_code`
- `POS-13` / `e3` / `attributes.delivered_response_text`
- `POS-13` / `root` / `last_rag_stage`

**Assessment:** POS-13 now supplies a complete zero-hit retrieval and delivered abstention with NO_RELEVANT_EVIDENCE, retrieval reference and final RAG stage. WT4 remains a non-abstention failure example.

**Validation evidence:** `POS-13` expected exit 0, observed 0.

**Action / exact question:** Retain the full zero-hit positive fixture. Conflict/insufficiency quality and runtime abstention behavior still require later evaluation; do not infer them from this structural case.

**Owners/reviewers:** Mohab, Nour, Ahmed. **Decisions:** No additional row-specific decision; shared gates remain. **Findings:** No unresolved reproduced row-specific finding.

### E25 — Technical failure/cancel/pending

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** Stage, known/unknown outcome, error category, retry/replay/continuation references.

**v1.6 representation:** Root `execution_status`, `last_app_state`, `last_rag_stage`, `is_partial_walkthrough`, `fixture_provenance`, `execution_budget_telemetry`; `tool_result.a.transport_diagnostics`; `recovery_check.a.{recovery_of_call_id,recovery_of_result_id,queried_idempotency_key,queried_business_payload_sha256,reconciliation_status,resolved_side_effect_state,unresolved_reason_code,recovered_result_envelope}`; documented §4.7 retry metadata.

**Source:** `updated_schemas_v6.md`, lines 374–429; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT3` / `e8` / `attributes.queried_idempotency_key`
- `WT3` / `e8` / `attributes.unresolved_reason_code`
- `WT2` / `root` / `fixture_provenance`

**Assessment:** Recovery identity, counter arithmetic and optional retry checks improved. ERROR/no-effect bypass, valid UNKNOWN rejection, unsupported completion and unaccounted submission retries remain.

**Validation evidence:** `old_recovery_key` expected FINDING, observed FINDING; `old_recovery_digest` expected FINDING, observed FINDING; `old_negative_counter` expected FINDING, observed FINDING; `old_missing_counters` expected FINDING, observed FINDING; `old_fencing` expected FINDING, observed FINDING; `old_optional_retry` expected PASS, observed PASS; `timeout_error_claims_no_effect` expected FINDING, observed PASS; `unknown_after_runtime_exception` expected PASS, observed FINDING; `unresolved_recovery_still_completed` expected FINDING, observed PASS; `approval_submission_retry_unaccounted` expected FINDING, observed PASS.

**Action / exact question:** Mohab: correct R16-02/03/04 with separate positive/negative fixtures. Mohamed/Nour confirm validity/continuation under OD-04 and replay/budget rules under OD-12.

**Owners/reviewers:** Mohab, Mohamed, Nour, Ahmed, Alaa. **Decisions:** OD-04, OD-05, OD-12. **Findings:** R16-02, R16-03, R16-04.

### E26 — Run/version provenance

**Status: OPEN** (v1.5: OPEN).

**Required evidence:** Provider, exact configured model identifier and available version, application, prompt, model/config, retriever, corpus/index, tools, policy, scenario/config references.

**v1.6 representation:** `versions.{provider,configured_model_id,application_version,prompt_version,retriever_version,corpus_version,index_version,embedding_model_version,policy_kb_version,policy_bundle_version,tool_schema_version,sdk_version,effective_config_ref,config_digest}`; §4.6 declares `returned_model_version`, `chunker_version`; root `ingestion_mode`, `metadata_availability`, `fixture_provenance`/`replay_provenance`.

**Source:** `updated_schemas_v6.md`, lines 501–518; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `root` / `versions.effective_config_ref`
- `WT4` / `root` / `versions.config_digest`
- `WT3` / `root` / `metadata_availability.token_usage.status`

**Assessment:** Version/configuration and missingness containers exist. Immutable resolution, code/source lineage, provider-returned values, retention and redaction conventions remain unaccepted.

**Validation evidence:** `WT1–WT4 field paths` baseline/path check.

**Action / exact question:** Alaa/Mohab: give exact immutable config/code references and availability/redaction rules with fixtures; Nour verifies provider/RAG fit. Illustrative identifiers do not establish deployment.

**Owners/reviewers:** Alaa, Mohab, Nour. **Decisions:** OD-13, OD-LLM-01, OD-LLM-02. **Findings:** No unresolved reproduced row-specific finding.

### E27 — Controlled scenario association

**Status: CHANGE REQUIRED** (v1.5: CHANGE REQUIRED).

**Required evidence:** Opaque scenario/version/run reference; independent label/cause/recipe records kept outside runtime inference input.

**v1.6 representation:** Root `scenario_metadata` and scenario/recipe/ground-truth references; §4.6.4 excludes labels/qrels/recipes, poisoned-document flags, fixture expectations, label-bearing IDs and post-run analysis from inference projections.

**Source:** `updated_schemas_v6.md`, lines 501–518; SHA-256 `84b749967df6cab5dd8f71d15768647ca10625554eb3f09ed76d6a77dd1a6997`.

**Verified representative paths:**

- `WT4` / `root` / `scenario_metadata.expected_relevant_doc_ids`
- `WT4` / `e1` / `attributes.retrieved_documents.0.source_metadata.is_poisoned_test_doc`

**Assessment:** Legitimate retrieved-document/qrel overlap now passes. injected_root_cause_in_runtime still passes, so actual evaluator-only cause leakage is not fully excluded.

**Validation evidence:** `old_legitimate_qrel_overlap` expected PASS, observed PASS; `injected_root_cause_in_runtime` expected FINDING, observed PASS.

**Action / exact question:** Mohab/Alaa/Ahmed: enforce provenance/projection exclusions for injected cause and other sidecar-only fields, while allowing legitimate document IDs in retrieval. Test both independently.

**Owners/reviewers:** Mohab, Alaa, Ahmed, Nour. **Decisions:** OD-05, OD-13. **Findings:** R16-05.

## Shared gates

- OD-05 remains blocking.
- OD-APP-OBS-01 observation semantics remain confirmed; adapter verification, approval validity and continuation remain pending.
- OD-03 candidate and OD-04 authored response are prepared but unaccepted.
- R16-01–09 disposition remains CHANGES_REQUIRED; full schema acceptance is not a row-count calculation.
- WT4 intentionally demonstrates a bad answer; structural citation checks do not prove entailment.
- Paths identify representation; source freshness/authenticity and concurrency safety require runtime evidence.

- **R16-06:** Unknown approval keys and invalid event timestamps pass; field-path presence is not exhaustive shape/time validation.
- **R16-07:** Governance/schema interface translation and certification meanings require joint agreement.
- **R16-08:** Dispatch-claim allocation versus post-ALLOW consumption and root-wide uniqueness need joint agreement and implementation evidence.
- **R16-09:** Stale revision/default names and report/package reproducibility need correction; source hashes take precedence over stale labels.

## Reproduction

See [validation instructions](validation/README.md#v16-evidence-mapping-reproduction). The checker verifies unchanged requirement identities, counts, source hashes and representative paths. It does not decide semantic correctness or stakeholder acceptance.
