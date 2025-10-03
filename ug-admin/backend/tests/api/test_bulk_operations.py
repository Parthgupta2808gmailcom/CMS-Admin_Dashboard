"""
Tests for bulk operations API endpoints.

This module contains comprehensive tests for bulk import/export functionality
including file validation, error handling, and audit logging verification.
"""

import pytest
import io
import csv
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app
from app.core.auth import UserRole
from app.services.bulk_operations import ImportResult, ExportResult, ImportFormat, ExportFormat


class TestBulkImportEndpoint:
    """Test cases for bulk import endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.bulk_operations.bulk_operations_service.import_students_from_file')
    def test_successful_csv_import(self, mock_import, mock_get_role, mock_verify_token):
        """Test successful CSV import with admin user."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock import result
        mock_import.return_value = ImportResult(
            total_rows=3,
            successful_imports=3,
            failed_imports=0,
            errors=[],
            created_student_ids=["student1", "student2", "student3"],
            processing_time_seconds=1.5
        )
        
        # Create CSV content
        csv_content = """name,email,country,application_status
John Doe,john@test.com,USA,Exploring
Jane Smith,jane@test.com,Canada,Shortlisting
Bob Wilson,bob@test.com,UK,Applying"""
        
        # Create file-like object
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        files = {"file": ("students.csv", csv_file, "text/csv")}
        data = {"format_type": "csv", "validate_only": False}
        
        response = self.client.post("/api/v1/bulk/import", headers=headers, files=files, data=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["import_result"]["total_rows"] == 3
        assert result["import_result"]["successful_imports"] == 3
        assert result["import_result"]["failed_imports"] == 0
        assert len(result["import_result"]["created_student_ids"]) == 3
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_import_requires_admin_role(self, mock_get_role, mock_verify_token):
        """Test that import endpoint requires admin role."""
        
        # Mock authentication with staff user
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        csv_content = "name,email,country\nTest User,test@test.com,USA"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        files = {"file": ("students.csv", csv_file, "text/csv")}
        
        response = self.client.post("/api/v1/bulk/import", headers=headers, files=files)
        
        assert response.status_code == 403
        result = response.json()
        assert "Insufficient permissions" in result["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.bulk_operations.bulk_operations_service.import_students_from_file')
    def test_import_with_validation_errors(self, mock_import, mock_get_role, mock_verify_token):
        """Test import with validation errors."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock import result with errors
        mock_import.return_value = ImportResult(
            total_rows=3,
            successful_imports=2,
            failed_imports=1,
            errors=[
                {
                    "row_number": 2,
                    "row_data": {"name": "", "email": "invalid-email", "country": "USA"},
                    "error_type": "ValidationError",
                    "error_message": "Student data validation failed",
                    "field_errors": {"name": "Field required", "email": "Invalid email format"}
                }
            ],
            created_student_ids=["student1", "student3"],
            processing_time_seconds=1.2
        )
        
        csv_content = """name,email,country
John Doe,john@test.com,USA
,invalid-email,USA
Jane Smith,jane@test.com,Canada"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        files = {"file": ("students.csv", csv_file, "text/csv")}
        
        response = self.client.post("/api/v1/bulk/import", headers=headers, files=files)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is False  # Has errors
        assert result["import_result"]["successful_imports"] == 2
        assert result["import_result"]["failed_imports"] == 1
        assert len(result["import_result"]["errors"]) == 1
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_import_empty_file_validation(self, mock_get_role, mock_verify_token):
        """Test validation of empty file upload."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Create empty file
        empty_file = io.BytesIO(b"")
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        files = {"file": ("empty.csv", empty_file, "text/csv")}
        
        response = self.client.post("/api/v1/bulk/import", headers=headers, files=files)
        
        assert response.status_code == 400
        result = response.json()
        assert "empty" in result["message"].lower()
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.bulk_operations.bulk_operations_service.import_students_from_file')
    def test_validate_only_mode(self, mock_import, mock_get_role, mock_verify_token):
        """Test validate-only mode that doesn't create students."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock import result for validation only
        mock_import.return_value = ImportResult(
            total_rows=2,
            successful_imports=2,
            failed_imports=0,
            errors=[],
            created_student_ids=[],  # No students created in validation mode
            processing_time_seconds=0.5
        )
        
        csv_content = """name,email,country
John Doe,john@test.com,USA
Jane Smith,jane@test.com,Canada"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        files = {"file": ("students.csv", csv_file, "text/csv")}
        data = {"validate_only": True}
        
        response = self.client.post("/api/v1/bulk/import", headers=headers, files=files, data=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert "validation successful" in result["message"].lower()
        assert len(result["import_result"]["created_student_ids"]) == 0


class TestBulkExportEndpoint:
    """Test cases for bulk export endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.bulk_operations.bulk_operations_service.export_students')
    def test_successful_csv_export(self, mock_export, mock_get_role, mock_verify_token):
        """Test successful CSV export with staff user."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock export result
        csv_content = b"id,name,email,country\nstudent1,John Doe,john@test.com,USA\nstudent2,Jane Smith,jane@test.com,Canada"
        export_result = ExportResult(
            total_students=2,
            export_format=ExportFormat.CSV,
            file_size_bytes=len(csv_content),
            processing_time_seconds=0.8,
            filters_applied={}
        )
        
        mock_export.return_value = (csv_content, export_result)
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        params = {"format_type": "csv"}
        
        response = self.client.get("/api/v1/bulk/export", headers=headers, params=params)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "students_export_2_records.csv" in response.headers["content-disposition"]
        assert response.content == csv_content
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.bulk_operations.bulk_operations_service.export_students')
    def test_json_export_with_filters(self, mock_export, mock_get_role, mock_verify_token):
        """Test JSON export with filtering parameters."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock export result
        json_content = json.dumps({
            "students": [{"id": "student1", "name": "John Doe", "email": "john@test.com"}],
            "export_info": {"total_count": 1, "exported_at": "2025-01-01T12:00:00"}
        }).encode('utf-8')
        
        export_result = ExportResult(
            total_students=1,
            export_format=ExportFormat.JSON,
            file_size_bytes=len(json_content),
            processing_time_seconds=0.5,
            filters_applied={"application_status": "Exploring", "country": "USA"}
        )
        
        mock_export.return_value = (json_content, export_result)
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        params = {
            "format_type": "json",
            "application_status": "Exploring",
            "country": "USA",
            "include_fields": "id,name,email"
        }
        
        response = self.client.get("/api/v1/bulk/export", headers=headers, params=params)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        assert "students_export_1_records.json" in response.headers["content-disposition"]
        
        # Verify export was called with correct filters
        mock_export.assert_called_once()
        call_args = mock_export.call_args
        assert call_args[1]["filters"]["application_status"] == "Exploring"
        assert call_args[1]["filters"]["country"] == "USA"
        assert call_args[1]["include_fields"] == ["id", "name", "email"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_export_requires_staff_or_admin(self, mock_get_role, mock_verify_token):
        """Test that export endpoint requires staff or admin role."""
        
        # Mock authentication failure (no role)
        mock_verify_token.return_value = {"uid": "user-123", "email": "user@test.com"}
        mock_get_role.return_value = None
        
        headers = {"Authorization": "Bearer invalid-role-token"}
        
        response = self.client.get("/api/v1/bulk/export", headers=headers)
        
        # Should fail due to authentication/authorization
        assert response.status_code in [401, 403]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.bulk_operations.bulk_operations_service.export_students')
    def test_export_with_date_filters(self, mock_export, mock_get_role, mock_verify_token):
        """Test export with date range filtering."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock export result
        csv_content = b"id,name,email,last_active\nstudent1,John Doe,john@test.com,2025-01-01"
        export_result = ExportResult(
            total_students=1,
            export_format=ExportFormat.CSV,
            file_size_bytes=len(csv_content),
            processing_time_seconds=0.3,
            filters_applied={"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        
        mock_export.return_value = (csv_content, export_result)
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        params = {
            "format_type": "csv",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        }
        
        response = self.client.get("/api/v1/bulk/export", headers=headers, params=params)
        
        assert response.status_code == 200
        
        # Verify export was called with date filters
        mock_export.assert_called_once()
        call_args = mock_export.call_args
        assert call_args[1]["filters"]["start_date"] == "2025-01-01"
        assert call_args[1]["filters"]["end_date"] == "2025-01-31"
