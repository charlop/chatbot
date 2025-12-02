import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    exclude: ['**/node_modules/**', '**/e2e/**', '**/.next/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        '.next/',
        'coverage/',
        'e2e/',
        '*.config.*',
        '**/*.d.ts',
        '**/*.test.{ts,tsx}',
        '**/__tests__/**',
        '**/types/**',
        'app/layout.tsx', // Next.js root layout
        'app/globals.css', // CSS files
      ],
      // Enforce minimum coverage thresholds to catch untested code
      thresholds: {
        lines: 80,        // Minimum 80% line coverage
        functions: 80,    // Minimum 80% function coverage
        branches: 75,     // Minimum 75% branch coverage
        statements: 80,   // Minimum 80% statement coverage
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
