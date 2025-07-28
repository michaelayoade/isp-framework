import { apiClient } from '@/api/client';

// Customer types
export interface Customer {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  status: 'active' | 'suspended' | 'pending' | 'cancelled';
  category?: string;
  location_id?: number;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  name: string;
  email: string;
  phone?: string;
  address?: string;
  category?: string;
  location_id?: number;
}

export interface CustomerUpdate {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  category?: string;
  location_id?: number;
}

export interface CustomerList {
  customers: Customer[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface CustomerFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  category?: string;
  location_id?: number;
}

// Customer API service
export class CustomerService {
  private basePath = '/customers';

  async getCustomers(filters: CustomerFilters = {}): Promise<CustomerList> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.per_page) params.append('per_page', filters.per_page.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    if (filters.location_id) params.append('location_id', filters.location_id.toString());

    const response = await apiClient.get(`${this.basePath}?${params.toString()}`);
    return response.data;
  }

  async getCustomer(id: number): Promise<Customer> {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data;
  }

  async createCustomer(customerData: CustomerCreate): Promise<Customer> {
    const response = await apiClient.post(this.basePath, customerData);
    return response.data;
  }

  async updateCustomer(id: number, customerData: CustomerUpdate): Promise<Customer> {
    const response = await apiClient.put(`${this.basePath}/${id}`, customerData);
    return response.data;
  }

  async deleteCustomer(id: number): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async updateCustomerStatus(id: number, status: string, reason?: string): Promise<Customer> {
    const response = await apiClient.patch(`${this.basePath}/${id}/status`, {
      status,
      reason
    });
    return response.data;
  }
}

// Export singleton instance
export const customerService = new CustomerService();
