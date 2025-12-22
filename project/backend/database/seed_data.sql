-- =============================================================================
-- Contract Refund Eligibility System - Seed Data
-- =============================================================================
-- Version: 1.0
-- Date: 2025-12-22
-- Purpose: Seed jurisdictions and initial state validation rules
-- =============================================================================

-- =============================================================================
-- JURISDICTIONS (50 US States + Federal Default)
-- =============================================================================

INSERT INTO jurisdictions (jurisdiction_id, jurisdiction_name, country_code, state_code, is_active) VALUES
-- Federal default (no specific state)
('US-FEDERAL', 'Federal (Default)', 'US', NULL, true),

-- All 50 US states (alphabetical by state code)
('US-AL', 'Alabama', 'US', 'AL', true),
('US-AK', 'Alaska', 'US', 'AK', true),
('US-AZ', 'Arizona', 'US', 'AZ', true),
('US-AR', 'Arkansas', 'US', 'AR', true),
('US-CA', 'California', 'US', 'CA', true),
('US-CO', 'Colorado', 'US', 'CO', true),
('US-CT', 'Connecticut', 'US', 'CT', true),
('US-DE', 'Delaware', 'US', 'DE', true),
('US-FL', 'Florida', 'US', 'FL', true),
('US-GA', 'Georgia', 'US', 'GA', true),
('US-HI', 'Hawaii', 'US', 'HI', true),
('US-ID', 'Idaho', 'US', 'ID', true),
('US-IL', 'Illinois', 'US', 'IL', true),
('US-IN', 'Indiana', 'US', 'IN', true),
('US-IA', 'Iowa', 'US', 'IA', true),
('US-KS', 'Kansas', 'US', 'KS', true),
('US-KY', 'Kentucky', 'US', 'KY', true),
('US-LA', 'Louisiana', 'US', 'LA', true),
('US-ME', 'Maine', 'US', 'ME', true),
('US-MD', 'Maryland', 'US', 'MD', true),
('US-MA', 'Massachusetts', 'US', 'MA', true),
('US-MI', 'Michigan', 'US', 'MI', true),
('US-MN', 'Minnesota', 'US', 'MN', true),
('US-MS', 'Mississippi', 'US', 'MS', true),
('US-MO', 'Missouri', 'US', 'MO', true),
('US-MT', 'Montana', 'US', 'MT', true),
('US-NE', 'Nebraska', 'US', 'NE', true),
('US-NV', 'Nevada', 'US', 'NV', true),
('US-NH', 'New Hampshire', 'US', 'NH', true),
('US-NJ', 'New Jersey', 'US', 'NJ', true),
('US-NM', 'New Mexico', 'US', 'NM', true),
('US-NY', 'New York', 'US', 'NY', true),
('US-NC', 'North Carolina', 'US', 'NC', true),
('US-ND', 'North Dakota', 'US', 'ND', true),
('US-OH', 'Ohio', 'US', 'OH', true),
('US-OK', 'Oklahoma', 'US', 'OK', true),
('US-OR', 'Oregon', 'US', 'OR', true),
('US-PA', 'Pennsylvania', 'US', 'PA', true),
('US-RI', 'Rhode Island', 'US', 'RI', true),
('US-SC', 'South Carolina', 'US', 'SC', true),
('US-SD', 'South Dakota', 'US', 'SD', true),
('US-TN', 'Tennessee', 'US', 'TN', true),
('US-TX', 'Texas', 'US', 'TX', true),
('US-UT', 'Utah', 'US', 'UT', true),
('US-VT', 'Vermont', 'US', 'VT', true),
('US-VA', 'Virginia', 'US', 'VA', true),
('US-WA', 'Washington', 'US', 'WA', true),
('US-WV', 'West Virginia', 'US', 'WV', true),
('US-WI', 'Wisconsin', 'US', 'WI', true),
('US-WY', 'Wyoming', 'US', 'WY', true);

-- =============================================================================
-- FEDERAL DEFAULT VALIDATION RULES
-- =============================================================================
-- These rules represent the baseline validation when no state-specific rule exists
-- Migrated from hardcoded RuleValidator logic

INSERT INTO state_validation_rules (jurisdiction_id, rule_category, rule_config, effective_date, is_active, rule_description) VALUES
-- Federal GAP Insurance Premium validation
('US-FEDERAL', 'gap_premium',
 '{
   "min": 100,
   "max": 2000,
   "strict": false
 }'::jsonb,
 '2024-01-01', true,
 'Default GAP premium range for federal baseline - allows $100 to $2000'),

-- Federal Cancellation Fee validation
('US-FEDERAL', 'cancellation_fee',
 '{
   "min": 0,
   "max": 100,
   "strict": false
 }'::jsonb,
 '2024-01-01', true,
 'Default cancellation fee range for federal baseline - allows $0 to $100'),

-- Federal Refund Calculation Method validation
('US-FEDERAL', 'refund_method',
 '{
   "allowed_values": [
     "pro-rata",
     "pro rata",
     "prorata",
     "rule of 78s",
     "rule of 78''s",
     "actuarial",
     "flat",
     "none"
   ]
 }'::jsonb,
 '2024-01-01', true,
 'Recognized refund calculation methods for federal baseline - all common methods allowed');

-- =============================================================================
-- STATE-SPECIFIC VALIDATION RULES
-- =============================================================================
-- Initial state rules for California, New York, and Texas

-- -----------------------------------------------------------------------------
-- CALIFORNIA RULES (Stricter than federal)
-- -----------------------------------------------------------------------------

-- California GAP Premium: $200-$1500 (stricter than federal $100-$2000)
INSERT INTO state_validation_rules (jurisdiction_id, rule_category, rule_config, effective_date, is_active, rule_description) VALUES
('US-CA', 'gap_premium',
 '{
   "min": 200,
   "max": 1500,
   "strict": true,
   "disclosure_required": true,
   "reason": "California Insurance Code §1758.7"
 }'::jsonb,
 '2024-01-01', true,
 'California GAP premium requirements - stricter than federal baseline, requires disclosure');

-- California Cancellation Fee: $0-$75 (stricter than federal $0-$100)
INSERT INTO state_validation_rules (jurisdiction_id, rule_category, rule_config, effective_date, is_active, rule_description) VALUES
('US-CA', 'cancellation_fee',
 '{
   "min": 0,
   "max": 75,
   "strict": false,
   "warning_threshold": 50,
   "reason": "California regulatory guidance"
 }'::jsonb,
 '2024-01-01', true,
 'California cancellation fee limits - max $75, warn above $50');

-- -----------------------------------------------------------------------------
-- NEW YORK RULES (Prohibits Rule of 78s)
-- -----------------------------------------------------------------------------

-- New York Refund Method: Pro-rata only, Rule of 78s prohibited
INSERT INTO state_validation_rules (jurisdiction_id, rule_category, rule_config, effective_date, is_active, rule_description) VALUES
('US-NY', 'refund_method',
 '{
   "allowed_values": [
     "pro-rata",
     "prorata",
     "pro rata"
   ],
   "prohibited_values": [
     "rule of 78s",
     "rule of 78''s"
   ],
   "strict": true,
   "reason": "NY Insurance Law §3426 - Rule of 78s prohibited"
 }'::jsonb,
 '2024-01-01', true,
 'New York refund method restrictions - only pro-rata allowed, Rule of 78s explicitly prohibited');

-- -----------------------------------------------------------------------------
-- TEXAS RULES
-- -----------------------------------------------------------------------------

-- Texas Cancellation Fee: $0-$75
INSERT INTO state_validation_rules (jurisdiction_id, rule_category, rule_config, effective_date, is_active, rule_description) VALUES
('US-TX', 'cancellation_fee',
 '{
   "min": 0,
   "max": 75,
   "strict": false,
   "warning_threshold": 50
 }'::jsonb,
 '2024-01-01', true,
 'Texas cancellation fee limits - max $75, warn above $50');

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Uncomment to verify seed data after import

-- -- Count jurisdictions (should be 51: 50 states + 1 federal)
-- SELECT COUNT(*) AS jurisdiction_count FROM jurisdictions;
--
-- -- List all jurisdictions
-- SELECT jurisdiction_id, jurisdiction_name, state_code FROM jurisdictions ORDER BY state_code;
--
-- -- Count validation rules (should be at least 6: 3 federal + 3 state-specific)
-- SELECT COUNT(*) AS rule_count FROM state_validation_rules;
--
-- -- List all validation rules by jurisdiction
-- SELECT
--     j.jurisdiction_name,
--     svr.rule_category,
--     svr.is_active,
--     svr.rule_description
-- FROM state_validation_rules svr
-- JOIN jurisdictions j ON svr.jurisdiction_id = j.jurisdiction_id
-- ORDER BY j.jurisdiction_name, svr.rule_category;

-- =============================================================================
-- END OF SEED DATA
-- =============================================================================
