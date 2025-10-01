"""
API v1 router configuration.

This module aggregates all v1 API endpoints and provides
a single router for the main application to include.
"""

from fastapi import APIRouter
from app.api.v1.health import router as health_router

# Create the main v1 API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(health_router)