'use client';

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

/**
 * Main Layout Component
 * Combines Sidebar, Header, and Main Content Area
 *
 * Layout structure:
 * - Sidebar: 64px fixed width on left
 * - Content Area (flex):
 *   - Header: Full width, fixed height at top
 *   - Main: Scrollable content area below header
 */
export function Layout({ children, title }: LayoutProps) {
  return (
    <div className="flex h-screen bg-neutral-50 overflow-hidden">
      {/* Sidebar - Fixed 64px width */}
      <Sidebar />

      {/* Main Content Area - Flex grows to fill remaining space */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - Fixed height at top */}
        <Header title={title} />

        {/* Main Content - Scrollable */}
        <main className="flex-1 overflow-auto p-6" role="main">
          {children}
        </main>
      </div>
    </div>
  );
}
