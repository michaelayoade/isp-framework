// Common types shared across features
// This module consolidates frequently used types to reduce duplication

/**
 * Generic paginated response structure used by all API endpoints
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/**
 * Common API error response structure
 */
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

/**
 * Base address structure used across customer, reseller, and other entities
 */
export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
  country?: string;
}

/**
 * Common audit fields for entities
 */
export interface AuditFields {
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

/**
 * Base entity interface with common fields
 */
export interface BaseEntity extends AuditFields {
  id: number;
}

/**
 * Common status types used across different entities
 */
export type EntityStatus = 'active' | 'inactive' | 'suspended' | 'pending' | 'cancelled';

/**
 * Common filter interface for list endpoints
 */
export interface BaseFilters {
  search?: string;
  status?: EntityStatus;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/**
 * Common statistics structure
 */
export interface BaseStats {
  total: number;
  active: number;
  inactive: number;
  growth_rate?: number;
}

/**
 * Common time period filter
 */
export interface TimePeriodFilter {
  start_date?: string;
  end_date?: string;
  period?: 'day' | 'week' | 'month' | 'quarter' | 'year';
}

/**
 * Common form validation error structure
 */
export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Common API response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
}

/**
 * Common loading state for async operations
 */
export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

/**
 * Common contact information structure
 */
export interface ContactInfo {
  email: string;
  phone?: string;
  mobile?: string;
  fax?: string;
}

/**
 * Common money/currency structure
 */
export interface Money {
  amount: number;
  currency: string;
}

/**
 * Common file/attachment structure
 */
export interface FileAttachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  uploaded_at: string;
}
