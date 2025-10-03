"""
Advanced search service for student data with multi-field filtering.

This module provides sophisticated search capabilities including
full-text search, multi-field filtering, date range queries,
and efficient pagination with proper indexing strategies.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.errors import AppError, ValidationError
from app.core.audit import audit_logger, AuditAction
from app.core.auth import AuthenticatedUser
from app.schemas.student import Student, ApplicationStatus
from app.repositories.students import student_repository

logger = get_logger(__name__)


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class SearchField(str, Enum):
    """Searchable fields in student records."""
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    COUNTRY = "country"
    GRADE = "grade"
    APPLICATION_STATUS = "application_status"
    LAST_ACTIVE = "last_active"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SearchFilter(BaseModel):
    """Individual search filter."""
    
    field: SearchField
    operator: str = Field(..., description="Comparison operator (eq, ne, gt, gte, lt, lte, contains, in)")
    value: Any = Field(..., description="Filter value")
    
    class Config:
        use_enum_values = True


class DateRangeFilter(BaseModel):
    """Date range filter for datetime fields."""
    
    field: SearchField
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class SearchQuery(BaseModel):
    """Comprehensive search query with filters, sorting, and pagination."""
    
    # Text search
    text_query: Optional[str] = Field(None, description="Full-text search query")
    search_fields: List[SearchField] = Field(
        default=[SearchField.NAME, SearchField.EMAIL],
        description="Fields to search in for text query"
    )
    
    # Filters
    filters: List[SearchFilter] = Field(default=[], description="Field-specific filters")
    date_filters: List[DateRangeFilter] = Field(default=[], description="Date range filters")
    
    # Application status filter (common use case)
    application_statuses: Optional[List[ApplicationStatus]] = Field(
        None, description="Filter by application status"
    )
    
    # Country filter (common use case)
    countries: Optional[List[str]] = Field(None, description="Filter by countries")
    
    # Sorting
    sort_field: SearchField = Field(SearchField.CREATED_AT, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    
    # Pagination
    limit: int = Field(50, ge=1, le=1000, description="Number of results per page")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    class Config:
        use_enum_values = True


class SearchResult(BaseModel):
    """Search results with metadata."""
    
    students: List[Student]
    total_count: int
    filtered_count: int
    page_info: Dict[str, Any]
    search_metadata: Dict[str, Any]
    
    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.page_info["offset"] + self.page_info["limit"] < self.filtered_count


class SearchService:
    """
    Advanced search service for student data.
    
    This service provides comprehensive search functionality including
    full-text search, multi-field filtering, date ranges, and efficient
    pagination with audit logging.
    """
    
    def __init__(self):
        """Initialize the search service."""
        self.max_results = 1000  # Maximum results per query
        logger.info("SearchService initialized")
    
    async def search_students(
        self,
        query: SearchQuery,
        user: AuthenticatedUser
    ) -> SearchResult:
        """
        Execute advanced search query for students.
        
        Args:
            query: Search query with filters and pagination
            user: Authenticated user performing the search
            
        Returns:
            SearchResult with matching students and metadata
            
        Raises:
            ValidationError: If search query is invalid
            AppError: If search operation fails
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Executing student search",
                extra={
                    "user_id": user.uid,
                    "text_query": query.text_query,
                    "filters_count": len(query.filters),
                    "sort_field": query.sort_field.value,
                    "limit": query.limit,
                    "offset": query.offset
                }
            )
            
            # Validate search query
            self._validate_search_query(query)
            
            # Build Firestore query
            firestore_query = await self._build_firestore_query(query)
            
            # Execute query to get total count (without pagination)
            total_students = await student_repository.list_students(limit=10000, offset=0)
            total_count = len(total_students)
            
            # Execute filtered query
            filtered_students = await self._execute_filtered_query(firestore_query, query)
            filtered_count = len(filtered_students)
            
            # Apply text search if specified
            if query.text_query:
                filtered_students = self._apply_text_search(filtered_students, query)
                filtered_count = len(filtered_students)
            
            # Apply sorting
            filtered_students = self._apply_sorting(filtered_students, query)
            
            # Apply pagination
            paginated_students = filtered_students[query.offset:query.offset + query.limit]
            
            # Create page info
            page_info = {
                "limit": query.limit,
                "offset": query.offset,
                "current_page": (query.offset // query.limit) + 1,
                "total_pages": (filtered_count + query.limit - 1) // query.limit,
                "has_next": query.offset + query.limit < filtered_count,
                "has_previous": query.offset > 0
            }
            
            # Create search metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            search_metadata = {
                "processing_time_seconds": processing_time,
                "query_complexity": self._calculate_query_complexity(query),
                "filters_applied": len(query.filters) + len(query.date_filters),
                "text_search_used": bool(query.text_query),
                "executed_at": datetime.utcnow().isoformat()
            }
            
            # Create search result
            result = SearchResult(
                students=paginated_students,
                total_count=total_count,
                filtered_count=filtered_count,
                page_info=page_info,
                search_metadata=search_metadata
            )
            
            # Log audit event
            await audit_logger.log_student_action(
                user=user,
                action=AuditAction.SEARCH_STUDENTS,
                details={
                    "text_query": query.text_query,
                    "filters_count": len(query.filters),
                    "date_filters_count": len(query.date_filters),
                    "results_count": len(paginated_students),
                    "filtered_count": filtered_count,
                    "processing_time_seconds": processing_time,
                    "sort_field": query.sort_field.value,
                    "sort_order": query.sort_order.value
                },
                success=True
            )
            
            logger.info(
                f"Search completed: {len(paginated_students)} results",
                extra={
                    "user_id": user.uid,
                    "filtered_count": filtered_count,
                    "processing_time": processing_time
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log failed audit event
            await audit_logger.log_student_action(
                user=user,
                action=AuditAction.SEARCH_STUDENTS,
                details={
                    "text_query": query.text_query,
                    "error": str(e),
                    "processing_time_seconds": processing_time
                },
                success=False,
                error_message=str(e)
            )
            
            logger.error(
                f"Search failed: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "text_query": query.text_query,
                    "error": str(e)
                }
            )
            
            if isinstance(e, (ValidationError, AppError)):
                raise
            else:
                raise AppError(
                    message="Student search operation failed",
                    code="SEARCH_ERROR",
                    details={"error": str(e)}
                )
    
    async def get_search_suggestions(
        self,
        field: SearchField,
        partial_value: str,
        user: AuthenticatedUser,
        limit: int = 10
    ) -> List[str]:
        """
        Get search suggestions for autocomplete functionality.
        
        Args:
            field: Field to get suggestions for
            partial_value: Partial value to match
            user: Authenticated user requesting suggestions
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested values
        """
        try:
            logger.debug(
                f"Getting search suggestions for {field.value}",
                extra={
                    "user_id": user.uid,
                    "field": field.value,
                    "partial_value": partial_value,
                    "limit": limit
                }
            )
            
            # Get all students (in a real implementation, you'd use indexed queries)
            students = await student_repository.list_students(limit=1000, offset=0)
            
            # Extract unique values for the field
            values = set()
            for student in students:
                field_value = getattr(student, field.value, None)
                
                if field_value:
                    # Convert to string for comparison
                    if hasattr(field_value, 'value'):  # Enum
                        field_value = field_value.value
                    else:
                        field_value = str(field_value)
                    
                    # Check if it matches the partial value
                    if partial_value.lower() in field_value.lower():
                        values.add(field_value)
            
            # Sort and limit results
            suggestions = sorted(list(values))[:limit]
            
            logger.debug(
                f"Found {len(suggestions)} suggestions for {field.value}",
                extra={
                    "user_id": user.uid,
                    "suggestions_count": len(suggestions)
                }
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(
                f"Failed to get search suggestions: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "field": field.value,
                    "error": str(e)
                }
            )
            return []
    
    async def get_search_facets(
        self,
        user: AuthenticatedUser,
        base_query: Optional[SearchQuery] = None
    ) -> Dict[str, Any]:
        """
        Get search facets (aggregated counts) for filtering UI.
        
        Args:
            user: Authenticated user requesting facets
            base_query: Optional base query to apply before faceting
            
        Returns:
            Dictionary with facet counts for each field
        """
        try:
            logger.debug(
                f"Getting search facets",
                extra={"user_id": user.uid}
            )
            
            # Get students (apply base query if provided)
            if base_query:
                search_result = await self.search_students(base_query, user)
                students = search_result.students
            else:
                students = await student_repository.list_students(limit=10000, offset=0)
            
            # Calculate facets
            facets = {
                "application_status": {},
                "country": {},
                "grade": {},
                "total_count": len(students)
            }
            
            for student in students:
                # Application status facet
                if student.application_status:
                    status = student.application_status.value
                    facets["application_status"][status] = facets["application_status"].get(status, 0) + 1
                
                # Country facet
                if student.country:
                    country = student.country
                    facets["country"][country] = facets["country"].get(country, 0) + 1
                
                # Grade facet
                if student.grade:
                    grade = student.grade
                    facets["grade"][grade] = facets["grade"].get(grade, 0) + 1
            
            # Sort facets by count (descending)
            for facet_name in ["application_status", "country", "grade"]:
                facets[facet_name] = dict(
                    sorted(facets[facet_name].items(), key=lambda x: x[1], reverse=True)
                )
            
            logger.debug(
                f"Generated search facets",
                extra={
                    "user_id": user.uid,
                    "total_students": facets["total_count"],
                    "status_facets": len(facets["application_status"]),
                    "country_facets": len(facets["country"]),
                    "grade_facets": len(facets["grade"])
                }
            )
            
            return facets
            
        except Exception as e:
            logger.error(
                f"Failed to get search facets: {str(e)}",
                extra={
                    "user_id": user.uid,
                    "error": str(e)
                }
            )
            return {
                "application_status": {},
                "country": {},
                "grade": {},
                "total_count": 0,
                "error": str(e)
            }
    
    def _validate_search_query(self, query: SearchQuery) -> None:
        """Validate search query parameters."""
        
        # Validate limit
        if query.limit > self.max_results:
            raise ValidationError(
                message=f"Search limit too high: {query.limit}",
                details={
                    "max_allowed": self.max_results,
                    "requested": query.limit
                }
            )
        
        # Validate filters
        for filter_item in query.filters:
            if filter_item.operator not in ["eq", "ne", "gt", "gte", "lt", "lte", "contains", "in"]:
                raise ValidationError(
                    message=f"Invalid filter operator: {filter_item.operator}",
                    details={
                        "valid_operators": ["eq", "ne", "gt", "gte", "lt", "lte", "contains", "in"]
                    }
                )
        
        # Validate date filters
        for date_filter in query.date_filters:
            if date_filter.start_date and date_filter.end_date:
                if date_filter.start_date > date_filter.end_date:
                    raise ValidationError(
                        message="Start date must be before end date",
                        details={
                            "start_date": date_filter.start_date.isoformat(),
                            "end_date": date_filter.end_date.isoformat()
                        }
                    )
    
    async def _build_firestore_query(self, query: SearchQuery) -> Dict[str, Any]:
        """Build Firestore query from search parameters."""
        
        # This is a simplified implementation
        # In a real system, you'd build actual Firestore query objects
        firestore_query = {
            "filters": [],
            "sort_field": query.sort_field.value,
            "sort_order": query.sort_order.value
        }
        
        # Add basic filters
        for filter_item in query.filters:
            firestore_query["filters"].append({
                "field": filter_item.field.value,
                "operator": filter_item.operator,
                "value": filter_item.value
            })
        
        # Add date filters
        for date_filter in query.date_filters:
            if date_filter.start_date:
                firestore_query["filters"].append({
                    "field": date_filter.field.value,
                    "operator": "gte",
                    "value": date_filter.start_date
                })
            
            if date_filter.end_date:
                firestore_query["filters"].append({
                    "field": date_filter.field.value,
                    "operator": "lte",
                    "value": date_filter.end_date
                })
        
        # Add application status filter
        if query.application_statuses:
            firestore_query["filters"].append({
                "field": "application_status",
                "operator": "in",
                "value": [status.value for status in query.application_statuses]
            })
        
        # Add country filter
        if query.countries:
            firestore_query["filters"].append({
                "field": "country",
                "operator": "in",
                "value": query.countries
            })
        
        return firestore_query
    
    async def _execute_filtered_query(
        self,
        firestore_query: Dict[str, Any],
        query: SearchQuery
    ) -> List[Student]:
        """Execute the filtered query against Firestore."""
        
        # For now, get all students and apply filters in memory
        # In a production system, you'd push these filters to Firestore
        all_students = await student_repository.list_students(limit=10000, offset=0)
        
        filtered_students = []
        
        for student in all_students:
            include_student = True
            
            # Apply each filter
            for filter_config in firestore_query["filters"]:
                field_name = filter_config["field"]
                operator = filter_config["operator"]
                filter_value = filter_config["value"]
                
                student_value = getattr(student, field_name, None)
                
                # Handle enum values
                if hasattr(student_value, 'value'):
                    student_value = student_value.value
                
                # Apply operator
                if operator == "eq" and student_value != filter_value:
                    include_student = False
                    break
                elif operator == "ne" and student_value == filter_value:
                    include_student = False
                    break
                elif operator == "gt" and not (student_value and student_value > filter_value):
                    include_student = False
                    break
                elif operator == "gte" and not (student_value and student_value >= filter_value):
                    include_student = False
                    break
                elif operator == "lt" and not (student_value and student_value < filter_value):
                    include_student = False
                    break
                elif operator == "lte" and not (student_value and student_value <= filter_value):
                    include_student = False
                    break
                elif operator == "contains" and not (student_value and str(filter_value).lower() in str(student_value).lower()):
                    include_student = False
                    break
                elif operator == "in" and student_value not in filter_value:
                    include_student = False
                    break
            
            if include_student:
                filtered_students.append(student)
        
        return filtered_students
    
    def _apply_text_search(self, students: List[Student], query: SearchQuery) -> List[Student]:
        """Apply text search to student list."""
        
        if not query.text_query:
            return students
        
        search_terms = query.text_query.lower().split()
        matching_students = []
        
        for student in students:
            # Check if any search term matches any search field
            student_matches = False
            
            for field in query.search_fields:
                field_value = getattr(student, field.value, None)
                
                if field_value:
                    field_text = str(field_value).lower()
                    
                    # Check if all search terms are found in this field
                    if all(term in field_text for term in search_terms):
                        student_matches = True
                        break
            
            if student_matches:
                matching_students.append(student)
        
        return matching_students
    
    def _apply_sorting(self, students: List[Student], query: SearchQuery) -> List[Student]:
        """Apply sorting to student list."""
        
        def get_sort_key(student):
            value = getattr(student, query.sort_field.value, None)
            
            # Handle None values (put them at the end)
            if value is None:
                return datetime.min if query.sort_field in [SearchField.LAST_ACTIVE, SearchField.CREATED_AT, SearchField.UPDATED_AT] else ""
            
            # Handle enum values
            if hasattr(value, 'value'):
                return value.value
            
            return value
        
        reverse = query.sort_order == SortOrder.DESC
        
        return sorted(students, key=get_sort_key, reverse=reverse)
    
    def _calculate_query_complexity(self, query: SearchQuery) -> str:
        """Calculate query complexity for monitoring."""
        
        complexity_score = 0
        
        # Text search adds complexity
        if query.text_query:
            complexity_score += 2
        
        # Each filter adds complexity
        complexity_score += len(query.filters)
        complexity_score += len(query.date_filters)
        
        # Large result sets add complexity
        if query.limit > 100:
            complexity_score += 1
        
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 5:
            return "medium"
        else:
            return "high"


# Global service instance
search_service = SearchService()
