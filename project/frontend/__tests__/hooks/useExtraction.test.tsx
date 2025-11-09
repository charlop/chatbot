import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { SWRConfig } from 'swr';

// Mock the extractions API
const mockGetExtraction = vi.fn();

vi.mock('@/lib/api/extractions', () => ({
  getExtraction: mockGetExtraction,
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
});
