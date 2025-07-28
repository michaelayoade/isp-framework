'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/utils/cn';
import { layout } from '@/lib/design-tokens';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  Router,
  Ticket,
  Settings,
  ChevronLeft,
  Wifi,
  MessageSquare,
  Building,
  ChevronRight,
} from 'lucide-react';

interface SidebarItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const sidebarItems: SidebarItem[] = [
  {
    label: 'Dashboard',
    href: '/admin',
    icon: LayoutDashboard,
  },
  {
    label: 'Customers',
    href: '/customers',
    icon: Users,
  },
  {
    label: 'Billing',
    href: '/billing',
    icon: CreditCard,
  },
  {
    label: 'Network',
    href: '/network',
    icon: Wifi,
  },
  {
    label: 'Tickets',
    href: '/tickets',
    icon: MessageSquare,
  },
  {
    label: 'Customer Portal',
    href: '/customer-portal',
    icon: Users,
  },
  {
    label: 'Reseller Portal',
    href: '/reseller-portal',
    icon: Building,
  },
  {
    label: 'Devices',
    href: '/admin/devices',
    icon: Router,
  },
  {
    label: 'Tickets',
    href: '/admin/tickets',
    icon: Ticket,
    badge: '3',
  },
  {
    label: 'Settings',
    href: '/admin/settings',
    icon: Settings,
  },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

  const toggleCollapsed = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div
      className={cn(
        'fixed left-0 top-0 z-40 h-screen flex flex-col bg-white border-r border-gray-200 transition-all duration-300',
        'hidden lg:flex', // Hide on mobile, show on large screens
        isCollapsed ? 'w-16' : 'w-64',
        className
      )}
      style={{
        width: isCollapsed ? layout.sidebar.collapsedWidth : layout.sidebar.width,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!isCollapsed && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">ISP</span>
            </div>
            <span className="font-semibold text-gray-900">Framework</span>
          </div>
        )}
        <button
          onClick={toggleCollapsed}
          className="p-1 rounded-md hover:bg-gray-100 transition-colors"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-gray-500" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-green-50 text-green-700 border-r-2 border-green-600'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                isCollapsed && 'justify-center'
              )}
            >
              <Icon className={cn('w-5 h-5', isCollapsed ? 'mx-auto' : '')} />
              {!isCollapsed && (
                <>
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="px-2 py-1 text-xs bg-red-100 text-red-600 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-200">

          <div className="text-xs text-gray-500">
            ISP Framework v1.0
          </div>
        </div>
      )}
    </div>
  );
}
