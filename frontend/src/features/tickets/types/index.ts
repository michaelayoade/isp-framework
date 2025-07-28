// Tickets module type definitions
export interface Ticket {
  id: number;
  ticket_number: string;
  title: string;
  description: string;
  customer_id: number;
  customer?: Customer;
  assigned_to?: number;
  assignee?: Administrator;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  source: TicketSource;
  tags: string[];
  attachments: TicketAttachment[];
  comments: TicketComment[];
  resolution?: string;
  resolved_at?: string;
  closed_at?: string;
  due_date?: string;
  first_response_at?: string;
  created_at: string;
  updated_at: string;
}

export type TicketStatus = 'open' | 'in_progress' | 'pending' | 'resolved' | 'closed';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent' | 'critical';
export type TicketCategory = 'technical' | 'billing' | 'service' | 'general' | 'complaint';
export type TicketSource = 'web' | 'email' | 'phone' | 'chat' | 'portal';

export interface TicketComment {
  id: number;
  ticket_id: number;
  author_id: number;
  author?: Administrator | Customer;
  author_type: 'admin' | 'customer';
  content: string;
  is_internal: boolean;
  attachments: TicketAttachment[];
  created_at: string;
}

export interface TicketAttachment {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  file_path: string;
  uploaded_by: number;
  created_at: string;
}

export interface KnowledgeBaseArticle {
  id: number;
  title: string;
  content: string;
  category: string;
  tags: string[];
  is_published: boolean;
  view_count: number;
  helpful_count: number;
  author_id: number;
  author?: Administrator;
  created_at: string;
  updated_at: string;
}

export interface SupportStats {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  average_response_time: number;
  average_resolution_time: number;
  customer_satisfaction: number;
  tickets_by_priority: Record<TicketPriority, number>;
  tickets_by_category: Record<TicketCategory, number>;
  tickets_by_status: Record<TicketStatus, number>;
}

export interface TicketFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  assigned_to?: number;
  customer_id?: number;
  created_from?: string;
  created_to?: string;
  tags?: string[];
}

export interface CreateTicketData {
  title: string;
  description: string;
  customer_id: number;
  category: TicketCategory;
  priority: TicketPriority;
  source: TicketSource;
  tags?: string[];
  attachments?: File[];
}

export interface UpdateTicketData {
  title?: string;
  description?: string;
  category?: TicketCategory;
  priority?: TicketPriority;
  status?: TicketStatus;
  assigned_to?: number;
  tags?: string[];
  resolution?: string;
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

export interface Administrator {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
