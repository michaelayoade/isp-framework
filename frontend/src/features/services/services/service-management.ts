import { apiClient } from '@/api/client';
import type { 
  ServiceBase, 
  InternetService, 
  VoiceService, 
  BundleService,
  CustomerService,
  ServiceTemplate,
  ServiceFilters,
  CreateInternetServiceData,
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

  async updateInternetService(id: number, data: Partial<CreateInternetServiceData>): Promise<InternetService> {
    const response = await apiClient.put(`${this.basePath}/internet/${id}`, data);
    return response.data;
  }

  // Voice services
  async getVoiceServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<VoiceService>> {
    const response = await apiClient.get(`${this.basePath}/voice`, { params: filters });
    return response.data;
  }

  async createVoiceService(data: Record<string, unknown>): Promise<VoiceService> {
    const response = await apiClient.post(`${this.basePath}/voice`, data);
    return response.data;
  }

  // Bundle services
  async getBundleServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<BundleService>> {
    const response = await apiClient.get(`${this.basePath}/bundles`, { params: filters });
    return response.data;
  }

  async createBundleService(data: Record<string, unknown>): Promise<BundleService> {
    const response = await apiClient.post(`${this.basePath}/bundles`, data);
    return response.data;
  }

  // Customer service management
  async getCustomerServices(customerId: number): Promise<CustomerService[]> {
    const response = await apiClient.get(`/customers/${customerId}/services`);
    return response.data;
  }

  async assignServiceToCustomer(customerId: number, serviceId: number, config?: Record<string, unknown>): Promise<CustomerService> {
    const response = await apiClient.post(`/customers/${customerId}/services`, {
      service_id: serviceId,
      configuration: config,
    });
    return response.data;
  }

  async updateCustomerService(customerId: number, serviceId: number, data: Record<string, unknown>): Promise<CustomerService> {
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

  async createServiceTemplate(data: Record<string, unknown>): Promise<ServiceTemplate> {
    const response = await apiClient.post(`${this.basePath}/templates`, data);
    return response.data;
  }

  // Service provisioning
  async provisionService(customerId: number, serviceId: number): Promise<{ status: string; details: Record<string, unknown> }> {
    const response = await apiClient.post(`/customers/${customerId}/services/${serviceId}/provision`);
    return response.data;
  }

  async getProvisioningStatus(customerId: number, serviceId: number): Promise<{ status: string; progress: number }> {
    const response = await apiClient.get(`/customers/${customerId}/services/${serviceId}/provision/status`);
    return response.data;
  }
}

export const serviceManagementService = new ServiceManagementService();
