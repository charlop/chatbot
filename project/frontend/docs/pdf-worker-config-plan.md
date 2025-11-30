# PDF.js Worker Configuration Plan

## Problem

The current local worker approach (`/pdf-worker/pdf.worker.min.mjs`) will not work in Docker production builds because:

1. `public/pdf-worker/` is in `.gitignore` - it won't be in the Docker build context
2. The Dockerfile uses `npm ci --only=production` which may skip postinstall scripts
3. Even if postinstall ran, the file would be in the `deps` stage but not properly propagated

## Recommendation: Use CDN with Version Auto-Detection

Revert to CDN-based approach but with clean auto-versioning. This is the simplest, most reliable solution.

**Rationale**:
- No file copying or Dockerfile modifications needed
- Version automatically matches installed pdfjs-dist package
- Works identically in dev and production
- No external file management concerns
- unpkg.com/jsdelivr are highly reliable CDNs used by millions of projects

## Implementation

### 1. Update `lib/pdf/config.ts`

```typescript
export function getPDFWorkerSrc(version: string): string {
  return `https://unpkg.com/pdfjs-dist@${version}/build/pdf.worker.min.mjs`;
}

export function getPDFDocumentOptions(version: string) {
  return {
    cMapUrl: `https://unpkg.com/pdfjs-dist@${version}/cmaps/`,
    cMapPacked: true,
  };
}
```

### 2. Remove Global Script from `app/layout.tsx`

Delete the `<Script id="pdf-worker-init">` block entirely. The worker URL will be set when PDF components initialize, using the dynamic import pattern already in place.

### 3. Update Callers to Pass Version

In `PDFRenderer.tsx` and `textExtractor.ts`:
```typescript
const pdf = await import('react-pdf');
pdf.pdfjs.GlobalWorkerOptions.workerSrc = getPDFWorkerSrc(pdf.pdfjs.version);
```

### 4. Clean Up

- Remove postinstall script from `package.json`
- Remove `/public/pdf-worker` from `.gitignore`
- Delete `public/pdf-worker/` directory

## Files to Modify

1. `lib/pdf/config.ts` - Simplify to use CDN with version parameter
2. `app/layout.tsx` - Remove beforeInteractive script
3. `package.json` - Remove postinstall script
4. `.gitignore` - Remove pdf-worker entry
5. `components/pdf/PDFRenderer.tsx` - Pass version to getPDFWorkerSrc
6. `lib/pdf/textExtractor.ts` - Pass version to getPDFWorkerSrc

## Trade-offs Accepted

- External CDN dependency (unpkg.com) - acceptable for this use case
- First load requires CDN fetch - cached thereafter
- If CDN is down, PDF viewer won't work - very rare occurrence
