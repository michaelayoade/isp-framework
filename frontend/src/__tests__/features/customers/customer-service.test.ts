import { customerService } from '@/features/customers/services/customer-service';
import { Customer, CreateCustomerData, UpdateCustomerData } from '@/features/customers/types';

// Mock fetch globally
global.fetch = jest.fn();

const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('CustomerService', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  const mockCustomer: Customer = {
    id: 1,
    first_name: 'John',
    last_name: 'Doe',
    email: 'john.doe@example.com',
    phone: '+1234567890',
    address: {
      street: '123 Main St',
      city: 'Anytown',
      state: 'CA',
      zip: '12345'
    },
    status: 'active',
    service_plan: 'Fiber 100Mbps',
    monthly_fee: 89.99,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  };

  describe('getCustomers', () => {
    it('should fetch customers with default parameters', async () => {
      const mockResponse = {
        items: [mockCustomer],
        total: 1,
        page: 1,
        per_page: 10,
        total_pages: 1
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await customerService.getCustomers();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/customers',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should fetch customers with filters', async () => {
      const filters = { search: 'john', status: 'active' as const, page: 2 };
      const mockResponse = {
        items: [mockCustomer],
        total: 1,
        page: 2,
        per_page: 10,
        total_pages: 1
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await customerService.getCustomers(filters);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/customers?search=john&status=active&page=2',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getCustomer', () => {
    it('should fetch a single customer by ID', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomer,
      } as Response);

      const result = await customerService.getCustomer(1);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/customers/1',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockCustomer);
    });
  });

  describe('createCustomer', () => {
    it('should create a new customer', async () => {
      const createData: CreateCustomerData = {
        first_name: 'Jane',
        last_name: 'Smith',
        email: 'jane.smith@example.com',
        phone: '+1987654321',
        address: {
          street: '456 Oak Ave',
          city: 'Another City',
          state: 'NY',
          zip: '67890'
        },
        service_plan: 'Fiber 50Mbps'
      };

      const createdCustomer = { ...mockCustomer, ...createData, id: 2 };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => createdCustomer,
      } as Response);

      const result = await customerService.createCustomer(createData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/customers',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(createData),
        })
      );
      expect(result).toEqual(createdCustomer);
    });
  });

  describe('updateCustomer', () => {
    it('should update an existing customer', async () => {
      const updateData: UpdateCustomerData = {
        first_name: 'John Updated',
        status: 'suspended'
      };

      const updatedCustomer = { ...mockCustomer, ...updateData };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedCustomer,
      } as Response);

      const result = await customerService.updateCustomer(1, updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/customers/1',
        expect.objectContaining({
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateData),
        })
      );
      expect(result).toEqual(updatedCustomer);
    });
  });

  describe('deleteCustomer', () => {
    it('should delete a customer', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response);

      await customerService.deleteCustomer(1);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/customers/1',
        expect.objectContaining({
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });
  });

  describe('error handling', () => {
    it('should throw an error when the response is not ok', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      } as Response);

      await expect(customerService.getCustomer(999)).rejects.toThrow('HTTP error! status: 404');
    });
  });
});
