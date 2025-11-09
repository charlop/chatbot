import { apiClient } from './client';

/**
 * Type definitions for Chat API
 */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  context?: {
    contractId?: string;
    relevantPage?: number;
    [key: string]: any;
  };
}

export interface ChatHistory {
  contractId: string;
  messages: ChatMessage[];
  sessionId?: string;
}

/**
 * Send a message to the AI chat interface
 * @param contractId - The contract ID for context
 * @param message - The user's message/question
 * @param history - Previous chat messages for context
 * @returns Promise with AI response and optional context
 */
export const sendMessage = async (
  contractId: string,
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/chat', {
    contractId,
    message,
    history,
  });
  return response.data;
};

/**
 * Get chat history for a contract
 * @param contractId - The contract ID
 * @returns Promise with chat history
 */
export const getChatHistory = async (contractId: string): Promise<ChatHistory> => {
  const response = await apiClient.get<ChatHistory>(`/chat/${contractId}`);
  return response.data;
};

/**
 * Clear chat history for a contract (if needed in the future)
 * @param contractId - The contract ID
 * @returns Promise with success confirmation
 */
export const clearChatHistory = async (contractId: string): Promise<{ success: boolean }> => {
  const response = await apiClient.delete<{ success: boolean }>(`/chat/${contractId}`);
  return response.data;
};
