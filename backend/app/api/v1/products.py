"""
Product endpoints for search, discovery, and product information.

Provides REST API endpoints for product catalog operations including
search, filtering, categorization, and detailed product information.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...database.repositories import Neo4jRepository, get_neo4j_repository
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ProductResponse(BaseModel):
    """Product response model."""
    product_id: str
    product_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[str] = None
    price: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    labels: List[str] = Field(default_factory=list)


class ProductListResponse(BaseModel):
    """Product list response with pagination."""
    products: List[ProductResponse]
    pagination: Dict[str, Any]
    filters_applied: Dict[str, Any]
    total_count: Optional[int] = None


class CategoryResponse(BaseModel):
    """Category response model."""
    categories: List[str]
    count: int


class ProductSearchResponse(BaseModel):
    """Product search response with relevance scoring."""
    products: List[ProductResponse]
    search_term: str
    pagination: Dict[str, Any]
    total_count: Optional[int] = None


# =============================================================================
# PRODUCT ENDPOINTS
# =============================================================================

@router.get("/", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by product category"),
    subcategory: Optional[str] = Query(None, description="Filter by product subcategory"),
    limit: int = Query(default=settings.ITEMS_PER_PAGE, le=settings.MAX_ITEMS_PER_PAGE, ge=1),
    offset: int = Query(default=0, ge=0),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get products with optional filtering and pagination.
    
    Args:
        category: Filter by product category
        subcategory: Filter by product subcategory  
        limit: Maximum number of products to return
        offset: Number of products to skip for pagination
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        List of products with pagination information
    """
    try:
        # Apply category filter if provided
        if category:
            products_data = await neo4j_repo.get_products_by_category(
                category=category,
                limit=limit,
                skip=offset
            )
            filters_applied = {"category": category}
        else:
            # Get all products (this would need to be implemented in repository)
            products_data = await neo4j_repo.search_products(
                search_term="",  # Empty search to get all
                limit=limit,
                skip=offset
            )
            filters_applied = {}
        
        # Convert to response models
        products = [
            ProductResponse(
                product_id=product.get("product_id", ""),
                product_name=product.get("product_name", ""),
                category=product.get("category"),
                subcategory=product.get("subcategory"),
                description=product.get("description"),
                specifications=product.get("specifications"),
                price=product.get("price"),
                manufacturer=product.get("manufacturer"),
                model=product.get("model"),
                labels=product.get("labels", [])
            )
            for product in products_data
        ]
        
        # Pagination info
        pagination = {
            "limit": limit,
            "offset": offset,
            "has_next": len(products) == limit,
            "has_previous": offset > 0,
            "next_offset": offset + limit if len(products) == limit else None,
            "previous_offset": max(0, offset - limit) if offset > 0 else None
        }
        
        return ProductListResponse(
            products=products,
            pagination=pagination,
            filters_applied=filters_applied,
            total_count=None  # Would need separate count query
        )
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve products: {str(e)}"
        )


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., description="Search query for products"),
    limit: int = Query(default=settings.ITEMS_PER_PAGE, le=settings.MAX_ITEMS_PER_PAGE, ge=1),
    offset: int = Query(default=0, ge=0),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Search products by name, description, or specifications.
    
    Args:
        q: Search query string
        limit: Maximum number of products to return
        offset: Number of products to skip for pagination
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        Search results with relevance scoring
    """
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query must be at least 2 characters long"
            )
        
        # Perform search
        products_data = await neo4j_repo.search_products(
            search_term=q.strip(),
            limit=limit,
            skip=offset
        )
        
        # Convert to response models
        products = [
            ProductResponse(
                product_id=product.get("product_id", ""),
                product_name=product.get("product_name", ""),
                category=product.get("category"),
                subcategory=product.get("subcategory"),
                description=product.get("description"),
                specifications=product.get("specifications"),
                price=product.get("price"),
                manufacturer=product.get("manufacturer"),
                model=product.get("model"),
                labels=product.get("labels", [])
            )
            for product in products_data
        ]
        
        # Pagination info
        pagination = {
            "limit": limit,
            "offset": offset,
            "has_next": len(products) == limit,
            "has_previous": offset > 0,
            "next_offset": offset + limit if len(products) == limit else None,
            "previous_offset": max(0, offset - limit) if offset > 0 else None
        }
        
        return ProductSearchResponse(
            products=products,
            search_term=q,
            pagination=pagination,
            total_count=None  # Would need separate count query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Product search failed: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get detailed product information by ID.
    
    Args:
        product_id: Unique product identifier
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        Detailed product information
    """
    try:
        product_data = await neo4j_repo.get_product_by_id(product_id)
        
        if not product_data:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_id}"
            )
        
        return ProductResponse(
            product_id=product_data.get("product_id", ""),
            product_name=product_data.get("product_name", ""),
            category=product_data.get("category"),
            subcategory=product_data.get("subcategory"),
            description=product_data.get("description"),
            specifications=product_data.get("specifications"),
            price=product_data.get("price"),
            manufacturer=product_data.get("manufacturer"),
            model=product_data.get("model"),
            labels=product_data.get("labels", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product: {str(e)}"
        )


@router.get("/categories/", response_model=CategoryResponse)
async def get_categories(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get all available product categories.
    
    Args:
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        List of all product categories
    """
    try:
        categories = await neo4j_repo.get_all_categories()
        
        return CategoryResponse(
            categories=categories,
            count=len(categories)
        )
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.get("/categories/{category}/subcategories", response_model=CategoryResponse)
async def get_subcategories(
    category: str,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get subcategories for a specific category.
    
    Args:
        category: Product category
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        List of subcategories for the specified category
    """
    try:
        subcategories = await neo4j_repo.get_all_subcategories(category=category)
        
        return CategoryResponse(
            categories=subcategories,
            count=len(subcategories)
        )
        
    except Exception as e:
        logger.error(f"Error getting subcategories for {category}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve subcategories: {str(e)}"
        )


@router.get("/{product_id}/relationships")
async def get_product_relationships(
    product_id: str,
    relationship_types: Optional[List[str]] = Query(None, description="Filter by relationship types"),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get relationships for a specific product.
    
    Args:
        product_id: Product identifier
        relationship_types: Optional filter for relationship types
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        Product relationships and connected nodes
    """
    try:
        # First check if product exists
        product = await neo4j_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_id}"
            )
        
        # Get relationships
        relationships = await neo4j_repo.get_product_relationships(
            product_id=product_id,
            relationship_types=relationship_types
        )
        
        return {
            "product_id": product_id,
            "product_name": product.get("product_name"),
            "relationships": relationships,
            "relationship_count": len(relationships),
            "filters_applied": {
                "relationship_types": relationship_types
            } if relationship_types else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting relationships for product {product_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product relationships: {str(e)}"
        )