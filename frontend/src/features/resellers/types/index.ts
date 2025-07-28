// Reseller module type definitions
export interface Reseller {
  id: number;
  company_name: string;
  contact_name: string;
  email: string;
  phone: string;
  status: ResellerStatus;
  tier: ResellerTier;
  commission_rate: number;
  parent_reseller_id?: number;
  parent_reseller?: Reseller;
  children_resellers: Reseller[];
  address: Address;
  contract_start_date: string;
  contract_end_date?: string;
  total_customers: number;
  active_customers: number;
  monthly_revenue: number;
  total_commission: number;
  created_at: string;
  updated_at: string;
}

export type ResellerStatus = 'active' | 'inactive' | 'suspended' | 'terminated';
export type ResellerTier = 'bronze' | 'silver' | 'gold' | 'platinum';

// Re-export from common types to maintain backward compatibility
export type { Address } from '@/types/common';

export interface ResellerCustomer {
  id: number;
  customer_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  status: 'active' | 'inactive' | 'suspended';
  services: ResellerCustomerService[];
  monthly_revenue: number;
  registration_date: string;
}

export interface ResellerCustomerService {
  id: number;
  service_name: string;
  service_type: 'internet' | 'voice' | 'bundle';
  monthly_fee: number;
  commission_amount: number;
  status: 'active' | 'suspended' | 'terminated';
}

export interface CommissionReport {
  period: string;
  total_commission: number;
  customer_commissions: CustomerCommission[];
  service_breakdown: ServiceCommissionBreakdown[];
  payment_status: 'pending' | 'paid' | 'overdue';
  payment_date?: string;
}

export interface CustomerCommission {
  customer_id: number;
  customer_name: string;
  services: ServiceCommissionBreakdown[];
  total_commission: number;
}

export interface ServiceCommissionBreakdown {
  service_type: string;
  service_count: number;
  total_revenue: number;
  commission_rate: number;
  commission_amount: number;
}

export interface ResellerDashboard {
  total_customers: number;
  active_customers: number;
  monthly_revenue: number;
  total_commission: number;
  commission_this_month: number;
  customer_growth: number;
  revenue_growth: number;
  top_services: ServiceStats[];
  recent_customers: ResellerCustomer[];
  commission_trend: CommissionTrend[];
}

export interface ServiceStats {
  service_type: string;
  customer_count: number;
  revenue: number;
  commission: number;
}

export interface CommissionTrend {
  period: string;
  commission: number;
  customers: number;
}

export interface ResellerFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: ResellerStatus;
  tier?: ResellerTier;
  parent_reseller_id?: number;
  created_from?: string;
  created_to?: string;
}

export interface CreateResellerData {
  company_name: string;
  contact_name: string;
  email: string;
  phone: string;
  tier: ResellerTier;
  commission_rate: number;
  parent_reseller_id?: number;
  address: Address;
  contract_start_date: string;
  contract_end_date?: string;
}

export interface UpdateResellerData {
  company_name?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  status?: ResellerStatus;
  tier?: ResellerTier;
  commission_rate?: number;
  address?: Address;
  contract_end_date?: string;
}

// Re-export from common types to maintain backward compatibility
export type { PaginatedResponse } from '@/types/common';
