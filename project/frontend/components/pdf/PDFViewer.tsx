'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { HighlightRegion } from './HighlightOverlay';
import { PDFControls } from './PDFControls';

// Dynamically import PDFRenderer with SSR disabled
const PDFRenderer = dynamic(
  () => import('./PDFRenderer').then((mod) => ({ default: mod.PDFRenderer })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">Loading PDF viewer...</p>
        </div>
      </div>
    ),
  }
);

export interface PDFViewerProps {
  contractId: string;
  fileName?: string;
  pageNumber?: number;
  highlights?: HighlightRegion[];
  scrollTrigger?: number;
  onLoadSuccess?: () => void;
  onLoadError?: (error: Error) => void;
}

// Re-export HighlightRegion for convenience
export type { HighlightRegion };

export const PDFViewer = ({
  contractId,
  fileName = 'Contract.pdf',
  pageNumber = 1,
  highlights = [],
  scrollTrigger,
  onLoadSuccess,
  onLoadError,
}: PDFViewerProps) => {
  const [currentPage, setCurrentPage] = useState(pageNumber);
  const [scale, setScale] = useState(1.0);
  const [numPages, setNumPages] = useState(0);
  const [pageWidth, setPageWidth] = useState(612); // Standard US Letter width in points
  const [pageHeight, setPageHeight] = useState(792); // Standard US Letter height in points

  // Ref for scroll container
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  // Track if we're programmatically scrolling to avoid scroll loop
  const isProgrammaticScrollRef = useRef(false);

  // Backend PDF endpoint URL
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1';
  const pdfEndpoint = `${API_BASE_URL}/contracts/${contractId}/pdf`;

  // Function to scroll to a specific page
  const scrollToPage = (page: number) => {
    isProgrammaticScrollRef.current = true;
    setCurrentPage(page); // Update current page for highlighting
    const pageElement = scrollContainerRef.current?.querySelector(`[data-page="${page}"]`);
    if (pageElement) {
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    // Reset flag after scroll completes
    setTimeout(() => {
      isProgrammaticScrollRef.current = false;
    }, 1000);
  };

  // Update page when prop changes (scroll to that page)
  useEffect(() => {
    if (pageNumber) {
      scrollToPage(pageNumber);
    }
  }, [pageNumber]);

  // Scroll when scrollTrigger changes (even if page number is the same)
  useEffect(() => {
    if (scrollTrigger && pageNumber) {
      scrollToPage(pageNumber);
    }
  }, [scrollTrigger]);

  // IntersectionObserver to track which page is currently visible
  useEffect(() => {
    if (!scrollContainerRef.current || numPages === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        // Skip updates during programmatic scrolling
        if (isProgrammaticScrollRef.current) return;

        // Find the most visible page
        let mostVisiblePage: { page: number; ratio: number } = { page: 1, ratio: 0 };

        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > mostVisiblePage.ratio) {
            const pageNum = parseInt(entry.target.getAttribute('data-page') || '1');
            mostVisiblePage = { page: pageNum, ratio: entry.intersectionRatio };
          }
        });

        if (mostVisiblePage.ratio > 0) {
          setCurrentPage(mostVisiblePage.page);
        }
      },
      {
        root: scrollContainerRef.current,
        threshold: [0, 0.25, 0.5, 0.75, 1.0],
      }
    );

    // Observe all page elements
    const pageElements = scrollContainerRef.current.querySelectorAll('[data-page]');
    pageElements.forEach((el) => observer.observe(el));

    return () => {
      pageElements.forEach((el) => observer.unobserve(el));
      observer.disconnect();
    };
  }, [numPages]);

  const handleLoadSuccess = (pages: number) => {
    setNumPages(pages);
    onLoadSuccess?.();
  };

  const handleLoadError = (error: Error) => {
    console.error('PDF load error:', error);
    onLoadError?.(error);
  };

  const handlePageLoadSuccess = (page: any) => {
    // Update page dimensions based on actual PDF page
    if (page) {
      const viewport = page.getViewport({ scale: 1.0 });
      setPageWidth(viewport.width);
      setPageHeight(viewport.height);
    }
  };

  const handleZoomIn = () => {
    setScale(s => Math.min(s + 0.25, 2.0));
  };

  const handleZoomOut = () => {
    setScale(s => Math.max(s - 0.25, 0.5));
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleDownload = () => {
    window.open(pdfEndpoint, '_blank');
  };

  const handlePrint = () => {
    // Create a new window with the PDF for printing
    const printWindow = window.open(pdfEndpoint, '_blank');
    if (printWindow) {
      printWindow.onload = () => {
        printWindow.print();
      };
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-neutral-200 dark:border-neutral-700 dark:bg-neutral-800">
      {/* PDF Controls Toolbar */}
      <PDFControls
        currentPage={currentPage}
        numPages={numPages}
        scale={scale}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onPageChange={handlePageChange}
        onDownload={handleDownload}
        onPrint={handlePrint}
        fileName={fileName}
      />

      {/* PDF Rendering Area with Highlights - contained scroll */}
      <div ref={scrollContainerRef} className="flex-1 overflow-auto bg-neutral-50 dark:bg-neutral-900 relative min-h-0">
        <div className="p-4">
          <PDFRenderer
            contractId={contractId}
            scale={scale}
            highlights={highlights}
            pageWidth={pageWidth}
            pageHeight={pageHeight}
            onLoadSuccess={handleLoadSuccess}
            onLoadError={handleLoadError}
            onPageLoadSuccess={handlePageLoadSuccess}
          />
        </div>
      </div>
    </div>
  );
};
