"""
Simplified Intent Extraction Agent for 2-Agent Architecture
Converts natural language queries into structured welding requirements
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

# Import from existing models
from .state_models import WeldingProcess, Material, Industry, ExtractedIntent
from ..core.config_loader import get_config_loader

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SimpleWeldingIntent:
    """Simplified welding intent for 2-agent system"""
    # Core parameters
    processes: List[str] = field(default_factory=list)
    material: Optional[str] = None
    power_watts: Optional[int] = None
    current_amps: Optional[int] = None
    voltage: Optional[int] = None
    thickness_mm: Optional[float] = None
    
    # Context
    environment: Optional[str] = None
    application: Optional[str] = None
    industry: Optional[str] = None
    
    # Quality metrics
    confidence: float = 0.0
    completeness: float = 0.0
    missing_params: List[str] = field(default_factory=list)
    
    def is_sufficient_for_package(self) -> bool:
        """Determine if we have enough info to form a package"""
        return (bool(self.processes) and 
                (self.material or self.application or self.industry) and
                self.confidence > 0.6)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility"""
        return {
            "process": self.processes,
            "material": self.material,
            "current": self.current_amps,
            "voltage": self.voltage,
            "thickness": self.thickness_mm,
            "environment": self.environment,
            "application": self.application,
            "industry": self.industry,
            "confidence": self.confidence,
            "completeness": self.completeness,
            "missing_params": self.missing_params
        }


class SimpleIntentAgent:
    """
    Simplified Intent Extraction Agent for the 2-agent architecture.
    
    Focuses on robust LLM integration with proper JSON parsing
    and confidence scoring for welding requirements extraction.
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.2):
        """Initialize the simplified intent extraction agent"""
        
        self.model = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Load configuration
        self.config_loader = get_config_loader()
        
        # Create the extraction prompt
        self._create_extraction_prompt()
        
    def _create_extraction_prompt(self):
        """Create the intent extraction prompt with emphasis on clean JSON output"""
        
        # Get lists from configuration
        welding_processes = self.config_loader.get_all_welding_processes()
        materials = self.config_loader.get_materials()
        industries = self.config_loader.get_industries()
        
        self.system_prompt = f"""You are an expert welding engineer with 20+ years of experience. 
Extract welding requirements from user queries and return ONLY a valid JSON object.

CRITICAL: Return ONLY valid JSON. No markdown blocks, no explanations, no extra text.

WELDING PROCESSES: {', '.join(welding_processes)}
MATERIALS: {', '.join(materials)}
INDUSTRIES: {', '.join(industries)}

Example output:
{{
    "processes": ["MIG"],
    "material": "aluminum",
    "current_amps": 150,
    "power_watts": 3000,
    "thickness_mm": 3.0,
    "environment": "indoor",
    "application": "automotive",
    "industry": "automotive", 
    "confidence": 0.85,
    "completeness": 0.7,
    "missing_params": ["voltage"]
}}

RULES:
1. processes: Always array, even for single process
2. confidence: 0.0-1.0 based on information clarity
3. completeness: 0.0-1.0 based on parameter coverage
4. missing_params: List critical missing information
5. Use null for unknown values, not empty strings"""

    def extract_clean_json(self, llm_response: str) -> Dict[str, Any]:
        """
        Safely extract JSON from LLM response, handling markdown blocks and formatting issues
        """
        try:
            # Remove markdown code blocks
            cleaned = re.sub(r'```(?:json)?\n?', '', llm_response)
            cleaned = re.sub(r'```\n?', '', cleaned)
            
            # Remove extra whitespace and newlines
            cleaned = cleaned.strip()
            
            # Find JSON object boundaries
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            
            if not json_match:
                raise ValueError(f"No JSON object found in response: {llm_response[:200]}...")
            
            json_str = json_match.group(0)
            
            # First attempt
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common issues
                # Remove trailing commas
                fixed_json = re.sub(r',(\s*[}\]])', r'\1', json_str)
                # Fix unquoted keys
                fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)
                return json.loads(fixed_json)
                
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {llm_response}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    async def extract_intent(self, user_query: str, context: Dict[str, Any] = None) -> SimpleWeldingIntent:
        """
        Extract welding intent from natural language query
        
        Args:
            user_query: User's natural language input
            context: Optional context from previous interactions
            
        Returns:
            SimpleWeldingIntent with extracted requirements
        """
        try:
            logger.info(f"Extracting intent from query: {user_query[:100]}...")
            
            # Format context for prompt
            context_str = ""
            if context:
                context_str = f"Previous context: {json.dumps(context, indent=2)}"
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
Extract welding requirements from this query:

Query: "{user_query}"

{context_str}

Return only valid JSON:""")
            ]
            
            # Get LLM response
            response = await self.model.ainvoke(messages)
            response_text = response.content
            
            logger.debug(f"LLM response: {response_text}")
            
            # Parse the JSON response
            parsed_data = self.extract_clean_json(response_text)
            
            # Create SimpleWeldingIntent from parsed data
            intent = SimpleWeldingIntent(
                processes=parsed_data.get("processes", []),
                material=parsed_data.get("material"),
                power_watts=parsed_data.get("power_watts"),
                current_amps=parsed_data.get("current_amps"),
                voltage=parsed_data.get("voltage"),
                thickness_mm=parsed_data.get("thickness_mm"),
                environment=parsed_data.get("environment"),
                application=parsed_data.get("application"),
                industry=parsed_data.get("industry"),
                confidence=parsed_data.get("confidence", 0.0),
                completeness=parsed_data.get("completeness", 0.0),
                missing_params=parsed_data.get("missing_params", [])
            )
            
            logger.info(f"Intent extraction completed with confidence: {intent.confidence:.2f}")
            
            return intent
            
        except Exception as e:
            logger.error(f"Error in intent extraction: {e}")
            
            # Return fallback intent with low confidence
            return SimpleWeldingIntent(
                confidence=0.1,
                completeness=0.1,
                missing_params=["Unable to parse query"]
            )

    def generate_clarification_questions(self, intent: SimpleWeldingIntent) -> List[str]:
        """Generate clarification questions for incomplete intent"""
        
        questions = []
        
        if not intent.processes:
            questions.append("What welding process do you need? (MIG, TIG, Stick, etc.)")
        
        if not intent.material and not intent.industry:
            questions.append("What material will you be welding? (steel, aluminum, stainless steel, etc.)")
        
        if not intent.current_amps and not intent.power_watts:
            questions.append("What power requirements do you have? (amps or watts)")
        
        if not intent.thickness_mm:
            questions.append("What thickness material will you be welding? (in mm or inches)")
        
        if not intent.application and not intent.industry:
            questions.append("What is the intended application? (automotive, construction, fabrication, etc.)")
        
        # Add specific missing parameters
        for param in intent.missing_params:
            if param == "voltage":
                questions.append("What voltage requirement do you have? (110V, 220V, 480V)")
            elif param == "environment":
                questions.append("Where will you be welding? (indoor, outdoor, marine, etc.)")
        
        return questions[:3]  # Limit to top 3 questions