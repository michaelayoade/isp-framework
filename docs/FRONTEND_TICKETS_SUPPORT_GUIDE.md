# ISP Framework - Tickets & Support Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a comprehensive modular architecture for the tickets and support module frontend, covering ticket management, customer support workflows, knowledge base, and support analytics.

## Modular Architecture

```
src/features/tickets/
├── components/
│   ├── dashboard/              # Support dashboard
│   ├── ticket-list/            # Ticket management
│   ├── ticket-detail/          # Individual ticket view
│   ├── create-ticket/          # Ticket creation
│   ├── knowledge-base/         # Knowledge base
│   ├── analytics/              # Support analytics
│   └── shared/                 # Shared support components
├── hooks/                      # Tickets-specific hooks
├── services/                   # Tickets API layer
├── types/                      # Tickets type definitions
├── utils/                      # Tickets utilities
└── constants/                  # Tickets constants
```

## 1. Type Definitions

```typescript
// src/features/tickets/types/index.ts
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
// src/features/tickets/services/tickets-service.ts
import { apiClient } from '@/api/client';

export class TicketsService {
  private readonly basePath = '/tickets';

  // Ticket management
  async getTickets(filters: TicketFilters = {}) {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data;
  }

  async getTicket(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data;
  }

  async createTicket(data: CreateTicketData) {
    const formData = new FormData();
    
    // Add ticket data
    Object.entries(data).forEach(([key, value]) => {
      if (key === 'attachments') return;
      if (Array.isArray(value)) {
        value.forEach(item => formData.append(`${key}[]`, item));
      } else {
        formData.append(key, value);
      }
    });

    // Add attachments
    if (data.attachments) {
      data.attachments.forEach(file => {
        formData.append('attachments[]', file);
      });
    }

    const response = await apiClient.post(this.basePath, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async updateTicket(id: number, data: UpdateTicketData) {
    const response = await apiClient.put(`${this.basePath}/${id}`, data);
    return response.data;
  }

  async deleteTicket(id: number) {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async assignTicket(id: number, assigneeId: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/assign`, {
      assigned_to: assigneeId
    });
    return response.data;
  }

  async closeTicket(id: number, resolution?: string) {
    const response = await apiClient.post(`${this.basePath}/${id}/close`, { resolution });
    return response.data;
  }

  // Comments
  async addComment(ticketId: number, content: string, isInternal = false, attachments?: File[]) {
    const formData = new FormData();
    formData.append('content', content);
    formData.append('is_internal', isInternal.toString());

    if (attachments) {
      attachments.forEach(file => {
        formData.append('attachments[]', file);
      });
    }

    const response = await apiClient.post(`${this.basePath}/${ticketId}/comments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async updateComment(ticketId: number, commentId: number, content: string) {
    const response = await apiClient.put(`${this.basePath}/${ticketId}/comments/${commentId}`, {
      content
    });
    return response.data;
  }

  async deleteComment(ticketId: number, commentId: number) {
    await apiClient.delete(`${this.basePath}/${ticketId}/comments/${commentId}`);
  }

  // Knowledge base
  async getKnowledgeBaseArticles(filters = {}) {
    const response = await apiClient.get('/knowledge-base', { params: filters });
    return response.data;
  }

  async getKnowledgeBaseArticle(id: number) {
    const response = await apiClient.get(`/knowledge-base/${id}`);
    return response.data;
  }

  async createKnowledgeBaseArticle(data: any) {
    const response = await apiClient.post('/knowledge-base', data);
    return response.data;
  }

  async updateKnowledgeBaseArticle(id: number, data: any) {
    const response = await apiClient.put(`/knowledge-base/${id}`, data);
    return response.data;
  }

  // Statistics
  async getSupportStats(timeRange = '30d') {
    const response = await apiClient.get(`${this.basePath}/stats`, {
      params: { time_range: timeRange }
    });
    return response.data;
  }

  async getTicketTrends(period = 'daily') {
    const response = await apiClient.get(`${this.basePath}/trends`, {
      params: { period }
    });
    return response.data;
  }

  // File operations
  async downloadAttachment(attachmentId: number) {
    const response = await apiClient.get(`${this.basePath}/attachments/${attachmentId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  }

  async deleteAttachment(attachmentId: number) {
    await apiClient.delete(`${this.basePath}/attachments/${attachmentId}`);
  }
}

export const ticketsService = new TicketsService();
```

## 3. Core Components

### 3.1 Support Dashboard

```typescript
// src/features/tickets/components/dashboard/SupportDashboard.tsx
'use client';

import { useState } from 'react';
import { useSupportStats, useTickets } from '../../hooks';
import { SupportStatsCards } from './SupportStatsCards';
import { TicketTrendsChart } from '../analytics/TicketTrendsChart';
import { RecentTickets } from './RecentTickets';
import { QuickActions } from './QuickActions';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, BarChart3, BookOpen, Users } from 'lucide-react';

export function SupportDashboard() {
  const [timeRange, setTimeRange] = useState('30d');
  const [activeTab, setActiveTab] = useState('overview');
  
  const { data: stats } = useSupportStats(timeRange);
  const { data: recentTickets } = useTickets({ 
    per_page: 10, 
    status: 'open' 
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Support Dashboard</h1>
          <p className="text-muted-foreground">
            Manage customer support tickets and knowledge base
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <BarChart3 className="mr-2 h-4 w-4" />
            Reports
          </Button>
          <Button variant="outline">
            <BookOpen className="mr-2 h-4 w-4" />
            Knowledge Base
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Ticket
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && <SupportStatsCards stats={stats} />}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tickets">All Tickets</TabsTrigger>
          <TabsTrigger value="knowledge-base">Knowledge Base</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <TicketTrendsChart timeRange={timeRange} />
              <RecentTickets data={recentTickets} />
            </div>
            <div>
              <QuickActions />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="tickets">
          <TicketManagement />
        </TabsContent>

        <TabsContent value="knowledge-base">
          <KnowledgeBaseManagement />
        </TabsContent>

        <TabsContent value="analytics">
          <SupportAnalytics timeRange={timeRange} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3.2 Ticket Detail View

```typescript
// src/features/tickets/components/ticket-detail/TicketDetailView.tsx
'use client';

import { useState } from 'react';
import { useTicket, useAddComment, useUpdateTicket } from '../../hooks';
import { TicketHeader } from './TicketHeader';
import { TicketComments } from './TicketComments';
import { TicketSidebar } from './TicketSidebar';
import { CommentForm } from './CommentForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { MessageSquare, Paperclip, Clock, User } from 'lucide-react';

interface TicketDetailViewProps {
  ticketId: number;
}

export function TicketDetailView({ ticketId }: TicketDetailViewProps) {
  const [activeTab, setActiveTab] = useState('comments');
  const { data: ticket, isLoading } = useTicket(ticketId);
  const addComment = useAddComment();
  const updateTicket = useUpdateTicket();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">Ticket not found</p>
        </CardContent>
      </Card>
    );
  }

  const handleAddComment = async (content: string, isInternal: boolean, attachments?: File[]) => {
    await addComment.mutateAsync({
      ticketId: ticket.id,
      content,
      isInternal,
      attachments,
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'urgent': return 'destructive';
      case 'high': return 'default';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'destructive';
      case 'in_progress': return 'default';
      case 'pending': return 'secondary';
      case 'resolved': return 'default';
      case 'closed': return 'outline';
      default: return 'secondary';
    }
  };

  return (
    <div className="space-y-6">
      {/* Ticket Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl font-bold">{ticket.title}</h1>
                <Badge variant={getStatusColor(ticket.status)}>
                  {ticket.status.replace('_', ' ').toUpperCase()}
                </Badge>
                <Badge variant={getPriorityColor(ticket.priority)}>
                  {ticket.priority.toUpperCase()}
                </Badge>
              </div>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>#{ticket.ticket_number}</span>
                <span className="flex items-center">
                  <User className="mr-1 h-3 w-3" />
                  {ticket.customer?.first_name} {ticket.customer?.last_name}
                </span>
                <span className="flex items-center">
                  <Clock className="mr-1 h-3 w-3" />
                  Created {new Date(ticket.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            <TicketHeader ticket={ticket} onUpdate={updateTicket.mutateAsync} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            <p>{ticket.description}</p>
          </div>
          
          {ticket.attachments.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-2 flex items-center">
                <Paperclip className="mr-1 h-3 w-3" />
                Attachments
              </h4>
              <div className="flex flex-wrap gap-2">
                {ticket.attachments.map((attachment) => (
                  <Badge key={attachment.id} variant="outline">
                    {attachment.original_filename}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-3">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="comments" className="flex items-center">
                <MessageSquare className="mr-2 h-4 w-4" />
                Comments ({ticket.comments.length})
              </TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            <TabsContent value="comments" className="space-y-4">
              <TicketComments comments={ticket.comments} />
              <Separator />
              <CommentForm
                onSubmit={handleAddComment}
                isLoading={addComment.isPending}
              />
            </TabsContent>

            <TabsContent value="history">
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">Ticket history will be implemented here.</p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <TicketSidebar ticket={ticket} onUpdate={updateTicket.mutateAsync} />
        </div>
      </div>
    </div>
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/tickets/hooks/useTickets.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ticketsService } from '../services/tickets-service';
import { useToast } from '@/hooks/use-toast';

export function useTickets(filters = {}) {
  return useQuery({
    queryKey: ['tickets', filters],
    queryFn: () => ticketsService.getTickets(filters),
    keepPreviousData: true,
  });
}

export function useTicket(id: number) {
  return useQuery({
    queryKey: ['tickets', id],
    queryFn: () => ticketsService.getTicket(id),
    enabled: !!id,
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ticketsService.createTicket,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      toast({
        title: 'Success',
        description: 'Ticket created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create ticket',
        variant: 'destructive',
      });
    },
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      ticketsService.updateTicket(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['tickets', id] });
      toast({
        title: 'Success',
        description: 'Ticket updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update ticket',
        variant: 'destructive',
      });
    },
  });
}

export function useAddComment() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ ticketId, content, isInternal, attachments }: {
      ticketId: number;
      content: string;
      isInternal: boolean;
      attachments?: File[];
    }) => ticketsService.addComment(ticketId, content, isInternal, attachments),
    onSuccess: (_, { ticketId }) => {
      queryClient.invalidateQueries({ queryKey: ['tickets', ticketId] });
      toast({
        title: 'Success',
        description: 'Comment added successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to add comment',
        variant: 'destructive',
      });
    },
  });
}

export function useSupportStats(timeRange = '30d') {
  return useQuery({
    queryKey: ['support-stats', timeRange],
    queryFn: () => ticketsService.getSupportStats(timeRange),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export function useKnowledgeBaseArticles(filters = {}) {
  return useQuery({
    queryKey: ['knowledge-base', filters],
    queryFn: () => ticketsService.getKnowledgeBaseArticles(filters),
    keepPreviousData: true,
  });
}
```

## 5. Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- Set up tickets module structure
- Implement types and service layer
- Create basic hooks and utilities

### Phase 2: Ticket Management (Days 3-4)
- Build ticket list and filtering
- Implement ticket creation and editing
- Create ticket assignment workflow

### Phase 3: Ticket Detail & Comments (Days 5-6)
- Build comprehensive ticket detail view
- Implement comment system with attachments
- Create ticket status management

### Phase 4: Knowledge Base (Days 7-8)
- Build knowledge base article management
- Implement article search and categorization
- Create customer-facing knowledge base

### Phase 5: Analytics & Reporting (Days 9-10)
- Build support analytics dashboard
- Implement performance metrics
- Create customer satisfaction tracking

This modular architecture provides comprehensive support ticket management with knowledge base integration, detailed analytics, and efficient customer service workflows.
