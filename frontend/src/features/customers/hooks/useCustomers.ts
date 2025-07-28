import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { customerService } from '../services/customer-service';
import { useToast } from '@/hooks/use-toast';
import type { CustomerFilters, CreateCustomerData, UpdateCustomerData } from '../types';

export function useCustomers(filters: CustomerFilters = {}) {
  return useQuery({
    queryKey: ['customers', filters],
    queryFn: () => customerService.getCustomers(filters),
  });
}

export function useCustomer(id: number) {
  return useQuery({
    queryKey: ['customers', id],
    queryFn: () => customerService.getCustomer(id),
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateCustomerData) => customerService.createCustomer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      toast({
        title: 'Success',
        description: 'Customer created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create customer',
        variant: 'destructive',
      });
    },
  });
}

export function useUpdateCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateCustomerData }) =>
      customerService.updateCustomer(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customers', id] });
      toast({
        title: 'Success',
        description: 'Customer updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update customer',
        variant: 'destructive',
      });
    },
  });
}

export function useDeleteCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => customerService.deleteCustomer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      toast({
        title: 'Success',
        description: 'Customer deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete customer',
        variant: 'destructive',
      });
    },
  });
}

export function useSuspendCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      customerService.suspendCustomer(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customers', id] });
      toast({
        title: 'Success',
        description: 'Customer suspended successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to suspend customer',
        variant: 'destructive',
      });
    },
  });
}

export function useReactivateCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => customerService.reactivateCustomer(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customers', id] });
      toast({
        title: 'Success',
        description: 'Customer reactivated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to reactivate customer',
        variant: 'destructive',
      });
    },
  });
}

export function useCustomerServices(customerId: number) {
  return useQuery({
    queryKey: ['customers', customerId, 'services'],
    queryFn: () => customerService.getCustomerServices(customerId),
    enabled: !!customerId,
  });
}

export function useCustomerBilling(customerId: number) {
  return useQuery({
    queryKey: ['customers', customerId, 'billing'],
    queryFn: () => customerService.getCustomerBilling(customerId),
    enabled: !!customerId,
  });
}
