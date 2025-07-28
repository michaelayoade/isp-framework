import { PaginatedResponse, Address, BaseEntity } from '@/types/common';

export interface Customer extends BaseEntity {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address: Address;
  status: CustomerStatus;
  service_plan: string;
  monthly_fee: number;
  created_at: string;
  updated_at: string;
}

export type CustomerStatus = 'active' | 'suspended' | 'pending' | 'cancelled';

export interface CustomerFilters {
  search?: string;
  status?: CustomerStatus;
  service_plan?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface CreateCustomerData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address: Address;
  service_plan: string;
}

export interface UpdateCustomerData extends Partial<CreateCustomerData> {
  status?: CustomerStatus;
}

export interface CustomerStats {
  total: number;
  active: number;
  suspended: number;
  pending: number;
  cancelled: number;
  monthly_revenue: number;
  growth_rate: number;
}

export type CustomerListResponse = PaginatedResponse<Customer>;
