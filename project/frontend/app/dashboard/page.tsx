'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { SearchBar } from '@/components/search/SearchBar';
import { RecentSearches } from '@/components/search/RecentSearches';
import { SearchResults } from '@/components/search/SearchResults';
import { SearchContractResponse } from '@/lib/api/contracts';

export default function Dashboard() {
  const router = useRouter();
  const [searchValue, setSearchValue] = useState('');
  const [refreshRecentSearches, setRefreshRecentSearches] = useState(0);
  const [searchResult, setSearchResult] = useState<SearchContractResponse | null>(null);

  const handleSearchSuccess = (result: SearchContractResponse) => {
    // Store the search result to display
    setSearchResult(result);

    // Refresh recent searches to show the new search
    setRefreshRecentSearches((prev) => prev + 1);
  };

  const handleNewSearch = () => {
    // Clear the search result and reset the search value
    setSearchResult(null);
    setSearchValue('');
  };

  const handleViewDetails = (contractId: string) => {
    // Navigate to contract details page
    router.push(`/contracts/${contractId}`);
  };

  const handleRecentSearchSelect = (accountNumber: string) => {
    // Pre-populate search bar with selected account number
    setSearchValue(accountNumber);
    // Optionally trigger search automatically
    // For now, just populate the field so user can review and click Search
  };

  const handleRecentSearchesClear = () => {
    setRefreshRecentSearches((prev) => prev + 1);
  };

  return (
    <Layout title="Dashboard">
      <div className="max-w-7xl mx-auto">
        {/* Dashboard Content */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
            Welcome to the Contract Refund Eligibility System
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Search for a contract to begin the refund eligibility review process.
          </p>
        </div>

        {/* Search Section */}
        <div className="mb-8 max-w-2xl">
          {!searchResult ? (
            <>
              <SearchBar
                value={searchValue}
                onChange={setSearchValue}
                onSuccess={handleSearchSuccess}
                placeholder="Enter account number (e.g., ACC-TEST-00001)"
                autoFocus
              />
              <RecentSearches
                key={refreshRecentSearches}
                onSelect={handleRecentSearchSelect}
                onClear={handleRecentSearchesClear}
              />
            </>
          ) : (
            <SearchResults
              result={searchResult}
              onNewSearch={handleNewSearch}
              onViewDetails={() => handleViewDetails(searchResult.contractId)}
            />
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Processed Contracts */}
          <div className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
                  Contracts Processed
                </p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mt-2">
                  0
                </p>
              </div>
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
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
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
              Last 30 days
            </p>
          </div>

          {/* Average Confidence */}
          <div className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
                  Avg Confidence
                </p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mt-2">
                  --
                </p>
              </div>
              <div className="w-12 h-12 bg-success-100 dark:bg-success-900/30 rounded-lg flex items-center justify-center">
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
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
              AI extraction accuracy
            </p>
          </div>

          {/* Pending Reviews */}
          <div className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
                  Pending Reviews
                </p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mt-2">
                  0
                </p>
              </div>
              <div className="w-12 h-12 bg-warning-100 dark:bg-warning-900/30 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-warning-600 dark:text-warning-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
              Awaiting approval
            </p>
          </div>
        </div>

        {/* Getting Started */}
        <div className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-8 transition-colors">
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Getting Started
          </h3>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center text-primary-600 dark:text-primary-400 font-semibold">
                1
              </div>
              <div>
                <h4 className="font-medium text-neutral-900 dark:text-neutral-100">
                  Search for a Contract
                </h4>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                  Use the search functionality to find a contract by account number
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center text-primary-600 dark:text-primary-400 font-semibold">
                2
              </div>
              <div>
                <h4 className="font-medium text-neutral-900 dark:text-neutral-100">
                  Review AI Extraction
                </h4>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                  View the extracted data alongside the PDF with confidence scores
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center text-primary-600 dark:text-primary-400 font-semibold">
                3
              </div>
              <div>
                <h4 className="font-medium text-neutral-900 dark:text-neutral-100">
                  Approve or Correct
                </h4>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                  Approve accurate extractions or make corrections before finalizing
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
