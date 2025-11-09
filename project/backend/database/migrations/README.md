# Database Migrations
## Using Alembic for Schema Version Control

---

## Overview

This directory will contain Alembic migration scripts for version-controlled database schema changes. Alembic provides a way to:

- Track schema changes over time
- Apply changes incrementally
- Rollback changes if needed
- Maintain consistency across environments

---

## Initial Setup

### 1. Install Dependencies

```bash
cd project/backend
pip install alembic psycopg2-binary sqlalchemy
```

### 2. Initialize Alembic

```bash
# Initialize Alembic (creates alembic/ directory and alembic.ini)
alembic init alembic
```

This creates:
```
backend/
├── alembic/
│   ├── versions/          # Migration scripts go here
│   ├── env.py            # Alembic environment config
│   ├── script.py.mako    # Template for new migrations
│   └── README
├── alembic.ini           # Alembic configuration
```

### 3. Configure Database Connection

Edit `alembic.ini`:

```ini
# Replace this line:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# With your database URL (use environment variable in production):
sqlalchemy.url = postgresql://postgres:password@localhost/contract_refund_system
```

**For production**, use environment variables in `alembic/env.py`:

```python
from os import environ
config.set_main_option('sqlalchemy.url', environ.get('DATABASE_URL'))
```

### 4. Configure SQLAlchemy Models

Edit `alembic/env.py` to import your SQLAlchemy models:

```python
# Add this import at the top
from app.models.database import Base  # Your SQLAlchemy Base

# Update target_metadata
target_metadata = Base.metadata
```

---

## Creating Migrations

### Auto-generate Migration from Schema

Alembic can detect changes between your SQLAlchemy models and database:

```bash
# Create migration from detected changes
alembic revision --autogenerate -m "Initial schema"
```

This creates a file like `alembic/versions/001_initial_schema.py`.

### Manual Migration

For complex changes or raw SQL:

```bash
# Create empty migration
alembic revision -m "Add custom index"
```

Edit the generated file:

```python
def upgrade():
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_custom
        ON extractions(contract_id, status);
    """)

def downgrade():
    op.execute("DROP INDEX idx_custom;")
```

---

## Applying Migrations

### Upgrade to Latest

```bash
# Apply all pending migrations
alembic upgrade head
```

### Upgrade Incrementally

```bash
# Upgrade one version
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade abc123
```

### Check Current Version

```bash
# Show current database version
alembic current

# Show migration history
alembic history --verbose
```

---

## Rolling Back

### Downgrade One Version

```bash
alembic downgrade -1
```

### Downgrade to Specific Revision

```bash
alembic downgrade abc123
```

### Downgrade to Base (Empty Database)

```bash
# WARNING: This removes all tables!
alembic downgrade base
```

---

## Migration Best Practices

### 1. Always Review Auto-generated Migrations

Auto-generated migrations may not be perfect:
- Review the `upgrade()` and `downgrade()` functions
- Test migrations on a copy of production data
- Ensure downgrade logic is correct

### 2. Make Migrations Reversible

Every `upgrade()` should have a corresponding `downgrade()`:

```python
def upgrade():
    op.add_column('extractions', sa.Column('new_field', sa.String(100)))

def downgrade():
    op.drop_column('extractions', 'new_field')
```

### 3. Use Transactions

Alembic wraps migrations in transactions by default. For non-transactional operations (e.g., `CREATE INDEX CONCURRENTLY`), disable transactions:

```python
# At the top of the migration file
# revision = 'abc123'
# down_revision = 'xyz789'
# ...

def upgrade():
    # Disable transaction for this operation
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY idx_custom ON table(column);")
```

### 4. Test Migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 5. Version Control

Commit migration files to git:
```bash
git add alembic/versions/001_initial_schema.py
git commit -m "Add initial schema migration"
```

---

## Example Migration Workflow

### Scenario: Add a new column to `extractions` table

1. **Update SQLAlchemy model** (`app/models/database/extraction.py`):

```python
class Extraction(Base):
    __tablename__ = 'extractions'
    # ... existing columns ...
    review_notes = Column(String(500))  # New column
```

2. **Generate migration**:

```bash
alembic revision --autogenerate -m "Add review_notes to extractions"
```

3. **Review generated migration** (`alembic/versions/002_add_review_notes.py`):

```python
def upgrade():
    op.add_column('extractions',
        sa.Column('review_notes', sa.String(length=500), nullable=True))

def downgrade():
    op.drop_column('extractions', 'review_notes')
```

4. **Test migration**:

```bash
# Apply migration
alembic upgrade head

# Verify column exists
psql -d contract_refund_system -c "\d extractions"

# Test rollback
alembic downgrade -1

# Verify column removed
psql -d contract_refund_system -c "\d extractions"

# Re-apply
alembic upgrade head
```

5. **Commit to version control**:

```bash
git add alembic/versions/002_add_review_notes.py
git commit -m "Add review_notes column to extractions table"
```

---

## Initial Migration from Existing Schema

If you already have the database created from `schema.sql`, you need to tell Alembic to start from that state:

### Option 1: Stamp Current State

```bash
# Create initial empty migration
alembic revision -m "Initial schema"

# Mark database as having this migration applied (don't run upgrade)
alembic stamp head
```

### Option 2: Import Schema and Auto-generate

1. Import your SQLAlchemy models to match `schema.sql`
2. Run auto-generate to create the initial migration
3. Apply to a fresh database

---

## Common Migration Operations

### Add Column

```python
op.add_column('table_name',
    sa.Column('column_name', sa.String(100), nullable=True))
```

### Drop Column

```python
op.drop_column('table_name', 'column_name')
```

### Create Index

```python
op.create_index('idx_name', 'table_name', ['column_name'])
```

### Drop Index

```python
op.drop_index('idx_name', table_name='table_name')
```

### Add Foreign Key

```python
op.create_foreign_key(
    'fk_name',
    'source_table', 'target_table',
    ['source_column'], ['target_column']
)
```

### Execute Raw SQL

```python
op.execute("ALTER TABLE table_name ADD CONSTRAINT check_name CHECK (column > 0);")
```

---

## Troubleshooting

### Issue: "Can't locate revision identified by 'xyz'"

**Cause:** Migration file was deleted or not committed to git.

**Solution:**
- Restore the migration file from git history
- Or downgrade to a known good state and re-create migrations

### Issue: Migration fails midway

**Cause:** Error in migration SQL or constraint violation.

**Solution:**
1. Fix the data issue manually
2. Comment out the problematic operation in the migration
3. Mark as applied: `alembic stamp head`
4. Create a new migration with the fix

### Issue: Different environments out of sync

**Cause:** Migrations applied in different order.

**Solution:**
- Use `alembic current` to check version on each environment
- Apply missing migrations: `alembic upgrade head`
- Never skip migrations

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/db-migration.yml
name: Database Migration

on:
  push:
    branches: [main]
    paths:
      - 'backend/alembic/versions/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install alembic psycopg2-binary sqlalchemy

      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          cd backend
          alembic upgrade head
```

---

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Next Steps:**

1. Set up Alembic in the backend project
2. Create initial migration from `schema.sql`
3. Test migration workflow on development database
4. Configure CI/CD to auto-apply migrations

---

**End of Migrations README**
