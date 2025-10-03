/**
 * Main Application Component
 * 
 * Root component that sets up all providers and routing for the
 * Undergraduation.com Admin Dashboard.
 */

import React from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { SnackbarProvider } from 'notistack';
import { ThemeProvider } from './providers/ThemeProvider';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './providers/AuthProvider';
import { Routes } from './routes';

/**
 * Error fallback component for the error boundary
 */
function ErrorFallback({ error, resetErrorBoundary }: { 
  error: Error; 
  resetErrorBoundary: () => void;
}) {
  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '2rem',
        textAlign: 'center',
        backgroundColor: '#f5f5f5',
      }}
    >
      <h1 style={{ color: '#d32f2f', marginBottom: '1rem' }}>
        Something went wrong
      </h1>
      <p style={{ marginBottom: '1rem', maxWidth: '600px' }}>
        {error.message || 'An unexpected error occurred in the application.'}
      </p>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button
          onClick={resetErrorBoundary}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#1976d2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Try Again
        </button>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#757575',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Reload Page
        </button>
      </div>
      
      {/* Error details for development */}
      {import.meta.env.DEV && (
        <details style={{ marginTop: '2rem', textAlign: 'left' }}>
          <summary style={{ cursor: 'pointer', marginBottom: '1rem' }}>
            Error Details (Development)
          </summary>
          <pre
            style={{
              backgroundColor: '#f0f0f0',
              padding: '1rem',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '0.875rem',
            }}
          >
            {error.stack}
          </pre>
        </details>
      )}
    </div>
  );
}

/**
 * Main App Component
 */
export function App() {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        // Log error to console in development
        if (import.meta.env.DEV) {
          console.error('Application Error:', error, errorInfo);
        }
        
        // In production, you would send this to an error reporting service
        // like Sentry, LogRocket, etc.
      }}
    >
      {/* Theme Provider - MUI theming and CSS baseline */}
      <ThemeProvider>
        {/* Snackbar Provider - Global notifications */}
        <SnackbarProvider
          maxSnack={3}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          autoHideDuration={5000}
          preventDuplicate
        >
          {/* React Query Provider - Data fetching and caching */}
          <QueryProvider>
            {/* Auth Provider - Firebase authentication and user state */}
            <AuthProvider>
              {/* Application Routes */}
              <Routes />
            </AuthProvider>
          </QueryProvider>
        </SnackbarProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
