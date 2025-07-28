# ISP Framework - Networking & IPAM Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a comprehensive modular architecture for the networking and IP Address Management (IPAM) module frontend, covering network topology, device management, IP allocation, and infrastructure monitoring.

## Modular Architecture

```
src/features/networking/
├── components/
│   ├── dashboard/              # Networking dashboard
│   ├── topology/               # Network topology visualization
│   ├── devices/                # Device management
│   ├── ip-management/          # IP address management
│   ├── monitoring/             # Network monitoring
│   ├── sites/                  # Site management
│   └── shared/                 # Shared networking components
├── hooks/                      # Networking-specific hooks
├── services/                   # Networking API layer
├── types/                      # Networking type definitions
├── utils/                      # Networking utilities
└── constants/                  # Networking constants
```

## 1. Type Definitions

```typescript
// src/features/networking/types/index.ts
export interface NetworkSite {
  id: number;
  name: string;
  description?: string;
  location_id: number;
  location?: Location;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: number;
  name: string;
  address: string;
  city: string;
  state: string;
  country: string;
  latitude?: number;
  longitude?: number;
}

export interface IPv4Network {
  id: number;
  network_address: string;
  subnet_mask: number;
  gateway: string;
  dns_primary?: string;
  dns_secondary?: string;
  site_id: number;
  site?: NetworkSite;
  vlan_id?: number;
  is_active: boolean;
  description?: string;
  created_at: string;
}

export interface IPv4Address {
  id: number;
  ip_address: string;
  network_id: number;
  network?: IPv4Network;
  status: IPStatus;
  assignment_type: 'static' | 'dynamic' | 'reserved';
  assigned_to?: string;
  customer_id?: number;
  service_id?: number;
  mac_address?: string;
  hostname?: string;
  last_seen?: string;
  created_at: string;
}

export type IPStatus = 'available' | 'assigned' | 'reserved' | 'blocked';

export interface NetworkDevice {
  id: number;
  name: string;
  device_type: DeviceType;
  ip_address: string;
  mac_address?: string;
  site_id: number;
  site?: NetworkSite;
  status: DeviceStatus;
  parent_device_id?: number;
  parent_device?: NetworkDevice;
  children?: NetworkDevice[];
  monitoring_enabled: boolean;
  last_contact?: string;
  uptime?: number;
  cpu_usage?: number;
  memory_usage?: number;
  created_at: string;
}

export type DeviceType = 'router' | 'switch' | 'access_point' | 'firewall' | 'server' | 'other';
export type DeviceStatus = 'online' | 'offline' | 'maintenance' | 'error';

export interface RouterSector {
  id: number;
  name: string;
  router_id: number;
  router?: NetworkDevice;
  frequency: string;
  channel_width: string;
  max_clients: number;
  current_clients: number;
  signal_strength: number;
  is_active: boolean;
}

export interface NetworkStats {
  total_networks: number;
  total_ips: number;
  assigned_ips: number;
  available_ips: number;
  utilization_percentage: number;
  active_devices: number;
  offline_devices: number;
  device_health_score: number;
}

export interface NetworkFilters {
  page?: number;
  per_page?: number;
  search?: string;
  site_id?: number;
  status?: IPStatus | DeviceStatus;
  device_type?: DeviceType;
  assignment_type?: string;
  network_id?: number;
}
```

## 2. Service Layer

```typescript
// src/features/networking/services/networking-service.ts
import { apiClient } from '@/api/client';

export class NetworkingService {
  private readonly basePath = '/networking';

  // Network management
  async getNetworks(filters = {}) {
    const response = await apiClient.get(`${this.basePath}/networks`, { params: filters });
    return response.data;
  }

  async createNetwork(data) {
    const response = await apiClient.post(`${this.basePath}/networks`, data);
    return response.data;
  }

  // IP address management
  async getIPAddresses(filters = {}) {
    const response = await apiClient.get(`${this.basePath}/ip-addresses`, { params: filters });
    return response.data;
  }

  async assignIPAddress(ipId, assignmentData) {
    const response = await apiClient.post(`${this.basePath}/ip-addresses/${ipId}/assign`, assignmentData);
    return response.data;
  }

  async releaseIPAddress(ipId) {
    const response = await apiClient.post(`${this.basePath}/ip-addresses/${ipId}/release`);
    return response.data;
  }

  // Device management
  async getDevices(filters = {}) {
    const response = await apiClient.get(`${this.basePath}/devices`, { params: filters });
    return response.data;
  }

  async getDeviceDetails(deviceId) {
    const response = await apiClient.get(`${this.basePath}/devices/${deviceId}`);
    return response.data;
  }

  async updateDeviceStatus(deviceId, status) {
    const response = await apiClient.put(`${this.basePath}/devices/${deviceId}/status`, { status });
    return response.data;
  }

  // Site management
  async getSites() {
    const response = await apiClient.get(`${this.basePath}/sites`);
    return response.data;
  }

  async createSite(data) {
    const response = await apiClient.post(`${this.basePath}/sites`, data);
    return response.data;
  }

  // Network topology
  async getTopology(siteId) {
    const response = await apiClient.get(`${this.basePath}/topology`, { 
      params: siteId ? { site_id: siteId } : {} 
    });
    return response.data;
  }

  // Monitoring
  async getNetworkStats() {
    const response = await apiClient.get(`${this.basePath}/stats`);
    return response.data;
  }

  async getDeviceMetrics(deviceId, timeRange = '1h') {
    const response = await apiClient.get(`${this.basePath}/devices/${deviceId}/metrics`, {
      params: { time_range: timeRange }
    });
    return response.data;
  }
}

export const networkingService = new NetworkingService();
```

## 3. Core Components

### 3.1 Networking Dashboard

```typescript
// src/features/networking/components/dashboard/NetworkingDashboard.tsx
'use client';

import { useState } from 'react';
import { useNetworkStats, useDevices } from '../../hooks';
import { NetworkStatsCards } from './NetworkStatsCards';
import { NetworkTopology } from '../topology/NetworkTopology';
import { DeviceStatusOverview } from '../devices/DeviceStatusOverview';
import { IPUtilizationChart } from '../charts/IPUtilizationChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Plus, Globe, Router, Activity } from 'lucide-react';

export function NetworkingDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const { data: networkStats } = useNetworkStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Networking & IPAM</h1>
          <p className="text-muted-foreground">
            Manage IP addresses, network devices, and infrastructure
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            Monitoring
          </Button>
          <Button variant="outline">
            <Globe className="mr-2 h-4 w-4" />
            Network Map
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Network
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {networkStats && <NetworkStatsCards stats={networkStats} />}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="networks">Networks</TabsTrigger>
          <TabsTrigger value="devices">Devices</TabsTrigger>
          <TabsTrigger value="ip-management">IP Management</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <NetworkTopology />
            <div className="space-y-6">
              <DeviceStatusOverview />
              <IPUtilizationChart />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="networks">
          <NetworkManagement />
        </TabsContent>

        <TabsContent value="devices">
          <DeviceManagement />
        </TabsContent>

        <TabsContent value="ip-management">
          <IPAddressManagement />
        </TabsContent>

        <TabsContent value="monitoring">
          <NetworkMonitoring />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3.2 Network Topology Visualization

```typescript
// src/features/networking/components/topology/NetworkTopology.tsx
'use client';

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNetworkTopology } from '../../hooks';

export function NetworkTopology() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { data: topology, isLoading } = useNetworkTopology();

  useEffect(() => {
    if (!topology || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw network topology
    drawNetworkNodes(ctx, topology.nodes);
    drawNetworkConnections(ctx, topology.connections);
  }, [topology]);

  const drawNetworkNodes = (ctx: CanvasRenderingContext2D, nodes: any[]) => {
    nodes.forEach(node => {
      const { x, y, type, status } = node;
      
      // Set color based on device type and status
      ctx.fillStyle = getNodeColor(type, status);
      ctx.beginPath();
      ctx.arc(x, y, 15, 0, 2 * Math.PI);
      ctx.fill();
      
      // Draw device icon/label
      ctx.fillStyle = '#fff';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(getDeviceIcon(type), x, y + 4);
    });
  };

  const drawNetworkConnections = (ctx: CanvasRenderingContext2D, connections: any[]) => {
    connections.forEach(conn => {
      const { from, to, status } = conn;
      
      ctx.strokeStyle = status === 'active' ? '#22c55e' : '#ef4444';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    });
  };

  const getNodeColor = (type: string, status: string) => {
    if (status === 'offline') return '#ef4444';
    switch (type) {
      case 'router': return '#3b82f6';
      case 'switch': return '#10b981';
      case 'access_point': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'router': return '🔀';
      case 'switch': return '🔗';
      case 'access_point': return '📡';
      case 'firewall': return '🛡️';
      default: return '📱';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Network Topology</CardTitle>
          <Select defaultValue="all">
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select site" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sites</SelectItem>
              <SelectItem value="site1">Main Office</SelectItem>
              <SelectItem value="site2">Branch Office</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            width={600}
            height={400}
            className="border rounded-md w-full max-w-full"
          />
        )}
      </CardContent>
    </Card>
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/networking/hooks/useNetworking.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { networkingService } from '../services/networking-service';
import { useToast } from '@/hooks/use-toast';

export function useNetworkStats() {
  return useQuery({
    queryKey: ['network-stats'],
    queryFn: () => networkingService.getNetworkStats(),
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}

export function useNetworks(filters = {}) {
  return useQuery({
    queryKey: ['networks', filters],
    queryFn: () => networkingService.getNetworks(filters),
    keepPreviousData: true,
  });
}

export function useDevices(filters = {}) {
  return useQuery({
    queryKey: ['network-devices', filters],
    queryFn: () => networkingService.getDevices(filters),
    keepPreviousData: true,
  });
}

export function useIPAddresses(filters = {}) {
  return useQuery({
    queryKey: ['ip-addresses', filters],
    queryFn: () => networkingService.getIPAddresses(filters),
    keepPreviousData: true,
  });
}

export function useNetworkTopology(siteId) {
  return useQuery({
    queryKey: ['network-topology', siteId],
    queryFn: () => networkingService.getTopology(siteId),
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

export function useAssignIPAddress() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ ipId, assignmentData }) => 
      networkingService.assignIPAddress(ipId, assignmentData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ip-addresses'] });
      toast({
        title: 'Success',
        description: 'IP address assigned successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to assign IP address',
        variant: 'destructive',
      });
    },
  });
}

export function useDeviceMetrics(deviceId, timeRange = '1h') {
  return useQuery({
    queryKey: ['device-metrics', deviceId, timeRange],
    queryFn: () => networkingService.getDeviceMetrics(deviceId, timeRange),
    enabled: !!deviceId,
    refetchInterval: 30 * 1000,
  });
}
```

## 5. Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- Set up networking module structure
- Implement types and service layer
- Create basic hooks and utilities

### Phase 2: Network Management (Days 3-4)
- Build network and subnet management
- Implement site management
- Create network creation/editing forms

### Phase 3: IP Address Management (Days 5-6)
- Build IP address allocation interface
- Implement IP assignment/release functionality
- Create IP utilization tracking

### Phase 4: Device Management (Days 7-8)
- Implement device discovery and management
- Build device monitoring dashboard
- Create device configuration interface

### Phase 5: Topology & Monitoring (Days 9-10)
- Build network topology visualization
- Implement real-time monitoring
- Create alerting and notification system

This modular architecture provides comprehensive network and IP address management capabilities while maintaining flexibility for future networking features and integrations.
