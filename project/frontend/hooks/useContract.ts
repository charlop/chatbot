import useSWR from 'swr';
import { getContract, searchContract, Contract, SearchContractResponse } from '@/lib/api/contracts';

/**
 * Hook to fetch contract data with SWR caching
 * @param contractId - The contract ID to fetch (null to skip fetching)
 * @returns SWR response with contract data, loading, and error states
 */
export const useContract = (contractId: string | null) => {
  const {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  } = useSWR<Contract>(
    contractId ? `/contract/${contractId}` : null,
    () => contractId ? getContract(contractId) : Promise.resolve(null as any),
    {
      revalidateOnFocus: false, // Don't revalidate on window focus
      revalidateOnReconnect: true, // Revalidate on network reconnect
      shouldRetryOnError: true,
      errorRetryCount: 2,
      dedupingInterval: 2000, // 2 seconds
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

/**
 * Hook to search for a contract by account number
 * @param accountNumber - The account number to search for (null to skip searching)
 * @returns SWR response with search results, loading, and error states
 */
export const useSearchContract = (accountNumber: string | null) => {
  const {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  } = useSWR<SearchContractResponse>(
    accountNumber ? `/search/${accountNumber}` : null,
    () => accountNumber ? searchContract(accountNumber) : Promise.resolve(null as any),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false, // Search results shouldn't auto-revalidate
      shouldRetryOnError: true,
      errorRetryCount: 1,
      dedupingInterval: 5000, // 5 seconds - cache search results longer
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
