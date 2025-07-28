'use client';

import React from 'react';
import { cn } from '@/utils/cn';
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';

interface AppLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function AppLayout({ children, className }: AppLayoutProps) {
  return (
    <div className={cn('flex h-screen bg-gray-50', className)}>
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <Topbar />
        
        {/* Page Content */}
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
