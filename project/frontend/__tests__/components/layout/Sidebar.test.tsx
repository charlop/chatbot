import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/__tests__/utils/test-utils';
import { Sidebar } from '@/components/layout/Sidebar';

// Mock next/navigation
const mockPush = vi.fn();
const mockPathname = '/dashboard';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => mockPathname,
}));

describe('Sidebar Component', () => {
  describe('Layout and Structure', () => {
    it('should render sidebar with correct width', () => {
      const { container } = render(<Sidebar />);
      const sidebar = container.firstChild as HTMLElement;

      expect(sidebar).toHaveClass('w-16'); // 64px in Tailwind (w-16)
    });

    it('should have vertical layout', () => {
      const { container } = render(<Sidebar />);
      const sidebar = container.firstChild as HTMLElement;

      expect(sidebar).toHaveClass('flex', 'flex-col');
    });

    it('should have full height', () => {
      const { container } = render(<Sidebar />);
      const sidebar = container.firstChild as HTMLElement;

      expect(sidebar).toHaveClass('h-screen');
    });

    it('should have background color', () => {
      const { container } = render(<Sidebar />);
      const sidebar = container.firstChild as HTMLElement;

      expect(sidebar).toHaveClass('bg-neutral-900');
    });
  });

  describe('Navigation Items', () => {
    it('should render dashboard navigation link', () => {
      render(<Sidebar />);

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      expect(dashboardLink).toBeInTheDocument();
    });

    it('should render admin navigation link', () => {
      render(<Sidebar />);

      const adminLink = screen.getByRole('link', { name: /admin/i });
      expect(adminLink).toBeInTheDocument();
    });

    it('should have correct hrefs for navigation links', () => {
      render(<Sidebar />);

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      const adminLink = screen.getByRole('link', { name: /admin/i });

      expect(dashboardLink).toHaveAttribute('href', '/dashboard');
      expect(adminLink).toHaveAttribute('href', '/admin');
    });
  });

  describe('Active State', () => {
    it('should highlight active navigation item', () => {
      render(<Sidebar />);

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });

      // Should have active styling when on dashboard route
      expect(dashboardLink).toHaveClass('bg-primary-500');
    });
  });

  describe('User Profile Section', () => {
    it('should render user profile section at bottom', () => {
      render(<Sidebar />);

      const profileSection = screen.getByTestId('user-profile-section');
      expect(profileSection).toBeInTheDocument();
    });

    it('should display user avatar or initials', () => {
      render(<Sidebar />);

      // Look for avatar or user initials
      const avatar = screen.getByTestId('user-avatar');
      expect(avatar).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have navigation landmark', () => {
      render(<Sidebar />);

      const nav = screen.getByRole('navigation');
      expect(nav).toBeInTheDocument();
    });

    it('should have accessible labels for icon-only links', () => {
      render(<Sidebar />);

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      const adminLink = screen.getByRole('link', { name: /admin/i });

      expect(dashboardLink).toHaveAccessibleName();
      expect(adminLink).toHaveAccessibleName();
    });

    it('should support keyboard navigation', () => {
      render(<Sidebar />);

      const links = screen.getAllByRole('link');

      links.forEach(link => {
        expect(link).not.toHaveAttribute('tabIndex', '-1');
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should maintain fixed width on different screen sizes', () => {
      const { container } = render(<Sidebar />);
      const sidebar = container.firstChild as HTMLElement;

      // Should have fixed width class (not responsive)
      expect(sidebar).toHaveClass('w-16');
    });
  });

  describe('Styling', () => {
    it('should have proper spacing between navigation items', () => {
      render(<Sidebar />);

      const nav = screen.getByRole('navigation');

      expect(nav).toHaveClass('space-y-2');
    });

    it('should have transition effects on navigation links', () => {
      render(<Sidebar />);

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });

      // Check for transition classes which indicate hover effects are implemented
      expect(dashboardLink).toHaveClass('transition-all');
    });
  });
});
