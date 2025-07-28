# ISP Framework - Billing Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a comprehensive modular architecture for the billing module frontend, focusing on invoice management, payment processing, financial reporting, and billing analytics.

## Modular Architecture

```
src/features/billing/
├── components/
│   ├── dashboard/              # Billing dashboard components
│   ├── invoices/              # Invoice management
│   ├── payments/              # Payment processing
│   ├── reports/               # Financial reports
│   ├── charts/                # Billing analytics charts
│   └── shared/                # Shared billing components
├── hooks/                     # Billing-specific hooks
├── services/                  # Billing API services
├── types/                     # Billing type definitions
├── utils/                     # Billing utilities
└── constants/                 # Billing constants
```

## 1. Type Definitions

```typescript
// src/features/billing/types/index.ts
export interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  customer_name: string;
  billing_account_id: number;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  balance: number;
  items: InvoiceItem[];
  payments: Payment[];
  created_at: string;
  updated_at: string;
}

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';

export interface InvoiceItem {
  id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
  service_id?: number;
  tax_rate?: number;
}

export interface Payment {
  id: number;
  payment_number: string;
  invoice_id: number;
  customer_id: number;
  amount: number;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  transaction_id?: string;
  payment_date: string;
  notes?: string;
  created_at: string;
}

export type PaymentMethod = 'cash' | 'bank_transfer' | 'credit_card' | 'mobile_money';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export interface BillingStats {
  total_revenue: number;
  monthly_revenue: number;
  outstanding_amount: number;
  overdue_amount: number;
  total_invoices: number;
  paid_invoices: number;
  overdue_invoices: number;
  average_payment_time: number;
}

export interface BillingFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: InvoiceStatus | PaymentStatus;
  customer_id?: number;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
}
```

## 2. Service Layer

```typescript
// src/features/billing/services/billing-service.ts
import { apiClient } from '@/lib/api-client';
import type { 
  Invoice, 
  Payment, 
  BillingStats, 
  BillingFilters,
  PaginatedResponse 
} from '../types';

export class BillingService {
  private readonly basePath = '/billing';

  // Invoice operations
  async getInvoices(filters: BillingFilters = {}): Promise<PaginatedResponse<Invoice>> {
    const response = await apiClient.get(`${this.basePath}/invoices`, { params: filters });
    return response.data;
  }

  async getInvoice(id: number): Promise<Invoice> {
    const response = await apiClient.get(`${this.basePath}/invoices/${id}`);
    return response.data;
  }

  async createInvoice(data: CreateInvoiceData): Promise<Invoice> {
    const response = await apiClient.post(`${this.basePath}/invoices`, data);
    return response.data;
  }

  async updateInvoice(id: number, data: UpdateInvoiceData): Promise<Invoice> {
    const response = await apiClient.put(`${this.basePath}/invoices/${id}`, data);
    return response.data;
  }

  async sendInvoice(id: number): Promise<Invoice> {
    const response = await apiClient.post(`${this.basePath}/invoices/${id}/send`);
    return response.data;
  }

  async cancelInvoice(id: number, reason?: string): Promise<Invoice> {
    const response = await apiClient.post(`${this.basePath}/invoices/${id}/cancel`, { reason });
    return response.data;
  }

  // Payment operations
  async getPayments(filters: BillingFilters = {}): Promise<PaginatedResponse<Payment>> {
    const response = await apiClient.get(`${this.basePath}/payments`, { params: filters });
    return response.data;
  }

  async createPayment(data: CreatePaymentData): Promise<Payment> {
    const response = await apiClient.post(`${this.basePath}/payments`, data);
    return response.data;
  }

  async refundPayment(id: number, amount: number, reason?: string): Promise<Payment> {
    const response = await apiClient.post(`${this.basePath}/payments/${id}/refund`, {
      amount,
      reason,
    });
    return response.data;
  }

  // Analytics and reporting
  async getBillingStats(dateRange?: { from: string; to: string }): Promise<BillingStats> {
    const response = await apiClient.get(`${this.basePath}/stats`, { params: dateRange });
    return response.data;
  }

  async getRevenueChart(period: 'daily' | 'weekly' | 'monthly' = 'monthly'): Promise<ChartData[]> {
    const response = await apiClient.get(`${this.basePath}/charts/revenue`, { 
      params: { period } 
    });
    return response.data;
  }

  async exportInvoices(filters: BillingFilters = {}): Promise<Blob> {
    const response = await apiClient.get(`${this.basePath}/invoices/export`, {
      params: filters,
      responseType: 'blob',
    });
    return response.data;
  }
}

export const billingService = new BillingService();
```

## 3. Core Components

### 3.1 Billing Dashboard

```typescript
// src/features/billing/components/dashboard/BillingDashboard.tsx
'use client';

import { useState } from 'react';
import { useBillingStats, useRevenueChart } from '../../hooks';
import { BillingStatsCards } from './BillingStatsCards';
import { RevenueChart } from '../charts/RevenueChart';
import { RecentInvoices } from '../invoices/RecentInvoices';
import { PaymentSummary } from '../payments/PaymentSummary';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DateRangePicker } from '@/components/ui/date-range-picker';
import { Button } from '@/components/ui/button';
import { Download, Plus, FileText } from 'lucide-react';

export function BillingDashboard() {
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    to: new Date(),
  });

  const { data: stats, isLoading: statsLoading } = useBillingStats(dateRange);
  const { data: revenueData, isLoading: chartLoading } = useRevenueChart('monthly');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Billing & Payments</h1>
          <p className="text-muted-foreground">
            Manage invoices, payments, and financial reporting
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
          />
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Invoice
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && <BillingStatsCards stats={stats} isLoading={statsLoading} />}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <RevenueChart data={revenueData} isLoading={chartLoading} />
            </CardContent>
          </Card>
        </div>

        {/* Payment Summary */}
        <div>
          <PaymentSummary />
        </div>
      </div>

      {/* Tabs for detailed views */}
      <Tabs defaultValue="invoices" className="space-y-4">
        <TabsList>
          <TabsTrigger value="invoices">Recent Invoices</TabsTrigger>
          <TabsTrigger value="payments">Recent Payments</TabsTrigger>
          <TabsTrigger value="overdue">Overdue Items</TabsTrigger>
        </TabsList>

        <TabsContent value="invoices">
          <RecentInvoices />
        </TabsContent>

        <TabsContent value="payments">
          <RecentPayments />
        </TabsContent>

        <TabsContent value="overdue">
          <OverdueInvoices />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3.2 Invoice Management

```typescript
// src/features/billing/components/invoices/InvoiceList.tsx
'use client';

import { useMemo, useState } from 'react';
import { useInvoices } from '../../hooks';
import { InvoiceStatusBadge } from './InvoiceStatusBadge';
import { InvoiceActions } from './InvoiceActions';
import { DataTable } from '@/components/ui/data-table';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Invoice, BillingFilters } from '../../types';

export function InvoiceList() {
  const [filters, setFilters] = useState<BillingFilters>({
    page: 1,
    per_page: 25,
  });

  const { data, isLoading } = useInvoices(filters);

  const columns = useMemo(() => [
    {
      accessorKey: 'invoice_number',
      header: 'Invoice #',
      cell: ({ row }) => (
        <div className="font-medium">
          {row.original.invoice_number}
        </div>
      ),
    },
    {
      accessorKey: 'customer_name',
      header: 'Customer',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.customer_name}</div>
          <div className="text-sm text-muted-foreground">
            ID: {row.original.customer_id}
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'issue_date',
      header: 'Issue Date',
      cell: ({ getValue }) => formatDate(getValue() as string),
    },
    {
      accessorKey: 'due_date',
      header: 'Due Date',
      cell: ({ getValue }) => formatDate(getValue() as string),
    },
    {
      accessorKey: 'total_amount',
      header: 'Amount',
      cell: ({ getValue }) => formatCurrency(getValue() as number),
    },
    {
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ getValue }) => {
        const balance = getValue() as number;
        return (
          <span className={balance > 0 ? 'text-red-600' : 'text-green-600'}>
            {formatCurrency(balance)}
          </span>
        );
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => (
        <InvoiceStatusBadge status={getValue() as InvoiceStatus} />
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => <InvoiceActions invoice={row.original} />,
    },
  ], []);

  return (
    <DataTable
      columns={columns}
      data={data?.items || []}
      isLoading={isLoading}
      pagination={{
        pageIndex: (filters.page || 1) - 1,
        pageSize: filters.per_page || 25,
      }}
      onPaginationChange={(pagination) => {
        setFilters(prev => ({
          ...prev,
          page: pagination.pageIndex + 1,
          per_page: pagination.pageSize,
        }));
      }}
    />
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/billing/hooks/useBilling.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { billingService } from '../services';
import { useToast } from '@/hooks/use-toast';
import type { BillingFilters, CreateInvoiceData, CreatePaymentData } from '../types';

export function useInvoices(filters: BillingFilters = {}) {
  return useQuery({
    queryKey: ['invoices', filters],
    queryFn: () => billingService.getInvoices(filters),
    keepPreviousData: true,
  });
}

export function useInvoice(id: number) {
  return useQuery({
    queryKey: ['invoices', id],
    queryFn: () => billingService.getInvoice(id),
    enabled: !!id,
  });
}

export function useCreateInvoice() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateInvoiceData) => billingService.createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing-stats'] });
      toast({
        title: 'Success',
        description: 'Invoice created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create invoice',
        variant: 'destructive',
      });
    },
  });
}

export function usePayments(filters: BillingFilters = {}) {
  return useQuery({
    queryKey: ['payments', filters],
    queryFn: () => billingService.getPayments(filters),
    keepPreviousData: true,
  });
}

export function useCreatePayment() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreatePaymentData) => billingService.createPayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing-stats'] });
      toast({
        title: 'Success',
        description: 'Payment recorded successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to record payment',
        variant: 'destructive',
      });
    },
  });
}

export function useBillingStats(dateRange?: { from: Date; to: Date }) {
  return useQuery({
    queryKey: ['billing-stats', dateRange],
    queryFn: () => billingService.getBillingStats(
      dateRange ? {
        from: dateRange.from.toISOString(),
        to: dateRange.to.toISOString(),
      } : undefined
    ),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export function useRevenueChart(period: 'daily' | 'weekly' | 'monthly' = 'monthly') {
  return useQuery({
    queryKey: ['revenue-chart', period],
    queryFn: () => billingService.getRevenueChart(period),
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });
}
```

## 5. Utility Functions

```typescript
// src/features/billing/utils/index.ts
import type { Invoice, Payment, InvoiceStatus, PaymentStatus } from '../types';

export function getInvoiceStatusColor(status: InvoiceStatus): string {
  const colors = {
    draft: 'bg-gray-100 text-gray-800',
    sent: 'bg-blue-100 text-blue-800',
    paid: 'bg-green-100 text-green-800',
    overdue: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  };
  return colors[status] || colors.draft;
}

export function getPaymentStatusColor(status: PaymentStatus): string {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    refunded: 'bg-gray-100 text-gray-800',
  };
  return colors[status] || colors.pending;
}

export function calculateInvoiceBalance(invoice: Invoice): number {
  return invoice.total_amount - invoice.paid_amount;
}

export function isInvoiceOverdue(invoice: Invoice): boolean {
  if (invoice.status === 'paid' || invoice.status === 'cancelled') {
    return false;
  }
  return new Date(invoice.due_date) < new Date();
}

export function calculatePaymentTotal(payments: Payment[]): number {
  return payments
    .filter(payment => payment.status === 'completed')
    .reduce((total, payment) => total + payment.amount, 0);
}

export function formatInvoiceNumber(invoice: Invoice): string {
  return invoice.invoice_number || `INV-${invoice.id.toString().padStart(6, '0')}`;
}

export function generateInvoicePDF(invoice: Invoice): Promise<Blob> {
  // Implementation for PDF generation
  // This would typically use a library like jsPDF or call a backend endpoint
  return Promise.resolve(new Blob());
}

export function validateInvoiceData(data: any): string[] {
  const errors: string[] = [];
  
  if (!data.customer_id) {
    errors.push('Customer is required');
  }
  
  if (!data.items || data.items.length === 0) {
    errors.push('At least one invoice item is required');
  }
  
  if (data.items) {
    data.items.forEach((item: any, index: number) => {
      if (!item.description) {
        errors.push(`Item ${index + 1}: Description is required`);
      }
      if (!item.quantity || item.quantity <= 0) {
        errors.push(`Item ${index + 1}: Quantity must be greater than 0`);
      }
      if (!item.unit_price || item.unit_price <= 0) {
        errors.push(`Item ${index + 1}: Unit price must be greater than 0`);
      }
    });
  }
  
  return errors;
}
```

## 6. Constants

```typescript
// src/features/billing/constants/index.ts
export const INVOICE_STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft', color: 'gray' },
  { value: 'sent', label: 'Sent', color: 'blue' },
  { value: 'paid', label: 'Paid', color: 'green' },
  { value: 'overdue', label: 'Overdue', color: 'red' },
  { value: 'cancelled', label: 'Cancelled', color: 'gray' },
] as const;

export const PAYMENT_METHOD_OPTIONS = [
  { value: 'cash', label: 'Cash', icon: 'Banknote' },
  { value: 'bank_transfer', label: 'Bank Transfer', icon: 'Building2' },
  { value: 'credit_card', label: 'Credit Card', icon: 'CreditCard' },
  { value: 'mobile_money', label: 'Mobile Money', icon: 'Smartphone' },
] as const;

export const PAYMENT_STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending', color: 'yellow' },
  { value: 'completed', label: 'Completed', color: 'green' },
  { value: 'failed', label: 'Failed', color: 'red' },
  { value: 'refunded', label: 'Refunded', color: 'gray' },
] as const;

export const BILLING_PERIODS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
] as const;

export const EXPORT_FORMATS = [
  { value: 'csv', label: 'CSV', extension: '.csv' },
  { value: 'xlsx', label: 'Excel', extension: '.xlsx' },
  { value: 'pdf', label: 'PDF', extension: '.pdf' },
] as const;
```

## 7. Implementation Phases

### Phase 1: Core Structure (Days 1-2)
- Set up feature module structure
- Implement types and service layer
- Create basic hooks

### Phase 2: Invoice Management (Days 3-4)
- Build invoice list and detail views
- Implement invoice creation/editing forms
- Add invoice actions (send, cancel, etc.)

### Phase 3: Payment Processing (Days 5-6)
- Create payment recording interface
- Build payment history views
- Implement refund functionality

### Phase 4: Analytics & Reporting (Days 7-8)
- Build billing dashboard with stats
- Create revenue charts and analytics
- Implement export functionality

This modular architecture ensures the billing module is comprehensive, maintainable, and easily extensible for future financial features.
