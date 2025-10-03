"""
Tests for advanced search API endpoints.

This module contains comprehensive tests for search functionality
including multi-field filtering, full-text search, facets, and suggestions.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.core.auth import UserRole
from app.services.search import SearchResult, SearchField, SortOrder
from app.schemas.student import Student, ApplicationStatus


class TestAdvancedSearchEndpoint:
    """Test cases for advanced search endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.search_students')
    def test_successful_text_search(self, mock_search, mock_get_role, mock_verify_token):
        """Test successful text search with staff user."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock search result
        mock_students = [
            Student(
                id="student1",
                name="John Doe",
                email="john@test.com",
                country="USA",
                application_status=ApplicationStatus.EXPLORING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_search_result = SearchResult(
            students=mock_students,
            total_count=100,
            filtered_count=1,
            page_info={
                "limit": 50,
                "offset": 0,
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False
            },
            search_metadata={
                "processing_time_seconds": 0.5,
                "query_complexity": "low",
                "filters_applied": 1,
                "text_search_used": True
            }
        )
        
        mock_search.return_value = mock_search_result
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        search_request = {
            "text_query": "John Doe",
            "search_fields": ["name", "email"],
            "limit": 50,
            "offset": 0
        }
        
        response = self.client.post("/api/v1/search/students", headers=headers, json=search_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["results"]["students"]) == 1
        assert result["results"]["students"][0]["name"] == "John Doe"
        assert result["results"]["filtered_count"] == 1
        assert result["results"]["search_metadata"]["text_search_used"] is True
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.search_students')
    def test_search_with_filters(self, mock_search, mock_get_role, mock_verify_token):
        """Test search with application status and country filters."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock search result
        mock_students = [
            Student(
                id="student1",
                name="John Doe",
                email="john@test.com",
                country="USA",
                application_status=ApplicationStatus.APPLYING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Student(
                id="student2",
                name="Jane Smith",
                email="jane@test.com",
                country="USA",
                application_status=ApplicationStatus.APPLYING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_search_result = SearchResult(
            students=mock_students,
            total_count=100,
            filtered_count=2,
            page_info={
                "limit": 50,
                "offset": 0,
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False
            },
            search_metadata={
                "processing_time_seconds": 0.3,
                "query_complexity": "medium",
                "filters_applied": 2,
                "text_search_used": False
            }
        )
        
        mock_search.return_value = mock_search_result
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        search_request = {
            "application_statuses": ["Applying"],
            "countries": ["USA"],
            "sort_field": "name",
            "sort_order": "asc",
            "limit": 50,
            "offset": 0
        }
        
        response = self.client.post("/api/v1/search/students", headers=headers, json=search_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["results"]["students"]) == 2
        assert all(s["country"] == "USA" for s in result["results"]["students"])
        assert all(s["application_status"] == "Applying" for s in result["results"]["students"])
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_search_requires_staff_or_admin(self, mock_get_role, mock_verify_token):
        """Test that search endpoint requires staff or admin role."""
        
        # Mock authentication with invalid role
        mock_verify_token.return_value = {"uid": "user-123", "email": "user@test.com"}
        mock_get_role.return_value = None
        
        headers = {"Authorization": "Bearer invalid-role-token"}
        search_request = {"text_query": "test"}
        
        response = self.client.post("/api/v1/search/students", headers=headers, json=search_request)
        
        assert response.status_code in [401, 403]
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.search_students')
    def test_search_pagination(self, mock_search, mock_get_role, mock_verify_token):
        """Test search with pagination parameters."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock search result for page 2
        mock_students = [
            Student(
                id="student51",
                name="Student 51",
                email="student51@test.com",
                country="Canada",
                application_status=ApplicationStatus.EXPLORING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_search_result = SearchResult(
            students=mock_students,
            total_count=100,
            filtered_count=100,
            page_info={
                "limit": 50,
                "offset": 50,
                "current_page": 2,
                "total_pages": 2,
                "has_next": False,
                "has_previous": True
            },
            search_metadata={
                "processing_time_seconds": 0.4,
                "query_complexity": "low",
                "filters_applied": 0,
                "text_search_used": False
            }
        )
        
        mock_search.return_value = mock_search_result
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        search_request = {
            "limit": 50,
            "offset": 50,
            "sort_field": "created_at",
            "sort_order": "desc"
        }
        
        response = self.client.post("/api/v1/search/students", headers=headers, json=search_request)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["results"]["page_info"]["current_page"] == 2
        assert result["results"]["page_info"]["has_previous"] is True
        assert result["results"]["page_info"]["has_next"] is False


class TestSearchSuggestionsEndpoint:
    """Test cases for search suggestions endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.get_search_suggestions')
    def test_get_name_suggestions(self, mock_suggestions, mock_get_role, mock_verify_token):
        """Test getting name suggestions for autocomplete."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock suggestions
        mock_suggestions.return_value = ["John Doe", "John Smith", "Johnny Wilson"]
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        params = {
            "field": "name",
            "partial_value": "John",
            "limit": 10
        }
        
        response = self.client.get("/api/v1/search/suggestions", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["suggestions"]) == 3
        assert all("John" in suggestion for suggestion in result["suggestions"])
        assert result["field"] == "name"
        assert result["partial_value"] == "John"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.get_search_suggestions')
    def test_get_country_suggestions(self, mock_suggestions, mock_get_role, mock_verify_token):
        """Test getting country suggestions."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock suggestions
        mock_suggestions.return_value = ["United States", "United Kingdom"]
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        params = {
            "field": "country",
            "partial_value": "Unit",
            "limit": 5
        }
        
        response = self.client.get("/api/v1/search/suggestions", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["suggestions"]) == 2
        assert result["field"] == "country"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    def test_suggestions_require_authentication(self, mock_get_role, mock_verify_token):
        """Test that suggestions endpoint requires authentication."""
        
        # No authentication header
        params = {
            "field": "name",
            "partial_value": "test"
        }
        
        response = self.client.get("/api/v1/search/suggestions", params=params)
        
        assert response.status_code == 403  # No auth header


class TestSearchFacetsEndpoint:
    """Test cases for search facets endpoint."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.get_search_facets')
    def test_get_search_facets(self, mock_facets, mock_get_role, mock_verify_token):
        """Test getting search facets for filtering UI."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock facets
        mock_facets.return_value = {
            "application_status": {
                "Exploring": 45,
                "Shortlisting": 32,
                "Applying": 18,
                "Submitted": 5
            },
            "country": {
                "USA": 60,
                "Canada": 25,
                "UK": 15
            },
            "grade": {
                "12": 50,
                "11": 30,
                "Graduate": 20
            },
            "total_count": 100
        }
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        
        response = self.client.get("/api/v1/search/facets", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["facets"]["total_count"] == 100
        assert "application_status" in result["facets"]
        assert "country" in result["facets"]
        assert "grade" in result["facets"]
        assert result["facets"]["application_status"]["Exploring"] == 45
        assert result["facets"]["country"]["USA"] == 60
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.get_search_facets')
    def test_facets_with_admin_user(self, mock_facets, mock_get_role, mock_verify_token):
        """Test facets endpoint with admin user."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock facets
        mock_facets.return_value = {
            "application_status": {"Exploring": 10},
            "country": {"USA": 10},
            "grade": {"12": 10},
            "total_count": 10
        }
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        
        response = self.client.get("/api/v1/search/facets", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True


class TestSimpleSearchEndpoint:
    """Test cases for simple search endpoint (backward compatibility)."""
    
    client = TestClient(app)
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.search_students')
    def test_simple_search_with_query_params(self, mock_search, mock_get_role, mock_verify_token):
        """Test simple search using query parameters."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "staff-123", "email": "staff@test.com"}
        mock_get_role.return_value = UserRole.STAFF
        
        # Mock search result
        mock_students = [
            Student(
                id="student1",
                name="Test Student",
                email="test@test.com",
                country="USA",
                application_status=ApplicationStatus.EXPLORING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_search_result = SearchResult(
            students=mock_students,
            total_count=50,
            filtered_count=1,
            page_info={
                "limit": 20,
                "offset": 0,
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False
            },
            search_metadata={
                "processing_time_seconds": 0.2,
                "query_complexity": "low",
                "filters_applied": 2,
                "text_search_used": True
            }
        )
        
        mock_search.return_value = mock_search_result
        
        headers = {"Authorization": "Bearer valid-staff-token"}
        params = {
            "q": "Test",
            "status": "Exploring",
            "country": "USA",
            "sort": "name",
            "order": "asc",
            "limit": 20,
            "offset": 0
        }
        
        response = self.client.get("/api/v1/search/students/simple", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["results"]["students"]) == 1
        assert result["results"]["students"][0]["name"] == "Test Student"
    
    @patch('app.core.auth.firebase_auth.verify_id_token')
    @patch('app.core.auth.get_user_role_from_firestore')
    @patch('app.services.search.search_service.search_students')
    def test_simple_search_without_query(self, mock_search, mock_get_role, mock_verify_token):
        """Test simple search without text query (list all)."""
        
        # Mock authentication
        mock_verify_token.return_value = {"uid": "admin-123", "email": "admin@test.com"}
        mock_get_role.return_value = UserRole.ADMIN
        
        # Mock search result
        mock_students = [
            Student(
                id="student1",
                name="Student 1",
                email="student1@test.com",
                country="Canada",
                application_status=ApplicationStatus.SHORTLISTING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_search_result = SearchResult(
            students=mock_students,
            total_count=100,
            filtered_count=50,
            page_info={
                "limit": 50,
                "offset": 0,
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False
            },
            search_metadata={
                "processing_time_seconds": 0.1,
                "query_complexity": "low",
                "filters_applied": 1,
                "text_search_used": False
            }
        )
        
        mock_search.return_value = mock_search_result
        
        headers = {"Authorization": "Bearer valid-admin-token"}
        params = {
            "country": "Canada",
            "limit": 50
        }
        
        response = self.client.get("/api/v1/search/students/simple", headers=headers, params=params)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["results"]["search_metadata"]["text_search_used"] is False
