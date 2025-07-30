'use client';

import { usePathname } from 'next/navigation';
import { CustomerNavigation } from '@/components/ui/layout/customer-navigation';
import { CustomerHeader } from '@/components/ui/layout/customer-header';
import { ErrorBoundary } from '@/components/error-boundary';

interface CustomerLayoutProps {
  children: React.ReactNode;
}

export default function CustomerLayout({ children }: CustomerLayoutProps) {
  const pathname = usePathname();
  
  // Don't show header and navigation on login page
  if (pathname === '/customer/login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
        <ErrorBoundary>{children}</ErrorBoundary>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <CustomerHeader />
      <CustomerNavigation />
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    </div>
  );
}
