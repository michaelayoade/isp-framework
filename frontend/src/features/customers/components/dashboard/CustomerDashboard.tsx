'use client';

import { useState } from 'react';
import { useCustomers } from '../../hooks/useCustomers';
import { CustomerList } from '../list/CustomerList';
import { CustomerFilters } from '../filters/CustomerFilters';
import { CustomerStats } from './CustomerStats';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Users, Download } from 'lucide-react';
import { CreateCustomerForm } from '../forms/CreateCustomerForm';
import type { CustomerFilters as CustomerFiltersType } from '../../types';

export function CustomerDashboard() {
  const [filters, setFilters] = useState<CustomerFiltersType>({
    page: 1,
    per_page: 25,
  });
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const { data, isLoading } = useCustomers(filters);

  const handleFiltersChange = (newFilters: Partial<CustomerFiltersType>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handleExport = async () => {
    // Implementation for export functionality
    console.log('Export customers');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Customers</h1>
          <p className="text-muted-foreground">
            Manage customer accounts and services
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Customer
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Customer</DialogTitle>
              </DialogHeader>
              <CreateCustomerForm
                onSuccess={() => setIsCreateDialogOpen(false)}
                onCancel={() => setIsCreateDialogOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <CustomerStats />

      {/* Main Content */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <Users className="mr-2 h-5 w-5" />
                Customer List
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {data?.total ? `${data.total} customers total` : 'Loading customers...'}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <CustomerFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />
          
          <CustomerList
            data={data}
            isLoading={isLoading}
            onPageChange={(page) => setFilters(prev => ({ ...prev, page }))}
          />
        </CardContent>
      </Card>
    </div>
  );
}
