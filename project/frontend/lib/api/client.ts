import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { retryInterceptor } from './retry';

/**
 * Custom API Error class for structured error handling
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }
}

/**
 * Transform Axios errors into our custom ApiError format
 */
const transformError = (error: AxiosError): ApiError => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as any;
    const message = data?.message || error.message || 'An error occurred';

    return new ApiError(message, status, data);
  } else if (error.request) {
    // Request was made but no response received (network error)
    return new ApiError(
      'Network error: Unable to reach the server',
      0,
      { code: error.code }
    );
  } else {
    // Something else happened
    return new ApiError(
      error.message || 'An unexpected error occurred',
      0
    );
  }
};

/**
 * Transform snake_case keys to camelCase recursively
 * Backend uses snake_case (Python convention) but frontend uses camelCase (JavaScript convention)
 */
function toCamelCase(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => toCamelCase(item));
  }

  if (typeof obj === 'object' && obj.constructor === Object) {
    const newObj: any = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        // Convert snake_case to camelCase
        const camelKey = key.replace(/_([a-z])/g, (_, letter) =>
          letter.toUpperCase()
        );
        newObj[camelKey] = toCamelCase(obj[key]);
      }
    }
    return newObj;
  }

  return obj;
}

/**
 * Create and configure the Axios instance
 */
const createApiClient = (): AxiosInstance => {
  const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1';

  const client = axios.create({
    baseURL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add timestamp for logging/debugging
      (config as any).metadata = { startTime: Date.now() };

      // TODO: Add auth token when auth is implemented (Day 3 skipped for MVP)
      // const token = getAuthToken();
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`;
      // }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor - Success handler
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log response time if needed
      const config = response.config as any;
      if (config.metadata?.startTime) {
        const duration = Date.now() - config.metadata.startTime;
        // Could send to analytics/monitoring
        console.debug(`Request to ${response.config.url} took ${duration}ms`);
      }

      // Transform response data from snake_case to camelCase
      if (response.data) {
        response.data = toCamelCase(response.data);
      }

      return response;
    },
    async (error: AxiosError) => {
      // First, try to retry the request if applicable
      try {
        return await retryInterceptor(error, client);
      } catch (retryError) {
        // If retry fails or is not applicable, handle the error
        error = retryError as AxiosError;
      }

      // Error handling after retry attempts exhausted
      // Transform axios error to our custom ApiError
      const apiError = transformError(error);

      // Handle specific status codes
      switch (apiError.statusCode) {
        case 401:
          // Unauthorized - could trigger logout when auth is implemented
          console.error('Unauthorized access - authentication required');
          // TODO: Trigger auth refresh or redirect to login
          break;

        case 403:
          // Forbidden - user doesn't have permission
          console.error('Forbidden - insufficient permissions');
          break;

        case 404:
          // Not found
          console.error('Resource not found');
          break;

        case 500:
        case 502:
        case 503:
        case 504:
          // Server errors
          console.error('Server error occurred');
          break;

        case 0:
          // Network error
          console.error('Network error - unable to reach server');
          break;

        default:
          console.error(`API error: ${apiError.message}`);
      }

      return Promise.reject(apiError);
    }
  );

  return client;
};

// Export the configured axios instance
export const apiClient = createApiClient();

// Export types for use in other modules
export type { AxiosResponse, AxiosError };
