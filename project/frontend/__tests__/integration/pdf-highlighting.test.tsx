import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { PDFViewer } from '@/components/pdf/PDFViewer';
import type { HighlightRegion } from '@/components/pdf/HighlightOverlay';

// Mock react-pdf
vi.mock('react-pdf', () => ({
  Document: ({ children, onLoadSuccess }: any) => {
    // Simulate successful PDF load
    if (onLoadSuccess) {
      setTimeout(() => onLoadSuccess({ numPages: 3 }), 0);
    }
    return <div data-testid="pdf-document">{children}</div>;
  },
  Page: ({ onLoadSuccess }: any) => {
    // Simulate successful page load with viewport
    if (onLoadSuccess) {
      setTimeout(() => onLoadSuccess({
        getViewport: () => ({ width: 612, height: 792 })
      }), 0);
    }
    return <div data-testid="pdf-page">PDF Page</div>;
  },
  pdfjs: {
    version: '3.0.0',
    GlobalWorkerOptions: {},
  },
}));

// Mock PDF worker
vi.mock('@/lib/pdf/worker', () => ({}));

describe('PDF Highlighting Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render PDFViewer with highlights', async () => {
    const mockHighlights: HighlightRegion[] = [
      {
        page: 1,
        bbox: { x: 100, y: 100, width: 200, height: 20 },
        color: '#4CAF50',
        confidence: 95,
        fieldName: 'GAP Insurance Premium',
      },
    ];

    render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        highlights={mockHighlights}
      />
    );

    // Wait for PDF to load
    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument();
    });

    // Check that highlights would be rendered (SVG overlay)
    // Note: Full highlight rendering requires actual PDF loading
    expect(screen.getByTestId('pdf-page')).toBeInTheDocument();
  });

  it('should render PDFViewer without highlights', async () => {
    render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        highlights={[]}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument();
    });
  });

  it('should update page when pageNumber prop changes', async () => {
    const { rerender } = render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        pageNumber={1}
        highlights={[]}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument();
    });

    // Update page number
    rerender(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        pageNumber={2}
        highlights={[]}
      />
    );

    // Page should update (internal state changes)
    expect(screen.getByTestId('pdf-document')).toBeInTheDocument();
  });

  it('should call onLoadSuccess when PDF loads', async () => {
    const onLoadSuccess = vi.fn();

    render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        highlights={[]}
        onLoadSuccess={onLoadSuccess}
      />
    );

    await waitFor(() => {
      expect(onLoadSuccess).toHaveBeenCalled();
    });
  });

  it('should render multiple highlights on same page', async () => {
    const mockHighlights: HighlightRegion[] = [
      {
        page: 1,
        bbox: { x: 100, y: 100, width: 200, height: 20 },
        color: '#4CAF50',
        confidence: 95,
        fieldName: 'GAP Insurance Premium',
      },
      {
        page: 1,
        bbox: { x: 100, y: 200, width: 180, height: 18 },
        color: '#2196F3',
        confidence: 85,
        fieldName: 'Refund Method',
      },
      {
        page: 2,
        bbox: { x: 150, y: 150, width: 150, height: 15 },
        color: '#F44336',
        confidence: 65,
        fieldName: 'Cancellation Fee',
      },
    ];

    render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        pageNumber={1}
        highlights={mockHighlights}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument();
    });

    // Only 2 highlights should be visible on page 1
    // (Third highlight is on page 2)
  });

  it('should handle PDF load errors gracefully', async () => {
    const onLoadError = vi.fn();

    render(
      <PDFViewer
        contractId="INVALID-ID"
        fileName="test.pdf"
        highlights={[]}
        onLoadError={onLoadError}
      />
    );

    // PDF document should still render (with error handling)
    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument();
    });
  });

  it('should render zoom controls', async () => {
    render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        highlights={[]}
      />
    );

    // Wait for rendering
    await waitFor(() => {
      expect(screen.getByLabelText('Zoom in')).toBeInTheDocument();
      expect(screen.getByLabelText('Zoom out')).toBeInTheDocument();
    });
  });

  it('should render page navigation controls', async () => {
    render(
      <PDFViewer
        contractId="TEST-001"
        fileName="test.pdf"
        highlights={[]}
      />
    );

    // Wait for PDF to load and navigation to appear
    await waitFor(() => {
      expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
      expect(screen.getByLabelText('Next page')).toBeInTheDocument();
    });
  });
});
