import { apiClient } from '@/api/client';
import type {
  RadiusSession,
  RadiusClient,
  RadiusUser,
  RadiusAccounting,
  RadiusStats,
  RadiusFilters,
  CreateRadiusUserData,
  UpdateRadiusUserData,
  CreateRadiusClientData,
  UpdateRadiusClientData,
  PaginatedResponse,
} from '../types';

export class RadiusService {
  private readonly basePath = '/radius';

  // Session management
  async getSessions(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/sessions`, { params: filters });
    return response.data as PaginatedResponse<RadiusSession>;
  }

  async getSession(id: number) {
    const response = await apiClient.get(`${this.basePath}/sessions/${id}`);
    return response.data as RadiusSession;
  }

  async disconnectSession(sessionId: string) {
    const response = await apiClient.post(`${this.basePath}/sessions/${sessionId}/disconnect`);
    return response.data;
  }

  async getActiveSessions(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/sessions/active`, { params: filters });
    return response.data as PaginatedResponse<RadiusSession>;
  }

  // User management
  async getUsers(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/users`, { params: filters });
    return response.data as PaginatedResponse<RadiusUser>;
  }

  async getUser(id: number) {
    const response = await apiClient.get(`${this.basePath}/users/${id}`);
    return response.data as RadiusUser;
  }

  async createUser(data: CreateRadiusUserData) {
    const response = await apiClient.post(`${this.basePath}/users`, data);
    return response.data as RadiusUser;
  }

  async updateUser(id: number, data: UpdateRadiusUserData) {
    const response = await apiClient.put(`${this.basePath}/users/${id}`, data);
    return response.data as RadiusUser;
  }

  async deleteUser(id: number) {
    await apiClient.delete(`${this.basePath}/users/${id}`);
  }

  async activateUser(id: number) {
    const response = await apiClient.post(`${this.basePath}/users/${id}/activate`);
    return response.data as RadiusUser;
  }

  async deactivateUser(id: number) {
    const response = await apiClient.post(`${this.basePath}/users/${id}/deactivate`);
    return response.data as RadiusUser;
  }

  // Client management
  async getClients(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/clients`, { params: filters });
    return response.data as PaginatedResponse<RadiusClient>;
  }

  async getClient(id: number) {
    const response = await apiClient.get(`${this.basePath}/clients/${id}`);
    return response.data as RadiusClient;
  }

  async createClient(data: CreateRadiusClientData) {
    const response = await apiClient.post(`${this.basePath}/clients`, data);
    return response.data as RadiusClient;
  }

  async updateClient(id: number, data: UpdateRadiusClientData) {
    const response = await apiClient.put(`${this.basePath}/clients/${id}`, data);
    return response.data as RadiusClient;
  }

  async deleteClient(id: number) {
    await apiClient.delete(`${this.basePath}/clients/${id}`);
  }

  async testClient(id: number) {
    const response = await apiClient.post(`${this.basePath}/clients/${id}/test`);
    return response.data;
  }

  // Accounting
  async getAccounting(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/accounting`, { params: filters });
    return response.data as PaginatedResponse<RadiusAccounting>;
  }

  async getAccountingRecord(id: number) {
    const response = await apiClient.get(`${this.basePath}/accounting/${id}`);
    return response.data as RadiusAccounting;
  }

  // Statistics
  async getStats(timeRange = '24h') {
    const response = await apiClient.get(`${this.basePath}/stats`, {
      params: { time_range: timeRange }
    });
    return response.data as RadiusStats;
  }

  async getSessionTrends(period = 'hourly') {
    const response = await apiClient.get(`${this.basePath}/stats/trends`, {
      params: { period }
    });
    return response.data;
  }

  async getUserStats(userId: number, timeRange = '7d') {
    const response = await apiClient.get(`${this.basePath}/users/${userId}/stats`, {
      params: { time_range: timeRange }
    });
    return response.data;
  }

  async getNasStats(nasIp: string, timeRange = '7d') {
    const response = await apiClient.get(`${this.basePath}/nas/${nasIp}/stats`, {
      params: { time_range: timeRange }
    });
    return response.data;
  }

  // Authentication testing
  async testAuthentication(username: string, password: string) {
    const response = await apiClient.post(`${this.basePath}/test-auth`, {
      username,
      password
    });
    return response.data;
  }

  // Server management
  async getServerStatus() {
    const response = await apiClient.get(`${this.basePath}/server/status`);
    return response.data;
  }

  async restartServer() {
    const response = await apiClient.post(`${this.basePath}/server/restart`);
    return response.data;
  }

  async reloadConfig() {
    const response = await apiClient.post(`${this.basePath}/server/reload`);
    return response.data;
  }

  // Logs
  async getLogs(filters = {}) {
    const response = await apiClient.get(`${this.basePath}/logs`, { params: filters });
    return response.data;
  }

  async clearLogs() {
    const response = await apiClient.delete(`${this.basePath}/logs`);
    return response.data;
  }
}

export const radiusService = new RadiusService();
