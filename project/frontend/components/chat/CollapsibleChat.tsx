import React, { useState, useEffect, useCallback } from 'react';
import { ChatInterface } from './ChatInterface';
import type { ChatMessage } from '@/lib/api/chat';

export interface CollapsibleChatProps {
  /**
   * List of chat messages
   */
  messages: ChatMessage[];

  /**
   * Callback when user sends a message
   */
  onSendMessage: (message: string) => void;

  /**
   * Contract ID for context
   */
  contractId: string;

  /**
   * Account number for display
   */
  accountNumber?: string;

  /**
   * Whether the assistant is currently responding
   */
  isLoading?: boolean;

  /**
   * Error message to display
   */
  error?: string;

  /**
   * Whether to start expanded
   */
  defaultExpanded?: boolean;

  /**
   * Callback when expand state changes
   */
  onExpandChange?: (expanded: boolean) => void;

  /**
   * Optional CSS class
   */
  className?: string;
}

/**
 * Collapsible chat wrapper that provides expand/collapse functionality
 */
export const CollapsibleChat: React.FC<CollapsibleChatProps> = ({
  messages,
  onSendMessage,
  contractId,
  accountNumber,
  isLoading = false,
  error,
  defaultExpanded = false,
  onExpandChange,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [previousContractId, setPreviousContractId] = useState(contractId);

  // Detect contract changes
  useEffect(() => {
    if (contractId !== previousContractId) {
      setPreviousContractId(contractId);
      // You could add visual feedback here (e.g., brief highlight animation)
    }
  }, [contractId, previousContractId]);

  const handleToggle = useCallback(() => {
    const newExpanded = !isExpanded;
    setIsExpanded(newExpanded);
    onExpandChange?.(newExpanded);
  }, [isExpanded, onExpandChange]);

  // Keyboard shortcut: Ctrl+` or Cmd+`
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault();
        handleToggle();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleToggle]);

  const heightClass = isExpanded ? 'h-[400px]' : 'h-[92px]';

  return (
    <div
      data-testid="collapsible-chat"
      className={`transition-all duration-300 ease-in-out ${heightClass} ${className}`}
    >
      {/* Header with Context and Toggle Button */}
      <div className="flex items-center justify-between px-4 py-2 bg-neutral-50 border-b border-neutral-200">
        <div className="flex items-center gap-3">
          {accountNumber && (
            <div className="text-xs">
              <span className="font-medium text-neutral-700">Account:</span>{' '}
              <span className="text-neutral-900">{accountNumber}</span>
            </div>
          )}
          <div className="text-xs text-neutral-600">
            <span className="font-medium">Contract:</span> {contractId}
          </div>
        </div>

        <button
          onClick={handleToggle}
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Collapse chat' : 'Expand chat'}
          className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-2 py-1"
        >
          {isExpanded ? (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
              Collapse
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 15l7-7 7 7"
                />
              </svg>
              Expand
            </>
          )}
        </button>
      </div>

      {/* Chat Interface - Single Instance */}
      <div className="h-[calc(100%-40px)]">
        <ChatInterface
          messages={messages}
          onSendMessage={onSendMessage}
          contractId={contractId}
          isLoading={isLoading}
          error={error}
          className={isExpanded ? '' : 'collapsed'}
        />
      </div>
    </div>
  );
};
