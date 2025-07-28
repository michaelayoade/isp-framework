import { useGetInvoices, useGetPayments } from '@/api/billing/iSPFrameworkBillingAPI';
import { toInvoiceUI, toPaymentUI, type InvoiceUI, type PaymentUI } from '@/mappers/billing';
import type { GetInvoicesParams, GetPaymentsParams } from '@/api/_schemas';

export interface InvoiceFilters {
  page?: number;
  per_page?: number;
  customer_id?: number;
  status?: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  date_from?: string;
  date_to?: string;
}

export interface PaymentFilters {
  page?: number;
  per_page?: number;
  customer_id?: number;
  invoice_id?: number;
}

export function useInvoices(filters: InvoiceFilters = {}) {
  // Convert UI filters to API params
  const apiParams: GetInvoicesParams = {
    page: filters.page || 1,
    per_page: filters.per_page || 10,
    customer_id: filters.customer_id,
    status: filters.status,
    date_from: filters.date_from,
    date_to: filters.date_to,
  };

  // Use generated React Query hook
  const { data: response, error, isLoading, refetch } = useGetInvoices(apiParams);

  // Extract data from axios response structure
  const apiData = response?.data;
  
  // Map API response to UI models
  const invoices: InvoiceUI[] = apiData?.data ? apiData.data.map(toInvoiceUI) : [];
  const pagination = apiData?.pagination ?? {
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  };

  return {
    invoices,
    pagination,
    loading: isLoading,
    error: error ? String(error) : null,
    refetch,
  };
}

export function usePayments(filters: PaymentFilters = {}) {
  // Convert UI filters to API params
  const apiParams: GetPaymentsParams = {
    page: filters.page || 1,
    per_page: filters.per_page || 10,
    customer_id: filters.customer_id,
    invoice_id: filters.invoice_id,
  };

  // Use generated React Query hook
  const { data: response, error, isLoading, refetch } = useGetPayments(apiParams);

  // Extract data from axios response structure
  const apiData = response?.data;
  
  // Map API response to UI models
  const payments: PaymentUI[] = apiData?.data ? apiData.data.map(toPaymentUI) : [];
  const pagination = apiData?.pagination ?? {
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  };

  return {
    payments,
    pagination,
    loading: isLoading,
    error: error ? String(error) : null,
    refetch,
  };
}
