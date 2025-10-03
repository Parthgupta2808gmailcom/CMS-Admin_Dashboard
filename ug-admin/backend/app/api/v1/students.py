"""
Student API endpoints for CRUD operations.

This module provides RESTful API endpoints for managing student data,
including creation, retrieval, updates, and deletion with proper
validation, error handling, and pagination support.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi import status as http_status
from pydantic import BaseModel

from app.core.errors import AppError, NotFoundError, ValidationError
from app.core.logging import get_logger, log_request_info
from app.core.auth import (
    AuthenticatedUser,
    UserRole,
    require_admin,
    require_staff_or_admin,
    require_any_authenticated
)
from app.schemas.student import (
    Student, 
    StudentCreate, 
    StudentUpdate, 
    StudentListResponse,
    ApplicationStatus
)
from app.services.students import student_service

# Create router for student endpoints
router = APIRouter(prefix="/students", tags=["students"])

logger = get_logger(__name__)


class StudentResponse(BaseModel):
    """Standard student response model."""
    student: Student
    message: str = "Operation successful"


class StudentsListResponse(BaseModel):
    """Response model for student list operations."""
    students: List[Student]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    message: str = "Students retrieved successfully"


class MessageResponse(BaseModel):
    """Standard message response model."""
    message: str
    student_id: Optional[str] = None


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a new student",
    description="Create a new student record with validation and business rules"
)
async def create_student(
    student_data: StudentCreate,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> StudentResponse:
    """
    Create a new student record.
    
    This endpoint creates a new student with comprehensive validation,
    business rule enforcement, and proper error handling.
    
    Args:
        student_data: Student creation data
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin required)
        
    Returns:
        Created student with system-generated fields
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors, 
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="create_student",
        message="Student creation requested",
        extra={
            "email": student_data.email, 
            "student_name": student_data.name,
            "created_by_user": current_user.uid,
            "created_by_role": current_user.role.value
        }
    )
    
    try:
        # Create student through service layer
        created_student = await student_service.create_student(student_data)
        
        logger.info(
            f"Student created successfully via API: {created_student.id}",
            extra={
                "student_id": created_student.id,
                "email": created_student.email,
                "endpoint": "create_student"
            }
        )
        
        return StudentResponse(
            student=created_student,
            message="Student created successfully"
        )
        
    except ValidationError as e:
        logger.warning(
            f"Validation error creating student: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "create_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "message": e.message,
                "details": e.details
            }
        )
        
    except AppError as e:
        logger.error(
            f"Application error creating student: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "create_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to create student",
                "code": e.code
            }
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error creating student: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": "create_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.get(
    "/",
    response_model=StudentsListResponse,
    summary="List students with pagination and filtering",
    description="Retrieve a paginated list of students with optional filtering by name, email, and status"
)
async def list_students(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of students per page"),
    name: Optional[str] = Query(None, description="Filter by student name (partial match)"),
    email: Optional[str] = Query(None, description="Filter by student email (partial match)"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    order_by: str = Query("created_at", description="Field to order by"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$", description="Order direction")
) -> StudentsListResponse:
    """
    List students with pagination and filtering.
    
    This endpoint provides a paginated list of students with optional
    filtering capabilities and flexible ordering.
    
    Args:
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin required)
        page: Page number (1-based)
        page_size: Number of students per page (1-100)
        name: Optional name filter (partial match)
        email: Optional email filter (partial match)
        status: Optional application status filter
        order_by: Field to order by
        order_direction: Order direction (asc/desc)
        
    Returns:
        Paginated list of students with metadata
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="list_students",
        message="Student list requested",
        extra={
            "page": page,
            "page_size": page_size,
            "filters": {
                "name": name,
                "email": email,
                "status": status
            },
            "requested_by_user": current_user.uid,
            "requested_by_role": current_user.role.value
        }
    )
    
    try:
        # Get students through service layer
        result = await student_service.list_students(
            page=page,
            page_size=page_size,
            name_filter=name,
            email_filter=email,
            status_filter=status,
            order_by=order_by,
            order_direction=order_direction
        )
        
        logger.info(
            f"Students listed successfully: {len(result.students)} returned",
            extra={
                "returned_count": len(result.students),
                "page": page,
                "page_size": page_size,
                "endpoint": "list_students"
            }
        )
        
        return StudentsListResponse(
            students=result.students,
            total_count=result.total_count,
            page=result.page,
            page_size=result.page_size,
            has_next=result.has_next,
            message=f"Retrieved {len(result.students)} students"
        )
        
    except ValidationError as e:
        logger.warning(
            f"Validation error listing students: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "list_students"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "message": e.message,
                "details": e.details
            }
        )
        
    except AppError as e:
        logger.error(
            f"Application error listing students: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "list_students"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to list students",
                "code": e.code
            }
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error listing students: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": "list_students"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Get student by ID",
    description="Retrieve a specific student by their unique identifier"
)
async def get_student(
    student_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> StudentResponse:
    """
    Get a student by their ID.
    
    This endpoint retrieves a specific student record by ID with
    proper error handling for not found cases.
    
    Args:
        student_id: Unique student identifier
        request: FastAPI request object for logging
        
    Returns:
        Student data if found
        
    Raises:
        HTTPException: 404 if student not found, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="get_student",
        message="Student retrieval requested",
        extra={"student_id": student_id}
    )
    
    try:
        # Get student through service layer
        student = await student_service.get_student_by_id(student_id)
        
        logger.info(
            f"Student retrieved successfully via API: {student_id}",
            extra={
                "student_id": student_id,
                "endpoint": "get_student"
            }
        )
        
        return StudentResponse(
            student=student,
            message="Student retrieved successfully"
        )
        
    except NotFoundError as e:
        logger.warning(
            f"Student not found: {student_id}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "endpoint": "get_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Student not found",
                "message": f"Student with ID {student_id} does not exist",
                "student_id": student_id
            }
        )
        
    except ValidationError as e:
        logger.warning(
            f"Validation error getting student: {e.message}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "details": e.details,
                "endpoint": "get_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "message": e.message,
                "details": e.details
            }
        )
        
    except AppError as e:
        logger.error(
            f"Application error getting student: {e.message}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "get_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to retrieve student",
                "code": e.code
            }
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error getting student: {str(e)}",
            extra={
                "student_id": student_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": "get_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Update student",
    description="Update a student record with partial updates allowed"
)
async def update_student(
    student_id: str,
    update_data: StudentUpdate,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> StudentResponse:
    """
    Update a student record.
    
    This endpoint allows partial updates of student information with
    proper validation and business rule enforcement.
    
    Args:
        student_id: Unique student identifier
        update_data: Partial student data for update
        request: FastAPI request object for logging
        current_user: Authenticated user (admin required)
        
    Returns:
        Updated student data
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      404 if student not found, 400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="update_student",
        message="Student update requested",
        extra={
            "student_id": student_id,
            "update_fields": list(update_data.model_dump(exclude_unset=True).keys())
        }
    )
    
    try:
        # Update student through service layer
        updated_student = await student_service.update_student(student_id, update_data)
        
        logger.info(
            f"Student updated successfully via API: {student_id}",
            extra={
                "student_id": student_id,
                "updated_fields": list(update_data.model_dump(exclude_unset=True).keys()),
                "endpoint": "update_student"
            }
        )
        
        return StudentResponse(
            student=updated_student,
            message="Student updated successfully"
        )
        
    except NotFoundError as e:
        logger.warning(
            f"Student not found for update: {student_id}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "endpoint": "update_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Student not found",
                "message": f"Student with ID {student_id} does not exist",
                "student_id": student_id
            }
        )
        
    except ValidationError as e:
        logger.warning(
            f"Validation error updating student: {e.message}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "details": e.details,
                "endpoint": "update_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "message": e.message,
                "details": e.details
            }
        )
        
    except AppError as e:
        logger.error(
            f"Application error updating student: {e.message}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "update_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to update student",
                "code": e.code
            }
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error updating student: {str(e)}",
            extra={
                "student_id": student_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": "update_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.delete(
    "/{student_id}",
    response_model=MessageResponse,
    summary="Delete student",
    description="Delete a student record permanently"
)
async def delete_student(
    student_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> MessageResponse:
    """
    Delete a student record.
    
    This endpoint permanently deletes a student record with proper
    validation and error handling.
    
    Args:
        student_id: Unique student identifier
        request: FastAPI request object for logging
        current_user: Authenticated user (admin required)
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      404 if student not found, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="delete_student",
        message="Student deletion requested",
        extra={"student_id": student_id}
    )
    
    try:
        # Delete student through service layer
        await student_service.delete_student(student_id)
        
        logger.info(
            f"Student deleted successfully via API: {student_id}",
            extra={
                "student_id": student_id,
                "endpoint": "delete_student"
            }
        )
        
        return MessageResponse(
            message="Student deleted successfully",
            student_id=student_id
        )
        
    except NotFoundError as e:
        logger.warning(
            f"Student not found for deletion: {student_id}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "endpoint": "delete_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Student not found",
                "message": f"Student with ID {student_id} does not exist",
                "student_id": student_id
            }
        )
        
    except ValidationError as e:
        logger.warning(
            f"Validation error deleting student: {e.message}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "details": e.details,
                "endpoint": "delete_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "message": e.message,
                "details": e.details
            }
        )
        
    except AppError as e:
        logger.error(
            f"Application error deleting student: {e.message}",
            extra={
                "student_id": student_id,
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "delete_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to delete student",
                "code": e.code
            }
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error deleting student: {str(e)}",
            extra={
                "student_id": student_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": "delete_student"
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )
