/**
 * PDF.js configuration
 * Centralized configuration for PDF.js worker and resources
 */

/**
 * Get the PDF.js worker source URL from CDN
 * @param version - The pdfjs version from pdfjs.version
 */
export function getPDFWorkerSrc(version: string): string {
  return `https://unpkg.com/pdfjs-dist@${version}/build/pdf.worker.min.mjs`;
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
