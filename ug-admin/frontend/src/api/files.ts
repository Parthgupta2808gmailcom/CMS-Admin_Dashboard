import { apiClient } from './axios';

export interface StudentFile {
  id: string;
  studentId: string;
  filename: string;
  originalName: string;
  fileType: string;
  fileSize: number;
  uploadedAt: string;
  uploadedBy: string;
  downloadUrl: string;
  metadata?: Record<string, any>;
}

export interface FileUploadResponse {
  file: StudentFile;
  message: string;
}

export const filesApi = {
  // Get files for a specific student
  getStudentFiles: async (studentId: string): Promise<StudentFile[]> => {
    const response = await apiClient.get(`/students/${studentId}/files`);
    return response.data.files || [];
  },

  // Upload file for a student
  uploadFile: async (studentId: string, file: File, metadata?: Record<string, any>): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await apiClient.post(`/students/${studentId}/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Delete a file
  deleteFile: async (studentId: string, fileId: string): Promise<void> => {
    await apiClient.delete(`/students/${studentId}/files/${fileId}`);
  },

  // Get file download URL
  getDownloadUrl: async (studentId: string, fileId: string): Promise<string> => {
    const response = await apiClient.get(`/students/${studentId}/files/${fileId}/download`);
    return response.data.downloadUrl;
  },
};
