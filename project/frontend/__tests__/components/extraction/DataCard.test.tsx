import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DataCard } from '@/components/extraction/DataCard';

describe('DataCard Component', () => {
  const mockOnChange = vi.fn();
  const mockOnViewInDocument = vi.fn();

  const defaultProps = {
    label: 'GAP Insurance Premium',
    value: '1500.00',
    confidence: 95,
    source: 'Page 2, Section 3',
    onChange: mockOnChange,
    onViewInDocument: mockOnViewInDocument,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Display', () => {
    it('should render field label', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.getByText('GAP Insurance Premium')).toBeInTheDocument();
    });

    it('should render field value', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.getByText('1500.00')).toBeInTheDocument();
    });

    it('should render confidence badge', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.getByText('95%')).toBeInTheDocument();
    });

    it('should render source location', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.getByText(/Page 2, Section 3/)).toBeInTheDocument();
    });

    it('should render "View in document" button', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.getByRole('button', { name: /view in document/i })).toBeInTheDocument();
    });
  });

  describe('View in Document', () => {
    it('should call onViewInDocument when button clicked', async () => {
      render(<DataCard {...defaultProps} />);
      const button = screen.getByRole('button', { name: /view in document/i });

      await userEvent.click(button);

      expect(mockOnViewInDocument).toHaveBeenCalledTimes(1);
    });

    it('should not render button when onViewInDocument is not provided', () => {
      const props = { ...defaultProps, onViewInDocument: undefined };
      render(<DataCard {...props} />);

      expect(screen.queryByRole('button', { name: /view in document/i })).not.toBeInTheDocument();
    });
  });

  describe('Inline Editing', () => {
    it('should show view mode by default', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.getByText('1500.00')).toBeInTheDocument();
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('should enter edit mode when value is clicked', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue('1500.00');
      expect(input).toHaveFocus();
    });

    it('should update value when typing', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);
      const input = screen.getByRole('textbox');

      await userEvent.clear(input);
      await userEvent.type(input, '1600.00');

      expect(input).toHaveValue('1600.00');
    });

    it('should save value on Enter key', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);
      const input = screen.getByRole('textbox');

      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Enter}');

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith('1600.00');
      });
    });

    it('should save value on blur', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);
      const input = screen.getByRole('textbox');

      await userEvent.clear(input);
      await userEvent.type(input, '1600.00');

      fireEvent.blur(input);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith('1600.00');
      });
    });

    it('should cancel edit on Escape key', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);
      const input = screen.getByRole('textbox');

      await userEvent.clear(input);
      await userEvent.type(input, '1600.00{Escape}');

      await waitFor(() => {
        expect(screen.getByText('1500.00')).toBeInTheDocument();
        expect(mockOnChange).not.toHaveBeenCalled();
      });
    });

    it('should not call onChange if value unchanged', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);
      const input = screen.getByRole('textbox');

      fireEvent.blur(input);

      await waitFor(() => {
        expect(mockOnChange).not.toHaveBeenCalled();
      });
    });
  });

  describe('Edited State', () => {
    it('should show edited indicator when isEdited is true', () => {
      render(<DataCard {...defaultProps} isEdited={true} />);
      expect(screen.getByText(/edited/i)).toBeInTheDocument();
    });

    it('should not show edited indicator by default', () => {
      render(<DataCard {...defaultProps} />);
      expect(screen.queryByText(/edited/i)).not.toBeInTheDocument();
    });

    it('should show edited indicator with custom icon', () => {
      render(<DataCard {...defaultProps} isEdited={true} />);
      const indicator = screen.getByText(/edited/i);
      expect(indicator).toHaveClass('text-primary');
    });
  });

  describe('Disabled State', () => {
    it('should not enter edit mode when disabled', async () => {
      render(<DataCard {...defaultProps} disabled={true} />);
      const valueElement = screen.getByText('1500.00');

      await userEvent.click(valueElement);

      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('should gray out value when disabled', () => {
      render(<DataCard {...defaultProps} disabled={true} />);
      const valueElement = screen.getByText('1500.00');
      expect(valueElement).toHaveClass('text-neutral-400');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');
      expect(valueElement).toHaveAttribute('role', 'button');
      expect(valueElement).toHaveAttribute('aria-label');
    });

    it('should be keyboard accessible', () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');
      expect(valueElement).toHaveAttribute('tabIndex', '0');
    });

    it('should support keyboard navigation in edit mode', async () => {
      render(<DataCard {...defaultProps} />);
      const valueElement = screen.getByText('1500.00');

      valueElement.focus();
      await userEvent.keyboard('{Enter}');

      const input = screen.getByRole('textbox');
      expect(input).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty value', () => {
      render(<DataCard {...defaultProps} value="" />);
      expect(screen.getByText(/no value/i)).toBeInTheDocument();
    });

    it('should handle undefined confidence', () => {
      render(<DataCard {...defaultProps} confidence={undefined} />);
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('should handle missing source', () => {
      render(<DataCard {...defaultProps} source={undefined} />);
      expect(screen.queryByText(/page/i)).not.toBeInTheDocument();
    });

    it('should handle very long values', () => {
      const longValue = 'A'.repeat(200);
      render(<DataCard {...defaultProps} value={longValue} />);
      expect(screen.getByText(longValue)).toBeInTheDocument();
    });
  });
});
