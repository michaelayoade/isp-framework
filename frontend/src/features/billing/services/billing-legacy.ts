import { apiClient } from '@/api/client';

// Invoice types
export interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  customer_name?: string;
  amount: number;
  tax_amount: number;
  total_amount: number;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date: string;
  paid_date?: string;
  created_at: string;
  updated_at: string;
}

export interface InvoiceCreate {
  customer_id: number;
  amount: number;
  tax_amount?: number;
  due_date: string;
  description?: string;
  items?: InvoiceItemCreate[];
}

export interface InvoiceItem {
  id: number;
  invoice_id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface InvoiceItemCreate {
  description: string;
  quantity: number;
  unit_price: number;
}

// Payment types
export interface Payment {
  id: number;
  payment_number: string;
  customer_id: number;
  invoice_id?: number;
  amount: number;
  payment_method: 'cash' | 'card' | 'bank_transfer' | 'check' | 'online';
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  payment_date: string;
  reference?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentCreate {
  customer_id: number;
  invoice_id?: number;
  amount: number;
  payment_method: string;
  reference?: string;
  payment_date?: string;
}

// Billing overview types
export interface BillingOverview {
  total_revenue: number;
  monthly_revenue: number;
  outstanding_amount: number;
  overdue_amount: number;
  total_invoices: number;
  paid_invoices: number;
  overdue_invoices: number;
  total_customers: number;
  active_customers: number;
}

export interface BillingFilters {
  page?: number;
  per_page?: number;
  customer_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
  overdue_only?: boolean;
  unpaid_only?: boolean;
}

// Billing API service
export class BillingService {
  private basePath = '/billing';

  // Invoice methods
  async getInvoices(filters: BillingFilters = {}): Promise<{ invoices: Invoice[]; total: number }> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const response = await apiClient.get(`${this.basePath}/invoices?${params.toString()}`);
    return response.data;
  }

  async getInvoice(id: number): Promise<Invoice> {
    const response = await apiClient.get(`${this.basePath}/invoices/${id}`);
    return response.data;
  }

  async createInvoice(invoiceData: InvoiceCreate): Promise<Invoice> {
    const response = await apiClient.post(`${this.basePath}/invoices`, invoiceData);
    return response.data;
  }

  async updateInvoice(id: number, invoiceData: Partial<InvoiceCreate>): Promise<Invoice> {
    const response = await apiClient.put(`${this.basePath}/invoices/${id}`, invoiceData);
    return response.data;
  }

  async sendInvoice(id: number): Promise<void> {
    await apiClient.post(`${this.basePath}/invoices/${id}/send`);
  }

  async cancelInvoice(id: number, reason?: string): Promise<void> {
    await apiClient.post(`${this.basePath}/invoices/${id}/cancel`, { reason });
  }

  async getOverdueInvoices(): Promise<Invoice[]> {
    const response = await apiClient.get(`${this.basePath}/invoices/overdue`);
    return response.data;
  }

  async getCustomerInvoices(customerId: number, limit = 100, offset = 0): Promise<Invoice[]> {
    const response = await apiClient.get(
      `${this.basePath}/invoices/customer/${customerId}?limit=${limit}&offset=${offset}`
    );
    return response.data;
  }

  // Payment methods
  async getPayments(filters: BillingFilters = {}): Promise<{ payments: Payment[]; total: number }> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const response = await apiClient.get(`${this.basePath}/payments?${params.toString()}`);
    return response.data;
  }

  async getPayment(id: number): Promise<Payment> {
    const response = await apiClient.get(`${this.basePath}/payments/${id}`);
    return response.data;
  }

  async createPayment(paymentData: PaymentCreate): Promise<Payment> {
    const response = await apiClient.post(`${this.basePath}/payments`, paymentData);
    return response.data;
  }

  async getInvoicePayments(invoiceId: number): Promise<Payment[]> {
    const response = await apiClient.get(`${this.basePath}/payments/invoice/${invoiceId}`);
    return response.data;
  }

  async getCustomerPayments(customerId: number, limit = 100, offset = 0): Promise<Payment[]> {
    const response = await apiClient.get(
      `${this.basePath}/payments/customer/${customerId}?limit=${limit}&offset=${offset}`
    );
    return response.data;
  }

  // Overview and statistics
  async getBillingOverview(startDate?: string, endDate?: string): Promise<BillingOverview> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await apiClient.get(`${this.basePath}/overview?${params.toString()}`);
    return response.data;
  }

  async getCustomerBillingSummary(customerId: number): Promise<Record<string, unknown>> {
    const response = await apiClient.get(`${this.basePath}/customer/${customerId}/summary`);
    return response.data;
  }

  async getBillingStatistics(startDate?: string, endDate?: string): Promise<Record<string, unknown>> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await apiClient.get(`${this.basePath}/statistics?${params.toString()}`);
    return response.data;
  }
}

// Export singleton instance
export const billingService = new BillingService();
