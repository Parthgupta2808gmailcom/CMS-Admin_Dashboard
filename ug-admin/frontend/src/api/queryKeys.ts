/**
 * Centralized Query Keys for React Query
 * 
 * Provides type-safe, hierarchical query keys to avoid cache collisions
 * and enable efficient cache invalidation patterns.
 */

// Base query key factories
export const queryKeys = {
  // Health checks
  health: {
    all: ['health'] as const,
    liveness: () => [...queryKeys.health.all, 'liveness'] as const,
    readiness: () => [...queryKeys.health.all, 'readiness'] as const,
  },

  // Students
  students: {
    all: ['students'] as const,
    lists: () => [...queryKeys.students.all, 'list'] as const,
    list: (params?: StudentsListParams) => [...queryKeys.students.lists(), params] as const,
    details: () => [...queryKeys.students.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.students.details(), id] as const,
  },

  // Search
  search: {
    all: ['search'] as const,
    students: (params?: SearchParams) => [...queryKeys.search.all, 'students', params] as const,
    suggestions: (field: string, value: string) => [...queryKeys.search.all, 'suggestions', field, value] as const,
    facets: () => [...queryKeys.search.all, 'facets'] as const,
  },

  // Files
  files: {
    all: ['files'] as const,
    lists: () => [...queryKeys.files.all, 'list'] as const,
    studentFiles: (studentId: string, type?: string) => [...queryKeys.files.lists(), studentId, type] as const,
    details: () => [...queryKeys.files.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.files.details(), id] as const,
    statistics: () => [...queryKeys.files.all, 'statistics'] as const,
  },

  // Email notifications
  notifications: {
    all: ['notifications'] as const,
    logs: (params?: EmailLogsParams) => [...queryKeys.notifications.all, 'logs', params] as const,
    templates: () => [...queryKeys.notifications.all, 'templates'] as const,
  },

  // Email campaigns
  email: {
    all: ['email'] as const,
    templates: () => [...queryKeys.email.all, 'templates'] as const,
    campaigns: () => [...queryKeys.email.all, 'campaigns'] as const,
    campaign: (id: string) => [...queryKeys.email.all, 'campaign', id] as const,
  },

  // Bulk operations
  bulk: {
    all: ['bulk'] as const,
    importHistory: () => [...queryKeys.bulk.all, 'import-history'] as const,
    exportHistory: () => [...queryKeys.bulk.all, 'export-history'] as const,
  },

  // Audit logs
  audit: {
    all: ['audit'] as const,
    logs: (params?: AuditLogsParams) => [...queryKeys.audit.all, 'logs', params] as const,
    userActivity: (userId: string, days?: number) => [...queryKeys.audit.all, 'user-activity', userId, days] as const,
  },

  // Audits (alias for compatibility)
  audits: {
    all: ['audits'] as const,
    byTarget: (target: string) => [...queryKeys.audits.all, 'target', target] as const,
    byUser: (user: string) => [...queryKeys.audits.all, 'user', user] as const,
  },

  // Insights and analytics
  insights: {
    all: ['insights'] as const,
    dashboard: () => [...queryKeys.insights.all, 'dashboard'] as const,
    studentStats: (period?: string) => [...queryKeys.insights.all, 'student-stats', period] as const,
    activityStats: (period?: string) => [...queryKeys.insights.all, 'activity-stats', period] as const,
  },

  // User management
  users: {
    all: ['users'] as const,
    profile: () => [...queryKeys.users.all, 'profile'] as const,
    list: (params?: UsersListParams) => [...queryKeys.users.all, 'list', params] as const,
  },
} as const;

// Parameter types for query keys
export interface StudentsListParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  status?: string;
  country?: string;
  search?: string;
}

export interface SearchParams {
  text_query?: string;
  search_fields?: string[];
  application_statuses?: string[];
  countries?: string[];
  sort_field?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface EmailLogsParams {
  student_id?: string;
  template?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface AuditLogsParams {
  user_id?: string;
  action?: string;
  target_type?: string;
  target_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface UsersListParams {
  page?: number;
  limit?: number;
  role?: string;
  status?: string;
  search?: string;
}

/**
 * Utility functions for query key management
 */
export const queryKeyUtils = {
  /**
   * Invalidate all student-related queries
   */
  invalidateStudents: () => queryKeys.students.all,

  /**
   * Invalidate specific student detail
   */
  invalidateStudent: (id: string) => queryKeys.students.detail(id),

  /**
   * Invalidate all search queries
   */
  invalidateSearch: () => queryKeys.search.all,

  /**
   * Invalidate all file queries for a student
   */
  invalidateStudentFiles: (studentId: string) => queryKeys.files.studentFiles(studentId),

  /**
   * Invalidate all notification logs
   */
  invalidateNotificationLogs: () => queryKeys.notifications.logs(),

  /**
   * Invalidate all insights
   */
  invalidateInsights: () => queryKeys.insights.all,

  /**
   * Get all query keys that should be invalidated when a student is updated
   */
  getStudentUpdateInvalidations: (studentId: string) => [
    queryKeys.students.all,
    queryKeys.students.detail(studentId),
    queryKeys.search.all,
    queryKeys.insights.all,
  ],

  /**
   * Get all query keys that should be invalidated when a file is uploaded
   */
  getFileUploadInvalidations: (studentId: string) => [
    queryKeys.files.studentFiles(studentId),
    queryKeys.files.statistics(),
    queryKeys.students.detail(studentId),
  ],

  /**
   * Get all query keys that should be invalidated when an email is sent
   */
  getEmailSentInvalidations: (studentId?: string) => [
    queryKeys.notifications.logs(),
    queryKeys.insights.all,
    ...(studentId ? [queryKeys.students.detail(studentId)] : []),
  ],
};

export default queryKeys;
