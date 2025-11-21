import React from 'react';

export interface ChatMessageProps {
  /**
   * Role of the message sender
   */
  role: 'user' | 'assistant';

  /**
   * Message content
   */
  content: string;

  /**
   * Timestamp in ISO 8601 format
   */
  timestamp?: string;

  /**
   * Whether the assistant is currently loading/thinking
   */
  isLoading?: boolean;

  /**
   * Optional CSS class
   */
  className?: string;
}

/**
 * Formats ISO timestamp to HH:MM format
 */
const formatTime = (isoTimestamp: string): string => {
  const date = new Date(isoTimestamp);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
};

/**
 * Loading indicator for assistant messages
 */
const LoadingIndicator: React.FC = () => (
  <div
    className="flex items-center gap-1"
    aria-label="Assistant is thinking"
    role="status"
  >
    <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
    <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
    <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
);

/**
 * Chat message component for displaying user or assistant messages
 */
export const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  timestamp,
  isLoading = false,
  className = '',
}) => {
  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  // Container alignment
  const containerClass = isUser ? 'ml-auto' : 'mr-auto';

  // Message bubble styling
  const bubbleClass = isUser
    ? 'bg-[#954293] text-white'
    : 'bg-neutral-100 text-neutral-900';

  return (
    <article
      role="article"
      aria-label={`${isUser ? 'User' : 'Assistant'} message`}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 ${className}`}
    >
      <div className={`max-w-[80%] ${containerClass}`}>
        {/* Message Bubble */}
        <div className={`rounded-lg px-4 py-2 ${bubbleClass}`}>
          {isLoading && isAssistant ? (
            <LoadingIndicator />
          ) : (
            <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
          )}
        </div>

        {/* Timestamp */}
        {timestamp && !isLoading && (
          <div className={`mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            <time
              dateTime={timestamp}
              className="text-xs text-neutral-500"
            >
              {formatTime(timestamp)}
            </time>
          </div>
        )}
      </div>
    </article>
  );
};
