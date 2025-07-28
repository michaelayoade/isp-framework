// RADIUS module type definitions
export interface RadiusSession {
  id: number;
  session_id: string;
  username: string;
  customer_id: number;
  customer?: Customer;
  nas_ip_address: string;
  nas_port: number;
  nas_port_type: string;
  service_type: string;
  framed_ip_address?: string;
  framed_netmask?: string;
  calling_station_id?: string;
  called_station_id?: string;
  session_time: number;
  input_octets: number;
  output_octets: number;
  input_packets: number;
  output_packets: number;
  terminate_cause?: string;
  start_time: string;
  stop_time?: string;
  last_update: string;
  status: SessionStatus;
}

export type SessionStatus = 'active' | 'stopped' | 'expired';

export interface RadiusClient {
  id: number;
  name: string;
  shortname: string;
  type: string;
  secret: string;
  server: string;
  community?: string;
  description?: string;
  nas_type: string;
  ports?: number;
  virtual_server?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RadiusUser {
  id: number;
  username: string;
  customer_id: number;
  customer?: Customer;
  password?: string;
  is_active: boolean;
  max_sessions: number;
  simultaneous_use: number;
  session_timeout?: number;
  idle_timeout?: number;
  expiration?: string;
  attributes: RadiusAttribute[];
  groups: RadiusGroup[];
  created_at: string;
  updated_at: string;
}

export interface RadiusAttribute {
  id: number;
  attribute: string;
  op: string;
  value: string;
  type: 'check' | 'reply';
}

export interface RadiusGroup {
  id: number;
  groupname: string;
  priority: number;
  attributes: RadiusAttribute[];
}

export interface RadiusAccounting {
  id: number;
  session_id: string;
  username: string;
  realm?: string;
  nas_ip_address: string;
  nas_port_id?: string;
  nas_port_type?: string;
  start_time?: string;
  stop_time?: string;
  session_time?: number;
  authentication: string;
  connection_info_start?: string;
  connection_info_stop?: string;
  input_octets?: number;
  output_octets?: number;
  called_station_id?: string;
  calling_station_id?: string;
  terminate_cause?: string;
  service_type?: string;
  framed_protocol?: string;
  framed_ip_address?: string;
  created_at: string;
}

export interface RadiusStats {
  total_sessions: number;
  active_sessions: number;
  total_users: number;
  active_users: number;
  total_clients: number;
  active_clients: number;
  authentication_requests: number;
  authentication_accepts: number;
  authentication_rejects: number;
  accounting_requests: number;
  accounting_responses: number;
  sessions_by_nas: NasSessionStats[];
  top_users: UserSessionStats[];
  session_duration_avg: number;
  data_usage_total: DataUsageStats;
}

export interface NasSessionStats {
  nas_ip_address: string;
  nas_name: string;
  active_sessions: number;
  total_sessions: number;
  data_in: number;
  data_out: number;
}

export interface UserSessionStats {
  username: string;
  customer_name: string;
  session_count: number;
  session_time: number;
  data_in: number;
  data_out: number;
  last_session: string;
}

export interface DataUsageStats {
  input_octets: number;
  output_octets: number;
  total_octets: number;
  input_packets: number;
  output_packets: number;
  total_packets: number;
}

export interface RadiusFilters {
  page?: number;
  per_page?: number;
  search?: string;
  username?: string;
  nas_ip_address?: string;
  status?: SessionStatus;
  start_time_from?: string;
  start_time_to?: string;
  customer_id?: number;
}

export interface CreateRadiusUserData {
  username: string;
  customer_id: number;
  password?: string;
  max_sessions?: number;
  simultaneous_use?: number;
  session_timeout?: number;
  idle_timeout?: number;
  expiration?: string;
  attributes?: RadiusAttribute[];
  groups?: number[];
}

export interface UpdateRadiusUserData {
  password?: string;
  is_active?: boolean;
  max_sessions?: number;
  simultaneous_use?: number;
  session_timeout?: number;
  idle_timeout?: number;
  expiration?: string;
  attributes?: RadiusAttribute[];
  groups?: number[];
}

export interface CreateRadiusClientData {
  name: string;
  shortname: string;
  type: string;
  secret: string;
  server: string;
  community?: string;
  description?: string;
  nas_type: string;
  ports?: number;
  virtual_server?: string;
}

export interface UpdateRadiusClientData {
  name?: string;
  shortname?: string;
  type?: string;
  secret?: string;
  server?: string;
  community?: string;
  description?: string;
  nas_type?: string;
  ports?: number;
  virtual_server?: string;
  is_active?: boolean;
}

export interface Customer {
  id: number;
  customer_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  status: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
