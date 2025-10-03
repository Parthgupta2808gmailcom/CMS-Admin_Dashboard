/**
 * Students API Service
 * 
 * Provides typed API methods for student CRUD operations,
 * search, and bulk operations with proper error handling.
 */

import { apiClient, uploadFile, downloadFile } from './axios';
import type { StudentsListParams, SearchParams } from './queryKeys';
import { MockApiService } from '../services/mockApiService';
import { ApplicationStatus, type Student } from '../types/student';

// Re-export for backward compatibility
export { ApplicationStatus, type Student };

export interface StudentCreate {
  name: string;
  email: string;
  phone?: string;
  country: string;
  grade?: string;
  application_status?: ApplicationStatus;
  last_active?: string;
}

export interface StudentUpdate {
  name?: string;
  email?: string;
  phone?: string;
  country?: string;
  grade?: string;
  application_status?: ApplicationStatus;
  last_active?: string;
  ai_summary?: string;
}

export interface StudentResponse {
  student: Student;
  message: string;
}

export interface StudentsListResponse {
  students: Student[];
  total_count: number;
  page_info: {
    limit: number;
    offset: number;
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  message: string;
}

export interface SearchResult {
  students: Student[];
  total_count: number;
  filtered_count: number;
  page_info: {
    limit: number;
    offset: number;
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  search_metadata: {
    processing_time_seconds: number;
    query_complexity: string;
    filters_applied: number;
    text_search_used: boolean;
    executed_at: string;
  };
}

export interface SearchResponse {
  success: boolean;
  message: string;
  results: SearchResult;
}

export interface BulkImportResult {
  total_rows: number;
  successful_imports: number;
  failed_imports: number;
  errors: Array<{
    row_number: number;
    row_data: Record<string, any>;
    error_type: string;
    error_message: string;
    field_errors?: Record<string, string>;
  }>;
  created_student_ids: string[];
  processing_time_seconds: number;
}

export interface BulkImportResponse {
  success: boolean;
  message: string;
  import_result: BulkImportResult;
}

/**
 * Students API service class
 */
export class StudentsApi {
  /**
   * Get paginated list of students
   */
  static async getStudents(params: StudentsListParams = {}): Promise<StudentsListResponse> {
    // Use mock data in development mode
    if (MockApiService.isMockMode()) {
      return MockApiService.getStudents(params) as Promise<StudentsListResponse>;
    }

    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.sort) queryParams.append('sort', params.sort);
    if (params.order) queryParams.append('order', params.order);
    if (params.status) queryParams.append('status', params.status);
    if (params.country) queryParams.append('country', params.country);
    if (params.search) queryParams.append('search', params.search);

    const url = `/students/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiClient.get<StudentsListResponse>(url);
    return response.data;
  }

  /**
   * Get student by ID
   */
  static async getStudent(id: string): Promise<StudentResponse> {
    // Use mock data in development mode
    if (MockApiService.isMockMode()) {
      return MockApiService.getStudent(id) as Promise<StudentResponse>;
    }

    const response = await apiClient.get<StudentResponse>(`/students/${id}`);
    return response.data;
  }

  /**
   * Create new student
   */
  static async createStudent(data: StudentCreate): Promise<StudentResponse> {
    const response = await apiClient.post<StudentResponse>('/students/', data);
    return response.data;
  }

  /**
   * Update existing student
   */
  static async updateStudent(id: string, data: StudentUpdate): Promise<StudentResponse> {
    const response = await apiClient.put<StudentResponse>(`/students/${id}`, data);
    return response.data;
  }

  /**
   * Delete student
   */
  static async deleteStudent(id: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/students/${id}`);
    return response.data;
  }

  /**
   * Advanced search for students
   */
  static async searchStudents(params: SearchParams): Promise<SearchResponse> {
    const response = await apiClient.post<SearchResponse>('/search/students', params);
    return response.data;
  }

  /**
   * Get search suggestions
   */
  static async getSearchSuggestions(
    field: string, 
    partialValue: string, 
    limit = 10
  ): Promise<{ success: boolean; suggestions: string[]; field: string; partial_value: string }> {
    const queryParams = new URLSearchParams({
      field,
      partial_value: partialValue,
      limit: limit.toString(),
    });

    const response = await apiClient.get(`/search/suggestions?${queryParams.toString()}`);
    return response.data;
  }

  /**
   * Get search facets
   */
  static async getSearchFacets(): Promise<{
    success: boolean;
    facets: {
      application_status: Record<string, number>;
      country: Record<string, number>;
      grade: Record<string, number>;
      total_count: number;
    };
  }> {
    const response = await apiClient.get('/search/facets');
    return response.data;
  }

  /**
   * Bulk import students from file
   */
  static async bulkImportStudents(
    file: File,
    formatType?: 'csv' | 'json',
    validateOnly = false,
    onProgress?: (progress: number) => void
  ): Promise<BulkImportResponse> {
    const formData: Record<string, any> = {
      validate_only: validateOnly.toString(),
    };

    if (formatType) {
      formData.format_type = formatType;
    }

    const response = await uploadFile('/bulk/import', file, formData, onProgress);
    return response.data;
  }

  /**
   * Export students to file
   */
  static async exportStudents(params: {
    format_type?: 'csv' | 'json';
    application_status?: string;
    country?: string;
    start_date?: string;
    end_date?: string;
    include_fields?: string;
  } = {}): Promise<void> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value) queryParams.append(key, value);
    });

    const url = `/bulk/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    // Determine filename based on format and filters
    const format = params.format_type || 'csv';
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `students_export_${timestamp}.${format}`;
    
    await downloadFile(url, filename);
  }

  /**
   * Get student statistics for insights
   */
  static async getStudentStats(): Promise<{
    total_students: number;
    by_status: Record<string, number>;
    by_country: Record<string, number>;
    recent_activity: {
      new_students_7d: number;
      updated_students_7d: number;
      active_students_7d: number;
    };
  }> {
    // This would be a custom endpoint for dashboard stats
    // For now, we'll derive from the regular students list
    const response = await apiClient.get('/students/?limit=1000');
    const students: Student[] = response.data.students;
    
    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const stats = {
      total_students: students.length,
      by_status: {} as Record<string, number>,
      by_country: {} as Record<string, number>,
      recent_activity: {
        new_students_7d: 0,
        updated_students_7d: 0,
        active_students_7d: 0,
      },
    };

    students.forEach(student => {
      // Count by status
      const status = student.application_status;
      stats.by_status[status] = (stats.by_status[status] || 0) + 1;

      // Count by country
      stats.by_country[student.country] = (stats.by_country[student.country] || 0) + 1;

      // Count recent activity
      const createdAt = new Date(student.created_at);
      const updatedAt = new Date(student.updated_at);
      const lastActive = student.last_active ? new Date(student.last_active) : null;

      if (createdAt >= sevenDaysAgo) {
        stats.recent_activity.new_students_7d++;
      }

      if (updatedAt >= sevenDaysAgo) {
        stats.recent_activity.updated_students_7d++;
      }

      if (lastActive && lastActive >= sevenDaysAgo) {
        stats.recent_activity.active_students_7d++;
      }
    });

    return stats;
  }
}

export default StudentsApi;
