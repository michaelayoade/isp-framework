// Plugins module type definitions
export interface Plugin {
  id: number;
  name: string;
  slug: string;
  version: string;
  description: string;
  author: string;
  author_email?: string;
  homepage?: string;
  repository?: string;
  license: string;
  category: PluginCategory;
  tags: string[];
  icon?: string;
  screenshots: string[];
  is_active: boolean;
  is_installed: boolean;
  installation_status: InstallationStatus;
  configuration: Record<string, unknown>;
  dependencies: PluginDependency[];
  hooks: PluginHook[];
  api_endpoints: PluginEndpoint[];
  permissions: string[];
  min_framework_version: string;
  max_framework_version?: string;
  install_size: number;
  download_count: number;
  rating: number;
  review_count: number;
  last_updated: string;
  created_at: string;
}

export type PluginCategory = 
  | 'billing' 
  | 'communications' 
  | 'networking' 
  | 'monitoring' 
  | 'reporting' 
  | 'integration' 
  | 'utility' 
  | 'security';

export type InstallationStatus = 
  | 'not_installed' 
  | 'downloading' 
  | 'installing' 
  | 'installed' 
  | 'updating' 
  | 'uninstalling' 
  | 'failed';

export interface PluginDependency {
  name: string;
  version: string;
  type: 'plugin' | 'system' | 'python';
  is_satisfied: boolean;
}

export interface PluginHook {
  name: string;
  description: string;
  parameters: PluginHookParameter[];
  return_type?: string;
}

export interface PluginHookParameter {
  name: string;
  type: string;
  required: boolean;
  description?: string;
}

export interface PluginEndpoint {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  description: string;
  authentication_required: boolean;
  permissions: string[];
}

export interface PluginConfiguration {
  plugin_id: number;
  settings: Record<string, unknown>;
  is_enabled: boolean;
  environment_variables: Record<string, string>;
  webhook_urls: string[];
  api_keys: Record<string, string>;
  updated_at: string;
}

export interface PluginStats {
  total_plugins: number;
  installed_plugins: number;
  active_plugins: number;
  available_updates: number;
  marketplace_plugins: number;
  categories: Record<PluginCategory, number>;
  installation_health: number;
}

export interface PluginFilters {
  page?: number;
  per_page?: number;
  search?: string;
  category?: PluginCategory;
  is_installed?: boolean;
  is_active?: boolean;
  author?: string;
  tags?: string[];
  min_rating?: number;
}

export interface InstallPluginData {
  plugin_id?: number;
  plugin_url?: string;
  plugin_file?: File;
  auto_activate?: boolean;
  configuration?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
