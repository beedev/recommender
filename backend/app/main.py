"""
Main FastAPI application for the Pconfig Recommender API.

This module sets up the FastAPI application with middleware, error handlers,
dependency injection, and API routing for the welding equipment recommendation system.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn

from .core.config import settings, get_cors_config
from .database import init_databases, close_all_connections, health_check_all_databases
from .database.sqlalchemy_config import init_sqlalchemy, close_sqlalchemy
from .api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log") if not settings.is_development else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    
    Handles startup and shutdown tasks including database connections.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize databases
    try:
        # Initialize SQLAlchemy for authentication
        init_sqlalchemy()
        logger.info("SQLAlchemy initialized for authentication")
        
        # Initialize other databases
        db_status = await init_databases()
        logger.info(f"Database initialization status: {db_status}")
        
        # Store database status in app state
        app.state.database_status = db_status
        
        # Log successful connections
        for db_name, status in db_status.items():
            if status.get("status") == "connected":
                logger.info(f"✓ {db_name.title()} database connected successfully")
            else:
                logger.error(f"✗ {db_name.title()} database connection failed: {status.get('error')}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        app.state.database_status = {"error": str(e)}
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_sqlalchemy()
    await close_all_connections()
    logger.info("Application shutdown completed")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered welding equipment recommendation system with Neo4j graph database",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan
    )
    
    # Configure CORS middleware
    if settings.ENABLE_CORS:
        cors_config = get_cors_config()
        app.add_middleware(
            CORSMiddleware,
            **cors_config
        )
        logger.info("CORS middleware enabled")
    
    # Add trusted host middleware for production
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure this properly for production
        )
        logger.info("TrustedHost middleware enabled")
    
    # Include API routes
    app.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX
    )
    
    return app


# Create the FastAPI application
app = create_application()


# =============================================================================
# GLOBAL EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with consistent error format.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTP_ERROR",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """
    Handle internal server errors with consistent error format.
    
    Args:
        request: FastAPI request object
        exc: Exception
        
    Returns:
        JSON error response
    """
    logger.error(f"Internal server error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "INTERNAL_SERVER_ERROR",
                "status_code": 500,
                "message": "An internal server error occurred" if settings.is_production else str(exc),
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Handle value errors as bad requests.
    
    Args:
        request: FastAPI request object
        exc: ValueError
        
    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "VALIDATION_ERROR",
                "status_code": 400,
                "message": str(exc),
                "path": str(request.url.path)
            }
        }
    )


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API information and status
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "redoc": f"{settings.API_V1_PREFIX}/redoc",
        "openapi": f"{settings.API_V1_PREFIX}/openapi.json"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with database status.
    
    Returns:
        Application and database health status
    """
    # Check database connections
    db_health = await health_check_all_databases()
    
    # Determine overall health
    all_healthy = all(
        status.get("status") == "healthy" 
        for status in db_health.values()
    )
    
    # Calculate response time (basic application health)
    import time
    start_time = time.time()
    test_operation = {"test": "ok"}  # Simple operation
    response_time = (time.time() - start_time) * 1000
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": "2024-09-14T16:33:00Z",  # Current timestamp would be dynamic
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "application": {
            "status": "healthy",
            "response_time_ms": round(response_time, 2)
        },
        "databases": db_health,
        "details": {
            "uptime_seconds": 0,  # Would be calculated from startup time
            "memory_usage": "N/A"  # Would be actual memory usage
        }
    }


@app.get("/info")
async def app_info():
    """
    Application information endpoint.
    
    Returns:
        Detailed application information
    """
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "api": {
            "version": "v1",
            "prefix": settings.API_V1_PREFIX,
            "documentation": {
                "swagger": f"{settings.API_V1_PREFIX}/docs",
                "redoc": f"{settings.API_V1_PREFIX}/redoc",
                "openapi": f"{settings.API_V1_PREFIX}/openapi.json"
            }
        },
        "features": {
            "cors_enabled": settings.ENABLE_CORS,
            "authentication": "JWT",
            "databases": ["Neo4j", "PostgreSQL"],
            "caching": "PostgreSQL + Redis (optional)"
        },
        "configuration": {
            "items_per_page": settings.ITEMS_PER_PAGE,
            "max_items_per_page": settings.MAX_ITEMS_PER_PAGE,
            "api_timeout": settings.API_TIMEOUT,
            "max_retries": settings.MAX_API_RETRIES
        }
    }


# =============================================================================
# CUSTOM OPENAPI CONFIGURATION
# =============================================================================

def custom_openapi():
    """
    Custom OpenAPI schema generation.
    
    Returns:
        OpenAPI schema with custom configuration
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        ## Pconfig Welding Equipment Recommendation System
        
        AI-powered recommendation system for welding equipment using Neo4j graph database
        and advanced machine learning algorithms.
        
        ### Features:
        - **Product Search & Discovery**: Search welding equipment by category, specifications
        - **AI Recommendations**: Personalized product recommendations based on user needs
        - **Graph Relationships**: Explore product relationships and compatibility
        - **Package Management**: Pre-configured equipment packages for specific applications
        - **User Management**: Authentication, preferences, and session management
        
        ### Authentication:
        This API uses JWT tokens for authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ### Rate Limiting:
        API requests are rate-limited to ensure fair usage and system stability.
        
        ### Support:
        For technical support, please contact the development team.
        """,
        routes=app.routes,
        servers=[
            {"url": "/", "description": "Current server"}
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for user authentication"
        }
    }
    
    # Add tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "Products",
            "description": "Product search and information"
        },
        {
            "name": "Recommendations",
            "description": "AI-powered product recommendations"
        },
        {
            "name": "Packages",
            "description": "Equipment packages and bundles"
        },
        {
            "name": "User Management",
            "description": "User profiles and preferences"
        },
        {
            "name": "Health",
            "description": "System health and monitoring"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        access_log=settings.DEBUG_LOGGING,
        log_level="debug" if settings.DEBUG else "info"
    )