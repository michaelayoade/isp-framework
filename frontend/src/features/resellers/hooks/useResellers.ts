import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resellerService } from '../services/reseller-service';
import { useToast } from '@/hooks/use-toast';
import type { ResellerFilters, CreateResellerData, UpdateResellerData } from '../types';

export function useResellers(filters: ResellerFilters = {}) {
  return useQuery({
    queryKey: ['resellers', filters],
    queryFn: () => resellerService.getResellers(filters),
    keepPreviousData: true,
  });
}

export function useReseller(id: number) {
  return useQuery({
    queryKey: ['resellers', id],
    queryFn: () => resellerService.getReseller(id),
    enabled: !!id,
  });
}

export function useResellerProfile() {
  return useQuery({
    queryKey: ['reseller', 'profile'],
    queryFn: () => resellerService.getProfile(),
    retry: 1,
  });
}

export function useResellerDashboard() {
  return useQuery({
    queryKey: ['reseller', 'dashboard'],
    queryFn: () => resellerService.getDashboard(),
    retry: 1,
  });
}

export function useResellerCustomers(filters = {}) {
  return useQuery({
    queryKey: ['reseller', 'customers', filters],
    queryFn: () => resellerService.getCustomers(filters),
    keepPreviousData: true,
  });
}

export function useCommissionReports(filters = {}) {
  return useQuery({
    queryKey: ['reseller', 'commissions', filters],
    queryFn: () => resellerService.getCommissionReports(filters),
    keepPreviousData: true,
  });
}

export function useCreateReseller() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateResellerData) => resellerService.createReseller(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resellers'] });
      toast({
        title: 'Success',
        description: 'Reseller created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create reseller',
        variant: 'destructive',
      });
    },
  });
}

export function useUpdateReseller() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateResellerData }) =>
      resellerService.updateReseller(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['resellers'] });
      queryClient.invalidateQueries({ queryKey: ['resellers', id] });
      toast({
        title: 'Success',
        description: 'Reseller updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update reseller',
        variant: 'destructive',
      });
    },
  });
}

export function useDeleteReseller() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => resellerService.deleteReseller(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resellers'] });
      toast({
        title: 'Success',
        description: 'Reseller deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete reseller',
        variant: 'destructive',
      });
    },
  });
}
