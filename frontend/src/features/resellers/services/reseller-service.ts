import { apiClient } from '@/api/client';

export interface Reseller {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  status: 'active' | 'inactive' | 'suspended';
  tier: 'bronze' | 'silver' | 'gold';
  commission_rate: number;
  created_at: string;
  updated_at: string;
}

export interface ResellerDashboard {
  total_customers: number;
  active_customers: number;
  monthly_revenue: number;
  total_commission: number;
  pending_commission: number;
  commission_rate: number;
}

export interface ResellerCustomer {
  id: number;
  name: string;
  email: string;
  phone?: string;
  status: 'active' | 'inactive' | 'suspended';
  plan: string;
  monthly_rate: number;
  signup_date: string;
  commission: number;
}

export interface CommissionReport {
  id: string;
  month: string;
  customers: number;
  revenue: number;
  commission: number;
  status: 'pending' | 'paid';
  payout_date: string;
}

export interface ResellerStats {
  customer_growth: Array<{ month: string; count: number }>;
  revenue_trend: Array<{ month: string; revenue: number }>;
  commission_history: Array<{ month: string; commission: number }>;
}

class ResellerService {
  // Get current reseller profile
  async getProfile(): Promise<Reseller> {
    const response = await apiClient.get('/resellers/me');
    return response.data;
  }

  // Get reseller dashboard data
  async getDashboard(): Promise<ResellerDashboard> {
    const response = await apiClient.get('/resellers/me/dashboard');
    return response.data;
  }

  // Get reseller customers
  async getCustomers(params?: {
    page?: number;
    per_page?: number;
    search?: string;
    status?: string;
  }): Promise<{
    customers: ResellerCustomer[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }> {
    const response = await apiClient.get('/resellers/me/customers', { params });
    return response.data;
  }

  // Get commission report
  async getCommissionReport(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<CommissionReport[]> {
    const response = await apiClient.get('/resellers/me/commission-report', { params });
    return response.data;
  }

  // Get commission reports (alias for getCommissionReport)
  async getCommissionReports(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<CommissionReport[]> {
    return this.getCommissionReport(params);
  }

  // Get reseller statistics
  async getStats(resellerId: number): Promise<ResellerStats> {
    const response = await apiClient.get(`/resellers/${resellerId}/stats`);
    return response.data;
  }

  // Update reseller profile
  async updateProfile(data: Partial<Reseller>): Promise<Reseller> {
    const response = await apiClient.put('/resellers/me', data);
    return response.data;
  }

  // Assign customer to reseller
  async assignCustomer(customerId: number): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`/resellers/me/assign-customer/${customerId}`);
    return response.data;
  }

  // Unassign customer from reseller
  async unassignCustomer(customerId: number): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/resellers/unassign-customer/${customerId}`);
    return response.data;
  }

  // Reseller authentication
  async login(username: string, password: string): Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: Reseller;
  }> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await apiClient.post('/auth/resellers/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  }

  // Get current reseller from token
  async getCurrentReseller(): Promise<Reseller> {
    const response = await apiClient.get('/auth/resellers/me');
    return response.data;
  }

  // Refresh reseller token
  async refreshToken(refreshToken: string): Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
  }> {
    const response = await apiClient.post('/auth/resellers/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  // Change reseller password
  async changePassword(currentPassword: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/auth/resellers/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  }

  // Logout reseller
  async logout(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/auth/resellers/logout');
    return response.data;
  }
}

export const resellerService = new ResellerService();
