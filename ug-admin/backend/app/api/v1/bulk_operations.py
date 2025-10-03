"""
API endpoints for bulk operations (import/export).

This module provides REST API endpoints for bulk importing and exporting
student data with proper authentication, validation, and audit logging.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Request, Depends
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from app.core.errors import AppError, ValidationError
from app.core.logging import get_logger, log_request_info
from app.core.auth import AuthenticatedUser, require_admin, require_staff_or_admin
from app.services.bulk_operations import (
    bulk_operations_service, 
    ImportFormat, 
    ExportFormat, 
    ImportResult
)

# Create router for bulk operations endpoints
router = APIRouter(prefix="/bulk", tags=["bulk-operations"])

logger = get_logger(__name__)


class BulkImportResponse(BaseModel):
    """Response model for bulk import operations."""
    
    success: bool
    message: str
    import_result: ImportResult


class BulkExportResponse(BaseModel):
    """Response model for bulk export operations."""
    
    success: bool
    message: str
    total_students: int
    file_size_bytes: int
    processing_time_seconds: float


@router.post(
    "/import",
    response_model=BulkImportResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Bulk import students from CSV/JSON",
    description="Import multiple students from uploaded CSV or JSON file with validation and error reporting"
)
async def bulk_import_students(
    request: Request,
    file: UploadFile = File(..., description="CSV or JSON file containing student data"),
    format_type: Optional[ImportFormat] = Form(None, description="File format (auto-detected if not specified)"),
    validate_only: bool = Form(False, description="Only validate data without creating students"),
    current_user: AuthenticatedUser = Depends(require_admin)
) -> BulkImportResponse:
    """
    Import multiple students from uploaded file.
    
    This endpoint allows administrators to bulk import student data from CSV or JSON files.
    The import process includes comprehensive validation, error reporting per row,
    and audit logging for compliance.
    
    **Admin access required** - Only administrators can perform bulk imports.
    
    Args:
        request: FastAPI request object for logging
        file: Uploaded file containing student data
        format_type: File format (CSV or JSON), auto-detected if not specified
        validate_only: If true, only validates data without creating students
        current_user: Authenticated admin user
        
    Returns:
        Import result with success/failure statistics and detailed error reports
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="bulk_import_students",
        message="Bulk import requested",
        extra={
            "file_name": file.filename,
            "file_size": file.size,
            "format_type": format_type.value if format_type else "auto-detect",
            "validate_only": validate_only,
            "admin_user": current_user.uid
        }
    )
    
    try:
        # Validate file upload
        if not file.filename:
            raise ValidationError(
                message="No file uploaded",
                details={"required": "CSV or JSON file"}
            )
        
        if file.size == 0:
            raise ValidationError(
                message="Uploaded file is empty",
                details={"file_name": file.filename}
            )
        
        # Perform bulk import
        import_result = await bulk_operations_service.import_students_from_file(
            file=file,
            user=current_user,
            format_type=format_type,
            validate_only=validate_only
        )
        
        # Determine success based on results
        success = import_result.failed_imports == 0
        
        if success:
            message = f"Successfully imported {import_result.successful_imports} students"
            if validate_only:
                message = f"Validation successful: {import_result.successful_imports} valid records"
        else:
            message = f"Import completed with errors: {import_result.successful_imports} successful, {import_result.failed_imports} failed"
        
        logger.info(
            f"Bulk import completed: {import_result.success_rate:.1f}% success rate",
            extra={
                "admin_user": current_user.uid,
                "file_name": file.filename,
                "total_rows": import_result.total_rows,
                "successful": import_result.successful_imports,
                "failed": import_result.failed_imports,
                "processing_time": import_result.processing_time_seconds
            }
        )
        
        return BulkImportResponse(
            success=success,
            message=message,
            import_result=import_result
        )
        
    except ValidationError as e:
        logger.warning(
            f"Bulk import validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "bulk_import_students",
                "admin_user": current_user.uid,
                "file_name": file.filename
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
            f"Bulk import application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "bulk_import_students",
                "admin_user": current_user.uid,
                "file_name": file.filename
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Import operation failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/export",
    summary="Export students to CSV/JSON",
    description="Export student data in CSV or JSON format with optional filtering"
)
async def export_students(
    request: Request,
    format_type: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    application_status: Optional[str] = Query(None, description="Filter by application status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    include_fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> StreamingResponse:
    """
    Export student data in specified format.
    
    This endpoint allows staff and administrators to export student data
    with optional filtering and field selection. The export includes
    audit logging for compliance tracking.
    
    **Staff or Admin access required** - Staff and administrators can export data.
    
    Args:
        request: FastAPI request object for logging
        format_type: Export format (CSV or JSON)
        application_status: Optional filter by application status
        country: Optional filter by country
        start_date: Optional filter by start date
        end_date: Optional filter by end date
        include_fields: Optional comma-separated list of fields to include
        current_user: Authenticated user (staff or admin)
        
    Returns:
        StreamingResponse with exported file content
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="export_students",
        message="Student export requested",
        extra={
            "format_type": format_type.value,
            "application_status": application_status,
            "country": country,
            "start_date": start_date,
            "end_date": end_date,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Build filters
        filters = {}
        if application_status:
            filters["application_status"] = application_status
        if country:
            filters["country"] = country
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        
        # Parse include_fields
        fields_list = None
        if include_fields:
            fields_list = [field.strip() for field in include_fields.split(",")]
        
        # Perform export
        file_content, export_result = await bulk_operations_service.export_students(
            user=current_user,
            format_type=format_type,
            filters=filters,
            include_fields=fields_list
        )
        
        # Determine content type and filename
        if format_type == ExportFormat.CSV:
            content_type = "text/csv"
            filename = f"students_export_{export_result.total_students}_records.csv"
        else:
            content_type = "application/json"
            filename = f"students_export_{export_result.total_students}_records.json"
        
        logger.info(
            f"Student export completed: {export_result.total_students} students",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "format": format_type.value,
                "total_students": export_result.total_students,
                "file_size": export_result.file_size_bytes,
                "processing_time": export_result.processing_time_seconds,
                "filters": filters
            }
        )
        
        # Create streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except ValidationError as e:
        logger.warning(
            f"Export validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "export_students",
                "user": current_user.uid,
                "format": format_type.value
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
            f"Export application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "export_students",
                "user": current_user.uid,
                "format": format_type.value
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Export operation failed",
                "message": e.message,
                "code": e.code
            }
        )
