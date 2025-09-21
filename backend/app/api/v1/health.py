"""
Health check endpoints for system monitoring and diagnostics.

Provides detailed health status for databases, external services,
and application components.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ...database import health_check_all_databases, get_database_connections
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with database and service status.
    
    Returns:
        Comprehensive health status including all components
    """
    try:
        # Check database connections
        db_health = await health_check_all_databases()
        
        # Determine overall health
        all_databases_healthy = all(
            status.get("status") == "healthy" 
            for status in db_health.values()
        )
        
        # Calculate overall status
        overall_status = "healthy" if all_databases_healthy else "degraded"
        
        # Get configuration status
        config_status = {
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG,
            "cors_enabled": settings.ENABLE_CORS,
            "jwt_configured": bool(settings.JWT_SECRET_KEY),
            "openai_configured": bool(settings.OPENAI_API_KEY)
        }
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT
            },
            "databases": db_health,
            "configuration": config_status,
            "api": {
                "version": "v1",
                "base_path": settings.API_V1_PREFIX,
                "items_per_page": settings.ITEMS_PER_PAGE,
                "max_items_per_page": settings.MAX_ITEMS_PER_PAGE
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "service": {
                    "name": settings.APP_NAME,
                    "version": settings.APP_VERSION
                }
            }
        )


@router.get("/database")
async def database_health():
    """
    Database-specific health check.
    
    Returns:
        Database connection status and statistics
    """
    try:
        db_health = await health_check_all_databases()
        
        # Get database connections for additional info
        connections = await get_database_connections()
        
        # Add database info if available
        enhanced_status = {}
        for db_name, health in db_health.items():
            enhanced_status[db_name] = {
                **health,
                "connection_available": db_name in connections
            }
            
            # Add specific database information
            if db_name == "neo4j" and health.get("status") == "healthy":
                try:
                    neo4j_conn = connections["neo4j"]
                    db_info = await neo4j_conn.get_database_info()
                    enhanced_status[db_name]["database_info"] = db_info
                except Exception as e:
                    logger.warning(f"Could not get Neo4j database info: {e}")
            
            elif db_name == "postgres" and health.get("status") == "healthy":
                try:
                    postgres_conn = connections["postgres"]
                    db_info = await postgres_conn.get_database_info()
                    enhanced_status[db_name]["database_info"] = db_info
                except Exception as e:
                    logger.warning(f"Could not get PostgreSQL database info: {e}")
        
        return {
            "status": "healthy" if all(
                status.get("status") == "healthy" 
                for status in enhanced_status.values()
            ) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "databases": enhanced_status
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/readiness")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    
    Returns:
        Service readiness status
    """
    try:
        # Check if databases are ready
        db_health = await health_check_all_databases()
        
        # Service is ready if at least one database is healthy
        neo4j_ready = db_health.get("neo4j", {}).get("status") == "healthy"
        postgres_ready = db_health.get("postgres", {}).get("status") == "healthy"
        
        ready = neo4j_ready  # Neo4j is required for core functionality
        
        if not ready:
            raise HTTPException(
                status_code=503,
                detail="Service not ready - Neo4j database unavailable"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "neo4j": neo4j_ready,
                "postgres": postgres_ready
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    
    Returns:
        Service liveness status
    """
    # Simple liveness check - if we can respond, we're alive
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }