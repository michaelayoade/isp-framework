import { rest } from 'msw';
import type { PaginatedCustomerResponse, Customer } from '@/api/_schemas';

// Mock customer data
const mockCustomers: Customer[] = [
  {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1234567890',
    status: 'active',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
    service_plan: 'Premium',
    monthly_fee: 99.99,
    address: {
      street: '123 Main St',
      city: 'Anytown',
      state: 'CA',
      zip_code: '12345',
      country: 'USA',
    },
  },
  {
    id: 2,
    name: 'Jane Smith',
    email: 'jane@example.com',
    phone: '+0987654321',
    status: 'inactive',
    created_at: '2023-02-01T00:00:00Z',
    updated_at: '2023-02-02T00:00:00Z',
    service_plan: 'Basic',
    monthly_fee: 49.99,
  },
  {
    id: 3,
    name: 'Bob Johnson',
    email: 'bob@example.com',
    phone: '+1122334455',
    status: 'suspended',
    created_at: '2023-03-01T00:00:00Z',
    updated_at: '2023-03-02T00:00:00Z',
    service_plan: 'Standard',
    monthly_fee: 79.99,
    address: {
      street: '456 Oak Ave',
      city: 'Springfield',
      state: 'IL',
      zip_code: '62701',
      country: 'USA',
    },
  },
];

export const customerHandlers = [
  // GET /customers - List customers with pagination and filters
  rest.get('http://localhost:8000/customers', (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const perPage = parseInt(req.url.searchParams.get('per_page') || '10');
    const search = req.url.searchParams.get('search');
    const status = req.url.searchParams.get('status');

    // Filter customers based on query params
    let filteredCustomers = [...mockCustomers];
    
    if (search) {
      filteredCustomers = filteredCustomers.filter(
        (customer) =>
          customer.name.toLowerCase().includes(search.toLowerCase()) ||
          customer.email.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    if (status) {
      filteredCustomers = filteredCustomers.filter(
        (customer) => customer.status === status
      );
    }

    // Paginate results
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    const paginatedCustomers = filteredCustomers.slice(startIndex, endIndex);

    const response: PaginatedCustomerResponse = {
      data: paginatedCustomers,
      pagination: {
        page,
        per_page: perPage,
        total: filteredCustomers.length,
        total_pages: Math.ceil(filteredCustomers.length / perPage),
      },
    };

    return res(ctx.status(200), ctx.json(response));
  }),

  // GET /customers/:id - Get single customer
  rest.get('http://localhost:8000/customers/:id', (req, res, ctx) => {
    const { id } = req.params;
    const customer = mockCustomers.find((c) => c.id === parseInt(id as string));
    
    if (!customer) {
      return res(ctx.status(404));
    }
    
    return res(ctx.status(200), ctx.json(customer));
  }),

  // POST /customers - Create customer
  rest.post('http://localhost:8000/customers', async (req, res, ctx) => {
    const newCustomer = await req.json() as Partial<Customer>;
    
    const customer: Customer = {
      id: mockCustomers.length + 1,
      name: newCustomer.name || '',
      email: newCustomer.email || '',
      phone: newCustomer.phone || '',
      status: newCustomer.status || 'active',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      service_plan: newCustomer.service_plan,
      monthly_fee: newCustomer.monthly_fee,
      address: newCustomer.address,
    };
    
    mockCustomers.push(customer);
    return res(ctx.status(201), ctx.json(customer));
  }),

  // PUT /customers/:id - Update customer
  rest.put('http://localhost:8000/customers/:id', async (req, res, ctx) => {
    const { id } = req.params;
    const updates = await req.json() as Partial<Customer>;
    const customerIndex = mockCustomers.findIndex((c) => c.id === parseInt(id as string));
    
    if (customerIndex === -1) {
      return res(ctx.status(404));
    }
    
    mockCustomers[customerIndex] = {
      ...mockCustomers[customerIndex],
      ...updates,
      updated_at: new Date().toISOString(),
    };
    
    return res(ctx.status(200), ctx.json(mockCustomers[customerIndex]));
  }),
];
