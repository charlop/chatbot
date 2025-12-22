import React from 'react';
import StateIndicator from './StateIndicator';

interface ContractMetadataProps {
  /**
   * Contract ID
   */
  contractId: string;

  /**
   * Account number (optional)
   */
  accountNumber?: string;

  /**
   * Primary state
   */
  state?: string;

  /**
   * Additional applicable states
   */
  applicableStates?: string[];

  /**
   * Contract type (e.g., "GAP Insurance")
   */
  contractType?: string;

  /**
   * Template version
   */
  templateVersion?: string;
}

/**
 * ContractMetadata component displays contract metadata in a grid layout.
 *
 * Design:
 * - 2-column grid on larger screens
 * - Light neutral background
 * - Clear labels and values
 * - State prominently displayed with StateIndicator
 */
export const ContractMetadata: React.FC<ContractMetadataProps> = ({
  contractId,
  accountNumber,
  state,
  applicableStates,
  contractType,
  templateVersion,
}) => {
  return (
    <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-4 mb-6">
      <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">
        Contract Details
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Account Number */}
        {accountNumber && (
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
              Account Number
            </p>
            <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 font-mono">
              {accountNumber}
            </p>
          </div>
        )}

        {/* Contract ID */}
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
            Contract ID
          </p>
          <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 font-mono">
            {contractId}
          </p>
        </div>

        {/* State */}
        {state && (
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
              State
            </p>
            <StateIndicator
              state={state}
              applicableStates={applicableStates?.filter((s) => s !== state)}
            />
          </div>
        )}

        {/* Contract Type */}
        {contractType && (
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
              Contract Type
            </p>
            <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
              {contractType}
            </p>
          </div>
        )}

        {/* Template Version */}
        {templateVersion && (
          <div className="md:col-span-2">
            <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase mb-1">
              Template Version
            </p>
            <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
              {templateVersion}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContractMetadata;
