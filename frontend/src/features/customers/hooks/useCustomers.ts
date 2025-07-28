import { useState, useEffect, useCallback } from 'react';
import { Customer, CustomerFilters, CustomerStats } from '../types';
import { customerService } from '../services/customer-service';

export function useCustomers(filters: CustomerFilters = {}) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  });

  const fetchCustomers = useCallback(async (newFilters: CustomerFilters = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const mergedFilters = { ...filters, ...newFilters };
      const response = await customerService.getCustomers(mergedFilters);
      
      setCustomers(response.items);
      setPagination({
        page: response.page,
        per_page: response.per_page,
        total: response.total,
        total_pages: response.total_pages,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch customers');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  const refetch = () => fetchCustomers();
  
  const updateFilters = (newFilters: CustomerFilters) => {
    fetchCustomers(newFilters);
  };

  return {
    customers,
    loading,
    error,
    pagination,
    refetch,
    updateFilters,
  };
}

export function useCustomer(id: number) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCustomer = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await customerService.getCustomer(id);
        setCustomer(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch customer');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchCustomer();
    }
  }, [id]);

  const refetch = async () => {
    if (id) {
      try {
        setLoading(true);
        const response = await customerService.getCustomer(id);
        setCustomer(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch customer');
      } finally {
        setLoading(false);
      }
    }
  };

  return {
    customer,
    loading,
    error,
    refetch,
  };
}

export function useCustomerStats() {
  const [stats, setStats] = useState<CustomerStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await customerService.getCustomerStats();
        setStats(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch customer stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const refetch = async () => {
    try {
      setLoading(true);
      const response = await customerService.getCustomerStats();
      setStats(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch customer stats');
    } finally {
      setLoading(false);
    }
  };

  return {
    stats,
    loading,
    error,
    refetch,
  };
}
