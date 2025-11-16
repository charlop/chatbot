# Local Development Setup Guide

Complete guide for setting up the local development environment for the Contract Refund Eligibility System backend.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** (we use Python 3.12.10)
- **UV package manager** ([installation guide](https://github.com/astral-sh/uv))
- **Docker & Docker Compose** ([installation guide](https://docs.docker.com/get-docker/))
- **Git** (for version control)

---

## Quick Start (5 minutes)

```bash
# 1. Start PostgreSQL and Redis
docker-compose up -d

# 2. Wait for services to be healthy (check with)
docker-compose ps

# 3. Create test database
docker exec contract-postgres createdb -U postgres contract_refund_system_test

# 4. Install Python dependencies
uv sync --all-extras

# 5. Seed the database with test data
uv run python scripts/seed_db.py --with-extractions

# 6. Start the backend server
uv run uvicorn app.main:app --reload --port 8001

# 7. Open API documentation
open http://localhost:8001/docs
```

---

## Detailed Setup Instructions

### 1. Start Database Services

Start PostgreSQL and Redis using Docker Compose:

```bash
# Start services in background
docker-compose up -d

# Check service status
docker-compose ps

# Expected output:
# NAME                 STATUS              PORTS
# contract-postgres    Up (healthy)        0.0.0.0:5432->5432/tcp
# contract-redis       Up (healthy)        0.0.0.0:6379->6379/tcp
```

**What This Does:**
- Starts PostgreSQL 15 on port 5432
- Starts Redis 7 on port 6379
- Creates persistent volumes for data
- Automatically runs schema.sql on first start

**View Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

### 2. Create Test Database

The main database (`contract_refund_system`) is created automatically. Create the test database:

```bash
docker exec contract-postgres createdb -U postgres contract_refund_system_test
```

**Verify Databases:**
```bash
docker exec -it contract-postgres psql -U postgres -c "\l"

# Expected databases:
# contract_refund_system       (development)
# contract_refund_system_test  (testing)
```

---

### 3. Verify Database Connection

Test the connection from your host machine:

```bash
# Using psql (if installed locally)
psql -h localhost -U postgres -d contract_refund_system -c "SELECT 1"

# Using Docker
docker exec -it contract-postgres psql -U postgres -d contract_refund_system

# Inside psql:
# \dt                    # List tables
# \d contracts           # Describe contracts table
# SELECT COUNT(*) FROM contracts;
# \q                     # Quit
```

---

### 4. Install Python Dependencies

Install all project dependencies using UV:

```bash
# Install all dependencies (including dev tools)
uv sync --all-extras

# Verify installation
uv run python --version
# Python 3.12.10

# Check installed packages
uv pip list
```

---

### 5. Seed the Database

Populate the database with test data:

```bash
# Seed users and contracts only
uv run python scripts/seed_db.py

# Seed users, contracts, AND extractions
uv run python scripts/seed_db.py --with-extractions
```

**Expected Output:**
```
============================================================
DATABASE SEEDING SCRIPT
============================================================
Database: postgresql+asyncpg://postgres:***@localhost:5432/contract_refund_system

Initializing database...
✅ Database initialized

Seeding users...
  Created user: admin@example.com
  Created user: user1@example.com
  Created user: user2@example.com
✅ Users seeded

Seeding contracts...
  Created contract: GAP-2024-0001 (Test Customer 1)
  Created contract: GAP-2024-0002 (Test Customer 2)
  ...
  Created contract: GAP-2024-0015 (Test Customer 15)
✅ Contracts seeded

Seeding extractions...
  Created extraction for contract: GAP-2024-0001 (status: pending)
  Created extraction for contract: GAP-2024-0002 (status: approved)
  ...
✅ Extractions seeded

============================================================
✅ SEEDING COMPLETE
============================================================
```

**What This Creates:**
- 3 users (1 admin, 2 regular users)
- 15 contracts (with realistic vehicle data)
- 5 extractions (2 approved, 1 rejected, 2 pending) - if `--with-extractions` used

**Verify Data:**
```bash
docker exec -it contract-postgres psql -U postgres -d contract_refund_system -c "
  SELECT 'Users' as table_name, COUNT(*) as count FROM users
  UNION ALL
  SELECT 'Contracts', COUNT(*) FROM contracts
  UNION ALL
  SELECT 'Extractions', COUNT(*) FROM extractions;
"

# Expected:
#   table_name  | count
# --------------+-------
#   Users       |     3
#   Contracts   |    15
#   Extractions |     5
```

---

### 6. Start the Backend Server

Start the FastAPI development server:

```bash
# Start with auto-reload (recommended for development)
uv run uvicorn app.main:app --reload --port 8001

# Or with custom host (accessible from other devices on network)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Or run directly
uv run python -m app.main
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Starting Contract Refund Eligibility System
INFO:     Environment: development
INFO:     Debug mode: False
INFO:     Database connection verified
INFO:     Application startup complete.
```

**Test the Server:**
```bash
# Health check
curl http://localhost:8001/health

# Readiness check (should show database: connected)
curl http://localhost:8001/ready

# API documentation
open http://localhost:8001/docs
```

---

## Running Tests

### Smoke Tests (No Database Required)

```bash
uv run pytest tests/test_main.py -v --no-cov
```

### All Tests (Requires Database)

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/unit/test_models.py -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Development Tools

### pgAdmin (Database GUI)

Start pgAdmin for database management:

```bash
# Start pgAdmin (using profile)
docker-compose --profile tools up -d pgadmin

# Access pgAdmin
open http://localhost:5050

# Login credentials:
# Email: admin@example.com
# Password: admin
```

**Add PostgreSQL Server in pgAdmin:**
1. Right-click "Servers" → "Register" → "Server"
2. General tab:
   - Name: Local Development
3. Connection tab:
   - Host: postgres (or host.docker.internal)
   - Port: 5432
   - Username: postgres
   - Password: postgres
   - Save password: Yes

### Code Quality Tools

```bash
# Format code
uv run black app tests

# Lint code
uv run ruff check app tests

# Type check
uv run mypy app

# Run all quality checks
uv run black app tests && \
uv run ruff check app tests && \
uv run mypy app
```

---

## Useful Docker Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (⚠️ deletes all data)
docker-compose down -v

# Restart specific service
docker-compose restart postgres
docker-compose restart redis

# View service logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Check service health
docker-compose ps
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it contract-postgres psql -U postgres -d contract_refund_system

# Run SQL file
docker exec -i contract-postgres psql -U postgres -d contract_refund_system < database/schema.sql

# Backup database
docker exec contract-postgres pg_dump -U postgres contract_refund_system > backup.sql

# Restore database
docker exec -i contract-postgres psql -U postgres -d contract_refund_system < backup.sql

# Drop and recreate database
docker exec contract-postgres psql -U postgres -c "DROP DATABASE IF EXISTS contract_refund_system"
docker exec contract-postgres psql -U postgres -c "CREATE DATABASE contract_refund_system"
docker exec -i contract-postgres psql -U postgres -d contract_refund_system < database/schema.sql
```

### Redis Operations

```bash
# Connect to Redis CLI
docker exec -it contract-redis redis-cli

# Inside redis-cli:
# PING                    # Test connection
# KEYS *                  # List all keys
# GET <key>               # Get value
# FLUSHALL                # Clear all data (⚠️ use with caution)
# EXIT                    # Quit
```

---

## Environment Variables

The `.env` file contains all configuration. Key variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_refund_system
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_refund_system_test

# Redis
REDIS_URL=redis://localhost:6379/0
TEST_REDIS_URL=redis://localhost:6379/1

# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# LLM Providers (add your actual API keys)
ANTHROPIC_API_KEY=sk-ant-placeholder-replace-with-real-key
OPENAI_API_KEY=sk-placeholder-replace-with-real-key
LLM_PROVIDER=anthropic

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## Troubleshooting

### Port Already in Use

If ports 5432 or 6379 are already in use:

```bash
# Find process using port
lsof -i :5432
lsof -i :6379

# Kill process (replace PID)
kill -9 <PID>

# Or use different ports in docker-compose.yml
ports:
  - "5433:5432"  # Change host port
```

### Database Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Verify database exists
docker exec contract-postgres psql -U postgres -c "\l"
```

### Seeding Script Fails

```bash
# Check database connection
psql -h localhost -U postgres -d contract_refund_system -c "SELECT 1"

# Drop and recreate database
docker exec contract-postgres psql -U postgres -c "DROP DATABASE contract_refund_system"
docker exec contract-postgres psql -U postgres -c "CREATE DATABASE contract_refund_system"

# Re-run schema
docker exec -i contract-postgres psql -U postgres -d contract_refund_system < database/schema.sql

# Re-run seeding
uv run python scripts/seed_db.py --with-extractions
```

### Health Check Fails

```bash
# Check if services are healthy
docker-compose ps

# Check application logs
uv run uvicorn app.main:app --reload --port 8001
# Look for "Database connection verified" message

# Test database directly
docker exec contract-postgres psql -U postgres -d contract_refund_system -c "SELECT 1"
```

### Uvicorn Port Conflict (Day 4)

If you see "Address already in use" error:

```bash
# Find and kill existing uvicorn processes
ps aux | grep "uvicorn" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

# Wait a moment, then restart
sleep 2 && uv run uvicorn app.main:app --reload --port 8001

# Or use a different port
uv run uvicorn app.main:app --reload --port 8002
```

### Contract API Returns 404

If contract search returns 404 but data exists:

```bash
# Verify contract exists in database
docker exec -it contract-postgres psql -U postgres -d contract_refund_system -c "
  SELECT contract_id, account_number, customer_name
  FROM contracts
  LIMIT 5;
"

# Check exact account number (case-sensitive)
docker exec -it contract-postgres psql -U postgres -d contract_refund_system -c "
  SELECT contract_id, account_number
  FROM contracts
  WHERE account_number = 'ACC-TEST-00001';
"

# Re-seed database if needed
uv run python scripts/seed_db.py --with-extractions
```

### Audit Event Type Error

If you see "invalid event_type" error:

```bash
# Valid event types are defined in database/schema.sql:
# 'search', 'view', 'extract', 'edit', 'approve', 'reject', 'chat',
# 'login', 'logout', 'user_created', 'user_updated', 'user_deleted'

# Check audit events
docker exec -it contract-postgres psql -U postgres -d contract_refund_system -c "
  SELECT event_type, COUNT(*) as count
  FROM audit_events
  GROUP BY event_type
  ORDER BY count DESC;
"
```

---

## Clean Restart

To completely reset your local environment:

```bash
# 1. Stop and remove all containers and volumes
docker-compose down -v

# 2. Start fresh
docker-compose up -d

# 3. Create test database
docker exec contract-postgres createdb -U postgres contract_refund_system_test

# 4. Verify services
docker-compose ps

# 5. Seed database
uv run python scripts/seed_db.py --with-extractions

# 6. Start server
uv run uvicorn app.main:app --reload --port 8001
```

---

## Testing Contract API Endpoints (Day 4)

### Contract Search Endpoint

Search for a contract by account number:

```bash
# Search for existing contract
curl -X POST http://localhost:8001/api/v1/contracts/search \
  -H "Content-Type: application/json" \
  -d '{"account_number": "ACC-TEST-00001"}'

# Expected response (200 OK):
{
  "contract_id": "GAP-2024-0001",
  "account_number": "ACC-TEST-00001",
  "pdf_url": "https://example.com/contracts/GAP-2024-0001.pdf",
  "document_repository_id": "DOC-REPO-000001",
  "contract_type": "GAP",
  "contract_date": "2025-11-12",
  "customer_name": "Test Customer 1",
  "vehicle_info": {
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "vin": "1HGCM82633A000001",
    "color": "Black"
  },
  "created_at": "2025-11-12T15:50:08.224437Z",
  "updated_at": "2025-11-12T15:50:08.224437Z",
  "last_synced_at": null
}

# Search for non-existent contract (404)
curl -X POST http://localhost:8001/api/v1/contracts/search \
  -H "Content-Type: application/json" \
  -d '{"account_number": "ACC-DOES-NOT-EXIST"}'
```

### Contract Retrieval Endpoint

Get a contract by its ID:

```bash
# Get contract by ID
curl http://localhost:8001/api/v1/contracts/GAP-2024-0001

# Get contract without extraction data
curl "http://localhost:8001/api/v1/contracts/GAP-2024-0001?include_extraction=false"

# Get non-existent contract (404)
curl http://localhost:8001/api/v1/contracts/INVALID-ID
```

### Testing with API Documentation

The interactive API documentation provides a web interface for testing endpoints:

```bash
# Open Swagger UI
open http://localhost:8001/docs

# Or ReDoc
open http://localhost:8001/redoc
```

**Available Endpoints (Day 4):**
- `POST /api/v1/contracts/search` - Search for contract by account number
- `GET /api/v1/contracts/{contract_id}` - Retrieve contract by ID
- `GET /health` - Health check
- `GET /ready` - Readiness check with database status

### Verify Audit Logging

All contract operations are logged to the audit_events table:

```bash
docker exec -it contract-postgres psql -U postgres -d contract_refund_system -c "
  SELECT event_id, event_type, contract_id, event_data, timestamp
  FROM audit_events
  ORDER BY timestamp DESC
  LIMIT 10;
"
```

---

## Next Steps

Once your local environment is set up:

1. ✅ **Day 4 Complete**: Contract Search and Retrieval APIs implemented
2. ✅ **Explore API Documentation**: http://localhost:8001/docs
3. ✅ **Test Contract Endpoints**:
   - POST http://localhost:8001/api/v1/contracts/search
   - GET http://localhost:8001/api/v1/contracts/{contract_id}
4. ✅ **Test Health Endpoints**:
   - http://localhost:8001/health
   - http://localhost:8001/ready
5. ✅ **Run Tests**: `uv run pytest tests/ -v`
6. ✅ **Explore Database**: Use pgAdmin at http://localhost:5050
7. 📋 **Next**: Implement Day 5 tasks (LLM Integration & Extraction)

---

## Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8001 | N/A |
| API Docs (Swagger) | http://localhost:8001/docs | N/A |
| API Docs (ReDoc) | http://localhost:8001/redoc | N/A |
| PostgreSQL | localhost:5432 | postgres/postgres |
| Redis | localhost:6379 | N/A |
| pgAdmin | http://localhost:5050 | admin@example.com/admin |

| Database | Purpose |
|----------|---------|
| contract_refund_system | Development |
| contract_refund_system_test | Testing |

---

**Environment Status**: ✅ Ready for Development
**Next**: Continue with Day 4 implementation!
