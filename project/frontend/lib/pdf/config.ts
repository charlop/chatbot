/**
 * PDF.js configuration
 * Centralized configuration for PDF.js worker and resources
 */

/**
 * Get the PDF.js worker source URL from CDN
 * Using CDN to avoid bundling/MIME type issues with Next.js 16
 */
export function getPDFWorkerSrc(): string {
  // Use fixed version 4.10.38 (matches our locked pdfjs-dist version)
  return 'https://unpkg.com/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs';
}

/**
 * Get PDF.js document options for character maps
 * Required for rendering PDFs with non-Latin characters
 * @param version - The pdfjs version from pdfjs.version
 */
export function getPDFDocumentOptions(version: string) {
  return {
    cMapUrl: `https://unpkg.com/pdfjs-dist@${version}/cmaps/`,
    cMapPacked: true,
  };
}
