"""
Step-by-Step Package Builder API Endpoints

Provides interactive package building with component selection based on:
1. Sales history frequency ranking
2. Golden package compatibility fallback
3. Conditional accessories based on selections
4. Visual tile-based product presentation
"""

import logging
import time
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...database.repositories import Neo4jRepository, get_neo4j_repository
from ...core.config import settings
from ...agents.agent_state import safe_enum_value

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class ComponentType(str, Enum):
    POWERSOURCE = "PowerSource"
    FEEDER = "Feeder"
    COOLER = "Cooler" 
    TORCH = "Torch"
    ACCESSORY = "Accessory"

class SalesFrequency(str, Enum):
    VERY_HIGH = "very_high"  # >100 sales
    HIGH = "high"            # 51-100 sales
    MEDIUM = "medium"        # 21-50 sales
    LOW = "low"              # 6-20 sales
    RARE = "rare"            # 1-5 sales
    UNKNOWN = "unknown"      # No sales data


# =============================================================================
# REQUEST MODELS
# =============================================================================

class StepByStepRequest(BaseModel):
    """Request for step-by-step package building"""
    process: List[str] = Field(..., description="Welding processes (MIG, TIG, MMA)")
    material: Optional[str] = Field(None, description="Base material")
    current: Optional[int] = Field(None, description="Required current in amps")
    voltage: Optional[int] = Field(None, description="Required voltage")
    thickness: Optional[float] = Field(None, description="Material thickness in mm")
    environment: Optional[str] = Field(None, description="Working environment")
    application: Optional[str] = Field(None, description="Specific application")

class ComponentSelectionRequest(BaseModel):
    """Request for next component selection based on previous choices"""
    selected_powersource_id: Optional[str] = None
    selected_feeder_id: Optional[str] = None
    selected_cooler_id: Optional[str] = None
    selected_torch_id: Optional[str] = None
    requirements: StepByStepRequest


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SalesMetrics(BaseModel):
    """Sales frequency and metrics for a product"""
    total_sales: int
    frequency_rank: SalesFrequency
    popularity_score: float = Field(ge=0, le=10)
    sales_period: str = "last_12_months"
    frequency_label: str
    
class ProductTile(BaseModel):
    """Product tile with sales frequency and visual info"""
    product_id: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    specifications: Optional[Dict[str, Any]] = None
    
    # Sales and ranking info
    sales_metrics: SalesMetrics
    
    # Compatibility info
    compatibility_score: float = Field(ge=0, le=1)
    compatibility_reason: str
    
    # Visual presentation
    image_url: Optional[str] = None
    featured: bool = False
    recommended: bool = False
    
    # Phase 1 integration
    package_context: Optional[Dict[str, Any]] = None
    
class ComponentOptionsResponse(BaseModel):
    """Response with component options as tiles"""
    step: int
    component_type: ComponentType
    title: str
    description: str
    total_options: int
    
    # Grouped by sales frequency
    very_high_frequency: List[ProductTile] = []
    high_frequency: List[ProductTile] = []
    medium_frequency: List[ProductTile] = []
    low_frequency: List[ProductTile] = []
    rare_frequency: List[ProductTile] = []
    unknown_frequency: List[ProductTile] = []
    
    # Context info
    requirements_summary: Dict[str, Any]
    selected_components: Dict[str, str] = {}  # component_type -> product_id
    
    # Phase 1 integration info
    phase1_integration: Optional[Dict[str, Any]] = None
    
class PackageBuildResponse(BaseModel):
    """Response for complete package build status"""
    package_id: str
    selected_components: Dict[str, ProductTile]
    total_price: Optional[float] = None
    compatibility_score: float
    recommended_accessories: List[ProductTile] = []
    conditional_accessories: List[ProductTile] = []  # Based on selections
    package_complete: bool


# =============================================================================
# STEP-BY-STEP ENDPOINTS
# =============================================================================

@router.post("/powersources", response_model=ComponentOptionsResponse)
async def get_powersource_options(
    request: StepByStepRequest,
    limit: int = Query(default=20, le=50, ge=5),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 1: Get PowerSource options with sales frequency tiles
    
    Returns PowerSources ordered by sales frequency, with golden package fallback
    """
    try:
        logger.info(f"Getting PowerSource options for: {request}")
        
        # Find compatible PowerSources with sales data
        powersources = await _get_compatible_powersources_with_sales(
            neo4j_repo, request, limit
        )
        
        # Convert to tiles with sales frequency
        tiles = []
        for ps in powersources:
            tile = await _create_product_tile(
                neo4j_repo, ps, ComponentType.POWERSOURCE, request
            )
            tiles.append(tile)
        
        # Group by sales frequency
        frequency_groups = _group_tiles_by_frequency(tiles)
        
        return ComponentOptionsResponse(
            step=1,
            component_type=ComponentType.POWERSOURCE,
            title="Choose Your PowerSource",
            description="Select a welding power source compatible with your requirements",
            total_options=len(tiles),
            **frequency_groups,
            requirements_summary=request.dict()
        )
        
    except Exception as e:
        logger.error(f"Error getting PowerSource options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feeders", response_model=ComponentOptionsResponse)  
async def get_feeder_options(
    request: ComponentSelectionRequest,
    limit: int = Query(default=15, le=30, ge=5),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 2: Get Feeder options compatible with selected PowerSource
    
    Ordered by:
    1. Sales history with selected PowerSource
    2. Golden package compatibility
    3. General compatibility
    """
    try:
        if not request.selected_powersource_id:
            raise HTTPException(
                status_code=400, 
                detail="PowerSource must be selected first"
            )
        
        # Find compatible feeders with sales preference
        feeders = await _get_compatible_feeders_with_sales(
            neo4j_repo, request.selected_powersource_id, request.requirements, limit
        )
        
        # Convert to tiles
        tiles = []
        for feeder in feeders:
            tile = await _create_product_tile(
                neo4j_repo, feeder, ComponentType.FEEDER, 
                request.requirements, request.selected_powersource_id
            )
            tiles.append(tile)
        
        # Group by frequency
        frequency_groups = _group_tiles_by_frequency(tiles)
        
        return ComponentOptionsResponse(
            step=2,
            component_type=ComponentType.FEEDER,
            title="Choose Your Wire Feeder",
            description="Select a wire feeder compatible with your PowerSource",
            total_options=len(tiles),
            **frequency_groups,
            requirements_summary=request.requirements.dict(),
            selected_components={"powersource": request.selected_powersource_id}
        )
        
    except Exception as e:
        logger.error(f"Error getting Feeder options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/coolers", response_model=ComponentOptionsResponse)
async def get_cooler_options(
    request: ComponentSelectionRequest,
    limit: int = Query(default=10, le=20, ge=5),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 3: Get Cooler options compatible with selected components
    """
    try:
        if not request.selected_powersource_id:
            raise HTTPException(
                status_code=400,
                detail="PowerSource must be selected first"
            )
        
        # Find compatible coolers
        coolers = await _get_compatible_coolers_with_sales(
            neo4j_repo, request.selected_powersource_id, 
            request.selected_feeder_id, request.requirements, limit
        )
        
        # Convert to tiles
        tiles = []
        for cooler in coolers:
            tile = await _create_product_tile(
                neo4j_repo, cooler, ComponentType.COOLER,
                request.requirements, request.selected_powersource_id
            )
            tiles.append(tile)
            
        frequency_groups = _group_tiles_by_frequency(tiles)
        
        selected_components = {"powersource": request.selected_powersource_id}
        if request.selected_feeder_id:
            selected_components["feeder"] = request.selected_feeder_id
        
        return ComponentOptionsResponse(
            step=3,
            component_type=ComponentType.COOLER,
            title="Choose Your Cooler (Optional)",
            description="Select a cooling system for high-duty cycle applications",
            total_options=len(tiles),
            **frequency_groups,
            requirements_summary=request.requirements.dict(),
            selected_components=selected_components
        )
        
    except Exception as e:
        logger.error(f"Error getting Cooler options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accessories", response_model=ComponentOptionsResponse)
async def get_accessory_options(
    request: ComponentSelectionRequest,
    limit: int = Query(default=25, le=50, ge=10),
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 4: Get Accessories with conditional logic based on selections
    
    Returns accessories grouped by:
    1. Essential (required for operation)
    2. Recommended (high sales frequency with this config)
    3. Optional (general accessories)
    """
    try:
        if not request.selected_powersource_id:
            raise HTTPException(
                status_code=400,
                detail="PowerSource must be selected first"
            )
        
        # Get conditional accessories based on selections
        accessories = await _get_conditional_accessories(
            neo4j_repo, request, limit
        )
        
        # Convert to tiles with conditional logic
        tiles = []
        for accessory in accessories:
            tile = await _create_accessory_tile(
                neo4j_repo, accessory, request
            )
            tiles.append(tile)
        
        frequency_groups = _group_tiles_by_frequency(tiles)
        
        selected_components = {"powersource": request.selected_powersource_id}
        if request.selected_feeder_id:
            selected_components["feeder"] = request.selected_feeder_id
        if request.selected_cooler_id:
            selected_components["cooler"] = request.selected_cooler_id
        
        return ComponentOptionsResponse(
            step=4,
            component_type=ComponentType.ACCESSORY,
            title="Add Accessories",
            description="Complete your package with essential and recommended accessories",
            total_options=len(tiles),
            **frequency_groups,
            requirements_summary=request.requirements.dict(),
            selected_components=selected_components
        )
        
    except Exception as e:
        logger.error(f"Error getting Accessory options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete", response_model=PackageBuildResponse)
async def complete_package_build(
    powersource_id: str,
    feeder_id: Optional[str] = None,
    cooler_id: Optional[str] = None,
    torch_id: Optional[str] = None,
    accessory_ids: List[str] = [],
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Complete package building and return final package summary
    """
    try:
        # Build final package with all selections
        package = await _build_final_package(
            neo4j_repo, powersource_id, feeder_id, cooler_id, torch_id, accessory_ids
        )
        
        return package
        
    except Exception as e:
        logger.error(f"Error completing package build: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrate-recommendations", response_model=ComponentOptionsResponse)
async def integrate_phase1_recommendations(
    request: StepByStepRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    PHASE 1 + PHASE 2 INTEGRATION ENDPOINT
    
    Integrates Phase 1 package recommendations with Phase 2 step-by-step builder.
    This endpoint provides the best of both worlds:
    - Phase 1: Complete package recommendations based on requirements
    - Phase 2: Step-by-step approach with sales frequency tiles
    
    Use this when Sparky AI determines the user wants to see complete packages
    but also allows step-by-step modification.
    """
    try:
        logger.info(f"Integrating Phase 1 recommendations with step-by-step builder: {request}")
        
        # Import Phase 1 models and service
        from .recommendations import (
            PackageRecommendationRequest, 
            get_package_recommendations
        )
        
        # Convert StepByStepRequest to PackageRecommendationRequest
        phase1_request = PackageRecommendationRequest(
            process=request.process,
            material=request.material,
            current=request.current,
            voltage=request.voltage,
            thickness=request.thickness,
            environment=request.environment,
            application=request.application
        )
        
        # Get Phase 1 complete package recommendations
        phase1_response = await get_package_recommendations(phase1_request, neo4j_repo)
        
        # Extract PowerSources from Phase 1 packages for step-by-step builder
        recommended_powersources = []
        for package in phase1_response.packages:
            powersource_data = {
                "product_id": package.powersource.product_id,
                "product_name": package.powersource.product_name,
                "category": package.powersource.category,
                "subcategory": package.powersource.subcategory,
                "description": package.powersource.description,
                "manufacturer": package.powersource.manufacturer,
                "price": package.powersource.price,
                "sales_count": int(package.popularity_score * 100),  # Convert popularity to sales count
                "package_context": {
                    "complete_package_id": package.package_id,
                    "total_price": package.total_price,
                    "compatibility_confidence": package.compatibility_confidence,
                    "recommendation_reason": package.recommendation_reason
                }
            }
            recommended_powersources.append(powersource_data)
        
        # Create enhanced tiles with Phase 1 package context
        enhanced_tiles = []
        for ps_data in recommended_powersources:
            tile = await _create_enhanced_powersource_tile_with_package_context(
                neo4j_repo, ps_data, request
            )
            enhanced_tiles.append(tile)
        
        # Group by frequency but prioritize Phase 1 recommendations
        frequency_groups = _group_tiles_by_frequency_with_phase1_priority(enhanced_tiles)
        
        return ComponentOptionsResponse(
            step=1,
            component_type=ComponentType.POWERSOURCE,
            title="Smart PowerSource Selection",
            description="PowerSources from complete packages (Phase 1) + step-by-step customization (Phase 2)",
            total_options=len(enhanced_tiles),
            **frequency_groups,
            requirements_summary=request.dict(),
            selected_components={},
            phase1_integration={
                "total_packages_found": phase1_response.total_found,
                "algorithm": phase1_response.algorithm,
                "response_time_ms": phase1_response.response_time_ms
            }
        )
        
    except Exception as e:
        logger.error(f"Error integrating Phase 1 recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _get_compatible_powersources_with_sales(
    neo4j_repo: Neo4jRepository,
    request: StepByStepRequest,
    limit: int
) -> List[Dict[str, Any]]:
    """Find compatible PowerSources with sales frequency data"""
    
    try:
        # Build compatibility query with sales data
        cypher_query = """
        MATCH (ps:Product {category: 'PowerSource'})
        OPTIONAL MATCH (ps)-[sold:SOLD_WITH]->(other)
        WITH ps, COUNT(sold) as sales_count
        WHERE 1=1
        """
        
        cypher_params = {}
        
        # Add compatibility filters
        if "MIG" in request.process:
            cypher_query += " AND (ps.description CONTAINS 'MIG' OR ps.description CONTAINS 'multi-process')"
        
        if request.current and request.current >= 250:
            cypher_query += " AND (ps.description CONTAINS '300' OR ps.description CONTAINS '400' OR ps.description CONTAINS '500')"
        
        cypher_query += """
        RETURN ps, sales_count
        ORDER BY sales_count DESC, ps.product_id
        LIMIT $limit
        """
        cypher_params["limit"] = limit
        
        result = await neo4j_repo.connection.execute_query(cypher_query, cypher_params)
        
        powersources = []
        for record in result:
            ps_data = dict(record["ps"])
            ps_data["sales_count"] = record["sales_count"]
            powersources.append(ps_data)
        
        logger.info(f"Found {len(powersources)} compatible PowerSources with sales data")
        return powersources
        
    except Exception as e:
        logger.error(f"Error getting PowerSources with sales: {e}")
        return []

async def _get_compatible_feeders_with_sales(
    neo4j_repo: Neo4jRepository,
    powersource_id: str,
    requirements: StepByStepRequest,
    limit: int
) -> List[Dict[str, Any]]:
    """Find compatible feeders ordered by sales frequency with the PowerSource"""
    
    try:
        cypher_query = """
        MATCH (ps:Product {product_id: $powersource_id})
        MATCH (f:Product {category: 'Feeder'})
        OPTIONAL MATCH (ps)-[:SOLD_WITH]-(f) 
        OPTIONAL MATCH (f)-[sold:SOLD_WITH]->(other)
        WITH f, COUNT(sold) as sales_count,
             CASE WHEN EXISTS((ps)-[:SOLD_WITH]-(f)) THEN 10 ELSE 0 END as compatibility_bonus
        RETURN f, sales_count, compatibility_bonus
        ORDER BY compatibility_bonus DESC, sales_count DESC
        LIMIT $limit
        """
        
        result = await neo4j_repo.connection.execute_query(
            cypher_query, 
            {"powersource_id": powersource_id, "limit": limit}
        )
        
        feeders = []
        for record in result:
            feeder_data = dict(record["f"])
            feeder_data["sales_count"] = record["sales_count"]
            feeder_data["compatibility_bonus"] = record["compatibility_bonus"]
            feeders.append(feeder_data)
        
        return feeders
        
    except Exception as e:
        logger.error(f"Error getting compatible feeders: {e}")
        return []

async def _get_compatible_coolers_with_sales(
    neo4j_repo: Neo4jRepository,
    powersource_id: str,
    feeder_id: Optional[str],
    requirements: StepByStepRequest,
    limit: int
) -> List[Dict[str, Any]]:
    """Find compatible coolers with sales frequency"""
    
    try:
        cypher_query = """
        MATCH (ps:Product {product_id: $powersource_id})
        MATCH (c:Product {category: 'Cooler'})
        OPTIONAL MATCH (ps)-[:SOLD_WITH]-(c)
        OPTIONAL MATCH (c)-[sold:SOLD_WITH]->(other)
        WITH c, COUNT(sold) as sales_count,
             CASE WHEN EXISTS((ps)-[:SOLD_WITH]-(c)) THEN 10 ELSE 0 END as compatibility_bonus
        """
        
        cypher_params = {"powersource_id": powersource_id, "limit": limit}
        
        # Add feeder compatibility if selected
        if feeder_id:
            cypher_query += """
            OPTIONAL MATCH (f:Product {product_id: $feeder_id})-[:SOLD_WITH]-(c)
            WITH c, sales_count, compatibility_bonus + 
                 CASE WHEN EXISTS((f)-[:SOLD_WITH]-(c)) THEN 5 ELSE 0 END as final_compatibility
            """
            cypher_params["feeder_id"] = feeder_id
        else:
            cypher_query += " WITH c, sales_count, compatibility_bonus as final_compatibility"
        
        cypher_query += """
        RETURN c, sales_count, final_compatibility
        ORDER BY final_compatibility DESC, sales_count DESC
        LIMIT $limit
        """
        
        result = await neo4j_repo.connection.execute_query(cypher_query, cypher_params)
        
        coolers = []
        for record in result:
            cooler_data = dict(record["c"])
            cooler_data["sales_count"] = record["sales_count"] 
            cooler_data["compatibility_score"] = record["final_compatibility"] / 15.0  # Normalize
            coolers.append(cooler_data)
        
        return coolers
        
    except Exception as e:
        logger.error(f"Error getting compatible coolers: {e}")
        return []

async def _get_conditional_accessories(
    neo4j_repo: Neo4jRepository,
    request: ComponentSelectionRequest,
    limit: int
) -> List[Dict[str, Any]]:
    """Get accessories with conditional logic based on selected components"""
    
    try:
        # Build complex conditional query
        cypher_query = """
        MATCH (ps:Product {product_id: $powersource_id})
        MATCH (acc:Product {category: 'Accessory'})
        """
        
        cypher_params = {
            "powersource_id": request.selected_powersource_id,
            "limit": limit
        }
        
        # Add conditional logic for different component combinations
        conditions = ["(ps)-[:SOLD_WITH]-(acc)"]  # Base: sold with powersource
        
        if request.selected_feeder_id:
            cypher_query += " MATCH (f:Product {product_id: $feeder_id})"
            cypher_params["feeder_id"] = request.selected_feeder_id
            conditions.append("(f)-[:SOLD_WITH]-(acc)")
        
        if request.selected_cooler_id:
            cypher_query += " MATCH (c:Product {product_id: $cooler_id})"
            cypher_params["cooler_id"] = request.selected_cooler_id
            conditions.append("(c)-[:SOLD_WITH]-(acc)")
        
        # Add process-specific accessories
        if "MIG" in request.requirements.process:
            conditions.append("acc.description CONTAINS 'MIG'")
            
        if "TIG" in request.requirements.process:
            conditions.append("acc.description CONTAINS 'TIG'")
        
        # Combine conditions
        cypher_query += f"""
        OPTIONAL MATCH (acc)-[sold:SOLD_WITH]->(other)
        WITH acc, COUNT(sold) as sales_count,
             CASE WHEN {' OR '.join([f'EXISTS({cond})' for cond in conditions])} THEN 1 ELSE 0 END as is_compatible
        WHERE is_compatible = 1
        RETURN acc, sales_count
        ORDER BY sales_count DESC
        LIMIT $limit
        """
        
        result = await neo4j_repo.connection.execute_query(cypher_query, cypher_params)
        
        accessories = []
        for record in result:
            acc_data = dict(record["acc"])
            acc_data["sales_count"] = record["sales_count"]
            accessories.append(acc_data)
        
        return accessories
        
    except Exception as e:
        logger.error(f"Error getting conditional accessories: {e}")
        return []

async def _create_product_tile(
    neo4j_repo: Neo4jRepository,
    product: Dict[str, Any],
    component_type: ComponentType,
    requirements: StepByStepRequest,
    powersource_id: Optional[str] = None
) -> ProductTile:
    """Create a product tile with sales frequency and compatibility info"""
    
    sales_count = product.get("sales_count", 0)
    compatibility_bonus = product.get("compatibility_bonus", 0)
    
    # Calculate sales frequency
    sales_metrics = _calculate_sales_frequency(sales_count)
    
    # Calculate compatibility score
    compatibility_score = min(1.0, (compatibility_bonus + 5) / 15.0)
    
    # Generate compatibility reason
    compatibility_reason = _generate_compatibility_reason(
        product, requirements, powersource_id, compatibility_bonus
    )
    
    return ProductTile(
        product_id=product.get("product_id", ""),
        product_name=product.get("name", ""),
        category=product.get("category", component_type.value),
        subcategory=product.get("subcategory"),
        manufacturer=product.get("manufacturer"),
        description=product.get("description"),
        price=product.get("price"),
        specifications=product.get("specifications"),
        sales_metrics=sales_metrics,
        compatibility_score=compatibility_score,
        compatibility_reason=compatibility_reason,
        recommended=(sales_count > 20 and compatibility_bonus > 0),
        featured=(sales_count > 50)
    )

async def _create_accessory_tile(
    neo4j_repo: Neo4jRepository,
    accessory: Dict[str, Any],
    request: ComponentSelectionRequest
) -> ProductTile:
    """Create accessory tile with conditional reasoning"""
    
    sales_count = accessory.get("sales_count", 0)
    sales_metrics = _calculate_sales_frequency(sales_count)
    
    # Determine if accessory is essential based on selections
    is_essential = _is_essential_accessory(accessory, request)
    
    compatibility_reason = f"Compatible with selected components"
    if is_essential:
        compatibility_reason = "Essential for your configuration"
    elif sales_count > 10:
        compatibility_reason = f"Popular choice ({sales_count} recent sales)"
    
    return ProductTile(
        product_id=accessory.get("product_id", ""),
        product_name=accessory.get("name", ""),
        category="Accessory",
        subcategory=accessory.get("subcategory"),
        manufacturer=accessory.get("manufacturer"), 
        description=accessory.get("description"),
        price=accessory.get("price"),
        sales_metrics=sales_metrics,
        compatibility_score=1.0 if is_essential else 0.8,
        compatibility_reason=compatibility_reason,
        recommended=is_essential or sales_count > 15,
        featured=is_essential
    )

def _calculate_sales_frequency(sales_count: int) -> SalesMetrics:
    """Calculate sales frequency metrics"""
    
    if sales_count > 100:
        freq_rank = SalesFrequency.VERY_HIGH
        freq_label = f"Very Popular ({sales_count} sales)"
        popularity = 10.0
    elif sales_count > 50:
        freq_rank = SalesFrequency.HIGH  
        freq_label = f"Popular ({sales_count} sales)"
        popularity = 8.0
    elif sales_count > 20:
        freq_rank = SalesFrequency.MEDIUM
        freq_label = f"Moderate ({sales_count} sales)"
        popularity = 6.0
    elif sales_count > 5:
        freq_rank = SalesFrequency.LOW
        freq_label = f"Occasional ({sales_count} sales)"
        popularity = 4.0
    elif sales_count > 0:
        freq_rank = SalesFrequency.RARE
        freq_label = f"Rare ({sales_count} sales)"
        popularity = 2.0
    else:
        freq_rank = SalesFrequency.UNKNOWN
        freq_label = "No sales data"
        popularity = 1.0
    
    return SalesMetrics(
        total_sales=sales_count,
        frequency_rank=freq_rank,
        popularity_score=popularity,
        frequency_label=freq_label
    )

def _group_tiles_by_frequency(tiles: List[ProductTile]) -> Dict[str, List[ProductTile]]:
    """Group product tiles by sales frequency"""
    
    groups = {
        "very_high_frequency": [],
        "high_frequency": [],
        "medium_frequency": [],
        "low_frequency": [],
        "rare_frequency": [],
        "unknown_frequency": []
    }
    
    for tile in tiles:
        freq = tile.sales_metrics.frequency_rank
        if freq == SalesFrequency.VERY_HIGH:
            groups["very_high_frequency"].append(tile)
        elif freq == SalesFrequency.HIGH:
            groups["high_frequency"].append(tile)
        elif freq == SalesFrequency.MEDIUM:
            groups["medium_frequency"].append(tile)
        elif freq == SalesFrequency.LOW:
            groups["low_frequency"].append(tile)
        elif freq == SalesFrequency.RARE:
            groups["rare_frequency"].append(tile)
        else:
            groups["unknown_frequency"].append(tile)
    
    return groups

def _generate_compatibility_reason(
    product: Dict[str, Any],
    requirements: StepByStepRequest,
    powersource_id: Optional[str],
    compatibility_bonus: int
) -> str:
    """Generate human-readable compatibility reasoning"""
    
    reasons = []
    
    if compatibility_bonus > 0:
        reasons.append("Previously sold together")
    
    if requirements.current and "300" in product.get("description", ""):
        reasons.append(f"Supports {requirements.current}A requirement")
    
    if "MIG" in requirements.process and "MIG" in product.get("description", ""):
        reasons.append("MIG process compatible")
        
    if not reasons:
        reasons.append("Compatible with your requirements")
    
    return "; ".join(reasons)

def _is_essential_accessory(
    accessory: Dict[str, Any],
    request: ComponentSelectionRequest
) -> bool:
    """Determine if accessory is essential based on component selections"""
    
    description = accessory.get("description", "").lower()
    
    # Essential for specific processes
    if "MIG" in request.requirements.process:
        if any(term in description for term in ["wire", "tip", "nozzle", "liner"]):
            return True
    
    if "TIG" in request.requirements.process:
        if any(term in description for term in ["tungsten", "cup", "collet", "lens"]):
            return True
    
    # Essential for specific materials
    # Fixed 2025-01-09: Use safe_enum_value to handle both enum objects and strings from enhanced orchestrator
    # OLD: if request.requirements.material == "aluminum":
    if safe_enum_value(request.requirements.material) == "aluminum":
        if "aluminum" in description:
            return True
    
    return False

async def _build_final_package(
    neo4j_repo: Neo4jRepository,
    powersource_id: str,
    feeder_id: Optional[str],
    cooler_id: Optional[str], 
    torch_id: Optional[str],
    accessory_ids: List[str]
) -> PackageBuildResponse:
    """Build final package response with all selected components"""
    
    try:
        selected_components = {}
        total_price = 0.0
        
        # Get PowerSource
        ps = await neo4j_repo.get_product_by_id(powersource_id)
        if ps:
            ps_tile = ProductTile(
                product_id=ps.get("product_id", ""),
                product_name=ps.get("name", ""),
                category="PowerSource",
                price=ps.get("price"),
                sales_metrics=_calculate_sales_frequency(0)  # Simplified
            )
            selected_components["powersource"] = ps_tile
            if ps.get("price"):
                total_price += ps.get("price")
        
        # Add other components similarly...
        # (Feeder, Cooler, Torch, Accessories)
        
        package_id = f"custom_{powersource_id}_{int(time.time())}"
        
        return PackageBuildResponse(
            package_id=package_id,
            selected_components=selected_components,
            total_price=total_price if total_price > 0 else None,
            compatibility_score=1.0,
            package_complete=bool(powersource_id),
            recommended_accessories=[],
            conditional_accessories=[]
        )
        
    except Exception as e:
        logger.error(f"Error building final package: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _create_enhanced_powersource_tile_with_package_context(
    neo4j_repo: Neo4jRepository,
    powersource_data: Dict[str, Any],
    request: StepByStepRequest
) -> ProductTile:
    """Create enhanced PowerSource tile with Phase 1 package context"""
    
    sales_count = powersource_data.get("sales_count", 0)
    sales_metrics = _calculate_sales_frequency(sales_count)
    frequency = sales_metrics.frequency_rank
    
    # Enhanced compatibility score with Phase 1 context
    package_context = powersource_data.get("package_context", {})
    base_compatibility = package_context.get("compatibility_confidence", 0.8)
    
    # Boost compatibility if from Phase 1 recommendation
    compatibility_score = min(base_compatibility + 0.1, 1.0)
    
    # Enhanced compatibility reason with package context
    compatibility_reason = f"From complete package recommendation: {package_context.get('recommendation_reason', 'Compatible with requirements')}"
    
    return ProductTile(
        product_id=powersource_data["product_id"],
        product_name=powersource_data["product_name"],
        category=powersource_data["category"],
        subcategory=powersource_data.get("subcategory"),
        description=powersource_data.get("description"),
        manufacturer=powersource_data.get("manufacturer"),
        price=powersource_data.get("price"),
        sales_metrics=sales_metrics,
        compatibility_score=compatibility_score,
        compatibility_reason=compatibility_reason,
        featured=frequency in [SalesFrequency.VERY_HIGH, SalesFrequency.HIGH],
        recommended=True,  # All Phase 1 items are recommended
        package_context=package_context  # Add package context to tile
    )

def _get_frequency_label(frequency: SalesFrequency) -> str:
    """Convert frequency enum to display label"""
    if frequency == SalesFrequency.VERY_HIGH:
        return "Very Popular"
    elif frequency == SalesFrequency.HIGH:
        return "Popular"
    elif frequency == SalesFrequency.MEDIUM:
        return "Moderate"
    elif frequency == SalesFrequency.LOW:
        return "Occasional"
    elif frequency == SalesFrequency.RARE:
        return "Rare"
    else:
        return "No sales data"

def _group_tiles_by_frequency_with_phase1_priority(tiles: List[ProductTile]) -> Dict[str, List[ProductTile]]:
    """Group tiles by frequency with Phase 1 recommendations prioritized"""
    
    # First separate Phase 1 vs regular tiles
    phase1_tiles = [t for t in tiles if hasattr(t, 'package_context') and t.package_context]
    regular_tiles = [t for t in tiles if not (hasattr(t, 'package_context') and t.package_context)]
    
    # Group by frequency
    groups = {
        "very_high_frequency": [],
        "high_frequency": [],
        "medium_frequency": [],
        "low_frequency": [],
        "rare_frequency": [],
        "unknown_frequency": []
    }
    
    # Process Phase 1 tiles first (priority)
    for tile in phase1_tiles:
        freq = tile.sales_metrics.frequency_rank
        if freq == SalesFrequency.VERY_HIGH:
            groups["very_high_frequency"].insert(0, tile)  # Insert at beginning
        elif freq == SalesFrequency.HIGH:
            groups["high_frequency"].insert(0, tile)
        elif freq == SalesFrequency.MEDIUM:
            groups["medium_frequency"].insert(0, tile)
        elif freq == SalesFrequency.LOW:
            groups["low_frequency"].insert(0, tile)
        elif freq == SalesFrequency.RARE:
            groups["rare_frequency"].insert(0, tile)
        else:
            groups["unknown_frequency"].insert(0, tile)
    
    # Then add regular tiles
    for tile in regular_tiles:
        freq = tile.sales_metrics.frequency_rank
        if freq == SalesFrequency.VERY_HIGH:
            groups["very_high_frequency"].append(tile)
        elif freq == SalesFrequency.HIGH:
            groups["high_frequency"].append(tile)
        elif freq == SalesFrequency.MEDIUM:
            groups["medium_frequency"].append(tile)
        elif freq == SalesFrequency.LOW:
            groups["low_frequency"].append(tile)
        elif freq == SalesFrequency.RARE:
            groups["rare_frequency"].append(tile)
        else:
            groups["unknown_frequency"].append(tile)
    
    return groups