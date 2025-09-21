"""
Package endpoints for equipment packages and bundles.

Provides REST API endpoints for package operations including
package discovery, contents, and package-based recommendations.
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...database.repositories import Neo4jRepository, get_neo4j_repository
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class PackageResponse(BaseModel):
    """Package response model."""
    package_id: str
    package_name: str
    description: Optional[str] = None
    application: Optional[str] = None
    industry: Optional[str] = None
    price_range: Optional[str] = None
    labels: List[str] = Field(default_factory=list)


class PackageProductResponse(BaseModel):
    """Package product relationship response."""
    product_id: str
    product_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    relationship_type: Optional[str] = None
    order: Optional[int] = None
    quantity: Optional[int] = None
    is_required: Optional[bool] = None


class PackageDetailResponse(BaseModel):
    """Detailed package response with products."""
    package: PackageResponse
    products: List[PackageProductResponse]
    product_count: int
    total_estimated_price: Optional[float] = None


class PackageListResponse(BaseModel):
    """Package list response with pagination."""
    packages: List[PackageResponse]
    pagination: Dict[str, Any]
    total_count: Optional[int] = None


# =============================================================================
# PACKAGE ENDPOINTS
# =============================================================================

@router.get("/", response_model=PackageListResponse)
async def get_packages(
    application: Optional[str] = Query(None, description="Filter by application type"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    limit: int = Query(default=settings.ITEMS_PER_PAGE, le=settings.MAX_ITEMS_PER_PAGE, ge=1),
    offset: int = Query(default=0, ge=0),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get equipment packages with optional filtering and pagination.
    
    Args:
        application: Filter by application type
        industry: Filter by industry
        limit: Maximum number of packages to return
        offset: Number of packages to skip for pagination
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        List of packages with pagination information
    """
    try:
        # Get packages (filtering would need to be implemented in repository)
        packages_data = await neo4j_repo.get_all_packages(
            limit=limit,
            skip=offset
        )
        
        # Convert to response models
        packages = [
            PackageResponse(
                package_id=package.get("package_id", ""),
                package_name=package.get("package_name", ""),
                description=package.get("description"),
                application=package.get("application"),
                industry=package.get("industry"),
                price_range=package.get("price_range"),
                labels=package.get("labels", [])
            )
            for package in packages_data
        ]
        
        # Apply client-side filtering (ideally this would be in the repository)
        if application:
            packages = [
                pkg for pkg in packages
                if pkg.application and application.lower() in pkg.application.lower()
            ]
        
        if industry:
            packages = [
                pkg for pkg in packages
                if pkg.industry and industry.lower() in pkg.industry.lower()
            ]
        
        # Pagination info
        pagination = {
            "limit": limit,
            "offset": offset,
            "has_next": len(packages) == limit,
            "has_previous": offset > 0,
            "next_offset": offset + limit if len(packages) == limit else None,
            "previous_offset": max(0, offset - limit) if offset > 0 else None
        }
        
        return PackageListResponse(
            packages=packages,
            pagination=pagination,
            total_count=None  # Would need separate count query
        )
        
    except Exception as e:
        logger.error(f"Error getting packages: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve packages: {str(e)}"
        )


@router.get("/{package_id}", response_model=PackageDetailResponse)
async def get_package(
    package_id: str,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get detailed package information including all products.
    
    Args:
        package_id: Unique package identifier
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        Detailed package information with products
    """
    try:
        # Get package basic info
        package_data = await neo4j_repo.get_package_by_id(package_id)
        
        if not package_data:
            raise HTTPException(
                status_code=404,
                detail=f"Package not found: {package_id}"
            )
        
        # Get package products
        package_products = await neo4j_repo.get_package_products(package_id)
        
        # Convert package to response model
        package = PackageResponse(
            package_id=package_data.get("package_id", ""),
            package_name=package_data.get("package_name", ""),
            description=package_data.get("description"),
            application=package_data.get("application"),
            industry=package_data.get("industry"),
            price_range=package_data.get("price_range"),
            labels=package_data.get("labels", [])
        )
        
        # Convert products to response models
        products = []
        total_price = 0.0
        
        for item in package_products:
            product = item["product"]
            relationship = item["relationship"]
            
            product_response = PackageProductResponse(
                product_id=product.get("product_id", ""),
                product_name=product.get("product_name", ""),
                category=product.get("category"),
                subcategory=product.get("subcategory"),
                relationship_type=relationship.get("type"),
                order=relationship.get("order"),
                quantity=relationship.get("quantity", 1),
                is_required=relationship.get("is_required", True)
            )
            
            products.append(product_response)
            
            # Calculate estimated price if available
            if product.get("price") and relationship.get("quantity"):
                total_price += product["price"] * relationship.get("quantity", 1)
        
        return PackageDetailResponse(
            package=package,
            products=products,
            product_count=len(products),
            total_estimated_price=total_price if total_price > 0 else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting package {package_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve package: {str(e)}"
        )


@router.get("/{package_id}/products", response_model=List[PackageProductResponse])
async def get_package_products(
    package_id: str,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get all products in a specific package.
    
    Args:
        package_id: Package identifier
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        List of products in the package with relationship details
    """
    try:
        # First check if package exists
        package = await neo4j_repo.get_package_by_id(package_id)
        if not package:
            raise HTTPException(
                status_code=404,
                detail=f"Package not found: {package_id}"
            )
        
        # Get package products
        package_products = await neo4j_repo.get_package_products(package_id)
        
        # Convert to response models
        products = []
        for item in package_products:
            product = item["product"]
            relationship = item["relationship"]
            
            product_response = PackageProductResponse(
                product_id=product.get("product_id", ""),
                product_name=product.get("product_name", ""),
                category=product.get("category"),
                subcategory=product.get("subcategory"),
                relationship_type=relationship.get("type"),
                order=relationship.get("order"),
                quantity=relationship.get("quantity", 1),
                is_required=relationship.get("is_required", True)
            )
            
            products.append(product_response)
        
        return products
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting products for package {package_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve package products: {str(e)}"
        )


@router.get("/{package_id}/similar")
async def get_similar_packages(
    package_id: str,
    limit: int = Query(default=5, le=20, ge=1),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Get packages similar to the specified package.
    
    Args:
        package_id: Package identifier
        limit: Maximum number of similar packages to return
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        List of similar packages with similarity scoring
    """
    try:
        # First check if package exists
        package = await neo4j_repo.get_package_by_id(package_id)
        if not package:
            raise HTTPException(
                status_code=404,
                detail=f"Package not found: {package_id}"
            )
        
        # This would require implementing similar package logic in repository
        # For now, return a placeholder response
        return {
            "package_id": package_id,
            "package_name": package.get("package_name"),
            "similar_packages": [],
            "message": "Similar package detection not yet implemented",
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar packages for {package_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve similar packages: {str(e)}"
        )


@router.get("/search/{application}")
async def search_packages_by_application(
    application: str,
    limit: int = Query(default=settings.ITEMS_PER_PAGE, le=settings.MAX_ITEMS_PER_PAGE, ge=1),
    offset: int = Query(default=0, ge=0),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Search packages by application type.
    
    Args:
        application: Application type to search for
        limit: Maximum number of packages to return
        offset: Number of packages to skip for pagination
        neo4j_repo: Neo4j repository dependency
        
    Returns:
        Packages matching the application type
    """
    try:
        if not application or len(application.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Application query must be at least 2 characters long"
            )
        
        # Get all packages and filter (ideally this would be done in repository)
        all_packages = await neo4j_repo.get_all_packages(
            limit=100,  # Get more to filter
            skip=0
        )
        
        # Filter packages by application
        matching_packages = [
            package for package in all_packages
            if (package.get("application") and 
                application.lower() in package.get("application", "").lower()) or
               (package.get("description") and 
                application.lower() in package.get("description", "").lower())
        ]
        
        # Apply pagination to filtered results
        paginated_packages = matching_packages[offset:offset + limit]
        
        # Convert to response models
        packages = [
            PackageResponse(
                package_id=package.get("package_id", ""),
                package_name=package.get("package_name", ""),
                description=package.get("description"),
                application=package.get("application"),
                industry=package.get("industry"),
                price_range=package.get("price_range"),
                labels=package.get("labels", [])
            )
            for package in paginated_packages
        ]
        
        # Pagination info
        pagination = {
            "limit": limit,
            "offset": offset,
            "has_next": len(matching_packages) > offset + limit,
            "has_previous": offset > 0,
            "next_offset": offset + limit if len(matching_packages) > offset + limit else None,
            "previous_offset": max(0, offset - limit) if offset > 0 else None
        }
        
        return {
            "packages": packages,
            "search_term": application,
            "pagination": pagination,
            "total_matches": len(matching_packages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching packages by application {application}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Package search failed: {str(e)}"
        )