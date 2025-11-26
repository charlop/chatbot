'use client';

import { useEffect, useState } from 'react';
import { getPDFWorkerSrc, getPDFDocumentOptions } from '@/lib/pdf/config';

interface PDFRendererProps {
  contractId: string;
  pageNumber?: number;
  scale?: number;
  onLoadSuccess?: (numPages: number) => void;
  onLoadError?: (error: Error) => void;
  onPageLoadSuccess?: (page: any) => void;
  className?: string;
}

export const PDFRenderer = ({
  contractId,
  pageNumber = 1,
  scale = 1.0,
  onLoadSuccess,
  onLoadError,
  onPageLoadSuccess,
  className = '',
}: PDFRendererProps) => {
  const [ReactPDF, setReactPDF] = useState<any>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize PDF.js worker and load react-pdf components
  useEffect(() => {
    const initPDF = async () => {
      try {
        // Dynamically import CSS (TypeScript doesn't recognize CSS imports, but webpack does)
        // @ts-ignore - CSS imports are handled by webpack
        await import('react-pdf/dist/Page/AnnotationLayer.css');
        // @ts-ignore - CSS imports are handled by webpack
        await import('react-pdf/dist/Page/TextLayer.css');

        // Dynamically import react-pdf to avoid SSR issues
        const pdf = await import('react-pdf');

        // Configure worker using centralized config (version auto-detected)
        pdf.pdfjs.GlobalWorkerOptions.workerSrc = getPDFWorkerSrc(pdf.pdfjs.version);

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

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
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

  // Get pdfjs version for document options
  const pdfjsVersion = ReactPDF.pdfjs?.version || '5.4.394';

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
        options={getPDFDocumentOptions(pdfjsVersion)}
      >
        <Page
          pageNumber={pageNumber}
          scale={scale}
          renderTextLayer={true}      // Enable text layer for search and highlighting
          renderAnnotationLayer={true} // Enable links/forms
          loading={
            <div className="flex items-center justify-center h-full min-h-[400px]">
              <div className="animate-pulse text-sm text-neutral-500">Loading page...</div>
            </div>
          }
          onLoadSuccess={onPageLoadSuccess}
          className="pdf-page"
        />
      </Document>
    </div>
  );
};
