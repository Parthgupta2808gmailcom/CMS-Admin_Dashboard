/**
 * Loading State Components
 * 
 * Reusable loading indicators for different UI contexts
 * with consistent styling and accessibility.
 */

import React from 'react';
import {
  Box,
  CircularProgress,
  Skeleton,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';

interface LoadingStateProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

/**
 * Basic loading spinner with optional message
 */
export function LoadingState({ message = 'Loading...', size = 'medium' }: LoadingStateProps) {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 56,
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      py={4}
      gap={2}
    >
      <CircularProgress size={sizeMap[size]} />
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}

/**
 * Page-level loading state
 */
export function PageLoadingState({ message = 'Loading page...' }: { message?: string }) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="60vh"
      gap={2}
    >
      <CircularProgress size={48} />
      <Typography variant="h6" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}

/**
 * Card loading skeleton
 */
export function CardLoadingSkeleton() {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="60%" height={32} />
        <Skeleton variant="text" width="40%" height={24} sx={{ mt: 1 }} />
        <Skeleton variant="rectangular" height={100} sx={{ mt: 2 }} />
        <Box display="flex" gap={1} mt={2}>
          <Skeleton variant="rectangular" width={80} height={32} />
          <Skeleton variant="rectangular" width={80} height={32} />
        </Box>
      </CardContent>
    </Card>
  );
}

/**
 * Table loading skeleton
 */
interface TableLoadingSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableLoadingSkeleton({ rows = 5, columns = 4 }: TableLoadingSkeletonProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          {Array.from({ length: columns }).map((_, index) => (
            <TableCell key={index}>
              <Skeleton variant="text" width="80%" />
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <TableRow key={rowIndex}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <TableCell key={colIndex}>
                <Skeleton variant="text" width={colIndex === 0 ? '60%' : '80%'} />
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/**
 * List loading skeleton
 */
interface ListLoadingSkeletonProps {
  items?: number;
}

export function ListLoadingSkeleton({ items = 3 }: ListLoadingSkeletonProps) {
  return (
    <Box>
      {Array.from({ length: items }).map((_, index) => (
        <Box key={index} display="flex" alignItems="center" gap={2} py={2}>
          <Skeleton variant="circular" width={40} height={40} />
          <Box flexGrow={1}>
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width="40%" />
          </Box>
          <Skeleton variant="rectangular" width={80} height={32} />
        </Box>
      ))}
    </Box>
  );
}

/**
 * Inline loading indicator for buttons or small spaces
 */
export function InlineLoadingState({ size = 16 }: { size?: number }) {
  return (
    <CircularProgress
      size={size}
      sx={{
        display: 'inline-flex',
        verticalAlign: 'middle',
      }}
    />
  );
}

export default LoadingState;
