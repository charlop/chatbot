import { AxiosError, AxiosInstance } from 'axios';

/**
 * Configuration for retry logic
 */
export interface RetryConfig {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
}

const DEFAULT_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
};

/**
 * Determine if an error should be retried
 * Retry on:
 * - Network errors (no response)
 * - 5xx server errors
 * - Timeout errors
 *
 * Do NOT retry on:
 * - 4xx client errors (bad request, unauthorized, forbidden, not found, etc.)
 */
export const shouldRetry = (error: AxiosError): boolean => {
  // No response means network error - should retry
  if (!error.response) {
    return true;
  }

  const status = error.response.status;

  // Retry on 5xx server errors
  if (status >= 500 && status < 600) {
    return true;
  }

  // Don't retry on 4xx client errors
  if (status >= 400 && status < 500) {
    return false;
  }

  return false;
};

/**
 * Calculate retry delay using exponential backoff
 * Formula: min(initialDelay * 2^attempt, maxDelay)
 */
export const getRetryDelay = (
  attemptNumber: number,
  config: RetryConfig = {}
): number => {
  const { initialDelay, maxDelay } = { ...DEFAULT_CONFIG, ...config };
  const delay = initialDelay * Math.pow(2, attemptNumber);
  return Math.min(delay, maxDelay);
};

/**
 * Sleep utility for async delays
 */
const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Retry interceptor for axios
 * This interceptor will automatically retry failed requests based on the retry configuration
 */
export const retryInterceptor = async (
  error: AxiosError,
  axiosInstance: AxiosInstance,
  config: RetryConfig = {}
): Promise<any> => {
  const { maxRetries } = { ...DEFAULT_CONFIG, ...config };

  // Initialize retry count if not present
  const retryConfig = error.config as any;
  if (!retryConfig) {
    return Promise.reject(error);
  }

  retryConfig.__retryCount = retryConfig.__retryCount || 0;

  // Check if we should retry this error
  if (!shouldRetry(error)) {
    return Promise.reject(error);
  }

  // Check if we've exceeded max retries
  if (retryConfig.__retryCount >= maxRetries) {
    return Promise.reject(error);
  }

  // Increment retry count
  retryConfig.__retryCount += 1;

  // Calculate delay for this attempt
  const delay = getRetryDelay(retryConfig.__retryCount - 1, config);

  console.debug(
    `Retrying request (attempt ${retryConfig.__retryCount}/${maxRetries}) after ${delay}ms`
  );

  // Wait before retrying
  await sleep(delay);

  // Retry the request
  return axiosInstance.request(retryConfig);
};

/**
 * Setup retry interceptor on an axios instance
 */
export const setupRetryInterceptor = (
  axiosInstance: AxiosInstance,
  config: RetryConfig = {}
): void => {
  axiosInstance.interceptors.response.use(
    undefined, // Don't modify successful responses
    (error: AxiosError) => retryInterceptor(error, axiosInstance, config)
  );
};
