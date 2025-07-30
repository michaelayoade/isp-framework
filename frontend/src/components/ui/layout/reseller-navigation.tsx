'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/utils/cn';
import { 
  Home, 
  Users, 
  CreditCard, 
  Settings, 
  Ticket, 
  Wifi,
  FileText,
  BarChart3
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', href: '/reseller/dashboard', icon: Home },
  { name: 'Customers', href: '/reseller/customers', icon: Users },
  { name: 'Services', href: '/reseller/services', icon: Wifi },
  { name: 'Billing', href: '/reseller/billing', icon: CreditCard },
  { name: 'Reports', href: '/reseller/reports', icon: BarChart3 },
  { name: 'Tickets', href: '/reseller/tickets', icon: Ticket },
  { name: 'Documents', href: '/reseller/documents', icon: FileText },
  { name: 'Settings', href: '/reseller/settings', icon: Settings },
];

export function ResellerNavigation() {
  const pathname = usePathname();
  
  return (
    <nav className="bg-white border-r border-gray-200 w-64 flex-shrink-0 min-h-screen">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Navigation</h2>
        <ul className="space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center px-3 py-2 text-sm font-medium rounded-md',
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
