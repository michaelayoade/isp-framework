import { apiClient } from '@/api/client';
import type { 
  Customer, 
  CustomerFilters, 
  CreateCustomerData, 
  UpdateCustomerData,
  PaginatedResponse 
} from '../types';

export class CustomerService {
  private readonly basePath = '/customers';

  async getCustomers(filters: CustomerFilters = {}): Promise<PaginatedResponse<Customer>> {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data;
  }

  async getCustomer(id: number): Promise<Customer> {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data;
  }

  async createCustomer(data: CreateCustomerData): Promise<Customer> {
    const response = await apiClient.post(this.basePath, data);
    return response.data;
  }

  async updateCustomer(id: number, data: UpdateCustomerData): Promise<Customer> {
    const response = await apiClient.put(`${this.basePath}/${id}`, data);
    return response.data;
  }

  async deleteCustomer(id: number): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async suspendCustomer(id: number, reason?: string): Promise<Customer> {
    const response = await apiClient.post(`${this.basePath}/${id}/suspend`, { reason });
    return response.data;
  }

  async reactivateCustomer(id: number): Promise<Customer> {
    const response = await apiClient.post(`${this.basePath}/${id}/reactivate`);
    return response.data;
  }

  async getCustomerServices(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}/services`);
    return response.data;
  }

  async getCustomerBilling(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}/billing`);
    return response.data;
  }

  async exportCustomers(filters: CustomerFilters = {}, format: 'csv' | 'excel' = 'csv') {
    const response = await apiClient.get(`${this.basePath}/export`, {
      params: { ...filters, format },
      responseType: 'blob',
    });
    return response.data;
  }
}

export const customerService = new CustomerService();

// Re-export types for convenience
export type { Customer, CustomerFilters, CreateCustomerData, UpdateCustomerData, PaginatedResponse } from '../types';
