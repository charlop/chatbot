/**
 * Utility functions for managing recent contract searches in localStorage
 */

const RECENT_SEARCHES_KEY = 'contract-recent-searches';
const MAX_RECENT_SEARCHES = 5;

/**
 * Get recent searches from localStorage
 * @returns Array of account numbers (oldest first)
 */
export const getRecentSearches = (): string[] => {
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (!stored || stored === 'null') {
      return [];
    }

    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return [];
    }

    // Filter and clean
    const cleaned = parsed
      .map((search) => (typeof search === 'string' ? search.trim() : ''))
      .filter((search) => search.length > 0);

    // Deduplicate (keep first occurrence)
    return Array.from(new Set(cleaned));
  } catch (error) {
    console.error('Error loading recent searches from localStorage:', error);
    return [];
  }
};

/**
 * Add a search to recent searches
 * Maintains max 5 searches, removes duplicates, and keeps newest searches
 * @param accountNumber - Account number to add
 */
export const addRecentSearch = (accountNumber: string): void => {
  try {
    const trimmed = accountNumber.trim();
    if (!trimmed) {
      return;
    }

    let searches = getRecentSearches();

    // Remove if already exists (to move to end)
    searches = searches.filter((search) => search !== trimmed);

    // Add to end (newest)
    searches.push(trimmed);

    // Keep only last N searches
    if (searches.length > MAX_RECENT_SEARCHES) {
      searches = searches.slice(-MAX_RECENT_SEARCHES);
    }

    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(searches));
  } catch (error) {
    console.error('Error saving recent search to localStorage:', error);
  }
};

/**
 * Clear all recent searches from localStorage
 */
export const clearRecentSearches = (): void => {
  try {
    localStorage.removeItem(RECENT_SEARCHES_KEY);
  } catch (error) {
    console.error('Error clearing recent searches from localStorage:', error);
  }
};
