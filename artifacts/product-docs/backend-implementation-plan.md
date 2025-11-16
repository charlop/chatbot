# Backend Implementation Plan
## Contract Refund Eligibility System - Detailed Task Breakdown

**Version:** 1.0
**Date:** 2025-11-09
**Duration:** 12 days (Days 1-12)
**Total Effort:** ~96 hours (12 days × 8 hours)

---

## Overview

This document breaks down the backend implementation into manageable 8-hour work chunks, following TDD principles and keeping things simple. This is a **glorified chatbot with a basic user form** - we're not over-engineering.

**Philosophy:** Build the simplest thing that works, test it thoroughly, then iterate.

### ✅ Existing Work

**Database schema already complete!** (Nov 6, 2025)
- Location: `project/backend/database/`
- 521-line PostgreSQL schema with all required tables
- Production-ready with indexes, constraints, triggers
- ER diagram and documentation included
- **Impact**: Day 1 schema design already done, saves ~4 hours

We'll build the FastAPI application to use this existing schema.

---

## Progress Tracking

**Last Updated:** 2025-11-09

### Completed Days ✅

- ✅ **Day 1 (PARTIAL)**: Database Schema Design (Nov 6, 2025)
  - PostgreSQL schema designed (521 lines)
  - All tables created: contracts, extractions, corrections, audit_events, users, chat_messages
  - Indexes, constraints, triggers implemented
  - ER diagram and documentation complete
  - Seed data script ready
  - Location: `project/backend/database/`
  - **Note**: Auth fields exist but will be ignored until Phase 2

### Next Up 🎯

- **Day 1 (REMAINING)**: FastAPI Project Setup
  - Initialize FastAPI project structure
  - Configure testing infrastructure (pytest)
  - Set up Alembic migrations (map to existing schema)

- **Day 2**: SQLAlchemy Models
  - Map existing schema to SQLAlchemy ORM models
  - Repository layer implementation

### Overall Progress

- **Days Completed**: 1 of 12 (8% - schema complete)
- **Schema**: ✅ Complete (production-ready)
- **Tests Passing**: 0 tests (no code yet)
- **Components Built**: Database schema only
- **Documentation**: Schema docs complete

---

## Tech Stack Summary

- **Framework**: FastAPI (Python 3.12+) ⏳
- **Database**: PostgreSQL 15.x (RDS) ⏳
- **ORM**: SQLAlchemy 2.0 ⏳
- **Migrations**: Alembic ⏳
- **Cache**: Redis (ElastiCache) ⏳
- **LLM Integration**: Vendor-agnostic (OpenAI, Anthropic, Bedrock) ⏳
- **HTTP Client**: httpx (async) ⏳
- **Testing**: pytest + pytest-asyncio + httpx test client ⏳
- **Validation**: Pydantic V2 ⏳
- **Auth**: Deferred to Phase 2 ⏭️

---

## Week 1: Database & Core APIs (Days 1-6)

### Day 1 (8 hours): Project Setup & Database Schema Design ⚠️ PARTIALLY COMPLETE

**Status**: Database schema ✅ complete | FastAPI project ⏳ pending

**Goals**: Initialize FastAPI project, ~~design database schema~~, set up migrations

**Tasks:**

1. **~~Database Schema Design~~** ✅ **COMPLETE** (Previously done)
   - ✅ Schema designed (521 lines, production-ready)
   - ✅ All tables: contracts, extractions, corrections, audit_events, users, chat_messages
   - ✅ ER diagram documented (Mermaid format)
   - ✅ Seed data script created
   - ✅ Location: `project/backend/database/`
   - **Note**: Auth-related fields exist (auth_provider, auth_provider_user_id) but will be ignored in Phase 1

2. **Initialize FastAPI Project** ⏳ **REMAINING** (2 hours)
   ```bash
   cd project/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic-settings
   pip install pytest pytest-asyncio httpx pytest-cov
   ```
   - Create project structure (app/, tests/, alembic/)
   - Configure `requirements.txt`
   - Set up path aliases and imports
   - Create basic `main.py` with health check endpoint

3. **Alembic Configuration** ⏳ **REMAINING** (2 hours)
   - Initialize Alembic in `project/backend/`
   - Configure connection to PostgreSQL (env vars)
   - Create initial migration from existing schema.sql
   - Alternative: Use existing schema.sql directly (simpler for greenfield)
   - Write tests for database connectivity
   - Document migration commands in README

4. **Testing Infrastructure** ⏳ **REMAINING** (2 hours)
   - Configure pytest with async support
   - Set up test database (separate from dev)
   - Create fixtures for database session
   - Create test utilities (create_test_contract, etc.)
   - Write first smoke test (database connection)

5. **Database Setup** ⏳ **REMAINING** (1 hour)
   - Run schema.sql on local PostgreSQL
   - Optionally run seed data
   - Verify tables created correctly
   - Test database connectivity from Python

**Deliverables:**
- ✅ Database schema designed and documented (DONE)
- ⏳ FastAPI project initialized
- ⏳ Alembic configured (or schema.sql approach)
- ⏳ Testing infrastructure ready
- ⏳ Database tables created locally

---

### Day 2 (8 hours): Database Models & Repository Pattern

**Goals**: Implement SQLAlchemy models and repository layer using TDD

**Tasks:**

1. **SQLAlchemy Models** (3 hours)
   - Write tests for model creation, relationships
   - Implement `models/database/contract.py`
   - Implement `models/database/extraction.py`
   - Implement `models/database/correction.py`
   - Implement `models/database/audit_event.py`
   - Implement `models/database/user.py` (stub)
   - Add indexes on frequently queried columns
   - Test model relationships (foreign keys, cascades)

2. **Repository Layer (Base Pattern)** (2 hours)
   - Write tests for CRUD operations
   - Implement `repositories/base.py` (generic CRUD)
   - Add async support (SQLAlchemy async engine)
   - Test database connection pooling
   - Keep it simple - just basic CRUD for now

3. **Contract Repository** (1.5 hours)
   - Write tests for contract-specific queries
   - Implement `repositories/contract_repository.py`
   - Methods: `get_by_id`, `get_by_account_number`, `create`, `update`
   - Test duplicate handling (idempotency)

4. **Extraction Repository** (1.5 hours)
   - Write tests for extraction queries
   - Implement `repositories/extraction_repository.py`
   - Methods: `get_by_contract_id`, `create`, `update_status`, `get_pending`
   - Test unique constraint (one extraction per contract)

**Deliverables:**
- ✅ All SQLAlchemy models with tests
- ✅ Repository pattern implemented
- ✅ Contract & Extraction repositories tested
- ✅ Database connection working

---

### Day 3 (8 hours): Pydantic Schemas & Database Seeding

**Goals**: Create request/response schemas and seed database with test data

**Tasks:**

1. **Pydantic Request Schemas** (2 hours)
   - Write tests for validation
   - Implement `schemas/requests.py`:
     - `ContractSearchRequest` (account_number validation)
     - `ExtractionApprovalRequest`
     - `ExtractionEditRequest` (field_name, corrected_value, reason)
     - `ChatMessageRequest`
   - Add custom validators (account number format, etc.)
   - Test validation edge cases

2. **Pydantic Response Schemas** (2 hours)
   - Write tests for serialization
   - Implement `schemas/responses.py`:
     - `ContractResponse`
     - `ExtractionResponse` (with confidence badges, sources)
     - `AuditEventResponse`
     - `ErrorResponse` (standardized error format)
   - Test nested serialization
   - Configure JSON encoders (dates, decimals)

3. **Database Seeding** (2 hours)
   - Create seed script `scripts/seed_db.py`
   - Seed test contracts (10-20 samples)
   - Seed admin user (for future auth)
   - Test seed idempotency (can run multiple times)
   - Document seeding commands

4. **Connection & Session Management** (2 hours)
   - Implement `database.py` (engine, session factory)
   - Add dependency injection for DB session
   - Configure connection pooling
   - Add health check for database connectivity
   - Test connection failures gracefully

**Deliverables:**
- ✅ All Pydantic schemas with validation tests
- ✅ Database seeding script
- ✅ Connection management configured
- ✅ Health check endpoint working

---

### Day 4 (8 hours): FastAPI Core Setup & Contract Search API

**Goals**: Set up FastAPI application structure and implement contract search

**Tasks:**

1. **FastAPI Application Structure** (2 hours)
   - Implement `app/main.py` with proper app initialization
   - Configure CORS middleware (for frontend)
   - Add request logging middleware
   - Add error handling middleware (global exception handler)
   - Configure API versioning (`/api/v1`)
   - Test middleware stack

2. **Configuration Management** (1 hour)
   - Implement `config.py` using Pydantic Settings
   - Environment variables: DATABASE_URL, REDIS_URL, LLM_API_KEYS
   - Add validation for required env vars
   - Test different environments (dev, test, prod)

3. **Contract Search Endpoint** (3 hours)
   - Write tests for search endpoint (TDD)
   - Implement `POST /api/v1/contracts/search`
   - Flow:
     1. Validate account number
     2. Check cache (Redis) for contract
     3. Query database for contract_id
     4. If not found, query external RDB (mock for now)
     5. Store in database
     6. Log audit event
     7. Return contract metadata
   - Test success case, not found, cache hit
   - Keep external RDB call mocked for now

4. **Contract Retrieval Endpoint** (2 hours)
   - Write tests for retrieval (TDD)
   - Implement `GET /api/v1/contracts/{contract_id}`
   - Return contract + extraction (if exists)
   - Log audit event (view)
   - Test different states (no extraction, pending, approved)

**Deliverables:**
- ✅ FastAPI app with middleware configured
- ✅ Configuration management working
- ✅ Contract search endpoint with tests
- ✅ Contract retrieval endpoint with tests

---

### Day 5 (8 hours): LLM Abstraction Layer (Vendor-Agnostic)

**Goals**: Build vendor-agnostic LLM integration supporting OpenAI, Anthropic, Bedrock

**Tasks:**

1. **LLM Provider Base Class** (2 hours)
   - Write tests for provider interface
   - Implement `integrations/llm_providers/base.py`:
     ```python
     class LLMProvider(ABC):
         @abstractmethod
         async def extract_contract_data(
             self, text: str, contract_id: str
         ) -> ExtractionResult:
             pass
     ```
   - Define `ExtractionResult` model (Pydantic)
   - Test interface contract

2. **OpenAI Provider** (2 hours)
   - Write tests with mocked OpenAI API
   - Implement `integrations/llm_providers/openai_provider.py`
   - Use function calling for structured output
   - Extract 3 fields: GAP premium, refund method, cancellation fee
   - Include confidence scores and source locations
   - Test error handling (timeouts, rate limits)

3. **Anthropic Provider** (2 hours)
   - Write tests with mocked Anthropic API
   - Implement `integrations/llm_providers/anthropic_provider.py`
   - Use tool use for structured output
   - Same extraction logic as OpenAI
   - Test model selection (Claude 3.5 Sonnet)

4. **LLM Service Layer** (2 hours)
   - Write tests for provider selection
   - Implement `services/llm_service.py`
   - Factory pattern for provider selection (based on config)
   - Add retry logic with exponential backoff (3 retries)
   - Add circuit breaker (opens after 5 failures)
   - Test fallback between providers

**Deliverables:**
- ✅ LLM provider abstraction layer
- ✅ OpenAI provider with tests
- ✅ Anthropic provider with tests
- ✅ LLM service with retry/circuit breaker

---

### Day 6 (8 hours): Extraction Workflow & PDF Streaming

**Goals**: Implement extraction endpoint, S3 PDF streaming, and contract text retrieval

**Architecture Context:**
- PDFs stored in S3 with IAM authentication (not publicly accessible)
- Document text and embeddings populated by external batch ETL (not called at runtime)
- Backend provides streaming proxy for PDFs
- See: `artifacts/product-docs/architecture-pdf-streaming.md`

**Tasks:**

1. **S3 Service & PDF Streaming** (2 hours)
   - Add `boto3` to requirements
   - Write tests for S3 streaming (TDD)
   - Implement `services/s3_service.py`
     - `stream_pdf(bucket: str, key: str)` - Stream PDF from S3
     - Redis caching (TTL: 15 minutes)
     - Error handling (S3 not found, access denied)
   - Implement `GET /api/v1/contracts/{contract_id}/pdf` endpoint
     - Check Redis cache first
     - Query DB for s3_bucket/s3_key
     - Stream from S3 with IAM credentials
     - Return StreamingResponse
     - Log audit event
   - Test with sample S3 bucket (local or mock)

2. **Contract Model Updates** (1 hour)
   - Update `models/database/contract.py`:
     - Add `document_text` (TEXT) - OCR'd text from ETL
     - Add `embeddings` (JSONB) - Vector embeddings from ETL
     - Add `s3_bucket` (VARCHAR) - S3 bucket name
     - Add `s3_key` (VARCHAR) - S3 object key
     - Add `text_extracted_at` (TIMESTAMP)
     - Add `text_extraction_status` (VARCHAR)
     - Remove/deprecate `pdf_url` (replaced by S3 streaming)
   - Update `schemas/responses.py`:
     - Add S3 fields to ContractResponse
     - Remove `pdf_url` from response
   - Drop and recreate local database (no migration needed)

3. **Extraction Service** (3 hours)
   - Write tests for extraction flow (TDD)
   - Implement `services/extraction_service.py`
   - Orchestration logic:
     1. Check if extraction already exists (DB + Redis cache)
     2. Retrieve document text from DB (`contract.document_text`)
     3. Call LLM provider (via LLM service from Day 5)
     4. Parse structured output (ExtractionResult)
     5. Store extraction in database (status: pending)
     6. Log audit event
     7. Cache extraction in Redis (TTL: 30 minutes)
   - Test with mocked LLM responses
   - Test error scenarios (LLM timeout, parsing failure, missing text)
   - Test idempotency (don't re-extract if already exists)

4. **Extraction Endpoints** (2 hours)
   - Write tests for extraction endpoints
   - Implement `POST /api/v1/extractions/create`
     - Accepts `contract_id` in request body
     - Calls extraction service
     - Returns extraction data with confidence scores
     - Handle errors gracefully (fallback message)
     - Test idempotency (return existing if already extracted)
   - Implement `GET /api/v1/extractions/{extraction_id}`
     - Return extraction with audit trail
     - Include extraction metadata (model, provider, cost)
     - Test different extraction states (pending, approved, rejected)

**Deliverables:**
- ✅ S3 service with PDF streaming and caching
- ✅ PDF endpoint (`GET /contracts/{id}/pdf`)
- ✅ Contract model with document text and S3 fields
- ✅ Extraction service orchestrating LLM calls
- ✅ Extraction endpoints with tests
- ✅ End-to-end extraction flow working

**Note:** External document ETL is out of scope - it's a batch process that populates:
- `document_text` - OCR'd PDF text
- `embeddings` - Vector embeddings
- `s3_bucket`, `s3_key` - PDF location

We only consume this data at runtime; we don't call any external document API.

---

## Week 2: Approval Workflow & Features (Days 7-12)

### Day 7 (8 hours): Simplified Submission Workflow

**Goals**: Implement single submit endpoint that handles approval with optional corrections

**Background:**
Simplified workflow removes separate approve/reject/edit endpoints in favor of a single submit endpoint:
- User reviews extraction, optionally edits fields inline
- Single "Submit" button sends all changes at once
- Corrections stored in `corrections` table (for fine-tuning metrics)
- Extraction values updated with corrections (source of truth)
- No rejection workflow - if data is wrong, user just corrects it

**Tasks:**

1. **Database Schema Changes** (1 hour)
   - Write migration to remove rejection fields from Extraction model
   - Remove: `rejected_at`, `rejected_by`, `rejection_reason` columns
   - Update status constraint to only allow: 'pending', 'approved'
   - Remove CheckConstraint for 'rejected' status
   - Test migration up/down

2. **Update Models & Schemas** (1.5 hours)
   - Update `models/database/extraction.py`:
     - Remove rejection fields
     - Update status constraint
   - Update `schemas/responses.py`:
     - Remove rejection fields from ExtractionResponse
   - Remove `ExtractionRejectionRequest` schema
   - Remove `ExtractionApprovalRequest` schema (replaced by submit)
   - Remove `ExtractionEditRequest` schema (replaced by submit)
   - Create new `ExtractionSubmitRequest` schema:
     ```python
     class FieldCorrection(BaseModel):
         field_name: str  # gap_insurance_premium, refund_calculation_method, cancellation_fee
         corrected_value: str
         correction_reason: str | None = None

     class ExtractionSubmitRequest(BaseModel):
         corrections: List[FieldCorrection] = []
         notes: str | None = None
     ```

3. **Correction Repository** (1 hour)
   - Write tests for correction CRUD
   - Implement `repositories/correction_repository.py`
   - Methods: `create_correction`, `get_by_extraction_id`, `bulk_create`
   - Test correction creation

4. **Submission Service Logic** (3 hours)
   - Write tests for submit flow (with/without corrections)
   - Implement `submit_extraction()` in `services/extraction_service.py`:
     ```python
     async def submit_extraction(
         extraction_id: UUID,
         corrections: List[FieldCorrection],
         notes: str | None = None,
         submitted_by: UUID | None = None,
     ) -> Extraction:
         # 1. Validate extraction exists and is pending
         # 2. For each correction:
         #    - Create Correction record (audit trail)
         #    - Update corresponding field in Extraction (source of truth)
         # 3. Update status to 'approved'
         # 4. Set approved_at and approved_by
         # 5. Log audit event
         # 6. Return updated extraction
     ```
   - Test atomic transaction (all or nothing)
   - Test submit without corrections (simple approval)
   - Test submit with multiple corrections
   - Test validation (invalid field names, empty values)
   - Test idempotency (can't submit already-approved extraction)

5. **Submit Endpoint** (1 hour)
   - Write tests for submit API
   - Implement `POST /api/v1/extractions/{extraction_id}/submit`
   - Request body: `ExtractionSubmitRequest`
   - Response: Updated `ExtractionResponse` with corrections
   - Test error scenarios (not found, already submitted, validation errors)
   - Log audit event with correction details

6. **Audit Repository** (0.5 hours)
   - Write tests for audit queries
   - Implement `repositories/audit_repository.py`
   - Methods: `create_event`, `get_by_contract_id`, `get_by_extraction_id`
   - Ensure append-only (no deletes/updates)
   - Test event ordering and filtering

**Deliverables:**
- ✅ Database migration removing rejection fields
- ✅ Updated models and schemas
- ✅ Correction repository with tests
- ✅ Submit service with correction handling
- ✅ Submit endpoint with tests
- ✅ Audit repository with event sourcing
- ✅ Complete simplified submission workflow functional

**Note:** This simplification makes the workflow more intuitive:
- User sees extraction → edits any incorrect values → clicks "Submit"
- Backend handles both correction tracking (for ML improvement) and updating the source of truth
- No confusing approve/reject/edit split - just one clear action

---

### Day 8 (8 hours): Audit Logging & Event Sourcing

**Goals**: Comprehensive audit trail implementation

**Tasks:**

1. **Audit Service** (3 hours)
   - Write tests for audit event creation
   - Implement `services/audit_service.py`
   - Event types: search, view, extract, edit, approve, reject, chat
   - Capture: timestamp, user_id (stub), action, event_data
   - Immutable logging (no modifications)
   - Test event data serialization

2. **Audit Query Endpoints** (2 hours)
   - Write tests for audit queries
   - Implement `GET /api/v1/audit/contract/{contract_id}`
   - Implement `GET /api/v1/audit/extraction/{extraction_id}`
   - Return full audit trail with timestamps
   - Test filtering and pagination

3. **Middleware for Auto-Logging** (2 hours)
   - Write tests for automatic logging
   - Implement middleware to log all API requests
   - Capture: endpoint, method, status_code, duration
   - Store in audit_events table
   - Test exclusions (health check, static files)

4. **Performance Optimization** (1 hour)
   - Add indexes on audit_events (contract_id, timestamp)
   - Test query performance with 10k+ events
   - Consider partitioning strategy (future)

**Deliverables:**
- ✅ Audit service with comprehensive logging
- ✅ Audit query endpoints
- ✅ Auto-logging middleware
- ✅ Optimized audit queries

---

### Day 9 (8 hours): Chat Interface Backend

**Goals**: Implement AI chat for contract Q&A

**Tasks:**

1. **Chat Service** (3 hours)
   - Write tests for chat functionality
   - Implement `services/chat_service.py`
   - Build context from contract + extraction data
   - Include chat history in prompt
   - Call LLM provider with chat-optimized prompt
   - Extract citations/sources from response
   - Test multi-turn conversations

2. **Chat Endpoint** (2 hours)
   - Write tests for chat API
   - Implement `POST /api/v1/chat`
   - Request: `{contract_id, message, history}`
   - Response: `{response, sources, context}`
   - Log audit event (chat message)
   - Test error handling (LLM failure)

3. **Account Number Detection** (2 hours)
   - Add regex detection for account numbers in chat
   - If detected, trigger contract search automatically
   - Return contract switch confirmation
   - Test edge cases (partial numbers, false positives)

4. **Chat History Storage** (1 hour)
   - Store chat sessions in Redis (session-based)
   - TTL: 4 hours (configurable)
   - Test session expiration
   - Simple - no persistent chat history yet

**Deliverables:**
- ✅ Chat service with LLM integration
- ✅ Chat endpoint functional
- ✅ Account number detection working
- ✅ Chat history in Redis

---

### Day 10 (8 hours): Redis Caching Layer

**Goals**: Implement comprehensive caching strategy

**Tasks:**

1. **Redis Client Setup** (1.5 hours)
   - Configure Redis connection
   - Implement `utils/cache.py` wrapper
   - Add connection pooling
   - Test connection handling

2. **Cache Strategy Implementation** (3 hours)
   - Contract lookup caching (15-min TTL)
   - Extraction result caching (1-hour TTL)
   - Document text caching (30-min TTL)
   - Session data caching (4-hour TTL)
   - Test cache hits/misses
   - Test TTL expiration

3. **Cache Invalidation** (2 hours)
   - Invalidate extraction cache on approval/edit
   - Invalidate contract cache on update
   - Test cache coherency
   - Add cache warming strategy (future)

4. **Cache Monitoring** (1.5 hours)
   - Add cache hit rate metrics
   - Log cache operations
   - Test cache performance impact
   - Document caching strategy

**Deliverables:**
- ✅ Redis client configured
- ✅ Comprehensive caching implemented
- ✅ Cache invalidation working
- ✅ Cache monitoring in place

---

### Day 11 (8 hours): Admin Endpoints & User Management

**Goals**: Build admin APIs for user management (ready for future auth)

**Tasks:**

1. **User Repository** (1.5 hours)
   - Write tests for user CRUD
   - Implement `repositories/user_repository.py`
   - Methods: `create`, `get_by_id`, `get_all`, `update`, `delete` (soft)
   - Test unique constraints (email, username)

2. **User Management Endpoints** (4 hours)
   - Write tests for user CRUD endpoints
   - Implement `POST /api/v1/admin/users` (create)
   - Implement `GET /api/v1/admin/users` (list with pagination)
   - Implement `PUT /api/v1/admin/users/{user_id}` (update role, status)
   - Implement `DELETE /api/v1/admin/users/{user_id}` (soft delete)
   - Test validation (email format, role enum)
   - **Note**: No auth checks yet - add in Phase 2

3. **System Metrics Endpoint** (2 hours)
   - Write tests for metrics
   - Implement `GET /api/v1/admin/metrics`
   - Return:
     - Total contracts processed
     - Average extraction time
     - Cache hit rate
     - Extractions by status (pending, approved, rejected)
     - Daily/weekly counts
   - Test metrics calculations

4. **Health & Readiness Probes** (0.5 hours)
   - Implement `GET /health` (liveness)
   - Implement `GET /ready` (readiness - DB + Redis check)
   - Test probe responses

**Deliverables:**
- ✅ User management endpoints (auth-ready)
- ✅ System metrics endpoint
- ✅ Health/readiness probes
- ✅ Admin API complete

---

### Day 12 (8 hours): Integration Testing, Docker & Deployment Prep

**Goals**: Comprehensive testing and production readiness

**Tasks:**

1. **Integration Tests** (3 hours)
   - Write end-to-end test: search → extract → approve
   - Write test: search → extract → edit → approve
   - Write test: chat interaction flow
   - Write test: admin user management
   - Test error scenarios (LLM timeout, DB failure)
   - Ensure test coverage >90%

2. **Docker Configuration** (2 hours)
   - Create `Dockerfile` (multi-stage build)
   - Create `.dockerignore`
   - Build and test Docker image locally
   - Optimize image size (<500MB)
   - Test container startup and health checks

3. **Environment Configuration** (1 hour)
   - Create `.env.example` with all required vars
   - Document environment variables in README
   - Add configuration validation on startup
   - Test with different env configurations

4. **API Documentation** (2 hours)
   - FastAPI auto-generates OpenAPI docs
   - Add descriptions to all endpoints
   - Add request/response examples
   - Document error codes and formats
   - Test Swagger UI at `/docs`

**Deliverables:**
- ✅ Integration tests passing (>90% coverage)
- ✅ Docker image built and tested
- ✅ Environment configuration documented
- ✅ API documentation complete (OpenAPI)
- ✅ **Backend ready for deployment!**

---

## Summary: Task Checklist

### Week 1: Database & Core APIs (Days 1-6)
- [ ] Day 1: Project setup, database schema, Alembic migrations
- [ ] Day 2: SQLAlchemy models, repository pattern
- [ ] Day 3: Pydantic schemas, database seeding
- [ ] Day 4: FastAPI setup, contract search API
- [ ] Day 5: LLM abstraction layer (OpenAI, Anthropic)
- [ ] Day 6: Extraction workflow, document service

### Week 2: Approval & Features (Days 7-12)
- [ ] Day 7: Simplified submission workflow (single submit endpoint with corrections)
- [ ] Day 8: Audit logging, event sourcing
- [ ] Day 9: Chat interface backend
- [ ] Day 10: Redis caching layer
- [ ] Day 11: Admin endpoints, user management
- [ ] Day 12: Integration tests, Docker, deployment

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration (Pydantic Settings)
│   ├── database.py             # Database connection, session
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── contracts.py    # Contract search, retrieval
│   │       ├── extractions.py  # Extract, approve, reject, edit
│   │       ├── chat.py         # AI chat interface
│   │       ├── audit.py        # Audit log queries
│   │       └── admin.py        # User management, metrics
│   ├── models/
│   │   ├── __init__.py
│   │   └── database/           # SQLAlchemy models
│   │       ├── __init__.py
│   │       ├── contract.py
│   │       ├── extraction.py
│   │       ├── correction.py
│   │       ├── audit_event.py
│   │       └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # Base repository (CRUD)
│   │   ├── contract_repository.py
│   │   ├── extraction_repository.py
│   │   ├── audit_repository.py
│   │   └── user_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── contract_service.py
│   │   ├── extraction_service.py
│   │   ├── llm_service.py
│   │   ├── document_service.py
│   │   ├── audit_service.py
│   │   └── chat_service.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── llm_providers/
│   │       ├── __init__.py
│   │       ├── base.py         # Abstract base provider
│   │       ├── openai_provider.py
│   │       └── anthropic_provider.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py          # Request/response logging
│   │   └── error_handling.py   # Global error handler
│   └── utils/
│       ├── __init__.py
│       ├── cache.py            # Redis utilities
│       └── validators.py       # Custom validators
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── test_data/              # Sample contracts, responses
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── scripts/
│   └── seed_db.py              # Database seeding
├── .env.example
├── Dockerfile
├── docker-compose.yml          # Local dev environment
├── requirements.txt
├── pyproject.toml              # Poetry config (optional)
├── pytest.ini
└── README.md
```

---

## Dependencies & Risks

### Dependencies
- [ ] PostgreSQL database access (RDS or local)
- [ ] Redis instance (ElastiCache or local)
- [ ] LLM API keys (OpenAI and/or Anthropic)
- [ ] External RDB API details (can mock initially)
- [ ] Document repository API details (can mock initially)

### Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **LLM API rate limits** | Medium | Medium | Implement retry logic, circuit breaker, fallback provider |
| **Database performance** | Low | Medium | Add indexes, use connection pooling, consider read replicas later |
| **External API downtime** | Medium | Low | Graceful degradation, mock responses for development |
| **Scope creep** | High | Medium | Stick to 12-day plan, defer enhancements to Phase 2 |
| **Test coverage gaps** | Low | High | Enforce >90% coverage, TDD approach throughout |

---

## Testing Strategy

### Unit Tests (pytest)
- Test all service methods in isolation
- Test repository CRUD operations
- Test LLM provider implementations (mocked)
- Test Pydantic schema validation
- Target: >90% coverage

### Integration Tests
- Test API endpoints with test database
- Test complete workflows (search → extract → approve)
- Test error scenarios (timeouts, validation failures)
- Test caching behavior

### Manual Testing
- Test with real LLM APIs (OpenAI, Anthropic)
- Test with sample PDF documents
- Test error handling (network failures, timeouts)
- Performance testing (response times)

---

## Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Contract search response time (p95) | < 3 seconds | API logs, monitoring |
| LLM extraction time (p95) | < 10 seconds | Service metrics |
| Cache hit rate | > 70% | Redis metrics |
| API error rate | < 1% | Error logs |
| Test coverage | > 90% | pytest-cov |

---

## Environment Variables

Required environment variables (document in `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/contracts_db
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_DEFAULT=3600

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AWS_BEDROCK_REGION=us-east-1  # If using Bedrock

# Application
APP_ENV=development  # development, staging, production
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# External Services (mock for now)
EXTERNAL_RDB_API_URL=https://api.example.com/contracts
DOCUMENT_REPO_API_URL=https://docs.example.com/api

# Circuit Breaker
LLM_CIRCUIT_BREAKER_THRESHOLD=5
LLM_RETRY_MAX_ATTEMPTS=3
```

---

## Deployment Checklist (Day 12)

- [ ] All integration tests passing
- [ ] Test coverage >90%
- [ ] Docker image built and tested
- [ ] Environment variables documented
- [ ] Health/readiness endpoints working
- [ ] Database migrations applied
- [ ] Seed data loaded (if needed)
- [ ] API documentation complete (Swagger)
- [ ] Error handling tested
- [ ] Logging configured (structured JSON)
- [ ] Ready for frontend integration!

---

## Next Steps After Backend Complete

1. **Frontend Integration**: Connect frontend (Day 6+) to backend APIs
2. **End-to-End Testing**: Test complete user flows
3. **Performance Optimization**: Based on real usage patterns
4. **Auth Integration**: Add Auth0/Okta when provider determined
5. **External Integrations**: Connect real external RDB and document repository
6. **Production Deployment**: Deploy to AWS ECS

---

## Simplifications (Keep It Simple!)

This is a **glorified chatbot with a basic form**. We're intentionally keeping things simple:

1. **No complex workflows** - just search → review → approve
2. **No state machines** - simple status field (pending/approved/rejected)
3. **No background jobs** - synchronous processing is fine for Phase 1
4. **No WebSockets** - regular HTTP is sufficient
5. **No advanced caching** - simple Redis TTL-based caching
6. **No auth complexity** - deferred to Phase 2
7. **Mock external services** - integrate real APIs later

**Remember:** Build the simplest thing that works, test it thoroughly, ship it, then iterate based on real usage.

---

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-09 | Claude Code | Initial backend implementation plan (12 days, no auth) |
| 1.1 | 2025-11-16 | Claude Code | Updated Day 7 to simplified submission workflow. Removed separate approve/reject/edit endpoints in favor of single submit endpoint with corrections array. Corrections stored in both `corrections` table (ML metrics) and `extractions` table (source of truth). |

---

**End of Backend Implementation Plan**
