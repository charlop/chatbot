import React from 'react';

export interface ConfidenceBadgeProps {
  /**
   * Confidence score (0-100)
   */
  confidence?: number;

  /**
   * Optional CSS class for custom styling
   */
  className?: string;
}

/**
 * Badge component that displays confidence score with color-coding
 * - Green (≥90%): High confidence
 * - Orange (70-89%): Medium confidence
 * - Red (<70%): Low confidence
 */
export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  className = '',
}) => {
  // Handle undefined confidence
  if (confidence === undefined || confidence === null) {
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-neutral-100 text-neutral-600 ${className}`}
        role="status"
        aria-label="Confidence not available"
        tabIndex={0}
        title="Confidence score not available"
      >
        N/A
      </span>
    );
  }

  // Round confidence to whole number
  const roundedConfidence = Math.round(confidence);

  // Determine color and tooltip based on confidence level
  let bgColor: string;
  let textColor: string;
  let tooltipText: string;
  let confidenceLevel: string;

  if (roundedConfidence >= 90) {
    bgColor = 'bg-success-light';
    textColor = 'text-success-dark';
    confidenceLevel = 'High confidence';
    tooltipText = 'High confidence - extraction is very likely accurate';
  } else if (roundedConfidence >= 70) {
    bgColor = 'bg-warning-light';
    textColor = 'text-warning-dark';
    confidenceLevel = 'Medium confidence';
    tooltipText = 'Medium confidence - extraction should be reviewed';
  } else {
    bgColor = 'bg-danger-light';
    textColor = 'text-danger-dark';
    confidenceLevel = 'Low confidence';
    tooltipText = 'Low confidence - extraction requires careful verification';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${bgColor} ${textColor} ${className}`}
      role="status"
      aria-label={`${confidenceLevel}: ${roundedConfidence} percent`}
      tabIndex={0}
      title={tooltipText}
    >
      {roundedConfidence}%
    </span>
  );
};
