# ISP Framework - Services Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a modular architecture for the services module frontend, covering Internet services, Voice services, Bundle packages, service provisioning, and customer service management.

## Modular Architecture

```
src/features/services/
├── components/
│   ├── dashboard/              # Services dashboard
│   ├── internet/              # Internet service management
│   ├── voice/                 # Voice service management
│   ├── bundles/               # Bundle packages
│   ├── provisioning/          # Service provisioning
│   ├── templates/             # Service templates
│   └── shared/                # Shared service components
├── hooks/                     # Service-specific hooks
├── services/                  # Service API layer
├── types/                     # Service type definitions
├── utils/                     # Service utilities
└── constants/                 # Service constants
```

## 1. Type Definitions

```typescript
// src/features/services/types/index.ts
export interface ServiceBase {
  id: number;
  name: string;
  description: string;
  status: ServiceStatus;
  monthly_fee: number;
  setup_fee?: number;
  category: ServiceCategory;
  created_at: string;
  updated_at: string;
}

export type ServiceStatus = 'active' | 'inactive' | 'suspended' | 'terminated';
export type ServiceCategory = 'internet' | 'voice' | 'bundle' | 'recurring';

export interface InternetService extends ServiceBase {
  category: 'internet';
  bandwidth_down: number;
  bandwidth_up: number;
  data_limit?: number;
  technology: 'fiber' | 'wireless' | 'dsl' | 'satellite';
  static_ip: boolean;
  ip_addresses?: string[];
}

export interface VoiceService extends ServiceBase {
  category: 'voice';
  phone_number: string;
  included_minutes?: number;
  international_calling: boolean;
  voicemail: boolean;
  call_forwarding: boolean;
}

export interface BundleService extends ServiceBase {
  category: 'bundle';
  included_services: ServiceBase[];
  discount_percentage: number;
  bundle_type: 'internet_voice' | 'triple_play' | 'custom';
}

export interface CustomerService {
  id: number;
  customer_id: number;
  service_id: number;
  service: ServiceBase;
  status: CustomerServiceStatus;
  activation_date: string;
  suspension_date?: string;
  termination_date?: string;
  ip_assignments?: IPAssignment[];
  usage_stats?: UsageStats;
  billing_info: ServiceBilling;
}

export type CustomerServiceStatus = 'pending' | 'active' | 'suspended' | 'terminated';

export interface IPAssignment {
  id: number;
  ip_address: string;
  ip_type: 'ipv4' | 'ipv6';
  assignment_type: 'static' | 'dynamic';
  assigned_at: string;
}

export interface UsageStats {
  period: string;
  data_used: number;
  data_limit?: number;
  minutes_used?: number;
  minutes_included?: number;
}

export interface ServiceBilling {
  monthly_charge: number;
  prorated_charge?: number;
  next_billing_date: string;
  billing_cycle: 'monthly' | 'quarterly' | 'yearly';
}

export interface ServiceTemplate {
  id: number;
  name: string;
  description: string;
  category: ServiceCategory;
  default_config: Record<string, any>;
  pricing_model: 'fixed' | 'tiered' | 'usage_based';
  is_active: boolean;
}

export interface ServiceFilters {
  page?: number;
  per_page?: number;
  search?: string;
  category?: ServiceCategory;
  status?: ServiceStatus;
  customer_id?: number;
  technology?: string;
  price_min?: number;
  price_max?: number;
}
```

## 2. Service Layer

```typescript
// src/features/services/services/service-management.ts
import { apiClient } from '@/lib/api-client';
import type { 
  ServiceBase, 
  InternetService, 
  VoiceService, 
  BundleService,
  CustomerService,
  ServiceTemplate,
  ServiceFilters,
  PaginatedResponse 
} from '../types';

export class ServiceManagementService {
  private readonly basePath = '/services';

  // Service catalog operations
  async getServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<ServiceBase>> {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data;
  }

  async getService(id: number): Promise<ServiceBase> {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data;
  }

  // Internet services
  async getInternetServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<InternetService>> {
    const response = await apiClient.get(`${this.basePath}/internet`, { params: filters });
    return response.data;
  }

  async createInternetService(data: CreateInternetServiceData): Promise<InternetService> {
    const response = await apiClient.post(`${this.basePath}/internet`, data);
    return response.data;
  }

  async updateInternetService(id: number, data: UpdateInternetServiceData): Promise<InternetService> {
    const response = await apiClient.put(`${this.basePath}/internet/${id}`, data);
    return response.data;
  }

  // Voice services
  async getVoiceServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<VoiceService>> {
    const response = await apiClient.get(`${this.basePath}/voice`, { params: filters });
    return response.data;
  }

  async createVoiceService(data: CreateVoiceServiceData): Promise<VoiceService> {
    const response = await apiClient.post(`${this.basePath}/voice`, data);
    return response.data;
  }

  // Bundle services
  async getBundleServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<BundleService>> {
    const response = await apiClient.get(`${this.basePath}/bundles`, { params: filters });
    return response.data;
  }

  async createBundleService(data: CreateBundleServiceData): Promise<BundleService> {
    const response = await apiClient.post(`${this.basePath}/bundles`, data);
    return response.data;
  }

  // Customer service management
  async getCustomerServices(customerId: number): Promise<CustomerService[]> {
    const response = await apiClient.get(`/customers/${customerId}/services`);
    return response.data;
  }

  async assignServiceToCustomer(customerId: number, serviceId: number, config?: any): Promise<CustomerService> {
    const response = await apiClient.post(`/customers/${customerId}/services`, {
      service_id: serviceId,
      configuration: config,
    });
    return response.data;
  }

  async updateCustomerService(customerId: number, serviceId: number, data: any): Promise<CustomerService> {
    const response = await apiClient.put(`/customers/${customerId}/services/${serviceId}`, data);
    return response.data;
  }

  async suspendCustomerService(customerId: number, serviceId: number, reason?: string): Promise<CustomerService> {
    const response = await apiClient.post(`/customers/${customerId}/services/${serviceId}/suspend`, { reason });
    return response.data;
  }

  async reactivateCustomerService(customerId: number, serviceId: number): Promise<CustomerService> {
    const response = await apiClient.post(`/customers/${customerId}/services/${serviceId}/reactivate`);
    return response.data;
  }

  async terminateCustomerService(customerId: number, serviceId: number, reason?: string): Promise<CustomerService> {
    const response = await apiClient.post(`/customers/${customerId}/services/${serviceId}/terminate`, { reason });
    return response.data;
  }

  // Service templates
  async getServiceTemplates(category?: ServiceCategory): Promise<ServiceTemplate[]> {
    const response = await apiClient.get(`${this.basePath}/templates`, { 
      params: category ? { category } : {} 
    });
    return response.data;
  }

  async createServiceTemplate(data: CreateServiceTemplateData): Promise<ServiceTemplate> {
    const response = await apiClient.post(`${this.basePath}/templates`, data);
    return response.data;
  }

  // Service provisioning
  async provisionService(customerId: number, serviceId: number): Promise<{ status: string; details: any }> {
    const response = await apiClient.post(`/customers/${customerId}/services/${serviceId}/provision`);
    return response.data;
  }

  async getProvisioningStatus(customerId: number, serviceId: number): Promise<{ status: string; progress: number }> {
    const response = await apiClient.get(`/customers/${customerId}/services/${serviceId}/provision/status`);
    return response.data;
  }
}

export const serviceManagementService = new ServiceManagementService();
```

## 3. Core Components

### 3.1 Services Dashboard

```typescript
// src/features/services/components/dashboard/ServicesDashboard.tsx
'use client';

import { useState } from 'react';
import { useServices, useServiceStats } from '../../hooks';
import { ServiceStatsCards } from './ServiceStatsCards';
import { ServiceCatalog } from '../catalog/ServiceCatalog';
import { ServiceUsageChart } from '../charts/ServiceUsageChart';
import { RecentActivations } from './RecentActivations';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Plus, Settings, BarChart3 } from 'lucide-react';

export function ServicesDashboard() {
  const [activeTab, setActiveTab] = useState('catalog');
  const { data: serviceStats } = useServiceStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Services</h1>
          <p className="text-muted-foreground">
            Manage service catalog and customer subscriptions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <BarChart3 className="mr-2 h-4 w-4" />
            Analytics
          </Button>
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Templates
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Service
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {serviceStats && <ServiceStatsCards stats={serviceStats} />}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="catalog">Service Catalog</TabsTrigger>
          <TabsTrigger value="internet">Internet Services</TabsTrigger>
          <TabsTrigger value="voice">Voice Services</TabsTrigger>
          <TabsTrigger value="bundles">Bundle Packages</TabsTrigger>
          <TabsTrigger value="provisioning">Provisioning</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ServiceCatalog />
            </div>
            <div className="space-y-6">
              <ServiceUsageChart />
              <RecentActivations />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="internet">
          <InternetServiceManagement />
        </TabsContent>

        <TabsContent value="voice">
          <VoiceServiceManagement />
        </TabsContent>

        <TabsContent value="bundles">
          <BundleServiceManagement />
        </TabsContent>

        <TabsContent value="provisioning">
          <ServiceProvisioningDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3.2 Internet Service Management

```typescript
// src/features/services/components/internet/InternetServiceManagement.tsx
'use client';

import { useState } from 'react';
import { useInternetServices } from '../../hooks';
import { InternetServiceList } from './InternetServiceList';
import { InternetServiceForm } from './InternetServiceForm';
import { InternetServiceFilters } from './InternetServiceFilters';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus } from 'lucide-react';
import type { ServiceFilters } from '../../types';

export function InternetServiceManagement() {
  const [filters, setFilters] = useState<ServiceFilters>({
    page: 1,
    per_page: 20,
    category: 'internet',
  });
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const { data, isLoading } = useInternetServices(filters);

  const handleFiltersChange = (newFilters: Partial<ServiceFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Internet Services</CardTitle>
              <p className="text-sm text-muted-foreground">
                Manage broadband and internet service packages
              </p>
            </div>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Internet Service
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Internet Service</DialogTitle>
                </DialogHeader>
                <InternetServiceForm
                  onSubmit={async (data) => {
                    // Handle creation
                    setIsCreateDialogOpen(false);
                  }}
                  onCancel={() => setIsCreateDialogOpen(false)}
                />
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <InternetServiceFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />
          
          <InternetServiceList
            data={data}
            isLoading={isLoading}
            onPageChange={(page) => setFilters(prev => ({ ...prev, page }))}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

### 3.3 Service Form Components

```typescript
// src/features/services/components/internet/InternetServiceForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { InternetService } from '../../types';

const internetServiceSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().optional(),
  monthly_fee: z.number().min(0, 'Monthly fee must be positive'),
  setup_fee: z.number().min(0, 'Setup fee must be positive').optional(),
  bandwidth_down: z.number().min(1, 'Download bandwidth must be at least 1 Mbps'),
  bandwidth_up: z.number().min(1, 'Upload bandwidth must be at least 1 Mbps'),
  data_limit: z.number().optional(),
  technology: z.enum(['fiber', 'wireless', 'dsl', 'satellite']),
  static_ip: z.boolean(),
});

type InternetServiceFormData = z.infer<typeof internetServiceSchema>;

interface InternetServiceFormProps {
  service?: InternetService;
  onSubmit: (data: InternetServiceFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function InternetServiceForm({ service, onSubmit, onCancel, isLoading }: InternetServiceFormProps) {
  const form = useForm<InternetServiceFormData>({
    resolver: zodResolver(internetServiceSchema),
    defaultValues: {
      name: service?.name || '',
      description: service?.description || '',
      monthly_fee: service?.monthly_fee || 0,
      setup_fee: service?.setup_fee || 0,
      bandwidth_down: service?.bandwidth_down || 10,
      bandwidth_up: service?.bandwidth_up || 5,
      data_limit: service?.data_limit || undefined,
      technology: service?.technology || 'fiber',
      static_ip: service?.static_ip || false,
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Service Name</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Fiber 100Mbps" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="technology"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Technology</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select technology" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="fiber">Fiber Optic</SelectItem>
                        <SelectItem value="wireless">Wireless</SelectItem>
                        <SelectItem value="dsl">DSL</SelectItem>
                        <SelectItem value="satellite">Satellite</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Service description and features"
                      {...field} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Technical Specifications */}
        <Card>
          <CardHeader>
            <CardTitle>Technical Specifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="bandwidth_down"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Download Speed (Mbps)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        placeholder="100"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="bandwidth_up"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Upload Speed (Mbps)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        placeholder="50"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="data_limit"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Data Limit (GB)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        placeholder="Leave empty for unlimited"
                        {...field}
                        onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="static_ip"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Static IP Address</FormLabel>
                      <p className="text-sm text-muted-foreground">
                        Include static IP address with this service
                      </p>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* Pricing */}
        <Card>
          <CardHeader>
            <CardTitle>Pricing</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="monthly_fee"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monthly Fee ($)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        step="0.01"
                        placeholder="99.99"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="setup_fee"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Setup Fee ($)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        step="0.01"
                        placeholder="0.00"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex justify-end space-x-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Saving...' : service ? 'Update Service' : 'Create Service'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/services/hooks/useServices.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serviceManagementService } from '../services';
import { useToast } from '@/hooks/use-toast';
import type { ServiceFilters, CreateInternetServiceData } from '../types';

export function useServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', filters],
    queryFn: () => serviceManagementService.getServices(filters),
    keepPreviousData: true,
  });
}

export function useInternetServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', 'internet', filters],
    queryFn: () => serviceManagementService.getInternetServices(filters),
    keepPreviousData: true,
  });
}

export function useVoiceServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', 'voice', filters],
    queryFn: () => serviceManagementService.getVoiceServices(filters),
    keepPreviousData: true,
  });
}

export function useBundleServices(filters: ServiceFilters = {}) {
  return useQuery({
    queryKey: ['services', 'bundles', filters],
    queryFn: () => serviceManagementService.getBundleServices(filters),
    keepPreviousData: true,
  });
}

export function useCustomerServices(customerId: number) {
  return useQuery({
    queryKey: ['customers', customerId, 'services'],
    queryFn: () => serviceManagementService.getCustomerServices(customerId),
    enabled: !!customerId,
  });
}

export function useCreateInternetService() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateInternetServiceData) => 
      serviceManagementService.createInternetService(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
      toast({
        title: 'Success',
        description: 'Internet service created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create internet service',
        variant: 'destructive',
      });
    },
  });
}

export function useAssignServiceToCustomer() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ customerId, serviceId, config }: { 
      customerId: number; 
      serviceId: number; 
      config?: any 
    }) => serviceManagementService.assignServiceToCustomer(customerId, serviceId, config),
    onSuccess: (_, { customerId }) => {
      queryClient.invalidateQueries({ queryKey: ['customers', customerId, 'services'] });
      toast({
        title: 'Success',
        description: 'Service assigned to customer successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to assign service to customer',
        variant: 'destructive',
      });
    },
  });
}

export function useServiceStats() {
  return useQuery({
    queryKey: ['services', 'stats'],
    queryFn: () => {
      // This would typically call a stats endpoint
      // For now, return mock data structure
      return Promise.resolve({
        total_services: 0,
        active_services: 0,
        internet_services: 0,
        voice_services: 0,
        bundle_services: 0,
        total_subscriptions: 0,
        monthly_revenue: 0,
      });
    },
    refetchInterval: 5 * 60 * 1000,
  });
}
```

## 5. Implementation Phases

### Phase 1: Core Structure (Days 1-2)
- Set up feature module structure
- Implement types and service layer
- Create basic hooks and utilities

### Phase 2: Service Catalog (Days 3-4)
- Build service catalog dashboard
- Implement service CRUD operations
- Create service templates system

### Phase 3: Internet Services (Days 5-6)
- Build internet service management
- Create bandwidth and technology configuration
- Implement IP address management

### Phase 4: Voice & Bundle Services (Days 7-8)
- Implement voice service management
- Create bundle package system
- Add discount and pricing logic

### Phase 5: Customer Service Management (Days 9-10)
- Build customer service assignment
- Implement service provisioning
- Create usage tracking and billing integration

This modular architecture provides a comprehensive foundation for managing all types of ISP services while maintaining flexibility for future service types and features.
