"""
Sales Frequency-Based Guided Flow API Endpoints

Interactive step-by-step package building using enterprise smart Neo4j system
with sales frequency ranking for optimal recommendations.

Flow:
1. PowerSource selection (sales frequency ranked)
2. Top 3 Feeders (compatible + sales frequency)
3. Top 3 Coolers (compatible + sales frequency)
4. Additional products (semantic search + sales frequency)
5. Complete package (expert mode logic)
"""

import logging
import time
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....database.repositories import Neo4jRepository, get_neo4j_repository
from ....services.enterprise.smart_neo4j_service import SmartNeo4jService, get_smart_neo4j_service
from ....services.enterprise.enterprise_orchestrator_service import EnterpriseOrchestratorService, get_enterprise_orchestrator_service
from ....services.enterprise.intelligent_intent_service import get_intelligent_intent_service
from ....core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class GuidedStepRequest(BaseModel):
    """Base request for guided flow steps"""
    query: str = Field(..., description="Original user query for context")
    user_context: Dict[str, Any] = Field(default={}, description="User context")
    session_id: str = Field(..., description="Session ID for state management")
    language: str = Field(default="en", description="Response language")

class ComponentSelectionRequest(GuidedStepRequest):
    """Request with component selections"""
    selected_powersource_id: Optional[str] = None
    selected_feeder_id: Optional[str] = None  
    selected_cooler_id: Optional[str] = None
    additional_products: List[str] = Field(default=[], description="Additional selected product IDs")

class SemanticSearchRequest(GuidedStepRequest):
    """Request for semantic product search"""
    search_query: str = Field(..., description="Product search query")
    selected_powersource_id: Optional[str] = None
    selected_feeder_id: Optional[str] = None
    selected_cooler_id: Optional[str] = None

class SalesRankedProduct(BaseModel):
    """Product with sales frequency ranking"""
    product_id: str
    product_name: str
    category: str
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    sales_frequency: int = Field(description="Total sales count")
    popularity_rank: int = Field(description="Rank based on sales (1=most popular)")
    compatibility_score: float = Field(ge=0, le=1)
    compatibility_reason: str
    price: Optional[float] = None
    image_url: Optional[str] = None

class GuidedStepResponse(BaseModel):
    """Response for guided flow steps"""
    step: int = Field(description="Current step number")
    step_name: str = Field(description="Step description")
    title: str = Field(description="UI title")
    description: str = Field(description="Step explanation")
    products: List[SalesRankedProduct] = Field(description="Recommended products")
    total_options: int = Field(description="Total products available")
    session_state: Dict[str, Any] = Field(description="Current selections")
    next_step_available: bool = Field(description="Can proceed to next step")
    completion_ready: bool = Field(description="Ready for package completion")

class GuidedPackageResponse(BaseModel):
    """Final package response using expert mode logic"""
    package: Dict[str, Any] = Field(description="Complete package with 7 categories")
    formation_method: str = Field(description="Package formation method used")
    sales_evidence: str = Field(description="Sales history analysis")
    total_price: float = Field(description="Total package price")
    confidence: float = Field(description="Package confidence score")
    golden_package_used: bool = Field(description="Whether golden package fallback was used")


# =============================================================================
# SALES FREQUENCY UTILITIES - Now handled by SmartNeo4jService
# =============================================================================


# =============================================================================
# GUIDED FLOW ENDPOINTS
# =============================================================================

@router.post("/powersources", response_model=GuidedStepResponse)
async def get_guided_powersources(
    request: GuidedStepRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 1: Get PowerSources ranked by sales frequency using Enterprise Orchestrator with LangSmith
    """
    try:
        logger.info(f"Guided Step 1: PowerSource selection for session {request.session_id}")
        
        # Create user context for enterprise orchestrator
        from ....services.enterprise import UserContext
        user_context = UserContext(
            user_id=request.user_context.get("user_id", "guided_user"),
            session_id=request.session_id,
            preferred_language=request.language,
            expertise_history=[],
            previous_queries=[],
            industry_context=request.user_context.get("industry_context"),
            organization=request.user_context.get("organization"),
            role="guided_mode_user",
            permissions=[]
        )
        
        # Use enterprise orchestrator for full LangSmith observability
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        # Craft specific query for PowerSource selection with sales ranking
        powersource_query = f"""
        I need to see all available PowerSources ranked by sales frequency for guided selection.
        Show me the top 6 PowerSources with their specifications and sales data.
        This is step 1 of guided flow for session {request.session_id}.
        """
        
        # Process through enterprise orchestrator (gets LangSmith tracing)
        enterprise_response = await orchestrator.process_recommendation_request(
            query=powersource_query,
            user_context=user_context,
            session_id=request.session_id
        )
        
        # Extract PowerSources from enterprise response and convert to sales ranked format
        sales_ranked_products = []
        if enterprise_response.packages:
            for rank, package in enumerate(enterprise_response.packages[:6], 1):
                if package.power_source:
                    product = SalesRankedProduct(
                        product_id=package.power_source.get("product_id", ""),
                        product_name=package.power_source.get("product_name", "Unknown Product"),
                        category="PowerSource",
                        description=package.power_source.get("description", "No description available"),
                        specifications=package.power_source.get("specifications", {}),
                        sales_frequency=package.power_source.get("sales_frequency", 0),
                        popularity_rank=rank,
                        compatibility_score=1.0,
                        compatibility_reason="High sales frequency",
                        price=package.power_source.get("price"),
                        image_url=package.power_source.get("image_url")
                    )
                    sales_ranked_products.append(product)
        
        return GuidedStepResponse(
            step=1,
            step_name="powersource_selection",
            title="Choose Your PowerSource",
            description="Select a welding power source. These are ranked by popularity based on sales data.",
            products=sales_ranked_products,
            total_options=len(sales_ranked_products),
            session_state={},
            next_step_available=False,
            completion_ready=False
        )
        
    except Exception as e:
        logger.error(f"Error in guided PowerSource selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feeders", response_model=GuidedStepResponse)
async def get_guided_feeders(
    request: ComponentSelectionRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 2: Get top 3 Feeders compatible with selected PowerSource using Enterprise Orchestrator with LangSmith
    """
    try:
        if not request.selected_powersource_id:
            raise HTTPException(status_code=400, detail="PowerSource must be selected first")
        
        logger.info(f"Guided Step 2: Feeder selection for PowerSource {request.selected_powersource_id}")
        
        # Create user context for enterprise orchestrator
        from ....services.enterprise import UserContext
        user_context = UserContext(
            user_id=request.user_context.get("user_id", "guided_user"),
            session_id=request.session_id,
            preferred_language=request.language,
            expertise_history=[],
            previous_queries=[f"Selected PowerSource: {request.selected_powersource_id}"],
            industry_context=request.user_context.get("industry_context"),
            organization=request.user_context.get("organization"),
            role="guided_mode_user",
            permissions=[]
        )
        
        # Use enterprise orchestrator for full LangSmith observability
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        # Craft specific query for Feeder selection with compatibility and sales ranking
        feeder_query = f"""
        I need the top 3 Feeders that are compatible with PowerSource {request.selected_powersource_id}.
        Show me feeders ranked by sales frequency that work with this specific power source.
        This is step 2 of guided flow for session {request.session_id}.
        """
        
        # Process through enterprise orchestrator (gets LangSmith tracing)
        enterprise_response = await orchestrator.process_recommendation_request(
            query=feeder_query,
            user_context=user_context,
            session_id=request.session_id
        )
        
        # Extract Feeders from enterprise response and convert to sales ranked format
        sales_ranked_products = []
        if enterprise_response.packages:
            for rank, package in enumerate(enterprise_response.packages[:3], 1):
                if package.feeder:
                    product = SalesRankedProduct(
                        product_id=package.feeder.get("product_id", ""),
                        product_name=package.feeder.get("product_name", "Unknown Product"),
                        category="Feeder",
                        description=package.feeder.get("description", "No description available"),
                        specifications=package.feeder.get("specifications", {}),
                        sales_frequency=package.feeder.get("sales_frequency", 0),
                        popularity_rank=rank,
                        compatibility_score=0.9,
                        compatibility_reason="High sales frequency and compatibility",
                        price=package.feeder.get("price"),
                        image_url=package.feeder.get("image_url")
                    )
                    sales_ranked_products.append(product)
        
        return GuidedStepResponse(
            step=2,
            step_name="feeder_selection", 
            title="Choose Your Wire Feeder",
            description=f"Top 3 feeders compatible with your PowerSource, ranked by sales popularity.",
            products=sales_ranked_products,
            total_options=len(sales_ranked_products),
            session_state={"selected_powersource_id": request.selected_powersource_id},
            next_step_available=False,
            completion_ready=False
        )
        
    except Exception as e:
        logger.error(f"Error in guided Feeder selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coolers", response_model=GuidedStepResponse)
async def get_guided_coolers(
    request: ComponentSelectionRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 3: Get top 3 Coolers compatible with selected PowerSource and Feeder using Enterprise Orchestrator with LangSmith
    """
    try:
        if not request.selected_powersource_id or not request.selected_feeder_id:
            raise HTTPException(status_code=400, detail="PowerSource and Feeder must be selected first")
        
        logger.info(f"Guided Step 3: Cooler selection for Trinity completion")
        
        # Create user context for enterprise orchestrator
        from ....services.enterprise import UserContext
        user_context = UserContext(
            user_id=request.user_context.get("user_id", "guided_user"),
            session_id=request.session_id,
            preferred_language=request.language,
            expertise_history=[],
            previous_queries=[
                f"Selected PowerSource: {request.selected_powersource_id}",
                f"Selected Feeder: {request.selected_feeder_id}"
            ],
            industry_context=request.user_context.get("industry_context"),
            organization=request.user_context.get("organization"),
            role="guided_mode_user",
            permissions=[]
        )
        
        # Use enterprise orchestrator for full LangSmith observability
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        # Craft specific query for Cooler selection with compatibility and sales ranking
        cooler_query = f"""
        I need the top 3 Coolers that are compatible with both PowerSource {request.selected_powersource_id} 
        and Feeder {request.selected_feeder_id}. Show me coolers ranked by sales frequency that work 
        with this specific Trinity combination. This completes the Trinity package.
        This is step 3 of guided flow for session {request.session_id}.
        """
        
        # Process through enterprise orchestrator (gets LangSmith tracing)
        enterprise_response = await orchestrator.process_recommendation_request(
            query=cooler_query,
            user_context=user_context,
            session_id=request.session_id
        )
        
        # Extract Coolers from enterprise response and convert to sales ranked format
        sales_ranked_products = []
        if enterprise_response.packages:
            for rank, package in enumerate(enterprise_response.packages[:3], 1):
                if package.cooler:
                    product = SalesRankedProduct(
                        product_id=package.cooler.get("product_id", ""),
                        product_name=package.cooler.get("product_name", "Unknown Product"),
                        category="Cooler",
                        description=package.cooler.get("description", "No description available"),
                        specifications=package.cooler.get("specifications", {}),
                        sales_frequency=package.cooler.get("sales_frequency", 0),
                        popularity_rank=rank,
                        compatibility_score=0.9,
                        compatibility_reason="High sales frequency and Trinity compatibility",
                        price=package.cooler.get("price"),
                        image_url=package.cooler.get("image_url")
                    )
                    sales_ranked_products.append(product)
        
        return GuidedStepResponse(
            step=3,
            step_name="cooler_selection",
            title="Choose Your Cooling System",
            description="Top 3 coolers compatible with your selections, ranked by sales popularity. This completes your Trinity package.",
            products=sales_ranked_products,
            total_options=len(sales_ranked_products),
            session_state={
                "selected_powersource_id": request.selected_powersource_id,
                "selected_feeder_id": request.selected_feeder_id
            },
            next_step_available=True,
            completion_ready=True
        )
        
    except Exception as e:
        logger.error(f"Error in guided Cooler selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-accessories", response_model=GuidedStepResponse)
async def search_guided_accessories(
    request: SemanticSearchRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 4: Semantic search for additional products using Enterprise Orchestrator with LangSmith
    """
    try:
        if not request.selected_powersource_id or not request.selected_feeder_id or not request.selected_cooler_id:
            raise HTTPException(status_code=400, detail="Trinity must be completed first")
        
        logger.info(f"Guided Step 4: Accessory search for '{request.search_query}'")
        
        # Create user context for enterprise orchestrator
        from ....services.enterprise import UserContext
        user_context = UserContext(
            user_id=request.user_context.get("user_id", "guided_user"),
            session_id=request.session_id,
            preferred_language=request.language,
            expertise_history=[],
            previous_queries=[
                f"Selected PowerSource: {request.selected_powersource_id}",
                f"Selected Feeder: {request.selected_feeder_id}",
                f"Selected Cooler: {request.selected_cooler_id}"
            ],
            industry_context=request.user_context.get("industry_context"),
            organization=request.user_context.get("organization"),
            role="guided_mode_user",
            permissions=[]
        )
        
        # Use enterprise orchestrator for full LangSmith observability
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        # Craft specific query for accessory/product search with semantic matching
        accessory_query = f"""
        I have completed my Trinity selection: PowerSource {request.selected_powersource_id}, 
        Feeder {request.selected_feeder_id}, and Cooler {request.selected_cooler_id}.
        
        Now I need to search for: {request.search_query}
        
        Show me the top 3 products that match this search query, ranked by sales frequency.
        This is step 4 of guided flow for session {request.session_id}.
        """
        
        # Process through enterprise orchestrator (gets LangSmith tracing)
        enterprise_response = await orchestrator.process_recommendation_request(
            query=accessory_query,
            user_context=user_context,
            session_id=request.session_id
        )
        
        # Extract products from enterprise response and convert to sales ranked format
        sales_ranked_accessories = []
        if enterprise_response.packages:
            # Look through all packages for any additional products/accessories
            rank = 1
            for package in enterprise_response.packages[:3]:
                # Check consumables and accessories
                for consumable in (package.consumables or []):
                    if len(sales_ranked_accessories) < 3:
                        product = SalesRankedProduct(
                            product_id=consumable.get("product_id", ""),
                            product_name=consumable.get("product_name", "Unknown Product"),
                            category=consumable.get("category", "Consumable"),
                            description=consumable.get("description", "No description available"),
                            specifications=consumable.get("specifications", {}),
                            sales_frequency=consumable.get("sales_frequency", 0),
                            popularity_rank=rank,
                            compatibility_score=0.8,
                            compatibility_reason="Semantic match with sales data",
                            price=consumable.get("price"),
                            image_url=consumable.get("image_url")
                        )
                        sales_ranked_accessories.append(product)
                        rank += 1
                
                for accessory in (package.accessories or []):
                    if len(sales_ranked_accessories) < 3:
                        product = SalesRankedProduct(
                            product_id=accessory.get("product_id", ""),
                            product_name=accessory.get("product_name", "Unknown Product"),
                            category=accessory.get("category", "Accessory"),
                            description=accessory.get("description", "No description available"),
                            specifications=accessory.get("specifications", {}),
                            sales_frequency=accessory.get("sales_frequency", 0),
                            popularity_rank=rank,
                            compatibility_score=0.8,
                            compatibility_reason="Semantic match with sales data",
                            price=accessory.get("price"),
                            image_url=accessory.get("image_url")
                        )
                        sales_ranked_accessories.append(product)
                        rank += 1
        
        return GuidedStepResponse(
            step=4,
            step_name="accessory_search",
            title="Additional Products Found",
            description=f"Products matching '{request.search_query}' ranked by sales popularity.",
            products=sales_ranked_accessories,
            total_options=len(sales_ranked_accessories),
            session_state={
                "selected_powersource_id": request.selected_powersource_id,
                "selected_feeder_id": request.selected_feeder_id,
                "selected_cooler_id": request.selected_cooler_id
            },
            next_step_available=True,
            completion_ready=True
        )
        
    except Exception as e:
        logger.error(f"Error in guided accessory search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete", response_model=GuidedPackageResponse)
async def complete_guided_package(
    request: ComponentSelectionRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
):
    """
    Step 5: Complete package using enterprise orchestrator for full 3-agent workflow with LangSmith
    """
    try:
        if not request.selected_powersource_id or not request.selected_feeder_id or not request.selected_cooler_id:
            raise HTTPException(status_code=400, detail="Trinity components must be selected")
        
        logger.info(f"Guided Step 5: Package completion using enterprise orchestrator")
        
        # Construct query with user selections for enterprise orchestrator
        guided_query = f"""
        I need a complete welding package with PowerSource {request.selected_powersource_id}, 
        Feeder {request.selected_feeder_id}, and Cooler {request.selected_cooler_id}.
        """
        
        # Add additional products if selected
        if request.additional_products:
            additional_list = ", ".join(request.additional_products)
            guided_query += f" Also include these additional products: {additional_list}."
        
        guided_query += " Please provide a complete 7-category package with sales analysis and golden package fallback."
        
        # Use the EXISTING enterprise orchestrator - gets all benefits!
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        enterprise_response = await orchestrator.process_recommendation_request(
            query=guided_query,
            user_context=request.user_context,
            session_id=request.session_id
        )
        
        # Extract the best package from enterprise response
        if not enterprise_response.packages or len(enterprise_response.packages) == 0:
            raise HTTPException(status_code=500, detail="No packages generated by enterprise orchestrator")
        
        best_package = enterprise_response.packages[0]
        
        # Transform enterprise response to guided package response format
        package_data = {
            "package_id": f"guided_enterprise_{request.session_id}",
            "components": {},
            "total_price": best_package.total_price or 0.0,
            "formation_method": "Enterprise 3-Agent Workflow with Sales Analysis",
            "trinity_compliance": best_package.trinity_compliance
        }
        
        # Map Trinity components and additional components
        if best_package.power_source:
            package_data["components"]["PowerSource"] = best_package.power_source
        if best_package.feeder:
            package_data["components"]["Feeder"] = best_package.feeder  
        if best_package.cooler:
            package_data["components"]["Cooler"] = best_package.cooler
            
        # Add consumables and accessories
        for i, consumable in enumerate(best_package.consumables or []):
            package_data["components"][f"Consumable_{i+1}"] = consumable
        for i, accessory in enumerate(best_package.accessories or []):
            package_data["components"][f"Accessory_{i+1}"] = accessory
        
        return GuidedPackageResponse(
            package=package_data,
            formation_method="Enterprise 3-Agent Workflow (Agent 1: Intent + Agent 2: Neo4j + Agent 3: Response)",
            sales_evidence="Sales history analysis and compatibility verification completed by enterprise system",
            total_price=package_data["total_price"],
            confidence=best_package.package_score or 0.9,
            golden_package_used=getattr(best_package, "golden_package_used", False)
        )
        
    except Exception as e:
        logger.error(f"Error in guided package completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=Dict[str, Any])
async def get_guided_session_state(
    session_id: str
):
    """Get current state of guided flow session"""
    # In a real implementation, this would retrieve session state from database/cache
    # For now, return empty state
    return {
        "session_id": session_id,
        "current_step": 1,
        "selections": {},
        "completion_ready": False
    }