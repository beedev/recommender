"""
Intent Extraction Agent for Welding Recommendations.

Converts natural language queries into structured welding parameters
using LangChain with OpenAI models and advanced prompt engineering.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser

# Traceable decorator (if langsmith is available)
try:
    from langsmith import traceable
except ImportError:
    # Fallback decorator if langsmith is not available
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator

from .state_models import (
    ExtractedIntent, WeldingIntentState, WeldingProcess, Material, Industry,
    ConfidenceLevel, confidence_to_level
)
from ..core.config import settings

logger = logging.getLogger(__name__)


class IntentExtractionAgent:
    """
    Agent responsible for extracting welding requirements from natural language.
    
    Capabilities:
    - Multi-language support for welding terminology
    - Context-aware parameter extraction 
    - Confidence scoring and validation
    - Ambiguity detection and clarification
    - Domain-specific entity recognition
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.2):
        """Initialize the intent extraction agent"""
        
        self.model = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=ExtractedIntent)
        
        # Welding terminology patterns
        self.process_patterns = {
            'MIG': r'\b(mig|gmaw|gas\s*metal\s*arc|wire\s*feed|semi\s*auto)\b',
            'TIG': r'\b(tig|gtaw|gas\s*tungsten\s*arc|heliarc|argon\s*arc)\b',
            'MMA': r'\b(mma|manual\s*metal\s*arc|stick|electrode|rod)\b',
            'FLUX_CORE': r'\b(flux\s*core|fcaw|flux\s*cored|self\s*shield)\b'
        }
        
        self.material_patterns = {
            'steel': r'\b(steel|carbon\s*steel|mild\s*steel|structural\s*steel)\b',
            'stainless_steel': r'\b(stainless|stainless\s*steel|ss|316|304|inox)\b', 
            'aluminum': r'\b(aluminum|aluminium|al|6061|5356|4043)\b',
            'copper': r'\b(copper|cu|brass|bronze)\b'
        }
        
        self.industry_patterns = {
            'automotive': r'\b(automotive|auto|car|vehicle|chassis)\b',
            'aerospace': r'\b(aerospace|aircraft|aviation|flight)\b',
            'marine': r'\b(marine|ship|boat|naval|maritime)\b',
            'construction': r'\b(construction|building|structural|bridge)\b'
        }
        
        # Create extraction prompt
        self._create_extraction_prompt()
        
    def _create_extraction_prompt(self):
        """Create the extraction prompt template"""
        
        system_template = """You are an expert welding engineer with 20+ years of experience in industrial welding applications. 
Your task is to extract structured welding requirements from natural language queries.

WELDING PROCESS MAPPING:
- MIG/GMAW: Wire feed, gas metal arc, semi-automatic welding
- TIG/GTAW: Tungsten electrode, gas tungsten arc, precision welding  
- MMA/STICK: Manual metal arc, electrode welding, rod welding
- FLUX_CORE: Self-shielded flux cored arc welding

MATERIAL TYPES:
- Steel: Carbon steel, mild steel, structural steel
- Stainless Steel: 304, 316, duplex, austenitic stainless
- Aluminum: 6061, 5356, 4043, aerospace alloys
- Specialty: Copper, nickel, titanium, exotic alloys

POWER REQUIREMENTS:
- Light duty: 100-200W, 50-150A
- Medium duty: 200-400W, 150-300A  
- Heavy duty: 400-800W, 300-500A
- Industrial: 800W+, 500A+

EXTRACTION RULES:
1. Always provide confidence score (0.0-1.0)
2. Extract numeric values with appropriate units
3. Identify ambiguous terms that need clarification
4. Consider industry context for parameter inference
5. Flag missing critical information

Output the extracted intent as valid JSON matching the ExtractedIntent schema.

{format_instructions}"""

        human_template = """Extract welding requirements from this query:

Query: "{user_query}"

Additional Context: {context}

Focus on:
1. Welding process(es) mentioned or implied
2. Material type and specifications  
3. Power/current/voltage requirements
4. Application context and industry
5. Similar purchase references
6. Any ambiguous terms requiring clarification

Extract requirements:"""

        self.extraction_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
    async def _llm_preprocess_domain_terms(self, query: str) -> str:
        """
        Use LLM to preprocess domain-specific welding terms before enum validation.
        Maps colloquial terms to standard enum values.
        """
        try:
            preprocessing_prompt = f"""
You are a welding expert. Normalize this query by replacing colloquial welding terms with standard terminology.

Standard welding processes: MIG, TIG, MMA, STICK, FLUX_CORE, MULTI_PROCESS, GMAW, GTAW, SMAW, FCAW, SAW, PAW

Query: "{query}"

Replace non-standard welding terms with standard ones:
- "pulse welding" → "MIG" (pulse is a MIG technique)
- "wire welding" → "MIG"
- "argon welding" → "TIG"
- "electrode welding" → "STICK"
- "rod welding" → "STICK"
- "arc welding" → "MIG" (or appropriate context-based process)

Keep all other terms unchanged. Return only the normalized query text.
"""
            
            response = await self.model.agenerate([[HumanMessage(content=preprocessing_prompt)]])
            normalized_query = response.generations[0][0].text.strip()
            
            logger.info(f"🔄 LLM domain preprocessing: '{query}' → '{normalized_query}'")
            return normalized_query
            
        except Exception as e:
            logger.warning(f"LLM preprocessing failed: {e}")
            return query  # Fallback to original

    @traceable(name="intent_extraction")
    async def extract_intent(self, state: WeldingIntentState) -> WeldingIntentState:
        """
        Extract welding intent from natural language query.
        
        Args:
            state: Current workflow state with user query
            
        Returns:
            Updated state with extracted intent
        """
        try:
            logger.info(f"Extracting intent from query: {state.user_query[:100]}...")
            
            # LLM-based domain term preprocessing (fixes enum validation issues)
            domain_preprocessed_query = await self._llm_preprocess_domain_terms(state.user_query)
            
            # Standard pre-processing (abbreviations, normalization)
            preprocessed_query = self._preprocess_query(domain_preprocessed_query)
            
            # Pattern-based pre-extraction
            pattern_results = self._extract_with_patterns(preprocessed_query)
            
            # LLM-based extraction
            llm_results = await self._extract_with_llm(
                preprocessed_query, 
                state.context,
                pattern_results
            )
            
            # Combine and validate results
            combined_intent = self._combine_extractions(pattern_results, llm_results)
            validated_intent = self._validate_intent(combined_intent, state.user_query)
            
            # Update state
            state.raw_extraction = {
                "pattern_results": pattern_results,
                "llm_results": llm_results,
                "preprocessing": {
                    "original_query": state.user_query,
                    "domain_preprocessed_query": domain_preprocessed_query,
                    "final_preprocessed_query": preprocessed_query
                }
            }
            
            state.extracted_intent = validated_intent
            state.needs_clarification = validated_intent.confidence < 0.6
            
            if state.needs_clarification:
                state.clarification_questions = self._generate_clarification_questions(validated_intent)
            
            logger.info(f"Intent extraction completed with confidence: {validated_intent.confidence:.2f}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in intent extraction: {e}")
            state.retry_count += 1
            
            if state.retry_count < state.max_retries:
                # Simplified extraction on retry
                fallback_intent = self._fallback_extraction(state.user_query)
                state.extracted_intent = fallback_intent
            else:
                # Create minimal intent with low confidence
                state.extracted_intent = ExtractedIntent(
                    confidence=0.1,
                    confidence_level=ConfidenceLevel.UNCERTAIN,
                    extraction_issues=[f"Extraction failed: {str(e)}"],
                    original_query=state.user_query
                )
            
            return state
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for better extraction"""
        
        # Normalize case
        processed = query.lower()
        
        # Expand common abbreviations
        abbreviations = {
            r'\bss\b': 'stainless steel',
            r'\bal\b': 'aluminum', 
            r'\bamps?\b': 'amperes',
            r'\bvolts?\b': 'voltage',
            r'\bw\b': 'watts',
            r'\bmm\b': 'millimeters',
            r'\bin\b': 'inches',
            r'\bga\b': 'gauge'
        }
        
        for pattern, replacement in abbreviations.items():
            processed = re.sub(pattern, replacement, processed)
        
        # Clean up whitespace
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        return processed
    
    def _extract_with_patterns(self, query: str) -> Dict[str, Any]:
        """Extract parameters using regex patterns"""
        
        results = {
            "processes": [],
            "materials": [],
            "industries": [],
            "numeric_values": {},
            "confidence": 0.0
        }
        
        # Extract welding processes
        for process, pattern in self.process_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                results["processes"].append(process)
        
        # Extract materials  
        for material, pattern in self.material_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                results["materials"].append(material)
        
        # Extract industries
        for industry, pattern in self.industry_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                results["industries"].append(industry)
        
        # Extract numeric values
        numeric_patterns = {
            'watts': r'(\d+)\s*w(?:atts?)?',
            'amps': r'(\d+)\s*a(?:mp(?:s|eres?)?)?',
            'voltage': r'(\d+)\s*v(?:olts?)?',
            'thickness': r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters?|inches?|in|ga|gauge)'
        }
        
        for param, pattern in numeric_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    results["numeric_values"][param] = value
                except ValueError:
                    continue
        
        # Calculate pattern-based confidence
        total_extractions = (
            len(results["processes"]) +
            len(results["materials"]) +
            len(results["numeric_values"]) +
            len(results["industries"])
        )
        
        results["confidence"] = min(total_extractions * 0.15, 0.8)
        
        return results
    
    async def _extract_with_llm(
        self, 
        query: str, 
        context: Dict[str, Any],
        pattern_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract parameters using LLM"""
        
        try:
            # Format the prompt
            formatted_prompt = self.extraction_prompt.format_messages(
                user_query=query,
                context=context,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response
            response = await self.model.agenerate([formatted_prompt])
            response_text = response.generations[0][0].text
            
            # Parse response
            try:
                parsed_intent = self.output_parser.parse(response_text)
                return {
                    "parsed_intent": parsed_intent.dict(),
                    "raw_response": response_text,
                    "confidence": parsed_intent.confidence
                }
            except Exception as parse_error:
                logger.warning(f"Failed to parse LLM response: {parse_error}")
                return {
                    "error": f"Parse error: {parse_error}",
                    "raw_response": response_text,
                    "confidence": 0.3
                }
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {
                "error": f"LLM error: {e}",
                "confidence": 0.2
            }
    
    def _combine_extractions(
        self, 
        pattern_results: Dict[str, Any], 
        llm_results: Dict[str, Any]
    ) -> ExtractedIntent:
        """Combine pattern and LLM extraction results"""
        
        # Start with LLM results if available
        if "parsed_intent" in llm_results:
            intent = ExtractedIntent(**llm_results["parsed_intent"])
        else:
            intent = ExtractedIntent()
        
        # Enhance with pattern results
        if pattern_results["processes"]:
            # Convert to enum values
            processes = []
            for p in pattern_results["processes"]:
                try:
                    processes.append(WeldingProcess(p))
                except ValueError:
                    continue
            
            if processes:
                intent.welding_process = processes
        
        if pattern_results["materials"] and not intent.material:
            try:
                intent.material = Material(pattern_results["materials"][0])
            except ValueError:
                pass
        
        if pattern_results["industries"] and not intent.industry:
            try:
                intent.industry = Industry(pattern_results["industries"][0])
            except ValueError:
                pass
        
        # Add numeric values from patterns if not in LLM results
        numeric_values = pattern_results["numeric_values"]
        if "watts" in numeric_values and not intent.power_watts:
            intent.power_watts = int(numeric_values["watts"])
        
        if "amps" in numeric_values and not intent.current_amps:
            intent.current_amps = int(numeric_values["amps"])
        
        if "voltage" in numeric_values and not intent.voltage:
            intent.voltage = int(numeric_values["voltage"])
        
        if "thickness" in numeric_values and not intent.thickness_mm:
            intent.thickness_mm = numeric_values["thickness"]
        
        # Combine confidence scores
        pattern_confidence = pattern_results.get("confidence", 0.0)
        llm_confidence = llm_results.get("confidence", 0.0)
        intent.confidence = (pattern_confidence + llm_confidence) / 2
        
        intent.confidence_level = confidence_to_level(intent.confidence)
        
        return intent
    
    def _validate_intent(self, intent: ExtractedIntent, original_query: str) -> ExtractedIntent:
        """Validate and clean extracted intent"""
        
        intent.original_query = original_query
        issues = []
        
        # Validate numeric ranges
        if intent.power_watts and (intent.power_watts < 50 or intent.power_watts > 50000):
            issues.append(f"Power watts {intent.power_watts} outside typical range (50-50000W)")
            
        if intent.current_amps and (intent.current_amps < 5 or intent.current_amps > 2000):
            issues.append(f"Current {intent.current_amps} outside typical range (5-2000A)")
            
        if intent.voltage and (intent.voltage < 12 or intent.voltage > 600):
            issues.append(f"Voltage {intent.voltage} outside typical range (12-600V)")
            
        if intent.thickness_mm and (intent.thickness_mm < 0.1 or intent.thickness_mm > 200):
            issues.append(f"Thickness {intent.thickness_mm}mm outside typical range (0.1-200mm)")
        
        # Check for conflicting parameters
        if intent.welding_process:
            if WeldingProcess.TIG in intent.welding_process and intent.material == Material.ALUMINUM:
                if intent.current_amps and intent.current_amps > 300:
                    issues.append("High current unusual for aluminum TIG welding")
        
        # Detect missing critical information
        if not intent.welding_process:
            issues.append("No welding process identified")
            intent.confidence *= 0.7
            
        if not intent.material and not intent.industry:
            issues.append("No material or industry context identified") 
            intent.confidence *= 0.8
        
        intent.extraction_issues = issues
        
        # Adjust confidence based on validation
        if len(issues) > 2:
            intent.confidence *= 0.6
        elif len(issues) > 0:
            intent.confidence *= 0.8
            
        intent.confidence_level = confidence_to_level(intent.confidence)
        
        return intent
    
    def _generate_clarification_questions(self, intent: ExtractedIntent) -> List[str]:
        """Generate clarification questions for ambiguous intent"""
        
        questions = []
        
        if not intent.welding_process:
            questions.append("What welding process do you need? (MIG, TIG, Stick/MMA, or Multi-process)")
        
        if not intent.material:
            questions.append("What material will you be welding? (Steel, Stainless Steel, Aluminum, etc.)")
        
        if not intent.power_watts and not intent.current_amps:
            questions.append("What power requirements do you have? (Watts or Amperage)")
        
        if not intent.thickness_mm:
            questions.append("What material thickness will you be welding? (in mm or inches)")
        
        if not intent.industry and not intent.application:
            questions.append("What is the intended application or industry? (Automotive, Construction, etc.)")
        
        if intent.ambiguous_terms:
            questions.append(f"Could you clarify what you mean by: {', '.join(intent.ambiguous_terms)}?")
        
        return questions[:3]  # Limit to top 3 questions
    
    def _fallback_extraction(self, query: str) -> ExtractedIntent:
        """Simple fallback extraction when LLM fails"""
        
        # Use only pattern matching for fallback
        pattern_results = self._extract_with_patterns(query)
        
        intent = ExtractedIntent(
            original_query=query,
            confidence=0.3,
            confidence_level=ConfidenceLevel.LOW,
            extraction_issues=["Using fallback extraction method"]
        )
        
        # Apply pattern results
        if pattern_results["processes"]:
            try:
                intent.welding_process = [WeldingProcess(p) for p in pattern_results["processes"]]
            except ValueError:
                pass
        
        if pattern_results["materials"]:
            try:
                intent.material = Material(pattern_results["materials"][0])
            except ValueError:
                pass
        
        return intent