'use client';

import { useState } from 'react';
import { useInvoices } from '@/features/billing/hooks/useBilling';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';

export default function InvoicesPage() {
  const [filters, setFilters] = useState({
    page: 1,
    per_page: 10,
    customer_id: undefined as number | undefined,
    status: undefined as 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | undefined,
  });

  const { invoices, pagination, loading, error, refetch } = useInvoices(filters);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'sent': return 'brand-outline';
      case 'overdue': return 'destructive';
      case 'draft': return 'secondary';
      case 'cancelled': return 'outline';
      default: return 'secondary';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Invoices</h1>
        <p className="text-muted-foreground">
          Manage customer invoices and billing information
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Invoice Management</CardTitle>
          <CardDescription>
            View, filter, and manage customer invoices
          </CardDescription>
          
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
            <div className="space-y-2 w-full sm:w-auto">
              <label className="text-sm font-medium">Customer ID</label>
              <Input
                type="number"
                placeholder="Filter by customer"
                value={filters.customer_id || ''}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  customer_id: e.target.value ? parseInt(e.target.value) : undefined
                }))}
                className="w-full sm:w-40"
              />
            </div>
            <div className="space-y-2 w-full sm:w-auto">
              <label className="text-sm font-medium">Status</label>
              <Select
                value={filters.status || 'all'}
                onValueChange={(value) => setFilters(prev => ({
                  ...prev,
                  status: value === 'all' ? undefined : value as 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'
                }))}
              >
                <SelectTrigger className="w-full sm:w-40">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <Button 
                variant="outline"
                onClick={() => setFilters({
                  page: 1,
                  per_page: 10,
                  customer_id: undefined,
                  status: undefined,
                })}
                className="w-full sm:w-auto"
              >
                Clear Filters
              </Button>
              <Button onClick={() => refetch()} className="w-full sm:w-auto">
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading invoices...
            </div>
          )}
          
          {error && (
            <div className="text-red-600 py-4">
              Error: {error}
            </div>
          )}
          
          {!loading && !error && (
            <>
              <div className="space-y-4">
                {invoices.map((invoice) => (
                  <div key={invoice.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">{invoice.invoiceNumber}</h3>
                        <p className="text-sm text-muted-foreground">{invoice.customerName}</p>
                      </div>
                      <Badge variant={getStatusVariant(invoice.status)}>
                        {invoice.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Issue Date:</span><br />
                        {invoice.issueDate.toLocaleDateString()}
                      </div>
                      <div>
                        <span className="font-medium">Due Date:</span><br />
                        {invoice.dueDate.toLocaleDateString()}
                      </div>
                      <div>
                        <span className="font-medium">Subtotal:</span><br />
                        ${invoice.subtotal.toFixed(2)}
                      </div>
                      <div>
                        <span className="font-medium">Total:</span><br />
                        <span className="font-bold">${invoice.totalAmount.toFixed(2)}</span>
                      </div>
                    </div>
                    {invoice.lineItems.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <span className="text-sm font-medium">Line Items:</span>
                        <ul className="mt-1 space-y-1">
                          {invoice.lineItems.map((item) => (
                            <li key={item.id} className="text-sm text-muted-foreground">
                              {item.description} - Qty: {item.quantity} × ${item.unitPrice.toFixed(2)} = ${item.totalPrice.toFixed(2)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {invoices.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No invoices found matching the current filters.
                </div>
              )}
              
              <div className="mt-6 flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  Showing {invoices.length} of {pagination.total} invoices
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(pagination.page || 1) <= 1}
                    onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(pagination.page || 1) >= (pagination.total_pages || 1)}
                    onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
