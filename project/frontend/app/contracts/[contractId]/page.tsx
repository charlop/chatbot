'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { PDFViewer } from '@/components/pdf/PDFViewer';
import { DataPanel } from '@/components/extraction/DataPanel';
import { getContract, Contract } from '@/lib/api/contracts';
import {
  submitExtraction,
  createExtraction,
  FieldCorrection,
  Extraction,
} from '@/lib/api/extractions';
import { ApiError } from '@/lib/api/client';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';

export default function ContractDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const contractId = params.contractId as string;
  const { success, error: showError } = useToast();

  const [contract, setContract] = useState<Contract | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContract = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getContract(contractId);
        console.log('Contract data received:', data);
        console.log('Extracted data:', data.extracted_data);
        setContract(data);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.message || 'Failed to load contract');
        console.error('Error loading contract:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (contractId) {
      fetchContract();
    }
  }, [contractId]);

  const handleTriggerExtraction = async () => {
    try {
      setIsExtracting(true);
      // Trigger extraction
      await createExtraction(contractId);

      success('Extraction started successfully');

      // Refresh contract data to get the extraction results
      const updatedContract = await getContract(contractId);
      setContract(updatedContract);
    } catch (err) {
      const apiError = err as ApiError;
      showError(apiError.message || 'Failed to trigger extraction');
      console.error('Error triggering extraction:', err);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSubmit = async (corrections: FieldCorrection[], notes?: string) => {
    if (!contract?.extracted_data) {
      showError('No extraction data available');
      return;
    }

    try {
      // Submit extraction with corrections
      await submitExtraction(contractId, { corrections, notes });

      success(
        corrections.length > 0
          ? `Submitted with ${corrections.length} correction${corrections.length === 1 ? '' : 's'}`
          : 'Extraction approved successfully'
      );

      // Refresh contract data
      const updatedContract = await getContract(contractId);
      setContract(updatedContract);
    } catch (err) {
      const apiError = err as ApiError;
      showError(apiError.message || 'Failed to submit extraction');
      console.error('Error submitting extraction:', err);
    }
  };

  const handleJumpToField = (source: string) => {
    // TODO: Implement page jumping based on source location
    console.log('Jump to field:', source);
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  if (isLoading) {
    return (
      <Layout title="Loading Contract">
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-neutral-600 dark:text-neutral-400">Loading contract details...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !contract) {
    return (
      <Layout title="Error">
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-danger-100 dark:bg-danger-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-danger-600 dark:text-danger-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
              Failed to Load Contract
            </h2>
            <p className="text-neutral-600 dark:text-neutral-400 mb-6">
              {error || 'Contract not found'}
            </p>
            <Button onClick={handleBackToDashboard}>
              Back to Dashboard
            </Button>
          </div>
        </div>
      </Layout>
    );
  }

  // Transform contract data to Extraction format for DataPanel
  const extraction: Extraction | null = contract?.extracted_data
    ? {
        id: contract.id || contractId,
        contractId: contract.contractId,
        gap_premium: contract.extracted_data.gap_premium || 0,
        gap_premium_confidence: contract.extracted_data.gap_premium_confidence,
        gap_premium_source: contract.extracted_data.gap_premium_source,
        refund_method: contract.extracted_data.refund_method || '',
        refund_method_confidence: contract.extracted_data.refund_method_confidence,
        refund_method_source: contract.extracted_data.refund_method_source,
        cancellation_fee: contract.extracted_data.cancellation_fee || 0,
        cancellation_fee_confidence: contract.extracted_data.cancellation_fee_confidence,
        cancellation_fee_source: contract.extracted_data.cancellation_fee_source,
        status: (contract.status as 'pending' | 'approved') || 'pending',
      }
    : null;

  return (
    <Layout title={`Contract ${contract.accountNumber}`}>
      {/* Back Button */}
      <div className="mb-4">
        <button
          onClick={handleBackToDashboard}
          className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Dashboard
        </button>
      </div>

      {/* Main Content - Two Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-250px)]">
        {/* Left Panel - PDF Viewer (2/3 width on large screens) */}
        <div className="lg:col-span-2 h-full">
          <PDFViewer
            contractId={contract.contractId}
            fileName={`${contract.accountNumber}.pdf`}
          />
        </div>

        {/* Right Panel - Extracted Data (1/3 width on large screens) */}
        <div className="lg:col-span-1 h-full overflow-hidden">
          {extraction ? (
            <DataPanel
              extraction={extraction}
              onSubmit={handleSubmit}
              onViewInDocument={handleJumpToField}
            />
          ) : (
            <div className="flex flex-col h-full bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
              {/* Contract Details */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
                  Contract Details
                </h3>

                {/* Customer Information */}
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                    Customer Information
                  </h4>
                  <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-lg p-3 space-y-1">
                    <div className="text-sm">
                      <span className="text-neutral-500 dark:text-neutral-400">Name:</span>{' '}
                      <span className="text-neutral-900 dark:text-neutral-100 font-medium">
                        {contract.customerName}
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-neutral-500 dark:text-neutral-400">Account:</span>{' '}
                      <span className="text-neutral-900 dark:text-neutral-100 font-mono">
                        {contract.accountNumber}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Vehicle Information */}
                {contract.vehicleInfo && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                      Vehicle Information
                    </h4>
                    <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-lg p-3 space-y-1">
                      <div className="text-sm">
                        <span className="text-neutral-500 dark:text-neutral-400">Make/Model:</span>{' '}
                        <span className="text-neutral-900 dark:text-neutral-100 font-medium">
                          {contract.vehicleInfo.year} {contract.vehicleInfo.make} {contract.vehicleInfo.model}
                        </span>
                      </div>
                      <div className="text-sm">
                        <span className="text-neutral-500 dark:text-neutral-400">VIN:</span>{' '}
                        <span className="text-neutral-900 dark:text-neutral-100 font-mono">
                          {contract.vehicleInfo.vin}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Contract Metadata */}
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                    Contract Metadata
                  </h4>
                  <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-lg p-3 space-y-1">
                    <div className="text-sm">
                      <span className="text-neutral-500 dark:text-neutral-400">Contract ID:</span>{' '}
                      <span className="text-neutral-900 dark:text-neutral-100 font-mono">
                        {contract.contractId}
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-neutral-500 dark:text-neutral-400">Type:</span>{' '}
                      <span className="text-neutral-900 dark:text-neutral-100">
                        {contract.contractType}
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-neutral-500 dark:text-neutral-400">Date:</span>{' '}
                      <span className="text-neutral-900 dark:text-neutral-100">
                        {contract.contractDate
                          ? new Date(contract.contractDate).toLocaleDateString()
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Extraction CTA */}
              <div className="border-t border-neutral-200 dark:border-neutral-700 p-6 bg-neutral-50 dark:bg-neutral-900/30">
                <div className="text-center">
                  <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg
                      className="w-6 h-6 text-primary-600 dark:text-primary-400"
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
                  <h4 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                    Extract Data
                  </h4>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-3">
                    Extract GAP premium, refund method, and cancellation fee from this contract.
                  </p>
                  <Button
                    onClick={handleTriggerExtraction}
                    loading={isExtracting}
                    disabled={isExtracting}
                    className="w-full"
                  >
                    {isExtracting ? 'Extracting...' : 'Start Extraction'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
