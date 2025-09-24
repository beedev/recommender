"""
API v1 endpoints for the Pconfig Recommender API.

This package contains version 1 of the API endpoints with versioned routing
and backwards compatibility support.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .health import router as health_router
from .products import router as products_router
from .packages import router as packages_router
from .package_builder import router as package_builder_router
# from .recommendations import router as recommendations_router  # Archived
from .sparky import router as sparky_router
from .system import router as system_router
from .enhanced_orchestrator import router as orchestrator_router
# from .agent_recommendations import router as agent_recommendations_router  # Archived
from .enterprise import enterprise_router
from .vector_compatibility import router as vector_compatibility_router

# Main API router for v1
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)

api_router.include_router(
    products_router,
    prefix="/products", 
    tags=["Products"]
)

api_router.include_router(
    packages_router,
    prefix="/packages",
    tags=["Packages"] 
)

api_router.include_router(
    package_builder_router,
    prefix="/package-builder",
    tags=["Package Builder"]
)

# api_router.include_router(
#     recommendations_router,
#     prefix="/recommendations", 
#     tags=["Recommendations"]
# )  # Archived

api_router.include_router(
    sparky_router,
    prefix="/sparky",
    tags=["Sparky AI"]
)

api_router.include_router(
    system_router,
    prefix="/system",
    tags=["System"]
)

api_router.include_router(
    orchestrator_router,
    prefix="/orchestrator",
    tags=["Agent Orchestration"]
)

# api_router.include_router(
#     agent_recommendations_router,
#     prefix="/agents",
#     tags=["Agent Recommendations"]
# )  # Archived

api_router.include_router(
    enterprise_router,
    prefix="/enterprise",
    tags=["Enterprise Recommendations"]
)

api_router.include_router(
    vector_compatibility_router,
    prefix="/vector-compatibility",
    tags=["Vector Compatibility Search"]
)

__all__ = ["api_router"]