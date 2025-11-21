import { useState, useCallback } from 'react';
import { sendMessage, ChatMessage, ChatResponse } from '@/lib/api/chat';

/**
 * Hook for managing chat state and sending messages
 * @param contractId - The contract ID for chat context
 * @returns Chat state and functions for sending messages
 */
export const useChat = (contractId: string | null) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const send = useCallback(async (message: string): Promise<ChatResponse | null> => {
    if (!contractId || !message.trim()) {
      return null;
    }

    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    // Create updated messages array for API call
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);

    try {
      // Send message to API with current history (including the new user message)
      const response = await sendMessage(contractId, message, updatedMessages);

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      setIsLoading(false);
      return response;
    } catch (err) {
      const error = err as Error;
      setError(error);
      setIsLoading(false);

      // Add error message to chat
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);

      throw error;
    }
  }, [contractId, messages]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    send,
    clearMessages,
  };
};
