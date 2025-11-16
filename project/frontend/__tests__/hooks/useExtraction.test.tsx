import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { SWRConfig } from 'swr';

// Mock the extractions API
const mockGetExtraction = vi.fn();
const mockSubmitExtraction = vi.fn();

vi.mock('@/lib/api/extractions', () => ({
  getExtraction: mockGetExtraction,
  submitExtraction: mockSubmitExtraction,
}));

// Wrapper component to provide SWR config
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
    {children}
  </SWRConfig>
);

describe('useExtraction Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch extraction data successfully', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
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
      status: 'pending' as const,
    };

    mockGetExtraction.mockResolvedValue(mockData);

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.error).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle errors when fetching extraction', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockError = new Error('Extraction not found');

    mockGetExtraction.mockRejectedValue(mockError);

    const { result } = renderHook(() => useExtraction('INVALID'), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    expect(result.current.data).toBeUndefined();
  });

  it('should not fetch when contractId is null', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');

    const { result } = renderHook(() => useExtraction(null), { wrapper });

    expect(mockGetExtraction).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it('should provide mutate function for cache updates', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
      id: 'EXT123',
      contractId: 'C123456',
      gap_premium: 1500.00,
      refund_method: 'Pro-Rata',
      cancellation_fee: 50.00,
    };

    mockGetExtraction.mockResolvedValue(mockData);

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.mutate).toBeDefined();
    expect(typeof result.current.mutate).toBe('function');
  });

  it('should revalidate extraction data', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
      id: 'EXT123',
      contractId: 'C123456',
      gap_premium: 1500.00,
      refund_method: 'Pro-Rata',
      cancellation_fee: 50.00,
    };

    mockGetExtraction.mockResolvedValue(mockData);

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.isValidating).toBeDefined();
  });

  it('should provide submit function', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
      id: 'EXT123',
      contractId: 'C123456',
      gap_premium: 1500.00,
      refund_method: 'Pro-Rata',
      cancellation_fee: 50.00,
      status: 'pending' as const,
    };

    mockGetExtraction.mockResolvedValue(mockData);

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.submit).toBeDefined();
    expect(typeof result.current.submit).toBe('function');
  });

  it('should submit extraction without corrections', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
      id: 'EXT123',
      contractId: 'C123456',
      gap_premium: 1500.00,
      refund_method: 'Pro-Rata',
      cancellation_fee: 50.00,
      status: 'pending' as const,
    };

    const mockSubmittedData = {
      ...mockData,
      status: 'approved' as const,
    };

    mockGetExtraction.mockResolvedValue(mockData);
    mockSubmitExtraction.mockResolvedValue(mockSubmittedData);

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    // Submit without corrections
    await act(async () => {
      await result.current.submit({
        corrections: [],
        notes: 'All values look correct',
      });
    });

    // Verify the API was called correctly
    expect(mockSubmitExtraction).toHaveBeenCalledWith('EXT123', {
      corrections: [],
      notes: 'All values look correct',
    });
  });

  it('should submit extraction with corrections', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
      id: 'EXT123',
      contractId: 'C123456',
      gap_premium: 1500.00,
      refund_method: 'Pro-Rata',
      cancellation_fee: 50.00,
      status: 'pending' as const,
    };

    const mockSubmittedData = {
      ...mockData,
      gap_premium: 1600.00,
      status: 'approved' as const,
    };

    mockGetExtraction.mockResolvedValue(mockData);
    mockSubmitExtraction.mockResolvedValue(mockSubmittedData);

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    // Submit with corrections
    await act(async () => {
      await result.current.submit({
        corrections: [
          {
            field_name: 'gap_insurance_premium',
            corrected_value: '1600.00',
            correction_reason: 'OCR misread decimal',
          },
        ],
        notes: 'Corrected premium',
      });
    });

    // Verify the API was called correctly with corrections
    expect(mockSubmitExtraction).toHaveBeenCalledWith('EXT123', {
      corrections: [
        {
          field_name: 'gap_insurance_premium',
          corrected_value: '1600.00',
          correction_reason: 'OCR misread decimal',
        },
      ],
      notes: 'Corrected premium',
    });
  });

  it('should throw error when submitting without loaded data', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');

    const { result } = renderHook(() => useExtraction(null), { wrapper });

    await expect(
      result.current.submit({ corrections: [] })
    ).rejects.toThrow('Cannot submit: extraction data not loaded');
  });

  it('should handle submit errors gracefully', async () => {
    const { useExtraction } = await import('@/hooks/useExtraction');
    const mockData = {
      id: 'EXT123',
      contractId: 'C123456',
      gap_premium: 1500.00,
      refund_method: 'Pro-Rata',
      cancellation_fee: 50.00,
      status: 'pending' as const,
    };

    mockGetExtraction.mockResolvedValue(mockData);
    mockSubmitExtraction.mockRejectedValue(new Error('Submission failed'));

    const { result } = renderHook(() => useExtraction('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    await act(async () => {
      await expect(
        result.current.submit({ corrections: [] })
      ).rejects.toThrow('Submission failed');
    });
  });
});
