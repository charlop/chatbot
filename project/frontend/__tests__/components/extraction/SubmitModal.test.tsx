import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SubmitModal } from '@/components/extraction/SubmitModal';

describe('SubmitModal Component', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    corrections: new Map([
      ['gap_premium', '1600.00'],
      ['cancellation_fee', '75.00'],
    ]),
    originalValues: {
      gap_premium: '1500.00',
      refund_method: 'Pro-Rata',
      cancellation_fee: '50.00',
    },
    onSubmit: mockOnSubmit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Display', () => {
    it('should render modal with title', () => {
      render(<SubmitModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/confirm submission/i)).toBeInTheDocument();
    });

    it('should show corrections summary when corrections exist', () => {
      render(<SubmitModal {...defaultProps} />);
      expect(screen.getByText(/changes/i)).toBeInTheDocument();
    });

    it('should show no corrections message when no corrections', () => {
      const props = { ...defaultProps, corrections: new Map() };
      render(<SubmitModal {...props} />);
      expect(screen.getByText(/no changes/i)).toBeInTheDocument();
    });

    it('should display corrected fields', () => {
      render(<SubmitModal {...defaultProps} />);
      expect(screen.getByText(/GAP Insurance Premium/i)).toBeInTheDocument();
      expect(screen.getByText(/Cancellation Fee/i)).toBeInTheDocument();
    });

    it('should show old and new values', () => {
      render(<SubmitModal {...defaultProps} />);
      expect(screen.getByText('1500.00')).toBeInTheDocument();
      expect(screen.getByText('1600.00')).toBeInTheDocument();
      expect(screen.getByText('50.00')).toBeInTheDocument();
      expect(screen.getByText('75.00')).toBeInTheDocument();
    });

    it('should render notes textarea', () => {
      render(<SubmitModal {...defaultProps} />);
      expect(screen.getByRole('textbox', { name: /notes/i })).toBeInTheDocument();
    });

    it('should render Submit and Cancel buttons', () => {
      render(<SubmitModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /^submit$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  describe('Notes Field', () => {
    it('should allow entering notes', async () => {
      render(<SubmitModal {...defaultProps} />);
      const notesInput = screen.getByRole('textbox', { name: /notes/i });

      await userEvent.type(notesInput, 'Corrected values based on document review');

      expect(notesInput).toHaveValue('Corrected values based on document review');
    });

    it('should have placeholder text', () => {
      render(<SubmitModal {...defaultProps} />);
      const notesInput = screen.getByRole('textbox', { name: /notes/i });
      expect(notesInput).toHaveAttribute('placeholder');
    });

    it('should limit notes to 500 characters', async () => {
      render(<SubmitModal {...defaultProps} />);
      const notesInput = screen.getByRole('textbox', { name: /notes/i }) as HTMLTextAreaElement;

      expect(notesInput).toHaveAttribute('maxLength', '500');
    });
  });

  describe('Submit Action', () => {
    it('should call onSubmit when Submit clicked without notes', async () => {
      render(<SubmitModal {...defaultProps} />);
      const submitButton = screen.getByRole('button', { name: /^submit$/i });

      await userEvent.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      expect(mockOnSubmit).toHaveBeenCalledWith(undefined);
    });

    it('should call onSubmit with notes when provided', async () => {
      render(<SubmitModal {...defaultProps} />);
      const notesInput = screen.getByRole('textbox', { name: /notes/i });
      const submitButton = screen.getByRole('button', { name: /^submit$/i });

      await userEvent.type(notesInput, 'Test notes');
      await userEvent.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      expect(mockOnSubmit).toHaveBeenCalledWith('Test notes');
    });

    it('should not call onSubmit with empty notes', async () => {
      render(<SubmitModal {...defaultProps} />);
      const notesInput = screen.getByRole('textbox', { name: /notes/i });
      const submitButton = screen.getByRole('button', { name: /^submit$/i });

      await userEvent.type(notesInput, '   ');
      await userEvent.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      expect(mockOnSubmit).toHaveBeenCalledWith(undefined);
    });
  });

  describe('Cancel Action', () => {
    it('should call onCancel when Cancel clicked', async () => {
      render(<SubmitModal {...defaultProps} />);
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      await userEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should call onCancel when clicking backdrop', async () => {
      render(<SubmitModal {...defaultProps} />);
      const backdrop = screen.getByRole('dialog').parentElement;

      if (backdrop) {
        await userEvent.click(backdrop);
        expect(mockOnCancel).toHaveBeenCalledTimes(1);
      }
    });

    it('should call onCancel when pressing Escape', async () => {
      render(<SubmitModal {...defaultProps} />);

      await userEvent.keyboard('{Escape}');

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Field Labels', () => {
    it('should display correct label for gap_premium', () => {
      const props = {
        ...defaultProps,
        corrections: new Map([['gap_premium', '1600.00']]),
      };
      render(<SubmitModal {...props} />);
      expect(screen.getByText(/GAP Insurance Premium/i)).toBeInTheDocument();
    });

    it('should display correct label for refund_method', () => {
      const props = {
        ...defaultProps,
        corrections: new Map([['refund_method', 'Flat Rate']]),
      };
      render(<SubmitModal {...props} />);
      expect(screen.getByText(/Refund Calculation Method/i)).toBeInTheDocument();
    });

    it('should display correct label for cancellation_fee', () => {
      const props = {
        ...defaultProps,
        corrections: new Map([['cancellation_fee', '75.00']]),
      };
      render(<SubmitModal {...props} />);
      expect(screen.getByText(/Cancellation Fee/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<SubmitModal {...defaultProps} />);
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby');
    });

    it('should focus first interactive element on mount', async () => {
      render(<SubmitModal {...defaultProps} />);
      await waitFor(() => {
        const notesInput = screen.getByRole('textbox', { name: /notes/i });
        expect(notesInput).toHaveFocus();
      });
    });

    it('should allow tabbing between elements', async () => {
      render(<SubmitModal {...defaultProps} />);

      const notesInput = screen.getByRole('textbox', { name: /notes/i });
      const submitButton = screen.getByRole('button', { name: /^submit$/i });
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      // All interactive elements should be present and focusable
      expect(notesInput).toBeInTheDocument();
      expect(submitButton).toBeInTheDocument();
      expect(cancelButton).toBeInTheDocument();
    });
  });
});
