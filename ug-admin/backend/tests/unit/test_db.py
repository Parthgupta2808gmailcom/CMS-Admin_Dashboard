"""
Unit tests for database connectivity and Firestore client.

This module tests the core database functionality including client
initialization, connectivity checks, and error handling scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from google.api_core import exceptions as gcp_exceptions

from app.core.db import get_firestore_client, check_firestore, reset_firestore_client
from app.core.errors import AppError
from app.core.config import settings


class TestFirestoreClient:
    """Test suite for Firestore client initialization and management."""
    
    def setup_method(self):
        """Reset Firestore client before each test."""
        reset_firestore_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_firestore_client()
    
    @patch('app.core.db.firestore.Client')
    def test_get_firestore_client_success(self, mock_client_class):
        """Test successful Firestore client initialization."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Call the function
        client = get_firestore_client()
        
        # Verify client was created with correct parameters
        mock_client_class.assert_called_once()
        assert client == mock_client
        
        # Verify client was created with correct parameters
        call_args = mock_client_class.call_args
        assert call_args.kwargs['project'] == settings.firebase_project_id
    
    @patch('app.core.db.firestore.Client')
    def test_get_firestore_client_singleton(self, mock_client_class):
        """Test that Firestore client is a singleton."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Get client twice
        client1 = get_firestore_client()
        client2 = get_firestore_client()
        
        # Should be the same instance
        assert client1 is client2
        assert client1 is mock_client
        
        # Client should only be created once
        assert mock_client_class.call_count == 1
    
    @patch('app.core.db.firestore.Client')
    def test_get_firestore_client_initialization_error(self, mock_client_class):
        """Test Firestore client initialization failure."""
        # Mock client creation to raise an exception
        mock_client_class.side_effect = Exception("Connection failed")
        
        # Should raise AppError
        with pytest.raises(AppError) as exc_info:
            get_firestore_client()
        
        assert exc_info.value.code == "INTERNAL"
        assert "Failed to initialize Firestore client" in exc_info.value.message
        assert "Connection failed" in str(exc_info.value.details["error"])
    
    def test_reset_firestore_client(self):
        """Test that reset_firestore_client clears the global instance."""
        with patch('app.core.db.firestore.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Initialize client
            client1 = get_firestore_client()
            assert client1 is mock_client
            
            # Reset client
            reset_firestore_client()
            
            # Get client again - should create new instance
            client2 = get_firestore_client()
            assert client2 is mock_client
            assert mock_client_class.call_count == 2


class TestFirestoreConnectivity:
    """Test suite for Firestore connectivity checks."""
    
    def setup_method(self):
        """Reset Firestore client before each test."""
        reset_firestore_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_firestore_client()
    
    @patch('app.core.db.get_firestore_client')
    def test_check_firestore_success(self, mock_get_client):
        """Test successful Firestore connectivity check."""
        # Mock client and collections
        mock_client = Mock()
        mock_collections = [Mock(), Mock(), Mock()]
        mock_client.collections.return_value = mock_collections
        mock_get_client.return_value = mock_client
        
        # Call the function
        result = check_firestore()
        
        # Verify result
        assert result["status"] == "up"
        assert result["project_id"] == settings.firebase_project_id
        assert result["collections_count"] == 3
        assert "timestamp" in result
        
        # Verify client was called
        mock_get_client.assert_called_once()
        mock_client.collections.assert_called_once()
    
    @patch('app.core.db.get_firestore_client')
    def test_check_firestore_permission_denied(self, mock_get_client):
        """Test Firestore connectivity check with permission denied."""
        # Mock client to raise permission denied
        mock_client = Mock()
        mock_client.collections.side_effect = gcp_exceptions.PermissionDenied("Access denied")
        mock_get_client.return_value = mock_client
        
        # Should raise AppError with AUTH code
        with pytest.raises(AppError) as exc_info:
            check_firestore()
        
        assert exc_info.value.code == "AUTH"
        assert "Firestore access denied" in exc_info.value.message
        assert "Access denied" in str(exc_info.value.details["error"])
    
    @patch('app.core.db.get_firestore_client')
    def test_check_firestore_service_unavailable(self, mock_get_client):
        """Test Firestore connectivity check with service unavailable."""
        # Mock client to raise service unavailable
        mock_client = Mock()
        mock_client.collections.side_effect = gcp_exceptions.ServiceUnavailable("Service down")
        mock_get_client.return_value = mock_client
        
        # Should raise AppError with INTERNAL code
        with pytest.raises(AppError) as exc_info:
            check_firestore()
        
        assert exc_info.value.code == "INTERNAL"
        assert "Firestore service unavailable" in exc_info.value.message
        assert "Service down" in str(exc_info.value.details["error"])
    
    @patch('app.core.db.get_firestore_client')
    def test_check_firestore_unexpected_error(self, mock_get_client):
        """Test Firestore connectivity check with unexpected error."""
        # Mock client to raise unexpected error
        mock_client = Mock()
        mock_client.collections.side_effect = Exception("Unexpected error")
        mock_get_client.return_value = mock_client
        
        # Should raise AppError with INTERNAL code
        with pytest.raises(AppError) as exc_info:
            check_firestore()
        
        assert exc_info.value.code == "INTERNAL"
        assert "Firestore connectivity check failed" in exc_info.value.message
        assert "Unexpected error" in str(exc_info.value.details["error"])
    
    @patch('app.core.db.get_firestore_client')
    def test_check_firestore_client_initialization_error(self, mock_get_client):
        """Test Firestore connectivity check when client initialization fails."""
        # Mock client initialization to fail
        mock_get_client.side_effect = AppError("Client init failed", "INTERNAL")
        
        # Should raise the same AppError
        with pytest.raises(AppError) as exc_info:
            check_firestore()
        
        assert exc_info.value.code == "INTERNAL"
        assert "Firestore connectivity check failed" in exc_info.value.message


class TestFirestoreCollection:
    """Test suite for Firestore collection access."""
    
    def setup_method(self):
        """Reset Firestore client before each test."""
        reset_firestore_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_firestore_client()
    
    @patch('app.core.db.get_firestore_client')
    def test_get_firestore_collection_success(self, mock_get_client):
        """Test successful collection retrieval."""
        from app.core.db import get_firestore_collection
        
        # Mock client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collection.return_value = mock_collection
        mock_get_client.return_value = mock_client
        
        # Call the function
        collection = get_firestore_collection("test_collection")
        
        # Verify result
        assert collection == mock_collection
        mock_client.collection.assert_called_once_with("test_collection")
    
    @patch('app.core.db.get_firestore_client')
    def test_get_firestore_collection_error(self, mock_get_client):
        """Test collection retrieval with error."""
        from app.core.db import get_firestore_collection
        
        # Mock client to raise error
        mock_get_client.side_effect = Exception("Client error")
        
        # Should raise AppError
        with pytest.raises(AppError) as exc_info:
            get_firestore_collection("test_collection")
        
        assert exc_info.value.code == "INTERNAL"
        assert "Failed to access collection: test_collection" in exc_info.value.message
        assert "Client error" in str(exc_info.value.details["error"])
