"""
Email notification service with audit logging and template management.

This module provides functionality for sending email notifications
with template support, audit logging, and pluggable email providers
for scalable communication with students and staff.
"""

import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from jinja2 import Template, Environment, BaseLoader

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors import AppError, ValidationError
from app.core.audit import audit_logger, AuditAction
from app.core.auth import AuthenticatedUser
from app.core.db import get_firestore_client
from app.schemas.student import Student

logger = get_logger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers."""
    MOCK = "mock"
    SENDGRID = "sendgrid"
    SES = "ses"
    SMTP = "smtp"


class EmailTemplate(str, Enum):
    """Available email templates."""
    WELCOME = "welcome"
    APPLICATION_REMINDER = "application_reminder"
    DOCUMENT_REQUEST = "document_request"
    STATUS_UPDATE = "status_update"
    FOLLOWUP = "followup"
    INTERVIEW_INVITATION = "interview_invitation"
    ADMISSION_DECISION = "admission_decision"


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class EmailRecipient(BaseModel):
    """Email recipient information."""
    
    email: EmailStr
    name: Optional[str] = None
    student_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class EmailMessage(BaseModel):
    """Email message structure."""
    
    id: Optional[str] = Field(None, description="Message ID")
    template: EmailTemplate = Field(..., description="Email template to use")
    recipients: List[EmailRecipient] = Field(..., description="Email recipients")
    subject: str = Field(..., description="Email subject")
    html_content: str = Field(..., description="HTML email content")
    text_content: Optional[str] = Field(None, description="Plain text email content")
    sender_email: str = Field(..., description="Sender email address")
    sender_name: str = Field(..., description="Sender name")
    priority: EmailPriority = Field(EmailPriority.NORMAL, description="Email priority")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled send time")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailLog(BaseModel):
    """Email delivery log entry."""
    
    id: str = Field(..., description="Log entry ID")
    message_id: str = Field(..., description="Email message ID")
    recipient_email: str = Field(..., description="Recipient email")
    student_id: Optional[str] = Field(None, description="Associated student ID")
    template: EmailTemplate = Field(..., description="Email template used")
    subject: str = Field(..., description="Email subject")
    status: EmailStatus = Field(..., description="Delivery status")
    sent_by: str = Field(..., description="User who sent the email")
    sent_at: datetime = Field(default_factory=datetime.utcnow, description="Send timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    provider_response: Dict[str, Any] = Field(default_factory=dict, description="Provider response")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationService:
    """
    Service for managing email notifications and communications.
    
    This service provides functionality for sending templated emails
    with audit logging, delivery tracking, and support for multiple
    email providers.
    """
    
    def __init__(self):
        """Initialize the notification service."""
        self.firestore_client = get_firestore_client()
        self.email_logs_collection = "email_logs"
        
        # Email provider configuration
        self.provider = EmailProvider.MOCK  # Default to mock for development
        self.sender_email = getattr(settings, 'default_sender_email', 'noreply@undergraduation.com')
        self.sender_name = getattr(settings, 'default_sender_name', 'Undergraduation.com')
        
        # Template configuration
        self.template_env = Environment(loader=BaseLoader())
        self.templates = self._load_email_templates()
        
        logger.info(f"NotificationService initialized with provider: {self.provider.value}")
    
    async def send_email(
        self,
        template: EmailTemplate,
        recipients: List[EmailRecipient],
        template_data: Dict[str, Any],
        user: AuthenticatedUser,
        subject_override: Optional[str] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        scheduled_at: Optional[datetime] = None
    ) -> List[EmailLog]:
        """
        Send an email using a template to multiple recipients.
        
        Args:
            template: Email template to use
            recipients: List of email recipients
            template_data: Data to populate the template
            user: Authenticated user sending the email
            subject_override: Optional subject override
            priority: Email priority level
            scheduled_at: Optional scheduled send time
            
        Returns:
            List of email log entries for each recipient
            
        Raises:
            ValidationError: If template or recipients are invalid
            AppError: If email sending fails
        """
        try:
            logger.info(
                f"Sending email: {template.value}",
                extra={
                    "user_id": user.uid,
                    "template": template.value,
                    "recipients_count": len(recipients),
                    "priority": priority.value
                }
            )
            
            # Validate recipients
            if not recipients:
                raise ValidationError(
                    message="No recipients specified for email",
                    details={"template": template.value}
                )
            
            # Get template configuration
            template_config = self.templates.get(template)
            if not template_config:
                raise ValidationError(
                    message=f"Email template not found: {template.value}",
                    details={"available_templates": list(self.templates.keys())}
                )
            
            # Generate email content
            subject = subject_override or self._render_template(
                template_config["subject"], template_data
            )
            html_content = self._render_template(
                template_config["html_template"], template_data
            )
            text_content = self._render_template(
                template_config.get("text_template", ""), template_data
            ) if template_config.get("text_template") else None
            
            # Create email message
            message = EmailMessage(
                template=template,
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                sender_email=self.sender_email,
                sender_name=self.sender_name,
                priority=priority,
                scheduled_at=scheduled_at,
                template_data=template_data
            )
            
            # Send to each recipient
            email_logs = []
            
            for recipient in recipients:
                try:
                    # Send email via provider
                    provider_response = await self._send_via_provider(message, recipient)
                    
                    # Create email log
                    email_log = EmailLog(
                        id=f"email_{datetime.utcnow().timestamp()}_{recipient.email}",
                        message_id=message.id or f"msg_{datetime.utcnow().timestamp()}",
                        recipient_email=recipient.email,
                        student_id=recipient.student_id,
                        template=template,
                        subject=subject,
                        status=EmailStatus.SENT,
                        sent_by=user.uid,
                        provider_response=provider_response
                    )
                    
                    # Store email log
                    await self._store_email_log(email_log)
                    
                    # Log audit event
                    await audit_logger.log_email_action(
                        user=user,
                        recipient_email=recipient.email,
                        subject=subject,
                        template_name=template.value,
                        student_id=recipient.student_id,
                        success=True
                    )
                    
                    email_logs.append(email_log)
                    
                    logger.debug(
                        f"Email sent successfully to {recipient.email}",
                        extra={
                            "user_id": user.uid,
                            "recipient": recipient.email,
                            "template": template.value
                        }
                    )
                    
                except Exception as e:
                    # Create failed email log
                    email_log = EmailLog(
                        id=f"email_{datetime.utcnow().timestamp()}_{recipient.email}",
                        message_id=message.id or f"msg_{datetime.utcnow().timestamp()}",
                        recipient_email=recipient.email,
                        student_id=recipient.student_id,
                        template=template,
                        subject=subject,
                        status=EmailStatus.FAILED,
                        sent_by=user.uid,
                        error_message=str(e)
                    )
                    
                    # Store failed email log
                    await self._store_email_log(email_log)
                    
                    # Log failed audit event
                    await audit_logger.log_email_action(
                        user=user,
                        recipient_email=recipient.email,
                        subject=subject,
                        template_name=template.value,
                        student_id=recipient.student_id,
                        success=False,
                        error_message=str(e)
                    )
                    
                    email_logs.append(email_log)
                    
                    logger.warning(
                        f"Failed to send email to {recipient.email}: {str(e)}",
                        extra={
                            "user_id": user.uid,
                            "recipient": recipient.email,
                            "template": template.value,
                            "error": str(e)
                        }
                    )
            
            successful_sends = sum(1 for log in email_logs if log.status == EmailStatus.SENT)
            
            logger.info(
                f"Email batch completed: {successful_sends}/{len(recipients)} successful",
                extra={
                    "user_id": user.uid,
                    "template": template.value,
                    "total_recipients": len(recipients),
                    "successful_sends": successful_sends
                }
            )
            
            return email_logs
            
        except Exception as e:
            logger.error(
                f"Email sending failed: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "template": template.value,
                    "error": str(e)
                }
            )
            
            if isinstance(e, (ValidationError, AppError)):
                raise
            else:
                raise AppError(
                    message="Email sending operation failed",
                    code="EMAIL_SEND_ERROR",
                    details={"error": str(e)}
                )
    
    async def send_student_notification(
        self,
        student: Student,
        template: EmailTemplate,
        template_data: Dict[str, Any],
        user: AuthenticatedUser,
        subject_override: Optional[str] = None
    ) -> EmailLog:
        """
        Send a notification email to a specific student.
        
        Args:
            student: Student to send email to
            template: Email template to use
            template_data: Template data (student data will be added automatically)
            user: Authenticated user sending the email
            subject_override: Optional subject override
            
        Returns:
            Email log entry
        """
        # Add student data to template data
        enhanced_template_data = {
            "student": {
                "name": student.name,
                "email": student.email,
                "id": student.id,
                "application_status": student.application_status.value if student.application_status else None,
                "country": student.country,
                "grade": student.grade
            },
            **template_data
        }
        
        # Create recipient
        recipient = EmailRecipient(
            email=student.email,
            name=student.name,
            student_id=student.id
        )
        
        # Send email
        email_logs = await self.send_email(
            template=template,
            recipients=[recipient],
            template_data=enhanced_template_data,
            user=user,
            subject_override=subject_override
        )
        
        return email_logs[0] if email_logs else None
    
    async def send_bulk_notifications(
        self,
        students: List[Student],
        template: EmailTemplate,
        template_data: Dict[str, Any],
        user: AuthenticatedUser,
        subject_override: Optional[str] = None
    ) -> List[EmailLog]:
        """
        Send bulk notifications to multiple students.
        
        Args:
            students: List of students to send emails to
            template: Email template to use
            template_data: Base template data
            user: Authenticated user sending the emails
            subject_override: Optional subject override
            
        Returns:
            List of email log entries
        """
        logger.info(
            f"Sending bulk notifications: {template.value}",
            extra={
                "user_id": user.uid,
                "template": template.value,
                "students_count": len(students)
            }
        )
        
        all_email_logs = []
        
        # Send emails in batches to avoid overwhelming the provider
        batch_size = 10
        
        for i in range(0, len(students), batch_size):
            batch_students = students[i:i + batch_size]
            
            # Create recipients for this batch
            recipients = [
                EmailRecipient(
                    email=student.email,
                    name=student.name,
                    student_id=student.id
                )
                for student in batch_students
            ]
            
            # Enhance template data with batch info
            batch_template_data = {
                "batch_info": {
                    "batch_number": (i // batch_size) + 1,
                    "total_batches": (len(students) + batch_size - 1) // batch_size,
                    "students_in_batch": len(batch_students)
                },
                **template_data
            }
            
            # Send batch
            try:
                batch_logs = await self.send_email(
                    template=template,
                    recipients=recipients,
                    template_data=batch_template_data,
                    user=user,
                    subject_override=subject_override
                )
                
                all_email_logs.extend(batch_logs)
                
            except Exception as e:
                logger.error(
                    f"Failed to send email batch {i // batch_size + 1}: {str(e)}",
                    extra={
                        "user_id": user.uid,
                        "batch_start": i,
                        "batch_size": len(batch_students),
                        "error": str(e)
                    }
                )
                # Continue with next batch
                continue
        
        successful_sends = sum(1 for log in all_email_logs if log.status == EmailStatus.SENT)
        
        logger.info(
            f"Bulk notification completed: {successful_sends}/{len(students)} successful",
            extra={
                "user_id": user.uid,
                "template": template.value,
                "total_students": len(students),
                "successful_sends": successful_sends
            }
        )
        
        return all_email_logs
    
    async def get_email_logs(
        self,
        user: AuthenticatedUser,
        student_id: Optional[str] = None,
        template: Optional[EmailTemplate] = None,
        status: Optional[EmailStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EmailLog]:
        """
        Get email logs with filtering and pagination.
        
        Args:
            user: Authenticated user requesting logs
            student_id: Filter by student ID
            template: Filter by email template
            status: Filter by email status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            List of email log entries
        """
        try:
            logger.debug(
                f"Getting email logs",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "template": template.value if template else None,
                    "status": status.value if status else None,
                    "limit": limit,
                    "offset": offset
                }
            )
            
            # Build query
            query = self.firestore_client.collection(self.email_logs_collection)
            
            # Apply filters
            if student_id:
                query = query.where("student_id", "==", student_id)
            
            if template:
                query = query.where("template", "==", template.value)
            
            if status:
                query = query.where("status", "==", status.value)
            
            if start_date:
                query = query.where("sent_at", ">=", start_date.isoformat())
            
            if end_date:
                query = query.where("sent_at", "<=", end_date.isoformat())
            
            # Apply ordering and pagination
            query = query.order_by("sent_at", direction="DESCENDING")
            query = query.limit(limit).offset(offset)
            
            # Execute query
            docs = query.stream()
            
            # Convert to email log entries
            email_logs = []
            for doc in docs:
                try:
                    data = doc.to_dict()
                    # Convert timestamps back to datetime
                    for field in ['sent_at', 'delivered_at']:
                        if field in data and isinstance(data[field], str):
                            data[field] = datetime.fromisoformat(data[field])
                    
                    email_logs.append(EmailLog(**data))
                except Exception as e:
                    logger.warning(f"Failed to parse email log {doc.id}: {str(e)}")
                    continue
            
            logger.debug(
                f"Retrieved {len(email_logs)} email logs",
                extra={
                    "user_id": user.uid,
                    "logs_count": len(email_logs)
                }
            )
            
            return email_logs
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve email logs: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "error": str(e)
                }
            )
            return []
    
    def _load_email_templates(self) -> Dict[EmailTemplate, Dict[str, str]]:
        """Load email templates configuration."""
        
        # In a real implementation, these would be loaded from files or database
        templates = {
            EmailTemplate.WELCOME: {
                "subject": "Welcome to Undergraduation.com, {{ student.name }}!",
                "html_template": """
                <html>
                <body>
                    <h1>Welcome {{ student.name }}!</h1>
                    <p>Thank you for joining Undergraduation.com. We're excited to help you with your university application journey.</p>
                    <p>Your application status: <strong>{{ student.application_status }}</strong></p>
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                    <p>Best regards,<br>The Undergraduation.com Team</p>
                </body>
                </html>
                """,
                "text_template": """
                Welcome {{ student.name }}!
                
                Thank you for joining Undergraduation.com. We're excited to help you with your university application journey.
                
                Your application status: {{ student.application_status }}
                
                If you have any questions, please don't hesitate to contact us.
                
                Best regards,
                The Undergraduation.com Team
                """
            },
            EmailTemplate.APPLICATION_REMINDER: {
                "subject": "Application Reminder - {{ student.name }}",
                "html_template": """
                <html>
                <body>
                    <h1>Application Reminder</h1>
                    <p>Hi {{ student.name }},</p>
                    <p>This is a friendly reminder about your university application.</p>
                    <p>Current status: <strong>{{ student.application_status }}</strong></p>
                    <p>{{ reminder_message }}</p>
                    <p>Please log in to your account to continue your application.</p>
                    <p>Best regards,<br>The Undergraduation.com Team</p>
                </body>
                </html>
                """,
                "text_template": """
                Application Reminder
                
                Hi {{ student.name }},
                
                This is a friendly reminder about your university application.
                Current status: {{ student.application_status }}
                
                {{ reminder_message }}
                
                Please log in to your account to continue your application.
                
                Best regards,
                The Undergraduation.com Team
                """
            },
            EmailTemplate.DOCUMENT_REQUEST: {
                "subject": "Document Request - {{ document_type }}",
                "html_template": """
                <html>
                <body>
                    <h1>Document Request</h1>
                    <p>Hi {{ student.name }},</p>
                    <p>We need the following document for your application:</p>
                    <p><strong>{{ document_type }}</strong></p>
                    <p>{{ request_details }}</p>
                    <p>Please upload the document to your account as soon as possible.</p>
                    <p>Best regards,<br>The Undergraduation.com Team</p>
                </body>
                </html>
                """
            },
            EmailTemplate.STATUS_UPDATE: {
                "subject": "Application Status Update - {{ student.name }}",
                "html_template": """
                <html>
                <body>
                    <h1>Application Status Update</h1>
                    <p>Hi {{ student.name }},</p>
                    <p>Your application status has been updated to: <strong>{{ new_status }}</strong></p>
                    <p>{{ status_message }}</p>
                    <p>{{ next_steps }}</p>
                    <p>Best regards,<br>The Undergraduation.com Team</p>
                </body>
                </html>
                """
            },
            EmailTemplate.FOLLOWUP: {
                "subject": "Follow-up - {{ student.name }}",
                "html_template": """
                <html>
                <body>
                    <h1>Follow-up</h1>
                    <p>Hi {{ student.name }},</p>
                    <p>{{ followup_message }}</p>
                    <p>If you have any questions or need assistance, please don't hesitate to reach out.</p>
                    <p>Best regards,<br>The Undergraduation.com Team</p>
                </body>
                </html>
                """
            }
        }
        
        return templates
    
    def _render_template(self, template_str: str, data: Dict[str, Any]) -> str:
        """Render a Jinja2 template with provided data."""
        
        try:
            template = self.template_env.from_string(template_str)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            return template_str  # Return original string if rendering fails
    
    async def _send_via_provider(
        self,
        message: EmailMessage,
        recipient: EmailRecipient
    ) -> Dict[str, Any]:
        """Send email via configured provider."""
        
        if self.provider == EmailProvider.MOCK:
            return await self._send_via_mock(message, recipient)
        elif self.provider == EmailProvider.SENDGRID:
            return await self._send_via_sendgrid(message, recipient)
        elif self.provider == EmailProvider.SES:
            return await self._send_via_ses(message, recipient)
        elif self.provider == EmailProvider.SMTP:
            return await self._send_via_smtp(message, recipient)
        else:
            raise AppError(
                message=f"Unsupported email provider: {self.provider}",
                code="UNSUPPORTED_PROVIDER"
            )
    
    async def _send_via_mock(
        self,
        message: EmailMessage,
        recipient: EmailRecipient
    ) -> Dict[str, Any]:
        """Mock email sending for development."""
        
        logger.info(
            f"MOCK EMAIL SENT",
            extra={
                "to": recipient.email,
                "subject": message.subject,
                "template": message.template.value,
                "provider": "mock"
            }
        )
        
        # Simulate provider response
        return {
            "provider": "mock",
            "message_id": f"mock_{datetime.utcnow().timestamp()}",
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _send_via_sendgrid(
        self,
        message: EmailMessage,
        recipient: EmailRecipient
    ) -> Dict[str, Any]:
        """Send email via SendGrid (placeholder implementation)."""
        
        # This would integrate with SendGrid API
        # For now, return mock response
        logger.info(f"SendGrid email would be sent to {recipient.email}")
        
        return {
            "provider": "sendgrid",
            "message_id": f"sg_{datetime.utcnow().timestamp()}",
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _send_via_ses(
        self,
        message: EmailMessage,
        recipient: EmailRecipient
    ) -> Dict[str, Any]:
        """Send email via AWS SES (placeholder implementation)."""
        
        # This would integrate with AWS SES
        # For now, return mock response
        logger.info(f"AWS SES email would be sent to {recipient.email}")
        
        return {
            "provider": "ses",
            "message_id": f"ses_{datetime.utcnow().timestamp()}",
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _send_via_smtp(
        self,
        message: EmailMessage,
        recipient: EmailRecipient
    ) -> Dict[str, Any]:
        """Send email via SMTP (placeholder implementation)."""
        
        # This would use smtplib to send emails
        # For now, return mock response
        logger.info(f"SMTP email would be sent to {recipient.email}")
        
        return {
            "provider": "smtp",
            "message_id": f"smtp_{datetime.utcnow().timestamp()}",
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _store_email_log(self, email_log: EmailLog) -> None:
        """Store email log in Firestore."""
        
        try:
            # Convert to dictionary
            log_data = email_log.model_dump()
            
            # Convert datetime fields to ISO strings
            for field in ['sent_at', 'delivered_at']:
                if field in log_data and log_data[field]:
                    log_data[field] = log_data[field].isoformat()
            
            # Store in Firestore
            doc_ref = self.firestore_client.collection(self.email_logs_collection).document(email_log.id)
            doc_ref.set(log_data)
            
            logger.debug(f"Email log stored: {email_log.id}")
            
        except Exception as e:
            logger.error(f"Failed to store email log: {str(e)}")
            # Don't raise exception as this is logging only


# Global service instance
notification_service = NotificationService()
