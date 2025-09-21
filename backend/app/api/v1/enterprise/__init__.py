"""
Enterprise API Package
API endpoints for the 3-agent enterprise agentic system
"""

from fastapi import APIRouter
from .enterprise_recommendations import router as recommendations_router
from .guided_flow import router as guided_flow_router

# Main enterprise router
enterprise_router = APIRouter()

# Include sub-routers
enterprise_router.include_router(
    recommendations_router,
    tags=["Enterprise Recommendations"]
)

enterprise_router.include_router(
    guided_flow_router,
    prefix="/guided",
    tags=["Guided Flow"]
)

__all__ = ["enterprise_router"]