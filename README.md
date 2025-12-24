# Contract Refund Eligibility System

AI-powered tool for F&I back-office specialists to extract and validate contractual terms from aftermarket insurance products (GAP, VSC, Tire & Wheel). Features multi-policy account support, AI-driven data extraction, and state-specific refund logic.

## Tech Stack

**Backend**: FastAPI • PostgreSQL • Redis • SQLAlchemy • LocalStack S3
**Frontend**: Next.js 16 • React • TypeScript • Tailwind CSS
**AI**: Anthropic Claude (document extraction)
**Infrastructure**: Docker Compose • UV (Python package manager)

## Prerequisites

- **Docker Desktop** - Containers for PostgreSQL, Redis, LocalStack
- **UV** - Python package manager ([install](https://github.com/astral-sh/uv))
- **Node.js 18+** - Frontend runtime
- **Python 3.12+** - Backend runtime

## Getting Started

### Quick Start (Recommended)

Start all services with test data in one command:

```bash
cd project
./start.sh --seed
```

This will:
1. Start Docker containers (PostgreSQL, Redis, LocalStack S3)
2. Create and seed the database with multi-policy test accounts
3. Set up S3 buckets and upload test PDFs
4. Start the FastAPI backend on http://localhost:8001
5. Start the Next.js frontend on http://localhost:3000

**URLs**:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

### Manual Setup (For Granular Control)

#### 1. Start Docker Services

```bash
cd project/backend
docker-compose up -d
```

**Services**:
- PostgreSQL: `localhost:5433` (user: `postgres`, password: `postgres`)
- Redis: `localhost:6379`
- LocalStack S3: `localhost:4566` (AWS endpoint)

#### 2. Create Database

```bash
# Connect to PostgreSQL container
docker exec -it contract-postgres psql -U postgres

# Create database
CREATE DATABASE contract_refund_system;
\q

# Apply schema
docker exec -i contract-postgres psql -U postgres -d contract_refund_system \
  < database/schema.sql
```

#### 3. Seed Database (Optional)

```bash
# Option A: Using seed script (recommended)
cd project/backend
uv run python scripts/seed_db.py --with-extractions

# Option B: Direct SQL seeding
docker exec -i contract-postgres psql -U postgres -d contract_refund_system \
  < database/seed_data.sql
```

**Test Accounts** (multi-policy):
- `000000000001` - 1 policy (edge case)
- `000000000002` - 2 policies (DI_F → GAP, GAP_O → VSC)
- `000000000003` - 3 policies
- `000000000004` - 5 policies (stress test)

#### 4. Setup LocalStack S3

```bash
cd project/backend
uv run python scripts/setup_s3.py --all
```

This creates the `contracts-dev` bucket and uploads test PDFs for all contract templates.

**Verify S3 setup**:
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://contracts-dev/templates/
```

#### 5. Start Backend

```bash
cd project/backend

# Set environment variables for LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Start FastAPI
uv run uvicorn app.main:app --reload --port 8001
```

**Logs**: `tail -f /tmp/backend.log`

#### 6. Start Frontend

```bash
cd project/frontend

# Install dependencies (first time only)
npm install

# Start Next.js dev server
npm run dev
```

**Logs**: `tail -f /tmp/frontend.log`

## Common Tasks

### Stop All Services

```bash
cd project
./stop.sh --all  # Stops backend, frontend, and Docker containers
```

### View Logs

```bash
# Backend
tail -f /tmp/backend.log

# Frontend
tail -f /tmp/frontend.log

# Docker services
docker-compose -f project/backend/docker-compose.yml logs -f postgres
```

### Reset Database

```bash
# Drop and recreate
docker exec -it contract-postgres psql -U postgres -d contract_refund_system \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Reapply schema and seed data
cd project/backend
docker exec -i contract-postgres psql -U postgres -d contract_refund_system \
  < database/schema.sql
docker exec -i contract-postgres psql -U postgres -d contract_refund_system \
  < database/seed_data.sql
```

### Run Tests

```bash
# Backend unit tests
cd project/backend
uv run pytest tests/unit -v

# Backend integration tests
uv run pytest tests/integration -v

# Frontend tests
cd project/frontend
npm test
```

### Test Multi-Policy Search

```bash
# Search account with 2 policies
curl -X POST http://localhost:8001/api/v1/contracts/search \
  -H "Content-Type: application/json" \
  -d '{"account_number": "000000000002"}'

# Expected response: MultiPolicyResponse with 2 policies
# {
#   "account_number": "000000000002",
#   "state": "FL",
#   "policies": [
#     {"policy_id": "DI_F", "contract_id": "GAP-2024-TEMPLATE-001", ...},
#     {"policy_id": "GAP_O", "contract_id": "VSC-2024-TEMPLATE-004", ...}
#   ],
#   "total_policies": 2
# }
```

## Architecture Overview

### Multi-Policy Support

The system supports multiple insurance policies per account using a composite key `(account_number, policy_id)`.

**Flow**:
1. User searches by account number
2. System returns `MultiPolicyResponse` with all policies in a table
3. User selects a specific policy to view contract details
4. System navigates to `/contracts/{contractId}?policy={policyId}`

**Database Schema**:
```sql
CREATE TABLE account_template_mappings (
    account_number VARCHAR(100) NOT NULL,
    policy_id VARCHAR(50) NOT NULL,
    contract_template_id VARCHAR(100) NOT NULL,
    CONSTRAINT unique_account_policy UNIQUE (account_number, policy_id)
);
```

### Caching Strategy

**Three-tier cache**:
1. **Redis** (in-memory, TTL: 1 hour) - Fastest access
2. **PostgreSQL** (`account_template_mappings`) - Persistent cache
3. **External DB** (remote relational DB) - Source of truth

### S3 Document Storage

Contract PDFs are stored in LocalStack S3 (development) or AWS S3 (production).

**Bucket structure**:
```
contracts-dev/
└── templates/
    ├── gap-001.pdf
    ├── vsc-004.pdf
    └── tire-007.pdf
```

## Project Structure

```
.
├── project/
│   ├── start.sh                    # Start all services
│   ├── stop.sh                     # Stop all services
│   ├── backend/                    # FastAPI application
│   │   ├── app/
│   │   │   ├── api/v1/            # REST endpoints
│   │   │   ├── models/            # SQLAlchemy models
│   │   │   ├── repositories/      # Data access layer
│   │   │   ├── services/          # Business logic
│   │   │   └── integrations/      # External DB, S3 clients
│   │   ├── database/
│   │   │   ├── schema.sql         # PostgreSQL schema
│   │   │   └── seed_data.sql      # Test data
│   │   ├── scripts/
│   │   │   ├── seed_db.py         # Database seeding
│   │   │   └── setup_s3.py        # S3 setup for LocalStack
│   │   ├── tests/                 # Unit & integration tests
│   │   └── docker-compose.yml     # PostgreSQL, Redis, LocalStack
│   └── frontend/                  # Next.js application
│       ├── app/                   # Pages (App Router)
│       ├── components/            # React components
│       │   └── search/
│       │       ├── PolicyListTable.tsx  # Multi-policy table view
│       │       └── SearchResults.tsx     # Conditional rendering
│       └── lib/api/               # API client & types
└── artifacts/
    └── product-docs/
        └── PRD.md                 # Product requirements
```

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/contract_refund_system
REDIS_URL=redis://localhost:6379/0

# S3 (LocalStack)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_BUCKET_NAME=contracts-dev

# LLM
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic

# App
APP_ENV=development
DEBUG=true
```

### Frontend (.env.local)

```bash
# API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api/v1
```

## Troubleshooting

### Port Already in Use

```bash
# Kill processes
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8001 | xargs kill -9  # Backend
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep contract-postgres

# Test connection
docker exec -it contract-postgres psql -U postgres -c "SELECT 1"
```

### LocalStack S3 Issues

```bash
# Check LocalStack is running
curl http://localhost:4566/_localstack/health

# Recreate bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://contracts-dev
uv run python project/backend/scripts/setup_s3.py --all
```

### Schema Mismatch Errors

If you see `column does not exist` errors, the database schema is outdated:

```bash
# Drop and recreate database with latest schema
cd project/backend
docker exec -it contract-postgres psql -U postgres -d contract_refund_system \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

docker exec -i contract-postgres psql -U postgres -d contract_refund_system \
  < database/schema.sql
docker exec -i contract-postgres psql -U postgres -d contract_refund_system \
  < database/seed_data.sql
```

## Documentation

- **PRD**: `artifacts/product-docs/PRD.md`
- **API Docs**: http://localhost:8001/docs (interactive Swagger UI)
- **Implementation Phases**: `artifacts/product-docs/implementation-phase*.md`
- **Testing Strategy**: `docs/testing-strategy-catch-runtime-errors.md`

## Development Workflow

**Daily workflow**:
```bash
./project/start.sh --seed     # Morning: start with fresh data
# ... develop ...
./project/stop.sh --all       # Evening: stop everything
```

**Testing before commit**:
```bash
cd project/backend
uv run pytest tests/ -v       # Backend tests

cd ../frontend
npm test                      # Frontend tests
npm run lint                  # Linting
```

---

**Quick Start**: `cd project && ./start.sh --seed`
**API Docs**: http://localhost:8001/docs
**Frontend**: http://localhost:3000
