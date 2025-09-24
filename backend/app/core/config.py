"""
Core configuration management for the Pconfig Recommender API.

This module provides centralized configuration management with environment-based
settings, security configurations, and database connection parameters.
"""

import os
import secrets
from typing import List, Optional, Union
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic.functional_validators import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_NAME: str = "Pconfig Recommender API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="NODE_ENV")
    
    # Server configuration
    HOST: str = Field(default="0.0.0.0", env="SERVER_HOST")
    PORT: int = Field(default=3000, env="backend_port")
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    SECRET_KEY: str = Field(env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES: int = Field(default=3600, description="1 hour in seconds")
    JWT_REFRESH_TOKEN_EXPIRES: int = Field(default=2592000, description="30 days in seconds")
    JWT_ALGORITHM: str = "HS256"
    
    # CORS settings
    ENABLE_CORS: bool = Field(default=True, env="ENABLE_CORS")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    # Neo4j configuration
    NEO4J_URI: str = Field(env="NEO4J_URI")
    NEO4J_USERNAME: str = Field(env="NEO4J_USERNAME")
    NEO4J_PASSWORD: str = Field(env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(env="NEO4J_DATABASE")
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = Field(default=50)
    NEO4J_CONNECTION_ACQUISITION_TIMEOUT: int = Field(default=60)
    NEO4J_CONNECTION_TIMEOUT: int = Field(default=30)
    NEO4J_MAX_TRANSACTION_RETRY_TIME: int = Field(default=30)
    
    # PostgreSQL configuration
    POSTGRES_HOST: str = Field(env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(env="POSTGRES_DB")
    POSTGRES_USER: str = Field(env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(env="POSTGRES_PASSWORD")
    POSTGRES_MAX_CONNECTIONS: int = Field(default=20)
    POSTGRES_MIN_CONNECTIONS: int = Field(default=5)
    
    # Redis configuration (optional)
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    ENABLE_REDIS_CACHING: bool = Field(default=True, env="ENABLE_REDIS_CACHING")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    API_V1_PREFIX: str = "/api/v1"
    ITEMS_PER_PAGE: int = Field(default=20, env="ITEMS_PER_PAGE")
    MAX_ITEMS_PER_PAGE: int = Field(default=100, env="MAX_ITEMS_PER_PAGE")
    API_TIMEOUT: int = Field(default=30, env="API_TIMEOUT")
    MAX_API_RETRIES: int = Field(default=3, env="MAX_API_RETRIES")
    
    # =============================================================================
    # LLM/AI CONFIGURATION
    # =============================================================================
    OPENAI_API_KEY: Optional[str] = Field(env="OPENAI_API_KEY")
    DEFAULT_TEMPERATURE: float = Field(default=0.3, env="DEFAULT_TEMPERATURE")
    MAX_TOKENS: int = Field(default=4000, env="MAX_TOKENS")
    
    # LangSmith configuration
    LANGSMITH_API_KEY: Optional[str] = Field(env="LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = Field(default="Recommender", env="LANGSMITH_PROJECT")
    
    # Agent Transaction Tracking
    ENABLE_AGENT_TRACKING: bool = Field(default=True, env="ENABLE_AGENT_TRACKING")
    AGENT_TRACKING_BATCH_SIZE: int = Field(default=100, env="AGENT_TRACKING_BATCH_SIZE")
    AGENT_TRACKING_FLUSH_INTERVAL: int = Field(default=30, env="AGENT_TRACKING_FLUSH_INTERVAL")
    
    # Vector Compatibility Configuration
    VECTOR_CONFIDENCE_THRESHOLD: float = Field(default=0.8, env="VECTOR_CONFIDENCE_THRESHOLD")
    VECTOR_SEARCH_LIMIT: int = Field(default=20, env="VECTOR_SEARCH_LIMIT")
    ENABLE_COMPATIBILITY_FALLBACK: bool = Field(default=True, env="ENABLE_COMPATIBILITY_FALLBACK")
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO")
    DEBUG_LOGGING: bool = Field(default=False, env="DEBUG_LOGGING")
    
    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    @property
    def neo4j_connection_url(self) -> str:
        """Complete Neo4j connection URL."""
        return f"{self.NEO4J_URI}"
    
    @property
    def postgres_dsn(self) -> str:
        """Complete PostgreSQL connection URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    # =============================================================================
    # VALIDATORS
    # =============================================================================
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is not empty and has sufficient length."""
        if not v:
            raise ValueError("SECRET_KEY must be provided")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Ensure JWT_SECRET_KEY is not empty and has sufficient length."""
        if not v:
            raise ValueError("JWT_SECRET_KEY must be provided")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("NEO4J_URI")
    @classmethod
    def validate_neo4j_uri(cls, v: str) -> str:
        """Validate Neo4j URI format."""
        if not v:
            raise ValueError("NEO4J_URI must be provided")
        if not v.startswith(("bolt://", "neo4j://", "bolt+s://", "neo4j+s://")):
            raise ValueError("NEO4J_URI must use bolt:// or neo4j:// protocol")
        return v
    
    @field_validator("POSTGRES_HOST")
    @classmethod
    def validate_postgres_host(cls, v: str) -> str:
        """Ensure PostgreSQL host is provided."""
        if not v:
            raise ValueError("POSTGRES_HOST must be provided")
        return v
    
    @field_validator("ITEMS_PER_PAGE")
    @classmethod
    def validate_items_per_page(cls, v: int) -> int:
        """Ensure ITEMS_PER_PAGE is positive and reasonable."""
        if v <= 0:
            raise ValueError("ITEMS_PER_PAGE must be positive")
        if v > 1000:
            raise ValueError("ITEMS_PER_PAGE must not exceed 1000")
        return v
    
    @field_validator("MAX_ITEMS_PER_PAGE")
    @classmethod
    def validate_max_items_per_page(cls, v: int) -> int:
        """Ensure MAX_ITEMS_PER_PAGE is greater than 0."""
        if v <= 0:
            raise ValueError("MAX_ITEMS_PER_PAGE must be positive")
        return v
    
    @field_validator("VECTOR_CONFIDENCE_THRESHOLD")
    @classmethod
    def validate_vector_confidence_threshold(cls, v: float) -> float:
        """Ensure VECTOR_CONFIDENCE_THRESHOLD is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("VECTOR_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        return v
    
    @field_validator("VECTOR_SEARCH_LIMIT")
    @classmethod
    def validate_vector_search_limit(cls, v: int) -> int:
        """Ensure VECTOR_SEARCH_LIMIT is positive and reasonable."""
        if v <= 0:
            raise ValueError("VECTOR_SEARCH_LIMIT must be positive")
        if v > 100:
            raise ValueError("VECTOR_SEARCH_LIMIT should not exceed 100 for performance reasons")
        return v
    
    model_config = {
        "env_file": "../.env",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()


def generate_secret_key() -> str:
    """
    Generate a cryptographically secure secret key.
    
    Returns:
        str: Random secret key
    """
    return secrets.token_hex(32)


def get_cors_config() -> dict:
    """
    Get CORS configuration based on environment settings.
    
    Returns:
        dict: CORS configuration for FastAPI
    """
    settings = get_settings()
    
    if not settings.ENABLE_CORS:
        return {}
    
    return {
        "allow_origins": settings.ALLOWED_ORIGINS,
        "allow_credentials": True,
        "allow_methods": settings.ALLOWED_METHODS,
        "allow_headers": settings.ALLOWED_HEADERS,
    }


# Export settings instance for convenience
settings = get_settings()