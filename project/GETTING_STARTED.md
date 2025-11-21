# Getting Started Guide
## Contract Refund Eligibility System - Complete Setup

**Last Updated:** November 16, 2025
**Target Audience:** Developers setting up the project for the first time

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [LLM Provider Setup](#llm-provider-setup)
5. [PDF Storage Configuration](#pdf-storage-configuration)
6. [Database Setup](#database-setup)
7. [Local Development](#local-development)
8. [Troubleshooting](#troubleshooting)
9. [Architecture Overview](#architecture-overview)

---

## Prerequisites

Before starting, ensure you have these tools installed:

### Required

- **Docker Desktop** (v20.10+) - For PostgreSQL and Redis
  ```bash
  # Verify installation
  docker --version
  docker-compose --version
  ```

- **UV** (Python package manager) - For backend dependencies
  ```bash
  # Install UV (if not installed)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Verify installation
  uv --version
  ```

- **Node.js & npm** (v18+) - For frontend
  ```bash
  # Verify installation
  node --version
  npm --version
  ```

### Optional

- **netcat (nc)** - For health checks (usually pre-installed on macOS/Linux)
- **AWS CLI** - If using real S3 for PDFs (production)
- **LocalStack** - For local S3 emulation (recommended for local development)

---

## Quick Start

**Fastest way to get running:**

```bash
# 1. Clone repository
cd /Users/chris/dev/chatbot/project

# 2. Configure environment variables (see Environment Configuration section)
cp backend/.env.example backend/.env
# Edit backend/.env with your LLM API key

# 3. Start all services with test data
./start.sh --seed

# 4. Access the application
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8001
# API Docs:  http://localhost:8001/docs
```

**That's it!** You now have:
- ✅ PostgreSQL database (seeded with 15 test contracts)
- ✅ Redis cache
- ✅ Backend API running
- ✅ Frontend running

---

## Environment Configuration

### Backend Environment Variables

The backend requires environment variables for configuration. All available options are in `.env.example`.

#### Step 1: Copy Example File

```bash
cd backend
cp .env.example .env
```

#### Step 2: Edit Required Variables

**Minimum required configuration:**

```bash
# backend/.env

# =============================================================================
# Application Settings
# =============================================================================
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# =============================================================================
# Database (Default - works with Docker Compose)
# =============================================================================
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_refund_system

# =============================================================================
# Redis (Default - works with Docker Compose)
# =============================================================================
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# LLM Provider (REQUIRED - See LLM Provider Setup section)
# =============================================================================
LLM_PROVIDER=anthropic  # Options: anthropic, openai, bedrock

# Add your API key (choose one):
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OR
OPENAI_API_KEY=sk-your-key-here
# OR (for AWS Bedrock)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BEDROCK_REGION=us-east-1

# =============================================================================
# CORS (Default - allows frontend on localhost:3000)
# =============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

#### Optional Configuration

```bash
# LLM Fine-tuning
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.1

ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4000
ANTHROPIC_TEMPERATURE=0.1

# Cache TTLs (in seconds)
CACHE_TTL_CONTRACT=900      # 15 minutes
CACHE_TTL_EXTRACTION=3600   # 1 hour
CACHE_TTL_DOCUMENT=1800     # 30 minutes

# Connection Pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
```

### Frontend Environment Variables

The frontend uses Next.js and automatically connects to `http://localhost:8001` for the backend API.

**No frontend environment configuration required for local development.**

For production, create `frontend/.env.production`:

```bash
# frontend/.env.production
NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com
```

---

## LLM Provider Setup

The system supports three LLM providers. You only need to configure **ONE**.

### Option 1: Anthropic (Recommended)

**Why Anthropic?**
- Best extraction accuracy for contract data
- Lowest cost per token
- Built-in support for large context windows

**Setup:**

1. **Get API Key:**
   - Sign up at https://console.anthropic.com
   - Navigate to API Keys
   - Create a new API key

2. **Configure:**
   ```bash
   # backend/.env
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # Optional - default is latest
   ```

3. **Test:**
   ```bash
   curl -X POST http://localhost:8001/api/v1/extractions \
     -H 'Content-Type: application/json' \
     -d '{"contractId": "GAP-2024-0001"}'
   ```

### Option 2: OpenAI

**Why OpenAI?**
- Widely supported
- Good for general-purpose extraction
- Familiar for most developers

**Setup:**

1. **Get API Key:**
   - Sign up at https://platform.openai.com
   - Navigate to API Keys
   - Create a new secret key

2. **Configure:**
   ```bash
   # backend/.env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-openai-key-here
   OPENAI_MODEL=gpt-4-turbo-preview  # Optional - default
   ```

3. **Test:**
   ```bash
   curl -X POST http://localhost:8001/api/v1/extractions \
     -H 'Content-Type: application/json' \
     -d '{"contractId": "GAP-2024-0001"}'
   ```

### Option 3: AWS Bedrock

**Why AWS Bedrock?**
- Enterprise deployments with existing AWS infrastructure
- Centralized billing and governance
- No separate API keys needed (uses IAM)

**Setup:**

1. **Configure AWS Credentials:**
   ```bash
   # Option A: Use AWS credentials file
   aws configure
   # Enter Access Key ID, Secret Access Key, Region

   # Option B: Use environment variables
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

2. **Enable Bedrock Model Access:**
   - Go to AWS Console → Bedrock → Model Access
   - Request access to: `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - Wait for approval (usually instant)

3. **Configure:**
   ```bash
   # backend/.env
   LLM_PROVIDER=bedrock
   AWS_BEDROCK_REGION=us-east-1
   AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

   # If not using ~/.aws/credentials:
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   ```

4. **Test:**
   ```bash
   curl -X POST http://localhost:8001/api/v1/extractions \
     -H 'Content-Type: application/json' \
     -d '{"contractId": "GAP-2024-0001"}'
   ```

### Switching Providers

To switch providers, just change `LLM_PROVIDER` and restart the backend:

```bash
# Edit backend/.env
LLM_PROVIDER=openai  # Change from anthropic to openai

# Restart backend
lsof -ti:8001 | xargs kill
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

---

## PDF Storage Configuration

### Architecture Overview

The system stores PDFs in **S3** (AWS S3 in production, LocalStack S3 for local development):

```
Database (PostgreSQL)
  └─ contracts table
       ├─ contract_id: "GAP-2024-0001"
       ├─ s3_bucket: "test-contract-documents"
       ├─ s3_key: "contracts/2024/000000000001/GAP-2024-0001.pdf"
       └─ ... other metadata

Backend API
  └─ S3Service (boto3)
       ├─ Fetches PDF from S3 (LocalStack or AWS)
       ├─ Caches in Redis (15 minutes)
       └─ Streams to frontend
```

### Local Development with LocalStack

**LocalStack** is a local AWS cloud stack that emulates S3, making local development identical to production.

#### What's Already Set Up

The project is pre-configured with LocalStack:

- ✅ **LocalStack** added to Docker Compose
- ✅ **S3Service** configured to use LocalStack endpoint
- ✅ **Seed script** creates S3 bucket and uploads test PDFs automatically

#### Quick Start

LocalStack starts automatically when you run:

```bash
./start.sh --seed
```

This will:
1. Start LocalStack S3 on port 4566
2. Create the `test-contract-documents` bucket
3. Generate and upload 15 test PDFs to match the seeded contracts

#### Manual Setup (if needed)

If you need to manually set up or reset the S3 bucket:

```bash
# Create bucket
cd backend
uv run python scripts/setup_s3.py --create-bucket

# Upload test PDFs
uv run python scripts/setup_s3.py --upload-pdfs

# Reset everything (delete and recreate)
uv run python scripts/setup_s3.py --reset
```

#### Verify S3 Setup

```bash
# List buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List files in bucket
aws --endpoint-url=http://localhost:4566 s3 ls s3://test-contract-documents/contracts/2024/ --recursive

# Download a test PDF
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://test-contract-documents/contracts/2024/000000000001/GAP-2024-0001.pdf \
  /tmp/test.pdf

# View in browser
open /tmp/test.pdf
```

#### How It Works

1. **LocalStack Container**
   - Runs S3 emulation on `localhost:4566`
   - Data persists in `backend/localstack/` directory
   - No AWS account or credentials needed

2. **Test PDF Generation**
   - Script generates realistic GAP insurance contract PDFs
   - Includes all required fields (premium, refund method, cancellation fee)
   - Matches the contract data in the database

3. **S3Service Configuration**
   - Detects `AWS_ENDPOINT_URL` environment variable
   - Uses LocalStack endpoint (`http://localhost:4566`) for local dev
   - Uses real AWS S3 in production (when env var not set)

#### Configuration

The backend `.env` file is already configured for LocalStack:

```bash
# backend/.env
AWS_ENDPOINT_URL=http://localhost:4566  # LocalStack endpoint
AWS_ACCESS_KEY_ID=test                   # Dummy credentials for LocalStack
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
```

#### Troubleshooting

**Problem:** PDFs not found (404 error)

```bash
# Check if LocalStack is running
docker ps | grep localstack

# Check if bucket exists
aws --endpoint-url=http://localhost:4566 s3 ls

# Recreate bucket and upload PDFs
cd backend
uv run python scripts/setup_s3.py --reset
```

**Problem:** LocalStack won't start

```bash
# Check logs
docker logs contract-localstack

# Restart LocalStack
cd backend
docker-compose restart localstack
```

**Problem:** Permission denied errors

```bash
# LocalStack uses dummy credentials, so this shouldn't happen
# But if it does, check that AWS_ENDPOINT_URL is set correctly
echo $AWS_ENDPOINT_URL  # Should be http://localhost:4566
```

### Production Deployment

For production, remove the `AWS_ENDPOINT_URL` from your environment and configure real AWS credentials:

```bash
# Production .env (no AWS_ENDPOINT_URL)
AWS_ACCESS_KEY_ID=your-real-access-key
AWS_SECRET_ACCESS_KEY=your-real-secret-key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=prod-contract-documents
```

The S3Service will automatically detect the absence of `AWS_ENDPOINT_URL` and connect to real AWS S3

---

## Database Setup

### Automatic Setup (Recommended)

The `start.sh` script handles database initialization automatically:

```bash
./start.sh --seed
```

This will:
1. Start PostgreSQL via Docker Compose
2. Create database schema (if not exists)
3. Seed with 15 test contracts
4. Create test users

### Manual Setup

If you prefer manual control:

```bash
# 1. Start PostgreSQL
cd backend
docker-compose up -d postgres

# 2. Wait for PostgreSQL to be ready
sleep 5

# 3. Create database (if needed)
docker exec -it backend-postgres psql -U postgres -c "CREATE DATABASE contract_refund_system;"

# 4. Run schema
docker exec -it backend-postgres psql -U postgres -d contract_refund_system -f /docker-entrypoint-initdb.d/schema.sql

# 5. Seed data
cd backend
uv run python scripts/seed_db.py --with-extractions
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it backend-postgres psql -U postgres -d contract_refund_system

# Run queries
contract_refund_system=# SELECT contract_id, account_number, customer_name FROM contracts LIMIT 5;
```

### Test Data

After seeding, you'll have:

**Users:**
- `admin@example.com` (admin role)
- `user1@example.com` (user role)
- `user2@example.com` (user role)

**Contracts:**
- 15 test contracts with IDs: `GAP-2024-0001` through `GAP-2024-0015`
- Account numbers: `000000000001` through `000000000015`
- Mix of GAP and VSC contracts
- Sample vehicle data (Toyota, Honda, Ford, etc.)

**Extractions:**
- First 5 contracts have pre-extracted data
- Mix of statuses: pending, approved, rejected
- Confidence scores: 88-95%

---

## Local Development

### Starting Services

**Option A: All services (recommended)**
```bash
./start.sh --seed
```

**Option B: Backend only**
```bash
./start.sh --backend-only --seed
```

**Option C: Manual startup**
```bash
# 1. Start Docker services
cd backend
docker-compose up -d

# 2. Start backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 3. Start frontend (in new terminal)
cd frontend
npm run dev
```

### Stopping Services

```bash
# Quick stop (kill all)
kill $(cat /tmp/project_pids.txt | grep PID | cut -d= -f2)
cd backend && docker-compose down

# Or stop individually
kill <BACKEND_PID>
kill <FRONTEND_PID>
cd backend && docker-compose down
```

### Development Workflow

1. **Make code changes**
   - Backend: Auto-reloads with `--reload` flag
   - Frontend: Auto-reloads with `npm run dev`

2. **Run tests**
   ```bash
   # Backend tests
   cd backend
   uv run pytest

   # Frontend tests
   cd frontend
   npm test
   ```

3. **Check logs**
   ```bash
   # Backend
   tail -f /tmp/backend.log

   # Frontend
   tail -f /tmp/frontend.log

   # Docker
   cd backend && docker-compose logs -f
   ```

4. **Test API endpoints**
   ```bash
   # Health check
   curl http://localhost:8001/health

   # Search contract
   curl -X POST http://localhost:8001/api/v1/contracts/search \
     -H 'Content-Type: application/json' \
     -d '{"account_number": "000000000001"}'

   # Get contract
   curl http://localhost:8001/api/v1/contracts/GAP-2024-0001
   ```

---

## Troubleshooting

### Port Already in Use

**Problem:** Port 8001, 3000, 5432, or 6379 already in use

**Solution:**
```bash
# Find and kill process on port
lsof -ti:8001 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # PostgreSQL
lsof -ti:6379 | xargs kill -9  # Redis
```

### Database Connection Failed

**Problem:** `FATAL: database "contract_refund_system" does not exist`

**Solution:**
```bash
# Recreate database
docker exec -it backend-postgres psql -U postgres -c "DROP DATABASE IF EXISTS contract_refund_system;"
docker exec -it backend-postgres psql -U postgres -c "CREATE DATABASE contract_refund_system;"

# Re-seed
cd backend
uv run python scripts/seed_db.py --with-extractions
```

### LLM API Key Invalid

**Problem:** `401 Unauthorized` when calling extraction endpoint

**Solution:**
```bash
# Verify API key is set
cat backend/.env | grep API_KEY

# Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 10, "messages": [{"role": "user", "content": "Hello"}]}'
```

### Frontend Won't Start

**Problem:** `npm ERR! missing script: dev`

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### PDF Streaming Fails

**Problem:** `404 Not Found` when accessing `/contracts/{id}/pdf`

**Solution:**
- **If using real S3:** Verify AWS credentials and bucket exists
- **If using LocalStack:** Ensure LocalStack is running and bucket is created
- **If using Mock:** Verify mock service is configured in `.env`

```bash
# Check if contract has S3 location
curl http://localhost:8001/api/v1/contracts/GAP-2024-0001 | jq '.s3_bucket, .s3_key'

# Test S3 access
aws --endpoint-url=http://localhost:4566 s3 ls s3://test-contract-documents/
```

### Redis Connection Failed

**Problem:** `Error connecting to Redis`

**Solution:**
```bash
# Restart Redis
cd backend
docker-compose restart redis

# Test connection
docker exec -it backend-redis redis-cli ping
# Should respond: PONG
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Browser                           │
│                   http://localhost:3000                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                          │
│  - React components                                          │
│  - API client (axios)                                        │
│  - PDF viewer (react-pdf)                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                           │
│                http://localhost:8001                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Endpoints                                      │   │
│  │  - /contracts/search                                │   │
│  │  - /contracts/{id}                                  │   │
│  │  - /contracts/{id}/pdf                              │   │
│  │  - /extractions                                     │   │
│  │  - /chat                                            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Services                                           │   │
│  │  - ContractService                                  │   │
│  │  - ExtractionService                                │   │
│  │  - ChatService                                      │   │
│  │  - S3Service (PDF streaming)                        │   │
│  │  - LLMService (Anthropic/OpenAI/Bedrock)            │   │
│  └─────────────────────────────────────────────────────┘   │
└────┬────────────────────────────────┬─────────────────┬─────┘
     │                                │                 │
     ▼                                ▼                 ▼
┌──────────┐                  ┌──────────────┐   ┌──────────┐
│PostgreSQL│                  │    Redis     │   │  S3 or   │
│localhost │                  │  localhost   │   │LocalStack│
│  :5432   │                  │    :6379     │   │  :4566   │
│          │                  │              │   │          │
│ Stores:  │                  │  Caches:     │   │ Stores:  │
│ - Users  │                  │  - PDFs      │   │ - PDFs   │
│ - Contracts                 │  - Contracts │   │          │
│ - Extractions               │  - Sessions  │   │          │
│ - Audit                     │              │   │          │
└──────────┘                  └──────────────┘   └──────────┘
```

---

## Next Steps

After completing this setup:

1. **Test the complete flow** using `END_TO_END_GUIDE.md`
2. **Review the PRD** at `artifacts/product-docs/PRD.md`
3. **Check implementation status** at `frontend/INTEGRATION_COMPLETE.md`
4. **Explore the API** at http://localhost:8001/docs

---

## Additional Resources

- **Backend README:** `backend/README.md`
- **Database Schema:** `backend/database/schema.sql`
- **API Documentation:** http://localhost:8001/docs (when running)
- **Frontend Plan:** `artifacts/product-docs/frontend-implementation-plan.md`
- **End-to-End Testing:** `project/END_TO_END_GUIDE.md`

---

**Questions or Issues?**

- Check logs: `tail -f /tmp/backend.log` and `tail -f /tmp/frontend.log`
- Review troubleshooting section above
- Check database: `docker exec -it backend-postgres psql -U postgres -d contract_refund_system`

**Happy coding! 🚀**
