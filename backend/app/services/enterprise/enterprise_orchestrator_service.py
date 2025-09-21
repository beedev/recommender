"""
Enterprise Orchestrator Service - 3-Agent Agentic Architecture
Coordinates Intelligent Intent Processor, Smart Neo4j Recommender, and Multilingual Response Generator
"""

import time
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import Depends

from langgraph.graph import StateGraph, START, END
from langsmith import Client

from .enhanced_state_models import (
    EnterpriseWorkflowState, 
    UserContext, 
    EnhancedProcessedIntent,
    ScoredRecommendations,
    EnterpriseRecommendationResponse,
    ExpertiseMode,
    LanguageCode
)
from .intelligent_intent_service import IntelligentIntentService
from .smart_neo4j_service import SmartNeo4jService  
from .multilingual_response_service import MultilingualResponseService
from .enterprise_observability_service import EnterpriseObservabilityService

from ...database.repositories import Neo4jRepository, get_neo4j_repository
from ...core.config import settings

logger = logging.getLogger(__name__)


class EnterpriseOrchestratorService:
    """
    Enterprise-grade orchestrator coordinating 3 specialized agents:
    - Agent 1: Intelligent Intent Processor (multilingual + auto-mode detection)
    - Agent 2: Smart Neo4j Recommender (graph algorithms + Trinity formation)  
    - Agent 3: Multilingual Response Generator (enterprise formatting + explanations)
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        """Initialize enterprise orchestrator with 3-agent architecture"""
        
        self.neo4j_repo = neo4j_repo
        
        # Initialize the 3 enterprise agents
        self.agent_1 = IntelligentIntentService()
        self.agent_2 = SmartNeo4jService(neo4j_repo)
        self.agent_3 = MultilingualResponseService()
        
        # Enterprise observability
        self.observability = EnterpriseObservabilityService()
        
        # Initialize LangSmith for enterprise tracing
        self.langsmith_client = None
        if settings.LANGSMITH_API_KEY:
            try:
                self.langsmith_client = Client(api_key=settings.LANGSMITH_API_KEY)
                import os
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
                os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or "welding-recommender-enterprise"
                logger.info("LangSmith enterprise tracing enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith: {e}")
        
        # Create enterprise workflow
        self.workflow = self._create_enterprise_workflow()
        
        logger.info("Enterprise 3-Agent Orchestrator initialized successfully")
    
    def _create_enterprise_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for enterprise 3-agent system"""
        
        workflow = StateGraph(EnterpriseWorkflowState)
        
        # Add the 3 agent nodes
        workflow.add_node("intelligent_intent_processor", self._agent_1_intent_processing)
        workflow.add_node("smart_neo4j_recommender", self._agent_2_neo4j_recommendations)
        workflow.add_node("multilingual_response_generator", self._agent_3_response_generation)
        
        # Add error handling and fallback nodes
        workflow.add_node("handle_intent_fallback", self._handle_intent_fallback)
        workflow.add_node("handle_neo4j_fallback", self._handle_neo4j_fallback)
        workflow.add_node("generate_error_response", self._generate_error_response)
        
        # Define linear workflow with conditional fallbacks
        workflow.add_edge(START, "intelligent_intent_processor")
        
        # Agent 1 → Agent 2 (with fallback handling)
        workflow.add_conditional_edges(
            "intelligent_intent_processor",
            self._should_fallback_intent,
            {
                "proceed": "smart_neo4j_recommender",
                "fallback": "handle_intent_fallback"
            }
        )
        
        # Agent 2 → Agent 3 (with fallback handling)  
        workflow.add_conditional_edges(
            "smart_neo4j_recommender",
            self._should_fallback_neo4j,
            {
                "proceed": "multilingual_response_generator",
                "fallback": "handle_neo4j_fallback"
            }
        )
        
        # Normal completion
        workflow.add_edge("multilingual_response_generator", END)
        
        # Fallback paths
        workflow.add_edge("handle_intent_fallback", "smart_neo4j_recommender")
        workflow.add_edge("handle_neo4j_fallback", "multilingual_response_generator")
        workflow.add_edge("generate_error_response", END)
        
        return workflow.compile()
    
    async def _agent_1_intent_processing(self, state: EnterpriseWorkflowState) -> EnterpriseWorkflowState:
        """Agent 1: Intelligent Intent Processing with auto-mode detection"""
        
        agent_start_time = time.time()
        trace_id = state["trace_id"]
        
        try:
            logger.info(f"[Agent 1 - Intent] Processing query: {state['user_query'][:100]}... (trace: {trace_id})")
            
            # Start agent observability tracking
            self.observability.record_agent_start(trace_id, "intelligent_intent_processor")
            
            # Process query with Agent 1
            processed_intent = await self.agent_1.process_query(
                query=state['user_query'],
                user_context=state["user_context"],
                trace_id=trace_id
            )
            
            # Update state with Agent 1 results
            state["processed_intent"] = processed_intent
            state["intent_processing_time_ms"] = (time.time() - agent_start_time) * 1000
            state["current_agent"] = "smart_neo4j_recommender"
            
            # Record success metrics
            self.observability.record_agent_success(
                trace_id, 
                "intelligent_intent_processor",
                state["intent_processing_time_ms"],
                {
                    "language_detected": processed_intent.detected_language.value,
                    "expertise_mode": processed_intent.expertise_mode.value,
                    "confidence": processed_intent.confidence,
                    "mode_detection_confidence": processed_intent.mode_detection_confidence
                }
            )
            
            logger.info(f"[Agent 1 - Intent] Completed - Language: {processed_intent.detected_language.value}, Mode: {processed_intent.expertise_mode.value}, Confidence: {processed_intent.confidence:.2f}")
            
        except Exception as e:
            processing_time = (time.time() - agent_start_time) * 1000
            logger.error(f"[Agent 1 - Intent] Error: {e}")
            
            # Record failure
            self.observability.record_agent_error(trace_id, "intelligent_intent_processor", str(e), processing_time)
            
            state["errors"].append(f"Intent processing failed: {e}")
            state["requires_fallback"] = True
            state["intent_processing_time_ms"] = processing_time
        
        return state
    
    async def _agent_2_neo4j_recommendations(self, state: EnterpriseWorkflowState) -> EnterpriseWorkflowState:
        """Agent 2: Smart Neo4j Recommendations with graph algorithms"""
        
        agent_start_time = time.time()
        trace_id = state["trace_id"]
        
        try:
            if not state["processed_intent"]:
                raise ValueError("No processed intent available from Agent 1")
            
            expertise_mode = state["processed_intent"].expertise_mode.value
            logger.info(f"[Agent 2 - Neo4j] Generating recommendations for {expertise_mode} mode (trace: {trace_id})")
            
            # Start agent observability tracking
            self.observability.record_agent_start(trace_id, "smart_neo4j_recommender")
            
            # Generate recommendations with Agent 2
            scored_recommendations = await self.agent_2.generate_recommendations(
                processed_intent=state["processed_intent"],
                trace_id=trace_id
            )
            
            # Update state with Agent 2 results
            state["scored_recommendations"] = scored_recommendations
            state["neo4j_processing_time_ms"] = (time.time() - agent_start_time) * 1000
            state["current_agent"] = "multilingual_response_generator"
            
            # Check if fallback is needed due to empty results
            if len(scored_recommendations.packages) == 0:
                logger.warning(f"[Fallback] Neo4j processing found 0 packages, triggering fallback")
                state["requires_fallback"] = True
            
            # Record success metrics
            self.observability.record_agent_success(
                trace_id,
                "smart_neo4j_recommender", 
                state["neo4j_processing_time_ms"],
                {
                    "packages_found": len(scored_recommendations.packages),
                    "trinity_formation_rate": scored_recommendations.trinity_formation_rate,
                    "search_strategy": scored_recommendations.search_metadata.strategy.value,
                    "algorithms_used": [alg.value for alg in scored_recommendations.algorithms_used],
                    "neo4j_queries": scored_recommendations.neo4j_queries_executed
                }
            )
            
            logger.info(f"[Agent 2 - Neo4j] Completed - {len(scored_recommendations.packages)} packages, Trinity rate: {scored_recommendations.trinity_formation_rate:.2f}")
            
        except Exception as e:
            processing_time = (time.time() - agent_start_time) * 1000
            logger.error(f"[Agent 2 - Neo4j] Error: {e}")
            
            # Record failure
            self.observability.record_agent_error(trace_id, "smart_neo4j_recommender", str(e), processing_time)
            
            state["errors"].append(f"Neo4j recommendation generation failed: {e}")
            state["requires_fallback"] = True
            state["neo4j_processing_time_ms"] = processing_time
        
        return state
    
    async def _agent_3_response_generation(self, state: EnterpriseWorkflowState) -> EnterpriseWorkflowState:
        """Agent 3: Multilingual Response Generation with enterprise formatting"""
        
        agent_start_time = time.time()
        trace_id = state["trace_id"]
        
        try:
            if not state["scored_recommendations"] or not state["processed_intent"]:
                raise ValueError("Missing recommendations or intent from previous agents")
            
            detected_language = state["processed_intent"].detected_language.value
            expertise_mode = state["processed_intent"].expertise_mode.value
            logger.info(f"[Agent 3 - Response] Generating {detected_language} response for {expertise_mode} mode (trace: {trace_id})")
            
            # Start agent observability tracking
            self.observability.record_agent_start(trace_id, "multilingual_response_generator")
            
            # Generate final response with Agent 3
            final_response = await self.agent_3.generate_response(
                recommendations=state["scored_recommendations"],
                original_intent=state["processed_intent"],
                trace_id=trace_id
            )
            
            # Update state with Agent 3 results
            state["final_response"] = final_response
            state["response_generation_time_ms"] = (time.time() - agent_start_time) * 1000
            state["workflow_complete"] = True
            
            # Calculate total execution time
            state["total_execution_time_ms"] = (time.time() - state["start_time"]) * 1000
            
            # Record success metrics
            self.observability.record_agent_success(
                trace_id,
                "multilingual_response_generator",
                state["response_generation_time_ms"],
                {
                    "response_language": final_response.formatted_response.response_language.value,
                    "explanation_level": final_response.formatted_response.explanation_level.value,
                    "overall_confidence": final_response.overall_confidence,
                    "business_insights_count": len(final_response.business_insights),
                    "satisfaction_prediction": final_response.satisfaction_prediction
                }
            )
            
            logger.info(f"[Agent 3 - Response] Completed - Language: {final_response.formatted_response.response_language.value}, Confidence: {final_response.overall_confidence:.2f}")
            
        except Exception as e:
            processing_time = (time.time() - agent_start_time) * 1000
            logger.error(f"[Agent 3 - Response] Error: {e}")
            
            # Record failure
            self.observability.record_agent_error(trace_id, "multilingual_response_generator", str(e), processing_time)
            
            state["errors"].append(f"Response generation failed: {e}")
            state["requires_fallback"] = True
            state["response_generation_time_ms"] = processing_time
        
        return state
    
    def _should_fallback_intent(self, state: EnterpriseWorkflowState) -> str:
        """Determine if Agent 1 requires fallback handling"""
        
        if (state["requires_fallback"] or 
            not state["processed_intent"] or 
            state["processed_intent"].confidence < 0.3):
            return "fallback"
        
        return "proceed"
    
    def _should_fallback_neo4j(self, state: EnterpriseWorkflowState) -> str:
        """Determine if Agent 2 requires fallback handling"""
        
        if (state["requires_fallback"] or 
            not state["scored_recommendations"] or 
            len(state["scored_recommendations"].packages) == 0):
            return "fallback"
        
        return "proceed"
    
    async def _handle_intent_fallback(self, state: EnterpriseWorkflowState) -> EnterpriseWorkflowState:
        """Handle Agent 1 fallback with simplified intent processing"""
        
        logger.warning(f"[Fallback] Intent processing fallback triggered")
        
        try:
            # Create basic intent with fallback values
            if not state["processed_intent"]:
                from ...agents.simple_intent_agent import SimpleIntentAgent
                from .enhanced_state_models import EnhancedProcessedIntent
                
                # Use existing simple agent as fallback
                simple_agent = SimpleIntentAgent()
                basic_intent = await simple_agent.extract_intent(state['user_query'], {})
                
                # Convert to enhanced format with minimal enhancement
                state["processed_intent"] = EnhancedProcessedIntent.from_extracted_intent(
                    basic_intent,
                    original_query=state['user_query'],
                    processed_query=state['user_query'],
                    detected_language=LanguageCode.EN,
                    expertise_mode=ExpertiseMode.HYBRID,
                    trace_id=state["trace_id"]
                )
            
            state["warnings"].append("Used fallback intent processing")
            
        except Exception as e:
            logger.error(f"[Fallback] Intent fallback failed: {e}")
            state["errors"].append(f"Intent fallback failed: {e}")
        
        return state
    
    async def _handle_neo4j_fallback(self, state: EnterpriseWorkflowState) -> EnterpriseWorkflowState:
        """Handle Agent 2 fallback with simplified Neo4j queries"""
        
        logger.warning(f"[Fallback] Neo4j processing fallback triggered")
        
        try:
            # Use existing simple Neo4j agent as fallback
            from ...agents.simple_neo4j_agent import SimpleNeo4jAgent
            from .enhanced_state_models import ScoredRecommendations, RoutingDecision, SearchStrategy
            
            simple_neo4j = SimpleNeo4jAgent(self.neo4j_repo)
            
            # Convert enhanced intent back to simple format for fallback
            if state["processed_intent"] and state["processed_intent"].original_intent:
                simple_package = await simple_neo4j.form_welding_package(
                    state["processed_intent"].original_intent,
                    expertise_mode=state["processed_intent"].expertise_mode.value if state["processed_intent"].expertise_mode else None
                )
                
                if simple_package:
                    # Convert simple package to enterprise format
                    trinity_package = self.agent_2._convert_simple_to_trinity_package(simple_package)
                    
                    state["scored_recommendations"] = ScoredRecommendations(
                        packages=[trinity_package],
                        total_packages_found=1,
                        search_metadata=RoutingDecision(
                            strategy=SearchStrategy.HYBRID,
                            algorithms=[],
                            weights={"fallback": 1.0},
                            reasoning="Fallback to simple Neo4j agent"
                        ),
                        algorithms_used=[],
                        trace_id=state["trace_id"]
                    )
            
            state["warnings"].append("Used fallback Neo4j processing")
            
        except Exception as e:
            logger.error(f"[Fallback] Neo4j fallback failed: {e}")
            state["errors"].append(f"Neo4j fallback failed: {e}")
        
        return state
    
    async def _generate_error_response(self, state: EnterpriseWorkflowState) -> EnterpriseWorkflowState:
        """Generate error response when all fallbacks fail"""
        
        logger.error(f"[Error Response] Generating error response due to critical failures")
        
        # Create minimal error response with required fields
        from .enhanced_state_models import RoutingDecision, SearchStrategy, EnhancedProcessedIntent, ExpertiseMode
        
        error_routing = RoutingDecision(
            strategy=SearchStrategy.HYBRID,
            algorithms=[],
            weights={"error": 1.0},
            reasoning="Error occurred during processing"
        )
        
        # Use existing intent or create minimal one
        if state["processed_intent"]:
            error_intent = state["processed_intent"]
        else:
            error_intent = EnhancedProcessedIntent(
                query=state['user_query'],
                original_query=state['user_query'],
                processed_query=state['user_query'],
                detected_language=LanguageCode.EN,
                expertise_mode=ExpertiseMode.HYBRID,
                confidence=0.0,
                trace_id=state["trace_id"]
            )
        
        error_response = EnterpriseRecommendationResponse(
            packages=[],
            total_found=0,
            formatted_response=self.agent_3._create_error_response(
                state["errors"],
                error_intent.detected_language
            ),
            explanations={"error": "Unable to process request due to system errors"},
            overall_confidence=0.0,
            search_metadata=error_routing,
            original_intent=error_intent,
            trace_id=state["trace_id"],
            needs_follow_up=True,
            follow_up_questions=["Could you please rephrase your welding requirements?"]
        )
        
        state["final_response"] = error_response
        state["workflow_complete"] = True
        
        return state
    
    async def process_recommendation_request(
        self,
        query: str,
        user_context: UserContext,
        session_id: str
    ) -> EnterpriseRecommendationResponse:
        """
        Main entry point for enterprise recommendation processing
        
        Args:
            query: User's natural language welding query
            user_context: Enhanced user context with enterprise features
            session_id: Session identifier for tracking
            
        Returns:
            Complete enterprise recommendation response
        """
        
        start_time = time.time()
        trace_id = f"ent_{session_id}_{int(start_time)}"
        
        try:
            logger.info(f"[Enterprise Orchestrator] Processing request - Session: {session_id}, Trace: {trace_id}")
            
            # Start enterprise observability tracking
            self.observability.start_trace(trace_id, {
                "session_id": session_id,
                "user_id": user_context.user_id,
                "query_length": len(query),
                "preferred_language": user_context.preferred_language
            })
            
            # Initialize enterprise workflow state
            initial_state: EnterpriseWorkflowState = {
                "user_query": query,
                "user_context": user_context,
                "session_id": session_id,
                "trace_id": trace_id,
                "start_time": start_time,
                "processed_intent": None,
                "intent_processing_time_ms": 0.0,
                "scored_recommendations": None,
                "neo4j_processing_time_ms": 0.0,
                "final_response": None,
                "response_generation_time_ms": 0.0,
                "current_agent": "intent_processor",
                "workflow_complete": False,
                "requires_fallback": False,
                "errors": [],
                "warnings": [],
                "langsmith_run_id": None,
                "total_execution_time_ms": 0.0,
                "success_indicators": {},
                "performance_metrics": {}
            }
            
            # Execute enterprise 3-agent workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Validate results
            if not final_state["final_response"]:
                raise ValueError("Workflow completed without generating final response")
            
            # Complete observability tracking
            self.observability.complete_trace(
                trace_id,
                final_state["final_response"],
                final_state["total_execution_time_ms"],
                {
                    "agent_1_time_ms": final_state["intent_processing_time_ms"],
                    "agent_2_time_ms": final_state["neo4j_processing_time_ms"],
                    "agent_3_time_ms": final_state["response_generation_time_ms"],
                    "errors_count": len(final_state["errors"]),
                    "warnings_count": len(final_state["warnings"])
                }
            )
            
            total_time = final_state["total_execution_time_ms"]
            confidence = final_state["final_response"].overall_confidence
            logger.info(f"[Enterprise Orchestrator] Completed successfully - Total time: {total_time:.1f}ms, Confidence: {confidence:.2f}")
            
            return final_state["final_response"]
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"[Enterprise Orchestrator] Critical failure: {e}")
            
            # Record critical error
            self.observability.record_critical_error(trace_id, str(e), processing_time_ms)
            
            # Return minimal error response
            from .enhanced_state_models import (
                EnterpriseRecommendationResponse, 
                MultilingualResponse, 
                RoutingDecision, 
                SearchStrategy,
                EnhancedProcessedIntent,
                ExpertiseMode
            )
            
            # Create minimal routing decision for error case
            error_routing = RoutingDecision(
                strategy=SearchStrategy.HYBRID,
                algorithms=[],
                weights={"error": 1.0},
                reasoning="Error occurred during processing"
            )
            
            # Create minimal intent for error case
            error_intent = EnhancedProcessedIntent(
                query=query,
                original_query=query,
                processed_query=query,
                detected_language=LanguageCode(user_context.preferred_language or "en"),
                expertise_mode=ExpertiseMode.HYBRID,
                confidence=0.0,
                trace_id=trace_id
            )
            
            return EnterpriseRecommendationResponse(
                packages=[],
                total_found=0,
                formatted_response=MultilingualResponse(
                    title="System Error",
                    summary="We encountered an error processing your request. Please try again.",
                    detailed_explanation="Our system is temporarily unable to process welding recommendations. Please contact support if this continues.",
                    response_language=LanguageCode(user_context.preferred_language or "en")
                ),
                explanations={"error": str(e)},
                overall_confidence=0.0,
                search_metadata=error_routing,
                original_intent=error_intent,
                trace_id=trace_id,
                total_processing_time_ms=processing_time_ms,
                needs_follow_up=True,
                follow_up_questions=["Would you like to try rephrasing your welding requirements?"]
            )


# Singleton service instance
_enterprise_orchestrator_service: Optional[EnterpriseOrchestratorService] = None


async def get_enterprise_orchestrator_service(neo4j_repo: Neo4jRepository) -> EnterpriseOrchestratorService:
    """Get enterprise orchestrator service instance"""
    return EnterpriseOrchestratorService(neo4j_repo)