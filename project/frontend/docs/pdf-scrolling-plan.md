# PDF Continuous Scrolling Implementation Plan

## Overview
Convert the PDF viewer from single-page navigation (< > buttons) to natural continuous scrolling where all pages are rendered vertically in a scrollable container.

## Requirements
- PDFs are 10-20 pages, <2MB, mostly text - render all pages at once (no virtualization)
- Keep "jump to field" functionality - clicking extracted data scrolls to that location
- Keep page indicator showing current visible page
- Keep zoom controls

## Files to Modify

### 1. `components/pdf/PDFRenderer.tsx`
**Current**: Renders single `<Page>` component based on `pageNumber` prop
**Change**: Render all pages in a vertical stack

```tsx
// Instead of single Page:
<Page pageNumber={pageNumber} ... />

// Render all pages:
{Array.from({ length: numPages }, (_, i) => (
  <div key={i + 1} data-page={i + 1} className="pdf-page-wrapper">
    <Page pageNumber={i + 1} scale={scale} ... />
  </div>
))}
```

**New props needed**:
- `numPages` - total pages (from parent after document loads)
- `containerRef` - for scroll-to functionality
- Remove `pageNumber` prop (no longer needed for rendering)

### 2. `components/pdf/PDFViewer.tsx`
**Changes**:
- Add scroll container ref
- Add IntersectionObserver to detect which page is visible (updates `currentPage` for indicator)
- Implement `scrollToPage(pageNum)` function for jump-to-field
- Pass scroll container ref to PDFRenderer

**Key additions**:
```tsx
const scrollContainerRef = useRef<HTMLDivElement>(null);

// Scroll to specific page
const scrollToPage = (page: number) => {
  const pageElement = scrollContainerRef.current?.querySelector(`[data-page="${page}"]`);
  pageElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

// IntersectionObserver to track visible page
useEffect(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const pageNum = parseInt(entry.target.getAttribute('data-page') || '1');
          setCurrentPage(pageNum);
        }
      });
    },
    { threshold: 0.5, root: scrollContainerRef.current }
  );
  // Observe all [data-page] elements...
}, [numPages]);
```

### 3. `components/pdf/PDFControls.tsx`
**Changes**:
- Remove < > navigation buttons (or repurpose as "jump to prev/next page")
- Keep page indicator (shows current visible page from scroll position)
- Keep zoom controls
- Keep page input for "jump to page X"

### 4. `components/pdf/HighlightOverlay.tsx`
**Current**: Only shows highlights for `currentPage`
**Change**: Show highlights for ALL pages, positioned correctly within each page wrapper

**Recommended approach**: Integrate highlight rendering into PDFRenderer - each page wrapper contains its Page + Highlights. This keeps highlights co-located with their page.

### 5. `app/contracts/[contractId]/page.tsx`
**Changes**:
- Update `handleJumpToField` to use new `scrollToPage` mechanism
- Pass scroll function down to child components

## Implementation Order

1. **PDFRenderer** - Add multi-page rendering with data-page attributes
2. **PDFViewer** - Add scroll container, IntersectionObserver, scrollToPage function
3. **HighlightOverlay** - Integrate into PDFRenderer per-page
4. **PDFControls** - Simplify navigation UI
5. **ContractDetailsPage** - Update jump-to-field to use scroll

## Testing Checklist
- [ ] All pages render vertically
- [ ] Natural scrolling works
- [ ] Page indicator updates on scroll
- [ ] Zoom in/out works on all pages
- [ ] Jump to page (input field) scrolls to correct page
- [ ] Clicking extracted data field scrolls PDF to highlight
- [ ] Highlights appear on correct pages at correct positions
- [ ] Performance acceptable with 20-page PDF
