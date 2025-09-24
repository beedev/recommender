"""
Vector Compatibility Search API Endpoints
Implements vector-first compatibility search with intelligent fallback
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...agents.simple_neo4j_agent import SimpleNeo4jAgent
from ...database.repositories import get_neo4j_repository
from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class VectorCompatibilityRequest(BaseModel):
    """Request for vector compatibility search"""
    query: str = Field(..., description="Natural language compatibility query")
    target_product_id: Optional[str] = Field(None, description="Specific product to find compatibility for")
    category_filter: Optional[str] = Field(None, description="Filter by product category")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")

class CompatibilityResult(BaseModel):
    """Single compatibility search result"""
    product_id: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    compatibility_score: float = Field(description="Similarity/compatibility score (0.0-1.0)")
    sales_frequency: int = Field(default=0, description="Historical sales frequency")

class VectorCompatibilityResponse(BaseModel):
    """Response from vector compatibility search"""
    query: str
    method_used: str = Field(description="Search method: vector_high_confidence|vector_low_confidence|rules_fallback|no_results|error")
    confidence_threshold: float = Field(description="Vector confidence threshold used")
    results: List[CompatibilityResult]
    total_found: int
    execution_time_ms: float
    target_product_context: Optional[str] = None

# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_simple_neo4j_agent(neo4j_repo=Depends(get_neo4j_repository)) -> SimpleNeo4jAgent:
    """Get SimpleNeo4jAgent instance"""
    return SimpleNeo4jAgent(neo4j_repo)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/compatibility-search", response_model=VectorCompatibilityResponse)
async def vector_compatibility_search(
    request: VectorCompatibilityRequest,
    agent: SimpleNeo4jAgent = Depends(get_simple_neo4j_agent)
):
    """
    Vector-first compatibility search with intelligent fallback.
    
    Examples:
    - "Find feeders compatible with Aristo 500 ix for aluminum marine work"
    - "What coolers work with MIG welding in outdoor conditions"  
    - "Portable accessories for heavy duty steel fabrication"
    """
    
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Vector compatibility search: '{request.query}'")
        
        # Perform vector compatibility search with fallback
        results, method_used = await agent.find_compatible_products_with_fallback(
            compatibility_query=request.query,
            target_product_id=request.target_product_id,
            category_filter=request.category_filter,
            limit=request.limit
        )
        
        # Get target product context for response
        target_context = None
        if request.target_product_id:
            target_product = await agent._get_product_context(request.target_product_id)
            if target_product:
                target_context = f"{target_product['name']} ({target_product['category']})"
        
        # Convert to response format
        compatibility_results = [
            CompatibilityResult(
                product_id=result.product_id,
                product_name=result.product_name,
                category=result.category,
                subcategory=result.subcategory,
                description=result.description,
                compatibility_score=result.compatibility_score,
                sales_frequency=result.sales_frequency or 0
            )
            for result in results
        ]
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        logger.info(f"Compatibility search complete: {len(results)} results using {method_used} in {execution_time:.1f}ms")
        
        return VectorCompatibilityResponse(
            query=request.query,
            method_used=method_used,
            confidence_threshold=settings.VECTOR_CONFIDENCE_THRESHOLD,
            results=compatibility_results,
            total_found=len(results),
            execution_time_ms=execution_time,
            target_product_context=target_context
        )
        
    except Exception as e:
        logger.error(f"Vector compatibility search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility search failed: {str(e)}")

@router.get("/compatibility-search/config")
async def get_compatibility_config():
    """Get current compatibility search configuration"""
    return {
        "vector_confidence_threshold": settings.VECTOR_CONFIDENCE_THRESHOLD,
        "vector_search_limit": settings.VECTOR_SEARCH_LIMIT,
        "enable_compatibility_fallback": settings.ENABLE_COMPATIBILITY_FALLBACK,
        "description": {
            "vector_confidence_threshold": "Minimum confidence score for vector results (0.0-1.0)",
            "vector_search_limit": "Maximum candidates to retrieve from vector search",
            "enable_compatibility_fallback": "Whether to use rules-based fallback when vector confidence is low"
        }
    }

@router.get("/compatibility-search/test-queries")
async def get_test_queries():
    """Get example compatibility queries for testing"""
    return {
        "simple_queries": [
            "Find MIG welders for aluminum",
            "Portable feeders for steel work",
            "Heavy duty coolers for industrial use",
            "TIG torches for stainless steel"
        ],
        "complex_queries": [
            "Find feeders compatible with Aristo 500 ix for aluminum marine work",
            "What coolers work with MIG welding in outdoor windy conditions",
            "Portable accessories for heavy duty steel fabrication in construction",
            "Find all products compatible with Warrior 400i that work with stainless steel in aerospace environment"
        ],
        "target_product_queries": [
            {
                "query": "compatible feeders for marine aluminum work",
                "target_product_id": "0094378274",  # Example Aristo product
                "description": "Find feeders specifically compatible with this power source"
            }
        ]
    }