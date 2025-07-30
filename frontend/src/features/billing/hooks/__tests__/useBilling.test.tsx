import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useInvoices, usePayments } from '../useBilling';

// Create a wrapper component for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  
  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
  
  TestWrapper.displayName = 'TestWrapper';
  return TestWrapper;
};

describe('useBilling hooks', () => {

  describe('useInvoices', () => {
    it('should fetch and map invoices from API', async () => {
      const { result } = renderHook(() => useInvoices(), {
        wrapper: createWrapper(),
      });

      // Initially loading
      expect(result.current.loading).toBe(true);
      expect(result.current.invoices).toEqual([]);

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Check that data was fetched and mapped correctly
      expect(result.current.invoices).toHaveLength(3);
      expect(result.current.invoices[0]).toEqual({
        id: 1,
        invoiceNumber: 'INV-2024-001',
        customerId: 1,
        customerName: 'John Doe',
        status: 'sent',
        issueDate: new Date('2024-01-01'),
        dueDate: new Date('2024-01-31'),
        subtotal: 99.99,
        taxAmount: 9.99,
        totalAmount: 109.98,
        currency: 'USD',
        createdAt: new Date('2024-01-01T00:00:00Z'),
        updatedAt: new Date('2024-01-01T00:00:00Z'),
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

      expect(result.current.pagination).toEqual({
        page: 1,
        per_page: 10,
        total: 3,
        total_pages: 1,
      });
    });

    it('should handle filters correctly', async () => {
      const { result } = renderHook(
        () => useInvoices({ 
          customer_id: 2, 
          status: 'paid' 
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should only return Jane Smith's paid invoice
      expect(result.current.invoices).toHaveLength(1);
      expect(result.current.invoices[0].customerName).toBe('Jane Smith');
      expect(result.current.invoices[0].status).toBe('paid');
    });

    it('should handle pagination', async () => {
      const { result } = renderHook(
        () => useInvoices({ page: 1, per_page: 2 }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should return first 2 invoices
      expect(result.current.invoices).toHaveLength(2);
      expect(result.current.pagination).toEqual({
        page: 1,
        per_page: 2,
        total: 3,
        total_pages: 2,
      });
    });

    it('should handle date filters', async () => {
      const { result } = renderHook(
        () => useInvoices({ 
          date_from: '2024-01-01',
          date_to: '2024-01-31'
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should return invoices within date range (excludes overdue invoice from 2023)
      expect(result.current.invoices).toHaveLength(2);
      expect(result.current.invoices.every(invoice => 
        invoice.issueDate >= new Date('2024-01-01')
      )).toBe(true);
    });

    it('should handle empty results', async () => {
      const { result } = renderHook(
        () => useInvoices({ customer_id: 999 }), // Non-existent customer
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.invoices).toEqual([]);
      expect(result.current.pagination.total).toBe(0);
    });
  });

  describe('usePayments', () => {
    it('should fetch and map payments from API', async () => {
      const { result } = renderHook(() => usePayments(), {
        wrapper: createWrapper(),
      });

      // Initially loading
      expect(result.current.loading).toBe(true);
      expect(result.current.payments).toEqual([]);

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Check that data was fetched and mapped correctly
      expect(result.current.payments).toHaveLength(2);
      expect(result.current.payments[0]).toEqual({
        id: 1,
        invoiceId: 2,
        customerId: 2,
        amount: 54.98,
        currency: 'USD',
        paymentMethod: 'credit_card',
        paymentDate: new Date('2024-01-16T10:30:00Z'),
        referenceNumber: 'CC-2024-001',
        notes: 'Automatic payment',
        createdAt: new Date('2024-01-16T10:30:00Z'),
      });

      expect(result.current.pagination).toEqual({
        page: 1,
        per_page: 10,
        total: 2,
        total_pages: 1,
      });
    });

    it('should handle customer filter', async () => {
      const { result } = renderHook(
        () => usePayments({ customer_id: 2 }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should only return payments for customer 2
      expect(result.current.payments).toHaveLength(1);
      expect(result.current.payments[0].customerId).toBe(2);
    });

    it('should handle invoice filter', async () => {
      const { result } = renderHook(
        () => usePayments({ invoice_id: 1 }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should only return payments for invoice 1
      expect(result.current.payments).toHaveLength(1);
      expect(result.current.payments[0].invoiceId).toBe(1);
      expect(result.current.payments[0].paymentMethod).toBe('bank_transfer');
    });

    it('should handle empty results', async () => {
      const { result } = renderHook(
        () => usePayments({ customer_id: 999 }), // Non-existent customer
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.payments).toEqual([]);
      expect(result.current.pagination.total).toBe(0);
    });
  });
});
