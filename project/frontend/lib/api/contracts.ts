import { apiClient } from './client';

/**
 * Type definitions for Contract API responses
 */
export interface ExtractedData {
  gap_premium: number;
  gap_premium_confidence?: number;
  gap_premium_source?: string;
  refund_method: string;
  refund_method_confidence?: number;
  refund_method_source?: string;
  cancellation_fee: number;
  cancellation_fee_confidence?: number;
  cancellation_fee_source?: string;
}

export interface AuditInfo {
  processed_by?: string;
  processed_at?: string;
  model_version?: string;
  processing_time_ms?: number;
  corrections_made?: number;
}

export interface Contract {
  id: string;
  accountNumber: string;
  pdfUrl?: string;
  extracted_data?: ExtractedData;
  audit_info?: AuditInfo;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SearchContractResponse {
  contractId: string;
  accountNumber: string;
  status: string;
}

/**
 * Search for a contract by account number
 * @param accountNumber - The account number to search for (format: XXXX-XXXX-XXXX)
 * @returns Promise with contract search results
 */
export const searchContract = async (
  accountNumber: string
): Promise<SearchContractResponse> => {
  const response = await apiClient.post<SearchContractResponse>('/search', {
    accountNumber,
  });
  return response.data;
};

/**
 * Get contract details by contract ID
 * @param contractId - The contract ID
 * @returns Promise with full contract details including extracted data and audit info
 */
export const getContract = async (contractId: string): Promise<Contract> => {
  const response = await apiClient.get<Contract>(`/contract/${contractId}`);
  return response.data;
};

/**
 * Get contract PDF URL
 * @param contractId - The contract ID
 * @returns Promise with PDF URL
 */
export const getContractPdfUrl = async (contractId: string): Promise<string> => {
  const contract = await getContract(contractId);
  if (!contract.pdfUrl) {
    throw new Error('PDF URL not available for this contract');
  }
  return contract.pdfUrl;
};
