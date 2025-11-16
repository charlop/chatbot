import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { RecentSearches } from '@/components/search/RecentSearches';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('RecentSearches Component', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Rendering', () => {
    it('should render empty state when no recent searches', () => {
      render(<RecentSearches />);

      expect(screen.queryByText(/recent searches/i)).not.toBeInTheDocument();
    });

    it('should render list of recent searches when they exist', () => {
      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002', 'ACC-TEST-00003'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      expect(screen.getByText(/recent searches/i)).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00001')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00002')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00003')).toBeInTheDocument();
    });

    it('should show maximum of 5 recent searches', () => {
      const searches = [
        'ACC-TEST-00001', // Oldest - should not appear
        'ACC-TEST-00002',
        'ACC-TEST-00003',
        'ACC-TEST-00004',
        'ACC-TEST-00005',
        'ACC-TEST-00006', // Newest
      ];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      // Should show last 5 (most recent)
      expect(screen.queryByText('ACC-TEST-00001')).not.toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00002')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00003')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00004')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00005')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00006')).toBeInTheDocument();
    });

    it('should display searches in reverse chronological order (newest first)', () => {
      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002', 'ACC-TEST-00003'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const items = screen.getAllByRole('button');
      // Skip the "Clear all" button, check search items
      const searchButtons = items.filter((item) =>
        item.textContent?.startsWith('ACC-')
      );

      expect(searchButtons[0]).toHaveTextContent('ACC-TEST-00003');
      expect(searchButtons[1]).toHaveTextContent('ACC-TEST-00002');
      expect(searchButtons[2]).toHaveTextContent('ACC-TEST-00001');
    });
  });

  describe('localStorage Integration', () => {
    it('should load recent searches from localStorage on mount', () => {
      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      expect(screen.getByText('ACC-TEST-00001')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00002')).toBeInTheDocument();
    });

    it('should reload searches when component remounts', () => {
      const { unmount } = render(<RecentSearches />);

      // Initially no searches
      expect(screen.queryByText(/recent searches/i)).not.toBeInTheDocument();

      // Unmount and add a search to localStorage
      unmount();
      const newSearch = 'ACC-TEST-99999';
      localStorage.setItem(
        'contract-recent-searches',
        JSON.stringify([newSearch])
      );

      // Remount - should load new search
      render(<RecentSearches />);
      expect(screen.getByText('ACC-TEST-99999')).toBeInTheDocument();
    });

    it('should display only first 5 searches when more are in localStorage', () => {
      // Simulate localStorage with 6 searches already managed by another component
      const searches = [
        'ACC-TEST-00002', // Oldest (should not display)
        'ACC-TEST-00003',
        'ACC-TEST-00004',
        'ACC-TEST-00005',
        'ACC-TEST-00006',
        'ACC-TEST-00007', // Newest
      ];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      // Should show only first 5
      expect(screen.queryByText('ACC-TEST-00002')).not.toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00003')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00004')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00005')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00006')).toBeInTheDocument();
      expect(screen.getByText('ACC-TEST-00007')).toBeInTheDocument();
    });

    it('should handle localStorage being unavailable', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock localStorage.getItem to throw
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('localStorage is disabled');
      });

      // Should not crash
      expect(() => render(<RecentSearches />)).not.toThrow();

      consoleErrorSpy.mockRestore();
      vi.restoreAllMocks();
    });

    it('should handle corrupted localStorage data', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Set invalid JSON
      localStorage.setItem('contract-recent-searches', 'INVALID_JSON{{{');

      // Should not crash
      expect(() => render(<RecentSearches />)).not.toThrow();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Click Interactions', () => {
    it('should call onSelect when a recent search is clicked', async () => {
      const user = userEvent.setup();
      const onSelectMock = vi.fn();

      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches onSelect={onSelectMock} />);

      const searchButton = screen.getByText('ACC-TEST-00001');
      await user.click(searchButton);

      expect(onSelectMock).toHaveBeenCalledWith('ACC-TEST-00001');
    });

    it('should call onSelect with correct account number for each search', async () => {
      const user = userEvent.setup();
      const onSelectMock = vi.fn();

      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002', 'ACC-TEST-00003'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches onSelect={onSelectMock} />);

      // Click second search
      await user.click(screen.getByText('ACC-TEST-00002'));
      expect(onSelectMock).toHaveBeenCalledWith('ACC-TEST-00002');

      // Click third search
      await user.click(screen.getByText('ACC-TEST-00003'));
      expect(onSelectMock).toHaveBeenCalledWith('ACC-TEST-00003');
    });

    it('should be clickable via keyboard (Enter key)', async () => {
      const user = userEvent.setup();
      const onSelectMock = vi.fn();

      const searches = ['ACC-TEST-00001'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches onSelect={onSelectMock} />);

      const searchButton = screen.getByText('ACC-TEST-00001');
      searchButton.focus();
      await user.keyboard('{Enter}');

      expect(onSelectMock).toHaveBeenCalledWith('ACC-TEST-00001');
    });
  });

  describe('Clear Functionality', () => {
    it('should have a clear all button when searches exist', () => {
      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      expect(screen.getByRole('button', { name: /clear all/i })).toBeInTheDocument();
    });

    it('should remove all searches when clear all is clicked', async () => {
      const user = userEvent.setup();

      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002', 'ACC-TEST-00003'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await user.click(clearButton);

      await waitFor(() => {
        expect(screen.queryByText('ACC-TEST-00001')).not.toBeInTheDocument();
        expect(screen.queryByText('ACC-TEST-00002')).not.toBeInTheDocument();
        expect(screen.queryByText('ACC-TEST-00003')).not.toBeInTheDocument();
      });
    });

    it('should clear localStorage when clear all is clicked', async () => {
      const user = userEvent.setup();

      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await user.click(clearButton);

      await waitFor(() => {
        const storedSearches = localStorage.getItem('contract-recent-searches');
        expect(storedSearches).toBeNull();
      });
    });

    it('should call onClear callback when clear all is clicked', async () => {
      const user = userEvent.setup();
      const onClearMock = vi.fn();

      const searches = ['ACC-TEST-00001'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches onClear={onClearMock} />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await user.click(clearButton);

      expect(onClearMock).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible name for recent searches list', () => {
      const searches = ['ACC-TEST-00001'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      // Check for heading or label
      expect(screen.getByText(/recent searches/i)).toBeInTheDocument();
    });

    it('should have accessible names for search buttons', () => {
      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const buttons = screen.getAllByRole('button');
      const searchButtons = buttons.filter((btn) =>
        btn.textContent?.startsWith('ACC-')
      );

      searchButtons.forEach((button) => {
        expect(button).toHaveAccessibleName();
      });
    });

    it('should have accessible name for clear all button', () => {
      const searches = ['ACC-TEST-00001'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      expect(clearButton).toHaveAccessibleName(/clear all/i);
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      const onSelectMock = vi.fn();

      const searches = ['ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches onSelect={onSelectMock} />);

      // Tab to first focusable element (Clear all button)
      await user.tab();
      const clearButton = screen.getByRole('button', { name: /clear all/i });
      expect(clearButton).toHaveFocus();

      // Tab to first search button
      await user.tab();
      const firstSearchButton = screen.getByText('ACC-TEST-00002'); // Newest first
      expect(firstSearchButton).toHaveFocus();

      // Press Enter
      await user.keyboard('{Enter}');
      expect(onSelectMock).toHaveBeenCalledWith('ACC-TEST-00002');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty array in localStorage', () => {
      localStorage.setItem('contract-recent-searches', JSON.stringify([]));

      render(<RecentSearches />);

      expect(screen.queryByText(/recent searches/i)).not.toBeInTheDocument();
    });

    it('should handle null in localStorage', () => {
      localStorage.setItem('contract-recent-searches', 'null');

      render(<RecentSearches />);

      expect(screen.queryByText(/recent searches/i)).not.toBeInTheDocument();
    });

    it('should deduplicate searches (same search appears only once)', () => {
      const searches = ['ACC-TEST-00001', 'ACC-TEST-00001', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const searchButtons = screen.getAllByRole('button').filter((btn) =>
        btn.textContent?.startsWith('ACC-')
      );

      // Should only have 2 unique searches
      expect(searchButtons).toHaveLength(2);
    });

    it('should trim whitespace from searches', () => {
      const searches = ['  ACC-TEST-00001  ', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      expect(screen.getByText('ACC-TEST-00001')).toBeInTheDocument();
    });

    it('should ignore empty strings in searches', () => {
      const searches = ['', 'ACC-TEST-00001', '   ', 'ACC-TEST-00002'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches />);

      const searchButtons = screen.getAllByRole('button').filter((btn) =>
        btn.textContent?.startsWith('ACC-')
      );

      // Should only have 2 valid searches
      expect(searchButtons).toHaveLength(2);
    });
  });

  describe('Component Props', () => {
    it('should use custom maxItems prop', () => {
      const searches = ['ACC-1', 'ACC-2', 'ACC-3', 'ACC-4', 'ACC-5', 'ACC-6'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      render(<RecentSearches maxItems={3} />);

      const searchButtons = screen.getAllByRole('button').filter((btn) =>
        btn.textContent?.startsWith('ACC-')
      );

      expect(searchButtons).toHaveLength(3);
    });

    it('should use custom className prop', () => {
      const searches = ['ACC-TEST-00001'];
      localStorage.setItem('contract-recent-searches', JSON.stringify(searches));

      const { container } = render(
        <RecentSearches className="custom-class" />
      );

      const element = container.querySelector('.custom-class');
      expect(element).toBeInTheDocument();
    });
  });
});
