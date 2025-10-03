/**
 * Students Query Hooks
 * 
 * React Query hooks for fetching and managing student data
 * with proper caching, error handling, and optimistic updates.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { StudentsApi } from '../../api/students';
import type { Student, StudentCreate, StudentUpdate } from '../../api/students';
import { queryKeys } from '../../api/queryKeys';
import type { StudentsListParams, SearchParams } from '../../api/queryKeys';
import { ApiError } from '../../api/axios';

/**
 * Hook to fetch paginated list of students
 */
export function useStudentsQuery(params: StudentsListParams = {}) {
  return useQuery({
    queryKey: queryKeys.students.list(params),
    queryFn: () => StudentsApi.getStudents(params),
    staleTime: 30 * 1000, // 30 seconds
    retry: (failureCount, error) => {
      // Don't retry on client errors
      if (error instanceof ApiError && error.status && error.status < 500) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

/**
 * Hook to fetch a single student by ID
 */
export function useStudentQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.students.detail(id),
    queryFn: () => StudentsApi.getStudent(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
    retry: (failureCount, error) => {
      // Don't retry on 404 errors
      if (error instanceof ApiError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

/**
 * Hook to search students with advanced filters
 */
export function useStudentsSearchQuery(params: SearchParams) {
  return useQuery({
    queryKey: queryKeys.search.students(params),
    queryFn: () => StudentsApi.searchStudents(params),
    enabled: !!(params.text_query || params.application_statuses || params.countries),
    staleTime: 15 * 1000, // 15 seconds (shorter for search results)
  });
}

/**
 * Hook to get search suggestions
 */
export function useSearchSuggestionsQuery(field: string, partialValue: string) {
  return useQuery({
    queryKey: queryKeys.search.suggestions(field, partialValue),
    queryFn: () => StudentsApi.getSearchSuggestions(field, partialValue),
    enabled: !!(field && partialValue && partialValue.length >= 2),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get search facets
 */
export function useSearchFacetsQuery() {
  return useQuery({
    queryKey: queryKeys.search.facets(),
    queryFn: () => StudentsApi.getSearchFacets(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to create a new student
 */
export function useCreateStudentMutation() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: (data: StudentCreate) => StudentsApi.createStudent(data),
    onSuccess: (response) => {
      // Invalidate and refetch students list
      queryClient.invalidateQueries({ queryKey: queryKeys.students.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.search.all });
      
      // Show success message
      enqueueSnackbar(`Student "${response.student.name}" created successfully`, {
        variant: 'success',
      });
    },
    onError: (error: ApiError) => {
      // Show error message
      enqueueSnackbar(error.message || 'Failed to create student', {
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to update an existing student
 */
export function useUpdateStudentMutation() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: StudentUpdate }) =>
      StudentsApi.updateStudent(id, data),
    onSuccess: (response, { id }) => {
      // Update the student in cache
      queryClient.setQueryData(
        queryKeys.students.detail(id),
        response
      );
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.students.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.search.all });
      
      // Show success message
      enqueueSnackbar(`Student "${response.student.name}" updated successfully`, {
        variant: 'success',
      });
    },
    onError: (error: ApiError) => {
      // Show error message
      enqueueSnackbar(error.message || 'Failed to update student', {
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to delete a student
 */
export function useDeleteStudentMutation() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: (id: string) => StudentsApi.deleteStudent(id),
    onSuccess: (_, id) => {
      // Remove student from cache
      queryClient.removeQueries({ queryKey: queryKeys.students.detail(id) });
      
      // Invalidate students list
      queryClient.invalidateQueries({ queryKey: queryKeys.students.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.search.all });
      
      // Show success message
      enqueueSnackbar('Student deleted successfully', {
        variant: 'success',
      });
    },
    onError: (error: ApiError) => {
      // Show error message
      enqueueSnackbar(error.message || 'Failed to delete student', {
        variant: 'error',
      });
    },
  });
}

/**
 * Hook for bulk import students
 */
export function useBulkImportMutation() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: ({
      file,
      formatType,
      validateOnly,
      onProgress,
    }: {
      file: File;
      formatType?: 'csv' | 'json';
      validateOnly?: boolean;
      onProgress?: (progress: number) => void;
    }) => StudentsApi.bulkImportStudents(file, formatType, validateOnly, onProgress),
    onSuccess: (response) => {
      const { import_result } = response;
      
      // Invalidate students list if any were created
      if (import_result.successful_imports > 0) {
        queryClient.invalidateQueries({ queryKey: queryKeys.students.lists() });
        queryClient.invalidateQueries({ queryKey: queryKeys.search.all });
      }
      
      // Show appropriate message based on results
      if (import_result.failed_imports === 0) {
        enqueueSnackbar(
          `Successfully imported ${import_result.successful_imports} students`,
          { variant: 'success' }
        );
      } else {
        enqueueSnackbar(
          `Import completed: ${import_result.successful_imports} successful, ${import_result.failed_imports} failed`,
          { variant: 'warning' }
        );
      }
    },
    onError: (error: ApiError) => {
      enqueueSnackbar(error.message || 'Failed to import students', {
        variant: 'error',
      });
    },
  });
}

/**
 * Hook to get student statistics for dashboard
 */
export function useStudentStatsQuery() {
  return useQuery({
    queryKey: ['students', 'stats'],
    queryFn: () => StudentsApi.getStudentStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Utility hook to prefetch student data
 */
export function usePrefetchStudent() {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.students.detail(id),
      queryFn: () => StudentsApi.getStudent(id),
      staleTime: 60 * 1000,
    });
  };
}
