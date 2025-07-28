# ISP Framework - Customer Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a comprehensive approach to building a modular, maintainable customer module frontend for the ISP Framework. The architecture emphasizes scalability, reusability, and ease of feature addition.

## Current Tech Stack

- **Framework**: Next.js 15.4.4 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: TanStack Query (React Query)
- **Tables**: TanStack Table
- **Forms**: React Hook Form + Zod validation
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React

## Modular Architecture Overview

```
src/
├── app/
│   └── customers/                    # Route-based pages
├── features/
│   └── customers/                    # Feature-specific modules
│       ├── components/               # Customer-specific components
│       ├── hooks/                    # Customer-specific hooks
│       ├── services/                 # Customer API services
│       ├── types/                    # Customer type definitions
│       ├── utils/                    # Customer utilities
│       └── constants/                # Customer constants
├── components/
│   ├── ui/                          # Reusable UI components
│   └── shared/                      # Shared business components
└── lib/                             # Global utilities and configs
```

## 1. Feature-Based Module Structure

### 1.1 Core Customer Feature Module

Create a dedicated feature module for customers:

```typescript
// src/features/customers/index.ts
export * from './components';
export * from './hooks';
export * from './services';
export * from './types';
export * from './utils';
export * from './constants';
```

### 1.2 Customer Types & Interfaces

```typescript
// src/features/customers/types/index.ts
export interface Customer {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  status: CustomerStatus;
  category?: string;
  location_id?: number;
  portal_id?: string;
  billing_account?: BillingAccount;
  services?: CustomerService[];
  created_at: string;
  updated_at: string;
}

export type CustomerStatus = 'active' | 'suspended' | 'pending' | 'cancelled';

export interface CustomerFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: CustomerStatus;
  category?: string;
  location_id?: number;
  date_from?: string;
  date_to?: string;
}

export interface CustomerFormData {
  name: string;
  email: string;
  phone?: string;
  address?: string;
  category?: string;
  location_id?: number;
}

export interface CustomerStats {
  total_customers: number;
  active_customers: number;
  suspended_customers: number;
  pending_customers: number;
  monthly_growth: number;
  revenue_per_customer: number;
}
```

### 1.3 Customer Services Layer

```typescript
// src/features/customers/services/customer-service.ts
import { apiClient } from '@/lib/api-client';
import type { 
  Customer, 
  CustomerFilters, 
  CustomerFormData, 
  CustomerStats,
  PaginatedResponse 
} from '../types';

export class CustomerService {
  private readonly basePath = '/customers';

  async getCustomers(filters: CustomerFilters = {}): Promise<PaginatedResponse<Customer>> {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data;
  }

  async getCustomer(id: number): Promise<Customer> {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data;
  }

  async createCustomer(data: CustomerFormData): Promise<Customer> {
    const response = await apiClient.post(this.basePath, data);
    return response.data;
  }

  async updateCustomer(id: number, data: Partial<CustomerFormData>): Promise<Customer> {
    const response = await apiClient.put(`${this.basePath}/${id}`, data);
    return response.data;
  }

  async deleteCustomer(id: number): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async updateCustomerStatus(
    id: number, 
    status: CustomerStatus, 
    reason?: string
  ): Promise<Customer> {
    const response = await apiClient.patch(`${this.basePath}/${id}/status`, {
      status,
      reason,
    });
    return response.data;
  }

  async getCustomerStats(): Promise<CustomerStats> {
    const response = await apiClient.get(`${this.basePath}/stats`);
    return response.data;
  }

  async exportCustomers(filters: CustomerFilters = {}): Promise<Blob> {
    const response = await apiClient.get(`${this.basePath}/export`, {
      params: filters,
      responseType: 'blob',
    });
    return response.data;
  }
}

export const customerService = new CustomerService();
```

## 2. Component Architecture

### 2.1 Component Hierarchy

```
CustomerModule/
├── CustomerDashboard/              # Main dashboard component
├── CustomerList/                   # Customer listing with table
├── CustomerDetails/                # Customer detail view
├── CustomerForm/                   # Create/Edit customer form
├── CustomerStats/                  # Statistics widgets
├── CustomerFilters/                # Advanced filtering
├── CustomerActions/                # Bulk actions
└── CustomerModals/                 # Modal dialogs
    ├── CreateCustomerModal/
    ├── EditCustomerModal/
    ├── DeleteCustomerModal/
    └── StatusChangeModal/
```

### 2.2 Customer Dashboard Component

```typescript
// src/features/customers/components/CustomerDashboard.tsx
'use client';

import { useState } from 'react';
import { useCustomers, useCustomerStats } from '../hooks';
import { CustomerStats } from './CustomerStats';
import { CustomerList } from './CustomerList';
import { CustomerFilters } from './CustomerFilters';
import { CustomerActions } from './CustomerActions';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import type { CustomerFilters as CustomerFiltersType } from '../types';

export function CustomerDashboard() {
  const [filters, setFilters] = useState<CustomerFiltersType>({
    page: 1,
    per_page: 10,
  });
  const [selectedCustomers, setSelectedCustomers] = useState<number[]>([]);

  const { data: customersData, isLoading } = useCustomers(filters);
  const { data: stats } = useCustomerStats();

  const handleFiltersChange = (newFilters: Partial<CustomerFiltersType>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Customers</h1>
          <p className="text-muted-foreground">
            Manage your customer base and track growth
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Customer
        </Button>
      </div>

      {/* Stats */}
      {stats && <CustomerStats stats={stats} />}

      {/* Filters and Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Management</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <CustomerFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />
          
          {selectedCustomers.length > 0 && (
            <CustomerActions
              selectedCustomers={selectedCustomers}
              onSelectionChange={setSelectedCustomers}
            />
          )}

          <CustomerList
            data={customersData}
            isLoading={isLoading}
            selectedCustomers={selectedCustomers}
            onSelectionChange={setSelectedCustomers}
            onPageChange={handlePageChange}
            currentPage={filters.page || 1}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

## 3. Custom Hooks

### 3.1 Customer Data Hooks

```typescript
// src/features/customers/hooks/useCustomers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { customerService } from '../services';
import { useToast } from '@/hooks/use-toast';
import type { CustomerFilters, CustomerFormData } from '../types';

export function useCustomers(filters: CustomerFilters = {}) {
  return useQuery({
    queryKey: ['customers', filters],
    queryFn: () => customerService.getCustomers(filters),
    keepPreviousData: true,
  });
}

export function useCustomer(id: number) {
  return useQuery({
    queryKey: ['customers', id],
    queryFn: () => customerService.getCustomer(id),
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CustomerFormData) => customerService.createCustomer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      toast({
        title: 'Success',
        description: 'Customer created successfully',
      });
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: 'Failed to create customer',
        variant: 'destructive',
      });
    },
  });
}
```

## 4. Implementation Steps

### Phase 1: Setup Feature Module Structure (Day 1)
1. Create `src/features/customers/` directory structure
2. Set up types, constants, and utilities
3. Create base service layer
4. Set up custom hooks

### Phase 2: Core Components (Days 2-3)
1. Implement CustomerDashboard
2. Build CustomerList with TanStack Table
3. Create CustomerForm with validation
4. Add CustomerStats widgets

### Phase 3: Advanced Features (Days 4-5)
1. Add filtering and search functionality
2. Implement bulk actions
3. Create modal dialogs
4. Add export functionality

### Phase 4: Integration & Testing (Day 6)
1. Connect to backend APIs
2. Add error handling
3. Implement loading states
4. Test all functionality

## 5. Best Practices

### 5.1 Code Organization
- Keep components small and focused
- Use custom hooks for data fetching
- Separate business logic from UI components
- Follow consistent naming conventions

### 5.2 Performance Optimization
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Optimize API calls with proper caching
- Use skeleton loading states

### 5.3 Accessibility
- Add proper ARIA labels
- Ensure keyboard navigation
- Use semantic HTML elements
- Test with screen readers

### 5.4 Error Handling
- Implement global error boundaries
- Show user-friendly error messages
- Add retry mechanisms for failed requests
- Log errors for debugging

## 6. Future Enhancements

### 6.1 Advanced Features
- Real-time customer updates via WebSocket
- Advanced analytics and reporting
- Customer segmentation tools
- Automated customer lifecycle management

### 6.2 Integration Points
- CRM system integration
- Email marketing automation
- Customer support ticketing
- Payment gateway integration

This modular architecture ensures the customer module is maintainable, scalable, and easy to extend with new features as the ISP Framework grows.
