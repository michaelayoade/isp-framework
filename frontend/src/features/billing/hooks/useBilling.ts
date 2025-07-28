import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { billingService, InvoiceListResponse, PaymentListResponse, BillingOverview, Invoice, InvoiceCreate, PaymentCreate, InvoiceFilters } from '../services/billing-service';
import { useToast } from '@/hooks/use-toast';

export function useBillingOverview() {
  return useQuery<BillingOverview>({
    queryKey: ['billing', 'overview'],
    queryFn: () => billingService.getBillingOverview(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export function useInvoices(filters = {}) {
  return useQuery<InvoiceListResponse>({
    queryKey: ['billing', 'invoices', filters],
    queryFn: () => billingService.getInvoices(filters),
  });
}

export function useInvoice(id: string) {
  return useQuery<Invoice>({
    queryKey: ['billing', 'invoices', id],
    queryFn: () => billingService.getInvoice(id),
    enabled: !!id,
  });
}

export function usePayments(filters = {}) {
  return useQuery<PaymentListResponse>({
    queryKey: ['billing', 'payments', filters],
    queryFn: () => billingService.getPayments(filters),
  });
}

export function useCreateInvoice() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: billingService.createInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing', 'overview'] });
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

export function useUpdateInvoice() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<InvoiceCreate> }) =>
      billingService.updateInvoice(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['billing', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing', 'invoices', id] });
      queryClient.invalidateQueries({ queryKey: ['billing', 'overview'] });
      toast({
        title: 'Success',
        description: 'Invoice updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update invoice',
        variant: 'destructive',
      });
    },
  });
}

export function useDeleteInvoice() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: billingService.deleteInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing', 'overview'] });
      toast({
        title: 'Success',
        description: 'Invoice deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete invoice',
        variant: 'destructive',
      });
    },
  });
}

export function useRecordPayment() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ data }: { data: PaymentCreate }) =>
      billingService.createPayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing', 'payments'] });
      queryClient.invalidateQueries({ queryKey: ['billing', 'overview'] });
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

export function useExportInvoices() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ format, filters }: { format: 'csv' | 'xlsx'; filters?: InvoiceFilters }) =>
      billingService.exportInvoices(filters, format),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Export completed successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to export data',
        variant: 'destructive',
      });
    },
  });
}
