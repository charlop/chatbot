import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AxiosResponse } from 'axios';

// Mock the API client
const mockGet = vi.fn();
const mockPost = vi.fn();

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
  },
}));

describe('Chat API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('sendMessage', () => {
    it('should send a message and get AI response', async () => {
      const { sendMessage } = await import('@/lib/api/chat');
      const mockResponse: AxiosResponse = {
        data: {
          response: 'The GAP Insurance Premium is $1,500.00',
          context: {
            contractId: 'C123456',
            relevantPage: 2,
          },
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await sendMessage('C123456', 'What is the GAP premium?', []);

      expect(mockPost).toHaveBeenCalledWith('/chat', {
        contractId: 'C123456',
        message: 'What is the GAP premium?',
        history: [],
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should send message with chat history', async () => {
      const { sendMessage } = await import('@/lib/api/chat');
      const history = [
        { role: 'user', content: 'What is the refund method?' },
        { role: 'assistant', content: 'The refund method is Pro-Rata' },
      ];

      mockPost.mockResolvedValue({
        data: { response: 'Yes, that is correct.' },
      } as AxiosResponse);

      await sendMessage('C123456', 'Is that pro-rata?', history);

      expect(mockPost).toHaveBeenCalledWith('/chat', {
        contractId: 'C123456',
        message: 'Is that pro-rata?',
        history,
      });
    });

    it('should handle API errors gracefully', async () => {
      const { sendMessage } = await import('@/lib/api/chat');
      const error = {
        response: {
          status: 500,
          data: { message: 'AI service unavailable' },
        },
      };

      mockPost.mockRejectedValue(error);

      await expect(
        sendMessage('C123456', 'Test question', [])
      ).rejects.toThrow();
    });

    it('should handle empty messages', async () => {
      const { sendMessage } = await import('@/lib/api/chat');

      mockPost.mockResolvedValue({
        data: { response: 'Please provide a question.' },
      } as AxiosResponse);

      const result = await sendMessage('C123456', '', []);

      expect(mockPost).toHaveBeenCalled();
      expect(result).toBeDefined();
    });
  });

  describe('getChatHistory', () => {
    it('should retrieve chat history for a contract', async () => {
      const { getChatHistory } = await import('@/lib/api/chat');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'C123456',
          messages: [
            {
              role: 'user',
              content: 'What is the GAP premium?',
              timestamp: '2025-11-09T00:00:00Z',
            },
            {
              role: 'assistant',
              content: 'The GAP Insurance Premium is $1,500.00',
              timestamp: '2025-11-09T00:00:01Z',
            },
          ],
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getChatHistory('C123456');

      expect(mockGet).toHaveBeenCalledWith('/chat/C123456');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle empty chat history', async () => {
      const { getChatHistory } = await import('@/lib/api/chat');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'C123456',
          messages: [],
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getChatHistory('C123456');

      expect(result.messages).toHaveLength(0);
    });

    it('should handle errors when retrieving history', async () => {
      const { getChatHistory } = await import('@/lib/api/chat');
      const error = {
        response: {
          status: 404,
          data: { message: 'Chat history not found' },
        },
      };

      mockGet.mockRejectedValue(error);

      await expect(getChatHistory('INVALID')).rejects.toThrow();
    });
  });

  describe('Type Safety', () => {
    it('should return properly typed chat response', async () => {
      const { sendMessage } = await import('@/lib/api/chat');
      const mockResponse: AxiosResponse = {
        data: {
          response: 'The GAP Insurance Premium is $1,500.00',
          context: {
            contractId: 'C123456',
          },
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockPost.mockResolvedValue(mockResponse);

      const result = await sendMessage('C123456', 'What is the GAP premium?', []);

      expect(result).toHaveProperty('response');
      expect(typeof result.response).toBe('string');
    });

    it('should properly type chat history messages', async () => {
      const { getChatHistory } = await import('@/lib/api/chat');
      const mockResponse: AxiosResponse = {
        data: {
          contractId: 'C123456',
          messages: [
            { role: 'user', content: 'Test', timestamp: '2025-11-09T00:00:00Z' },
          ],
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      mockGet.mockResolvedValue(mockResponse);

      const result = await getChatHistory('C123456');

      expect(result.messages[0]).toHaveProperty('role');
      expect(result.messages[0]).toHaveProperty('content');
      expect(result.messages[0].role).toMatch(/user|assistant/);
    });
  });
});
