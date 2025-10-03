"""
Firestore database client configuration with retry/backoff logic.

This module provides a singleton Firestore client with proper error handling,
connection retry logic, and health check capabilities for the readiness probe.
"""

import os
import time
from typing import Optional, Dict, Any
from google.cloud import firestore
from google.cloud.firestore import Client
from google.api_core import retry, exceptions as gcp_exceptions
from google.oauth2 import service_account
import logging

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global Firestore client instance
_firestore_client: Optional[Client] = None


def get_firestore_client() -> Client:
    """
    Get or create a singleton Firestore client with retry configuration.
    
    This function implements lazy initialization of the Firestore client
    with proper retry logic and error handling. The client is created
    only when first accessed and reused across the application.
    
    Returns:
        Configured Firestore client instance
        
    Raises:
        AppError: If Firestore client cannot be initialized
    """
    global _firestore_client
    
    if _firestore_client is None:
        try:
            # Configure retry strategy for Firestore operations
            retry_strategy = retry.Retry(
                initial=1.0,  # Initial delay in seconds
                maximum=10.0,  # Maximum delay in seconds
                multiplier=2.0,  # Exponential backoff multiplier
                deadline=60.0,  # Total timeout in seconds
                predicate=retry.if_exception_type(
                    gcp_exceptions.ServiceUnavailable,
                    gcp_exceptions.DeadlineExceeded,
                    gcp_exceptions.InternalServerError,
                )
            )
            
            # Create service account credentials
            credentials_info = {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "private_key_id": settings.firebase_private_key_id,
                "private_key": settings.firebase_private_key,
                "client_email": settings.firebase_client_email,
                "client_id": settings.firebase_client_id,
                "auth_uri": settings.firebase_auth_uri,
                "token_uri": settings.firebase_token_uri,
            }
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # Initialize Firestore client with credentials and database ID
            _firestore_client = firestore.Client(
                project=settings.firebase_project_id,
                credentials=credentials,
                database="cms-students"
            )
            
            logger.info(
                "Firestore client initialized",
                extra={
                    "project_id": settings.firebase_project_id,
                    "retry_enabled": True
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to initialize Firestore client: {str(e)}",
                extra={
                    "project_id": settings.firebase_project_id,
                    "error_type": type(e).__name__
                }
            )
            raise AppError(
                message="Failed to initialize Firestore client",
                code="INTERNAL",
                details={"error": str(e), "project_id": settings.firebase_project_id}
            )
    
    return _firestore_client


def check_firestore() -> Dict[str, Any]:
    """
    Check Firestore connectivity for readiness probe.
    
    This function performs a lightweight operation to verify that
    the Firestore client can successfully connect and perform
    basic operations. It's designed to be fast and non-intrusive.
    
    Returns:
        Dictionary with connectivity status and details
        
    Raises:
        AppError: If Firestore is not accessible
    """
    try:
        client = get_firestore_client()
        
        # Perform a lightweight operation to test connectivity
        # List collections is a simple read operation that doesn't
        # require specific permissions and is fast to execute
        collections = list(client.collections())
        
        logger.info(
            "Firestore connectivity check successful",
            extra={
                "collections_count": len(collections),
                "project_id": settings.firebase_project_id
            }
        )
        
        return {
            "status": "up",
            "project_id": settings.firebase_project_id,
            "collections_count": len(collections),
            "timestamp": time.time()
        }
        
    except gcp_exceptions.PermissionDenied as e:
        logger.error(
            "Firestore permission denied",
            extra={
                "error": str(e),
                "project_id": settings.firebase_project_id
            }
        )
        raise AppError(
            message="Firestore access denied",
            code="AUTH",
            details={"error": str(e), "project_id": settings.firebase_project_id}
        )
        
    except gcp_exceptions.ServiceUnavailable as e:
        logger.error(
            "Firestore service unavailable",
            extra={
                "error": str(e),
                "project_id": settings.firebase_project_id
            }
        )
        raise AppError(
            message="Firestore service unavailable",
            code="INTERNAL",
            details={"error": str(e), "project_id": settings.firebase_project_id}
        )
        
    except Exception as e:
        logger.error(
            f"Firestore connectivity check failed: {str(e)}",
            extra={
                "error_type": type(e).__name__,
                "project_id": settings.firebase_project_id
            }
        )
        raise AppError(
            message="Firestore connectivity check failed",
            code="INTERNAL",
            details={"error": str(e), "project_id": settings.firebase_project_id}
        )


def reset_firestore_client() -> None:
    """
    Reset the global Firestore client instance.
    
    This function is primarily used for testing to ensure
    clean state between test runs. It should not be called
    in production code.
    """
    global _firestore_client
    _firestore_client = None
    logger.info("Firestore client reset")


def get_firestore_collection(collection_name: str) -> firestore.CollectionReference:
    """
    Get a Firestore collection reference with error handling.
    
    Args:
        collection_name: Name of the collection to retrieve
        
    Returns:
        Firestore collection reference
        
    Raises:
        AppError: If collection cannot be accessed
    """
    try:
        client = get_firestore_client()
        collection = client.collection(collection_name)
        
        logger.debug(
            f"Retrieved collection reference: {collection_name}",
            extra={"collection_name": collection_name}
        )
        
        return collection
        
    except Exception as e:
        logger.error(
            f"Failed to get collection {collection_name}: {str(e)}",
            extra={
                "collection_name": collection_name,
                "error_type": type(e).__name__
            }
        )
        raise AppError(
            message=f"Failed to access collection: {collection_name}",
            code="INTERNAL",
            details={"error": str(e), "collection_name": collection_name}
        )
