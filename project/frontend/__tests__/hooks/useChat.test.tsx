import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useChat } from '@/hooks/useChat';
import * as chatAPI from '@/lib/api/chat';

// Mock the chat API
vi.mock('@/lib/api/chat', () => ({
  sendMessage: vi.fn(),
  ChatMessage: {},
  ChatResponse: {},
}));

describe('useChat Hook', () => {
  const mockContractId = 'contract-123';
  const mockSendMessage = chatAPI.sendMessage as ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockSendMessage.mockClear();
  });

  describe('Initialization', () => {
    it('should initialize with empty messages', () => {
      const { result } = renderHook(() => useChat(mockContractId));

      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should provide send and clearMessages functions', () => {
      const { result } = renderHook(() => useChat(mockContractId));

      expect(typeof result.current.send).toBe('function');
      expect(typeof result.current.clearMessages).toBe('function');
    });
  });

  describe('Sending Messages', () => {
    it('should add user message immediately', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Assistant response',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      act(() => {
        result.current.send('User question');
      });

      // User message should be added immediately
      await waitFor(() => {
        expect(result.current.messages).toHaveLength(1);
        expect(result.current.messages[0]).toMatchObject({
          role: 'user',
          content: 'User question',
        });
      });
    });

    it('should add assistant response after API call', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Assistant response',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      await act(async () => {
        await result.current.send('User question');
      });

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(2);
        expect(result.current.messages[1]).toMatchObject({
          role: 'assistant',
          content: 'Assistant response',
        });
      });
    });

    it('should set loading state during API call', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockSendMessage.mockReturnValue(promise);

      const { result } = renderHook(() => useChat(mockContractId));

      act(() => {
        result.current.send('User question');
      });

      // Should be loading
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      // Resolve the API call
      await act(async () => {
        resolvePromise!({
          response: 'Assistant response',
          context: {},
        });
        await promise;
      });

      // Should no longer be loading
      expect(result.current.isLoading).toBe(false);
    });

    it('should call sendMessage with correct parameters', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Assistant response',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      await act(async () => {
        await result.current.send('User question');
      });

      expect(mockSendMessage).toHaveBeenCalledWith(
        mockContractId,
        'User question',
        expect.arrayContaining([
          expect.objectContaining({
            role: 'user',
            content: 'User question',
          }),
        ])
      );
    });

    it('should not send if contractId is null', async () => {
      const { result } = renderHook(() => useChat(null));

      const response = await act(async () => {
        return await result.current.send('User question');
      });

      expect(response).toBeNull();
      expect(mockSendMessage).not.toHaveBeenCalled();
      expect(result.current.messages).toHaveLength(0);
    });

    it('should not send empty messages', async () => {
      const { result } = renderHook(() => useChat(mockContractId));

      const response = await act(async () => {
        return await result.current.send('   ');
      });

      expect(response).toBeNull();
      expect(mockSendMessage).not.toHaveBeenCalled();
      expect(result.current.messages).toHaveLength(0);
    });

    it('should include previous messages in API call', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Response 1',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      // Send first message
      await act(async () => {
        await result.current.send('Question 1');
      });

      mockSendMessage.mockResolvedValue({
        response: 'Response 2',
        context: {},
      });

      // Send second message
      await act(async () => {
        await result.current.send('Question 2');
      });

      // Second call should include history
      expect(mockSendMessage).toHaveBeenLastCalledWith(
        mockContractId,
        'Question 2',
        expect.arrayContaining([
          expect.objectContaining({ role: 'user', content: 'Question 1' }),
          expect.objectContaining({ role: 'assistant', content: 'Response 1' }),
          expect.objectContaining({ role: 'user', content: 'Question 2' }),
        ])
      );
    });
  });

  describe('Error Handling', () => {
    it('should set error state when API call fails', async () => {
      const apiError = new Error('API Error');
      mockSendMessage.mockRejectedValue(apiError);

      const { result } = renderHook(() => useChat(mockContractId));

      try {
        await act(async () => {
          await result.current.send('User question');
        });
      } catch (e) {
        // Expected error
      }

      await waitFor(() => {
        expect(result.current.error).toEqual(apiError);
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should add error message to chat on failure', async () => {
      mockSendMessage.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useChat(mockContractId));

      try {
        await act(async () => {
          await result.current.send('User question');
        });
      } catch (e) {
        // Expected
      }

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(2);
        expect(result.current.messages[1]).toMatchObject({
          role: 'assistant',
          content: expect.stringContaining('error'),
        });
      });
    });

    it('should clear error on successful send', async () => {
      // First call fails
      mockSendMessage.mockRejectedValueOnce(new Error('API Error'));

      const { result } = renderHook(() => useChat(mockContractId));

      try {
        await act(async () => {
          await result.current.send('Question 1');
        });
      } catch (e) {
        // Expected
      }

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Second call succeeds
      mockSendMessage.mockResolvedValue({
        response: 'Success response',
        context: {},
      });

      await act(async () => {
        await result.current.send('Question 2');
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });
  });

  describe('Clear Messages', () => {
    it('should clear all messages', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Assistant response',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      // Add some messages
      await act(async () => {
        await result.current.send('Question 1');
      });

      expect(result.current.messages).toHaveLength(2);

      // Clear messages
      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toHaveLength(0);
      expect(result.current.error).toBeNull();
    });

    it('should clear error state', async () => {
      mockSendMessage.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useChat(mockContractId));

      try {
        await act(async () => {
          await result.current.send('User question');
        });
      } catch (e) {
        // Expected
      }

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Contract ID Changes', () => {
    it('should handle contract ID changes', () => {
      const { result, rerender } = renderHook(
        ({ contractId }) => useChat(contractId),
        { initialProps: { contractId: 'contract-1' } }
      );

      // Send message with first contract
      act(() => {
        result.current.send('Question for contract 1');
      });

      // Change contract ID
      rerender({ contractId: 'contract-2' });

      // Should still have the same messages (messages aren't auto-cleared)
      // This is intentional - user must explicitly clear if switching contracts
      expect(result.current.messages.length).toBeGreaterThan(0);
    });
  });

  describe('Timestamps', () => {
    it('should add timestamps to messages', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Assistant response',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      await act(async () => {
        await result.current.send('User question');
      });

      await waitFor(() => {
        expect(result.current.messages[0].timestamp).toBeDefined();
        expect(result.current.messages[1].timestamp).toBeDefined();
      });
    });

    it('should use ISO 8601 format for timestamps', async () => {
      mockSendMessage.mockResolvedValue({
        response: 'Assistant response',
        context: {},
      });

      const { result } = renderHook(() => useChat(mockContractId));

      await act(async () => {
        await result.current.send('User question');
      });

      await waitFor(() => {
        const timestamp = result.current.messages[0].timestamp;
        expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
      });
    });
  });
});
