import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DataPanel } from '@/components/extraction/DataPanel';
import type { Extraction } from '@/lib/api/extractions';

describe('DataPanel Component', () => {
  const mockOnSubmit = vi.fn();
  const mockOnViewInDocument = vi.fn();

  const mockExtraction: Extraction = {
    id: 'EXT123',
    contractId: 'C123456',
    gap_premium: 1500.00,
    gap_premium_confidence: 95,
    gap_premium_source: 'Page 2, Section 3',
    refund_method: 'Pro-Rata',
    refund_method_confidence: 85,
    refund_method_source: 'Page 3, Section 1',
    cancellation_fee: 50.00,
    cancellation_fee_confidence: 70,
    cancellation_fee_source: 'Page 1, Section 5',
    status: 'pending',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Display', () => {
    it('should render all three data cards', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      expect(screen.getByText('GAP Insurance Premium')).toBeInTheDocument();
      expect(screen.getByText('Refund Calculation Method')).toBeInTheDocument();
      expect(screen.getByText('Cancellation Fee')).toBeInTheDocument();
    });

    it('should render Submit button', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
    });

    it('should have 464px width', () => {
      const { container } = render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      const panel = container.firstChild as HTMLElement;
      expect(panel).toHaveClass('w-[464px]');
    });

    it('should be scrollable', () => {
      const { container } = render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      const panel = container.firstChild as HTMLElement;
      expect(panel).toHaveClass('overflow-y-auto');
    });

    it('should display field values correctly', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      expect(screen.getByText('1500.00')).toBeInTheDocument();
      expect(screen.getByText('Pro-Rata')).toBeInTheDocument();
      expect(screen.getByText('50.00')).toBeInTheDocument();
    });

    it('should display confidence badges', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('70%')).toBeInTheDocument();
    });

    it('should display source locations', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      expect(screen.getByText(/Page 2, Section 3/)).toBeInTheDocument();
      expect(screen.getByText(/Page 3, Section 1/)).toBeInTheDocument();
      expect(screen.getByText(/Page 1, Section 5/)).toBeInTheDocument();
    });
  });

  describe('Field Editing', () => {
    it('should track corrections when field is edited', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      // Click on GAP premium value to edit
      const premiumValue = screen.getByText('1500.00');
      await userEvent.click(premiumValue);

      // Change value
      const input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        // Check edited indicator appears
        expect(screen.getByText(/edited/i)).toBeInTheDocument();
      });
    });

    it('should track multiple corrections', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      // Edit GAP premium
      const premiumValue = screen.getByText('1500.00');
      await userEvent.click(premiumValue);
      let input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText('1600.00')).toBeInTheDocument();
      });

      // Edit cancellation fee
      const feeValue = screen.getByText('50.00');
      await userEvent.click(feeValue);
      input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '75.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText('75.00')).toBeInTheDocument();
        // Both should show edited indicator
        const editedIndicators = screen.getAllByText(/edited/i);
        expect(editedIndicators).toHaveLength(2);
      });
    });

    it('should remove correction if field reverted to original value', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      // Edit value
      const premiumValue = screen.getByText('1500.00');
      await userEvent.click(premiumValue);
      let input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText('1600.00')).toBeInTheDocument();
      });

      // Revert to original
      const editedValue = screen.getByText('1600.00');
      await userEvent.click(editedValue);
      input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1500.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText('1500.00')).toBeInTheDocument();
        expect(screen.queryByText(/edited/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Submit Button', () => {
    it('should be enabled when there are no corrections', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).not.toBeDisabled();
    });

    it('should be enabled when there are corrections', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      // Make a correction
      const premiumValue = screen.getByText('1500.00');
      await userEvent.click(premiumValue);
      const input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /submit/i });
        expect(submitButton).not.toBeDisabled();
      });
    });

    it('should show corrections count when corrections exist', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      // Make a correction
      const premiumValue = screen.getByText('1500.00');
      await userEvent.click(premiumValue);
      const input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/1 correction/i)).toBeInTheDocument();
      });
    });

    it('should show plural corrections count', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      // Make two corrections
      const premiumValue = screen.getByText('1500.00');
      await userEvent.click(premiumValue);
      let input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText('1600.00')).toBeInTheDocument();
      });

      const feeValue = screen.getByText('50.00');
      await userEvent.click(feeValue);
      input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, '75.00{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/2 corrections/i)).toBeInTheDocument();
      });
    });

    it('should open modal when submit is clicked', async () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });
  });

  describe('View in Document', () => {
    it('should call onViewInDocument with correct source', async () => {
      render(
        <DataPanel
          extraction={mockExtraction}
          onSubmit={mockOnSubmit}
          onViewInDocument={mockOnViewInDocument}
        />
      );

      // Click "View in document" for GAP premium
      const viewButtons = screen.getAllByText(/view in document/i);
      await userEvent.click(viewButtons[0]);

      expect(mockOnViewInDocument).toHaveBeenCalledWith('Page 2, Section 3');
    });

    it('should not show view buttons when onViewInDocument not provided', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);

      expect(screen.queryByText(/view in document/i)).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable editing when status is approved', () => {
      const approvedExtraction = { ...mockExtraction, status: 'approved' as const };
      render(<DataPanel extraction={approvedExtraction} onSubmit={mockOnSubmit} />);

      const premiumValue = screen.getByText('1500.00');
      expect(premiumValue).toHaveClass('cursor-not-allowed');
    });

    it('should disable submit button when status is approved', () => {
      const approvedExtraction = { ...mockExtraction, status: 'approved' as const };
      render(<DataPanel extraction={approvedExtraction} onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toHaveAttribute('aria-label');
    });

    it('should be keyboard navigable', () => {
      render(<DataPanel extraction={mockExtraction} onSubmit={mockOnSubmit} />);
      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toHaveAttribute('type', 'button');
    });
  });
});
