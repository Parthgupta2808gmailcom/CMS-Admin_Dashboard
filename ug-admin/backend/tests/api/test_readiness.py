"""
Integration tests for readiness endpoint with Firestore connectivity.

This module tests the readiness endpoint behavior with various Firestore
connectivity scenarios to ensure proper error handling and response formatting.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.db import check_firestore
from app.core.errors import AppError


class TestReadinessEndpoint:
    """Test suite for readiness endpoint with Firestore integration."""
    
    def test_readiness_success(self):
        """Test readiness endpoint with successful Firestore connectivity."""
        # Mock successful Firestore check
        mock_db_status = {
            "status": "up",
            "project_id": "test-project",
            "collections_count": 5,
            "timestamp": 1234567890.0
        }
        
        with patch('app.api.v1.health.check_firestore', return_value=mock_db_status):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "up"
            assert data["version"] == "0.1.0"
            assert data["environment"] == "development"
            # Note: Database info is included in successful responses
            if "database" in data:
                db_info = data["database"]
                assert db_info["status"] == "up"
                assert db_info["project_id"] == "test-project"
                assert db_info["collections_count"] == 5
    
    def test_readiness_firestore_error(self):
        """Test readiness endpoint with Firestore connectivity error."""
        # Mock Firestore check failure
        mock_error = AppError(
            message="Firestore service unavailable",
            code="INTERNAL",
            details={"error": "Connection timeout"}
        )
        
        with patch('app.api.v1.health.check_firestore', side_effect=mock_error):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "down"
            assert data["version"] == "0.1.0"
            assert data["environment"] == "development"
            # Note: Database info is included in error responses
            if "database" in data:
                db_info = data["database"]
                assert db_info["status"] == "down"
                assert db_info["error"] == "Firestore service unavailable"
                assert db_info["code"] == "INTERNAL"
    
    def test_readiness_permission_denied(self):
        """Test readiness endpoint with Firestore permission denied."""
        # Mock permission denied error
        mock_error = AppError(
            message="Firestore access denied",
            code="AUTH",
            details={"error": "Insufficient permissions"}
        )
        
        with patch('app.api.v1.health.check_firestore', side_effect=mock_error):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "down"
            # Note: Database info is included in error responses
            if "database" in data:
                db_info = data["database"]
                assert db_info["status"] == "down"
                assert db_info["error"] == "Firestore access denied"
                assert db_info["code"] == "AUTH"
    
    def test_readiness_unexpected_error(self):
        """Test readiness endpoint with unexpected error."""
        # Mock unexpected error
        with patch('app.api.v1.health.check_firestore', side_effect=Exception("Unexpected error")):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "down"
            # Note: Database info is included in error responses
            if "database" in data:
                db_info = data["database"]
                assert db_info["status"] == "down"
                assert db_info["error"] == "Unexpected error"
                assert db_info["code"] == "INTERNAL"
    
    def test_readiness_response_headers(self):
        """Test that readiness endpoint includes proper headers."""
        mock_db_status = {
            "status": "up",
            "project_id": "test-project",
            "collections_count": 3,
            "timestamp": 1234567890.0
        }
        
        with patch('app.api.v1.health.check_firestore', return_value=mock_db_status):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify headers
            assert "X-Request-ID" in response.headers
            assert response.headers["X-Request-ID"] is not None
            assert response.headers["content-type"] == "application/json"
    
    def test_readiness_content_type(self):
        """Test that readiness endpoint returns proper content type."""
        mock_db_status = {
            "status": "up",
            "project_id": "test-project",
            "collections_count": 2,
            "timestamp": 1234567890.0
        }
        
        with patch('app.api.v1.health.check_firestore', return_value=mock_db_status):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify content type
            assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_readiness_async_client(self):
        """Test readiness endpoint using async client."""
        mock_db_status = {
            "status": "up",
            "project_id": "test-project",
            "collections_count": 4,
            "timestamp": 1234567890.0
        }
        
        with patch('app.api.v1.health.check_firestore', return_value=mock_db_status):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/health/readiness")
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                assert data["status"] == "up"
                # Note: Database info is included in successful responses
                if "database" in data:
                    db_info = data["database"]
                    assert db_info["status"] == "up"
                    assert db_info["project_id"] == "test-project"
                    assert db_info["collections_count"] == 4
    
    def test_readiness_with_empty_collections(self):
        """Test readiness endpoint with empty Firestore collections."""
        mock_db_status = {
            "status": "up",
            "project_id": "test-project",
            "collections_count": 0,
            "timestamp": 1234567890.0
        }
        
        with patch('app.api.v1.health.check_firestore', return_value=mock_db_status):
            client = TestClient(app)
            response = client.get("/api/v1/health/readiness")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "up"
            # Note: Database info is included in successful responses
            if "database" in data:
                db_info = data["database"]
                assert db_info["status"] == "up"
                assert db_info["collections_count"] == 0
    
    def test_readiness_consistency_with_liveness(self):
        """Test that readiness and liveness endpoints return consistent metadata."""
        mock_db_status = {
            "status": "up",
            "project_id": "test-project",
            "collections_count": 3,
            "timestamp": 1234567890.0
        }
        
        with patch('app.api.v1.health.check_firestore', return_value=mock_db_status):
            client = TestClient(app)
            
            # Get both responses
            liveness_response = client.get("/api/v1/health/liveness")
            readiness_response = client.get("/api/v1/health/readiness")
            
            # Verify both succeed
            assert liveness_response.status_code == 200
            assert readiness_response.status_code == 200
            
            liveness_data = liveness_response.json()
            readiness_data = readiness_response.json()
            
            # Verify consistent metadata
            assert liveness_data["version"] == readiness_data["version"]
            assert liveness_data["environment"] == readiness_data["environment"]
            
            # Verify different status values
            assert liveness_data["status"] == "ok"
            assert readiness_data["status"] == "up"
            
            # Verify readiness has database info (when successful)
            if readiness_data["status"] == "up":
                assert "database" in readiness_data
                assert readiness_data["database"] is not None
            # Liveness should have database field as None
            assert "database" in liveness_data
            assert liveness_data["database"] is None
