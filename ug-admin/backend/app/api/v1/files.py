"""
API endpoints for file upload and management.

This module provides REST API endpoints for uploading, managing, and
downloading student files with proper authentication, validation,
and audit logging.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Path, Query, Request, Depends
from fastapi import status as http_status
from pydantic import BaseModel

from app.core.errors import AppError, ValidationError
from app.core.logging import get_logger, log_request_info
from app.core.auth import AuthenticatedUser, require_staff_or_admin
from app.services.file_storage import (
    file_storage_service,
    FileType,
    StoredFile,
    FileUploadResult
)

# Create router for file endpoints
router = APIRouter(prefix="/files", tags=["files"])

logger = get_logger(__name__)


class FileUploadResponse(BaseModel):
    """Response model for file upload operations."""
    
    success: bool
    message: str
    file: StoredFile
    upload_time_seconds: float


class FilesListResponse(BaseModel):
    """Response model for file listing."""
    
    success: bool
    message: str
    files: List[StoredFile]
    total_count: int


class FileDeleteResponse(BaseModel):
    """Response model for file deletion."""
    
    success: bool
    message: str


@router.post(
    "/students/{student_id}/upload",
    response_model=FileUploadResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Upload file for student",
    description="Upload a file (transcript, essay, document) for a specific student"
)
async def upload_student_file(
    student_id: str = Path(..., description="ID of the student"),
    file: UploadFile = File(..., description="File to upload"),
    file_type: FileType = Form(..., description="Type of file being uploaded"),
    description: Optional[str] = Form(None, description="Optional file description"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> FileUploadResponse:
    """
    Upload a file for a specific student.
    
    This endpoint allows staff and administrators to upload files for students
    including transcripts, essays, recommendations, and other documents.
    Files are stored securely with metadata tracking and audit logging.
    
    **Staff or Admin access required** - Staff and administrators can upload files.
    
    Supported file types:
    - PDF documents (.pdf)
    - Word documents (.doc, .docx)
    - Text files (.txt)
    - Images (.jpg, .jpeg, .png, .gif)
    - Excel files (.xls, .xlsx)
    
    Args:
        student_id: ID of the student to upload file for
        file: File to upload (max 50MB)
        file_type: Type of file (transcript, essay, recommendation, etc.)
        description: Optional description of the file
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Upload result with file metadata and upload statistics
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="upload_student_file",
        message="File upload requested",
        extra={
            "student_id": student_id,
            "file_name": file.filename,
            "file_size": file.size,
            "file_type": file_type.value,
            "content_type": file.content_type,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Validate student_id format (basic validation)
        if not student_id or len(student_id) < 3:
            raise ValidationError(
                message="Invalid student ID format",
                details={"student_id": student_id}
            )
        
        # Prepare metadata
        metadata = {}
        if description:
            metadata["description"] = description
        
        # Upload file
        upload_result = await file_storage_service.upload_file(
            file=file,
            student_id=student_id,
            file_type=file_type,
            user=current_user,
            metadata=metadata
        )
        
        logger.info(
            f"File uploaded successfully: {upload_result.file.id}",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "student_id": student_id,
                "file_id": upload_result.file.id,
                "file_name": upload_result.file.original_filename,
                "file_size": upload_result.file.file_size,
                "upload_time": upload_result.upload_time_seconds
            }
        )
        
        return FileUploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded successfully",
            file=upload_result.file,
            upload_time_seconds=upload_result.upload_time_seconds
        )
        
    except ValidationError as e:
        logger.warning(
            f"File upload validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "upload_student_file",
                "user": current_user.uid,
                "student_id": student_id,
                "file_name": file.filename
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "File upload validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"File upload application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "upload_student_file",
                "user": current_user.uid,
                "student_id": student_id,
                "file_name": file.filename
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "File upload failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/students/{student_id}",
    response_model=FilesListResponse,
    summary="List student files",
    description="Get all files for a specific student with optional filtering by file type"
)
async def list_student_files(
    student_id: str = Path(..., description="ID of the student"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> FilesListResponse:
    """
    List all files for a specific student.
    
    This endpoint retrieves all files associated with a student,
    with optional filtering by file type. Files are returned
    in reverse chronological order (newest first).
    
    **Staff or Admin access required** - Staff and administrators can view files.
    
    Args:
        student_id: ID of the student
        file_type: Optional filter by file type
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        List of files for the student with metadata
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="list_student_files",
        message="Student files list requested",
        extra={
            "student_id": student_id,
            "file_type": file_type.value if file_type else None,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Validate student_id format
        if not student_id or len(student_id) < 3:
            raise ValidationError(
                message="Invalid student ID format",
                details={"student_id": student_id}
            )
        
        # Get student files
        files = await file_storage_service.get_student_files(
            student_id=student_id,
            user=current_user,
            file_type=file_type
        )
        
        logger.debug(
            f"Retrieved {len(files)} files for student {student_id}",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "student_id": student_id,
                "files_count": len(files),
                "file_type_filter": file_type.value if file_type else None
            }
        )
        
        return FilesListResponse(
            success=True,
            message=f"Found {len(files)} files for student",
            files=files,
            total_count=len(files)
        )
        
    except ValidationError as e:
        logger.warning(
            f"List files validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "list_student_files",
                "user": current_user.uid,
                "student_id": student_id
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "File listing validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"List files application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "list_student_files",
                "user": current_user.uid,
                "student_id": student_id
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "File listing failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/{file_id}",
    response_model=StoredFile,
    summary="Get file details",
    description="Get detailed information about a specific file"
)
async def get_file_details(
    file_id: str = Path(..., description="ID of the file"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> StoredFile:
    """
    Get detailed information about a specific file.
    
    This endpoint retrieves comprehensive metadata about a file
    including upload information, file properties, and storage details.
    
    **Staff or Admin access required** - Staff and administrators can view file details.
    
    Args:
        file_id: ID of the file
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Detailed file information and metadata
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      404 if file not found, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="get_file_details",
        message="File details requested",
        extra={
            "file_id": file_id,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Get file details
        file_details = await file_storage_service.get_file_by_id(
            file_id=file_id,
            user=current_user
        )
        
        if not file_details:
            logger.warning(
                f"File not found: {file_id}",
                extra={
                    "user": current_user.uid,
                    "file_id": file_id,
                    "endpoint": "get_file_details"
                }
            )
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File not found",
                    "message": f"File with ID '{file_id}' does not exist",
                    "file_id": file_id
                }
            )
        
        logger.debug(
            f"File details retrieved: {file_id}",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "file_id": file_id,
                "student_id": file_details.student_id,
                "file_name": file_details.original_filename
            }
        )
        
        return file_details
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except AppError as e:
        logger.error(
            f"Get file details application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "get_file_details",
                "user": current_user.uid,
                "file_id": file_id
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to get file details",
                "message": e.message,
                "code": e.code
            }
        )


@router.delete(
    "/{file_id}",
    response_model=FileDeleteResponse,
    summary="Delete file",
    description="Delete a file (soft delete - marks as deleted but preserves metadata)"
)
async def delete_file(
    file_id: str = Path(..., description="ID of the file to delete"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> FileDeleteResponse:
    """
    Delete a file (soft delete).
    
    This endpoint performs a soft delete on a file, marking it as deleted
    while preserving the metadata for audit purposes. The file will no longer
    appear in file listings but the audit trail is maintained.
    
    **Staff or Admin access required** - Staff and administrators can delete files.
    
    Args:
        file_id: ID of the file to delete
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Confirmation of successful deletion
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      404 if file not found, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="delete_file",
        message="File deletion requested",
        extra={
            "file_id": file_id,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Delete file
        success = await file_storage_service.delete_file(
            file_id=file_id,
            user=current_user
        )
        
        if not success:
            logger.warning(
                f"File deletion failed: {file_id}",
                extra={
                    "user": current_user.uid,
                    "file_id": file_id,
                    "endpoint": "delete_file"
                }
            )
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File not found or deletion failed",
                    "message": f"Could not delete file with ID '{file_id}'",
                    "file_id": file_id
                }
            )
        
        logger.info(
            f"File deleted successfully: {file_id}",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "file_id": file_id,
                "endpoint": "delete_file"
            }
        )
        
        return FileDeleteResponse(
            success=True,
            message=f"File '{file_id}' deleted successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except AppError as e:
        logger.error(
            f"Delete file application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "delete_file",
                "user": current_user.uid,
                "file_id": file_id
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "File deletion failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/storage/statistics",
    summary="Get storage statistics",
    description="Get storage usage statistics and file analytics"
)
async def get_storage_statistics(
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
):
    """
    Get storage usage statistics.
    
    This endpoint provides comprehensive statistics about file storage
    including total files, storage usage, file type distribution,
    and other analytics for monitoring and reporting.
    
    **Staff or Admin access required** - Staff and administrators can view statistics.
    
    Args:
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Storage statistics and analytics
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="get_storage_statistics",
        message="Storage statistics requested",
        extra={
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Get storage statistics
        stats = await file_storage_service.get_storage_statistics(
            user=current_user
        )
        
        logger.debug(
            f"Storage statistics generated",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "total_files": stats.get("total_files", 0),
                "total_size_mb": stats.get("total_size_bytes", 0) / (1024 * 1024)
            }
        )
        
        return {
            "success": True,
            "message": "Storage statistics retrieved successfully",
            "statistics": stats
        }
        
    except AppError as e:
        logger.error(
            f"Storage statistics application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "get_storage_statistics",
                "user": current_user.uid
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to get storage statistics",
                "message": e.message,
                "code": e.code
            }
        )
