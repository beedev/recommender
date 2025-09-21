"""
Sparky AI Service - Phase 2 LLM Intent Translation Layer
Bharath's Implementation with Langsmith Integration

This service provides the core AI intelligence for Sparky chatbot:
1. LLM-powered intent extraction from natural language
2. Multilingual support (English, Spanish, French, German)
3. Welding domain expertise integration
4. Conversation context management
5. Langsmith tracing for observability
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langsmith import Client
import openai

from ..core.config import settings
from ..database.repositories import Neo4jRepository
from ..agents.agent_state import safe_enum_value

logger = logging.getLogger(__name__)


class WeldingProcess(Enum):
    """Supported welding processes"""
    MIG = "MIG"
    TIG = "TIG" 
    MMA = "MMA"
    STICK = "STICK"
    GMAW = "GMAW"
    GTAW = "GTAW"
    SMAW = "SMAW"


class Material(Enum):
    """Supported materials"""
    ALUMINUM = "aluminum"
    STEEL = "steel"
    STAINLESS = "stainless"
    CARBON_STEEL = "carbon_steel"
    MILD_STEEL = "mild_steel"


@dataclass
class WeldingRequirements:
    """Structured welding requirements extracted from natural language"""
    processes: List[WeldingProcess]
    material: Optional[Material] = None
    current_amps: Optional[int] = None
    voltage: Optional[int] = None
    thickness_mm: Optional[float] = None
    environment: Optional[str] = None
    application: Optional[str] = None
    certifications: List[str] = None
    safety_requirements: List[str] = None
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility"""
        return {
            "process": [p.value for p in self.processes],
            "material": self.material.value if self.material else None,
            "current": self.current_amps,
            "voltage": self.voltage,
            "thickness": self.thickness_mm,
            "environment": self.environment,
            "application": self.application
        }


@dataclass 
class ConversationContext:
    """Manages conversation state and user preferences"""
    user_id: str
    session_id: str
    language: str = "en"
    conversation_history: List[Dict[str, str]] = None
    user_preferences: Dict[str, Any] = None
    extracted_requirements: Optional[WeldingRequirements] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.user_preferences is None:
            self.user_preferences = {}


class SparkyService:
    """
    Phase 2 Sparky AI Service with LLM Intent Translation
    
    Core capabilities:
    - Natural language understanding for welding requirements
    - Multilingual conversation support
    - Welding domain expertise
    - Conversation memory and context
    - Langsmith observability
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        self.neo4j_repo = neo4j_repo
        
        # Initialize LangChain LLM
        self.llm = ChatOpenAI(
            temperature=settings.DEFAULT_TEMPERATURE,
            model="gpt-4-1106-preview",  # Latest GPT-4 Turbo
            max_tokens=settings.MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize Langsmith tracing
        self.langsmith_client = None
        self.tracer = None
        if settings.LANGSMITH_API_KEY:
            self.langsmith_client = Client(api_key=settings.LANGSMITH_API_KEY)
            # Set environment for Langsmith
            import os
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            logger.info(f"Langsmith tracing enabled for project: {settings.LANGSMITH_PROJECT}")
        
        # Welding domain knowledge
        self.welding_expertise = self._load_welding_expertise()
        
        # Active conversations
        self.conversations: Dict[str, ConversationContext] = {}
    
    def _load_welding_expertise(self) -> Dict[str, Any]:
        """Load welding domain expertise and safety guidelines"""
        return {
            "safety_guidelines": {
                "marine": ["corrosion resistance", "IP65 rating", "salt spray protection"],
                "aerospace": ["AWS D17.1 certification", "aluminum expertise", "X-ray testing"],
                "automotive": ["high-speed welding", "thin material capability", "robotic integration"],
                "shipyard": ["heavy-duty cycle", "thick plate capability", "wind resistance"]
            },
            "material_expertise": {
                "aluminum": {
                    "processes": ["TIG", "MIG"],
                    "considerations": ["AC welding", "argon shielding", "cleaning requirements"],
                    "thickness_ranges": {"TIG": "0.5-12mm", "MIG": "1-25mm"}
                },
                "stainless": {
                    "processes": ["TIG", "MIG"], 
                    "considerations": ["argon/CO2 mix", "low heat input", "distortion control"],
                    "thickness_ranges": {"TIG": "0.3-8mm", "MIG": "0.8-20mm"}
                },
                "steel": {
                    "processes": ["MIG", "MMA", "TIG"],
                    "considerations": ["CO2 shielding", "high deposition rate", "penetration"],
                    "thickness_ranges": {"MIG": "0.6-25mm", "MMA": "2-50mm", "TIG": "0.5-10mm"}
                }
            },
            "current_recommendations": {
                "thin_material": {"under_2mm": "50-120A", "2-4mm": "100-180A"},
                "medium_material": {"4-8mm": "150-250A", "8-12mm": "200-350A"},
                "thick_material": {"12-20mm": "300-450A", "over_20mm": "400-600A"}
            }
        }
    
    async def extract_welding_intent(
        self, 
        user_message: str, 
        context: ConversationContext
    ) -> Tuple[WeldingRequirements, str]:
        """
        Extract structured welding requirements from natural language using LLM
        
        Args:
            user_message: User's natural language input
            context: Conversation context and history
            
        Returns:
            Tuple of (extracted requirements, AI response message)
        """
        
        try:
            # Build conversation-aware system prompt
            system_prompt = self._build_system_prompt(context)
            
            # Create conversation messages
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history for context
            for msg in context.conversation_history[-3:]:  # Last 3 exchanges
                if msg["sender"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            # Get LLM response with Langsmith tracing
            response = await self.llm.ainvoke(
                messages,
                config={
                    "tags": ["sparky", "intent_extraction", context.language],
                    "metadata": {
                        "user_id": context.user_id,
                        "session_id": context.session_id,
                        "language": context.language
                    }
                }
            )
            
            ai_response = response.content
            
            # Parse the structured response
            requirements, response_text = self._parse_llm_response(ai_response, context)
            
            # Update conversation history
            context.conversation_history.append({
                "sender": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            context.conversation_history.append({
                "sender": "sparky", 
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Store extracted requirements in context
            if requirements.processes:
                context.extracted_requirements = requirements
            
            return requirements, response_text
            
        except Exception as e:
            logger.error(f"Error in LLM intent extraction: {e}")
            return WeldingRequirements(processes=[]), self._get_fallback_response(context.language)
    
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build context-aware system prompt with welding expertise"""
        
        base_prompt = f"""You are Sparky, an expert welding equipment assistant. You help users find the perfect welding equipment for their specific needs.

CORE CAPABILITIES:
1. Extract welding requirements from natural language
2. Provide expert welding advice and safety guidance  
3. Communicate in {context.language} (but understand all languages)
4. Remember conversation context and user preferences

WELDING EXPERTISE:
{json.dumps(self.welding_expertise, indent=2)}

RESPONSE FORMAT:
Always respond with a JSON object containing:
{{
    "requirements": {{
        "processes": ["MIG"|"TIG"|"MMA"|"STICK"],
        "material": "aluminum"|"steel"|"stainless"|null,
        "current_amps": number|null,
        "voltage": number|null, 
        "thickness_mm": number|null,
        "environment": string|null,
        "application": string|null,
        "certifications": [string],
        "safety_requirements": [string],
        "confidence_score": 0.0-1.0
    }},
    "response": "Natural language response to user",
    "follow_up_questions": ["question1", "question2"],
    "expertise_notes": ["expert insight 1", "expert insight 2"]
}}

CONVERSATION RULES:
1. If requirements are unclear, ask clarifying questions
2. Always prioritize safety considerations
3. Provide specific current/voltage recommendations based on material and thickness
4. Mention relevant certifications for specialized applications
5. Be conversational and helpful, not robotic
6. If user switches languages, respond in their language

CURRENT CONTEXT:
- User preferences: {context.user_preferences}
- Previous requirements: {context.extracted_requirements.to_dict() if context.extracted_requirements else None}
"""
        
        return base_prompt
    
    def _parse_llm_response(
        self, 
        llm_response: str, 
        context: ConversationContext
    ) -> Tuple[WeldingRequirements, str]:
        """Parse structured LLM response into requirements and response text"""
        
        try:
            # Extract JSON from response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in LLM response")
            
            json_str = llm_response[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Extract requirements
            req_data = parsed.get("requirements", {})
            requirements = WeldingRequirements(
                processes=[WeldingProcess(p) for p in req_data.get("processes", [])],
                material=Material(req_data["material"]) if req_data.get("material") else None,
                current_amps=req_data.get("current_amps"),
                voltage=req_data.get("voltage"),
                thickness_mm=req_data.get("thickness_mm"),
                environment=req_data.get("environment"),
                application=req_data.get("application"),
                certifications=req_data.get("certifications", []),
                safety_requirements=req_data.get("safety_requirements", []),
                confidence_score=req_data.get("confidence_score", 0.0)
            )
            
            # Extract response text
            response_text = parsed.get("response", "I'd be happy to help you with welding equipment recommendations!")
            
            # Add expertise notes if present
            expertise_notes = parsed.get("expertise_notes", [])
            if expertise_notes:
                response_text += "\n\n💡 **Expert Tips:**\n" + "\n".join(f"• {note}" for note in expertise_notes)
            
            return requirements, response_text
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Raw LLM response: {llm_response}")
            
            # Fallback to simple requirements
            return WeldingRequirements(processes=[]), self._get_fallback_response(context.language)
    
    def _get_fallback_response(self, language: str = "en") -> str:
        """Get fallback response when LLM fails"""
        responses = {
            "en": "I'd be happy to help you with welding equipment recommendations! Please let me know what welding process you need (MIG, TIG, or Stick) and what material you're working with.",
            "es": "¡Estaré encantado de ayudarte con recomendaciones de equipos de soldadura! Por favor, dime qué proceso de soldadura necesitas (MIG, TIG o Electrodo) y con qué material estás trabajando.",
            "fr": "Je serais ravi de vous aider avec des recommandations d'équipement de soudage! Veuillez me dire de quel processus de soudage vous avez besoin (MIG, TIG ou Électrode) et avec quel matériau vous travaillez.",
            "de": "Gerne helfe ich Ihnen bei Empfehlungen für Schweißgeräte! Bitte teilen Sie mir mit, welches Schweißverfahren Sie benötigen (MIG, WIG oder Lichtbogen) und mit welchem Material Sie arbeiten."
        }
        return responses.get(language, responses["en"])
    
    async def get_conversation_context(self, user_id: str, session_id: str, language: str = "en") -> ConversationContext:
        """Get or create conversation context for user session"""
        
        context_key = f"{user_id}:{session_id}"
        
        if context_key not in self.conversations:
            self.conversations[context_key] = ConversationContext(
                user_id=user_id,
                session_id=session_id,
                language=language
            )
        
        # Update language if changed
        self.conversations[context_key].language = language
        
        return self.conversations[context_key]
    
    async def process_conversation(
        self, 
        user_message: str,
        user_id: str = "anonymous",
        session_id: str = "default",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Main conversation processing method
        
        Args:
            user_message: User's input message
            user_id: User identifier for context
            session_id: Session identifier for context  
            language: User's preferred language
            
        Returns:
            Dictionary with response, requirements, and recommendations
        """
        
        try:
            # Get conversation context
            context = await self.get_conversation_context(user_id, session_id, language)
            
            # Extract intent using LLM
            requirements, response_text = await self.extract_welding_intent(user_message, context)
            
            # If we have valid requirements, use enhanced orchestrator for recommendations
            packages = []
            step_by_step_url = None
            if requirements.processes and any([
                requirements.material,
                requirements.current_amps,
                requirements.thickness_mm
            ]):
                try:
                    # Use new 2-agent system for package recommendations
                    from ..services.simple_orchestrator_service import get_simple_orchestrator_service
                    
                    orchestrator_service = await get_simple_orchestrator_service(self.neo4j_repo)
                    
                    # Process through 2-agent orchestrator
                    orchestrator_result = await orchestrator_service.process_request(
                        message=user_message,
                        user_id=user_id,
                        session_id=session_id,
                        language=language
                    )
                    
                    # Extract packages from orchestrator result
                    if orchestrator_result.get("packages"):
                        packages = orchestrator_result["packages"]
                    
                    # If the 2-agent system provides a better response, use it
                    if orchestrator_result.get("response") and orchestrator_result.get("confidence", 0) > 0.6:
                        response_text = orchestrator_result["response"]
                    
                    # Generate step-by-step builder URL (kept for backward compatibility)
                    step_by_step_url = "/api/v1/package-builder/powersources"
                    
                except Exception as e:
                    logger.error(f"Error getting 2-agent recommendations: {e}")
                    packages = []
            
            # Enhance response with step-by-step builder info
            response_data = {
                "response": response_text,
                "requirements": requirements.to_dict() if requirements.processes else None,
                "packages": packages,
                "conversation_id": f"{user_id}:{session_id}",
                "language": language,
                "confidence": requirements.confidence_score if requirements.processes else 0.0
            }
            
            # Add step-by-step builder URL if we have requirements
            if step_by_step_url and requirements.processes:
                response_data["step_by_step_builder"] = {
                    "available": True,
                    "url": step_by_step_url,
                    "description": "Build your package step-by-step with sales frequency insights"
                }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return {
                "response": self._get_fallback_response(language),
                "requirements": None,
                "packages": [],
                "conversation_id": f"{user_id}:{session_id}",
                "language": language,
                "confidence": 0.0
            }


# Singleton service instance
_sparky_service: Optional[SparkyService] = None

def get_sparky_service(neo4j_repo: Neo4jRepository) -> SparkyService:
    """Get singleton Sparky service instance"""
    global _sparky_service
    if _sparky_service is None:
        _sparky_service = SparkyService(neo4j_repo)
    return _sparky_service