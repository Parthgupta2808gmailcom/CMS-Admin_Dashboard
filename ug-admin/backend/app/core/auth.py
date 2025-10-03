"""
Firebase Authentication and Authorization middleware.

This module provides comprehensive Firebase JWT token validation,
user role management, and role-based access control (RBAC) for
securing API endpoints with proper error handling and logging.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import AppError, ValidationError
from app.core.logging import get_logger
from app.core.db import get_firestore_client

logger = get_logger(__name__)

# Security scheme for FastAPI documentation
security = HTTPBearer()


def initialize_firebase_admin():
    """
    Initialize Firebase Admin SDK if not already initialized.
    
    This function sets up Firebase Admin SDK using the same credentials
    as the Firestore client for consistency.
    """
    if not firebase_admin._apps:
        try:
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
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(credentials_info)
            firebase_admin.initialize_app(cred)
            
            logger.info("Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
            raise AppError(
                message="Failed to initialize authentication service",
                code="AUTH",
                details={"error": str(e)}
            )
    else:
        logger.debug("Firebase Admin SDK already initialized")


# Initialize Firebase Admin SDK on module import
initialize_firebase_admin()


class UserRole(str, Enum):
    """Enumeration of user roles for role-based access control."""
    ADMIN = "admin"
    STAFF = "staff"


class AuthenticatedUser(BaseModel):
    """Model representing an authenticated user with role information."""
    uid: str
    email: str
    role: UserRole
    name: Optional[str] = None
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True


class AuthError(AppError):
    """Custom exception for authentication errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTH",
            details=details or {}
        )


class ForbiddenError(AppError):
    """Custom exception for authorization/permission errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN", 
            details=details or {}
        )


class FirebaseAuthManager:
    """
    Manager class for Firebase authentication operations.
    
    Handles token verification, user role management, and
    provides utilities for authentication and authorization.
    """
    
    def __init__(self):
        """Initialize Firebase Auth Manager with Firestore client."""
        self.firestore_client = get_firestore_client()
        self.users_collection = "users"
        logger.info("FirebaseAuthManager initialized")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded claims.
        
        Args:
            token: Firebase ID token string
            
        Returns:
            Decoded token claims with user information
            
        Raises:
            AuthError: If token is invalid, expired, or verification fails
        """
        try:
            # Verify the ID token with Firebase Admin SDK
            # This validates signature, expiration, and issuer
            decoded_token = firebase_auth.verify_id_token(token)
            
            logger.info(
                f"Token verified successfully for user: {decoded_token.get('uid')}",
                extra={
                    "user_id": decoded_token.get("uid"),
                    "email": decoded_token.get("email"),
                    "token_issued_at": decoded_token.get("iat"),
                    "token_expires_at": decoded_token.get("exp")
                }
            )
            
            return decoded_token
            
        except firebase_auth.InvalidIdTokenError as e:
            logger.warning(
                f"Invalid Firebase token: {str(e)}",
                extra={"error": str(e), "error_type": "InvalidIdTokenError"}
            )
            raise AuthError(
                message="Invalid authentication token",
                details={"error": "Token validation failed", "reason": str(e)}
            )
            
        except firebase_auth.ExpiredIdTokenError as e:
            logger.warning(
                f"Expired Firebase token: {str(e)}",
                extra={"error": str(e), "error_type": "ExpiredIdTokenError"}
            )
            raise AuthError(
                message="Authentication token has expired",
                details={"error": "Token expired", "reason": str(e)}
            )
            
        except firebase_auth.RevokedIdTokenError as e:
            logger.warning(
                f"Revoked Firebase token: {str(e)}",
                extra={"error": str(e), "error_type": "RevokedIdTokenError"}
            )
            raise AuthError(
                message="Authentication token has been revoked",
                details={"error": "Token revoked", "reason": str(e)}
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error verifying token: {str(e)}",
                extra={"error": str(e), "error_type": type(e).__name__}
            )
            raise AuthError(
                message="Authentication verification failed",
                details={"error": "Unexpected verification error", "reason": str(e)}
            )
    
    async def get_user_role(self, uid: str) -> UserRole:
        """
        Retrieve user role from Firestore users collection.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            User role enum value
            
        Raises:
            AuthError: If user not found or role retrieval fails
        """
        try:
            # Get user document from Firestore
            user_doc_ref = self.firestore_client.collection(self.users_collection).document(uid)
            user_doc = user_doc_ref.get()
            
            if not user_doc.exists:
                logger.warning(
                    f"User not found in users collection: {uid}",
                    extra={"user_id": uid, "collection": self.users_collection}
                )
                # Default to staff role for new users, but log this for admin review
                await self._create_default_user(uid)
                return UserRole.STAFF
            
            user_data = user_doc.to_dict()
            role_str = user_data.get("role", "staff")
            
            try:
                role = UserRole(role_str)
                logger.debug(
                    f"Retrieved role for user {uid}: {role}",
                    extra={"user_id": uid, "role": role.value}
                )
                return role
                
            except ValueError:
                logger.warning(
                    f"Invalid role '{role_str}' for user {uid}, defaulting to staff",
                    extra={"user_id": uid, "invalid_role": role_str}
                )
                # Update user with valid role
                await self._update_user_role(uid, UserRole.STAFF)
                return UserRole.STAFF
                
        except Exception as e:
            logger.error(
                f"Failed to retrieve user role for {uid}: {str(e)}",
                extra={"user_id": uid, "error": str(e), "error_type": type(e).__name__}
            )
            raise AuthError(
                message="Failed to retrieve user permissions",
                details={"error": "Role retrieval failed", "user_id": uid}
            )
    
    async def _create_default_user(self, uid: str) -> None:
        """
        Create a default user record in Firestore with staff role.
        
        Args:
            uid: Firebase user ID
        """
        try:
            user_data = {
                "role": UserRole.STAFF.value,
                "created_at": time.time(),
                "last_login": time.time(),
                "status": "active"
            }
            
            user_doc_ref = self.firestore_client.collection(self.users_collection).document(uid)
            user_doc_ref.set(user_data)
            
            logger.info(
                f"Created default user record for {uid}",
                extra={"user_id": uid, "default_role": UserRole.STAFF.value}
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create default user record for {uid}: {str(e)}",
                extra={"user_id": uid, "error": str(e)}
            )
            # Don't raise here - we'll continue with default role
    
    async def _update_user_role(self, uid: str, role: UserRole) -> None:
        """
        Update user role in Firestore.
        
        Args:
            uid: Firebase user ID
            role: New role to assign
        """
        try:
            user_doc_ref = self.firestore_client.collection(self.users_collection).document(uid)
            user_doc_ref.update({
                "role": role.value,
                "updated_at": time.time()
            })
            
            logger.info(
                f"Updated role for user {uid} to {role.value}",
                extra={"user_id": uid, "new_role": role.value}
            )
            
        except Exception as e:
            logger.error(
                f"Failed to update role for user {uid}: {str(e)}",
                extra={"user_id": uid, "role": role.value, "error": str(e)}
            )
    
    async def update_last_login(self, uid: str) -> None:
        """
        Update user's last login timestamp.
        
        Args:
            uid: Firebase user ID
        """
        try:
            user_doc_ref = self.firestore_client.collection(self.users_collection).document(uid)
            user_doc_ref.update({
                "last_login": time.time()
            })
            
            logger.debug(
                f"Updated last login for user: {uid}",
                extra={"user_id": uid}
            )
            
        except Exception as e:
            logger.warning(
                f"Failed to update last login for user {uid}: {str(e)}",
                extra={"user_id": uid, "error": str(e)}
            )
            # Don't raise - this is not critical for authentication


# Global auth manager instance
auth_manager = FirebaseAuthManager()


async def extract_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract and validate Bearer token from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials from FastAPI security
        
    Returns:
        Extracted token string
        
    Raises:
        AuthError: If token format is invalid or missing
    """
    if not credentials:
        logger.warning("Missing authorization credentials")
        raise AuthError(
            message="Authentication required",
            details={"error": "Missing Authorization header"}
        )
    
    if credentials.scheme.lower() != "bearer":
        logger.warning(
            f"Invalid authentication scheme: {credentials.scheme}",
            extra={"scheme": credentials.scheme}
        )
        raise AuthError(
            message="Invalid authentication scheme",
            details={"error": "Expected Bearer token", "received_scheme": credentials.scheme}
        )
    
    if not credentials.credentials:
        logger.warning("Empty token in authorization header")
        raise AuthError(
            message="Authentication token required",
            details={"error": "Empty token provided"}
        )
    
    return credentials.credentials


async def authenticate_user(token: str = Depends(extract_token_from_header)) -> AuthenticatedUser:
    """
    Authenticate user using Firebase token and retrieve role information.
    
    This dependency verifies the Firebase ID token, retrieves user role
    from Firestore, and returns an authenticated user object.
    
    Args:
        token: Firebase ID token from Authorization header
        
    Returns:
        Authenticated user with role information
        
    Raises:
        AuthError: If authentication fails
    """
    try:
        # Verify token with Firebase
        decoded_token = await auth_manager.verify_token(token)
        
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        
        if not uid:
            raise AuthError(
                message="Invalid token: missing user ID",
                details={"error": "Token missing required claims"}
            )
        
        # Get user role from Firestore
        role = await auth_manager.get_user_role(uid)
        
        # Update last login timestamp (non-blocking)
        try:
            await auth_manager.update_last_login(uid)
        except Exception as e:
            # Log but don't fail authentication for this
            logger.warning(f"Failed to update last login: {str(e)}")
        
        authenticated_user = AuthenticatedUser(
            uid=uid,
            email=email,
            role=role,
            name=name
        )
        
        logger.info(
            f"User authenticated successfully: {email} ({role.value})",
            extra={
                "user_id": uid,
                "email": email,
                "role": role.value,
                "authentication_time": time.time()
            }
        )
        
        return authenticated_user
        
    except AuthError:
        # Re-raise auth errors as-is
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during authentication: {str(e)}",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        raise AuthError(
            message="Authentication failed",
            details={"error": "Unexpected authentication error"}
        )


def require_role(required_roles: List[UserRole]):
    """
    Create a dependency that requires specific user roles.
    
    This function returns a FastAPI dependency that checks if the
    authenticated user has one of the required roles.
    
    Args:
        required_roles: List of roles that are allowed access
        
    Returns:
        FastAPI dependency function
        
    Example:
        @router.delete("/students/{id}")
        async def delete_student(
            id: str,
            user: AuthenticatedUser = Depends(require_role([UserRole.ADMIN]))
        ):
            # Only admins can delete students
    """
    def role_checker(user: AuthenticatedUser = Depends(authenticate_user)) -> AuthenticatedUser:
        """
        Check if authenticated user has required role.
        
        Args:
            user: Authenticated user from authentication dependency
            
        Returns:
            Authenticated user if role check passes
            
        Raises:
            ForbiddenError: If user doesn't have required role
        """
        if user.role not in required_roles:
            logger.warning(
                f"Access denied: user {user.email} ({user.role.value}) attempted to access resource requiring {[r.value for r in required_roles]}",
                extra={
                    "user_id": user.uid,
                    "user_role": user.role.value,
                    "required_roles": [r.value for r in required_roles],
                    "access_denied": True
                }
            )
            raise ForbiddenError(
                message=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}",
                details={
                    "user_role": user.role.value,
                    "required_roles": [r.value for r in required_roles]
                }
            )
        
        logger.debug(
            f"Role check passed for user {user.email}: {user.role.value} in {[r.value for r in required_roles]}",
            extra={
                "user_id": user.uid,
                "user_role": user.role.value,
                "required_roles": [r.value for r in required_roles]
            }
        )
        
        return user
    
    return role_checker


# Convenience dependencies for common role requirements
require_admin = require_role([UserRole.ADMIN])
require_staff_or_admin = require_role([UserRole.STAFF, UserRole.ADMIN])
require_any_authenticated = authenticate_user


def setup_auth_error_handlers(app):
    """
    Set up error handlers for authentication and authorization errors.
    
    Args:
        app: FastAPI application instance
    """
    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        """Handle authentication errors with consistent response format."""
        logger.warning(
            f"Authentication error: {exc.message}",
            extra={
                "error_code": exc.code,
                "error_details": exc.details,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        raise HTTPException(
            status_code=401,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None)
            }
        )
    
    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(request: Request, exc: ForbiddenError):
        """Handle authorization errors with consistent response format."""
        logger.warning(
            f"Authorization error: {exc.message}",
            extra={
                "error_code": exc.code,
                "error_details": exc.details,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        raise HTTPException(
            status_code=403,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None)
            }
        )
