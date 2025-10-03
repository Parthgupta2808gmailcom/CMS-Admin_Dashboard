/**
 * Authentication Provider
 * 
 * Manages Firebase authentication state, user roles, and provides
 * authentication context throughout the application.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { User } from 'firebase/auth';
import { AuthService } from '../../auth/firebase';
import { UserRole } from '../../auth/roles';
import type { AuthenticatedUser } from '../../auth/roles';
import { apiClient } from '../../api/axios';

// Authentication context interface
interface AuthContextType {
  // Authentication state
  user: AuthenticatedUser | null;
  firebaseUser: User | null;
  loading: boolean;
  
  // Authentication methods
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  
  // Token management
  getIdToken: (forceRefresh?: boolean) => Promise<string | null>;
  
  // Role checking helpers
  isAdmin: boolean;
  isStaff: boolean;
  isAuthenticated: boolean;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider props interface
interface AuthProviderProps {
  children: ReactNode;
  initialUser?: AuthenticatedUser | null; // For testing
}

/**
 * Authentication Provider component
 */
export function AuthProvider({ children, initialUser }: AuthProviderProps) {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [user, setUser] = useState<AuthenticatedUser | null>(initialUser || null);
  const [loading, setLoading] = useState(!initialUser);

  /**
   * Fetch user role from backend after authentication
   */
  const fetchUserRole = async (firebaseUser: User): Promise<UserRole> => {
    try {
      // Get ID token to make authenticated request
      const token = await firebaseUser.getIdToken();
      
      // Make request to backend to get user role
      // This assumes you have an endpoint like /auth/me or similar
      const response = await apiClient.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // Extract role from response
      const role = response.data.role || response.data.user?.role;
      
      // Validate role
      if (Object.values(UserRole).includes(role)) {
        return role as UserRole;
      }
      
      // Default to staff if role is invalid
      console.warn('Invalid role received from backend, defaulting to staff:', role);
      return UserRole.STAFF;
      
    } catch (error) {
      console.error('Failed to fetch user role:', error);
      
      // Default to staff role if backend request fails
      // In a production app, you might want to handle this differently
      return UserRole.STAFF;
    }
  };

  /**
   * Handle Firebase auth state changes
   */
  useEffect(() => {
    // Skip Firebase initialization in test mode
    if (initialUser !== undefined) {
      setLoading(false);
      return;
    }

    const unsubscribe = AuthService.onAuthStateChanged(async (firebaseUser) => {
      setLoading(true);
      
      try {
        if (firebaseUser) {
          // User is signed in
          setFirebaseUser(firebaseUser);
          
          // Fetch user role from backend
          const role = await fetchUserRole(firebaseUser);
          
          // Create authenticated user object
          const authenticatedUser: AuthenticatedUser = {
            uid: firebaseUser.uid,
            email: firebaseUser.email || '',
            role,
            displayName: firebaseUser.displayName || undefined,
            photoURL: firebaseUser.photoURL || undefined,
          };
          
          setUser(authenticatedUser);
          
          console.log('User authenticated:', {
            uid: authenticatedUser.uid,
            email: authenticatedUser.email,
            role: authenticatedUser.role,
          });
        } else {
          // User is signed out
          setFirebaseUser(null);
          setUser(null);
          console.log('User signed out');
        }
      } catch (error) {
        console.error('Auth state change error:', error);
        setFirebaseUser(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    });

    // Listen for token expiration events
    const handleTokenExpired = () => {
      console.warn('Token expired, signing out user');
      signOut();
    };

    window.addEventListener('auth:token-expired', handleTokenExpired);

    // Cleanup
    return () => {
      unsubscribe();
      window.removeEventListener('auth:token-expired', handleTokenExpired);
    };
  }, []);

  /**
   * Sign in with email and password
   */
  const signIn = async (email: string, password: string): Promise<void> => {
    try {
      setLoading(true);
      await AuthService.signInWithEmail(email, password);
      // Auth state change will be handled by the listener
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  /**
   * Sign in with Google
   */
  const signInWithGoogle = async (): Promise<void> => {
    try {
      setLoading(true);
      await AuthService.signInWithGoogle();
      // Auth state change will be handled by the listener
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  /**
   * Sign out current user
   */
  const signOut = async (): Promise<void> => {
    try {
      await AuthService.signOut();
      // Auth state change will be handled by the listener
    } catch (error) {
      console.error('Sign out error:', error);
      // Force clear state even if sign out fails
      setFirebaseUser(null);
      setUser(null);
    }
  };

  /**
   * Get current user's ID token
   */
  const getIdToken = async (forceRefresh = false): Promise<string | null> => {
    return AuthService.getIdToken(forceRefresh);
  };

  // Computed properties for role checking
  const isAdmin = user?.role === UserRole.ADMIN;
  const isStaff = user?.role === UserRole.STAFF || user?.role === UserRole.ADMIN;
  const isAuthenticated = user !== null;

  // Context value
  const value: AuthContextType = {
    user,
    firebaseUser,
    loading,
    signIn,
    signInWithGoogle,
    signOut,
    getIdToken,
    isAdmin,
    isStaff,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

/**
 * Hook to get current authenticated user
 */
export function useUser(): AuthenticatedUser | null {
  const { user } = useAuth();
  return user;
}

/**
 * Hook to check if user has admin role
 */
export function useIsAdmin(): boolean {
  const { isAdmin } = useAuth();
  return isAdmin;
}

/**
 * Hook to check if user has staff role (includes admin)
 */
export function useIsStaff(): boolean {
  const { isStaff } = useAuth();
  return isStaff;
}

/**
 * Hook to check if user is authenticated
 */
export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

export default AuthProvider;
