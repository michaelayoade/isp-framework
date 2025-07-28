// Communications module type definitions
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
  metadata?: Record<string, unknown>;
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

export interface CreateTemplateData {
  name: string;
  category: TemplateCategory;
  communication_type: CommunicationType;
  subject_template?: string;
  body_template: string;
  html_template?: string;
  description?: string;
  is_active: boolean;
  language: string;
  required_variables: string[];
  optional_variables: string[];
}

export interface SendCommunicationData {
  template_id?: number;
  communication_type: CommunicationType;
  recipient_email?: string;
  recipient_phone?: string;
  subject?: string;
  body: string;
  customer_id?: number;
  variables?: Record<string, unknown>;
}
