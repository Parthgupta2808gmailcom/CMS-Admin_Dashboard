/**
 * StudentsListPage Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StudentsListPage } from './StudentsListPage';
import { renderWithProviders, mockApiResponses, mockAxios } from '../../tests/utils';

// Mock the API
vi.mock('../../api/students', () => ({
  studentsApi: {
    getStudents: vi.fn(),
    deleteStudent: vi.fn(),
    bulkImportStudents: vi.fn(),
    exportStudents: vi.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  };
});

describe('StudentsListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock successful API response
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudents.mockResolvedValue(mockApiResponses.students.list);
  });

  it('renders students list correctly', async () => {
    renderWithProviders(<StudentsListPage />);

    // Check for page title
    expect(screen.getByText('Students')).toBeInTheDocument();

    // Wait for students to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    // Check for table headers
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Country')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentsListPage />);

    const searchInput = screen.getByPlaceholderText(/search students/i);
    await user.type(searchInput, 'John');

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.getStudents).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'John' })
      );
    });
  });

  it('handles status filter', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentsListPage />);

    // Find and click the status filter
    const statusFilter = screen.getByLabelText(/application status/i);
    await user.click(statusFilter);
    
    // Select a status
    await user.click(screen.getByText('Exploring'));

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.getStudents).toHaveBeenCalledWith(
        expect.objectContaining({ applicationStatus: 'Exploring' })
      );
    });
  });

  it('navigates to student detail on row click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentsListPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    await user.click(screen.getByText('John Doe'));

    expect(mockNavigate).toHaveBeenCalledWith('/students/student-1');
  });

  it('shows loading state', () => {
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudents.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithProviders(<StudentsListPage />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows error state', async () => {
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudents.mockRejectedValue(new Error('Failed to fetch'));

    renderWithProviders(<StudentsListPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no students', async () => {
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudents.mockResolvedValue({
      students: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    });

    renderWithProviders(<StudentsListPage />);

    await waitFor(() => {
      expect(screen.getByText(/no students found/i)).toBeInTheDocument();
    });
  });

  it('handles pagination', async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentsListPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Find pagination controls (this depends on your pagination implementation)
    const nextButton = screen.getByLabelText(/next page/i);
    if (nextButton && !nextButton.hasAttribute('disabled')) {
      await user.click(nextButton);

      await waitFor(() => {
        const { studentsApi } = require('../../api/students');
        expect(studentsApi.getStudents).toHaveBeenCalledWith(
          expect.objectContaining({ page: 2 })
        );
      });
    }
  });

  it('shows bulk actions for admin users', async () => {
    renderWithProviders(<StudentsListPage />); // Default user is admin

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    expect(screen.getByText(/import/i)).toBeInTheDocument();
    expect(screen.getByText(/export/i)).toBeInTheDocument();
  });

  it('hides bulk actions for staff users', async () => {
    const { mockStaffUser } = await import('../../tests/utils');
    renderWithProviders(<StudentsListPage />, { user: mockStaffUser });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    expect(screen.queryByText(/import/i)).not.toBeInTheDocument();
  });
});
