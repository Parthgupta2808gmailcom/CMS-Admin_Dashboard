"""
API v1 router configuration.

This module aggregates all v1 API endpoints and provides
a single router for the main application to include.
"""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.students import router as students_router
from app.api.v1.bulk_operations import router as bulk_operations_router
from app.api.v1.search import router as search_router
from app.api.v1.files import router as files_router
from app.api.v1.notifications import router as notifications_router

# Create the main v1 API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(health_router)
api_router.include_router(students_router)
api_router.include_router(bulk_operations_router)
api_router.include_router(search_router)
api_router.include_router(files_router)
api_router.include_router(notifications_router)