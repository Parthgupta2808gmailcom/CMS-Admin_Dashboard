"""
File storage service for secure file uploads and management.

This module provides functionality for uploading, storing, and managing
student files (transcripts, essays, documents) using Firebase Storage
with comprehensive validation, metadata tracking, and audit logging.
"""

import os
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import UploadFile
import firebase_admin
from firebase_admin import storage

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors import AppError, ValidationError
from app.core.audit import audit_logger, AuditAction
from app.core.auth import AuthenticatedUser
from app.core.db import get_firestore_client

logger = get_logger(__name__)


class FileType(str, Enum):
    """Supported file types for uploads."""
    TRANSCRIPT = "transcript"
    ESSAY = "essay"
    RECOMMENDATION = "recommendation"
    PORTFOLIO = "portfolio"
    CERTIFICATE = "certificate"
    OTHER = "other"


class FileStatus(str, Enum):
    """File processing status."""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class StoredFile(BaseModel):
    """Model for file metadata stored in Firestore."""
    
    id: str = Field(..., description="Unique file identifier")
    student_id: str = Field(..., description="ID of associated student")
    original_filename: str = Field(..., description="Original filename")
    storage_filename: str = Field(..., description="Filename in storage")
    file_type: FileType = Field(..., description="Type of file")
    mime_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of file content")
    storage_path: str = Field(..., description="Path in Firebase Storage")
    download_url: Optional[str] = Field(None, description="Public download URL")
    status: FileStatus = Field(FileStatus.UPLOADED, description="File processing status")
    uploaded_by: str = Field(..., description="User ID who uploaded the file")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional file metadata")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileUploadResult(BaseModel):
    """Result of a file upload operation."""
    
    file: StoredFile
    upload_time_seconds: float
    validation_results: Dict[str, Any]


class FileStorageService:
    """
    Service for managing file uploads and storage.
    
    This service handles secure file uploads to Firebase Storage with
    validation, metadata tracking, and audit logging for compliance.
    """
    
    def __init__(self):
        """Initialize the file storage service."""
        self.firestore_client = get_firestore_client()
        self.files_collection = "student_files"
        
        # File validation settings
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_mime_types = {
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/plain': ['.txt'],
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
        }
        
        # Initialize Firebase Storage
        self._initialize_storage()
        
        logger.info("FileStorageService initialized")
    
    def _initialize_storage(self):
        """Initialize Firebase Storage bucket."""
        try:
            # Get default bucket or use configured bucket
            bucket_name = getattr(settings, 'firebase_storage_bucket', None)
            
            if bucket_name:
                self.bucket = storage.bucket(bucket_name)
            else:
                self.bucket = storage.bucket()
            
            logger.info(f"Firebase Storage initialized with bucket: {self.bucket.name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Storage: {str(e)}")
            # For development, we'll create a mock bucket
            self.bucket = None
            logger.warning("Running in mock mode - files will not be actually stored")
    
    async def upload_file(
        self,
        file: UploadFile,
        student_id: str,
        file_type: FileType,
        user: AuthenticatedUser,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileUploadResult:
        """
        Upload a file for a student with validation and metadata tracking.
        
        Args:
            file: Uploaded file from FastAPI
            student_id: ID of the student this file belongs to
            file_type: Type of file being uploaded
            user: Authenticated user uploading the file
            metadata: Additional metadata for the file
            
        Returns:
            FileUploadResult with file information and upload statistics
            
        Raises:
            ValidationError: If file validation fails
            AppError: If upload operation fails
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Starting file upload: {file.filename}",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "file_type": file_type.value,
                    "file_size": file.size
                }
            )
            
            # Validate file
            validation_results = await self._validate_file(file)
            
            # Read file content
            file_content = await file.read()
            
            # Generate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check for duplicate files
            existing_file = await self._check_duplicate_file(student_id, file_hash)
            if existing_file:
                logger.warning(
                    f"Duplicate file detected: {file_hash}",
                    extra={
                        "student_id": student_id,
                        "existing_file_id": existing_file.id
                    }
                )
                # You might want to return the existing file or raise an error
                # For now, we'll continue with the upload
            
            # Generate unique filename and storage path
            file_id = str(uuid.uuid4())
            file_extension = self._get_file_extension(file.filename)
            storage_filename = f"{file_id}{file_extension}"
            storage_path = f"students/{student_id}/files/{storage_filename}"
            
            # Upload to Firebase Storage
            download_url = None
            if self.bucket:
                download_url = await self._upload_to_firebase_storage(
                    file_content, storage_path, file.content_type
                )
            else:
                # Mock upload for development
                download_url = f"mock://storage/{storage_path}"
                logger.warning("Mock upload - file not actually stored")
            
            # Create file metadata
            stored_file = StoredFile(
                id=file_id,
                student_id=student_id,
                original_filename=file.filename or "unknown",
                storage_filename=storage_filename,
                file_type=file_type,
                mime_type=file.content_type or "application/octet-stream",
                file_size=len(file_content),
                file_hash=file_hash,
                storage_path=storage_path,
                download_url=download_url,
                status=FileStatus.UPLOADED,
                uploaded_by=user.uid,
                metadata=metadata or {}
            )
            
            # Store metadata in Firestore
            await self._store_file_metadata(stored_file)
            
            # Calculate upload time
            upload_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create upload result
            upload_result = FileUploadResult(
                file=stored_file,
                upload_time_seconds=upload_time,
                validation_results=validation_results
            )
            
            # Log audit event
            await audit_logger.log_file_action(
                user=user,
                action=AuditAction.UPLOAD_FILE,
                file_id=file_id,
                student_id=student_id,
                file_name=file.filename,
                file_size=len(file_content),
                success=True
            )
            
            logger.info(
                f"File upload completed: {file_id}",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "file_id": file_id,
                    "file_size": len(file_content),
                    "upload_time": upload_time
                }
            )
            
            return upload_result
            
        except Exception as e:
            upload_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log failed audit event
            await audit_logger.log_file_action(
                user=user,
                action=AuditAction.UPLOAD_FILE,
                file_id="upload_failed",
                student_id=student_id,
                file_name=file.filename,
                file_size=file.size,
                success=False,
                error_message=str(e)
            )
            
            logger.error(
                f"File upload failed: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "file_name": file.filename,
                    "error": str(e)
                }
            )
            
            if isinstance(e, (ValidationError, AppError)):
                raise
            else:
                raise AppError(
                    message="File upload operation failed",
                    code="FILE_UPLOAD_ERROR",
                    details={"error": str(e)}
                )
    
    async def get_student_files(
        self,
        student_id: str,
        user: AuthenticatedUser,
        file_type: Optional[FileType] = None
    ) -> List[StoredFile]:
        """
        Get all files for a student.
        
        Args:
            student_id: ID of the student
            user: Authenticated user requesting files
            file_type: Optional filter by file type
            
        Returns:
            List of stored files for the student
        """
        try:
            logger.debug(
                f"Getting files for student: {student_id}",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "file_type": file_type.value if file_type else None
                }
            )
            
            # Query Firestore for student files
            query = self.firestore_client.collection(self.files_collection)
            query = query.where("student_id", "==", student_id)
            query = query.where("status", "!=", FileStatus.DELETED.value)
            
            if file_type:
                query = query.where("file_type", "==", file_type.value)
            
            query = query.order_by("uploaded_at", direction="DESCENDING")
            
            # Execute query
            docs = query.stream()
            
            # Convert to StoredFile objects
            files = []
            for doc in docs:
                try:
                    data = doc.to_dict()
                    # Convert timestamp back to datetime
                    if 'uploaded_at' in data and isinstance(data['uploaded_at'], str):
                        data['uploaded_at'] = datetime.fromisoformat(data['uploaded_at'])
                    
                    files.append(StoredFile(**data))
                except Exception as e:
                    logger.warning(f"Failed to parse file document {doc.id}: {str(e)}")
                    continue
            
            logger.debug(
                f"Found {len(files)} files for student {student_id}",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "files_count": len(files)
                }
            )
            
            return files
            
        except Exception as e:
            logger.error(
                f"Failed to get student files: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "student_id": student_id,
                    "error": str(e)
                }
            )
            return []
    
    async def get_file_by_id(
        self,
        file_id: str,
        user: AuthenticatedUser
    ) -> Optional[StoredFile]:
        """
        Get a specific file by ID.
        
        Args:
            file_id: ID of the file
            user: Authenticated user requesting the file
            
        Returns:
            StoredFile object or None if not found
        """
        try:
            doc_ref = self.firestore_client.collection(self.files_collection).document(file_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Convert timestamp back to datetime
            if 'uploaded_at' in data and isinstance(data['uploaded_at'], str):
                data['uploaded_at'] = datetime.fromisoformat(data['uploaded_at'])
            
            return StoredFile(**data)
            
        except Exception as e:
            logger.error(
                f"Failed to get file by ID: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "file_id": file_id,
                    "error": str(e)
                }
            )
            return None
    
    async def delete_file(
        self,
        file_id: str,
        user: AuthenticatedUser
    ) -> bool:
        """
        Delete a file (soft delete by updating status).
        
        Args:
            file_id: ID of the file to delete
            user: Authenticated user deleting the file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            logger.info(
                f"Deleting file: {file_id}",
                extra={
                    "user_id": user.uid,
                    "file_id": file_id
                }
            )
            
            # Get file metadata
            stored_file = await self.get_file_by_id(file_id, user)
            if not stored_file:
                raise ValidationError(
                    message=f"File not found: {file_id}",
                    details={"file_id": file_id}
                )
            
            # Update status to deleted
            doc_ref = self.firestore_client.collection(self.files_collection).document(file_id)
            doc_ref.update({
                "status": FileStatus.DELETED.value,
                "deleted_at": datetime.utcnow().isoformat(),
                "deleted_by": user.uid
            })
            
            # Log audit event
            await audit_logger.log_file_action(
                user=user,
                action=AuditAction.DELETE_FILE,
                file_id=file_id,
                student_id=stored_file.student_id,
                file_name=stored_file.original_filename,
                file_size=stored_file.file_size,
                success=True
            )
            
            logger.info(
                f"File deleted successfully: {file_id}",
                extra={
                    "user_id": user.uid,
                    "file_id": file_id,
                    "student_id": stored_file.student_id
                }
            )
            
            return True
            
        except Exception as e:
            # Log failed audit event
            await audit_logger.log_file_action(
                user=user,
                action=AuditAction.DELETE_FILE,
                file_id=file_id,
                success=False,
                error_message=str(e)
            )
            
            logger.error(
                f"Failed to delete file: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "file_id": file_id,
                    "error": str(e)
                }
            )
            
            return False
    
    async def _validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file."""
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check file size
        if file.size and file.size > self.max_file_size:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"File size ({file.size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)"
            )
        
        # Check MIME type
        if file.content_type and file.content_type not in self.allowed_mime_types:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"File type '{file.content_type}' is not allowed"
            )
        
        # Check filename extension
        if file.filename:
            file_extension = self._get_file_extension(file.filename).lower()
            
            if file.content_type and file.content_type in self.allowed_mime_types:
                allowed_extensions = self.allowed_mime_types[file.content_type]
                if file_extension not in allowed_extensions:
                    validation_results["warnings"].append(
                        f"File extension '{file_extension}' doesn't match MIME type '{file.content_type}'"
                    )
        
        # Check for suspicious filenames
        if file.filename:
            suspicious_patterns = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
            if any(pattern in file.filename for pattern in suspicious_patterns):
                validation_results["valid"] = False
                validation_results["errors"].append("Filename contains suspicious characters")
        
        if not validation_results["valid"]:
            raise ValidationError(
                message="File validation failed",
                details=validation_results
            )
        
        return validation_results
    
    async def _check_duplicate_file(self, student_id: str, file_hash: str) -> Optional[StoredFile]:
        """Check if a file with the same hash already exists for the student."""
        
        try:
            query = self.firestore_client.collection(self.files_collection)
            query = query.where("student_id", "==", student_id)
            query = query.where("file_hash", "==", file_hash)
            query = query.where("status", "!=", FileStatus.DELETED.value)
            
            docs = list(query.stream())
            
            if docs:
                data = docs[0].to_dict()
                if 'uploaded_at' in data and isinstance(data['uploaded_at'], str):
                    data['uploaded_at'] = datetime.fromisoformat(data['uploaded_at'])
                return StoredFile(**data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to check for duplicate files: {str(e)}")
            return None
    
    async def _upload_to_firebase_storage(
        self,
        file_content: bytes,
        storage_path: str,
        content_type: str
    ) -> str:
        """Upload file content to Firebase Storage."""
        
        try:
            # Create blob in Firebase Storage
            blob = self.bucket.blob(storage_path)
            
            # Upload file content
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # Make the file publicly accessible (optional, depending on requirements)
            # blob.make_public()
            
            # Generate signed URL for secure access
            # For now, we'll use the public URL
            download_url = blob.public_url
            
            logger.debug(f"File uploaded to Firebase Storage: {storage_path}")
            
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload to Firebase Storage: {str(e)}")
            raise AppError(
                message="Failed to upload file to storage",
                code="STORAGE_UPLOAD_ERROR",
                details={"error": str(e)}
            )
    
    async def _store_file_metadata(self, stored_file: StoredFile) -> None:
        """Store file metadata in Firestore."""
        
        try:
            # Convert to dictionary
            file_data = stored_file.model_dump()
            file_data['uploaded_at'] = stored_file.uploaded_at.isoformat()
            
            # Store in Firestore
            doc_ref = self.firestore_client.collection(self.files_collection).document(stored_file.id)
            doc_ref.set(file_data)
            
            logger.debug(f"File metadata stored: {stored_file.id}")
            
        except Exception as e:
            logger.error(f"Failed to store file metadata: {str(e)}")
            raise AppError(
                message="Failed to store file metadata",
                code="METADATA_STORAGE_ERROR",
                details={"error": str(e)}
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        
        if not filename or '.' not in filename:
            return ""
        
        return '.' + filename.split('.')[-1].lower()
    
    async def get_storage_statistics(self, user: AuthenticatedUser) -> Dict[str, Any]:
        """Get storage usage statistics."""
        
        try:
            # Query all files (not deleted)
            query = self.firestore_client.collection(self.files_collection)
            query = query.where("status", "!=", FileStatus.DELETED.value)
            
            docs = query.stream()
            
            # Calculate statistics
            stats = {
                "total_files": 0,
                "total_size_bytes": 0,
                "files_by_type": {},
                "files_by_status": {},
                "average_file_size": 0,
                "largest_file_size": 0,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            file_sizes = []
            
            for doc in docs:
                try:
                    data = doc.to_dict()
                    
                    stats["total_files"] += 1
                    file_size = data.get("file_size", 0)
                    stats["total_size_bytes"] += file_size
                    file_sizes.append(file_size)
                    
                    # Count by type
                    file_type = data.get("file_type", "unknown")
                    stats["files_by_type"][file_type] = stats["files_by_type"].get(file_type, 0) + 1
                    
                    # Count by status
                    file_status = data.get("status", "unknown")
                    stats["files_by_status"][file_status] = stats["files_by_status"].get(file_status, 0) + 1
                    
                    # Track largest file
                    if file_size > stats["largest_file_size"]:
                        stats["largest_file_size"] = file_size
                        
                except Exception as e:
                    logger.warning(f"Failed to process file document for stats: {str(e)}")
                    continue
            
            # Calculate average
            if file_sizes:
                stats["average_file_size"] = sum(file_sizes) / len(file_sizes)
            
            logger.info(
                f"Storage statistics generated",
                extra={
                    "user_id": user.uid,
                    "total_files": stats["total_files"],
                    "total_size_mb": stats["total_size_bytes"] / (1024 * 1024)
                }
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                f"Failed to generate storage statistics: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "error": str(e)
                }
            )
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }


# Global service instance
file_storage_service = FileStorageService()
