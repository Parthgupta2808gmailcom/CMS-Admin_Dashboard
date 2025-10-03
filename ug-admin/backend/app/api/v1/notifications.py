"""
API endpoints for email notifications and communication.

This module provides REST API endpoints for sending email notifications,
managing email templates, and tracking email delivery with proper
authentication and audit logging.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi import status as http_status
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.core.errors import AppError, ValidationError
from app.core.logging import get_logger, log_request_info
from app.core.auth import AuthenticatedUser, require_staff_or_admin
from app.services.notifications import (
    notification_service,
    EmailTemplate,
    EmailPriority,
    EmailStatus,
    EmailRecipient,
    EmailLog
)
from app.services.students import student_service

# Create router for notification endpoints
router = APIRouter(prefix="/notifications", tags=["notifications"])

logger = get_logger(__name__)


class SendEmailRequest(BaseModel):
    """Request model for sending emails."""
    
    template: EmailTemplate = Field(..., description="Email template to use")
    recipients: List[EmailRecipient] = Field(..., description="Email recipients")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    subject_override: Optional[str] = Field(None, description="Override template subject")
    priority: EmailPriority = Field(EmailPriority.NORMAL, description="Email priority")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule email for later")
    
    class Config:
        use_enum_values = True


class SendStudentEmailRequest(BaseModel):
    """Request model for sending email to a specific student."""
    
    student_id: str = Field(..., description="ID of the student")
    template: EmailTemplate = Field(..., description="Email template to use")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    subject_override: Optional[str] = Field(None, description="Override template subject")
    
    class Config:
        use_enum_values = True


class SendBulkEmailRequest(BaseModel):
    """Request model for sending bulk emails to multiple students."""
    
    student_ids: List[str] = Field(..., description="List of student IDs")
    template: EmailTemplate = Field(..., description="Email template to use")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    subject_override: Optional[str] = Field(None, description="Override template subject")
    
    class Config:
        use_enum_values = True


class EmailResponse(BaseModel):
    """Response model for email operations."""
    
    success: bool
    message: str
    email_logs: List[EmailLog]
    successful_sends: int
    failed_sends: int


class EmailLogsResponse(BaseModel):
    """Response model for email logs listing."""
    
    success: bool
    message: str
    logs: List[EmailLog]
    total_count: int


@router.post(
    "/send",
    response_model=EmailResponse,
    summary="Send email to recipients",
    description="Send templated email to specified recipients with audit logging"
)
async def send_email(
    email_request: SendEmailRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> EmailResponse:
    """
    Send email to specified recipients using a template.
    
    This endpoint allows staff and administrators to send templated emails
    to multiple recipients with comprehensive audit logging and delivery tracking.
    
    **Staff or Admin access required** - Staff and administrators can send emails.
    
    Available templates:
    - welcome: Welcome new students
    - application_reminder: Remind about application status
    - document_request: Request specific documents
    - status_update: Notify about status changes
    - followup: General follow-up communications
    
    Args:
        email_request: Email parameters including template, recipients, and data
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Email sending results with delivery logs and statistics
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="send_email",
        message="Email send requested",
        extra={
            "template": email_request.template.value,
            "recipients_count": len(email_request.recipients),
            "priority": email_request.priority.value,
            "scheduled": bool(email_request.scheduled_at),
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Send email
        email_logs = await notification_service.send_email(
            template=email_request.template,
            recipients=email_request.recipients,
            template_data=email_request.template_data,
            user=current_user,
            subject_override=email_request.subject_override,
            priority=email_request.priority,
            scheduled_at=email_request.scheduled_at
        )
        
        # Calculate statistics
        successful_sends = sum(1 for log in email_logs if log.status == EmailStatus.SENT)
        failed_sends = len(email_logs) - successful_sends
        
        logger.info(
            f"Email batch completed: {successful_sends}/{len(email_logs)} successful",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "template": email_request.template.value,
                "total_recipients": len(email_request.recipients),
                "successful_sends": successful_sends,
                "failed_sends": failed_sends
            }
        )
        
        return EmailResponse(
            success=failed_sends == 0,
            message=f"Email sent to {successful_sends}/{len(email_logs)} recipients successfully",
            email_logs=email_logs,
            successful_sends=successful_sends,
            failed_sends=failed_sends
        )
        
    except ValidationError as e:
        logger.warning(
            f"Email send validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "send_email",
                "user": current_user.uid,
                "template": email_request.template.value
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Email validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"Email send application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "send_email",
                "user": current_user.uid,
                "template": email_request.template.value
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Email sending failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.post(
    "/send-to-student",
    response_model=EmailResponse,
    summary="Send email to specific student",
    description="Send templated email to a specific student with automatic student data injection"
)
async def send_student_email(
    email_request: SendStudentEmailRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> EmailResponse:
    """
    Send email to a specific student.
    
    This endpoint sends a templated email to a specific student, automatically
    injecting student data into the template for personalization.
    
    **Staff or Admin access required** - Staff and administrators can send emails.
    
    Args:
        email_request: Email parameters including student ID and template
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Email sending result with delivery log
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 404 if student not found,
                      500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="send_student_email",
        message="Student email send requested",
        extra={
            "student_id": email_request.student_id,
            "template": email_request.template.value,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Get student details
        student = await student_service.get_student_by_id(email_request.student_id)
        if not student:
            logger.warning(
                f"Student not found for email: {email_request.student_id}",
                extra={
                    "user": current_user.uid,
                    "student_id": email_request.student_id,
                    "endpoint": "send_student_email"
                }
            )
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Student not found",
                    "message": f"Student with ID '{email_request.student_id}' does not exist",
                    "student_id": email_request.student_id
                }
            )
        
        # Send email to student
        email_log = await notification_service.send_student_notification(
            student=student,
            template=email_request.template,
            template_data=email_request.template_data,
            user=current_user,
            subject_override=email_request.subject_override
        )
        
        if not email_log:
            raise AppError(
                message="Failed to send email to student",
                code="EMAIL_SEND_FAILED",
                details={"student_id": email_request.student_id}
            )
        
        successful = email_log.status == EmailStatus.SENT
        
        logger.info(
            f"Student email {'sent' if successful else 'failed'}: {email_request.student_id}",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "student_id": email_request.student_id,
                "student_email": student.email,
                "template": email_request.template.value,
                "success": successful
            }
        )
        
        return EmailResponse(
            success=successful,
            message=f"Email {'sent successfully' if successful else 'failed'} to {student.email}",
            email_logs=[email_log],
            successful_sends=1 if successful else 0,
            failed_sends=0 if successful else 1
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except ValidationError as e:
        logger.warning(
            f"Student email validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "send_student_email",
                "user": current_user.uid,
                "student_id": email_request.student_id
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Email validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"Student email application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "send_student_email",
                "user": current_user.uid,
                "student_id": email_request.student_id
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Student email sending failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.post(
    "/send-bulk",
    response_model=EmailResponse,
    summary="Send bulk emails to multiple students",
    description="Send templated emails to multiple students with batch processing"
)
async def send_bulk_emails(
    email_request: SendBulkEmailRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> EmailResponse:
    """
    Send bulk emails to multiple students.
    
    This endpoint sends templated emails to multiple students in batches
    with automatic student data injection and comprehensive error handling.
    
    **Staff or Admin access required** - Staff and administrators can send bulk emails.
    
    Args:
        email_request: Bulk email parameters including student IDs and template
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Bulk email sending results with delivery logs and statistics
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="send_bulk_emails",
        message="Bulk email send requested",
        extra={
            "student_ids_count": len(email_request.student_ids),
            "template": email_request.template.value,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Validate student IDs count
        if len(email_request.student_ids) > 1000:
            raise ValidationError(
                message="Too many students for bulk email",
                details={
                    "max_allowed": 1000,
                    "requested": len(email_request.student_ids)
                }
            )
        
        # Get students
        students = []
        missing_students = []
        
        for student_id in email_request.student_ids:
            try:
                student = await student_service.get_student_by_id(student_id)
                if student:
                    students.append(student)
                else:
                    missing_students.append(student_id)
            except Exception as e:
                logger.warning(f"Failed to get student {student_id}: {str(e)}")
                missing_students.append(student_id)
        
        if missing_students:
            logger.warning(
                f"Some students not found for bulk email: {len(missing_students)} missing",
                extra={
                    "user": current_user.uid,
                    "missing_count": len(missing_students),
                    "missing_students": missing_students[:10]  # Log first 10
                }
            )
        
        if not students:
            raise ValidationError(
                message="No valid students found for bulk email",
                details={
                    "requested_count": len(email_request.student_ids),
                    "missing_students": missing_students
                }
            )
        
        # Send bulk emails
        email_logs = await notification_service.send_bulk_notifications(
            students=students,
            template=email_request.template,
            template_data=email_request.template_data,
            user=current_user,
            subject_override=email_request.subject_override
        )
        
        # Calculate statistics
        successful_sends = sum(1 for log in email_logs if log.status == EmailStatus.SENT)
        failed_sends = len(email_logs) - successful_sends
        
        logger.info(
            f"Bulk email completed: {successful_sends}/{len(students)} successful",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "template": email_request.template.value,
                "total_students": len(students),
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "missing_students": len(missing_students)
            }
        )
        
        message = f"Bulk email sent to {successful_sends}/{len(students)} students successfully"
        if missing_students:
            message += f" ({len(missing_students)} students not found)"
        
        return EmailResponse(
            success=failed_sends == 0 and len(missing_students) == 0,
            message=message,
            email_logs=email_logs,
            successful_sends=successful_sends,
            failed_sends=failed_sends
        )
        
    except ValidationError as e:
        logger.warning(
            f"Bulk email validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "send_bulk_emails",
                "user": current_user.uid,
                "student_count": len(email_request.student_ids)
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Bulk email validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"Bulk email application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "send_bulk_emails",
                "user": current_user.uid,
                "student_count": len(email_request.student_ids)
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Bulk email sending failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/logs",
    response_model=EmailLogsResponse,
    summary="Get email logs",
    description="Retrieve email delivery logs with filtering and pagination"
)
async def get_email_logs(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    template: Optional[EmailTemplate] = Query(None, description="Filter by email template"),
    status: Optional[EmailStatus] = Query(None, description="Filter by email status"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs per page"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> EmailLogsResponse:
    """
    Get email delivery logs with filtering and pagination.
    
    This endpoint retrieves email logs for monitoring and auditing purposes
    with comprehensive filtering options and pagination support.
    
    **Staff or Admin access required** - Staff and administrators can view email logs.
    
    Args:
        student_id: Optional filter by student ID
        template: Optional filter by email template
        status: Optional filter by delivery status
        start_date: Optional filter by start date
        end_date: Optional filter by end date
        limit: Number of logs per page
        offset: Number of logs to skip
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Email logs with filtering and pagination metadata
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="get_email_logs",
        message="Email logs requested",
        extra={
            "student_id": student_id,
            "template": template.value if template else None,
            "status": status.value if status else None,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Parse date filters
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
            except ValueError:
                raise ValidationError(
                    message="Invalid start_date format",
                    details={"expected_format": "YYYY-MM-DDTHH:MM:SS", "received": start_date}
                )
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
            except ValueError:
                raise ValidationError(
                    message="Invalid end_date format",
                    details={"expected_format": "YYYY-MM-DDTHH:MM:SS", "received": end_date}
                )
        
        # Get email logs
        logs = await notification_service.get_email_logs(
            user=current_user,
            student_id=student_id,
            template=template,
            status=status,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=limit,
            offset=offset
        )
        
        logger.debug(
            f"Retrieved {len(logs)} email logs",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "logs_count": len(logs),
                "student_id": student_id,
                "template": template.value if template else None,
                "status": status.value if status else None
            }
        )
        
        return EmailLogsResponse(
            success=True,
            message=f"Retrieved {len(logs)} email logs",
            logs=logs,
            total_count=len(logs)  # In a real implementation, you'd get the total count separately
        )
        
    except ValidationError as e:
        logger.warning(
            f"Email logs validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "get_email_logs",
                "user": current_user.uid
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Email logs validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"Email logs application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "get_email_logs",
                "user": current_user.uid
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve email logs",
                "message": e.message,
                "code": e.code
            }
        )
