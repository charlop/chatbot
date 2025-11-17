import { apiClient } from './client';

/**
 * Type definitions for Contract API responses
 */
export interface ExtractedData {
  extractionId: string;
  gapPremium: number;
  gapPremiumConfidence?: number;
  gapPremiumSource?: any;
  refundMethod: string;
  refundMethodConfidence?: number;
  refundMethodSource?: any;
  cancellationFee: number;
  cancellationFeeConfidence?: number;
  cancellationFeeSource?: any;
  status?: 'pending' | 'approved';
  // Audit metadata
  llmModelVersion?: string;
  llmProvider?: string;
  processingTimeMs?: number;
  extractedAt?: string;
  extractedBy?: string;
  approvedAt?: string;
  approvedBy?: string;
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
  contractId: string;
  accountNumber: string;

  // S3 Storage (for backend use and debugging)
  s3Bucket?: string;
  s3Key?: string;

  // Document Content Status (populated by external ETL)
  textExtractionStatus?: string; // 'pending', 'completed', 'failed'
  textExtractedAt?: string;

  documentRepositoryId?: string;
  contract_type?: string;
  contractType?: string;
  contract_date?: string;
  contractDate?: string;
  customer_name?: string;
  customerName?: string;
  vehicleInfo?: Record<string, any>;
  vehicle_info?: Record<string, any>;
  extractedData?: ExtractedData;
  extracted_data?: ExtractedData;
  audit_info?: AuditInfo;
  status?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
  lastSyncedAt?: string;
  last_synced_at?: string;
}

export interface SearchContractResponse {
  contractId: string;
  accountNumber: string;

  // S3 Storage (for backend use and debugging)
  s3Bucket?: string;
  s3Key?: string;

  // Document Content Status
  textExtractionStatus?: string;
  textExtractedAt?: string;

  documentRepositoryId?: string;
  contractType: string;
  contractDate?: string;
  customerName?: string;
  vehicleInfo?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  lastSyncedAt?: string;
}

/**
 * Search for a contract by account number
 * @param accountNumber - The account number to search for (format: XXX-XXXX-XXXXX or 12 digits)
 * @returns Promise with contract search results
 */
export const searchContract = async (
  accountNumber: string
): Promise<SearchContractResponse> => {
  // Strip dashes - backend expects only digits
  const cleanedAccountNumber = accountNumber.replace(/\D/g, '');

  // Backend expects snake_case
  const response = await apiClient.post<SearchContractResponse>('/contracts/search', {
    account_number: cleanedAccountNumber,
  });
  return response.data;
};

/**
 * Get contract details by contract ID
 * @param contractId - The contract ID
 * @returns Promise with full contract details including extracted data and audit info
 */
export const getContract = async (contractId: string): Promise<Contract> => {
  const response = await apiClient.get<Contract>(`/contracts/${contractId}`);
  return response.data;
};

/**
 * Get contract PDF URL (backend proxy endpoint)
 * @param contractId - The contract ID
 * @returns Promise with PDF endpoint URL
 */
export const getContractPdfUrl = async (contractId: string): Promise<string> => {
  return `/api/v1/contracts/${contractId}/pdf`;
};
