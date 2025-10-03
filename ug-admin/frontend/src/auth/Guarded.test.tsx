/**
 * Guarded Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { Guarded } from './Guarded';
import { UserRole } from './roles';
import { renderWithProviders, mockAdminUser, mockStaffUser } from '../tests/utils';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Guarded', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders children when user is authenticated', () => {
    renderWithProviders(
      <Guarded>
        <div>Protected Content</div>
      </Guarded>,
      { user: mockAdminUser }
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated', () => {
    renderWithProviders(
      <Guarded>
        <div>Protected Content</div>
      </Guarded>,
      { user: null }
    );

    expect(mockNavigate).toHaveBeenCalledWith('/login');
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when user has required role', () => {
    renderWithProviders(
      <Guarded roles={[UserRole.ADMIN]}>
        <div>Admin Content</div>
      </Guarded>,
      { user: mockAdminUser }
    );

    expect(screen.getByText('Admin Content')).toBeInTheDocument();
  });

  it('shows access denied when user lacks required role', () => {
    renderWithProviders(
      <Guarded roles={[UserRole.ADMIN]}>
        <div>Admin Content</div>
      </Guarded>,
      { user: mockStaffUser }
    );

    expect(screen.getByText(/access denied/i)).toBeInTheDocument();
    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
  });

  it('allows staff to access staff-only content', () => {
    renderWithProviders(
      <Guarded roles={[UserRole.STAFF]}>
        <div>Staff Content</div>
      </Guarded>,
      { user: mockStaffUser }
    );

    expect(screen.getByText('Staff Content')).toBeInTheDocument();
  });

  it('allows admin to access staff content (role hierarchy)', () => {
    renderWithProviders(
      <Guarded roles={[UserRole.STAFF]}>
        <div>Staff Content</div>
      </Guarded>,
      { user: mockAdminUser }
    );

    expect(screen.getByText('Staff Content')).toBeInTheDocument();
  });

  it('allows multiple roles', () => {
    renderWithProviders(
      <Guarded roles={[UserRole.ADMIN, UserRole.STAFF]}>
        <div>Multi-Role Content</div>
      </Guarded>,
      { user: mockStaffUser }
    );

    expect(screen.getByText('Multi-Role Content')).toBeInTheDocument();
  });
});
