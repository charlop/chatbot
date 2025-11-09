import { describe, it, expect } from 'vitest';
import { render, screen } from '@/__tests__/utils/test-utils';
import { Layout } from '@/components/layout/Layout';

describe('Layout Component', () => {
  describe('Structure', () => {
    it('should render layout container', () => {
      render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const content = screen.getByText('Test Content');
      expect(content).toBeInTheDocument();
    });

    it('should render sidebar', () => {
      render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const sidebar = screen.getByRole('navigation');
      expect(sidebar).toBeInTheDocument();
    });

    it('should render header', () => {
      render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();
    });

    it('should render main content area', () => {
      render(
        <Layout>
          <div data-testid="main-content">Test Content</div>
        </Layout>
      );

      const mainContent = screen.getByTestId('main-content');
      expect(mainContent).toBeInTheDocument();
    });
  });

  describe('Layout Spacing', () => {
    it('should have flex layout', () => {
      const { container } = render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const layoutContainer = container.firstChild as HTMLElement;
      expect(layoutContainer).toHaveClass('flex');
    });

    it('should have full height', () => {
      const { container } = render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const layoutContainer = container.firstChild as HTMLElement;
      expect(layoutContainer).toHaveClass('h-screen');
    });

    it('should have proper background color', () => {
      const { container } = render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const layoutContainer = container.firstChild as HTMLElement;
      expect(layoutContainer).toHaveClass('bg-neutral-50');
    });
  });

  describe('Content Rendering', () => {
    it('should render children in main content area', () => {
      render(
        <Layout>
          <div>Child Component 1</div>
          <div>Child Component 2</div>
        </Layout>
      );

      expect(screen.getByText('Child Component 1')).toBeInTheDocument();
      expect(screen.getByText('Child Component 2')).toBeInTheDocument();
    });

    it('should render multiple children correctly', () => {
      const { container } = render(
        <Layout>
          <div>First</div>
          <div>Second</div>
          <div>Third</div>
        </Layout>
      );

      const mainContent = container.querySelector('main');
      expect(mainContent?.children).toHaveLength(3);
    });
  });

  describe('Props', () => {
    it('should pass title prop to header', () => {
      render(
        <Layout title="Custom Title">
          <div>Test Content</div>
        </Layout>
      );

      expect(screen.getByText('Custom Title')).toBeInTheDocument();
    });

    it('should use default title when not provided', () => {
      render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const heading = screen.getByRole('heading');
      expect(heading).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('should maintain sidebar width', () => {
      const { container } = render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const sidebar = container.querySelector('aside');
      expect(sidebar).toHaveClass('w-16');
    });

    it('should allow main content to flex', () => {
      const { container } = render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      const mainArea = container.querySelector('div.flex-1');
      expect(mainArea).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper semantic HTML structure', () => {
      render(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );

      // Should have navigation (sidebar)
      expect(screen.getByRole('navigation')).toBeInTheDocument();

      // Should have banner (header)
      expect(screen.getByRole('banner')).toBeInTheDocument();

      // Should have main
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });
});
