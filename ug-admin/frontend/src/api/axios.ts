/**
 * Axios Configuration with Authentication Interceptors
 * 
 * Sets up Axios instance with automatic token injection, error handling,
 * and request/response interceptors for the admin dashboard API.
 */

import axios, { type AxiosInstance, type AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { AuthService } from '../auth/firebase';

// API base configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Backend error response interface
interface BackendError {
  code: string;
  message: string;
  details?: Record<string, any>;
  request_id?: string;
}

// API error class for consistent error handling
export class ApiError extends Error {
  public code: string;
  public details?: Record<string, any>;
  public requestId?: string;
  public status?: number;

  constructor(
    message: string, 
    code: string = 'UNKNOWN_ERROR', 
    status?: number,
    details?: Record<string, any>,
    requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
    this.requestId = requestId;
  }
}

/**
 * Create configured Axios instance
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth token
  client.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      try {
        // Get fresh Firebase ID token
        const token = await AuthService.getIdToken();
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp for debugging
        (config as any).metadata = {
          startTime: Date.now(),
        };

        console.debug('API Request:', {
          method: config.method?.toUpperCase(),
          url: config.url,
          hasAuth: !!token,
        });

        return config;
      } catch (error) {
        console.error('Request interceptor error:', error);
        return config;
      }
    },
    (error) => {
      console.error('Request interceptor error:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling and logging
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log successful responses in development
      if (import.meta.env.DEV) {
        const duration = Date.now() - ((response.config as any).metadata?.startTime || 0);
        console.debug('API Response:', {
          method: response.config.method?.toUpperCase(),
          url: response.config.url,
          status: response.status,
          duration: `${duration}ms`,
        });
      }

      return response;
    },
    async (error: AxiosError) => {
      const originalRequest = error.config;

      // Log error details
      console.error('API Error:', {
        method: originalRequest?.method?.toUpperCase(),
        url: originalRequest?.url,
        status: error.response?.status,
        message: error.message,
      });

      // Handle different error scenarios
      if (error.response) {
        // Server responded with error status
        const { status, data } = error.response;
        
        // Try to extract backend error format
        let backendError: BackendError | null = null;
        
        if (data && typeof data === 'object') {
          // Handle FastAPI error format
          if ('detail' in data) {
            if (typeof (data as any).detail === 'string') {
              backendError = {
                code: 'API_ERROR',
                message: (data as any).detail,
              };
            } else if (typeof (data as any).detail === 'object') {
              backendError = {
                code: (data as any).detail.code || 'API_ERROR',
                message: (data as any).detail.message || 'An error occurred',
                details: (data as any).detail.details,
                request_id: (data as any).detail.request_id,
              };
            }
          }
          // Handle direct backend error format
          else if ('code' in data && 'message' in data) {
            backendError = data as BackendError;
          }
        }

        // Handle authentication errors
        if (status === 401) {
          // Token expired or invalid - try to refresh
          if (originalRequest && !(originalRequest as any)._retry) {
            (originalRequest as any)._retry = true;
            
            try {
              // Force token refresh
              const newToken = await AuthService.getIdToken(true);
              
              if (newToken && originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return client(originalRequest);
              }
            } catch (refreshError) {
              console.error('Token refresh failed:', refreshError);
              // Redirect to login or emit auth error event
              window.dispatchEvent(new CustomEvent('auth:token-expired'));
            }
          }

          throw new ApiError(
            backendError?.message || 'Authentication required',
            backendError?.code || 'AUTH_ERROR',
            status,
            backendError?.details,
            backendError?.request_id
          );
        }

        // Handle authorization errors
        if (status === 403) {
          throw new ApiError(
            backendError?.message || 'Insufficient permissions',
            backendError?.code || 'FORBIDDEN',
            status,
            backendError?.details,
            backendError?.request_id
          );
        }

        // Handle validation errors
        if (status === 400 || status === 422) {
          throw new ApiError(
            backendError?.message || 'Invalid request data',
            backendError?.code || 'VALIDATION_ERROR',
            status,
            backendError?.details,
            backendError?.request_id
          );
        }

        // Handle not found errors
        if (status === 404) {
          throw new ApiError(
            backendError?.message || 'Resource not found',
            backendError?.code || 'NOT_FOUND',
            status,
            backendError?.details,
            backendError?.request_id
          );
        }

        // Handle server errors
        if (status >= 500) {
          throw new ApiError(
            backendError?.message || 'Internal server error',
            backendError?.code || 'SERVER_ERROR',
            status,
            backendError?.details,
            backendError?.request_id
          );
        }

        // Handle other HTTP errors
        throw new ApiError(
          backendError?.message || `HTTP ${status} error`,
          backendError?.code || 'HTTP_ERROR',
          status,
          backendError?.details,
          backendError?.request_id
        );
      } else if (error.request) {
        // Network error (no response received)
        throw new ApiError(
          'Network error. Please check your connection and try again.',
          'NETWORK_ERROR'
        );
      } else {
        // Request setup error
        throw new ApiError(
          'Request configuration error',
          'REQUEST_ERROR'
        );
      }
    }
  );

  return client;
}

// Create and export the configured API client
export const apiClient = createApiClient();

/**
 * Utility function to handle file uploads with progress
 */
export async function uploadFile(
  url: string,
  file: File,
  additionalData?: Record<string, any>,
  onProgress?: (progress: number) => void
): Promise<AxiosResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  // Add additional form data
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  return apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
}

/**
 * Utility function to download files
 */
export async function downloadFile(url: string, filename?: string): Promise<void> {
  try {
    const response = await apiClient.get(url, {
      responseType: 'blob',
    });

    // Create blob URL and trigger download
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Download error:', error);
    throw error;
  }
}

/**
 * Type-safe API response wrapper
 */
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
}

/**
 * Utility function for type-safe API calls
 */
export async function apiCall<T = any>(
  method: 'get' | 'post' | 'put' | 'delete' | 'patch',
  url: string,
  data?: any,
  config?: any
): Promise<T> {
  const response = await apiClient[method](url, data, config);
  return response.data;
}

export default apiClient;
