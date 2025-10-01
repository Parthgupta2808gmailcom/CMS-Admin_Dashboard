"""
Centralized error handling with custom exceptions and FastAPI handlers.

This module defines the application's error contract and provides
consistent error responses across all API endpoints.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

from app.core.logging import get_logger, request_id_var


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class AppError(Exception):
    """Base application error with structured error information."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION", details)


class AuthError(AppError):
    """Raised when authentication or authorization fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTH", details)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NOT_FOUND", details)


def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        code: Error code (VALIDATION, NOT_FOUND, AUTH, INTERNAL)
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code
        
    Returns:
        JSONResponse with standardized error format
    """
    request_id = request_id_var.get()
    
    error_response = ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True)
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom application errors."""
    logger = get_logger(__name__)
    
    # Log the error with context
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "error_code": exc.code,
            "error_details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Determine HTTP status code based on error type
    status_code = 500
    if exc.code == "VALIDATION":
        status_code = 400
    elif exc.code == "AUTH":
        status_code = 401
    elif exc.code == "NOT_FOUND":
        status_code = 404
    
    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=status_code
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger = get_logger(__name__)
    
    # Extract validation error details
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation error",
        extra={
            "validation_errors": errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return create_error_response(
        code="VALIDATION",
        message="Request validation failed",
        details={"validation_errors": errors},
        status_code=422
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger = get_logger(__name__)
    
    # Map HTTP status codes to error codes
    error_code = "INTERNAL"
    if exc.status_code == 401:
        error_code = "AUTH"
    elif exc.status_code == 403:
        error_code = "AUTH"
    elif exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif 400 <= exc.status_code < 500:
        error_code = "VALIDATION"
    
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return create_error_response(
        code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger = get_logger(__name__)
    
    logger.exception(
        f"Unexpected error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    return create_error_response(
        code="INTERNAL",
        message="An unexpected error occurred",
        status_code=500
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application errors
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(ValidationError, app_error_handler)
    app.add_exception_handler(AuthError, app_error_handler)
    app.add_exception_handler(NotFoundError, app_error_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # General exception handler (catch-all)
    app.add_exception_handler(Exception, general_exception_handler)
