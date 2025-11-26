# PDF Highlighting Implementation Plan

## Overview

Migrate from iframe-based PDF viewer to **react-pdf (PDF.js)** to add visual highlighting for extracted contract fields with confidence-based color coding and text search capability.

**User Requirements:**
- Full capability approach (16-24 hours effort)
- Exact text matching for highlights (not approximate)
- Text search in PDFs (MVP + future feature)
- Backend will provide text snippets, frontend finds coordinates programmatically

**Key Architectural Decision:**
Backend LLM receives raw text (not PDFs), so it can only return text snippets like `"GAP Insurance Premium: $500.00"`. Frontend must programmatically find this text in the PDF and save coordinates to database.

---

## Current State

### Existing Implementation
- **PDFViewer.tsx**: iframe with native browser rendering (165 lines)
- **Backend PDF endpoint**: `/api/v1/contracts/{contractId}/pdf` (proxy to S3)
- **Source data format**: `{page: number, line: number}` in JSONB columns
- **HighlightRegion interface**: Defined but completely unused (lines 13-22)
- **"View in Document" links**: Jump to page via hash anchor, no highlighting

### Data Flow (Current)
```
Backend Extraction API
└─> {gap_premium_source: {page: 1, line: 10}}
    └─> Frontend transforms to "Page 1, Line 10"
        └─> Regex parses page number
            └─> iframe.src = "#page=1"
```

---

## Proposed Architecture

### New Data Flow
```
Backend Extraction API
└─> {gap_premium_source: {page: 1, text: "GAP Premium: $500.00"}}
    └─> Frontend loads PDF via PDF.js
        └─> Extract text layer from page 1
            └─> Search for "GAP Premium: $500.00"
                └─> Get bounding box {x, y, width, height}
                    └─> Save to database (optional: for caching)
                        └─> Render SVG highlight at coordinates
```

### Component Architecture
```
PDFViewer (orchestrator)
├─── PDFRenderer (react-pdf integration)
│    ├─── Document (loads PDF)
│    └─── Page (renders canvas + text layer)
├─── HighlightOverlay (SVG layer)
│    └─── HighlightBox[] (confidence-colored rectangles)
├─── PDFControls (zoom, navigation, search)
└─── SearchPanel (text search across PDF)
```

---

## Implementation Plan

### Phase 1: PDF.js Foundation (4-5 hours)

#### 1.1 Install Dependencies
```bash
npm install react-pdf pdfjs-dist
npm install -D @types/react-pdf
```

**Versions:**
- react-pdf: ^9.1.1 (latest, Next.js 15 + React 19 compatible)
- pdfjs-dist: ^4.8.69 (PDF.js core library)

#### 1.2 Configure PDF.js Worker

**File**: `/lib/pdf/worker.ts` (NEW)
```typescript
import { pdfjs } from 'react-pdf';

if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc =
    `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
}
```

**File**: `next.config.mjs` (MODIFY)
```javascript
const nextConfig = {
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    config.resolve.alias.encoding = false;
    return config;
  },
};
```

#### 1.3 Create PDFTextExtractor Service

**File**: `/lib/pdf/textExtractor.ts` (NEW)

**Purpose**: Extract text layer and find text snippets programmatically

```typescript
interface TextItem {
  str: string;           // Text content
  transform: number[];   // [scaleX, skewX, skewY, scaleY, x, y]
  width: number;
  height: number;
}

interface TextLocation {
  text: string;
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
}

export class PDFTextExtractor {
  private pdfDocument: PDFDocumentProxy | null = null;

  async loadPDF(url: string): Promise<void> {
    this.pdfDocument = await pdfjs.getDocument(url).promise;
  }

  async findTextLocation(
    searchText: string,
    pageNum: number
  ): Promise<TextLocation | null> {
    if (!this.pdfDocument) throw new Error('PDF not loaded');

    const page = await this.pdfDocument.getPage(pageNum);
    const textContent = await page.getTextContent();
    const viewport = page.getViewport({ scale: 1.0 });

    // Find text items that match search text
    const matches = this.searchTextItems(textContent.items, searchText);
    if (matches.length === 0) return null;

    // Calculate bounding box for matched text
    const bbox = this.calculateBoundingBox(matches, viewport.height);

    return {
      text: searchText,
      page: pageNum,
      bbox,
    };
  }

  private searchTextItems(items: TextItem[], searchText: string): TextItem[] {
    // Normalize text for comparison
    const normalizedSearch = searchText.toLowerCase().trim();
    const matches: TextItem[] = [];
    let currentText = '';
    let currentItems: TextItem[] = [];

    for (const item of items) {
      currentText += item.str.toLowerCase();
      currentItems.push(item);

      if (currentText.includes(normalizedSearch)) {
        // Found match - return items that contain the search text
        return currentItems;
      }

      // Keep window of last N items (for multi-item matches)
      if (currentItems.length > 20) {
        const removed = currentItems.shift();
        currentText = currentText.slice(removed!.str.length);
      }
    }

    return matches;
  }

  private calculateBoundingBox(
    items: TextItem[],
    pageHeight: number
  ): { x: number; y: number; width: number; height: number } {
    // Extract coordinates from transform matrix [a, b, c, d, x, y]
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;

    for (const item of items) {
      const [, , , , x, y] = item.transform;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + item.width);
      maxY = Math.max(maxY, y + item.height);
    }

    // Convert PDF coordinates (bottom-left origin) to viewport (top-left)
    return {
      x: minX,
      y: pageHeight - maxY,
      width: maxX - minX,
      height: maxY - minY,
    };
  }
}
```

**Key Algorithm**:
- PDF.js provides text items with transform matrices
- Search for text snippet by concatenating item strings
- Extract bounding box by finding min/max coordinates
- Convert from PDF coordinate system (bottom-left origin) to viewport (top-left)

#### 1.4 Update Backend Schema (Extraction Model)

**File**: `/app/models/database/extraction.py` (MODIFY lines 55-67)

**Current:**
```python
gap_premium_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
# Format: {"page": 1, "line": 10}
```

**Updated:**
```python
gap_premium_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
# Format: {
#   "page": 1,
#   "text": "GAP Insurance Premium: $500.00",
#   "bbox": {"x": 72, "y": 150, "width": 200, "height": 12}  # Optional
# }
```

**Migration Strategy:**
- Phase 1: Add `text` field to JSONB (LLM must return matched text)
- Phase 2: Add optional `bbox` field (populated by frontend after text search)
- Phase 3: Use cached `bbox` when available (skip text search)

**Backend API Update Required:**
LLM prompt must instruct extraction to return the actual text snippet, not just page/line.

---

### Phase 2: react-pdf Integration (4-5 hours)

#### 2.1 Create PDFRenderer Component

**File**: `/components/pdf/PDFRenderer.tsx` (NEW)

**Purpose**: Replace iframe with react-pdf Document/Page rendering

```typescript
import { Document, Page } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

interface PDFRendererProps {
  contractId: string;
  pageNumber?: number;
  onLoadSuccess?: (numPages: number) => void;
  onLoadError?: (error: Error) => void;
  onPageChange?: (page: number) => void;
}

export const PDFRenderer: React.FC<PDFRendererProps> = ({
  contractId,
  pageNumber = 1,
  onLoadSuccess,
  onLoadError,
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [scale, setScale] = useState<number>(1.0);

  // Backend PDF endpoint
  const pdfUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/contracts/${contractId}/pdf`;

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    onLoadSuccess?.(numPages);
  }

  function onDocumentLoadError(error: Error) {
    console.error('PDF load error:', error);
    onLoadError?.(error);
  }

  return (
    <div className="pdf-renderer-container">
      <Document
        file={pdfUrl}
        onLoadSuccess={onDocumentLoadSuccess}
        onLoadError={onDocumentLoadError}
        loading={<PDFLoadingSkeleton />}
        error={<PDFErrorState />}
      >
        <Page
          pageNumber={pageNumber}
          scale={scale}
          renderTextLayer={true}      // Enable text layer for search
          renderAnnotationLayer={true} // Enable links/forms
          loading={<PageLoadingSkeleton />}
        />
      </Document>
    </div>
  );
};
```

**Key Features:**
- Loads PDF from backend proxy endpoint
- Renders text layer (required for search and text extraction)
- Handles loading/error states
- Exposes scale for zoom controls

#### 2.2 Create HighlightOverlay Component

**File**: `/components/pdf/HighlightOverlay.tsx` (NEW)

**Purpose**: Render SVG highlights on top of PDF canvas

```typescript
interface HighlightRegion {
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
  color: string;
  confidence?: number;
  fieldName?: string;
}

interface HighlightOverlayProps {
  highlights: HighlightRegion[];
  currentPage: number;
  scale: number;
  pageWidth: number;
  pageHeight: number;
}

export const HighlightOverlay: React.FC<HighlightOverlayProps> = ({
  highlights,
  currentPage,
  scale,
  pageWidth,
  pageHeight,
}) => {
  // Filter to current page only
  const pageHighlights = highlights.filter(h => h.page === currentPage);

  return (
    <svg
      className="absolute inset-0 pointer-events-none z-10"
      width={pageWidth * scale}
      height={pageHeight * scale}
      viewBox={`0 0 ${pageWidth} ${pageHeight}`}
    >
      {pageHighlights.map((highlight, idx) => (
        <rect
          key={idx}
          x={highlight.bbox.x}
          y={highlight.bbox.y}
          width={highlight.bbox.width}
          height={highlight.bbox.height}
          fill={highlight.color}
          fillOpacity={0.3}
          stroke={highlight.color}
          strokeWidth={2 / scale}
          rx={2}
          className="pointer-events-auto transition-all hover:fill-opacity-50"
        >
          <title>{highlight.fieldName} ({highlight.confidence}% confidence)</title>
        </rect>
      ))}
    </svg>
  );
};
```

**Why SVG over Canvas:**
- Scales perfectly with zoom (vector graphics)
- Easy hover effects and tooltips
- Better accessibility (ARIA labels)
- Simpler coordinate transformations

#### 2.3 Integrate into PDFViewer

**File**: `/components/pdf/PDFViewer.tsx` (MAJOR REFACTOR)

**Changes:**
1. Replace iframe with PDFRenderer
2. Add HighlightOverlay
3. Keep existing toolbar and controls
4. Update props to accept highlights

```typescript
export interface PDFViewerProps {
  contractId: string;
  fileName?: string;
  pageNumber?: number;
  highlights?: HighlightRegion[];  // NEW
  onLoadSuccess?: () => void;
  onLoadError?: (error: Error) => void;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  contractId,
  pageNumber = 1,
  highlights = [],
  onLoadSuccess,
  onLoadError,
}) => {
  const [currentPage, setCurrentPage] = useState(pageNumber);
  const [scale, setScale] = useState(1.0);
  const [numPages, setNumPages] = useState(0);

  // Update page when prop changes
  useEffect(() => {
    if (pageNumber) setCurrentPage(pageNumber);
  }, [pageNumber]);

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border">
      {/* Toolbar: zoom, page nav, download */}
      <PDFControls
        currentPage={currentPage}
        numPages={numPages}
        scale={scale}
        onZoomIn={() => setScale(s => Math.min(s + 0.25, 2.0))}
        onZoomOut={() => setScale(s => Math.max(s - 0.25, 0.5))}
        onPageChange={setCurrentPage}
      />

      {/* PDF Rendering Area */}
      <div className="relative flex-1 overflow-auto">
        <PDFRenderer
          contractId={contractId}
          pageNumber={currentPage}
          onLoadSuccess={(n) => {
            setNumPages(n);
            onLoadSuccess?.();
          }}
          onLoadError={onLoadError}
        />

        <HighlightOverlay
          highlights={highlights}
          currentPage={currentPage}
          scale={scale}
          pageWidth={612}  // Standard US Letter width in points
          pageHeight={792} // Standard US Letter height in points
        />
      </div>
    </div>
  );
};
```

---

### Phase 3: Text Search & Highlight Generation (3-4 hours)

#### 3.1 Create useHighlights Hook

**File**: `/hooks/useHighlights.ts` (NEW)

**Purpose**: Transform extraction data to HighlightRegion objects with text search

```typescript
interface ExtractionSource {
  page: number;
  text: string;
  bbox?: { x: number; y: number; width: number; height: number };
}

interface Extraction {
  gap_premium_source?: ExtractionSource;
  gap_premium_confidence?: number;
  refund_method_source?: ExtractionSource;
  refund_method_confidence?: number;
  cancellation_fee_source?: ExtractionSource;
  cancellation_fee_confidence?: number;
}

export function useHighlights(
  contractId: string,
  extraction: Extraction | null
): {
  highlights: HighlightRegion[];
  isLoading: boolean;
  error: Error | null;
} {
  const [highlights, setHighlights] = useState<HighlightRegion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!extraction) {
      setHighlights([]);
      return;
    }

    async function generateHighlights() {
      setIsLoading(true);
      setError(null);

      try {
        const extractor = new PDFTextExtractor();
        const pdfUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/contracts/${contractId}/pdf`;
        await extractor.loadPDF(pdfUrl);

        const results: HighlightRegion[] = [];

        // Process each extracted field
        if (extraction.gap_premium_source) {
          const location = await extractor.findTextLocation(
            extraction.gap_premium_source.text,
            extraction.gap_premium_source.page
          );

          if (location) {
            results.push({
              page: location.page,
              bbox: location.bbox,
              color: getConfidenceColor(extraction.gap_premium_confidence),
              confidence: extraction.gap_premium_confidence,
              fieldName: 'GAP Insurance Premium',
            });
          }
        }

        // Repeat for refund_method and cancellation_fee...

        setHighlights(results);
      } catch (err) {
        setError(err as Error);
        console.error('Highlight generation error:', err);
      } finally {
        setIsLoading(false);
      }
    }

    generateHighlights();
  }, [contractId, extraction]);

  return { highlights, isLoading, error };
}

function getConfidenceColor(confidence?: number): string {
  if (!confidence) return '#9E9E9E'; // Gray
  if (confidence >= 90) return '#4CAF50';  // Green
  if (confidence >= 70) return '#2196F3';  // Blue
  return '#F44336';  // Red
}
```

**Confidence Color Scheme:**
- 90-100%: Green (high confidence)
- 70-89%: Blue (medium confidence)
- 0-69%: Red (low confidence - needs review)
- No confidence: Gray

#### 3.2 Integrate into Contract Page

**File**: `/app/contracts/[contractId]/page.tsx` (MODIFY lines 111-127, 176-198)

**Changes:**
1. Use `useHighlights` hook to generate highlights
2. Pass highlights to PDFViewer
3. Update "View in Document" handler to support text search

```typescript
export default function ContractDetailsPage() {
  const params = useParams();
  const contractId = params.contractId as string;

  const { data: contract, error, isLoading } = useContract(contractId);
  const [currentPdfPage, setCurrentPdfPage] = useState<number>(1);

  // Generate highlights from extraction data
  const { highlights, isLoading: highlightsLoading } = useHighlights(
    contractId,
    contract?.extractedData || null
  );

  // Handle "View in Document" click
  const handleJumpToField = (source: ExtractionSource) => {
    // Navigate to page
    setCurrentPdfPage(source.page);

    // Highlight will automatically appear via highlights array
    // Optional: Add temporary "pulse" effect
  };

  return (
    <div className="flex h-screen">
      {/* PDF Viewer (2/3 width) */}
      <div className="w-2/3">
        <PDFViewer
          contractId={contractId}
          pageNumber={currentPdfPage}
          highlights={highlights}
        />
      </div>

      {/* Data Panel (1/3 width) */}
      <div className="w-1/3">
        <DataPanel
          extraction={contract?.extractedData}
          onViewInDocument={(source) => handleJumpToField(source)}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
```

#### 3.3 Update DataCard Component

**File**: `/components/extraction/DataCard.tsx` (MODIFY lines 181-199)

**Changes:**
- Update `onViewInDocument` to pass full source object (not string)

```typescript
export interface DataCardProps {
  label: string;
  value: string | number | null;
  confidence?: number;
  source?: ExtractionSource;  // CHANGED: was string, now object
  onViewInDocument?: (source: ExtractionSource) => void;  // CHANGED
  // ... other props
}

// In JSX:
{onViewInDocument && source && (
  <button
    onClick={() => onViewInDocument(source)}
    className="text-xs font-medium text-primary hover:text-primary-dark"
  >
    View in document →
  </button>
)}
```

---

### Phase 4: Text Search Feature (2-3 hours)

#### 4.1 Create SearchPanel Component

**File**: `/components/pdf/SearchPanel.tsx` (NEW)

**Purpose**: Search across PDF and highlight matches

```typescript
interface SearchPanelProps {
  contractId: string;
  onSearchResults?: (results: SearchResult[]) => void;
}

interface SearchResult {
  page: number;
  text: string;
  bbox: { x: number; y: number; width: number; height: number };
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  contractId,
  onSearchResults,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  async function handleSearch() {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const extractor = new PDFTextExtractor();
      const pdfUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/contracts/${contractId}/pdf`;
      await extractor.loadPDF(pdfUrl);

      const searchResults: SearchResult[] = [];
      const numPages = await extractor.getNumPages();

      // Search all pages
      for (let page = 1; page <= numPages; page++) {
        const location = await extractor.findTextLocation(searchQuery, page);
        if (location) {
          searchResults.push({
            page: location.page,
            text: location.text,
            bbox: location.bbox,
          });
        }
      }

      setResults(searchResults);
      onSearchResults?.(searchResults);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div className="search-panel p-4 border-b">
      <div className="flex gap-2">
        <Input
          placeholder="Search in PDF..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={isSearching}>
          {isSearching ? 'Searching...' : 'Search'}
        </Button>
      </div>

      {results.length > 0 && (
        <div className="mt-4">
          <p className="text-sm text-gray-600">
            {results.length} result{results.length !== 1 ? 's' : ''} found
          </p>
          <ul className="mt-2 space-y-1">
            {results.map((result, idx) => (
              <li key={idx} className="text-sm">
                Page {result.page}: {result.text}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

#### 4.2 Integrate Search into PDFViewer

Add SearchPanel above PDF rendering area with toggle button.

---

### Phase 5: Testing & Performance (2-3 hours)

#### 5.1 Unit Tests

**File**: `/__tests__/lib/pdf/textExtractor.test.ts` (NEW)

```typescript
describe('PDFTextExtractor', () => {
  it('should load PDF and extract text', async () => {
    const extractor = new PDFTextExtractor();
    await extractor.loadPDF('/test.pdf');
    // Assert PDF loaded
  });

  it('should find text location in PDF', async () => {
    const extractor = new PDFTextExtractor();
    await extractor.loadPDF('/test.pdf');

    const location = await extractor.findTextLocation('GAP Premium', 1);
    expect(location).toBeTruthy();
    expect(location?.bbox).toHaveProperty('x');
    expect(location?.bbox).toHaveProperty('y');
  });

  it('should return null for text not found', async () => {
    const extractor = new PDFTextExtractor();
    await extractor.loadPDF('/test.pdf');

    const location = await extractor.findTextLocation('DOES_NOT_EXIST', 1);
    expect(location).toBeNull();
  });
});
```

**File**: `/__tests__/components/pdf/HighlightOverlay.test.tsx` (NEW)

```typescript
describe('HighlightOverlay', () => {
  it('should render highlights for current page', () => {
    const highlights = [
      { page: 1, bbox: {x: 100, y: 100, width: 200, height: 20}, color: '#4CAF50' },
      { page: 2, bbox: {x: 100, y: 100, width: 200, height: 20}, color: '#F44336' },
    ];

    const { container } = render(
      <HighlightOverlay
        highlights={highlights}
        currentPage={1}
        scale={1.0}
        pageWidth={612}
        pageHeight={792}
      />
    );

    // Should render 1 rectangle (page 1 only)
    const rects = container.querySelectorAll('rect');
    expect(rects).toHaveLength(1);
  });

  it('should apply confidence colors', () => {
    const highlight = {
      page: 1,
      bbox: {x: 100, y: 100, width: 200, height: 20},
      color: '#4CAF50',
      confidence: 95,
    };

    const { container } = render(
      <HighlightOverlay
        highlights={[highlight]}
        currentPage={1}
        scale={1.0}
        pageWidth={612}
        pageHeight={792}
      />
    );

    const rect = container.querySelector('rect');
    expect(rect).toHaveAttribute('fill', '#4CAF50');
  });
});
```

#### 5.2 Integration Tests

**File**: `/__tests__/integration/pdf-highlighting.test.tsx` (NEW)

```typescript
describe('PDF Highlighting Integration', () => {
  it('should highlight extracted fields', async () => {
    const mockExtraction = {
      gap_premium_source: {
        page: 1,
        text: 'GAP Insurance Premium: $500.00',
      },
      gap_premium_confidence: 95,
    };

    render(
      <ContractDetailsPage
        contract={{ contractId: 'TEST-001', extractedData: mockExtraction }}
      />
    );

    // Wait for highlights to load
    await waitFor(() => {
      const highlight = screen.getByLabelText(/GAP Insurance Premium/);
      expect(highlight).toBeInTheDocument();
    });
  });

  it('should navigate to page when "View in Document" clicked', async () => {
    // Test navigation + highlighting
  });
});
```

#### 5.3 Performance Optimization

**Caching Strategy:**
```typescript
// Cache text extraction results
const textCache = new Map<string, TextLocation>();

async function findTextLocationCached(
  contractId: string,
  searchText: string,
  page: number
): Promise<TextLocation | null> {
  const cacheKey = `${contractId}:${page}:${searchText}`;

  if (textCache.has(cacheKey)) {
    return textCache.get(cacheKey)!;
  }

  const location = await extractor.findTextLocation(searchText, page);
  if (location) {
    textCache.set(cacheKey, location);
  }

  return location;
}
```

**Memory Management:**
```typescript
// Cleanup on unmount
useEffect(() => {
  return () => {
    pdfDocument?.destroy();
    textCache.clear();
  };
}, []);
```

---

## Backend Changes Required

### Update LLM Extraction Prompt

**File**: `/app/integrations/llm_providers/base.py` (MODIFY lines 62-72)

**Current Schema:**
```python
"source": {
    "type": "object",
    "properties": {
        "page": {"type": "integer"},
        "section": {"type": "string"},
        "line": {"type": "integer"},
    },
}
```

**New Schema:**
```python
"source": {
    "type": "object",
    "properties": {
        "page": {"type": "integer", "description": "Page number where text was found"},
        "text": {"type": "string", "description": "Exact text snippet extracted (e.g., 'GAP Insurance Premium: $500.00')"},
        "section": {"type": "string", "description": "Section name (optional)"},
    },
    "required": ["page", "text"]
}
```

**Prompt Update:**
Instruct LLM to return the actual extracted text in the `text` field, not just page/line coordinates.

**Example:**
```json
{
  "gap_insurance_premium": {
    "value": 500.00,
    "confidence": 95.5,
    "source": {
      "page": 1,
      "text": "GAP Insurance Premium: $500.00",
      "section": "Coverage Details"
    }
  }
}
```

### Optional: Store Bounding Boxes in Database

**Enhancement (Phase 2):**
After frontend finds text and calculates bounding box, save it to database for caching:

```python
"source": {
    "page": 1,
    "text": "GAP Insurance Premium: $500.00",
    "bbox": {"x": 72, "y": 150, "width": 200, "height": 12}  # Cached by frontend
}
```

**Benefits:**
- Faster subsequent loads (skip text search)
- Consistent highlighting
- Audit trail of extraction locations

---

## File Modification Summary

### New Files (8)
1. `/lib/pdf/worker.ts` - PDF.js worker configuration
2. `/lib/pdf/textExtractor.ts` - Text search and coordinate extraction
3. `/components/pdf/PDFRenderer.tsx` - react-pdf integration
4. `/components/pdf/HighlightOverlay.tsx` - SVG highlight rendering
5. `/components/pdf/SearchPanel.tsx` - Text search UI
6. `/hooks/useHighlights.ts` - Highlight generation hook
7. `/__tests__/lib/pdf/textExtractor.test.ts` - Unit tests
8. `/__tests__/components/pdf/HighlightOverlay.test.tsx` - Component tests

### Modified Files (6)
1. `/components/pdf/PDFViewer.tsx` - Replace iframe with PDFRenderer
2. `/components/extraction/DataCard.tsx` - Update source prop type
3. `/components/extraction/DataPanel.tsx` - Pass source objects
4. `/app/contracts/[contractId]/page.tsx` - Integrate useHighlights hook
5. `/app/integrations/llm_providers/base.py` - Update extraction schema
6. `next.config.mjs` - Add webpack aliases for PDF.js

### Total Lines of Code: ~800-1000 LOC

---

## Implementation Timeline

### Day 1: Foundation (4-5 hours)
- Install dependencies and configure worker
- Create PDFTextExtractor service
- Write unit tests for text extraction
- Test with sample PDFs

### Day 2: React-PDF Integration (4-5 hours)
- Create PDFRenderer component
- Create HighlightOverlay component
- Refactor PDFViewer to use new components
- Test rendering and highlighting

### Day 3: Highlight Generation (3-4 hours)
- Create useHighlights hook
- Integrate into contract page
- Update DataCard for source objects
- Test end-to-end flow

### Day 4: Search Feature (2-3 hours)
- Create SearchPanel component
- Integrate search into PDFViewer
- Add keyboard shortcuts
- Test search functionality

### Day 5: Testing & Polish (2-3 hours)
- Write integration tests
- Performance optimization
- Browser testing
- Bug fixes

**Total Effort: 16-24 hours (2-3 weeks at 1-2 hours/day)**

---

## Success Criteria

### Functional
- ✅ PDF loads via react-pdf (not iframe)
- ✅ Visual highlights appear for extracted fields
- ✅ Colors match confidence scores (green/blue/red)
- ✅ "View in Document" navigates to correct page with highlight
- ✅ Text search finds and highlights matches
- ✅ Works with real contract PDFs

### Performance
- ✅ PDF loads in < 2 seconds (p95)
- ✅ Text search completes in < 1 second per page
- ✅ Highlights render in < 100ms
- ✅ Memory usage < 150MB per document
- ✅ No UI blocking during text extraction

### Quality
- ✅ 90%+ test coverage for new code
- ✅ Integration tests pass
- ✅ No console errors or warnings
- ✅ WCAG 2.1 AA accessible (keyboard nav, ARIA labels)

---

## Risks & Mitigations

### Risk 1: Text Search Accuracy
**Problem**: Text might not match exactly (formatting, line breaks)
**Mitigation**:
- Normalize text (lowercase, trim whitespace)
- Fuzzy matching (allow minor differences)
- Fallback to page-only navigation if text not found

### Risk 2: PDF.js Performance with Large PDFs
**Problem**: 50+ page documents may load slowly
**Mitigation**:
- Lazy load pages (only render visible pages)
- Cache rendered pages
- Use web worker for text extraction (non-blocking)

### Risk 3: Backend LLM Returns Incorrect Text
**Problem**: LLM returns paraphrased text instead of exact snippet
**Mitigation**:
- Update prompt to emphasize "extract exact text as written"
- Validate extracted text against source document (future)
- Log mismatches for prompt tuning

### Risk 4: Browser Compatibility
**Problem**: PDF.js may not work in older browsers
**Mitigation**:
- Test on Chrome, Firefox, Safari, Edge
- Feature detection and fallback to iframe if needed
- Display warning for unsupported browsers

---

## Future Enhancements (Out of Scope)

1. **Annotation Tools**: User-drawn highlights and notes
2. **Highlight Export**: Download PDF with highlights embedded
3. **Smart Zoom**: Auto-zoom to highlight when clicked
4. **Multi-Page Highlights**: Single field spanning multiple pages
5. **OCR Integration**: Extract text from image-based PDFs
6. **Collaborative Highlights**: Share highlights with team
7. **Historical Tracking**: Version control for highlights

---

## Critical Files for Implementation

### Priority 1 (Core Functionality)
1. `/lib/pdf/textExtractor.ts` - Text search algorithm (NEW)
2. `/components/pdf/PDFRenderer.tsx` - react-pdf integration (NEW)
3. `/components/pdf/HighlightOverlay.tsx` - Highlight rendering (NEW)
4. `/hooks/useHighlights.ts` - Highlight generation logic (NEW)
5. `/components/pdf/PDFViewer.tsx` - Main orchestrator (REFACTOR)

### Priority 2 (Integration)
6. `/app/contracts/[contractId]/page.tsx` - Wire up highlights (MODIFY)
7. `/components/extraction/DataCard.tsx` - Update props (MODIFY)
8. `/app/integrations/llm_providers/base.py` - Update schema (MODIFY)

### Priority 3 (Search Feature)
9. `/components/pdf/SearchPanel.tsx` - Search UI (NEW)

### Priority 4 (Testing)
10. `/__tests__/lib/pdf/textExtractor.test.ts` - Unit tests (NEW)
11. `/__tests__/integration/pdf-highlighting.test.tsx` - Integration tests (NEW)

---

**Plan Status**: Ready for implementation
**Last Updated**: 2025-11-26
**Estimated Effort**: 16-24 hours over 2-3 weeks
