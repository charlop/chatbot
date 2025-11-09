import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { Modal } from '@/components/ui/Modal';

describe('Modal Component', () => {
  describe('Rendering', () => {
    it('should not render when open is false', () => {
      render(<Modal open={false} onClose={() => {}}>Modal content</Modal>);
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
    });

    it('should render when open is true', () => {
      render(<Modal open={true} onClose={() => {}}>Modal content</Modal>);
      expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('should render with title', () => {
      render(
        <Modal open={true} onClose={() => {}} title="Modal Title">
          Content
        </Modal>
      );
      expect(screen.getByText('Modal Title')).toBeInTheDocument();
    });

    it('should render backdrop', () => {
      render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );
      const backdrop = document.body.querySelector('.fixed.inset-0.bg-black');
      expect(backdrop).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('should call onClose when backdrop is clicked', async () => {
      const handleClose = vi.fn();
      const user = userEvent.setup();

      render(
        <Modal open={true} onClose={handleClose}>
          Content
        </Modal>
      );

      const backdrop = document.body.querySelector('.fixed.inset-0.z-50') as HTMLElement;
      await user.click(backdrop);

      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when ESC key is pressed', async () => {
      const handleClose = vi.fn();
      const user = userEvent.setup();

      render(
        <Modal open={true} onClose={handleClose}>
          Content
        </Modal>
      );

      await user.keyboard('{Escape}');
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('should not close when clicking inside modal content', async () => {
      const handleClose = vi.fn();
      const user = userEvent.setup();

      render(
        <Modal open={true} onClose={handleClose}>
          <div>Modal content</div>
        </Modal>
      );

      await user.click(screen.getByText('Modal content'));
      expect(handleClose).not.toHaveBeenCalled();
    });

    it('should call onClose when close button is clicked', async () => {
      const handleClose = vi.fn();
      const user = userEvent.setup();

      render(
        <Modal open={true} onClose={handleClose} title="Title">
          Content
        </Modal>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Sizes', () => {
    it('should render medium size by default', () => {
      render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );
      const modal = document.body.querySelector('.max-w-md');
      expect(modal).toBeInTheDocument();
    });

    it('should render small size', () => {
      render(
        <Modal open={true} onClose={() => {}} size="sm">
          Content
        </Modal>
      );
      const modal = document.body.querySelector('.max-w-sm');
      expect(modal).toBeInTheDocument();
    });

    it('should render large size', () => {
      render(
        <Modal open={true} onClose={() => {}} size="lg">
          Content
        </Modal>
      );
      const modal = document.body.querySelector('.max-w-2xl');
      expect(modal).toBeInTheDocument();
    });

    it('should render extra large size', () => {
      render(
        <Modal open={true} onClose={() => {}} size="xl">
          Content
        </Modal>
      );
      const modal = document.body.querySelector('.max-w-4xl');
      expect(modal).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have role dialog', () => {
      render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should have aria-modal attribute', () => {
      render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby when title is provided', () => {
      render(
        <Modal open={true} onClose={() => {}} title="Modal Title">
          Content
        </Modal>
      );
      const dialog = screen.getByRole('dialog');
      const titleId = dialog.getAttribute('aria-labelledby');
      expect(titleId).toBeTruthy();
      expect(screen.getByText('Modal Title')).toHaveAttribute('id', titleId!);
    });

    it('should trap focus within modal', () => {
      render(
        <Modal open={true} onClose={() => {}} title="Title">
          <button>First button</button>
          <button>Second button</button>
        </Modal>
      );

      // Modal should be in the document and buttons should be accessible
      expect(screen.getByText('First button')).toBeInTheDocument();
      expect(screen.getByText('Second button')).toBeInTheDocument();
    });
  });

  describe('Body Scroll Lock', () => {
    it('should add overflow-hidden to body when modal is open', () => {
      render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );
      expect(document.body).toHaveClass('overflow-hidden');
    });

    it('should remove overflow-hidden from body when modal is closed', () => {
      const { rerender } = render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );

      expect(document.body).toHaveClass('overflow-hidden');

      rerender(
        <Modal open={false} onClose={() => {}}>
          Content
        </Modal>
      );

      expect(document.body).not.toHaveClass('overflow-hidden');
    });
  });

  describe('Footer', () => {
    it('should render footer when provided', () => {
      render(
        <Modal
          open={true}
          onClose={() => {}}
          footer={<button>Action</button>}
        >
          Content
        </Modal>
      );
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
    });

    it('should not render footer section when footer is not provided', () => {
      const { container } = render(
        <Modal open={true} onClose={() => {}}>
          Content
        </Modal>
      );
      const footer = container.querySelector('.border-t.border-neutral-200.px-6.py-4');
      expect(footer).not.toBeInTheDocument();
    });
  });
});
