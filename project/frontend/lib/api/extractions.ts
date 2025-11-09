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
  status?: 'pending' | 'approved' | 'rejected';
  created_at?: string;
  updated_at?: string;
}

export interface ApprovalResponse {
  success: boolean;
  audit_id?: string;
  message?: string;
}

export interface EditResponse {
  success: boolean;
  field: string;
  oldValue: any;
  newValue: any;
  message?: string;
}

export interface RejectResponse {
  success: boolean;
  message?: string;
}

export interface ExtractionCorrections {
  gap_premium?: number;
  refund_method?: string;
  cancellation_fee?: number;
}

export type ExtractionField = 'gap_premium' | 'refund_method' | 'cancellation_fee';

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
 * Approve extraction data
 * @param contractId - The contract ID
 * @param userId - The user ID approving the extraction
 * @param corrections - Optional corrections to apply before approval
 * @returns Promise with approval confirmation
 */
export const approveExtraction = async (
  contractId: string,
  userId: string,
  corrections?: ExtractionCorrections
): Promise<ApprovalResponse> => {
  const response = await apiClient.post<ApprovalResponse>(`/contract/${contractId}/approve`, {
    userId,
    ...(corrections && { corrections }),
  });
  return response.data;
};

/**
 * Edit a single extraction field
 * @param contractId - The contract ID
 * @param field - The field to edit
 * @param value - The new value
 * @param reason - Optional reason for the correction
 * @returns Promise with edit confirmation
 */
export const editExtraction = async (
  contractId: string,
  field: ExtractionField,
  value: number | string,
  reason?: string
): Promise<EditResponse> => {
  const response = await apiClient.patch<EditResponse>(`/contract/${contractId}/extraction`, {
    field,
    value,
    ...(reason && { reason }),
  });
  return response.data;
};

/**
 * Reject extraction data
 * @param contractId - The contract ID
 * @param reason - Reason for rejection
 * @returns Promise with rejection confirmation
 */
export const rejectExtraction = async (
  contractId: string,
  reason: string
): Promise<RejectResponse> => {
  const response = await apiClient.post<RejectResponse>(`/contract/${contractId}/reject`, {
    reason,
  });
  return response.data;
};
