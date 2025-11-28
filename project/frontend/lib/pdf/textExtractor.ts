import { getPDFWorkerSrc } from './config';

interface TextItem {
  str: string;
  transform: number[];
  width: number;
  height: number;
}

interface TextLocation {
  text: string;
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
}

export class PDFTextExtractor {
  private pdfDocument: any = null;

  async loadPDF(url: string): Promise<void> {
    // Use react-pdf's pdfjs to ensure consistent worker configuration
    const { pdfjs } = await import('react-pdf');

    // Set worker URL (react-pdf will have already set a default, we override it)
    pdfjs.GlobalWorkerOptions.workerSrc = getPDFWorkerSrc();

    this.pdfDocument = await pdfjs.getDocument(url).promise;
  }

  async getNumPages(): Promise<number> {
    if (!this.pdfDocument) throw new Error('PDF not loaded');
    return this.pdfDocument.numPages;
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
    const matches = this.searchTextItems(textContent.items as TextItem[], searchText);
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
      // Only process actual TextItem objects with str property
      if (!('str' in item)) continue;

      currentText += item.str.toLowerCase();
      currentItems.push(item);

      if (currentText.includes(normalizedSearch)) {
        // Found match - return items that contain the search text
        return currentItems;
      }

      // Keep window of last N items (for multi-item matches)
      if (currentItems.length > 20) {
        const removed = currentItems.shift();
        if (removed) {
          currentText = currentText.slice(removed.str.length);
        }
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
      const width = item.width || 0;
      const height = item.height || 0;

      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + width);
      maxY = Math.max(maxY, y + height);
    }

    // Convert PDF coordinates (bottom-left origin) to viewport (top-left)
    return {
      x: minX,
      y: pageHeight - maxY,
      width: maxX - minX,
      height: maxY - minY,
    };
  }

  destroy(): void {
    this.pdfDocument?.destroy();
    this.pdfDocument = null;
  }
}
