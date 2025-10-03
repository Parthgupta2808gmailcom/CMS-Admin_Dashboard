"""
Student repository for Firestore data access.

This module implements the repository pattern for student data operations,
providing a clean abstraction layer over Firestore with proper error handling
and data validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from google.cloud.firestore import CollectionReference, DocumentReference
from google.api_core import exceptions as gcp_exceptions

from app.core.db import get_firestore_collection
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger
from app.schemas.student import Student, StudentCreate, StudentUpdate

logger = get_logger(__name__)

# Firestore collection name for students
STUDENTS_COLLECTION = "students"


class StudentRepository:
    """
    Repository for student data operations in Firestore.
    
    This class provides CRUD operations for student data with proper
    error handling, validation, and logging. It follows the repository
    pattern to abstract Firestore-specific implementation details.
    """
    
    def __init__(self):
        """Initialize the student repository."""
        self.collection: CollectionReference = get_firestore_collection(STUDENTS_COLLECTION)
        logger.info(f"Student repository initialized for collection: {STUDENTS_COLLECTION}")
    
    async def create_student(self, student_data: StudentCreate) -> Student:
        """
        Create a new student record in Firestore.
        
        Args:
            student_data: Student data for creation
            
        Returns:
            Created student with generated ID and timestamps
            
        Raises:
            AppError: If student creation fails
        """
        try:
            # Generate document ID (Firestore will auto-generate if not provided)
            doc_ref = self.collection.document()
            student_id = doc_ref.id
            
            # Prepare document data with timestamps
            now = datetime.utcnow()
            doc_data = {
                **student_data.dict(),
                "id": student_id,
                "created_at": now,
                "updated_at": now,
            }
            
            # Create document in Firestore
            doc_ref.set(doc_data)
            
            # Retrieve the created document to ensure consistency
            created_student = Student(**doc_data)
            
            logger.info(
                f"Student created successfully: {student_id}",
                extra={
                    "student_id": student_id,
                    "email": student_data.email,
                    "student_name": student_data.name
                }
            )
            
            return created_student
            
        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                f"Permission denied creating student: {str(e)}",
                extra={"error": str(e)}
            )
            raise AppError(
                message="Permission denied creating student",
                code="AUTH",
                details={"error": str(e)}
            )
            
        except gcp_exceptions.ServiceUnavailable as e:
            logger.error(
                f"Service unavailable creating student: {str(e)}",
                extra={"error": str(e)}
            )
            raise AppError(
                message="Service unavailable creating student",
                code="INTERNAL",
                details={"error": str(e)}
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error creating student: {str(e)}",
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
        Retrieve a student by their ID.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            Student data if found
            
        Raises:
            NotFoundError: If student is not found
            AppError: If retrieval fails
        """
        try:
            doc_ref: DocumentReference = self.collection.document(student_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(
                    f"Student not found: {student_id}",
                    extra={"student_id": student_id}
                )
                raise NotFoundError(
                    message=f"Student not found: {student_id}",
                    details={"student_id": student_id}
                )
            
            # Convert Firestore document to Student model
            student_data = doc.to_dict()
            student = Student(**student_data)
            
            logger.debug(
                f"Student retrieved successfully: {student_id}",
                extra={"student_id": student_id}
            )
            
            return student
            
        except NotFoundError:
            # Re-raise NotFoundError as-is
            raise
            
        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                f"Permission denied retrieving student: {str(e)}",
                extra={"student_id": student_id, "error": str(e)}
            )
            raise AppError(
                message="Permission denied retrieving student",
                code="AUTH",
                details={"error": str(e), "student_id": student_id}
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving student: {str(e)}",
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
        limit: int = 50,
        offset: int = 0,
        name_filter: Optional[str] = None,
        email_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[Student]:
        """
        List students with pagination, filtering, and ordering.
        
        Args:
            limit: Maximum number of students to return (default: 50, max: 100)
            offset: Number of students to skip (default: 0)
            name_filter: Optional name filter (partial match)
            email_filter: Optional email filter (partial match)
            status_filter: Optional application status filter
            order_by: Field to order by (default: "created_at")
            order_direction: Order direction - "asc" or "desc" (default: "desc")
            
        Returns:
            List of students matching the criteria
            
        Raises:
            AppError: If listing fails
        """
        try:
            # Validate and constrain limit
            limit = min(max(limit, 1), 100)
            offset = max(offset, 0)
            
            # Build query with filtering
            query = self.collection
            
            # Apply filters
            if name_filter:
                # Note: Firestore doesn't support full-text search natively
                # This is a simplified implementation for demonstration
                # In production, you'd use Firestore's array-contains or
                # implement full-text search with Algolia/Elasticsearch
                query = query.where("name", ">=", name_filter).where("name", "<=", name_filter + "\uf8ff")
            
            if email_filter:
                query = query.where("email", ">=", email_filter).where("email", "<=", email_filter + "\uf8ff")
            
            if status_filter:
                query = query.where("application_status", "==", status_filter)
            
            # Apply ordering (convert direction to Firestore format)
            firestore_direction = "ASCENDING" if order_direction.lower() == "asc" else "DESCENDING"
            query = query.order_by(order_by, direction=firestore_direction)
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            docs = query.stream()
            
            # Convert documents to Student models
            students = []
            for doc in docs:
                try:
                    student_data = doc.to_dict()
                    student = Student(**student_data)
                    students.append(student)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse student document: {doc.id}",
                        extra={
                            "document_id": doc.id,
                            "error": str(e)
                        }
                    )
                    # Continue processing other documents
                    continue
            
            logger.info(
                f"Listed {len(students)} students",
                extra={
                    "limit": limit,
                    "offset": offset,
                    "order_by": order_by,
                    "order_direction": order_direction,
                    "returned_count": len(students),
                    "filters": {
                        "name": name_filter,
                        "email": email_filter,
                        "status": status_filter
                    }
                }
            )
            
            return students
            
        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                f"Permission denied listing students: {str(e)}",
                extra={"error": str(e)}
            )
            raise AppError(
                message="Permission denied listing students",
                code="AUTH",
                details={"error": str(e)}
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error listing students: {str(e)}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "limit": limit,
                    "offset": offset
                }
            )
            raise AppError(
                message="Failed to list students",
                code="INTERNAL",
                details={"error": str(e)}
            )
    
    async def update_student(self, student_id: str, update_data: StudentUpdate) -> Student:
        """
        Update a student record with partial data.
        
        Args:
            student_id: Unique student identifier
            update_data: Partial student data for update
            
        Returns:
            Updated student data
            
        Raises:
            NotFoundError: If student is not found
            AppError: If update fails
        """
        try:
            doc_ref: DocumentReference = self.collection.document(student_id)
            
            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                logger.warning(
                    f"Student not found for update: {student_id}",
                    extra={"student_id": student_id}
                )
                raise NotFoundError(
                    message=f"Student not found: {student_id}",
                    details={"student_id": student_id}
                )
            
            # Prepare update data with timestamp
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update document in Firestore
            doc_ref.update(update_dict)
            
            # Retrieve updated document
            updated_doc = doc_ref.get()
            updated_data = updated_doc.to_dict()
            updated_student = Student(**updated_data)
            
            logger.info(
                f"Student updated successfully: {student_id}",
                extra={
                    "student_id": student_id,
                    "updated_fields": list(update_dict.keys())
                }
            )
            
            return updated_student
            
        except NotFoundError:
            # Re-raise NotFoundError as-is
            raise
            
        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                f"Permission denied updating student: {str(e)}",
                extra={"student_id": student_id, "error": str(e)}
            )
            raise AppError(
                message="Permission denied updating student",
                code="AUTH",
                details={"error": str(e), "student_id": student_id}
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error updating student: {str(e)}",
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
        Delete a student record.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            True if deletion was successful
            
        Raises:
            NotFoundError: If student is not found
            AppError: If deletion fails
        """
        try:
            doc_ref: DocumentReference = self.collection.document(student_id)
            
            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                logger.warning(
                    f"Student not found for deletion: {student_id}",
                    extra={"student_id": student_id}
                )
                raise NotFoundError(
                    message=f"Student not found: {student_id}",
                    details={"student_id": student_id}
                )
            
            # Delete document
            doc_ref.delete()
            
            logger.info(
                f"Student deleted successfully: {student_id}",
                extra={"student_id": student_id}
            )
            
            return True
            
        except NotFoundError:
            # Re-raise NotFoundError as-is
            raise
            
        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                f"Permission denied deleting student: {str(e)}",
                extra={"student_id": student_id, "error": str(e)}
            )
            raise AppError(
                message="Permission denied deleting student",
                code="AUTH",
                details={"error": str(e), "student_id": student_id}
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error deleting student: {str(e)}",
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


# Global repository instance
student_repository = StudentRepository()
