'use client';

import {
  SearchContractResponse,
  isMultiPolicyResponse,
  isSingleContractResponse,
} from '@/lib/api/contracts';
import { Button } from '@/components/ui/Button';
import { PolicyListTable } from './PolicyListTable';

export interface SearchResultsProps {
  result: SearchContractResponse;
  onViewDetails?: (contractId?: string, policyId?: string) => void;
  onNewSearch?: () => void;
}

/**
 * Display search results after finding a contract or multiple policies
 */
export const SearchResults = ({
  result,
  onViewDetails,
  onNewSearch,
}: SearchResultsProps) => {
  // Type discrimination: render different UI based on response type
  if (isMultiPolicyResponse(result)) {
    // Multi-policy response: show table of all policies
    return (
      <PolicyListTable
        accountNumber={result.accountNumber}
        state={result.state}
        policies={result.policies}
        onPolicySelect={(contractId, policyId) => {
          onViewDetails?.(contractId, policyId);
        }}
        onNewSearch={onNewSearch}
      />
    );
  }

  // Single contract response: show contract card
  if (!isSingleContractResponse(result)) {
    // This should never happen due to union type, but add defensive check
    return (
      <div className="w-full bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6">
        <p className="text-neutral-600 dark:text-neutral-400">Invalid response format</p>
      </div>
    );
  }

  const getContractTypeColor = (contractType: string) => {
    const lowerType = contractType.toLowerCase();
    if (lowerType.includes('gap')) {
      return 'text-primary-600 bg-primary-100 dark:text-primary-400 dark:bg-primary-900/30';
    }
    if (lowerType.includes('warranty')) {
      return 'text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/30';
    }
    return 'text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800';
  };

  return (
    <div className="w-full bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6 transition-colors">
      {/* Success Header */}
      <div className="flex items-start gap-4 mb-6">
        <div className="flex-shrink-0 w-12 h-12 bg-success-100 dark:bg-success-900/30 rounded-full flex items-center justify-center">
          <svg
            className="w-6 h-6 text-success-600 dark:text-success-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            Contract Template Found
          </h3>
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
            We found a contract template matching your search criteria.
          </p>
        </div>
      </div>

      {/* Contract Template Details */}
      <div className="space-y-4 mb-6">
        <div className="flex items-center justify-between py-3 border-b border-neutral-200 dark:border-neutral-700">
          <span className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
            Template ID
          </span>
          <span className="text-sm font-mono text-neutral-900 dark:text-neutral-100">
            {result.contractId}
          </span>
        </div>

        <div className="flex items-center justify-between py-3 border-b border-neutral-200 dark:border-neutral-700">
          <span className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
            Contract Type
          </span>
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full ${getContractTypeColor(
              result.contractType
            )}`}
          >
            {result.contractType}
          </span>
        </div>

        {result.templateVersion && (
          <div className="flex items-center justify-between py-3 border-b border-neutral-200 dark:border-neutral-700">
            <span className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
              Template Version
            </span>
            <span className="text-sm text-neutral-900 dark:text-neutral-100">
              {result.templateVersion}
            </span>
          </div>
        )}

        {result.effectiveDate && (
          <div className="flex items-center justify-between py-3 border-b border-neutral-200 dark:border-neutral-700">
            <span className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
              Effective Date
            </span>
            <span className="text-sm text-neutral-900 dark:text-neutral-100">
              {new Date(result.effectiveDate).toLocaleDateString()}
            </span>
          </div>
        )}

        {result.contractDate && (
          <div className="flex items-center justify-between py-3 border-b border-neutral-200 dark:border-neutral-700">
            <span className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
              Created Date
            </span>
            <span className="text-sm text-neutral-900 dark:text-neutral-100">
              {new Date(result.contractDate).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {onViewDetails && (
          <Button onClick={() => onViewDetails(result.contractId)} className="flex-1">
            View Full Details
          </Button>
        )}
        {onNewSearch && (
          <Button onClick={onNewSearch} variant="outline" className="flex-1">
            New Search
          </Button>
        )}
      </div>

      {/* Info Note */}
      <div className="mt-4 p-3 bg-primary-50 dark:bg-primary-900/20 rounded-md">
        <p className="text-xs text-primary-700 dark:text-primary-300">
          <strong>Note:</strong> Full contract template details including AI-extracted data are
          available in the contract details view.
        </p>
      </div>
    </div>
  );
};
