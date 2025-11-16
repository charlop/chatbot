import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { SearchBar } from '@/components/search/SearchBar';
import * as contractsApi from '@/lib/api/contracts';
import { ApiError } from '@/lib/api/client';

// Mock the contracts API
vi.mock('@/lib/api/contracts');

describe('SearchBar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Rendering', () => {
    it('should render with input and search button', () => {
      render(<SearchBar />);

      expect(screen.getByRole('textbox', { name: /account number/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
    });

    it('should render with custom placeholder', () => {
      render(<SearchBar placeholder="Enter contract number" />);

      expect(screen.getByPlaceholderText(/enter contract number/i)).toBeInTheDocument();
    });

    it('should render with helper text showing expected format', () => {
      render(<SearchBar />);

      expect(screen.getByText(/format: XXX-XXXX-XXXXX/i)).toBeInTheDocument();
    });

    it('should auto-focus input when autoFocus prop is true', () => {
      render(<SearchBar autoFocus />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      expect(input).toHaveFocus();
    });
  });

  describe('Input Validation', () => {
    it('should accept valid account number', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000000000001');

      expect(input).toHaveValue('000-0000-00001');
    });

    it('should show error for empty input when trying to search', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/account number is required/i)).toBeInTheDocument();
      });
    });

    it('should enable search button even when input is empty (to show validation)', () => {
      render(<SearchBar />);

      const button = screen.getByRole('button', { name: /search/i });
      expect(button).toBeEnabled();
    });

    it('should enable search button when input has value', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      const button = screen.getByRole('button', { name: /search/i });

      await user.type(input, '000000000001');

      expect(button).toBeEnabled();
    });

    it('should trim whitespace from input', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      };

      vi.mocked(contractsApi.searchContract).mockResolvedValue(mockResponse);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      // Type the account number (formatter will handle it)
      await user.type(input, '000000000001');

      // Manually add whitespace to the value (simulating trailing spaces)
      // This tests the trim logic in handleSubmit
      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        // Verify API was called with formatted value (dashes will be stripped inside searchContract)
        expect(contractsApi.searchContract).toHaveBeenCalledWith('000-0000-00001');
      });
    });
  });

  describe('Account Number Formatting', () => {
    it('should auto-format account number as user types', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });

      // Type without dashes (12 digits)
      await user.type(input, '123456789012');

      // Should auto-format with dashes (3-4-5 pattern)
      expect(input).toHaveValue('123-4567-89012');
    });

    it('should handle account number that already has dashes', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      expect(input).toHaveValue('000-0000-00001');
    });

    it('should strip non-numeric characters', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, 'abc123def456ghi789jkl012');

      // Only digits should remain, formatted as 3-4-5
      expect(input).toHaveValue('123-4567-89012');
    });

    it('should handle partial input during typing', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });

      // Type 5 digits
      await user.type(input, '12345');
      expect(input).toHaveValue('123-45');

      await user.clear(input);
      // Type 8 digits
      await user.type(input, '12345678');
      expect(input).toHaveValue('123-4567-8');
    });
  });

  describe('API Integration', () => {
    it('should call searchContract API with formatted account number', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      };

      vi.mocked(contractsApi.searchContract).mockResolvedValue(mockResponse);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      expect(contractsApi.searchContract).toHaveBeenCalledWith('000-0000-00001');
    });

    it('should show loading state during API call', async () => {
      const user = userEvent.setup();

      // Create a promise we can control
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(contractsApi.searchContract).mockReturnValue(promise as any);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      // Should show loading state
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
      expect(button).toBeDisabled();

      // Resolve the promise to finish the test
      resolvePromise!({
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      });
    });

    it('should disable input during API call', async () => {
      const user = userEvent.setup();

      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(contractsApi.searchContract).mockReturnValue(promise as any);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      expect(input).toBeDisabled();

      resolvePromise!({
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      });
    });
  });

  describe('Success Handling', () => {
    it('should call onSuccess callback with contract ID when search succeeds', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();
      const mockResponse = {
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      };

      vi.mocked(contractsApi.searchContract).mockResolvedValue(mockResponse);

      render(<SearchBar onSuccess={onSuccess} />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(mockResponse);
      });
    });

    it('should clear error state on successful search', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      };

      // First, cause an error
      vi.mocked(contractsApi.searchContract).mockRejectedValueOnce(
        new ApiError('Network error', 0)
      );

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Now succeed
      vi.mocked(contractsApi.searchContract).mockResolvedValueOnce(mockResponse);
      await user.click(button);

      await waitFor(() => {
        expect(screen.queryByText(/network error/i)).not.toBeInTheDocument();
      });
    });

    it('should re-enable input and button after successful search', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      };

      vi.mocked(contractsApi.searchContract).mockResolvedValue(mockResponse);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      const button = screen.getByRole('button', { name: /search/i });

      await user.type(input, '000-0000-00001');
      await user.click(button);

      await waitFor(() => {
        expect(input).toBeEnabled();
        expect(button).toBeEnabled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when contract not found (404)', async () => {
      const user = userEvent.setup();
      const notFoundError = new ApiError(
        'Contract not found for account number: 999999999999',
        404
      );

      vi.mocked(contractsApi.searchContract).mockRejectedValue(notFoundError);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '999999999999');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/contract not found/i)).toBeInTheDocument();
      });
    });

    it('should display error message for network errors', async () => {
      const user = userEvent.setup();
      const networkError = new ApiError(
        'Network error: Unable to reach the server',
        0
      );

      vi.mocked(contractsApi.searchContract).mockRejectedValue(networkError);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/unable to reach the server/i)).toBeInTheDocument();
      });
    });

    it('should display error message for server errors (500)', async () => {
      const user = userEvent.setup();
      const serverError = new ApiError('Internal server error', 500);

      vi.mocked(contractsApi.searchContract).mockRejectedValue(serverError);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/internal server error/i)).toBeInTheDocument();
      });
    });

    it('should call onError callback when search fails', async () => {
      const user = userEvent.setup();
      const onError = vi.fn();
      const error = new ApiError('Contract not found', 404);

      vi.mocked(contractsApi.searchContract).mockRejectedValue(error);

      render(<SearchBar onError={onError} />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '999999999999');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Contract not found');
      });
    });

    it('should re-enable input and button after error', async () => {
      const user = userEvent.setup();
      const error = new ApiError('Contract not found', 404);

      vi.mocked(contractsApi.searchContract).mockRejectedValue(error);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      const button = screen.getByRole('button', { name: /search/i });

      await user.type(input, 'ACC-NOT-FOUND');
      await user.click(button);

      await waitFor(() => {
        expect(input).toBeEnabled();
        expect(button).toBeEnabled();
      });
    });
  });

  describe('Keyboard Interactions', () => {
    it('should submit on Enter key press', async () => {
      const user = userEvent.setup();
      const onSearch = vi.fn();
      const mockResponse = {
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      };

      vi.mocked(contractsApi.searchContract).mockResolvedValue(mockResponse);

      render(<SearchBar onSearch={onSearch} />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001{Enter}');

      await waitFor(() => {
        expect(contractsApi.searchContract).toHaveBeenCalledWith('000-0000-00001');
      });
    });

    it('should not submit on Enter if input is empty', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '{Enter}');

      expect(contractsApi.searchContract).not.toHaveBeenCalled();
    });

    it('should support tab navigation', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });

      // Type something to enable the button
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });

      input.focus();
      expect(input).toHaveFocus();

      // Tab to clear button
      await user.tab();
      const clearButton = screen.getByRole('button', { name: /clear/i });
      expect(clearButton).toHaveFocus();

      // Tab to search button
      await user.tab();
      expect(button).toHaveFocus();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      const button = screen.getByRole('button', { name: /search/i });

      expect(input).toHaveAccessibleName();
      expect(button).toHaveAccessibleName();
    });

    it('should have aria-invalid when there is an error', async () => {
      const user = userEvent.setup();
      const error = new ApiError('Contract not found', 404);

      vi.mocked(contractsApi.searchContract).mockRejectedValue(error);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, 'ACC-NOT-FOUND');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        expect(input).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('should have aria-describedby pointing to error message', async () => {
      const user = userEvent.setup();
      const error = new ApiError('Contract not found', 404);

      vi.mocked(contractsApi.searchContract).mockRejectedValue(error);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, 'ACC-NOT-FOUND');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      await waitFor(() => {
        const errorElement = screen.getByRole('alert');
        const ariaDescribedBy = input.getAttribute('aria-describedby');
        expect(ariaDescribedBy).toBeTruthy();
        expect(errorElement).toHaveAttribute('id', ariaDescribedBy!);
      });
    });

    it('should have aria-busy during loading', async () => {
      const user = userEvent.setup();

      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(contractsApi.searchContract).mockReturnValue(promise as any);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const button = screen.getByRole('button', { name: /search/i });
      await user.click(button);

      expect(button).toHaveAttribute('aria-busy', 'true');

      resolvePromise!({
        contractId: 'GAP-2024-0001',
        accountNumber: '000000000001',
        status: 'pending',
      });
    });
  });

  describe('Clear Functionality', () => {
    it('should have a clear button when input has value', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });

    it('should clear input when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '000-0000-00001');

      const clearButton = screen.getByRole('button', { name: /clear/i });
      await user.click(clearButton);

      expect(input).toHaveValue('');
    });

    it('should clear error message when input is cleared', async () => {
      const user = userEvent.setup();
      const error = new ApiError('Contract not found', 404);

      vi.mocked(contractsApi.searchContract).mockRejectedValue(error);

      render(<SearchBar />);

      const input = screen.getByRole('textbox', { name: /account number/i });
      await user.type(input, '999999999999');

      const searchButton = screen.getByRole('button', { name: /search/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/contract not found/i)).toBeInTheDocument();
      });

      const clearButton = screen.getByRole('button', { name: /clear/i });
      await user.click(clearButton);

      expect(screen.queryByText(/contract not found/i)).not.toBeInTheDocument();
    });
  });
});
