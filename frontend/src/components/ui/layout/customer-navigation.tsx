'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/utils/cn';
import { 
  Home, 
  User, 
  CreditCard, 
  Settings, 
  Ticket, 
  Wifi,
  FileText
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', href: '/customer/dashboard', icon: Home },
  { name: 'Profile', href: '/customer/profile', icon: User },
  { name: 'Services', href: '/customer/services', icon: Wifi },
  { name: 'Billing', href: '/customer/billing', icon: CreditCard },
  { name: 'Tickets', href: '/customer/tickets', icon: Ticket },
  { name: 'Documents', href: '/customer/documents', icon: FileText },
  { name: 'Settings', href: '/customer/settings', icon: Settings },
];

export function CustomerNavigation() {
  const pathname = usePathname();
  
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex space-x-8 overflow-x-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center py-4 px-1 border-b-2 text-sm font-medium whitespace-nowrap',
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <Icon className="h-5 w-5 mr-2" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
