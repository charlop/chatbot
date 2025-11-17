'use client';

import { useState, useEffect, useRef } from 'react';

export interface PDFViewerProps {
  contractId: string; // Changed from url - now loads PDF via backend proxy
  fileName?: string;
  pageNumber?: number; // Optional page number to jump to
  onLoadSuccess?: () => void;
  onLoadError?: (error: Error) => void;
}

export interface HighlightRegion {
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  confidence?: number;
  fieldName?: string;
}

export const PDFViewer = ({
  contractId,
  fileName = 'Contract.pdf',
  pageNumber,
  onLoadSuccess,
  onLoadError,
}: PDFViewerProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number | undefined>(pageNumber);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Construct backend PDF endpoint URL
  const pdfEndpoint = `/api/v1/contracts/${contractId}/pdf`;

  // Update current page when pageNumber prop changes
  useEffect(() => {
    if (pageNumber !== undefined && pageNumber !== currentPage) {
      setCurrentPage(pageNumber);

      // Update iframe src to jump to page
      if (iframeRef.current) {
        const pageHash = pageNumber > 0 ? `#page=${pageNumber}` : '';
        iframeRef.current.src = `${pdfEndpoint}${pageHash}#toolbar=1&navpanes=1&scrollbar=1`;
      }
    }
  }, [pageNumber, currentPage, pdfEndpoint]);

  const handleIframeLoad = () => {
    setIsLoading(false);
    setError(null);
    if (onLoadSuccess) {
      onLoadSuccess();
    }
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError('Failed to load PDF. Please try again.');
    if (onLoadError) {
      onLoadError(new Error('Failed to load PDF'));
    }
  };

  const handleDownload = () => {
    // Use backend endpoint for download
    window.open(pdfEndpoint, '_blank');
  };

  const handlePrint = () => {
    const iframe = document.querySelector('iframe');
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.print();
    }
  };

  const handleOpenInNewTab = () => {
    window.open(pdfEndpoint, '_blank');
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-neutral-200 dark:border-neutral-700">
      {/* PDF Toolbar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center gap-4">
          <h3 className="text-base font-medium text-neutral-900 dark:text-neutral-100">
            {fileName}
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
            aria-label="Download PDF"
            title="Download"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>

          <button
            onClick={handlePrint}
            className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
            aria-label="Print PDF"
            title="Print"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
          </button>

          <button
            onClick={handleOpenInNewTab}
            className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
            aria-label="Open in new tab"
            title="Open in new tab"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
        </div>
      </div>

      {/* PDF Content Area */}
      <div className="flex-1 overflow-hidden bg-neutral-50 dark:bg-neutral-900">
        {isLoading && (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-400">Loading PDF...</p>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 bg-danger-100 dark:bg-danger-900/30 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-danger-600 dark:text-danger-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-danger-600 dark:text-danger-400">{error}</p>
          </div>
        )}

        {!error && (
          <iframe
            ref={iframeRef}
            src={`${pdfEndpoint}#toolbar=1&navpanes=1&scrollbar=1`}
            className="w-full h-full border-0"
            title={fileName}
            onLoad={handleIframeLoad}
            onError={handleIframeError}
          />
        )}
      </div>
    </div>
  );
};
