'use client';

import React from 'react';
import { cn } from '@/utils/cn';
import { layout } from '@/lib/design-tokens';
import { ChevronRight } from 'lucide-react';
import Link from 'next/link';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageShellProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  className?: string;
}

export function PageShell({
  children,
  title,
  subtitle,
  breadcrumbs,
  actions,
  className,
}: PageShellProps) {
  return (
    <div className={cn('flex-1 flex flex-col min-h-0', className)}>
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        {/* Breadcrumbs */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
            {breadcrumbs.map((item, index) => (
              <React.Fragment key={index}>
                {index > 0 && (
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                )}
                {item.href ? (
                  <Link
                    href={item.href}
                    className="hover:text-gray-700 transition-colors"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span className="text-gray-900 font-medium">{item.label}</span>
                )}
              </React.Fragment>
            ))}
          </nav>
        )}

        {/* Title and Actions */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {subtitle && (
              <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center space-x-3">{actions}</div>}
        </div>
      </div>

      {/* Page Content */}
      <div
        className="flex-1 overflow-auto bg-gray-50"
        style={{ padding: layout.content.padding }}
      >
        <div
          className="mx-auto"
          style={{ maxWidth: layout.content.maxWidth }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

interface PageContentProps {
  children: React.ReactNode;
  className?: string;
}

export function PageContent({ children, className }: PageContentProps) {
  return (
    <div
      className={cn(
        'bg-white/90 backdrop-blur rounded-lg border border-gray-200 shadow-sm',
        className
      )}
      style={{ padding: layout.content.padding }}
    >
      {children}
    </div>
  );
}

interface PageSectionProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
}

export function PageSection({
  children,
  title,
  subtitle,
  className,
}: PageSectionProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {(title || subtitle) && (
        <div>
          {title && (
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          )}
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
