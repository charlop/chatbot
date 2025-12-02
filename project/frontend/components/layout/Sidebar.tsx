'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * Navigation items configuration
 */
const navigationItems = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: (
      <svg
        className="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
        />
      </svg>
    ),
  },
  {
    name: 'Admin',
    href: '/admin',
    icon: (
      <svg
        className="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
  },
];

/**
 * Sidebar Component
 * Fixed width sidebar with navigation icons and user profile
 */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-16 h-screen bg-neutral-900 flex flex-col items-center py-4">
      {/* Logo/Brand Section */}
      <div className="mb-8">
        <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-base">cAI</span>
        </div>
      </div>

      {/* Navigation Section */}
      <nav className="flex-1 flex flex-col items-center space-y-2">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`
                w-12 h-12 flex items-center justify-center rounded-lg
                transition-all duration-200
                ${
                  isActive
                    ? 'bg-primary-500 text-white'
                    : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
                }
              `}
              aria-label={item.name}
              title={item.name}
            >
              {item.icon}
            </Link>
          );
        })}
      </nav>

      {/* User Profile Section */}
      <div data-testid="user-profile-section" className="mt-auto">
        <button
          className="w-12 h-12 rounded-full bg-neutral-700 hover:bg-neutral-600 transition-colors flex items-center justify-center"
          aria-label="User profile"
          title="User profile"
          data-testid="user-avatar"
        >
          <span className="text-white text-sm font-medium">U</span>
        </button>
      </div>
    </aside>
  );
}
