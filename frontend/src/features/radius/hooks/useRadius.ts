import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { radiusService } from '../services/radius-service';
import { useToast } from '@/hooks/use-toast';
import type { 
  RadiusFilters, 
  CreateRadiusUserData, 
  UpdateRadiusUserData,
  CreateRadiusClientData,
  UpdateRadiusClientData 
} from '../types';

export function useRadiusSessions(filters: RadiusFilters = {}) {
  return useQuery({
    queryKey: ['radius', 'sessions', filters],
    queryFn: () => radiusService.getSessions(filters),
    keepPreviousData: true,
  });
}

export function useRadiusSession(id: number) {
  return useQuery({
    queryKey: ['radius', 'sessions', id],
    queryFn: () => radiusService.getSession(id),
    enabled: !!id,
  });
}

export function useActiveSessions(filters: RadiusFilters = {}) {
  return useQuery({
    queryKey: ['radius', 'sessions', 'active', filters],
    queryFn: () => radiusService.getActiveSessions(filters),
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    keepPreviousData: true,
  });
}

export function useDisconnectSession() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (sessionId: string) => radiusService.disconnectSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radius', 'sessions'] });
      toast({
        title: 'Success',
        description: 'Session disconnected successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to disconnect session',
        variant: 'destructive',
      });
    },
  });
}

export function useRadiusUsers(filters: RadiusFilters = {}) {
  return useQuery({
    queryKey: ['radius', 'users', filters],
    queryFn: () => radiusService.getUsers(filters),
    keepPreviousData: true,
  });
}

export function useRadiusUser(id: number) {
  return useQuery({
    queryKey: ['radius', 'users', id],
    queryFn: () => radiusService.getUser(id),
    enabled: !!id,
  });
}

export function useCreateRadiusUser() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateRadiusUserData) => radiusService.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radius', 'users'] });
      toast({
        title: 'Success',
        description: 'RADIUS user created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create RADIUS user',
        variant: 'destructive',
      });
    },
  });
}

export function useUpdateRadiusUser() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateRadiusUserData }) =>
      radiusService.updateUser(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['radius', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['radius', 'users', id] });
      toast({
        title: 'Success',
        description: 'RADIUS user updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update RADIUS user',
        variant: 'destructive',
      });
    },
  });
}

export function useDeleteRadiusUser() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => radiusService.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radius', 'users'] });
      toast({
        title: 'Success',
        description: 'RADIUS user deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete RADIUS user',
        variant: 'destructive',
      });
    },
  });
}

export function useRadiusClients(filters: RadiusFilters = {}) {
  return useQuery({
    queryKey: ['radius', 'clients', filters],
    queryFn: () => radiusService.getClients(filters),
    keepPreviousData: true,
  });
}

export function useRadiusClient(id: number) {
  return useQuery({
    queryKey: ['radius', 'clients', id],
    queryFn: () => radiusService.getClient(id),
    enabled: !!id,
  });
}

export function useCreateRadiusClient() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateRadiusClientData) => radiusService.createClient(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radius', 'clients'] });
      toast({
        title: 'Success',
        description: 'RADIUS client created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create RADIUS client',
        variant: 'destructive',
      });
    },
  });
}

export function useUpdateRadiusClient() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateRadiusClientData }) =>
      radiusService.updateClient(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['radius', 'clients'] });
      queryClient.invalidateQueries({ queryKey: ['radius', 'clients', id] });
      toast({
        title: 'Success',
        description: 'RADIUS client updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update RADIUS client',
        variant: 'destructive',
      });
    },
  });
}

export function useRadiusStats(timeRange = '24h') {
  return useQuery({
    queryKey: ['radius', 'stats', timeRange],
    queryFn: () => radiusService.getStats(timeRange),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export function useRadiusAccounting(filters: RadiusFilters = {}) {
  return useQuery({
    queryKey: ['radius', 'accounting', filters],
    queryFn: () => radiusService.getAccounting(filters),
    keepPreviousData: true,
  });
}

export function useTestAuthentication() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      radiusService.testAuthentication(username, password),
    onSuccess: (data) => {
      toast({
        title: data.success ? 'Success' : 'Failed',
        description: data.message || 'Authentication test completed',
        variant: data.success ? 'default' : 'destructive',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to test authentication',
        variant: 'destructive',
      });
    },
  });
}

export function useRadiusServerStatus() {
  return useQuery({
    queryKey: ['radius', 'server', 'status'],
    queryFn: () => radiusService.getServerStatus(),
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}
