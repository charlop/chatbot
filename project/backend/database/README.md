# Database Documentation
## Contract Refund Eligibility System

**Version:** 1.0
**Database:** PostgreSQL 15.x
**Date:** 2025-11-06

---

## Overview

This directory contains all database-related files for the Contract Refund Eligibility System, including schema definitions, migration scripts, seed data, and documentation.

## Directory Structure

```
database/
├── README.md                    # This file
├── schema.sql                   # Complete database schema (DDL)
├── seed/
│   └── seed_data.sql           # Initial seed data for development
├── migrations/
│   └── README.md               # Migration instructions (Alembic)
└── docs/
    ├── ER-diagram.md           # Entity Relationship Diagram
    └── data-dictionary.md      # Complete data dictionary
```

---

## Quick Start

### 1. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE contract_refund_system;

# Connect to new database
\c contract_refund_system
```

### 2. Run Schema

```bash
# Execute schema file
psql -U postgres -d contract_refund_system -f schema.sql
```

### 3. Load Seed Data (Development Only)

```bash
# Execute seed data file
psql -U postgres -d contract_refund_system -f seed/seed_data.sql
```

**Important:** The seed data includes sample users with mock auth provider IDs:
- Admin: `admin@company.com`
- User: `jane.doe@company.com`

**Authentication is handled by external provider (Auth0, Okta, AWS Cognito, etc.)**
Configure your auth provider to match these sample emails for development/testing.

---

## Database Schema

### Core Tables

1. **users** - User profiles with authorization roles (authentication via external provider)
2. **sessions** - Session metadata for audit trail (auth tokens managed by external provider)
3. **contracts** - Contract metadata synced from external relational database
4. **extractions** - AI-extracted data from contracts with confidence scores
5. **corrections** - Human corrections to AI extractions for tracking accuracy
6. **audit_events** - Immutable event log for compliance and audit trail
7. **system_config** - Application configuration settings
8. **chat_messages** - AI chat conversation history
9. **extraction_metrics** - Daily aggregated metrics for AI extraction performance

### Views

- **v_extraction_details** - Complete extraction info with user details
- **v_user_activity** - Aggregated user statistics
- **v_daily_extraction_stats** - Daily performance metrics

### Functions

- **calculate_extraction_accuracy(p_extraction_id UUID)** - Calculate extraction accuracy
- **cleanup_expired_sessions()** - Delete expired sessions

---

## Key Features

### 1. Authentication & Authorization

**Authentication:** External provider (Auth0, Okta, AWS Cognito, etc.)
- No passwords stored in database
- JWT tokens validated on each request
- User profile synced from auth provider on first login

**Authorization (RBAC):** Two roles supported
- **Admin**: Full access including user management
- **User**: Can search, view, edit, and approve contracts

### 2. Event Sourcing & Audit Trail

The `audit_events` table is **immutable** (cannot be updated or deleted). Every system action is logged:
- User searches
- Contract views
- AI extractions
- Human edits
- Approvals/rejections
- Chat interactions
- User management actions

### 3. Confidence Scoring

Every extracted field includes:
- **Value**: The extracted data
- **Confidence Score**: 0-100 (AI's confidence level)
- **Source Location**: Page, section, line in document (JSONB)

### 4. Human-in-the-Loop

The `corrections` table tracks when humans correct AI errors:
- Original AI value preserved
- Corrected value stored
- Correction reason (optional)
- Used for AI accuracy metrics

### 5. LLM Vendor Abstraction

The schema supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- AWS Bedrock (Claude via Bedrock)

Tracked fields:
- `llm_provider` - Provider name
- `llm_model_version` - Specific model version
- `prompt_tokens`, `completion_tokens` - Token usage
- `total_cost_usd` - API cost tracking

---

## Data Retention

| Table | Retention Period | Notes |
|-------|------------------|-------|
| contracts | 7 years | Regulatory requirement |
| extractions | 7 years | Business records |
| corrections | 7 years | Accuracy tracking |
| audit_events | 7 years minimum | Compliance requirement |
| users | Indefinite | Active accounts |
| sessions | 4 hours | Auto-cleanup |
| chat_messages | 1 year | Optional longer retention |

---

## Performance Considerations

### Indexes

All frequently queried columns have indexes:
- Foreign keys
- Status fields
- Timestamp fields for time-range queries
- Account numbers (most common lookup)

### Partial Indexes

Recent audit events (last 30 days) have a partial index for faster queries:
```sql
CREATE INDEX idx_audit_events_recent ON audit_events(timestamp DESC)
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days';
```

### Future Optimization: Partitioning

After 6 months of operation, consider partitioning `audit_events` by month:
- Improves query performance on recent data
- Enables efficient archival of old data
- Supports 7-year retention requirement

See `schema.sql` for partitioning example (commented out).

---

## Backup Strategy

### Daily Incremental Backups
```bash
# Backup with pg_dump
pg_dump -U postgres -d contract_refund_system -F c -f backup_$(date +%Y%m%d).dump

# Restore from backup
pg_restore -U postgres -d contract_refund_system backup_20251106.dump
```

### Weekly Full Backups
```bash
# Full database backup
pg_dumpall -U postgres -f full_backup_$(date +%Y%m%d).sql
```

### Point-in-Time Recovery (PITR)

Enable WAL archiving in `postgresql.conf`:
```ini
wal_level = replica
archive_mode = on
archive_command = 'cp %p /path/to/archive/%f'
```

---

## Migrations (Alembic)

For version-controlled schema changes, use Alembic:

```bash
# Install Alembic
pip install alembic psycopg2-binary

# Initialize Alembic (one-time setup)
cd project/backend
alembic init alembic

# Create a new migration
alembic revision -m "Add new column to extractions"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

See `migrations/README.md` for detailed instructions.

---

## Testing

### Unit Tests

Test database operations with pytest:

```python
# tests/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine('postgresql://test:test@localhost/test_db')
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_user(db_session):
    user = User(username='test', email='test@test.com')
    db_session.add(user)
    db_session.commit()
    assert user.user_id is not None
```

### Integration Tests

Test complete workflows:
1. Search for contract
2. Extract data with LLM
3. User corrects extraction
4. User approves extraction
5. Verify audit trail

---

## Security Considerations

### 1. SQL Injection Prevention

- **Always use parameterized queries**
- Never concatenate user input into SQL strings
- Use ORM (SQLAlchemy) when possible

❌ **Bad:**
```python
query = f"SELECT * FROM users WHERE username = '{username}'"
```

✅ **Good:**
```python
query = "SELECT * FROM users WHERE username = %s"
cursor.execute(query, (username,))
```

### 2. Authentication Security

- **No passwords stored in database** - Authentication handled by external provider
- JWT tokens validated on each request against auth provider
- Use environment variables for database credentials and auth provider configuration
- Rotate auth provider client secrets regularly

### 3. Data Encryption

- **At rest**: RDS encryption enabled
- **In transit**: TLS 1.2+ for all connections
- **Secrets**: AWS Secrets Manager for credentials

### 4. Audit Trail Immutability

- Triggers prevent UPDATE and DELETE on `audit_events`
- Ensures compliance and forensic analysis capability

### 5. Least Privilege Access

```sql
-- Application user (read/write)
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
REVOKE DELETE ON audit_events FROM app_user;

-- Read-only user (reporting)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

---

## Monitoring

### Slow Query Monitoring

Enable slow query logging in `postgresql.conf`:
```ini
log_min_duration_statement = 1000  # Log queries taking > 1 second
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d '
```

### Database Metrics

Monitor these key metrics:
- Query performance (p95 latency)
- Connection pool usage
- Cache hit ratio
- Table bloat
- Index usage

### Alerts

Set up CloudWatch alarms for:
- Database CPU > 80%
- Disk space < 20% free
- Connection count > 80% of max
- Replication lag > 1 minute

---

## Troubleshooting

### Issue: Slow queries on audit_events

**Solution:** Ensure partial index is created and queries use timestamp filters:
```sql
SELECT * FROM audit_events
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### Issue: Session table growing too large

**Solution:** Run cleanup function regularly:
```sql
SELECT cleanup_expired_sessions();
```

Or set up a cron job:
```bash
# Clean up expired sessions daily at 2 AM
0 2 * * * psql -U postgres -d contract_refund_system -c "SELECT cleanup_expired_sessions();"
```

### Issue: Duplicate contract extractions

**Solution:** The UNIQUE constraint on `contract_id` prevents this. If you encounter an error, check for application-level race conditions.

---

## Documentation

- **ER Diagram**: See `docs/ER-diagram.md` (Mermaid format)
- **Data Dictionary**: See `docs/data-dictionary.md` (complete field descriptions)
- **Schema SQL**: See `schema.sql` (DDL with comments)
- **Seed Data**: See `seed/seed_data.sql` (sample data)

---

## Support

For questions or issues:
1. Check the data dictionary for table/column details
2. Review the ER diagram for relationships
3. Consult the PRD for business requirements
4. Contact the database administrator

---

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-06 | Claude Code | Initial database design and documentation |

---

**End of README**
