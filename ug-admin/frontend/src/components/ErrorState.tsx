/**
 * Error State Components
 * 
 * Reusable error display components with retry functionality
 * and consistent error messaging.
 */

import React from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Card,
  CardContent,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { ApiError } from '../api/axios';

interface ErrorStateProps {
  error?: Error | ApiError | string;
  onRetry?: () => void;
  title?: string;
  message?: string;
  showDetails?: boolean;
}

/**
 * Basic error state component
 */
export function ErrorState({
  error,
  onRetry,
  title = 'Something went wrong',
  message,
  showDetails = false,
}: ErrorStateProps) {
  // Extract error message
  const errorMessage = React.useMemo(() => {
    if (message) return message;
    
    if (typeof error === 'string') return error;
    
    if (error instanceof ApiError) {
      return error.message || 'An API error occurred';
    }
    
    if (error instanceof Error) {
      return error.message || 'An unexpected error occurred';
    }
    
    return 'An unknown error occurred';
  }, [error, message]);

  // Extract error code for API errors
  const errorCode = error instanceof ApiError ? error.code : undefined;
  const errorStatus = error instanceof ApiError ? error.status : undefined;

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      py={4}
      px={2}
      textAlign="center"
    >
      <ErrorIcon
        sx={{
          fontSize: 48,
          color: 'error.main',
          mb: 2,
        }}
      />
      
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 400 }}>
        {errorMessage}
      </Typography>

      {/* Error details for development or debugging */}
      {showDetails && (errorCode || errorStatus) && (
        <Box sx={{ mb: 2, textAlign: 'left' }}>
          {errorCode && (
            <Typography variant="caption" display="block">
              Error Code: {errorCode}
            </Typography>
          )}
          {errorStatus && (
            <Typography variant="caption" display="block">
              Status: {errorStatus}
            </Typography>
          )}
        </Box>
      )}

      {onRetry && (
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </Box>
  );
}

/**
 * Page-level error state
 */
export function PageErrorState({
  error,
  onRetry,
  title = 'Failed to load page',
}: ErrorStateProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="60vh"
    >
      <ErrorState
        error={error}
        onRetry={onRetry}
        title={title}
        showDetails={import.meta.env.DEV}
      />
    </Box>
  );
}

/**
 * Inline error alert
 */
interface InlineErrorProps {
  error?: Error | ApiError | string;
  severity?: 'error' | 'warning';
  onClose?: () => void;
  action?: React.ReactNode;
}

export function InlineError({
  error,
  severity = 'error',
  onClose,
  action,
}: InlineErrorProps) {
  const errorMessage = React.useMemo(() => {
    if (typeof error === 'string') return error;
    if (error instanceof Error) return error.message;
    return 'An error occurred';
  }, [error]);

  if (!error) return null;

  return (
    <Alert
      severity={severity}
      onClose={onClose}
      action={action}
      sx={{ mb: 2 }}
    >
      <AlertTitle>
        {severity === 'error' ? 'Error' : 'Warning'}
      </AlertTitle>
      {errorMessage}
    </Alert>
  );
}

/**
 * Card-based error display
 */
export function ErrorCard({
  error,
  onRetry,
  title = 'Error',
}: ErrorStateProps) {
  const errorMessage = React.useMemo(() => {
    if (typeof error === 'string') return error;
    if (error instanceof Error) return error.message;
    return 'An error occurred';
  }, [error]);

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="flex-start" gap={2}>
          <ErrorIcon color="error" />
          <Box flexGrow={1}>
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {errorMessage}
            </Typography>
            {onRetry && (
              <Button
                size="small"
                startIcon={<RefreshIcon />}
                onClick={onRetry}
              >
                Retry
              </Button>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

/**
 * Network error specific component
 */
export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      title="Connection Problem"
      message="Unable to connect to the server. Please check your internet connection and try again."
      onRetry={onRetry}
    />
  );
}

/**
 * Not found error component
 */
export function NotFoundError({ 
  resource = 'resource',
  onGoBack,
}: { 
  resource?: string;
  onGoBack?: () => void;
}) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      py={4}
      textAlign="center"
    >
      <WarningIcon
        sx={{
          fontSize: 48,
          color: 'warning.main',
          mb: 2,
        }}
      />
      
      <Typography variant="h6" gutterBottom>
        {resource.charAt(0).toUpperCase() + resource.slice(1)} Not Found
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        The {resource} you're looking for doesn't exist or may have been removed.
      </Typography>

      {onGoBack && (
        <Button variant="contained" onClick={onGoBack}>
          Go Back
        </Button>
      )}
    </Box>
  );
}

/**
 * Permission denied error component
 */
export function PermissionDeniedError() {
  return (
    <ErrorState
      title="Access Denied"
      message="You don't have permission to access this resource. Please contact your administrator if you believe this is an error."
    />
  );
}

export default ErrorState;
