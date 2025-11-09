import useSWR from 'swr';
import { getExtraction, Extraction } from '@/lib/api/extractions';

/**
 * Hook to fetch extraction data for a contract with SWR caching
 * @param contractId - The contract ID to fetch extraction for (null to skip fetching)
 * @returns SWR response with extraction data, loading, and error states
 */
export const useExtraction = (contractId: string | null) => {
  const {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  } = useSWR<Extraction>(
    contractId ? `/contract/${contractId}/extraction` : null,
    () => contractId ? getExtraction(contractId) : Promise.resolve(null as any),
    {
      revalidateOnFocus: false, // Don't revalidate on window focus
      revalidateOnReconnect: true, // Revalidate on network reconnect
      shouldRetryOnError: true,
      errorRetryCount: 2,
      dedupingInterval: 2000, // 2 seconds
      // Extraction data changes frequently when being edited, so we want fresh data
      revalidateIfStale: true,
    }
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
};
