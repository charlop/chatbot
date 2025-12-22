import React, { useState } from 'react';

interface StateValidationNoteProps {
  /**
   * State jurisdiction (e.g., "US-CA")
   */
  jurisdiction?: string;

  /**
   * State-specific validation message
   */
  message?: string;

  /**
   * Multi-state conflicts (if any)
   */
  conflicts?: Array<{
    jurisdiction: string;
    field: string;
    conflict: string;
  }>;
}

/**
 * StateValidationNote component displays state-specific validation context.
 *
 * Design:
 * - Light teal background callout
 * - Collapsible for long content
 * - Shows which state rules were applied
 * - Highlights multi-state conflicts
 */
export const StateValidationNote: React.FC<StateValidationNoteProps> = ({
  jurisdiction,
  message,
  conflicts,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!jurisdiction && !message && (!conflicts || conflicts.length === 0)) {
    return null;
  }

  const hasConflicts = conflicts && conflicts.length > 0;

  return (
    <div className="mt-2 rounded-md bg-state-50 border border-state-200 p-3">
      {/* Main message */}
      {message && (
        <div className="flex items-start gap-2">
          <svg
            className="w-4 h-4 text-state-400 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-xs text-state-700">{message}</p>
        </div>
      )}

      {/* Multi-state conflicts */}
      {hasConflicts && (
        <div className="mt-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs font-semibold text-state-600 hover:text-state-700"
          >
            <svg
              className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
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
            Multi-State Conflicts ({conflicts.length})
          </button>

          {isExpanded && (
            <ul className="mt-2 space-y-1">
              {conflicts.map((conflict, index) => (
                <li
                  key={index}
                  className="text-xs text-state-700 pl-4 flex items-start gap-2"
                >
                  <span className="font-semibold">{conflict.jurisdiction}:</span>
                  <span>{conflict.conflict}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default StateValidationNote;
