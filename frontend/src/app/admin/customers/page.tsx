'use client';

import { useState } from 'react';
import { useCustomers } from '@/features/customers/hooks/useCustomers';
import { 
  useCreateCustomerMutation, 
  useUpdateCustomerMutation, 
  useDeleteCustomerMutation,
  type CustomerFormData 
} from '@/features/customers/hooks/useCustomerMutations';
import { CustomerFormModal } from '@/features/customers/components/CustomerFormModal';
import { CustomerDeleteModal } from '@/features/customers/components/CustomerDeleteModal';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Search, Plus, Eye, Edit, Trash2 } from 'lucide-react';
import type { CustomerFilters } from '@/features/customers/hooks/useCustomers';
import type { CustomerUI } from '@/mappers/customers/customerMapper';

export default function CustomersPage() {
  const [filters, setFilters] = useState<CustomerFilters>({
    page: 1,
    per_page: 10,
  });

  // Modal state management
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerUI | null>(null);

  const { customers, pagination, loading, error, refetch } = useCustomers(filters);
  
  // CRUD mutations
  const createCustomerMutation = useCreateCustomerMutation();
  const updateCustomerMutation = useUpdateCustomerMutation();
  const deleteCustomerMutation = useDeleteCustomerMutation();

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'suspended': return 'destructive';
      case 'inactive': return 'secondary';
      default: return 'outline';
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  // Modal handlers
  const handleCreateCustomer = () => {
    setSelectedCustomer(null);
    setFormModalOpen(true);
  };

  const handleEditCustomer = (customer: CustomerUI) => {
    setSelectedCustomer(customer);
    setFormModalOpen(true);
  };

  const handleDeleteCustomer = (customer: CustomerUI) => {
    setSelectedCustomer(customer);
    setDeleteModalOpen(true);
  };

  const handleViewCustomer = (customer: CustomerUI) => {
    // TODO: Implement customer detail view
    console.log('View customer:', customer);
  };

  // CRUD operations
  const handleFormSubmit = async (data: CustomerFormData) => {
    if (selectedCustomer) {
      // Update existing customer
      await updateCustomerMutation.mutateAsync({ id: selectedCustomer.id, data });
    } else {
      // Create new customer
      await createCustomerMutation.mutateAsync(data);
    }
  };

  const handleConfirmDelete = async (customerId: number) => {
    await deleteCustomerMutation.mutateAsync(customerId);
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Customers</h1>
          <p className="text-muted-foreground">Manage your customer base</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              Error loading customers: {error}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Customers</h1>
        <p className="text-muted-foreground">Manage your customer base</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Customer Management</CardTitle>
          <CardDescription>
            View, filter, and manage customers
          </CardDescription>
          
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
            <div className="space-y-2 w-full sm:w-auto">
              <label className="text-sm font-medium">Search</label>
              <form onSubmit={handleSearch} className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search customers..."
                  value={filters.search || ''}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    search: e.target.value || undefined
                  }))}
                  className="pl-10 w-full sm:w-64"
                />
              </form>
            </div>
            <div className="space-y-2 w-full sm:w-auto">
              <label className="text-sm font-medium">Status</label>
              <Select
                value={filters.status || 'all'}
                onValueChange={(value) => setFilters(prev => ({
                  ...prev,
                  status: value === 'all' ? undefined : value as 'active' | 'inactive' | 'suspended'
                }))}
              >
                <SelectTrigger className="w-full sm:w-40">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <Button 
                variant="outline"
                onClick={() => setFilters({
                  page: 1,
                  per_page: 10,
                  search: undefined,
                  status: undefined,
                })}
                className="w-full sm:w-auto"
              >
                Clear Filters
              </Button>
              <Button onClick={() => refetch()} className="w-full sm:w-auto">
                Refresh
              </Button>
              <Button 
                variant="brand" 
                className="w-full sm:w-auto"
                onClick={handleCreateCustomer}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Customer
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin" />
              <span className="ml-2">Loading customers...</span>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {customers.map((customer) => (
                  <div key={customer.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">{customer.name}</h3>
                        <p className="text-sm text-muted-foreground">{customer.email}</p>
                      </div>
                      <Badge variant={getStatusVariant(customer.status)}>
                        {customer.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                      <div>
                        <span className="font-medium">Phone:</span><br />
                        {customer.phone}
                      </div>
                      <div>
                        <span className="font-medium">Service Plan:</span><br />
                        {customer.servicePlan || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Monthly Fee:</span><br />
                        {customer.monthlyFee ? `$${customer.monthlyFee.toFixed(2)}` : 'N/A'}
                      </div>
                    </div>
                    {customer.address && (
                      <div className="text-sm mb-4">
                        <span className="font-medium">Address:</span><br />
                        <span className="text-muted-foreground">
                          {customer.address.street}, {customer.address.city}, {customer.address.state} {customer.address.zipCode}
                        </span>
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleViewCustomer(customer)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleEditCustomer(customer)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-red-600 hover:text-red-700"
                        onClick={() => handleDeleteCustomer(customer)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {pagination.total_pages && pagination.total_pages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <div className="text-sm text-muted-foreground">
                    Showing {((pagination.page || 1) - 1) * (pagination.per_page || 10) + 1} to{' '}
                    {Math.min((pagination.page || 1) * (pagination.per_page || 10), pagination.total || 0)} of{' '}
                    {pagination.total || 0} customers
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={(pagination.page || 1) <= 1}
                      onClick={() => setFilters(prev => ({ ...prev, page: (prev.page || 1) - 1 }))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={(pagination.page || 1) >= (pagination.total_pages || 1)}
                      onClick={() => setFilters(prev => ({ ...prev, page: (prev.page || 1) + 1 }))}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* CRUD Modals */}
      <CustomerFormModal
        open={formModalOpen}
        onOpenChange={setFormModalOpen}
        customer={selectedCustomer}
        onSubmit={handleFormSubmit}
        loading={createCustomerMutation.isPending || updateCustomerMutation.isPending}
      />

      <CustomerDeleteModal
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        customer={selectedCustomer}
        onConfirm={handleConfirmDelete}
        loading={deleteCustomerMutation.isPending}
      />
    </div>
  );
}
