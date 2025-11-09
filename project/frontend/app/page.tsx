import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-primary-50 to-neutral-50 dark:from-neutral-900 dark:to-neutral-800 transition-colors">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-bold text-neutral-900 dark:text-neutral-100">
          Contract Refund Eligibility System
        </h1>
        <p className="mt-4 text-xl text-neutral-600 dark:text-neutral-400 max-w-2xl">
          AI-powered contract review and refund eligibility determination
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors font-medium"
          >
            View Dashboard
          </Link>
          <a
            href="https://github.com"
            className="px-6 py-3 border-2 border-primary-500 text-primary-500 rounded-md hover:bg-primary-50 transition-colors font-medium"
          >
            Documentation
          </a>
        </div>
        <div className="mt-12 text-sm text-neutral-500">
          <p>Day 2: Base UI Components ✅</p>
          <p className="mt-2">5 components | 105 tests passing</p>
        </div>
      </div>
    </main>
  );
}
