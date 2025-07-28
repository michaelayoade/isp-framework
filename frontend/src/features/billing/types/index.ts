// Billing module type definitions
export interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  customer_name: string;
  billing_account_id: number;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  balance: number;
  items: InvoiceItem[];
  payments: Payment[];
  created_at: string;
  updated_at: string;
}

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';

export interface InvoiceItem {
  id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
  service_id?: number;
  tax_rate?: number;
}

export interface Payment {
  id: number;
  payment_number: string;
  invoice_id: number;
  customer_id: number;
  amount: number;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  transaction_id?: string;
  payment_date: string;
  notes?: string;
  created_at: string;
}

export type PaymentMethod = 'cash' | 'bank_transfer' | 'credit_card' | 'mobile_money';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export interface BillingStats {
  total_revenue: number;
  monthly_revenue: number;
  outstanding_amount: number;
  overdue_amount: number;
  total_invoices: number;
  paid_invoices: number;
  overdue_invoices: number;
  average_payment_time: number;
}

export interface BillingFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: InvoiceStatus | PaymentStatus;
  customer_id?: number;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
