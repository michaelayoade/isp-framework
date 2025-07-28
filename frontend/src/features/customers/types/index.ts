// Customer module type definitions
export interface Customer {
  id: number;
  customer_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  status: CustomerStatus;
  account_type: AccountType;
  registration_date: string;
  last_login?: string;
  billing_address: Address;
  service_address?: Address;
  services: CustomerService[];
  billing_info: BillingInfo;
  created_at: string;
  updated_at: string;
}

export type CustomerStatus = 'active' | 'inactive' | 'suspended' | 'terminated';
export type AccountType = 'residential' | 'business' | 'enterprise';

export interface Address {
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface CustomerService {
  id: number;
  service_name: string;
  service_type: 'internet' | 'voice' | 'bundle';
  status: 'active' | 'suspended' | 'terminated';
  monthly_fee: number;
  activation_date: string;
  next_billing_date: string;
}

export interface BillingInfo {
  payment_method: 'cash' | 'bank_transfer' | 'credit_card' | 'mobile_money';
  billing_cycle: 'monthly' | 'quarterly' | 'yearly';
  auto_pay: boolean;
  credit_limit?: number;
  outstanding_balance: number;
}

export interface CustomerFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: CustomerStatus;
  account_type?: AccountType;
  service_type?: string;
  registration_date_from?: string;
  registration_date_to?: string;
}

export interface CreateCustomerData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  account_type: AccountType;
  billing_address: Address;
  service_address?: Address;
  payment_method: string;
  billing_cycle: string;
}

export interface UpdateCustomerData extends Partial<CreateCustomerData> {
  status?: CustomerStatus;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
