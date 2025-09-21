"""
LangGraph Workflow for Welding Equipment Recommendations.

Orchestrates the 2-agent system using LangGraph for workflow management
and LangSmith for observability and tracing.
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
# LangSmith imports (if available)
try:
    from langsmith import traceable, Client
except ImportError:
    # Fallback implementations if langsmith is not available
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator
    
    class Client:
        def __init__(self, **kwargs):
            pass

from .state_models import (
    WeldingRecommendationState, WeldingIntentState, QueryGenerationState,
    ExtractedIntent, RecommendationResponse, RecommendationItem,
    QueryStrategy, ConfidenceLevel
)
from .intent_extraction_agent import IntentExtractionAgent  
from .cypher_query_agent import CypherQueryAgent
from ..database.repositories import Neo4jRepository
from ..core.config import settings

logger = logging.getLogger(__name__)


class WeldingRecommendationGraph:
    """
    LangGraph-based workflow for welding equipment recommendations.
    
    Workflow Steps:
    1. Intent Extraction - Convert natural language to structured parameters
    2. Query Strategy Selection - Determine optimal Neo4j query approach
    3. Query Generation & Execution - Build and run Cypher queries
    4. Result Processing - Rank and format recommendations
    5. Quality Assessment - Evaluate results and suggest improvements
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        """Initialize the recommendation graph workflow"""
        
        self.neo4j_repo = neo4j_repo
        
        # Initialize agents
        self.intent_agent = IntentExtractionAgent()
        self.query_agent = CypherQueryAgent(neo4j_repo)
        
        # Initialize LangSmith client if available
        self.langsmith_client = None
        if settings.LANGSMITH_API_KEY:
            try:
                self.langsmith_client = Client(
                    api_key=settings.LANGSMITH_API_KEY,
                    api_url="https://api.smith.langchain.com"
                )
                logger.info("LangSmith client initialized for tracing")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
        
        # Build the workflow graph
        self.graph = self._build_graph()
        
    def _build_graph(self) -> CompiledStateGraph:
        """Build the LangGraph workflow"""
        
        # Create state graph
        workflow = StateGraph(WeldingRecommendationState)
        
        # Add workflow nodes
        workflow.add_node("intent_extraction", self._intent_extraction_node)
        workflow.add_node("strategy_selection", self._strategy_selection_node)
        workflow.add_node("query_generation", self._query_generation_node)
        workflow.add_node("result_processing", self._result_processing_node)
        workflow.add_node("quality_assessment", self._quality_assessment_node)
        workflow.add_node("clarification_handler", self._clarification_handler_node)
        
        # Define workflow edges
        workflow.set_entry_point("intent_extraction")
        
        # Intent extraction -> strategy selection or clarification
        workflow.add_conditional_edges(
            "intent_extraction",
            self._should_request_clarification,
            {
                "clarify": "clarification_handler",
                "continue": "strategy_selection"
            }
        )
        
        # Clarification -> strategy selection (after user input)
        workflow.add_edge("clarification_handler", "strategy_selection")
        
        # Strategy selection -> query generation
        workflow.add_edge("strategy_selection", "query_generation")
        
        # Query generation -> result processing
        workflow.add_edge("query_generation", "result_processing")
        
        # Result processing -> quality assessment or retry
        workflow.add_conditional_edges(
            "result_processing",
            self._should_retry_with_fallback,
            {
                "retry": "query_generation",
                "complete": "quality_assessment"
            }
        )
        
        # Quality assessment -> end
        workflow.add_edge("quality_assessment", END)
        
        # Add memory for conversation state
        memory = MemorySaver()
        
        # Compile the graph
        compiled_graph = workflow.compile(checkpointer=memory)
        
        logger.info("LangGraph workflow compiled successfully")
        return compiled_graph
    
    @traceable(name="welding_recommendation_workflow")
    async def recommend(
        self, 
        user_query: str, 
        user_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> RecommendationResponse:
        """
        Main entry point for welding equipment recommendations.
        
        Args:
            user_query: Natural language query from user
            user_context: Additional context (user preferences, history, etc.)
            session_id: Optional session ID for conversation tracking
            
        Returns:
            RecommendationResponse with recommendations and metadata
        """
        
        start_time = time.time()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize workflow state
        initial_state = WeldingRecommendationState(
            user_query=user_query,
            user_context=user_context or {},
            session_id=session_id,
            intent_state=WeldingIntentState(
                user_query=user_query,
                context=user_context or {}
            ),
            query_state=QueryGenerationState()
        )
        
        logger.info(f"Starting recommendation workflow for session {session_id}")
        
        try:
            # Execute the workflow
            config = {
                "thread_id": session_id,
                "tags": ["welding_recommendation", "production"]
            }
            
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Calculate total execution time
            execution_time = (time.time() - start_time) * 1000
            final_state.total_execution_time_ms = execution_time
            
            # Build response
            response = self._build_response(final_state, execution_time)
            
            logger.info(
                f"Recommendation workflow completed in {execution_time:.2f}ms. "
                f"Found {len(response.items)} recommendations"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Return error response
            return RecommendationResponse(
                items=[],
                total_found=0,
                original_query=user_query,
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                clarification_needed=True,
                suggested_questions=[
                    "Could you provide more specific welding requirements?",
                    "What type of welding process do you need?",
                    "What material will you be welding?"
                ]
            )
    
    async def _intent_extraction_node(self, state: WeldingRecommendationState) -> WeldingRecommendationState:
        """Node for intent extraction"""
        
        logger.debug("Executing intent extraction node")
        
        try:
            # Extract intent using the intent agent
            updated_intent_state = await self.intent_agent.extract_intent(state.intent_state)
            state.intent_state = updated_intent_state
            
            # Update workflow state
            state.current_step = "intent_extraction"
            
            # Check if clarification is needed
            if updated_intent_state.needs_clarification:
                state.needs_user_input = True
                logger.info("Intent extraction requires clarification")
            else:
                logger.info(f"Intent extracted with confidence: {updated_intent_state.extracted_intent.confidence:.2f}")
            
            return state
            
        except Exception as e:
            logger.error(f"Intent extraction node failed: {e}")
            state.intent_state.extracted_intent = ExtractedIntent(
                confidence=0.1,
                confidence_level=ConfidenceLevel.UNCERTAIN,
                extraction_issues=[f"Node execution failed: {str(e)}"],
                original_query=state.user_query
            )
            return state
    
    async def _strategy_selection_node(self, state: WeldingRecommendationState) -> WeldingRecommendationState:
        """Node for query strategy selection"""
        
        logger.debug("Executing strategy selection node")
        
        try:
            intent = state.intent_state.extracted_intent
            if not intent:
                raise ValueError("No extracted intent available for strategy selection")
            
            # Set the intent in query state
            state.query_state.intent = intent
            
            # Strategy selection logic will be handled by the query agent
            state.current_step = "strategy_selection"
            
            logger.info(f"Strategy selection completed for intent with {len(intent.welding_process)} processes")
            
            return state
            
        except Exception as e:
            logger.error(f"Strategy selection node failed: {e}")
            state.query_state.errors.append(f"Strategy selection failed: {str(e)}")
            return state
    
    async def _query_generation_node(self, state: WeldingRecommendationState) -> WeldingRecommendationState:
        """Node for query generation and execution"""
        
        logger.debug("Executing query generation node")
        
        try:
            # Generate and execute queries using the query agent
            updated_query_state = await self.query_agent.generate_and_execute_queries(state.query_state)
            state.query_state = updated_query_state
            
            state.current_step = "query_generation"
            
            if updated_query_state.execution_successful:
                logger.info(f"Query generation successful: {len(updated_query_state.processed_results)} results")
            else:
                logger.warning("Query generation had issues, may need fallback")
            
            return state
            
        except Exception as e:
            logger.error(f"Query generation node failed: {e}")
            state.query_state.errors.append(f"Query generation failed: {str(e)}")
            state.query_state.execution_successful = False
            return state
    
    async def _result_processing_node(self, state: WeldingRecommendationState) -> WeldingRecommendationState:
        """Node for result processing and ranking"""
        
        logger.debug("Executing result processing node")
        
        try:
            # Results are already processed by the query agent
            # This node handles additional post-processing
            
            processed_results = state.query_state.processed_results
            
            # Apply additional business logic filtering
            filtered_results = self._apply_business_filters(processed_results, state.intent_state.extracted_intent)
            
            # Limit results to reasonable number
            max_results = 20
            limited_results = filtered_results[:max_results]
            
            # Store in state
            state.recommendations = [item.dict() for item in limited_results]
            state.current_step = "result_processing"
            
            logger.info(f"Result processing completed: {len(limited_results)} final recommendations")
            
            return state
            
        except Exception as e:
            logger.error(f"Result processing node failed: {e}")
            state.recommendations = []
            return state
    
    async def _quality_assessment_node(self, state: WeldingRecommendationState) -> WeldingRecommendationState:
        """Node for quality assessment and final preparation"""
        
        logger.debug("Executing quality assessment node")
        
        try:
            # Assess overall recommendation quality
            quality_metrics = self._assess_recommendation_quality(state)
            
            # Store metadata
            state.metadata.update({
                "quality_assessment": quality_metrics,
                "workflow_stats": {
                    "intent_confidence": state.intent_state.extracted_intent.confidence if state.intent_state.extracted_intent else 0.0,
                    "query_success": state.query_state.execution_successful,
                    "result_count": len(state.recommendations),
                    "fallback_used": state.query_state.fallback_used
                }
            })
            
            state.current_step = "quality_assessment"
            state.workflow_complete = True
            
            logger.info(f"Quality assessment completed. Overall quality: {quality_metrics.get('overall_score', 0.0):.2f}")
            
            return state
            
        except Exception as e:
            logger.error(f"Quality assessment node failed: {e}")
            state.metadata["quality_assessment_error"] = str(e)
            state.workflow_complete = True
            return state
    
    async def _clarification_handler_node(self, state: WeldingRecommendationState) -> WeldingRecommendationState:
        """Node for handling clarification requests"""
        
        logger.debug("Executing clarification handler node")
        
        # In a real implementation, this would handle user responses to clarification questions
        # For now, we'll proceed with what we have
        
        state.needs_user_input = False
        state.current_step = "clarification_handled"
        
        logger.info("Clarification handler executed (proceeding with available information)")
        
        return state
    
    def _should_request_clarification(self, state: WeldingRecommendationState) -> str:
        """Conditional edge: determine if clarification is needed"""
        
        if state.intent_state.needs_clarification:
            intent = state.intent_state.extracted_intent
            
            # Only request clarification for very low confidence
            if intent and intent.confidence < 0.4:
                return "clarify"
        
        return "continue"
    
    def _should_retry_with_fallback(self, state: WeldingRecommendationState) -> str:
        """Conditional edge: determine if query should be retried"""
        
        # Check if we have sufficient results
        if len(state.recommendations) < 3 and not state.query_state.fallback_used:
            # Could retry with different strategy
            pass
        
        # For now, always complete
        return "complete"
    
    def _apply_business_filters(
        self, 
        results: List[RecommendationItem], 
        intent: Optional[ExtractedIntent]
    ) -> List[RecommendationItem]:
        """Apply business logic filters to results"""
        
        filtered_results = []
        
        for item in results:
            # Basic quality filters
            if item.overall_score < 0.1:
                continue
            
            # Category filters (ensure we have actual products)
            if not item.product_id or not item.product_name:
                continue
            
            # Availability filters (could check inventory, etc.)
            # if not self._check_availability(item):
            #     continue
            
            filtered_results.append(item)
        
        return filtered_results
    
    def _assess_recommendation_quality(self, state: WeldingRecommendationState) -> Dict[str, Any]:
        """Assess overall quality of recommendations"""
        
        metrics = {
            "overall_score": 0.0,
            "coverage_score": 0.0,
            "diversity_score": 0.0,
            "confidence_score": 0.0,
            "result_count": len(state.recommendations),
            "issues": []
        }
        
        if not state.recommendations:
            metrics["issues"].append("No recommendations found")
            return metrics
        
        # Use query state metrics if available
        if state.query_state.execution_successful:
            metrics["coverage_score"] = state.query_state.coverage_score
            metrics["diversity_score"] = state.query_state.diversity_score
            metrics["overall_score"] = state.query_state.result_quality_score
        
        # Intent confidence
        if state.intent_state.extracted_intent:
            metrics["confidence_score"] = state.intent_state.extracted_intent.confidence
        
        # Overall quality calculation
        if metrics["overall_score"] == 0.0:
            # Calculate from available components
            components = [
                metrics["coverage_score"],
                metrics["diversity_score"], 
                metrics["confidence_score"],
                min(len(state.recommendations) / 10, 1.0)  # Result count factor
            ]
            metrics["overall_score"] = sum(c for c in components if c > 0) / len([c for c in components if c > 0])
        
        # Quality issues
        if metrics["overall_score"] < 0.5:
            metrics["issues"].append("Low overall recommendation quality")
        
        if len(state.recommendations) < 5:
            metrics["issues"].append("Limited number of recommendations")
        
        if metrics["confidence_score"] < 0.6:
            metrics["issues"].append("Low confidence in intent extraction")
        
        return metrics
    
    def _build_response(self, state: WeldingRecommendationState, execution_time_ms: float) -> RecommendationResponse:
        """Build final recommendation response"""
        
        # Convert recommendation dicts back to items
        items = []
        for rec_dict in state.recommendations:
            try:
                items.append(RecommendationItem(**rec_dict))
            except Exception as e:
                logger.warning(f"Error converting recommendation item: {e}")
                continue
        
        # Extract intent and quality metrics
        intent = state.intent_state.extracted_intent
        quality_metrics = state.metadata.get("quality_assessment", {})
        
        # Determine if clarification is needed
        clarification_needed = (
            quality_metrics.get("overall_score", 0.0) < 0.5 or
            len(items) < 3 or
            (intent and intent.confidence < 0.6)
        )
        
        # Generate suggestions
        suggestions = []
        if clarification_needed:
            suggestions = self._generate_improvement_suggestions(state)
        
        # Build response
        response = RecommendationResponse(
            items=items,
            total_found=len(items),
            original_query=state.user_query,
            extracted_intent=intent,
            query_strategy_used=state.query_state.primary_query.query_type if state.query_state.primary_query else None,
            confidence=quality_metrics.get("confidence_score", 0.0),
            coverage=quality_metrics.get("coverage_score", 0.0),
            diversity=quality_metrics.get("diversity_score", 0.0),
            execution_time_ms=execution_time_ms,
            agent_workflow_id=state.session_id,
            clarification_needed=clarification_needed,
            suggested_questions=state.intent_state.clarification_questions,
            refinement_suggestions=suggestions
        )
        
        return response
    
    def _generate_improvement_suggestions(self, state: WeldingRecommendationState) -> List[str]:
        """Generate suggestions for improving recommendations"""
        
        suggestions = []
        intent = state.intent_state.extracted_intent
        
        if not intent:
            suggestions.append("Please provide more specific welding requirements")
            return suggestions
        
        # Suggest missing information
        if not intent.welding_process:
            suggestions.append("Specify the welding process (MIG, TIG, Stick, etc.)")
        
        if not intent.material:
            suggestions.append("Indicate the material type (steel, aluminum, stainless steel, etc.)")
        
        if not intent.power_watts and not intent.current_amps:
            suggestions.append("Provide power requirements (watts or amperage)")
        
        if not intent.thickness_mm:
            suggestions.append("Specify material thickness")
        
        if not intent.industry and not intent.application:
            suggestions.append("Describe the intended application or industry")
        
        # Suggest refinements based on results
        if len(state.recommendations) > 15:
            suggestions.append("Consider adding more specific requirements to narrow results")
        elif len(state.recommendations) < 3:
            suggestions.append("Consider broadening requirements or try alternative search terms")
        
        return suggestions[:3]  # Limit to top 3 suggestions


def create_welding_graph(neo4j_repo: Neo4jRepository) -> WeldingRecommendationGraph:
    """
    Factory function to create a welding recommendation graph.
    
    Args:
        neo4j_repo: Neo4j repository instance
        
    Returns:
        Configured WeldingRecommendationGraph instance
    """
    
    return WeldingRecommendationGraph(neo4j_repo)