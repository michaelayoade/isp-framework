'use client';

import { useState } from 'react';
import { useInvoices, usePayments } from '@/features/billing/hooks/useBilling';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { Loader2 } from 'lucide-react';

export default function BillingTestPage() {
  const [invoiceFilters, setInvoiceFilters] = useState({
    page: 1,
    per_page: 10,
    customer_id: undefined as number | undefined,
    status: undefined as 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | undefined,
  });

  const [paymentFilters, setPaymentFilters] = useState({
    page: 1,
    per_page: 10,
    customer_id: undefined as number | undefined,
    invoice_id: undefined as number | undefined,
  });

  const { invoices, pagination: invoicePagination, loading: invoicesLoading, error: invoicesError } = useInvoices(invoiceFilters);
  const { payments, pagination: paymentPagination, loading: paymentsLoading, error: paymentsError } = usePayments(paymentFilters);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'bg-green-100 text-green-800';
      case 'sent': return 'bg-blue-100 text-blue-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentMethodColor = (method: string) => {
    switch (method) {
      case 'credit_card': return 'bg-purple-100 text-purple-800';
      case 'bank_transfer': return 'bg-blue-100 text-blue-800';
      case 'cash': return 'bg-green-100 text-green-800';
      case 'check': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Billing Module Test Page</h1>
        <p className="text-muted-foreground mt-2">
          Testing contract-first API integration with generated clients, mappers, and MSW mocking
        </p>
      </div>

      {/* Invoices Section */}
      <Card>
        <CardHeader>
          <CardTitle>Invoices</CardTitle>
          <CardDescription>
            Generated from OpenAPI spec → Orval client → Data mappers → React Query hooks
          </CardDescription>
          
          {/* Invoice Filters */}
          <div className="flex gap-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Customer ID</label>
              <Input
                type="number"
                placeholder="Filter by customer"
                value={invoiceFilters.customer_id || ''}
                onChange={(e) => setInvoiceFilters(prev => ({
                  ...prev,
                  customer_id: e.target.value ? parseInt(e.target.value) : undefined
                }))}
                className="w-40"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select
                value={invoiceFilters.status || ''}
                onValueChange={(value) => setInvoiceFilters(prev => ({
                  ...prev,
                  status: value as 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' || undefined
                }))}
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All statuses</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button 
              variant="outline"
              onClick={() => setInvoiceFilters({
                page: 1,
                per_page: 10,
                customer_id: undefined,
                status: undefined,
              })}
            >
              Clear Filters
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {invoicesLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading invoices...
            </div>
          )}
          
          {invoicesError && (
            <div className="text-red-600 py-4">
              Error: {invoicesError}
            </div>
          )}
          
          {!invoicesLoading && !invoicesError && (
            <>
              <div className="space-y-4">
                {invoices.map((invoice) => (
                  <div key={invoice.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">{invoice.invoiceNumber}</h3>
                        <p className="text-sm text-muted-foreground">{invoice.customerName}</p>
                      </div>
                      <Badge className={getStatusColor(invoice.status)}>
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
                  Showing {invoices.length} of {invoicePagination.total} invoices
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(invoicePagination.page || 1) <= 1}
                    onClick={() => setInvoiceFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(invoicePagination.page || 1) >= (invoicePagination.total_pages || 1)}
                    onClick={() => setInvoiceFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="border-t my-8" />

      {/* Payments Section */}
      <Card>
        <CardHeader>
          <CardTitle>Payments</CardTitle>
          <CardDescription>
            Real-time payment data with filtering and pagination
          </CardDescription>
          
          {/* Payment Filters */}
          <div className="flex gap-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Customer ID</label>
              <Input
                type="number"
                placeholder="Filter by customer"
                value={paymentFilters.customer_id || ''}
                onChange={(e) => setPaymentFilters(prev => ({
                  ...prev,
                  customer_id: e.target.value ? parseInt(e.target.value) : undefined
                }))}
                className="w-40"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Invoice ID</label>
              <Input
                type="number"
                placeholder="Filter by invoice"
                value={paymentFilters.invoice_id || ''}
                onChange={(e) => setPaymentFilters(prev => ({
                  ...prev,
                  invoice_id: e.target.value ? parseInt(e.target.value) : undefined
                }))}
                className="w-40"
              />
            </div>
            <Button 
              variant="outline"
              onClick={() => setPaymentFilters({
                page: 1,
                per_page: 10,
                customer_id: undefined,
                invoice_id: undefined,
              })}
            >
              Clear Filters
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {paymentsLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading payments...
            </div>
          )}
          
          {paymentsError && (
            <div className="text-red-600 py-4">
              Error: {paymentsError}
            </div>
          )}
          
          {!paymentsLoading && !paymentsError && (
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
                      <Badge className={getPaymentMethodColor(payment.paymentMethod)}>
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
                  Showing {payments.length} of {paymentPagination.total} payments
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(paymentPagination.page || 1) <= 1}
                    onClick={() => setPaymentFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(paymentPagination.page || 1) >= (paymentPagination.total_pages || 1)}
                    onClick={() => setPaymentFilters(prev => ({ ...prev, page: prev.page + 1 }))}
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
