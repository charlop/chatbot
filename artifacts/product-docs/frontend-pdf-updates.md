# Frontend PDF Updates - Implementation Plan

**Date:** November 15, 2025
**Status:** Approved
**Estimated Effort:** 2-3 hours

## Overview

Update frontend to load PDFs via backend proxy endpoint instead of direct S3 URLs, due to S3 IAM authentication requirements.

## Problem Statement

### Current Implementation (Broken)
- Frontend receives `pdfUrl` from `ContractResponse`
- Assumed to be publicly accessible URL
- Loads directly in iframe: `<iframe src={pdfUrl} />`
- **Issue:** PDFs are in S3 with IAM auth - not publicly accessible

### Required Changes
- Backend will provide streaming endpoint: `GET /api/v1/contracts/{id}/pdf`
- Frontend must call this endpoint instead of direct URL
- Iframe will load from backend proxy
- No changes to visual/UX behavior

## Architecture Change

### Before (Direct S3 URL)
```
Frontend PDFViewer
    └─> <iframe src="https://s3.amazonaws.com/..." />
            └─> 403 Forbidden (IAM auth required)
```

### After (Backend Proxy)
```
Frontend PDFViewer
    └─> <iframe src="/api/v1/contracts/{contractId}/pdf" />
            └─> Backend API
                    └─> S3 (with IAM credentials)
                            └─> PDF stream
```

## Files to Modify

### 1. PDFViewer Component
**File:** `frontend/components/pdf/PDFViewer.tsx`

**Current Interface:**
```typescript
interface PDFViewerProps {
  url: string;              // Direct S3 URL
  fileName?: string;
  onLoadSuccess?: () => void;
  onLoadError?: (error: string) => void;
}
```

**New Interface:**
```typescript
interface PDFViewerProps {
  contractId: string;        // Changed: now takes contractId instead of url
  fileName?: string;
  onLoadSuccess?: () => void;
  onLoadError?: (error: string) => void;
}
```

**Implementation Changes:**
```typescript
export const PDFViewer = ({
  contractId,  // Changed from 'url'
  fileName,
  onLoadSuccess,
  onLoadError
}: PDFViewerProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Construct backend endpoint URL
  const pdfEndpoint = `/api/v1/contracts/${contractId}/pdf`;

  const handleLoad = () => {
    setIsLoading(false);
    setError(null);
    onLoadSuccess?.();
  };

  const handleError = () => {
    const errorMsg = 'Failed to load PDF';
    setError(errorMsg);
    setIsLoading(false);
    onLoadError?.(errorMsg);
  };

  const handleDownload = () => {
    // Use same endpoint for download
    window.open(pdfEndpoint, '_blank');
  };

  const handlePrint = () => {
    const iframe = document.querySelector('iframe');
    iframe?.contentWindow?.print();
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border">
      {/* PDF Toolbar */}
      <div className="flex items-center justify-between px-6 py-4 border-b">
        <h3 className="text-lg font-semibold text-neutral-900">
          {fileName || `Contract ${contractId}`}
        </h3>
        <div className="flex gap-2">
          <button
            onClick={handleDownload}
            className="px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-100 rounded-lg"
          >
            Download
          </button>
          <button
            onClick={handlePrint}
            className="px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-100 rounded-lg"
          >
            Print
          </button>
          <button
            onClick={() => window.open(pdfEndpoint, '_blank')}
            className="px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-100 rounded-lg"
          >
            Open in New Tab
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-hidden bg-neutral-50 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
              <p className="text-neutral-600">Loading PDF...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-center">
              <p className="text-danger-600 mb-4">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        <iframe
          src={`${pdfEndpoint}#toolbar=1&navpanes=1&scrollbar=1`}
          className="w-full h-full border-0"
          title={fileName || `Contract ${contractId}`}
          onLoad={handleLoad}
          onError={handleError}
        />
      </div>
    </div>
  );
};
```

### 2. Contract Details Page
**File:** `frontend/app/contracts/[contractId]/page.tsx`

**Current Usage:**
```typescript
<PDFViewer
  url={contract.pdfUrl}  // Old prop
  fileName={`Contract-${contract.accountNumber}.pdf`}
/>
```

**New Usage:**
```typescript
<PDFViewer
  contractId={contract.contractId}  // New prop
  fileName={`Contract-${contract.accountNumber}.pdf`}
/>
```

### 3. API Client Types
**File:** `frontend/lib/api/contracts.ts`

**Current Interface:**
```typescript
export interface Contract {
  id: string;
  contractId: string;
  accountNumber: string;
  pdfUrl: string;  // To be deprecated
  // ... other fields
}
```

**Updated Interface:**
```typescript
export interface Contract {
  id: string;
  contractId: string;
  accountNumber: string;

  // PDF access - removed direct URL
  // pdfUrl: string;  // DEPRECATED - use GET /contracts/{id}/pdf instead

  // S3 metadata (optional, for debugging)
  s3Bucket?: string;
  s3Key?: string;

  // Other fields
  documentRepositoryId?: string;
  contractType?: string;
  contractDate?: string;
  customerName?: string;
  vehicleInfo?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}
```

**Note:** No API client method changes needed - PDF is loaded directly via iframe src.

## Implementation Steps

### Step 1: Update PDFViewer Component (30 min)
1. Change prop from `url: string` to `contractId: string`
2. Update iframe src to use backend endpoint
3. Update download/print handlers
4. Test loading states and error handling

### Step 2: Update Contract Details Page (15 min)
1. Change PDFViewer prop from `url={contract.pdfUrl}` to `contractId={contract.contractId}`
2. Remove any references to `pdfUrl`
3. Test page render

### Step 3: Update TypeScript Types (15 min)
1. Update `Contract` interface in `lib/api/contracts.ts`
2. Mark `pdfUrl` as deprecated with comment
3. Add optional S3 metadata fields
4. Run `npm run type-check`

### Step 4: Testing (60 min)
1. Unit test PDFViewer with new props
2. Integration test iframe loading
3. Test download/print functionality
4. Test error states (404, 403, 500)
5. Test loading spinner
6. Manual browser testing (Chrome, Firefox, Safari)

## Testing Checklist

### Unit Tests
- [ ] PDFViewer renders with contractId prop
- [ ] Correct endpoint URL constructed
- [ ] Loading state shows spinner
- [ ] Error state shows retry button
- [ ] Download button opens correct URL
- [ ] Print button calls contentWindow.print()

### Integration Tests
```typescript
// frontend/tests/components/PDFViewer.test.tsx
describe('PDFViewer', () => {
  it('should load PDF from backend endpoint', async () => {
    render(<PDFViewer contractId="TEST-001" />);

    const iframe = screen.getByTitle(/Contract TEST-001/);
    expect(iframe).toHaveAttribute('src', '/api/v1/contracts/TEST-001/pdf#toolbar=1&navpanes=1&scrollbar=1');
  });

  it('should show loading state initially', () => {
    render(<PDFViewer contractId="TEST-001" />);
    expect(screen.getByText(/Loading PDF.../)).toBeInTheDocument();
  });

  it('should handle load success', async () => {
    const onLoadSuccess = vi.fn();
    render(<PDFViewer contractId="TEST-001" onLoadSuccess={onLoadSuccess} />);

    const iframe = screen.getByTitle(/Contract TEST-001/);
    fireEvent.load(iframe);

    expect(onLoadSuccess).toHaveBeenCalled();
    expect(screen.queryByText(/Loading PDF.../)).not.toBeInTheDocument();
  });

  it('should handle load error', async () => {
    const onLoadError = vi.fn();
    render(<PDFViewer contractId="TEST-001" onLoadError={onLoadError} />);

    const iframe = screen.getByTitle(/Contract TEST-001/);
    fireEvent.error(iframe);

    expect(onLoadError).toHaveBeenCalledWith('Failed to load PDF');
    expect(screen.getByText(/Failed to load PDF/)).toBeInTheDocument();
  });
});
```

### Manual Testing
1. Navigate to contract details page
2. Verify PDF loads in iframe
3. Test zoom controls (browser native)
4. Test page navigation
5. Click Download - verify file downloads
6. Click Print - verify print dialog opens
7. Click "Open in New Tab" - verify new tab with PDF
8. Test with slow network (throttle to 3G)
9. Test with invalid contract ID (404 error)
10. Test with unauthorized access (403 error)

## Backend Dependencies

### Required Backend Endpoints
Frontend assumes backend provides:

```http
GET /api/v1/contracts/{contract_id}/pdf
Authorization: Bearer {token}
```

**Response:**
- Success: PDF binary stream (application/pdf)
- Error 404: Contract not found
- Error 403: Unauthorized
- Error 500: Server error

**Headers:**
- `Content-Type: application/pdf`
- `Content-Disposition: inline; filename="contract-{id}.pdf"`
- `Cache-Control: private, max-age=900`

### API Contract Update
The `GET /api/v1/contracts/{id}` endpoint should:
- ❌ Remove `pdfUrl` from response (or mark deprecated)
- ✅ Keep `contractId` in response
- ✅ Optionally include `s3Bucket`, `s3Key` (for debugging)

## Migration Strategy

### Backward Compatibility
During transition, support both old and new approaches:

```typescript
export const PDFViewer = ({
  contractId,
  url,  // Deprecated, for backward compat
  fileName,
  onLoadSuccess,
  onLoadError
}: PDFViewerProps) => {
  // Priority: use contractId if provided, fall back to url
  const pdfSource = contractId
    ? `/api/v1/contracts/${contractId}/pdf`
    : url;

  if (!contractId && !url) {
    throw new Error('PDFViewer requires either contractId or url prop');
  }

  // ... rest of component
};
```

**Deprecation Warning:**
```typescript
useEffect(() => {
  if (url && !contractId) {
    console.warn('[PDFViewer] The "url" prop is deprecated. Please use "contractId" instead.');
  }
}, [url, contractId]);
```

### Rollout Plan
1. **Phase 1:** Update PDFViewer to accept both props
2. **Phase 2:** Update all callers to use `contractId`
3. **Phase 3:** Remove `url` prop support
4. **Phase 4:** Remove `pdfUrl` from API responses

## Error Handling

### Error States

**1. Contract Not Found (404)**
```typescript
if (error?.status === 404) {
  return (
    <div className="text-center p-8">
      <p className="text-danger-600 mb-4">Contract not found</p>
      <Link href="/dashboard" className="text-primary-600 hover:underline">
        Return to Dashboard
      </Link>
    </div>
  );
}
```

**2. Unauthorized (403)**
```typescript
if (error?.status === 403) {
  return (
    <div className="text-center p-8">
      <p className="text-danger-600 mb-4">You don't have permission to view this contract</p>
      <button onClick={() => router.back()} className="text-primary-600">
        Go Back
      </button>
    </div>
  );
}
```

**3. Server Error (500)**
```typescript
if (error?.status === 500) {
  return (
    <div className="text-center p-8">
      <p className="text-danger-600 mb-4">Failed to load PDF. Please try again.</p>
      <button onClick={() => window.location.reload()} className="btn-primary">
        Retry
      </button>
    </div>
  );
}
```

## Performance Considerations

### Caching
- Browser automatically caches iframe content
- Backend sets `Cache-Control: private, max-age=900`
- PDFs cached for 15 minutes in browser

### Loading Performance
- Iframe loads asynchronously (non-blocking)
- Loading spinner shows until iframe load event
- No impact on initial page render

### Bandwidth
- Same bandwidth as before (PDF still streams)
- Backend caching reduces server load
- No additional network requests

## Security Notes

### CORS
Not required - frontend and backend on same origin:
- Frontend: `https://app.example.com`
- Backend: `https://app.example.com/api/...`

### Authentication
- Frontend includes JWT token in requests
- Backend validates token before streaming
- Token automatically sent via cookies/headers

### Content Security Policy (CSP)
Update CSP to allow iframe:
```html
<meta
  http-equiv="Content-Security-Policy"
  content="frame-src 'self';"
/>
```

## Rollback Plan

If issues arise, can quickly rollback:

1. **Revert PDFViewer:** Change `contractId` back to `url` prop
2. **Revert API:** Return `pdfUrl` in ContractResponse
3. **Revert caller:** Pass `pdfUrl` instead of `contractId`

**Estimated rollback time:** < 15 minutes

## Future Enhancements

1. **PDF Annotations:**
   - Allow users to highlight/comment on PDFs
   - Save annotations to backend

2. **Thumbnail Preview:**
   - Show PDF thumbnail before full load
   - Improve perceived performance

3. **Progressive Loading:**
   - Load first page immediately
   - Stream remaining pages in background

4. **Download Options:**
   - Download original
   - Download with annotations
   - Download as images

## Summary

**Changes Required:**
- ✅ Update PDFViewer component (contractId instead of url)
- ✅ Update contract details page (pass contractId)
- ✅ Update TypeScript types (deprecate pdfUrl)
- ✅ Add tests for new behavior

**No Changes Required:**
- ❌ API client methods (iframe loads directly)
- ❌ Visual appearance (looks identical)
- ❌ User experience (no behavioral changes)

**Estimated Effort:** 2-3 hours (including testing)

**Risk:** Low - isolated change, easy rollback

---

**Document Version:** 1.0
**Last Updated:** November 15, 2025
**Status:** Ready for Implementation
