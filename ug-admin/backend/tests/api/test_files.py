"""
Tests for file upload and management API endpoints.

This module contains comprehensive tests for file upload functionality
including validation, storage, metadata tracking, and audit logging.
"""

import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from app.main import app
from app.core.auth import UserRole
from app.services.file_storage import StoredFile, FileType, FileStatus, FileUploadResult


class TestFileUploadEndpoint:
    """Test cases for file upload endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.upload_file')
    def test_successful_file_upload(self, mock_upload, mock_get_role, mock_verify_token):
        """Test successful file upload with staff user."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock upload result
        mock_stored_file = StoredFile(
            id="file-123",
            student_id="student-456",
            original_filename="transcript.pdf",
            storage_filename="file-123.pdf",
            file_type=FileType.TRANSCRIPT,
            mime_type="application/pdf",
            file_size=1024000,
            file_hash="abc123def456",
            storage_path="students/student-456/files/file-123.pdf",
            download_url="https://storage.example.com/file-123.pdf",
            status=FileStatus.UPLOADED,
            uploaded_by="staff-123",
            uploaded_at=datetime.utcnow(),
            metadata={"description": "Official transcript"}
        )
        
        mock_upload_result = FileUploadResult(
            file=mock_stored_file,
            upload_time_seconds=2.5,
            validation_results={"valid": True, "errors": [], "warnings": []}
        )
        
        mock_upload.return_value = mock_upload_result
        
        # Create test file
        pdf_content = b"%PDF-1.4 fake pdf content"
        pdf_file = io.BytesIO(pdf_content)
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        files = {"file": ("transcript.pdf", pdf_file, "application/pdf")}
        data = {
            "file_type": "transcript",
            "description": "Official transcript"
        }
        
        response = self.client.post(
            "/api/v1/files/students/student-456/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["file"]["id"] == "file-123"
        assert result["file"]["original_filename"] == "transcript.pdf"
        assert result["file"]["file_type"] == "transcript"
        assert result["upload_time_seconds"] == 2.5
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_upload_requires_staff_or_admin(self, mock_get_role, mock_verify_token):
        """Test that file upload requires staff or admin role."""
        
        # Mock authentication with invalid role
        mock_verify_token.return_value = {"uid": "user-123", "email": "user@test.com"}
        mock_get_role.return_value = None
        
        # Create test file
        test_file = io.BytesIO(b"test content")
        
        headers = {"Authorization": "Bearer invalid-role-token"}
        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "other"}
        
        response = self.client.post(
            "/api/v1/files/students/student-123/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code in [401, 403]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_upload_invalid_student_id(self, mock_get_role, mock_verify_token):
        """Test upload with invalid student ID."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Create test file
        test_file = io.BytesIO(b"test content")
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "other"}
        
        # Invalid student ID (too short)
        response = self.client.post(
            "/api/v1/files/students/ab/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "Invalid student ID format" in result["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.upload_file')
    def test_upload_different_file_types(self, mock_upload, mock_get_role, mock_verify_token):
        """Test uploading different file types."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        file_types_to_test = [
            ("essay", "essay.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("recommendation", "recommendation.pdf", "application/pdf"),
            ("portfolio", "portfolio.jpg", "image/jpeg"),
            ("certificate", "certificate.png", "image/png")
        ]
        
        for file_type, filename, mime_type in file_types_to_test:
            # Mock upload result for each file type
            mock_stored_file = StoredFile(
                id=f"file-{file_type}",
                student_id="student-789",
                original_filename=filename,
                storage_filename=f"file-{file_type}.ext",
                file_type=FileType(file_type),
                mime_type=mime_type,
                file_size=512000,
                file_hash=f"hash-{file_type}",
                storage_path=f"students/student-789/files/file-{file_type}.ext",
                download_url=f"https://storage.example.com/file-{file_type}.ext",
                status=FileStatus.UPLOADED,
                uploaded_by="admin-123",
                uploaded_at=datetime.utcnow(),
                metadata={}
            )
            
            mock_upload_result = FileUploadResult(
                file=mock_stored_file,
                upload_time_seconds=1.0,
                validation_results={"valid": True, "errors": [], "warnings": []}
            )
            
            mock_upload.return_value = mock_upload_result
            
            # Create test file
            test_content = b"test file content"
            test_file = io.BytesIO(test_content)
            
            headers = {"Authorization": "Bearer valid-admin-token"}
            files = {"file": (filename, test_file, mime_type)}
            data = {"file_type": file_type}
            
            response = self.client.post(
                "/api/v1/files/students/student-789/upload",
                headers=headers,
                files=files,
                data=data
            )
            
            assert response.status_code == 201
            result = response.json()
            assert result["success"] is True
            assert result["file"]["file_type"] == file_type
            assert result["file"]["original_filename"] == filename


class TestFileListingEndpoint:
    """Test cases for file listing endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.get_student_files')
    def test_list_student_files(self, mock_get_files, mock_get_role, mock_verify_token):
        """Test listing all files for a student."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock files
        mock_files = [
            StoredFile(
                id="file-1",
                student_id="student-123",
                original_filename="transcript.pdf",
                storage_filename="file-1.pdf",
                file_type=FileType.TRANSCRIPT,
                mime_type="application/pdf",
                file_size=1024000,
                file_hash="hash1",
                storage_path="students/student-123/files/file-1.pdf",
                download_url="https://storage.example.com/file-1.pdf",
                status=FileStatus.UPLOADED,
                uploaded_by="staff-123",
                uploaded_at=datetime.utcnow(),
                metadata={}
            ),
            StoredFile(
                id="file-2",
                student_id="student-123",
                original_filename="essay.docx",
                storage_filename="file-2.docx",
                file_type=FileType.ESSAY,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                file_size=512000,
                file_hash="hash2",
                storage_path="students/student-123/files/file-2.docx",
                download_url="https://storage.example.com/file-2.docx",
                status=FileStatus.UPLOADED,
                uploaded_by="admin-456",
                uploaded_at=datetime.utcnow(),
                metadata={}
            )
        ]
        
        mock_get_files.return_value = mock_files
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        
        response = self.client.get("/api/v1/files/students/student-123", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["files"]) == 2
        assert result["total_count"] == 2
        assert result["files"][0]["file_type"] == "transcript"
        assert result["files"][1]["file_type"] == "essay"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.get_student_files')
    def test_list_files_with_type_filter(self, mock_get_files, mock_get_role, mock_verify_token):
        """Test listing files with file type filter."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock filtered files (only transcripts)
        mock_files = [
            StoredFile(
                id="file-1",
                student_id="student-456",
                original_filename="transcript.pdf",
                storage_filename="file-1.pdf",
                file_type=FileType.TRANSCRIPT,
                mime_type="application/pdf",
                file_size=1024000,
                file_hash="hash1",
                storage_path="students/student-456/files/file-1.pdf",
                download_url="https://storage.example.com/file-1.pdf",
                status=FileStatus.UPLOADED,
                uploaded_by="admin-123",
                uploaded_at=datetime.utcnow(),
                metadata={}
            )
        ]
        
        mock_get_files.return_value = mock_files
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        params = {"file_type": "transcript"}
        
        response = self.client.get("/api/v1/files/students/student-456", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["files"]) == 1
        assert result["files"][0]["file_type"] == "transcript"
        
        # Verify the service was called with the filter
        mock_get_files.assert_called_once()
        call_args = mock_get_files.call_args
        assert call_args[1]["file_type"] == FileType.TRANSCRIPT
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.get_student_files')
    def test_list_files_empty_result(self, mock_get_files, mock_get_role, mock_verify_token):
        """Test listing files when student has no files."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock empty result
        mock_get_files.return_value = []
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        
        response = self.client.get("/api/v1/files/students/student-empty", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["files"]) == 0
        assert result["total_count"] == 0


class TestFileDetailsEndpoint:
    """Test cases for file details endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.get_file_by_id')
    def test_get_file_details(self, mock_get_file, mock_get_role, mock_verify_token):
        """Test getting detailed file information."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock file details
        mock_file = StoredFile(
            id="file-details-123",
            student_id="student-789",
            original_filename="recommendation.pdf",
            storage_filename="file-details-123.pdf",
            file_type=FileType.RECOMMENDATION,
            mime_type="application/pdf",
            file_size=2048000,
            file_hash="detailed-hash",
            storage_path="students/student-789/files/file-details-123.pdf",
            download_url="https://storage.example.com/file-details-123.pdf",
            status=FileStatus.UPLOADED,
            uploaded_by="admin-456",
            uploaded_at=datetime.utcnow(),
            metadata={"description": "Teacher recommendation letter", "teacher": "Prof. Smith"}
        )
        
        mock_get_file.return_value = mock_file
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        
        response = self.client.get("/api/v1/files/file-details-123", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "file-details-123"
        assert result["student_id"] == "student-789"
        assert result["original_filename"] == "recommendation.pdf"
        assert result["file_type"] == "recommendation"
        assert result["file_size"] == 2048000
        assert result["metadata"]["description"] == "Teacher recommendation letter"
        assert result["metadata"]["teacher"] == "Prof. Smith"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.get_file_by_id')
    def test_get_file_details_not_found(self, mock_get_file, mock_get_role, mock_verify_token):
        """Test getting details for non-existent file."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock file not found
        mock_get_file.return_value = None
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        
        response = self.client.get("/api/v1/files/nonexistent-file", headers=headers)
        
        assert response.status_code == 404
        result = response.json()
        assert "File not found" in result["message"]
        assert result["file_id"] == "nonexistent-file"


class TestFileDeleteEndpoint:
    """Test cases for file deletion endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.delete_file')
    def test_successful_file_deletion(self, mock_delete, mock_get_role, mock_verify_token):
        """Test successful file deletion."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock successful deletion
        mock_delete.return_value = True
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        
        response = self.client.delete("/api/v1/files/file-to-delete", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.delete_file')
    def test_delete_file_not_found(self, mock_delete, mock_get_role, mock_verify_token):
        """Test deleting non-existent file."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock deletion failure (file not found)
        mock_delete.return_value = False
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        
        response = self.client.delete("/api/v1/files/nonexistent-file", headers=headers)
        
        assert response.status_code == 404
        result = response.json()
        assert "File not found" in result["message"]


class TestStorageStatisticsEndpoint:
    """Test cases for storage statistics endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.file_storage.file_storage_service.get_storage_statistics')
    def test_get_storage_statistics(self, mock_get_stats, mock_get_role, mock_verify_token):
        """Test getting storage usage statistics."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock statistics
        mock_stats = {
            "total_files": 150,
            "total_size_bytes": 104857600,  # 100 MB
            "files_by_type": {
                "transcript": 45,
                "essay": 38,
                "recommendation": 32,
                "portfolio": 20,
                "certificate": 15
            },
            "files_by_status": {
                "uploaded": 140,
                "processing": 5,
                "ready": 135,
                "error": 3,
                "deleted": 7
            },
            "average_file_size": 699050.67,
            "largest_file_size": 5242880,  # 5 MB
            "generated_at": "2025-01-01T12:00:00Z"
        }
        
        mock_get_stats.return_value = mock_stats
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        
        response = self.client.get("/api/v1/files/storage/statistics", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["statistics"]["total_files"] == 150
        assert result["statistics"]["total_size_bytes"] == 104857600
        assert result["statistics"]["files_by_type"]["transcript"] == 45
        assert result["statistics"]["files_by_status"]["uploaded"] == 140
        assert result["statistics"]["average_file_size"] == 699050.67
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_statistics_requires_authentication(self, mock_get_role, mock_verify_token):
        """Test that statistics endpoint requires authentication."""
        
        # No authentication header
        response = self.client.get("/api/v1/files/storage/statistics")
        
        assert response.status_code == 403
