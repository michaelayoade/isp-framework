# ISP Framework - Plugins Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a comprehensive modular architecture for the plugins module frontend, covering plugin management, installation, configuration, and marketplace integration for extending ISP Framework functionality.

## Modular Architecture

```
src/features/plugins/
├── components/
│   ├── dashboard/              # Plugins dashboard
│   ├── marketplace/            # Plugin marketplace
│   ├── installed/              # Installed plugins management
│   ├── configuration/          # Plugin configuration
│   ├── development/            # Plugin development tools
│   └── shared/                 # Shared plugin components
├── hooks/                      # Plugins-specific hooks
├── services/                   # Plugins API layer
├── types/                      # Plugins type definitions
├── utils/                      # Plugins utilities
└── constants/                  # Plugins constants
```

## 1. Type Definitions

```typescript
// src/features/plugins/types/index.ts
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
  configuration: Record<string, any>;
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
  settings: Record<string, any>;
  is_enabled: boolean;
  environment_variables: Record<string, string>;
  webhook_urls: string[];
  api_keys: Record<string, string>;
  updated_at: string;
}

export interface PluginLog {
  id: number;
  plugin_id: number;
  plugin?: Plugin;
  level: LogLevel;
  message: string;
  context: Record<string, any>;
  stack_trace?: string;
  timestamp: string;
}

export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

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
  configuration?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
```

## 2. Service Layer

```typescript
// src/features/plugins/services/plugins-service.ts
import { apiClient } from '@/api/client';

export class PluginsService {
  private readonly basePath = '/plugins';

  // Plugin management
  async getPlugins(filters: PluginFilters = {}) {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data;
  }

  async getPlugin(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data;
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
    return response.data;
  }

  async uninstallPlugin(id: number, removeData = false) {
    const response = await apiClient.delete(`${this.basePath}/${id}`, {
      data: { remove_data: removeData }
    });
    return response.data;
  }

  async activatePlugin(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/activate`);
    return response.data;
  }

  async deactivatePlugin(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/deactivate`);
    return response.data;
  }

  async updatePlugin(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/update`);
    return response.data;
  }

  // Plugin configuration
  async getPluginConfiguration(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}/configuration`);
    return response.data;
  }

  async updatePluginConfiguration(id: number, configuration: Record<string, any>) {
    const response = await apiClient.put(`${this.basePath}/${id}/configuration`, {
      settings: configuration
    });
    return response.data;
  }

  async resetPluginConfiguration(id: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/configuration/reset`);
    return response.data;
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
    return response.data;
  }

  async getMarketplacePlugin(slug: string) {
    const response = await apiClient.get(`${this.basePath}/marketplace/${slug}`);
    return response.data;
  }

  async searchMarketplace(query: string, filters = {}) {
    const response = await apiClient.get(`${this.basePath}/marketplace/search`, {
      params: { q: query, ...filters }
    });
    return response.data;
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
    return response.data;
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
```

## 3. Core Components

### 3.1 Plugins Dashboard

```typescript
// src/features/plugins/components/dashboard/PluginsDashboard.tsx
'use client';

import { useState } from 'react';
import { usePlugins, usePluginStats } from '../../hooks';
import { PluginStatsCards } from './PluginStatsCards';
import { InstalledPlugins } from '../installed/InstalledPlugins';
import { PluginMarketplace } from '../marketplace/PluginMarketplace';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Store, Settings, Code, RefreshCw } from 'lucide-react';

export function PluginsDashboard() {
  const [activeTab, setActiveTab] = useState('installed');
  
  const { data: stats, refetch: refetchStats } = usePluginStats();
  const { data: installedPlugins } = usePlugins({ is_installed: true });

  const handleRefresh = () => {
    refetchStats();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Plugins</h1>
          <p className="text-muted-foreground">
            Extend your ISP Framework with plugins and integrations
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline">
            <Code className="mr-2 h-4 w-4" />
            Developer Tools
          </Button>
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Plugin Settings
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Install Plugin
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && <PluginStatsCards stats={stats} />}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="installed" className="flex items-center">
            Installed Plugins
            {installedPlugins && (
              <Badge variant="secondary" className="ml-2">
                {installedPlugins.total}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="marketplace" className="flex items-center">
            <Store className="mr-2 h-4 w-4" />
            Marketplace
          </TabsTrigger>
          <TabsTrigger value="development">Development</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="installed">
          <InstalledPlugins />
        </TabsContent>

        <TabsContent value="marketplace">
          <PluginMarketplace />
        </TabsContent>

        <TabsContent value="development">
          <PluginDevelopment />
        </TabsContent>

        <TabsContent value="settings">
          <PluginSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3.2 Plugin Card Component

```typescript
// src/features/plugins/components/shared/PluginCard.tsx
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import { 
  MoreHorizontal, 
  Download, 
  Settings, 
  Trash2, 
  Play, 
  Pause, 
  Star,
  ExternalLink,
  Shield,
  AlertTriangle
} from 'lucide-react';
import { useInstallPlugin, useUninstallPlugin, useActivatePlugin, useDeactivatePlugin } from '../../hooks';
import type { Plugin } from '../../types';

interface PluginCardProps {
  plugin: Plugin;
  showInstallButton?: boolean;
  showMarketplaceInfo?: boolean;
}

export function PluginCard({ plugin, showInstallButton = false, showMarketplaceInfo = false }: PluginCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const installPlugin = useInstallPlugin();
  const uninstallPlugin = useUninstallPlugin();
  const activatePlugin = useActivatePlugin();
  const deactivatePlugin = useDeactivatePlugin();

  const handleInstall = () => {
    installPlugin.mutate({ plugin_id: plugin.id, auto_activate: true });
  };

  const handleUninstall = () => {
    uninstallPlugin.mutate({ id: plugin.id, removeData: false });
  };

  const handleToggleActive = () => {
    if (plugin.is_active) {
      deactivatePlugin.mutate(plugin.id);
    } else {
      activatePlugin.mutate(plugin.id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'installed': return 'default';
      case 'installing': return 'secondary';
      case 'updating': return 'secondary';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      billing: 'bg-blue-100 text-blue-800',
      communications: 'bg-green-100 text-green-800',
      networking: 'bg-purple-100 text-purple-800',
      monitoring: 'bg-orange-100 text-orange-800',
      reporting: 'bg-yellow-100 text-yellow-800',
      integration: 'bg-pink-100 text-pink-800',
      utility: 'bg-gray-100 text-gray-800',
      security: 'bg-red-100 text-red-800',
    };
    return colors[category] || colors.utility;
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={plugin.icon} alt={plugin.name} />
              <AvatarFallback>
                {plugin.name.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-lg">{plugin.name}</CardTitle>
              <p className="text-sm text-muted-foreground">
                v{plugin.version} by {plugin.author}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {plugin.is_installed && (
              <Badge variant={plugin.is_active ? 'default' : 'secondary'}>
                {plugin.is_active ? 'Active' : 'Inactive'}
              </Badge>
            )}
            <Badge variant={getStatusColor(plugin.installation_status)}>
              {plugin.installation_status.replace('_', ' ')}
            </Badge>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {plugin.is_installed ? (
                  <>
                    <DropdownMenuItem onClick={handleToggleActive}>
                      {plugin.is_active ? (
                        <>
                          <Pause className="mr-2 h-4 w-4" />
                          Deactivate
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-4 w-4" />
                          Activate
                        </>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Settings className="mr-2 h-4 w-4" />
                      Configure
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleUninstall} className="text-red-600">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Uninstall
                    </DropdownMenuItem>
                  </>
                ) : (
                  <DropdownMenuItem onClick={handleInstall}>
                    <Download className="mr-2 h-4 w-4" />
                    Install
                  </DropdownMenuItem>
                )}
                {plugin.homepage && (
                  <DropdownMenuItem>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Visit Homepage
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Description */}
        <p className="text-sm text-muted-foreground line-clamp-2">
          {plugin.description}
        </p>

        {/* Category and Tags */}
        <div className="flex flex-wrap gap-2">
          <Badge className={getCategoryColor(plugin.category)}>
            {plugin.category}
          </Badge>
          {plugin.tags.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
          {plugin.tags.length > 2 && (
            <Badge variant="outline" className="text-xs">
              +{plugin.tags.length - 2} more
            </Badge>
          )}
        </div>

        {/* Marketplace Info */}
        {showMarketplaceInfo && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <Star className="mr-1 h-3 w-3 fill-current text-yellow-500" />
                {plugin.rating.toFixed(1)} ({plugin.review_count})
              </span>
              <span>{plugin.download_count.toLocaleString()} downloads</span>
            </div>
            <span>{new Date(plugin.last_updated).toLocaleDateString()}</span>
          </div>
        )}

        {/* Installation Progress */}
        {(plugin.installation_status === 'installing' || 
          plugin.installation_status === 'updating' ||
          plugin.installation_status === 'downloading') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="capitalize">{plugin.installation_status}...</span>
              <span>45%</span>
            </div>
            <Progress value={45} className="h-2" />
          </div>
        )}

        {/* Dependencies Warning */}
        {plugin.dependencies.some(dep => !dep.is_satisfied) && (
          <div className="flex items-center space-x-2 p-2 bg-yellow-50 rounded-md">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              Missing dependencies
            </span>
          </div>
        )}

        {/* Permissions */}
        {plugin.permissions.length > 0 && (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <Shield className="h-3 w-3" />
            <span>Requires {plugin.permissions.length} permissions</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-2 pt-2">
          {showInstallButton && !plugin.is_installed && (
            <Button 
              onClick={handleInstall} 
              disabled={installPlugin.isPending}
              className="flex-1"
            >
              <Download className="mr-2 h-4 w-4" />
              Install
            </Button>
          )}
          
          {plugin.is_installed && (
            <Button
              variant="outline"
              onClick={handleToggleActive}
              disabled={activatePlugin.isPending || deactivatePlugin.isPending}
              className="flex-1"
            >
              {plugin.is_active ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Deactivate
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Activate
                </>
              )}
            </Button>
          )}
          
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/plugins/hooks/usePlugins.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pluginsService } from '../services/plugins-service';
import { useToast } from '@/hooks/use-toast';

export function usePlugins(filters = {}) {
  return useQuery({
    queryKey: ['plugins', filters],
    queryFn: () => pluginsService.getPlugins(filters),
    keepPreviousData: true,
  });
}

export function usePlugin(id: number) {
  return useQuery({
    queryKey: ['plugins', id],
    queryFn: () => pluginsService.getPlugin(id),
    enabled: !!id,
  });
}

export function usePluginStats() {
  return useQuery({
    queryKey: ['plugin-stats'],
    queryFn: () => pluginsService.getPluginStats(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export function useMarketplacePlugins(filters = {}) {
  return useQuery({
    queryKey: ['marketplace-plugins', filters],
    queryFn: () => pluginsService.getMarketplacePlugins(filters),
    keepPreviousData: true,
  });
}

export function useInstallPlugin() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: pluginsService.installPlugin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugin-stats'] });
      toast({
        title: 'Success',
        description: 'Plugin installation started',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to install plugin',
        variant: 'destructive',
      });
    },
  });
}

export function useUninstallPlugin() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, removeData }: { id: number; removeData?: boolean }) =>
      pluginsService.uninstallPlugin(id, removeData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugin-stats'] });
      toast({
        title: 'Success',
        description: 'Plugin uninstalled successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to uninstall plugin',
        variant: 'destructive',
      });
    },
  });
}

export function useActivatePlugin() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: pluginsService.activatePlugin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      toast({
        title: 'Success',
        description: 'Plugin activated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to activate plugin',
        variant: 'destructive',
      });
    },
  });
}

export function useDeactivatePlugin() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: pluginsService.deactivatePlugin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      toast({
        title: 'Success',
        description: 'Plugin deactivated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to deactivate plugin',
        variant: 'destructive',
      });
    },
  });
}

export function usePluginConfiguration(id: number) {
  return useQuery({
    queryKey: ['plugin-configuration', id],
    queryFn: () => pluginsService.getPluginConfiguration(id),
    enabled: !!id,
  });
}

export function useUpdatePluginConfiguration() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, configuration }: { id: number; configuration: Record<string, any> }) =>
      pluginsService.updatePluginConfiguration(id, configuration),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['plugin-configuration', id] });
      toast({
        title: 'Success',
        description: 'Plugin configuration updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update plugin configuration',
        variant: 'destructive',
      });
    },
  });
}
```

## 5. Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- Set up plugins module structure
- Implement types and service layer
- Create basic hooks and utilities

### Phase 2: Plugin Management (Days 3-4)
- Build installed plugins dashboard
- Implement plugin activation/deactivation
- Create plugin configuration interface

### Phase 3: Plugin Marketplace (Days 5-6)
- Build marketplace browsing interface
- Implement plugin installation workflow
- Create plugin search and filtering

### Phase 4: Plugin Development Tools (Days 7-8)
- Build plugin validation tools
- Implement plugin templates
- Create development documentation

### Phase 5: Advanced Features (Days 9-10)
- Build plugin analytics and monitoring
- Implement plugin health checks
- Create plugin update management

This modular architecture provides comprehensive plugin management capabilities with marketplace integration, development tools, and robust configuration management for extending ISP Framework functionality.
