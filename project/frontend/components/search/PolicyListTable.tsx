'use client';

import { PolicySummary } from '@/lib/api/contracts';
import { Button } from '@/components/ui/Button';

export interface PolicyListTableProps {
  accountNumber: string;
  state?: string;
  policies: PolicySummary[];
  onPolicySelect?: (contractId: string, policyId: string) => void;
  onNewSearch?: () => void;
}

/**
 * Display all policies for an account in a table format
 */
export const PolicyListTable = ({
  accountNumber,
  state,
  policies,
  onPolicySelect,
  onNewSearch,
}: PolicyListTableProps) => {
  const getContractTypeColor = (contractType: string) => {
    const lowerType = contractType.toLowerCase();
    if (lowerType.includes('gap')) {
      return 'text-primary-600 bg-primary-100 dark:text-primary-400 dark:bg-primary-900/30';
    }
    if (lowerType.includes('warranty') || lowerType.includes('vsc')) {
      return 'text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/30';
    }
    if (lowerType.includes('tire')) {
      return 'text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/30';
    }
    return 'text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800';
  };

  const getStatusColor = (isActive?: boolean) => {
    return isActive !== false
      ? 'text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/30'
      : 'text-neutral-500 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800';
  };

  return (
    <div className="w-full bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 transition-colors">
      {/* Header */}
      <div className="p-6 border-b border-neutral-200 dark:border-neutral-700">
        <div className="flex items-start gap-4">
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {policies.length} {policies.length === 1 ? 'Policy' : 'Policies'} Found
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
              Account <span className="font-mono">{accountNumber}</span>
              {state && (
                <>
                  {' '}
                  •{' '}
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900/30 dark:text-primary-300">
                    {state}
                  </span>
                </>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-neutral-50 dark:bg-neutral-900/50 border-b border-neutral-200 dark:border-neutral-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Policy ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Policy Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Template ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Version
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
            {policies.map((policy) => (
              <tr
                key={policy.policyId}
                className="hover:bg-neutral-50 dark:hover:bg-neutral-900/30 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-mono font-medium text-neutral-900 dark:text-neutral-100">
                    {policy.policyId}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getContractTypeColor(
                      policy.contractType
                    )}`}
                  >
                    {policy.contractType}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-mono text-neutral-600 dark:text-neutral-400">
                    {policy.contractId}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {policy.templateVersion || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      policy.isActive
                    )}`}
                  >
                    {policy.isActive !== false ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  {onPolicySelect && (
                    <button
                      onClick={() => onPolicySelect(policy.contractId, policy.policyId)}
                      className="inline-flex items-center px-3 py-1.5 border border-primary-600 dark:border-primary-400 rounded-md text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 font-medium transition-colors"
                    >
                      View Details
                      <svg
                        className="ml-1.5 w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {policies.length === 0 && (
        <div className="p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-neutral-400 dark:text-neutral-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-neutral-900 dark:text-neutral-100">
            No policies found
          </h3>
          <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
            No policies are associated with this account.
          </p>
        </div>
      )}

      {/* Footer Actions */}
      {policies.length > 0 && onNewSearch && (
        <div className="p-6 border-t border-neutral-200 dark:border-neutral-700">
          <Button onClick={onNewSearch} variant="outline" className="w-full">
            New Search
          </Button>
        </div>
      )}

      {/* Info Note */}
      {policies.length > 0 && (
        <div className="p-6 border-t border-neutral-200 dark:border-neutral-700">
          <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-md">
            <p className="text-xs text-primary-700 dark:text-primary-300">
              <strong>Note:</strong> Click "View Details" on any policy to see the full contract
              template including AI-extracted data.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
