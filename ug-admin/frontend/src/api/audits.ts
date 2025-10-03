import { apiClient } from './axios';

export interface AuditLog {
  id: string;
  user: string;
  action: string;
  target: string;
  timestamp: string;
  details: Record<string, any>;
}

export interface AuditLogsResponse {
  entries: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditLogsParams {
  user?: string;
  action?: string;
  target?: string;
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

export const auditsApi = {
  // Get audit logs with filters
  getAuditLogs: async (params?: AuditLogsParams): Promise<AuditLogsResponse> => {
    const response = await apiClient.get('/audits', { params });
    return response.data;
  },

  // Get audit logs for a specific target (e.g., student)
  getAuditLogsByTarget: async (target: string, limit = 10): Promise<AuditLogsResponse> => {
    const response = await apiClient.get('/audits', {
      params: { target, limit }
    });
    return response.data;
  },

  // Get audit logs for a specific user
  getAuditLogsByUser: async (user: string, limit = 10): Promise<AuditLogsResponse> => {
    const response = await apiClient.get('/audits', {
      params: { user, limit }
    });
    return response.data;
  },
};
