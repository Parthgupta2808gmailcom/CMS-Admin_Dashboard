"""
Comprehensive audit logging system for compliance and analytics.

This module provides structured audit logging for all critical actions
in the system, storing logs in Firestore for compliance, security,
and analytics purposes.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.db import get_firestore_client
from app.core.logging import get_logger
from app.core.auth import AuthenticatedUser

logger = get_logger(__name__)


class AuditAction(str, Enum):
    """Enumeration of auditable actions in the system."""
    
    # Student operations
    CREATE_STUDENT = "CREATE_STUDENT"
    UPDATE_STUDENT = "UPDATE_STUDENT"
    DELETE_STUDENT = "DELETE_STUDENT"
    VIEW_STUDENT = "VIEW_STUDENT"
    
    # Bulk operations
    BULK_IMPORT_STUDENTS = "BULK_IMPORT_STUDENTS"
    EXPORT_STUDENTS = "EXPORT_STUDENTS"
    
    # File operations
    UPLOAD_FILE = "UPLOAD_FILE"
    DELETE_FILE = "DELETE_FILE"
    DOWNLOAD_FILE = "DOWNLOAD_FILE"
    
    # Email operations
    SEND_EMAIL = "SEND_EMAIL"
    
    # Authentication operations
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    
    # Administrative operations
    CHANGE_USER_ROLE = "CHANGE_USER_ROLE"
    
    # Search operations
    SEARCH_STUDENTS = "SEARCH_STUDENTS"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLogEntry(BaseModel):
    """Model for audit log entries stored in Firestore."""
    
    id: Optional[str] = Field(None, description="Firestore document ID")
    user_id: str = Field(..., description="ID of user who performed the action")
    user_email: str = Field(..., description="Email of user who performed the action")
    user_role: str = Field(..., description="Role of user who performed the action")
    action: AuditAction = Field(..., description="Action that was performed")
    target_type: str = Field(..., description="Type of target (student, file, etc.)")
    target_id: Optional[str] = Field(None, description="ID of the target resource")
    severity: AuditSeverity = Field(AuditSeverity.MEDIUM, description="Severity of the action")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the action occurred")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional action details")
    success: bool = Field(True, description="Whether the action was successful")
    error_message: Optional[str] = Field(None, description="Error message if action failed")
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditLogger:
    """
    Centralized audit logging service.
    
    This class provides methods to log various types of actions
    with proper context and metadata for compliance and analytics.
    """
    
    def __init__(self):
        """Initialize the audit logger with Firestore client."""
        self.firestore_client = get_firestore_client()
        self.collection_name = "audit_logs"
        self.collection = self.firestore_client.collection(self.collection_name)
        logger.info("AuditLogger initialized")
    
    async def log_action(
        self,
        user: AuthenticatedUser,
        action: AuditAction,
        target_type: str,
        target_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log an audit event to Firestore.
        
        Args:
            user: Authenticated user performing the action
            action: Type of action being performed
            target_type: Type of resource being acted upon
            target_id: ID of the specific resource (optional)
            severity: Severity level of the action
            details: Additional context and metadata
            success: Whether the action was successful
            error_message: Error message if action failed
            ip_address: User's IP address
            user_agent: User's browser/client information
            
        Returns:
            Document ID of the created audit log entry
            
        Raises:
            Exception: If audit logging fails (logged but not re-raised)
        """
        try:
            # Create audit log entry
            audit_entry = AuditLogEntry(
                user_id=user.uid,
                user_email=user.email,
                user_role=user.role.value,
                action=action,
                target_type=target_type,
                target_id=target_id,
                severity=severity,
                details=details or {},
                success=success,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Convert to dictionary for Firestore
            audit_data = audit_entry.model_dump(exclude={'id'})
            audit_data['timestamp'] = audit_entry.timestamp.isoformat()
            
            # Store in Firestore
            doc_ref = self.collection.add(audit_data)
            audit_id = doc_ref[1].id
            
            logger.info(
                f"Audit log created: {action.value}",
                extra={
                    "audit_id": audit_id,
                    "user_id": user.uid,
                    "user_email": user.email,
                    "action": action.value,
                    "target_type": target_type,
                    "target_id": target_id,
                    "severity": severity.value,
                    "success": success
                }
            )
            
            return audit_id
            
        except Exception as e:
            # Log the error but don't fail the main operation
            logger.error(
                f"Failed to create audit log: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "action": action.value,
                    "target_type": target_type,
                    "target_id": target_id,
                    "error": str(e)
                }
            )
            # Return a placeholder ID to indicate logging attempted
            return "audit_log_failed"
    
    async def log_student_action(
        self,
        user: AuthenticatedUser,
        action: AuditAction,
        student_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convenience method for logging student-related actions.
        
        Args:
            user: Authenticated user performing the action
            action: Student-related action
            student_id: ID of the student being acted upon
            details: Additional context about the action
            success: Whether the action was successful
            error_message: Error message if action failed
            request_info: HTTP request information (IP, user agent)
            
        Returns:
            Audit log document ID
        """
        # Determine severity based on action
        severity_map = {
            AuditAction.CREATE_STUDENT: AuditSeverity.MEDIUM,
            AuditAction.UPDATE_STUDENT: AuditSeverity.MEDIUM,
            AuditAction.DELETE_STUDENT: AuditSeverity.HIGH,
            AuditAction.VIEW_STUDENT: AuditSeverity.LOW,
            AuditAction.BULK_IMPORT_STUDENTS: AuditSeverity.HIGH,
            AuditAction.EXPORT_STUDENTS: AuditSeverity.MEDIUM,
        }
        
        severity = severity_map.get(action, AuditSeverity.MEDIUM)
        
        return await self.log_action(
            user=user,
            action=action,
            target_type="student",
            target_id=student_id,
            severity=severity,
            details=details,
            success=success,
            error_message=error_message,
            ip_address=request_info.get("ip_address") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
    
    async def log_file_action(
        self,
        user: AuthenticatedUser,
        action: AuditAction,
        file_id: str,
        student_id: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convenience method for logging file-related actions.
        
        Args:
            user: Authenticated user performing the action
            action: File-related action
            file_id: ID of the file being acted upon
            student_id: ID of the associated student
            file_name: Name of the file
            file_size: Size of the file in bytes
            success: Whether the action was successful
            error_message: Error message if action failed
            request_info: HTTP request information
            
        Returns:
            Audit log document ID
        """
        details = {
            "student_id": student_id,
            "file_name": file_name,
            "file_size": file_size
        }
        
        # Remove None values
        details = {k: v for k, v in details.items() if v is not None}
        
        severity = AuditSeverity.MEDIUM
        if action == AuditAction.DELETE_FILE:
            severity = AuditSeverity.HIGH
        
        return await self.log_action(
            user=user,
            action=action,
            target_type="file",
            target_id=file_id,
            severity=severity,
            details=details,
            success=success,
            error_message=error_message,
            ip_address=request_info.get("ip_address") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
    
    async def log_email_action(
        self,
        user: AuthenticatedUser,
        recipient_email: str,
        subject: str,
        template_name: Optional[str] = None,
        student_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Convenience method for logging email-related actions.
        
        Args:
            user: Authenticated user sending the email
            recipient_email: Email address of the recipient
            subject: Email subject line
            template_name: Name of email template used
            student_id: ID of associated student
            success: Whether the email was sent successfully
            error_message: Error message if sending failed
            
        Returns:
            Audit log document ID
        """
        details = {
            "recipient_email": recipient_email,
            "subject": subject,
            "template_name": template_name,
            "student_id": student_id
        }
        
        # Remove None values
        details = {k: v for k, v in details.items() if v is not None}
        
        return await self.log_action(
            user=user,
            action=AuditAction.SEND_EMAIL,
            target_type="email",
            target_id=recipient_email,
            severity=AuditSeverity.LOW,
            details=details,
            success=success,
            error_message=error_message
        )
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """
        Retrieve audit logs with filtering and pagination.
        
        Args:
            user_id: Filter by user ID
            action: Filter by action type
            target_type: Filter by target type
            target_id: Filter by target ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            List of audit log entries
        """
        try:
            query = self.collection
            
            # Apply filters
            if user_id:
                query = query.where("user_id", "==", user_id)
            
            if action:
                query = query.where("action", "==", action.value)
            
            if target_type:
                query = query.where("target_type", "==", target_type)
            
            if target_id:
                query = query.where("target_id", "==", target_id)
            
            if start_date:
                query = query.where("timestamp", ">=", start_date.isoformat())
            
            if end_date:
                query = query.where("timestamp", "<=", end_date.isoformat())
            
            # Apply ordering and pagination
            query = query.order_by("timestamp", direction="DESCENDING")
            query = query.limit(limit).offset(offset)
            
            # Execute query
            docs = query.stream()
            
            # Convert to audit log entries
            audit_logs = []
            for doc in docs:
                try:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    # Convert timestamp back to datetime
                    if 'timestamp' in data:
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    audit_logs.append(AuditLogEntry(**data))
                except Exception as e:
                    logger.warning(f"Failed to parse audit log {doc.id}: {str(e)}")
                    continue
            
            logger.info(
                f"Retrieved {len(audit_logs)} audit logs",
                extra={
                    "user_id": user_id,
                    "action": action.value if action else None,
                    "target_type": target_type,
                    "limit": limit,
                    "offset": offset
                }
            )
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {str(e)}")
            return []
    
    async def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get a summary of user activity for the specified period.
        
        Args:
            user_id: User ID to get activity for
            days: Number of days to look back
            
        Returns:
            Dictionary with activity summary statistics
        """
        try:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date.replace(day=start_date.day - days)
            
            logs = await self.get_audit_logs(
                user_id=user_id,
                start_date=start_date,
                limit=1000  # Get more logs for analysis
            )
            
            # Analyze activity
            action_counts = {}
            daily_activity = {}
            
            for log in logs:
                # Count actions
                action = log.action.value
                action_counts[action] = action_counts.get(action, 0) + 1
                
                # Count daily activity
                day = log.timestamp.date().isoformat()
                daily_activity[day] = daily_activity.get(day, 0) + 1
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_actions": len(logs),
                "action_breakdown": action_counts,
                "daily_activity": daily_activity,
                "most_active_day": max(daily_activity.items(), key=lambda x: x[1]) if daily_activity else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate user activity summary: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }


# Global audit logger instance
audit_logger = AuditLogger()


def get_request_info(request) -> Dict[str, Any]:
    """
    Extract relevant information from FastAPI request for audit logging.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dictionary with request information
    """
    try:
        return {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params) if request.query_params else {}
        }
    except Exception as e:
        logger.warning(f"Failed to extract request info: {str(e)}")
        return {}


# Decorator for automatic audit logging
def audit_action(action: AuditAction, target_type: str = "unknown"):
    """
    Decorator to automatically audit API endpoint calls.
    
    Args:
        action: The audit action to log
        target_type: Type of resource being acted upon
        
    Usage:
        @audit_action(AuditAction.CREATE_STUDENT, "student")
        async def create_student(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user and request from function arguments
            user = None
            request = None
            
            for arg in args:
                if isinstance(arg, AuthenticatedUser):
                    user = arg
                elif hasattr(arg, 'client'):  # FastAPI Request
                    request = arg
            
            # Check kwargs as well
            for key, value in kwargs.items():
                if isinstance(value, AuthenticatedUser):
                    user = value
                elif hasattr(value, 'client'):  # FastAPI Request
                    request = value
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                
                # Log successful action
                if user:
                    request_info = get_request_info(request) if request else {}
                    await audit_logger.log_action(
                        user=user,
                        action=action,
                        target_type=target_type,
                        success=True,
                        request_info=request_info
                    )
                
                return result
                
            except Exception as e:
                # Log failed action
                if user:
                    request_info = get_request_info(request) if request else {}
                    await audit_logger.log_action(
                        user=user,
                        action=action,
                        target_type=target_type,
                        success=False,
                        error_message=str(e),
                        request_info=request_info
                    )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator
