'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Router, Server, Globe } from 'lucide-react';

// Mock data - replace with actual API calls
const mockStats = {
  total_networks: 15,
  total_ips: 2048,
  assigned_ips: 1247,
  available_ips: 801,
  utilization_percentage: 60.9,
  active_devices: 23,
  offline_devices: 2,
};

export function NetworkingDashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Networking & IPAM</h1>
          <p className="text-muted-foreground">
            Manage IP addresses, network devices, and infrastructure
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Globe className="mr-2 h-4 w-4" />
            Network Map
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Network
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total IP Addresses</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.total_ips.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {mockStats.assigned_ips} assigned, {mockStats.available_ips} available
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">IP Utilization</CardTitle>
            <div className="h-4 w-4 rounded-full bg-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.utilization_percentage}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div 
                className="bg-blue-500 h-2 rounded-full" 
                style={{ width: `${mockStats.utilization_percentage}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Devices</CardTitle>
            <Router className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.active_devices}</div>
            <p className="text-xs text-muted-foreground">
              {mockStats.offline_devices} offline
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Networks</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.total_networks}</div>
            <p className="text-xs text-muted-foreground">
              Across all sites
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="networks">Networks</TabsTrigger>
          <TabsTrigger value="devices">Devices</TabsTrigger>
          <TabsTrigger value="ip-management">IP Management</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Network Topology</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Network topology visualization will be implemented here.</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Device Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center">
                      <Badge variant="default" className="mr-2">Online</Badge>
                      Routers
                    </span>
                    <span>8/10</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center">
                      <Badge variant="default" className="mr-2">Online</Badge>
                      Switches
                    </span>
                    <span>15/15</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center">
                      <Badge variant="destructive" className="mr-2">Offline</Badge>
                      Access Points
                    </span>
                    <span>2/5</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="networks">
          <Card>
            <CardHeader>
              <CardTitle>Network Management</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Network configuration and management interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="devices">
          <Card>
            <CardHeader>
              <CardTitle>Device Management</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Network device monitoring and configuration interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ip-management">
          <Card>
            <CardHeader>
              <CardTitle>IP Address Management</CardTitle>
            </CardHeader>
            <CardContent>
              <p>IP address allocation and management interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring">
          <Card>
            <CardHeader>
              <CardTitle>Network Monitoring</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Real-time network monitoring and alerts will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
