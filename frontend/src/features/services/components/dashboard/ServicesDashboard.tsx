'use client';

import React from 'react';
import { useServiceStats } from '../../hooks/useServices';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Plus, Settings, BarChart3 } from 'lucide-react';

export function ServicesDashboard() {
  const [activeTab, setActiveTab] = useState('catalog');
  const { data: serviceStats } = useServiceStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Services</h1>
          <p className="text-muted-foreground">
            Manage service catalog and customer subscriptions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <BarChart3 className="mr-2 h-4 w-4" />
            Analytics
          </Button>
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Templates
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Service
          </Button>
        </div>
      </div>

      {/* Stats cards */}
      {serviceStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{serviceStats.total_services}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Active Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{serviceStats.active_services}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Internet Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{serviceStats.internet_services}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Monthly Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${serviceStats.monthly_revenue}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="catalog">Service Catalog</TabsTrigger>
          <TabsTrigger value="internet">Internet Services</TabsTrigger>
          <TabsTrigger value="voice">Voice Services</TabsTrigger>
          <TabsTrigger value="bundles">Bundle Packages</TabsTrigger>
          <TabsTrigger value="provisioning">Provisioning</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog">
          <Card>
            <CardHeader>
              <CardTitle>Service Catalog</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Service catalog management interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="internet">
          <Card>
            <CardHeader>
              <CardTitle>Internet Services</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Internet service management interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="voice">
          <Card>
            <CardHeader>
              <CardTitle>Voice Services</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Voice service management interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bundles">
          <Card>
            <CardHeader>
              <CardTitle>Bundle Packages</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Bundle service management interface will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="provisioning">
          <Card>
            <CardHeader>
              <CardTitle>Service Provisioning</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Service provisioning dashboard will be implemented here.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
