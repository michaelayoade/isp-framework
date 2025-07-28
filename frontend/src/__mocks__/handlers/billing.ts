import { rest } from 'msw';
import type { PaginatedInvoiceResponse, PaginatedPaymentResponse, Invoice, Payment } from '@/api/_schemas';

// Mock invoice data
const mockInvoices: Invoice[] = [
  {
    id: 1,
    invoice_number: 'INV-2024-001',
    customer_id: 1,
    customer_name: 'John Doe',
    status: 'sent',
    issue_date: '2024-01-01',
    due_date: '2024-01-31',
    subtotal: 99.99,
    tax_amount: 9.99,
    total_amount: 109.98,
    currency: 'USD',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    line_items: [
      {
        id: 1,
        description: 'Premium Internet Service',
        quantity: 1,
        unit_price: 99.99,
        total_price: 99.99,
      },
    ],
  },
  {
    id: 2,
    invoice_number: 'INV-2024-002',
    customer_id: 2,
    customer_name: 'Jane Smith',
    status: 'paid',
    issue_date: '2024-01-15',
    due_date: '2024-02-14',
    subtotal: 49.99,
    tax_amount: 4.99,
    total_amount: 54.98,
    currency: 'USD',
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-16T00:00:00Z',
    line_items: [
      {
        id: 2,
        description: 'Basic Internet Service',
        quantity: 1,
        unit_price: 49.99,
        total_price: 49.99,
      },
    ],
  },
  {
    id: 3,
    invoice_number: 'INV-2024-003',
    customer_id: 3,
    customer_name: 'Bob Johnson',
    status: 'overdue',
    issue_date: '2023-12-01',
    due_date: '2023-12-31',
    subtotal: 79.99,
    tax_amount: 7.99,
    total_amount: 87.98,
    currency: 'USD',
    created_at: '2023-12-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    line_items: [
      {
        id: 3,
        description: 'Standard Internet Service',
        quantity: 1,
        unit_price: 79.99,
        total_price: 79.99,
      },
    ],
  },
];

// Mock payment data
const mockPayments: Payment[] = [
  {
    id: 1,
    invoice_id: 2,
    customer_id: 2,
    amount: 54.98,
    currency: 'USD',
    payment_method: 'credit_card',
    payment_date: '2024-01-16T10:30:00Z',
    reference_number: 'CC-2024-001',
    notes: 'Automatic payment',
    created_at: '2024-01-16T10:30:00Z',
  },
  {
    id: 2,
    invoice_id: 1,
    customer_id: 1,
    amount: 50.00,
    currency: 'USD',
    payment_method: 'bank_transfer',
    payment_date: '2024-01-20T14:15:00Z',
    reference_number: 'BT-2024-001',
    notes: 'Partial payment',
    created_at: '2024-01-20T14:15:00Z',
  },
];

export const billingHandlers = [
  // GET /invoices - List invoices with pagination and filters
  rest.get('http://localhost:8000/invoices', (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const perPage = parseInt(req.url.searchParams.get('per_page') || '10');
    const customerId = req.url.searchParams.get('customer_id');
    const status = req.url.searchParams.get('status');
    const dateFrom = req.url.searchParams.get('date_from');
    const dateTo = req.url.searchParams.get('date_to');

    // Filter invoices based on query params
    let filteredInvoices = [...mockInvoices];
    
    if (customerId) {
      filteredInvoices = filteredInvoices.filter(
        (invoice) => invoice.customer_id === parseInt(customerId)
      );
    }
    
    if (status) {
      filteredInvoices = filteredInvoices.filter(
        (invoice) => invoice.status === status
      );
    }

    if (dateFrom) {
      filteredInvoices = filteredInvoices.filter(
        (invoice) => invoice.issue_date && invoice.issue_date >= dateFrom
      );
    }

    if (dateTo) {
      filteredInvoices = filteredInvoices.filter(
        (invoice) => invoice.issue_date && invoice.issue_date <= dateTo
      );
    }

    // Paginate results
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    const paginatedInvoices = filteredInvoices.slice(startIndex, endIndex);

    const response: PaginatedInvoiceResponse = {
      data: paginatedInvoices,
      pagination: {
        page,
        per_page: perPage,
        total: filteredInvoices.length,
        total_pages: Math.ceil(filteredInvoices.length / perPage),
      },
    };

    return res(ctx.status(200), ctx.json(response));
  }),

  // GET /invoices/:id - Get single invoice
  rest.get('http://localhost:8000/invoices/:id', (req, res, ctx) => {
    const { id } = req.params;
    const invoice = mockInvoices.find((i) => i.id === parseInt(id as string));
    
    if (!invoice) {
      return res(ctx.status(404));
    }
    
    return res(ctx.status(200), ctx.json(invoice));
  }),

  // POST /invoices - Create invoice
  rest.post('http://localhost:8000/invoices', async (req, res, ctx) => {
    const newInvoice = await req.json() as Partial<Invoice>;
    
    const invoice: Invoice = {
      id: mockInvoices.length + 1,
      invoice_number: `INV-2024-${String(mockInvoices.length + 1).padStart(3, '0')}`,
      customer_id: newInvoice.customer_id || 0,
      customer_name: 'New Customer',
      status: 'draft',
      issue_date: new Date().toISOString().split('T')[0],
      due_date: newInvoice.due_date || new Date().toISOString().split('T')[0],
      subtotal: 0,
      tax_amount: 0,
      total_amount: 0,
      currency: 'USD',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      line_items: newInvoice.line_items || [],
    };
    
    mockInvoices.push(invoice);
    return res(ctx.status(201), ctx.json(invoice));
  }),

  // GET /payments - List payments with pagination and filters
  rest.get('http://localhost:8000/payments', (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const perPage = parseInt(req.url.searchParams.get('per_page') || '10');
    const customerId = req.url.searchParams.get('customer_id');
    const invoiceId = req.url.searchParams.get('invoice_id');

    // Filter payments based on query params
    let filteredPayments = [...mockPayments];
    
    if (customerId) {
      filteredPayments = filteredPayments.filter(
        (payment) => payment.customer_id === parseInt(customerId)
      );
    }
    
    if (invoiceId) {
      filteredPayments = filteredPayments.filter(
        (payment) => payment.invoice_id === parseInt(invoiceId)
      );
    }

    // Paginate results
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    const paginatedPayments = filteredPayments.slice(startIndex, endIndex);

    const response: PaginatedPaymentResponse = {
      data: paginatedPayments,
      pagination: {
        page,
        per_page: perPage,
        total: filteredPayments.length,
        total_pages: Math.ceil(filteredPayments.length / perPage),
      },
    };

    return res(ctx.status(200), ctx.json(response));
  }),

  // POST /payments - Create payment
  rest.post('http://localhost:8000/payments', async (req, res, ctx) => {
    const newPayment = await req.json() as Partial<Payment>;
    
    const payment: Payment = {
      id: mockPayments.length + 1,
      invoice_id: newPayment.invoice_id || 0,
      customer_id: newPayment.customer_id || 0,
      amount: newPayment.amount || 0,
      currency: 'USD',
      payment_method: newPayment.payment_method || 'credit_card',
      payment_date: new Date().toISOString(),
      reference_number: newPayment.reference_number,
      notes: newPayment.notes,
      created_at: new Date().toISOString(),
    };
    
    mockPayments.push(payment);
    return res(ctx.status(201), ctx.json(payment));
  }),
];
