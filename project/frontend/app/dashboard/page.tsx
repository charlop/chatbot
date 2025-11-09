'use client';

import { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';

// Mock data
const mockContract = {
  id: '1',
  accountNumber: '1234-5678-9012',
  customerName: 'John Smith',
  vehicleYear: 2020,
  vehicleMake: 'Toyota',
  vehicleModel: 'Camry',
  contractDate: '2023-01-15',
  extractedData: {
    accountNumber: {
      value: '1234-5678-9012',
      confidence: 98,
      location: { page: 1, section: 'header' }
    },
    vehicleInfo: {
      value: '2020 Toyota Camry',
      confidence: 95,
      location: { page: 1, section: 'vehicle-details' }
    },
    contractDate: {
      value: '2023-01-15',
      confidence: 92,
      location: { page: 1, section: 'contract-info' }
    }
  },
  processedBy: 'AI Model v2.1',
  processedAt: '2024-11-08T10:30:00Z',
  status: 'pending_review'
};

export default function Dashboard() {
  const [selectedContract] = useState(mockContract);
  const { theme, toggleTheme } = useTheme();

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-success-600 bg-success-50 border-success-200 dark:text-success-400 dark:bg-success-900/20 dark:border-success-700';
    if (confidence >= 70) return 'text-warning-600 bg-warning-50 border-warning-200 dark:text-warning-400 dark:bg-warning-900/20 dark:border-warning-700';
    return 'text-danger-600 bg-danger-50 border-danger-200 dark:text-danger-400 dark:bg-danger-900/20 dark:border-danger-700';
  };

  return (
    <div className="flex h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Sidebar - 64px */}
      <aside className="w-16 bg-neutral-900 flex flex-col items-center py-4 space-y-6">
        <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>

        <button className="w-10 h-10 flex items-center justify-center text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        </button>

        <button className="w-10 h-10 flex items-center justify-center text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>

        <div className="flex-1" />

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-10 h-10 flex items-center justify-center text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        <button className="w-10 h-10 flex items-center justify-center text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors">
          <div className="w-8 h-8 bg-primary-400 rounded-full flex items-center justify-center text-white text-sm font-medium">
            JS
          </div>
        </button>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 flex items-center px-6 transition-colors">
          <div className="flex-1">
            <div className="max-w-md">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by account number..."
                  className="w-full pl-10 pr-4 py-2 border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  defaultValue={selectedContract.accountNumber}
                />
                <svg className="w-5 h-5 text-neutral-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>
        </header>

        {/* Content: PDF Viewer + Data Panel */}
        <div className="flex-1 flex overflow-hidden">
          {/* PDF Viewer - 840px */}
          <div className="w-[840px] bg-neutral-100 dark:bg-neutral-800 border-r border-neutral-200 dark:border-neutral-700 overflow-auto transition-colors">
            <div className="p-6">
              {/* PDF Controls */}
              <div className="bg-white dark:bg-neutral-900 rounded-lg shadow-sm p-4 mb-4 flex items-center justify-between transition-colors">
                <div className="flex items-center gap-4">
                  <button className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">Page 1 of 1</span>
                  <button className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button className="px-3 py-1 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded transition-colors text-sm">50%</button>
                  <button className="px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded transition-colors text-sm font-medium">100%</button>
                  <button className="px-3 py-1 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded transition-colors text-sm">150%</button>
                  <button className="px-3 py-1 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded transition-colors text-sm">200%</button>
                </div>
                <button className="px-4 py-2 border border-neutral-300 dark:border-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg transition-colors text-sm flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download PDF
                </button>
              </div>

              {/* Mock PDF Content */}
              <div className="bg-white dark:bg-neutral-900 rounded-lg shadow-lg p-8 min-h-[1000px] transition-colors">
                <div className="border-b-2 border-neutral-200 dark:border-neutral-700 pb-4 mb-6">
                  <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">Vehicle Service Contract</h1>
                  <p className="text-neutral-600 dark:text-neutral-400 mt-1">Contract #: {selectedContract.accountNumber}</p>
                </div>

                <div className="space-y-6">
                  <div className="relative">
                    <div className="absolute -left-2 -top-2 -right-2 -bottom-2 bg-success-100 dark:bg-success-900/20 border-2 border-success-500 dark:border-success-600 rounded opacity-30 pointer-events-none" />
                    <div className="bg-neutral-50 dark:bg-neutral-800 p-4 rounded">
                      <h2 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Account Information</h2>
                      <p className="text-neutral-700 dark:text-neutral-300">Account Number: <span className="font-mono">{selectedContract.accountNumber}</span></p>
                      <p className="text-neutral-700 dark:text-neutral-300">Customer: {selectedContract.customerName}</p>
                    </div>
                  </div>

                  <div className="relative">
                    <div className="absolute -left-2 -top-2 -right-2 -bottom-2 bg-success-100 dark:bg-success-900/20 border-2 border-success-500 dark:border-success-600 rounded opacity-30 pointer-events-none" />
                    <div className="bg-neutral-50 dark:bg-neutral-800 p-4 rounded">
                      <h2 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Vehicle Details</h2>
                      <p className="text-neutral-700 dark:text-neutral-300">Year: {selectedContract.vehicleYear}</p>
                      <p className="text-neutral-700 dark:text-neutral-300">Make: {selectedContract.vehicleMake}</p>
                      <p className="text-neutral-700 dark:text-neutral-300">Model: {selectedContract.vehicleModel}</p>
                    </div>
                  </div>

                  <div className="relative">
                    <div className="absolute -left-2 -top-2 -right-2 -bottom-2 bg-warning-100 dark:bg-warning-900/20 border-2 border-warning-500 dark:border-warning-600 rounded opacity-30 pointer-events-none" />
                    <div className="bg-neutral-50 dark:bg-neutral-800 p-4 rounded">
                      <h2 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Contract Information</h2>
                      <p className="text-neutral-700 dark:text-neutral-300">Contract Date: {selectedContract.contractDate}</p>
                      <p className="text-neutral-700 dark:text-neutral-300">Status: Active</p>
                      <p className="text-neutral-700 dark:text-neutral-300">Term: 36 months / 36,000 miles</p>
                    </div>
                  </div>

                  <div className="bg-neutral-50 dark:bg-neutral-800 p-4 rounded">
                    <h2 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Coverage Details</h2>
                    <ul className="list-disc list-inside text-neutral-700 dark:text-neutral-300 space-y-1">
                      <li>Engine components</li>
                      <li>Transmission</li>
                      <li>Drive axle</li>
                      <li>Electrical system</li>
                      <li>Air conditioning</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Data Panel - 464px */}
          <div className="w-[464px] bg-white dark:bg-neutral-800 flex flex-col transition-colors">
            <div className="flex-1 overflow-auto p-6 space-y-4">
              <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">Extracted Data</h2>

              {/* Account Number Card */}
              <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 space-y-3 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Account Number</p>
                    <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mt-1 font-mono">
                      {selectedContract.extractedData.accountNumber.value}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getConfidenceColor(selectedContract.extractedData.accountNumber.confidence)}`}>
                    {selectedContract.extractedData.accountNumber.confidence}% confident
                  </span>
                </div>
                <button className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View in document
                </button>
              </div>

              {/* Vehicle Info Card */}
              <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 space-y-3 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Vehicle Information</p>
                    <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mt-1">
                      {selectedContract.extractedData.vehicleInfo.value}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getConfidenceColor(selectedContract.extractedData.vehicleInfo.confidence)}`}>
                    {selectedContract.extractedData.vehicleInfo.confidence}% confident
                  </span>
                </div>
                <button className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View in document
                </button>
              </div>

              {/* Contract Date Card */}
              <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 space-y-3 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Contract Date</p>
                    <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mt-1">
                      {selectedContract.extractedData.contractDate.value}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getConfidenceColor(selectedContract.extractedData.contractDate.confidence)}`}>
                    {selectedContract.extractedData.contractDate.confidence}% confident
                  </span>
                </div>
                <button className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View in document
                </button>
              </div>

              {/* Audit Info */}
              <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-lg p-4 space-y-2 transition-colors">
                <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Processing Information</h3>
                <div className="text-xs text-neutral-600 dark:text-neutral-400 space-y-1">
                  <p>Processed by: {selectedContract.processedBy}</p>
                  <p>Processed at: {new Date(selectedContract.processedAt).toLocaleString()}</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="border-t border-neutral-200 dark:border-neutral-700 p-6 space-y-3 transition-colors">
              <button className="w-full px-6 py-3 bg-success-500 text-white rounded-lg hover:bg-success-600 dark:bg-success-600 dark:hover:bg-success-700 transition-colors font-medium">
                Approve Extraction
              </button>
              <button className="w-full px-6 py-3 border-2 border-danger-500 dark:border-danger-600 text-danger-500 dark:text-danger-400 rounded-lg hover:bg-danger-50 dark:hover:bg-danger-900/20 transition-colors font-medium">
                Reject & Request Re-extraction
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
