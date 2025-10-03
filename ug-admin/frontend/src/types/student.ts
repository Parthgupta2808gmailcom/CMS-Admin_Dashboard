/**
 * Student Types and Enums
 * 
 * Shared types to avoid circular dependencies
 */

export const ApplicationStatus = {
  EXPLORING: 'Exploring',
  SHORTLISTING: 'Shortlisting',
  APPLYING: 'Applying',
  SUBMITTED: 'Submitted',
  ADMITTED: 'Admitted',
  REJECTED: 'Rejected',
  DEFERRED: 'Deferred',
} as const;

export type ApplicationStatus = typeof ApplicationStatus[keyof typeof ApplicationStatus];

// Student interfaces
export interface Student {
  id: string;
  name: string;
  email: string;
  phone?: string;
  country: string;
  grade?: string;
  application_status: ApplicationStatus;
  last_active?: string;
  ai_summary?: string;
  created_at: string;
  updated_at: string;
}
