"""
Comprehensive tests for health check endpoints.

This module tests the liveness and readiness endpoints to ensure
proper functionality and response format compliance.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    def test_liveness_endpoint(self):
        """
        Test that the liveness endpoint returns correct status.
        
        The liveness probe should return 200 with status "ok" to indicate
        the service is running and can accept requests.
        """
        client = TestClient(app)
        response = client.get("/api/v1/health/liveness")
        
        # Verify response status
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        
        # Verify response content
        assert data["status"] == "ok"
        assert isinstance(data["version"], str)
        assert isinstance(data["environment"], str)
    
    def test_readiness_endpoint(self):
        """
        Test that the readiness endpoint returns correct status.
        
        The readiness probe should return 200 with status "starting"
        (placeholder until Firestore integration in Phase 2).
        """
        client = TestClient(app)
        response = client.get("/api/v1/health/readiness")
        
        # Verify response status
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        
        # Verify response content (now includes database check)
        assert data["status"] in ["up", "down"]
        assert isinstance(data["version"], str)
        assert isinstance(data["environment"], str)
    
    def test_health_endpoints_response_headers(self):
        """
        Test that health endpoints include proper headers.
        
        Verify that request ID headers are included in responses
        for proper request correlation.
        """
        client = TestClient(app)
        
        # Test liveness headers
        liveness_response = client.get("/api/v1/health/liveness")
        assert "X-Request-ID" in liveness_response.headers
        assert liveness_response.headers["X-Request-ID"] is not None
        
        # Test readiness headers
        readiness_response = client.get("/api/v1/health/readiness")
        assert "X-Request-ID" in readiness_response.headers
        assert readiness_response.headers["X-Request-ID"] is not None
    
    def test_health_endpoints_content_type(self):
        """
        Test that health endpoints return proper content type.
        
        Verify that responses are returned as JSON with correct
        content-type headers.
        """
        client = TestClient(app)
        
        # Test liveness content type
        liveness_response = client.get("/api/v1/health/liveness")
        assert liveness_response.headers["content-type"] == "application/json"
        
        # Test readiness content type
        readiness_response = client.get("/api/v1/health/readiness")
        assert readiness_response.headers["content-type"] == "application/json"
    
    def test_health_endpoints_consistency(self):
        """
        Test that health endpoints return consistent data.
        
        Verify that both endpoints return the same version and
        environment information for consistency.
        """
        client = TestClient(app)
        
        # Get responses from both endpoints
        liveness_response = client.get("/api/v1/health/liveness")
        readiness_response = client.get("/api/v1/health/readiness")
        
        liveness_data = liveness_response.json()
        readiness_data = readiness_response.json()
        
        # Verify consistent metadata
        assert liveness_data["version"] == readiness_data["version"]
        assert liveness_data["environment"] == readiness_data["environment"]
        
        # Verify different status values
        assert liveness_data["status"] == "ok"
        assert readiness_data["status"] in ["up", "down"]
    
    @pytest.mark.asyncio
    async def test_health_endpoints_async(self):
        """
        Test health endpoints using async client.
        
        Verify that endpoints work correctly with async HTTP client
        for comprehensive testing coverage.
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test liveness with async client
            liveness_response = await client.get("/api/v1/health/liveness")
            assert liveness_response.status_code == 200
            liveness_data = liveness_response.json()
            assert liveness_data["status"] == "ok"
            
            # Test readiness with async client
            readiness_response = await client.get("/api/v1/health/readiness")
            assert readiness_response.status_code == 200
            readiness_data = readiness_response.json()
            assert readiness_data["status"] in ["up", "down"]


class TestRootEndpoint:
    """Test suite for the root endpoint."""
    
    def test_root_endpoint(self):
        """
        Test that the root endpoint returns application information.
        
        Verify that the root endpoint provides basic application
        metadata including name, version, and environment.
        """
        client = TestClient(app)
        response = client.get("/")
        
        # Verify response status
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "environment" in data
        assert "status" in data
        
        # Verify response content
        assert data["status"] == "running"
        assert isinstance(data["name"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["environment"], str)
