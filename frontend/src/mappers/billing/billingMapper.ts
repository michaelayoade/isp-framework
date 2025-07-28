import { z } from 'zod';
import type { 
  Invoice as InvoiceDTO, 
  Payment as PaymentDTO, 
  InvoiceLineItem as InvoiceLineItemDTO 
} from '@/api/_schemas';

// UI models (what the frontend components expect)
export interface InvoiceUI {
  id: number;
  invoiceNumber: string;
  customerId: number;
  customerName: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issueDate: Date;
  dueDate: Date;
  subtotal: number;
  taxAmount: number;
  totalAmount: number;
  currency: string;
  createdAt: Date;
  updatedAt: Date;
  lineItems: InvoiceLineItemUI[];
}

export interface InvoiceLineItemUI {
  id: number;
  description: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

export interface PaymentUI {
  id: number;
  invoiceId: number;
  customerId: number;
  amount: number;
  currency: string;
  paymentMethod: 'credit_card' | 'bank_transfer' | 'cash' | 'check';
  paymentDate: Date;
  referenceNumber?: string;
  notes?: string;
  createdAt: Date;
}

// Validation schemas for graceful handling of unknown/optional fields
const InvoiceLineItemSchema = z.object({
  id: z.number(),
  description: z.string(),
  quantity: z.number(),
  unit_price: z.number(),
  total_price: z.number(),
});

const InvoiceSchema = z.object({
  id: z.number(),
  invoice_number: z.string(),
  customer_id: z.number(),
  customer_name: z.string(),
  status: z.string().transform((val) => {
    if (['draft', 'sent', 'paid', 'overdue', 'cancelled'].includes(val)) {
      return val as 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
    }
    return 'draft'; // Default for invalid values
  }),
  issue_date: z.string(),
  due_date: z.string(),
  subtotal: z.number(),
  tax_amount: z.number(),
  total_amount: z.number(),
  currency: z.string().default('USD'),
  created_at: z.string(),
  updated_at: z.string(),
  line_items: z.array(InvoiceLineItemSchema).default([]),
});

const PaymentSchema = z.object({
  id: z.number(),
  invoice_id: z.number(),
  customer_id: z.number(),
  amount: z.number(),
  currency: z.string().default('USD'),
  payment_method: z.string().transform((val) => {
    if (['credit_card', 'bank_transfer', 'cash', 'check'].includes(val)) {
      return val as 'credit_card' | 'bank_transfer' | 'cash' | 'check';
    }
    return 'credit_card'; // Default for invalid values
  }),
  payment_date: z.string(),
  reference_number: z.string().optional(),
  notes: z.string().optional(),
  created_at: z.string(),
});

/**
 * Convert Invoice API DTO to UI model
 */
export const toInvoiceUI = (dto: InvoiceDTO): InvoiceUI => {
  const validated = InvoiceSchema.parse(dto);
  
  return {
    id: validated.id,
    invoiceNumber: validated.invoice_number,
    customerId: validated.customer_id,
    customerName: validated.customer_name,
    status: validated.status,
    issueDate: new Date(validated.issue_date),
    dueDate: new Date(validated.due_date),
    subtotal: validated.subtotal,
    taxAmount: validated.tax_amount,
    totalAmount: validated.total_amount,
    currency: validated.currency,
    createdAt: new Date(validated.created_at),
    updatedAt: new Date(validated.updated_at),
    lineItems: validated.line_items.map(toInvoiceLineItemUI),
  };
};

/**
 * Convert UI model to Invoice API DTO
 */
export const toInvoiceDTO = (ui: Partial<InvoiceUI>): Partial<InvoiceDTO> => {
  return {
    customer_id: ui.customerId,
    status: ui.status,
    due_date: ui.dueDate?.toISOString().split('T')[0], // Convert to date string
    line_items: ui.lineItems?.map(toInvoiceLineItemDTO),
  };
};

/**
 * Convert InvoiceLineItem DTO to UI model
 */
export const toInvoiceLineItemUI = (dto: InvoiceLineItemDTO): InvoiceLineItemUI => {
  const validated = InvoiceLineItemSchema.parse(dto);
  
  return {
    id: validated.id,
    description: validated.description,
    quantity: validated.quantity,
    unitPrice: validated.unit_price,
    totalPrice: validated.total_price,
  };
};

/**
 * Convert InvoiceLineItem UI model to DTO
 */
export const toInvoiceLineItemDTO = (ui: InvoiceLineItemUI): Partial<InvoiceLineItemDTO> => {
  return {
    description: ui.description,
    quantity: ui.quantity,
    unit_price: ui.unitPrice,
  };
};

/**
 * Convert Payment API DTO to UI model
 */
export const toPaymentUI = (dto: PaymentDTO): PaymentUI => {
  const validated = PaymentSchema.parse(dto);
  
  return {
    id: validated.id,
    invoiceId: validated.invoice_id,
    customerId: validated.customer_id,
    amount: validated.amount,
    currency: validated.currency,
    paymentMethod: validated.payment_method,
    paymentDate: new Date(validated.payment_date),
    referenceNumber: validated.reference_number,
    notes: validated.notes,
    createdAt: new Date(validated.created_at),
  };
};

/**
 * Convert Payment UI model to DTO
 */
export const toPaymentDTO = (ui: Partial<PaymentUI>): Partial<PaymentDTO> => {
  return {
    invoice_id: ui.invoiceId,
    amount: ui.amount,
    payment_method: ui.paymentMethod,
    reference_number: ui.referenceNumber,
    notes: ui.notes,
  };
};
