'use client';

import { useState } from 'react';
import { Customer, CustomerFilters } from '@/features/customers/types';
import { useCustomers } from '@/features/customers/hooks/useCustomers';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface CustomerListProps {
  onCustomerSelect?: (customer: Customer) => void;
  onCreateCustomer?: () => void;
}

export function CustomerList({ onCustomerSelect, onCreateCustomer }: CustomerListProps) {
  const [filters, setFilters] = useState<CustomerFilters>({});
  const { customers, loading, error, pagination, updateFilters } = useCustomers(filters);

  const handleFilterChange = (key: keyof CustomerFilters, value: string) => {
    const newFilters = { ...filters, [key]: value || undefined };
    setFilters(newFilters);
    updateFilters(newFilters);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-100 text-green-800">Active</Badge>;
      case 'suspended':
        return <Badge variant="destructive">Suspended</Badge>;
      case 'pending':
        return <Badge variant="secondary">Pending</Badge>;
      case 'cancelled':
        return <Badge variant="outline">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="text-muted-foreground">Loading customers...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            Error loading customers: {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Customer List</CardTitle>
            <CardDescription>
              Manage your customer base ({pagination.total} total customers)
            </CardDescription>
          </div>
          {onCreateCustomer && (
            <Button onClick={onCreateCustomer}>
              Add Customer
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex items-center space-x-2 mb-4">
          <Input
            placeholder="Search customers..."
            value={filters.search || ''}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="max-w-sm"
          />
          <Select
            value={filters.status || 'all'}
            onValueChange={(value) => handleFilterChange('status', value === 'all' ? '' : value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="suspended">Suspended</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Customer Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Service Plan</TableHead>
                <TableHead>Monthly Fee</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {customers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No customers found
                  </TableCell>
                </TableRow>
              ) : (
                customers.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell className="font-medium">
                      {customer.first_name} {customer.last_name}
                    </TableCell>
                    <TableCell>{customer.email}</TableCell>
                    <TableCell>{customer.phone}</TableCell>
                    <TableCell>{getStatusBadge(customer.status)}</TableCell>
                    <TableCell>{customer.service_plan}</TableCell>
                    <TableCell>${customer.monthly_fee}</TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onCustomerSelect?.(customer)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {pagination.total_pages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Showing {((pagination.page - 1) * pagination.per_page) + 1} to{' '}
              {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
              {pagination.total} customers
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.page <= 1}
                onClick={() => handleFilterChange('page', (pagination.page - 1).toString())}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.page >= pagination.total_pages}
                onClick={() => handleFilterChange('page', (pagination.page + 1).toString())}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
