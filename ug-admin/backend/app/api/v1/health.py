"""
Health check endpoints for monitoring and load balancer integration.

This module provides liveness and readiness probes following Kubernetes
and cloud-native best practices for service health monitoring.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.logging import get_logger, log_request_info
from app.core.config import settings
from app.core.db import check_firestore
from app.core.errors import AppError

# Create router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Standard health check response model."""
    status: str
    version: str
    environment: str
    database: Optional[Dict[str, Any]] = None


@router.get("/liveness", response_model=HealthResponse)
async def liveness_check(request: Request) -> Dict[str, Any]:
    """
    Liveness probe endpoint.
    
    This endpoint indicates whether the service is running and can
    accept requests. It should return quickly and not perform
    expensive operations.
    
    Returns:
        Health status indicating the service is alive
    """
    log_request_info(
        request=request,
        endpoint="liveness",
        message="Liveness check requested"
    )
    
    logger.info("Liveness check performed")
    
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.env
    }


@router.get("/readiness", response_model=HealthResponse)
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Readiness probe endpoint with Firestore connectivity check.
    
    This endpoint indicates whether the service is ready to serve
    traffic by checking database connectivity and other dependencies.
    
    Returns:
        Health status indicating the service is ready
    """
    log_request_info(
        request=request,
        endpoint="readiness",
        message="Readiness check requested"
    )
    
    try:
        # Check Firestore connectivity
        db_status = check_firestore()
        
        logger.info(
            "Readiness check successful",
            extra={
                "firestore_status": db_status["status"],
                "project_id": db_status.get("project_id"),
                "collections_count": db_status.get("collections_count")
            }
        )
        
        return {
            "status": "up",
            "version": settings.app_version,
            "environment": settings.env,
            "database": {
                "status": db_status["status"],
                "project_id": db_status.get("project_id"),
                "collections_count": db_status.get("collections_count")
            }
        }
        
    except AppError as e:
        logger.error(
            f"Readiness check failed: {e.message}",
            extra={
                "error_code": e.code,
                "error_details": e.details,
                "endpoint": "readiness"
            }
        )
        
        return {
            "status": "down",
            "version": settings.app_version,
            "environment": settings.env,
            "database": {
                "status": "down",
                "error": e.message,
                "code": e.code
            }
        }
        
    except Exception as e:
        logger.error(
            f"Unexpected error in readiness check: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": "readiness"
            }
        )
        
        return {
            "status": "down",
            "version": settings.app_version,
            "environment": settings.env,
            "database": {
                "status": "down",
                "error": "Unexpected error",
                "code": "INTERNAL"
            }
        }
