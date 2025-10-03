/**
 * Test utilities and helpers
 * 
 * Provides common testing utilities, mocks, and wrapper components
 */

import React from 'react';
import { vi } from 'vitest';
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { theme } from '../styles/theme';
import { AuthProvider } from '../app/providers/AuthProvider';
import { UserRole, type AuthenticatedUser } from '../auth/roles';

// Mock user data
export const mockAdminUser: AuthenticatedUser = {
  uid: 'admin-123',
  email: 'admin@test.com',
  role: UserRole.ADMIN,
  displayName: 'Test Admin',
};

export const mockStaffUser: AuthenticatedUser = {
  uid: 'staff-123',
  email: 'staff@test.com',
  role: UserRole.STAFF,
  displayName: 'Test Staff',
};

// Mock students data
export const mockStudents = [
  {
    id: 'student-1',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1234567890',
    country: 'USA',
    grade: '12',
    applicationStatus: 'Exploring',
    lastActive: '2024-01-15T10:00:00Z',
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'student-2',
    name: 'Jane Smith',
    email: 'jane@example.com',
    phone: '+1234567891',
    country: 'Canada',
    grade: '11',
    applicationStatus: 'Applying',
    lastActive: '2024-01-14T15:30:00Z',
    createdAt: '2024-01-02T00:00:00Z',
  },
];

// Mock files data
export const mockFiles = [
  {
    id: 'file-1',
    studentId: 'student-1',
    filename: 'transcript.pdf',
    originalName: 'transcript.pdf',
    fileType: 'application/pdf',
    fileSize: 1024000,
    uploadedAt: '2024-01-15T10:00:00Z',
    uploadedBy: 'admin@test.com',
    downloadUrl: 'https://example.com/files/transcript.pdf',
  },
];

// Mock campaigns data
export const mockCampaigns = [
  {
    id: 'campaign-1',
    subject: 'Welcome to UG!',
    recipients: 10,
    sent: 8,
    failed: 2,
    status: 'completed' as const,
    createdAt: '2024-01-15T10:00:00Z',
    createdBy: 'admin@test.com',
  },
];

// Mock audit logs
export const mockAuditLogs = [
  {
    id: 'audit-1',
    user: 'admin@test.com',
    action: 'CREATE_STUDENT',
    target: 'student-1',
    timestamp: '2024-01-15T10:00:00Z',
    details: { name: 'John Doe' },
  },
];

/**
 * Custom render function with all providers
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  user?: AuthenticatedUser | null;
  initialEntries?: string[];
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    user = mockAdminUser,
    initialEntries = ['/'],
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  // Create a fresh QueryClient for each test
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <QueryClientProvider client={queryClient}>
            <AuthProvider initialUser={user}>
              {children}
            </AuthProvider>
          </QueryClientProvider>
        </ThemeProvider>
      </BrowserRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

/**
 * Mock API responses
 */
export const mockApiResponses = {
  students: {
    list: {
      students: mockStudents,
      total: mockStudents.length,
      page: 1,
      limit: 10,
      totalPages: 1,
    },
    detail: mockStudents[0],
  },
  files: {
    list: mockFiles,
  },
  campaigns: {
    list: {
      campaigns: mockCampaigns,
      total: mockCampaigns.length,
    },
  },
  audits: {
    list: {
      entries: mockAuditLogs,
      total: mockAuditLogs.length,
      limit: 10,
      offset: 0,
    },
  },
};

/**
 * Wait for async operations to complete
 */
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

/**
 * Mock axios instance
 */
export const mockAxios = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  patch: vi.fn(),
};

// Re-export everything from testing library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
