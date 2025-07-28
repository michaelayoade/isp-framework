import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ticketsService } from '../services/tickets-service';
import { useToast } from '@/hooks/use-toast';
import type { TicketFilters, CreateTicketData, UpdateTicketData } from '../types';

export function useTickets(filters: TicketFilters = {}) {
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
    mutationFn: (data: CreateTicketData) => ticketsService.createTicket(data),
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
    mutationFn: ({ id, data }: { id: number; data: UpdateTicketData }) =>
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

export function useDeleteTicket() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => ticketsService.deleteTicket(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      toast({
        title: 'Success',
        description: 'Ticket deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete ticket',
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

export function useKnowledgeBaseArticle(id: number) {
  return useQuery({
    queryKey: ['knowledge-base', id],
    queryFn: () => ticketsService.getKnowledgeBaseArticle(id),
    enabled: !!id,
  });
}

export function useCreateKnowledgeBaseArticle() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: Record<string, unknown>) => ticketsService.createKnowledgeBaseArticle(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-base'] });
      toast({
        title: 'Success',
        description: 'Knowledge base article created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create knowledge base article',
        variant: 'destructive',
      });
    },
  });
}
