import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/components/chat/ChatInterface';
import type { ChatMessage } from '@/lib/api/chat';

describe('ChatInterface Component', () => {
  const mockMessages: ChatMessage[] = [
    {
      role: 'user',
      content: 'What is the GAP premium?',
      timestamp: '2025-11-16T10:00:00Z',
    },
    {
      role: 'assistant',
      content: 'The GAP Insurance Premium is $1,250.00',
      timestamp: '2025-11-16T10:00:05Z',
    },
  ];

  const mockOnSendMessage = vi.fn();
  const defaultProps = {
    messages: mockMessages,
    onSendMessage: mockOnSendMessage,
    contractId: 'test-contract-123',
  };

  beforeEach(() => {
    mockOnSendMessage.mockClear();
  });

  describe('Rendering', () => {
    it('should render chat interface', () => {
      render(<ChatInterface {...defaultProps} />);
      expect(screen.getByRole('region', { name: /chat/i })).toBeInTheDocument();
    });

    it('should render all messages', () => {
      render(<ChatInterface {...defaultProps} />);
      expect(screen.getByText('What is the GAP premium?')).toBeInTheDocument();
      expect(screen.getByText('The GAP Insurance Premium is $1,250.00')).toBeInTheDocument();
    });

    it('should render empty state when no messages', () => {
      render(<ChatInterface {...defaultProps} messages={[]} />);
      expect(screen.getByText(/no messages yet|start a conversation/i)).toBeInTheDocument();
    });

    it('should render input box', () => {
      render(<ChatInterface {...defaultProps} />);
      expect(screen.getByPlaceholderText(/ask a question|type a message/i)).toBeInTheDocument();
    });

    it('should render send button', () => {
      render(<ChatInterface {...defaultProps} />);
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });
  });

  describe('Message Input', () => {
    it('should allow typing in input field', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'New message');

      expect(input).toHaveValue('New message');
    });

    it('should clear input after sending message', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'Test message');
      await user.click(screen.getByRole('button', { name: /send/i }));

      expect(input).toHaveValue('');
    });

    it('should not send empty messages', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      expect(mockOnSendMessage).not.toHaveBeenCalled();
    });

    it('should not send whitespace-only messages', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, '   ');
      await user.click(screen.getByRole('button', { name: /send/i }));

      expect(mockOnSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('Sending Messages', () => {
    it('should call onSendMessage when send button clicked', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'New question');
      await user.click(screen.getByRole('button', { name: /send/i }));

      expect(mockOnSendMessage).toHaveBeenCalledWith('New question');
    });

    it('should send message when Enter key is pressed', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'New question{Enter}');

      expect(mockOnSendMessage).toHaveBeenCalledWith('New question');
    });

    it('should not send message when Shift+Enter is pressed', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

      expect(mockOnSendMessage).not.toHaveBeenCalled();
      // Input should contain newline
      expect(input).toHaveValue('Line 1\nLine 2');
    });
  });

  describe('Loading State', () => {
    it('should disable input when loading', () => {
      render(<ChatInterface {...defaultProps} isLoading={true} />);
      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      expect(input).toBeDisabled();
    });

    it('should disable send button when loading', () => {
      render(<ChatInterface {...defaultProps} isLoading={true} />);
      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it('should show loading indicator in assistant message', () => {
      const messagesWithLoading: ChatMessage[] = [
        ...mockMessages,
        {
          role: 'assistant',
          content: '',
        },
      ];
      render(
        <ChatInterface
          {...defaultProps}
          messages={messagesWithLoading}
          isLoading={true}
        />
      );
      expect(screen.getByLabelText(/thinking|loading/i)).toBeInTheDocument();
    });
  });

  describe('Auto-scroll', () => {
    it('should scroll to bottom when new messages arrive', async () => {
      const scrollIntoViewMock = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoViewMock;

      const { rerender } = render(<ChatInterface {...defaultProps} />);

      const newMessages: ChatMessage[] = [
        ...mockMessages,
        {
          role: 'user',
          content: 'Another question',
          timestamp: '2025-11-16T10:01:00Z',
        },
      ];

      rerender(<ChatInterface {...defaultProps} messages={newMessages} />);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled();
      });
    });
  });

  describe('Message List', () => {
    it('should render messages in scrollable container', () => {
      render(<ChatInterface {...defaultProps} />);
      const messageList = screen.getByRole('log');
      expect(messageList).toHaveClass('overflow-y-auto');
    });

    it('should maintain message order', () => {
      render(<ChatInterface {...defaultProps} />);
      const messages = screen.getAllByRole('article');
      expect(messages).toHaveLength(2);
      // First message should be user
      expect(messages[0]).toHaveAttribute('aria-label', expect.stringMatching(/user/i));
      // Second message should be assistant
      expect(messages[1]).toHaveAttribute('aria-label', expect.stringMatching(/assistant/i));
    });
  });

  describe('Contract Context', () => {
    it('should display contract ID indicator', () => {
      render(<ChatInterface {...defaultProps} />);
      expect(screen.getByText(/test-contract-123/i)).toBeInTheDocument();
    });

    it('should update when contract ID changes', () => {
      const { rerender } = render(<ChatInterface {...defaultProps} />);
      expect(screen.getByText(/test-contract-123/i)).toBeInTheDocument();

      rerender(<ChatInterface {...defaultProps} contractId="new-contract-456" />);
      expect(screen.getByText(/new-contract-456/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when provided', () => {
      render(
        <ChatInterface
          {...defaultProps}
          error="Failed to send message"
        />
      );
      expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
    });

    it('should clear error when sending new message', async () => {
      const user = userEvent.setup();
      const { rerender } = render(
        <ChatInterface
          {...defaultProps}
          error="Previous error"
        />
      );
      expect(screen.getByText(/previous error/i)).toBeInTheDocument();

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      await user.type(input, 'New message');

      // Simulate error being cleared by parent
      rerender(<ChatInterface {...defaultProps} error={undefined} />);

      expect(screen.queryByText(/previous error/i)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ChatInterface {...defaultProps} />);
      expect(screen.getByRole('region', { name: /chat/i })).toBeInTheDocument();
      expect(screen.getByRole('log')).toBeInTheDocument();
    });

    it('should have accessible input field', () => {
      render(<ChatInterface {...defaultProps} />);
      const input = screen.getByPlaceholderText(/ask a question|type a message/i);
      expect(input).toHaveAccessibleName();
    });

    it('should have accessible send button', () => {
      render(<ChatInterface {...defaultProps} />);
      const button = screen.getByRole('button', { name: /send/i });
      expect(button).toHaveAccessibleName();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const input = screen.getByPlaceholderText(/ask a question|type a message/i);

      // Tab to input
      await user.tab();
      expect(input).toHaveFocus();

      // Type something to enable send button
      await user.type(input, 'Test');

      // Now tab to send button (which is now enabled)
      await user.tab();
      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toHaveFocus();
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom className', () => {
      render(<ChatInterface {...defaultProps} className="custom-chat-class" />);
      const chatRegion = screen.getByRole('region', { name: /chat/i });
      expect(chatRegion).toHaveClass('custom-chat-class');
    });
  });
});
