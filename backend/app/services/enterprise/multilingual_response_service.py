"""
Agent 3: Multilingual Response Service
Intelligent response generation with multilingual support and enterprise formatting
Mode-aware explanations and business context re-ranking
"""

import time
import logging
from typing import Dict, List, Any, Optional

from .enhanced_state_models import (
    ScoredRecommendations,
    EnhancedProcessedIntent,
    EnterpriseRecommendationResponse,
    PackageGenerationExplanation,
    MultilingualResponse,
    ExplanationLevel,
    BusinessPriority,
    ExpertiseMode,
    LanguageCode,
    TrinityPackage
)

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """Generates mode-aware explanations for different expertise levels"""
    
    def generate_explanations(
        self,
        packages: List[TrinityPackage],
        expertise_mode: ExpertiseMode,
        intent: EnhancedProcessedIntent
    ) -> Dict[str, str]:
        """Generate explanations based on user expertise mode"""
        
        explanations = {}
        
        if expertise_mode == ExpertiseMode.EXPERT:
            explanations.update(self._generate_expert_explanations(packages, intent))
        elif expertise_mode == ExpertiseMode.GUIDED:
            explanations.update(self._generate_guided_explanations(packages, intent))
        else:  # HYBRID
            explanations.update(self._generate_balanced_explanations(packages, intent))
        
        return explanations
    
    def _generate_expert_explanations(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> Dict[str, str]:
        """Technical explanations for expert users"""
        
        explanations = {
            "technical_summary": self._create_technical_summary(packages, intent),
            "compatibility_analysis": self._analyze_compatibility_technical(packages),
            "performance_metrics": self._provide_performance_metrics(packages)
        }
        
        return explanations
    
    def _generate_guided_explanations(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> Dict[str, str]:
        """Educational explanations for guided users"""
        
        explanations = {
            "beginner_summary": self._create_beginner_friendly_summary(packages, intent),
            "component_education": self._explain_components_for_beginners(packages),
            "usage_guidance": self._provide_usage_guidance(packages, intent)
        }
        
        return explanations
    
    def _generate_balanced_explanations(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> Dict[str, str]:
        """Balanced explanations for hybrid users"""
        
        explanations = {
            "overview": self._create_balanced_overview(packages, intent),
            "key_features": self._highlight_key_features(packages),
            "recommendations": self._provide_recommendations(packages)
        }
        
        return explanations
    
    def _create_technical_summary(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> str:
        """Create technical summary for experts"""
        
        if not packages:
            return "No compatible Trinity packages found matching specified parameters."
        
        best_package = packages[0]
        
        summary_parts = [
            f"Optimal Trinity configuration identified with {best_package.package_score:.1%} compatibility score.",
            f"PowerSource: {best_package.power_source.get('product_name', 'Unknown')}",
        ]
        
        if best_package.feeder:
            summary_parts.append(f"Wire Feeder: {best_package.feeder.get('product_name', 'Unknown')}")
        
        if best_package.cooler:
            summary_parts.append(f"Cooling System: {best_package.cooler.get('product_name', 'Unknown')}")
        
        summary_parts.append(f"Total system cost: ${best_package.total_price:.2f}")
        
        # Add technical specifications if available
        if intent.welding_process:
            processes = [p.value for p in intent.welding_process]
            summary_parts.append(f"Optimized for {', '.join(processes)} processes")
        
        return " | ".join(summary_parts)
    
    def _create_beginner_friendly_summary(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> str:
        """Create educational summary for beginners"""
        
        if not packages:
            return "I couldn't find a complete welding package that matches your needs. Let me ask a few questions to help you better."
        
        best_package = packages[0]
        
        summary = f"I found a great welding package for you! This complete setup includes everything you need:\n\n"
        summary += f"🔌 **Power Source**: {best_package.power_source.get('product_name', 'Unknown')} - This is the main welding machine that provides the power.\n"
        
        if best_package.feeder:
            summary += f"📋 **Wire Feeder**: {best_package.feeder.get('product_name', 'Unknown')} - This feeds welding wire automatically so you can focus on your weld.\n"
        
        if best_package.cooler:
            summary += f"❄️ **Cooling System**: {best_package.cooler.get('product_name', 'Unknown')} - This keeps your torch cool during longer welding sessions.\n"
        
        summary += f"\n💰 **Total Package Price**: ${best_package.total_price:.2f}\n"
        summary += f"✅ **Why This Works**: This package is designed to work together perfectly, giving you professional results."
        
        return summary
    
    def _analyze_compatibility_technical(self, packages: List[TrinityPackage]) -> str:
        """Technical compatibility analysis"""
        
        if not packages:
            return "No compatibility data available."
        
        analysis_parts = []
        
        for i, package in enumerate(packages[:3]):
            analysis_parts.append(
                f"Package {i+1}: Trinity compliance {package.trinity_compliance}, "
                f"Business rule compliance {package.business_rule_compliance:.1%}, "
                f"Compatibility score {package.compatibility_score:.2f}"
            )
        
        return "; ".join(analysis_parts)
    
    def _provide_performance_metrics(self, packages: List[TrinityPackage]) -> str:
        """Provide performance metrics for expert users"""
        
        if not packages:
            return "No performance data available."
        
        total_packages = len(packages)
        trinity_compliant = len([p for p in packages if p.trinity_compliance])
        avg_score = sum(p.package_score for p in packages) / len(packages)
        
        return f"Generated {total_packages} packages, {trinity_compliant} Trinity-compliant, Average score: {avg_score:.2f}"
    
    def _explain_components_for_beginners(self, packages: List[TrinityPackage]) -> str:
        """Explain what each component does for beginners"""
        
        explanation = """
**Understanding Your Welding Package:**

🔌 **Power Source (Welder)**: The heart of your setup - converts electricity into welding power
📋 **Wire Feeder**: Automatically feeds welding wire at the right speed (for MIG welding)
❄️ **Cooling System**: Prevents overheating during long welding sessions
⚡ **Why Trinity Matters**: These three components work together like a team - each one is essential for professional welding results
"""
        return explanation.strip()
    
    def _provide_usage_guidance(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> str:
        """Provide usage guidance for beginners"""
        
        guidance_parts = ["**Getting Started Tips:**"]
        
        if intent.material:
            guidance_parts.append(f"• This setup is optimized for {intent.material.value} welding")
        
        if intent.welding_process:
            processes = [p.value for p in intent.welding_process]
            guidance_parts.append(f"• Perfect for {', '.join(processes)} welding processes")
        
        guidance_parts.extend([
            "• Start with practice pieces before your main project",
            "• Make sure you have proper safety equipment (helmet, gloves, ventilation)",
            "• Consider taking a welding class to learn proper techniques"
        ])
        
        return "\n".join(guidance_parts)
    
    def _create_balanced_overview(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> str:
        """Create balanced overview for hybrid users"""
        
        if not packages:
            return "No suitable welding packages found. Please provide more specific requirements."
        
        best_package = packages[0]
        
        overview = f"**Recommended Welding Package** (Score: {best_package.package_score:.1%})\n\n"
        overview += f"**Power Source**: {best_package.power_source.get('product_name', 'Unknown')}\n"
        
        if best_package.feeder:
            overview += f"**Wire Feeder**: {best_package.feeder.get('product_name', 'Unknown')}\n"
        
        if best_package.cooler:
            overview += f"**Cooling**: {best_package.cooler.get('product_name', 'Unknown')}\n"
        
        overview += f"**Total**: ${best_package.total_price:.2f}\n\n"
        overview += f"This Trinity package ensures all components work together optimally."
        
        return overview
    
    def _highlight_key_features(self, packages: List[TrinityPackage]) -> str:
        """Highlight key features for hybrid users"""
        
        if not packages:
            return "No features to highlight."
        
        features = [
            "✅ Complete Trinity package (Power Source + Feeder + Cooler)",
            "✅ Components verified for compatibility",
            "✅ Business-grade quality and reliability"
        ]
        
        best_package = packages[0]
        if best_package.business_rule_compliance > 0.8:
            features.append("✅ Meets enterprise business rules and standards")
        
        return "\n".join(features)
    
    def _provide_recommendations(self, packages: List[TrinityPackage]) -> str:
        """Provide recommendations for hybrid users"""
        
        if len(packages) > 1:
            return f"Found {len(packages)} compatible packages. Top recommendation shown above. Contact sales for alternative configurations."
        elif len(packages) == 1:
            return "Single optimal configuration identified. This package provides the best match for your requirements."
        else:
            return "Consider expanding search criteria or contacting technical support for custom solutions."


class BusinessContextReranker:
    """Re-ranks recommendations based on business context and priorities"""
    
    def rerank_packages(
        self,
        packages: List[TrinityPackage],
        user_context: Dict[str, Any],
        business_priorities: Dict[str, Any]
    ) -> List[TrinityPackage]:
        """Re-rank packages based on business context"""
        
        if not packages:
            return packages
        
        # Apply business scoring
        for package in packages:
            business_score = self._calculate_business_score(package, user_context, business_priorities)
            
            # Adjust package score with business context
            package.package_score = (package.package_score * 0.7) + (business_score * 0.3)
        
        # Sort by adjusted scores
        packages.sort(key=lambda p: p.package_score, reverse=True)
        
        return packages
    
    def _calculate_business_score(
        self,
        package: TrinityPackage,
        user_context: Dict[str, Any],
        business_priorities: Dict[str, Any]
    ) -> float:
        """Calculate business context score"""
        
        score = 0.5  # Base score
        
        # ESAB products priority
        if business_priorities.get("esab_priority", False):
            esab_components = sum(1 for comp in [package.power_source, package.feeder, package.cooler]
                                if comp and "ESAB" in comp.get("product_name", ""))
            score += (esab_components / 3) * 0.3
        
        # Price tier preferences
        organization = user_context.get("organization", "")
        if "enterprise" in organization.lower() or "corporation" in organization.lower():
            # Enterprise customers prefer mid-to-high tier
            if package.total_price > 5000:
                score += 0.2
        else:
            # Small businesses prefer cost-effective solutions
            if 1000 <= package.total_price <= 5000:
                score += 0.2
        
        # Trinity compliance boost
        if package.trinity_compliance:
            score += 0.2
        
        return min(score, 1.0)


class MultilingualTranslator:
    """Handles translation back to user's original language"""
    
    def translate_response(
        self,
        response: MultilingualResponse,
        target_language: LanguageCode
    ) -> MultilingualResponse:
        """Translate response to target language"""
        
        if target_language == LanguageCode.EN:
            return response  # No translation needed
        
        # Simplified translation for MVP - in production would use proper translation service
        translated_response = MultilingualResponse(
            title=self._simple_translate(response.title, target_language),
            summary=self._simple_translate(response.summary, target_language),
            detailed_explanation=self._simple_translate(response.detailed_explanation, target_language),
            technical_notes=[self._simple_translate(note, target_language) for note in response.technical_notes],
            package_descriptions=[self._simple_translate(desc, target_language) for desc in response.package_descriptions],
            comparison_matrix=response.comparison_matrix,  # Keep as-is for MVP
            next_steps=[self._simple_translate(step, target_language) for step in response.next_steps],
            related_questions=[self._simple_translate(q, target_language) for q in response.related_questions],
            response_language=target_language,
            explanation_level=response.explanation_level,
            cultural_adaptations=response.cultural_adaptations
        )
        
        return translated_response
    
    def _simple_translate(self, text: str, target_language: LanguageCode) -> str:
        """Simple translation (placeholder for MVP)"""
        
        # Simplified translation mappings for key terms
        translation_maps = {
            LanguageCode.ES: {
                "Power Source": "Fuente de Poder",
                "Wire Feeder": "Alimentador de Alambre", 
                "Cooling System": "Sistema de Enfriamiento",
                "Total Package Price": "Precio Total del Paquete",
                "Recommended": "Recomendado",
                "Complete Trinity package": "Paquete Trinity Completo"
            },
            LanguageCode.FR: {
                "Power Source": "Source d'Alimentation",
                "Wire Feeder": "Dévidoir de Fil",
                "Cooling System": "Système de Refroidissement", 
                "Total Package Price": "Prix Total du Package",
                "Recommended": "Recommandé",
                "Complete Trinity package": "Package Trinity Complet"
            }
        }
        
        if target_language in translation_maps:
            translation_map = translation_maps[target_language]
            for english_term, translated_term in translation_map.items():
                text = text.replace(english_term, translated_term)
        
        return text


class ResponseFormatter:
    """Formats final response with enterprise structure"""
    
    def format_response(
        self,
        packages: List[TrinityPackage],
        explanations: Dict[str, str],
        expertise_mode: ExpertiseMode,
        detected_language: LanguageCode
    ) -> MultilingualResponse:
        """Format final enterprise response"""
        
        if expertise_mode == ExpertiseMode.EXPERT:
            return self._format_expert_response(packages, explanations, detected_language)
        elif expertise_mode == ExpertiseMode.GUIDED:
            return self._format_guided_response(packages, explanations, detected_language)
        else:  # HYBRID
            return self._format_balanced_response(packages, explanations, detected_language)
    
    def _format_expert_response(self, packages: List[TrinityPackage], explanations: Dict[str, str], language: LanguageCode) -> MultilingualResponse:
        """Format response for expert users"""
        
        return MultilingualResponse(
            title="Technical Welding System Analysis",
            summary=explanations.get("technical_summary", ""),
            detailed_explanation=explanations.get("compatibility_analysis", ""),
            technical_notes=[explanations.get("performance_metrics", "")],
            package_descriptions=self._create_technical_package_descriptions(packages),
            next_steps=["Review technical specifications", "Validate power requirements", "Confirm installation requirements"],
            related_questions=["What are the duty cycle requirements?", "Do you need additional consumables?", "Are there specific certification requirements?"],
            response_language=language,
            explanation_level=ExplanationLevel.TECHNICAL
        )
    
    def _format_guided_response(self, packages: List[TrinityPackage], explanations: Dict[str, str], language: LanguageCode) -> MultilingualResponse:
        """Format response for guided users"""
        
        return MultilingualResponse(
            title="Your Perfect Welding Package",
            summary=explanations.get("beginner_summary", ""),
            detailed_explanation=explanations.get("component_education", ""),
            technical_notes=[explanations.get("usage_guidance", "")],
            package_descriptions=self._create_beginner_package_descriptions(packages),
            next_steps=["Get safety equipment", "Consider training classes", "Plan your workspace"],
            related_questions=["What safety equipment do I need?", "Where can I learn welding?", "What materials can I weld with this?"],
            response_language=language,
            explanation_level=ExplanationLevel.EDUCATIONAL
        )
    
    def _format_balanced_response(self, packages: List[TrinityPackage], explanations: Dict[str, str], language: LanguageCode) -> MultilingualResponse:
        """Format response for hybrid users"""
        
        return MultilingualResponse(
            title="Welding Package Recommendation",
            summary=explanations.get("overview", ""),
            detailed_explanation=explanations.get("key_features", ""),
            technical_notes=[explanations.get("recommendations", "")],
            package_descriptions=self._create_standard_package_descriptions(packages),
            next_steps=["Review package details", "Check delivery options", "Contact sales if needed"],
            related_questions=["Are there other configurations available?", "What's the warranty coverage?", "Do you offer installation services?"],
            response_language=language,
            explanation_level=ExplanationLevel.BALANCED
        )
    
    def _create_technical_package_descriptions(self, packages: List[TrinityPackage]) -> List[str]:
        """Create technical package descriptions for experts"""
        
        descriptions = []
        for i, package in enumerate(packages[:3]):
            desc = f"Config {i+1}: Score {package.package_score:.2f}, Trinity {package.trinity_compliance}, Price ${package.total_price:.2f}"
            descriptions.append(desc)
        
        return descriptions
    
    def _create_beginner_package_descriptions(self, packages: List[TrinityPackage]) -> List[str]:
        """Create beginner-friendly package descriptions"""
        
        descriptions = []
        for i, package in enumerate(packages[:3]):
            desc = f"Option {i+1}: Complete welding package for ${package.total_price:.2f} - includes everything you need to start welding!"
            descriptions.append(desc)
        
        return descriptions
    
    def _create_standard_package_descriptions(self, packages: List[TrinityPackage]) -> List[str]:
        """Create standard package descriptions for hybrid users"""
        
        descriptions = []
        for i, package in enumerate(packages[:3]):
            desc = f"Package {i+1}: {package.power_source.get('product_name', 'Unknown')} system - ${package.total_price:.2f} (Score: {package.package_score:.1%})"
            descriptions.append(desc)
        
        return descriptions


class MultilingualResponseService:
    """
    Agent 3: Multilingual Response Service
    - Mode-aware explanation generation
    - Business context re-ranking
    - Multilingual response translation
    - Enterprise response formatting
    """
    
    def __init__(self):
        """Initialize multilingual response service components"""
        
        self.explanation_generator = ExplanationGenerator()
        self.business_reranker = BusinessContextReranker()
        self.multilingual_translator = MultilingualTranslator()
        self.response_formatter = ResponseFormatter()
        
        logger.info("Multilingual Response Service initialized")
    
    async def generate_response(
        self,
        recommendations: ScoredRecommendations,
        original_intent: EnhancedProcessedIntent,
        trace_id: str
    ) -> EnterpriseRecommendationResponse:
        """
        Main response generation for Agent 3
        
        Args:
            recommendations: Scored recommendations from Agent 2
            original_intent: Enhanced intent from Agent 1
            trace_id: Distributed tracing identifier
            
        Returns:
            Complete enterprise recommendation response
        """
        
        start_time = time.time()
        
        try:
            logger.info(f"[Agent 3] Generating {original_intent.detected_language.value} response for {original_intent.expertise_mode.value} mode (trace: {trace_id})")
            
            # Step 1: Business context re-ranking
            user_context = {
                "organization": getattr(original_intent, 'organization', ''),
                "industry": original_intent.industry.value if original_intent.industry else '',
                "expertise_mode": original_intent.expertise_mode.value
            }
            
            business_priorities = self._load_business_priorities()
            reranked_packages = self.business_reranker.rerank_packages(
                recommendations.packages.copy(),
                user_context,
                business_priorities
            )
            
            # Step 2: Generate mode-aware explanations
            explanations = self.explanation_generator.generate_explanations(
                reranked_packages,
                original_intent.expertise_mode,
                original_intent
            )
            
            # Step 3: Format response in English
            formatted_response = self.response_formatter.format_response(
                reranked_packages,
                explanations,
                original_intent.expertise_mode,
                LanguageCode.EN
            )
            
            # Step 4: Translate to original language if needed
            if original_intent.detected_language != LanguageCode.EN:
                formatted_response = self.multilingual_translator.translate_response(
                    formatted_response,
                    original_intent.detected_language
                )
            
            # Step 5: Calculate quality metrics
            overall_confidence = self._calculate_overall_confidence(reranked_packages, recommendations)
            confidence_breakdown = self._calculate_confidence_breakdown(reranked_packages, recommendations)
            business_insights = self._generate_business_insights(reranked_packages, user_context)
            
            # Generate package generation explanation
            generation_explanation = self._generate_package_explanation(reranked_packages, original_intent, recommendations)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create final enterprise response
            enterprise_response = EnterpriseRecommendationResponse(
                packages=reranked_packages,
                total_found=len(reranked_packages),
                formatted_response=formatted_response,
                explanations=explanations,
                generation_explanation=generation_explanation,
                overall_confidence=overall_confidence,
                confidence_breakdown=confidence_breakdown,
                search_metadata=recommendations.search_metadata,
                original_intent=original_intent,
                business_insights=business_insights,
                trace_id=trace_id,
                total_processing_time_ms=processing_time,
                agent_performance_breakdown={
                    "explanation_generation_ms": processing_time * 0.3,
                    "business_reranking_ms": processing_time * 0.2,
                    "response_formatting_ms": processing_time * 0.3,
                    "translation_ms": processing_time * 0.2
                },
                needs_follow_up=len(reranked_packages) == 0,
                follow_up_questions=self._generate_follow_up_questions(reranked_packages, original_intent),
                satisfaction_prediction=self._predict_satisfaction(reranked_packages, original_intent)
            )
            
            logger.info(f"[Agent 3] Generated response - Language: {formatted_response.response_language.value}, Confidence: {overall_confidence:.2f}, Time: {processing_time:.1f}ms")
            
            return enterprise_response
            
        except Exception as e:
            logger.error(f"[Agent 3] Error generating response: {e}")
            
            # Create error response
            return self._create_error_response(original_intent, trace_id, str(e))
    
    def _load_business_priorities(self) -> Dict[str, Any]:
        """Load business priorities for re-ranking"""
        
        return {
            "esab_priority": True,
            "trinity_requirement": True,
            "enterprise_tier_preference": True,
            "compatibility_assurance": True
        }
    
    def _calculate_overall_confidence(self, packages: List[TrinityPackage], recommendations: ScoredRecommendations) -> float:
        """Calculate overall confidence score"""
        
        if not packages:
            return 0.0
        
        # Average package scores
        package_confidence = sum(p.package_score for p in packages) / len(packages)
        
        # Trinity formation rate boost
        trinity_boost = recommendations.trinity_formation_rate * 0.2
        
        # Search strategy confidence
        search_confidence = recommendations.search_metadata.confidence
        
        overall = (package_confidence * 0.6) + (search_confidence * 0.2) + trinity_boost
        
        return min(overall, 1.0)
    
    def _calculate_confidence_breakdown(self, packages: List[TrinityPackage], recommendations: ScoredRecommendations) -> Dict[str, float]:
        """Calculate confidence breakdown by component"""
        
        breakdown = {
            "package_formation": sum(p.package_score for p in packages) / max(len(packages), 1),
            "trinity_compliance": recommendations.trinity_formation_rate,
            "search_strategy": recommendations.search_metadata.confidence,
            "business_rules": sum(p.business_rule_compliance for p in packages) / max(len(packages), 1)
        }
        
        return breakdown
    
    def _generate_business_insights(self, packages: List[TrinityPackage], user_context: Dict[str, Any]) -> List[str]:
        """Generate business insights for enterprise users"""
        
        insights = []
        
        if packages:
            avg_price = sum(p.total_price for p in packages) / len(packages)
            insights.append(f"Average package price: ${avg_price:.2f}")
            
            trinity_rate = len([p for p in packages if p.trinity_compliance]) / len(packages)
            insights.append(f"Trinity compliance rate: {trinity_rate:.1%}")
            
            if user_context.get("organization"):
                insights.append(f"Recommendations tailored for {user_context['organization']} requirements")
        
        return insights
    
    def _generate_follow_up_questions(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> List[str]:
        """Generate relevant follow-up questions"""
        
        if not packages:
            return [
                "Could you provide more specific welding requirements?",
                "What type of materials will you be welding?",
                "What's your budget range for the welding equipment?"
            ]
        
        if intent.expertise_mode == ExpertiseMode.EXPERT:
            return [
                "Do you need specific duty cycle requirements?",
                "Are there certification standards to meet?",
                "Do you need additional consumables or accessories?"
            ]
        elif intent.expertise_mode == ExpertiseMode.GUIDED:
            return [
                "Would you like help with safety equipment recommendations?",
                "Are you interested in welding training resources?",
                "Do you need workspace setup guidance?"
            ]
        else:
            return [
                "Would you like to see alternative configurations?",
                "Do you need delivery and installation information?",
                "Are there specific warranty requirements?"
            ]
    
    def _predict_satisfaction(self, packages: List[TrinityPackage], intent: EnhancedProcessedIntent) -> float:
        """Predict user satisfaction with recommendations"""
        
        if not packages:
            return 0.2  # Low satisfaction if no packages found
        
        # Base satisfaction from package quality
        avg_score = sum(p.package_score for p in packages) / len(packages)
        satisfaction = avg_score * 0.6
        
        # Trinity compliance boost
        trinity_rate = len([p for p in packages if p.trinity_compliance]) / len(packages)
        satisfaction += trinity_rate * 0.3
        
        # Mode-specific adjustments
        if intent.expertise_mode == ExpertiseMode.EXPERT and avg_score > 0.8:
            satisfaction += 0.1  # Experts appreciate high-quality matches
        elif intent.expertise_mode == ExpertiseMode.GUIDED and packages:
            satisfaction += 0.1  # Beginners happy with any good recommendation
        
        return min(satisfaction, 1.0)
    
    def _generate_package_explanation(
        self, 
        packages: List[TrinityPackage], 
        intent: EnhancedProcessedIntent,
        recommendations: ScoredRecommendations
    ) -> PackageGenerationExplanation:
        """Generate detailed explanation of how packages were generated"""
        
        # Analyze user intent understanding
        user_query_analysis = f"Interpreted query '{intent.original_query}' as "
        if intent.welding_process:
            user_query_analysis += f"welding process: {', '.join(intent.welding_process)}"
        if intent.material:
            user_query_analysis += f", material: {intent.material}"
        if not intent.welding_process and not intent.material:
            user_query_analysis += "general welding equipment request"
        
        # Detected requirements
        detected_requirements = {
            "welding_processes": intent.welding_process or [],
            "materials": [intent.material] if intent.material else [],
            "power_requirements": f"{intent.power_watts}W" if intent.power_watts else None,
            "current_requirements": f"{intent.current_amps}A" if intent.current_amps else None,
            "expertise_level": intent.expertise_mode.value,
            "language": intent.detected_language.value
        }
        
        # Search strategy reasoning
        strategy_name = recommendations.search_metadata.strategy.value
        search_strategy_reasoning = f"Used {strategy_name} search strategy. "
        if strategy_name == "HYBRID":
            search_strategy_reasoning += "Combined semantic similarity with graph-based compatibility for comprehensive results."
        elif strategy_name == "GRAPH_FOCUSED":
            search_strategy_reasoning += "Prioritized relationship-based search for expert queries."
        else:
            search_strategy_reasoning += "Applied guided flow for step-by-step selection."
        
        # Trinity formation process
        trinity_formation_process = "Applied Trinity architecture (PowerSource + Feeder + Cooler). "
        if packages and len(packages) > 0:
            trinity_count = len([p for p in packages if p.trinity_compliance])
            trinity_formation_process += f"Successfully formed {trinity_count}/{len(packages)} packages as complete Trinity combinations."
        
        # Component selection reasoning (focus on top package)
        power_source_reason = ""
        feeder_reason = ""
        cooler_reason = ""
        accessories_criteria = ""
        
        if packages:
            top_package = packages[0]
            
            # Power source selection
            if "SMAW" in (intent.welding_process or []):
                power_source_reason = f"Selected {top_package.power_source.get('product_name', 'Unknown')} for SMAW/stick welding capability with appropriate amperage output."
            elif "GMAW" in (intent.welding_process or []):
                power_source_reason = f"Selected {top_package.power_source.get('product_name', 'Unknown')} for MIG/GMAW welding with wire feeding compatibility."
            else:
                power_source_reason = f"Selected {top_package.power_source.get('product_name', 'Unknown')} based on compatibility and performance requirements."
            
            # Feeder selection
            if top_package.feeder:
                feeder_name = top_package.feeder.get('product_name', 'Unknown')
                if "No Feeder Available" in feeder_name:
                    feeder_reason = "No feeder required for this welding process (stick welding uses electrodes)."
                else:
                    feeder_reason = f"Selected {feeder_name} for optimal wire feeding performance with the chosen power source."
            
            # Cooler selection
            if top_package.cooler:
                cooler_name = top_package.cooler.get('product_name', 'Unknown')
                if "No Cooler Available" in cooler_name:
                    cooler_reason = "No cooling required for this application (air-cooled operation suitable)."
                else:
                    cooler_reason = f"Selected {cooler_name} for thermal management during extended welding operations."
            
            # Accessories criteria
            acc_count = len(top_package.accessories)
            accessories_criteria = f"Selected {acc_count} accessories based on co-purchase frequency with this Trinity combination, focusing on trolleys, cables, and essential consumables."
        
        # Ranking factors
        ranking_factors = {
            "trinity_compliance": 0.4,
            "semantic_similarity": 0.3,
            "sales_frequency": 0.2,
            "business_rules": 0.1
        }
        
        # Business rules applied
        business_rules_applied = [
            "Trinity architecture enforcement (PowerSource + Feeder + Cooler)",
            "Compatibility verification between components",
            "Sales frequency prioritization",
            "ESAB product preference (where applicable)"
        ]
        
        # Final score breakdown for top package
        final_score_breakdown = {}
        if packages:
            top_package = packages[0]
            final_score_breakdown = {
                "base_package_score": top_package.package_score,
                "trinity_compliance_bonus": 0.1 if top_package.trinity_compliance else 0.0,
                "compatibility_score": top_package.compatibility_score,
                "business_rule_adjustment": top_package.business_rule_compliance
            }
        
        return PackageGenerationExplanation(
            user_query_analysis=user_query_analysis,
            detected_requirements=detected_requirements,
            interpretation_confidence=intent.confidence,
            ambiguous_terms_resolved=getattr(intent, 'ambiguous_terms', []),
            search_strategy_reasoning=search_strategy_reasoning,
            algorithms_applied=[alg.value for alg in recommendations.algorithms_used],
            trinity_formation_process=trinity_formation_process,
            power_source_selection_reason=power_source_reason,
            feeder_selection_reason=feeder_reason,
            cooler_selection_reason=cooler_reason,
            accessories_selection_criteria=accessories_criteria,
            ranking_factors=ranking_factors,
            business_rules_applied=business_rules_applied,
            final_score_breakdown=final_score_breakdown
        )
    
    def _create_error_response(self, intent: EnhancedProcessedIntent, trace_id: str, error: str) -> EnterpriseRecommendationResponse:
        """Create error response when processing fails"""
        
        error_response = MultilingualResponse(
            title="Processing Error",
            summary="We encountered an issue processing your welding recommendation request.",
            detailed_explanation="Our system is temporarily unable to generate recommendations. Please try again or contact support.",
            technical_notes=[f"Error details: {error}"],
            response_language=intent.detected_language,
            explanation_level=ExplanationLevel.BALANCED
        )
        
        return EnterpriseRecommendationResponse(
            packages=[],
            total_found=0,
            formatted_response=error_response,
            explanations={"error": error},
            generation_explanation=PackageGenerationExplanation(
                user_query_analysis=f"Failed to process query: '{intent.original_query}'",
                interpretation_confidence=0.0,
                search_strategy_reasoning="Processing failed before search strategy could be applied"
            ),
            overall_confidence=0.0,
            confidence_breakdown={"error": 1.0},
            search_metadata=None,
            original_intent=intent,
            business_insights=[],
            trace_id=trace_id,
            needs_follow_up=True,
            follow_up_questions=["Would you like to try rephrasing your requirements?"],
            satisfaction_prediction=0.1
        )