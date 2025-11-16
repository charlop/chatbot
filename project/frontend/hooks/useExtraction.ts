import useSWR from 'swr';
import {
  getExtraction,
  submitExtraction,
  Extraction,
  SubmitExtractionRequest
} from '@/lib/api/extractions';

/**
 * Hook to fetch extraction data with SWR caching and submission mutation
 * @param contractId - The contract ID to fetch extraction for (null to skip fetching)
 * @returns SWR response with extraction data, loading, error states, and submit function
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

  /**
   * Submit extraction with optional corrections
   * Uses optimistic updates to immediately reflect changes in the UI
   * @param request - Submission request with corrections and notes
   */
  const submit = async (request: SubmitExtractionRequest) => {
    if (!data?.id) {
      throw new Error('Cannot submit: extraction data not loaded');
    }

    // Optimistic update: immediately update status to approved
    await mutate(
      async () => {
        const result = await submitExtraction(data.id, request);
        return result;
      },
      {
        optimisticData: data ? { ...data, status: 'approved' as const } : undefined,
        revalidate: true,
      }
    );
  };

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
    submit,
  };
};
