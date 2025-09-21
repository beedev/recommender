"""
Enterprise Services Package
3-Agent Agentic Architecture for Enterprise Welding Recommendations

This package contains the enterprise-grade services that implement the 3-agent architecture:
- Agent 1: Intelligent Intent Processor (multilingual + auto-mode detection)
- Agent 2: Smart Neo4j Recommender (graph algorithms + Trinity formation)
- Agent 3: Multilingual Response Generator (enterprise formatting + explanations)

Plus supporting services:
- Enterprise Orchestrator (coordinates all 3 agents)
- Enterprise Observability (comprehensive monitoring)
"""

from .enterprise_orchestrator_service import (
    EnterpriseOrchestratorService,
    get_enterprise_orchestrator_service
)
from .intelligent_intent_service import IntelligentIntentService, get_intelligent_intent_service
from .smart_neo4j_service import SmartNeo4jService, get_smart_neo4j_service
from .multilingual_response_service import MultilingualResponseService
from .enterprise_observability_service import EnterpriseObservabilityService
from .enhanced_state_models import (
    EnhancedProcessedIntent,
    ScoredRecommendations,
    EnterpriseRecommendationResponse,
    TrinityPackage,
    UserContext,
    ExpertiseMode,
    LanguageCode,
    SearchStrategy,
    GraphAlgorithm
)

__all__ = [
    # Main orchestrator service
    "EnterpriseOrchestratorService",
    "get_enterprise_orchestrator_service",
    
    # 3 Agent services
    "IntelligentIntentService",
    "get_intelligent_intent_service",
    "SmartNeo4jService", 
    "get_smart_neo4j_service",
    "MultilingualResponseService",
    
    # Supporting services
    "EnterpriseObservabilityService",
    
    # Data models
    "EnhancedProcessedIntent",
    "ScoredRecommendations",
    "EnterpriseRecommendationResponse",
    "TrinityPackage",
    "UserContext",
    "ExpertiseMode",
    "LanguageCode",
    "SearchStrategy",
    "GraphAlgorithm"
]