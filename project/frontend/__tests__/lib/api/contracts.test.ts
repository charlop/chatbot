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
    it('should search for a contract by account number and strip dashes', async () => {
      const { searchContract } = await import('@/lib/api/contracts');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'GAP-2024-TEMPLATE-001',
          contractType: 'GAP',
          templateVersion: '1.0',
          isActive: true,
          s3Bucket: 'test-bucket',
          s3Key: 'templates/GAP-2024-TEMPLATE-001.pdf',
          createdAt: '2025-11-01T00:00:00Z',
          updatedAt: '2025-11-01T00:00:00Z',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      // Call with formatted value (with dashes)
      const result = await searchContract('123-4567-89012');

      // Should strip dashes before sending to API
      expect(mockPost).toHaveBeenCalledWith('/contracts/search', {
        account_number: '123456789012',
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

      await expect(searchContract('000-0000-00000')).rejects.toThrow();
    });

    it('should handle account numbers without dashes', async () => {
      const { searchContract } = await import('@/lib/api/contracts');

      // Should work with unformatted input too
      mockPost.mockResolvedValue({ data: {} } as AxiosResponse);
      await searchContract('123456789012');

      expect(mockPost).toHaveBeenCalledWith('/contracts/search', {
        account_number: '123456789012',
      });
    });
  });

  describe('getContract', () => {
    it('should get contract template by ID', async () => {
      const { getContract } = await import('@/lib/api/contracts');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'GAP-2024-TEMPLATE-001',
          contractType: 'GAP',
          templateVersion: '1.0',
          isActive: true,
          s3Bucket: 'test-bucket',
          s3Key: 'templates/GAP-2024-TEMPLATE-001.pdf',
          extractedData: {
            gapInsurancePremium: { value: 1500.00, confidence: 95.5 },
            refundCalculationMethod: { value: 'Pro-Rata', confidence: 88.0 },
            cancellationFee: { value: 50.00, confidence: 92.0 },
          },
          createdAt: '2025-11-01T00:00:00Z',
          updatedAt: '2025-11-01T00:00:00Z',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getContract('GAP-2024-TEMPLATE-001');

      expect(mockGet).toHaveBeenCalledWith('/contracts/GAP-2024-TEMPLATE-001');
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
    it('should return properly typed contract template data', async () => {
      const { getContract } = await import('@/lib/api/contracts');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'GAP-2024-TEMPLATE-001',
          contractType: 'GAP',
          templateVersion: '1.0',
          isActive: true,
          s3Bucket: 'test-bucket',
          s3Key: 'templates/GAP-2024-TEMPLATE-001.pdf',
          extractedData: {
            gapInsurancePremium: { value: 1500.00, confidence: 95.5 },
            refundCalculationMethod: { value: 'Pro-Rata', confidence: 88.0 },
            cancellationFee: { value: 50.00, confidence: 92.0 },
          },
          createdAt: '2025-11-01T00:00:00Z',
          updatedAt: '2025-11-01T00:00:00Z',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getContract('GAP-2024-TEMPLATE-001');

      // Type assertions to verify template structure
      expect(result).toHaveProperty('contractId');
      expect(result).toHaveProperty('contractType');
      expect(result).toHaveProperty('templateVersion');
      expect(result).toHaveProperty('isActive');
      expect(result).toHaveProperty('extractedData');
    });
  });
});
