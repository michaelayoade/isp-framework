import { useGetCustomers } from '@/api/customers/iSPFrameworkCustomersAPI';
import { toCustomerUI, type CustomerUI } from '@/mappers/customers';
import type { GetCustomersParams } from '@/api/_schemas';

export interface CustomerFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: 'active' | 'inactive' | 'suspended';
}

export function useCustomers(filters: CustomerFilters = {}) {
  // Convert UI filters to API params
  const apiParams: GetCustomersParams = {
    page: filters.page || 1,
    per_page: filters.per_page || 10,
    search: filters.search,
    status: filters.status,
  };

  // Use generated React Query hook
  const { data: response, error, isLoading, refetch } = useGetCustomers(apiParams);

  // Extract data from axios response structure
  const apiData = response?.data;
  
  // Map API response to UI models
  const customers: CustomerUI[] = apiData?.data ? apiData.data.map(toCustomerUI) : [];
  const pagination = apiData?.pagination ?? {
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  };

  return {
    customers,
    pagination,
    loading: isLoading,
    error: error ? String(error) : null,
    refetch,
  };
}
