import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  useCreateCustomer, 
  useUpdateCustomer 
} from '@/api/customers/iSPFrameworkCustomersAPI';
import { axiosInstance } from '@/api/_utils/axios-instance';
import type { 
  CreateCustomerRequest, 
  UpdateCustomerRequest 
} from '@/api/_schemas';

export interface CustomerFormData {
  name: string;
  email: string;
  phone: string;
  status: 'active' | 'inactive' | 'suspended';
  servicePlan?: string;
  monthlyFee?: number;
  address?: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
}

export function useCreateCustomerMutation() {
  const queryClient = useQueryClient();
  const createCustomerMutation = useCreateCustomer();

  return useMutation({
    mutationFn: async (data: CustomerFormData) => {
      // Convert UI form data to API DTO
      const createRequest: CreateCustomerRequest = {
        name: data.name,
        email: data.email,
        phone: data.phone,
        service_plan: data.servicePlan,
        address: data.address ? {
          street: data.address.street,
          city: data.address.city,
          state: data.address.state,
          zip_code: data.address.zipCode,
          country: data.address.country,
        } : undefined,
      };

      const response = await createCustomerMutation.mutateAsync({ data: createRequest });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch customers list
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });
}

export function useUpdateCustomerMutation() {
  const queryClient = useQueryClient();
  const updateCustomerMutation = useUpdateCustomer();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CustomerFormData }) => {
      // Convert UI form data to API DTO
      const updateRequest: UpdateCustomerRequest = {
        name: data.name,
        email: data.email,
        phone: data.phone,
        status: data.status,
        service_plan: data.servicePlan,
        address: data.address ? {
          street: data.address.street,
          city: data.address.city,
          state: data.address.state,
          zip_code: data.address.zipCode,
          country: data.address.country,
        } : undefined,
      };

      const response = await updateCustomerMutation.mutateAsync({ 
        customerId: id, 
        data: updateRequest 
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch customers list
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });
}

export function useDeleteCustomerMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (customerId: number) => {
      const response = await axiosInstance({
        url: `/customers/${customerId}`,
        method: 'DELETE'
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch customers list
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });
}

// Hook for getting a single customer (for editing)
export function useCustomer(_customerId: number | null) {
  // This would typically use a separate API call, but for now we'll
  // extract from the customers list or implement when needed
  return {
    customer: null,
    loading: false,
    error: null,
  };
}
