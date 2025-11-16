# PDF Streaming Architecture

**Date:** November 15, 2025
**Status:** Approved
**Version:** 1.0

## Overview

This document describes the architecture for serving PDF documents from S3 with IAM authentication via a backend proxy endpoint, including caching strategy and integration with the external document ETL pipeline.

## Problem Statement

### Original Architecture (Incorrect Assumption)
- PDFs assumed to be publicly accessible via direct URLs
- Frontend loaded PDFs directly from URLs in iframe
- No authentication or access control
- No server-side caching

### Requirements
1. PDFs stored in S3 with IAM authentication (NOT publicly accessible)
2. Frontend must display PDFs in viewer
3. Backend must stream PDFs securely
4. Document text and embeddings populated by external ETL (batch process)
5. High performance with caching
6. Audit trail for all PDF access

## Architecture Decision

### Chosen Approach: Backend Proxy with Streaming

**Rejected Alternative:** Presigned S3 URLs

**Rationale:**
- ✅ **Security:** All S3 credentials stay server-side
- ✅ **Access Control:** Fine-grained permission checks before streaming
- ✅ **Caching:** Redis cache reduces S3 bandwidth costs
- ✅ **Audit Trail:** Every PDF access logged with user context
- ✅ **Simplicity:** Frontend doesn't need URL refresh logic
- ✅ **Flexibility:** Can add transformations, watermarks, redactions in future

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ External Document ETL Pipeline (Batch Process)                  │
│ - Runs nightly/periodically                                     │
│ - OCRs PDFs, generates embeddings                              │
│ - Populates Postgres with: text, embeddings, S3 paths          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │   PostgreSQL   │
        │   contracts    │
        │   - s3_bucket  │
        │   - s3_key     │
        │   - doc_text   │
        │   - embeddings │
        └────────┬───────┘
                 │
┌────────────────┴────────────────┐
│         Backend API             │
│  ┌──────────────────────────┐  │
│  │ GET /contracts/{id}/pdf  │  │
│  │                          │  │
│  │ 1. Check Redis cache     │  │
│  │ 2. Query DB for S3 info  │  │
│  │ 3. Stream from S3        │  │
│  │ 4. Cache in Redis        │  │
│  │ 5. Log audit event       │  │
│  └──────────────────────────┘  │
└─────────────────┬───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   Frontend      │
         │   <iframe>      │
         │   src="/api/... │
         └─────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────┐
│ Frontend (Next.js)                                       │
│                                                          │
│  PDFViewer.tsx                                          │
│    └─> <iframe src="/api/v1/contracts/{id}/pdf" />     │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Backend API (FastAPI)                                    │
│                                                          │
│  ┌─────────────────────────────────────────┐            │
│  │ contracts.py                            │            │
│  │                                         │            │
│  │ GET /contracts/{contract_id}/pdf       │            │
│  │   ├─> auth_middleware.verify_user()    │            │
│  │   ├─> contract_service.get_pdf_stream()│            │
│  │   └─> audit_service.log_access()       │            │
│  └──────────────┬──────────────────────────┘            │
│                 │                                        │
│  ┌──────────────▼──────────────────────────┐            │
│  │ contract_service.py                     │            │
│  │                                         │            │
│  │ get_pdf_stream(contract_id)            │            │
│  │   ├─> Check Redis                      │            │
│  │   ├─> Query DB for s3_bucket/key       │            │
│  │   └─> Call s3_service                  │            │
│  └──────────────┬──────────────────────────┘            │
│                 │                                        │
│  ┌──────────────▼──────────────────────────┐            │
│  │ s3_service.py                           │            │
│  │                                         │            │
│  │ stream_pdf(bucket, key)                │            │
│  │   ├─> boto3.S3.get_object()            │            │
│  │   ├─> StreamingResponse()              │            │
│  │   └─> Cache in Redis                   │            │
│  └─────────────────────────────────────────┘            │
└────────┬─────────────────────┬─────────────┬────────────┘
         │                     │             │
         ▼                     ▼             ▼
   ┌──────────┐         ┌──────────┐   ┌─────────┐
   │   S3     │         │PostgreSQL│   │  Redis  │
   │ (IAM)    │         │contracts │   │ (cache) │
   └──────────┘         └──────────┘   └─────────┘
```

## Database Schema

### Contract Table Updates

```sql
CREATE TABLE contracts (
    -- Existing fields
    contract_id VARCHAR(100) PRIMARY KEY,
    account_number VARCHAR(100) NOT NULL,

    -- PDF Storage (S3 IAM-protected)
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key VARCHAR(1024) NOT NULL,

    -- Document Content (populated by ETL)
    document_text TEXT,                    -- OCR'd text
    embeddings JSONB,                      -- Vector embeddings
    text_extracted_at TIMESTAMP,
    text_extraction_status VARCHAR(50),   -- 'pending', 'completed', 'failed'

    -- Metadata
    document_repository_id VARCHAR(100),   -- External ETL reference
    contract_type VARCHAR(50) DEFAULT 'GAP',
    contract_date DATE,
    customer_name VARCHAR(255),
    vehicle_info JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_synced_at TIMESTAMP,

    -- Indexes
    INDEX idx_contracts_account_number (account_number),
    INDEX idx_contracts_s3_key (s3_bucket, s3_key),
    INDEX idx_contracts_extraction_status (text_extraction_status)
);
```

**Key Changes:**
- ✅ Added `s3_bucket`, `s3_key` - S3 location
- ✅ Added `document_text` - OCR'd text for LLM extraction
- ✅ Added `embeddings` - Vector data for semantic search (future)
- ✅ Added extraction status tracking
- ❌ Removed/deprecated `pdf_url` - PDFs no longer publicly accessible

## API Contract

### Endpoint: Stream PDF

```http
GET /api/v1/contracts/{contract_id}/pdf
Authorization: Bearer {token}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: inline; filename="contract-{contract_id}.pdf"
Cache-Control: private, max-age=900
X-Cache-Status: HIT|MISS

<PDF binary stream>
```

**Error Responses:**
```http
404 Not Found - Contract not found
403 Forbidden - User lacks permission
500 Internal Server Error - S3 error
```

### Sequence Diagram

```
Frontend          API Gateway       Contract Service    S3 Service      Redis       S3
   │                   │                   │                │            │         │
   │ GET /pdf          │                   │                │            │         │
   ├──────────────────>│                   │                │            │         │
   │                   │ verify_auth()     │                │            │         │
   │                   ├──────────────────>│                │            │         │
   │                   │                   │ check_cache()  │            │         │
   │                   │                   ├───────────────────────────>│         │
   │                   │                   │                │   <MISS>   │         │
   │                   │                   │<───────────────────────────┤         │
   │                   │                   │ get_s3_info()  │            │         │
   │                   │                   ├────> DB query  │            │         │
   │                   │                   │ stream_pdf()   │            │         │
   │                   │                   ├───────────────>│            │         │
   │                   │                   │                │ GetObject  │         │
   │                   │                   │                ├──────────────────────>│
   │                   │                   │                │<────────────────────┤
   │                   │                   │                │ cache_pdf()│         │
   │                   │                   │                ├───────────>│         │
   │                   │<──────────────────┤                │            │         │
   │<──────────────────┤                   │                │            │         │
   │  <PDF stream>     │                   │                │            │         │
```

## Caching Strategy

### Two-Tier Caching

**Tier 1: Redis (Hot Cache)**
- **Purpose:** Frequently accessed PDFs
- **TTL:** 15 minutes (900 seconds)
- **Key Pattern:** `pdf:{contract_id}`
- **Max Size:** Binary PDFs (varies, ~500KB - 5MB)
- **Eviction:** LRU (Least Recently Used)

**Tier 2: Database (Warm Cache)**
- **Purpose:** Document text for LLM extraction
- **TTL:** Permanent (updated by ETL)
- **Field:** `document_text`
- **Size:** ~10-50KB per document

### Cache Flow

```python
async def get_pdf_stream(contract_id: str) -> StreamingResponse:
    # 1. Try Redis cache
    cached_pdf = await redis.get(f"pdf:{contract_id}")
    if cached_pdf:
        logger.info(f"PDF cache HIT for {contract_id}")
        return StreamingResponse(
            io.BytesIO(cached_pdf),
            media_type="application/pdf",
            headers={"X-Cache-Status": "HIT"}
        )

    # 2. Query database for S3 location
    contract = await db.query(Contract).filter_by(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")

    # 3. Stream from S3
    pdf_bytes = await s3_service.get_object(contract.s3_bucket, contract.s3_key)

    # 4. Cache in Redis (async, don't block response)
    asyncio.create_task(redis.setex(f"pdf:{contract_id}", 900, pdf_bytes))

    # 5. Return streaming response
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"X-Cache-Status": "MISS"}
    )
```

### Cache Invalidation

**When to invalidate:**
1. Contract updated (new PDF uploaded)
2. Manual cache flush via admin endpoint
3. TTL expires naturally

**Invalidation strategy:**
```python
async def invalidate_pdf_cache(contract_id: str):
    await redis.delete(f"pdf:{contract_id}")
    await redis.delete(f"text:{contract_id}")  # Also clear text cache
```

## ETL Integration

### External Document Pipeline (Out of Scope)

The external document ETL pipeline is **not part of this application**. It's a separate batch process that:

1. **Runs periodically** (nightly or on-demand)
2. **Processes PDFs:**
   - Extracts text via OCR
   - Generates vector embeddings
   - Stores results in S3
3. **Populates database:**
   - Inserts/updates `contracts` table
   - Sets `document_text`, `embeddings`, `s3_bucket`, `s3_key`
   - Updates `text_extracted_at`, `text_extraction_status`

### Data Contract

**ETL Output Schema:**
```json
{
  "contract_id": "CONTRACT-12345",
  "s3_bucket": "contracts-production",
  "s3_key": "contracts/2024/11/CONTRACT-12345.pdf",
  "document_text": "GAP INSURANCE CONTRACT...",
  "embeddings": [0.123, -0.456, ...],  // 1536-dim vector
  "text_extracted_at": "2024-11-15T10:30:00Z",
  "text_extraction_status": "completed"
}
```

**Database Insert:**
```sql
INSERT INTO contracts (
    contract_id, s3_bucket, s3_key,
    document_text, embeddings,
    text_extracted_at, text_extraction_status
) VALUES (
    'CONTRACT-12345',
    'contracts-production',
    'contracts/2024/11/CONTRACT-12345.pdf',
    'GAP INSURANCE CONTRACT...',
    '[0.123, -0.456, ...]',
    '2024-11-15T10:30:00Z',
    'completed'
) ON CONFLICT (contract_id) DO UPDATE SET
    document_text = EXCLUDED.document_text,
    embeddings = EXCLUDED.embeddings,
    text_extracted_at = EXCLUDED.text_extracted_at,
    text_extraction_status = EXCLUDED.text_extraction_status;
```

## Security Considerations

### Authentication & Authorization

**Backend IAM Role (for S3):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::contracts-production/*"
    }
  ]
}
```

**Frontend Authentication:**
- User must be authenticated (JWT token)
- Backend verifies token before serving PDF
- Audit log records user_id, contract_id, timestamp

### Data Protection

1. **In Transit:**
   - HTTPS/TLS 1.3 for all API calls
   - S3 transfers use AWS SDK (encrypted)

2. **At Rest:**
   - S3 server-side encryption (SSE-S3 or SSE-KMS)
   - Database encryption (PostgreSQL TDE)
   - Redis encryption optional (local dev)

3. **Access Control:**
   - Role-based access (finance specialist, admin)
   - Contract-level permissions (future)

## Performance Metrics

### Target SLAs

| Metric | Target | Notes |
|--------|--------|-------|
| PDF Load Time (Cached) | < 100ms | Redis cache hit |
| PDF Load Time (S3) | < 500ms | S3 download + cache |
| Cache Hit Ratio | > 80% | For frequently accessed contracts |
| Concurrent Streams | 100+ | Horizontal scaling |

### Monitoring

**Key Metrics:**
- `pdf_cache_hit_ratio` - Redis cache effectiveness
- `pdf_load_time_p95` - 95th percentile load time
- `s3_download_errors` - S3 availability issues
- `pdf_access_count` - Usage patterns

**Alerts:**
- Cache hit ratio < 70%
- P95 load time > 1 second
- S3 error rate > 1%

## Migration Path

### Phase 1: Update Schema (Day 6)
- ✅ Add new fields to Contract model
- ✅ Update ContractResponse schema
- ✅ Drop/recreate local database

### Phase 2: Implement S3 Service (Day 6)
- Add boto3 dependency
- Create S3Service class
- Implement streaming logic
- Add Redis caching

### Phase 3: Add PDF Endpoint (Day 6)
- Create GET /contracts/{id}/pdf route
- Integrate S3 service
- Add audit logging
- Test with sample PDFs

### Phase 4: Update Frontend (Day 6)
- Update PDFViewer to use new endpoint
- Remove direct URL loading
- Test iframe rendering

### Phase 5: ETL Integration (Future)
- External team provides document pipeline
- Populate document_text, embeddings
- Test LLM extraction with real data

## Testing Strategy

### Unit Tests
- S3Service.get_object() with mocked boto3
- Caching logic (Redis mock)
- Error handling (404, 403, 500)

### Integration Tests
- End-to-end PDF streaming
- Cache invalidation
- Audit logging

### Load Tests
- 100 concurrent PDF streams
- Cache performance under load
- S3 bandwidth limits

## Future Enhancements

1. **PDF Transformations:**
   - Watermarking
   - Redaction of sensitive data
   - PDF/A conversion for archival

2. **Advanced Caching:**
   - CloudFront CDN for edge caching
   - Partial content/range requests
   - Compression (if beneficial)

3. **Analytics:**
   - Most accessed contracts
   - Access patterns by user role
   - Cache optimization recommendations

## References

- [FastAPI StreamingResponse Docs](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/cache/)
- [AWS S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

---

**Document Version:** 1.0
**Last Updated:** November 15, 2025
**Status:** Approved for Implementation
