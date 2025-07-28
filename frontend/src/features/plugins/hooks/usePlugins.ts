import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pluginsService } from '../services/plugins-service';
import { useToast } from '@/hooks/use-toast';
import type { PluginFilters, InstallPluginData } from '../types';

export function usePlugins(filters: PluginFilters = {}) {
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

export function useMarketplacePlugins(filters: PluginFilters = {}) {
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
    mutationFn: (data: InstallPluginData) => pluginsService.installPlugin(data),
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
    mutationFn: (id: number) => pluginsService.activatePlugin(id),
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
    mutationFn: (id: number) => pluginsService.deactivatePlugin(id),
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
    mutationFn: ({ id, configuration }: { id: number; configuration: Record<string, unknown> }) =>
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
