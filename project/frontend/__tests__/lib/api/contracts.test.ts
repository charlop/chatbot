import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AxiosResponse } from 'axios';

// Mock the API client
const mockGet = vi.fn();
const mockPost = vi.fn();

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
  },
}));

describe('Contracts API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('searchContract', () => {
    it('should search for a contract by account number', async () => {
      const { searchContract } = await import('@/lib/api/contracts');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'C123456',
          accountNumber: '1234-5678-9012',
          status: 'active',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await searchContract('1234-5678-9012');

      expect(mockPost).toHaveBeenCalledWith('/search', {
        accountNumber: '1234-5678-9012',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error when account number not found', async () => {
      const { searchContract } = await import('@/lib/api/contracts');
      const error = {
        response: {
          status: 404,
          data: { message: 'Contract not found' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(searchContract('0000-0000-0000')).rejects.toThrow();
    });

    it('should validate account number format', async () => {
      const { searchContract } = await import('@/lib/api/contracts');

      // Should not throw for valid format
      mockPost.mockResolvedValue({ data: {} } as AxiosResponse);
      await expect(searchContract('1234-5678-9012')).resolves.toBeDefined();
    });
  });

  describe('getContract', () => {
    it('should get contract by ID', async () => {
      const { getContract } = await import('@/lib/api/contracts');
      const mockResponse: AxiosResponse = {
        data: {
          id: 'C123456',
          accountNumber: '1234-5678-9012',
          pdfUrl: 'https://example.com/contract.pdf',
          extracted_data: {
            gap_premium: 1500.00,
            refund_method: 'Pro-Rata',
            cancellation_fee: 50.00,
          },
          audit_info: {
            processed_by: 'user123',
            processed_at: '2025-11-09T00:00:00Z',
            model_version: 'gpt-4',
          },
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getContract('C123456');

      expect(mockGet).toHaveBeenCalledWith('/contract/C123456');
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error when contract ID not found', async () => {
      const { getContract } = await import('@/lib/api/contracts');
      const error = {
        response: {
          status: 404,
          data: { message: 'Contract not found' },
        },
      };

      mockGet.mockRejectedValue(error);

      await expect(getContract('INVALID')).rejects.toThrow();
    });

    it('should handle server errors gracefully', async () => {
      const { getContract } = await import('@/lib/api/contracts');
      const error = {
        response: {
          status: 500,
          data: { message: 'Internal server error' },
        },
      };

      mockGet.mockRejectedValue(error);

      await expect(getContract('C123456')).rejects.toThrow();
    });
  });

  describe('Type Safety', () => {
    it('should return properly typed contract data', async () => {
      const { getContract } = await import('@/lib/api/contracts');
      const mockResponse: AxiosResponse = {
        data: {
          id: 'C123456',
          accountNumber: '1234-5678-9012',
          pdfUrl: 'https://example.com/contract.pdf',
          extracted_data: {
            gap_premium: 1500.00,
            refund_method: 'Pro-Rata',
            cancellation_fee: 50.00,
          },
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getContract('C123456');

      // Type assertions to verify structure
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('accountNumber');
      expect(result).toHaveProperty('pdfUrl');
      expect(result).toHaveProperty('extracted_data');
    });
  });
});
