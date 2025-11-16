import { apiClient } from './client';

/**
 * Type definitions for Extraction API responses
 */
export interface Extraction {
  id: string;
  contractId: string;
  gap_premium: number;
  gap_premium_confidence?: number;
  gap_premium_source?: string;
  refund_method: string;
  refund_method_confidence?: number;
  refund_method_source?: string;
  cancellation_fee: number;
  cancellation_fee_confidence?: number;
  cancellation_fee_source?: string;
  status?: 'pending' | 'approved';
  created_at?: string;
  updated_at?: string;
}

/**
 * Field correction for submission
 * Matches backend FieldCorrection schema
 */
export interface FieldCorrection {
  field_name: 'gap_insurance_premium' | 'refund_calculation_method' | 'cancellation_fee';
  corrected_value: string;
  correction_reason?: string;
}

/**
 * Request payload for submitting extraction
 * Matches backend ExtractionSubmitRequest schema
 */
export interface SubmitExtractionRequest {
  corrections: FieldCorrection[];
  notes?: string;
}

/**
 * Response from submission
 */
export interface SubmitExtractionResponse extends Extraction {
  // Backend returns the updated Extraction
}

/**
 * Create/trigger extraction for a contract
 * @param contractId - The contract ID
 * @param force_reextract - Force re-extraction even if exists
 * @returns Promise with extraction data
 */
export const createExtraction = async (
  contractId: string,
  force_reextract: boolean = false
): Promise<Extraction> => {
  const response = await apiClient.post<Extraction>('/extractions/create', {
    contract_id: contractId,
    force_reextract,
  });
  return response.data;
};

/**
 * Get extraction data for a contract
 * @param contractId - The contract ID
 * @returns Promise with extraction data including confidence scores and source locations
 */
export const getExtraction = async (contractId: string): Promise<Extraction> => {
  const response = await apiClient.get<Extraction>(`/contract/${contractId}/extraction`);
  return response.data;
};

/**
 * Submit extraction with optional corrections
 * Combines approval with inline field corrections in a single operation
 * @param extractionId - The extraction ID
 * @param request - Submission request with optional corrections and notes
 * @returns Promise with updated extraction data
 */
export const submitExtraction = async (
  extractionId: string,
  request: SubmitExtractionRequest
): Promise<SubmitExtractionResponse> => {
  const response = await apiClient.post<SubmitExtractionResponse>(
    `/extractions/${extractionId}/submit`,
    request
  );
  return response.data;
};
