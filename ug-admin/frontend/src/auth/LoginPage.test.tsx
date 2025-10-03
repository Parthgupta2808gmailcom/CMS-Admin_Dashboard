/**
 * LoginPage Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginPage } from './LoginPage';
import { renderWithProviders } from '../tests/utils';

// Mock Firebase auth functions
const mockSignInWithEmailAndPassword = vi.fn();
const mockSignInWithPopup = vi.fn();

vi.mock('./firebase', () => ({
  auth: {
    currentUser: null,
    onAuthStateChanged: vi.fn(),
  },
  googleProvider: {},
}));

vi.mock('firebase/auth', () => ({
  signInWithEmailAndPassword: mockSignInWithEmailAndPassword,
  signInWithPopup: mockSignInWithPopup,
  GoogleAuthProvider: vi.fn(),
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form correctly', () => {
    renderWithProviders(<LoginPage />, { user: null });

    expect(screen.getByText('Welcome to UG Admin')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
  });

  it('handles email/password login successfully', async () => {
    const user = userEvent.setup();
    mockSignInWithEmailAndPassword.mockResolvedValueOnce({
      user: { uid: 'test-uid', email: 'test@example.com' },
    });

    renderWithProviders(<LoginPage />, { user: null });

    // Fill in the form
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    
    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockSignInWithEmailAndPassword).toHaveBeenCalledWith(
        expect.anything(),
        'test@example.com',
        'password123'
      );
    });
  });

  it('handles Google login successfully', async () => {
    const user = userEvent.setup();
    mockSignInWithPopup.mockResolvedValueOnce({
      user: { uid: 'google-uid', email: 'google@example.com' },
    });

    renderWithProviders(<LoginPage />, { user: null });

    await user.click(screen.getByRole('button', { name: /continue with google/i }));

    await waitFor(() => {
      expect(mockSignInWithPopup).toHaveBeenCalled();
    });
  });

  it('displays error message on login failure', async () => {
    const user = userEvent.setup();
    mockSignInWithEmailAndPassword.mockRejectedValueOnce(
      new Error('Invalid credentials')
    );

    renderWithProviders(<LoginPage />, { user: null });

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { user: null });

    // Try to submit without filling fields
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Check for validation messages (this depends on your validation implementation)
    expect(screen.getByLabelText(/email/i)).toBeInvalid();
  });

  it('redirects authenticated users', () => {
    renderWithProviders(<LoginPage />); // With default admin user

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
