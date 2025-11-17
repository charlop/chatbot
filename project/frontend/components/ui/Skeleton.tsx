import React from 'react';

export interface SkeletonProps {
  /**
   * Width of the skeleton (CSS value)
   */
  width?: string;

  /**
   * Height of the skeleton (CSS value)
   */
  height?: string;

  /**
   * Border radius variant
   */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';

  /**
   * Additional CSS classes
   */
  className?: string;
}

const roundedVariants = {
  none: '',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  full: 'rounded-full',
};

/**
 * Skeleton loader component for displaying loading states
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  rounded = 'md',
  className = '',
}) => {
  const style: React.CSSProperties = {};
  if (width) style.width = width;
  if (height) style.height = height;

  return (
    <div
      className={`animate-pulse bg-neutral-200 dark:bg-neutral-700 ${roundedVariants[rounded]} ${className}`}
      style={style}
      aria-label="Loading..."
      role="status"
    />
  );
};

/**
 * Skeleton group for multiple skeleton elements
 */
export interface SkeletonGroupProps {
  count?: number;
  className?: string;
  skeletonProps?: SkeletonProps;
}

export const SkeletonGroup: React.FC<SkeletonGroupProps> = ({
  count = 3,
  className = '',
  skeletonProps = {},
}) => {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton key={index} {...skeletonProps} />
      ))}
    </div>
  );
};

/**
 * Card skeleton for card-based layouts
 */
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 p-6 ${className}`}>
      <Skeleton width="60%" height="24px" className="mb-4" />
      <SkeletonGroup count={3} skeletonProps={{ height: '16px' }} />
    </div>
  );
};

/**
 * Data field skeleton for form-like layouts
 */
export const SkeletonDataField: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`space-y-2 ${className}`}>
      <Skeleton width="40%" height="14px" />
      <Skeleton width="100%" height="20px" />
    </div>
  );
};
