import { apiClient } from '@/api/client';

export interface CustomerPortalAuth {
  portal_id: string;
  customer_id: number;
  access_token: string;
  expires_at: string;
}

export interface CustomerProfile {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  status: 'active' | 'inactive' | 'suspended';
  plan: string;
  monthly_rate: number;
  next_bill_date: string;
  account_balance: number;
  created_at: string;
  updated_at: string;
}

export interface CustomerInvoice {
  id: string;
  customer_id: number;
  amount: number;
  status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date: string;
  paid_date?: string;
  description?: string;
  items: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    total: number;
  }>;
}

export interface CustomerTicket {
  id: string;
  customer_id: number;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  created_at: string;
  updated_at: string;
  responses: Array<{
    id: number;
    message: string;
    created_by: string;
    created_at: string;
    is_internal: boolean;
  }>;
}

export interface CustomerActivity {
  id: number;
  type: 'payment' | 'service_change' | 'support_ticket' | 'maintenance' | 'other';
  description: string;
  date: string;
  metadata?: Record<string, unknown>;
}

export interface ServiceUsage {
  period: string;
  download_gb: number;
  upload_gb: number;
  total_gb: number;
  peak_speed_mbps: number;
  uptime_percentage: number;
}

class CustomerPortalService {
  // Customer portal authentication
  async authenticatePortal(portalId: string, accessCode?: string): Promise<CustomerPortalAuth> {
    const response = await apiClient.post('/auth/portal/authenticate', {
      portal_id: portalId,
      access_code: accessCode,
    });
    return response.data;
  }

  // Validate portal access
  async validatePortal(portalId: string): Promise<{ valid: boolean; customer_id?: number }> {
    const response = await apiClient.post('/auth/portal/validate', {
      portal_id: portalId,
    });
    return response.data;
  }

  // Get customer profile by portal ID
  async getCustomerProfile(portalId: string): Promise<CustomerProfile> {
    const response = await apiClient.get(`/auth/portal/customer/${portalId}`);
    return response.data;
  }

  // Customer direct authentication (if available)
  async customerLogin(email: string, password: string): Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    customer: CustomerProfile;
  }> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await apiClient.post('/customers/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  }

  // Get customer invoices
  async getInvoices(customerId: number, params?: {
    page?: number;
    per_page?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{
    invoices: CustomerInvoice[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }> {
    const response = await apiClient.get(`/customers/${customerId}/invoices`, { params });
    return response.data;
  }

  // Get specific invoice
  async getInvoice(customerId: number, invoiceId: string): Promise<CustomerInvoice> {
    const response = await apiClient.get(`/customers/${customerId}/invoices/${invoiceId}`);
    return response.data;
  }

  // Download invoice PDF
  async downloadInvoice(customerId: number, invoiceId: string): Promise<Blob> {
    const response = await apiClient.get(`/customers/${customerId}/invoices/${invoiceId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Get customer support tickets
  async getTickets(customerId: number, params?: {
    page?: number;
    per_page?: number;
    status?: string;
    priority?: string;
  }): Promise<{
    tickets: CustomerTicket[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }> {
    const response = await apiClient.get(`/customers/${customerId}/tickets`, { params });
    return response.data;
  }

  // Get specific ticket
  async getTicket(customerId: number, ticketId: string): Promise<CustomerTicket> {
    const response = await apiClient.get(`/customers/${customerId}/tickets/${ticketId}`);
    return response.data;
  }

  // Create new support ticket
  async createTicket(customerId: number, data: {
    subject: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'urgent';
    category: string;
  }): Promise<CustomerTicket> {
    const response = await apiClient.post(`/customers/${customerId}/tickets`, data);
    return response.data;
  }

  // Add response to ticket
  async addTicketResponse(customerId: number, ticketId: string, message: string): Promise<{
    success: boolean;
    response_id: number;
  }> {
    const response = await apiClient.post(`/customers/${customerId}/tickets/${ticketId}/responses`, {
      message,
    });
    return response.data;
  }

  // Get customer activity history
  async getActivity(customerId: number, params?: {
    page?: number;
    per_page?: number;
    type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{
    activities: CustomerActivity[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }> {
    const response = await apiClient.get(`/customers/${customerId}/activity`, { params });
    return response.data;
  }

  // Get service usage data
  async getServiceUsage(customerId: number, params?: {
    start_date?: string;
    end_date?: string;
    period?: 'daily' | 'weekly' | 'monthly';
  }): Promise<ServiceUsage[]> {
    const response = await apiClient.get(`/customers/${customerId}/usage`, { params });
    return response.data;
  }

  // Update customer profile
  async updateProfile(customerId: number, data: Partial<CustomerProfile>): Promise<CustomerProfile> {
    const response = await apiClient.put(`/customers/${customerId}/profile`, data);
    return response.data;
  }

  // Get payment methods
  async getPaymentMethods(customerId: number): Promise<Array<{
    id: string;
    type: 'card' | 'bank_account' | 'paypal';
    last_four?: string;
    brand?: string;
    is_default: boolean;
    expires_at?: string;
  }>> {
    const response = await apiClient.get(`/customers/${customerId}/payment-methods`);
    return response.data;
  }

  // Process payment for invoice
  async payInvoice(customerId: number, invoiceId: string, paymentMethodId?: string): Promise<{
    success: boolean;
    payment_id: string;
    redirect_url?: string;
  }> {
    const response = await apiClient.post(`/customers/${customerId}/invoices/${invoiceId}/pay`, {
      payment_method_id: paymentMethodId,
    });
    return response.data;
  }

  // Get customer notifications
  async getNotifications(customerId: number, params?: {
    page?: number;
    per_page?: number;
    unread_only?: boolean;
  }): Promise<{
    notifications: Array<{
      id: number;
      title: string;
      message: string;
      type: 'info' | 'warning' | 'error' | 'success';
      read: boolean;
      created_at: string;
    }>;
    total: number;
    unread_count: number;
  }> {
    const response = await apiClient.get(`/customers/${customerId}/notifications`, { params });
    return response.data;
  }

  // Mark notification as read
  async markNotificationRead(customerId: number, notificationId: number): Promise<{ success: boolean }> {
    const response = await apiClient.put(`/customers/${customerId}/notifications/${notificationId}/read`);
    return response.data;
  }

  // Customer logout
  async logout(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/customers/auth/logout');
    return response.data;
  }
}

export const customerPortalService = new CustomerPortalService();
