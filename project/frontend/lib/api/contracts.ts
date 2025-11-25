import { apiClient } from './client';

/**
 * Type definitions for Contract Template API responses
 *
 * NOTE: These are contract TEMPLATES, not filled customer contracts.
 * Templates contain placeholders like [CUSTOMER NAME], [VIN NUMBER], etc.
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

export interface ContractTemplate {
  id: string;
  contractId: string; // Template ID (e.g., GAP-2024-TEMPLATE-001)

  // S3 Storage (for backend use and debugging)
  s3Bucket?: string;
  s3Key?: string;

  // Document Content Status (populated by external ETL)
  textExtractionStatus?: string; // 'pending', 'completed', 'failed'
  textExtractedAt?: string;

  // Template Metadata
  documentRepositoryId?: string;
  contractType?: string; // GAP, VSC, etc.
  contractDate?: string; // When template was created

  // Template Versioning
  templateVersion?: string; // e.g., "1.0", "2.0"
  effectiveDate?: string; // When this version became active
  deprecatedDate?: string; // When this version was superseded
  isActive?: boolean; // Whether this template version is currently active

  // Extracted data from template
  extractedData?: ExtractedData;
  extracted_data?: ExtractedData;
  audit_info?: AuditInfo;
  status?: string;

  // Timestamps
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
  lastSyncedAt?: string;
  last_synced_at?: string;
}

// Alias for backward compatibility
export type Contract = ContractTemplate;

export interface SearchContractResponse {
  contractId: string; // Template ID

  // S3 Storage (for backend use and debugging)
  s3Bucket?: string;
  s3Key?: string;

  // Document Content Status
  textExtractionStatus?: string;
  textExtractedAt?: string;

  // Template Metadata
  documentRepositoryId?: string;
  contractType: string;
  contractDate?: string;

  // Template Versioning
  templateVersion?: string;
  effectiveDate?: string;
  deprecatedDate?: string;
  isActive?: boolean;

  // Timestamps
  createdAt: string;
  updatedAt: string;
  lastSyncedAt?: string;
}

/**
 * Search for a contract template by account number
 *
 * Account number search uses hybrid cache strategy:
 * 1. Check Redis cache (fast path)
 * 2. Check account_mappings table (DB cache)
 * 3. Call external API (fallback)
 * 4. Fetch template details
 *
 * @param accountNumber - The account number to search for (12 digits)
 * @returns Promise with contract template search results
 */
export const searchContractByAccount = async (
  accountNumber: string
): Promise<SearchContractResponse> => {
  // Strip dashes and non-digits - backend expects only digits
  const cleanedAccountNumber = accountNumber.replace(/\D/g, '');

  // Backend expects snake_case
  const response = await apiClient.post<SearchContractResponse>('/contracts/search', {
    account_number: cleanedAccountNumber,
  });
  return response.data;
};

/**
 * Search for a contract template by template ID
 *
 * @param contractId - The contract template ID (e.g., GAP-2024-TEMPLATE-001)
 * @returns Promise with contract template search results
 */
export const searchContractById = async (
  contractId: string
): Promise<SearchContractResponse> => {
  const response = await apiClient.post<SearchContractResponse>('/contracts/search', {
    contract_id: contractId,
  });
  return response.data;
};

/**
 * Search for a contract template by either account number or template ID
 *
 * @param searchTerm - Either account number (12 digits) or template ID
 * @returns Promise with contract template search results
 */
export const searchContract = async (
  searchTerm: string
): Promise<SearchContractResponse> => {
  // Auto-detect search type: if it's all digits and 12 chars, assume account number
  const isAccountNumber = /^\d{12}$/.test(searchTerm.replace(/\D/g, ''));

  if (isAccountNumber) {
    return searchContractByAccount(searchTerm);
  } else {
    return searchContractById(searchTerm);
  }
};

/**
 * Get contract template details by template ID
 *
 * @param contractId - The contract template ID
 * @returns Promise with full template details including extracted data
 */
export const getContract = async (contractId: string): Promise<Contract> => {
  const response = await apiClient.get<Contract>(`/contracts/${contractId}`);
  return response.data;
};

/**
 * Get contract template PDF URL (backend proxy endpoint)
 *
 * @param contractId - The contract template ID
 * @returns Promise with PDF endpoint URL
 */
export const getContractPdfUrl = async (contractId: string): Promise<string> => {
  return `/api/v1/contracts/${contractId}/pdf`;
};
