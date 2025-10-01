"""
Health check endpoints for monitoring and load balancer integration.

This module provides liveness and readiness probes following Kubernetes
and cloud-native best practices for service health monitoring.
"""

from typing import Dict, Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.logging import get_logger, log_request_info
from app.core.config import settings

# Create router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Standard health check response model."""
    status: str
    version: str
    environment: str


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
    Readiness probe endpoint.
    
    This endpoint indicates whether the service is ready to serve
    traffic. In future phases, this will include database connectivity
    checks and other dependency validations.
    
    Returns:
        Health status indicating the service is ready
    """
    log_request_info(
        request=request,
        endpoint="readiness",
        message="Readiness check requested"
    )
    
    logger.info("Readiness check performed")
    
    # TODO: In Phase 2, add Firestore connectivity check
    # For now, return a placeholder status
    return {
        "status": "starting",  # Placeholder until Firestore integration
        "version": settings.app_version,
        "environment": settings.env
    }
