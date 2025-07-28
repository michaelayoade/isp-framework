import {
  toInvoiceUI,
  toInvoiceDTO,
  toInvoiceLineItemUI,
  toInvoiceLineItemDTO,
  toPaymentUI,
  toPaymentDTO,
} from '../billingMapper';
import type { Invoice, Payment, InvoiceLineItem } from '@/api/_schemas';

describe('billingMapper', () => {
  describe('toInvoiceUI', () => {
    it('should convert invoice DTO to UI model correctly', () => {
      const dto: Invoice = {
        id: 1,
        invoice_number: 'INV-2024-001',
        customer_id: 123,
        customer_name: 'John Doe',
        status: 'sent',
        issue_date: '2024-01-01',
        due_date: '2024-01-31',
        subtotal: 99.99,
        tax_amount: 9.99,
        total_amount: 109.98,
        currency: 'USD',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T12:00:00Z',
        line_items: [
          {
            id: 1,
            description: 'Premium Internet Service',
            quantity: 1,
            unit_price: 99.99,
            total_price: 99.99,
          },
        ],
      };

      const result = toInvoiceUI(dto);

      expect(result).toEqual({
        id: 1,
        invoiceNumber: 'INV-2024-001',
        customerId: 123,
        customerName: 'John Doe',
        status: 'sent',
        issueDate: new Date('2024-01-01'),
        dueDate: new Date('2024-01-31'),
        subtotal: 99.99,
        taxAmount: 9.99,
        totalAmount: 109.98,
        currency: 'USD',
        createdAt: new Date('2024-01-01T00:00:00Z'),
        updatedAt: new Date('2024-01-01T12:00:00Z'),
        lineItems: [
          {
            id: 1,
            description: 'Premium Internet Service',
            quantity: 1,
            unitPrice: 99.99,
            totalPrice: 99.99,
          },
        ],
      });
    });

    it('should handle invalid status gracefully', () => {
      const dto: Invoice = {
        id: 1,
        invoice_number: 'INV-2024-001',
        customer_id: 123,
        customer_name: 'John Doe',
        status: 'invalid_status' as 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled',
        issue_date: '2024-01-01',
        due_date: '2024-01-31',
        subtotal: 99.99,
        tax_amount: 9.99,
        total_amount: 109.98,
        currency: 'USD',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T12:00:00Z',
        line_items: [],
      };

      const result = toInvoiceUI(dto);
      expect(result.status).toBe('draft'); // Should default to 'draft'
    });

    it('should handle missing line items', () => {
      const dto: Invoice = {
        id: 1,
        invoice_number: 'INV-2024-001',
        customer_id: 123,
        customer_name: 'John Doe',
        status: 'sent',
        issue_date: '2024-01-01',
        due_date: '2024-01-31',
        subtotal: 99.99,
        tax_amount: 9.99,
        total_amount: 109.98,
        currency: 'USD',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T12:00:00Z',
        line_items: undefined,
      };

      const result = toInvoiceUI(dto);
      expect(result.lineItems).toEqual([]);
    });
  });

  describe('toInvoiceDTO', () => {
    it('should convert invoice UI model to DTO correctly', () => {
      const ui = {
        customerId: 123,
        status: 'sent' as const,
        dueDate: new Date('2024-01-31'),
        lineItems: [
          {
            id: 1,
            description: 'Premium Internet Service',
            quantity: 1,
            unitPrice: 99.99,
            totalPrice: 99.99,
          },
        ],
      };

      const result = toInvoiceDTO(ui);

      expect(result).toEqual({
        customer_id: 123,
        status: 'sent',
        due_date: '2024-01-31',
        line_items: [
          {
            description: 'Premium Internet Service',
            quantity: 1,
            unit_price: 99.99,
          },
        ],
      });
    });
  });

  describe('toPaymentUI', () => {
    it('should convert payment DTO to UI model correctly', () => {
      const dto: Payment = {
        id: 1,
        invoice_id: 123,
        customer_id: 456,
        amount: 109.98,
        currency: 'USD',
        payment_method: 'credit_card',
        payment_date: '2024-01-16T10:30:00Z',
        reference_number: 'CC-2024-001',
        notes: 'Automatic payment',
        created_at: '2024-01-16T10:30:00Z',
      };

      const result = toPaymentUI(dto);

      expect(result).toEqual({
        id: 1,
        invoiceId: 123,
        customerId: 456,
        amount: 109.98,
        currency: 'USD',
        paymentMethod: 'credit_card',
        paymentDate: new Date('2024-01-16T10:30:00Z'),
        referenceNumber: 'CC-2024-001',
        notes: 'Automatic payment',
        createdAt: new Date('2024-01-16T10:30:00Z'),
      });
    });

    it('should handle invalid payment method gracefully', () => {
      const dto: Payment = {
        id: 1,
        invoice_id: 123,
        customer_id: 456,
        amount: 109.98,
        currency: 'USD',
        payment_method: 'invalid_method' as 'credit_card' | 'bank_transfer' | 'cash' | 'check',
        payment_date: '2024-01-16T10:30:00Z',
        created_at: '2024-01-16T10:30:00Z',
      };

      const result = toPaymentUI(dto);
      expect(result.paymentMethod).toBe('credit_card'); // Should default to 'credit_card'
    });

    it('should handle optional fields', () => {
      const dto: Payment = {
        id: 1,
        invoice_id: 123,
        customer_id: 456,
        amount: 109.98,
        currency: 'USD',
        payment_method: 'bank_transfer',
        payment_date: '2024-01-16T10:30:00Z',
        created_at: '2024-01-16T10:30:00Z',
        // reference_number and notes are optional
      };

      const result = toPaymentUI(dto);
      expect(result.referenceNumber).toBeUndefined();
      expect(result.notes).toBeUndefined();
    });
  });

  describe('toPaymentDTO', () => {
    it('should convert payment UI model to DTO correctly', () => {
      const ui = {
        invoiceId: 123,
        amount: 109.98,
        paymentMethod: 'credit_card' as const,
        referenceNumber: 'CC-2024-001',
        notes: 'Automatic payment',
      };

      const result = toPaymentDTO(ui);

      expect(result).toEqual({
        invoice_id: 123,
        amount: 109.98,
        payment_method: 'credit_card',
        reference_number: 'CC-2024-001',
        notes: 'Automatic payment',
      });
    });
  });

  describe('toInvoiceLineItemUI', () => {
    it('should convert line item DTO to UI model correctly', () => {
      const dto: InvoiceLineItem = {
        id: 1,
        description: 'Premium Internet Service',
        quantity: 2,
        unit_price: 49.99,
        total_price: 99.98,
      };

      const result = toInvoiceLineItemUI(dto);

      expect(result).toEqual({
        id: 1,
        description: 'Premium Internet Service',
        quantity: 2,
        unitPrice: 49.99,
        totalPrice: 99.98,
      });
    });
  });

  describe('toInvoiceLineItemDTO', () => {
    it('should convert line item UI model to DTO correctly', () => {
      const ui = {
        id: 1,
        description: 'Premium Internet Service',
        quantity: 2,
        unitPrice: 49.99,
        totalPrice: 99.98,
      };

      const result = toInvoiceLineItemDTO(ui);

      expect(result).toEqual({
        description: 'Premium Internet Service',
        quantity: 2,
        unit_price: 49.99,
      });
    });
  });
});
