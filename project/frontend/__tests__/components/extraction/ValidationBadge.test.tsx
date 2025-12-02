import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ValidationBadge } from '@/components/extraction/ValidationBadge';

describe('ValidationBadge Component', () => {
  describe('Rendering based on status', () => {
    it('should render green badge for pass status', () => {
      render(<ValidationBadge status="pass" reason="All checks passed" />);
      const badge = screen.getByText(/pass/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-green-100', 'text-green-800', 'border-green-200');
    });

    it('should render yellow badge for warning status', () => {
      render(<ValidationBadge status="warning" reason="Statistical outlier detected" />);
      const badge = screen.getByText(/warning/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800', 'border-yellow-200');
    });

    it('should render red badge for fail status', () => {
      render(<ValidationBadge status="fail" reason="Value out of range" />);
      const badge = screen.getByText(/fail/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-red-100', 'text-red-800', 'border-red-200');
    });

    it('should render checkmark icon for pass status', () => {
      render(<ValidationBadge status="pass" reason="All checks passed" />);
      const badge = screen.getByText(/pass/i);
      expect(badge.textContent).toContain('✓');
    });

    it('should render warning icon for warning status', () => {
      render(<ValidationBadge status="warning" reason="Statistical outlier" />);
      const badge = screen.getByText(/warning/i);
      expect(badge.textContent).toContain('⚠');
    });

    it('should render x icon for fail status', () => {
      render(<ValidationBadge status="fail" reason="Out of range" />);
      const badge = screen.getByText(/fail/i);
      expect(badge.textContent).toContain('✗');
    });
  });

  describe('Tooltip functionality', () => {
    it('should display reason as tooltip for pass status', () => {
      render(<ValidationBadge status="pass" reason="GAP premium within valid range" />);
      const badge = screen.getByText(/pass/i);
      expect(badge).toHaveAttribute('title', 'GAP premium within valid range');
    });

    it('should display reason as tooltip for warning status', () => {
      render(<ValidationBadge status="warning" reason="Value is a statistical outlier" />);
      const badge = screen.getByText(/warning/i);
      expect(badge).toHaveAttribute('title', 'Value is a statistical outlier');
    });

    it('should display reason as tooltip for fail status', () => {
      render(<ValidationBadge status="fail" reason="Cancellation fee exceeds premium" />);
      const badge = screen.getByText(/fail/i);
      expect(badge).toHaveAttribute('title', 'Cancellation fee exceeds premium');
    });

    it('should handle undefined reason gracefully', () => {
      render(<ValidationBadge status="pass" />);
      const badge = screen.getByText(/pass/i);
      // Should not crash and title should be undefined or empty
      const title = badge.getAttribute('title');
      expect(title === null || title === undefined).toBe(true);
    });

    it('should handle empty reason string', () => {
      render(<ValidationBadge status="warning" reason="" />);
      const badge = screen.getByText(/warning/i);
      expect(badge).toHaveAttribute('title', '');
    });
  });

  describe('Null status handling', () => {
    it('should render nothing when status is undefined', () => {
      const { container } = render(<ValidationBadge status={undefined} reason="Some reason" />);
      expect(container).toBeEmptyDOMElement();
    });

    it('should render nothing when status is not provided', () => {
      const { container } = render(<ValidationBadge reason="Some reason" />);
      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('Badge styling', () => {
    it('should apply consistent base classes', () => {
      render(<ValidationBadge status="pass" reason="Valid" />);
      const badge = screen.getByText(/pass/i);
      expect(badge).toHaveClass('inline-flex', 'items-center', 'gap-1');
      expect(badge).toHaveClass('px-2', 'py-1', 'rounded-md');
      expect(badge).toHaveClass('text-xs', 'font-medium', 'border');
    });

    it('should have proper spacing for icon and text', () => {
      render(<ValidationBadge status="warning" reason="Outlier" />);
      const badge = screen.getByText(/warning/i);
      expect(badge).toHaveClass('gap-1');
    });
  });

  describe('Badge content', () => {
    it('should display status text for pass', () => {
      render(<ValidationBadge status="pass" reason="Valid" />);
      expect(screen.getByText(/pass/i)).toBeInTheDocument();
    });

    it('should display status text for warning', () => {
      render(<ValidationBadge status="warning" reason="Outlier" />);
      expect(screen.getByText(/warning/i)).toBeInTheDocument();
    });

    it('should display status text for fail', () => {
      render(<ValidationBadge status="fail" reason="Invalid" />);
      expect(screen.getByText(/fail/i)).toBeInTheDocument();
    });

    it('should combine icon and status text', () => {
      render(<ValidationBadge status="pass" reason="Valid" />);
      const badge = screen.getByText(/pass/i);
      expect(badge.textContent).toMatch(/✓\s*pass/i);
    });
  });

  describe('Integration with DataCard', () => {
    it('should render properly when no reason is provided', () => {
      render(<ValidationBadge status="pass" />);
      const badge = screen.getByText(/pass/i);
      expect(badge).toBeInTheDocument();
    });

    it('should handle all three status types in sequence', () => {
      const { rerender } = render(<ValidationBadge status="pass" reason="Valid" />);
      expect(screen.getByText(/pass/i)).toBeInTheDocument();

      rerender(<ValidationBadge status="warning" reason="Outlier" />);
      expect(screen.getByText(/warning/i)).toBeInTheDocument();

      rerender(<ValidationBadge status="fail" reason="Invalid" />);
      expect(screen.getByText(/fail/i)).toBeInTheDocument();
    });
  });

  describe('Visual feedback', () => {
    it('should use distinct colors for each status', () => {
      const { rerender } = render(<ValidationBadge status="pass" reason="Valid" />);
      const passBadge = screen.getByText(/pass/i);
      expect(passBadge).toHaveClass('bg-green-100');

      rerender(<ValidationBadge status="warning" reason="Outlier" />);
      const warningBadge = screen.getByText(/warning/i);
      expect(warningBadge).toHaveClass('bg-yellow-100');

      rerender(<ValidationBadge status="fail" reason="Invalid" />);
      const failBadge = screen.getByText(/fail/i);
      expect(failBadge).toHaveClass('bg-red-100');
    });

    it('should use semantic text colors matching background', () => {
      render(<ValidationBadge status="pass" reason="Valid" />);
      const passBadge = screen.getByText(/pass/i);
      expect(passBadge).toHaveClass('text-green-800');

      const { rerender } = render(<ValidationBadge status="warning" reason="Outlier" />);
      const warningBadge = screen.getByText(/warning/i);
      expect(warningBadge).toHaveClass('text-yellow-800');

      rerender(<ValidationBadge status="fail" reason="Invalid" />);
      const failBadge = screen.getByText(/fail/i);
      expect(failBadge).toHaveClass('text-red-800');
    });

    it('should have border colors matching status', () => {
      render(<ValidationBadge status="pass" reason="Valid" />);
      const passBadge = screen.getByText(/pass/i);
      expect(passBadge).toHaveClass('border-green-200');

      const { rerender } = render(<ValidationBadge status="warning" reason="Outlier" />);
      const warningBadge = screen.getByText(/warning/i);
      expect(warningBadge).toHaveClass('border-yellow-200');

      rerender(<ValidationBadge status="fail" reason="Invalid" />);
      const failBadge = screen.getByText(/fail/i);
      expect(failBadge).toHaveClass('border-red-200');
    });
  });

  describe('Complex validation messages', () => {
    it('should handle long validation messages in tooltip', () => {
      const longMessage =
        'Value $1500.00 is a statistical outlier (avg: $500.00, stddev: $50.00). This significantly deviates from historical patterns.';
      render(<ValidationBadge status="warning" reason={longMessage} />);
      const badge = screen.getByText(/warning/i);
      expect(badge).toHaveAttribute('title', longMessage);
    });

    it('should handle validation messages with special characters', () => {
      const message = 'GAP premium ($2500.00) exceeds maximum range ($100.00-$2000.00)';
      render(<ValidationBadge status="fail" reason={message} />);
      const badge = screen.getByText(/fail/i);
      expect(badge).toHaveAttribute('title', message);
    });

    it('should handle validation messages with line breaks or newlines', () => {
      const message = 'Validation failed:\nValue out of range';
      render(<ValidationBadge status="fail" reason={message} />);
      const badge = screen.getByText(/fail/i);
      expect(badge).toHaveAttribute('title', message);
    });
  });
});
