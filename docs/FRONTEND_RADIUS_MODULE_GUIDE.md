# ISP Framework - RADIUS Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a comprehensive modular architecture for the RADIUS module frontend, covering authentication management, session monitoring, online users tracking, and RADIUS server configuration.

## Modular Architecture

```
src/features/radius/
├── components/
│   ├── dashboard/              # RADIUS dashboard
│   ├── sessions/               # Session management
│   ├── online-users/           # Online users monitoring
│   ├── authentication/         # Auth configuration
│   ├── clients/                # RADIUS clients management
│   ├── statistics/             # RADIUS statistics
│   └── shared/                 # Shared RADIUS components
├── hooks/                      # RADIUS-specific hooks
├── services/                   # RADIUS API layer
├── types/                      # RADIUS type definitions
├── utils/                      # RADIUS utilities
└── constants/                  # RADIUS constants
```

## 1. Type Definitions

```typescript
// src/features/radius/types/index.ts
export interface RadiusSession {
  id: number;
  session_id: string;
  customer_id: number;
  customer?: Customer;
  username: string;
  nas_ip_address: string;
  nas_port: number;
  service_type: string;
  framed_ip_address?: string;
  calling_station_id?: string;
  called_station_id?: string;
  session_start: string;
  session_duration?: number;
  input_octets?: number;
  output_octets?: number;
  input_packets?: number;
  output_packets?: number;
  terminate_cause?: string;
  session_end?: string;
  is_active: boolean;
  created_at: string;
}

export interface RadiusClient {
  id: number;
  name: string;
  ip_address: string;
  secret: string;
  nas_type: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OnlineUser {
  session_id: string;
  customer_id: number;
  customer_name: string;
  username: string;
  ip_address: string;
  nas_ip: string;
  nas_port: number;
  session_start: string;
  session_duration: number;
  bytes_in: number;
  bytes_out: number;
  packets_in: number;
  packets_out: number;
  last_update: string;
}

export interface RadiusStats {
  total_sessions: number;
  active_sessions: number;
  total_users: number;
  online_users: number;
  authentication_requests: number;
  authentication_accepts: number;
  authentication_rejects: number;
  accounting_requests: number;
  success_rate: number;
  average_session_duration: number;
  total_data_transferred: number;
}

export interface AuthenticationLog {
  id: number;
  username: string;
  customer_id?: number;
  nas_ip_address: string;
  request_type: 'Access-Request' | 'Accounting-Request';
  response_type: 'Access-Accept' | 'Access-Reject' | 'Accounting-Response';
  auth_method: string;
  failure_reason?: string;
  ip_address?: string;
  mac_address?: string;
  timestamp: string;
}

export interface RadiusFilters {
  page?: number;
  per_page?: number;
  search?: string;
  customer_id?: number;
  nas_ip?: string;
  is_active?: boolean;
  session_start_from?: string;
  session_start_to?: string;
  username?: string;
}

export interface SessionFilters extends RadiusFilters {
  include_terminated?: boolean;
  min_duration?: number;
  max_duration?: number;
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
// src/features/radius/services/radius-service.ts
import { apiClient } from '@/api/client';

export class RadiusService {
  private readonly basePath = '/radius';

  // Session management
  async getSessions(filters: SessionFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/sessions`, { params: filters });
    return response.data;
  }

  async getSession(sessionId: string) {
    const response = await apiClient.get(`${this.basePath}/sessions/${sessionId}`);
    return response.data;
  }

  async terminateSession(sessionId: string, reason?: string) {
    const response = await apiClient.post(`${this.basePath}/sessions/${sessionId}/terminate`, { reason });
    return response.data;
  }

  // Online users
  async getOnlineUsers(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/online-users`, { params: filters });
    return response.data;
  }

  async disconnectUser(sessionId: string, reason?: string) {
    const response = await apiClient.post(`${this.basePath}/online-users/${sessionId}/disconnect`, { reason });
    return response.data;
  }

  // RADIUS clients
  async getClients() {
    const response = await apiClient.get(`${this.basePath}/clients`);
    return response.data;
  }

  async createClient(data: CreateRadiusClientData) {
    const response = await apiClient.post(`${this.basePath}/clients`, data);
    return response.data;
  }

  async updateClient(id: number, data: UpdateRadiusClientData) {
    const response = await apiClient.put(`${this.basePath}/clients/${id}`, data);
    return response.data;
  }

  async deleteClient(id: number) {
    await apiClient.delete(`${this.basePath}/clients/${id}`);
  }

  async testClient(id: number) {
    const response = await apiClient.post(`${this.basePath}/clients/${id}/test`);
    return response.data;
  }

  // Authentication logs
  async getAuthenticationLogs(filters: RadiusFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/auth-logs`, { params: filters });
    return response.data;
  }

  // Statistics
  async getStats(timeRange: string = '24h') {
    const response = await apiClient.get(`${this.basePath}/stats`, { 
      params: { time_range: timeRange } 
    });
    return response.data;
  }

  async getSessionChart(period: 'hourly' | 'daily' | 'weekly' = 'hourly') {
    const response = await apiClient.get(`${this.basePath}/charts/sessions`, { 
      params: { period } 
    });
    return response.data;
  }

  async getAuthenticationChart(period: 'hourly' | 'daily' | 'weekly' = 'hourly') {
    const response = await apiClient.get(`${this.basePath}/charts/authentication`, { 
      params: { period } 
    });
    return response.data;
  }

  // Customer statistics
  async getCustomerStats(customerId: number) {
    const response = await apiClient.get(`${this.basePath}/customers/${customerId}/stats`);
    return response.data;
  }

  async getCustomerSessions(customerId: number, filters: SessionFilters = {}) {
    const response = await apiClient.get(`${this.basePath}/customers/${customerId}/sessions`, { 
      params: filters 
    });
    return response.data;
  }
}

export const radiusService = new RadiusService();
```

## 3. Core Components

### 3.1 RADIUS Dashboard

```typescript
// src/features/radius/components/dashboard/RadiusDashboard.tsx
'use client';

import { useState } from 'react';
import { useRadiusStats, useOnlineUsers } from '../../hooks';
import { RadiusStatsCards } from './RadiusStatsCards';
import { OnlineUsersTable } from '../online-users/OnlineUsersTable';
import { SessionChart } from '../charts/SessionChart';
import { AuthenticationChart } from '../charts/AuthenticationChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RefreshCw, Users, Shield, Activity } from 'lucide-react';

export function RadiusDashboard() {
  const [timeRange, setTimeRange] = useState('24h');
  const [activeTab, setActiveTab] = useState('overview');
  
  const { data: stats, refetch: refetchStats } = useRadiusStats(timeRange);
  const { data: onlineUsers } = useOnlineUsers();

  const handleRefresh = () => {
    refetchStats();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">RADIUS Management</h1>
          <p className="text-muted-foreground">
            Monitor authentication, sessions, and online users
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && <RadiusStatsCards stats={stats} />}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="online-users">Online Users</TabsTrigger>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="authentication">Authentication</TabsTrigger>
          <TabsTrigger value="clients">RADIUS Clients</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SessionChart timeRange={timeRange} />
            <AuthenticationChart timeRange={timeRange} />
          </div>
          
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="mr-2 h-5 w-5" />
                Currently Online Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <OnlineUsersTable data={onlineUsers} limit={10} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="online-users">
          <OnlineUsersManagement />
        </TabsContent>

        <TabsContent value="sessions">
          <SessionManagement />
        </TabsContent>

        <TabsContent value="authentication">
          <AuthenticationManagement />
        </TabsContent>

        <TabsContent value="clients">
          <RadiusClientsManagement />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3.2 Online Users Management

```typescript
// src/features/radius/components/online-users/OnlineUsersTable.tsx
'use client';

import { useState } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  SortingState,
} from '@tanstack/react-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, UserX, Eye, Activity } from 'lucide-react';
import { useDisconnectUser } from '../../hooks';
import { formatBytes, formatDuration } from '../../utils';
import type { OnlineUser } from '../../types';

interface OnlineUsersTableProps {
  data?: OnlineUser[];
  limit?: number;
}

export function OnlineUsersTable({ data = [], limit }: OnlineUsersTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const disconnectUser = useDisconnectUser();

  const displayData = limit ? data.slice(0, limit) : data;

  const columns: ColumnDef<OnlineUser>[] = [
    {
      accessorKey: 'customer_name',
      header: 'Customer',
    },
    {
      accessorKey: 'username',
      header: 'Username',
    },
    {
      accessorKey: 'ip_address',
      header: 'IP Address',
      cell: ({ row }) => (
        <code className="bg-muted px-2 py-1 rounded text-sm">
          {row.getValue('ip_address')}
        </code>
      ),
    },
    {
      accessorKey: 'session_duration',
      header: 'Duration',
      cell: ({ row }) => {
        const duration = row.getValue('session_duration') as number;
        return formatDuration(duration);
      },
    },
    {
      accessorKey: 'bytes_in',
      header: 'Data In',
      cell: ({ row }) => {
        const bytes = row.getValue('bytes_in') as number;
        return formatBytes(bytes);
      },
    },
    {
      accessorKey: 'bytes_out',
      header: 'Data Out',
      cell: ({ row }) => {
        const bytes = row.getValue('bytes_out') as number;
        return formatBytes(bytes);
      },
    },
    {
      accessorKey: 'nas_ip',
      header: 'NAS',
      cell: ({ row }) => (
        <code className="bg-muted px-2 py-1 rounded text-sm">
          {row.getValue('nas_ip')}
        </code>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      cell: () => (
        <Badge variant="default" className="bg-green-100 text-green-800">
          <Activity className="mr-1 h-3 w-3" />
          Online
        </Badge>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const user = row.original;
        
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => disconnectUser.mutate({ 
                  sessionId: user.session_id, 
                  reason: 'Admin disconnect' 
                })}
                className="text-red-600"
              >
                <UserX className="mr-2 h-4 w-4" />
                Disconnect
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const table = useReactTable({
    data: displayData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No online users found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/radius/hooks/useRadius.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { radiusService } from '../services/radius-service';
import { useToast } from '@/hooks/use-toast';

export function useRadiusStats(timeRange = '24h') {
  return useQuery({
    queryKey: ['radius-stats', timeRange],
    queryFn: () => radiusService.getStats(timeRange),
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}

export function useOnlineUsers(filters = {}) {
  return useQuery({
    queryKey: ['online-users', filters],
    queryFn: () => radiusService.getOnlineUsers(filters),
    refetchInterval: 10 * 1000, // Refetch every 10 seconds
  });
}

export function useRadiusSessions(filters = {}) {
  return useQuery({
    queryKey: ['radius-sessions', filters],
    queryFn: () => radiusService.getSessions(filters),
    keepPreviousData: true,
  });
}

export function useRadiusClients() {
  return useQuery({
    queryKey: ['radius-clients'],
    queryFn: () => radiusService.getClients(),
  });
}

export function useAuthenticationLogs(filters = {}) {
  return useQuery({
    queryKey: ['auth-logs', filters],
    queryFn: () => radiusService.getAuthenticationLogs(filters),
    keepPreviousData: true,
  });
}

export function useDisconnectUser() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ sessionId, reason }: { sessionId: string; reason?: string }) =>
      radiusService.disconnectUser(sessionId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['online-users'] });
      queryClient.invalidateQueries({ queryKey: ['radius-sessions'] });
      toast({
        title: 'Success',
        description: 'User disconnected successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to disconnect user',
        variant: 'destructive',
      });
    },
  });
}

export function useTerminateSession() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ sessionId, reason }: { sessionId: string; reason?: string }) =>
      radiusService.terminateSession(sessionId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radius-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['online-users'] });
      toast({
        title: 'Success',
        description: 'Session terminated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to terminate session',
        variant: 'destructive',
      });
    },
  });
}

export function useCreateRadiusClient() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: radiusService.createClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radius-clients'] });
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
```

## 5. Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- Set up RADIUS module structure
- Implement types and service layer
- Create basic hooks and utilities

### Phase 2: Session Management (Days 3-4)
- Build session monitoring interface
- Implement session termination functionality
- Create session history and analytics

### Phase 3: Online Users (Days 5-6)
- Build real-time online users dashboard
- Implement user disconnection functionality
- Create user activity monitoring

### Phase 4: Authentication Management (Days 7-8)
- Build authentication logs interface
- Implement RADIUS client management
- Create authentication analytics

### Phase 5: Advanced Features (Days 9-10)
- Build comprehensive reporting
- Implement real-time alerts
- Create customer-specific RADIUS analytics

This modular architecture provides comprehensive RADIUS management capabilities with real-time monitoring, session control, and detailed analytics for ISP authentication infrastructure.
