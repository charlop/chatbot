import { useState, useEffect } from 'react';
import { PDFTextExtractor } from '@/lib/pdf/textExtractor';
import { HighlightRegion } from '@/components/pdf/HighlightOverlay';
import { getConfidenceColor } from '@/components/pdf/HighlightOverlay';
import { textLocationCache } from '@/lib/pdf/cache';

/**
 * Source location from extraction data
 */
interface ExtractionSource {
  page: number;
  text: string;
  bbox?: { x: number; y: number; width: number; height: number };
}

/**
 * Extracted field data structure
 */
interface ExtractedData {
  extractionId: string;
  gapPremium?: number;
  gapPremiumConfidence?: number;
  gapPremiumSource?: ExtractionSource;
  refundMethod?: string;
  refundMethodConfidence?: number;
  refundMethodSource?: ExtractionSource;
  cancellationFee?: number;
  cancellationFeeConfidence?: number;
  cancellationFeeSource?: ExtractionSource;
  status?: 'pending' | 'approved';
}

/**
 * Hook return type
 */
interface UseHighlightsReturn {
  highlights: HighlightRegion[];
  isLoading: boolean;
  error: Error | null;
}

/**
 * Custom hook to generate PDF highlights from extraction data
 *
 * This hook:
 * 1. Takes extraction data with text snippets
 * 2. Uses PDFTextExtractor to find text locations in PDF
 * 3. Generates HighlightRegion objects with confidence-based colors
 * 4. Caches results to avoid re-searching on every render
 *
 * @param contractId - Contract ID to load PDF
 * @param extractedData - Extraction data with source text snippets
 * @returns Highlights array, loading state, and error state
 */
export function useHighlights(
  contractId: string,
  extractedData: ExtractedData | null | undefined
): UseHighlightsReturn {
  const [highlights, setHighlights] = useState<HighlightRegion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!extractedData) {
      setHighlights([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    // Check if we already have cached bounding boxes
    const hasCachedBboxes =
      (extractedData.gapPremiumSource?.bbox) ||
      (extractedData.refundMethodSource?.bbox) ||
      (extractedData.cancellationFeeSource?.bbox);

    // If all sources have cached bboxes, skip text search
    if (hasCachedBboxes) {
      const cachedHighlights: HighlightRegion[] = [];

      if (extractedData.gapPremiumSource?.bbox) {
        cachedHighlights.push({
          page: extractedData.gapPremiumSource.page,
          bbox: extractedData.gapPremiumSource.bbox,
          color: getConfidenceColor(extractedData.gapPremiumConfidence),
          confidence: extractedData.gapPremiumConfidence,
          fieldName: 'GAP Insurance Premium',
        });
      }

      if (extractedData.refundMethodSource?.bbox) {
        cachedHighlights.push({
          page: extractedData.refundMethodSource.page,
          bbox: extractedData.refundMethodSource.bbox,
          color: getConfidenceColor(extractedData.refundMethodConfidence),
          confidence: extractedData.refundMethodConfidence,
          fieldName: 'Refund Calculation Method',
        });
      }

      if (extractedData.cancellationFeeSource?.bbox) {
        cachedHighlights.push({
          page: extractedData.cancellationFeeSource.page,
          bbox: extractedData.cancellationFeeSource.bbox,
          color: getConfidenceColor(extractedData.cancellationFeeConfidence),
          confidence: extractedData.cancellationFeeConfidence,
          fieldName: 'Cancellation Fee',
        });
      }

      setHighlights(cachedHighlights);
      setIsLoading(false);
      setError(null);
      return;
    }

    // Otherwise, perform text search to generate bounding boxes
    async function generateHighlights() {
      if (!extractedData) return;

      setIsLoading(true);
      setError(null);

      try {
        const extractor = new PDFTextExtractor();
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1';
        const pdfUrl = `${API_BASE_URL}/contracts/${contractId}/pdf`;

        await extractor.loadPDF(pdfUrl);

        const results: HighlightRegion[] = [];

        // Process GAP Insurance Premium
        if (extractedData.gapPremiumSource?.text && extractedData.gapPremiumSource?.page) {
          // Check cache first
          let location = textLocationCache.get(
            contractId,
            extractedData.gapPremiumSource.page,
            extractedData.gapPremiumSource.text
          );

          // If not cached, search for it
          if (!location) {
            location = await extractor.findTextLocation(
              extractedData.gapPremiumSource.text,
              extractedData.gapPremiumSource.page
            );

            // Cache the result
            if (location) {
              textLocationCache.set(
                contractId,
                extractedData.gapPremiumSource.page,
                extractedData.gapPremiumSource.text,
                location
              );
            }
          }

          if (location) {
            results.push({
              page: location.page,
              bbox: location.bbox,
              color: getConfidenceColor(extractedData.gapPremiumConfidence),
              confidence: extractedData.gapPremiumConfidence,
              fieldName: 'GAP Insurance Premium',
            });
          }
        }

        // Process Refund Calculation Method
        if (extractedData.refundMethodSource?.text && extractedData.refundMethodSource?.page) {
          // Check cache first
          let location = textLocationCache.get(
            contractId,
            extractedData.refundMethodSource.page,
            extractedData.refundMethodSource.text
          );

          // If not cached, search for it
          if (!location) {
            location = await extractor.findTextLocation(
              extractedData.refundMethodSource.text,
              extractedData.refundMethodSource.page
            );

            // Cache the result
            if (location) {
              textLocationCache.set(
                contractId,
                extractedData.refundMethodSource.page,
                extractedData.refundMethodSource.text,
                location
              );
            }
          }

          if (location) {
            results.push({
              page: location.page,
              bbox: location.bbox,
              color: getConfidenceColor(extractedData.refundMethodConfidence),
              confidence: extractedData.refundMethodConfidence,
              fieldName: 'Refund Calculation Method',
            });
          }
        }

        // Process Cancellation Fee
        if (extractedData.cancellationFeeSource?.text && extractedData.cancellationFeeSource?.page) {
          // Check cache first
          let location = textLocationCache.get(
            contractId,
            extractedData.cancellationFeeSource.page,
            extractedData.cancellationFeeSource.text
          );

          // If not cached, search for it
          if (!location) {
            location = await extractor.findTextLocation(
              extractedData.cancellationFeeSource.text,
              extractedData.cancellationFeeSource.page
            );

            // Cache the result
            if (location) {
              textLocationCache.set(
                contractId,
                extractedData.cancellationFeeSource.page,
                extractedData.cancellationFeeSource.text,
                location
              );
            }
          }

          if (location) {
            results.push({
              page: location.page,
              bbox: location.bbox,
              color: getConfidenceColor(extractedData.cancellationFeeConfidence),
              confidence: extractedData.cancellationFeeConfidence,
              fieldName: 'Cancellation Fee',
            });
          }
        }

        setHighlights(results);

        // Cleanup
        extractor.destroy();
      } catch (err) {
        console.error('Highlight generation error:', err);
        setError(err as Error);
        setHighlights([]);
      } finally {
        setIsLoading(false);
      }
    }

    generateHighlights();
  }, [contractId, extractedData]);

  return { highlights, isLoading, error };
}
