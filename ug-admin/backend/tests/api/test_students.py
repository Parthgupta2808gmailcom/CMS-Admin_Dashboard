"""
Integration tests for student API endpoints.

This module provides comprehensive testing for all student CRUD operations,
including happy paths, error cases, validation, and edge cases.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.errors import AppError, NotFoundError, ValidationError
from app.schemas.student import Student, StudentCreate, StudentUpdate, ApplicationStatus


class TestStudentEndpoints:
    """Test suite for student CRUD endpoints."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = TestClient(app)
        
        # Sample student data for testing
        self.sample_student_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "country": "USA",
            "grade": "12th",
            "application_status": "Exploring"
        }
        
        self.sample_student = Student(
            id="test-student-id",
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            country="USA",
            grade="12th",
            application_status=ApplicationStatus.EXPLORING,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            last_active="2023-01-01T00:00:00Z"
        )
    
    @patch('app.services.students.student_service.create_student')
    def test_create_student_success(self, mock_create):
        """Test successful student creation."""
        # Mock service response
        mock_create.return_value = self.sample_student
        
        # Make request
        response = self.client.post("/api/v1/students/", json=self.sample_student_data)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        
        assert data["message"] == "Student created successfully"
        assert "student" in data
        assert data["student"]["id"] == "test-student-id"
        assert data["student"]["name"] == "John Doe"
        assert data["student"]["email"] == "john.doe@example.com"
        
        # Verify service was called
        mock_create.assert_called_once()
    
    @patch('app.services.students.student_service.create_student')
    def test_create_student_validation_error(self, mock_create):
        """Test student creation with validation error."""
        # Mock service to raise validation error
        mock_create.side_effect = ValidationError(
            message="Invalid email format",
            details={"field": "email", "value": "invalid-email"}
        )
        
        # Make request with invalid data
        invalid_data = self.sample_student_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = self.client.post("/api/v1/students/", json=invalid_data)
        
        # Verify error response
        assert response.status_code == 400
        data = response.json()
        
        assert data["detail"]["error"] == "Validation failed"
        assert "Invalid email format" in data["detail"]["message"]
    
    @patch('app.services.students.student_service.create_student')
    def test_create_student_server_error(self, mock_create):
        """Test student creation with server error."""
        # Mock service to raise app error
        mock_create.side_effect = AppError(
            message="Database connection failed",
            code="INTERNAL"
        )
        
        # Make request
        response = self.client.post("/api/v1/students/", json=self.sample_student_data)
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        
        assert data["detail"]["error"] == "Internal server error"
        assert data["detail"]["message"] == "Failed to create student"
    
    @patch('app.services.students.student_service.list_students')
    def test_list_students_success(self, mock_list):
        """Test successful student listing."""
        from app.schemas.student import StudentListResponse
        
        # Mock service response
        mock_response = StudentListResponse(
            students=[self.sample_student],
            total_count=1,
            page=1,
            page_size=50,
            has_next=False
        )
        mock_list.return_value = mock_response
        
        # Make request
        response = self.client.get("/api/v1/students/")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Retrieved 1 students"
        assert len(data["students"]) == 1
        assert data["students"][0]["id"] == "test-student-id"
        assert data["total_count"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert data["has_next"] is False
    
    @patch('app.services.students.student_service.list_students')
    def test_list_students_with_filters(self, mock_list):
        """Test student listing with filters."""
        from app.schemas.student import StudentListResponse
        
        # Mock service response
        mock_response = StudentListResponse(
            students=[self.sample_student],
            total_count=1,
            page=1,
            page_size=10,
            has_next=False
        )
        mock_list.return_value = mock_response
        
        # Make request with filters
        response = self.client.get(
            "/api/v1/students/",
            params={
                "page": 1,
                "page_size": 10,
                "name": "John",
                "email": "john",
                "status": "Exploring",
                "order_by": "name",
                "order_direction": "asc"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["students"]) == 1
        assert data["page_size"] == 10
        
        # Verify service was called with correct parameters
        mock_list.assert_called_once_with(
            page=1,
            page_size=10,
            name_filter="John",
            email_filter="john",
            status_filter=ApplicationStatus.EXPLORING,
            order_by="name",
            order_direction="asc"
        )
    
    @patch('app.services.students.student_service.list_students')
    def test_list_students_validation_error(self, mock_list):
        """Test student listing with validation error."""
        # Mock service to raise validation error
        mock_list.side_effect = ValidationError(
            message="Page number must be 1 or greater",
            details={"field": "page", "value": 0}
        )
        
        # Make request with invalid page
        response = self.client.get("/api/v1/students/", params={"page": 0})
        
        # Verify error response
        assert response.status_code == 400
        data = response.json()
        
        assert data["detail"]["error"] == "Validation failed"
        assert "Page number must be 1 or greater" in data["detail"]["message"]
    
    @patch('app.services.students.student_service.get_student_by_id')
    def test_get_student_success(self, mock_get):
        """Test successful student retrieval by ID."""
        # Mock service response
        mock_get.return_value = self.sample_student
        
        # Make request
        response = self.client.get("/api/v1/students/test-student-id")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Student retrieved successfully"
        assert data["student"]["id"] == "test-student-id"
        assert data["student"]["name"] == "John Doe"
        
        # Verify service was called
        mock_get.assert_called_once_with("test-student-id")
    
    @patch('app.services.students.student_service.get_student_by_id')
    def test_get_student_not_found(self, mock_get):
        """Test student retrieval with not found error."""
        # Mock service to raise not found error
        mock_get.side_effect = NotFoundError(
            message="Student not found: nonexistent-id",
            details={"student_id": "nonexistent-id"}
        )
        
        # Make request
        response = self.client.get("/api/v1/students/nonexistent-id")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        
        assert data["detail"]["error"] == "Student not found"
        assert "nonexistent-id" in data["detail"]["message"]
        assert data["detail"]["student_id"] == "nonexistent-id"
    
    @patch('app.services.students.student_service.update_student')
    def test_update_student_success(self, mock_update):
        """Test successful student update."""
        # Create updated student
        updated_student = self.sample_student.copy()
        updated_student.name = "Jane Doe"
        updated_student.email = "jane.doe@example.com"
        
        # Mock service response
        mock_update.return_value = updated_student
        
        # Make request
        update_data = {"name": "Jane Doe", "email": "jane.doe@example.com"}
        response = self.client.put("/api/v1/students/test-student-id", json=update_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Student updated successfully"
        assert data["student"]["name"] == "Jane Doe"
        assert data["student"]["email"] == "jane.doe@example.com"
        
        # Verify service was called
        mock_update.assert_called_once()
    
    @patch('app.services.students.student_service.update_student')
    def test_update_student_not_found(self, mock_update):
        """Test student update with not found error."""
        # Mock service to raise not found error
        mock_update.side_effect = NotFoundError(
            message="Student not found: nonexistent-id",
            details={"student_id": "nonexistent-id"}
        )
        
        # Make request
        update_data = {"name": "Jane Doe"}
        response = self.client.put("/api/v1/students/nonexistent-id", json=update_data)
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        
        assert data["detail"]["error"] == "Student not found"
        assert "nonexistent-id" in data["detail"]["message"]
    
    @patch('app.services.students.student_service.update_student')
    def test_update_student_validation_error(self, mock_update):
        """Test student update with validation error."""
        # Mock service to raise validation error
        mock_update.side_effect = ValidationError(
            message="At least one field must be provided for update",
            details={"update_data": {}}
        )
        
        # Make request with empty update data
        response = self.client.put("/api/v1/students/test-student-id", json={})
        
        # Verify error response
        assert response.status_code == 400
        data = response.json()
        
        assert data["detail"]["error"] == "Validation failed"
        assert "At least one field must be provided" in data["detail"]["message"]
    
    @patch('app.services.students.student_service.delete_student')
    def test_delete_student_success(self, mock_delete):
        """Test successful student deletion."""
        # Mock service response
        mock_delete.return_value = True
        
        # Make request
        response = self.client.delete("/api/v1/students/test-student-id")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Student deleted successfully"
        assert data["student_id"] == "test-student-id"
        
        # Verify service was called
        mock_delete.assert_called_once_with("test-student-id")
    
    @patch('app.services.students.student_service.delete_student')
    def test_delete_student_not_found(self, mock_delete):
        """Test student deletion with not found error."""
        # Mock service to raise not found error
        mock_delete.side_effect = NotFoundError(
            message="Student not found: nonexistent-id",
            details={"student_id": "nonexistent-id"}
        )
        
        # Make request
        response = self.client.delete("/api/v1/students/nonexistent-id")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        
        assert data["detail"]["error"] == "Student not found"
        assert "nonexistent-id" in data["detail"]["message"]
    
    def test_create_student_invalid_json(self):
        """Test student creation with invalid JSON."""
        # Make request with invalid JSON
        response = self.client.post(
            "/api/v1/students/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Verify error response
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_list_students_invalid_query_params(self):
        """Test student listing with invalid query parameters."""
        # Make request with invalid parameters
        response = self.client.get(
            "/api/v1/students/",
            params={
                "page": -1,
                "page_size": 200,  # Exceeds maximum
                "order_direction": "invalid"
            }
        )
        
        # Verify error response
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.asyncio
    @patch('app.services.students.student_service.create_student')
    async def test_create_student_async_client(self, mock_create):
        """Test student creation using async client."""
        # Mock service response
        mock_create.return_value = self.sample_student
        
        # Make async request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/students/", json=self.sample_student_data)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            
            assert data["message"] == "Student created successfully"
            assert data["student"]["id"] == "test-student-id"
    
    @pytest.mark.asyncio
    @patch('app.services.students.student_service.list_students')
    async def test_list_students_async_client(self, mock_list):
        """Test student listing using async client."""
        from app.schemas.student import StudentListResponse
        
        # Mock service response
        mock_response = StudentListResponse(
            students=[self.sample_student],
            total_count=1,
            page=1,
            page_size=50,
            has_next=False
        )
        mock_list.return_value = mock_response
        
        # Make async request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/students/")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["students"]) == 1
            assert data["students"][0]["id"] == "test-student-id"


class TestStudentEndpointsIntegration:
    """Integration tests for student endpoints with real service layer."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = TestClient(app)
    
    def test_endpoints_response_headers(self):
        """Test that student endpoints include proper headers."""
        with patch('app.services.students.student_service.list_students') as mock_list:
            from app.schemas.student import StudentListResponse
            
            mock_response = StudentListResponse(
                students=[],
                total_count=0,
                page=1,
                page_size=50,
                has_next=False
            )
            mock_list.return_value = mock_response
            
            response = self.client.get("/api/v1/students/")
            
            # Verify headers
            assert "X-Request-ID" in response.headers
            assert response.headers["content-type"] == "application/json"
    
    def test_endpoints_content_type(self):
        """Test that student endpoints return proper content type."""
        with patch('app.services.students.student_service.list_students') as mock_list:
            from app.schemas.student import StudentListResponse
            
            mock_response = StudentListResponse(
                students=[],
                total_count=0,
                page=1,
                page_size=50,
                has_next=False
            )
            mock_list.return_value = mock_response
            
            response = self.client.get("/api/v1/students/")
            
            # Verify content type
            assert response.headers["content-type"] == "application/json"
    
    def test_all_endpoints_exist(self):
        """Test that all expected endpoints are accessible."""
        # This test verifies that the routing is set up correctly
        # We expect 422 (validation error) or 500 (service error), not 404 (not found)
        
        endpoints = [
            ("POST", "/api/v1/students/"),
            ("GET", "/api/v1/students/"),
            ("GET", "/api/v1/students/test-id"),
            ("PUT", "/api/v1/students/test-id"),
            ("DELETE", "/api/v1/students/test-id")
        ]
        
        for method, endpoint in endpoints:
            if method == "POST":
                response = self.client.post(endpoint, json={})
            elif method == "PUT":
                response = self.client.put(endpoint, json={})
            else:
                response = self.client.request(method, endpoint)
            
            # Should not be 404 (not found) - endpoint should exist
            assert response.status_code != 404, f"Endpoint {method} {endpoint} not found"
