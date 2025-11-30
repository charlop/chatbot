import React, { useState } from 'react';
import { DataCard } from './DataCard';
import { SubmitModal } from './SubmitModal';
import { AuditTrail } from '@/components/audit/AuditTrail';
import type { Extraction, FieldCorrection } from '@/lib/api/extractions';
import type { ExtractedData } from '@/lib/api/contracts';

export interface DataPanelProps {
  /**
   * Extraction data to display
   */
  extraction: Extraction;

  /**
   * Extracted data from contract (includes audit metadata)
   */
  extractedData?: ExtractedData;

  /**
   * Callback when submit is clicked
   */
  onSubmit: (corrections: FieldCorrection[], notes?: string) => void;

  /**
   * Callback when "View in document" is clicked
   */
  onViewInDocument?: (source: string) => void;

  /**
   * Optional CSS class
   */
  className?: string;
}

// Field name mapping (frontend → backend)
const FIELD_NAME_MAP = {
  gap_premium: 'gap_insurance_premium',
  refund_method: 'refund_calculation_method',
  cancellation_fee: 'cancellation_fee',
} as const;

/**
 * Panel component for displaying all extracted data fields with edit capability
 * Fixed width: 464px
 */
export const DataPanel: React.FC<DataPanelProps> = ({
  extraction,
  extractedData,
  onSubmit,
  onViewInDocument,
  className = '',
}) => {
  const [corrections, setCorrections] = useState<Map<string, string>>(new Map());
  const [isModalOpen, setIsModalOpen] = useState(false);

  const isDisabled = extraction.status === 'approved';

  // Handle field change
  const handleFieldChange = (fieldKey: keyof typeof FIELD_NAME_MAP, newValue: string) => {
    // Get original value with proper formatting
    let originalValue: string;
    if (fieldKey === 'gap_premium' || fieldKey === 'cancellation_fee') {
      originalValue = extraction[fieldKey].toFixed(2);
    } else {
      originalValue = extraction[fieldKey];
    }

    if (newValue !== originalValue) {
      // Value changed - add correction
      setCorrections((prev) => {
        const next = new Map(prev);
        next.set(fieldKey, newValue);
        return next;
      });
    } else {
      // Value reverted to original - remove correction
      setCorrections((prev) => {
        const next = new Map(prev);
        next.delete(fieldKey);
        return next;
      });
    }
  };

  // Handle submit button click
  const handleSubmitClick = () => {
    setIsModalOpen(true);
  };

  // Handle modal submit
  const handleModalSubmit = (notes?: string) => {
    // Convert corrections map to array of FieldCorrection objects
    const correctionArray: FieldCorrection[] = Array.from(corrections.entries()).map(
      ([fieldKey, correctedValue]) => ({
        field_name: FIELD_NAME_MAP[fieldKey as keyof typeof FIELD_NAME_MAP],
        corrected_value: correctedValue,
      })
    );

    onSubmit(correctionArray, notes);
    setIsModalOpen(false);
  };

  // Handle modal cancel
  const handleModalCancel = () => {
    setIsModalOpen(false);
  };

  const correctionsCount = corrections.size;

  return (
    <>
      <div
        className={`w-[464px] h-full bg-neutral-50 border-l border-neutral-200 overflow-y-auto ${className}`}
      >
        <div className="p-6 space-y-4">
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-lg font-bold text-neutral-900">Extracted Data</h2>
            <p className="text-sm text-neutral-600 mt-1">
              Review and edit the extracted values below
            </p>
          </div>

          {/* GAP Insurance Premium */}
          <DataCard
            label="GAP Insurance Premium"
            value={
              corrections.has('gap_premium')
                ? corrections.get('gap_premium')!
                : extraction.gap_premium.toFixed(2)
            }
            confidence={extraction.gap_premium_confidence}
            source={extraction.gap_premium_source}
            isEdited={corrections.has('gap_premium')}
            disabled={isDisabled}
            onChange={(newValue) => handleFieldChange('gap_premium', newValue)}
            onViewInDocument={
              onViewInDocument && extractedData?.gapPremiumSource
                ? () => onViewInDocument(extractedData.gapPremiumSource)
                : undefined
            }
          />

          {/* Refund Calculation Method */}
          <DataCard
            label="Refund Calculation Method"
            value={
              corrections.has('refund_method')
                ? corrections.get('refund_method')!
                : extraction.refund_method
            }
            confidence={extraction.refund_method_confidence}
            source={extraction.refund_method_source}
            isEdited={corrections.has('refund_method')}
            disabled={isDisabled}
            onChange={(newValue) => handleFieldChange('refund_method', newValue)}
            onViewInDocument={
              onViewInDocument && extractedData?.refundMethodSource
                ? () => onViewInDocument(extractedData.refundMethodSource)
                : undefined
            }
          />

          {/* Cancellation Fee */}
          <DataCard
            label="Cancellation Fee"
            value={
              corrections.has('cancellation_fee')
                ? corrections.get('cancellation_fee')!
                : extraction.cancellation_fee.toFixed(2)
            }
            confidence={extraction.cancellation_fee_confidence}
            source={extraction.cancellation_fee_source}
            isEdited={corrections.has('cancellation_fee')}
            disabled={isDisabled}
            onChange={(newValue) => handleFieldChange('cancellation_fee', newValue)}
            onViewInDocument={
              onViewInDocument && extractedData?.cancellationFeeSource
                ? () => onViewInDocument(extractedData.cancellationFeeSource)
                : undefined
            }
          />

          {/* Audit Trail */}
          {extractedData && (
            <div className="pt-4 border-t border-neutral-200">
              <AuditTrail extractedData={extractedData} correctionsCount={correctionsCount} />
            </div>
          )}

          {/* Submit Button */}
          <div className="pt-4 border-t border-neutral-200">
            <button
              type="button"
              onClick={handleSubmitClick}
              disabled={isDisabled}
              aria-label={
                correctionsCount > 0
                  ? `Submit with ${correctionsCount} ${correctionsCount === 1 ? 'correction' : 'corrections'}`
                  : 'Submit extraction'
              }
              className={`w-full px-4 py-3 rounded-lg font-semibold text-white transition-colors ${
                isDisabled
                  ? 'bg-neutral-300 cursor-not-allowed'
                  : 'bg-[#954293] hover:bg-[#7a3678] focus:outline-none focus:ring-2 focus:ring-[#954293] focus:ring-offset-2'
              }`}
            >
              {correctionsCount > 0 ? (
                <span>
                  Submit ({correctionsCount}{' '}
                  {correctionsCount === 1 ? 'correction' : 'corrections'})
                </span>
              ) : (
                <span>Submit</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Submit Modal */}
      {isModalOpen && (
        <SubmitModal
          corrections={corrections}
          originalValues={{
            gap_premium: String(extraction.gap_premium),
            refund_method: extraction.refund_method,
            cancellation_fee: String(extraction.cancellation_fee),
          }}
          onSubmit={handleModalSubmit}
          onCancel={handleModalCancel}
        />
      )}
    </>
  );
};
