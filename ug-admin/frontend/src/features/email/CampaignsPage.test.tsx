/**
 * CampaignsPage Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CampaignsPage } from './CampaignsPage';
import { renderWithProviders, mockApiResponses } from '../../tests/utils';

// Mock the APIs
vi.mock('../../api/email', () => ({
  emailApi: {
    getCampaigns: vi.fn(),
    sendEmail: vi.fn(),
    getTemplates: vi.fn(),
  },
}));

vi.mock('../../api/students', () => ({
  studentsApi: {
    getStudents: vi.fn(),
  },
}));

describe('CampaignsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API responses
    const { emailApi } = require('../../api/email');
    const { studentsApi } = require('../../api/students');
    
    emailApi.getCampaigns.mockResolvedValue(mockApiResponses.campaigns.list);
    emailApi.getTemplates.mockResolvedValue([]);
    studentsApi.getStudents.mockResolvedValue(mockApiResponses.students.list);
  });

  it('renders campaigns page correctly', async () => {
    renderWithProviders(<CampaignsPage />);

    expect(screen.getByText('Email Campaigns')).toBeInTheDocument();
    expect(screen.getByText('New Campaign')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Welcome to UG!')).toBeInTheDocument();
    });
  });

  it('shows recipient filters', () => {
    renderWithProviders(<CampaignsPage />);

    expect(screen.getByText('Recipient Filters')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/name or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/application status/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/filter by country/i)).toBeInTheDocument();
  });

  it('updates recipient count based on filters', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText(/selected recipients: 2 students/i)).toBeInTheDocument();
    });

    // Apply a filter
    const statusFilter = screen.getByLabelText(/application status/i);
    await user.click(statusFilter);
    await user.click(screen.getByText('Exploring'));

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.getStudents).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'Exploring' })
      );
    });
  });

  it('opens compose dialog when clicking New Campaign', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CampaignsPage />);

    await user.click(screen.getByText('New Campaign'));

    expect(screen.getByText('New Email Campaign')).toBeInTheDocument();
    expect(screen.getByText(/recipients \(2\)/i)).toBeInTheDocument();
  });

  it('opens compose dialog when clicking Compose Email', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CampaignsPage />);

    await waitFor(async () => {
      const composeButton = screen.getByText('Compose Email');
      await user.click(composeButton);
    });

    expect(screen.getByText('New Email Campaign')).toBeInTheDocument();
  });

  it('displays campaigns list with correct information', async () => {
    renderWithProviders(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Welcome to UG!')).toBeInTheDocument();
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument(); // recipients
      expect(screen.getByText('8')).toBeInTheDocument(); // sent
      expect(screen.getByText('2')).toBeInTheDocument(); // failed
    });
  });

  it('shows empty state when no campaigns exist', async () => {
    const { emailApi } = require('../../api/email');
    emailApi.getCampaigns.mockResolvedValue({ campaigns: [], total: 0 });

    renderWithProviders(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('No campaigns yet')).toBeInTheDocument();
      expect(screen.getByText(/create your first email campaign/i)).toBeInTheDocument();
    });
  });

  it('handles search filter correctly', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CampaignsPage />);

    const searchInput = screen.getByPlaceholderText(/name or email/i);
    await user.type(searchInput, 'john');

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.getStudents).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'john' })
      );
    });
  });

  it('handles country filter correctly', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CampaignsPage />);

    const countryInput = screen.getByPlaceholderText(/filter by country/i);
    await user.type(countryInput, 'USA');

    await waitFor(() => {
      const { studentsApi } = require('../../api/students');
      expect(studentsApi.getStudents).toHaveBeenCalledWith(
        expect.objectContaining({ country: 'USA' })
      );
    });
  });

  it('disables compose button when no recipients', async () => {
    const { studentsApi } = require('../../api/students');
    studentsApi.getStudents.mockResolvedValue({ students: [], total: 0 });

    renderWithProviders(<CampaignsPage />);

    await waitFor(() => {
      const composeButton = screen.getByText('Compose Email');
      expect(composeButton).toBeDisabled();
    });
  });

  it('shows loading state', () => {
    const { emailApi } = require('../../api/email');
    emailApi.getCampaigns.mockImplementation(() => new Promise(() => {}));

    renderWithProviders(<CampaignsPage />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows error state', async () => {
    const { emailApi } = require('../../api/email');
    emailApi.getCampaigns.mockRejectedValue(new Error('Failed to fetch campaigns'));

    renderWithProviders(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch campaigns/i)).toBeInTheDocument();
    });
  });
});
