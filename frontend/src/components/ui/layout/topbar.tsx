'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { cn } from '@/utils/cn';
import { layout } from '@/lib/design-tokens';
import {
  Search,
  Bell,
  ChevronDown,
  User,
  Settings,
  LogOut,
  Building2,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface TopbarProps {
  className?: string;
}

export function Topbar({ className }: TopbarProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data - replace with real data from context/API
  const currentUser = {
    name: 'John Admin',
    email: 'admin@ispframework.com',
    avatar: null,
  };

  const currentTenant = {
    name: 'ISP Framework Demo',
    plan: 'Enterprise',
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/admin/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    // Implement logout logic
    router.push('/login');
  };

  return (
    <header
      className={cn(
        'flex items-center justify-between px-6 bg-white border-b border-gray-200',
        className
      )}
      style={{ height: layout.topbar.height }}
    >
      {/* Left: Search */}
      <div className="flex items-center space-x-4 flex-1 max-w-md">
        <form onSubmit={handleSearch} className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search customers, devices, tickets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 w-full"
          />
        </form>
      </div>

      {/* Right: Tenant, Notifications, Profile */}
      <div className="flex items-center space-x-4">
        {/* Tenant Switcher */}
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors">
            <Building2 className="w-4 h-4 text-gray-500" />
            <div className="text-left">
              <div className="text-sm font-medium text-gray-900">
                {currentTenant.name}
              </div>
              <div className="text-xs text-gray-500">{currentTenant.plan}</div>
            </div>
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Switch Tenant</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Building2 className="w-4 h-4 mr-2" />
              ISP Framework Demo
              <Badge variant="secondary" className="ml-auto">
                Current
              </Badge>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Building2 className="w-4 h-4 mr-2" />
              Regional ISP Co.
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Settings className="w-4 h-4 mr-2" />
              Tenant Settings
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger className="relative p-2 rounded-lg hover:bg-gray-50 transition-colors">
            <Bell className="w-5 h-5 text-gray-500" />
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center text-xs"
            >
              3
            </Badge>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="max-h-64 overflow-y-auto">
              <DropdownMenuItem className="flex-col items-start p-4">
                <div className="font-medium text-sm">Payment Failed</div>
                <div className="text-xs text-gray-500 mt-1">
                  Customer John Doe&apos;s payment was declined
                </div>
                <div className="text-xs text-gray-400 mt-1">2 minutes ago</div>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex-col items-start p-4">
                <div className="font-medium text-sm">Device Offline</div>
                <div className="text-xs text-gray-500 mt-1">
                  Router RT-001 has been offline for 15 minutes
                </div>
                <div className="text-xs text-gray-400 mt-1">15 minutes ago</div>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex-col items-start p-4">
                <div className="font-medium text-sm">New Ticket</div>
                <div className="text-xs text-gray-500 mt-1">
                  Support ticket #1234 created by Jane Smith
                </div>
                <span className="text-sm text-muted-foreground">John&apos;s ISP</span>
              </DropdownMenuItem>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="justify-center">
              View All Notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Profile Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
              {currentUser.avatar ? (
                <Image
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  width={32}
                  height={32}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <User className="w-4 h-4 text-white" />
              )}
            </div>
            <div className="text-left hidden md:block">
              <div className="text-sm font-medium text-gray-900">
                {currentUser.name}
              </div>
              <div className="text-xs text-gray-500">{currentUser.email}</div>
            </div>
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="w-4 h-4 mr-2" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
