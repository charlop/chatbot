-- =============================================================================
-- SEED DATA SCRIPT
-- Contract Refund Eligibility System
-- =============================================================================
-- Version: 1.0
-- Date: 2025-11-06
-- Purpose: Initial seed data for development and testing
-- =============================================================================

-- IMPORTANT: This script should be run AFTER schema.sql
-- IMPORTANT: Passwords are hashed with bcrypt (12 rounds)
-- IMPORTANT: Use environment-specific data for production

-- =============================================================================
-- SYSTEM CONFIGURATION
-- =============================================================================

INSERT INTO system_config (config_key, config_value, value_type, description, is_secret) VALUES
    ('confidence_threshold', '80', 'number', 'Minimum confidence score (0-100) for high confidence extraction', false),
    ('session_timeout_hours', '4', 'number', 'Session timeout in hours', false),
    ('llm_default_provider', 'openai', 'string', 'Default LLM provider: openai, anthropic, or bedrock', false),
    ('cache_ttl_minutes', '30', 'number', 'Cache TTL in minutes for document text', false),
    ('max_retries', '3', 'number', 'Maximum LLM API retries on failure', false),
    ('circuit_breaker_threshold', '5', 'number', 'Number of consecutive failures before circuit breaker opens', false),
    ('extraction_timeout_seconds', '15', 'number', 'Timeout for LLM extraction calls', false),
    ('enable_chat_feature', 'true', 'boolean', 'Enable AI chat interface', false),
    ('max_chat_history', '50', 'number', 'Maximum chat messages to retain per session', false),
    ('pdf_cache_ttl_minutes', '60', 'number', 'PDF cache TTL in minutes', false),
    ('require_correction_reason', 'false', 'boolean', 'Require users to provide reason for corrections', false),
    ('enable_metrics_collection', 'true', 'boolean', 'Enable daily metrics aggregation', false)
ON CONFLICT (config_key) DO NOTHING;

-- =============================================================================
-- USERS (Authentication via External Provider)
-- =============================================================================

-- Note: Authentication is handled by external provider (Auth0, Okta, AWS Cognito, etc.)
-- These are sample users with mock auth provider IDs for development/testing

-- Admin user
INSERT INTO users (
    auth_provider,
    auth_provider_user_id,
    email,
    username,
    first_name,
    last_name,
    role,
    is_active
) VALUES
    ('auth0', 'auth0|admin-mock-sub-123456', 'admin@company.com', 'admin', 'System', 'Administrator', 'admin', true)
ON CONFLICT (auth_provider_user_id) DO NOTHING;

-- Regular users
INSERT INTO users (
    auth_provider,
    auth_provider_user_id,
    email,
    username,
    first_name,
    last_name,
    role,
    is_active
) VALUES
    ('auth0', 'auth0|user-jane-doe-789012', 'jane.doe@company.com', 'jane.doe', 'Jane', 'Doe', 'user', true),
    ('auth0', 'auth0|user-john-smith-345678', 'john.smith@company.com', 'john.smith', 'John', 'Smith', 'user', true),
    ('auth0', 'auth0|user-sarah-johnson-901234', 'sarah.johnson@company.com', 'sarah.johnson', 'Sarah', 'Johnson', 'user', true)
ON CONFLICT (auth_provider_user_id) DO NOTHING;

-- =============================================================================
-- SAMPLE CONTRACTS (For Testing)
-- =============================================================================

-- Sample GAP contracts
-- Note: PDFs stored in S3 with IAM auth, document text populated by external ETL
INSERT INTO contracts (
    contract_id,
    account_number,
    s3_bucket,
    s3_key,
    document_text,
    text_extraction_status,
    text_extracted_at,
    document_repository_id,
    contract_type,
    contract_date,
    customer_name,
    vehicle_info
) VALUES
    ('GAP-2024-001001', 'ACC-100001', 'contracts-dev', 'contracts/2024/01/GAP-2024-001001.pdf',
     'This GAP Insurance Agreement provides coverage for the difference between the outstanding loan balance and the actual cash value of the vehicle in the event of a total loss. Premium: $1250.00. Cancellation Fee: $50.00. Refund Method: Pro-Rata.',
     'completed', CURRENT_TIMESTAMP - INTERVAL '1 day',
     'DOC-001001', 'GAP', '2024-01-15', 'Customer #100001', '{"make": "Toyota", "model": "Camry", "year": 2023, "vin": "1HGBH41JXMN109186"}'),
    ('GAP-2024-001002', 'ACC-100002', 'contracts-dev', 'contracts/2024/01/GAP-2024-001002.pdf',
     'GAP Insurance Contract. Premium: $1895.00. Cancellation Fee: $75.00. Refund Calculation: Rule of 78s method.',
     'completed', CURRENT_TIMESTAMP - INTERVAL '1 day',
     'DOC-001002', 'GAP', '2024-01-20', 'Customer #100002', '{"make": "Honda", "model": "Accord", "year": 2023, "vin": "19XFB2F59CE000001"}'),
    ('GAP-2024-001003', 'ACC-100003', 'contracts-dev', 'contracts/2024/02/GAP-2024-001003.pdf',
     'GAP Coverage Agreement. Premium Amount: $2150.00. Administrative Fee for Cancellation: $100.00. Refund: Pro-Rata calculation.',
     'completed', CURRENT_TIMESTAMP - INTERVAL '2 days',
     'DOC-001003', 'GAP', '2024-02-10', 'Customer #100003', '{"make": "Ford", "model": "F-150", "year": 2024, "vin": "1FTFW1E80MFC10001"}'),
    ('GAP-2024-001004', 'ACC-100004', 'contracts-dev', 'contracts/2024/02/GAP-2024-001004.pdf',
     NULL, 'pending', NULL,
     'DOC-001004', 'GAP', '2024-02-15', 'Customer #100004', '{"make": "Chevrolet", "model": "Silverado", "year": 2024, "vin": "1GC4YPE77HF100001"}'),
    ('GAP-2024-001005', 'ACC-100005', 'contracts-dev', 'contracts/2024/03/GAP-2024-001005.pdf',
     NULL, 'pending', NULL,
     'DOC-001005', 'GAP', '2024-03-01', 'Customer #100005', '{"make": "Tesla", "model": "Model 3", "year": 2024, "vin": "5YJ3E1EB9KF000001"}'),
    ('GAP-2024-001006', 'ACC-100006', 'contracts-dev', 'contracts/2024/03/GAP-2024-001006.pdf',
     NULL, 'pending', NULL,
     'DOC-001006', 'GAP', '2024-03-10', 'Customer #100006', '{"make": "BMW", "model": "X5", "year": 2024, "vin": "5UXCR6C08K0A00001"}'),
    ('GAP-2024-001007', 'ACC-100007', 'contracts-dev', 'contracts/2024/03/GAP-2024-001007.pdf',
     NULL, 'failed', CURRENT_TIMESTAMP - INTERVAL '3 days',
     'DOC-001007', 'GAP', '2024-03-15', 'Customer #100007', '{"make": "Mercedes-Benz", "model": "GLE", "year": 2024, "vin": "4JGDA5HB0KA000001"}'),
    ('GAP-2024-001008', 'ACC-100008', 'contracts-dev', 'contracts/2024/04/GAP-2024-001008.pdf',
     NULL, 'pending', NULL,
     'DOC-001008', 'GAP', '2024-04-01', 'Customer #100008', '{"make": "Audi", "model": "Q5", "year": 2024, "vin": "WA1BNAFY5K2000001"}'),
    ('GAP-2024-001009', 'ACC-100009', 'contracts-dev', 'contracts/2024/04/GAP-2024-001009.pdf',
     NULL, 'pending', NULL,
     'DOC-001009', 'GAP', '2024-04-10', 'Customer #100009', '{"make": "Lexus", "model": "RX", "year": 2024, "vin": "2T2HZMAA3LC000001"}'),
    ('GAP-2024-001010', 'ACC-100010', 'contracts-dev', 'contracts/2024/04/GAP-2024-001010.pdf',
     NULL, 'pending', NULL,
     'DOC-001010', 'GAP', '2024-04-20', 'Customer #100010', '{"make": "Nissan", "model": "Altima", "year": 2024, "vin": "1N4BL4BV5RN000001"}')
ON CONFLICT (contract_id) DO NOTHING;

-- =============================================================================
-- SAMPLE EXTRACTIONS (For Testing)
-- =============================================================================

-- Get user IDs for foreign key references
DO $$
DECLARE
    v_user_id UUID;
    v_admin_id UUID;
BEGIN
    -- Get first regular user ID
    SELECT user_id INTO v_user_id FROM users WHERE role = 'user' LIMIT 1;
    -- Get admin user ID
    SELECT user_id INTO v_admin_id FROM users WHERE role = 'admin' LIMIT 1;

    -- Sample extraction 1: High confidence, approved
    INSERT INTO extractions (
        contract_id,
        gap_insurance_premium,
        gap_premium_confidence,
        gap_premium_source,
        refund_calculation_method,
        refund_method_confidence,
        refund_method_source,
        cancellation_fee,
        cancellation_fee_confidence,
        cancellation_fee_source,
        llm_model_version,
        llm_provider,
        processing_time_ms,
        prompt_tokens,
        completion_tokens,
        total_cost_usd,
        status,
        extracted_by,
        approved_by,
        approved_at
    ) VALUES (
        'GAP-2024-001001',
        1250.00,
        95.5,
        '{"page": 3, "section": "Coverage Details", "line": 12}',
        'Pro-Rata',
        92.3,
        '{"page": 5, "section": "Cancellation Terms", "line": 8}',
        50.00,
        98.1,
        '{"page": 5, "section": "Fees", "line": 15}',
        'gpt-4-turbo-2024-04-09',
        'openai',
        7234,
        3200,
        420,
        0.012345,
        'approved',
        v_user_id,
        v_user_id,
        CURRENT_TIMESTAMP - INTERVAL '2 hours'
    ) ON CONFLICT (contract_id) DO NOTHING;

    -- Sample extraction 2: Medium confidence, pending
    INSERT INTO extractions (
        contract_id,
        gap_insurance_premium,
        gap_premium_confidence,
        gap_premium_source,
        refund_calculation_method,
        refund_method_confidence,
        refund_method_source,
        cancellation_fee,
        cancellation_fee_confidence,
        cancellation_fee_source,
        llm_model_version,
        llm_provider,
        processing_time_ms,
        prompt_tokens,
        completion_tokens,
        total_cost_usd,
        status,
        extracted_by
    ) VALUES (
        'GAP-2024-001002',
        1895.00,
        82.4,
        '{"page": 2, "section": "Premium Breakdown", "line": 5}',
        'Rule of 78s',
        75.6,
        '{"page": 6, "section": "Refund Policy", "line": 12}',
        75.00,
        88.9,
        '{"page": 6, "section": "Fees Schedule", "line": 20}',
        'claude-3-opus-20240229',
        'anthropic',
        9123,
        3500,
        450,
        0.015678,
        'pending',
        v_user_id
    ) ON CONFLICT (contract_id) DO NOTHING;

    -- Sample extraction 3: Low confidence, pending (needs human review)
    INSERT INTO extractions (
        contract_id,
        gap_insurance_premium,
        gap_premium_confidence,
        gap_premium_source,
        refund_calculation_method,
        refund_method_confidence,
        refund_method_source,
        cancellation_fee,
        cancellation_fee_confidence,
        cancellation_fee_source,
        llm_model_version,
        llm_provider,
        processing_time_ms,
        prompt_tokens,
        completion_tokens,
        total_cost_usd,
        status,
        extracted_by
    ) VALUES (
        'GAP-2024-001003',
        2150.00,
        65.2,
        '{"page": 4, "section": "Coverage", "line": 18}',
        'Pro-Rata',
        68.8,
        '{"page": 7, "section": "Cancellation", "line": 5}',
        100.00,
        72.3,
        '{"page": 7, "section": "Administrative Fees", "line": 22}',
        'gpt-4-turbo-2024-04-09',
        'openai',
        8567,
        3300,
        440,
        0.013456,
        'pending',
        v_user_id
    ) ON CONFLICT (contract_id) DO NOTHING;

    -- Sample extraction 4: Rejected (incorrect contract type)
    INSERT INTO extractions (
        contract_id,
        gap_insurance_premium,
        gap_premium_confidence,
        gap_premium_source,
        refund_calculation_method,
        refund_method_confidence,
        refund_method_source,
        cancellation_fee,
        cancellation_fee_confidence,
        cancellation_fee_source,
        llm_model_version,
        llm_provider,
        processing_time_ms,
        prompt_tokens,
        completion_tokens,
        total_cost_usd,
        status,
        extracted_by,
        rejected_by,
        rejected_at,
        rejection_reason
    ) VALUES (
        'GAP-2024-001004',
        1500.00,
        45.2,
        '{"page": 3, "section": "Terms", "line": 10}',
        'Unknown',
        38.5,
        '{"page": 5, "section": "Details", "line": 15}',
        0.00,
        55.1,
        '{"page": 5, "section": "Fees", "line": 20}',
        'claude-3-opus-20240229',
        'anthropic',
        7890,
        3400,
        430,
        0.014234,
        'rejected',
        v_user_id,
        v_admin_id,
        CURRENT_TIMESTAMP - INTERVAL '1 hour',
        'Incorrect contract type - this is not a GAP insurance contract'
    ) ON CONFLICT (contract_id) DO NOTHING;
END $$;

-- =============================================================================
-- SAMPLE CORRECTIONS (For Testing AI Accuracy)
-- =============================================================================

DO $$
DECLARE
    v_extraction_id UUID;
    v_user_id UUID;
BEGIN
    -- Get extraction ID for GAP-2024-001001
    SELECT extraction_id INTO v_extraction_id FROM extractions WHERE contract_id = 'GAP-2024-001001';
    -- Get first user ID
    SELECT user_id INTO v_user_id FROM users WHERE role = 'user' LIMIT 1;

    -- Sample correction: AI extracted wrong premium amount
    IF v_extraction_id IS NOT NULL THEN
        INSERT INTO corrections (
            extraction_id,
            field_name,
            original_value,
            corrected_value,
            correction_reason,
            corrected_by
        ) VALUES (
            v_extraction_id,
            'gap_insurance_premium',
            '1250.00',
            '1350.00',
            'OCR error - verified manually in source document on page 3',
            v_user_id
        );
    END IF;
END $$;

-- =============================================================================
-- SAMPLE AUDIT EVENTS (For Testing Audit Trail)
-- =============================================================================

DO $$
DECLARE
    v_user_id UUID;
    v_contract_id VARCHAR(100) := 'GAP-2024-001001';
    v_extraction_id UUID;
    v_session_id UUID;
BEGIN
    -- Get user and extraction IDs
    SELECT user_id INTO v_user_id FROM users WHERE username = 'jane.doe';
    SELECT extraction_id INTO v_extraction_id FROM extractions WHERE contract_id = v_contract_id;

    -- Create a sample session (auth tokens managed by external provider, not stored here)
    INSERT INTO sessions (user_id, ip_address, user_agent, expires_at)
    VALUES (
        v_user_id,
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        CURRENT_TIMESTAMP + INTERVAL '4 hours'
    )
    RETURNING session_id INTO v_session_id;

    -- Audit event: User searched for contract
    INSERT INTO audit_events (
        event_type,
        contract_id,
        user_id,
        event_data,
        ip_address,
        user_agent,
        session_id,
        duration_ms
    ) VALUES (
        'search',
        NULL,
        v_user_id,
        '{"query": "ACC-100001", "results_count": 1}',
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        v_session_id,
        234
    );

    -- Audit event: User viewed contract
    INSERT INTO audit_events (
        event_type,
        contract_id,
        extraction_id,
        user_id,
        event_data,
        ip_address,
        user_agent,
        session_id,
        duration_ms
    ) VALUES (
        'view',
        v_contract_id,
        v_extraction_id,
        v_user_id,
        '{"source": "search_results"}',
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        v_session_id,
        567
    );

    -- Audit event: AI extracted data
    INSERT INTO audit_events (
        event_type,
        contract_id,
        extraction_id,
        user_id,
        event_data,
        ip_address,
        user_agent,
        session_id,
        duration_ms,
        cost_usd
    ) VALUES (
        'extract',
        v_contract_id,
        v_extraction_id,
        v_user_id,
        '{"llm_provider": "openai", "model": "gpt-4-turbo-2024-04-09"}',
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        v_session_id,
        7234,
        0.012345
    );

    -- Audit event: User edited extracted data
    INSERT INTO audit_events (
        event_type,
        contract_id,
        extraction_id,
        user_id,
        event_data,
        ip_address,
        user_agent,
        session_id,
        duration_ms
    ) VALUES (
        'edit',
        v_contract_id,
        v_extraction_id,
        v_user_id,
        '{"field": "gap_insurance_premium", "old_value": "1250.00", "new_value": "1350.00", "reason": "OCR error"}',
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        v_session_id,
        123
    );

    -- Audit event: User approved extraction
    INSERT INTO audit_events (
        event_type,
        contract_id,
        extraction_id,
        user_id,
        event_data,
        ip_address,
        user_agent,
        session_id,
        duration_ms
    ) VALUES (
        'approve',
        v_contract_id,
        v_extraction_id,
        v_user_id,
        '{"corrections_made": 1}',
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        v_session_id,
        89
    );
END $$;

-- =============================================================================
-- SAMPLE CHAT MESSAGES (For Testing Chat Feature)
-- =============================================================================

DO $$
DECLARE
    v_user_id UUID;
    v_session_id UUID;
    v_contract_id VARCHAR(100) := 'GAP-2024-001001';
BEGIN
    -- Get user and session IDs
    SELECT user_id INTO v_user_id FROM users WHERE username = 'jane.doe';
    SELECT session_id INTO v_session_id FROM sessions WHERE user_id = v_user_id LIMIT 1;

    -- User message
    INSERT INTO chat_messages (
        session_id,
        contract_id,
        user_id,
        role,
        content
    ) VALUES (
        v_session_id,
        v_contract_id,
        v_user_id,
        'user',
        'What is the refund calculation method for this contract?'
    );

    -- Assistant response
    INSERT INTO chat_messages (
        session_id,
        contract_id,
        user_id,
        role,
        content,
        llm_provider,
        llm_model_version,
        prompt_tokens,
        completion_tokens,
        processing_time_ms,
        cost_usd
    ) VALUES (
        v_session_id,
        v_contract_id,
        v_user_id,
        'assistant',
        'Based on the contract analysis, the refund calculation method is Pro-Rata. This means that refunds are calculated proportionally based on the unused portion of the coverage period. The cancellation fee of $50.00 will be deducted from any refund amount.',
        'openai',
        'gpt-4-turbo-2024-04-09',
        150,
        85,
        2345,
        0.003456
    );
END $$;

-- =============================================================================
-- SAMPLE EXTRACTION METRICS (For Testing Dashboard)
-- =============================================================================

-- Metrics for past 7 days
INSERT INTO extraction_metrics (
    date,
    total_extractions,
    successful_extractions,
    failed_extractions,
    avg_processing_time_ms,
    avg_confidence_score,
    total_cost_usd,
    llm_provider
) VALUES
    (CURRENT_DATE - INTERVAL '6 days', 45, 42, 3, 7800, 87.5, 12.34, 'openai'),
    (CURRENT_DATE - INTERVAL '5 days', 52, 50, 2, 8100, 88.2, 14.56, 'openai'),
    (CURRENT_DATE - INTERVAL '4 days', 38, 36, 2, 7600, 86.8, 10.23, 'openai'),
    (CURRENT_DATE - INTERVAL '3 days', 61, 58, 3, 8300, 89.1, 16.78, 'openai'),
    (CURRENT_DATE - INTERVAL '2 days', 49, 47, 2, 7950, 87.9, 13.45, 'openai'),
    (CURRENT_DATE - INTERVAL '1 day', 55, 53, 2, 8050, 88.5, 15.12, 'openai'),
    (CURRENT_DATE, 12, 12, 0, 7900, 88.3, 3.45, 'openai')
ON CONFLICT (date, llm_provider) DO NOTHING;

-- =============================================================================
-- VERIFICATION QUERIES (Comment out after verifying)
-- =============================================================================

-- Verify users created
-- SELECT username, email, role, is_active FROM users ORDER BY role DESC, username;

-- Verify contracts created
-- SELECT contract_id, account_number, contract_type FROM contracts ORDER BY contract_id;

-- Verify extractions created
-- SELECT contract_id, status, gap_insurance_premium, refund_calculation_method, cancellation_fee FROM extractions ORDER BY extracted_at DESC;

-- Verify audit events created
-- SELECT event_type, contract_id, timestamp FROM audit_events ORDER BY timestamp DESC LIMIT 10;

-- Verify system config
-- SELECT config_key, config_value, value_type, description FROM system_config ORDER BY config_key;

-- =============================================================================
-- END OF SEED DATA
-- =============================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Seed data successfully loaded!';
    RAISE NOTICE 'Sample users created with mock auth provider IDs';
    RAISE NOTICE 'Authentication is handled by external provider (Auth0, Okta, AWS Cognito, etc.)';
    RAISE NOTICE 'Configure your auth provider to match the sample emails: admin@company.com, jane.doe@company.com';
END $$;
