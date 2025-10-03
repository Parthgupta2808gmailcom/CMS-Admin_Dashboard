"""
Student data models with Pydantic validation.

This module defines the complete student data schema with proper validation,
type safety, and serialization for the Undergraduation.com platform.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.logging import get_logger

logger = get_logger(__name__)


class ApplicationStatus(str, Enum):
    """Enumeration of student application statuses."""
    EXPLORING = "Exploring"
    SHORTLISTING = "Shortlisting"
    APPLYING = "Applying"
    SUBMITTED = "Submitted"


class StudentBase(BaseModel):
    """
    Base student model with core fields and validation.
    
    This model defines the essential student information required
    for the platform, with proper validation rules and constraints.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Student's full name"
    )
    email: EmailStr = Field(
        ...,
        description="Student's email address"
    )
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="Student's phone number"
    )
    country: str = Field(
        ...,
        min_length=2,
        max_length=3,
        description="Student's country code (ISO 3166-1 alpha-3)"
    )
    grade: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Student's current grade or year"
    )
    application_status: ApplicationStatus = Field(
        default=ApplicationStatus.EXPLORING,
        description="Current application status"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name contains only letters, spaces, and common punctuation."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Allow letters, spaces, hyphens, apostrophes, and periods
        import re
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v.strip()):
            raise ValueError('Name contains invalid characters')
        
        return v.strip()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format if provided."""
        if v is None:
            return v
        
        # Remove all non-digit characters for validation
        import re
        digits_only = re.sub(r'\D', '', v)
        
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError('Phone number must be 10-15 digits')
        
        return v
    
    @field_validator('country')
    @classmethod
    def validate_country_code(cls, v):
        """Validate country code format (ISO 3166-1 alpha-3)."""
        if not v or len(v) != 3:
            raise ValueError('Country code must be 3 characters (ISO 3166-1 alpha-3)')
        
        # Convert to uppercase for consistency
        country_code = v.upper()
        
        # Basic validation - should be letters only
        if not country_code.isalpha():
            raise ValueError('Country code must contain only letters')
        
        return country_code
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        """Validate grade format if provided."""
        if v is None:
            return v
        
        # Allow common grade formats: "12th", "Grade 12", "Senior", etc.
        import re
        if not re.match(r"^[a-zA-Z0-9\s\-\.]+$", v.strip()):
            raise ValueError('Grade contains invalid characters')
        
        return v.strip()
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Prevent additional fields


class Student(StudentBase):
    """
    Complete student model with database fields.
    
    This model extends StudentBase with additional fields that are
    managed by the system (ID, timestamps, AI summary).
    """
    id: str = Field(
        ...,
        description="Unique student identifier"
    )
    ai_summary: Optional[str] = Field(
        None,
        max_length=1000,
        description="AI-generated summary of student profile"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record last update timestamp"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"


class StudentCreate(StudentBase):
    """
    Student creation model for API input validation.
    
    This model is used for validating student data when creating
    new student records through the API.
    """
    pass  # Inherits all fields from StudentBase


class StudentUpdate(BaseModel):
    """
    Student update model for partial updates.
    
    This model allows partial updates of student information,
    with all fields being optional for flexible updates.
    """
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Student's full name"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Student's email address"
    )
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="Student's phone number"
    )
    country: Optional[str] = Field(
        None,
        min_length=2,
        max_length=3,
        description="Student's country code (ISO 3166-1 alpha-3)"
    )
    grade: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Student's current grade or year"
    )
    application_status: Optional[ApplicationStatus] = Field(
        None,
        description="Current application status"
    )
    ai_summary: Optional[str] = Field(
        None,
        max_length=1000,
        description="AI-generated summary of student profile"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name if provided."""
        if v is None:
            return v
        return StudentBase.validate_name(v)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number if provided."""
        if v is None:
            return v
        return StudentBase.validate_phone(v)
    
    @field_validator('country')
    @classmethod
    def validate_country_code(cls, v):
        """Validate country code if provided."""
        if v is None:
            return v
        return StudentBase.validate_country_code(v)
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        """Validate grade if provided."""
        if v is None:
            return v
        return StudentBase.validate_grade(v)
    
    @model_validator(mode='before')
    @classmethod
    def validate_at_least_one_field(cls, values):
        """Ensure at least one field is provided for update."""
        if isinstance(values, dict) and not any(values.values()):
            raise ValueError('At least one field must be provided for update')
        return values
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"


class StudentListResponse(BaseModel):
    """
    Response model for student list operations.
    
    This model provides pagination and metadata for student list responses.
    """
    students: list[Student] = Field(
        ...,
        description="List of students"
    )
    total_count: int = Field(
        ...,
        description="Total number of students"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number"
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of students per page"
    )
    has_next: bool = Field(
        ...,
        description="Whether there are more pages"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        extra = "forbid"
