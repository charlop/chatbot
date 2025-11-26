import { pdfjs } from 'react-pdf';

// Configure PDF.js worker for Next.js (browser only)
// Worker file is copied to public/pdf-worker during build
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = '/pdf-worker/pdf.worker.min.mjs';
}
