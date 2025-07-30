'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/ui/layout/sidebar';
import { Topbar } from '@/components/ui/layout/topbar';
import { ErrorBoundary } from '@/components/error-boundary';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  
  // Don't show sidebar and topbar on login page
  if (pathname === '/admin/login') {
    return (
      <div className="min-h-screen bg-gray-50">
        <ErrorBoundary>{children}</ErrorBoundary>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto p-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ErrorBoundary>{children}</ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
}
