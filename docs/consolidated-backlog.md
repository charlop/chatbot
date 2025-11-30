# Contract Refund Eligibility System - Consolidated Backlog

**Created**: 2025-11-29
**Status**: Ready for Implementation

---

## Executive Summary

This backlog consolidates remaining work from the backend and frontend implementation plans, plus the new Agentic AI feature. Work is prioritized as:

1. **MVP Completion** - User management (critical), Docker/deployment
2. **Moderate Testing** - Integration tests for critical paths, expand E2E
3. **Agentic AI Phase 1** - Validation Agent only

System metrics dashboard is deferred (data accessible via RDS directly).

---

## Current State

### Backend Status
| Component | Status |
|-----------|--------|
| Days 1-9 (Core APIs) | ✅ Complete |
| Day 10 (Redis Caching) | ✅ Complete |
| Day 11 (Admin Endpoints) | ❌ User CRUD needed, metrics deferred |
| Day 12 (Docker/Tests) | ⚠️ Partial - needs Dockerfile, more integration tests |

### Frontend Status
| Component | Status |
|-----------|--------|
| Days 1-12 (Core MVP) | ✅ Complete |
| Day 13 (Admin - Users) | ❌ Not started |
| Day 14 (Admin - Metrics) | ⏭️ Deferred |
| Days 15-20 (Polish/Tests) | ⚠️ Partial - Dockerfile exists, limited E2E |

### Agentic AI Status
| Component | Status |
|-----------|--------|
| Phase 1: Validation Agent | ❌ Not started |
| Phase 2: Ambiguity Resolution | ⏭️ Deferred |
| Phase 3: Enhanced Chat | ⏭️ Deferred |

---

## Sprint 1: MVP Completion (User Management)

### 1.1 Backend: User Management API
**Priority**: Critical
**Effort**: 1 day

**Tasks**:
1. Create `app/api/v1/admin.py` with user CRUD endpoints:
   - `POST /api/v1/admin/users` - Create user
   - `GET /api/v1/admin/users` - List users (with pagination)
   - `GET /api/v1/admin/users/{user_id}` - Get user by ID
   - `PUT /api/v1/admin/users/{user_id}` - Update user (role, status)
   - `DELETE /api/v1/admin/users/{user_id}` - Soft delete user

2. Create `app/repositories/user_repository.py`:
   - `create()`, `get_by_id()`, `get_all()`, `update()`, `soft_delete()`
   - Handle unique constraints (email)

3. Update `app/main.py` to include admin router

4. Write unit tests for repository and integration tests for endpoints

**Files to Create**:
- `project/backend/app/api/v1/admin.py`
- `project/backend/app/repositories/user_repository.py`
- `project/backend/tests/unit/test_user_repository.py`
- `project/backend/tests/integration/test_admin_api.py`

**Files to Modify**:
- `project/backend/app/main.py` (add admin router)

---

### 1.2 Frontend: Admin Panel - User Management
**Priority**: Critical
**Effort**: 1-2 days

**Tasks**:
1. Create `components/admin/UserTable.tsx`:
   - Display users in table format
   - Columns: Name, Email, Role, Status, Actions
   - Add sorting and filtering
   - Write tests

2. Create `components/admin/UserForm.tsx`:
   - Form for create/edit user
   - Fields: Email, First Name, Last Name, Role
   - Zod validation
   - Write tests

3. Create `app/admin/page.tsx`:
   - Protected route (admin role check can be stubbed for now)
   - UserTable with create/edit/delete actions
   - Modal for UserForm

4. Create `lib/api/admin.ts`:
   - API client methods for user CRUD
   - Write tests

5. Update Sidebar to link to admin page

**Files to Create**:
- `project/frontend/components/admin/UserTable.tsx`
- `project/frontend/components/admin/UserForm.tsx`
- `project/frontend/app/admin/page.tsx`
- `project/frontend/lib/api/admin.ts`
- `project/frontend/__tests__/components/admin/UserTable.test.tsx`
- `project/frontend/__tests__/components/admin/UserForm.test.tsx`
- `project/frontend/__tests__/lib/api/admin.test.ts`

**Files to Modify**:
- `project/frontend/components/layout/Sidebar.tsx` (add admin link)

---

## Sprint 2: Agentic AI - Phase 1 (Validation Agent)

### 2.1 Backend: Validation Agent Service
**Priority**: Medium-High (leadership visibility)
**Effort**: 2-3 days

**Tasks**:
1. Create database schema for validation results:
   ```sql
   CREATE TABLE validation_results (
       validation_id UUID PRIMARY KEY,
       extraction_id UUID REFERENCES extractions,
       validated_at TIMESTAMP,
       overall_status VARCHAR(20), -- pass, warning, fail
       field_validations JSONB,
       insights JSONB,
       suggestions JSONB,
       validation_duration_ms INTEGER
   );
   ```

2. Create validation service (`app/services/validation_agent_service.py`):
   - Orchestrates validation workflow
   - Runs automatically after extraction

3. Create validator tools:
   - `historical_validator.py` - Compare against historical approved extractions
   - `rule_validator.py` - Business logic checks (premium ranges, fee limits)
   - `consistency_validator.py` - Cross-field validation

4. Integrate with extraction flow (call after LLM extraction)

5. Update extraction response to include validation results

**Files to Create**:
- `project/backend/app/services/validation_agent_service.py`
- `project/backend/app/validators/historical_validator.py`
- `project/backend/app/validators/rule_validator.py`
- `project/backend/app/validators/consistency_validator.py`
- `project/backend/app/models/database/validation_result.py`
- `project/backend/tests/unit/test_validation_agent.py`

**Files to Modify**:
- `project/backend/app/services/extraction_service.py` (add validation step)
- `project/backend/app/schemas/responses.py` (add validation to response)
- `project/backend/database/schema.sql` (add validation_results table)

---

### 2.2 Frontend: Validation Display
**Priority**: Medium-High
**Effort**: 1 day

**Tasks**:
1. Create `components/extraction/ValidationBadge.tsx`:
   - Display pass/warning/fail status per field
   - Tooltip with agent's reasoning

2. Create `components/extraction/AgentInsights.tsx`:
   - Expandable panel showing agent's analysis
   - Display suggestions from agent

3. Update `DataCard.tsx` to show validation status

4. Update `DataPanel.tsx` to show overall validation status

**Files to Create**:
- `project/frontend/components/extraction/ValidationBadge.tsx`
- `project/frontend/components/extraction/AgentInsights.tsx`
- `project/frontend/__tests__/components/extraction/ValidationBadge.test.tsx`
- `project/frontend/__tests__/components/extraction/AgentInsights.test.tsx`

**Files to Modify**:
- `project/frontend/components/extraction/DataCard.tsx`
- `project/frontend/components/extraction/DataPanel.tsx`
- `project/frontend/lib/api/extractions.ts` (update types)

---

## Sprint 3: Docker & Deployment

### 3.1 Backend: Dockerfile
**Priority**: Medium
**Effort**: 2-4 hours

**Tasks**:
1. Create `Dockerfile` with multi-stage build:
   - Stage 1: Install dependencies
   - Stage 2: Production image (slim)
   - Include health check
   - Non-root user for security

2. Create `.dockerignore`

3. Test build and run locally

4. Document in README

**Files to Create**:
- `project/backend/Dockerfile`
- `project/backend/.dockerignore`

**Files to Modify**:
- `project/backend/README.md` (Docker instructions)

---

### 3.2 Full Stack: Docker Compose Update
**Priority**: Medium
**Effort**: 2-4 hours

**Tasks**:
1. Update `docker-compose.yml` to include:
   - Backend service (FastAPI)
   - Frontend service (Next.js)
   - PostgreSQL, Redis, LocalStack (already exist)

2. Add production docker-compose.prod.yml variant

3. Update `project/start.sh` to support Docker mode

**Files to Modify**:
- `project/backend/docker-compose.yml`
- `project/start.sh`

**Files to Create**:
- `project/docker-compose.prod.yml` (optional)

---

## Sprint 4: Testing Improvements

### 4.1 Backend: Integration Tests
**Priority**: Medium
**Effort**: 1 day

**Tasks**:
1. Add integration tests for extraction endpoints:
   - `POST /api/v1/extractions/create`
   - `POST /api/v1/extractions/{id}/submit`

2. Add integration tests for chat endpoint:
   - `POST /api/v1/chat`

3. Add integration tests for audit endpoints:
   - `GET /api/v1/audit/contract/{id}`
   - `GET /api/v1/audit/extraction/{id}`

**Files to Create**:
- `project/backend/tests/integration/test_extractions_api.py`
- `project/backend/tests/integration/test_chat_api.py`
- `project/backend/tests/integration/test_audit_api.py`

---

### 4.2 Frontend: E2E Tests
**Priority**: Medium
**Effort**: 1 day

**Tasks**:
1. Expand E2E tests in `e2e/smoke.spec.ts` or create new spec files:
   - Test: Search → View Contract → Submit (no corrections)
   - Test: Search → View → Edit Fields → Submit (with corrections)
   - Test: Chat interaction
   - Test: Admin user management (if implemented)

2. Add test data fixtures

**Files to Create/Modify**:
- `project/frontend/e2e/contract-flow.spec.ts`
- `project/frontend/e2e/admin.spec.ts`

---

### 4.3 Frontend: Unit Test Coverage
**Priority**: Medium
**Effort**: 4-6 hours

**Tasks**:
Add missing tests for:
- `Skeleton.tsx`
- `SearchResults.tsx`
- `PDFViewer.tsx` / `PDFRenderer.tsx`
- `ContractDetailsSkeleton.tsx`
- Dashboard page

**Files to Create**:
- `project/frontend/__tests__/components/ui/Skeleton.test.tsx`
- `project/frontend/__tests__/components/search/SearchResults.test.tsx`
- `project/frontend/__tests__/components/pdf/PDFViewer.test.tsx`

---

## Backlog Summary

| Sprint | Item | Priority | Effort |
|--------|------|----------|--------|
| 1 | Backend: User Management API | Critical | 1 day |
| 1 | Frontend: Admin Panel | Critical | 1-2 days |
| 2 | Backend: Validation Agent | Medium-High | 2-3 days |
| 2 | Frontend: Validation Display | Medium-High | 1 day |
| 3 | Backend: Dockerfile | Medium | 2-4 hours |
| 3 | Docker Compose Update | Medium | 2-4 hours |
| 4 | Backend: Integration Tests | Medium | 1 day |
| 4 | Frontend: E2E Tests | Medium | 1 day |
| 4 | Frontend: Unit Test Coverage | Medium | 4-6 hours |

**Total Estimated Effort**: ~10-12 days

---

## Deferred Items

These items are explicitly deferred and can be added later:

1. **System Metrics Dashboard** (Admin Panel Day 14) - Data accessible via RDS
2. **Agentic AI Phase 2** - Ambiguity Resolution
3. **Agentic AI Phase 3** - Enhanced Agentic Chat
4. **Storybook Documentation**
5. **Comprehensive E2E Suite** (>90% coverage target)

---

## Success Criteria

### MVP Completion
- [ ] User CRUD endpoints working (backend)
- [ ] Admin panel with user management (frontend)
- [ ] Backend containerized with Dockerfile
- [ ] Full stack runnable via docker-compose

### Testing
- [ ] Integration tests for extractions, chat, audit APIs
- [ ] E2E tests for search→view→submit flow
- [ ] Unit tests for untested components

### Agentic AI Phase 1
- [ ] Validation agent runs after every extraction
- [ ] Pass/warning/fail status displayed per field
- [ ] Agent reasoning visible in UI
- [ ] Validation adds <3 seconds to extraction time
