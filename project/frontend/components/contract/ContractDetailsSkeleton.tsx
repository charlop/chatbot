import React from 'react';
import { Skeleton, SkeletonDataField } from '@/components/ui/Skeleton';

/**
 * Skeleton loader for contract details page
 */
export const ContractDetailsSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-250px)]">
      {/* Left Panel - PDF Skeleton */}
      <div className="lg:col-span-2 h-full">
        <div className="flex flex-col h-full bg-white rounded-xl border border-neutral-200 dark:border-neutral-700">
          {/* Toolbar skeleton */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
            <Skeleton width="180px" height="20px" />
            <div className="flex gap-2">
              <Skeleton width="40px" height="40px" rounded="lg" />
              <Skeleton width="40px" height="40px" rounded="lg" />
              <Skeleton width="40px" height="40px" rounded="lg" />
            </div>
          </div>

          {/* PDF content skeleton */}
          <div className="flex-1 bg-neutral-50 dark:bg-neutral-900 flex items-center justify-center">
            <div className="text-center">
              <Skeleton width="80px" height="80px" rounded="full" className="mx-auto mb-4" />
              <Skeleton width="120px" height="16px" className="mx-auto" />
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Data Skeleton */}
      <div className="lg:col-span-1 h-full">
        <div className="w-[464px] h-full bg-neutral-50 border-l border-neutral-200 dark:border-neutral-700 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Header skeleton */}
            <div>
              <Skeleton width="150px" height="24px" className="mb-2" />
              <Skeleton width="250px" height="14px" />
            </div>

            {/* Data cards skeleton */}
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <Skeleton width="140px" height="16px" />
                  <Skeleton width="60px" height="20px" rounded="full" />
                </div>
                <Skeleton width="100%" height="32px" />
                <Skeleton width="120px" height="14px" />
              </div>
            ))}

            {/* Audit trail skeleton */}
            <div className="pt-4 border-t border-neutral-200 dark:border-neutral-700">
              <Skeleton width="120px" height="16px" className="mb-3" />
              <div className="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-4 space-y-3">
                <SkeletonDataField />
                <SkeletonDataField />
                <SkeletonDataField />
              </div>
            </div>

            {/* Submit button skeleton */}
            <div className="pt-4 border-t border-neutral-200 dark:border-neutral-700">
              <Skeleton width="100%" height="48px" rounded="lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
