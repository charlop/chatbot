import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceBadge } from '@/components/extraction/ConfidenceBadge';

describe('ConfidenceBadge Component', () => {
  describe('Color Logic', () => {
    it('should display green badge for confidence >= 90%', () => {
      render(<ConfidenceBadge confidence={95} />);
      const badge = screen.getByText('95%');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-success-light');
    });

    it('should display green badge for confidence exactly 90%', () => {
      render(<ConfidenceBadge confidence={90} />);
      const badge = screen.getByText('90%');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-success-light');
    });

    it('should display orange badge for confidence between 70-89%', () => {
      render(<ConfidenceBadge confidence={85} />);
      const badge = screen.getByText('85%');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-warning-light');
    });

    it('should display orange badge for confidence exactly 70%', () => {
      render(<ConfidenceBadge confidence={70} />);
      const badge = screen.getByText('70%');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-warning-light');
    });

    it('should display red badge for confidence < 70%', () => {
      render(<ConfidenceBadge confidence={65} />);
      const badge = screen.getByText('65%');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-danger-light');
    });

    it('should display red badge for very low confidence', () => {
      render(<ConfidenceBadge confidence={30} />);
      const badge = screen.getByText('30%');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-danger-light');
    });
  });

  describe('Display', () => {
    it('should format confidence as percentage with no decimals', () => {
      render(<ConfidenceBadge confidence={92.5} />);
      expect(screen.getByText('93%')).toBeInTheDocument();
    });

    it('should handle whole numbers correctly', () => {
      render(<ConfidenceBadge confidence={88} />);
      expect(screen.getByText('88%')).toBeInTheDocument();
    });

    it('should round confidence values correctly', () => {
      render(<ConfidenceBadge confidence={89.4} />);
      expect(screen.getByText('89%')).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('should display tooltip with explanation for high confidence', () => {
      render(<ConfidenceBadge confidence={95} />);
      const badge = screen.getByText('95%');
      expect(badge).toHaveAttribute('title');
      expect(badge.getAttribute('title')).toContain('High confidence');
    });

    it('should display tooltip with explanation for medium confidence', () => {
      render(<ConfidenceBadge confidence={80} />);
      const badge = screen.getByText('80%');
      expect(badge).toHaveAttribute('title');
      expect(badge.getAttribute('title')).toContain('Medium confidence');
    });

    it('should display tooltip with explanation for low confidence', () => {
      render(<ConfidenceBadge confidence={50} />);
      const badge = screen.getByText('50%');
      expect(badge).toHaveAttribute('title');
      expect(badge.getAttribute('title')).toContain('Low confidence');
    });
  });

  describe('Edge Cases', () => {
    it('should handle 0% confidence', () => {
      render(<ConfidenceBadge confidence={0} />);
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle 100% confidence', () => {
      render(<ConfidenceBadge confidence={100} />);
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should handle undefined confidence', () => {
      render(<ConfidenceBadge confidence={undefined} />);
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<ConfidenceBadge confidence={85} />);
      const badge = screen.getByText('85%');
      expect(badge).toHaveAttribute('role', 'status');
      expect(badge).toHaveAttribute('aria-label');
    });

    it('should be keyboard accessible', () => {
      render(<ConfidenceBadge confidence={85} />);
      const badge = screen.getByText('85%');
      expect(badge).toHaveAttribute('tabIndex', '0');
    });
  });
});
