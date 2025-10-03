"""
Bulk operations service for efficient student data import/export.

This module provides functionality for bulk importing students from CSV/JSON
and exporting student data in various formats with proper validation,
error reporting, and audit logging.
"""

import csv
import json
import io
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ValidationError as PydanticValidationError
from fastapi import UploadFile

from app.core.logging import get_logger
from app.core.errors import AppError, ValidationError
from app.core.audit import audit_logger, AuditAction
from app.core.auth import AuthenticatedUser
from app.schemas.student import StudentCreate, Student, ApplicationStatus
from app.services.students import student_service

logger = get_logger(__name__)


class ImportFormat(str, Enum):
    """Supported import file formats."""
    CSV = "csv"
    JSON = "json"


class ExportFormat(str, Enum):
    """Supported export file formats."""
    CSV = "csv"
    JSON = "json"


class ImportResult(BaseModel):
    """Result of a bulk import operation."""
    
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]]
    created_student_ids: List[str]
    processing_time_seconds: float
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.successful_imports / self.total_rows) * 100


class ImportError(BaseModel):
    """Individual import error for a specific row."""
    
    row_number: int
    row_data: Dict[str, Any]
    error_type: str
    error_message: str
    field_errors: Optional[Dict[str, str]] = None


class ExportResult(BaseModel):
    """Result of a bulk export operation."""
    
    total_students: int
    export_format: ExportFormat
    file_size_bytes: int
    processing_time_seconds: float
    filters_applied: Dict[str, Any]


class BulkOperationsService:
    """
    Service for handling bulk import and export operations.
    
    This service provides methods for importing students from CSV/JSON files
    and exporting student data in various formats with comprehensive
    validation, error handling, and audit logging.
    """
    
    def __init__(self):
        """Initialize the bulk operations service."""
        self.max_import_rows = 1000  # Configurable limit
        self.supported_csv_headers = {
            "name", "email", "phone", "country", "grade", 
            "application_status", "last_active"
        }
        logger.info("BulkOperationsService initialized")
    
    async def import_students_from_file(
        self,
        file: UploadFile,
        user: AuthenticatedUser,
        format_type: Optional[ImportFormat] = None,
        validate_only: bool = False
    ) -> ImportResult:
        """
        Import students from uploaded CSV or JSON file.
        
        Args:
            file: Uploaded file containing student data
            user: Authenticated user performing the import
            format_type: File format (auto-detected if None)
            validate_only: If True, only validate without creating students
            
        Returns:
            ImportResult with success/failure statistics and errors
            
        Raises:
            ValidationError: If file format is invalid or unsupported
            AppError: If import operation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Detect file format if not specified
            if format_type is None:
                format_type = self._detect_file_format(file.filename)
            
            logger.info(
                f"Starting bulk import: {file.filename}",
                extra={
                    "user_id": user.uid,
                    "format": format_type.value,
                    "validate_only": validate_only,
                    "file_size": file.size
                }
            )
            
            # Read and parse file content
            content = await file.read()
            
            if format_type == ImportFormat.CSV:
                student_data_list = await self._parse_csv_content(content)
            elif format_type == ImportFormat.JSON:
                student_data_list = await self._parse_json_content(content)
            else:
                raise ValidationError(
                    message=f"Unsupported import format: {format_type}",
                    details={"supported_formats": [f.value for f in ImportFormat]}
                )
            
            # Validate row count
            if len(student_data_list) > self.max_import_rows:
                raise ValidationError(
                    message=f"Import file contains too many rows: {len(student_data_list)}",
                    details={
                        "max_allowed": self.max_import_rows,
                        "actual_count": len(student_data_list)
                    }
                )
            
            # Process each row
            import_result = await self._process_import_rows(
                student_data_list, user, validate_only
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            import_result.processing_time_seconds = processing_time
            
            # Log audit event
            await audit_logger.log_student_action(
                user=user,
                action=AuditAction.BULK_IMPORT_STUDENTS,
                details={
                    "file_name": file.filename,
                    "format": format_type.value,
                    "total_rows": import_result.total_rows,
                    "successful_imports": import_result.successful_imports,
                    "failed_imports": import_result.failed_imports,
                    "validate_only": validate_only,
                    "processing_time_seconds": processing_time
                },
                success=import_result.failed_imports == 0
            )
            
            logger.info(
                f"Bulk import completed: {import_result.successful_imports}/{import_result.total_rows} successful",
                extra={
                    "user_id": user.uid,
                    "file_name": file.filename,
                    "success_rate": import_result.success_rate,
                    "processing_time": processing_time
                }
            )
            
            return import_result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log failed audit event
            await audit_logger.log_student_action(
                user=user,
                action=AuditAction.BULK_IMPORT_STUDENTS,
                details={
                    "file_name": file.filename,
                    "error": str(e),
                    "processing_time_seconds": processing_time
                },
                success=False,
                error_message=str(e)
            )
            
            logger.error(
                f"Bulk import failed: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "file_name": file.filename,
                    "error": str(e)
                }
            )
            
            if isinstance(e, (ValidationError, AppError)):
                raise
            else:
                raise AppError(
                    message="Bulk import operation failed",
                    code="BULK_IMPORT_ERROR",
                    details={"error": str(e)}
                )
    
    async def export_students(
        self,
        user: AuthenticatedUser,
        format_type: ExportFormat = ExportFormat.CSV,
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None
    ) -> Tuple[bytes, ExportResult]:
        """
        Export student data in specified format.
        
        Args:
            user: Authenticated user performing the export
            format_type: Export format (CSV or JSON)
            filters: Optional filters to apply to student query
            include_fields: Optional list of fields to include in export
            
        Returns:
            Tuple of (file_content_bytes, ExportResult)
            
        Raises:
            AppError: If export operation fails
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Starting student export: {format_type.value}",
                extra={
                    "user_id": user.uid,
                    "format": format_type.value,
                    "filters": filters
                }
            )
            
            # Get students based on filters
            students = await self._get_students_for_export(filters or {})
            
            # Generate export content
            if format_type == ExportFormat.CSV:
                content = await self._generate_csv_export(students, include_fields)
            elif format_type == ExportFormat.JSON:
                content = await self._generate_json_export(students, include_fields)
            else:
                raise ValidationError(
                    message=f"Unsupported export format: {format_type}",
                    details={"supported_formats": [f.value for f in ExportFormat]}
                )
            
            # Calculate processing time and file size
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            file_size = len(content)
            
            # Create export result
            export_result = ExportResult(
                total_students=len(students),
                export_format=format_type,
                file_size_bytes=file_size,
                processing_time_seconds=processing_time,
                filters_applied=filters or {}
            )
            
            # Log audit event
            await audit_logger.log_student_action(
                user=user,
                action=AuditAction.EXPORT_STUDENTS,
                details={
                    "format": format_type.value,
                    "total_students": len(students),
                    "file_size_bytes": file_size,
                    "filters": filters,
                    "processing_time_seconds": processing_time
                },
                success=True
            )
            
            logger.info(
                f"Student export completed: {len(students)} students",
                extra={
                    "user_id": user.uid,
                    "format": format_type.value,
                    "file_size": file_size,
                    "processing_time": processing_time
                }
            )
            
            return content, export_result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log failed audit event
            await audit_logger.log_student_action(
                user=user,
                action=AuditAction.EXPORT_STUDENTS,
                details={
                    "format": format_type.value,
                    "error": str(e),
                    "processing_time_seconds": processing_time
                },
                success=False,
                error_message=str(e)
            )
            
            logger.error(
                f"Student export failed: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "format": format_type.value,
                    "error": str(e)
                }
            )
            
            if isinstance(e, (ValidationError, AppError)):
                raise
            else:
                raise AppError(
                    message="Student export operation failed",
                    code="EXPORT_ERROR",
                    details={"error": str(e)}
                )
    
    def _detect_file_format(self, filename: Optional[str]) -> ImportFormat:
        """Detect file format from filename extension."""
        if not filename:
            raise ValidationError(
                message="Cannot detect file format: no filename provided",
                details={"supported_extensions": [".csv", ".json"]}
            )
        
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            return ImportFormat.CSV
        elif filename_lower.endswith('.json'):
            return ImportFormat.JSON
        else:
            raise ValidationError(
                message=f"Unsupported file extension: {filename}",
                details={
                    "supported_extensions": [".csv", ".json"],
                    "detected_extension": filename.split('.')[-1] if '.' in filename else None
                }
            )
    
    async def _parse_csv_content(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV content into list of dictionaries."""
        try:
            # Decode content
            text_content = content.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(text_content))
            
            # Validate headers
            headers = set(csv_reader.fieldnames or [])
            invalid_headers = headers - self.supported_csv_headers
            
            if invalid_headers:
                logger.warning(f"Unknown CSV headers detected: {invalid_headers}")
            
            # Convert rows to list
            rows = []
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                # Clean up row data
                cleaned_row = {k: v.strip() if v else None for k, v in row.items() if k}
                # Remove empty values
                cleaned_row = {k: v for k, v in cleaned_row.items() if v is not None and v != ''}
                
                if cleaned_row:  # Only add non-empty rows
                    cleaned_row['_row_number'] = row_num
                    rows.append(cleaned_row)
            
            logger.info(f"Parsed CSV: {len(rows)} data rows")
            return rows
            
        except UnicodeDecodeError as e:
            raise ValidationError(
                message="Invalid file encoding. Please use UTF-8 encoded CSV files.",
                details={"error": str(e)}
            )
        except csv.Error as e:
            raise ValidationError(
                message="Invalid CSV format",
                details={"error": str(e)}
            )
        except Exception as e:
            raise ValidationError(
                message="Failed to parse CSV file",
                details={"error": str(e)}
            )
    
    async def _parse_json_content(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse JSON content into list of dictionaries."""
        try:
            # Decode content
            text_content = content.decode('utf-8')
            
            # Parse JSON
            data = json.loads(text_content)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of objects
                rows = data
            elif isinstance(data, dict) and 'students' in data:
                # Object with 'students' array
                rows = data['students']
            elif isinstance(data, dict):
                # Single student object
                rows = [data]
            else:
                raise ValidationError(
                    message="Invalid JSON structure. Expected array of objects or object with 'students' array.",
                    details={"received_type": type(data).__name__}
                )
            
            # Add row numbers
            for i, row in enumerate(rows):
                row['_row_number'] = i + 1
            
            logger.info(f"Parsed JSON: {len(rows)} data rows")
            return rows
            
        except UnicodeDecodeError as e:
            raise ValidationError(
                message="Invalid file encoding. Please use UTF-8 encoded JSON files.",
                details={"error": str(e)}
            )
        except json.JSONDecodeError as e:
            raise ValidationError(
                message="Invalid JSON format",
                details={"error": str(e), "line": getattr(e, 'lineno', None)}
            )
        except Exception as e:
            raise ValidationError(
                message="Failed to parse JSON file",
                details={"error": str(e)}
            )
    
    async def _process_import_rows(
        self,
        rows: List[Dict[str, Any]],
        user: AuthenticatedUser,
        validate_only: bool
    ) -> ImportResult:
        """Process import rows and create students."""
        
        total_rows = len(rows)
        successful_imports = 0
        failed_imports = 0
        errors = []
        created_student_ids = []
        
        for row in rows:
            row_number = row.pop('_row_number', 0)
            
            try:
                # Convert row to StudentCreate
                student_data = self._convert_row_to_student_create(row)
                
                if not validate_only:
                    # Create the student
                    created_student = await student_service.create_student(student_data)
                    created_student_ids.append(created_student.id)
                    
                    logger.debug(
                        f"Student created from import: {created_student.id}",
                        extra={
                            "row_number": row_number,
                            "student_email": created_student.email
                        }
                    )
                
                successful_imports += 1
                
            except PydanticValidationError as e:
                # Validation error - extract field-specific errors
                field_errors = {}
                for error in e.errors():
                    field_path = '.'.join(str(loc) for loc in error['loc'])
                    field_errors[field_path] = error['msg']
                
                import_error = ImportError(
                    row_number=row_number,
                    row_data=row,
                    error_type="ValidationError",
                    error_message="Student data validation failed",
                    field_errors=field_errors
                )
                
                errors.append(import_error.model_dump())
                failed_imports += 1
                
                logger.warning(
                    f"Validation error in row {row_number}: {field_errors}",
                    extra={"row_data": row}
                )
                
            except ValidationError as e:
                # Custom validation error
                import_error = ImportError(
                    row_number=row_number,
                    row_data=row,
                    error_type="ValidationError",
                    error_message=e.message,
                    field_errors=e.details
                )
                
                errors.append(import_error.model_dump())
                failed_imports += 1
                
                logger.warning(
                    f"Validation error in row {row_number}: {e.message}",
                    extra={"row_data": row, "error_details": e.details}
                )
                
            except Exception as e:
                # Unexpected error
                import_error = ImportError(
                    row_number=row_number,
                    row_data=row,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                errors.append(import_error.model_dump())
                failed_imports += 1
                
                logger.error(
                    f"Unexpected error in row {row_number}: {str(e)}",
                    extra={"row_data": row, "error": str(e)}
                )
        
        return ImportResult(
            total_rows=total_rows,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            errors=errors,
            created_student_ids=created_student_ids,
            processing_time_seconds=0.0  # Will be set by caller
        )
    
    def _convert_row_to_student_create(self, row: Dict[str, Any]) -> StudentCreate:
        """Convert a row dictionary to StudentCreate object."""
        
        # Map CSV/JSON fields to StudentCreate fields
        student_data = {}
        
        # Required fields
        if 'name' in row:
            student_data['name'] = row['name']
        
        if 'email' in row:
            student_data['email'] = row['email']
        
        if 'country' in row:
            student_data['country'] = row['country']
        
        # Optional fields
        if 'phone' in row:
            student_data['phone'] = row['phone']
        
        if 'grade' in row:
            student_data['grade'] = row['grade']
        
        # Handle application status
        if 'application_status' in row:
            status_value = row['application_status']
            # Try to match enum values (case insensitive)
            for status in ApplicationStatus:
                if status.value.lower() == status_value.lower():
                    student_data['application_status'] = status
                    break
            else:
                # If no match found, use the raw value and let validation handle it
                student_data['application_status'] = status_value
        
        # Handle last_active datetime
        if 'last_active' in row:
            last_active_str = row['last_active']
            try:
                # Try to parse various datetime formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        student_data['last_active'] = datetime.strptime(last_active_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If no format matches, let validation handle it
                    student_data['last_active'] = last_active_str
            except Exception:
                student_data['last_active'] = last_active_str
        
        return StudentCreate(**student_data)
    
    async def _get_students_for_export(self, filters: Dict[str, Any]) -> List[Student]:
        """Get students for export based on filters."""
        try:
            # Use the existing student service to get students
            # For now, get all students and apply basic filtering
            # In a real implementation, you'd want to push filters to the repository level
            
            students = await student_service.list_students(
                limit=10000,  # Large limit for export
                offset=0
            )
            
            # Apply additional filters if needed
            filtered_students = []
            
            for student in students:
                include_student = True
                
                # Filter by application status
                if 'application_status' in filters:
                    if student.application_status != filters['application_status']:
                        include_student = False
                
                # Filter by country
                if 'country' in filters:
                    if student.country.lower() != filters['country'].lower():
                        include_student = False
                
                # Filter by date range (last_active)
                if 'start_date' in filters and student.last_active:
                    start_date = datetime.fromisoformat(filters['start_date'])
                    if student.last_active < start_date:
                        include_student = False
                
                if 'end_date' in filters and student.last_active:
                    end_date = datetime.fromisoformat(filters['end_date'])
                    if student.last_active > end_date:
                        include_student = False
                
                if include_student:
                    filtered_students.append(student)
            
            return filtered_students
            
        except Exception as e:
            logger.error(f"Failed to get students for export: {str(e)}")
            raise AppError(
                message="Failed to retrieve students for export",
                code="EXPORT_QUERY_ERROR",
                details={"error": str(e)}
            )
    
    async def _generate_csv_export(
        self,
        students: List[Student],
        include_fields: Optional[List[str]] = None
    ) -> bytes:
        """Generate CSV export content."""
        
        # Default fields to include
        default_fields = [
            'id', 'name', 'email', 'phone', 'country', 'grade',
            'application_status', 'last_active', 'created_at', 'updated_at'
        ]
        
        fields = include_fields or default_fields
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        
        # Write header
        writer.writeheader()
        
        # Write student data
        for student in students:
            row = {}
            for field in fields:
                value = getattr(student, field, None)
                
                # Format datetime fields
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'value'):  # Enum
                    value = value.value
                
                row[field] = value
            
            writer.writerow(row)
        
        # Get CSV content as bytes
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')
    
    async def _generate_json_export(
        self,
        students: List[Student],
        include_fields: Optional[List[str]] = None
    ) -> bytes:
        """Generate JSON export content."""
        
        # Convert students to dictionaries
        students_data = []
        
        for student in students:
            student_dict = student.model_dump()
            
            # Filter fields if specified
            if include_fields:
                student_dict = {k: v for k, v in student_dict.items() if k in include_fields}
            
            students_data.append(student_dict)
        
        # Create JSON structure
        export_data = {
            "students": students_data,
            "export_info": {
                "total_count": len(students),
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json"
            }
        }
        
        # Convert to JSON bytes
        json_content = json.dumps(export_data, indent=2, default=str)
        return json_content.encode('utf-8')


# Global service instance
bulk_operations_service = BulkOperationsService()
