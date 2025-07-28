'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, Plus, Eye, Settings } from 'lucide-react';

interface ResellerPortalProps {
  className?: string;
}

export function ResellerPortal({ className }: ResellerPortalProps) {
  return (
    <div className={className}>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Customer Management
            </CardTitle>
            <CardDescription>
              Manage your customers and their services
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Customer
              </Button>
              <Button variant="outline">
                <Eye className="h-4 w-4 mr-2" />
                View All
              </Button>
            </div>
            <div className="text-sm text-muted-foreground">
              No customers registered yet. Start by adding your first customer.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
            <CardDescription>
              Your reseller account overview
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center">
                <div className="text-2xl font-bold">0</div>
                <div className="text-sm text-muted-foreground">Total Customers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">$0.00</div>
                <div className="text-sm text-muted-foreground">Monthly Commission</div>
              </div>
              <div className="text-center">
                <Badge variant="secondary">Active</Badge>
                <div className="text-sm text-muted-foreground mt-1">Account Status</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Account Settings
            </CardTitle>
            <CardDescription>
              Manage your reseller account preferences
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline">
              Update Profile
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ResellerPortal;
