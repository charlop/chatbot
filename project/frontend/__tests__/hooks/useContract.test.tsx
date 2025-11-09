import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { SWRConfig } from 'swr';

// Mock the contracts API
const mockGetContract = vi.fn();
const mockSearchContract = vi.fn();

vi.mock('@/lib/api/contracts', () => ({
  getContract: mockGetContract,
  searchContract: mockSearchContract,
}));

// Wrapper component to provide SWR config
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
    {children}
  </SWRConfig>
);

describe('useContract Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch contract data successfully', async () => {
    const { useContract } = await import('@/hooks/useContract');
    const mockData = {
      id: 'C123456',
      accountNumber: '1234-5678-9012',
      pdfUrl: 'https://example.com/contract.pdf',
      extracted_data: {
        gap_premium: 1500.00,
        refund_method: 'Pro-Rata',
        cancellation_fee: 50.00,
      },
    };

    mockGetContract.mockResolvedValue(mockData);

    const { result } = renderHook(() => useContract('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.error).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle errors when fetching contract', async () => {
    const { useContract } = await import('@/hooks/useContract');
    const mockError = new Error('Contract not found');

    mockGetContract.mockRejectedValue(mockError);

    const { result } = renderHook(() => useContract('INVALID'), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    expect(result.current.data).toBeUndefined();
  });

  it('should not fetch when contractId is null', async () => {
    const { useContract } = await import('@/hooks/useContract');

    const { result } = renderHook(() => useContract(null), { wrapper });

    expect(mockGetContract).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it('should provide isValidating state', async () => {
    const { useContract } = await import('@/hooks/useContract');
    mockGetContract.mockResolvedValue({ id: 'C123456' });

    const { result } = renderHook(() => useContract('C123456'), { wrapper });

    expect(result.current.isValidating).toBeDefined();
  });

  it('should allow manual revalidation via mutate', async () => {
    const { useContract } = await import('@/hooks/useContract');
    const mockData = { id: 'C123456' };
    mockGetContract.mockResolvedValue(mockData);

    const { result } = renderHook(() => useContract('C123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.mutate).toBeDefined();
    expect(typeof result.current.mutate).toBe('function');
  });
});

describe('useSearchContract Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should search for contract by account number', async () => {
    const { useSearchContract } = await import('@/hooks/useContract');
    const mockSearchResult = {
      contractId: 'C123456',
      accountNumber: '1234-5678-9012',
      status: 'active',
    };

    mockSearchContract.mockResolvedValue(mockSearchResult);

    const { result } = renderHook(() => useSearchContract('1234-5678-9012'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockSearchResult);
    });

    expect(result.current.error).toBeUndefined();
  });

  it('should handle search not found', async () => {
    const { useSearchContract } = await import('@/hooks/useContract');
    const mockError = new Error('Contract not found');

    mockSearchContract.mockRejectedValue(mockError);

    const { result } = renderHook(() => useSearchContract('0000-0000-0000'), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });
  });

  it('should not search when account number is null', async () => {
    const { useSearchContract } = await import('@/hooks/useContract');

    const { result } = renderHook(() => useSearchContract(null), { wrapper });

    expect(mockSearchContract).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });
});
