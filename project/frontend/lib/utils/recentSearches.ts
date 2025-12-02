/**
 * Utility functions for managing recent contract searches in localStorage
 */

const RECENT_SEARCHES_KEY = 'contract-recent-searches';
const MAX_RECENT_SEARCHES = 5;

export interface RecentSearch {
  searchTerm: string; // Account number or template ID searched
  searchType: 'account' | 'template'; // Type of search performed
  templateId: string; // Resolved template ID
  timestamp: string; // ISO timestamp of search
}

/**
 * Get recent searches from localStorage
 * @returns Array of recent searches (oldest first)
 */
export const getRecentSearches = (): RecentSearch[] => {
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (!stored || stored === 'null') {
      return [];
    }

    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return [];
    }

    // Support old format (array of strings) and migrate
    if (parsed.length > 0 && typeof parsed[0] === 'string') {
      // Old format: array of account numbers
      // Migrate to new format with deduplication
      const uniqueSearches = new Set(
        parsed
          .filter((search) => typeof search === 'string' && search.trim().length > 0)
          .map((s) => s.trim())
      );

      return Array.from(uniqueSearches).map((accountNumber) => ({
        searchTerm: accountNumber,
        searchType: 'account' as const,
        templateId: '', // Unknown for migrated data
        timestamp: new Date().toISOString(),
      }));
    }

    // New format: array of RecentSearch objects
    return parsed
      .filter(
        (search) =>
          search &&
          typeof search === 'object' &&
          search.searchTerm &&
          search.searchType &&
          search.templateId !== undefined // Allow empty string for migrated data
      )
      .map((search) => ({
        searchTerm: search.searchTerm.trim(),
        searchType: search.searchType,
        templateId: search.templateId,
        timestamp: search.timestamp || new Date().toISOString(),
      }));
  } catch (error) {
    console.error('Error loading recent searches from localStorage:', error);
    return [];
  }
};

/**
 * Add a search to recent searches
 * Maintains max 5 searches, removes duplicates, and keeps newest searches
 * @param searchTerm - Account number or template ID searched
 * @param searchType - Type of search performed ('account' or 'template')
 * @param templateId - Resolved template ID
 */
export const addRecentSearch = (
  searchTerm: string,
  searchType: 'account' | 'template',
  templateId: string
): void => {
  try {
    const trimmed = searchTerm.trim();
    if (!trimmed || !templateId) {
      return;
    }

    let searches = getRecentSearches();

    // Remove if same search term already exists (to move to end)
    searches = searches.filter((search) => search.searchTerm !== trimmed);

    // Add to end (newest)
    searches.push({
      searchTerm: trimmed,
      searchType,
      templateId,
      timestamp: new Date().toISOString(),
    });

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

/**
 * Format a recent search for display
 * @param search - Recent search object
 * @returns Formatted display string
 */
export const formatRecentSearch = (search: RecentSearch): string => {
  if (search.searchType === 'account') {
    return `Account: ${search.searchTerm}`;
  } else {
    return `Template: ${search.searchTerm}`;
  }
};
