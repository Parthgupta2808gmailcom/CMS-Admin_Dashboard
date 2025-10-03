/**
 * StudentDetailPage Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StudentDetailPage } from './StudentDetailPage';
import { renderWithProviders, mockApiResponses } from '../../tests/utils';

// Mock the APIs
vi.mock('../../api/students', () => ({
  studentsApi: {
    getStudentById: vi.fn(),
    updateStudent: vi.fn(),
    deleteStudent: vi.fn(),
  },
}));

vi.mock('../../api/files', () => ({
  filesApi: {
    getStudentFiles: vi.fn(),
    uploadFile: vi.fn(),
    deleteFile: vi.fn(),
  },
}));

vi.mock('../../api/audits', () => ({
  auditsApi: {
    getAuditLogs: vi.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'student-1' }),
    useNavigate: () => mockNavigate,
  };
});

describe('StudentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API responses
    const { studentsApi } = require('../../api/students');
    const { filesApi } = require('../../api/files');
    const { auditsApi } = require('../../api/audits');
    
    studentsApi.getStudentById.mockResolvedValue(mockApiResponses.students.detail);
    filesApi.getStudentFiles.mockResolvedValue(mockApiResponses.files.list);
    auditsApi.getAuditLogs.mockResolvedValue(mockApiResponses.audits.list);
  });

  it('renders student detail correctly', async () => {
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Check for tabs
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Files')).toBeInTheDocument();
    expect(screen.getByText('Activity')).toBeInTheDocument();

    // Check for student info
    expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('USA')).toBeInTheDocument();
  });

  it('allows admin to edit student information', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click edit button
    await user.click(screen.getByText('Edit'));

    // Check that fields are now editable
    const nameField = screen.getByDisplayValue('John Doe');
    expect(nameField).not.toBeDisabled();

    // Make a change
    await user.clear(nameField);
    await user.type(nameField, 'John Updated');

    // Save changes
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.updateStudent).toHaveBeenCalledWith(
        'student-1',
        expect.objectContaining({ name: 'John Updated' })
      );
    });
  });

  it('prevents staff from editing student information', async () => {
    const { mockStaffUser } = await import('../../tests/utils');
    renderWithProviders(<StudentDetailPage />, { user: mockStaffUser });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Edit button should not be visible for staff
    expect(screen.queryByText('Edit')).not.toBeInTheDocument();
  });

  it('switches between tabs correctly', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click Files tab
    await user.click(screen.getByText('Files'));
    expect(screen.getByText('Upload Files')).toBeInTheDocument();

    // Click Activity tab
    await user.click(screen.getByText('Activity'));
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('shows file upload interface in Files tab', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Files'));

    expect(screen.getByText('Upload Files')).toBeInTheDocument();
    expect(screen.getByText(/drop files here/i)).toBeInTheDocument();
  });

  it('shows audit logs in Activity tab', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Activity'));

    await waitFor(() => {
      expect(screen.getByText('CREATE_STUDENT')).toBeInTheDocument();
    });
  });

  it('handles delete student for admin', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click delete button
    await user.click(screen.getByText('Delete'));

    // Confirm deletion in dialog
    await user.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.deleteStudent).toHaveBeenCalledWith('student-1');
    });
  });

  it('shows loading state', () => {
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudentById.mockImplementation(() => new Promise(() => {}));

    renderWithProviders(<StudentDetailPage />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows error state', async () => {
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudentById.mockRejectedValue(new Error('Student not found'));

    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/student not found/i)).toBeInTheDocument();
    });
  });

  it('navigates back to students list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click back button
    const backButton = screen.getByLabelText(/back/i);
    await user.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith('/students');
  });
});
