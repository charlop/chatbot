'use client';

import { useEffect, useState, useMemo } from 'react';
import { getPDFWorkerSrc, getPDFDocumentOptions } from '@/lib/pdf/config';
import { HighlightOverlay, HighlightRegion } from './HighlightOverlay';

interface PDFRendererProps {
  contractId: string;
  scale?: number;
  highlights?: HighlightRegion[];
  pageWidth?: number;
  pageHeight?: number;
  onLoadSuccess?: (numPages: number) => void;
  onLoadError?: (error: Error) => void;
  onPageLoadSuccess?: (page: any) => void;
  className?: string;
}

export const PDFRenderer = ({
  contractId,
  scale = 1.0,
  highlights = [],
  pageWidth = 612,
  pageHeight = 792,
  onLoadSuccess,
  onLoadError,
  onPageLoadSuccess,
  className = '',
}: PDFRendererProps) => {
  const [ReactPDF, setReactPDF] = useState<any>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [numPages, setNumPages] = useState<number>(0);

  // Initialize PDF.js worker and load react-pdf components
  useEffect(() => {
    const initPDF = async () => {
      try {
        // Dynamically import CSS (TypeScript doesn't recognize CSS imports, but webpack does)
        // @ts-ignore - CSS imports are handled by webpack
        await import('react-pdf/dist/Page/AnnotationLayer.css');
        // @ts-ignore - CSS imports are handled by webpack
        await import('react-pdf/dist/Page/TextLayer.css');

        // Import react-pdf (this will set default worker to 'pdf.worker.mjs')
        const pdf = await import('react-pdf');

        // IMPORTANT: Set worker URL AFTER importing react-pdf to override its default
        const workerUrl = getPDFWorkerSrc();
        console.log('[PDFRenderer] Setting worker URL to:', workerUrl);
        pdf.pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
        console.log('[PDFRenderer] Worker URL after setting:', pdf.pdfjs.GlobalWorkerOptions.workerSrc);

        // Store the Document and Page components
        setReactPDF({
          Document: pdf.Document,
          Page: pdf.Page,
        });
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize PDF.js:', error);
        onLoadError?.(error as Error);
      }
    };

    initPDF();
  }, [onLoadError]);

  // Backend PDF endpoint
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1';
  const pdfUrl = `${API_BASE_URL}/contracts/${contractId}/pdf`;

  // Get pdfjs version for document options (safe to access even if ReactPDF is null)
  const pdfjsVersion = ReactPDF?.pdfjs?.version || '4.10.38';

  // Memoize options to prevent unnecessary reloads (must be called unconditionally)
  const documentOptions = useMemo(
    () => getPDFDocumentOptions(pdfjsVersion),
    [pdfjsVersion]
  );

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    onLoadSuccess?.(numPages);
  }

  function onDocumentLoadError(error: Error) {
    console.error('PDF load error:', error);
    onLoadError?.(error);
  }

  // Show loading state while initializing
  if (!isInitialized || !ReactPDF) {
    return (
      <div className={`pdf-renderer-container ${className}`}>
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">Initializing PDF viewer...</p>
          </div>
        </div>
      </div>
    );
  }

  const { Document, Page } = ReactPDF;

  return (
    <div className={`pdf-renderer-container ${className}`}>
      <Document
        file={pdfUrl}
        onLoadSuccess={onDocumentLoadSuccess}
        onLoadError={onDocumentLoadError}
        loading={
          <div className="flex items-center justify-center h-full min-h-[400px]">
            <div className="flex flex-col items-center gap-3">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">Loading PDF...</p>
            </div>
          </div>
        }
        error={
          <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
            <div className="w-16 h-16 bg-danger-100 dark:bg-danger-900/30 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-danger-600 dark:text-danger-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-danger-600 dark:text-danger-400 font-medium">Failed to load PDF</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">Please try again or contact support</p>
          </div>
        }
        options={documentOptions}
      >
        {Array.from({ length: numPages }, (_, i) => {
          const pageNum = i + 1;
          return (
            <div key={pageNum} data-page={pageNum} className="pdf-page-wrapper mb-4 relative">
              <Page
                pageNumber={pageNum}
                scale={scale}
                renderTextLayer={true}      // Enable text layer for search and highlighting
                renderAnnotationLayer={true} // Enable links/forms
                loading={
                  <div className="flex items-center justify-center h-full min-h-[400px]">
                    <div className="animate-pulse text-sm text-neutral-500">Loading page {pageNum}...</div>
                  </div>
                }
                onLoadSuccess={onPageLoadSuccess}
                className="pdf-page"
              />

              {/* Render highlights for this specific page */}
              {highlights.length > 0 && (
                <HighlightOverlay
                  highlights={highlights}
                  currentPage={pageNum}
                  scale={scale}
                  pageWidth={pageWidth}
                  pageHeight={pageHeight}
                />
              )}
            </div>
          );
        })}
      </Document>
    </div>
  );
};
