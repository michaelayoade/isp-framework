'use client';

import { useState } from 'react';
import { usePayments } from '@/features/billing/hooks/useBilling';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

export default function PaymentsPage() {
  const [filters, setFilters] = useState({
    page: 1,
    per_page: 10,
    customer_id: undefined as number | undefined,
    invoice_id: undefined as number | undefined,
  });

  const { payments, pagination, loading, error, refetch } = usePayments(filters);

  const getPaymentMethodVariant = (method: string) => {
    switch (method) {
      case 'credit_card': return 'brand-outline';
      case 'bank_transfer': return 'secondary';
      case 'cash': return 'success';
      case 'check': return 'outline';
      default: return 'secondary';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Payments</h1>
        <p className="text-muted-foreground">
          Track and manage customer payments
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Payment Management</CardTitle>
          <CardDescription>
            View and track customer payment records
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
              <label className="text-sm font-medium">Invoice ID</label>
              <Input
                type="number"
                placeholder="Filter by invoice"
                value={filters.invoice_id || ''}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  invoice_id: e.target.value ? parseInt(e.target.value) : undefined
                }))}
                className="w-full sm:w-40"
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <Button 
                variant="outline"
                onClick={() => setFilters({
                  page: 1,
                  per_page: 10,
                  customer_id: undefined,
                  invoice_id: undefined,
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
              Loading payments...
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
                {payments.map((payment) => (
                  <div key={payment.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">Payment #{payment.id}</h3>
                        <p className="text-sm text-muted-foreground">
                          Invoice #{payment.invoiceId} • Customer #{payment.customerId}
                        </p>
                      </div>
                      <Badge variant={getPaymentMethodVariant(payment.paymentMethod)}>
                        {payment.paymentMethod.replace('_', ' ')}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Amount:</span><br />
                        <span className="font-bold">${payment.amount.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="font-medium">Payment Date:</span><br />
                        {payment.paymentDate.toLocaleDateString()}
                      </div>
                      <div>
                        <span className="font-medium">Reference:</span><br />
                        {payment.referenceNumber || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Currency:</span><br />
                        {payment.currency}
                      </div>
                    </div>
                    {payment.notes && (
                      <div className="mt-3 pt-3 border-t">
                        <span className="text-sm font-medium">Notes:</span>
                        <p className="text-sm text-muted-foreground mt-1">{payment.notes}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {payments.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No payments found matching the current filters.
                </div>
              )}
              
              <div className="mt-6 flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  Showing {payments.length} of {pagination.total} payments
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
