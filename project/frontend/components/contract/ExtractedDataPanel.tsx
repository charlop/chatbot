'use client';

import { Contract } from '@/lib/api/contracts';
import { Button } from '@/components/ui/Button';

export interface ExtractedDataPanelProps {
  contract: Contract;
  onApprove?: () => void;
  onEdit?: () => void;
  onReject?: () => void;
  onJumpToField?: (page: number) => void;
}

interface ConfidenceBadgeProps {
  confidence?: number;
}

const ConfidenceBadge = ({ confidence }: ConfidenceBadgeProps) => {
  if (!confidence) {
    return (
      <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
        N/A
      </span>
    );
  }

  const level = confidence >= 95 ? 'high' : confidence >= 85 ? 'medium' : 'low';
  const colors = {
    high: 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-400',
    medium: 'bg-warning-100 dark:bg-warning-900/30 text-warning-700 dark:text-warning-400',
    low: 'bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400',
  };

  const labels = {
    high: 'High',
    medium: 'Med',
    low: 'Low',
  };

  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${colors[level]}`}>
      {labels[level]} {Math.round(confidence)}%
    </span>
  );
};

export const ExtractedDataPanel = ({
  contract,
  onApprove,
  onEdit,
  onReject,
  onJumpToField,
}: ExtractedDataPanelProps) => {
  // Calculate overall confidence
  const confidenceScores = [
    contract.extractedData?.gapPremiumConfidence,
    contract.extractedData?.refundMethodConfidence,
    contract.extractedData?.cancellationFeeConfidence,
  ].filter((score): score is number => score !== undefined && score !== null);

  const overallConfidence = confidenceScores.length > 0
    ? Math.round(confidenceScores.reduce((sum, score) => sum + score, 0) / confidenceScores.length)
    : 0;

  return (
    <div className="flex flex-col h-full bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Finance Review
        </h2>
        {overallConfidence > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-success-100 dark:bg-success-900/30 rounded-full">
            <div className="w-2 h-2 bg-success-600 dark:bg-success-400 rounded-full"></div>
            <span className="text-sm font-medium text-success-700 dark:text-success-400">
              Overall {overallConfidence}%
            </span>
          </div>
        )}
      </div>

      {/* Account Info Card */}
      <div className="grid grid-cols-2 gap-4 p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg mb-6">
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
            Account Number
          </p>
          <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            {contract.accountNumber}
          </p>
        </div>
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
            Contract Type
          </p>
          <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
            {contract.contract_type || 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
            Contract ID
          </p>
          <p className="text-xs font-mono text-neutral-900 dark:text-neutral-100">
            {contract.id}
          </p>
        </div>
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
            Customer
          </p>
          <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
            {contract.customer_name || 'N/A'}
          </p>
        </div>
      </div>

      {/* Extracted Fields */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-6">
        <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
          Extracted Fields
        </h3>

        {/* GAP Insurance Premium */}
        <div className="p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
          <div className="flex items-start justify-between mb-2">
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              GAP Insurance Premium
            </p>
            <ConfidenceBadge confidence={contract.extractedData?.gapPremiumConfidence} />
          </div>
          <p className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            {contract.extractedData?.gapPremium !== undefined && contract.extractedData?.gapPremium !== null
              ? `$${Number(contract.extractedData.gapPremium).toFixed(2)}`
              : 'Not extracted'}
          </p>
          {contract.extractedData?.gapPremiumSource && (
            <>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">
                {typeof contract.extractedData.gapPremiumSource === 'string'
                  ? contract.extractedData.gapPremiumSource
                  : JSON.stringify(contract.extractedData.gapPremiumSource)}
              </p>
              {onJumpToField && (
                <button
                  onClick={() => onJumpToField(1)}
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                >
                  View in document →
                </button>
              )}
            </>
          )}
        </div>

        {/* Refund Calculation Method */}
        <div className="p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
          <div className="flex items-start justify-between mb-2">
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              Refund Calculation Method
            </p>
            <ConfidenceBadge confidence={contract.extractedData?.refundMethodConfidence} />
          </div>
          <p className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            {contract.extractedData?.refundMethod || 'Not extracted'}
          </p>
          {contract.extractedData?.refundMethodSource && (
            <>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">
                {typeof contract.extractedData.refundMethodSource === 'string'
                  ? contract.extractedData.refundMethodSource
                  : JSON.stringify(contract.extractedData.refundMethodSource)}
              </p>
              {onJumpToField && (
                <button
                  onClick={() => onJumpToField(1)}
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                >
                  View in document →
                </button>
              )}
            </>
          )}
        </div>

        {/* Cancellation Fee */}
        <div className={`p-4 rounded-lg ${
          contract.extractedData?.cancellationFeeConfidence &&
          contract.extractedData.cancellationFeeConfidence < 90
            ? 'bg-warning-50 dark:bg-warning-900/10 border border-warning-200 dark:border-warning-800'
            : 'bg-neutral-50 dark:bg-neutral-900'
        }`}>
          <div className="flex items-start justify-between mb-2">
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              Cancellation Fee
            </p>
            <ConfidenceBadge confidence={contract.extractedData?.cancellationFeeConfidence} />
          </div>
          <p className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            {contract.extractedData?.cancellationFee !== undefined && contract.extractedData?.cancellationFee !== null
              ? `$${Number(contract.extractedData.cancellationFee).toFixed(2)}`
              : 'Not extracted'}
          </p>
          {contract.extractedData?.cancellationFeeSource && (
            <>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">
                {typeof contract.extractedData.cancellationFeeSource === 'string'
                  ? contract.extractedData.cancellationFeeSource
                  : JSON.stringify(contract.extractedData.cancellationFeeSource)}
              </p>
              {onJumpToField && (
                <button
                  onClick={() => onJumpToField(1)}
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                >
                  View in document →
                </button>
              )}
            </>
          )}
          {contract.extractedData?.cancellationFeeConfidence &&
           contract.extractedData.cancellationFeeConfidence < 90 && (
            <div className="mt-2 p-2 bg-warning-100 dark:bg-warning-900/20 rounded">
              <p className="text-xs text-warning-700 dark:text-warning-400">
                ⚠ Lower confidence - manual verification recommended
              </p>
            </div>
          )}
        </div>

        {/* Processing Audit */}
        {contract.audit_info && (
          <div className="p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
            <h4 className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
              Processing Audit
            </h4>
            <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
              Processed: {contract.audit_info.processed_at
                ? new Date(contract.audit_info.processed_at).toLocaleString()
                : 'N/A'}
            </p>
            {contract.audit_info.model_version && (
              <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Model: {contract.audit_info.model_version}
                {contract.audit_info.processing_time_ms &&
                  ` | Time: ${(contract.audit_info.processing_time_ms / 1000).toFixed(1)}s`}
              </p>
            )}
            {contract.audit_info.corrections_made !== undefined && (
              <p className="text-xs text-neutral-600 dark:text-neutral-400">
                Corrections: {contract.audit_info.corrections_made}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {onApprove && (
          <Button
            variant="success"
            onClick={onApprove}
            className="w-full"
            size="md"
          >
            Approve All
          </Button>
        )}
        {onEdit && (
          <Button
            onClick={onEdit}
            className="w-full bg-primary-600 hover:bg-primary-700"
            size="md"
          >
            Edit
          </Button>
        )}
        {onReject && (
          <Button
            variant="outline"
            onClick={onReject}
            className="w-full"
            size="md"
          >
            Reject
          </Button>
        )}
      </div>

      {/* AI Chat Input */}
      <div className="border border-neutral-200 dark:border-neutral-700 rounded-lg p-3">
        <input
          type="text"
          placeholder="Ask AI about this contract or search for another..."
          className="w-full bg-transparent text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 outline-none"
          disabled
        />
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-3 text-neutral-400 dark:text-neutral-500">
            <button className="hover:text-neutral-600 dark:hover:text-neutral-300" title="Attach file">
              📎
            </button>
            <button className="hover:text-neutral-600 dark:hover:text-neutral-300" title="Search">
              🔍
            </button>
          </div>
          <button
            className="w-8 h-8 bg-primary-600 hover:bg-primary-700 rounded-full flex items-center justify-center text-white transition-colors"
            disabled
            title="Send message"
          >
            →
          </button>
        </div>
      </div>

      {/* Status Footer */}
      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-3 text-center">
        Status: Ready for review • Updated {new Date(contract.updated_at || '').toLocaleDateString()}
      </p>
    </div>
  );
};
