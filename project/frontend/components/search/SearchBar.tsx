'use client';

import { useState, FormEvent, ChangeEvent, KeyboardEvent } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { searchContract, SearchContractResponse } from '@/lib/api/contracts';
import { ApiError } from '@/lib/api/client';
import { addRecentSearch } from '@/lib/utils/recentSearches';

export interface SearchBarProps {
  onSearch?: (accountNumber: string) => void;
  onSuccess?: (result: SearchContractResponse) => void;
  onError?: (error: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  value?: string; // Optional controlled value
  onChange?: (value: string) => void; // Optional controlled onChange
}

/**
 * Format account number with dashes
 * Format: XXX-XXXX-XXXXX (12 digits total)
 * Examples:
 *   000000000001 -> 000-0000-00001
 *   123456789012 -> 123-4567-89012
 *   123456 -> 123-456 (partial input)
 */
const formatAccountNumber = (value: string): string => {
  // Remove all non-digit characters
  const cleaned = value.replace(/\D/g, '');

  // Add dashes at appropriate positions (3-4-5 pattern)
  if (cleaned.length <= 3) {
    return cleaned;
  } else if (cleaned.length <= 7) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
  } else {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7, 12)}`;
  }
};

export const SearchBar = ({
  onSearch,
  onSuccess,
  onError,
  placeholder = 'Enter account number',
  autoFocus = false,
  value: controlledValue,
  onChange: controlledOnChange,
}: SearchBarProps) => {
  const [internalValue, setInternalValue] = useState('');

  // Use controlled value if provided, otherwise use internal state
  const isControlled = controlledValue !== undefined;
  const accountNumber = isControlled ? controlledValue : internalValue;
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const formatted = formatAccountNumber(e.target.value);

    if (isControlled && controlledOnChange) {
      controlledOnChange(formatted);
    } else {
      setInternalValue(formatted);
    }

    // Clear error when user types
    if (error) {
      setError('');
    }
  };

  const handleClear = () => {
    if (isControlled && controlledOnChange) {
      controlledOnChange('');
    } else {
      setInternalValue('');
    }
    setError('');
  };

  const handleSubmit = async (e?: FormEvent) => {
    if (e) {
      e.preventDefault();
    }

    const trimmed = accountNumber.trim();

    // Validate input
    if (!trimmed) {
      setError('Account number is required');
      return;
    }

    // Clear previous error
    setError('');
    setIsLoading(true);

    // Call onSearch callback
    if (onSearch) {
      onSearch(trimmed);
    }

    try {
      // Call API
      const response = await searchContract(trimmed);

      // Save to recent searches
      addRecentSearch(trimmed);

      // Success callback with full response
      if (onSuccess) {
        onSuccess(response);
      }
    } catch (err) {
      // Handle error
      const apiError = err as ApiError;
      const errorMessage = apiError.message || 'An error occurred while searching';

      setError(errorMessage);

      // Error callback
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (accountNumber.trim()) {
        handleSubmit();
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            label="Account Number"
            value={accountNumber}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            helperText={!error ? 'Format: XXX-XXXX-XXXXX (12 digits)' : undefined}
            error={error}
            disabled={isLoading}
            autoFocus={autoFocus}
            fullWidth
            aria-label="Account Number"
          />

          {accountNumber && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-9 text-neutral-400 hover:text-neutral-600 transition-colors"
              aria-label="Clear"
              disabled={isLoading}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        <div className="flex items-end">
          <Button
            type="submit"
            disabled={isLoading}
            loading={isLoading}
            aria-label="Search"
            className="h-[42px]"
          >
            Search
          </Button>
        </div>
      </div>
    </form>
  );
};
