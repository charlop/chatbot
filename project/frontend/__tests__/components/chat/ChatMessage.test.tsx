import { describe, it, expect } from 'vitest';
import { render, screen } from '@/__tests__/utils/test-utils';
import { ChatMessage } from '@/components/chat/ChatMessage';

describe('ChatMessage Component', () => {
  describe('Rendering', () => {
    it('should render user message with content', () => {
      render(
        <ChatMessage
          role="user"
          content="What is the cancellation fee?"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      expect(screen.getByText('What is the cancellation fee?')).toBeInTheDocument();
    });

    it('should render assistant message with content', () => {
      render(
        <ChatMessage
          role="assistant"
          content="The cancellation fee is $50.00"
          timestamp="2025-11-16T10:31:00Z"
        />
      );
      expect(screen.getByText('The cancellation fee is $50.00')).toBeInTheDocument();
    });
  });

  describe('Role Styling', () => {
    it('should apply user-specific styling for user messages', () => {
      render(
        <ChatMessage
          role="user"
          content="User message"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      const article = screen.getByRole('article');
      expect(article).toHaveClass('justify-end');
      // Check for the inner div with ml-auto class
      const container = article.querySelector('.ml-auto');
      expect(container).toBeInTheDocument();
    });

    it('should apply assistant-specific styling for assistant messages', () => {
      render(
        <ChatMessage
          role="assistant"
          content="Assistant message"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      const article = screen.getByRole('article');
      expect(article).toHaveClass('justify-start');
      // Check for the inner div with mr-auto class
      const container = article.querySelector('.mr-auto');
      expect(container).toBeInTheDocument();
    });

    it('should use purple background for user messages', () => {
      render(
        <ChatMessage
          role="user"
          content="User message"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      const messageBubble = screen.getByText('User message').closest('div');
      expect(messageBubble?.className).toMatch(/bg-\[#954293\]/);
    });

    it('should use gray background for assistant messages', () => {
      render(
        <ChatMessage
          role="assistant"
          content="Assistant message"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      const messageBubble = screen.getByText('Assistant message').closest('div');
      expect(messageBubble?.className).toMatch(/bg-neutral-100/);
    });
  });

  describe('Timestamp Display', () => {
    it('should display timestamp when provided', () => {
      render(
        <ChatMessage
          role="user"
          content="Message with timestamp"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      // Timestamp should be formatted in HH:MM format (will be in local timezone)
      const timeElement = screen.getByText(/\d{2}:\d{2}/);
      expect(timeElement).toBeInTheDocument();
    });

    it('should not display timestamp when not provided', () => {
      const { container } = render(
        <ChatMessage
          role="user"
          content="Message without timestamp"
        />
      );
      // Should not contain time element
      expect(container.querySelector('time')).not.toBeInTheDocument();
    });

    it('should format timestamp in HH:MM format', () => {
      render(
        <ChatMessage
          role="user"
          content="Message"
          timestamp="2025-11-16T14:45:30Z"
        />
      );
      // Check that it matches HH:MM pattern
      const timeElement = screen.getByText(/^\d{2}:\d{2}$/);
      expect(timeElement).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should display loading indicator when isLoading is true', () => {
      render(
        <ChatMessage
          role="assistant"
          content=""
          isLoading={true}
        />
      );
      expect(screen.getByLabelText(/thinking|loading/i)).toBeInTheDocument();
    });

    it('should not display content when loading', () => {
      render(
        <ChatMessage
          role="assistant"
          content="This should not appear"
          isLoading={true}
        />
      );
      expect(screen.queryByText('This should not appear')).not.toBeInTheDocument();
    });

    it('should display loading animation', () => {
      render(
        <ChatMessage
          role="assistant"
          content=""
          isLoading={true}
        />
      );
      // Check for loading dots or spinner
      const loadingElement = screen.getByLabelText(/thinking|loading/i);
      expect(loadingElement).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper role attribute', () => {
      render(
        <ChatMessage
          role="user"
          content="Accessible message"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      expect(screen.getByRole('article')).toBeInTheDocument();
    });

    it('should have aria-label indicating message role', () => {
      render(
        <ChatMessage
          role="user"
          content="User message"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      expect(screen.getByRole('article')).toHaveAttribute('aria-label', expect.stringMatching(/user/i));
    });

    it('should have proper time element with datetime attribute', () => {
      const timestamp = "2025-11-16T10:30:00Z";
      const { container } = render(
        <ChatMessage
          role="assistant"
          content="Message"
          timestamp={timestamp}
        />
      );
      const timeElement = container.querySelector('time');
      expect(timeElement).toBeInTheDocument();
      expect(timeElement).toHaveAttribute('dateTime', timestamp);
      // Check that it displays time in HH:MM format
      expect(timeElement?.textContent).toMatch(/^\d{2}:\d{2}$/);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty content gracefully', () => {
      render(
        <ChatMessage
          role="user"
          content=""
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      // Should still render the message container
      expect(screen.getByRole('article')).toBeInTheDocument();
    });

    it('should handle very long content', () => {
      const longContent = 'A'.repeat(1000);
      render(
        <ChatMessage
          role="assistant"
          content={longContent}
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });

    it('should handle content with newlines', () => {
      render(
        <ChatMessage
          role="assistant"
          content="Line 1\nLine 2\nLine 3"
          timestamp="2025-11-16T10:30:00Z"
        />
      );
      expect(screen.getByText(/Line 1.*Line 2.*Line 3/s)).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom className', () => {
      render(
        <ChatMessage
          role="user"
          content="Custom class message"
          timestamp="2025-11-16T10:30:00Z"
          className="custom-test-class"
        />
      );
      const messageContainer = screen.getByRole('article');
      expect(messageContainer).toHaveClass('custom-test-class');
    });
  });
});
