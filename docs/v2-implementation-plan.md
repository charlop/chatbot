# V2 Implementation Plan: Template-Based Contract System

## Overview

Transition from a customer-contract model to a template-based model where:
- Our database stores contract **templates** (no PII, no customer data)
- External database maps Account Numbers → Template IDs
- Users search by account number or template ID
- We display template PDFs with extracted refund eligibility data

## Architectural Decisions

1. **External DB Strategy**: Hybrid cache with fallback (cache → DB → external API → cache result)
2. **PDF Storage**: S3 (our bucket) - no change from current implementation
3. **Data Storage**: Store full template records in database
4. **External API Response**: Returns only Contract Template ID (we look up details locally)

## Implementation Strategy

### Phase 1: Database Schema Changes

#### 1.1 Create Account-Template Mapping Table

**New table**: `account_template_mappings`
```sql
CREATE TABLE account_template_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number VARCHAR(100) NOT NULL UNIQUE,
    contract_template_id VARCHAR(100) NOT NULL,

    -- Cache metadata
    source VARCHAR(50) NOT NULL CHECK (source IN ('external_api', 'manual', 'migrated')),
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_validated_at TIMESTAMP WITH TIME ZONE,

    -- Foreign key to templates (soft reference, allows unknown templates)
    FOREIGN KEY (contract_template_id) REFERENCES contracts(contract_id) ON DELETE CASCADE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_account_mappings_account_number ON account_template_mappings(account_number);
CREATE INDEX idx_account_mappings_template_id ON account_template_mappings(contract_template_id);
CREATE INDEX idx_account_mappings_cached_at ON account_template_mappings(cached_at);
```

**Rationale**:
- Separates account search concerns from template storage
- Enables caching of external API responses
- Tracks cache freshness for invalidation strategy
- Maintains audit trail of mapping sources

#### 1.2 Rename/Clarify Contracts Table

**Option A** (Recommended): Rename table conceptually but keep schema name
- Keep table named `contracts` for backward compatibility
- Update comments to clarify it stores templates
- Remove customer-specific fields

**Option B**: Create new table and migrate
- Create `contract_templates` table
- Migrate data from `contracts`
- Update all foreign keys

**Decision**: **Option A** - Less disruptive, cleaner migration

**Fields to REMOVE**:
```sql
-- Remove customer-specific fields
ALTER TABLE contracts DROP COLUMN customer_name;
ALTER TABLE contracts DROP COLUMN vehicle_info;

-- Remove account_number from contracts (now in mappings table)
ALTER TABLE contracts DROP COLUMN account_number;
```

**Fields to ADD/UPDATE**:
```sql
-- Clarify this is template metadata
ALTER TABLE contracts ADD COLUMN template_version VARCHAR(50);
ALTER TABLE contracts ADD COLUMN effective_date DATE;
ALTER TABLE contracts ADD COLUMN deprecated_date DATE;
ALTER TABLE contracts ADD COLUMN is_active BOOLEAN DEFAULT true;

-- Update comments
COMMENT ON TABLE contracts IS 'Contract templates (not filled customer contracts)';
COMMENT ON COLUMN contracts.contract_id IS 'Template identifier (e.g., GAP-2024-TEMPLATE-001)';
```

**Fields to KEEP** (still relevant for templates):
- contract_id (primary key, now template ID)
- s3_bucket, s3_key (template PDF location)
- document_text (template text for extraction)
- embeddings (for semantic search)
- text_extraction_status
- document_repository_id (external system reference)
- contract_type (GAP, Warranty, etc.)
- contract_date (when template was created)
- created_at, updated_at, last_synced_at

#### 1.3 Update Audit Events

Add new audit event types:
```sql
-- Add to audit_events.event_type CHECK constraint
ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_event_type_check;
ALTER TABLE audit_events ADD CONSTRAINT audit_events_event_type_check
    CHECK (event_type IN ('search', 'view', 'extract', 'edit', 'approve', 'reject', 'chat',
                          'account_lookup', 'template_view', 'mapping_cached'));
```

### Phase 2: Backend API Implementation

#### 2.1 External API Client

**New file**: `/app/integrations/external_rdb/client.py`

```python
class ExternalRDBClient:
    """Client for external Account → Template ID lookup"""

    async def lookup_template_by_account(
        self,
        account_number: str
    ) -> ExternalRDBResponse:
        """
        Query external database for template ID
        Returns: { "contract_template_id": "GAP-2024-TEMPLATE-001" }
        Raises: ExternalRDBError on failure
        """

    async def health_check(self) -> bool:
        """Check if external RDB is reachable"""
```

**Configuration** (`/app/config.py`):
```python
# External RDB API settings
external_rdb_api_url: str = "https://external-db.example.com/api/lookup"
external_rdb_api_key: SecretStr
external_rdb_timeout: int = 5  # seconds
external_rdb_retry_attempts: int = 3
external_rdb_cache_ttl: int = 3600  # 1 hour
```

#### 2.2 Account Mapping Repository

**New file**: `/app/repositories/account_mapping_repository.py`

```python
class AccountMappingRepository(BaseRepository[AccountTemplateMapping]):

    async def get_by_account_number(
        self,
        account_number: str
    ) -> AccountTemplateMapping | None:
        """Get cached mapping by account number"""

    async def create_or_update_mapping(
        self,
        account_number: str,
        template_id: str,
        source: str = "external_api"
    ) -> AccountTemplateMapping:
        """Upsert account-template mapping"""

    async def is_cache_fresh(
        self,
        mapping: AccountTemplateMapping,
        ttl_seconds: int = 3600
    ) -> bool:
        """Check if cached mapping is still fresh"""
```

#### 2.3 Contract Service Updates

**File**: `/app/services/contract_service.py`

Update `search_by_account_number()` method:

```python
async def search_by_account_number(
    self,
    account_number: str
) -> ContractResponse:
    """
    Hybrid lookup strategy:
    1. Check Redis cache (fast path)
    2. Check account_mappings table (DB cache)
    3. Call external API (fallback)
    4. Cache result in both Redis and DB
    5. Fetch template details from contracts table
    """

    # 1. Redis cache check
    cached = await self.redis.get(f"account_mapping:{account_number}")
    if cached:
        template_id = json.loads(cached)["template_id"]
        return await self.get_template_by_id(template_id)

    # 2. DB cache check
    mapping = await self.mapping_repo.get_by_account_number(account_number)
    if mapping and await self.mapping_repo.is_cache_fresh(mapping):
        await self._cache_in_redis(account_number, mapping.contract_template_id)
        return await self.get_template_by_id(mapping.contract_template_id)

    # 3. External API call
    try:
        result = await self.external_client.lookup_template_by_account(account_number)
        template_id = result.contract_template_id

        # 4. Cache in DB and Redis
        await self.mapping_repo.create_or_update_mapping(
            account_number=account_number,
            template_id=template_id,
            source="external_api"
        )
        await self._cache_in_redis(account_number, template_id)

        # 5. Fetch template
        return await self.get_template_by_id(template_id)

    except ExternalRDBError as e:
        # Log error, check if we have stale cache
        if mapping:
            logger.warning(f"External API failed, using stale cache: {e}")
            return await self.get_template_by_id(mapping.contract_template_id)
        raise ContractNotFoundError(f"Account {account_number} not found")
```

Add new method:
```python
async def get_template_by_id(self, template_id: str) -> ContractResponse:
    """Get contract template by ID (no account number needed)"""
    # Existing logic from get_by_id, but clarify it's templates
```

#### 2.4 API Endpoint Updates

**File**: `/app/api/v1/contracts.py`

Update search endpoint to support both search methods:

```python
@router.post("/search", response_model=ContractResponse)
async def search_contract(
    request: ContractSearchRequest,  # Can contain account_number OR contract_id
    service: ContractService = Depends(get_contract_service)
):
    """
    Search for contract template by:
    - account_number: User's account (queries external DB)
    - contract_id: Direct template lookup
    """
    if request.account_number:
        return await service.search_by_account_number(request.account_number)
    elif request.contract_id:
        return await service.get_template_by_id(request.contract_id)
    else:
        raise HTTPException(400, "Provide account_number or contract_id")
```

Update schemas in `/app/schemas/requests.py`:
```python
class ContractSearchRequest(BaseModel):
    account_number: str | None = Field(None, pattern=r'^\d{12}$')
    contract_id: str | None = Field(None, min_length=1, max_length=100)

    @model_validator(mode='after')
    def validate_one_search_param(self):
        if not (self.account_number or self.contract_id):
            raise ValueError("Provide account_number or contract_id")
        if self.account_number and self.contract_id:
            raise ValueError("Provide only one search parameter")
        return self
```

### Phase 3: Frontend Updates

#### 3.1 Terminology Updates

**Files to update**:
- `/components/search/SearchResults.tsx` - Display "Template ID" instead of "Contract ID" where appropriate
- `/app/contracts/[contractId]/page.tsx` - Add context that this is a template, not filled contract
- `/components/extraction/DataPanel.tsx` - Clarify extraction is from template

**Minimal UI changes** (most stays the same):
- Search by account number: works exactly as before
- Results display: slight terminology clarification
- PDF viewer: shows template (no change in functionality)
- Extraction display: same fields, same UI

#### 3.2 API Client Updates

**File**: `/lib/api/contracts.ts`

Update type definitions:
```typescript
export interface Contract {
  contractId: string;  // Now template ID
  // Remove: accountNumber, customerName, vehicleInfo
  contractType: string;
  contractDate: string;
  templateVersion?: string;
  effectiveDate?: string;
  isActive: boolean;
  // ... rest stays same
}

export interface SearchContractRequest {
  accountNumber?: string;  // Search by account
  contractId?: string;      // Search by template ID
}
```

No changes needed to search flow - backend handles the mapping lookup transparently.

#### 3.3 Recent Searches Updates

**File**: `/lib/utils/recentSearches.ts`

Update to track what was searched (account vs template):
```typescript
export interface RecentSearch {
  searchTerm: string;  // Account number or template ID
  searchType: 'account' | 'template';
  templateId: string;  // Resolved template ID
  timestamp: string;
}
```

### Phase 4: Testing & Data

#### 4.1 Update Seed Script

**File**: `/scripts/seed_db.py`

Replace customer contracts with templates:
```python
# Old: Customer-specific contracts
Contract(
    contract_id="GAP-2024-0001",
    account_number="000000000001",
    customer_name="John Doe",
    vehicle_info={"year": 2023, "make": "Toyota"}
)

# New: Contract templates
Contract(
    contract_id="GAP-2024-TEMPLATE-001",
    contract_type="GAP",
    template_version="1.0",
    document_text="[Template language with placeholders]",
    is_active=True
)

# Add account mappings for testing
AccountTemplateMapping(
    account_number="000000000001",
    contract_template_id="GAP-2024-TEMPLATE-001",
    source="migrated"
)
```

Create fewer templates (5-10) but many account mappings (100+) to simulate real usage.

#### 4.2 Mock External API for Tests

**New file**: `/tests/mocks/external_rdb_mock.py`

```python
class MockExternalRDB:
    """Mock external database for testing"""

    def __init__(self):
        self.mappings = {
            "000000000001": "GAP-2024-TEMPLATE-001",
            "000000000002": "GAP-2024-TEMPLATE-001",
            "000000000003": "GAP-2024-TEMPLATE-002",
            # ... more test mappings
        }

    async def lookup_template_by_account(self, account_number: str):
        if account_number in self.mappings:
            return {"contract_template_id": self.mappings[account_number]}
        raise ExternalRDBError("Not found")
```

#### 4.3 Update Existing Tests

**Files to update**:
- `/tests/services/test_contract_service.py` - Update to use templates
- `/tests/repositories/test_contract_repository.py` - Remove account_number queries
- `/tests/api/test_contracts.py` - Test both search methods
- All frontend component tests - Update mock data

### Phase 5: Fresh Start Strategy

#### 5.1 Database Reset

**Decision**: Start with clean database, no migration needed

**Steps**:
1. Archive existing database (optional backup for reference)
2. Drop all tables: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
3. Run schema.sql with updated V2 schema
4. Seed with template data using updated seed_db.py

**Benefits**:
- No complex migration logic
- No data inconsistencies
- Clean slate for template-based model
- Faster implementation

**Trade-off**: Lose historical extraction data (acceptable per user decision)

#### 5.2 No Backward Compatibility Needed

Since we're starting fresh:
- No old data to support
- No deprecated endpoints
- Clean API contracts from day 1
- Frontend and backend deployed together

### Phase 6: Configuration & Deployment

#### 6.1 Environment Variables

Add to `.env`:
```bash
# External RDB API
EXTERNAL_RDB_API_URL=https://external-db.example.com/api/lookup
EXTERNAL_RDB_API_KEY=<secret>
EXTERNAL_RDB_TIMEOUT=5
EXTERNAL_RDB_RETRY_ATTEMPTS=3
EXTERNAL_RDB_CACHE_TTL=3600

# Feature flags
ENABLE_EXTERNAL_RDB=true
ENABLE_HYBRID_CACHE=true
```

#### 6.2 Deployment Sequence

1. **Deploy database changes** (schema migrations)
   - Add new table: `account_template_mappings`
   - Add new columns to `contracts`
   - Run migration script (if converting existing data)

2. **Deploy backend**
   - External API client
   - Updated contract service with hybrid cache
   - Updated API endpoints
   - Verify external API connectivity

3. **Deploy frontend**
   - Updated terminology
   - Updated type definitions
   - Test search flow end-to-end

4. **Cleanup** (after grace period)
   - Remove deprecated columns from `contracts`
   - Remove old API backward compatibility code

## Implementation Order

**Phase 1: Database Schema Changes (Days 1-2)**
1. Update schema.sql with account_template_mappings table
2. Remove customer-specific fields from contracts table
3. Add template versioning fields
4. Update audit_events constraints
5. Test schema on local PostgreSQL

**Phase 2: Backend API Implementation (Days 3-7)**
6. Implement External RDB client (`/app/integrations/external_rdb/`)
7. Create AccountMapping model and repository
8. Update Contract model (remove customer fields)
9. Update contract service with hybrid cache logic
10. Update API endpoints and schemas
11. Add error handling and circuit breakers
12. Write unit tests for new components
13. Write integration tests
14. Test external API mocking

**Phase 3: Frontend Updates (Days 8-9)**
15. Update TypeScript types in `/lib/api/contracts.ts`
16. Update UI terminology in components
17. Update recent searches to track search type
18. Write/update frontend tests

**Phase 4: Testing & Data (Day 10)**
19. Update seed_db.py with template data
20. Create mock External RDB for tests
21. Update existing tests with template data
22. Test complete search flow (account → external API → template → display)
23. Test cache hit scenarios
24. Test external API failure scenarios
25. Performance testing

**Phase 5: Fresh Start Strategy (Day 11)**
26. Archive existing database (optional)
27. Reset database on dev/staging
28. Seed with template data

**Phase 6: Configuration & Deployment (Days 11-12)**
29. Configure environment variables
30. Deploy backend with feature flags
31. Deploy frontend
32. Integration testing on staging
33. Production deployment
34. Monitoring and verification

**Timeline**: ~2-3 weeks with 1-2 developers

## Critical Files to Modify

### Backend
- `/database/schema.sql` - Add account_mappings table
- `/app/integrations/external_rdb/client.py` - NEW
- `/app/repositories/account_mapping_repository.py` - NEW
- `/app/models/database/contract.py` - Remove customer fields
- `/app/models/database/account_mapping.py` - NEW
- `/app/services/contract_service.py` - Hybrid cache logic
- `/app/api/v1/contracts.py` - Updated endpoints
- `/app/schemas/requests.py` - Updated search request
- `/app/schemas/responses.py` - Updated contract response
- `/scripts/seed_db.py` - Template-based seed data

### Frontend
- `/lib/api/contracts.ts` - Updated types and API calls
- `/components/search/SearchResults.tsx` - Terminology updates
- `/app/contracts/[contractId]/page.tsx` - Terminology updates
- `/lib/utils/recentSearches.ts` - Track search type

### Testing
- `/tests/mocks/external_rdb_mock.py` - NEW
- Update all existing test files with template data

## Risk Mitigation

### Risk: External API Downtime
**Impact**: Users can't search by account number
**Mitigation**:
- Stale cache fallback (use expired mapping if external API fails)
- Circuit breaker pattern (fail fast after repeated failures)
- Health monitoring and alerts
- Manual mapping entry endpoint for critical accounts

### Risk: Cache Inconsistency
**Impact**: Users see outdated template for account
**Mitigation**:
- TTL-based cache invalidation (1 hour default)
- Manual cache clear endpoint for admins
- Log cache age in responses for debugging
- Consider cache warming for frequently accessed accounts

### Risk: Template ID Mismatch
**Impact**: External API returns template ID that doesn't exist in our DB
**Mitigation**:
- Soft foreign key (don't enforce constraint)
- Log missing templates for investigation
- Template sync job to fetch missing templates
- Graceful error message to user

### Risk: Performance Degradation
**Impact**: Slow searches when cache misses
**Mitigation**:
- Redis caching at multiple levels
- External API timeout (5s max)
- Async processing where possible
- Monitor p95/p99 latency

### Risk: Fresh Start Data Loss
**Impact**: Lose historical extraction data
**Mitigation**:
- Archive old database before reset (optional)
- Acceptable per user decision
- Clean slate is feature, not bug

## Success Criteria

**Functional**:
- [ ] Users can search by account number and retrieve correct template
- [ ] Users can search directly by template ID
- [ ] External API integration works with proper error handling
- [ ] Cache fallback works when external API is down
- [ ] Frontend displays template information clearly (not customer contract)
- [ ] Extractions can be created and linked to templates
- [ ] Recent searches track both search types (account/template)

**Performance**:
- [ ] Search with cache hit: < 200ms p95
- [ ] Search with cache miss (external API): < 2s p95
- [ ] External API timeout enforced (5s max)
- [ ] Redis cache hit rate > 80%

**Quality**:
- [ ] All tests pass with >90% coverage
- [ ] Integration tests cover external API failure scenarios
- [ ] Mock external API available for development
- [ ] Database schema validated on PostgreSQL

**Deployment**:
- [ ] Database reset successful on dev/staging
- [ ] Backend deployed with monitoring
- [ ] Frontend deployed and functional
- [ ] No runtime errors in production logs (first 24h)

## Architectural Decisions (Finalized)

### Template Versioning
**Decision**: Simple version field
- Add `template_version` VARCHAR(50) field to contracts table
- Add `effective_date` DATE field for when version became active
- Add `deprecated_date` DATE field for when version was superseded
- New version = update existing template record with new version number
- Extractions reference the template version they used

### Migration Strategy
**Decision**: Start fresh (templates only)
- Drop existing database and seed with clean template data
- No historical data migration needed
- Simpler, cleaner implementation
- Existing system can be archived if needed for reference

### Analytics
**Decision**: Use audit log only
- No additional analytics fields on contracts table
- Query `audit_events` for usage patterns
- Keeps data model simple and focused
- Sufficient for current needs

### Cache Invalidation
Manual cache refresh endpoint:
```python
@router.post("/admin/cache/clear/{account_number}")
async def clear_account_cache(account_number: str):
    """Clear cached mapping for specific account (admin only)"""
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Final - Ready for Implementation
