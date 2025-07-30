'use client';

import { usePathname } from 'next/navigation';
import { ResellerNavigation } from '@/components/ui/layout/reseller-navigation';
import { ResellerHeader } from '@/components/ui/layout/reseller-header';
import { ErrorBoundary } from '@/components/error-boundary';

interface ResellerLayoutProps {
  children: React.ReactNode;
}

export default function ResellerLayout({ children }: ResellerLayoutProps) {
  const pathname = usePathname();
  
  // Don't show header and navigation on login page
  if (pathname === '/reseller/login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        <ErrorBoundary>{children}</ErrorBoundary>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <ResellerHeader />
      <div className="flex">
        <ResellerNavigation />
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <ErrorBoundary>{children}</ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
}
