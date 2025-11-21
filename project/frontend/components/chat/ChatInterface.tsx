import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { ChatMessage } from './ChatMessage';
import { Button } from '../ui/Button';
import type { ChatMessage as ChatMessageType } from '@/lib/api/chat';

export interface ChatInterfaceProps {
  /**
   * List of chat messages
   */
  messages: ChatMessageType[];

  /**
   * Callback when user sends a message
   */
  onSendMessage: (message: string) => void;

  /**
   * Contract ID for context
   */
  contractId: string;

  /**
   * Whether the assistant is currently responding
   */
  isLoading?: boolean;

  /**
   * Error message to display
   */
  error?: string;

  /**
   * Optional CSS class
   */
  className?: string;
}

/**
 * Chat interface component with message list and input
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  contractId,
  isLoading = false,
  error,
  className = '',
}) => {
  const [inputValue, setInputValue] = useState('');
  const messageListRef = useRef<HTMLDivElement>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messageEndRef.current && typeof messageEndRef.current.scrollIntoView === 'function') {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = () => {
    const trimmedMessage = inputValue.trim();
    if (trimmedMessage && !isLoading) {
      onSendMessage(trimmedMessage);
      setInputValue('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter, but allow Shift+Enter for newlines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const hasMessages = messages.length > 0;
  const isCollapsed = className.includes('collapsed');

  return (
    <div
      role="region"
      aria-label="Chat interface"
      className={`flex flex-col h-full bg-white ${className}`}
    >
      {/* Contract Context Indicator - Hidden in collapsed mode (handled by CollapsibleChat) */}
      {!isCollapsed && (
        <div className="px-4 py-2 bg-neutral-50 border-b border-neutral-200">
          <p className="text-xs text-neutral-600">
            <span className="font-medium">Contract:</span> {contractId}
          </p>
        </div>
      )}

      {/* Message List - Hidden when collapsed */}
      {!isCollapsed && (
        <div
          ref={messageListRef}
          role="log"
          aria-live="polite"
          aria-atomic="false"
          className="flex-1 overflow-y-auto px-4 py-4"
        >
        {!hasMessages && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-neutral-500">No messages yet. Start a conversation!</p>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}-${message.timestamp || ''}`}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
          />
        ))}

        {/* Show loading indicator as last message */}
        {isLoading && (
          <ChatMessage
            role="assistant"
            content=""
            isLoading={true}
          />
        )}

          {/* Scroll anchor */}
          <div ref={messageEndRef} />
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2 bg-danger-50 border-t border-danger-200">
          <p className="text-sm text-danger-700">{error}</p>
        </div>
      )}

      {/* Input Area */}
      <div className="px-4 py-3 border-t border-neutral-200 bg-white">
        <div className="flex items-end gap-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask a question about this contract..."
            aria-label="Chat message input"
            rows={1}
            className="flex-1 resize-none rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-neutral-100 disabled:cursor-not-allowed"
            style={{
              minHeight: '38px',
              maxHeight: '120px',
            }}
          />
          <Button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            variant="primary"
            size="md"
            aria-label="Send message"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};
