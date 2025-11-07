# Entity Relationship Diagram
## Contract Refund Eligibility System

This document contains the ER diagram for the database schema.

## Diagram

```mermaid
erDiagram
    users ||--o{ sessions : "has"
    users ||--o{ extractions : "creates"
    users ||--o{ corrections : "makes"
    users ||--o{ audit_events : "triggers"
    users ||--o{ chat_messages : "sends"
    users ||--o{ system_config : "updates"

    contracts ||--|| extractions : "has"
    contracts ||--o{ audit_events : "tracked_in"
    contracts ||--o{ chat_messages : "discusses"

    extractions ||--o{ corrections : "has"
    extractions ||--o{ audit_events : "tracked_in"

    sessions ||--o{ audit_events : "tracked_in"
    sessions ||--o{ chat_messages : "contains"

    users {
        uuid user_id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        varchar role "admin or user"
        varchar first_name
        varchar last_name
        timestamp created_at
        timestamp updated_at
        timestamp last_login_at
        boolean is_active
    }

    sessions {
        uuid session_id PK
        uuid user_id FK
        text jwt_token
        uuid refresh_token
        inet ip_address
        text user_agent
        timestamp expires_at
        timestamp created_at
        timestamp last_activity
        boolean is_active
    }

    contracts {
        varchar contract_id PK
        varchar account_number
        text pdf_url
        varchar document_repository_id
        varchar contract_type
        date contract_date
        varchar customer_name
        jsonb vehicle_info
        timestamp created_at
        timestamp updated_at
        timestamp last_synced_at
    }

    extractions {
        uuid extraction_id PK
        varchar contract_id FK
        decimal gap_insurance_premium
        decimal gap_premium_confidence
        jsonb gap_premium_source
        varchar refund_calculation_method
        decimal refund_method_confidence
        jsonb refund_method_source
        decimal cancellation_fee
        decimal cancellation_fee_confidence
        jsonb cancellation_fee_source
        varchar llm_model_version
        varchar llm_provider
        integer processing_time_ms
        integer prompt_tokens
        integer completion_tokens
        decimal total_cost_usd
        varchar status "pending, approved, rejected"
        timestamp extracted_at
        uuid extracted_by FK
        timestamp approved_at
        uuid approved_by FK
        timestamp rejected_at
        uuid rejected_by FK
        text rejection_reason
        timestamp updated_at
    }

    corrections {
        uuid correction_id PK
        uuid extraction_id FK
        varchar field_name "gap_insurance_premium, refund_calculation_method, cancellation_fee"
        text original_value
        text corrected_value
        text correction_reason
        uuid corrected_by FK
        timestamp corrected_at
    }

    audit_events {
        uuid event_id PK
        varchar event_type "search, view, extract, edit, approve, reject, chat, login, logout"
        varchar contract_id FK
        uuid extraction_id FK
        uuid user_id FK
        jsonb event_data
        timestamp timestamp
        inet ip_address
        text user_agent
        uuid session_id FK
        integer duration_ms
        decimal cost_usd
    }

    system_config {
        varchar config_key PK
        text config_value
        varchar value_type "string, number, boolean, json"
        text description
        boolean is_secret
        timestamp created_at
        timestamp updated_at
        uuid updated_by FK
    }

    chat_messages {
        uuid message_id PK
        uuid session_id FK
        varchar contract_id FK
        uuid user_id FK
        varchar role "user, assistant, system"
        text content
        varchar llm_provider
        varchar llm_model_version
        integer prompt_tokens
        integer completion_tokens
        integer processing_time_ms
        decimal cost_usd
        timestamp created_at
    }

    extraction_metrics {
        uuid metric_id PK
        date date
        integer total_extractions
        integer successful_extractions
        integer failed_extractions
        integer avg_processing_time_ms
        decimal avg_confidence_score
        decimal total_cost_usd
        varchar llm_provider
        timestamp created_at
    }
```

## Key Relationships

### 1. Users → Extractions (One-to-Many)
- A user can create multiple extractions
- Each extraction is created by one user
- Tracks who extracted the data from contracts

### 2. Users → Corrections (One-to-Many)
- A user can make multiple corrections
- Each correction is made by one user
- Tracks who corrected AI extraction errors

### 3. Contracts → Extractions (One-to-One)
- Each contract has exactly one extraction record
- Ensures no duplicate processing of the same contract
- Enforced by UNIQUE constraint on contract_id

### 4. Extractions → Corrections (One-to-Many)
- An extraction can have multiple corrections (one per field)
- Each correction belongs to one extraction
- Tracks all human corrections to AI data

### 5. Users → Sessions (One-to-Many)
- A user can have multiple active sessions (different devices)
- Each session belongs to one user
- Supports session management and JWT tokens

### 6. Users → Audit Events (One-to-Many)
- A user triggers many audit events
- Each event is associated with one user
- Immutable audit trail for compliance

### 7. Contracts → Audit Events (One-to-Many)
- A contract is referenced in multiple audit events
- Tracks all actions performed on a contract
- Complete history of contract interactions

### 8. Sessions → Chat Messages (One-to-Many)
- A session contains multiple chat messages
- Messages are grouped by session for context
- Supports conversation history

## Database Features

### Constraints
- **Primary Keys**: UUID for all entities (globally unique)
- **Foreign Keys**: Enforce referential integrity
- **Unique Constraints**: Prevent duplicate data (e.g., one extraction per contract)
- **Check Constraints**: Validate data ranges (e.g., confidence 0-100)

### Indexes
- **Single-column indexes**: Fast lookups on frequently queried columns
- **Partial indexes**: Optimized for common query patterns (e.g., recent events)
- **Composite indexes**: Support multi-column queries

### Triggers
- **updated_at triggers**: Auto-update timestamps on row changes
- **Immutability triggers**: Prevent modification of audit_events

### Views
- **v_extraction_details**: Complete extraction info with user details
- **v_user_activity**: Aggregated user statistics
- **v_daily_extraction_stats**: Daily performance metrics

## Data Flow

1. **User Login**
   - User authenticates → `users` table
   - Session created → `sessions` table
   - Login event logged → `audit_events` table

2. **Contract Search**
   - User searches by account number
   - System queries → `contracts` table
   - Search event logged → `audit_events` table

3. **AI Extraction**
   - LLM extracts data from PDF
   - Extraction stored → `extractions` table
   - Extract event logged → `audit_events` table

4. **Human Review**
   - User reviews extraction
   - If corrections needed → `corrections` table
   - Edit event logged → `audit_events` table

5. **Approval**
   - User approves extraction
   - Status updated → `extractions` table
   - Approve event logged → `audit_events` table

6. **Chat Interaction**
   - User asks question about contract
   - Messages stored → `chat_messages` table
   - Chat event logged → `audit_events` table

## Partitioning Strategy (Future)

After 6 months of operation, consider partitioning `audit_events` by month:
- Improves query performance on recent data
- Enables efficient archival of old data
- Supports 7-year retention requirement

## Backup and Retention

| Table | Retention | Backup Strategy |
|-------|-----------|-----------------|
| users | Indefinite | Daily incremental, weekly full |
| contracts | 7 years | Daily incremental, weekly full |
| extractions | 7 years | Daily incremental, weekly full |
| corrections | 7 years | Daily incremental, weekly full |
| audit_events | 7 years minimum | Daily incremental, monthly archive |
| sessions | 4 hours | Not backed up (ephemeral) |
| chat_messages | 1 year | Weekly full |
| extraction_metrics | 7 years | Monthly full |
