/**
 * Route Guard Component
 * 
 * Protects routes by checking authentication status and user roles.
 * Redirects unauthenticated users to login page.
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../app/providers/AuthProvider';
import { UserRole, canAccessRoute } from './roles';

interface GuardedProps {
  children: React.ReactNode;
  roles?: UserRole[];
  fallback?: React.ReactNode;
}

/**
 * Loading component shown while checking authentication
 */
function AuthLoadingScreen() {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      gap={2}
    >
      <CircularProgress size={48} />
      <Typography variant="body1" color="text.secondary">
        Checking authentication...
      </Typography>
    </Box>
  );
}

/**
 * Access denied component shown when user lacks required permissions
 */
function AccessDeniedScreen() {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      gap={2}
      px={3}
    >
      <Typography variant="h4" color="error" gutterBottom>
        Access Denied
      </Typography>
      <Typography variant="body1" color="text.secondary" textAlign="center">
        You don't have permission to access this page.
        <br />
        Please contact your administrator if you believe this is an error.
      </Typography>
    </Box>
  );
}

/**
 * Route guard component that protects routes based on authentication and roles
 */
export function Guarded({ children, roles, fallback }: GuardedProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  // Show loading screen while checking authentication
  if (loading) {
    return <AuthLoadingScreen />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Check role-based access if roles are specified
  if (roles && roles.length > 0) {
    const hasRequiredRole = user && roles.includes(user.role);
    
    if (!hasRequiredRole) {
      return fallback || <AccessDeniedScreen />;
    }
  }

  // Check route-based access using the roles system
  if (!canAccessRoute(user, location.pathname)) {
    return fallback || <AccessDeniedScreen />;
  }

  // User is authenticated and has required permissions
  return <>{children}</>;
}

/**
 * Higher-order component for protecting routes
 */
export function withGuard<P extends object>(
  Component: React.ComponentType<P>,
  roles?: UserRole[]
) {
  return function GuardedComponent(props: P) {
    return (
      <Guarded roles={roles}>
        <Component {...props} />
      </Guarded>
    );
  };
}

/**
 * Hook for conditional rendering based on authentication
 */
export function useGuard(roles?: UserRole[]) {
  const { user, isAuthenticated, loading } = useAuth();
  
  const hasAccess = React.useMemo(() => {
    if (loading || !isAuthenticated) {
      return false;
    }
    
    if (!roles || roles.length === 0) {
      return true;
    }
    
    return user && roles.includes(user.role);
  }, [user, isAuthenticated, loading, roles]);
  
  return {
    hasAccess,
    isLoading: loading,
    isAuthenticated,
    user,
  };
}

/**
 * Component for conditional rendering based on roles
 */
interface RoleGuardProps {
  roles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RoleGuard({ roles, children, fallback = null }: RoleGuardProps) {
  const { hasAccess } = useGuard(roles);
  
  return hasAccess ? <>{children}</> : <>{fallback}</>;
}

/**
 * Component for admin-only content
 */
interface AdminOnlyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function AdminOnly({ children, fallback = null }: AdminOnlyProps) {
  return (
    <RoleGuard roles={[UserRole.ADMIN]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

/**
 * Component for staff and admin content
 */
interface StaffOrAdminProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function StaffOrAdmin({ children, fallback = null }: StaffOrAdminProps) {
  return (
    <RoleGuard roles={[UserRole.STAFF, UserRole.ADMIN]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

export default Guarded;
