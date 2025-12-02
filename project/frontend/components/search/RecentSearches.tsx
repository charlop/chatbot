'use client';

import { useState, useEffect } from 'react';
import {
  getRecentSearches,
  clearRecentSearches,
  RecentSearch,
  formatRecentSearch,
} from '@/lib/utils/recentSearches';

const DEFAULT_MAX_ITEMS = 5;

export interface RecentSearchesProps {
  onSelect?: (searchTerm: string) => void;
  onClear?: () => void;
  maxItems?: number;
  className?: string;
}

export const RecentSearches = ({
  onSelect,
  onClear,
  maxItems = DEFAULT_MAX_ITEMS,
  className = '',
}: RecentSearchesProps) => {
  const [searches, setSearches] = useState<RecentSearch[]>([]);

  // Load searches from localStorage on mount
  useEffect(() => {
    const recentSearches = getRecentSearches();
    setSearches(recentSearches);
  }, []);

  // Handle search selection
  const handleSelect = (searchTerm: string) => {
    if (onSelect) {
      onSelect(searchTerm);
    }
  };

  // Handle clear all
  const handleClearAll = () => {
    clearRecentSearches();
    setSearches([]);

    if (onClear) {
      onClear();
    }
  };

  // Don't render if no searches
  if (searches.length === 0) {
    return null;
  }

  // Show only the most recent N searches (last N items if array is ordered oldest-first)
  const displaySearches = searches.slice(-maxItems);

  return (
    <div className={`mt-2 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
          Recent Searches
        </h3>
        <button
          type="button"
          onClick={handleClearAll}
          className="text-xs text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition-colors"
          aria-label="Clear all recent searches"
        >
          Clear all
        </button>
      </div>

      <div className="space-y-1">
        {/* Display in reverse order (newest first) */}
        {[...displaySearches].reverse().map((search, index) => (
          <button
            key={`${search.searchTerm}-${search.timestamp}-${index}`}
            type="button"
            onClick={() => handleSelect(search.searchTerm)}
            className="w-full text-left px-3 py-2 text-sm text-neutral-700 dark:text-neutral-300 bg-neutral-50 dark:bg-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded border border-neutral-200 dark:border-neutral-700 transition-colors"
            aria-label={`Search for ${search.searchTerm}`}
          >
            {search.searchTerm}
          </button>
        ))}
      </div>
    </div>
  );
};
