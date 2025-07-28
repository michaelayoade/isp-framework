// Services module type definitions
export interface ServiceBase {
  id: number;
  name: string;
  description: string;
  status: ServiceStatus;
  monthly_fee: number;
  setup_fee?: number;
  category: ServiceCategory;
  created_at: string;
  updated_at: string;
}

export type ServiceStatus = 'active' | 'inactive' | 'suspended' | 'terminated';
export type ServiceCategory = 'internet' | 'voice' | 'bundle' | 'recurring';

export interface InternetService extends ServiceBase {
  category: 'internet';
  bandwidth_down: number;
  bandwidth_up: number;
  data_limit?: number;
  technology: 'fiber' | 'wireless' | 'dsl' | 'satellite';
  static_ip: boolean;
  ip_addresses?: string[];
}

export interface VoiceService extends ServiceBase {
  category: 'voice';
  phone_number: string;
  included_minutes?: number;
  international_calling: boolean;
  voicemail: boolean;
  call_forwarding: boolean;
}

export interface BundleService extends ServiceBase {
  category: 'bundle';
  included_services: ServiceBase[];
  discount_percentage: number;
  bundle_type: 'internet_voice' | 'triple_play' | 'custom';
}

export interface CustomerService {
  id: number;
  customer_id: number;
  service_id: number;
  service: ServiceBase;
  status: CustomerServiceStatus;
  activation_date: string;
  suspension_date?: string;
  termination_date?: string;
  ip_assignments?: IPAssignment[];
  usage_stats?: UsageStats;
  billing_info: ServiceBilling;
}

export type CustomerServiceStatus = 'pending' | 'active' | 'suspended' | 'terminated';

export interface IPAssignment {
  id: number;
  ip_address: string;
  ip_type: 'ipv4' | 'ipv6';
  assignment_type: 'static' | 'dynamic';
  assigned_at: string;
}

export interface UsageStats {
  period: string;
  data_used: number;
  data_limit?: number;
  minutes_used?: number;
  minutes_included?: number;
}

export interface ServiceBilling {
  monthly_charge: number;
  prorated_charge?: number;
  next_billing_date: string;
  billing_cycle: 'monthly' | 'quarterly' | 'yearly';
}

export interface ServiceTemplate {
  id: number;
  name: string;
  description: string;
  category: ServiceCategory;
  default_config: Record<string, unknown>;
  pricing_model: 'fixed' | 'tiered' | 'usage_based';
  is_active: boolean;
}

export interface ServiceFilters {
  page?: number;
  per_page?: number;
  search?: string;
  category?: ServiceCategory;
  status?: ServiceStatus;
  customer_id?: number;
  technology?: string;
  price_min?: number;
  price_max?: number;
}

export interface CreateInternetServiceData {
  name: string;
  description?: string;
  monthly_fee: number;
  setup_fee?: number;
  bandwidth_down: number;
  bandwidth_up: number;
  data_limit?: number;
  technology: 'fiber' | 'wireless' | 'dsl' | 'satellite';
  static_ip: boolean;
}

// Re-export from common types to maintain backward compatibility
export type { PaginatedResponse } from '@/types/common';
