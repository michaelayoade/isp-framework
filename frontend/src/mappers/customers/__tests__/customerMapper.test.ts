import { toCustomerUI, toCustomerDTO, toAddressUI, toAddressDTO } from '../customerMapper';
import type { Customer as CustomerDTO, Address as AddressDTO } from '@/api/_schemas';

describe('customerMapper', () => {
  describe('toCustomerUI', () => {
    it('should convert API DTO to UI model', () => {
      const dto: CustomerDTO = {
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
      };

      const result = toCustomerUI(dto);

      expect(result).toEqual({
        id: 1,
        name: 'John Doe',
        email: 'john@example.com',
        phone: '+1234567890',
        status: 'active',
        createdAt: new Date('2023-01-01T00:00:00Z'),
        updatedAt: new Date('2023-01-02T00:00:00Z'),
        servicePlan: 'Premium',
        monthlyFee: 99.99,
        address: {
          street: '123 Main St',
          city: 'Anytown',
          state: 'CA',
          zipCode: '12345',
          country: 'USA',
        },
      });
    });

    it('should handle missing optional fields', () => {
      const dto: CustomerDTO = {
        id: 2,
        name: 'Jane Smith',
        email: 'jane@example.com',
        phone: '+0987654321',
        status: 'inactive',
        created_at: '2023-02-01T00:00:00Z',
        updated_at: '2023-02-02T00:00:00Z',
      };

      const result = toCustomerUI(dto);

      expect(result).toEqual({
        id: 2,
        name: 'Jane Smith',
        email: 'jane@example.com',
        phone: '+0987654321',
        status: 'inactive',
        createdAt: new Date('2023-02-01T00:00:00Z'),
        updatedAt: new Date('2023-02-02T00:00:00Z'),
        address: undefined,
        servicePlan: undefined,
        monthlyFee: undefined,
      });
    });

    it('should provide default status for invalid values', () => {
      const dto = {
        id: 3,
        name: 'Test User',
        email: 'test@example.com',
        phone: '+1111111111',
        status: 'invalid_status' as 'active' | 'inactive' | 'suspended',
        created_at: '2023-03-01T00:00:00Z',
        updated_at: '2023-03-02T00:00:00Z',
      };

      const result = toCustomerUI(dto);

      expect(result.status).toBe('active'); // Default value
    });
  });

  describe('toCustomerDTO', () => {
    it('should convert UI model to API DTO', () => {
      const ui = {
        id: 1,
        name: 'John Doe',
        email: 'john@example.com',
        phone: '+1234567890',
        status: 'active' as const,
        createdAt: new Date('2023-01-01T00:00:00Z'),
        updatedAt: new Date('2023-01-02T00:00:00Z'),
        servicePlan: 'Premium',
        address: {
          street: '123 Main St',
          city: 'Anytown',
          state: 'CA',
          zipCode: '12345',
          country: 'USA',
        },
      };

      const result = toCustomerDTO(ui);

      expect(result).toEqual({
        name: 'John Doe',
        email: 'john@example.com',
        phone: '+1234567890',
        status: 'active',
        service_plan: 'Premium',
        address: {
          street: '123 Main St',
          city: 'Anytown',
          state: 'CA',
          zip_code: '12345',
          country: 'USA',
        },
      });
    });

    it('should handle partial UI model', () => {
      const ui = {
        name: 'Partial User',
        email: 'partial@example.com',
      };

      const result = toCustomerDTO(ui);

      expect(result).toEqual({
        name: 'Partial User',
        email: 'partial@example.com',
        phone: undefined,
        status: undefined,
        service_plan: undefined,
        address: undefined,
      });
    });
  });

  describe('toAddressUI', () => {
    it('should convert address DTO to UI model', () => {
      const dto: AddressDTO = {
        street: '456 Oak Ave',
        city: 'Springfield',
        state: 'IL',
        zip_code: '62701',
        country: 'USA',
      };

      const result = toAddressUI(dto);

      expect(result).toEqual({
        street: '456 Oak Ave',
        city: 'Springfield',
        state: 'IL',
        zipCode: '62701',
        country: 'USA',
      });
    });

    it('should provide defaults for missing fields', () => {
      const dto = {} as AddressDTO;

      const result = toAddressUI(dto);

      expect(result).toEqual({
        street: '',
        city: '',
        state: '',
        zipCode: '',
        country: '',
      });
    });
  });

  describe('toAddressDTO', () => {
    it('should convert address UI model to DTO', () => {
      const ui = {
        street: '789 Pine St',
        city: 'Portland',
        state: 'OR',
        zipCode: '97201',
        country: 'USA',
      };

      const result = toAddressDTO(ui);

      expect(result).toEqual({
        street: '789 Pine St',
        city: 'Portland',
        state: 'OR',
        zip_code: '97201',
        country: 'USA',
      });
    });
  });
});
