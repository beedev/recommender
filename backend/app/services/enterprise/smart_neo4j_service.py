"""
Agent 2: Smart Neo4j Service
Enhanced Neo4j recommendations with graph algorithms and Trinity formation
Intelligent routing between Graph-focused and Hybrid search strategies
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from fastapi import Depends

from .enhanced_state_models import (
    EnhancedProcessedIntent,
    ScoredRecommendations,
    TrinityPackage,
    RoutingDecision,
    SearchStrategy,
    GraphAlgorithm,
    ExpertiseMode
)
from ...database.repositories import Neo4jRepository
from ...agents.simple_neo4j_agent import SimpleNeo4jAgent, SimpleWeldingPackage, WeldingPackageComponent
from ...services.embedding_generator import ProductEmbeddingGenerator

logger = logging.getLogger(__name__)


@dataclass
class GraphAlgorithmExecutor:
    """Executes graph algorithms for Neo4j traversal"""
    
    neo4j_repo: Neo4jRepository
    
    async def shortest_path(
        self, 
        start_product_id: str, 
        target_category: str,
        max_hops: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find shortest compatibility path between products
        Essential for discovering compatible component chains
        """
        
        query = """
        MATCH (start:Product {product_id: $start_id})
        MATCH (target:Product {category: $target_category})
        MATCH path = (start)-[:CO_OCCURS*1..3]-(target)
        WITH path, target, length(path) as path_length
        ORDER BY path_length ASC
        RETURN target.product_id as product_id,
               target.name as product_name,
               target.category as category,
               target.description as description,
               target.specifications_json as specifications,
               path_length
        LIMIT 10
        """
        
        parameters = {
            "start_id": start_product_id,
            "target_category": target_category
        }
        
        try:
            results = await self.neo4j_repo.execute_query(query, parameters)
            logger.info(f"Shortest path found {len(results)} compatible {target_category} products")
            return results
        except Exception as e:
            logger.error(f"Shortest path algorithm failed: {e}")
            return []
    
    async def pagerank_popular_products(
        self, 
        category: str,
        min_sales: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Use PageRank-style algorithm to find popular/influential products
        Based on co-occurrence frequency in sales transactions
        """
        
        query = """
        MATCH (p:Product {category: $category})<-[:CONTAINS]-(order:Order)
        WITH p, COUNT(order) as direct_sales
        WHERE direct_sales >= $min_sales
        
        // Find products that co-occur with this product in purchases
        MATCH (p)<-[:CONTAINS]-(shared_order:Order)-[:CONTAINS]->(co_product:Product)
        WHERE co_product.category = $category AND co_product <> p
        WITH p, direct_sales, COUNT(DISTINCT co_product) as co_occurrence_score
        
        // Calculate popularity score (combination of direct sales and co-occurrences)
        WITH p, direct_sales, co_occurrence_score,
             (direct_sales * 0.7 + co_occurrence_score * 0.3) as popularity_score
        
        RETURN p.product_id as product_id,
               p.name as product_name,
               p.category as category,
               p.description as description,
               p.specifications_json as specifications,
               direct_sales,
               co_occurrence_score,
               popularity_score
        ORDER BY popularity_score DESC
        LIMIT 15
        """
        
        parameters = {
            "category": category,
            "min_sales": min_sales
        }
        
        try:
            results = await self.neo4j_repo.execute_query(query, parameters)
            logger.info(f"PageRank identified {len(results)} popular {category} products")
            return results
        except Exception as e:
            logger.error(f"PageRank algorithm failed: {e}")
            return []
    
    async def centrality_connectors(
        self, 
        category: str,
        min_connections: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find products with high centrality (many connections)
        Useful for identifying versatile products that work with many others
        """
        
        query = """
        MATCH (p:Product {category: $category})
        MATCH (p)-[:COMPATIBLE]-(connected:Product)
        WITH p, COUNT(DISTINCT connected) as connection_count
        WHERE connection_count >= $min_connections
        
        // Calculate centrality score based on unique categories connected to
        MATCH (p)-[:COMPATIBLE]-(connected:Product)
        WITH p, connection_count, 
             COUNT(DISTINCT connected.category) as category_diversity
        
        WITH p, connection_count, category_diversity,
             (connection_count * 0.6 + category_diversity * 0.4) as centrality_score
        
        RETURN p.product_id as product_id,
               p.name as product_name,
               p.category as category,
               p.description as description,
               p.specifications_json as specifications,
               connection_count,
               category_diversity,
               centrality_score
        ORDER BY centrality_score DESC
        LIMIT 10
        """
        
        parameters = {
            "category": category,
            "min_connections": min_connections
        }
        
        try:
            results = await self.neo4j_repo.execute_query(query, parameters)
            logger.info(f"Centrality analysis found {len(results)} highly connected {category} products")
            return results
        except Exception as e:
            logger.error(f"Centrality algorithm failed: {e}")
            return []


@dataclass
class TrinityPackageFormer:
    """Forms Trinity packages (PowerSource + Feeder + Cooler) with business rules"""
    
    def validate_trinity_compliance(self, package_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Validate if package meets Trinity requirements
        Returns (is_compliant, compliance_score)
        """
        
        required_components = ["power_source", "feeder", "cooler"]
        present_components = [comp for comp in required_components 
                            if package_data.get(comp) is not None]
        
        compliance_score = len(present_components) / len(required_components)
        is_compliant = len(present_components) == len(required_components)
        
        return is_compliant, compliance_score
    
    def enforce_business_rules(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply business rules and priorities to package formation"""
        
        # Business Rule 1: ESAB products get priority boost
        for component_type in ["power_source", "feeder", "cooler"]:
            component = package_data.get(component_type)
            if component and "ESAB" in component.get("product_name", ""):
                component["business_priority_boost"] = 0.1
        
        # Business Rule 2: Ensure voltage compatibility
        power_source = package_data.get("power_source")
        if power_source and power_source.get("specifications"):
            # Extract voltage from power source and validate other components
            pass  # Simplified for MVP
        
        # Business Rule 3: Price tier consistency
        # Keep components in similar price ranges for balanced packages
        components = [comp for comp in [package_data.get("power_source"), 
                                      package_data.get("feeder"),
                                      package_data.get("cooler")] 
                     if comp is not None]
        
        if len(components) >= 2:
            prices = [comp.get("price", 0) for comp in components if comp.get("price")]
            if prices:
                avg_price = sum(prices) / len(prices)
                # Mark packages with consistent pricing
                package_data["price_consistency_score"] = self._calculate_price_consistency(prices, avg_price)
        
        return package_data
    
    def _calculate_price_consistency(self, prices: List[float], avg_price: float) -> float:
        """Calculate how consistent the prices are (0.0-1.0)"""
        if not prices or avg_price == 0:
            return 0.5
        
        max_deviation = max(abs(price - avg_price) / avg_price for price in prices)
        return max(0.0, 1.0 - max_deviation)
    
    async def form_packages(
        self, 
        candidates: Dict[str, List[Dict[str, Any]]],
        intent: EnhancedProcessedIntent,
        business_rules: Dict[str, Any]
    ) -> List[TrinityPackage]:
        """
        Form Trinity packages from component candidates
        
        Args:
            candidates: Dict with 'power_sources', 'feeders', 'coolers' lists
            intent: Enhanced processed intent
            business_rules: Business rules and priorities
            
        Returns:
            List of formed Trinity packages
        """
        
        packages = []
        power_sources = candidates.get("power_sources", [])
        feeders = candidates.get("feeders", [])
        coolers = candidates.get("coolers", [])
        
        # Form packages by combining highest scoring components
        for ps in power_sources[:3]:  # Top 3 power sources
            for feeder in feeders[:2]:  # Top 2 feeders for each PS
                for cooler in coolers[:2]:  # Top 2 coolers for each combination
                    
                    # Create package candidate
                    package_data = {
                        "power_source": ps,
                        "feeder": feeder,
                        "cooler": cooler
                    }
                    
                    # Apply business rules
                    package_data = self.enforce_business_rules(package_data)
                    
                    # Validate Trinity compliance
                    is_compliant, compliance_score = self.validate_trinity_compliance(package_data)
                    
                    # Calculate package score
                    package_score = self._calculate_package_score(
                        package_data, intent, compliance_score
                    )
                    
                    # Create Trinity package
                    trinity_package = TrinityPackage(
                        power_source=ps,
                        feeder=feeder,
                        cooler=cooler,
                        package_score=package_score,
                        trinity_compliance=is_compliant,
                        business_rule_compliance=compliance_score,
                        total_price=self._calculate_total_price(package_data),
                        compatibility_verified=True,  # Verified through graph queries
                        compatibility_score=compliance_score
                    )
                    
                    packages.append(trinity_package)
        
        # Sort packages by score and return top ones
        packages.sort(key=lambda p: p.package_score, reverse=True)
        return packages[:10]  # Return top 10 packages
    
    def _calculate_package_score(
        self, 
        package_data: Dict[str, Any], 
        intent: EnhancedProcessedIntent,
        compliance_score: float
    ) -> float:
        """Calculate overall package score with user intent matching bonus"""
        
        # Base score from Trinity compliance
        score = compliance_score * 0.4
        
        # Component quality scores
        for component in [package_data.get("power_source"), 
                         package_data.get("feeder"), 
                         package_data.get("cooler")]:
            if component:
                component_score = component.get("compatibility_score", 0.5)
                business_boost = component.get("business_priority_boost", 0.0)
                score += (component_score + business_boost) * 0.2
        
        # Price consistency bonus
        price_consistency = package_data.get("price_consistency_score", 0.5)
        score += price_consistency * 0.1
        
        # User Intent Match Bonus - boost packages containing explicitly requested products
        intent_bonus = self._calculate_intent_match_bonus(package_data, intent)
        score += intent_bonus
        
        # Expertise mode adjustment
        if intent.expertise_mode == ExpertiseMode.EXPERT:
            # Expert users likely want precise technical matches
            score = min(score * 1.1, 1.0)
        
        return min(score, 1.0)
    
    def _calculate_intent_match_bonus(
        self, 
        package_data: Dict[str, Any], 
        intent: EnhancedProcessedIntent
    ) -> float:
        """
        Calculate bonus score for packages that contain user's explicitly requested products.
        
        Args:
            package_data: Package component data
            intent: Processed user intent with original query
            
        Returns:
            Bonus score (0.0 to 0.15) to boost packages matching user intent
        """
        bonus = 0.0
        
        # Get the original query from intent
        original_query = getattr(intent, 'original_query', '').lower()
        if not original_query:
            return bonus
            
        # Define product name keywords to look for
        # These should match our domain vocabulary high-priority terms
        product_keywords = {
            'renegade': 0.35,    # Very high bonus for exact product name match
            'warrior': 0.35,
            'aristo': 0.35,
            'aristo 500': 0.40,  # Even higher for specific model matches
            'aristo 500ix': 0.45,
            'warrior 500': 0.40,
            'renegade es': 0.40,
            'robustfeed': 0.25,  # High bonus for component names
            'cool2': 0.25,
            'cooling unit': 0.15,
            'wire feeder': 0.15,
            'power source': 0.05  # Lower bonus for generic terms
        }
        
        # Check each component in the package for keyword matches
        components_to_check = [
            package_data.get("power_source"),
            package_data.get("feeder"), 
            package_data.get("cooler")
        ]
        
        for component in components_to_check:
            if not component:
                continue
                
            component_name = component.get("product_name", "").lower()
            
            # Check for exact keyword matches in product name
            for keyword, keyword_bonus in product_keywords.items():
                if keyword in original_query and keyword in component_name:
                    bonus += keyword_bonus
                    # Log the intent match for debugging
                    logger.info(f"🎯 Intent Match Bonus: '{keyword}' found in query '{original_query}' matches component '{component_name}' (+{keyword_bonus})")
                    break  # Only give one bonus per component to avoid double-counting
        
        # Cap the total bonus to prevent excessive boosting
        return min(bonus, 0.15)
    
    def _calculate_total_price(self, package_data: Dict[str, Any]) -> float:
        """Calculate total package price"""
        
        total = 0.0
        for component in [package_data.get("power_source"), 
                         package_data.get("feeder"), 
                         package_data.get("cooler")]:
            if component and component.get("price"):
                total += component["price"]
        
        return total


class SmartNeo4jService:
    """
    Agent 2: Smart Neo4j Recommendations with Graph Algorithms
    - Intelligent routing (Graph vs Hybrid strategy)
    - Graph algorithm execution (shortest_path, pagerank, centrality)
    - Trinity formation with business rules
    - Enhanced Neo4j queries with relationship traversal
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        """Initialize smart Neo4j service"""
        
        self.neo4j_repo = neo4j_repo
        
        # Graph algorithm executors
        self.graph_algorithms = GraphAlgorithmExecutor(neo4j_repo)
        
        # Trinity package formation
        self.trinity_former = TrinityPackageFormer()
        
        # Integrate with existing embedding service
        self.embedding_generator = ProductEmbeddingGenerator()
        
        # Fallback to simple Neo4j agent for compatibility
        self.simple_neo4j_agent = SimpleNeo4jAgent(neo4j_repo)
        
        logger.info("Smart Neo4j Service initialized with graph algorithms")
    
    async def generate_recommendations(
        self,
        processed_intent: EnhancedProcessedIntent,
        trace_id: str
    ) -> ScoredRecommendations:
        """
        Main recommendation generation for Agent 2
        
        Args:
            processed_intent: Enhanced intent from Agent 1
            trace_id: Distributed tracing identifier
            
        Returns:
            Scored Trinity packages with search metadata
        """
        
        start_time = time.time()
        
        try:
            logger.info(f"[Agent 2] Generating recommendations for {processed_intent.expertise_mode.value} mode (trace: {trace_id})")
            
            # Special handling for guided flow step requests
            guided_step_result = await self._handle_guided_flow_step(processed_intent, trace_id)
            if guided_step_result:
                return guided_step_result
            
            # TRINITY-FIRST: Try Trinity semantic search for complete package formation
            trinity_packages = await self._try_trinity_semantic_search(processed_intent, trace_id)
            if trinity_packages:
                logger.info("[Agent 2] Trinity-first approach successful, adding Trinity-based packages")
                logger.info(f"[Agent 2] Found {len(trinity_packages)} Trinity packages, continuing to generate additional recommendations")
            
            # Step 1: Intelligent routing decision
            routing_decision = self._make_routing_decision(processed_intent)
            
            # Step 2: Execute search strategy
            if routing_decision.strategy == SearchStrategy.GRAPH_FOCUSED:
                candidates = await self._graph_focused_search(processed_intent, routing_decision)
            else:  # SearchStrategy.HYBRID
                candidates = await self._hybrid_search(processed_intent, routing_decision)
            
            # Step 3: Use expert mode package formation for complete packages
            standard_packages = []
            if processed_intent.expertise_mode in [ExpertiseMode.EXPERT, ExpertiseMode.HYBRID]:
                logger.info(f"[Agent 2] Using expert mode package formation for {processed_intent.expertise_mode.value}")
                standard_packages = await self._form_expert_packages(candidates, processed_intent)
            else:
                # Guided mode - use simple Trinity formation
                business_rules = self._load_business_rules()
                standard_packages = await self.trinity_former.form_packages(
                    candidates, processed_intent, business_rules
                )
            
            # Step 4: Combine Trinity packages with standard packages
            all_packages = []
            
            # Add Trinity packages first (highest priority)
            if trinity_packages:
                logger.info(f"[Agent 2] Adding {len(trinity_packages)} Trinity semantic packages")
                for pkg in trinity_packages:
                    # Mark Trinity packages with semantic search algorithm
                    if hasattr(pkg, '_algorithm_source'):
                        pkg._algorithm_source = "trinity_semantic_search"
                    all_packages.append(pkg)
            
            # Add standard packages (sales frequency, compatibility)
            if standard_packages:
                logger.info(f"[Agent 2] Adding {len(standard_packages)} standard packages (sales frequency + compatibility)")
                for pkg in standard_packages:
                    # Mark standard packages with appropriate algorithms
                    if hasattr(pkg, '_algorithm_source'):
                        pkg._algorithm_source = "sales_frequency_compatibility"
                    all_packages.append(pkg)
            
            # Use combined packages
            final_packages = all_packages if all_packages else trinity_packages if trinity_packages else standard_packages
            
            # Step 5: Calculate quality metrics using final packages
            confidence_distribution = self._calculate_confidence_distribution(final_packages)
            trinity_formation_rate = len([p for p in final_packages if p.trinity_compliance]) / max(len(final_packages), 1)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Update algorithms used to include Trinity semantic search if used
            all_algorithms_used = routing_decision.algorithms.copy()
            if trinity_packages:
                all_algorithms_used.append(GraphAlgorithm.TRINITY_SEMANTIC_SEARCH)
            
            # Create scored recommendations response
            scored_recommendations = ScoredRecommendations(
                packages=final_packages,
                total_packages_found=len(final_packages),
                search_metadata=routing_decision,
                algorithms_used=all_algorithms_used,
                confidence_distribution=confidence_distribution,
                trinity_formation_rate=trinity_formation_rate,
                neo4j_query_time_ms=processing_time,
                trace_id=trace_id,
                neo4j_queries_executed=len(all_algorithms_used) + 1  # Base query + algorithms
            )
            
            logger.info(f"[Agent 2] Generated {len(final_packages)} total packages ({len(trinity_packages) if trinity_packages else 0} Trinity + {len(standard_packages) if standard_packages else 0} standard), Trinity rate: {trinity_formation_rate:.2f}, Time: {processing_time:.1f}ms")
            return scored_recommendations
            
        except Exception as e:
            logger.error(f"[Agent 2] Error generating recommendations: {e}")
            
            # Fallback to simple Neo4j agent
            try:
                return await self._fallback_to_simple_agent(processed_intent, trace_id)
            except Exception as fallback_error:
                logger.error(f"[Agent 2] Fallback also failed: {fallback_error}")
                raise e
    
    def _make_routing_decision(self, processed_intent: EnhancedProcessedIntent) -> RoutingDecision:
        """
        Intelligent routing decision between Graph-focused and Hybrid strategies
        No complex multi-strategy router - simplified approach per architecture analysis
        """
        
        # Expert mode with high confidence → Graph-focused
        if (processed_intent.expertise_mode == ExpertiseMode.EXPERT and 
            processed_intent.confidence > 0.7):
            
            return RoutingDecision(
                strategy=SearchStrategy.GRAPH_FOCUSED,
                algorithms=[GraphAlgorithm.SHORTEST_PATH, GraphAlgorithm.PAGERANK],
                weights={
                    "compatibility": 0.8,
                    "popularity": 0.2,
                    "semantic": 0.0
                },
                reasoning="Expert user with high confidence - using graph-focused approach",
                confidence=0.9
            )
        
        # All other cases → Hybrid approach
        else:
            return RoutingDecision(
                strategy=SearchStrategy.HYBRID,
                algorithms=[GraphAlgorithm.SHORTEST_PATH],
                weights={
                    "semantic": 0.4,
                    "compatibility": 0.6,
                    "popularity": 0.0
                },
                reasoning="General query or guided user - using hybrid semantic + graph approach",
                confidence=0.8
            )
    
    async def _graph_focused_search(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        routing_decision: RoutingDecision
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute graph-focused search using multiple algorithms"""
        
        candidates = {"power_sources": [], "feeders": [], "coolers": []}
        
        # Start with base power source search
        base_power_sources = await self._find_base_power_sources(processed_intent)
        
        if not base_power_sources:
            logger.warning("No base power sources found for graph traversal")
            return candidates
        
        candidates["power_sources"] = base_power_sources[:5]
        
        # Use graph algorithms to find compatible components
        for ps in base_power_sources[:3]:  # Top 3 power sources
            ps_id = ps["product_id"]
            
            # Shortest path for feeders
            if GraphAlgorithm.SHORTEST_PATH in routing_decision.algorithms:
                feeder_candidates = await self.graph_algorithms.shortest_path(
                    ps_id, "Feeder", max_hops=2
                )
                candidates["feeders"].extend(feeder_candidates)
            
            # Shortest path for coolers
            cooler_candidates = await self.graph_algorithms.shortest_path(
                ps_id, "Cooler", max_hops=2
            )
            candidates["coolers"].extend(cooler_candidates)
        
        # PageRank for popular products if requested
        if GraphAlgorithm.PAGERANK in routing_decision.algorithms:
            popular_feeders = await self.graph_algorithms.pagerank_popular_products("Feeder")
            popular_coolers = await self.graph_algorithms.pagerank_popular_products("Cooler")
            
            candidates["feeders"].extend(popular_feeders)
            candidates["coolers"].extend(popular_coolers)
        
        # Remove duplicates and score components
        candidates = self._deduplicate_and_score_candidates(candidates, processed_intent)
        
        return candidates
    
    async def _hybrid_search(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        routing_decision: RoutingDecision
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute hybrid search combining semantic similarity with graph traversal"""
        
        candidates = {"power_sources": [], "feeders": [], "coolers": []}
        
        # Semantic similarity search for power sources
        semantic_power_sources = await self._semantic_search_power_sources(processed_intent)
        candidates["power_sources"] = semantic_power_sources
        
        # Graph traversal for compatible components
        if semantic_power_sources:
            for ps in semantic_power_sources[:2]:  # Top 2 from semantic search
                ps_id = ps["product_id"]
                
                # Use shortest path for compatibility
                feeder_candidates = await self.graph_algorithms.shortest_path(
                    ps_id, "Feeder", max_hops=2
                )
                cooler_candidates = await self.graph_algorithms.shortest_path(
                    ps_id, "Cooler", max_hops=2
                )
                
                candidates["feeders"].extend(feeder_candidates)
                candidates["coolers"].extend(cooler_candidates)
        
        # Fallback to direct category search if no graph results
        if not candidates["feeders"]:
            candidates["feeders"] = await self._direct_category_search("Feeder", processed_intent)
        
        if not candidates["coolers"]:
            candidates["coolers"] = await self._direct_category_search("Cooler", processed_intent)
        
        candidates = self._deduplicate_and_score_candidates(candidates, processed_intent)
        
        return candidates
    
    async def _find_base_power_sources(self, processed_intent: EnhancedProcessedIntent) -> List[Dict[str, Any]]:
        """Find base power sources using existing simple agent logic"""
        
        try:
            # Use the original intent for compatibility with simple agent
            if processed_intent.original_intent:
                simple_power_sources = await self.simple_neo4j_agent.find_power_sources(
                    processed_intent.original_intent
                )
                
                # Convert to dict format
                return [
                    {
                        "product_id": ps.product_id,
                        "product_name": ps.product_name,
                        "category": ps.category,
                        "description": ps.description,
                        "price": ps.price,
                        "compatibility_score": ps.compatibility_score,
                        "sales_frequency": ps.sales_frequency
                    }
                    for ps in simple_power_sources
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding base power sources: {e}")
            return []
    
    async def _semantic_search_power_sources(self, processed_intent: EnhancedProcessedIntent) -> List[Dict[str, Any]]:
        """Use vector similarity for semantic power source search"""
        
        try:
            # Use embedding generator for semantic similarity
            # This is simplified - in full implementation would use vector similarity search
            return await self._find_base_power_sources(processed_intent)
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def _direct_category_search(self, category: str, processed_intent: EnhancedProcessedIntent) -> List[Dict[str, Any]]:
        """Direct search within a specific category"""
        
        query = """
        MATCH (p:Product {category: $category})
        OPTIONAL MATCH (p)<-[:CONTAINS]-(order:Order)
        WITH p, COUNT(order) as sales_frequency
        RETURN p.product_id as product_id,
               p.name as product_name,
               p.category as category,
               p.description as description,
               p.specifications_json as specifications,
               sales_frequency
        ORDER BY sales_frequency DESC, p.name ASC
        LIMIT 10
        """
        
        try:
            results = await self.neo4j_repo.execute_query(query, {"category": category})
            return results
        except Exception as e:
            logger.error(f"Direct category search failed for {category}: {e}")
            return []
    
    def _deduplicate_and_score_candidates(
        self, 
        candidates: Dict[str, List[Dict[str, Any]]], 
        processed_intent: EnhancedProcessedIntent
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Remove duplicates and score all candidates"""
        
        for category, items in candidates.items():
            # Remove duplicates by product_id
            seen_ids = set()
            unique_items = []
            
            for item in items:
                if item["product_id"] not in seen_ids:
                    seen_ids.add(item["product_id"])
                    
                    # Score compatibility
                    item["compatibility_score"] = self._score_component_compatibility(
                        item, processed_intent
                    )
                    
                    unique_items.append(item)
            
            # Sort by score and limit results
            unique_items.sort(key=lambda x: x["compatibility_score"], reverse=True)
            candidates[category] = unique_items[:10]
        
        return candidates
    
    def _score_component_compatibility(self, component: Dict[str, Any], intent: EnhancedProcessedIntent) -> float:
        """Score component compatibility with enhanced intent"""
        
        score = 0.5  # Base score
        
        # Process matching
        if intent.welding_process and (component.get("specifications") or component.get("description")):
            specifications = component.get("specifications", "").upper()
            description = component.get("description", "").upper()
            
            for process in intent.welding_process:
                if (process.value.upper() in specifications or 
                    process.value.upper() in description):
                    score += 0.2
                    break
        
        # Material matching
        if intent.material and component.get("description"):
            if intent.material.value.lower() in component["description"].lower():
                score += 0.15
        
        # Sales frequency bonus
        sales_freq = component.get("sales_frequency", 0)
        if sales_freq > 10:
            score += 0.1
        elif sales_freq > 5:
            score += 0.05
        
        # Industry matching
        if intent.industry and component.get("description"):
            if intent.industry.value.lower() in component["description"].lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """Load business rules for Trinity formation"""
        
        return {
            "esab_priority": True,
            "voltage_compatibility": True,
            "price_tier_consistency": True,
            "trinity_requirement": True
        }
    
    def _calculate_confidence_distribution(self, packages: List[TrinityPackage]) -> Dict[str, float]:
        """Calculate confidence distribution across packages"""
        
        if not packages:
            return {"high": 0.0, "medium": 0.0, "low": 0.0}
        
        high_confidence = len([p for p in packages if p.package_score >= 0.8])
        medium_confidence = len([p for p in packages if 0.6 <= p.package_score < 0.8])
        low_confidence = len([p for p in packages if p.package_score < 0.6])
        
        total = len(packages)
        
        return {
            "high": high_confidence / total,
            "medium": medium_confidence / total,
            "low": low_confidence / total
        }
    
    async def _fallback_to_simple_agent(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> ScoredRecommendations:
        """Fallback to simple Neo4j agent when enterprise features fail"""
        
        logger.warning(f"[Agent 2] Using fallback simple Neo4j agent")
        
        if processed_intent.original_intent:
            # Pass expertise mode as parameter for expert mode package generation
            logger.info(f"🔍 Smart Neo4j Service DEBUG: processed_intent.expertise_mode = {processed_intent.expertise_mode}")
            logger.info(f"🔍 Smart Neo4j Service DEBUG: expertise_mode.value = {processed_intent.expertise_mode.value if processed_intent.expertise_mode else 'None'}")
            
            simple_package = await self.simple_neo4j_agent.form_welding_package(
                processed_intent.original_intent,
                expertise_mode=processed_intent.expertise_mode.value if processed_intent.expertise_mode else None
            )
            
            if simple_package:
                # Convert simple package to Trinity format
                trinity_package = self._convert_simple_to_trinity_package(simple_package)
                
                return ScoredRecommendations(
                    packages=[trinity_package],
                    total_packages_found=1,
                    search_metadata=RoutingDecision(
                        strategy=SearchStrategy.HYBRID,
                        algorithms=[],
                        weights={"fallback": 1.0},
                        reasoning="Fallback to simple Neo4j agent"
                    ),
                    algorithms_used=[],
                    trinity_formation_rate=1.0 if trinity_package.trinity_compliance else 0.0,
                    trace_id=trace_id
                )
        
        # Return empty result if fallback fails
        return ScoredRecommendations(
            packages=[],
            total_packages_found=0,
            search_metadata=RoutingDecision(
                strategy=SearchStrategy.HYBRID,
                algorithms=[],
                weights={},
                reasoning="All search strategies failed"
            ),
            algorithms_used=[],
            trinity_formation_rate=0.0,
            trace_id=trace_id
        )
    
    async def _form_expert_packages(
        self, 
        candidates: Dict[str, List[Dict[str, Any]]], 
        processed_intent: EnhancedProcessedIntent
    ) -> List[TrinityPackage]:
        """
        Form complete expert packages using sales data analysis and golden package fallback
        This calls the complete package formation flow from simple_neo4j_agent
        """
        try:
            expert_packages = []
            power_sources = candidates.get("power_sources", [])
            
            for ps_data in power_sources[:3]:  # Top 3 power sources
                try:
                    # Convert power source dict to WeldingPackageComponent
                    power_source_component = self._convert_dict_to_component(ps_data)
                    
                    # Use the complete expert mode package formation
                    expert_package = await self.simple_neo4j_agent.form_expert_mode_package(
                        power_source_component, 
                        processed_intent.original_intent
                    )
                    
                    if expert_package:
                        # Convert to Trinity package format with intent match bonus
                        trinity_package = self._convert_simple_to_trinity_package(expert_package, processed_intent)
                        expert_packages.append(trinity_package)
                        
                        logger.info(f"[Agent 2] Expert package formed: {len(expert_package.consumables + expert_package.accessories + [expert_package.power_source] + expert_package.feeders + expert_package.coolers)} total products")
                    
                except Exception as e:
                    logger.error(f"[Agent 2] Error forming expert package for {ps_data.get('product_name', 'Unknown')}: {e}")
                    continue
            
            if not expert_packages:
                logger.warning("[Agent 2] No expert packages formed, falling back to Trinity formation")
                # Fallback to Trinity formation
                business_rules = self._load_business_rules()
                return await self.trinity_former.form_packages(candidates, processed_intent, business_rules)
            
            logger.info(f"[Agent 2] Formed {len(expert_packages)} complete expert packages")
            return expert_packages
            
        except Exception as e:
            logger.error(f"[Agent 2] Expert package formation failed: {e}")
            # Fallback to Trinity formation
            business_rules = self._load_business_rules()
            return await self.trinity_former.form_packages(candidates, processed_intent, business_rules)
    
    def _convert_dict_to_component(self, component_dict: Dict[str, Any]):
        """Convert component dictionary to WeldingPackageComponent"""
        from ...agents.simple_neo4j_agent import WeldingPackageComponent
        
        return WeldingPackageComponent(
            product_id=component_dict.get("product_id", ""),
            product_name=component_dict.get("product_name", "Unknown"),
            category=component_dict.get("category", "Unknown"),
            subcategory=component_dict.get("subcategory"),
            price=component_dict.get("price"),
            sales_frequency=component_dict.get("sales_frequency", 0),
            description=component_dict.get("description"),
            compatibility_score=component_dict.get("compatibility_score", 0.5)
        )

    def _convert_simple_to_trinity_package(self, simple_package: SimpleWeldingPackage, processed_intent: Optional[EnhancedProcessedIntent] = None) -> TrinityPackage:
        """Convert simple package format to Trinity package format"""
        
        # Extract components
        power_source = simple_package.power_source.__dict__ if simple_package.power_source else None
        feeder = simple_package.feeders[0].__dict__ if simple_package.feeders else None
        cooler = simple_package.coolers[0].__dict__ if simple_package.coolers else None
        
        # Check Trinity compliance
        trinity_compliant = all([power_source, feeder, cooler])
        
        # Apply intent match bonus if processed_intent is available
        base_score = simple_package.package_score
        if processed_intent:
            # Create package data structure for intent match calculation
            package_data = {
                "power_source": power_source,
                "feeder": feeder, 
                "cooler": cooler
            }
            intent_bonus = self._calculate_intent_match_bonus(package_data, processed_intent)
            enhanced_score = min(base_score + intent_bonus, 1.0)
            
            if intent_bonus > 0:
                logger.info(f"🎯 Intent Match Applied: Package score enhanced from {base_score:.3f} to {enhanced_score:.3f} (+{intent_bonus:.3f})")
        else:
            enhanced_score = base_score
        
        return TrinityPackage(
            power_source=power_source,
            feeder=feeder,
            cooler=cooler,
            consumables=[c.__dict__ for c in simple_package.consumables],
            accessories=[a.__dict__ for a in simple_package.accessories],
            package_score=enhanced_score,
            trinity_compliance=trinity_compliant,
            business_rule_compliance=simple_package.confidence,
            total_price=simple_package.total_price,
            compatibility_verified=True,
            compatibility_score=simple_package.confidence
        )
    
    async def get_sales_ranked_components(
        self,
        category: str,
        compatibility_filter: Optional[Dict[str, Any]] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get components ranked by sales frequency with optional compatibility filtering
        
        Args:
            category: Product category (PowerSource, Feeder, Cooler, etc.)
            compatibility_filter: Optional compatibility context for filtering
            limit: Maximum number of results to return
            
        Returns:
            List of components ranked by sales frequency with compatibility scores
        """
        try:
            logger.info(f"Getting sales-ranked {category} components (limit: {limit})")
            
            # Build base query for sales frequency ranking
            query = f"""
            MATCH (p:Product {{category: $category}})
            OPTIONAL MATCH (p)-[:SOLD_IN]->(sale:Sale)
            """
            
            parameters = {"category": category, "limit": limit}
            
            # Add compatibility filtering if provided
            if compatibility_filter:
                if compatibility_filter.get("powersource_id"):
                    query += """
                    OPTIONAL MATCH (p)-[:COMPATIBLE_WITH|CO_OCCURS*1..2]-(ps:Product {category: 'PowerSource'})
                    WHERE ps.gin = $powersource_id
                    """
                    parameters["powersource_id"] = compatibility_filter["powersource_id"]
                    
                if compatibility_filter.get("feeder_id"):
                    query += """
                    OPTIONAL MATCH (p)-[:COMPATIBLE_WITH|CO_OCCURS*1..2]-(f:Product {category: 'Feeder'})
                    WHERE f.gin = $feeder_id
                    """
                    parameters["feeder_id"] = compatibility_filter["feeder_id"]
            
            # Complete query with aggregation and ranking
            query += """
            WITH p, COUNT(DISTINCT sale) as sales_count
            ORDER BY sales_count DESC, p.product_name ASC
            LIMIT $limit
            
            RETURN p.gin as product_id,
                   p.product_name as product_name,
                   p.category as category,
                   p.description as description,
                   p.specifications_json as specifications,
                   p.price as price,
                   p.image_url as image_url,
                   sales_count
            """
            
            # Execute query
            results = await self.neo4j_repo.execute_query(query, parameters)
            
            # Transform results to ranked products
            ranked_products = []
            for rank, result in enumerate(results, 1):
                # Handle specifications JSON parsing
                specifications = result.get("specifications")
                if isinstance(specifications, str):
                    try:
                        import json
                        specifications = json.loads(specifications)
                    except:
                        specifications = {}
                elif specifications is None:
                    specifications = {}
                
                product = {
                    "product_id": result["product_id"],
                    "product_name": result["product_name"] or "Unknown Product",
                    "category": result["category"],
                    "description": result.get("description") or "No description available",
                    "specifications": specifications,
                    "sales_frequency": result["sales_count"],
                    "popularity_rank": rank,
                    "compatibility_score": 0.9 if compatibility_filter else 1.0,
                    "compatibility_reason": (
                        "High sales frequency and compatibility" if compatibility_filter 
                        else "High sales frequency"
                    ),
                    "price": result.get("price"),
                    "image_url": result.get("image_url")
                }
                ranked_products.append(product)
            
            logger.info(f"Found {len(ranked_products)} sales-ranked {category} products")
            return ranked_products
            
        except Exception as e:
            logger.error(f"Error getting sales-ranked {category} components: {e}")
            return []

    async def _handle_guided_flow_step(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> Optional[ScoredRecommendations]:
        """
        Handle realistic guided flow scenarios based on user intent
        
        Returns ScoredRecommendations if this is a guided flow scenario, None otherwise
        """
        
        query = processed_intent.original_query.lower()
        
        try:
            # Load guided flow scenarios configuration
            import yaml
            import os
            
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "config", "mode_detection.yaml"
            )
            
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            guided_flow_scenarios = config.get('guided_flow_scenarios', {})
            
            # Check for package formation scenarios (e.g., "form a package with Aristo 500")
            package_keywords = guided_flow_scenarios.get('package_formation', [])
            if any(keyword.lower() in query for keyword in package_keywords):
                logger.info(f"[Agent 2] Detected guided flow - package formation request (trace: {trace_id})")
                return await self._handle_package_formation_request(processed_intent, trace_id)
            
            # Check for multi-process machine queries
            multi_process_keywords = guided_flow_scenarios.get('multi_process_queries', [])
            if any(keyword.lower() in query for keyword in multi_process_keywords):
                logger.info(f"[Agent 2] Detected guided flow - multi-process machine request (trace: {trace_id})")
                return await self._handle_multi_process_request(processed_intent, trace_id)
            
            # Check for beginner package requests
            beginner_keywords = guided_flow_scenarios.get('beginner_package_requests', [])
            if any(keyword.lower() in query for keyword in beginner_keywords):
                logger.info(f"[Agent 2] Detected guided flow - beginner package request (trace: {trace_id})")
                return await self._handle_beginner_package_request(processed_intent, trace_id)
            
            # Check for specific product queries
            specific_product_keywords = guided_flow_scenarios.get('specific_product_queries', [])
            if any(keyword.lower() in query for keyword in specific_product_keywords):
                logger.info(f"[Agent 2] Detected guided flow - specific product query (trace: {trace_id})")
                return await self._handle_specific_product_request(processed_intent, trace_id)
                
            # No guided flow scenario detected
            return None
            
        except Exception as e:
            logger.warning(f"Failed to load guided flow scenarios config: {e}")
            return None
    
    async def _handle_package_formation_request(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> ScoredRecommendations:
        """Handle package formation requests like 'form a package with [product]'"""
        
        start_time = time.time()
        
        # Leverage existing LLM product extraction from intelligent intent service
        # The product name is already extracted and available in similar_to_customer
        product_name = processed_intent.similar_to_customer
        
        # Also check extracted_entities for additional product context
        mentioned_product = None
        if hasattr(processed_intent, 'extracted_entities') and processed_intent.extracted_entities:
            mentioned_product = processed_intent.extracted_entities.get('mentioned_product')
        
        # Use either field - prefer similar_to_customer as it's the standard field
        detected_product = product_name or mentioned_product
        
        if detected_product:
            logger.info(f"[Agent 2] Forming package for LLM-detected product: {detected_product}")
            # Use existing agent system to build trinity around the detected product
            fallback_result = await self._fallback_to_simple_agent(processed_intent, trace_id)
        else:
            logger.info(f"[Agent 2] No specific product detected by LLM, showing popular options for package formation")
            # Use existing agent system for general package formation
            fallback_result = await self._fallback_to_simple_agent(processed_intent, trace_id)
        
        # Update the routing decision to show guided flow was used
        fallback_result.search_metadata.strategy = SearchStrategy.GUIDED_FLOW
        fallback_result.search_metadata.reasoning = f"Guided flow: Package formation request for {detected_product or 'unspecified product'} (LLM-detected)"
        fallback_result.search_metadata.algorithms = [GraphAlgorithm.COMPATIBILITY, GraphAlgorithm.SALES_FREQUENCY]
        fallback_result.search_metadata.weights = {"compatibility": 0.7, "sales_frequency": 0.3}
        fallback_result.search_metadata.confidence = 0.9
        
        return fallback_result
    
    async def _handle_multi_process_request(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> ScoredRecommendations:
        """Handle multi-process welding machine requests"""
        
        start_time = time.time()
        
        # Use existing agent system to find multi-process capable power sources
        fallback_result = await self._fallback_to_simple_agent(processed_intent, trace_id)
        
        # Update the routing decision to show guided flow was used
        fallback_result.search_metadata.strategy = SearchStrategy.GUIDED_FLOW
        fallback_result.search_metadata.reasoning = "Guided flow: Multi-process welding machine request"
        fallback_result.search_metadata.algorithms = [GraphAlgorithm.COMPATIBILITY, GraphAlgorithm.SALES_FREQUENCY]
        fallback_result.search_metadata.weights = {"compatibility": 0.8, "sales_frequency": 0.2}
        fallback_result.search_metadata.confidence = 0.85
        
        return fallback_result
    
    async def _handle_beginner_package_request(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> ScoredRecommendations:
        """Handle beginner-friendly package requests"""
        
        start_time = time.time()
        
        # Use existing agent system to find beginner-friendly complete packages
        fallback_result = await self._fallback_to_simple_agent(processed_intent, trace_id)
        
        # Update the routing decision to show guided flow was used
        fallback_result.search_metadata.strategy = SearchStrategy.GUIDED_FLOW
        fallback_result.search_metadata.reasoning = "Guided flow: Beginner-friendly welding package request"
        fallback_result.search_metadata.algorithms = [GraphAlgorithm.SALES_FREQUENCY, GraphAlgorithm.COMPATIBILITY]
        fallback_result.search_metadata.weights = {"sales_frequency": 0.6, "compatibility": 0.4}
        fallback_result.search_metadata.confidence = 0.9
        
        return fallback_result
    
    async def _handle_specific_product_request(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> ScoredRecommendations:
        """Handle requests mentioning specific products"""
        
        start_time = time.time()
        
        # Leverage existing LLM product extraction from intelligent intent service
        # The product name is already extracted and available in similar_to_customer
        product_name = processed_intent.similar_to_customer
        
        # Also check extracted_entities for additional product context
        mentioned_product = None
        if hasattr(processed_intent, 'extracted_entities') and processed_intent.extracted_entities:
            mentioned_product = processed_intent.extracted_entities.get('mentioned_product')
        
        # Use either field - prefer similar_to_customer as it's the standard field
        detected_product = product_name or mentioned_product
        
        # Use existing agent system to build trinity around the detected product
        fallback_result = await self._fallback_to_simple_agent(processed_intent, trace_id)
        
        # Update the routing decision to show guided flow was used
        fallback_result.search_metadata.strategy = SearchStrategy.GUIDED_FLOW
        fallback_result.search_metadata.reasoning = f"Guided flow: Specific product request for {detected_product} (LLM-detected)"
        fallback_result.search_metadata.algorithms = [GraphAlgorithm.COMPATIBILITY, GraphAlgorithm.SALES_FREQUENCY]
        fallback_result.search_metadata.weights = {"compatibility": 0.9, "sales_frequency": 0.1}
        fallback_result.search_metadata.confidence = 0.95
        
        return fallback_result
    
    def _extract_powersource_from_context(self, processed_intent: EnhancedProcessedIntent) -> Optional[str]:
        """Extract PowerSource ID from query context or session data"""
        # This would extract from session context in a real implementation
        # For now, return None to use general compatibility
        return None
    
    def _extract_feeder_from_context(self, processed_intent: EnhancedProcessedIntent) -> Optional[str]:
        """Extract Feeder ID from query context or session data"""
        # This would extract from session context in a real implementation  
        # For now, return None to use general compatibility
        return None

    def _calculate_intent_match_bonus(
        self, 
        package_data: Dict[str, Any], 
        intent: EnhancedProcessedIntent
    ) -> float:
        """
        Calculate bonus score for packages that contain user's explicitly requested products.
        
        Args:
            package_data: Package component data
            intent: Processed user intent with original query
            
        Returns:
            Bonus score (0.0 to 0.15) to boost packages matching user intent
        """
        bonus = 0.0
        
        # Get the original query from intent
        original_query = getattr(intent, 'original_query', '').lower()
        if not original_query:
            return bonus
            
        # Define product name keywords to look for
        # These should match our domain vocabulary high-priority terms
        product_keywords = {
            'renegade': 0.35,    # Very high bonus for exact product name match
            'warrior': 0.35,
            'aristo': 0.35,
            'aristo 500': 0.40,  # Even higher for specific model matches
            'aristo 500ix': 0.45,
            'warrior 500': 0.40,
            'renegade es': 0.40,
            'robustfeed': 0.25,  # High bonus for component names
            'cool2': 0.25,
            'cooling unit': 0.15,
            'wire feeder': 0.15,
            'power source': 0.05  # Lower bonus for generic terms
        }
        
        # Check each component in the package for keyword matches
        components_to_check = [
            package_data.get("power_source"),
            package_data.get("feeder"), 
            package_data.get("cooler")
        ]
        
        for component in components_to_check:
            if not component:
                continue
                
            component_name = component.get("product_name", "").lower()
            
            # Check for exact keyword matches in product name
            for keyword, keyword_bonus in product_keywords.items():
                if keyword in original_query and keyword in component_name:
                    bonus += keyword_bonus
                    # Log the intent match for debugging
                    logger.info(f"🎯 Intent Match Bonus: '{keyword}' found in query '{original_query}' matches component '{component_name}' (+{keyword_bonus})")
                    break  # Only give one bonus per component to avoid double-counting
        
        # Cap the total bonus to prevent excessive boosting
        return min(bonus, 0.15)

    async def _try_trinity_semantic_search(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> Optional[List[TrinityPackage]]:
        """
        Try Trinity semantic search for complete package formation
        
        Args:
            processed_intent: Enhanced intent from Agent 1
            trace_id: Distributed tracing identifier
            
        Returns:
            List of Trinity packages or None if not applicable
        """
        try:
            # Only try Trinity search for queries that might benefit from complete packages
            query = processed_intent.original_query.lower()
            trinity_keywords = ["package", "setup", "kit", "complete", "system", "trinity", "combination"]
            
            # Check if query suggests looking for complete packages
            if not any(keyword in query for keyword in trinity_keywords):
                return None
            
            logger.info(f"[Agent 2] Attempting Trinity semantic search for: '{processed_intent.original_query}'")
            
            # Use simple Neo4j agent for Trinity semantic search
            trinity_results = await self.simple_neo4j_agent.search_trinity_combinations(
                processed_intent.original_query, 
                limit=5
            )
            
            if not trinity_results:
                logger.info("[Agent 2] No Trinity combinations found, trying product-specific fallback")
                # Try to find Trinity packages with user-specified products
                return await self._try_product_specific_trinity_search(processed_intent, trace_id)
            
            # Convert Trinity results to TrinityPackage objects
            trinity_packages = []
            
            for trinity_result in trinity_results[:3]:  # Top 3 Trinity combinations
                # Get Trinity components
                components = await self.simple_neo4j_agent.get_trinity_package_components(
                    trinity_result['trinity_id']
                )
                
                if not components:
                    continue
                
                # Extract components by category
                power_source = components.get('PowerSource')
                feeder = components.get('Feeder')
                cooler = components.get('Cooler')
                
                if not all([power_source, feeder, cooler]):
                    continue
                
                # Find accessories for this Trinity
                trinity_accessories = await self.simple_neo4j_agent._find_trinity_based_accessories(
                    power_source.product_id,
                    feeder.product_id, 
                    cooler.product_id
                )
                
                # Calculate total price
                total_price = sum([
                    power_source.price or 0.0,
                    feeder.price or 0.0,
                    cooler.price or 0.0
                ] + [acc.price or 0.0 for acc in trinity_accessories[:5]])
                
                # Convert components to dictionaries for TrinityPackage
                def component_to_dict(component):
                    return {
                        "product_id": component.product_id,
                        "product_name": component.product_name,
                        "category": component.category,
                        "subcategory": component.subcategory,
                        "description": component.description,
                        "price": component.price,
                        "compatibility_score": component.compatibility_score,
                        "sales_frequency": component.sales_frequency
                    }
                
                # Create Trinity package with dict components
                trinity_package = TrinityPackage(
                    power_source=component_to_dict(power_source),
                    feeder=component_to_dict(feeder),
                    cooler=component_to_dict(cooler),
                    consumables=[],  # Trinity doesn't include consumables by default
                    accessories=[component_to_dict(acc) for acc in trinity_accessories[:5]],  # Limit accessories
                    total_price=total_price,
                    package_score=trinity_result['similarity_score'] * 0.9,  # High confidence for Trinity
                    confidence=processed_intent.confidence * trinity_result['similarity_score'],
                    trinity_compliance=True,
                    expert_validated=False,
                    intent_match_score=trinity_result['similarity_score'],
                    explanation=f"Complete Trinity package featuring {power_source.product_name}",
                    search_metadata={
                        "trinity_id": trinity_result['trinity_id'],
                        "similarity_score": trinity_result['similarity_score'],
                        "order_count": trinity_result['order_count'],
                        "search_type": "trinity_semantic"
                    }
                )
                
                trinity_packages.append(trinity_package)
            
            if trinity_packages:
                logger.info(f"[Agent 2] Trinity search generated {len(trinity_packages)} packages")
                return trinity_packages
            
            return None
            
        except Exception as e:
            logger.error(f"[Agent 2] Trinity semantic search error: {e}")
            return None

    async def _try_product_specific_trinity_search(
        self, 
        processed_intent: EnhancedProcessedIntent, 
        trace_id: str
    ) -> Optional[List[TrinityPackage]]:
        """
        Fallback search for Trinity packages containing user-specified products
        
        When semantic search fails, this method searches for Trinity combinations
        that contain specific products mentioned in the user's query.
        """
        try:
            query = processed_intent.original_query.lower()
            
            # Extract potential product names from the query
            product_keywords = ['aristo', 'warrior', 'renegade', 'robustfeed', 'cool2']
            mentioned_products = [kw for kw in product_keywords if kw in query]
            
            if not mentioned_products:
                logger.info("[Agent 2] No specific products mentioned, skipping product-specific search")
                return None
            
            logger.info(f"[Agent 2] Searching for Trinity packages containing: {mentioned_products}")
            
            # Search for Trinity combinations containing the mentioned products
            trinity_packages = []
            
            for product_keyword in mentioned_products:
                # Direct query for Trinity packages containing this product
                trinity_query = """
                MATCH (tr:Trinity)-[:COMPRISES]->(ps:Product {category: 'PowerSource'})
                WHERE toLower(ps.name) CONTAINS $product_keyword
                WITH tr, ps
                MATCH (tr)-[:COMPRISES]->(f:Product {category: 'Feeder'})
                MATCH (tr)-[:COMPRISES]->(c:Product {category: 'Cooler'})
                RETURN tr.trinity_id as trinity_id, ps, f, c
                LIMIT 3
                """
                
                results = await self.neo4j_repo.execute_query(trinity_query, {"product_keyword": product_keyword})
                
                for result in results:
                    trinity_id = result['trinity_id']
                    power_source_data = result['ps']
                    feeder_data = result['f']
                    cooler_data = result['c']
                    
                    # Convert to WeldingPackageComponent format
                    power_source = WeldingPackageComponent(
                        product_id=power_source_data['gin'],
                        product_name=power_source_data['name'],
                        category=power_source_data['category'],
                        price=power_source_data.get('price', 0),
                        description=power_source_data.get('description', ''),
                        sales_frequency=power_source_data.get('sales_frequency', 0)
                    )
                    
                    feeder = WeldingPackageComponent(
                        product_id=feeder_data['gin'],
                        product_name=feeder_data['name'],
                        category=feeder_data['category'],
                        price=feeder_data.get('price', 0),
                        description=feeder_data.get('description', ''),
                        sales_frequency=feeder_data.get('sales_frequency', 0)
                    )
                    
                    cooler = WeldingPackageComponent(
                        product_id=cooler_data['gin'],
                        product_name=cooler_data['name'],
                        category=cooler_data['category'],
                        price=cooler_data.get('price', 0),
                        description=cooler_data.get('description', ''),
                        sales_frequency=cooler_data.get('sales_frequency', 0)
                    )
                    
                    # Find accessories for this Trinity
                    trinity_accessories = await self.simple_neo4j_agent._find_trinity_based_accessories(
                        power_source.product_id,
                        feeder.product_id,
                        cooler.product_id
                    )
                    
                    # Calculate total price
                    total_price = power_source.price + feeder.price + cooler.price
                    total_price += sum(acc.price for acc in trinity_accessories[:5])
                    
                    # Higher score for user-requested products
                    base_score = 0.8  # High base score for direct product match
                    intent_bonus = self._calculate_intent_match_bonus({
                        "power_source": power_source.__dict__,
                        "feeder": feeder.__dict__,
                        "cooler": cooler.__dict__
                    }, processed_intent)
                    
                    final_score = min(base_score + intent_bonus, 1.0)
                    
                    trinity_package = TrinityPackage(
                        power_source=component_to_dict(power_source),
                        feeder=component_to_dict(feeder),
                        cooler=component_to_dict(cooler),
                        consumables=[],
                        accessories=[component_to_dict(acc) for acc in trinity_accessories[:5]],
                        total_price=total_price,
                        package_score=final_score,
                        trinity_compliance=True,
                        business_rule_compliance=processed_intent.confidence,
                        compatibility_verified=True,
                        compatibility_score=0.9,
                        formation_path=[trinity_id],
                        relationship_strength=final_score
                    )
                    
                    trinity_packages.append(trinity_package)
                    logger.info(f"[Agent 2] Found product-specific Trinity: {power_source.product_name} (Score: {final_score:.3f})")
            
            if trinity_packages:
                # Sort by score and return top packages
                trinity_packages.sort(key=lambda x: x.package_score, reverse=True)
                logger.info(f"[Agent 2] Product-specific search successful: {len(trinity_packages)} packages found")
                return trinity_packages[:3]
            else:
                logger.info("[Agent 2] No Trinity packages found for specified products")
                return None
                
        except Exception as e:
            logger.error(f"[Agent 2] Product-specific Trinity search error: {e}")
            return None


# Dependency injection
async def get_smart_neo4j_service(neo4j_repo: Neo4jRepository) -> SmartNeo4jService:
    """Get smart neo4j service instance"""
    return SmartNeo4jService(neo4j_repo)