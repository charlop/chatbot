import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { Toast, useToast, ToastProvider } from '@/components/ui/Toast';

// Helper component to test the hook
const ToastTester = () => {
  const { toast, success, error, warning, info } = useToast();

  return (
    <div>
      <button onClick={() => toast('Test toast')}>Show Toast</button>
      <button onClick={() => success('Success message')}>Show Success</button>
      <button onClick={() => error('Error message')}>Show Error</button>
      <button onClick={() => warning('Warning message')}>Show Warning</button>
      <button onClick={() => info('Info message')}>Show Info</button>
    </div>
  );
};

describe('Toast Component', () => {
  describe('Toast Display', () => {
    it('should display toast when triggered', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Toast'));

      await waitFor(() => {
        expect(screen.getByText('Test toast')).toBeInTheDocument();
      });
    });

    it('should display success toast with correct styling', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Success'));

      await waitFor(() => {
        const toast = screen.getByText('Success message').closest('div[role="alert"]');
        expect(toast).toHaveClass('bg-success-50');
      });
    });

    it('should display error toast with correct styling', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Error'));

      await waitFor(() => {
        const toast = screen.getByText('Error message').closest('div[role="alert"]');
        expect(toast).toHaveClass('bg-danger-50');
      });
    });

    it('should display warning toast with correct styling', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Warning'));

      await waitFor(() => {
        const toast = screen.getByText('Warning message').closest('div[role="alert"]');
        expect(toast).toHaveClass('bg-warning-50');
      });
    });

    it('should display info toast with correct styling', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Info'));

      await waitFor(() => {
        const toast = screen.getByText('Info message').closest('div[role="alert"]');
        expect(toast).toHaveClass('bg-primary-50');
      });
    });
  });

  describe('Manual Dismiss', () => {
    it('should dismiss when close button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Toast'));

      await waitFor(() => {
        expect(screen.getByText('Test toast')).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Test toast')).not.toBeInTheDocument();
      });
    });
  });

  describe('Toast Queue', () => {
    it('should display multiple toasts', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Success'));
      await user.click(screen.getByText('Show Error'));
      await user.click(screen.getByText('Show Warning'));

      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument();
        expect(screen.getByText('Error message')).toBeInTheDocument();
        expect(screen.getByText('Warning message')).toBeInTheDocument();
      });
    });

    it('should maintain toast order (newest at bottom)', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Success'));
      await user.click(screen.getByText('Show Error'));

      await waitFor(() => {
        const toasts = screen.getAllByRole('alert');
        expect(toasts[0]).toHaveTextContent('Success message');
        expect(toasts[1]).toHaveTextContent('Error message');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have role="alert" for each toast', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Toast'));

      await waitFor(() => {
        const toast = screen.getByText('Test toast').closest('div');
        expect(toast).toHaveAttribute('role', 'alert');
      });
    });

    it('should have aria-live="polite"', async () => {
      const user = userEvent.setup();

      render(
        <ToastProvider>
          <ToastTester />
        </ToastProvider>
      );

      await user.click(screen.getByText('Show Toast'));

      await waitFor(() => {
        const toast = screen.getByText('Test toast').closest('div');
        expect(toast).toHaveAttribute('aria-live', 'polite');
      });
    });
  });
});
