/**
 * Application Routes Configuration
 * 
 * Defines all routes for the admin dashboard with proper
 * authentication guards and role-based access control.
 */
// ../features/insights/InsightsDashboard
import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Guarded } from '../auth/Guarded';
import { UserRole } from '../auth/roles';
import { DashboardLayout } from './layout/DashboardLayout';
import { LoginPage } from '../auth/LoginPage';

// Direct imports for now (can optimize with lazy loading later)
import { InsightsDashboard } from '../features/insights/InsightsDashboard';
import { StudentsListPage } from '../features/students/StudentsListPage';
import { StudentDetailPage } from '../features/students/StudentDetailPage';
import { CampaignsPage } from '../features/email/CampaignsPage';

// Error boundary component
function ErrorBoundary({ error }: { error: Error }) {
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={() => window.location.reload()}>
        Reload Page
      </button>
    </div>
  );
}

// Loading component for lazy-loaded routes
function LoadingFallback() {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '200px' 
    }}>
      Loading...
    </div>
  );
}

// Wrapper for lazy-loaded components with suspense
function LazyWrapper({ children }: { children: React.ReactNode }) {
  return (
    <React.Suspense fallback={<LoadingFallback />}>
      {children}
    </React.Suspense>
  );
}

/**
 * Router configuration
 */
const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: <LoginPage />,
    errorElement: <ErrorBoundary error={new Error('Login page error')} />,
  },

  // Protected routes with dashboard layout
  {
    path: '/',
    element: (
      <Guarded>
        <DashboardLayout />
      </Guarded>
    ),
    errorElement: <ErrorBoundary error={new Error('Dashboard error')} />,
    children: [
      // Dashboard home
      {
        index: true,
        element: <InsightsDashboard />,
      },

      // Students routes
      {
        path: 'students',
        children: [
          {
            index: true,
            element: <StudentsListPage />,
          },
          {
            path: ':id',
            element: <StudentDetailPage />,
          },
        ],
      },

      // Email campaigns
      {
        path: 'campaigns',
        element: <CampaignsPage />,
      },

      // Admin-only routes
      {
        path: 'admin',
        element: (
          <Guarded roles={[UserRole.ADMIN]}>
            <div>Admin Panel (Coming Soon)</div>
          </Guarded>
        ),
      },

      // Audit logs (admin only)
      {
        path: 'audit-logs',
        element: (
          <Guarded roles={[UserRole.ADMIN]}>
            <div>Audit Logs (Coming Soon)</div>
          </Guarded>
        ),
      },

      // User management (admin only)
      {
        path: 'user-management',
        element: (
          <Guarded roles={[UserRole.ADMIN]}>
            <div>User Management (Coming Soon)</div>
          </Guarded>
        ),
      },
    ],
  },

  // Catch-all route for 404
  {
    path: '*',
    element: (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        textAlign: 'center'
      }}>
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Go back to dashboard</a>
      </div>
    ),
  },
]);

/**
 * Routes component that provides the router
 */
export function Routes() {
  return <RouterProvider router={router} />;
}

export default Routes;
