import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useCustomers } from '../useCustomers';

// Create a wrapper component for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const TestWrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
  
  TestWrapper.displayName = 'TestWrapper';
  return TestWrapper;
};

describe('useCustomers', () => {
  it('should fetch and map customers from API', async () => {
    const { result } = renderHook(() => useCustomers(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.loading).toBe(true);
    expect(result.current.customers).toEqual([]);

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Check that data was fetched and mapped correctly
    expect(result.current.customers).toHaveLength(3);
    expect(result.current.customers[0]).toEqual({
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

    // Check pagination
    expect(result.current.pagination).toEqual({
      page: 1,
      per_page: 10,
      total: 3,
      total_pages: 1,
    });

    expect(result.current.error).toBe(null);
  });

  it('should handle filters correctly', async () => {
    const { result } = renderHook(
      () => useCustomers({ search: 'john', status: 'active' }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should only return John Doe (active status + name matches)
    expect(result.current.customers).toHaveLength(1);
    expect(result.current.customers[0].name).toBe('John Doe');
    expect(result.current.customers[0].status).toBe('active');
  });

  it('should handle pagination', async () => {
    const { result } = renderHook(
      () => useCustomers({ page: 1, per_page: 2 }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should return first 2 customers
    expect(result.current.customers).toHaveLength(2);
    expect(result.current.pagination).toEqual({
      page: 1,
      per_page: 2,
      total: 3,
      total_pages: 2,
    });
  });

  it('should handle empty results', async () => {
    const { result } = renderHook(
      () => useCustomers({ search: 'nonexistent' }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.customers).toHaveLength(0);
    expect(result.current.pagination.total).toBe(0);
  });

  it('should handle customers without addresses', async () => {
    const { result } = renderHook(
      () => useCustomers({ search: 'jane' }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.customers).toHaveLength(1);
    expect(result.current.customers[0].name).toBe('Jane Smith');
    expect(result.current.customers[0].address).toBeUndefined();
  });
});
