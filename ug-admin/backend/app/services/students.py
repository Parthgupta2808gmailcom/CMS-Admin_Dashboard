"""
Student service layer for business logic orchestration.

This module provides the service layer for student operations, implementing
business logic and orchestrating between the API layer and repository layer.
It will be expanded in future phases with additional business rules.
"""

from typing import List, Optional
from datetime import datetime

from app.core.errors import AppError, ValidationError, NotFoundError
from app.core.logging import get_logger
from app.schemas.student import Student, StudentCreate, StudentUpdate, StudentListResponse
from app.repositories.students import student_repository

logger = get_logger(__name__)


class StudentService:
    """
    Service layer for student business logic.
    
    This class orchestrates student operations between the API layer
    and repository layer, implementing business rules and validation
    that are independent of the data storage implementation.
    """
    
    def __init__(self):
        """Initialize the student service."""
        self.repository = student_repository
        logger.info("Student service initialized")
    
    async def create_student(self, student_data: StudentCreate) -> Student:
        """
        Create a new student with business logic validation.
        
        Args:
            student_data: Student data for creation
            
        Returns:
            Created student with system-generated fields
            
        Raises:
            ValidationError: If business rules are violated
            AppError: If creation fails
        """
        try:
            # Business logic: Validate email uniqueness
            # Note: In a production system, this would require a separate
            # query to check for existing emails. For now, we'll let the
            # repository handle any uniqueness constraints.
            
            # Business logic: Set default application status if not provided
            if not student_data.application_status:
                student_data.application_status = "Exploring"
            
            # Business logic: Update last_active timestamp
            student_data.last_active = datetime.utcnow()
            
            logger.info(
                f"Creating student: {student_data.email}",
                extra={
                    "email": student_data.email,
                    "student_name": student_data.name,
                    "country": student_data.country
                }
            )
            
            # Delegate to repository
            created_student = await self.repository.create_student(student_data)
            
            logger.info(
                f"Student created successfully: {created_student.id}",
                extra={
                    "student_id": created_student.id,
                    "email": created_student.email
                }
            )
            
            return created_student
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
            
        except AppError:
            # Re-raise application errors as-is
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in create_student service: {str(e)}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "student_email": student_data.email
                }
            )
            raise AppError(
                message="Failed to create student",
                code="INTERNAL",
                details={"error": str(e)}
            )
    
    async def get_student_by_id(self, student_id: str) -> Student:
        """
        Retrieve a student by ID with business logic.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            Student data if found
            
        Raises:
            NotFoundError: If student is not found
            AppError: If retrieval fails
        """
        try:
            # Business logic: Validate student ID format
            if not student_id or not student_id.strip():
                raise ValidationError(
                    message="Student ID cannot be empty",
                    details={"student_id": student_id}
                )
            
            logger.debug(
                f"Retrieving student: {student_id}",
                extra={"student_id": student_id}
            )
            
            # Delegate to repository
            student = await self.repository.get_student_by_id(student_id)
            
            # Business logic: Update last_active timestamp on access
            # This could be done asynchronously to avoid blocking the response
            try:
                await self._update_last_active(student_id)
            except Exception as e:
                # Log but don't fail the request if last_active update fails
                logger.warning(
                    f"Failed to update last_active for student {student_id}: {str(e)}",
                    extra={"student_id": student_id, "error": str(e)}
                )
            
            logger.info(
                f"Student retrieved successfully: {student_id}",
                extra={"student_id": student_id}
            )
            
            return student
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
            
        except NotFoundError:
            # Re-raise not found errors as-is
            raise
            
        except AppError:
            # Re-raise application errors as-is
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in get_student_by_id service: {str(e)}",
                extra={
                    "student_id": student_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise AppError(
                message="Failed to retrieve student",
                code="INTERNAL",
                details={"error": str(e), "student_id": student_id}
            )
    
    async def list_students(
        self,
        page: int = 1,
        page_size: int = 50,
        name_filter: Optional[str] = None,
        email_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> StudentListResponse:
        """
        List students with pagination, filtering, and business logic.
        
        Args:
            page: Page number (1-based)
            page_size: Number of students per page (max 100)
            name_filter: Optional name filter (partial match)
            email_filter: Optional email filter (partial match)
            status_filter: Optional application status filter
            order_by: Field to order by
            order_direction: Order direction ("asc" or "desc")
            
        Returns:
            Paginated list of students with metadata
            
        Raises:
            ValidationError: If parameters are invalid
            AppError: If listing fails
        """
        try:
            # Business logic: Validate pagination parameters
            if page < 1:
                raise ValidationError(
                    message="Page number must be 1 or greater",
                    details={"page": page}
                )
            
            if page_size < 1 or page_size > 100:
                raise ValidationError(
                    message="Page size must be between 1 and 100",
                    details={"page_size": page_size}
                )
            
            if order_by not in ["created_at", "updated_at", "name", "email", "last_active"]:
                raise ValidationError(
                    message="Invalid order_by field",
                    details={"order_by": order_by}
                )
            
            if order_direction not in ["asc", "desc"]:
                raise ValidationError(
                    message="Order direction must be 'asc' or 'desc'",
                    details={"order_direction": order_direction}
                )
            
            # Calculate offset for repository
            offset = (page - 1) * page_size
            
            logger.info(
                f"Listing students: page={page}, page_size={page_size}",
                extra={
                    "page": page,
                    "page_size": page_size,
                    "order_by": order_by,
                    "order_direction": order_direction,
                    "filters": {
                        "name": name_filter,
                        "email": email_filter,
                        "status": status_filter
                    }
                }
            )
            
            # Delegate to repository with filters
            students = await self.repository.list_students(
                limit=page_size,
                offset=offset,
                name_filter=name_filter,
                email_filter=email_filter,
                status_filter=status_filter,
                order_by=order_by,
                order_direction=order_direction
            )
            
            # Business logic: Determine if there are more pages
            # Note: This is a simplified implementation. In production,
            # you'd want to implement proper cursor-based pagination
            # or count total records for accurate pagination metadata.
            has_next = len(students) == page_size
            
            response = StudentListResponse(
                students=students,
                total_count=len(students),  # Simplified - would need separate count query
                page=page,
                page_size=page_size,
                has_next=has_next
            )
            
            logger.info(
                f"Students listed successfully: {len(students)} returned",
                extra={
                    "returned_count": len(students),
                    "page": page,
                    "page_size": page_size
                }
            )
            
            return response
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
            
        except AppError:
            # Re-raise application errors as-is
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in list_students service: {str(e)}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "page": page,
                    "page_size": page_size
                }
            )
            raise AppError(
                message="Failed to list students",
                code="INTERNAL",
                details={"error": str(e)}
            )
    
    async def update_student(self, student_id: str, update_data: StudentUpdate) -> Student:
        """
        Update a student with business logic validation.
        
        Args:
            student_id: Unique student identifier
            update_data: Partial student data for update
            
        Returns:
            Updated student data
            
        Raises:
            ValidationError: If business rules are violated
            NotFoundError: If student is not found
            AppError: If update fails
        """
        try:
            # Business logic: Validate student ID
            if not student_id or not student_id.strip():
                raise ValidationError(
                    message="Student ID cannot be empty",
                    details={"student_id": student_id}
                )
            
            # Business logic: Ensure at least one field is provided
            if not any(update_data.dict(exclude_unset=True).values()):
                raise ValidationError(
                    message="At least one field must be provided for update",
                    details={"update_data": update_data.dict()}
                )
            
            logger.info(
                f"Updating student: {student_id}",
                extra={
                    "student_id": student_id,
                    "update_fields": list(update_data.dict(exclude_unset=True).keys())
                }
            )
            
            # Delegate to repository
            updated_student = await self.repository.update_student(student_id, update_data)
            
            logger.info(
                f"Student updated successfully: {student_id}",
                extra={"student_id": student_id}
            )
            
            return updated_student
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
            
        except NotFoundError:
            # Re-raise not found errors as-is
            raise
            
        except AppError:
            # Re-raise application errors as-is
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in update_student service: {str(e)}",
                extra={
                    "student_id": student_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise AppError(
                message="Failed to update student",
                code="INTERNAL",
                details={"error": str(e), "student_id": student_id}
            )
    
    async def delete_student(self, student_id: str) -> bool:
        """
        Delete a student with business logic validation.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            True if deletion was successful
            
        Raises:
            ValidationError: If business rules are violated
            NotFoundError: If student is not found
            AppError: If deletion fails
        """
        try:
            # Business logic: Validate student ID
            if not student_id or not student_id.strip():
                raise ValidationError(
                    message="Student ID cannot be empty",
                    details={"student_id": student_id}
                )
            
            logger.info(
                f"Deleting student: {student_id}",
                extra={"student_id": student_id}
            )
            
            # Delegate to repository
            result = await self.repository.delete_student(student_id)
            
            logger.info(
                f"Student deleted successfully: {student_id}",
                extra={"student_id": student_id}
            )
            
            return result
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
            
        except NotFoundError:
            # Re-raise not found errors as-is
            raise
            
        except AppError:
            # Re-raise application errors as-is
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in delete_student service: {str(e)}",
                extra={
                    "student_id": student_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise AppError(
                message="Failed to delete student",
                code="INTERNAL",
                details={"error": str(e), "student_id": student_id}
            )
    
    async def _update_last_active(self, student_id: str) -> None:
        """
        Update the last_active timestamp for a student.
        
        This is a private method used internally to update the
        last_active timestamp when a student is accessed.
        
        Args:
            student_id: Unique student identifier
        """
        try:
            update_data = StudentUpdate(last_active=datetime.utcnow())
            await self.repository.update_student(student_id, update_data)
            
            logger.debug(
                f"Updated last_active for student: {student_id}",
                extra={"student_id": student_id}
            )
            
        except Exception as e:
            # Log but don't raise - this is a non-critical operation
            logger.warning(
                f"Failed to update last_active for student {student_id}: {str(e)}",
                extra={"student_id": student_id, "error": str(e)}
            )


# Global service instance
student_service = StudentService()
