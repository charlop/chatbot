import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AxiosResponse } from 'axios';

// Mock the API client
const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPut = vi.fn();
const mockPatch = vi.fn();

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    patch: mockPatch,
  },
}));

describe('Extractions API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getExtraction', () => {
    it('should get extraction data for a contract', async () => {
      const { getExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          id: 'EXT123',
          contractId: 'C123456',
          gap_premium: 1500.00,
          gap_premium_confidence: 95,
          gap_premium_source: 'Page 2, Section 3',
          refund_method: 'Pro-Rata',
          refund_method_confidence: 92,
          refund_method_source: 'Page 3, Section 1',
          cancellation_fee: 50.00,
          cancellation_fee_confidence: 88,
          cancellation_fee_source: 'Page 1, Section 5',
          status: 'pending',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getExtraction('C123456');

      expect(mockGet).toHaveBeenCalledWith('/contract/C123456/extraction');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle extraction not found', async () => {
      const { getExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 404,
          data: { message: 'Extraction not found' },
        },
      };

      mockGet.mockRejectedValue(error);

      await expect(getExtraction('INVALID')).rejects.toThrow();
    });
  });

  describe('submitExtraction', () => {
    it('should submit extraction without corrections (simple approval)', async () => {
      const { submitExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          id: 'EXT123',
          contractId: 'C123456',
          gap_premium: 1500.00,
          gap_premium_confidence: 95,
          gap_premium_source: 'Page 2, Section 3',
          refund_method: 'Pro-Rata',
          refund_method_confidence: 92,
          refund_method_source: 'Page 3, Section 1',
          cancellation_fee: 50.00,
          cancellation_fee_confidence: 88,
          cancellation_fee_source: 'Page 1, Section 5',
          status: 'approved',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await submitExtraction('EXT123', {
        corrections: [],
        notes: 'All values look correct',
      });

      expect(mockPost).toHaveBeenCalledWith('/extractions/EXT123/submit', {
        corrections: [],
        notes: 'All values look correct',
      });
      expect(result).toEqual(mockResponse.data);
      expect(result.status).toBe('approved');
    });

    it('should submit extraction with corrections', async () => {
      const { submitExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          id: 'EXT123',
          contractId: 'C123456',
          gap_premium: 1600.00, // corrected value
          gap_premium_confidence: 95,
          refund_method: 'Pro-Rata',
          refund_method_confidence: 92,
          cancellation_fee: 75.00, // corrected value
          cancellation_fee_confidence: 88,
          status: 'approved',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await submitExtraction('EXT123', {
        corrections: [
          {
            field_name: 'gap_insurance_premium',
            corrected_value: '1600.00',
            correction_reason: 'OCR misread the decimal point',
          },
          {
            field_name: 'cancellation_fee',
            corrected_value: '75.00',
            correction_reason: 'Value from page 2',
          },
        ],
        notes: 'Corrected premium and fee amounts',
      });

      expect(mockPost).toHaveBeenCalledWith('/extractions/EXT123/submit', {
        corrections: [
          {
            field_name: 'gap_insurance_premium',
            corrected_value: '1600.00',
            correction_reason: 'OCR misread the decimal point',
          },
          {
            field_name: 'cancellation_fee',
            corrected_value: '75.00',
            correction_reason: 'Value from page 2',
          },
        ],
        notes: 'Corrected premium and fee amounts',
      });
      expect(result).toEqual(mockResponse.data);
      expect(result.gap_premium).toBe(1600.00);
      expect(result.cancellation_fee).toBe(75.00);
    });

    it('should submit extraction with corrections but no notes', async () => {
      const { submitExtraction } = await import('@/lib/api/extractions');
      mockPost.mockResolvedValue({
        data: {
          id: 'EXT123',
          status: 'approved',
          gap_premium: 1550.00,
        }
      } as AxiosResponse);

      await submitExtraction('EXT123', {
        corrections: [
          {
            field_name: 'gap_insurance_premium',
            corrected_value: '1550.00',
          },
        ],
      });

      expect(mockPost).toHaveBeenCalledWith('/extractions/EXT123/submit', {
        corrections: [
          {
            field_name: 'gap_insurance_premium',
            corrected_value: '1550.00',
          },
        ],
      });
    });

    it('should handle submission errors (extraction not found)', async () => {
      const { submitExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 404,
          data: { message: 'Extraction not found' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(
        submitExtraction('INVALID', { corrections: [] })
      ).rejects.toThrow();
    });

    it('should handle submission errors (already submitted)', async () => {
      const { submitExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 400,
          data: { message: 'Extraction already submitted' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(
        submitExtraction('EXT123', { corrections: [] })
      ).rejects.toThrow();
    });

    it('should handle submission errors (validation error)', async () => {
      const { submitExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 400,
          data: { message: 'Invalid field name' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(
        submitExtraction('EXT123', {
          corrections: [
            {
              field_name: 'invalid_field' as any,
              corrected_value: 'test',
            },
          ],
        })
      ).rejects.toThrow();
    });
  });

  describe('Type Safety', () => {
    it('should return properly typed extraction data', async () => {
      const { getExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          id: 'EXT123',
          contractId: 'C123456',
          gap_premium: 1500.00,
          refund_method: 'Pro-Rata',
          cancellation_fee: 50.00,
          status: 'pending',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getExtraction('C123456');

      // Type assertions
      expect(result).toHaveProperty('gap_premium');
      expect(result).toHaveProperty('refund_method');
      expect(result).toHaveProperty('cancellation_fee');
      expect(typeof result.gap_premium).toBe('number');
      expect(typeof result.refund_method).toBe('string');
      expect(typeof result.cancellation_fee).toBe('number');
    });
  });
});
