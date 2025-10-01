"""
Application configuration management using pydantic-settings.

This module centralizes all environment variable handling and provides
type-safe configuration access throughout the application.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment configuration
    env: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # CORS configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    # Firebase configuration (for future phases)
    firebase_project_id: str = Field(default="", description="Firebase project ID")
    firebase_private_key_id: str = Field(default="", description="Firebase private key ID")
    firebase_private_key: str = Field(default="", description="Firebase private key")
    firebase_client_email: str = Field(default="", description="Firebase client email")
    firebase_client_id: str = Field(default="", description="Firebase client ID")
    firebase_auth_uri: str = Field(default="https://accounts.google.com/o/oauth2/auth", description="Firebase auth URI")
    firebase_token_uri: str = Field(default="https://oauth2.googleapis.com/token", description="Firebase token URI")
    
    # Application metadata
    app_name: str = Field(default="UG Admin Backend", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() == "production"


# Global settings instance
# This will be imported throughout the application for configuration access
settings = Settings()
