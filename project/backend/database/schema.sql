-- =============================================================================
-- Contract Refund Eligibility System - Database Schema
-- =============================================================================
-- Version: 1.0
-- Date: 2025-11-06
-- Database: PostgreSQL 15.x
-- Description: Complete schema for contract extraction and audit system
-- =============================================================================

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- USERS AND AUTHENTICATION (External Auth Provider)
-- =============================================================================

-- Users table: Stores user profile data (authentication via external provider)
-- Authentication is handled by external provider (Auth0, Okta, AWS Cognito, etc.)
-- This table only stores user profile and authorization data
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- External auth provider identifiers
    auth_provider VARCHAR(50) NOT NULL, -- 'auth0', 'okta', 'cognito', etc.
    auth_provider_user_id VARCHAR(255) UNIQUE NOT NULL, -- sub claim from JWT

    -- User profile data (from auth provider)
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Application-specific authorization
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Index for user lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth_provider_user_id ON users(auth_provider_user_id);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- User sessions table: Track active sessions for audit and context
-- Note: Authentication tokens are managed by external auth provider
-- This table tracks session metadata for audit trail and user context
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Session metadata (no auth tokens stored)
    ip_address INET,
    user_agent TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    is_active BOOLEAN DEFAULT true
);

-- Indexes for session management
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_is_active ON sessions(is_active);

-- =============================================================================
-- CONTRACTS (TEMPLATES)
-- =============================================================================

-- Contracts table: Contract TEMPLATES (not filled customer contracts)
-- PDFs stored in S3 with IAM authentication (not publicly accessible)
-- Document text and embeddings populated by external batch ETL process
-- Account number mappings stored separately in account_template_mappings table
CREATE TABLE contracts (
    contract_id VARCHAR(100) PRIMARY KEY,

    -- S3 Storage (PDFs stored with IAM authentication)
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key VARCHAR(1024) NOT NULL,

    -- Document Content (populated by external ETL batch process)
    document_text TEXT,
    embeddings JSONB,
    text_extracted_at TIMESTAMP WITH TIME ZONE,
    text_extraction_status VARCHAR(50), -- 'pending', 'completed', 'failed'

    -- Template Metadata
    document_repository_id VARCHAR(100),
    contract_type VARCHAR(50) DEFAULT 'GAP', -- GAP, VSC, F&I, etc.
    contract_date DATE, -- When template was created

    -- Template Versioning
    template_version VARCHAR(50),
    effective_date DATE, -- When this version became active
    deprecated_date DATE, -- When this version was superseded
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT s3_bucket_not_empty CHECK (s3_bucket <> ''),
    CONSTRAINT s3_key_not_empty CHECK (s3_key <> '')
);

-- Indexes for contract template lookups
CREATE INDEX idx_contracts_contract_type ON contracts(contract_type);
CREATE INDEX idx_contracts_last_synced_at ON contracts(last_synced_at);
CREATE INDEX idx_contracts_contract_date ON contracts(contract_date);
CREATE INDEX idx_contracts_s3_location ON contracts(s3_bucket, s3_key);
CREATE INDEX idx_contracts_extraction_status ON contracts(text_extraction_status);
CREATE INDEX idx_contracts_is_active ON contracts(is_active);
CREATE INDEX idx_contracts_template_version ON contracts(template_version);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_contracts_updated_at
    BEFORE UPDATE ON contracts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- JURISDICTIONS (STATE-SPECIFIC VALIDATION)
-- =============================================================================

-- Jurisdictions table: States and regions with regulatory authority
-- Supports state-specific validation rules for contract terms
CREATE TABLE jurisdictions (
    jurisdiction_id VARCHAR(10) PRIMARY KEY,  -- 'US-CA', 'US-TX', 'US-NY', 'US-FEDERAL'
    jurisdiction_name VARCHAR(100) NOT NULL,  -- 'California', 'Texas', 'Federal (Default)'
    country_code VARCHAR(2) NOT NULL,         -- 'US'
    state_code VARCHAR(2),                    -- 'CA', 'TX', NULL for federal
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for jurisdiction lookups
CREATE INDEX idx_jurisdictions_state_code ON jurisdictions(state_code);
CREATE INDEX idx_jurisdictions_is_active ON jurisdictions(is_active);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_jurisdictions_updated_at
    BEFORE UPDATE ON jurisdictions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE jurisdictions IS 'Master list of US states and jurisdictions with regulatory authority';
COMMENT ON COLUMN jurisdictions.jurisdiction_id IS 'Unique identifier (e.g., US-CA for California)';
COMMENT ON COLUMN jurisdictions.state_code IS 'Two-letter state code (NULL for federal default)';

-- Contract-Jurisdiction Mappings table: Many-to-many relationship
-- Supports multi-state contracts with primary jurisdiction designation
CREATE TABLE contract_jurisdictions (
    contract_jurisdiction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id VARCHAR(100) NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
    jurisdiction_id VARCHAR(10) NOT NULL REFERENCES jurisdictions(jurisdiction_id),
    is_primary BOOLEAN DEFAULT false,         -- Primary jurisdiction for validation
    effective_date DATE,                      -- When this jurisdiction mapping became active
    expiration_date DATE,                     -- When superseded (NULL if current)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_contract_jurisdiction UNIQUE(contract_id, jurisdiction_id, effective_date)
);

-- Indexes for contract-jurisdiction mappings
CREATE INDEX idx_contract_jurisdictions_contract ON contract_jurisdictions(contract_id);
CREATE INDEX idx_contract_jurisdictions_jurisdiction ON contract_jurisdictions(jurisdiction_id);
CREATE INDEX idx_contract_jurisdictions_effective ON contract_jurisdictions(effective_date);

-- Comments
COMMENT ON TABLE contract_jurisdictions IS 'Many-to-many mapping supporting multi-state contracts';
COMMENT ON COLUMN contract_jurisdictions.is_primary IS 'Exactly one jurisdiction per contract should be primary';

-- State Validation Rules table: Database-driven rules with JSONB configuration
-- Supports rule versioning with effective dates
CREATE TABLE state_validation_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id VARCHAR(10) NOT NULL REFERENCES jurisdictions(jurisdiction_id),
    rule_category VARCHAR(50) NOT NULL,  -- 'gap_premium', 'cancellation_fee', 'refund_method'

    -- Flexible JSONB configuration
    rule_config JSONB NOT NULL,

    -- Rule versioning and lifecycle
    effective_date DATE NOT NULL,             -- When this rule version becomes active
    expiration_date DATE,                     -- When superseded (NULL if current)
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    rule_description TEXT,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_rule_category CHECK (rule_category IN (
        'gap_premium', 'cancellation_fee', 'refund_method'
    ))
);

-- Indexes for state validation rules
CREATE INDEX idx_state_rules_jurisdiction ON state_validation_rules(jurisdiction_id);
CREATE INDEX idx_state_rules_category ON state_validation_rules(rule_category);
CREATE INDEX idx_state_rules_effective ON state_validation_rules(effective_date);
CREATE INDEX idx_state_rules_active ON state_validation_rules(is_active, expiration_date);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_state_rules_updated_at
    BEFORE UPDATE ON state_validation_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE state_validation_rules IS 'State-specific validation rules with versioning support';
COMMENT ON COLUMN state_validation_rules.rule_config IS 'JSONB configuration for flexible rule definitions (e.g., {min: 200, max: 1500, strict: true})';

-- =============================================================================
-- ACCOUNT TEMPLATE MAPPINGS
-- =============================================================================

-- Account-Template Mappings table: Maps account numbers to contract template IDs
-- This table caches lookups from external database for performance
-- Supports hybrid cache strategy (Redis -> DB -> External API)
-- MULTI-POLICY SUPPORT: One account can have multiple policies (GAP, VSC, etc.)
CREATE TABLE account_template_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number VARCHAR(100) NOT NULL,
    policy_id VARCHAR(50) NOT NULL,
    contract_template_id VARCHAR(100) NOT NULL,

    -- Cache metadata
    source VARCHAR(50) NOT NULL CHECK (source IN ('external_api', 'manual', 'migrated')),
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_validated_at TIMESTAMP WITH TIME ZONE,

    -- Foreign key to templates (allows unknown templates to be cached)
    CONSTRAINT fk_template FOREIGN KEY (contract_template_id)
        REFERENCES contracts(contract_id) ON DELETE CASCADE,

    -- Composite unique constraint: one policy_id per account
    CONSTRAINT unique_account_policy UNIQUE (account_number, policy_id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for account-template mapping lookups
CREATE INDEX idx_account_mappings_account_number ON account_template_mappings(account_number);
CREATE INDEX idx_account_mappings_policy_id ON account_template_mappings(policy_id);
CREATE INDEX idx_account_mappings_account_policy ON account_template_mappings(account_number, policy_id);
CREATE INDEX idx_account_mappings_template_id ON account_template_mappings(contract_template_id);
CREATE INDEX idx_account_mappings_cached_at ON account_template_mappings(cached_at);
CREATE INDEX idx_account_mappings_source ON account_template_mappings(source);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_account_mappings_updated_at
    BEFORE UPDATE ON account_template_mappings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- EXTRACTIONS
-- =============================================================================

-- Extractions table: AI-extracted data from contracts
CREATE TABLE extractions (
    extraction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id VARCHAR(100) NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,

    -- GAP Insurance Premium field
    gap_insurance_premium DECIMAL(10,2),
    gap_premium_confidence DECIMAL(5,2) CHECK (gap_premium_confidence >= 0 AND gap_premium_confidence <= 100),
    gap_premium_source JSONB, -- {page: int, section: string, line: int}

    -- Refund Calculation Method field
    refund_calculation_method VARCHAR(100),
    refund_method_confidence DECIMAL(5,2) CHECK (refund_method_confidence >= 0 AND refund_method_confidence <= 100),
    refund_method_source JSONB,

    -- Cancellation Fee field
    cancellation_fee DECIMAL(10,2),
    cancellation_fee_confidence DECIMAL(5,2) CHECK (cancellation_fee_confidence >= 0 AND cancellation_fee_confidence <= 100),
    cancellation_fee_source JSONB,

    -- Metadata
    llm_model_version VARCHAR(100) NOT NULL,
    llm_provider VARCHAR(50), -- 'openai', 'anthropic', 'bedrock'
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_cost_usd DECIMAL(10,6),

    -- Status and approval
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    extracted_by UUID REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(user_id),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejected_by UUID REFERENCES users(user_id),
    rejection_reason TEXT,

    -- Validation results (Phase 1: Validation Agent)
    validation_status VARCHAR(20) CHECK (validation_status IN ('pass', 'warning', 'fail')),
    validation_results JSONB,
    validated_at TIMESTAMP WITH TIME ZONE,

    -- State validation tracking (Phase 2: State-Specific Validation)
    applied_jurisdiction_id VARCHAR(10) REFERENCES jurisdictions(jurisdiction_id),
    jurisdiction_applied_at TIMESTAMP WITH TIME ZONE,
    state_validation_results JSONB,

    -- Ensure only one extraction per contract
    CONSTRAINT unique_contract_extraction UNIQUE(contract_id)
);

-- Indexes for extraction queries
CREATE INDEX idx_extractions_contract_id ON extractions(contract_id);
CREATE INDEX idx_extractions_status ON extractions(status);
CREATE INDEX idx_extractions_extracted_at ON extractions(extracted_at);
CREATE INDEX idx_extractions_extracted_by ON extractions(extracted_by);
CREATE INDEX idx_extractions_llm_provider ON extractions(llm_provider);
CREATE INDEX idx_extractions_jurisdiction ON extractions(applied_jurisdiction_id);

-- Trigger to update updated_at timestamp (add updated_at column first)
ALTER TABLE extractions ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

CREATE TRIGGER update_extractions_updated_at
    BEFORE UPDATE ON extractions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- CORRECTIONS
-- =============================================================================

-- Corrections table: Track human corrections to AI extractions
CREATE TABLE corrections (
    correction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES extractions(extraction_id) ON DELETE CASCADE,
    field_name VARCHAR(50) NOT NULL CHECK (field_name IN (
        'gap_insurance_premium',
        'refund_calculation_method',
        'cancellation_fee'
    )),
    original_value TEXT,
    corrected_value TEXT NOT NULL,
    correction_reason TEXT,
    corrected_by UUID NOT NULL REFERENCES users(user_id),
    corrected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT corrected_value_not_empty CHECK (corrected_value <> '')
);

-- Indexes for correction tracking
CREATE INDEX idx_corrections_extraction_id ON corrections(extraction_id);
CREATE INDEX idx_corrections_field_name ON corrections(field_name);
CREATE INDEX idx_corrections_corrected_by ON corrections(corrected_by);
CREATE INDEX idx_corrections_corrected_at ON corrections(corrected_at);

-- =============================================================================
-- AUDIT TRAIL (Event Sourcing)
-- =============================================================================

-- Audit events table: Immutable log of all system events
CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'search',
        'view',
        'extract',
        'edit',
        'approve',
        'reject',
        'chat',
        'login',
        'logout',
        'user_created',
        'user_updated',
        'user_deleted',
        'account_lookup',
        'template_view',
        'mapping_cached',
        'state_rule_applied',
        'state_validation_failed',
        'multi_state_detected',
        'state_rule_created',
        'state_rule_updated'
    )),
    contract_id VARCHAR(100) REFERENCES contracts(contract_id),
    extraction_id UUID REFERENCES extractions(extraction_id),
    user_id UUID REFERENCES users(user_id),
    event_data JSONB, -- Flexible JSON for storing event-specific data (includes account_number for searches)
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    session_id UUID REFERENCES sessions(session_id),

    -- Performance and cost tracking
    duration_ms INTEGER,
    cost_usd DECIMAL(10,6)
);

-- Indexes for audit queries
CREATE INDEX idx_audit_events_contract_id ON audit_events(contract_id);
CREATE INDEX idx_audit_events_extraction_id ON audit_events(extraction_id);
CREATE INDEX idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);
CREATE INDEX idx_audit_events_event_type ON audit_events(event_type);
CREATE INDEX idx_audit_events_session_id ON audit_events(session_id);

-- Partial index for recent events removed due to CURRENT_TIMESTAMP immutability issue
-- Can be added later with a different approach if needed

-- Prevent updates and deletes on audit_events (immutable log)
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit events are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_audit_events_update
    BEFORE UPDATE ON audit_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER prevent_audit_events_delete
    BEFORE DELETE ON audit_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();

-- =============================================================================
-- CONFIGURATION
-- =============================================================================

-- System configuration table: Store application settings
CREATE TABLE system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    value_type VARCHAR(20) CHECK (value_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    is_secret BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(user_id)
);

CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- CHAT HISTORY
-- =============================================================================

-- Chat messages table: Store AI chat interactions
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    contract_id VARCHAR(100) REFERENCES contracts(contract_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    llm_provider VARCHAR(50),
    llm_model_version VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    processing_time_ms INTEGER,
    cost_usd DECIMAL(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT content_not_empty CHECK (content <> '')
);

-- Indexes for chat history
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_contract_id ON chat_messages(contract_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- =============================================================================
-- PERFORMANCE METRICS
-- =============================================================================

-- Extraction metrics table: Track AI extraction performance over time
CREATE TABLE extraction_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    total_extractions INTEGER DEFAULT 0,
    successful_extractions INTEGER DEFAULT 0,
    failed_extractions INTEGER DEFAULT 0,
    avg_processing_time_ms INTEGER,
    avg_confidence_score DECIMAL(5,2),
    total_cost_usd DECIMAL(10,2),
    llm_provider VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_daily_metrics UNIQUE(date, llm_provider)
);

CREATE INDEX idx_extraction_metrics_date ON extraction_metrics(date);
CREATE INDEX idx_extraction_metrics_llm_provider ON extraction_metrics(llm_provider);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View: Complete extraction information with user details
CREATE VIEW v_extraction_details AS
SELECT
    e.extraction_id,
    e.contract_id,
    c.contract_type,
    c.template_version,
    c.is_active AS template_is_active,
    e.gap_insurance_premium,
    e.gap_premium_confidence,
    e.refund_calculation_method,
    e.refund_method_confidence,
    e.cancellation_fee,
    e.cancellation_fee_confidence,
    e.status,
    e.llm_model_version,
    e.llm_provider,
    e.processing_time_ms,
    e.extracted_at,
    u_extract.username AS extracted_by_username,
    u_extract.email AS extracted_by_email,
    e.approved_at,
    u_approve.username AS approved_by_username,
    u_approve.email AS approved_by_email,
    CASE
        WHEN EXISTS (SELECT 1 FROM corrections cor WHERE cor.extraction_id = e.extraction_id)
        THEN true
        ELSE false
    END AS has_corrections
FROM extractions e
JOIN contracts c ON e.contract_id = c.contract_id
LEFT JOIN users u_extract ON e.extracted_by = u_extract.user_id
LEFT JOIN users u_approve ON e.approved_by = u_approve.user_id;

-- View: User activity summary
CREATE VIEW v_user_activity AS
SELECT
    u.user_id,
    u.username,
    u.email,
    u.role,
    u.is_active,
    u.last_login_at,
    COUNT(DISTINCT e.extraction_id) AS total_extractions,
    COUNT(DISTINCT CASE WHEN e.status = 'approved' THEN e.extraction_id END) AS approved_extractions,
    COUNT(DISTINCT cor.correction_id) AS total_corrections,
    COUNT(DISTINCT ae.event_id) AS total_events
FROM users u
LEFT JOIN extractions e ON u.user_id = e.extracted_by
LEFT JOIN corrections cor ON u.user_id = cor.corrected_by
LEFT JOIN audit_events ae ON u.user_id = ae.user_id
GROUP BY u.user_id, u.username, u.email, u.role, u.is_active, u.last_login_at;

-- View: Daily extraction statistics
CREATE VIEW v_daily_extraction_stats AS
SELECT
    DATE(extracted_at) AS extraction_date,
    COUNT(*) AS total_extractions,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) AS approved_count,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) AS rejected_count,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending_count,
    AVG(processing_time_ms) AS avg_processing_time_ms,
    AVG((gap_premium_confidence + refund_method_confidence + cancellation_fee_confidence) / 3.0) AS avg_confidence_score,
    SUM(total_cost_usd) AS total_cost_usd
FROM extractions
GROUP BY DATE(extracted_at)
ORDER BY extraction_date DESC;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function: Get extraction accuracy by comparing with corrections
CREATE OR REPLACE FUNCTION calculate_extraction_accuracy(p_extraction_id UUID)
RETURNS TABLE(
    field_name VARCHAR(50),
    was_corrected BOOLEAN,
    original_value TEXT,
    corrected_value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        unnest(ARRAY['gap_insurance_premium', 'refund_calculation_method', 'cancellation_fee']) AS field_name,
        EXISTS(
            SELECT 1 FROM corrections c
            WHERE c.extraction_id = p_extraction_id
            AND c.field_name = unnest(ARRAY['gap_insurance_premium', 'refund_calculation_method', 'cancellation_fee'])
        ) AS was_corrected,
        CASE unnest(ARRAY['gap_insurance_premium', 'refund_calculation_method', 'cancellation_fee'])
            WHEN 'gap_insurance_premium' THEN e.gap_insurance_premium::TEXT
            WHEN 'refund_calculation_method' THEN e.refund_calculation_method
            WHEN 'cancellation_fee' THEN e.cancellation_fee::TEXT
        END AS original_value,
        c.corrected_value
    FROM extractions e
    LEFT JOIN corrections c ON c.extraction_id = e.extraction_id
        AND c.field_name = unnest(ARRAY['gap_insurance_premium', 'refund_calculation_method', 'cancellation_fee'])
    WHERE e.extraction_id = p_extraction_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP
    OR (last_activity < CURRENT_TIMESTAMP - INTERVAL '4 hours' AND is_active = false);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PARTITIONING STRATEGY (For Future Optimization)
-- =============================================================================

-- Note: Audit events table should be partitioned by month after 6 months of operation
-- Example (to be executed later):
--
-- ALTER TABLE audit_events RENAME TO audit_events_old;
--
-- CREATE TABLE audit_events (
--     LIKE audit_events_old INCLUDING ALL
-- ) PARTITION BY RANGE (timestamp);
--
-- CREATE TABLE audit_events_2025_11 PARTITION OF audit_events
--     FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE users IS 'User profiles with authorization roles (authentication via external provider)';
COMMENT ON TABLE sessions IS 'Active user sessions for audit trail (auth tokens managed by external provider)';
COMMENT ON TABLE contracts IS 'Contract templates (not filled customer contracts) - PDFs and metadata';
COMMENT ON TABLE account_template_mappings IS 'Cache of account number to template ID mappings from external database';
COMMENT ON TABLE extractions IS 'AI-extracted data from contract templates with confidence scores';
COMMENT ON TABLE corrections IS 'Human corrections to AI extractions for tracking accuracy';
COMMENT ON TABLE audit_events IS 'Immutable event log for compliance and audit trail';
COMMENT ON TABLE system_config IS 'Application configuration settings';
COMMENT ON TABLE chat_messages IS 'AI chat conversation history';
COMMENT ON TABLE extraction_metrics IS 'Daily aggregated metrics for AI extraction performance';

COMMENT ON COLUMN users.auth_provider IS 'External authentication provider (auth0, okta, cognito, etc.)';
COMMENT ON COLUMN users.auth_provider_user_id IS 'Unique user ID from external auth provider (sub claim from JWT)';
COMMENT ON COLUMN contracts.contract_id IS 'Template identifier (e.g., GAP-2024-TEMPLATE-001)';
COMMENT ON COLUMN contracts.template_version IS 'Version number of this template (e.g., 1.0, 2.0)';
COMMENT ON COLUMN contracts.is_active IS 'Whether this template version is currently active';
COMMENT ON COLUMN account_template_mappings.source IS 'Source of mapping: external_api, manual, or migrated';
COMMENT ON COLUMN account_template_mappings.cached_at IS 'When mapping was cached from external source';
COMMENT ON COLUMN extractions.gap_premium_confidence IS 'Confidence score 0-100 for GAP insurance premium extraction';
COMMENT ON COLUMN extractions.llm_provider IS 'LLM provider used: openai, anthropic, or bedrock';
COMMENT ON COLUMN extractions.applied_jurisdiction_id IS 'Primary jurisdiction whose rules were applied during validation';
COMMENT ON COLUMN extractions.jurisdiction_applied_at IS 'When jurisdiction rules were applied';
COMMENT ON COLUMN extractions.state_validation_results IS 'Detailed state validation context and multi-state conflicts';
COMMENT ON COLUMN audit_events.event_data IS 'Flexible JSONB field for event-specific data (includes account_number for searches)';

-- =============================================================================
-- GRANTS (To be customized based on user roles)
-- =============================================================================

-- Example grants (uncomment and customize for production):
--
-- -- Application user (read/write)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
--
-- -- Read-only user (for reporting)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
