# ISP Framework - Communications Module Frontend Guide

_Date: 2025-07-27_  
_Version: 1.0_

## Overview

This guide provides a modular architecture for the communications module frontend, covering email templates, SMS management, notification systems, and communication analytics.

## Modular Architecture

```
src/features/communications/
├── components/
│   ├── dashboard/              # Communications dashboard
│   ├── templates/              # Template management
│   ├── campaigns/              # Email/SMS campaigns
│   ├── notifications/          # System notifications
│   ├── analytics/              # Communication analytics
│   └── shared/                 # Shared components
├── hooks/                      # Communication-specific hooks
├── services/                   # Communication API layer
├── types/                      # Communication type definitions
├── utils/                      # Communication utilities
└── constants/                  # Communication constants
```

## 1. Type Definitions

```typescript
// src/features/communications/types/index.ts
export interface CommunicationTemplate {
  id: number;
  name: string;
  category: TemplateCategory;
  communication_type: CommunicationType;
  subject_template?: string;
  body_template: string;
  html_template?: string;
  is_active: boolean;
  language: string;
  required_variables: string[];
  optional_variables: string[];
  created_at: string;
  updated_at: string;
}

export type CommunicationType = 'email' | 'sms' | 'push_notification';
export type TemplateCategory = 'customer_onboarding' | 'billing' | 'service_alerts' | 'support' | 'marketing';

export interface CommunicationLog {
  id: number;
  communication_type: CommunicationType;
  status: CommunicationStatus;
  recipient_email?: string;
  recipient_phone?: string;
  subject?: string;
  body: string;
  template_id?: number;
  customer_id?: number;
  sent_at?: string;
  delivered_at?: string;
  error_message?: string;
  created_at: string;
}

export type CommunicationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';

export interface CommunicationStats {
  total_sent: number;
  total_delivered: number;
  delivery_rate: number;
  open_rate: number;
  by_type: Record<CommunicationType, { sent: number; delivered: number; }>;
}
```

## 2. Service Layer

```typescript
// src/features/communications/services/communications-service.ts
import { apiClient } from '@/lib/api-client';

export class CommunicationsService {
  private readonly basePath = '/communications';

  async getTemplates(filters = {}) {
    const response = await apiClient.get(`${this.basePath}/templates`, { params: filters });
    return response.data;
  }

  async createTemplate(data) {
    const response = await apiClient.post(`${this.basePath}/templates`, data);
    return response.data;
  }

  async sendCommunication(data) {
    const response = await apiClient.post(`${this.basePath}/send`, data);
    return response.data;
  }

  async getStats(dateRange) {
    const response = await apiClient.get(`${this.basePath}/stats`, { params: dateRange });
    return response.data;
  }
}

export const communicationsService = new CommunicationsService();
```

## 3. Core Components

### 3.1 Communications Dashboard

```typescript
// src/features/communications/components/dashboard/CommunicationsDashboard.tsx
'use client';

import { useState } from 'react';
import { useCommunicationStats } from '../../hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Settings } from 'lucide-react';

export function CommunicationsDashboard() {
  const { data: stats } = useCommunicationStats();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Communications</h1>
          <p className="text-muted-foreground">Manage templates and campaigns</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Button>
        </div>
      </div>

      {/* Stats cards and content */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Sent</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_sent}</div>
            </CardContent>
          </Card>
          {/* More stat cards */}
        </div>
      )}
    </div>
  );
}
```

### 3.2 Template Editor

```typescript
// src/features/communications/components/templates/TemplateEditor.tsx
'use client';

import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';

export function TemplateEditor({ template, onSubmit, onCancel }) {
  const form = useForm({
    defaultValues: {
      name: template?.name || '',
      category: template?.category || 'customer_onboarding',
      communication_type: template?.communication_type || 'email',
      body_template: template?.body_template || '',
    },
  });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      <Input 
        placeholder="Template name"
        {...form.register('name')}
      />
      
      <Select {...form.register('category')}>
        <option value="customer_onboarding">Customer Onboarding</option>
        <option value="billing">Billing</option>
        <option value="service_alerts">Service Alerts</option>
      </Select>

      <Textarea 
        placeholder="Template content with {{variables}}"
        {...form.register('body_template')}
        className="min-h-[200px]"
      />

      <div className="flex justify-end space-x-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">
          {template ? 'Update' : 'Create'} Template
        </Button>
      </div>
    </form>
  );
}
```

## 4. Custom Hooks

```typescript
// src/features/communications/hooks/useCommunications.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { communicationsService } from '../services';
import { useToast } from '@/hooks/use-toast';

export function useCommunicationTemplates(filters = {}) {
  return useQuery({
    queryKey: ['communication-templates', filters],
    queryFn: () => communicationsService.getTemplates(filters),
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: communicationsService.createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication-templates'] });
      toast({ title: 'Success', description: 'Template created successfully' });
    },
  });
}

export function useCommunicationStats(dateRange) {
  return useQuery({
    queryKey: ['communication-stats', dateRange],
    queryFn: () => communicationsService.getStats(dateRange),
    refetchInterval: 5 * 60 * 1000,
  });
}
```

## 5. Implementation Phases

### Phase 1: Core Structure (Days 1-2)
- Set up feature module structure
- Implement types and service layer
- Create basic hooks

### Phase 2: Template Management (Days 3-4)
- Build template editor with Jinja2 support
- Create template preview functionality
- Add variable detection and validation

### Phase 3: Communication Sending (Days 5-6)
- Implement communication sending interface
- Build campaign management
- Add delivery tracking

### Phase 4: Analytics & Reporting (Days 7-8)
- Create communication analytics dashboard
- Build delivery rate charts
- Implement performance metrics

This modular architecture provides a solid foundation for managing all communication needs while maintaining flexibility for future enhancements.
