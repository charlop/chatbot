# Implementation Plan
## Contract Refund Eligibility System - Phase 1

**Version:** 1.0
**Date:** 2025-11-06
**Project Type:** Greenfield - New Development
**Timeline:** 12 Weeks

---

## Table of Contents

1. [Infrastructure (Weeks 1-2)](#1-infrastructure-weeks-1-2)
2. [Database (RDS PostgreSQL) (Weeks 2-3)](#2-database-rds-postgresql-weeks-2-3)
3. [Backend (Python) (Weeks 3-6)](#3-backend-python-weeks-3-6)
4. [Frontend (Next.js + React) (Weeks 6-9)](#4-frontend-nextjs--react-weeks-6-9)
5. [Integration & Testing (Weeks 9-11)](#5-integration--testing-weeks-9-11)
6. [Deployment & Launch (Week 12)](#6-deployment--launch-week-12)

---

## 1. INFRASTRUCTURE (Weeks 1-2)

### 1.1 AWS Foundation Setup

**AWS Account & Organization**
- Set up dedicated AWS account for the project
- Configure IAM users and roles (least privilege principle)
- Enable CloudTrail for audit logging
- Set up billing alerts and cost monitoring

**Network Infrastructure (Terraform)**
- VPC creation in US-East-1 (or customer preference)
- Multi-AZ subnets (public, private, data tier)
- Internet Gateway and NAT Gateways
- Route tables and network ACLs
- VPC endpoints for S3, Secrets Manager, CloudWatch
- Security groups (application, database, load balancer tiers)

### 1.2 Core Services Setup

**Secrets Management**
- AWS Secrets Manager for:
  - RDS credentials
  - LLM API keys (OpenAI, Anthropic, Bedrock)
  - JWT signing keys
  - External API credentials
- Rotation policies configured

**Storage (S3)**
- Bucket for PDFs with lifecycle policies:
  - Hot storage (< 1 year): S3 Standard
  - Warm storage (1-7 years): S3 Intelligent-Tiering
  - Cold storage (7+ years): S3 Glacier
- Enable versioning and encryption (SSE-S3)
- CloudFront distribution for PDF delivery
- CORS configuration for frontend access

**Container Infrastructure (ECS Fargate)**
- ECS cluster creation
- Task definitions (backend API)
- Application Load Balancer (ALB)
- Target groups with health checks
- Auto-scaling policies (CPU/memory based)
- Service discovery (AWS Cloud Map - optional)

**Caching (ElastiCache Redis)**
- Redis cluster (multi-AZ for HA)
- Parameter group configuration
- Security group with access from ECS only
- Use cases: session management, API response caching

### 1.3 CI/CD Pipeline

**GitHub Actions / AWS CodePipeline**
- Source stage: GitHub repository
- Build stage: Docker image builds (frontend + backend)
- Test stage: Unit tests, integration tests, security scans
- Deploy stage: ECS service updates (blue/green deployment)
- Rollback capabilities

**Container Registry (ECR)**
- Repositories for frontend and backend images
- Image scanning enabled
- Lifecycle policies (retain last 10 images)

### 1.4 Monitoring & Observability

**CloudWatch**
- Log groups for: ECS tasks, ALB, RDS, Lambda (if used)
- Metrics dashboards (API latency, error rates, LLM call times)
- Alarms for: High error rates, slow response times, database CPU

**Application Monitoring**
- Structured logging (JSON format)
- Correlation IDs for request tracing
- Custom metrics for business KPIs (extraction accuracy, cache hit rate)

### 1.5 Security Foundation

**TLS/SSL**
- AWS Certificate Manager (ACM) for HTTPS
- TLS 1.2+ enforcement on ALB

**WAF (Optional but Recommended)**
- Rate limiting rules
- SQL injection protection
- XSS protection

**Infrastructure Deliverables:**
- Terraform modules for all AWS resources
- Runbook for infrastructure operations
- Disaster recovery procedures (RTO: 4 hours, RPO: 1 hour)

---

## 2. DATABASE (RDS PostgreSQL) (Weeks 2-3)

### 2.1 RDS Instance Setup

**Database Configuration**
- Engine: PostgreSQL 15.x (latest stable)
- Instance class: db.t3.medium (start small, scale up)
- Multi-AZ deployment for high availability
- Storage: 100GB GP3 with auto-scaling enabled
- Automated backups: 7-day retention, daily snapshots
- Encryption at rest enabled (AWS KMS)
- Enhanced monitoring enabled (60-second granularity)

**Network & Security**
- Deploy in private subnets only
- Security group allowing access from ECS tasks only
- Parameter group for performance tuning
- Option group (if extensions needed)

### 2.2 Database Schema Design

**Core Tables:**

```sql
-- Users and Authentication
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Contract metadata (synced from external RDB)
CREATE TABLE contracts (
    contract_id VARCHAR(100) PRIMARY KEY,
    account_number VARCHAR(100) NOT NULL,
    pdf_url TEXT NOT NULL,
    document_repository_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_contracts_account_number ON contracts(account_number);

-- Extracted data from LLM
CREATE TABLE extractions (
    extraction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id VARCHAR(100) REFERENCES contracts(contract_id),
    gap_insurance_premium DECIMAL(10,2),
    gap_premium_confidence DECIMAL(5,2), -- 0-100
    gap_premium_source JSONB, -- {page, section, line}
    refund_calculation_method VARCHAR(100),
    refund_method_confidence DECIMAL(5,2),
    refund_method_source JSONB,
    cancellation_fee DECIMAL(10,2),
    cancellation_fee_confidence DECIMAL(5,2),
    cancellation_fee_source JSONB,
    llm_model_version VARCHAR(100) NOT NULL,
    processing_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    extracted_by UUID REFERENCES users(user_id),
    UNIQUE(contract_id) -- Only one extraction per contract
);
CREATE INDEX idx_extractions_contract_id ON extractions(contract_id);
CREATE INDEX idx_extractions_status ON extractions(status);

-- User corrections (for tracking AI vs human values)
CREATE TABLE corrections (
    correction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID REFERENCES extractions(extraction_id),
    field_name VARCHAR(50) NOT NULL,
    original_value TEXT,
    corrected_value TEXT NOT NULL,
    correction_reason TEXT,
    corrected_by UUID REFERENCES users(user_id),
    corrected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_corrections_extraction_id ON corrections(extraction_id);

-- Event Sourcing: Immutable audit log
CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- 'search', 'view', 'edit', 'approve', 'reject'
    contract_id VARCHAR(100) REFERENCES contracts(contract_id),
    extraction_id UUID REFERENCES extractions(extraction_id),
    user_id UUID REFERENCES users(user_id),
    event_data JSONB, -- Flexible JSON for storing event-specific data
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
CREATE INDEX idx_audit_events_contract_id ON audit_events(contract_id);
CREATE INDEX idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);
CREATE INDEX idx_audit_events_event_type ON audit_events(event_type);

-- User sessions (may use Redis instead, but schema for reference)
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    jwt_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

### 2.3 Database Optimizations

- **Indexes**: Created on foreign keys and frequently queried columns
- **Partitioning**: Consider partitioning `audit_events` by month (after 6 months)
- **Connection Pooling**: Use PgBouncer or application-level pooling
- **Read Replicas**: Add if read-heavy workload emerges

### 2.4 Data Migration & Seeding

**Initial seed data:**
- Admin user account
- Sample contracts for testing
- Configuration values (confidence thresholds)

**Nightly batch sync:**
- Lambda function or ECS scheduled task
- Sync contract IDs from external RDB to `contracts` table
- Idempotent inserts (ON CONFLICT DO UPDATE)

**Database Deliverables:**
- SQL schema files (versioned)
- Migration scripts (using Alembic or Flyway)
- ER diagram
- Data dictionary

---

## 3. BACKEND (Python) (Weeks 3-6)

### 3.1 Framework & Architecture

- **Framework**: FastAPI (high performance, async support, OpenAPI docs)
- **Architecture Pattern**: Clean Architecture / Layered Architecture
  - **API Layer**: FastAPI routes, request/response models
  - **Service Layer**: Business logic, orchestration
  - **Repository Layer**: Database access (SQLAlchemy ORM)
  - **Integration Layer**: External APIs (LLM, document repo, external RDB)

### 3.2 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management (env vars)
│   ├── dependencies.py         # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── contracts.py    # Contract search, retrieval
│   │   │   ├── extractions.py  # Approve, edit, reject
│   │   │   ├── chat.py         # AI chat interface
│   │   │   └── admin.py        # Admin user management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── contract_service.py # Contract search logic
│   │   ├── extraction_service.py # AI extraction orchestration
│   │   ├── llm_service.py      # LLM abstraction layer
│   │   ├── document_service.py # Document repository integration
│   │   ├── audit_service.py    # Event sourcing
│   │   └── auth_service.py     # JWT generation, validation
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── contract_repository.py
│   │   ├── extraction_repository.py
│   │   └── audit_repository.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain/             # Domain models (business logic)
│   │   └── database/           # SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── llm_providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Abstract base class
│   │   │   ├── openai.py       # OpenAI implementation
│   │   │   ├── anthropic.py    # Anthropic implementation
│   │   │   └── bedrock.py      # AWS Bedrock implementation
│   │   ├── document_repo_client.py
│   │   └── external_rdb_client.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── authentication.py   # JWT middleware
│   │   ├── logging.py          # Request/response logging
│   │   └── error_handling.py   # Global error handler
│   └── utils/
│       ├── __init__.py
│       ├── cache.py            # Redis caching utilities
│       ├── circuit_breaker.py  # Circuit breaker for LLM
│       └── validators.py       # Custom validators
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                    # Database migrations
├── Dockerfile
├── requirements.txt
└── README.md
```

### 3.3 Core Components Implementation

#### 3.3.1 Authentication & Authorization

- **JWT-based authentication**
  - Login endpoint: POST `/api/v1/auth/login`
  - Token refresh endpoint: POST `/api/v1/auth/refresh`
  - Logout endpoint: POST `/api/v1/auth/logout`

- **RBAC Middleware**
  - Decorator for role checking: `@require_role("admin")`
  - User context injection into requests

- **Password Security**
  - bcrypt hashing (12 rounds minimum)
  - Password complexity requirements

#### 3.3.2 Contract Search & Retrieval

**Endpoint**: `POST /api/v1/contracts/search`

Flow:
1. Validate account number format
2. Check local cache (Redis) for previous extraction
3. If cached, return from database
4. If not cached:
   a. Query external RDB API for contract_id
   b. If not found, return 404
   c. Store contract metadata in local DB
5. Log audit event (search)
6. Return contract metadata

**Endpoint**: `GET /api/v1/contracts/{contract_id}`

Flow:
1. Check if extraction exists in database
2. If exists and approved, return cached extraction
3. If not, trigger extraction workflow
4. Log audit event (view)

#### 3.3.3 LLM Extraction Service (Core Component)

**LLM Abstraction Layer** (Vendor-agnostic):

```python
# Base interface
class LLMProvider(ABC):
    @abstractmethod
    async def extract_contract_data(
        self,
        text: str,
        contract_id: str
    ) -> ExtractionResult:
        pass
```

**Extraction Flow**:

Endpoint: `POST /api/v1/extractions/{contract_id}/extract`

1. Retrieve PDF text/embeddings from document repository
2. Prepare extraction prompt with structured output schema
3. Call LLM with circuit breaker pattern:
   - Max 3 retries with exponential backoff
   - Timeout: 15 seconds
   - Circuit opens after 5 consecutive failures
4. Parse structured output (function calling / JSON mode):
   ```json
   {
     "gap_insurance_premium": {
       "value": 1250.00,
       "confidence": 0.95,
       "source": {"page": 3, "section": "Coverage Details"}
     },
     "refund_calculation_method": {
       "value": "Pro-Rata",
       "confidence": 0.88,
       "source": {"page": 5, "section": "Cancellation Terms"}
     },
     "cancellation_fee": {
       "value": 50.00,
       "confidence": 0.92,
       "source": {"page": 5, "section": "Fees"}
     }
   }
   ```
5. Store extraction in database (status: pending)
6. Log audit event (extraction)
7. Return extraction data

**Prompt Engineering** (Git-versioned):

```
You are analyzing a vehicle service contract (GAP insurance) for refund eligibility.

Extract the following information:

1. GAP Insurance Premium: The total premium amount paid for GAP insurance coverage
2. Refund Calculation Method: The method used to calculate refunds (e.g., Pro-Rata, Rule of 78s, Flat Fee)
3. Cancellation Fee: Any fee charged for cancelling the contract

For each field, provide:
- value: The extracted value
- confidence: Your confidence level (0.0 to 1.0)
- source: The location in the document (page number, section name)

Return your response in the following JSON format:
{schema}
```

#### 3.3.4 Review & Approval Endpoints

**Approve**: `POST /api/v1/extractions/{extraction_id}/approve`

Flow:
1. Validate extraction exists and status is 'pending'
2. Update status to 'approved'
3. Log audit event (approve)
4. Return success

**Edit**: `POST /api/v1/extractions/{extraction_id}/edit`

Request body:
```json
{
  "field_name": "gap_insurance_premium",
  "corrected_value": "1350.00",
  "correction_reason": "OCR error, verified manually"
}
```

Flow:
1. Validate extraction exists
2. Store correction in corrections table
3. Update extraction with corrected value
4. Log audit event (edit)
5. Return updated extraction

**Reject**: `POST /api/v1/extractions/{extraction_id}/reject`

Request body:
```json
{
  "reason": "Incorrect contract type - not GAP insurance"
}
```

Flow:
1. Update status to 'rejected'
2. Log audit event (reject) with reason
3. Return success

#### 3.3.5 AI Chat Interface

**Endpoint**: `POST /api/v1/chat`

Request body:
```json
{
  "contract_id": "ABC123",
  "message": "What is the refund policy for early cancellation?",
  "history": []
}
```

Flow:
1. Retrieve contract text from document repository
2. Build context with contract data + chat history
3. Call LLM with chat-optimized prompt
4. Stream response (Server-Sent Events)
5. Log audit event (chat)
6. Return AI response with sources

**Special command detection**:
- If message is an account number, trigger contract search
- If message is "search [account_number]", trigger search

#### 3.3.6 Admin Endpoints

**User Management**:
- `GET /api/v1/admin/users` - List all users
- `POST /api/v1/admin/users` - Create new user
- `PUT /api/v1/admin/users/{user_id}` - Update user (role, active status)
- `DELETE /api/v1/admin/users/{user_id}` - Soft delete user

**System Metrics**:
- `GET /api/v1/admin/metrics` - System health, extraction stats, cache hit rate

### 3.4 Caching Strategy (Redis)

- **Session data**: 4-hour TTL
- **Extraction results**: 1-hour TTL (cache key: `extraction:{contract_id}`)
- **Document text**: 30-minute TTL (cache key: `document:{contract_id}`)
- **External RDB lookups**: 15-minute TTL (cache key: `contract:{account_number}`)

### 3.5 Error Handling

- **Custom exceptions** for each error type
- **Global error handler** middleware
- **Structured error responses**:

```json
{
  "error": {
    "code": "CONTRACT_NOT_FOUND",
    "message": "Contract with account number 12345 not found",
    "details": null,
    "timestamp": "2025-11-06T10:30:00Z"
  }
}
```

### 3.6 Testing Strategy (TDD)

- **Unit tests**: All service layer methods (pytest)
- **Integration tests**: API endpoints with test database
- **Mocking**: External APIs (LLM, document repo, external RDB)
- **Coverage target**: > 90%

**Backend Deliverables:**
- FastAPI application with OpenAPI documentation
- LLM abstraction layer with 3 providers
- Complete test suite
- API documentation
- Docker image in ECR

---

## 4. FRONTEND (Next.js + React) (Weeks 6-9)

### 4.1 Framework & Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (Lightspeed design system)
- **PDF Viewer**: PDF.js (react-pdf wrapper)
- **State Management**: React Context API + SWR for data fetching
- **Form Handling**: React Hook Form + Zod validation
- **HTTP Client**: Axios with interceptors

### 4.2 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Landing page (redirects to /dashboard)
│   │   ├── login/
│   │   │   └── page.tsx        # Login page
│   │   ├── dashboard/
│   │   │   └── page.tsx        # Main contract review UI
│   │   └── admin/
│   │       └── page.tsx        # Admin panel
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx     # 64px navigation sidebar
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── search/
│   │   │   └── SearchBar.tsx   # Account number search
│   │   ├── pdf/
│   │   │   ├── PDFViewer.tsx   # 840px PDF display
│   │   │   └── PDFControls.tsx # Zoom, page nav, download
│   │   ├── extraction/
│   │   │   ├── DataPanel.tsx   # 464px data panel
│   │   │   ├── DataCard.tsx    # Individual field display
│   │   │   ├── ConfidenceBadge.tsx # Color-coded badges
│   │   │   └── EditField.tsx   # Inline editing
│   │   ├── audit/
│   │   │   └── AuditTrail.tsx  # Audit information display
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx # Expandable chat (92px → 400px)
│   │   │   └── ChatMessage.tsx
│   │   ├── admin/
│   │   │   ├── UserTable.tsx
│   │   │   └── UserForm.tsx
│   │   └── ui/
│   │       ├── Button.tsx      # Lightspeed styled buttons
│   │       ├── Input.tsx
│   │       ├── Card.tsx
│   │       └── Modal.tsx
│   ├── contexts/
│   │   ├── AuthContext.tsx     # Authentication state
│   │   └── ContractContext.tsx # Current contract state
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useContract.ts
│   │   ├── useExtraction.ts
│   │   └── useChat.ts
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts       # Axios instance with interceptors
│   │   │   ├── auth.ts         # Auth API calls
│   │   │   ├── contracts.ts    # Contract API calls
│   │   │   ├── extractions.ts  # Extraction API calls
│   │   │   └── chat.ts         # Chat API calls
│   │   ├── utils/
│   │   │   ├── formatters.ts   # Currency, date formatters
│   │   │   └── validators.ts   # Form validators
│   │   └── constants/
│   │       ├── colors.ts       # Lightspeed color palette
│   │       └── config.ts       # App configuration
│   ├── types/
│   │   ├── contract.ts
│   │   ├── extraction.ts
│   │   ├── user.ts
│   │   └── api.ts
│   └── styles/
│       └── globals.css         # Tailwind imports, custom styles
├── public/
│   └── assets/
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── package.json
└── README.md
```

### 4.3 Key Components Implementation

#### 4.3.1 Authentication Flow

- **Login Page** (`/login`)
  - Username/password form
  - JWT stored in httpOnly cookie (secure)
  - Redirect to `/dashboard` on success

- **Auth Context**
  - Provides user info, role, logout function
  - Automatic token refresh (before expiry)
  - Protected route wrapper component

#### 4.3.2 Main Dashboard Layout

**Layout Structure** (see mockup: `finance-specialist-ui.svg`):

```
┌─────────────────────────────────────────────────────────────┐
│ Header (Search Bar)                                        │
├──────┬──────────────────────────────────┬──────────────────┤
│      │                                  │                  │
│ Side │     PDF Viewer (840px)           │  Data Panel      │
│ bar  │                                  │  (464px)         │
│ 64px │                                  │                  │
│      │                                  │  - GAP Premium   │
│      │                                  │  - Refund Method │
│      │                                  │  - Cancel Fee    │
│      │                                  │  - Audit Trail   │
│      │                                  │  - Actions       │
│      │                                  │                  │
├──────┴──────────────────────────────────┴──────────────────┤
│ Chat Interface (Expandable: 92px collapsed → 400px open)   │
└─────────────────────────────────────────────────────────────┘
```

#### 4.3.3 Search Component

```tsx
// SearchBar.tsx
- Auto-focus on mount
- Account number input (formatted: XXXX-XXXX-XXXX)
- Search button with loading state
- Error message display
- Recent searches dropdown (local storage)
```

#### 4.3.4 PDF Viewer Component

```tsx
// PDFViewer.tsx using react-pdf
- PDF.js integration
- Page navigation (prev/next, jump to page)
- Zoom controls (50%, 100%, 150%, 200%, fit-width)
- Download button
- Highlight overlays (positioned absolutely)
- Color-coded highlights matching confidence levels:
  - Green: High confidence (> 90%)
  - Orange: Medium confidence (70-90%)
  - Red: Low confidence (< 70%)
- Auto-scroll to highlighted sections
```

#### 4.3.5 Data Panel Component

```tsx
// DataPanel.tsx (464px width, right-aligned)
<Card>
  <DataCard
    label="GAP Insurance Premium"
    value="$1,250.00"
    confidence={95}
    source={{page: 3, section: "Coverage Details"}}
    onEdit={handleEdit}
    onViewInDocument={scrollToSection}
  />
  <DataCard
    label="Refund Calculation Method"
    value="Pro-Rata"
    confidence={88}
    source={{page: 5, section: "Cancellation Terms"}}
  />
  <DataCard
    label="Cancellation Fee"
    value="$50.00"
    confidence={92}
    source={{page: 5, section: "Fees"}}
  />

  <AuditTrail
    processedBy="jane.doe@company.com"
    processedAt="2025-11-06T10:30:00Z"
    modelVersion="gpt-4-turbo-2024-04-09"
    processingTime="8.2 seconds"
  />

  <ActionButtons>
    <Button variant="success" onClick={handleApprove}>
      Approve
    </Button>
    <Button variant="outline" onClick={handleReject}>
      Reject
    </Button>
  </ActionButtons>
</Card>
```

#### 4.3.6 Confidence Badge Component

```tsx
// ConfidenceBadge.tsx
- Color-coded based on confidence:
  - Green (#2da062): ≥ 90%
  - Orange (#fe8700): 70-89%
  - Red (#dc3545): < 70%
- Displays percentage
- Tooltip with interpretation
```

#### 4.3.7 Inline Edit Component

```tsx
// EditField.tsx
- Click "Edit" button to enable editing
- Inline input field appears
- Save/Cancel buttons
- Correction reason (optional textarea)
- Validation on save
- Optimistic UI update
```

#### 4.3.8 Chat Interface Component

```tsx
// ChatInterface.tsx
- Collapsed state: 92px height, input + icons visible
- Expanded state: 300-400px height, full chat history
- Smooth animation on expand/collapse
- Message history (scrollable)
- Typing indicator for AI responses
- Support for:
  - Contract questions
  - Account number search (auto-detects number format)
  - Follow-up questions
- Context indicator showing active contract
```

#### 4.3.9 Admin Panel

```tsx
// Admin page (/admin)
- User table (username, email, role, status, actions)
- Create user button → modal form
- Edit user → modal form
- Deactivate user (soft delete)
- Role toggle (Admin ↔ User)
- System metrics dashboard:
  - Total contracts processed
  - Average extraction time
  - Cache hit rate
  - Daily active users
```

### 4.4 Styling (Tailwind + Lightspeed Design)

**Tailwind Config**:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        lightspeed: {
          purple: '#954293',
          'purple-dark': '#7a3577',
          green: '#2da062',
          orange: '#fe8700',
          'gray-light': '#f4f4f4',
          'gray-medium': '#e7eaf7',
          'gray-dark': '#737373',
          'gray-darker': '#1a1a1a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    }
  }
}
```

### 4.5 State Management Strategy

- **Authentication**: React Context (AuthContext)
- **Contract data**: SWR for caching and revalidation
- **Chat history**: Local state (useReducer)
- **Form state**: React Hook Form

### 4.6 API Integration

```ts
// lib/api/client.ts
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Include cookies
});

// Request interceptor: Add JWT to headers
apiClient.interceptors.request.use((config) => {
  const token = getToken(); // From cookie or localStorage
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401, refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      await refreshToken();
      // Retry original request
    }
    return Promise.reject(error);
  }
);
```

### 4.7 Testing Strategy

- **Unit tests**: Component logic (Vitest + React Testing Library)
- **Integration tests**: User flows (Playwright)
- **E2E tests**: Full workflow (search → review → approve)
- **Visual regression**: Storybook + Chromatic

**Frontend Deliverables:**
- Next.js application matching mockups
- Responsive layout (desktop only in Phase 1)
- Complete component library
- Docker image in ECR
- Storybook documentation

---

## 5. INTEGRATION & TESTING (Weeks 9-11)

### 5.1 External System Integrations

#### Integration 1: External RDB (Contract Source)

- **Mock implementation** for development
- **API client** with circuit breaker
- **Test data** for 100+ sample account numbers
- **Error handling** for:
  - Contract not found
  - API timeout
  - Network errors

#### Integration 2: Document Repository

- **Mock implementation** with sample PDFs
- **API client** for:
  - `GET /documents/{contract_id}/pdf`
  - `GET /documents/{contract_id}/text`
  - `GET /documents/{contract_id}/embeddings`
- **Caching strategy** (30-minute TTL)

#### Integration 3: LLM Providers

- **OpenAI**: GPT-4 Turbo with function calling
- **Anthropic**: Claude 3 Opus with tool use
- **AWS Bedrock**: Claude via Bedrock API
- **Fallback strategy**: Try providers in order until success

### 5.2 End-to-End Testing

**Test Scenarios**:
1. Happy path: Search → Extract → Approve
2. Correction flow: Search → Extract → Edit → Approve
3. Rejection flow: Search → Extract → Reject
4. Cache hit: Search previously processed contract
5. Chat interaction: Ask question about contract
6. Chat search: Search for new contract via chat
7. Admin: Create user, change role
8. Error handling: Contract not found, LLM timeout, API errors

### 5.3 Performance Testing

- **Load testing** with k6 or Locust:
  - 50 concurrent users
  - 1,000 contracts/day simulation
- **Response time validation**:
  - Search < 3 seconds (p95)
  - Extraction < 10 seconds (p95)
  - PDF load < 2 seconds
- **Database query optimization**: Check slow query log

### 5.4 Security Testing

- **OWASP Top 10 checks**:
  - SQL injection (parameterized queries)
  - XSS (input sanitization)
  - CSRF (SameSite cookies)
  - Authentication bypass attempts
  - Authorization checks (role-based access)
- **Penetration testing** (manual or automated tools)
- **Secrets scanning** (git-secrets, TruffleHog)

### 5.5 User Acceptance Testing (UAT)

- **Test group**: 5-10 finance users
- **Test period**: 1 week
- **Feedback collection**:
  - Usability issues
  - Extraction accuracy
  - Performance concerns
  - Feature requests

---

## 6. DEPLOYMENT & LAUNCH (Week 12)

### 6.1 Production Deployment Checklist

- [ ] Environment variables configured in AWS Secrets Manager
- [ ] Database backups enabled and tested
- [ ] CloudFront CDN configured for PDFs
- [ ] SSL certificates provisioned (ACM)
- [ ] WAF rules enabled
- [ ] Auto-scaling policies tested
- [ ] Monitoring dashboards configured
- [ ] Alarms configured (Slack/email notifications)
- [ ] Runbooks documented (incident response)
- [ ] Disaster recovery plan tested

### 6.2 Data Migration

- [ ] Nightly batch sync job deployed (contract IDs)
- [ ] Historical data loaded (if any)
- [ ] Data validation completed

### 6.3 User Training

- [ ] Training documentation created
- [ ] Video tutorials recorded
- [ ] Live training sessions conducted
- [ ] Support contacts documented

### 6.4 Launch

- [ ] Soft launch (pilot group of 5 users)
- [ ] Monitor metrics for 3 days
- [ ] Full launch to all finance users
- [ ] Post-launch support (on-call for 1 week)

### 6.5 Success Metrics Tracking

- [ ] Analytics configured (Mixpanel/Amplitude/custom)
- [ ] Dashboard for KPIs:
  - Time to review contract
  - Contracts processed per day
  - Extraction accuracy
  - Cache hit rate
  - User error rate

---

## Summary: Timeline & Dependencies

| Phase | Duration | Key Deliverables | Dependencies |
|-------|----------|------------------|--------------|
| **Infrastructure** | Weeks 1-2 | AWS setup, Terraform, CI/CD | AWS account access |
| **Database** | Weeks 2-3 | RDS setup, schema, migrations | Infrastructure |
| **Backend** | Weeks 3-6 | FastAPI app, LLM integration, APIs | Database |
| **Frontend** | Weeks 6-9 | Next.js app, UI components | Backend APIs |
| **Integration & Testing** | Weeks 9-11 | External integrations, E2E tests | Frontend + Backend |
| **Deployment & Launch** | Week 12 | Production deployment, training | UAT completion |

**Critical Path**: Infrastructure → Database → Backend → Frontend → Testing → Launch

**Parallel Work Opportunities**:
- Frontend development can start while backend APIs are being built (use mocks)
- Infrastructure can be set up while database schema is being designed
- Testing framework can be set up early in each phase

---

## Next Steps

1. Review and approve implementation plan
2. Set up development environment
3. Begin database schema implementation
4. Start infrastructure provisioning (when ready)
5. Initialize backend and frontend repositories

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-06 | Claude Code | Initial implementation plan based on PRD |
