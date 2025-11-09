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

  describe('approveExtraction', () => {
    it('should approve extraction with user ID', async () => {
      const { approveExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          success: true,
          audit_id: 'AUD123',
          message: 'Extraction approved successfully',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await approveExtraction('C123456', 'user123');

      expect(mockPost).toHaveBeenCalledWith('/contract/C123456/approve', {
        userId: 'user123',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should approve extraction with corrections', async () => {
      const { approveExtraction } = await import('@/lib/api/extractions');
      const corrections = {
        gap_premium: 1600.00,
        cancellation_fee: 75.00,
      };

      mockPost.mockResolvedValue({ data: { success: true } } as AxiosResponse);

      await approveExtraction('C123456', 'user123', corrections);

      expect(mockPost).toHaveBeenCalledWith('/contract/C123456/approve', {
        userId: 'user123',
        corrections,
      });
    });

    it('should handle approval errors', async () => {
      const { approveExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 500,
          data: { message: 'Failed to approve extraction' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(approveExtraction('C123456', 'user123')).rejects.toThrow();
    });
  });

  describe('editExtraction', () => {
    it('should edit extraction field with new value', async () => {
      const { editExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          success: true,
          field: 'gap_premium',
          oldValue: 1500.00,
          newValue: 1600.00,
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPatch.mockResolvedValue(mockResponse);

      const result = await editExtraction('C123456', 'gap_premium', 1600.00);

      expect(mockPatch).toHaveBeenCalledWith('/contract/C123456/extraction', {
        field: 'gap_premium',
        value: 1600.00,
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should edit extraction field with reason', async () => {
      const { editExtraction } = await import('@/lib/api/extractions');

      mockPatch.mockResolvedValue({ data: { success: true } } as AxiosResponse);

      await editExtraction('C123456', 'gap_premium', 1600.00, 'Corrected from contract PDF');

      expect(mockPatch).toHaveBeenCalledWith('/contract/C123456/extraction', {
        field: 'gap_premium',
        value: 1600.00,
        reason: 'Corrected from contract PDF',
      });
    });

    it('should handle edit errors', async () => {
      const { editExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 400,
          data: { message: 'Invalid field value' },
        },
      };

      mockPatch.mockRejectedValue(error);

      await expect(editExtraction('C123456', 'gap_premium', -100)).rejects.toThrow();
    });
  });

  describe('rejectExtraction', () => {
    it('should reject extraction with reason', async () => {
      const { rejectExtraction } = await import('@/lib/api/extractions');
      const mockResponse: AxiosResponse = {
        data: {
          success: true,
          message: 'Extraction rejected',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await rejectExtraction('C123456', 'Incorrect data extraction');

      expect(mockPost).toHaveBeenCalledWith('/contract/C123456/reject', {
        reason: 'Incorrect data extraction',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle rejection errors', async () => {
      const { rejectExtraction } = await import('@/lib/api/extractions');
      const error = {
        response: {
          status: 500,
          data: { message: 'Failed to reject extraction' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(rejectExtraction('C123456', 'Bad data')).rejects.toThrow();
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
