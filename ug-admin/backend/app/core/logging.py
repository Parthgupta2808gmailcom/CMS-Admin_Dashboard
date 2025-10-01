"""
Structured logging configuration with request ID tracking.

This module provides JSON-formatted logging with request correlation IDs
for better observability and debugging in distributed systems.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

# Context variable for storing request ID across the request lifecycle
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with request ID."""
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage", "exc_info",
                "exc_text", "stack_info"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and track request IDs.
    
    This middleware ensures every request has a unique identifier
    that can be used for correlation across logs and error tracking.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Generate request ID and add it to request context."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Set in context variable for logging
        request_id_var.set(request_id)
        
        # Add to request state for access in endpoints
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers for client correlation
        response.headers["X-Request-ID"] = request_id
        
        return response


def setup_logging() -> None:
    """
    Configure application logging with structured JSON output.
    
    This function sets up the logging configuration based on environment
    settings and ensures consistent log formatting across the application.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries in development
    if settings.is_development:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_request_info(request: Request, **extra: Any) -> None:
    """
    Log request information with structured data.
    
    Args:
        request: FastAPI request object
        **extra: Additional fields to include in the log
    """
    logger = get_logger(__name__)
    
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    # Add extra fields, but avoid conflicts with built-in LogRecord fields
    for key, value in extra.items():
        if key not in ["message", "asctime", "levelname", "levelno", "name", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "getMessage", "exc_info", "exc_text", "stack_info"]:
            log_data[key] = value
    
    logger.info("Request received", extra=log_data)


def log_response_info(response: Response, **extra: Any) -> None:
    """
    Log response information with structured data.
    
    Args:
        response: FastAPI response object
        **extra: Additional fields to include in the log
    """
    logger = get_logger(__name__)
    
    log_data = {
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        **extra
    }
    
    logger.info("Response sent", extra=log_data)
