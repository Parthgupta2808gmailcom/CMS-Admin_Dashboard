"""
Tests for email notification API endpoints.

This module contains comprehensive tests for email notification functionality
including template rendering, delivery tracking, and audit logging.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.core.auth import UserRole
from app.services.notifications import EmailLog, EmailStatus, EmailTemplate, EmailPriority, EmailRecipient
from app.schemas.student import Student, ApplicationStatus


class TestSendEmailEndpoint:
    """Test cases for send email endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.notifications.notification_service.send_email')
    def test_successful_email_send(self, mock_send_email, mock_get_role, mock_verify_token):
        """Test successful email sending with staff user."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock email logs
        mock_email_logs = [
            EmailLog(
                id="email-log-1",
                message_id="msg-123",
                recipient_email="student1@test.com",
                student_id="student-1",
                template=EmailTemplate.WELCOME,
                subject="Welcome to Undergraduation.com!",
                status=EmailStatus.SENT,
                sent_by="staff-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock", "status": "sent"}
            ),
            EmailLog(
                id="email-log-2",
                message_id="msg-124",
                recipient_email="student2@test.com",
                student_id="student-2",
                template=EmailTemplate.WELCOME,
                subject="Welcome to Undergraduation.com!",
                status=EmailStatus.SENT,
                sent_by="staff-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock", "status": "sent"}
            )
        ]
        
        mock_send_email.return_value = mock_email_logs
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        email_request = {
            "template": "welcome",
            "recipients": [
                {"email": "student1@test.com", "name": "Student One", "student_id": "student-1"},
                {"email": "student2@test.com", "name": "Student Two", "student_id": "student-2"}
            ],
            "template_data": {
                "welcome_message": "Welcome to our platform!"
            },
            "priority": "normal"
        }
        
        response = self.client.post("/api/v1/notifications/send", headers=headers, json=email_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["successful_sends"] == 2
        assert result["failed_sends"] == 0
        assert len(result["email_logs"]) == 2
        assert all(log["status"] == "sent" for log in result["email_logs"])
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.notifications.notification_service.send_email')
    def test_email_send_with_failures(self, mock_send_email, mock_get_role, mock_verify_token):
        """Test email sending with some failures."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock email logs with one failure
        mock_email_logs = [
            EmailLog(
                id="email-log-1",
                message_id="msg-123",
                recipient_email="valid@test.com",
                template=EmailTemplate.APPLICATION_REMINDER,
                subject="Application Reminder",
                status=EmailStatus.SENT,
                sent_by="admin-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock", "status": "sent"}
            ),
            EmailLog(
                id="email-log-2",
                message_id="msg-124",
                recipient_email="invalid@test.com",
                template=EmailTemplate.APPLICATION_REMINDER,
                subject="Application Reminder",
                status=EmailStatus.FAILED,
                sent_by="admin-123",
                sent_at=datetime.utcnow(),
                error_message="Invalid email address",
                provider_response={"provider": "mock", "status": "failed"}
            )
        ]
        
        mock_send_email.return_value = mock_email_logs
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        email_request = {
            "template": "application_reminder",
            "recipients": [
                {"email": "valid@test.com", "name": "Valid User"},
                {"email": "invalid@test.com", "name": "Invalid User"}
            ],
            "template_data": {
                "reminder_message": "Please complete your application"
            }
        }
        
        response = self.client.post("/api/v1/notifications/send", headers=headers, json=email_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False  # Has failures
        assert result["successful_sends"] == 1
        assert result["failed_sends"] == 1
        assert len(result["email_logs"]) == 2
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_send_email_requires_staff_or_admin(self, mock_get_role, mock_verify_token):
        """Test that send email endpoint requires staff or admin role."""
        
        # Mock authentication with invalid role
        mock_verify_token.return_value = {"uid": "user-123", "email": "user@test.com"}
        mock_get_role.return_value = None
        
        headers = {"Authorization": "Bearer invalid-role-token"}
        email_request = {
            "template": "welcome",
            "recipients": [{"email": "test@test.com"}],
            "template_data": {}
        }
        
        response = self.client.post("/api/v1/notifications/send", headers=headers, json=email_request)
        
        assert response.status_code in [401, 403]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_send_email_validation_errors(self, mock_get_role, mock_verify_token):
        """Test email send with validation errors."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        
        # Test with empty recipients
        email_request = {
            "template": "welcome",
            "recipients": [],
            "template_data": {}
        }
        
        response = self.client.post("/api/v1/notifications/send", headers=headers, json=email_request)
        
        assert response.status_code == 400
        result = response.json()
        assert "validation" in result["error"].lower()


class TestSendStudentEmailEndpoint:
    """Test cases for send student email endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.students.student_service.get_student_by_id')
    @patch('app.services.notifications.notification_service.send_student_notification')
    def test_successful_student_email(self, mock_send_notification, mock_get_student, mock_get_role, mock_verify_token):
        """Test successful email to specific student."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock student
        mock_student = Student(
            id="student-123",
            name="John Doe",
            email="john@test.com",
            country="USA",
            application_status=ApplicationStatus.EXPLORING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_get_student.return_value = mock_student
        
        # Mock email log
        mock_email_log = EmailLog(
            id="email-log-student",
            message_id="msg-student-123",
            recipient_email="john@test.com",
            student_id="student-123",
            template=EmailTemplate.STATUS_UPDATE,
            subject="Application Status Update",
            status=EmailStatus.SENT,
            sent_by="staff-123",
            sent_at=datetime.utcnow(),
            provider_response={"provider": "mock", "status": "sent"}
        )
        mock_send_notification.return_value = mock_email_log
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        email_request = {
            "student_id": "student-123",
            "template": "status_update",
            "template_data": {
                "new_status": "Shortlisting",
                "status_message": "Your application is now being reviewed"
            }
        }
        
        response = self.client.post("/api/v1/notifications/send-to-student", headers=headers, json=email_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["successful_sends"] == 1
        assert result["failed_sends"] == 0
        assert len(result["email_logs"]) == 1
        assert result["email_logs"][0]["recipient_email"] == "john@test.com"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.students.student_service.get_student_by_id')
    def test_student_email_student_not_found(self, mock_get_student, mock_get_role, mock_verify_token):
        """Test student email when student doesn't exist."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock student not found
        mock_get_student.return_value = None
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        email_request = {
            "student_id": "nonexistent-student",
            "template": "welcome",
            "template_data": {}
        }
        
        response = self.client.post("/api/v1/notifications/send-to-student", headers=headers, json=email_request)
        
        assert response.status_code == 404
        result = response.json()
        assert "Student not found" in result["message"]
        assert result["student_id"] == "nonexistent-student"


class TestSendBulkEmailsEndpoint:
    """Test cases for bulk email sending endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.students.student_service.get_student_by_id')
    @patch('app.services.notifications.notification_service.send_bulk_notifications')
    def test_successful_bulk_email(self, mock_send_bulk, mock_get_student, mock_get_role, mock_verify_token):
        """Test successful bulk email sending."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock students
        mock_students = [
            Student(
                id="student-1",
                name="Student One",
                email="student1@test.com",
                country="USA",
                application_status=ApplicationStatus.EXPLORING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Student(
                id="student-2",
                name="Student Two",
                email="student2@test.com",
                country="Canada",
                application_status=ApplicationStatus.SHORTLISTING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        # Mock get_student_by_id to return students based on ID
        def mock_get_student_side_effect(student_id):
            for student in mock_students:
                if student.id == student_id:
                    return student
            return None
        
        mock_get_student.side_effect = mock_get_student_side_effect
        
        # Mock bulk email logs
        mock_email_logs = [
            EmailLog(
                id="bulk-email-1",
                message_id="bulk-msg-1",
                recipient_email="student1@test.com",
                student_id="student-1",
                template=EmailTemplate.FOLLOWUP,
                subject="Follow-up Message",
                status=EmailStatus.SENT,
                sent_by="admin-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock", "status": "sent"}
            ),
            EmailLog(
                id="bulk-email-2",
                message_id="bulk-msg-2",
                recipient_email="student2@test.com",
                student_id="student-2",
                template=EmailTemplate.FOLLOWUP,
                subject="Follow-up Message",
                status=EmailStatus.SENT,
                sent_by="admin-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock", "status": "sent"}
            )
        ]
        mock_send_bulk.return_value = mock_email_logs
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        bulk_request = {
            "student_ids": ["student-1", "student-2"],
            "template": "followup",
            "template_data": {
                "followup_message": "We wanted to check in on your application progress"
            }
        }
        
        response = self.client.post("/api/v1/notifications/send-bulk", headers=headers, json=bulk_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["successful_sends"] == 2
        assert result["failed_sends"] == 0
        assert len(result["email_logs"]) == 2
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_bulk_email_too_many_students(self, mock_get_role, mock_verify_token):
        """Test bulk email with too many students."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        
        # Create request with too many student IDs (over 1000)
        bulk_request = {
            "student_ids": [f"student-{i}" for i in range(1001)],
            "template": "welcome",
            "template_data": {}
        }
        
        response = self.client.post("/api/v1/notifications/send-bulk", headers=headers, json=bulk_request)
        
        assert response.status_code == 400
        result = response.json()
        assert "too many students" in result["message"].lower()
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.students.student_service.get_student_by_id')
    @patch('app.services.notifications.notification_service.send_bulk_notifications')
    def test_bulk_email_with_missing_students(self, mock_send_bulk, mock_get_student, mock_get_role, mock_verify_token):
        """Test bulk email when some students are not found."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock get_student_by_id - only first student exists
        def mock_get_student_side_effect(student_id):
            if student_id == "existing-student":
                return Student(
                    id="existing-student",
                    name="Existing Student",
                    email="existing@test.com",
                    country="USA",
                    application_status=ApplicationStatus.EXPLORING,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            return None
        
        mock_get_student.side_effect = mock_get_student_side_effect
        
        # Mock bulk email logs (only for existing student)
        mock_email_logs = [
            EmailLog(
                id="bulk-email-existing",
                message_id="bulk-msg-existing",
                recipient_email="existing@test.com",
                student_id="existing-student",
                template=EmailTemplate.WELCOME,
                subject="Welcome!",
                status=EmailStatus.SENT,
                sent_by="staff-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock", "status": "sent"}
            )
        ]
        mock_send_bulk.return_value = mock_email_logs
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        bulk_request = {
            "student_ids": ["existing-student", "missing-student-1", "missing-student-2"],
            "template": "welcome",
            "template_data": {}
        }
        
        response = self.client.post("/api/v1/notifications/send-bulk", headers=headers, json=bulk_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False  # Has missing students
        assert result["successful_sends"] == 1
        assert result["failed_sends"] == 0
        assert "students not found" in result["message"]


class TestEmailLogsEndpoint:
    """Test cases for email logs endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.notifications.notification_service.get_email_logs')
    def test_get_email_logs(self, mock_get_logs, mock_get_role, mock_verify_token):
        """Test getting email logs with pagination."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock email logs
        mock_logs = [
            EmailLog(
                id="log-1",
                message_id="msg-1",
                recipient_email="student1@test.com",
                student_id="student-1",
                template=EmailTemplate.WELCOME,
                subject="Welcome!",
                status=EmailStatus.SENT,
                sent_by="admin-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock"}
            ),
            EmailLog(
                id="log-2",
                message_id="msg-2",
                recipient_email="student2@test.com",
                student_id="student-2",
                template=EmailTemplate.APPLICATION_REMINDER,
                subject="Application Reminder",
                status=EmailStatus.DELIVERED,
                sent_by="staff-456",
                sent_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
                provider_response={"provider": "mock"}
            )
        ]
        mock_get_logs.return_value = mock_logs
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        params = {
            "limit": 50,
            "offset": 0
        }
        
        response = self.client.get("/api/v1/notifications/logs", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["logs"]) == 2
        assert result["total_count"] == 2
        assert result["logs"][0]["template"] == "welcome"
        assert result["logs"][1]["template"] == "application_reminder"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.notifications.notification_service.get_email_logs')
    def test_get_email_logs_with_filters(self, mock_get_logs, mock_get_role, mock_verify_token):
        """Test getting email logs with filters."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock filtered logs
        mock_logs = [
            EmailLog(
                id="filtered-log",
                message_id="filtered-msg",
                recipient_email="specific@test.com",
                student_id="specific-student",
                template=EmailTemplate.STATUS_UPDATE,
                subject="Status Update",
                status=EmailStatus.SENT,
                sent_by="staff-123",
                sent_at=datetime.utcnow(),
                provider_response={"provider": "mock"}
            )
        ]
        mock_get_logs.return_value = mock_logs
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        params = {
            "student_id": "specific-student",
            "template": "status_update",
            "status": "sent",
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-01-31T23:59:59",
            "limit": 20,
            "offset": 0
        }
        
        response = self.client.get("/api/v1/notifications/logs", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["logs"]) == 1
        assert result["logs"][0]["student_id"] == "specific-student"
        assert result["logs"][0]["template"] == "status_update"
        
        # Verify the service was called with correct filters
        mock_get_logs.assert_called_once()
        call_args = mock_get_logs.call_args[1]
        assert call_args["student_id"] == "specific-student"
        assert call_args["template"].value == "status_update"
        assert call_args["status"].value == "sent"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_get_logs_invalid_date_format(self, mock_get_role, mock_verify_token):
        """Test getting logs with invalid date format."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        params = {
            "start_date": "invalid-date-format"
        }
        
        response = self.client.get("/api/v1/notifications/logs", headers=headers, params=params)
        
        assert response.status_code == 400
        result = response.json()
        assert "Invalid start_date format" in result["message"]
