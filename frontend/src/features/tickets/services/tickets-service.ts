import { apiClient } from '@/api/client';
import type {
  Ticket,
  TicketComment,
  KnowledgeBaseArticle,
  SupportStats,
  TicketFilters,
  CreateTicketData,
  UpdateTicketData,
  PaginatedResponse,
} from '../types';

export class TicketsService {
  private readonly basePath = '/tickets';

  // Ticket management
  async getTickets(filters: TicketFilters = {}) {
    const response = await apiClient.get(this.basePath, { params: filters });
    return response.data as PaginatedResponse<Ticket>;
  }

  async getTicket(id: number) {
    const response = await apiClient.get(`${this.basePath}/${id}`);
    return response.data as Ticket;
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
    return response.data as Ticket;
  }

  async updateTicket(id: number, data: UpdateTicketData) {
    const response = await apiClient.put(`${this.basePath}/${id}`, data);
    return response.data as Ticket;
  }

  async deleteTicket(id: number) {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async assignTicket(id: number, assigneeId: number) {
    const response = await apiClient.post(`${this.basePath}/${id}/assign`, {
      assigned_to: assigneeId
    });
    return response.data as Ticket;
  }

  async closeTicket(id: number, resolution?: string) {
    const response = await apiClient.post(`${this.basePath}/${id}/close`, { resolution });
    return response.data as Ticket;
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
    return response.data as TicketComment;
  }

  async updateComment(ticketId: number, commentId: number, content: string) {
    const response = await apiClient.put(`${this.basePath}/${ticketId}/comments/${commentId}`, {
      content
    });
    return response.data as TicketComment;
  }

  async deleteComment(ticketId: number, commentId: number) {
    await apiClient.delete(`${this.basePath}/${ticketId}/comments/${commentId}`);
  }

  // Knowledge base
  async getKnowledgeBaseArticles(filters = {}) {
    const response = await apiClient.get('/knowledge-base', { params: filters });
    return response.data as PaginatedResponse<KnowledgeBaseArticle>;
  }

  async getKnowledgeBaseArticle(id: number) {
    const response = await apiClient.get(`/knowledge-base/${id}`);
    return response.data as KnowledgeBaseArticle;
  }

  async createKnowledgeBaseArticle(data: Record<string, unknown>) {
    const response = await apiClient.post('/knowledge-base', data);
    return response.data as KnowledgeBaseArticle;
  }

  async updateKnowledgeBaseArticle(id: number, data: Record<string, unknown>) {
    const response = await apiClient.put(`/knowledge-base/${id}`, data);
    return response.data as KnowledgeBaseArticle;
  }

  async deleteKnowledgeBaseArticle(id: number) {
    await apiClient.delete(`/knowledge-base/${id}`);
  }

  // Statistics
  async getSupportStats(timeRange = '30d') {
    const response = await apiClient.get(`${this.basePath}/stats`, {
      params: { time_range: timeRange }
    });
    return response.data as SupportStats;
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

  // Export functionality
  async exportTickets(format: 'csv' | 'excel' | 'pdf', filters?: TicketFilters) {
    const response = await apiClient.get(`${this.basePath}/export`, {
      params: { format, ...filters },
      responseType: 'blob'
    });
    return response.data;
  }
}

export const ticketsService = new TicketsService();
