import { apiClient } from '@/api/client';
import type {
  Plugin,
  PluginConfiguration,
  PluginStats,
  PluginFilters,
  InstallPluginData,
  PaginatedResponse,
} from '../types';

export class PluginsService {
  private readonly basePath = '/plugins';

  // Plugin management
  async getPlugins(filters: PluginFilters = {}) {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data as PaginatedResponse<Plugin>;
  }

  async getPlugin(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data as Plugin;
  }

  async installPlugin(data: InstallPluginData) {
    const formData = new FormData();
    
    if (data.plugin_file) {
      formData.append('plugin_file', data.plugin_file);
    } else if (data.plugin_url) {
      formData.append('plugin_url', data.plugin_url);
    } else if (data.plugin_id) {
      formData.append('plugin_id', data.plugin_id.toString());
    }

    if (data.auto_activate !== undefined) {
      formData.append('auto_activate', data.auto_activate.toString());
    }

    if (data.configuration) {
      formData.append('configuration', JSON.stringify(data.configuration));
    }

    const response = await apiClient.post(`${this.basePath}/install`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as Plugin;
  }

  async uninstallPlugin(id: number, removeData = false) {
    const response = await apiClient.delete(`${this.basePath}/${id}`, {
      data: { remove_data: removeData }
    });
    return response.data;
  }

  async activatePlugin(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/activate`);
    return response.data as Plugin;
  }

  async deactivatePlugin(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/deactivate`);
    return response.data as Plugin;
  }

  async updatePlugin(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/update`);
    return response.data as Plugin;
  }

  // Plugin configuration
  async getPluginConfiguration(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}/configuration`);
    return response.data as PluginConfiguration;
  }

  async updatePluginConfiguration(id: number, configuration: Record<string, unknown>) {
    const response = await apiClient.put(`${this.basePath}/${id}/configuration`, {
      settings: configuration
    });
    return response.data as PluginConfiguration;
  }

  async resetPluginConfiguration(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/configuration/reset`);
    return response.data as PluginConfiguration;
  }

  // Plugin logs
  async getPluginLogs(id: number, filters = {}) {
    const response = await apiClient.get(`${this.basePath}/${id}/logs`, { params: filters });
    return response.data;
  }

  async clearPluginLogs(id: number) {
    const response = await apiClient.delete(`${this.basePath}/${id}/logs`);
    return response.data;
  }

  // Marketplace
  async getMarketplacePlugins(filters: PluginFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/marketplace`, { params: filters });
    return response.data as PaginatedResponse<Plugin>;
  }

  async getMarketplacePlugin(slug: string) {
    const response = await apiClient.get(`${this.basePath}/marketplace/${slug}`);
    return response.data as Plugin;
  }

  async searchMarketplace(query: string, filters = {}) {
    const response = await apiClient.get(`${this.basePath}/marketplace/search`, {
      params: { q: query, ...filters }
    });
    return response.data as PaginatedResponse<Plugin>;
  }

  // Plugin development
  async validatePlugin(pluginFile: File) {
    const formData = new FormData();
    formData.append('plugin_file', pluginFile);

    const response = await apiClient.post(`${this.basePath}/validate`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async getPluginTemplate(type: string) {
    const response = await apiClient.get(`${this.basePath}/templates/${type}`);
    return response.data;
  }

  // Statistics
  async getPluginStats() {
    const response = await apiClient.get(`${this.basePath}/stats`);
    return response.data as PluginStats;
  }

  async getInstallationStatus(installationId: string) {
    const response = await apiClient.get(`${this.basePath}/installations/${installationId}/status`);
    return response.data;
  }

  // Plugin health
  async checkPluginHealth(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}/health`);
    return response.data;
  }

  async runPluginDiagnostics(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/diagnostics`);
    return response.data;
  }
}

export const pluginsService = new PluginsService();
