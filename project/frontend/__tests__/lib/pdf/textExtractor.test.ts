import { describe, it, expect, beforeEach } from 'vitest';
import { PDFTextExtractor } from '@/lib/pdf/textExtractor';

describe('PDFTextExtractor', () => {
  let extractor: PDFTextExtractor;

  beforeEach(() => {
    extractor = new PDFTextExtractor();
  });

  it('should create an instance', () => {
    expect(extractor).toBeDefined();
    expect(extractor).toBeInstanceOf(PDFTextExtractor);
  });

  it('should throw error when trying to get pages without loading PDF', async () => {
    await expect(extractor.getNumPages()).rejects.toThrow('PDF not loaded');
  });

  it('should throw error when trying to find text without loading PDF', async () => {
    await expect(
      extractor.findTextLocation('test', 1)
    ).rejects.toThrow('PDF not loaded');
  });

  it('should cleanup on destroy', () => {
    extractor.destroy();
    expect(() => extractor.destroy()).not.toThrow();
  });

  // Note: Integration tests with actual PDFs would go in a separate test file
  // and require test PDF fixtures
});
