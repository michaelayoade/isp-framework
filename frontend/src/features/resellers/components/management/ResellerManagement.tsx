'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Search, Plus } from 'lucide-react';

interface ResellerManagementProps {
  className?: string;
}

export function ResellerManagement({ className }: ResellerManagementProps) {
  return (
    <div className={className}>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Reseller Management</CardTitle>
            <CardDescription>
              Manage reseller accounts and permissions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search resellers..." className="pl-8" />
              </div>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Reseller
              </Button>
            </div>

            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Customers</TableHead>
                    <TableHead>Commission</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                      No resellers found. Add your first reseller to get started.
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Commission Settings</CardTitle>
            <CardDescription>
              Configure commission rates and payment settings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Default Commission Rate</label>
                <Input type="number" placeholder="10" className="mt-1" />
                <p className="text-xs text-muted-foreground mt-1">Percentage of revenue</p>
              </div>
              <div>
                <label className="text-sm font-medium">Payment Schedule</label>
                <select className="w-full mt-1 px-3 py-2 border border-input bg-background rounded-md">
                  <option>Monthly</option>
                  <option>Quarterly</option>
                  <option>Annually</option>
                </select>
              </div>
            </div>
            <Button className="mt-4">Save Settings</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ResellerManagement;
