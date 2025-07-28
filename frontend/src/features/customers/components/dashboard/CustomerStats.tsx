'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, UserCheck, UserX, TrendingUp } from 'lucide-react';

// Mock data - replace with actual API call
const mockStats = {
  total_customers: 1247,
  active_customers: 1156,
  suspended_customers: 67,
  new_this_month: 23,
  growth_rate: 8.5,
};

export function CustomerStats() {
  const stats = mockStats; // Replace with actual hook call

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_customers.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            All registered customers
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Customers</CardTitle>
          <UserCheck className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.active_customers.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            Currently active accounts
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Suspended</CardTitle>
          <UserX className="h-4 w-4 text-red-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.suspended_customers}</div>
          <p className="text-xs text-muted-foreground">
            Suspended accounts
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">New This Month</CardTitle>
          <TrendingUp className="h-4 w-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.new_this_month}</div>
          <p className="text-xs text-muted-foreground">
            +{stats.growth_rate}% from last month
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
