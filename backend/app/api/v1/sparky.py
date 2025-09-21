"""
Sparky AI Chatbot API Endpoints - Phase 2 Implementation
Bharath's LLM-Powered Conversational Interface

Provides REST API endpoints for Sparky AI assistant with:
1. Natural language processing for welding requirements
2. Multilingual conversation support
3. Conversation context and memory management
4. Integration with Phase 1 recommendation engine
5. Langsmith observability and tracing
"""

import logging
import time
from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from ...database.repositories import Neo4jRepository, get_neo4j_repository
from ...services.sparky_service import get_sparky_service, SparkyService
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# REQUEST MODELS
# =============================================================================

class SparkyConversationRequest(BaseModel):
    """Request model for Sparky conversation"""
    message: str = Field(..., description="User's message to Sparky", min_length=1, max_length=2000)
    user_id: Optional[str] = Field(default="anonymous", description="User identifier for conversation context")
    session_id: Optional[str] = Field(default=None, description="Session identifier (auto-generated if not provided)")
    language: str = Field(default="en", description="User's preferred language (en, es, fr, de)")


class SparkyContextRequest(BaseModel):
    """Request model for conversation context management"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences to update")


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class WeldingRequirement(BaseModel):
    """Extracted welding requirements"""
    process: List[str]
    material: Optional[str] = None
    current: Optional[int] = None
    voltage: Optional[int] = None
    thickness: Optional[float] = None
    environment: Optional[str] = None
    application: Optional[str] = None


class SparkyPackageRecommendation(BaseModel):
    """Welding package recommendation from Sparky"""
    package_id: str
    powersource: Dict[str, Any]
    feeder: Optional[Dict[str, Any]] = None
    cooler: Optional[Dict[str, Any]] = None
    torch: Optional[Dict[str, Any]] = None
    accessories: List[Dict[str, Any]] = []
    total_price: Optional[float] = None
    compatibility_confidence: float
    recommendation_reason: str
    sales_evidence: str


class SparkyConversationResponse(BaseModel):
    """Response model for Sparky conversation"""
    response: str = Field(..., description="Sparky's response message")
    requirements: Optional[WeldingRequirement] = Field(None, description="Extracted welding requirements")
    packages: List[SparkyPackageRecommendation] = Field(default=[], description="Recommended packages")
    conversation_id: str = Field(..., description="Conversation identifier")
    language: str = Field(..., description="Response language")
    confidence: float = Field(..., description="Intent extraction confidence score")
    response_time_ms: int = Field(..., description="Response time in milliseconds")


class ConversationHistory(BaseModel):
    """Conversation history entry"""
    sender: str
    content: str
    timestamp: str


class SparkyContextResponse(BaseModel):
    """Response model for conversation context"""
    user_id: str
    session_id: str
    language: str
    conversation_history: List[ConversationHistory]
    preferences: Dict[str, Any]
    active_requirements: Optional[WeldingRequirement] = None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=SparkyConversationResponse, summary="Chat with Sparky AI")
async def chat_with_sparky(
    request: SparkyConversationRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository),
    accept_language: Optional[str] = Header(None)
) -> SparkyConversationResponse:
    """
    Chat with Sparky AI assistant for welding equipment recommendations.
    
    **Phase 2 Features:**
    - Natural language understanding using LLM
    - Multilingual support (English, Spanish, French, German)
    - Conversation context and memory
    - Welding domain expertise
    - Integration with Phase 1 recommendation engine
    - Langsmith tracing for observability
    
    **Example Usage:**
    ```json
    {
        "message": "I need MIG welding for aluminum, 300 amps",
        "language": "en"
    }
    ```
    
    **Multilingual Example:**
    ```json
    {
        "message": "Necesito soldadura MIG para aluminio, 300 amperios",
        "language": "es"
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Auto-detect language from header if not specified
        if not request.language and accept_language:
            detected_lang = accept_language.split(',')[0].split('-')[0].lower()
            if detected_lang in ['en', 'es', 'fr', 'de']:
                request.language = detected_lang
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())
        
        # Get Sparky service
        sparky_service = get_sparky_service(neo4j_repo)
        
        # Process conversation with LLM
        result = await sparky_service.process_conversation(
            user_message=request.message,
            user_id=request.user_id,
            session_id=session_id,
            language=request.language
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert requirements format
        requirements = None
        if result.get("requirements"):
            req_data = result["requirements"]
            requirements = WeldingRequirement(
                process=req_data.get("process", []),
                material=req_data.get("material"),
                current=req_data.get("current"),
                voltage=req_data.get("voltage"),
                thickness=req_data.get("thickness"),
                environment=req_data.get("environment"),
                application=req_data.get("application")
            )
        
        # Convert packages format
        packages = []
        for pkg in result.get("packages", []):
            packages.append(SparkyPackageRecommendation(
                package_id=pkg.get("package_id", ""),
                powersource=pkg.get("powersource", {}),
                feeder=pkg.get("feeder"),
                cooler=pkg.get("cooler"),
                torch=pkg.get("torch"),
                accessories=pkg.get("accessories", []),
                total_price=pkg.get("total_price"),
                compatibility_confidence=pkg.get("compatibility_confidence", 0.0),
                recommendation_reason=pkg.get("recommendation_reason", ""),
                sales_evidence=pkg.get("sales_evidence", "")
            ))
        
        response = SparkyConversationResponse(
            response=result["response"],
            requirements=requirements,
            packages=packages,
            conversation_id=result["conversation_id"],
            language=result["language"],
            confidence=result["confidence"],
            response_time_ms=response_time_ms
        )
        
        logger.info(f"Sparky chat processed: user={request.user_id}, "
                   f"session={session_id}, language={request.language}, "
                   f"confidence={result['confidence']:.2f}, time={response_time_ms}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Sparky chat: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Sparky chat processing failed",
                "message": "I'm having trouble right now. Please try again in a moment.",
                "error_code": "SPARKY_CHAT_ERROR"
            }
        )


@router.get("/context/{user_id}/{session_id}", response_model=SparkyContextResponse, 
           summary="Get conversation context")
async def get_conversation_context(
    user_id: str,
    session_id: str,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> SparkyContextResponse:
    """
    Get conversation context and history for a user session.
    
    Useful for:
    - Debugging conversation flow
    - Analytics and user behavior analysis
    - Conversation recovery after interruption
    """
    try:
        sparky_service = get_sparky_service(neo4j_repo)
        context = await sparky_service.get_conversation_context(user_id, session_id)
        
        # Convert conversation history
        history = []
        for msg in context.conversation_history:
            history.append(ConversationHistory(
                sender=msg["sender"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            ))
        
        # Convert active requirements
        active_requirements = None
        if context.extracted_requirements:
            req = context.extracted_requirements
            active_requirements = WeldingRequirement(
                process=[p.value for p in req.processes],
                material=req.material.value if req.material else None,
                current=req.current_amps,
                voltage=req.voltage,
                thickness=req.thickness_mm,
                environment=req.environment,
                application=req.application
            )
        
        return SparkyContextResponse(
            user_id=context.user_id,
            session_id=context.session_id,
            language=context.language,
            conversation_history=history,
            preferences=context.user_preferences,
            active_requirements=active_requirements
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve conversation context",
                "error_code": "CONTEXT_RETRIEVAL_ERROR"
            }
        )


@router.post("/context/{user_id}/{session_id}/preferences", summary="Update user preferences")
async def update_user_preferences(
    user_id: str,
    session_id: str,
    request: SparkyContextRequest,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> Dict[str, str]:
    """
    Update user preferences for personalized recommendations.
    
    **Example preferences:**
    ```json
    {
        "preferences": {
            "preferred_brands": ["ESAB", "Lincoln"],
            "typical_applications": ["automotive", "shipyard"],
            "experience_level": "expert",
            "budget_range": "premium",
            "preferred_processes": ["MIG", "TIG"]
        }
    }
    ```
    """
    try:
        sparky_service = get_sparky_service(neo4j_repo)
        context = await sparky_service.get_conversation_context(user_id, session_id)
        
        if request.preferences:
            context.user_preferences.update(request.preferences)
            logger.info(f"Updated preferences for user {user_id}, session {session_id}")
        
        return {"status": "success", "message": "Preferences updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to update user preferences",
                "error_code": "PREFERENCE_UPDATE_ERROR"
            }
        )


@router.delete("/context/{user_id}/{session_id}", summary="Clear conversation context")
async def clear_conversation_context(
    user_id: str,
    session_id: str,
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> Dict[str, str]:
    """
    Clear conversation context and history for a user session.
    
    Useful for:
    - Starting fresh conversations
    - Privacy compliance (user data deletion)
    - Debugging and testing
    """
    try:
        sparky_service = get_sparky_service(neo4j_repo)
        context_key = f"{user_id}:{session_id}"
        
        if context_key in sparky_service.conversations:
            del sparky_service.conversations[context_key]
            logger.info(f"Cleared conversation context for user {user_id}, session {session_id}")
        
        return {"status": "success", "message": "Conversation context cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing conversation context: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to clear conversation context",
                "error_code": "CONTEXT_CLEAR_ERROR"
            }
        )


@router.get("/languages", summary="Get supported languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages for Sparky AI.
    
    Returns language codes, names, and status information.
    """
    return {
        "supported_languages": [
            {"code": "en", "name": "English", "status": "fully_supported"},
            {"code": "es", "name": "Español", "status": "fully_supported"},
            {"code": "fr", "name": "Français", "status": "fully_supported"},
            {"code": "de", "name": "Deutsch", "status": "fully_supported"}
        ],
        "default_language": "en",
        "auto_detection": True,
        "fallback_language": "en"
    }


@router.get("/status", summary="Get Sparky service status")
async def get_sparky_status(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> Dict[str, Any]:
    """
    Get Sparky AI service status and health information.
    
    Includes LLM connectivity, Langsmith tracing, and conversation statistics.
    """
    try:
        sparky_service = get_sparky_service(neo4j_repo)
        
        # Check LLM connectivity
        llm_status = "healthy"
        langsmith_status = "disabled"
        
        try:
            # Quick LLM test
            test_response = await sparky_service.llm.ainvoke([HumanMessage(content="test")])
            llm_status = "healthy" if test_response else "unhealthy"
        except Exception:
            llm_status = "unhealthy"
        
        if sparky_service.tracer:
            langsmith_status = "enabled"
        
        return {
            "service_status": "healthy",
            "llm_status": llm_status,
            "langsmith_tracing": langsmith_status,
            "supported_languages": ["en", "es", "fr", "de"],
            "active_conversations": len(sparky_service.conversations),
            "welding_expertise_loaded": bool(sparky_service.welding_expertise),
            "phase": "Phase 2 - LLM Intent Translation",
            "version": "2.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting Sparky status: {e}")
        return {
            "service_status": "unhealthy",
            "error": str(e),
            "phase": "Phase 2 - LLM Intent Translation",
            "version": "2.0.0"
        }