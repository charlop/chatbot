import React from 'react';
import { ExtractedData } from '@/lib/api/contracts';

export interface AuditTrailProps {
  extractedData: ExtractedData;
  correctionsCount?: number;
}

/**
 * AuditTrail component displays extraction audit information
 * including model version, processing time, and approval status
 */
export const AuditTrail: React.FC<AuditTrailProps> = ({
  extractedData,
  correctionsCount = 0,
}) => {
  // Format timestamp to readable format
  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return 'N/A';

    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return 'Invalid date';
    }
  };

  // Format processing time
  const formatProcessingTime = (ms?: number): string => {
    if (!ms) return 'N/A';

    if (ms < 1000) {
      return `${ms}ms`;
    } else if (ms < 60000) {
      return `${(ms / 1000).toFixed(2)}s`;
    } else {
      const minutes = Math.floor(ms / 60000);
      const seconds = ((ms % 60000) / 1000).toFixed(0);
      return `${minutes}m ${seconds}s`;
    }
  };

  const {
    llmModelVersion,
    llmProvider,
    processingTimeMs,
    extractedAt,
    approvedAt,
    status,
  } = extractedData;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
        Audit Information
      </h4>

      <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-lg p-4 space-y-3">
        {/* Model Information */}
        <div className="space-y-1">
          <div className="text-xs text-neutral-500 dark:text-neutral-400">Model</div>
          <div className="text-sm text-neutral-900 dark:text-neutral-100 font-mono">
            {llmModelVersion || 'N/A'}
          </div>
          {llmProvider && (
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              Provider: {llmProvider}
            </div>
          )}
        </div>

        {/* Processing Time */}
        {processingTimeMs !== undefined && processingTimeMs !== null && (
          <div className="space-y-1">
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              Processing Time
            </div>
            <div className="text-sm text-neutral-900 dark:text-neutral-100">
              {formatProcessingTime(processingTimeMs)}
            </div>
          </div>
        )}

        {/* Extracted At */}
        {extractedAt && (
          <div className="space-y-1">
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              Extracted At
            </div>
            <div className="text-sm text-neutral-900 dark:text-neutral-100">
              {formatTimestamp(extractedAt)}
            </div>
          </div>
        )}

        {/* Approved At */}
        {status === 'approved' && approvedAt && (
          <div className="space-y-1">
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              Approved At
            </div>
            <div className="text-sm text-neutral-900 dark:text-neutral-100">
              {formatTimestamp(approvedAt)}
            </div>
          </div>
        )}

        {/* Corrections Made */}
        {correctionsCount > 0 && (
          <div className="space-y-1">
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              Corrections Made
            </div>
            <div className="text-sm text-neutral-900 dark:text-neutral-100">
              {correctionsCount} field{correctionsCount === 1 ? '' : 's'}
            </div>
          </div>
        )}

        {/* Status Badge */}
        <div className="pt-2 border-t border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center gap-2">
            <div className="text-xs text-neutral-500 dark:text-neutral-400">Status:</div>
            <span
              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                status === 'approved'
                  ? 'bg-[#2da062]/10 text-[#2da062] dark:bg-[#2da062]/20'
                  : 'bg-neutral-200 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-300'
              }`}
            >
              {status === 'approved' ? '✓ Approved' : 'Pending'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
