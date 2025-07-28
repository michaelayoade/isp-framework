// Networking/IPAM module type definitions
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

export interface Router {
  id: number;
  name: string;
  model: string;
  ip_address: string;
  management_ip: string;
  site_id: number;
  site?: NetworkSite;
  status: DeviceStatus;
  firmware_version?: string;
  last_contact?: string;
  uptime?: number;
  cpu_usage?: number;
  memory_usage?: number;
  created_at: string;
}

export type DeviceStatus = 'online' | 'offline' | 'maintenance' | 'error';

export interface RouterSector {
  id: number;
  name: string;
  router_id: number;
  router?: Router;
  frequency: string;
  channel_width: string;
  max_clients: number;
  current_clients: number;
  signal_strength: number;
  is_active: boolean;
}

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
  created_at: string;
}

export type DeviceType = 'router' | 'switch' | 'access_point' | 'firewall' | 'server' | 'other';

export interface NetworkFilters {
  page?: number;
  per_page?: number;
  search?: string;
  site_id?: number;
  status?: IPStatus | DeviceStatus;
  device_type?: DeviceType;
  assignment_type?: string;
}

export interface NetworkStats {
  total_networks: number;
  total_ips: number;
  assigned_ips: number;
  available_ips: number;
  utilization_percentage: number;
  active_devices: number;
  offline_devices: number;
}

// Re-export from common types to maintain backward compatibility
export type { PaginatedResponse } from '@/types/common';
