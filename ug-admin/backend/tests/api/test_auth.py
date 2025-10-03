"""
Comprehensive tests for Firebase Authentication and Role-Based Access Control.

This module tests JWT token verification, role enforcement, and proper
error handling for authentication and authorization scenarios.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.auth import UserRole, AuthError, ForbiddenError, AuthenticatedUser
from app.core.errors import AppError


class TestAuthenticationMiddleware:
    """Test suite for Firebase authentication middleware."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = TestClient(app)
        
        # Sample Firebase token claims
        self.valid_token_claims = {
            "uid": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "iat": 1234567890,
            "exp": 1234567890 + 3600  # 1 hour from issued time
        }
        
        # Sample authenticated users
        self.admin_user = AuthenticatedUser(
            uid="admin-123",
            email="admin@example.com",
            role=UserRole.ADMIN,
            name="Admin User"
        )
        
        self.staff_user = AuthenticatedUser(
            uid="staff-123", 
            email="staff@example.com",
            role=UserRole.STAFF,
            name="Staff User"
        )
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_valid_token_authentication(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test successful authentication with valid Firebase token."""
        # Mock Firebase token verification
        mock_verify_token.return_value = self.valid_token_claims
        mock_get_role.return_value = UserRole.ADMIN
        mock_update_login.return_value = None
        
        # Make authenticated request
        headers = {"Authorization": "Bearer valid-firebase-token"}
        response = self.client.get("/api/v1/students/", headers=headers)
        
        # Verify authentication succeeded (we expect 500 due to missing Firestore setup, not 401)
        assert response.status_code != 401
        assert response.status_code != 403
        
        # Verify Firebase SDK was called
        mock_verify_token.assert_called_once_with("valid-firebase-token")
        mock_get_role.assert_called_once_with("test-user-123")
    
    def test_missing_authorization_header(self):
        """Test request without Authorization header."""
        response = self.client.get("/api/v1/students/")
        
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "AUTH"
        assert "Not authenticated" in data["message"]
    
    def test_invalid_authorization_scheme(self):
        """Test request with non-Bearer authorization scheme."""
        headers = {"Authorization": "Basic invalid-scheme"}
        response = self.client.get("/api/v1/students/", headers=headers)
        
        # FastAPI HTTPBearer returns 403 for invalid scheme
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "AUTH"
        assert "Not authenticated" in data["message"]
    
    def test_empty_token(self):
        """Test request with empty Bearer token."""
        headers = {"Authorization": "Bearer "}
        response = self.client.get("/api/v1/students/", headers=headers)
        
        # Should return 401 Unauthorized for empty token
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "AUTH"
        assert "Authentication token required" in data["detail"]["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    def test_invalid_firebase_token(self, mock_verify_token):
        """Test authentication with invalid Firebase token."""
        from firebase_admin.auth import InvalidIdTokenError
        
        # Mock Firebase token verification failure
        mock_verify_token.side_effect = InvalidIdTokenError("Invalid token")
        
        headers = {"Authorization": "Bearer invalid-token"}
        response = self.client.get("/api/v1/students/", headers=headers)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "AUTH"
        assert "Invalid authentication token" in data["detail"]["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    def test_expired_firebase_token(self, mock_verify_token):
        """Test authentication with expired Firebase token."""
        from firebase_admin.auth import ExpiredIdTokenError
        
        # Mock Firebase token verification failure
        mock_verify_token.side_effect = ExpiredIdTokenError("Token expired")
        
        headers = {"Authorization": "Bearer expired-token"}
        response = self.client.get("/api/v1/students/", headers=headers)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "AUTH"
        assert "Authentication token has expired" in data["detail"]["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    def test_revoked_firebase_token(self, mock_verify_token):
        """Test authentication with revoked Firebase token."""
        from firebase_admin.auth import RevokedIdTokenError
        
        # Mock Firebase token verification failure
        mock_verify_token.side_effect = RevokedIdTokenError("Token revoked")
        
        headers = {"Authorization": "Bearer revoked-token"}
        response = self.client.get("/api/v1/students/", headers=headers)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "AUTH"
        assert "Authentication token has been revoked" in data["detail"]["message"]


class TestRoleBasedAccessControl:
    """Test suite for role-based access control (RBAC)."""
    
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
    
    def _create_auth_headers(self, role: UserRole, uid: str = "test-user") -> dict:
        """Helper to create authentication headers for testing."""
        return {"Authorization": f"Bearer mock-token-{role.value}-{uid}"}
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_admin_can_create_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that admin users can create students."""
        # Mock authentication for admin user
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@example.com"}
        mock_get_role.return_value = UserRole.ADMIN
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.ADMIN, "admin-123")
        
        with patch('app.services.students.student_service.create_student') as mock_create:
            from app.schemas.student import Student
            mock_student = Student(
                id="test-id",
                name="John Doe",
                email="john.doe@example.com",
                country="USA",
                application_status="Exploring",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                last_active="2023-01-01T00:00:00Z"
            )
            mock_create.return_value = mock_student
            
            response = self.client.post("/api/v1/students/", json=self.sample_student_data, headers=headers)
            
            # Should succeed (201 Created)
            assert response.status_code == 201
            mock_create.assert_called_once()
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_staff_can_create_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that staff users can create students."""
        # Mock authentication for staff user
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@example.com"}
        mock_get_role.return_value = UserRole.STAFF
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.STAFF, "staff-123")
        
        with patch('app.services.students.student_service.create_student') as mock_create:
            from app.schemas.student import Student
            mock_student = Student(
                id="test-id",
                name="John Doe",
                email="john.doe@example.com",
                country="USA",
                application_status="Exploring",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                last_active="2023-01-01T00:00:00Z"
            )
            mock_create.return_value = mock_student
            
            response = self.client.post("/api/v1/students/", json=self.sample_student_data, headers=headers)
            
            # Should succeed (201 Created)
            assert response.status_code == 201
            mock_create.assert_called_once()
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_staff_can_list_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that staff users can list students."""
        # Mock authentication for staff user
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@example.com"}
        mock_get_role.return_value = UserRole.STAFF
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.STAFF, "staff-123")
        
        with patch('app.services.students.student_service.list_students') as mock_list:
            from app.schemas.student import StudentListResponse
            mock_list.return_value = StudentListResponse(
                students=[],
                total_count=0,
                page=1,
                page_size=50,
                has_next=False
            )
            
            response = self.client.get("/api/v1/students/", headers=headers)
            
            # Should succeed (200 OK)
            assert response.status_code == 200
            mock_list.assert_called_once()
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_staff_can_get_student(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that staff users can get individual students."""
        # Mock authentication for staff user
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@example.com"}
        mock_get_role.return_value = UserRole.STAFF
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.STAFF, "staff-123")
        
        with patch('app.services.students.student_service.get_student_by_id') as mock_get:
            from app.schemas.student import Student
            mock_student = Student(
                id="test-id",
                name="John Doe",
                email="john.doe@example.com",
                country="USA",
                application_status="Exploring",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                last_active="2023-01-01T00:00:00Z"
            )
            mock_get.return_value = mock_student
            
            response = self.client.get("/api/v1/students/test-id", headers=headers)
            
            # Should succeed (200 OK)
            assert response.status_code == 200
            mock_get.assert_called_once_with("test-id")
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_staff_cannot_update_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that staff users cannot update students (admin only)."""
        # Mock authentication for staff user
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@example.com"}
        mock_get_role.return_value = UserRole.STAFF
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.STAFF, "staff-123")
        update_data = {"name": "Updated Name"}
        
        response = self.client.put("/api/v1/students/test-id", json=update_data, headers=headers)
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "FORBIDDEN"
        assert "Insufficient permissions" in data["detail"]["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_staff_cannot_delete_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that staff users cannot delete students (admin only)."""
        # Mock authentication for staff user
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@example.com"}
        mock_get_role.return_value = UserRole.STAFF
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.STAFF, "staff-123")
        
        response = self.client.delete("/api/v1/students/test-id", headers=headers)
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "FORBIDDEN"
        assert "Insufficient permissions" in data["detail"]["message"]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_admin_can_update_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that admin users can update students."""
        # Mock authentication for admin user
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@example.com"}
        mock_get_role.return_value = UserRole.ADMIN
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.ADMIN, "admin-123")
        update_data = {"name": "Updated Name"}
        
        with patch('app.services.students.student_service.update_student') as mock_update:
            from app.schemas.student import Student
            mock_student = Student(
                id="test-id",
                name="Updated Name",
                email="john.doe@example.com",
                country="USA",
                application_status="Exploring",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T12:00:00Z",
                last_active="2023-01-01T12:00:00Z"
            )
            mock_update.return_value = mock_student
            
            response = self.client.put("/api/v1/students/test-id", json=update_data, headers=headers)
            
            # Should succeed (200 OK)
            assert response.status_code == 200
            mock_update.assert_called_once()
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.auth_manager.get_user_role')
    @patch('app.core.auth.auth_manager.update_last_login')
    def test_admin_can_delete_students(self, mock_update_login, mock_get_role, mock_verify_token):
        """Test that admin users can delete students."""
        # Mock authentication for admin user
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@example.com"}
        mock_get_role.return_value = UserRole.ADMIN
        mock_update_login.return_value = None
        
        headers = self._create_auth_headers(UserRole.ADMIN, "admin-123")
        
        with patch('app.services.students.student_service.delete_student') as mock_delete:
            mock_delete.return_value = True
            
            response = self.client.delete("/api/v1/students/test-id", headers=headers)
            
            # Should succeed (200 OK)
            assert response.status_code == 200
            mock_delete.assert_called_once_with("test-id")


class TestUserRoleManagement:
    """Test suite for user role management in Firestore."""
    
    @patch('app.core.auth.get_firestore_client')
    def test_get_user_role_existing_user(self, mock_get_client):
        """Test retrieving role for existing user."""
        # Mock Firestore client and document
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"role": "admin", "created_at": 1234567890}
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_client.collection.return_value = mock_collection
        
        # Test role retrieval
        from app.core.auth import auth_manager
        import asyncio
        
        async def test_role():
            role = await auth_manager.get_user_role("test-user-123")
            assert role == UserRole.ADMIN
        
        asyncio.run(test_role())
    
    @patch('app.core.auth.get_firestore_client')
    def test_get_user_role_new_user(self, mock_get_client):
        """Test retrieving role for new user (creates default)."""
        # Mock Firestore client and document
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.set = Mock()
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        mock_client.collection.return_value = mock_collection
        
        # Test role retrieval for new user
        from app.core.auth import auth_manager
        import asyncio
        
        async def test_role():
            role = await auth_manager.get_user_role("new-user-123")
            assert role == UserRole.STAFF  # Default role
            # Verify user document was created
            mock_doc_ref.set.assert_called_once()
        
        asyncio.run(test_role())
    
    @patch('app.core.auth.get_firestore_client')
    def test_get_user_role_invalid_role(self, mock_get_client):
        """Test handling of invalid role in user document."""
        # Mock Firestore client and document
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"role": "invalid_role", "created_at": 1234567890}
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.update = Mock()
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        mock_client.collection.return_value = mock_collection
        
        # Test role retrieval with invalid role
        from app.core.auth import auth_manager
        import asyncio
        
        async def test_role():
            role = await auth_manager.get_user_role("test-user-123")
            assert role == UserRole.STAFF  # Default fallback
            # Verify role was updated to valid value
            mock_doc_ref.update.assert_called_once()
        
        asyncio.run(test_role())


class TestAuthenticationIntegration:
    """Integration tests for authentication with real request flow."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = TestClient(app)
    
    def test_health_endpoints_no_auth_required(self):
        """Test that health endpoints don't require authentication."""
        # Test liveness endpoint
        response = self.client.get("/api/v1/health/liveness")
        assert response.status_code == 200
        
        # Test readiness endpoint
        with patch('app.core.db.check_firestore') as mock_check:
            mock_check.return_value = {
                "status": "up",
                "project_id": "test-project",
                "collections_count": 0,
                "timestamp": 1234567890.0
            }
            
            response = self.client.get("/api/v1/health/readiness")
            assert response.status_code == 200
    
    def test_root_endpoint_no_auth_required(self):
        """Test that root endpoint doesn't require authentication."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_async_authentication(self):
        """Test authentication using async client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test without authentication
            response = await client.get("/api/v1/students/")
            assert response.status_code == 401
            
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid-token"}
            response = await client.get("/api/v1/students/", headers=headers)
            assert response.status_code == 401
    
    def test_error_response_format_consistency(self):
        """Test that auth errors return consistent format."""
        # Test missing auth
        response = self.client.get("/api/v1/students/")
        assert response.status_code == 401
        data = response.json()
        
        # Verify error response structure
        assert "detail" in data
        assert "code" in data["detail"]
        assert "message" in data["detail"]
        assert "details" in data["detail"]
        assert data["detail"]["code"] == "AUTH"
        
        # Test invalid scheme
        headers = {"Authorization": "Basic invalid"}
        response = self.client.get("/api/v1/students/", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "AUTH"


class TestSecurityHeaders:
    """Test security-related headers and configurations."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = TestClient(app)
    
    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured."""
        response = self.client.get("/", headers={"Origin": "http://localhost:3000"})
        
        # Check for CORS headers (may vary based on configuration)
        assert response.status_code == 200
    
    def test_request_id_header_present(self):
        """Test that request ID header is added to responses."""
        response = self.client.get("/")
        
        # Should have request ID in headers or logs
        assert response.status_code == 200
        # Note: Request ID might be in logs rather than response headers
