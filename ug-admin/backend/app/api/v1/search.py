"""
API endpoints for advanced student search functionality.

This module provides REST API endpoints for searching students with
multi-field filtering, full-text search, faceted search, and
search suggestions with proper authentication and audit logging.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi import status as http_status
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.errors import AppError, ValidationError
from app.core.logging import get_logger, log_request_info
from app.core.auth import AuthenticatedUser, require_staff_or_admin
from app.schemas.student import ApplicationStatus
from app.services.search import (
    search_service,
    SearchQuery,
    SearchResult,
    SearchField,
    SortOrder,
    SearchFilter,
    DateRangeFilter
)

# Create router for search endpoints
router = APIRouter(prefix="/search", tags=["search"])

logger = get_logger(__name__)


class SearchRequest(BaseModel):
    """Request model for advanced search."""
    
    text_query: Optional[str] = Field(None, description="Full-text search query")
    search_fields: List[SearchField] = Field(
        default=[SearchField.NAME, SearchField.EMAIL],
        description="Fields to search in for text query"
    )
    application_statuses: Optional[List[ApplicationStatus]] = Field(
        None, description="Filter by application status"
    )
    countries: Optional[List[str]] = Field(None, description="Filter by countries")
    sort_field: SearchField = Field(SearchField.CREATED_AT, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    limit: int = Field(50, ge=1, le=1000, description="Number of results per page")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    class Config:
        use_enum_values = True


class SearchResponse(BaseModel):
    """Response model for search results."""
    
    success: bool
    message: str
    results: SearchResult


class SearchSuggestionsResponse(BaseModel):
    """Response model for search suggestions."""
    
    success: bool
    message: str
    suggestions: List[str]
    field: str
    partial_value: str


class SearchFacetsResponse(BaseModel):
    """Response model for search facets."""
    
    success: bool
    message: str
    facets: Dict[str, Any]


@router.post(
    "/students",
    response_model=SearchResponse,
    summary="Advanced student search",
    description="Search students with multi-field filtering, full-text search, and pagination"
)
async def search_students(
    search_request: SearchRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> SearchResponse:
    """
    Perform advanced search on student records.
    
    This endpoint provides comprehensive search functionality including:
    - Full-text search across multiple fields
    - Multi-field filtering (status, country, etc.)
    - Date range filtering
    - Sorting and pagination
    - Search result analytics
    
    **Staff or Admin access required** - Staff and administrators can search students.
    
    Args:
        search_request: Search parameters and filters
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Search results with matching students and metadata
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="search_students",
        message="Student search requested",
        extra={
            "text_query": search_request.text_query,
            "search_fields": [f.value for f in search_request.search_fields],
            "application_statuses": [s.value for s in search_request.application_statuses] if search_request.application_statuses else None,
            "countries": search_request.countries,
            "sort_field": search_request.sort_field.value,
            "sort_order": search_request.sort_order.value,
            "limit": search_request.limit,
            "offset": search_request.offset,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Convert request to SearchQuery
        search_query = SearchQuery(
            text_query=search_request.text_query,
            search_fields=search_request.search_fields,
            application_statuses=search_request.application_statuses,
            countries=search_request.countries,
            sort_field=search_request.sort_field,
            sort_order=search_request.sort_order,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        # Execute search
        search_result = await search_service.search_students(
            query=search_query,
            user=current_user
        )
        
        logger.info(
            f"Search completed: {len(search_result.students)} results",
            extra={
                "user": current_user.uid,
                "user_role": current_user.role.value,
                "text_query": search_request.text_query,
                "results_count": len(search_result.students),
                "filtered_count": search_result.filtered_count,
                "total_count": search_result.total_count,
                "processing_time": search_result.search_metadata.get("processing_time_seconds")
            }
        )
        
        return SearchResponse(
            success=True,
            message=f"Found {search_result.filtered_count} students matching your search criteria",
            results=search_result
        )
        
    except ValidationError as e:
        logger.warning(
            f"Search validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "search_students",
                "user": current_user.uid,
                "text_query": search_request.text_query
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Search validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"Search application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "search_students",
                "user": current_user.uid,
                "text_query": search_request.text_query
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Search operation failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/suggestions",
    response_model=SearchSuggestionsResponse,
    summary="Get search suggestions",
    description="Get autocomplete suggestions for search fields"
)
async def get_search_suggestions(
    field: SearchField = Query(..., description="Field to get suggestions for"),
    partial_value: str = Query(..., description="Partial value to match"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> SearchSuggestionsResponse:
    """
    Get search suggestions for autocomplete functionality.
    
    This endpoint provides autocomplete suggestions for search fields
    to improve user experience and search accuracy.
    
    **Staff or Admin access required** - Staff and administrators can get suggestions.
    
    Args:
        field: Field to get suggestions for
        partial_value: Partial value to match against
        limit: Maximum number of suggestions to return
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        List of suggested values for the specified field
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      400 for validation errors, 500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="get_search_suggestions",
        message="Search suggestions requested",
        extra={
            "field": field.value,
            "partial_value": partial_value,
            "limit": limit,
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Get suggestions
        suggestions = await search_service.get_search_suggestions(
            field=field,
            partial_value=partial_value,
            user=current_user,
            limit=limit
        )
        
        logger.debug(
            f"Search suggestions generated: {len(suggestions)} suggestions",
            extra={
                "user": current_user.uid,
                "field": field.value,
                "partial_value": partial_value,
                "suggestions_count": len(suggestions)
            }
        )
        
        return SearchSuggestionsResponse(
            success=True,
            message=f"Found {len(suggestions)} suggestions for {field.value}",
            suggestions=suggestions,
            field=field.value,
            partial_value=partial_value
        )
        
    except ValidationError as e:
        logger.warning(
            f"Suggestions validation error: {e.message}",
            extra={
                "error": e.message,
                "details": e.details,
                "endpoint": "get_search_suggestions",
                "user": current_user.uid,
                "field": field.value
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Suggestions request validation failed",
                "message": e.message,
                "details": e.details
            }
        )
    except AppError as e:
        logger.error(
            f"Suggestions application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "get_search_suggestions",
                "user": current_user.uid,
                "field": field.value
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Suggestions operation failed",
                "message": e.message,
                "code": e.code
            }
        )


@router.get(
    "/facets",
    response_model=SearchFacetsResponse,
    summary="Get search facets",
    description="Get aggregated counts for search filtering UI"
)
async def get_search_facets(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> SearchFacetsResponse:
    """
    Get search facets for building filtering UI.
    
    This endpoint provides aggregated counts for various fields
    to help users understand the data distribution and build
    effective search filters.
    
    **Staff or Admin access required** - Staff and administrators can get facets.
    
    Args:
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Faceted counts for application status, country, grade, etc.
        
    Raises:
        HTTPException: 401 for auth errors, 403 for permission errors,
                      500 for server errors
    """
    log_request_info(
        request=request,
        endpoint="get_search_facets",
        message="Search facets requested",
        extra={
            "user": current_user.uid,
            "user_role": current_user.role.value
        }
    )
    
    try:
        # Get facets
        facets = await search_service.get_search_facets(
            user=current_user
        )
        
        logger.debug(
            f"Search facets generated",
            extra={
                "user": current_user.uid,
                "total_students": facets.get("total_count", 0),
                "status_facets": len(facets.get("application_status", {})),
                "country_facets": len(facets.get("country", {})),
                "grade_facets": len(facets.get("grade", {}))
            }
        )
        
        return SearchFacetsResponse(
            success=True,
            message=f"Generated facets for {facets.get('total_count', 0)} students",
            facets=facets
        )
        
    except AppError as e:
        logger.error(
            f"Facets application error: {e.message}",
            extra={
                "error": e.message,
                "code": e.code,
                "details": e.details,
                "endpoint": "get_search_facets",
                "user": current_user.uid
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Facets operation failed",
                "message": e.message,
                "code": e.code
            }
        )


# Simple GET endpoint for basic search (backward compatibility)
@router.get(
    "/students/simple",
    response_model=SearchResponse,
    summary="Simple student search",
    description="Simple search with query parameters (backward compatibility)"
)
async def simple_search_students(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    sort: SearchField = Query(SearchField.CREATED_AT, description="Sort field"),
    order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    limit: int = Query(50, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(require_staff_or_admin)
) -> SearchResponse:
    """
    Simple search endpoint using query parameters.
    
    This endpoint provides a simpler interface for basic search operations
    while maintaining backward compatibility with existing clients.
    
    **Staff or Admin access required** - Staff and administrators can search students.
    
    Args:
        q: Search query string
        status: Filter by application status
        country: Filter by country
        sort: Field to sort by
        order: Sort order (asc/desc)
        limit: Number of results per page
        offset: Number of results to skip
        request: FastAPI request object for logging
        current_user: Authenticated user (staff or admin)
        
    Returns:
        Search results with matching students and metadata
    """
    # Convert simple parameters to SearchRequest
    search_request = SearchRequest(
        text_query=q,
        application_statuses=[status] if status else None,
        countries=[country] if country else None,
        sort_field=sort,
        sort_order=order,
        limit=limit,
        offset=offset
    )
    
    # Use the main search endpoint
    return await search_students(
        search_request=search_request,
        request=request,
        current_user=current_user
    )
