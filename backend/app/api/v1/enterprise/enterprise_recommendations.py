"""
Enterprise Recommendation API Endpoints
Main API for the 3-agent enterprise agentic system
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import uuid

from ....services.enterprise import (
    EnterpriseOrchestratorService,
    get_enterprise_orchestrator_service,
    UserContext,
    EnterpriseRecommendationResponse
)
from ....database.repositories import Neo4jRepository, get_neo4j_repository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Enterprise Recommendations"])


# Request/Response Models
class EnterpriseRecommendationRequest(BaseModel):
    """Enterprise recommendation request model"""
    
    query: str = Field(..., min_length=5, max_length=2000, description="Natural language welding query")
    session_id: Optional[str] = Field(None, description="Session identifier for tracking")
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User context information")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    include_explanations: bool = Field(default=True, description="Include detailed explanations")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "I need a welding setup for aluminum car parts",
                    "session_id": "test_session_001",
                    "user_context": {
                        "user_id": "test_user",
                        "preferred_language": "en",
                        "organization": "AutoParts Inc",
                        "industry_context": "automotive"
                    },
                    "max_results": 5,
                    "include_explanations": True
                },
                {
                    "query": "PowerWave 450 compatible feeder and cooler",
                    "session_id": "expert_session_002", 
                    "user_context": {
                        "user_id": "expert_user",
                        "preferred_language": "en",
                        "expertise_history": ["GTAW", "GMAW", "amperage control"]
                    },
                    "max_results": 10,
                    "include_explanations": True
                },
                {
                    "query": "Necesito una soldadora para acero inoxidable",
                    "session_id": "spanish_session_003",
                    "user_context": {
                        "user_id": "spanish_user", 
                        "preferred_language": "es",
                        "organization": "Fabricación Mexicana"
                    },
                    "max_results": 8,
                    "include_explanations": True
                }
            ]
        }


class EnterpriseHealthResponse(BaseModel):
    """Enterprise system health response"""
    
    status: str = Field(..., description="Overall system status")
    agents_status: Dict[str, str] = Field(..., description="Individual agent health")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    quality_metrics: Dict[str, Any] = Field(..., description="Quality metrics")
    neo4j_status: str = Field(..., description="Neo4j database status")
    timestamp: str = Field(..., description="Health check timestamp")


class EnterpriseMetricsResponse(BaseModel):
    """Enterprise metrics response"""
    
    recommendation_metrics: Dict[str, Any] = Field(..., description="Recommendation performance")
    agent_metrics: Dict[str, Any] = Field(..., description="Individual agent metrics")
    quality_metrics: Dict[str, Any] = Field(..., description="Quality and confidence metrics")
    business_metrics: Dict[str, Any] = Field(..., description="Business-relevant metrics")


# API Endpoints
@router.post("/recommendations", response_model=EnterpriseRecommendationResponse)
async def enterprise_recommendations(
    request: EnterpriseRecommendationRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> EnterpriseRecommendationResponse:
    """
    Enterprise-grade natural language recommendations
    Uses 3-agent architecture with automatic mode detection and multilingual support
    """
    
    try:
        logger.info(f"Enterprise recommendation request: {request.query[:100]}...")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create user context
        user_context = UserContext(
            user_id=request.user_context.get("user_id", "anonymous"),
            session_id=session_id,
            preferred_language=request.user_context.get("preferred_language", "en"),
            expertise_history=request.user_context.get("expertise_history", []),
            previous_queries=request.user_context.get("previous_queries", []),
            industry_context=request.user_context.get("industry_context"),
            organization=request.user_context.get("organization"),
            role=request.user_context.get("role"),
            permissions=request.user_context.get("permissions", [])
        )
        
        # Create enterprise orchestrator
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        # Process through enterprise orchestrator
        response = await orchestrator.process_recommendation_request(
            query=request.query,
            user_context=user_context,
            session_id=session_id
        )
        
        # Limit results if requested
        if len(response.packages) > request.max_results:
            response.packages = response.packages[:request.max_results]
            response.total_found = len(response.packages)
        
        # Remove explanations if not requested
        if not request.include_explanations:
            response.explanations = {}
            response.formatted_response.detailed_explanation = ""
            response.formatted_response.technical_notes = []
        
        logger.info(f"Enterprise recommendation completed: {len(response.packages)} packages, confidence: {response.overall_confidence:.2f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Enterprise recommendation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate enterprise recommendations: {str(e)}"
        )


@router.get("/health", response_model=EnterpriseHealthResponse)
async def enterprise_health(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> EnterpriseHealthResponse:
    """Comprehensive system health for enterprise monitoring"""
    
    try:
        # Create enterprise orchestrator
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        # Check observability metrics
        observability = orchestrator.observability
        system_health = observability.get_system_health()
        agent_performance = observability.get_agent_performance()
        quality_metrics = observability.get_quality_metrics()
        
        # Check Neo4j status
        try:
            test_query = "MATCH (n) RETURN COUNT(n) as total LIMIT 1"
            await neo4j_repo.execute_query(test_query, {})
            neo4j_status = "healthy"
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            neo4j_status = "unhealthy"
        
        # Determine agent status
        agents_status = {}
        for agent_name in ["intelligent_intent_processor", "smart_neo4j_recommender", "multilingual_response_generator"]:
            if agent_name in agent_performance:
                success_rate = agent_performance[agent_name]["success_rate"]
                agents_status[agent_name] = "healthy" if success_rate > 0.9 else "degraded" if success_rate > 0.7 else "unhealthy"
            else:
                agents_status[agent_name] = "unknown"
        
        return EnterpriseHealthResponse(
            status=system_health["status"],
            agents_status=agents_status,
            performance_metrics={
                "avg_response_time_ms": system_health["avg_response_time_ms"],
                "success_rate": system_health["success_rate"],
                "total_requests": system_health["total_requests"]
            },
            quality_metrics=quality_metrics,
            neo4j_status=neo4j_status,
            timestamp=str(uuid.uuid4())  # Simplified timestamp
        )
        
    except Exception as e:
        logger.error(f"Enterprise health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/metrics", response_model=EnterpriseMetricsResponse)
async def enterprise_metrics(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> EnterpriseMetricsResponse:
    """Real-time enterprise metrics for monitoring dashboards"""
    
    try:
        # Create enterprise orchestrator
        orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
        
        observability = orchestrator.observability
        
        # Get all metrics
        system_health = observability.get_system_health()
        agent_performance = observability.get_agent_performance()
        quality_metrics = observability.get_quality_metrics()
        business_metrics = observability.get_business_metrics()
        
        return EnterpriseMetricsResponse(
            recommendation_metrics={
                "total_requests": system_health["total_requests"],
                "avg_response_time_ms": system_health["avg_response_time_ms"],
                "success_rate": system_health["success_rate"],
                "failed_requests": system_health["failed_requests"]
            },
            agent_metrics=agent_performance,
            quality_metrics=quality_metrics,
            business_metrics=business_metrics
        )
        
    except Exception as e:
        logger.error(f"Enterprise metrics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}"
        )


@router.post("/test")
async def test_enterprise_system(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> Dict[str, Any]:
    """
    Comprehensive test endpoint for the enterprise system
    Tests all 3 agents with various scenarios
    """
    
    test_results = {
        "test_timestamp": str(uuid.uuid4()),
        "overall_status": "unknown",
        "tests": {}
    }
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "expert_english_query",
            "query": "I need PowerWave 450 compatible wire feeder with 400A capacity and cooling system for continuous duty cycle",
            "user_context": {
                "user_id": "test_expert",
                "preferred_language": "en", 
                "expertise_history": ["GMAW", "wire feed speed", "duty cycle"],
                "organization": "Manufacturing Corp"
            },
            "expected_mode": "EXPERT"
        },
        {
            "name": "beginner_english_query", 
            "query": "I'm new to welding and need help choosing a welding machine for my garage projects",
            "user_context": {
                "user_id": "test_beginner",
                "preferred_language": "en",
                "expertise_history": [],
                "organization": "Home User"
            },
            "expected_mode": "GUIDED"
        },
        {
            "name": "spanish_multilingual_query",
            "query": "Necesito una soldadora para acero inoxidable en mi taller",
            "user_context": {
                "user_id": "test_spanish",
                "preferred_language": "es",
                "expertise_history": [],
                "organization": "Taller Mexicano"
            },
            "expected_language": "es"
        },
        {
            "name": "hybrid_technical_query",
            "query": "Looking for MIG welding setup for aluminum automotive parts",
            "user_context": {
                "user_id": "test_hybrid",
                "preferred_language": "en",
                "expertise_history": ["MIG"],
                "organization": "Auto Shop"
            },
            "expected_mode": "HYBRID"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_scenarios)
    
    # Create enterprise orchestrator
    orchestrator = await get_enterprise_orchestrator_service(neo4j_repo)
    
    for scenario in test_scenarios:
        test_name = scenario["name"]
        
        try:
            # Create user context
            user_context = UserContext(**scenario["user_context"])
            
            # Process request
            response = await orchestrator.process_recommendation_request(
                query=scenario["query"],
                user_context=user_context,
                session_id=f"test_{test_name}"
            )
            
            # Validate response
            test_result = {
                "status": "passed",
                "query": scenario["query"],
                "detected_language": response.original_intent.detected_language.value,
                "detected_mode": response.original_intent.expertise_mode.value,
                "packages_found": len(response.packages),
                "confidence": response.overall_confidence,
                "response_time_ms": response.total_processing_time_ms,
                "trinity_compliance": len([p for p in response.packages if p.trinity_compliance]),
                "errors": []
            }
            
            # Check expectations
            if "expected_mode" in scenario:
                if response.original_intent.expertise_mode.value != scenario["expected_mode"]:
                    test_result["errors"].append(f"Expected mode {scenario['expected_mode']}, got {response.original_intent.expertise_mode.value}")
            
            if "expected_language" in scenario:
                if response.original_intent.detected_language.value != scenario["expected_language"]:
                    test_result["errors"].append(f"Expected language {scenario['expected_language']}, got {response.original_intent.detected_language.value}")
            
            # Check basic functionality
            if response.overall_confidence < 0.1:
                test_result["errors"].append("Very low confidence score")
            
            if not response.formatted_response.summary:
                test_result["errors"].append("No summary generated")
            
            if test_result["errors"]:
                test_result["status"] = "failed"
            else:
                passed_tests += 1
                
        except Exception as e:
            test_result = {
                "status": "error",
                "query": scenario["query"],
                "error": str(e),
                "errors": [str(e)]
            }
            logger.error(f"Test {test_name} failed: {e}")
        
        test_results["tests"][test_name] = test_result
    
    # Overall status
    if passed_tests == total_tests:
        test_results["overall_status"] = "all_passed"
    elif passed_tests > 0:
        test_results["overall_status"] = "partial_passed"
    else:
        test_results["overall_status"] = "all_failed"
    
    test_results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": passed_tests / total_tests
    }
    
    return test_results