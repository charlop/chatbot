'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { PDFViewer } from '@/components/pdf/PDFViewer';
import { ExtractedDataPanel } from '@/components/contract/ExtractedDataPanel';
import { getContract, Contract } from '@/lib/api/contracts';
import { ApiError } from '@/lib/api/client';
import { Button } from '@/components/ui/Button';

export default function ContractDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const contractId = params.contractId as string;

  const [contract, setContract] = useState<Contract | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContract = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getContract(contractId);
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

  const handleApprove = () => {
    // TODO: Implement approval logic
    console.log('Approve contract:', contractId);
  };

  const handleEdit = () => {
    // TODO: Implement edit functionality
    console.log('Edit contract:', contractId);
  };

  const handleReject = () => {
    // TODO: Implement rejection logic
    console.log('Reject contract:', contractId);
  };

  const handleJumpToField = (page: number) => {
    // TODO: Implement page jumping
    console.log('Jump to page:', page);
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

  return (
    <Layout
      title={`Contract ${contract.accountNumber}`}
    >
      {/* Back Button */}
      <div className="mb-4">
        <button
          onClick={handleBackToDashboard}
          className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
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
          <ExtractedDataPanel
            contract={contract}
            onApprove={handleApprove}
            onEdit={handleEdit}
            onReject={handleReject}
            onJumpToField={handleJumpToField}
          />
        </div>
      </div>
    </Layout>
  );
}
