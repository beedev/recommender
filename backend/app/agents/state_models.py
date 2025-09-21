"""
State models for the LangGraph welding recommendation system.

Defines the shared state structures used across agents in the workflow.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from ..core.config_loader import get_config_loader

# Load configuration
config_loader = get_config_loader()

def create_welding_process_enum():
    """Dynamically create WeldingProcess enum from configuration"""
    welding_config = config_loader.load_welding_config()
    processes = {}
    
    # Add primary processes
    for process in welding_config.get('welding_processes', {}).get('primary', []):
        processes[process] = process
    
    # Add technical processes
    for process in welding_config.get('welding_processes', {}).get('technical', []):
        processes[process] = process
    
    return Enum('WeldingProcess', processes, type=str)

def create_material_enum():
    """Dynamically create Material enum from configuration"""
    welding_config = config_loader.load_welding_config()
    materials = {}
    
    for material in welding_config.get('materials', {}).get('primary', []):
        # Convert to enum format (uppercase key, lowercase value)
        enum_key = material.upper()
        materials[enum_key] = material
    
    return Enum('Material', materials, type=str)

def create_industry_enum():
    """Dynamically create Industry enum from configuration"""
    welding_config = config_loader.load_welding_config()
    industries = {}
    
    for industry in welding_config.get('industries', []):
        # Convert to enum format (uppercase key, lowercase value)
        enum_key = industry.upper()
        industries[enum_key] = industry
    
    return Enum('Industry', industries, type=str)

# Create dynamic enums
WeldingProcess = create_welding_process_enum()
Material = create_material_enum()
Industry = create_industry_enum()


class ConfidenceLevel(str, Enum):
    """Confidence levels for intent extraction"""
    HIGH = "high"        # 0.8+
    MEDIUM = "medium"    # 0.6-0.8
    LOW = "low"          # 0.4-0.6
    UNCERTAIN = "uncertain"  # <0.4


class QueryType(str, Enum):
    """Types of queries to generate"""
    BASIC_PROPERTY = "basic_property"
    RANGE_BASED = "range_based"
    TEXT_SEARCH = "text_search"
    INDUSTRY_BASED = "industry_based"
    SIMILAR_PURCHASE = "similar_purchase"
    COMPATIBILITY = "compatibility"
    HYBRID = "hybrid"


# =============================================================================
# INTENT EXTRACTION STATE
# =============================================================================

class ExtractedIntent(BaseModel):
    """Structured intent extracted from natural language"""
    
    # Core welding parameters
    welding_process: List[WeldingProcess] = Field(default_factory=list)
    material: Optional[Material] = None
    power_watts: Optional[int] = Field(None, ge=100, le=10000)
    current_amps: Optional[int] = Field(None, ge=10, le=1000)
    voltage: Optional[int] = Field(None, ge=12, le=480)
    thickness_mm: Optional[float] = Field(None, ge=0.1, le=100.0)
    
    # Application context
    industry: Optional[Industry] = None
    environment: Optional[str] = None  # indoor, outdoor, marine, etc.
    application: Optional[str] = None  # specific use case
    duty_cycle: Optional[str] = None   # light, medium, heavy, continuous
    
    # Similarity references
    similar_to_customer: Optional[str] = None
    similar_to_purchase: Optional[str] = None
    similar_to_package: Optional[str] = None
    
    # Quality indicators
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNCERTAIN
    extraction_issues: List[str] = Field(default_factory=list)
    
    # Source tracking
    original_query: str = ""
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    ambiguous_terms: List[str] = Field(default_factory=list)


class WeldingIntentState(BaseModel):
    """State for intent extraction workflow"""
    
    # Input
    user_query: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Processing state
    raw_extraction: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Output
    extracted_intent: Optional[ExtractedIntent] = None
    
    # Workflow control
    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    # LangSmith tracking
    run_id: Optional[str] = None
    trace_id: Optional[str] = None


# =============================================================================
# QUERY GENERATION STATE
# =============================================================================

class CypherQuery(BaseModel):
    """Generated Cypher query with metadata"""
    
    query: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    query_type: QueryType
    description: str = ""
    expected_results: int = 0
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    
    # Execution metadata
    execution_time_ms: Optional[float] = None
    result_count: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None


class QueryStrategy(BaseModel):
    """Query generation strategy"""
    
    primary_strategy: QueryType
    fallback_strategies: List[QueryType] = Field(default_factory=list)
    use_fuzzy_matching: bool = True
    use_text_search: bool = True
    max_results: int = 50
    
    # Ranking preferences
    prefer_sales_frequency: bool = True
    prefer_compatibility: bool = True
    prefer_industry_match: bool = True


class QueryGenerationState(BaseModel):
    """State for Cypher query generation and execution"""
    
    # Input
    intent: Optional[ExtractedIntent] = None
    query_strategy: Optional[QueryStrategy] = None
    
    # Query generation
    generated_queries: List[CypherQuery] = Field(default_factory=list)
    primary_query: Optional[CypherQuery] = None
    fallback_queries: List[CypherQuery] = Field(default_factory=list)
    
    # Execution results
    raw_results: List[Dict[str, Any]] = Field(default_factory=list)
    processed_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Quality metrics
    result_quality_score: float = 0.0
    coverage_score: float = 0.0  # How well results cover requirements
    diversity_score: float = 0.0  # Variety in results
    
    # Workflow control
    execution_successful: bool = False
    fallback_used: bool = False
    needs_refinement: bool = False
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# COMBINED WORKFLOW STATE
# =============================================================================

class WeldingRecommendationState(BaseModel):
    """Complete state for the welding recommendation workflow"""
    
    # Workflow inputs
    user_query: str = ""
    user_context: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    
    # Agent states
    intent_state: WeldingIntentState = Field(default_factory=WeldingIntentState)
    query_state: QueryGenerationState = Field(default_factory=QueryGenerationState)
    
    # Final outputs
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Workflow control
    current_step: str = "intent_extraction"
    workflow_complete: bool = False
    needs_user_input: bool = False
    
    # Performance tracking
    total_execution_time_ms: float = 0.0
    langsmith_run_id: Optional[str] = None


# =============================================================================
# RESULT MODELS
# =============================================================================

class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    
    product_id: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    
    # Scoring
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)
    popularity_score: float = Field(0.0, ge=0.0, le=1.0)
    compatibility_score: float = Field(0.0, ge=0.0, le=1.0)
    overall_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Explanation
    recommendation_reason: str = ""
    match_criteria: List[str] = Field(default_factory=list)
    
    # Neo4j metadata
    node_labels: List[str] = Field(default_factory=list)
    relationship_context: Dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    """Complete recommendation response"""
    
    # Core results
    items: List[RecommendationItem] = Field(default_factory=list)
    total_found: int = 0
    
    # Query context
    original_query: str = ""
    extracted_intent: Optional[ExtractedIntent] = None
    query_strategy_used: Optional[QueryType] = None
    
    # Quality metrics
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    coverage: float = Field(0.0, ge=0.0, le=1.0)
    diversity: float = Field(0.0, ge=0.0, le=1.0)
    
    # Execution metadata
    execution_time_ms: float = 0.0
    agent_workflow_id: Optional[str] = None
    
    # User feedback
    clarification_needed: bool = False
    suggested_questions: List[str] = Field(default_factory=list)
    refinement_suggestions: List[str] = Field(default_factory=list)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def confidence_to_level(confidence: float) -> ConfidenceLevel:
    """Convert numeric confidence to level enum"""
    if confidence >= 0.8:
        return ConfidenceLevel.HIGH
    elif confidence >= 0.6:
        return ConfidenceLevel.MEDIUM  
    elif confidence >= 0.4:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.UNCERTAIN


def should_use_fallback(primary_results: int, confidence: float) -> bool:
    """Determine if fallback strategy should be used"""
    return primary_results < 3 or confidence < 0.6


def calculate_overall_score(relevance: float, popularity: float, compatibility: float) -> float:
    """Calculate weighted overall score"""
    weights = {
        "relevance": 0.5,
        "popularity": 0.2, 
        "compatibility": 0.3
    }
    
    return (
        relevance * weights["relevance"] +
        popularity * weights["popularity"] + 
        compatibility * weights["compatibility"]
    )