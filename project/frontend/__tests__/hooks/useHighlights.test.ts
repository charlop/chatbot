import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useHighlights } from '@/hooks/useHighlights';
import * as PDFTextExtractorModule from '@/lib/pdf/textExtractor';

// Mock the PDFTextExtractor
vi.mock('@/lib/pdf/textExtractor', () => ({
  PDFTextExtractor: vi.fn().mockImplementation(() => ({
    loadPDF: vi.fn().mockResolvedValue(undefined),
    findTextLocation: vi.fn().mockResolvedValue({
      text: 'Test text',
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
    }),
    destroy: vi.fn(),
  })),
}));

describe('useHighlights', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return empty highlights when no extraction data', () => {
    const { result } = renderHook(() =>
      useHighlights('test-contract-id', null)
    );

    expect(result.current.highlights).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should use cached bboxes when available', async () => {
    const extractedData = {
      extractionId: 'test-extraction-id',
      gapPremium: 500,
      gapPremiumConfidence: 95,
      gapPremiumSource: {
        page: 1,
        text: 'GAP Premium: $500.00',
        bbox: { x: 100, y: 100, width: 200, height: 20 },
      },
    };

    const { result } = renderHook(() =>
      useHighlights('test-contract-id', extractedData)
    );

    await waitFor(() => {
      expect(result.current.highlights).toHaveLength(1);
    });

    expect(result.current.highlights[0]).toMatchObject({
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
      fieldName: 'GAP Insurance Premium',
      confidence: 95,
    });

    // Should not call text extractor when bbox is cached
    expect(PDFTextExtractorModule.PDFTextExtractor).not.toHaveBeenCalled();
  });

  it('should trigger text search when bbox not cached', async () => {
    const extractedData = {
      extractionId: 'test-extraction-id',
      gapPremium: 500,
      gapPremiumConfidence: 95,
      gapPremiumSource: {
        page: 1,
        text: 'GAP Premium: $500.00',
        // No bbox - will trigger text search
      },
    };

    const { result } = renderHook(() =>
      useHighlights('test-contract-id', extractedData)
    );

    // Wait for loading to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    }, { timeout: 2000 });

    // Text search should be attempted (constructor called)
    expect(PDFTextExtractorModule.PDFTextExtractor).toHaveBeenCalled();
  });

  it('should handle multiple fields', async () => {
    const extractedData = {
      extractionId: 'test-extraction-id',
      gapPremium: 500,
      gapPremiumConfidence: 95,
      gapPremiumSource: {
        page: 1,
        text: 'GAP Premium: $500.00',
        bbox: { x: 100, y: 100, width: 200, height: 20 },
      },
      refundMethod: 'Pro-rata',
      refundMethodConfidence: 85,
      refundMethodSource: {
        page: 2,
        text: 'Refund Method: Pro-rata',
        bbox: { x: 150, y: 200, width: 180, height: 18 },
      },
      cancellationFee: 50,
      cancellationFeeConfidence: 75,
      cancellationFeeSource: {
        page: 3,
        text: 'Cancellation Fee: $50.00',
        bbox: { x: 120, y: 150, width: 150, height: 15 },
      },
    };

    const { result } = renderHook(() =>
      useHighlights('test-contract-id', extractedData)
    );

    await waitFor(() => {
      expect(result.current.highlights).toHaveLength(3);
    });

    expect(result.current.highlights[0].fieldName).toBe('GAP Insurance Premium');
    expect(result.current.highlights[1].fieldName).toBe('Refund Calculation Method');
    expect(result.current.highlights[2].fieldName).toBe('Cancellation Fee');
  });

  it('should apply confidence-based colors', async () => {
    const extractedData = {
      extractionId: 'test-extraction-id',
      gapPremium: 500,
      gapPremiumConfidence: 95, // Should be green
      gapPremiumSource: {
        page: 1,
        text: 'GAP Premium: $500.00',
        bbox: { x: 100, y: 100, width: 200, height: 20 },
      },
      refundMethod: 'Pro-rata',
      refundMethodConfidence: 75, // Should be blue
      refundMethodSource: {
        page: 2,
        text: 'Refund Method: Pro-rata',
        bbox: { x: 150, y: 200, width: 180, height: 18 },
      },
      cancellationFee: 50,
      cancellationFeeConfidence: 50, // Should be red
      cancellationFeeSource: {
        page: 3,
        text: 'Cancellation Fee: $50.00',
        bbox: { x: 120, y: 150, width: 150, height: 15 },
      },
    };

    const { result } = renderHook(() =>
      useHighlights('test-contract-id', extractedData)
    );

    await waitFor(() => {
      expect(result.current.highlights).toHaveLength(3);
    });

    expect(result.current.highlights[0].color).toBe('#4CAF50'); // Green
    expect(result.current.highlights[1].color).toBe('#2196F3'); // Blue
    expect(result.current.highlights[2].color).toBe('#F44336'); // Red
  });

  it('should handle missing source data gracefully', () => {
    const extractedData = {
      extractionId: 'test-extraction-id',
      gapPremium: 500,
      gapPremiumConfidence: 95,
      // No source data
    };

    const { result } = renderHook(() =>
      useHighlights('test-contract-id', extractedData)
    );

    // Should immediately return empty highlights when no source data
    expect(result.current.highlights).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle undefined extractedData', () => {
      const { result } = renderHook(() =>
        useHighlights('test-contract-id', undefined)
      );

      expect(result.current.highlights).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle null extractedData', () => {
      const { result } = renderHook(() =>
        useHighlights('test-contract-id', null)
      );

      expect(result.current.highlights).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle extractedData with only one field', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        },
        // No refundMethod or cancellationFee
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].fieldName).toBe('GAP Insurance Premium');
    });

    it('should handle source with text but no page', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          text: 'GAP Premium: $500.00',
          // No page number
        } as any,
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      // Should not crash, should return empty highlights
      expect(result.current.highlights).toEqual([]);
    });

    it('should handle source with page but no text', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          page: 1,
          // No text
        } as any,
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      // Should not crash, should return empty highlights
      expect(result.current.highlights).toEqual([]);
    });

    it('should handle undefined confidence values', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        // No gapPremiumConfidence
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        },
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].confidence).toBeUndefined();
    });

    it('should handle empty contractId', async () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        },
      };

      const { result } = renderHook(() =>
        useHighlights('', extractedData)
      );

      // Should still work with empty contractId (used in PDF URL)
      expect(result.current.highlights).toHaveLength(1);
    });

    it('should handle mixed cached and uncached sources', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 }, // Cached
        },
        refundMethod: 'Pro-rata',
        refundMethodConfidence: 85,
        refundMethodSource: {
          page: 2,
          text: 'Refund Method: Pro-rata',
          // No bbox - not cached
        },
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      // When one has bbox, all cached sources should be used
      // This triggers the cached bbox path
      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].fieldName).toBe('GAP Insurance Premium');
    });

    it('should handle partial refundMethod source', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        refundMethod: 'Pro-rata',
        refundMethodConfidence: 85,
        refundMethodSource: {
          page: 2,
          text: 'Refund Method: Pro-rata',
          bbox: { x: 150, y: 200, width: 180, height: 18 },
        },
        // No gapPremium or cancellationFee
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].fieldName).toBe('Refund Calculation Method');
    });

    it('should handle partial cancellationFee source', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        cancellationFee: 50,
        cancellationFeeConfidence: 75,
        cancellationFeeSource: {
          page: 3,
          text: 'Cancellation Fee: $50.00',
          bbox: { x: 120, y: 150, width: 150, height: 15 },
        },
        // No gapPremium or refundMethod
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].fieldName).toBe('Cancellation Fee');
    });

    it('should handle zero confidence values', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 0, // Zero confidence
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        },
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].confidence).toBe(0);
    });

    it('should handle very high confidence values', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 100, // Perfect confidence
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        },
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].confidence).toBe(100);
    });

    it('should handle negative bbox values', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          page: 1,
          text: 'GAP Premium: $500.00',
          bbox: { x: -10, y: -20, width: 200, height: 20 }, // Negative coords
        },
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].bbox.x).toBe(-10);
      expect(result.current.highlights[0].bbox.y).toBe(-20);
    });

    it('should handle very large page numbers', () => {
      const extractedData = {
        extractionId: 'test-extraction-id',
        gapPremium: 500,
        gapPremiumConfidence: 95,
        gapPremiumSource: {
          page: 9999, // Very large page number
          text: 'GAP Premium: $500.00',
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        },
      };

      const { result } = renderHook(() =>
        useHighlights('test-contract-id', extractedData)
      );

      expect(result.current.highlights).toHaveLength(1);
      expect(result.current.highlights[0].page).toBe(9999);
    });
  });
});
