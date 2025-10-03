import { apiClient } from './axios';
import { MockApiService } from '../services/mockApiService';

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  variables: string[];
}

export interface EmailRecipient {
  id: string;
  name: string;
  email: string;
}

export interface EmailRequest {
  recipients: string[]; // student IDs
  subject: string;
  template?: string;
  variables?: Record<string, any>;
  body?: string;
}

export interface EmailResponse {
  campaignId: string;
  message: string;
  sent: number;
  failed: number;
}

export interface EmailCampaign {
  id: string;
  subject: string;
  template?: string;
  recipients: number;
  sent: number;
  failed: number;
  status: 'draft' | 'sending' | 'completed' | 'failed';
  createdAt: string;
  sentAt?: string;
  createdBy: string;
}

export const emailApi = {
  // Get email templates
  getTemplates: async (): Promise<EmailTemplate[]> => {
    if (MockApiService.isMockMode()) {
      const response = await MockApiService.getTemplates();
      return response.templates;
    }
    const response = await apiClient.get('/email/templates');
    return response.data.templates || [];
  },

  // Send email to students
  sendEmail: async (emailData: EmailRequest): Promise<EmailResponse> => {
    const response = await apiClient.post('/email/send', emailData);
    return response.data;
  },

  // Preview email with template variables
  previewEmail: async (templateId: string, variables: Record<string, any>): Promise<{ subject: string; body: string }> => {
    const response = await apiClient.post('/email/preview', {
      template: templateId,
      variables,
    });
    return response.data;
  },

  // Get email campaigns
  getCampaigns: async (params?: { limit?: number; offset?: number }): Promise<{
    campaigns: EmailCampaign[];
    total: number;
  }> => {
    if (MockApiService.isMockMode()) {
      return MockApiService.getCampaigns(params);
    }
    const response = await apiClient.get('/email/campaigns', { params });
    return response.data;
  },

  // Get campaign details
  getCampaignById: async (campaignId: string): Promise<EmailCampaign> => {
    const response = await apiClient.get(`/email/campaigns/${campaignId}`);
    return response.data.campaign;
  },
};
