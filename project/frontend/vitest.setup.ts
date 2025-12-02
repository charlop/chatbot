import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll, vi } from 'vitest';

// Store original console methods
const originalError = console.error;
const originalWarn = console.warn;

// Fail tests on console errors to catch runtime errors early
beforeAll(() => {
  console.error = (...args: any[]) => {
    const message = args[0]?.toString() || '';

    // Allowlist for expected errors that are safe to ignore
    const allowedErrors = [
      // React warnings in development
      'Warning: Failed prop type',
      'Warning: An update to',
      'Warning: ReactDOM.render',
      'An update to %s inside a test was not wrapped in act', // React testing act warnings
      // Test environment limitations
      'Not implemented: HTMLFormElement.prototype.submit',
      'Not implemented: HTMLCanvasElement.prototype.getContext',
      'Not implemented: HTMLMediaElement.prototype.play',
      // PDF.js warnings and errors in tests
      'Warning: Setting up fake worker',
      'Highlight generation error:', // Expected when PDF mock fails in tests
      // Next.js warnings
      'Warning: useSearchParams',
    ];

    // If the error matches any allowed pattern, just log it normally
    if (allowedErrors.some(allowed => message.includes(allowed))) {
      originalError(...args);
      return;
    }

    // Otherwise, log the error and fail the test
    originalError('❌ Console error detected in test:', ...args);
    throw new Error(`Console error: ${message}`);
  };

  // Track warnings but don't fail (informational only)
  console.warn = (...args: any[]) => {
    originalWarn('⚠️ [WARN]', ...args);
  };
});

afterAll(() => {
  // Restore original console methods
  console.error = originalError;
  console.warn = originalWarn;
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock DOMMatrix for PDF.js in test environment
global.DOMMatrix = class DOMMatrix {
  constructor() {
    // Mock implementation
  }
} as any;

// Mock window.matchMedia for ThemeProvider
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver for PDFViewer
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return [];
  }
} as any;

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: vi.fn(),
      replace: vi.fn(),
      prefetch: vi.fn(),
      back: vi.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    };
  },
  usePathname() {
    return '/';
  },
  useSearchParams() {
    return new URLSearchParams();
  },
}));
