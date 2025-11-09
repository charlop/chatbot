import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/__tests__/utils/test-utils';
import { Header } from '@/components/layout/Header';

describe('Header Component', () => {
  describe('Layout and Structure', () => {
    it('should render header element', () => {
      render(<Header />);

      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();
    });

    it('should have flex layout for horizontal arrangement', () => {
      const { container } = render(<Header />);
      const header = container.querySelector('header');

      expect(header).toHaveClass('flex');
    });

    it('should have proper height', () => {
      const { container } = render(<Header />);
      const header = container.querySelector('header');

      expect(header).toHaveClass('h-16');
    });

    it('should have background color', () => {
      const { container } = render(<Header />);
      const header = container.querySelector('header');

      expect(header).toHaveClass('bg-white');
    });
  });

  describe('Page Title', () => {
    it('should display current page title', () => {
      render(<Header title="Dashboard" />);

      const title = screen.getByText('Dashboard');
      expect(title).toBeInTheDocument();
    });

    it('should have default title when not provided', () => {
      render(<Header />);

      const title = screen.getByRole('heading');
      expect(title).toBeInTheDocument();
    });
  });

  describe('User Menu', () => {
    it('should render user menu button', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      expect(userMenuButton).toBeInTheDocument();
    });

    it('should open menu dropdown when clicked', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      // Menu should be visible
      const menu = screen.getByRole('menu');
      expect(menu).toBeInTheDocument();
    });

    it('should display profile menu item', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      const profileItem = screen.getByRole('menuitem', { name: /profile/i });
      expect(profileItem).toBeInTheDocument();
    });

    it('should display settings menu item', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      const settingsItem = screen.getByRole('menuitem', { name: /settings/i });
      expect(settingsItem).toBeInTheDocument();
    });

    it('should display logout menu item', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      const logoutItem = screen.getByRole('menuitem', { name: /logout/i });
      expect(logoutItem).toBeInTheDocument();
    });

    it('should close menu when clicking outside', async () => {
      const { container } = render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      // Menu should be open
      expect(screen.getByRole('menu')).toBeInTheDocument();

      // Click outside - need to fire on document for mousedown event
      fireEvent.mouseDown(document.body);

      // Menu should be closed after state update
      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes for user menu', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });

      expect(userMenuButton).toHaveAttribute('aria-haspopup', 'true');
      expect(userMenuButton).toHaveAttribute('aria-expanded');
    });

    it('should support keyboard navigation in menu', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      const menuItems = screen.getAllByRole('menuitem');

      menuItems.forEach(item => {
        expect(item).not.toHaveAttribute('tabIndex', '-1');
      });
    });

    it('should close menu on Escape key', () => {
      render(<Header />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      // Menu should be open
      expect(screen.getByRole('menu')).toBeInTheDocument();

      // Press Escape
      fireEvent.keyDown(userMenuButton, { key: 'Escape', code: 'Escape' });

      // Menu should be closed
      expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('should be full width', () => {
      const { container } = render(<Header />);
      const header = container.querySelector('header');

      expect(header).toHaveClass('w-full');
    });
  });

  describe('Visual Styling', () => {
    it('should have border bottom', () => {
      const { container } = render(<Header />);
      const header = container.querySelector('header');

      expect(header).toHaveClass('border-b');
    });

    it('should have proper padding', () => {
      const { container } = render(<Header />);
      const header = container.querySelector('header');

      expect(header).toHaveClass('px-6');
    });
  });

  describe('User Menu Actions', () => {
    it('should call logout handler when logout is clicked', () => {
      const onLogout = vi.fn();
      render(<Header onLogout={onLogout} />);

      const userMenuButton = screen.getByRole('button', { name: /user menu/i });
      fireEvent.click(userMenuButton);

      const logoutItem = screen.getByRole('menuitem', { name: /logout/i });
      fireEvent.click(logoutItem);

      expect(onLogout).toHaveBeenCalledTimes(1);
    });
  });
});
