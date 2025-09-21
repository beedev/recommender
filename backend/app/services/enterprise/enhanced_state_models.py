"""
Enhanced state models for the Enterprise 3-Agent Agentic System
Extends existing state models with enterprise features while maintaining compatibility
"""

import time
from typing import Dict, List, Optional, Any, Union, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
from dataclasses import dataclass, field

from ...agents.state_models import ExtractedIntent, RecommendationResponse


class ExpertiseMode(str, Enum):
    """Auto-detected user expertise levels"""
    EXPERT = "EXPERT"      # Technical professionals with domain knowledge
    GUIDED = "GUIDED"      # Users needing guidance and explanations
    HYBRID = "HYBRID"      # Mixed expertise, adaptive approach


class SearchStrategy(str, Enum):
    """Search strategy selection for Neo4j queries"""
    GRAPH_FOCUSED = "GRAPH_FOCUSED"    # Relationship-based for expert queries
    HYBRID = "HYBRID"                  # Combined vector + graph for broader coverage
    GUIDED_FLOW = "GUIDED_FLOW"        # Guided flow step-by-step selection


class LanguageCode(str, Enum):
    """Supported languages for multilingual processing"""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    PT = "pt"
    IT = "it"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    RU = "ru"
    AR = "ar"
    HI = "hi"


# =============================================================================
# ENHANCED INTENT MODELS (Agent 1)
# =============================================================================

@dataclass
class UserContext:
    """Enhanced user context for personalization"""
    user_id: str = "anonymous"
    session_id: str = "default"
    preferred_language: str = "en"
    expertise_history: List[str] = field(default_factory=list)
    previous_queries: List[str] = field(default_factory=list)
    industry_context: Optional[str] = None
    
    # Enterprise features
    organization: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = field(default_factory=list)


class EnhancedProcessedIntent(ExtractedIntent):
    """
    Extends ExtractedIntent with enterprise features for Agent 1 output
    Maintains backward compatibility while adding auto-mode detection
    """
    
    # Original query tracking
    original_query: str = ""
    processed_query: str = ""  # Translated to English if needed
    
    # Auto-detected capabilities
    detected_language: LanguageCode = LanguageCode.EN
    expertise_mode: ExpertiseMode = ExpertiseMode.HYBRID
    
    # Confidence and processing metadata
    mode_detection_confidence: float = Field(0.0, ge=0.0, le=1.0)
    language_detection_confidence: float = Field(0.0, ge=0.0, le=1.0)
    
    # Enterprise tracking
    trace_id: str = ""
    processing_start_time: float = field(default_factory=time.time)
    
    # Preserve original intent for fallback
    original_intent: Optional[ExtractedIntent] = None
    
    @classmethod
    def from_extracted_intent(
        cls, 
        intent: ExtractedIntent,
        **enterprise_kwargs
    ) -> "EnhancedProcessedIntent":
        """Convert existing ExtractedIntent to enhanced version"""
        
        # Extract all fields from the original intent
        if hasattr(intent, 'model_dump'):
            # Pydantic model
            intent_data = intent.model_dump()
        elif hasattr(intent, 'to_dict'):
            # SimpleWeldingIntent dataclass
            intent_data = intent.to_dict()
        else:
            # Fallback for other types
            intent_data = intent.__dict__ if hasattr(intent, '__dict__') else {}
        
        # Add enterprise fields
        intent_data.update(enterprise_kwargs)
        intent_data["original_intent"] = intent
        
        return cls(**intent_data)


# =============================================================================
# NEO4J QUERY MODELS (Agent 2)
# =============================================================================

class GraphAlgorithm(str, Enum):
    """Available graph algorithms for Neo4j queries"""
    SHORTEST_PATH = "shortest_path"
    PAGERANK = "pagerank"
    CENTRALITY = "centrality"
    CLUSTERING = "clustering"
    SALES_FREQUENCY = "sales_frequency"
    COMPATIBILITY = "compatibility"


@dataclass
class RoutingDecision:
    """Intelligent routing decision for Neo4j strategy"""
    strategy: SearchStrategy
    algorithms: List[GraphAlgorithm]
    weights: Dict[str, float]
    reasoning: str = ""
    confidence: float = 0.0


class TrinityPackage(BaseModel):
    """Enhanced Trinity package (PowerSource + Feeder + Cooler)"""
    
    # Core Trinity components (required)
    power_source: Dict[str, Any]
    feeder: Optional[Dict[str, Any]] = None
    cooler: Optional[Dict[str, Any]] = None
    
    # Additional components
    consumables: List[Dict[str, Any]] = Field(default_factory=list)
    accessories: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Business metrics
    package_score: float = Field(0.0, ge=0.0, le=1.0)
    trinity_compliance: bool = False
    business_rule_compliance: float = Field(0.0, ge=0.0, le=1.0)
    
    # Pricing
    total_price: float = 0.0
    currency: str = "USD"
    
    # Compatibility validation
    compatibility_verified: bool = False
    compatibility_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Neo4j metadata
    formation_path: List[str] = Field(default_factory=list)
    relationship_strength: float = Field(0.0, ge=0.0, le=1.0)


class ScoredRecommendations(BaseModel):
    """Agent 2 output: Scored Trinity packages with metadata"""
    
    packages: List[TrinityPackage] = Field(default_factory=list)
    total_packages_found: int = 0
    
    # Search metadata
    search_metadata: RoutingDecision
    algorithms_used: List[GraphAlgorithm]
    
    # Quality metrics
    confidence_distribution: Dict[str, float] = Field(default_factory=dict)
    trinity_formation_rate: float = Field(0.0, ge=0.0, le=1.0)
    
    # Performance tracking
    neo4j_query_time_ms: float = 0.0
    graph_traversal_time_ms: float = 0.0
    
    # Enterprise observability
    trace_id: str = ""
    neo4j_queries_executed: int = 0


# =============================================================================
# RESPONSE GENERATION MODELS (Agent 3)
# =============================================================================

class ExplanationLevel(str, Enum):
    """Explanation detail level based on expertise mode"""
    TECHNICAL = "technical"      # Expert mode: technical details
    EDUCATIONAL = "educational"  # Guided mode: learning-focused
    BALANCED = "balanced"        # Hybrid mode: moderate detail


class BusinessPriority(str, Enum):
    """Business context priorities for re-ranking"""
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_MAXIMIZATION = "performance_maximization"
    RELIABILITY_FOCUS = "reliability_focus"
    COMPATIBILITY_ASSURANCE = "compatibility_assurance"


class MultilingualResponse(BaseModel):
    """Formatted response with multilingual support"""
    
    # Content in user's language
    title: str = ""
    summary: str = ""
    detailed_explanation: str = ""
    technical_notes: List[str] = Field(default_factory=list)
    
    # Package presentations
    package_descriptions: List[str] = Field(default_factory=list)
    comparison_matrix: Optional[Dict[str, Any]] = None
    
    # User guidance
    next_steps: List[str] = Field(default_factory=list)
    related_questions: List[str] = Field(default_factory=list)
    
    # Metadata
    response_language: LanguageCode = LanguageCode.EN
    explanation_level: ExplanationLevel = ExplanationLevel.BALANCED
    cultural_adaptations: List[str] = Field(default_factory=list)


class EnterpriseRecommendationResponse(BaseModel):
    """Final Agent 3 output: Complete enterprise response"""
    
    # Core recommendation data
    packages: List[TrinityPackage]
    total_found: int = 0
    
    # Multilingual response
    formatted_response: MultilingualResponse
    explanations: Dict[str, str] = Field(default_factory=dict)
    
    # Quality and confidence
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    
    # Search context
    search_metadata: RoutingDecision
    original_intent: EnhancedProcessedIntent
    
    # Business intelligence
    business_insights: List[str] = Field(default_factory=list)
    cost_analysis: Optional[Dict[str, Any]] = None
    
    # Enterprise observability
    trace_id: str = ""
    total_processing_time_ms: float = 0.0
    agent_performance_breakdown: Dict[str, float] = Field(default_factory=dict)
    
    # User experience
    needs_follow_up: bool = False
    follow_up_questions: List[str] = Field(default_factory=list)
    satisfaction_prediction: float = Field(0.0, ge=0.0, le=1.0)


# =============================================================================
# ORCHESTRATION STATE
# =============================================================================

class EnterpriseWorkflowState(TypedDict):
    """Complete state for 3-agent enterprise workflow"""
    
    # Input
    user_query: str
    user_context: UserContext
    session_id: str
    
    # Agent 1 state (Intent Processing)
    processed_intent: Optional[EnhancedProcessedIntent]
    intent_processing_time_ms: float
    
    # Agent 2 state (Neo4j Recommendations)
    scored_recommendations: Optional[ScoredRecommendations]
    neo4j_processing_time_ms: float
    
    # Agent 3 state (Response Generation)
    final_response: Optional[EnterpriseRecommendationResponse]
    response_generation_time_ms: float
    
    # Workflow control
    current_agent: str
    workflow_complete: bool
    requires_fallback: bool
    
    # Error handling
    errors: List[str]
    warnings: List[str]
    
    # Enterprise observability
    trace_id: str
    langsmith_run_id: Optional[str]
    start_time: float
    total_execution_time_ms: float
    
    # Quality metrics
    success_indicators: Dict[str, bool]
    performance_metrics: Dict[str, float]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def detect_expertise_level(query: str, user_history: List[str] = None) -> ExpertiseMode:
    """Auto-detect user expertise level from query patterns"""
    
    expert_signals = [
        "amperage", "voltage", "duty cycle", "wire feed speed", "arc length",
        "penetration", "bead profile", "heat affected zone", "HAZ",
        "GMAW", "GTAW", "SMAW", "FCAW", "SAW",
        "ER70S", "ER4043", "E7018", "flux core",
        "reverse polarity", "DCEP", "DCEN", "AC TIG"
    ]
    
    guided_signals = [
        "beginner", "new to welding", "learning", "help me understand",
        "what do I need", "getting started", "first time", "basic",
        "simple", "easy", "recommended for beginners"
    ]
    
    expert_score = sum(1 for signal in expert_signals if signal.lower() in query.lower())
    guided_score = sum(1 for signal in guided_signals if signal.lower() in query.lower())
    
    if expert_score >= 3 or (expert_score >= 2 and len(query) > 100):
        return ExpertiseMode.EXPERT
    elif guided_score >= 2 or any(signal in query.lower() for signal in ["beginner", "new to welding", "learning"]):
        return ExpertiseMode.GUIDED
    else:
        return ExpertiseMode.HYBRID


def calculate_trinity_compliance(package: TrinityPackage) -> bool:
    """Check if package meets Trinity requirements (PowerSource + Feeder + Cooler)"""
    return (
        package.power_source is not None and
        package.feeder is not None and 
        package.cooler is not None
    )


def estimate_processing_complexity(intent: EnhancedProcessedIntent) -> float:
    """Estimate processing complexity for resource allocation"""
    complexity = 0.3  # Base complexity
    
    # Query complexity indicators
    if len(intent.original_query) > 200:
        complexity += 0.2
    
    # Multi-language adds complexity
    if intent.detected_language != LanguageCode.EN:
        complexity += 0.1
    
    # Expert mode may require deeper analysis
    if intent.expertise_mode == ExpertiseMode.EXPERT:
        complexity += 0.2
    
    # Multiple processes increase complexity
    if len(intent.welding_process) > 1:
        complexity += 0.1
    
    # Specific technical requirements
    if intent.power_watts or intent.current_amps or intent.voltage:
        complexity += 0.1
    
    return min(complexity, 1.0)