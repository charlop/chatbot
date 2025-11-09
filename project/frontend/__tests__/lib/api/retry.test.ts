import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AxiosError } from 'axios';

// Mock for testing retry logic
const createMockError = (status?: number, code?: string): AxiosError => {
  const error = new Error('Request failed') as AxiosError;
  if (status) {
    error.response = {
      status,
      data: {},
      statusText: 'Error',
      headers: {},
      config: {} as any,
    };
  }
  if (code) {
    error.code = code;
  }
  error.config = {} as any;
  error.isAxiosError = true;
  return error;
};

describe('Retry Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('shouldRetry', () => {
    it('should retry on network errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(undefined, 'ERR_NETWORK');
      expect(shouldRetry(error)).toBe(true);
    });

    it('should retry on timeout errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(undefined, 'ECONNABORTED');
      expect(shouldRetry(error)).toBe(true);
    });

    it('should retry on 500 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(500);
      expect(shouldRetry(error)).toBe(true);
    });

    it('should retry on 502 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(502);
      expect(shouldRetry(error)).toBe(true);
    });

    it('should retry on 503 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(503);
      expect(shouldRetry(error)).toBe(true);
    });

    it('should retry on 504 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(504);
      expect(shouldRetry(error)).toBe(true);
    });

    it('should NOT retry on 400 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(400);
      expect(shouldRetry(error)).toBe(false);
    });

    it('should NOT retry on 401 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(401);
      expect(shouldRetry(error)).toBe(false);
    });

    it('should NOT retry on 403 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(403);
      expect(shouldRetry(error)).toBe(false);
    });

    it('should NOT retry on 404 errors', async () => {
      const { shouldRetry } = await import('@/lib/api/retry');
      const error = createMockError(404);
      expect(shouldRetry(error)).toBe(false);
    });
  });

  describe('getRetryDelay', () => {
    it('should return 1000ms for first retry (attempt 0)', async () => {
      const { getRetryDelay } = await import('@/lib/api/retry');
      expect(getRetryDelay(0)).toBe(1000);
    });

    it('should return 2000ms for second retry (attempt 1)', async () => {
      const { getRetryDelay } = await import('@/lib/api/retry');
      expect(getRetryDelay(1)).toBe(2000);
    });

    it('should return 4000ms for third retry (attempt 2)', async () => {
      const { getRetryDelay } = await import('@/lib/api/retry');
      expect(getRetryDelay(2)).toBe(4000);
    });

    it('should cap at maxDelay (10000ms by default)', async () => {
      const { getRetryDelay } = await import('@/lib/api/retry');
      expect(getRetryDelay(10)).toBeLessThanOrEqual(10000);
    });
  });

  describe('retryInterceptor', () => {
    it('should be a function', async () => {
      const { retryInterceptor } = await import('@/lib/api/retry');
      expect(typeof retryInterceptor).toBe('function');
    });

    it('should respect maxRetries limit', async () => {
      const { retryInterceptor } = await import('@/lib/api/retry');
      const error = createMockError(500);
      const mockAxios = {
        request: vi.fn(),
      };

      // Set retry count to max already
      error.config = { ...error.config, __retryCount: 3 } as any;

      try {
        await retryInterceptor(error as any, mockAxios as any, { maxRetries: 3 });
        expect.fail('Should have thrown an error');
      } catch (e) {
        // Should not retry when maxRetries reached
        expect(mockAxios.request).not.toHaveBeenCalled();
      }
    });

    it('should not retry 4xx errors', async () => {
      const { retryInterceptor } = await import('@/lib/api/retry');
      const error = createMockError(404);
      const mockAxios = {
        request: vi.fn(),
      };

      try {
        await retryInterceptor(error as any, mockAxios as any);
      } catch (e) {
        // Expected to fail immediately
      }

      // Should not retry
      expect(mockAxios.request).not.toHaveBeenCalled();
    });
  });

  describe('Integration with exponential backoff', () => {
    it('should increase delay exponentially', async () => {
      const { getRetryDelay } = await import('@/lib/api/retry');
      const delay0 = getRetryDelay(0);
      const delay1 = getRetryDelay(1);
      const delay2 = getRetryDelay(2);

      expect(delay1).toBeGreaterThan(delay0);
      expect(delay2).toBeGreaterThan(delay1);
    });
  });
});
