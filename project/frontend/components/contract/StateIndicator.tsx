import React from 'react';

interface StateIndicatorProps {
  /**
   * Primary state code (e.g., "CA", "NY")
   */
  state: string;

  /**
   * Additional applicable states (for multi-state contracts)
   */
  applicableStates?: string[];

  /**
   * Size variant
   */
  size?: 'sm' | 'md';

  /**
   * Whether to show tooltip with full state name
   */
  showTooltip?: boolean;
}

// State code to full name mapping
const STATE_NAMES: Record<string, string> = {
  AL: 'Alabama',
  AK: 'Alaska',
  AZ: 'Arizona',
  AR: 'Arkansas',
  CA: 'California',
  CO: 'Colorado',
  CT: 'Connecticut',
  DE: 'Delaware',
  FL: 'Florida',
  GA: 'Georgia',
  HI: 'Hawaii',
  ID: 'Idaho',
  IL: 'Illinois',
  IN: 'Indiana',
  IA: 'Iowa',
  KS: 'Kansas',
  KY: 'Kentucky',
  LA: 'Louisiana',
  ME: 'Maine',
  MD: 'Maryland',
  MA: 'Massachusetts',
  MI: 'Michigan',
  MN: 'Minnesota',
  MS: 'Mississippi',
  MO: 'Missouri',
  MT: 'Montana',
  NE: 'Nebraska',
  NV: 'Nevada',
  NH: 'New Hampshire',
  NJ: 'New Jersey',
  NM: 'New Mexico',
  NY: 'New York',
  NC: 'North Carolina',
  ND: 'North Dakota',
  OH: 'Ohio',
  OK: 'Oklahoma',
  OR: 'Oregon',
  PA: 'Pennsylvania',
  RI: 'Rhode Island',
  SC: 'South Carolina',
  SD: 'South Dakota',
  TN: 'Tennessee',
  TX: 'Texas',
  UT: 'Utah',
  VT: 'Vermont',
  VA: 'Virginia',
  WA: 'Washington',
  WV: 'West Virginia',
  WI: 'Wisconsin',
  WY: 'Wyoming',
};

/**
 * StateIndicator component displays state information with a teal badge.
 *
 * Design:
 * - Teal background (#e3fffa)
 * - Dark teal text (#00857f)
 * - Rounded pill shape
 * - Optional tooltip with full state name
 */
export const StateIndicator: React.FC<StateIndicatorProps> = ({
  state,
  applicableStates,
  size = 'md',
  showTooltip = true,
}) => {
  const stateName = STATE_NAMES[state] || state;

  // Size classes
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
  };

  return (
    <div className="flex items-center gap-2">
      {/* Primary state badge */}
      <span
        className={`
          inline-flex items-center rounded-full font-semibold
          bg-state-50 text-state-400 border border-state-200
          ${sizeClasses[size]}
        `}
        title={showTooltip ? stateName : undefined}
        aria-label={`State: ${stateName}`}
      >
        <svg
          className="w-3 h-3 mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        {state}
      </span>

      {/* Additional states (multi-state) */}
      {applicableStates && applicableStates.length > 0 && (
        <span className="text-xs text-neutral-500">
          Also: {applicableStates.join(', ')}
        </span>
      )}
    </div>
  );
};

export default StateIndicator;
