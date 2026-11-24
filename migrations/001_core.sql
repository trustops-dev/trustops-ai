-- =============================================================================
-- TrustOps AI — Week 2 Core Relational & JSONB Database Migration (001_core.sql — v1.2.0 Draft Interface)
-- STATUS: DRAFT WEEK 2 INTERFACE SPECIFICATION & TRANSACTIONAL LOCK PROTOTYPE
-- (Not yet claimed as deployed to live production PostgreSQL runtime; paired with
-- runnable SqliteTransactionalClaimGate integration test in trustops_sdk.py).
-- Author: Eng. Mohab Mohsen (Platform, Backend, Database & Trace Schema Owner)
-- Target Engine: PostgreSQL 16+ (JSONB + relational integrity constraints)
-- Note on OD-10 (pgvector): Core trace/evaluation tables do NOT require pgvector.
-- Vector extension & rag_chunks index DDL are kept conditional on environment
-- verification per OD-10 and rag-contract.md rev 0.9.
-- =============================================================================

BEGIN;

-- 1. Registered Applications
CREATE TABLE IF NOT EXISTS applications (
    application_id       VARCHAR(128) PRIMARY KEY,
    application_type    VARCHAR(16)  NOT NULL CHECK (application_type IN ('agent', 'rag')),
    display_name        VARCHAR(255) NOT NULL,
    owner_team          VARCHAR(128) NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 2. Immutable Version Registry (Prompt, Model, Retriever, Corpus, Policy KB, Bundle, Gate Config)
CREATE TABLE IF NOT EXISTS version_registry (
    version_entry_id             VARCHAR(128) PRIMARY KEY,
    application_id              VARCHAR(128) NOT NULL REFERENCES applications(application_id),
    artifact_kind               VARCHAR(64)  NOT NULL CHECK (artifact_kind IN (
        'agent_version', 'prompt_template_version', 'configured_model_id',
        'effective_config_ref', 'retriever_version', 'corpus_version',
        'index_version', 'chunker_version', 'selector_version',
        'policy_kb_version', 'policy_bundle_version', 'tool_contract_version',
        'decision_config_version'
    )),
    version_tag                 VARCHAR(128) NOT NULL,
    pairing_or_membership_ref   VARCHAR(255) NULL,
    config_payload_json         JSONB        NOT NULL DEFAULT '{}'::jsonb,
    registered_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (application_id, artifact_kind, version_tag)
);

-- 3. Traces Table (Separates Inference-Safe Runtime Columns from Test-Only Ground-Truth Metadata)
CREATE TABLE IF NOT EXISTS traces (
    trace_id                        VARCHAR(128) PRIMARY KEY,
    schema_version                  VARCHAR(32)  NOT NULL CHECK (schema_version IN ('1.0', '1.0.0', 'v1.0', '1.10.0-draft', '1.11.0', '1.11.0-draft', '1.12.0', '1.14.0-draft', '1.15.0-draft', '1.16.0-draft', '1.17.0-draft', '1.18.0-draft')),
    application_id                  VARCHAR(128) NOT NULL REFERENCES applications(application_id),
    application_type                VARCHAR(16)  NOT NULL CHECK (application_type IN ('agent', 'rag')),
    ingestion_mode                  VARCHAR(32)  NOT NULL CHECK (ingestion_mode IN (
        'LIVE_RUNTIME', 'SEEDED_FAILURE_FIXTURE', 'REPLAY_VERIFICATION'
    )),
    is_partial_walkthrough          BOOLEAN      NOT NULL DEFAULT FALSE,
    environment                     VARCHAR(32)  NOT NULL CHECK (environment IN ('dev', 'test', 'ci', 'staging', 'prod')),
    started_at                      TIMESTAMPTZ  NOT NULL,
    completed_at                    TIMESTAMPTZ  NOT NULL,
    total_latency_ms                INTEGER      NOT NULL CHECK (total_latency_ms >= 0),
    execution_status                VARCHAR(64)  NOT NULL CHECK (execution_status IN (
        'ACTIVE', 'COMPLETED', 'SUCCEEDED', 'RECOVERED', 'WAITING_APPROVAL',
        'HALTED_POLICY_BLOCK', 'BLOCKED', 'STOPPED_BUSINESS_BLOCK',
        'STOPPED_APPROVAL_PENDING', 'STOPPED_APPROVAL_DENIED',
        'RECOVERY_PENDING', 'FAILED', 'TIMED_OUT', 'CANCELLED',
        'ABSTAINED', 'RUNTIME_ERROR'
    )),
    last_app_state                  VARCHAR(64)  NULL CHECK (last_app_state IS NULL OR last_app_state IN (
        'REQUEST_CAPTURED', 'POLICY_CHECKED', 'SUPPLIER_CHECKED',
        'APPROVAL_CALCULATED', 'APPROVAL_PENDING', 'APPROVED',
        'PO_CREATION', 'COMPLETION'
    )),
    last_rag_stage                  VARCHAR(64)  NULL CHECK (last_rag_stage IS NULL OR last_rag_stage IN (
        'USER_QUERY', 'QUERY_RECEIVED', 'RETRIEVAL', 'RETRIEVAL_COMPLETED',
        'EVIDENCE_SELECTION', 'CONTEXT_SELECTED', 'ANSWER_GENERATION',
        'GENERATION_COMPLETED', 'CITATION_BINDING', 'CITATION_VALIDATED',
        'ANSWER_DELIVERED', 'FINAL_RESPONSE', 'ABSTENTION', 'ERROR'
    )),
    root_request_id                 VARCHAR(128) NOT NULL,
    request_revision                VARCHAR(64)  NOT NULL,
    business_payload_sha256         CHAR(64)     NULL,
    envelope_sha256                 CHAR(64)     NOT NULL,
    versions_json                   JSONB        NOT NULL,
    metadata_availability_json      JSONB        NOT NULL,
    request_json                    JSONB        NOT NULL,
    execution_budget_telemetry_json JSONB        NOT NULL,
    -- Isolated test-only ground-truth & scenario metadata (NEVER exposed in inference projection views)
    scenario_metadata_json          JSONB        NULL,
    ingested_at                     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_trace_chronology CHECK (started_at <= completed_at),
    CONSTRAINT chk_app_state_vs_rag_stage CHECK (
        (application_type = 'agent' AND last_app_state IS NOT NULL AND last_rag_stage IS NULL) OR
        (application_type = 'rag'   AND last_app_state IS NULL     AND last_rag_stage IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_traces_app_ver_time
    ON traces (application_id, started_at DESC, execution_status);
CREATE INDEX IF NOT EXISTS idx_traces_root_request
    ON traces (root_request_id, request_revision);

-- 4. Trace Events Table (Strict 1-Indexed Sequence & Heterogeneous Typed JSONB Attributes)
CREATE TABLE IF NOT EXISTS trace_events (
    trace_id            VARCHAR(128) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    event_id            VARCHAR(128) NOT NULL,
    sequence_number     INTEGER      NOT NULL CHECK (sequence_number >= 1),
    timestamp           TIMESTAMPTZ  NOT NULL,
    event_type          VARCHAR(64)  NOT NULL CHECK (event_type IN (
        'retrieval', 'model_call', 'tool_proposal', 'argument_validation',
        'policy_check', 'tool_suppression', 'approval', 'agent_state',
        'tool_call', 'tool_result', 'recovery_check', 'final_response'
    )),
    step_name           VARCHAR(128) NOT NULL,
    actor               VARCHAR(128) NOT NULL,
    parent_event_id     VARCHAR(128) NULL,
    span_id             VARCHAR(64)  NULL,
    parent_span_id      VARCHAR(64)  NULL,
    latency_ms          INTEGER      NULL CHECK (latency_ms IS NULL OR latency_ms >= 0),
    status              VARCHAR(32)  NOT NULL,
    attributes_json     JSONB        NOT NULL,
    PRIMARY KEY (trace_id, event_id),
    UNIQUE (trace_id, sequence_number),
    FOREIGN KEY (trace_id, parent_event_id) REFERENCES trace_events(trace_id, event_id),
    -- A3: superseded_by_approval_id is a derived read-model field only and MUST stay NULL in every stored event
    CONSTRAINT chk_approval_event_superseded_by_null CHECK (
        event_type <> 'approval' OR (attributes_json->>'superseded_by_approval_id') IS NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_trace_events_type
    ON trace_events (trace_id, event_type, sequence_number);

-- 5. Root-Scoped Single-Use PO Dispatch Claim Consumption Ledger (E17, R16-08, SA-01, SA-02)
CREATE TABLE IF NOT EXISTS dispatch_claim_ledger (
    consumption_record_id                           VARCHAR(128) PRIMARY KEY,
    dispatch_claim_id                               VARCHAR(128) NOT NULL UNIQUE,
    root_request_id                                 VARCHAR(128) NOT NULL UNIQUE,
    request_revision                                VARCHAR(64)  NOT NULL,
    trace_id                                        VARCHAR(128) NOT NULL REFERENCES traces(trace_id),
    preallocated_at_proposal_id                     VARCHAR(128) NOT NULL,
    bound_authorization_check_id                    VARCHAR(128) NOT NULL UNIQUE,
    bound_action_verdict                            VARCHAR(16)  NOT NULL CHECK (bound_action_verdict = 'ALLOW'),
    transition_state_event_id                       VARCHAR(128) NOT NULL,
    resulting_state_revision_id                     VARCHAR(64)  NOT NULL,
    consumed_by_call_id                             VARCHAR(128) NOT NULL UNIQUE,
    bound_supplier_record_version                   VARCHAR(128) NOT NULL,
    observed_supplier_record_version_at_consumption VARCHAR(128) NOT NULL,
    bound_approval_record_version                   VARCHAR(128) NULL,
    observed_approval_record_version_at_consumption VARCHAR(128) NULL,
    bound_decision_record_seq                       INTEGER      NULL,
    observed_decision_record_seq_at_consumption     INTEGER      NULL,
    currentness_verified_at_consumption             BOOLEAN      NOT NULL CHECK (currentness_verified_at_consumption = TRUE),
    -- A4: Explicit stale reason code when a check/consumption is stale (NULL when currentness_verified_at_consumption = TRUE)
    stale_reason_code                               VARCHAR(64)  NULL CHECK (stale_reason_code IS NULL OR stale_reason_code IN (
        'APPROVAL_RECORD_SUPERSEDED',
        'APPROVAL_NO_LONGER_APPROVED',
        'SUPPLIER_RECORD_SUPERSEDED',
        'REQUEST_REVISION_CHANGED',
        'POLICY_BUNDLE_CHANGED'
    )),
    consumption_status                              VARCHAR(64)  NOT NULL CHECK (consumption_status = 'CONSUMED_SINGLE_USE_LOCKED'),
    redispatch_or_reset_permitted                   BOOLEAN      NOT NULL CHECK (redispatch_or_reset_permitted = FALSE),
    consumed_at                                     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_consumption_versions_match CHECK (
        bound_supplier_record_version = observed_supplier_record_version_at_consumption AND
        (bound_approval_record_version IS NOT DISTINCT FROM observed_approval_record_version_at_consumption) AND
        (bound_decision_record_seq IS NOT DISTINCT FROM observed_decision_record_seq_at_consumption)
    )
);


-- 5b. Authoritative Supplier & Approval Records for Atomic Consumption-Time Currentness Locking (SA-02 / OD-04 / OD-12)
CREATE TABLE IF NOT EXISTS supplier_records (
    supplier_id             VARCHAR(128) PRIMARY KEY,
    display_name            VARCHAR(255) NOT NULL,
    status                  VARCHAR(32)  NOT NULL CHECK (status IN ('APPROVED', 'NOT_APPROVED', 'UNKNOWN')),
    raw_status              VARCHAR(64)  NOT NULL,
    current_record_version  VARCHAR(128) NOT NULL,
    directory_version       VARCHAR(128) NOT NULL,
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_records (
    approval_id                 VARCHAR(128) PRIMARY KEY,
    approval_request_id         VARCHAR(128) NOT NULL,
    request_revision            VARCHAR(128) NOT NULL,
    approval_status             VARCHAR(32)  NOT NULL CHECK (approval_status IN ('APPROVED', 'DENIED', 'CANCELLED', 'SUPERSEDED')),
    approval_level              VARCHAR(64)  NOT NULL,
    bound_supplier_id           VARCHAR(128) NOT NULL REFERENCES supplier_records(supplier_id),
    bound_amount                NUMERIC(18,2) NOT NULL,
    bound_currency              VARCHAR(16)  NOT NULL,
    current_record_version      VARCHAR(128) NOT NULL,
    current_decision_record_seq BIGINT       NOT NULL CHECK (current_decision_record_seq > 0),
    supersedes_approval_id      VARCHAR(128) NULL REFERENCES approval_records(approval_id),
    superseded_by_approval_id   VARCHAR(128) NULL REFERENCES approval_records(approval_id),
    updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Transactional Atomic Claim Consumption Function (Acquires Row Locks via SELECT ... FOR UPDATE)
-- Proves currentness is verified against live authoritative supplier_records and approval_records
-- inside the transaction before inserting into dispatch_claim_ledger, rather than trusting a caller boolean.
CREATE OR REPLACE FUNCTION fn_consume_dispatch_claim_atomic(
    p_consumption_id              VARCHAR(128),
    p_dispatch_claim_id           VARCHAR(128),
    p_trace_id                    VARCHAR(128),
    p_root_workflow_id            VARCHAR(128),
    p_request_revision            VARCHAR(128),
    p_preallocated_at_proposal_id VARCHAR(128),
    p_bound_allow_check_id        VARCHAR(128),
    p_consuming_state_revision_id VARCHAR(128),
    p_consuming_call_id           VARCHAR(128),
    p_supplier_id                 VARCHAR(128),
    p_bound_supplier_version      VARCHAR(128),
    p_approval_id                 VARCHAR(128),
    p_bound_approval_version      VARCHAR(128),
    p_bound_decision_seq          BIGINT,
    p_consumed_at                 TIMESTAMPTZ
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_live_sup_ver   VARCHAR(128);
    v_live_sup_stat  VARCHAR(32);
    v_live_apr_ver   VARCHAR(128);
    v_live_apr_seq   BIGINT;
    v_live_apr_stat  VARCHAR(32);
    v_live_apr_supby VARCHAR(128);
BEGIN
    -- 1. Lock authoritative supplier row FOR UPDATE to serialize concurrent supplier updates
    SELECT current_record_version, status
      INTO v_live_sup_ver, v_live_sup_stat
      FROM supplier_records
     WHERE supplier_id = p_supplier_id
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_STALE_RECORD_VERSION_AT_CONSUMPTION: supplier_id % not found', p_supplier_id;
    END IF;

    -- 2. Lock authoritative approval row FOR UPDATE to serialize concurrent revocations/supersessions
    SELECT current_record_version, current_decision_record_seq, approval_status, superseded_by_approval_id
      INTO v_live_apr_ver, v_live_apr_seq, v_live_apr_stat, v_live_apr_supby
      FROM approval_records
     WHERE approval_id = p_approval_id
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_STALE_RECORD_VERSION_AT_CONSUMPTION: approval_id % not found', p_approval_id;
    END IF;

    -- 3. Verify live locked state matches the versions/sequence bound at ALLOW policy_check
    IF v_live_sup_ver <> p_bound_supplier_version OR v_live_sup_stat <> 'APPROVED' THEN
        RAISE EXCEPTION 'ERR_STALE_RECORD_VERSION_AT_CONSUMPTION: supplier version/status drifted (% / % vs %)',
            v_live_sup_ver, v_live_sup_stat, p_bound_supplier_version;
    END IF;

    IF v_live_apr_ver <> p_bound_approval_version
       OR v_live_apr_seq <> p_bound_decision_seq
       OR v_live_apr_stat <> 'APPROVED'
       OR v_live_apr_supby IS NOT NULL THEN
        RAISE EXCEPTION 'ERR_STALE_RECORD_VERSION_AT_CONSUMPTION: approval version/seq/status drifted (% / seq=% / status=% vs % / seq=%)',
            v_live_apr_ver, v_live_apr_seq, v_live_apr_stat, p_bound_approval_version, p_bound_decision_seq;
    END IF;

    -- 4. Insert single-use consumption row (UNIQUE constraints on dispatch_claim_id and root_workflow_id prevent double-consumption)
    INSERT INTO dispatch_claim_ledger (
        consumption_id, dispatch_claim_id, trace_id, root_workflow_id, request_revision,
        preallocated_at_proposal_id, bound_allow_check_id, consuming_state_revision_id,
        consuming_call_id, bound_supplier_record_version, observed_supplier_record_version_at_consumption,
        bound_approval_record_version, observed_approval_record_version_at_consumption,
        bound_decision_record_seq, observed_decision_record_seq_at_consumption,
        currentness_verified_at_consumption, consumption_status, consumed_at, redispatch_permitted
    ) VALUES (
        p_consumption_id, p_dispatch_claim_id, p_trace_id, p_root_workflow_id, p_request_revision,
        p_preallocated_at_proposal_id, p_bound_allow_check_id, p_consuming_state_revision_id,
        p_consuming_call_id, p_bound_supplier_version, v_live_sup_ver,
        p_bound_approval_version, v_live_apr_ver,
        p_bound_decision_seq, v_live_apr_seq,
        TRUE, 'CONSUMED_FOR_SINGLE_PO_CALL', p_consumed_at, FALSE
    );

    RETURN TRUE;
END;
$$;

-- 6. Repeatable Evaluation Runs & Evaluator Results (Never Overwrites Raw Trace Evidence)
CREATE TABLE IF NOT EXISTS evaluation_runs (
    evaluation_run_id       VARCHAR(128) PRIMARY KEY,
    evaluator_suite_version VARCHAR(64)  NOT NULL,
    dataset_version         VARCHAR(64)  NULL,
    decision_config_version VARCHAR(64)  NOT NULL,
    run_status              VARCHAR(32)  NOT NULL CHECK (run_status IN ('RUNNING', 'COMPLETED', 'PARTIAL_FAILURE', 'FAILED')),
    started_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at            TIMESTAMPTZ  NULL
);

CREATE TABLE IF NOT EXISTS evaluator_results (
    evaluator_result_id         VARCHAR(128) PRIMARY KEY,
    evaluation_run_id           VARCHAR(128) NOT NULL REFERENCES evaluation_runs(evaluation_run_id) ON DELETE CASCADE,
    trace_id                    VARCHAR(128) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    evaluator_family            VARCHAR(64)  NOT NULL,
    evaluator_version           VARCHAR(64)  NOT NULL,
    evaluator_execution_status  VARCHAR(64)  NOT NULL CHECK (evaluator_execution_status IN (
        'COMPLETED', 'SKIPPED_NOT_APPLICABLE', 'EVALUATOR_TECHNICAL_ERROR', 'INCOMPLETE_TRACE_EVIDENCE'
    )),
    findings_json               JSONB        NOT NULL DEFAULT '[]'::jsonb,
    metrics_json                JSONB        NOT NULL DEFAULT '{}'::jsonb,
    evidence_refs_json          JSONB        NOT NULL DEFAULT '[]'::jsonb,
    error_details_json          JSONB        NULL,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (evaluation_run_id, trace_id, evaluator_family)
);

-- 7. Failure Predictions, RCA Results & Post-Run Governance Enforcement Summary (SA-09)
CREATE TABLE IF NOT EXISTS failure_predictions (
    prediction_id               VARCHAR(128) PRIMARY KEY,
    evaluation_run_id           VARCHAR(128) NOT NULL REFERENCES evaluation_runs(evaluation_run_id) ON DELETE CASCADE,
    trace_id                    VARCHAR(128) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    classifier_type             VARCHAR(64)  NOT NULL CHECK (classifier_type IN ('RULE_BASELINE', 'LOGISTIC_REGRESSION', 'XGBOOST')),
    classifier_version          VARCHAR(64)  NOT NULL,
    primary_failure_class       VARCHAR(64)  NOT NULL,
    secondary_findings_json     JSONB        NOT NULL DEFAULT '[]'::jsonb,
    confidence_score            DOUBLE PRECISION NULL,
    evidence_refs_json          JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rca_results (
    rca_result_id               VARCHAR(128) PRIMARY KEY,
    evaluation_run_id           VARCHAR(128) NOT NULL REFERENCES evaluation_runs(evaluation_run_id) ON DELETE CASCADE,
    trace_id                    VARCHAR(128) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    rca_engine_version          VARCHAR(64)  NOT NULL,
    top1_root_cause             VARCHAR(64)  NULL,
    top3_ranked_causes_json     JSONB        NOT NULL DEFAULT '[]'::jsonb,
    evidence_refs_json          JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS governance_decisions (
    decision_id                     VARCHAR(128) PRIMARY KEY,
    evaluation_run_id               VARCHAR(128) NOT NULL REFERENCES evaluation_runs(evaluation_run_id) ON DELETE CASCADE,
    trace_id                        VARCHAR(128) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    decision_config_version         VARCHAR(64)  NOT NULL,
    decision                        VARCHAR(32)  NOT NULL CHECK (decision IN ('PASS', 'REVIEW', 'BLOCK', 'INCOMPLETE')),
    evaluation_status               VARCHAR(64)  NOT NULL,
    enforcement_outcome             VARCHAR(64)  NOT NULL CHECK (enforcement_outcome IN (
        'AUTHORIZED_AND_COMMITTED',
        'BLOCKED_PRE_TOOL_NO_SIDE_EFFECT',
        'AUTHORIZED_DISPATCH_RESOLVED_COMMITTED_VIA_RECOVERY',
        'AUTHORIZED_DISPATCH_RESOLVED_NO_SIDE_EFFECT',
        'AUTHORIZED_DISPATCH_UNRESOLVED_HOLD',
        'UNAUTHORIZED_DISPATCH_POLICY_BYPASS',
        'NOT_REACHED_STOPPED_BEFORE_PO_GATE',
        'NOT_APPLICABLE_RAG_WORKFLOW'
    )),
    governance_summary_json         JSONB        NOT NULL,
    fired_rules_json                JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_at                      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (evaluation_run_id, trace_id)
);

-- 8. Offline Human Adjudication Sidecar (Experiment Requirements §§1, 5)
CREATE TABLE IF NOT EXISTS adjudication_records (
    adjudication_id                 VARCHAR(128) PRIMARY KEY,
    trace_id                        VARCHAR(128) NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    dataset_version                 VARCHAR(64)  NOT NULL,
    adjudicated_primary_failure_class VARCHAR(64) NOT NULL,
    secondary_findings_json         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    adjudicated_root_cause          VARCHAR(64)  NULL,
    adjudication_status             VARCHAR(64)  NOT NULL CHECK (adjudication_status IN (
        'UNREVIEWED', 'SINGLE_ANNOTATED', 'DOUBLE_ANNOTATED_AGREED',
        'DISAGREEMENT_PENDING', 'ADJUDICATED_FINAL', 'INCONCLUSIVE_TECHNICAL_ERROR'
    )),
    annotation_guide_version        VARCHAR(64)  NOT NULL,
    evidence_refs_json              JSONB        NOT NULL,
    reviewer_annotations_json       JSONB        NOT NULL DEFAULT '[]'::jsonb,
    adjudicated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (trace_id, dataset_version)
);

-- 9. Quarantine Log for Evidence-Integrity Rejects (Experiment Requirements §8 Item 4)
CREATE TABLE IF NOT EXISTS quarantined_trace_rejects (
    quarantine_id       VARCHAR(128) PRIMARY KEY,
    trace_id            VARCHAR(128) NOT NULL,
    failure_codes_json  JSONB        NOT NULL,
    failure_details     TEXT         NOT NULL,
    schema_version      VARCHAR(32)  NOT NULL,
    validator_version   VARCHAR(32)  NOT NULL,
    ingestion_mode      VARCHAR(32)  NOT NULL,
    producer_build_ref  VARCHAR(128) NOT NULL,
    rejected_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 10. Inference-Safe Projection View (Guaranteed Free of Ground Truth, Adjudication & Security Tags)
CREATE OR REPLACE VIEW v_inference_safe_traces AS
SELECT
    trace_id,
    schema_version,
    application_id,
    application_type,
    ingestion_mode,
    is_partial_walkthrough,
    environment,
    started_at,
    completed_at,
    total_latency_ms,
    execution_status,
    last_app_state,
    last_rag_stage,
    versions_json               AS versions,
    metadata_availability_json  AS metadata_availability,
    request_json                AS request,
    execution_budget_telemetry_json AS execution_budget_telemetry
FROM traces;

COMMIT;