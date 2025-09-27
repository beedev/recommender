"""
Agent 1: Intelligent Intent Service
Multilingual intent processing with automatic mode detection
No manual toggles - automatically determines expertise level and language
"""

import time
import logging
import re
import yaml
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .enhanced_state_models import (
    UserContext,
    EnhancedProcessedIntent, 
    ExpertiseMode,
    LanguageCode,
    detect_expertise_level
)
from ...agents.simple_intent_agent import SimpleIntentAgent
from ...agents.state_models import ExtractedIntent

logger = logging.getLogger(__name__)


@dataclass
class AutoModeDetector:
    """Automatically detects user expertise mode using config file"""
    
    expert_signals: List[str] = None
    guided_signals: List[str] = None
    expert_weight: float = 0.4
    guided_weight: float = 0.6
    confidence_threshold: float = 0.7
    
    def __post_init__(self):
        """Load mode detection signals from config file"""
        self._load_config()
    
    def _load_config(self):
        """Load mode detection configuration from YAML file"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "config", "mode_detection.yaml"
            )
            
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            self.expert_signals = config.get('expert_signals', [])
            self.guided_signals = config.get('guided_signals', [])
            self.expert_weight = config.get('expert_weight', 0.4)
            self.guided_weight = config.get('guided_weight', 0.6)
            self.confidence_threshold = config.get('confidence_threshold', 0.7)
            
            logger.info(f"Loaded {len(self.expert_signals)} expert signals and {len(self.guided_signals)} guided signals from config")
            
        except Exception as e:
            logger.warning(f"Failed to load mode detection config: {e}. Using fallback signals.")
            self._load_fallback_signals()
    
    def _load_fallback_signals(self):
        """Fallback signals if config file loading fails"""
        self.expert_signals = [
            "Aristo 500 ix", "Warrior 400i", "Renegade 300",
            "compatible with", "wire feeder", "GMAW", "GTAW", "amperage"
        ]
        self.guided_signals = [
            "beginner", "help me choose", "new to welding", "learning", "what do I need"
        ]
    
    def detect_user_expertise(
        self, 
        query: str, 
        user_history: List[str] = None
    ) -> ExpertiseMode:
        """
        Automatically detect user expertise level from query content
        No manual toggles or user selection required
        """
        
        query_lower = query.lower()
        
        # Count expert signals
        expert_score = sum(1 for signal in self.expert_signals 
                          if signal.lower() in query_lower)
        
        # Count guided signals  
        guided_score = sum(1 for signal in self.guided_signals
                          if signal.lower() in query_lower)
        
        # Analyze query complexity
        complexity_indicators = self._analyze_query_complexity(query)
        
        # Check user history for experience patterns
        history_expertise = self._analyze_user_history(user_history or [])
        
        # Calculate final expertise score
        total_expert_score = (
            expert_score * 0.4 +           # Technical vocabulary (40%)
            complexity_indicators * 0.3 +   # Query complexity (30%)
            history_expertise * 0.2 +       # Historical patterns (20%)
            self._analyze_specificity(query) * 0.1  # Specificity level (10%)
        )
        
        # Determine expertise mode with confidence thresholds
        if total_expert_score >= 0.7:
            logger.info(f"Expert mode detected - Score: {total_expert_score:.2f}")
            return ExpertiseMode.EXPERT
        elif guided_score >= 2 or any(signal in query_lower for signal in 
                                     ["beginner", "new to welding", "learning", "help me"]):
            logger.info(f"Guided mode detected - Guided signals: {guided_score}")
            return ExpertiseMode.GUIDED
        else:
            logger.info(f"Hybrid mode detected - Expert score: {total_expert_score:.2f}, Guided score: {guided_score}")
            return ExpertiseMode.HYBRID
    
    def _analyze_query_complexity(self, query: str) -> float:
        """Analyze technical complexity of the query"""
        
        complexity_score = 0.0
        
        # Length indicates detail level
        if len(query) > 200:
            complexity_score += 0.3
        elif len(query) > 100:
            complexity_score += 0.2
        
        # Technical numbers and specifications
        technical_patterns = [
            r'\d+\s*(amp|amps|amperage)',     # Current specifications
            r'\d+\s*(volt|volts|voltage)',    # Voltage specifications  
            r'\d+\s*(watt|watts)',            # Power specifications
            r'\d+\s*(mm|inch|inches)',        # Thickness specifications
            r'\d+\s*(cfh|scfh)',              # Gas flow specifications
            r'\d+\s*(ipm|wfs)',               # Wire feed speed
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, query.lower()):
                complexity_score += 0.1
        
        # Multiple processes or materials
        if len(re.findall(r'\b(mig|tig|stick|flux\s*core|gtaw|gmaw|smaw|fcaw)\b', query.lower())) > 1:
            complexity_score += 0.2
        
        return min(complexity_score, 1.0)
    
    def _analyze_user_history(self, user_history: List[str]) -> float:
        """Analyze user's historical queries for expertise patterns"""
        
        if not user_history:
            return 0.5  # Neutral when no history
        
        # Count expert terms across all historical queries
        total_expert_signals = 0
        total_guided_signals = 0
        
        for historical_query in user_history[-10:]:  # Last 10 queries
            query_lower = historical_query.lower()
            total_expert_signals += sum(1 for signal in self.expert_signals 
                                       if signal.lower() in query_lower)
            total_guided_signals += sum(1 for signal in self.guided_signals
                                       if signal.lower() in query_lower)
        
        # Calculate historical expertise ratio
        if total_expert_signals + total_guided_signals == 0:
            return 0.5
        
        return total_expert_signals / (total_expert_signals + total_guided_signals)
    
    def _analyze_specificity(self, query: str) -> float:
        """Analyze how specific vs. general the query is"""
        
        # Specific product mentions
        specific_patterns = [
            r'power\s*wave\s*\d+',     # PowerWave models
            r'renegade\s*\w*\d*',      # Renegade models  
            r'warrior\s*\d+',          # Warrior models
            r'aristo\s*\d+',           # Aristo models
            r'dynasty\s*\d+',          # Dynasty models
        ]
        
        specificity_score = 0.0
        
        for pattern in specific_patterns:
            if re.search(pattern, query.lower()):
                specificity_score += 0.3
        
        # Specific technical requirements
        if any(term in query.lower() for term in ["compatible", "replacement", "upgrade"]):
            specificity_score += 0.2
        
        return min(specificity_score, 1.0)


@dataclass  
class MultilingualProcessor:
    """Handles multilingual processing and translation"""
    
    # Language detection patterns (simplified for MVP)
    language_patterns: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.language_patterns is None:
            self.language_patterns = {
                "es": [
                    "soldadura", "soldador", "electrodo", "arco", "corriente", "voltaje",
                    "necesito", "busco", "quiero", "ayuda", "recomendación", "para soldar",
                    "máquina", "equipo", "acero", "aluminio", "inoxidable"
                ],
                "fr": [
                    "soudage", "soudeur", "électrode", "arc", "courant", "tension",
                    "besoin", "cherche", "veux", "aide", "recommandation", "pour souder",
                    "machine", "équipement", "acier", "aluminium", "inoxydable"
                ],
                "de": [
                    "schweißen", "schweißer", "elektrode", "lichtbogen", "strom", "spannung",
                    "brauche", "suche", "möchte", "hilfe", "empfehlung", "zum schweißen",
                    "maschine", "ausrüstung", "stahl", "aluminium", "rostfrei"
                ],
                "pt": [
                    "soldagem", "soldador", "eletrodo", "arco", "corrente", "voltagem",
                    "preciso", "procuro", "quero", "ajuda", "recomendação", "para soldar",
                    "máquina", "equipamento", "aço", "alumínio", "inoxidável"
                ],
                "it": [
                    "saldatura", "saldatore", "elettrodo", "arco", "corrente", "tensione",
                    "ho bisogno", "cerco", "voglio", "aiuto", "raccomandazione", "per saldare",
                    "macchina", "attrezzatura", "acciaio", "alluminio", "inossidabile"
                ]
            }
    
    async def detect_language(self, query: str) -> LanguageCode:
        """Detect language from query content"""
        
        query_lower = query.lower()
        language_scores = {}
        
        # Score each language based on keyword matches
        for lang_code, keywords in self.language_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                language_scores[lang_code] = score
        
        # Default to English if no clear pattern
        if not language_scores:
            return LanguageCode.EN
        
        # Return language with highest score
        detected_lang = max(language_scores, key=language_scores.get)
        logger.info(f"Language detected: {detected_lang} (score: {language_scores[detected_lang]})")
        
        return LanguageCode(detected_lang)
    
    async def translate_to_english(self, query: str, detected_language: LanguageCode) -> str:
        """Translate query to English for processing (simplified for MVP)"""
        
        if detected_language == LanguageCode.EN:
            return query
        
        # Simple translation mappings for common welding terms
        translation_maps = {
            LanguageCode.ES: {
                "soldadura": "welding",
                "soldador": "welder",
                "necesito": "I need",
                "busco": "I'm looking for", 
                "quiero": "I want",
                "para soldar": "for welding",
                "acero": "steel",
                "aluminio": "aluminum",
                "inoxidable": "stainless steel",
                "máquina": "machine",
                "equipo": "equipment"
            },
            LanguageCode.FR: {
                "soudage": "welding",
                "soudeur": "welder", 
                "besoin": "need",
                "cherche": "looking for",
                "veux": "want",
                "pour souder": "for welding",
                "acier": "steel",
                "aluminium": "aluminum",
                "inoxydable": "stainless steel",
                "machine": "machine",
                "équipement": "equipment"
            },
            LanguageCode.DE: {
                "schweißen": "welding",
                "schweißer": "welder",
                "brauche": "need", 
                "suche": "looking for",
                "möchte": "want",
                "zum schweißen": "for welding",
                "stahl": "steel",
                "aluminium": "aluminum",
                "rostfrei": "stainless steel",
                "maschine": "machine",
                "ausrüstung": "equipment"
            }
        }
        
        translated_query = query
        
        if detected_language in translation_maps:
            translation_map = translation_maps[detected_language]
            for foreign_term, english_term in translation_map.items():
                translated_query = re.sub(
                    re.escape(foreign_term), 
                    english_term, 
                    translated_query, 
                    flags=re.IGNORECASE
                )
        
        logger.info(f"Translated from {detected_language.value}: '{query}' -> '{translated_query}'")
        return translated_query


class IntelligentIntentService:
    """
    Agent 1: Intelligent Intent Processing Service
    - Automatic language detection
    - Automatic expertise mode detection  
    - Enhanced intent extraction with confidence scoring
    - Backward compatibility with existing intent agents
    """
    
    def __init__(self):
        """Initialize intelligent intent service components"""
        
        self.mode_detector = AutoModeDetector()
        self.multilingual_processor = MultilingualProcessor()
        
        # Use existing simple intent agent as foundation
        self.fallback_intent_agent = SimpleIntentAgent()
        
        logger.info("Intelligent Intent Service initialized")
    
    async def process_query(
        self,
        query: str,
        user_context: UserContext,
        trace_id: str
    ) -> EnhancedProcessedIntent:
        """
        Main processing pipeline for Agent 1
        
        Args:
            query: User's natural language query
            user_context: Enhanced user context
            trace_id: Distributed tracing identifier
            
        Returns:
            Enhanced processed intent with auto-detected features
        """
        
        start_time = time.time()
        
        try:
            logger.info(f"[Agent 1] Processing query: {query[:100]}... (trace: {trace_id})")
            
            # Step 1: Auto-detect language
            detected_language = await self.multilingual_processor.detect_language(query)
            language_confidence = 0.9  # Simplified confidence for MVP
            
            # Step 2: Translate to English if needed
            english_query = await self.multilingual_processor.translate_to_english(
                query, detected_language
            )
            
            # Step 3: Auto-detect expertise mode
            expertise_mode = self.mode_detector.detect_user_expertise(
                english_query,
                user_context.expertise_history
            )
            mode_confidence = 0.8  # Simplified confidence for MVP
            
            # Step 4: Extract welding intent using existing agent
            base_intent = await self._extract_welding_intent(
                english_query,
                expertise_mode,
                user_context
            )
            
            # Step 5: Create enhanced intent with auto-detected features
            enhanced_intent = EnhancedProcessedIntent.from_extracted_intent(
                base_intent,
                original_query=query,
                processed_query=english_query,
                detected_language=detected_language,
                expertise_mode=expertise_mode,
                mode_detection_confidence=mode_confidence,
                language_detection_confidence=language_confidence,
                trace_id=trace_id,
                processing_start_time=start_time
            )
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"[Agent 1] Completed - Language: {detected_language.value}, Mode: {expertise_mode.value}, Confidence: {enhanced_intent.confidence:.2f}, Time: {processing_time:.1f}ms")
            
            return enhanced_intent
            
        except Exception as e:
            logger.error(f"[Agent 1] Error processing query: {e}")
            
            # Create fallback enhanced intent
            try:
                fallback_intent = await self.fallback_intent_agent.extract_intent(query, {})
                return EnhancedProcessedIntent.from_extracted_intent(
                    fallback_intent,
                    original_query=query,
                    processed_query=query,
                    detected_language=LanguageCode.EN,
                    expertise_mode=ExpertiseMode.HYBRID,
                    trace_id=trace_id,
                    processing_start_time=start_time
                )
            except Exception as fallback_error:
                logger.error(f"[Agent 1] Fallback also failed: {fallback_error}")
                raise e
    
    async def _extract_welding_intent(
        self,
        english_query: str,
        expertise_mode: ExpertiseMode,
        user_context: UserContext
    ) -> ExtractedIntent:
        """
        Extract welding intent with product-aware processing
        Handles both general welding queries and product-specific compatibility queries
        """
        
        # First, check if this is a product-specific compatibility query
        product_specific_intent = await self._extract_product_specific_intent(english_query)
        
        if product_specific_intent and product_specific_intent.confidence > 0.5:
            logger.info(f"Product-specific intent detected with confidence {product_specific_intent.confidence}")
            return product_specific_intent
        
        # Fall back to general welding parameter extraction
        enhanced_context = {
            "user_id": user_context.user_id,
            "session_id": user_context.session_id,
            "expertise_mode": expertise_mode.value,
            "industry_context": user_context.industry_context,
            "organization": user_context.organization,
            "previous_queries": user_context.previous_queries[-3:] if user_context.previous_queries else []
        }
        
        # Use existing intent agent with enhanced context
        simple_intent = await self.fallback_intent_agent.extract_intent(
            user_query=english_query,
            context=enhanced_context
        )
        
        # Convert SimpleWeldingIntent to ExtractedIntent format (with LLM process validation)
        base_intent = await self._convert_simple_to_extracted_intent(simple_intent, english_query)
        
        # Enhance confidence scoring based on expertise mode
        if expertise_mode == ExpertiseMode.EXPERT:
            # Expert users likely provide more precise requirements
            base_intent.confidence = min(base_intent.confidence * 1.2, 1.0)
        elif expertise_mode == ExpertiseMode.GUIDED:
            # Guided users may need more interpretation
            base_intent.confidence = base_intent.confidence * 0.9
        
        return base_intent
    
    async def _extract_product_specific_intent(self, query: str) -> Optional[ExtractedIntent]:
        """
        Extract intent for product-specific compatibility queries
        Recognizes our actual products: Aristo 500 ix, Warrior 400i, Renegade 300
        """
        
        query_lower = query.lower()
        
        # Known products in our database (using correct enum values)
        known_products = {
            "aristo 500 ix": {"type": "power_source", "current_amps": 500, "processes": ["TIG", "MIG"]},
            "warrior 400i": {"type": "power_source", "current_amps": 400, "processes": ["MIG", "TIG"]}, 
            "renegade 300": {"type": "power_source", "current_amps": 300, "processes": ["STICK", "TIG"]}
        }
        
        # Compatible equipment types (using correct enum values)
        equipment_types = {
            "wire feeder": {"category": "feeder", "compatibility_with": ["MIG", "FLUX_CORE"]},
            "cooler": {"category": "cooler", "compatibility_with": ["TIG", "MIG"]},
            "torch": {"category": "torch", "compatibility_with": ["TIG", "MIG"]},
            "regulator": {"category": "regulator", "compatibility_with": ["TIG", "MIG"]}
        }
        
        detected_product = None
        detected_equipment = None
        detected_processes = []
        
        # Find mentioned products
        for product_name, product_info in known_products.items():
            if product_name in query_lower:
                detected_product = product_name
                detected_processes.extend(product_info["processes"])
                break
        
        # Find mentioned equipment
        for equipment_name, equipment_info in equipment_types.items():
            if equipment_name in query_lower:
                detected_equipment = equipment_name
                detected_processes.extend(equipment_info["compatibility_with"])
                break
        
        # If we found both a product and equipment, this is a compatibility query
        if detected_product and detected_equipment:
            confidence = 0.9  # High confidence for specific product compatibility queries
            
            # Create ExtractedIntent for compatibility query
            intent = ExtractedIntent(
                welding_process=list(set(detected_processes)),  # Remove duplicates
                material=None,
                power_watts=None,
                current_amps=known_products[detected_product]["current_amps"],
                voltage=None,
                thickness_mm=None,
                industry=None,
                environment=None,
                application="compatibility",
                duty_cycle=None,
                similar_to_customer=detected_product,
                similar_to_purchase=None,
                similar_to_package=None,
                confidence=confidence,
                confidence_level="high",
                extraction_issues=[],
                original_query=query,
                extracted_entities={
                    "mentioned_product": detected_product,
                    "requested_equipment": detected_equipment,
                    "compatibility_type": "product_accessory"
                },
                ambiguous_terms=[]
            )
            
            logger.info(f"Product compatibility detected: {detected_product} + {detected_equipment}")
            return intent
        
        # Check for general product mentions without specific equipment
        elif detected_product:
            confidence = 0.7  # Medium confidence for product-only queries
            
            intent = ExtractedIntent(
                welding_process=detected_processes,
                material=None,
                power_watts=None,
                current_amps=known_products[detected_product]["current_amps"],
                voltage=None,
                thickness_mm=None,
                industry=None,
                environment=None,
                application="product_inquiry",
                duty_cycle=None,
                similar_to_customer=detected_product,
                similar_to_purchase=None,
                similar_to_package=None,
                confidence=confidence,
                confidence_level="medium",
                extraction_issues=[],
                original_query=query,
                extracted_entities={
                    "mentioned_product": detected_product,
                    "query_type": "product_specific"
                },
                ambiguous_terms=[]
            )
            
            logger.info(f"Product mention detected: {detected_product}")
            return intent
        
        return None
    
    async def _validate_welding_processes(self, processes: List[str]) -> List[str]:
        """
        Use LLM to validate and map welding process terms to enum-compatible values.
        Maps domain terms like 'pulse welding' to standard enum values using AI reasoning.
        """
        if not processes:
            return []
            
        from ...agents.state_models import WeldingProcess
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage
        
        # Get valid enum values
        valid_processes = [member.value for member in WeldingProcess]
        
        # Filter already valid processes
        already_valid = [p for p in processes if str(p).strip() in valid_processes]
        needs_validation = [p for p in processes if str(p).strip() not in valid_processes]
        
        if not needs_validation:
            return already_valid
            
        try:
            # Use LLM to map invalid terms to valid enum values
            from ...core.config import settings
            llm = ChatOpenAI(
                model_name="gpt-4", 
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            validation_prompt = f"""
You are a welding expert. Map these welding process terms to the closest standard welding process.

VALID WELDING PROCESSES: {', '.join(valid_processes)}

TERMS TO MAP: {', '.join(needs_validation)}

Rules:
- "pulse welding" → "MIG" (pulse is a MIG technique)
- "wire welding" → "MIG" 
- "argon welding" → "TIG"
- "electrode welding" → "STICK"
- "arc welding" → choose most appropriate based on context

For each term, return the most appropriate standard process from the valid list.
If a term is unclear or doesn't match any welding process, skip it.

Return ONLY a JSON array of the mapped standard processes (no duplicates):
["PROCESS1", "PROCESS2", ...]
"""
            
            response = await llm.agenerate([[HumanMessage(content=validation_prompt)]])
            response_text = response.generations[0][0].text.strip()
            
            # Parse LLM response
            import json
            try:
                mapped_processes = json.loads(response_text)
                if isinstance(mapped_processes, list):
                    # Validate that LLM returned valid enum values
                    validated_mapped = [p for p in mapped_processes if p in valid_processes]
                    
                    logger.info(f"🤖 LLM mapped {needs_validation} → {validated_mapped}")
                    
                    # Combine already valid + LLM mapped (remove duplicates)
                    all_processes = list(set(already_valid + validated_mapped))
                    return all_processes
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            
        # Fallback: return only already valid processes
        logger.warning(f"Using fallback validation - only returning already valid processes: {already_valid}")
        return already_valid
    
    async def _convert_simple_to_extracted_intent(self, simple_intent, query: str) -> ExtractedIntent:
        """
        Convert SimpleWeldingIntent to ExtractedIntent format
        Ensures compatibility with existing pipeline
        """
        
        # Map domain-specific welding terms to valid enum values using LLM (fixes pulse welding issue)
        validated_processes = await self._validate_welding_processes(simple_intent.processes or [])
        
        return ExtractedIntent(
            welding_process=validated_processes,
            material=simple_intent.material,
            power_watts=simple_intent.power_watts,
            current_amps=simple_intent.current_amps,
            voltage=simple_intent.voltage,
            thickness_mm=simple_intent.thickness_mm,
            industry=simple_intent.industry,
            environment=simple_intent.environment,
            application=simple_intent.application,
            duty_cycle=None,
            similar_to_customer=None,
            similar_to_purchase=None,
            similar_to_package=None,
            confidence=simple_intent.confidence,
            confidence_level="high" if simple_intent.confidence > 0.7 else "medium" if simple_intent.confidence > 0.4 else "low",
            extraction_issues=[],
            original_query=query,
            extracted_entities={},
            ambiguous_terms=simple_intent.missing_params
        )
    
    def calculate_confidence_score(
        self,
        base_intent: ExtractedIntent,
        expertise_mode: ExpertiseMode,
        language_confidence: float
    ) -> float:
        """Calculate overall confidence score for the enhanced intent"""
        
        # Base confidence from intent extraction
        intent_confidence = base_intent.confidence
        
        # Adjust based on expertise mode clarity
        mode_adjustment = {
            ExpertiseMode.EXPERT: 1.1,    # Expert queries typically clearer
            ExpertiseMode.GUIDED: 0.9,    # Guided queries may be ambiguous  
            ExpertiseMode.HYBRID: 1.0     # Neutral adjustment
        }
        
        # Combine factors
        overall_confidence = (
            intent_confidence * 0.7 +           # Intent extraction quality (70%)
            language_confidence * 0.2 +         # Language detection quality (20%)
            mode_adjustment[expertise_mode] * 0.1  # Mode detection adjustment (10%)
        )
        
        return min(overall_confidence, 1.0)


# Dependency injection
_intelligent_intent_service = None

async def get_intelligent_intent_service() -> IntelligentIntentService:
    """Get singleton intelligent intent service instance"""
    global _intelligent_intent_service
    if _intelligent_intent_service is None:
        _intelligent_intent_service = IntelligentIntentService()
    return _intelligent_intent_service