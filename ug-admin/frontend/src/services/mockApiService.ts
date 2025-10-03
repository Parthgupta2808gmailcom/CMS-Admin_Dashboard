/**
 * Mock API Service for Development
 * 
 * Intercepts API calls and returns mock data while keeping authentication real
 */

import { mockStudents, mockCampaigns, mockFiles } from '../data/mockData';
import type { StudentsListResponse, StudentResponse } from '../api/students';

// Enable/disable mock mode
const MOCK_MODE = import.meta.env.VITE_MOCK_API === 'true' || import.meta.env.DEV;

export class MockApiService {
  static isMockMode(): boolean {
    return MOCK_MODE;
  }

  // Students API mocks
  static async getStudents(params: any = {}): Promise<StudentsListResponse> {
    await this.delay(300); // Simulate network delay
    
    let filteredStudents = [...mockStudents];
    
    // Apply filters
    if (params.status) {
      filteredStudents = filteredStudents.filter(s => s.application_status === params.status);
    }
    
    if (params.country) {
      filteredStudents = filteredStudents.filter(s => 
        s.country.toLowerCase().includes(params.country.toLowerCase())
      );
    }
    
    if (params.search) {
      const search = params.search.toLowerCase();
      filteredStudents = filteredStudents.filter(s => 
        s.name.toLowerCase().includes(search) || 
        s.email.toLowerCase().includes(search)
      );
    }
    
    // Pagination
    const limit = params.limit || 10;
    const page = params.page || 1;
    const offset = (page - 1) * limit;
    const paginatedStudents = filteredStudents.slice(offset, offset + limit);
    
    return {
      students: paginatedStudents,
      total_count: filteredStudents.length,
      page_info: {
        limit,
        offset,
        current_page: page,
        total_pages: Math.ceil(filteredStudents.length / limit),
        has_next: offset + limit < filteredStudents.length,
        has_previous: page > 1,
      },
      message: 'Students retrieved successfully',
    } as StudentsListResponse;
  }

  static async getStudent(id: string): Promise<StudentResponse> {
    await this.delay(200);
    
    const student = mockStudents.find(s => s.id === id);
    if (!student) {
      throw new Error('Student not found');
    }
    
    return {
      student,
      message: 'Student retrieved successfully',
    } as StudentResponse;
  }

  // Email API mocks
  static async getCampaigns(params: any = {}) {
    await this.delay(250);
    
    const limit = params.limit || 10;
    const offset = params.offset || 0;
    const paginatedCampaigns = mockCampaigns.slice(offset, offset + limit);
    
    return {
      campaigns: paginatedCampaigns,
      total: mockCampaigns.length,
    };
  }

  static async getTemplates() {
    await this.delay(150);
    
    return {
      templates: [
        {
          id: 'welcome-template',
          name: 'Welcome Email',
          subject: 'Welcome to UG Admissions!',
          body: 'Dear {{name}}, welcome to our admissions program...',
          variables: ['name', 'program'],
        },
        {
          id: 'deadline-reminder',
          name: 'Deadline Reminder',
          subject: 'Application Deadline Approaching',
          body: 'Hi {{name}}, your application deadline for {{program}} is {{deadline}}...',
          variables: ['name', 'program', 'deadline'],
        },
      ],
    };
  }

  // Files API mocks
  static async getStudentFiles(studentId: string) {
    await this.delay(200);
    
    const studentFiles = mockFiles.filter(f => f.studentId === studentId);
    return studentFiles;
  }

  // Health check
  static async getHealthCheck() {
    await this.delay(100);
    
    return {
      status: 'ok',
      version: '0.1.0',
      environment: 'development',
      database: {
        status: 'up',
        project_id: 'mock-project',
        collections_count: 3,
      },
    };
  }

  // Utility method to simulate network delay
  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
