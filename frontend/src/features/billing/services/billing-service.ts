import { apiClient } from '@/api/client';

// Types based on backend API schema
export interface Invoice {
  id: string;
  customer_id: number;
  amount: number;
  tax_amount?: number;
  total_amount: number;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date: string;
  paid_date?: string;
  description?: string;
  items: InvoiceItem[];
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Payment {
  id: string;
  invoice_id: string;
  customer_id: number;
  amount: number;
  payment_method: 'cash' | 'card' | 'bank_transfer' | 'check' | 'other';
  payment_date: string;
  reference?: string;
  notes?: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  created_at: string;
  updated_at: string;
}

export interface CreditNote {
  id: string;
  invoice_id: string;
  customer_id: number;
  amount: number;
  reason: string;
  issue_date: string;
  status: 'draft' | 'issued' | 'applied';
  created_at: string;
  updated_at: string;
}

export interface BillingOverview {
  total_revenue: number;
  outstanding_amount: number;
  overdue_amount: number;
  total_invoices: number;
  paid_invoices: number;
  pending_invoices: number;
  overdue_invoices: number;
  recent_payments: Payment[];
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface PaymentListResponse {
  payments: Payment[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface CreditNoteListResponse {
  credit_notes: CreditNote[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface InvoiceFilters {
  page?: number;
  per_page?: number;
  status?: string;
  customer_id?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export interface PaymentFilters {
  page?: number;
  per_page?: number;
  status?: string;
  payment_method?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export interface InvoiceCreate {
  customer_id: number;
  amount: number;
  tax_amount?: number;
  due_date: string;
  description?: string;
  items: Omit<InvoiceItem, 'id'>[];
}

export interface PaymentCreate {
  invoice_id: string;
  amount: number;
  payment_method: string;
  payment_date: string;
  reference?: string;
  notes?: string;
}

class BillingService {
  // Invoice management
  async getInvoices(filters: InvoiceFilters = {}): Promise<InvoiceListResponse> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const response = await apiClient.get(`/billing/invoices?${params.toString()}`);
    return response.data;
  }

  async getInvoice(id: string): Promise<Invoice> {
    const response = await apiClient.get(`/billing/invoices/${id}`);
    return response.data;
  }

  async createInvoice(data: InvoiceCreate): Promise<Invoice> {
    const response = await apiClient.post('/billing/invoices/', data);
    return response.data;
  }

  async updateInvoice(id: string, data: Partial<InvoiceCreate>): Promise<Invoice> {
    const response = await apiClient.put(`/billing/invoices/${id}`, data);
    return response.data;
  }

  async deleteInvoice(id: string): Promise<void> {
    await apiClient.delete(`/billing/invoices/${id}`);
  }

  async sendInvoice(id: string): Promise<Invoice> {
    const response = await apiClient.post(`/billing/invoices/${id}/send`);
    return response.data;
  }

  // Payment management
  async getPayments(filters: PaymentFilters = {}): Promise<PaymentListResponse> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const response = await apiClient.get(`/billing/payments?${params.toString()}`);
    return response.data;
  }

  async getPayment(id: string): Promise<Payment> {
    const response = await apiClient.get(`/billing/payments/${id}`);
    return response.data;
  }

  async createPayment(data: PaymentCreate): Promise<Payment> {
    const response = await apiClient.post('/billing/payments/', data);
    return response.data;
  }

  async updatePayment(id: string, data: Partial<PaymentCreate>): Promise<Payment> {
    const response = await apiClient.put(`/billing/payments/${id}`, data);
    return response.data;
  }

  async deletePayment(id: string): Promise<void> {
    await apiClient.delete(`/billing/payments/${id}`);
  }

  // Credit notes
  async getCreditNotes(filters: InvoiceFilters = {}): Promise<CreditNoteListResponse> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const response = await apiClient.get(`/billing/credit-notes?${params.toString()}`);
    return response.data;
  }

  async createCreditNote(data: {
    invoice_id: string;
    amount: number;
    reason: string;
  }): Promise<CreditNote> {
    const response = await apiClient.post('/billing/credit-notes/', data);
    return response.data;
  }

  // Billing overview and analytics
  async getBillingOverview(): Promise<BillingOverview> {
    const response = await apiClient.get('/billing/overview');
    return response.data;
  }

  // Export functionality
  async exportInvoices(filters: InvoiceFilters = {}, format: 'csv' | 'xlsx' = 'csv'): Promise<Blob> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });
    params.append('format', format);

    const response = await apiClient.get(`/billing/invoices/export?${params.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async exportPayments(filters: PaymentFilters = {}, format: 'csv' | 'xlsx' = 'csv'): Promise<Blob> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });
    params.append('format', format);

    const response = await apiClient.get(`/billing/payments/export?${params.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const billingService = new BillingService();
