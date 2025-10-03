/**
 * React Query Provider Configuration
 * 
 * Sets up TanStack Query with sensible defaults for caching,
 * error handling, and retry logic for the admin dashboard.
 */

import React from 'react';
import { QueryClient, QueryClientProvider, type DefaultOptions } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ApiError } from '../../api/axios';

// Query client configuration
const queryConfig: DefaultOptions = {
  queries: {
    // Stale time: how long data is considered fresh
    staleTime: 30 * 1000, // 30 seconds
    
    // Cache time: how long inactive data stays in cache
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
    
    // Retry configuration
    retry: (failureCount, error) => {
      // Don't retry on auth errors or client errors (4xx)
      if (error instanceof ApiError) {
        if (error.status && error.status >= 400 && error.status < 500) {
          return false;
        }
      }
      
      // Retry up to 2 times for other errors
      return failureCount < 2;
    },
    
    // Retry delay with exponential backoff
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    
    // Refetch on window focus (useful for real-time updates)
    refetchOnWindowFocus: false,
    
    // Refetch on reconnect
    refetchOnReconnect: true,
    
    // Refetch on mount if data is stale
    refetchOnMount: true,
  },
  mutations: {
    // Retry mutations once on network errors
    retry: (failureCount, error) => {
      if (error instanceof ApiError) {
        // Don't retry client errors
        if (error.status && error.status >= 400 && error.status < 500) {
          return false;
        }
      }
      
      return failureCount < 1;
    },
    
    // Mutation retry delay
    retryDelay: 1000,
  },
};

// Create query client instance
const queryClient = new QueryClient({
  defaultOptions: queryConfig,
});

// Global error handler for queries
queryClient.setMutationDefaults(['students', 'create'], {
  onError: (error) => {
    console.error('Mutation error:', error);
    // You can add global error handling here, like showing toast notifications
  },
});

// Global success handler for mutations
queryClient.setMutationDefaults(['students', 'create'], {
  onSuccess: (data) => {
    console.log('Mutation success:', data);
    // You can add global success handling here
  },
});

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * Query Provider component that wraps the app with React Query
 */
export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Show React Query DevTools in development */}
      {import.meta.env.DEV && (
        <ReactQueryDevtools
          initialIsOpen={false}
          position="bottom"
        />
      )}
    </QueryClientProvider>
  );
}

/**
 * Hook to access the query client instance
 */
export function useQueryClient() {
  return queryClient;
}

/**
 * Utility functions for cache management
 */
export const cacheUtils = {
  /**
   * Invalidate all queries matching a pattern
   */
  invalidateQueries: (queryKey: unknown[]) => {
    return queryClient.invalidateQueries({ queryKey });
  },

  /**
   * Remove queries from cache
   */
  removeQueries: (queryKey: unknown[]) => {
    return queryClient.removeQueries({ queryKey });
  },

  /**
   * Set query data in cache
   */
  setQueryData: (queryKey: unknown[], data: any) => {
    return queryClient.setQueryData(queryKey, data);
  },

  /**
   * Get query data from cache
   */
  getQueryData: (queryKey: unknown[]) => {
    return queryClient.getQueryData(queryKey);
  },

  /**
   * Prefetch a query
   */
  prefetchQuery: (queryKey: unknown[], queryFn: () => Promise<any>) => {
    return queryClient.prefetchQuery({
      queryKey,
      queryFn,
    });
  },

  /**
   * Clear all cache
   */
  clear: () => {
    return queryClient.clear();
  },

  /**
   * Get cache stats for debugging
   */
  getStats: () => {
    const cache = queryClient.getQueryCache();
    const queries = cache.getAll();
    
    return {
      totalQueries: queries.length,
      activeQueries: queries.filter(q => q.getObserversCount() > 0).length,
      staleQueries: queries.filter(q => q.isStale()).length,
      invalidQueries: queries.filter(q => q.state.isInvalidated).length,
    };
  },
};

export default QueryProvider;
