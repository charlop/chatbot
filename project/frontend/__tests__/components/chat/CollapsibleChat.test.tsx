import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { CollapsibleChat } from '@/components/chat/CollapsibleChat';
import type { ChatMessage } from '@/lib/api/chat';

describe('CollapsibleChat Component', () => {
  const mockMessages: ChatMessage[] = [
    {
      role: 'user',
      content: 'Test question',
      timestamp: '2025-11-16T10:00:00Z',
    },
  ];

  const mockOnSendMessage = vi.fn();
  const defaultProps = {
    messages: mockMessages,
    onSendMessage: mockOnSendMessage,
    contractId: 'contract-123',
    accountNumber: 'ACC-001',
  };

  beforeEach(() => {
    mockOnSendMessage.mockClear();
  });

  describe('Rendering', () => {
    it('should render collapsible chat container', () => {
      render(<CollapsibleChat {...defaultProps} />);
      expect(screen.getByRole('region', { name: /chat/i })).toBeInTheDocument();
    });

    it('should render expand/collapse button', () => {
      render(<CollapsibleChat {...defaultProps} />);
      expect(screen.getByRole('button', { name: /expand|collapse/i })).toBeInTheDocument();
    });

    it('should start in collapsed state by default', () => {
      const { container } = render(<CollapsibleChat {...defaultProps} />);
      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('h-[92px]');
    });

    it('should allow starting in expanded state', () => {
      const { container } = render(
        <CollapsibleChat {...defaultProps} defaultExpanded={true} />
      );
      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('h-[400px]');
    });
  });

  describe('Expand/Collapse Functionality', () => {
    it('should expand when collapse button is clicked', async () => {
      const user = userEvent.setup();
      const { container } = render(<CollapsibleChat {...defaultProps} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('h-[400px]');
    });

    it('should collapse when expand button is clicked', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <CollapsibleChat {...defaultProps} defaultExpanded={true} />
      );

      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('h-[92px]');
    });

    it('should toggle state on multiple clicks', async () => {
      const user = userEvent.setup();
      const { container } = render(<CollapsibleChat {...defaultProps} />);

      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('h-[92px]');

      // Expand
      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);
      expect(chatContainer).toHaveClass('h-[400px]');

      // Collapse
      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);
      expect(chatContainer).toHaveClass('h-[92px]');
    });

    it('should call onExpandChange callback when expanded', async () => {
      const onExpandChange = vi.fn();
      const user = userEvent.setup();

      render(<CollapsibleChat {...defaultProps} onExpandChange={onExpandChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(onExpandChange).toHaveBeenCalledWith(true);
    });

    it('should call onExpandChange callback when collapsed', async () => {
      const onExpandChange = vi.fn();
      const user = userEvent.setup();

      render(
        <CollapsibleChat
          {...defaultProps}
          defaultExpanded={true}
          onExpandChange={onExpandChange}
        />
      );

      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      expect(onExpandChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Message List Visibility', () => {
    it('should hide message list when collapsed', () => {
      render(<CollapsibleChat {...defaultProps} />);
      const messageList = screen.queryByRole('log');
      expect(messageList).not.toBeInTheDocument();
    });

    it('should show message list when expanded', () => {
      render(<CollapsibleChat {...defaultProps} defaultExpanded={true} />);
      const messageList = screen.getByRole('log');
      expect(messageList).toBeVisible();
    });
  });

  describe('Input Preservation', () => {
    it('should preserve input text when collapsing', async () => {
      const user = userEvent.setup();
      render(<CollapsibleChat {...defaultProps} defaultExpanded={true} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'Test message');

      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      expect(input).toHaveValue('Test message');
    });

    it('should preserve input text when expanding', async () => {
      const user = userEvent.setup();
      render(<CollapsibleChat {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'Test message');

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(input).toHaveValue('Test message');
    });
  });

  describe('Smooth Animation', () => {
    it('should have transition classes for animation', () => {
      const { container } = render(<CollapsibleChat {...defaultProps} />);
      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('transition-all');
    });

    it('should have duration specified', () => {
      const { container } = render(<CollapsibleChat {...defaultProps} />);
      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer?.className).toMatch(/duration-/);
    });
  });

  describe('Context Indicator', () => {
    it('should display account number in header', () => {
      render(<CollapsibleChat {...defaultProps} />);
      expect(screen.getByText(/ACC-001/)).toBeInTheDocument();
    });

    it('should display contract ID in header', () => {
      render(<CollapsibleChat {...defaultProps} />);
      expect(screen.getByText(/contract-123/)).toBeInTheDocument();
    });

    it('should show context change indicator when contract changes', () => {
      const { rerender } = render(<CollapsibleChat {...defaultProps} />);

      rerender(
        <CollapsibleChat
          {...defaultProps}
          contractId="contract-456"
          accountNumber="ACC-002"
        />
      );

      // Should show some visual indication of context change
      expect(screen.getByText(/contract-456/)).toBeInTheDocument();
      expect(screen.getByText(/ACC-002/)).toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should support keyboard shortcut to toggle', async () => {
      const user = userEvent.setup();
      const { container } = render(<CollapsibleChat {...defaultProps} />);

      const chatContainer = container.querySelector('[data-testid="collapsible-chat"]');
      expect(chatContainer).toHaveClass('h-[92px]');

      // Press Ctrl+` or Cmd+` to toggle (common chat shortcut)
      await user.keyboard('{Control>}`{/Control}');

      expect(chatContainer).toHaveClass('h-[400px]');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes for collapsed state', () => {
      render(<CollapsibleChat {...defaultProps} />);
      const expandButton = screen.getByRole('button', { name: /expand/i });
      expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should have proper ARIA attributes for expanded state', () => {
      render(<CollapsibleChat {...defaultProps} defaultExpanded={true} />);
      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      expect(collapseButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('should have descriptive aria-label for toggle button', () => {
      render(<CollapsibleChat {...defaultProps} />);
      const button = screen.getByRole('button', { name: /expand chat|collapse chat/i });
      expect(button).toHaveAccessibleName();
    });
  });

  describe('Loading State', () => {
    it('should pass loading state to ChatInterface', () => {
      render(<CollapsibleChat {...defaultProps} isLoading={true} />);
      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      expect(input).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should pass error to ChatInterface', () => {
      render(<CollapsibleChat {...defaultProps} error="Test error" />);
      expect(screen.getByText(/test error/i)).toBeInTheDocument();
    });
  });
});
