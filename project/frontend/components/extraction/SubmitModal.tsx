import React, { useState, useEffect, useRef } from 'react';

export interface SubmitModalProps {
  /**
   * Map of field corrections (fieldKey -> newValue)
   */
  corrections: Map<string, string>;

  /**
   * Original values for all fields
   */
  originalValues: {
    gap_premium: string;
    refund_method: string;
    cancellation_fee: string;
  };

  /**
   * Callback when submit is confirmed
   */
  onSubmit: (notes?: string) => void;

  /**
   * Callback when modal is canceled
   */
  onCancel: () => void;
}

// Field labels for display
const FIELD_LABELS: Record<string, string> = {
  gap_premium: 'GAP Insurance Premium',
  refund_method: 'Refund Calculation Method',
  cancellation_fee: 'Cancellation Fee',
};

/**
 * Modal for confirming extraction submission with optional corrections summary
 */
export const SubmitModal: React.FC<SubmitModalProps> = ({
  corrections,
  originalValues,
  onSubmit,
  onCancel,
}) => {
  const [notes, setNotes] = useState('');
  const notesRef = useRef<HTMLTextAreaElement>(null);
  const titleId = `submit-modal-title-${Math.random().toString(36).substr(2, 9)}`;

  // Focus notes field on mount
  useEffect(() => {
    if (notesRef.current) {
      notesRef.current.focus();
    }
  }, []);

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onCancel]);

  const handleSubmit = () => {
    const trimmedNotes = notes.trim();
    onSubmit(trimmedNotes || undefined);
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  const correctionsArray = Array.from(corrections.entries());

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={handleBackdropClick}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-neutral-200">
          <h2 id={titleId} className="text-xl font-bold text-neutral-900">
            Confirm Submission
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto">
          {/* Corrections Summary */}
          {correctionsArray.length > 0 ? (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-neutral-900 mb-3">
                Changes ({correctionsArray.length})
              </h3>
              <div className="space-y-3">
                {correctionsArray.map(([fieldKey, newValue]) => {
                  const originalValue =
                    originalValues[fieldKey as keyof typeof originalValues];
                  return (
                    <div
                      key={fieldKey}
                      className="p-3 bg-neutral-50 rounded-lg border border-neutral-200"
                    >
                      <div className="text-xs font-semibold text-neutral-600 mb-1">
                        {FIELD_LABELS[fieldKey]}
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="line-through text-neutral-500">{originalValue}</span>
                        <span className="text-neutral-400">→</span>
                        <span className="font-medium text-primary">{newValue}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="mb-4 p-3 bg-neutral-50 rounded-lg">
              <p className="text-sm text-neutral-600">
                No changes made. Submitting will approve the extraction as-is.
              </p>
            </div>
          )}

          {/* Notes Field */}
          <div>
            <label htmlFor="notes" className="block text-sm font-semibold text-neutral-900 mb-2">
              Notes (optional)
            </label>
            <textarea
              id="notes"
              ref={notesRef}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this submission..."
              maxLength={500}
              rows={4}
              aria-label="Notes (optional)"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary resize-none"
            />
            <div className="mt-1 text-xs text-neutral-500 text-right">
              {notes.length}/500 characters
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-neutral-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-neutral-700 bg-neutral-100 rounded-lg hover:bg-neutral-200 transition-colors focus:outline-none focus:ring-2 focus:ring-neutral-400"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
};
