'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Settings } from 'lucide-react';

// Mock data - replace with actual API call
const mockStats = {
  total_sent: 1247,
  total_delivered: 1156,
  delivery_rate: 92.7,
  open_rate: 24.5,
};

export function CommunicationsDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Communications</h1>
          <p className="text-muted-foreground">Manage templates and campaigns</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Sent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.total_sent}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Delivered</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.total_delivered}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Delivery Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.delivery_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Open Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.open_rate}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Main content placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Communication Templates</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Template management interface will be implemented here.</p>
        </CardContent>
      </Card>
    </div>
  );
}
