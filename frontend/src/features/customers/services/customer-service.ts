import { Customer, CustomerFilters, CreateCustomerData, UpdateCustomerData, CustomerListResponse, CustomerStats } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class CustomerService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getCustomers(filters: CustomerFilters = {}): Promise<CustomerListResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const queryString = params.toString();
    const endpoint = `/customers${queryString ? `?${queryString}` : ''}`;
    
    return this.request<CustomerListResponse>(endpoint);
  }

  async getCustomer(id: number): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}`);
  }

  async createCustomer(data: CreateCustomerData): Promise<Customer> {
    return this.request<Customer>('/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCustomer(id: number, data: UpdateCustomerData): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCustomer(id: number): Promise<void> {
    await this.request<void>(`/customers/${id}`, {
      method: 'DELETE',
    });
  }

  async getCustomerStats(): Promise<CustomerStats> {
    return this.request<CustomerStats>('/customers/stats');
  }

  async suspendCustomer(id: number): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}/suspend`, {
      method: 'POST',
    });
  }

  async activateCustomer(id: number): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}/activate`, {
      method: 'POST',
    });
  }
}

export const customerService = new CustomerService();
