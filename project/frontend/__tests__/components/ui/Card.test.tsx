import { describe, it, expect } from 'vitest';
import { render, screen } from '@/__tests__/utils/test-utils';
import { Card } from '@/components/ui/Card';

describe('Card Component', () => {
  describe('Rendering', () => {
    it('should render children', () => {
      render(<Card>Card content</Card>);
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      render(<Card className="custom-class">Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('custom-class');
    });

    it('should have default styles', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('bg-white', 'border', 'rounded-lg', 'shadow-sm');
    });
  });

  describe('Padding Variants', () => {
    it('should render with medium padding by default', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('p-6');
    });

    it('should render with no padding', () => {
      render(<Card padding="none">Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('p-0');
    });

    it('should render with small padding', () => {
      render(<Card padding="sm">Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('p-4');
    });

    it('should render with large padding', () => {
      render(<Card padding="lg">Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('p-8');
    });
  });

  describe('Slots', () => {
    it('should render header slot', () => {
      render(
        <Card header={<div>Card Header</div>}>
          Content
        </Card>
      );
      expect(screen.getByText('Card Header')).toBeInTheDocument();
    });

    it('should render footer slot', () => {
      render(
        <Card footer={<div>Card Footer</div>}>
          Content
        </Card>
      );
      expect(screen.getByText('Card Footer')).toBeInTheDocument();
    });

    it('should render both header and footer', () => {
      render(
        <Card
          header={<div>Header</div>}
          footer={<div>Footer</div>}
        >
          Body
        </Card>
      );
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Body')).toBeInTheDocument();
      expect(screen.getByText('Footer')).toBeInTheDocument();
    });

    it('should apply dividers between header, body, and footer', () => {
      const { container } = render(
        <Card
          header={<div>Header</div>}
          footer={<div>Footer</div>}
        >
          Body
        </Card>
      );
      const dividers = container.querySelectorAll('.border-t');
      expect(dividers.length).toBeGreaterThan(0);
    });
  });

  describe('Hover Effect', () => {
    it('should add hover effect when hoverable prop is true', () => {
      render(<Card hoverable>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('hover:shadow-md');
    });

    it('should not have hover effect by default', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).not.toHaveClass('hover:shadow-md');
    });
  });

  describe('Full Width', () => {
    it('should render full width when fullWidth prop is true', () => {
      render(<Card fullWidth>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('w-full');
    });

    it('should not be full width by default', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).not.toHaveClass('w-full');
    });
  });

  describe('Accessibility', () => {
    it('should support aria-label', () => {
      const { container } = render(<Card aria-label="Information card">Content</Card>);
      const card = container.firstChild;
      expect(card).toHaveAttribute('aria-label', 'Information card');
    });

    it('should support custom role', () => {
      const { container } = render(<Card role="article">Content</Card>);
      const card = container.firstChild;
      expect(card).toHaveAttribute('role', 'article');
    });
  });
});
