"""
Main FastAPI application entry point.

This module initializes the FastAPI application with all middleware,
error handlers, and route configurations following MVC patterns.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, RequestIDMiddleware
from app.core.errors import setup_error_handlers
from app.core.auth import setup_auth_error_handlers
from app.api.v1 import api_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This factory function sets up all middleware, error handlers,
    and routes following the application's architecture patterns.
    
    Returns:
        Configured FastAPI application instance
    """
    # Initialize logging first
    setup_logging()
    
    # Create FastAPI application
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for Undergraduation.com Admin Dashboard",
        debug=settings.debug,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request ID middleware for logging correlation
    app.add_middleware(RequestIDMiddleware)
    
    # Setup error handlers
    setup_error_handlers(app)
    setup_auth_error_handlers(app)
    
    # Include API routes
    app.include_router(api_router)
    
    return app


# Create the application instance
app = create_app()


@app.get("/")
async def root():
    """
    Root endpoint providing basic application information.
    
    Returns:
        Basic application metadata
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.env,
        "status": "running"
    }
