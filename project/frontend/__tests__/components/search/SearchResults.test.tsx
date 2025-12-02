import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchResults } from '@/components/search/SearchResults';
import { SearchContractResponse } from '@/lib/api/contracts';

describe('SearchResults', () => {
  const mockResult: SearchContractResponse = {
    contractId: 'GAP-2024-001',
    contractType: 'GAP Insurance',
    templateVersion: '2.1',
    effectiveDate: '2024-01-01',
    contractDate: '2023-12-15',
  };

  describe('Rendering', () => {
    it('should render contract details successfully', () => {
      render(<SearchResults result={mockResult} />);

      expect(screen.getByText('Contract Template Found')).toBeInTheDocument();
      expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
      expect(screen.getByText('GAP Insurance')).toBeInTheDocument();
      expect(screen.getByText('2.1')).toBeInTheDocument();
    });

    it('should render without optional callbacks', () => {
      expect(() => {
        render(<SearchResults result={mockResult} />);
      }).not.toThrow();
    });

    it('should render with only onViewDetails callback', () => {
      render(<SearchResults result={mockResult} onViewDetails={vi.fn()} />);
      expect(screen.getByText('View Full Details')).toBeInTheDocument();
      expect(screen.queryByText('New Search')).not.toBeInTheDocument();
    });

    it('should render with only onNewSearch callback', () => {
      render(<SearchResults result={mockResult} onNewSearch={vi.fn()} />);
      expect(screen.getByText('New Search')).toBeInTheDocument();
      expect(screen.queryByText('View Full Details')).not.toBeInTheDocument();
    });

    it('should render with both callbacks', () => {
      render(
        <SearchResults
          result={mockResult}
          onViewDetails={vi.fn()}
          onNewSearch={vi.fn()}
        />
      );
      expect(screen.getByText('View Full Details')).toBeInTheDocument();
      expect(screen.getByText('New Search')).toBeInTheDocument();
    });
  });

  describe('Optional Fields', () => {
    it('should render without templateVersion', () => {
      const resultWithoutVersion = { ...mockResult, templateVersion: undefined };
      render(<SearchResults result={resultWithoutVersion} />);

      expect(screen.queryByText('Template Version')).not.toBeInTheDocument();
      expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
    });

    it('should render without effectiveDate', () => {
      const resultWithoutEffectiveDate = { ...mockResult, effectiveDate: undefined };
      render(<SearchResults result={resultWithoutEffectiveDate} />);

      expect(screen.queryByText('Effective Date')).not.toBeInTheDocument();
      expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
    });

    it('should render without contractDate', () => {
      const resultWithoutContractDate = { ...mockResult, contractDate: undefined };
      render(<SearchResults result={resultWithoutContractDate} />);

      expect(screen.queryByText('Created Date')).not.toBeInTheDocument();
      expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
    });

    it('should render with all optional fields missing', () => {
      const minimalResult: SearchContractResponse = {
        contractId: 'MIN-001',
        contractType: 'Basic',
      };

      render(<SearchResults result={minimalResult} />);

      expect(screen.getByText('MIN-001')).toBeInTheDocument();
      expect(screen.getByText('Basic')).toBeInTheDocument();
      expect(screen.queryByText('Template Version')).not.toBeInTheDocument();
      expect(screen.queryByText('Effective Date')).not.toBeInTheDocument();
      expect(screen.queryByText('Created Date')).not.toBeInTheDocument();
    });
  });

  describe('Contract Type Colors', () => {
    it('should apply primary color for GAP contracts', () => {
      const gapResult = { ...mockResult, contractType: 'GAP Insurance' };
      const { container } = render(<SearchResults result={gapResult} />);

      const badge = container.querySelector('.text-primary-600');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('GAP Insurance');
    });

    it('should apply success color for warranty contracts', () => {
      const warrantyResult = { ...mockResult, contractType: 'Extended Warranty' };
      render(<SearchResults result={warrantyResult} />);

      expect(screen.getByText('Extended Warranty')).toBeInTheDocument();
      // Verify it has the success color class
      const badge = screen.getByText('Extended Warranty');
      expect(badge).toHaveClass('text-success-600');
    });

    it('should apply neutral color for other contract types', () => {
      const otherResult = { ...mockResult, contractType: 'Service Contract' };
      render(<SearchResults result={otherResult} />);

      expect(screen.getByText('Service Contract')).toBeInTheDocument();
      // Verify it has the neutral color class
      const badge = screen.getByText('Service Contract');
      expect(badge).toHaveClass('text-neutral-600');
    });

    it('should handle case-insensitive GAP matching', () => {
      const gapLowercase = { ...mockResult, contractType: 'gap insurance' };
      const { container } = render(<SearchResults result={gapLowercase} />);

      const badge = container.querySelector('.text-primary-600');
      expect(badge).toBeInTheDocument();
    });

    it('should handle case-insensitive warranty matching', () => {
      const warrantyUppercase = { ...mockResult, contractType: 'WARRANTY' };
      const { container } = render(<SearchResults result={warrantyUppercase} />);

      const badge = container.querySelector('.text-success-600');
      expect(badge).toBeInTheDocument();
    });

    it('should handle partial GAP match', () => {
      const partialGap = { ...mockResult, contractType: 'Vehicle GAP Coverage' };
      const { container } = render(<SearchResults result={partialGap} />);

      const badge = container.querySelector('.text-primary-600');
      expect(badge).toBeInTheDocument();
    });

    it('should handle partial warranty match', () => {
      const partialWarranty = { ...mockResult, contractType: 'Vehicle Warranty Plan' };
      const { container } = render(<SearchResults result={partialWarranty} />);

      const badge = container.querySelector('.text-success-600');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Date Formatting', () => {
    it('should format effectiveDate correctly', () => {
      render(<SearchResults result={mockResult} />);

      // The date should be formatted as a locale date string
      const formattedDate = new Date('2024-01-01').toLocaleDateString();
      expect(screen.getByText(formattedDate)).toBeInTheDocument();
    });

    it('should format contractDate correctly', () => {
      render(<SearchResults result={mockResult} />);

      const formattedDate = new Date('2023-12-15').toLocaleDateString();
      expect(screen.getByText(formattedDate)).toBeInTheDocument();
    });

    it('should handle different date formats', () => {
      const result = {
        ...mockResult,
        effectiveDate: '2024-06-15T10:30:00Z',
        contractDate: '2024-05-20T08:15:00Z',
      };

      render(<SearchResults result={result} />);

      const effectiveFormatted = new Date('2024-06-15T10:30:00Z').toLocaleDateString();
      const contractFormatted = new Date('2024-05-20T08:15:00Z').toLocaleDateString();

      expect(screen.getByText(effectiveFormatted)).toBeInTheDocument();
      expect(screen.getByText(contractFormatted)).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should call onViewDetails when button is clicked', async () => {
      const user = userEvent.setup();
      const onViewDetails = vi.fn();

      render(<SearchResults result={mockResult} onViewDetails={onViewDetails} />);

      const button = screen.getByText('View Full Details');
      await user.click(button);

      expect(onViewDetails).toHaveBeenCalledTimes(1);
    });

    it('should call onNewSearch when button is clicked', async () => {
      const user = userEvent.setup();
      const onNewSearch = vi.fn();

      render(<SearchResults result={mockResult} onNewSearch={onNewSearch} />);

      const button = screen.getByText('New Search');
      await user.click(button);

      expect(onNewSearch).toHaveBeenCalledTimes(1);
    });

    it('should not throw when clicking buttons without callbacks', async () => {
      const user = userEvent.setup();

      render(<SearchResults result={mockResult} />);

      // No buttons should be rendered
      expect(screen.queryByText('View Full Details')).not.toBeInTheDocument();
      expect(screen.queryByText('New Search')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined result properties gracefully', () => {
      const resultWithUndefined = {
        contractId: 'TEST-001',
        contractType: 'Test',
        templateVersion: undefined,
        effectiveDate: undefined,
        contractDate: undefined,
      } as SearchContractResponse;

      expect(() => {
        render(<SearchResults result={resultWithUndefined} />);
      }).not.toThrow();
    });

    it('should handle empty string contractId', () => {
      const result = { ...mockResult, contractId: '' };
      render(<SearchResults result={result} />);

      expect(screen.getByText('Contract Template Found')).toBeInTheDocument();
    });

    it('should handle empty string contractType', () => {
      const result = { ...mockResult, contractType: '' };
      const { container } = render(<SearchResults result={result} />);

      // Should default to neutral color
      const badge = container.querySelector('.text-neutral-600');
      expect(badge).toBeInTheDocument();
    });

    it('should handle very long contractId', () => {
      const result = {
        ...mockResult,
        contractId: 'VERY-LONG-CONTRACT-ID-WITH-MANY-CHARACTERS-2024-Q1-VERSION-2.0',
      };

      render(<SearchResults result={result} />);
      expect(
        screen.getByText('VERY-LONG-CONTRACT-ID-WITH-MANY-CHARACTERS-2024-Q1-VERSION-2.0')
      ).toBeInTheDocument();
    });

    it('should handle special characters in contractType', () => {
      const result = {
        ...mockResult,
        contractType: 'GAP & Warranty (Extended)',
      };

      render(<SearchResults result={result} />);
      expect(screen.getByText('GAP & Warranty (Extended)')).toBeInTheDocument();
    });

    it('should handle invalid date strings', () => {
      const result = {
        ...mockResult,
        effectiveDate: 'invalid-date',
        contractDate: 'not-a-date',
      };

      render(<SearchResults result={result} />);

      // Should render "Invalid Date" or handle gracefully
      expect(screen.getByText('Contract Template Found')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(<SearchResults result={mockResult} />);

      const heading = screen.getByRole('heading', { name: /contract template found/i });
      expect(heading).toBeInTheDocument();
    });

    it('should have accessible buttons', () => {
      render(
        <SearchResults
          result={mockResult}
          onViewDetails={vi.fn()}
          onNewSearch={vi.fn()}
        />
      );

      const viewDetailsButton = screen.getByRole('button', { name: /view full details/i });
      const newSearchButton = screen.getByRole('button', { name: /new search/i });

      expect(viewDetailsButton).toBeInTheDocument();
      expect(newSearchButton).toBeInTheDocument();
    });

    it('should render success icon with proper SVG attributes', () => {
      const { container } = render(<SearchResults result={mockResult} />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('viewBox', '0 0 24 24');
    });
  });

  describe('Snapshot', () => {
    it('should match snapshot with full data', () => {
      const { container } = render(
        <SearchResults
          result={mockResult}
          onViewDetails={vi.fn()}
          onNewSearch={vi.fn()}
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('should match snapshot with minimal data', () => {
      const minimalResult: SearchContractResponse = {
        contractId: 'MIN-001',
        contractType: 'Basic',
      };

      const { container } = render(<SearchResults result={minimalResult} />);
      expect(container).toMatchSnapshot();
    });
  });
});
