import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serviceManagementService } from '../services/service-management';
import { useToast } from '@/hooks/use-toast';
import type { ServiceFilters, CreateInternetServiceData } from '../types';

export function useServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', filters],
    queryFn: () => serviceManagementService.getServices(filters),
    keepPreviousData: true,
  });
}

export function useInternetServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', 'internet', filters],
    queryFn: () => serviceManagementService.getInternetServices(filters),
    keepPreviousData: true,
  });
}

export function useVoiceServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', 'voice', filters],
    queryFn: () => serviceManagementService.getVoiceServices(filters),
    keepPreviousData: true,
  });
}

export function useBundleServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', 'bundles', filters],
    queryFn: () => serviceManagementService.getBundleServices(filters),
    keepPreviousData: true,
  });
}

export function useCustomerServices(customerId: number) {
  return useQuery({
    queryKey: ['customers', customerId, 'services'],
    queryFn: () => serviceManagementService.getCustomerServices(customerId),
    enabled: !!customerId,
  });
}

export function useCreateInternetService() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateInternetServiceData) => 
      serviceManagementService.createInternetService(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
      toast({
        title: 'Success',
        description: 'Internet service created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create internet service',
        variant: 'destructive',
      });
    },
  });
}

export function useAssignServiceToCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ customerId, serviceId, config }: { 
      customerId: number; 
      serviceId: number; 
      config?: Record<string, unknown> 
    }) => serviceManagementService.assignServiceToCustomer(customerId, serviceId, config),
    onSuccess: (_, { customerId }) => {
      queryClient.invalidateQueries({ queryKey: ['customers', customerId, 'services'] });
      toast({
        title: 'Success',
        description: 'Service assigned to customer successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to assign service to customer',
        variant: 'destructive',
      });
    },
  });
}

export function useServiceStats() {
  return useQuery({
    queryKey: ['services', 'stats'],
    queryFn: () => {
      // This would typically call a stats endpoint
      // For now, return mock data structure
      return Promise.resolve({
        total_services: 0,
        active_services: 0,
        internet_services: 0,
        voice_services: 0,
        bundle_services: 0,
        total_subscriptions: 0,
        monthly_revenue: 0,
      });
    },
    refetchInterval: 5 * 60 * 1000,
  });
}
