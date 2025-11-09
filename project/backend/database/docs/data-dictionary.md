# Data Dictionary
## Contract Refund Eligibility System

**Version:** 1.0
**Date:** 2025-11-06
**Database:** PostgreSQL 15.x

---

## Table of Contents

1. [users](#table-users)
2. [sessions](#table-sessions)
3. [contracts](#table-contracts)
4. [extractions](#table-extractions)
5. [corrections](#table-corrections)
6. [audit_events](#table-audit_events)
7. [system_config](#table-system_config)
8. [chat_messages](#table-chat_messages)
9. [extraction_metrics](#table-extraction_metrics)

---

## Table: users

**Description:** User profiles with authorization roles (authentication via external provider)

**Purpose:** Store user profile data and application-specific authorization (authentication handled externally)

**Authentication:** External provider (Auth0, Okta, AWS Cognito, etc.)

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| user_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique internal identifier for user | `<uuid>` |
| **External Auth Provider Fields** |
| auth_provider | VARCHAR(50) | NOT NULL | External authentication provider | `auth0`, `okta`, `cognito` |
| auth_provider_user_id | VARCHAR(255) | UNIQUE, NOT NULL | Unique user ID from auth provider (sub claim from JWT) | `auth0\|507f1f77bcf86cd799439011` |
| **User Profile Fields** |
| email | VARCHAR(255) | UNIQUE, NOT NULL, CHECK email format | User's email address (from auth provider) | `john.doe@company.com` |
| username | VARCHAR(100) | NULL | Username (from auth provider) | `john.doe` |
| first_name | VARCHAR(100) | NULL | User's first name (from auth provider) | `John` |
| last_name | VARCHAR(100) | NULL | User's last name (from auth provider) | `Doe` |
| **Application Authorization** |
| role | VARCHAR(20) | NOT NULL, CHECK IN ('admin', 'user') | Application role for access control | `user` or `admin` |
| is_active | BOOLEAN | DEFAULT true | Account active status | `true` |
| **Timestamps** |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp | `2025-11-06 10:30:00-05` |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Last profile update timestamp | `2025-11-06 15:45:00-05` |
| last_login_at | TIMESTAMP WITH TIME ZONE | NULL | Last successful login timestamp | `2025-11-06 09:00:00-05` |

**Indexes:**
- `idx_users_email` on `email`
- `idx_users_auth_provider_user_id` on `auth_provider_user_id`
- `idx_users_is_active` on `is_active`

**Triggers:**
- `update_users_updated_at` - Auto-updates `updated_at` on row modification

**Business Rules:**
- Authentication is handled entirely by external provider
- No passwords stored in database
- User record created on first login via auth provider callback
- `auth_provider_user_id` must match the `sub` claim from JWT
- Email updates should sync from auth provider

---

## Table: sessions

**Description:** Active user sessions for audit trail (auth tokens managed by external provider)

**Purpose:** Track session metadata for audit trail and user context (authentication handled by external provider)

**Note:** Authentication tokens (JWT) are not stored in database. They are managed by external auth provider and validated on each request.

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| session_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique session identifier | `<uuid>` |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(user_id) | User who owns this session | `<user-uuid>` |
| **Session Metadata** |
| ip_address | INET | NULL | Client IP address | `192.168.1.100` |
| user_agent | TEXT | NULL | Client browser/device info | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)...` |
| **Timestamps** |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Session start time | `2025-11-06 10:30:00-05` |
| last_activity | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Last request timestamp | `2025-11-06 11:15:00-05` |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | Session expiration time | `2025-11-06 14:30:00-05` |
| is_active | BOOLEAN | DEFAULT true | Session active status | `true` |

**Indexes:**
- `idx_sessions_user_id` on `user_id`
- `idx_sessions_expires_at` on `expires_at`
- `idx_sessions_is_active` on `is_active`

**Business Rules:**
- Sessions expire after 4 hours of inactivity (configurable)
- Inactive sessions are cleaned up by `cleanup_expired_sessions()` function
- Auth tokens (JWT) managed by external provider (not stored here)
- Session records used for audit trail and user activity tracking

---

## Table: contracts

**Description:** Contract metadata synced from external relational database

**Purpose:** Store contract references and metadata for lookup

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| contract_id | VARCHAR(100) | PRIMARY KEY | Unique contract identifier from external system | `GAP-2024-001234` |
| account_number | VARCHAR(100) | NOT NULL | Customer account number | `ACC-789456` |
| pdf_url | TEXT | NOT NULL, CHECK not empty | URL to PDF in document repository | `https://docs.example.com/contracts/GAP-2024-001234.pdf` |
| document_repository_id | VARCHAR(100) | NULL | ID in document repository system | `DOC-REP-456789` |
| contract_type | VARCHAR(50) | DEFAULT 'GAP' | Type of contract | `GAP`, `VSC`, `F&I` |
| contract_date | DATE | NULL | Contract effective date | `2024-03-15` |
| customer_name | VARCHAR(255) | NULL | Customer name (non-PII) | `Customer #789456` |
| vehicle_info | JSONB | NULL | Vehicle details (flexible schema) | `{"make": "Toyota", "model": "Camry", "year": 2023}` |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp | `2025-11-06 10:30:00-05` |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Record update timestamp | `2025-11-06 15:45:00-05` |
| last_synced_at | TIMESTAMP WITH TIME ZONE | NULL | Last sync from external RDB | `2025-11-06 02:00:00-05` |

**Indexes:**
- `idx_contracts_account_number` on `account_number` (most common lookup)
- `idx_contracts_contract_type` on `contract_type`
- `idx_contracts_last_synced_at` on `last_synced_at`
- `idx_contracts_contract_date` on `contract_date`

**Triggers:**
- `update_contracts_updated_at` - Auto-updates `updated_at` on row modification

**Business Rules:**
- Synced nightly from external relational database via batch job
- Uses upsert pattern (INSERT ON CONFLICT UPDATE) for idempotency

---

## Table: extractions

**Description:** AI-extracted data from contracts with confidence scores

**Purpose:** Store LLM extraction results, track status, and enable human review

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| extraction_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique extraction identifier | `<uuid>` |
| contract_id | VARCHAR(100) | NOT NULL, UNIQUE, FOREIGN KEY → contracts(contract_id) | Contract being extracted | `GAP-2024-001234` |
| **Gap Insurance Premium Fields** |
| gap_insurance_premium | DECIMAL(10,2) | NULL | Extracted GAP insurance premium amount | `1250.00` |
| gap_premium_confidence | DECIMAL(5,2) | NULL, CHECK 0-100 | AI confidence score (0-100) | `95.5` |
| gap_premium_source | JSONB | NULL | Source location in document | `{"page": 3, "section": "Coverage Details", "line": 12}` |
| **Refund Method Fields** |
| refund_calculation_method | VARCHAR(100) | NULL | Extracted refund calculation method | `Pro-Rata` |
| refund_method_confidence | DECIMAL(5,2) | NULL, CHECK 0-100 | AI confidence score (0-100) | `88.3` |
| refund_method_source | JSONB | NULL | Source location in document | `{"page": 5, "section": "Cancellation Terms"}` |
| **Cancellation Fee Fields** |
| cancellation_fee | DECIMAL(10,2) | NULL | Extracted cancellation fee amount | `50.00` |
| cancellation_fee_confidence | DECIMAL(5,2) | NULL, CHECK 0-100 | AI confidence score (0-100) | `92.1` |
| cancellation_fee_source | JSONB | NULL | Source location in document | `{"page": 5, "section": "Fees", "line": 8}` |
| **LLM Metadata** |
| llm_model_version | VARCHAR(100) | NOT NULL | LLM model used for extraction | `gpt-4-turbo-2024-04-09` |
| llm_provider | VARCHAR(50) | NULL | LLM provider name | `openai`, `anthropic`, `bedrock` |
| processing_time_ms | INTEGER | NULL, CHECK >= 0 | Extraction processing time (ms) | `8234` |
| prompt_tokens | INTEGER | NULL | Number of tokens in prompt | `3500` |
| completion_tokens | INTEGER | NULL | Number of tokens in completion | `450` |
| total_cost_usd | DECIMAL(10,6) | NULL | Total API cost in USD | `0.015234` |
| **Status & Approval** |
| status | VARCHAR(20) | DEFAULT 'pending', CHECK IN ('pending', 'approved', 'rejected') | Extraction status | `pending` |
| extracted_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Extraction timestamp | `2025-11-06 10:35:00-05` |
| extracted_by | UUID | NULL, FOREIGN KEY → users(user_id) | User who initiated extraction | `<user-uuid>` |
| approved_at | TIMESTAMP WITH TIME ZONE | NULL | Approval timestamp | `2025-11-06 10:40:00-05` |
| approved_by | UUID | NULL, FOREIGN KEY → users(user_id) | User who approved | `<user-uuid>` |
| rejected_at | TIMESTAMP WITH TIME ZONE | NULL | Rejection timestamp | `2025-11-06 10:40:00-05` |
| rejected_by | UUID | NULL, FOREIGN KEY → users(user_id) | User who rejected | `<user-uuid>` |
| rejection_reason | TEXT | NULL | Reason for rejection | `Incorrect contract type - not GAP insurance` |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Last update timestamp | `2025-11-06 10:45:00-05` |

**Indexes:**
- `idx_extractions_contract_id` on `contract_id`
- `idx_extractions_status` on `status`
- `idx_extractions_extracted_at` on `extracted_at`
- `idx_extractions_extracted_by` on `extracted_by`
- `idx_extractions_llm_provider` on `llm_provider`

**Constraints:**
- `unique_contract_extraction` - Only one extraction per contract (enforces idempotency)

**Triggers:**
- `update_extractions_updated_at` - Auto-updates `updated_at` on row modification

**Business Rules:**
- Only one extraction per contract (UNIQUE constraint)
- Confidence scores range from 0 to 100
- Source locations stored as flexible JSONB for future extensibility

---

## Table: corrections

**Description:** Human corrections to AI extractions for tracking accuracy

**Purpose:** Track when humans correct AI errors, improve future models

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| correction_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique correction identifier | `<uuid>` |
| extraction_id | UUID | NOT NULL, FOREIGN KEY → extractions(extraction_id) | Extraction being corrected | `<extraction-uuid>` |
| field_name | VARCHAR(50) | NOT NULL, CHECK IN ('gap_insurance_premium', 'refund_calculation_method', 'cancellation_fee') | Field being corrected | `gap_insurance_premium` |
| original_value | TEXT | NULL | AI's original extracted value | `1250.00` |
| corrected_value | TEXT | NOT NULL, CHECK not empty | Human-corrected value | `1350.00` |
| correction_reason | TEXT | NULL | Optional reason for correction | `OCR error, verified manually in document` |
| corrected_by | UUID | NOT NULL, FOREIGN KEY → users(user_id) | User who made correction | `<user-uuid>` |
| corrected_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Correction timestamp | `2025-11-06 10:38:00-05` |

**Indexes:**
- `idx_corrections_extraction_id` on `extraction_id`
- `idx_corrections_field_name` on `field_name`
- `idx_corrections_corrected_by` on `corrected_by`
- `idx_corrections_corrected_at` on `corrected_at`

**Business Rules:**
- Each field can be corrected multiple times (tracks correction history)
- Original value preserved for accuracy analysis
- Used to calculate AI extraction accuracy metrics

---

## Table: audit_events

**Description:** Immutable event log for compliance and audit trail

**Purpose:** Event sourcing, compliance, security monitoring, and forensic analysis

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| event_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique event identifier | `<uuid>` |
| event_type | VARCHAR(50) | NOT NULL, CHECK IN (see list below) | Type of event | `search`, `approve`, `chat` |
| contract_id | VARCHAR(100) | NULL, FOREIGN KEY → contracts(contract_id) | Contract involved in event | `GAP-2024-001234` |
| extraction_id | UUID | NULL, FOREIGN KEY → extractions(extraction_id) | Extraction involved in event | `<extraction-uuid>` |
| user_id | UUID | NULL, FOREIGN KEY → users(user_id) | User who triggered event | `<user-uuid>` |
| event_data | JSONB | NULL | Flexible event-specific data | `{"query": "ACC-789456", "results_count": 1}` |
| timestamp | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Event occurrence time | `2025-11-06 10:30:15-05` |
| ip_address | INET | NULL | Client IP address | `192.168.1.100` |
| user_agent | TEXT | NULL | Client browser/device info | `Mozilla/5.0...` |
| session_id | UUID | NULL, FOREIGN KEY → sessions(session_id) | Session associated with event | `<session-uuid>` |
| duration_ms | INTEGER | NULL | Event duration (for performance tracking) | `1234` |
| cost_usd | DECIMAL(10,6) | NULL | Event cost (for LLM calls) | `0.015234` |

**Event Types:**
- `search` - User searches for contract by account number
- `view` - User views contract details
- `extract` - AI extracts data from contract
- `edit` - User edits extracted data
- `approve` - User approves extraction
- `reject` - User rejects extraction
- `chat` - User interacts with AI chat
- `login` - User logs in
- `logout` - User logs out
- `user_created` - Admin creates new user
- `user_updated` - Admin updates user details
- `user_deleted` - Admin deactivates user

**Indexes:**
- `idx_audit_events_contract_id` on `contract_id`
- `idx_audit_events_extraction_id` on `extraction_id`
- `idx_audit_events_user_id` on `user_id`
- `idx_audit_events_timestamp` on `timestamp`
- `idx_audit_events_event_type` on `event_type`
- `idx_audit_events_session_id` on `session_id`
- `idx_audit_events_recent` on `timestamp DESC` (partial, last 30 days)

**Triggers:**
- `prevent_audit_events_update` - Prevents UPDATE on audit_events (immutable)
- `prevent_audit_events_delete` - Prevents DELETE on audit_events (immutable)

**Business Rules:**
- **Immutable:** Cannot be updated or deleted once created
- **7-year retention:** Minimum retention for regulatory compliance
- **Event Sourcing:** Complete audit trail of all system actions
- **Partitioning:** Consider monthly partitioning after 6 months

---

## Table: system_config

**Description:** Application configuration settings

**Purpose:** Store runtime configuration, feature flags, and system parameters

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| config_key | VARCHAR(100) | PRIMARY KEY | Configuration key | `confidence_threshold` |
| config_value | TEXT | NOT NULL | Configuration value | `80` |
| value_type | VARCHAR(20) | CHECK IN ('string', 'number', 'boolean', 'json') | Value data type | `number` |
| description | TEXT | NULL | Configuration description | `Minimum confidence score to auto-approve` |
| is_secret | BOOLEAN | DEFAULT false | Whether value contains sensitive data | `false` |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Config creation time | `2025-11-06 10:00:00-05` |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Config last update time | `2025-11-06 12:30:00-05` |
| updated_by | UUID | NULL, FOREIGN KEY → users(user_id) | User who last updated config | `<user-uuid>` |

**Triggers:**
- `update_system_config_updated_at` - Auto-updates `updated_at` on row modification

**Example Configuration Keys:**
- `confidence_threshold` - Minimum confidence for extraction (default: 80)
- `session_timeout_hours` - Session timeout in hours (default: 4)
- `llm_default_provider` - Default LLM provider (openai, anthropic, bedrock)
- `cache_ttl_minutes` - Cache TTL in minutes (default: 30)
- `max_retries` - Max LLM API retries (default: 3)

---

## Table: chat_messages

**Description:** AI chat conversation history

**Purpose:** Store chat interactions for context and audit purposes

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| message_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique message identifier | `<uuid>` |
| session_id | UUID | NULL, FOREIGN KEY → sessions(session_id) | Chat session identifier | `<session-uuid>` |
| contract_id | VARCHAR(100) | NULL, FOREIGN KEY → contracts(contract_id) | Contract being discussed | `GAP-2024-001234` |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(user_id) | User involved in chat | `<user-uuid>` |
| role | VARCHAR(20) | NOT NULL, CHECK IN ('user', 'assistant', 'system') | Message sender role | `user` or `assistant` |
| content | TEXT | NOT NULL, CHECK not empty | Message content | `What is the refund policy?` |
| llm_provider | VARCHAR(50) | NULL | LLM provider (for assistant messages) | `openai` |
| llm_model_version | VARCHAR(100) | NULL | LLM model version | `gpt-4-turbo-2024-04-09` |
| prompt_tokens | INTEGER | NULL | Tokens in prompt | `150` |
| completion_tokens | INTEGER | NULL | Tokens in completion | `80` |
| processing_time_ms | INTEGER | NULL | Response generation time | `2345` |
| cost_usd | DECIMAL(10,6) | NULL | API call cost | `0.003456` |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Message timestamp | `2025-11-06 10:35:00-05` |

**Indexes:**
- `idx_chat_messages_session_id` on `session_id`
- `idx_chat_messages_contract_id` on `contract_id`
- `idx_chat_messages_user_id` on `user_id`
- `idx_chat_messages_created_at` on `created_at`

**Business Rules:**
- Messages grouped by session for conversation context
- User messages have `role='user'`
- AI responses have `role='assistant'`
- System messages have `role='system'` (e.g., context switches)

---

## Table: extraction_metrics

**Description:** Daily aggregated metrics for AI extraction performance

**Purpose:** Track AI performance over time, identify trends, optimize models

| Column | Data Type | Constraints | Description | Example |
|--------|-----------|-------------|-------------|---------|
| metric_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique metric identifier | `<uuid>` |
| date | DATE | NOT NULL | Metric date | `2025-11-06` |
| total_extractions | INTEGER | DEFAULT 0 | Total extractions attempted | `125` |
| successful_extractions | INTEGER | DEFAULT 0 | Successful extractions | `118` |
| failed_extractions | INTEGER | DEFAULT 0 | Failed extractions | `7` |
| avg_processing_time_ms | INTEGER | NULL | Average processing time | `8234` |
| avg_confidence_score | DECIMAL(5,2) | NULL | Average confidence across all fields | `87.5` |
| total_cost_usd | DECIMAL(10,2) | NULL | Total LLM API cost | `15.67` |
| llm_provider | VARCHAR(50) | NULL | LLM provider | `openai` |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Metric creation time | `2025-11-07 00:05:00-05` |

**Indexes:**
- `idx_extraction_metrics_date` on `date`
- `idx_extraction_metrics_llm_provider` on `llm_provider`

**Constraints:**
- `unique_daily_metrics` - One row per (date, llm_provider) combination

**Business Rules:**
- Aggregated daily by automated job (runs at midnight)
- Used for performance dashboards and analytics
- Helps identify model drift and accuracy trends

---

## Views

### v_extraction_details

**Purpose:** Complete extraction information with user details

**Columns:**
- All extraction fields
- Account number and contract type
- Extracted by username/email
- Approved by username/email
- Has corrections flag

### v_user_activity

**Purpose:** Aggregated user statistics

**Columns:**
- User info (id, username, email, role)
- Total extractions, approved extractions
- Total corrections made
- Total audit events triggered

### v_daily_extraction_stats

**Purpose:** Daily performance metrics

**Columns:**
- Extraction date
- Total/approved/rejected/pending counts
- Average processing time
- Average confidence score
- Total cost

---

## Functions

### calculate_extraction_accuracy(p_extraction_id UUID)

**Purpose:** Calculate extraction accuracy by comparing with corrections

**Returns:** Table with field name, was_corrected flag, original and corrected values

### cleanup_expired_sessions()

**Purpose:** Delete expired sessions from database

**Returns:** Count of deleted sessions

---

## Data Types Reference

| Type | Description | Example |
|------|-------------|---------|
| UUID | Universally Unique Identifier | `<uuid>` |
| VARCHAR(n) | Variable-length string (max n chars) | `john.doe` |
| TEXT | Unlimited-length string | `Long description...` |
| DECIMAL(p,s) | Fixed-point number (p digits, s decimal) | `1250.00` |
| INTEGER | 32-bit integer | `12345` |
| BOOLEAN | True/false value | `true` |
| DATE | Calendar date | `2025-11-06` |
| TIMESTAMP WITH TIME ZONE | Timestamp with timezone | `2025-11-06 10:30:00-05` |
| INET | IPv4 or IPv6 address | `192.168.1.100` |
| JSONB | Binary JSON (indexed, efficient) | `{"key": "value"}` |

---

## Naming Conventions

- **Tables:** Lowercase, plural nouns (`users`, `contracts`)
- **Columns:** Lowercase, snake_case (`created_at`, `gap_premium_confidence`)
- **Primary Keys:** `{table_singular}_id` (`user_id`, `extraction_id`)
- **Foreign Keys:** Same name as referenced primary key
- **Indexes:** `idx_{table}_{columns}` (`idx_users_email`)
- **Constraints:** `{table}_{constraint_type}` or descriptive name
- **Triggers:** `{action}_{table}_{description}`

---

**End of Data Dictionary**
