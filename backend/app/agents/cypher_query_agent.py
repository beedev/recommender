"""
Dynamic Cypher Query Agent for Neo4j Database Operations.

Generates and executes optimized Cypher queries based on extracted welding intent.
Handles multiple query strategies with intelligent fallback mechanisms.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

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
    ExtractedIntent, QueryGenerationState, CypherQuery, QueryStrategy, QueryType,
    RecommendationItem, WeldingProcess, Material, Industry
)
from ..database.repositories import Neo4jRepository
from ..core.config import settings

logger = logging.getLogger(__name__)


class CypherQueryAgent:
    """
    Agent responsible for generating and executing dynamic Cypher queries.
    
    Capabilities:
    - Multi-strategy query generation
    - Intelligent fallback mechanisms
    - Fuzzy matching and text search
    - Performance optimization
    - Result ranking and scoring
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        """Initialize the Cypher query agent"""
        
        self.neo4j_repo = neo4j_repo
        
        # Query templates for different strategies
        self._init_query_templates()
        
        # Scoring weights for different factors
        self.scoring_weights = {
            "exact_match": 1.0,
            "fuzzy_match": 0.8,
            "text_search": 0.6,
            "sales_frequency": 0.3,
            "compatibility": 0.4,
            "industry_match": 0.5,
            "recent_popularity": 0.2
        }
        
    def _init_query_templates(self):
        """Initialize Cypher query templates"""
        
        self.query_templates = {
            QueryType.BASIC_PROPERTY: """
                MATCH (p:Product {{category: $category}})
                WHERE {conditions}
                OPTIONAL MATCH (p)-[s:SOLD_WITH]->(other)
                WITH p, COUNT(s) as sales_count
                RETURN p, sales_count
                ORDER BY sales_count DESC, p.product_id
                LIMIT $limit
            """,
            
            QueryType.RANGE_BASED: """
                MATCH (p:Product {{category: $category}})
                WHERE {range_conditions}
                OPTIONAL MATCH (p)-[s:SOLD_WITH]->(other)
                WITH p, COUNT(s) as sales_count
                RETURN p, sales_count
                ORDER BY sales_count DESC
                LIMIT $limit
            """,
            
            QueryType.TEXT_SEARCH: """
                MATCH (p:Product)
                WHERE {text_conditions}
                OPTIONAL MATCH (p)-[s:SOLD_WITH]->(other)
                WITH p, COUNT(s) as sales_count,
                     {relevance_score} as relevance
                RETURN p, sales_count, relevance
                ORDER BY relevance DESC, sales_count DESC
                LIMIT $limit
            """,
            
            QueryType.INDUSTRY_BASED: """
                MATCH (p:Product)-[:USED_IN_INDUSTRY]->(i:Industry {{name: $industry}})
                WHERE {additional_conditions}
                OPTIONAL MATCH (p)-[s:SOLD_WITH]->(other)
                WITH p, COUNT(s) as sales_count
                RETURN p, sales_count
                ORDER BY sales_count DESC
                LIMIT $limit
            """,
            
            QueryType.SIMILAR_PURCHASE: """
                MATCH (c:Customer)-[:MADE]->(o:Order)-[:CONTAINS]->(p:Product)
                WHERE {similarity_conditions}
                OPTIONAL MATCH (p)<-[:CONTAINS]-(other_order:Order)-[:CONTAINS]->(other:Product)
                WHERE other <> p
                WITH p, COUNT(other) as cooccurrence_count, COUNT(DISTINCT c) as customer_count
                RETURN p, cooccurrence_count as sales_count, customer_count
                ORDER BY customer_count DESC, cooccurrence_count DESC
                LIMIT $limit
            """,
            
            QueryType.COMPATIBILITY: """
                MATCH (ps:Product {{category: 'PowerSource'}})
                WHERE {powersource_conditions}
                MATCH (ps)-[:COMPATIBLE_WITH]->(comp:Product)
                WHERE comp.category IN $component_categories
                {component_conditions}
                OPTIONAL MATCH (comp)-[s:SOLD_WITH]->(other)
                WITH comp, COUNT(s) as sales_count,
                     COUNT(DISTINCT ps) as compatibility_count
                RETURN comp, sales_count, compatibility_count
                ORDER BY compatibility_count DESC, sales_count DESC
                LIMIT $limit
            """,
            
            QueryType.HYBRID: """
                CALL {{
                    // Strategy 1: Exact property match
                    MATCH (p1:Product) WHERE {exact_conditions}
                    OPTIONAL MATCH (p1)-[s1:SOLD_WITH]->(other1)
                    WITH p1 as product, COUNT(s1) as sales, 1.0 as strategy_weight
                    RETURN product, sales, strategy_weight
                    
                    UNION ALL
                    
                    // Strategy 2: Text search
                    MATCH (p2:Product) WHERE {text_conditions}
                    OPTIONAL MATCH (p2)-[s2:SOLD_WITH]->(other2)
                    WITH p2 as product, COUNT(s2) as sales, 0.7 as strategy_weight
                    RETURN product, sales, strategy_weight
                    
                    UNION ALL
                    
                    // Strategy 3: Industry match
                    MATCH (p3:Product)-[:USED_IN_INDUSTRY]->(i:Industry)
                    WHERE {industry_conditions}
                    OPTIONAL MATCH (p3)-[s3:SOLD_WITH]->(other3)
                    WITH p3 as product, COUNT(s3) as sales, 0.5 as strategy_weight
                    RETURN product, sales, strategy_weight
                }}
                WITH product, MAX(sales) as max_sales, MAX(strategy_weight) as max_weight
                RETURN product, max_sales, max_weight
                ORDER BY max_weight DESC, max_sales DESC
                LIMIT $limit
            """
        }
    
    @traceable(name="cypher_query_generation")
    async def generate_and_execute_queries(
        self, 
        state: QueryGenerationState
    ) -> QueryGenerationState:
        """
        Generate and execute Cypher queries based on extracted intent.
        
        Args:
            state: Current query generation state
            
        Returns:
            Updated state with query results
        """
        try:
            intent = state.intent
            if not intent:
                raise ValueError("No intent provided for query generation")
            
            logger.info(f"Generating queries for intent with confidence: {intent.confidence}")
            
            # Determine query strategy
            if not state.query_strategy:
                state.query_strategy = self._determine_query_strategy(intent)
            
            # Generate primary query
            primary_query = await self._generate_primary_query(intent, state.query_strategy)
            state.primary_query = primary_query
            state.generated_queries.append(primary_query)
            
            # Execute primary query
            await self._execute_query(primary_query)
            
            # Check if fallback is needed
            if self._should_use_fallback(primary_query, intent):
                logger.info("Primary query results insufficient, generating fallback queries")
                
                fallback_queries = await self._generate_fallback_queries(intent, state.query_strategy)
                state.fallback_queries = fallback_queries
                state.generated_queries.extend(fallback_queries)
                
                # Execute best fallback query
                if fallback_queries:
                    best_fallback = fallback_queries[0]
                    await self._execute_query(best_fallback)
                    state.fallback_used = True
            
            # Combine and process results
            state.raw_results = self._combine_query_results(state.generated_queries)
            state.processed_results = await self._process_and_rank_results(
                state.raw_results, intent
            )
            
            # Calculate quality metrics
            state.result_quality_score = self._calculate_quality_score(
                state.processed_results, intent
            )
            state.coverage_score = self._calculate_coverage_score(
                state.processed_results, intent
            )
            state.diversity_score = self._calculate_diversity_score(state.processed_results)
            
            state.execution_successful = True
            
            logger.info(f"Query execution completed. Found {len(state.processed_results)} results")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in query generation/execution: {e}")
            state.errors.append(f"Query execution failed: {str(e)}")
            state.execution_successful = False
            return state
    
    def _determine_query_strategy(self, intent: ExtractedIntent) -> QueryStrategy:
        """Determine the best query strategy based on intent"""
        
        # Analyze intent completeness and choose strategy
        has_exact_params = bool(
            intent.welding_process or 
            intent.power_watts or 
            intent.current_amps or
            intent.material
        )
        
        has_similarity_refs = bool(
            intent.similar_to_customer or 
            intent.similar_to_purchase or
            intent.similar_to_package
        )
        
        has_industry_context = bool(intent.industry or intent.application)
        
        # Determine primary strategy
        if has_similarity_refs:
            primary = QueryType.SIMILAR_PURCHASE
        elif has_exact_params and intent.confidence > 0.7:
            primary = QueryType.BASIC_PROPERTY
        elif intent.power_watts or intent.current_amps or intent.voltage:
            primary = QueryType.RANGE_BASED
        elif has_industry_context:
            primary = QueryType.INDUSTRY_BASED
        elif intent.confidence < 0.5:
            primary = QueryType.TEXT_SEARCH
        else:
            primary = QueryType.HYBRID
        
        # Determine fallback strategies
        fallbacks = []
        if primary != QueryType.TEXT_SEARCH:
            fallbacks.append(QueryType.TEXT_SEARCH)
        if primary != QueryType.INDUSTRY_BASED and has_industry_context:
            fallbacks.append(QueryType.INDUSTRY_BASED)
        if primary != QueryType.BASIC_PROPERTY and has_exact_params:
            fallbacks.append(QueryType.BASIC_PROPERTY)
        
        return QueryStrategy(
            primary_strategy=primary,
            fallback_strategies=fallbacks,
            use_fuzzy_matching=intent.confidence < 0.8,
            use_text_search=intent.confidence < 0.6,
            prefer_sales_frequency=True,
            prefer_compatibility=True,
            prefer_industry_match=has_industry_context
        )
    
    async def _generate_primary_query(
        self, 
        intent: ExtractedIntent, 
        strategy: QueryStrategy
    ) -> CypherQuery:
        """Generate the primary Cypher query"""
        
        query_type = strategy.primary_strategy
        template = self.query_templates[query_type]
        
        # Build conditions based on intent
        conditions, parameters = self._build_query_conditions(intent, query_type)
        
        # Format the template
        if query_type == QueryType.BASIC_PROPERTY:
            query = template.format(conditions=conditions)
            parameters.update({
                "category": self._get_primary_category(intent),
                "limit": strategy.max_results
            })
            
        elif query_type == QueryType.RANGE_BASED:
            query = template.format(range_conditions=conditions)
            parameters.update({
                "category": self._get_primary_category(intent),
                "limit": strategy.max_results
            })
            
        elif query_type == QueryType.TEXT_SEARCH:
            relevance_score = self._build_relevance_score(intent)
            query = template.format(
                text_conditions=conditions,
                relevance_score=relevance_score
            )
            parameters["limit"] = strategy.max_results
            
        elif query_type == QueryType.INDUSTRY_BASED:
            query = template.format(additional_conditions=conditions)
            parameters.update({
                "industry": intent.industry.value if intent.industry else "",
                "limit": strategy.max_results
            })
            
        elif query_type == QueryType.SIMILAR_PURCHASE:
            query = template.format(similarity_conditions=conditions)
            parameters["limit"] = strategy.max_results
            
        elif query_type == QueryType.COMPATIBILITY:
            query = template.format(
                powersource_conditions=conditions,
                component_conditions=""  # Can be extended
            )
            parameters.update({
                "component_categories": ["Feeder", "Cooler", "Torch", "Accessory"],
                "limit": strategy.max_results
            })
            
        elif query_type == QueryType.HYBRID:
            exact_cond, text_cond, industry_cond = self._build_hybrid_conditions(intent)
            query = template.format(
                exact_conditions=exact_cond,
                text_conditions=text_cond,
                industry_conditions=industry_cond
            )
            parameters["limit"] = strategy.max_results
        
        return CypherQuery(
            query=query,
            parameters=parameters,
            query_type=query_type,
            description=f"Primary {query_type.value} query for welding recommendations",
            expected_results=strategy.max_results,
            confidence=self._estimate_query_confidence(intent, query_type)
        )
    
    def _build_query_conditions(
        self, 
        intent: ExtractedIntent, 
        query_type: QueryType
    ) -> Tuple[str, Dict[str, Any]]:
        """Build WHERE conditions and parameters for the query"""
        
        conditions = []
        parameters = {}
        
        # Process conditions
        if intent.welding_process:
            process_conditions = []
            for i, process in enumerate(intent.welding_process):
                param_name = f"process_{i}"
                process_conditions.append(f"p.description CONTAINS ${param_name}")
                parameters[param_name] = process.value
            
            if process_conditions:
                conditions.append(f"({' OR '.join(process_conditions)})")
        
        # Material conditions
        if intent.material:
            conditions.append("p.material_compatibility CONTAINS $material")
            parameters["material"] = intent.material.value
        
        # Power range conditions (for range-based queries)
        if query_type == QueryType.RANGE_BASED:
            if intent.power_watts:
                conditions.append("(p.min_power <= $power_watts <= p.max_power OR p.power_watts >= $min_power_threshold)")
                parameters["power_watts"] = intent.power_watts
                parameters["min_power_threshold"] = intent.power_watts * 0.8
            
            if intent.current_amps:
                conditions.append("(p.min_current <= $current_amps <= p.max_current OR p.max_current >= $min_current_threshold)")
                parameters["current_amps"] = intent.current_amps
                parameters["min_current_threshold"] = intent.current_amps * 0.8
            
            if intent.voltage:
                conditions.append("(p.min_voltage <= $voltage <= p.max_voltage OR p.voltage = $voltage)")
                parameters["voltage"] = intent.voltage
        
        # Text search conditions
        if query_type == QueryType.TEXT_SEARCH:
            text_conditions = []
            
            if intent.welding_process:
                for i, process in enumerate(intent.welding_process):
                    param_name = f"text_process_{i}"
                    text_conditions.append(f"toLower(p.description) CONTAINS toLower(${param_name})")
                    parameters[param_name] = process.value
            
            if intent.material:
                text_conditions.append("toLower(p.description) CONTAINS toLower($text_material)")
                parameters["text_material"] = intent.material.value
            
            if intent.application:
                text_conditions.append("toLower(p.description) CONTAINS toLower($text_application)")
                parameters["text_application"] = intent.application
            
            if text_conditions:
                conditions.append(f"({' OR '.join(text_conditions)})")
        
        # Similarity conditions
        if query_type == QueryType.SIMILAR_PURCHASE:
            if intent.similar_to_customer:
                conditions.append("c.customer_id = $customer_id OR c.industry = $customer_industry")
                parameters["customer_id"] = intent.similar_to_customer
                # Could add industry lookup based on customer
            
            if intent.similar_to_purchase:
                conditions.append("pkg.package_id = $package_id")
                parameters["package_id"] = intent.similar_to_purchase
        
        # Combine conditions
        final_condition = " AND ".join(conditions) if conditions else "true"
        
        return final_condition, parameters
    
    def _build_hybrid_conditions(self, intent: ExtractedIntent) -> Tuple[str, str, str]:
        """Build conditions for hybrid query strategy"""
        
        # Exact match conditions
        exact_conditions = []
        if intent.welding_process:
            process_list = [f"'{p.value}'" for p in intent.welding_process]
            exact_conditions.append(f"p.welding_process IN [{','.join(process_list)}]")
        
        if intent.material:
            exact_conditions.append(f"p.material_compatibility CONTAINS '{intent.material.value}'")
            
        exact_cond = " AND ".join(exact_conditions) if exact_conditions else "true"
        
        # Text search conditions
        text_conditions = []
        if intent.welding_process:
            for process in intent.welding_process:
                text_conditions.append(f"toLower(p.description) CONTAINS '{process.value.lower()}'")
        
        if intent.material:
            text_conditions.append(f"toLower(p.description) CONTAINS '{intent.material.value.lower()}'")
            
        text_cond = " OR ".join(text_conditions) if text_conditions else "true"
        
        # Industry conditions
        industry_cond = f"i.name = '{intent.industry.value}'" if intent.industry else "true"
        
        return exact_cond, text_cond, industry_cond
    
    def _build_relevance_score(self, intent: ExtractedIntent) -> str:
        """Build relevance scoring expression for text search"""
        
        score_components = []
        
        # Process match scoring
        if intent.welding_process:
            for process in intent.welding_process:
                score_components.append(
                    f"CASE WHEN toLower(p.description) CONTAINS '{process.value.lower()}' THEN 3.0 ELSE 0.0 END"
                )
        
        # Material match scoring
        if intent.material:
            score_components.append(
                f"CASE WHEN toLower(p.description) CONTAINS '{intent.material.value.lower()}' THEN 2.0 ELSE 0.0 END"
            )
        
        # Power range scoring
        if intent.power_watts:
            score_components.append(
                f"CASE WHEN p.power_watts >= {intent.power_watts * 0.8} AND p.power_watts <= {intent.power_watts * 1.2} THEN 1.5 ELSE 0.0 END"
            )
        
        if score_components:
            return " + ".join(score_components)
        else:
            return "1.0"
    
    async def _generate_fallback_queries(
        self, 
        intent: ExtractedIntent, 
        strategy: QueryStrategy
    ) -> List[CypherQuery]:
        """Generate fallback queries"""
        
        fallback_queries = []
        
        for fallback_type in strategy.fallback_strategies:
            try:
                # Create fallback strategy
                fallback_strategy = QueryStrategy(
                    primary_strategy=fallback_type,
                    max_results=strategy.max_results // 2,  # Fewer results for fallbacks
                    use_fuzzy_matching=True,
                    use_text_search=True
                )
                
                # Generate fallback query
                fallback_query = await self._generate_primary_query(intent, fallback_strategy)
                fallback_query.description = f"Fallback {fallback_type.value} query"
                fallback_query.confidence *= 0.7  # Lower confidence for fallbacks
                
                fallback_queries.append(fallback_query)
                
            except Exception as e:
                logger.warning(f"Failed to generate fallback query {fallback_type}: {e}")
                continue
        
        return fallback_queries
    
    async def _execute_query(self, query: CypherQuery) -> None:
        """Execute a Cypher query and update its results"""
        
        try:
            start_time = time.time()
            
            logger.debug(f"Executing query: {query.query[:100]}...")
            
            # Execute the query
            result = await self.neo4j_repo.connection.execute_query(
                query.query, 
                query.parameters
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update query with results
            query.execution_time_ms = execution_time
            query.result_count = len(result)
            query.success = True
            
            # Store raw results in query object for processing
            setattr(query, '_raw_results', result)
            
            logger.info(f"Query executed successfully: {query.result_count} results in {execution_time:.2f}ms")
            
        except Exception as e:
            query.success = False
            query.error_message = str(e)
            logger.error(f"Query execution failed: {e}")
            setattr(query, '_raw_results', [])
    
    def _should_use_fallback(self, primary_query: CypherQuery, intent: ExtractedIntent) -> bool:
        """Determine if fallback queries should be used"""
        
        if not primary_query.success:
            return True
        
        if primary_query.result_count < 3:
            return True
        
        if intent.confidence < 0.6 and primary_query.result_count < 10:
            return True
        
        return False
    
    def _combine_query_results(self, queries: List[CypherQuery]) -> List[Dict[str, Any]]:
        """Combine results from multiple queries"""
        
        combined_results = []
        seen_product_ids = set()
        
        # Process queries by priority (primary first, then fallbacks)
        for query in queries:
            if not query.success:
                continue
                
            raw_results = getattr(query, '_raw_results', [])
            
            for record in raw_results:
                try:
                    product_data = dict(record["p"]) if "p" in record else dict(record["product"])
                    product_id = product_data.get("product_id")
                    
                    if product_id and product_id not in seen_product_ids:
                        # Add query metadata
                        product_data["_query_type"] = query.query_type.value
                        product_data["_query_confidence"] = query.confidence
                        product_data["_sales_count"] = record.get("sales_count", record.get("max_sales", 0))
                        
                        # Add any additional scoring data
                        if "relevance" in record:
                            product_data["_relevance_score"] = record["relevance"]
                        if "compatibility_count" in record:
                            product_data["_compatibility_count"] = record["compatibility_count"]
                        
                        combined_results.append(product_data)
                        seen_product_ids.add(product_id)
                        
                except Exception as e:
                    logger.warning(f"Error processing query result: {e}")
                    continue
        
        logger.info(f"Combined {len(combined_results)} unique results from {len(queries)} queries")
        return combined_results
    
    async def _process_and_rank_results(
        self, 
        raw_results: List[Dict[str, Any]], 
        intent: ExtractedIntent
    ) -> List[RecommendationItem]:
        """Process and rank the results"""
        
        processed_items = []
        
        for result in raw_results:
            try:
                # Create recommendation item
                item = RecommendationItem(
                    product_id=result.get("product_id", ""),
                    product_name=result.get("name", result.get("product_name", "")),
                    category=result.get("category", ""),
                    subcategory=result.get("subcategory"),
                    manufacturer=result.get("manufacturer"),
                    description=result.get("description"),
                    price=result.get("price")
                )
                
                # Calculate scores
                item.relevance_score = self._calculate_relevance_score(result, intent)
                item.popularity_score = self._calculate_popularity_score(result)
                item.compatibility_score = self._calculate_compatibility_score(result, intent)
                item.overall_score = self._calculate_overall_score(item)
                
                # Generate explanation
                item.recommendation_reason = self._generate_recommendation_reason(result, intent)
                item.match_criteria = self._extract_match_criteria(result, intent)
                
                # Add Neo4j metadata
                item.node_labels = result.get("_labels", [])
                item.relationship_context = {
                    "query_type": result.get("_query_type", ""),
                    "sales_count": result.get("_sales_count", 0),
                    "relevance_score": result.get("_relevance_score", 0.0)
                }
                
                processed_items.append(item)
                
            except Exception as e:
                logger.warning(f"Error processing result item: {e}")
                continue
        
        # Sort by overall score
        processed_items.sort(key=lambda x: x.overall_score, reverse=True)
        
        return processed_items
    
    def _calculate_relevance_score(self, result: Dict[str, Any], intent: ExtractedIntent) -> float:
        """Calculate relevance score based on intent matching"""
        
        score = 0.0
        
        # Process matching
        if intent.welding_process:
            description = result.get("description", "").lower()
            for process in intent.welding_process:
                if process.value.lower() in description:
                    score += 0.3
        
        # Material matching
        if intent.material:
            material_compat = result.get("material_compatibility", "").lower()
            description = result.get("description", "").lower()
            
            if intent.material.value.lower() in material_compat or intent.material.value.lower() in description:
                score += 0.3
        
        # Power range matching
        if intent.power_watts:
            product_power = result.get("power_watts")
            if product_power:
                power_diff = abs(product_power - intent.power_watts) / intent.power_watts
                score += max(0, 0.2 * (1 - power_diff))
        
        # Current range matching
        if intent.current_amps:
            max_current = result.get("max_current")
            min_current = result.get("min_current")
            
            if max_current and min_current:
                if min_current <= intent.current_amps <= max_current:
                    score += 0.2
                else:
                    # Partial score for close ranges
                    if intent.current_amps >= min_current * 0.8 and intent.current_amps <= max_current * 1.2:
                        score += 0.1
        
        # Query type bonus
        query_confidence = result.get("_query_confidence", 0.0)
        score += query_confidence * 0.1
        
        return min(score, 1.0)
    
    def _calculate_popularity_score(self, result: Dict[str, Any]) -> float:
        """Calculate popularity score based on sales data"""
        
        sales_count = result.get("_sales_count", 0)
        
        # Normalize sales count to 0-1 scale
        # Assuming max sales count of 1000 for normalization
        max_sales = 1000
        base_score = min(sales_count / max_sales, 1.0)
        
        # Boost for high sales
        if sales_count > 100:
            base_score += 0.1
        elif sales_count > 50:
            base_score += 0.05
        
        return min(base_score, 1.0)
    
    def _calculate_compatibility_score(self, result: Dict[str, Any], intent: ExtractedIntent) -> float:
        """Calculate compatibility score"""
        
        score = 0.5  # Base compatibility score
        
        # Compatibility relationship bonus
        compatibility_count = result.get("_compatibility_count", 0)
        if compatibility_count > 0:
            score += min(compatibility_count * 0.1, 0.3)
        
        # Industry matching bonus
        if intent.industry:
            # Would need to check industry relationships in a real implementation
            pass
        
        # Category-specific compatibility
        category = result.get("category", "")
        if category == "PowerSource" and (intent.power_watts or intent.current_amps):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_overall_score(self, item: RecommendationItem) -> float:
        """Calculate weighted overall score"""
        
        weights = {
            "relevance": 0.5,
            "popularity": 0.2,
            "compatibility": 0.3
        }
        
        return (
            item.relevance_score * weights["relevance"] +
            item.popularity_score * weights["popularity"] +
            item.compatibility_score * weights["compatibility"]
        )
    
    def _generate_recommendation_reason(self, result: Dict[str, Any], intent: ExtractedIntent) -> str:
        """Generate human-readable recommendation reason"""
        
        reasons = []
        
        # Process matching
        if intent.welding_process:
            description = result.get("description", "").lower()
            matching_processes = [
                p.value for p in intent.welding_process
                if p.value.lower() in description
            ]
            if matching_processes:
                reasons.append(f"Supports {', '.join(matching_processes)} welding")
        
        # Material compatibility
        if intent.material:
            material_compat = result.get("material_compatibility", "").lower()
            if intent.material.value.lower() in material_compat:
                reasons.append(f"Compatible with {intent.material.value}")
        
        # Sales popularity
        sales_count = result.get("_sales_count", 0)
        if sales_count > 50:
            reasons.append(f"Popular choice ({sales_count} recent sales)")
        elif sales_count > 10:
            reasons.append(f"Proven option ({sales_count} sales)")
        
        # Power matching
        if intent.power_watts:
            product_power = result.get("power_watts")
            if product_power and abs(product_power - intent.power_watts) < intent.power_watts * 0.2:
                reasons.append(f"Matches power requirement (~{intent.power_watts}W)")
        
        # Query type context
        query_type = result.get("_query_type", "")
        if query_type == "industry_based":
            reasons.append("Industry-specific recommendation")
        elif query_type == "similar_purchase":
            reasons.append("Based on similar purchases")
        
        return "; ".join(reasons) if reasons else "Compatible with your requirements"
    
    def _extract_match_criteria(self, result: Dict[str, Any], intent: ExtractedIntent) -> List[str]:
        """Extract specific match criteria"""
        
        criteria = []
        
        if intent.welding_process:
            criteria.append("welding_process")
        
        if intent.material:
            criteria.append("material_compatibility")
        
        if intent.power_watts or intent.current_amps:
            criteria.append("power_requirements")
        
        if intent.industry:
            criteria.append("industry_application")
        
        if result.get("_sales_count", 0) > 20:
            criteria.append("sales_frequency")
        
        return criteria
    
    def _calculate_quality_score(self, results: List[RecommendationItem], intent: ExtractedIntent) -> float:
        """Calculate overall quality score for the result set"""
        
        if not results:
            return 0.0
        
        # Average relevance score
        avg_relevance = sum(item.relevance_score for item in results) / len(results)
        
        # Top result quality (emphasize best matches)
        top_quality = results[0].overall_score if results else 0.0
        
        # Result count adequacy
        count_score = min(len(results) / 10, 1.0)  # Prefer 10+ results
        
        return (avg_relevance * 0.4 + top_quality * 0.4 + count_score * 0.2)
    
    def _calculate_coverage_score(self, results: List[RecommendationItem], intent: ExtractedIntent) -> float:
        """Calculate how well results cover the requirements"""
        
        if not results:
            return 0.0
        
        coverage_factors = []
        
        # Process coverage
        if intent.welding_process:
            processes_covered = set()
            for item in results:
                for process in intent.welding_process:
                    if process.value.lower() in item.description.lower():
                        processes_covered.add(process.value)
            
            coverage_factors.append(len(processes_covered) / len(intent.welding_process))
        
        # Material coverage
        if intent.material:
            material_covered = any(
                intent.material.value.lower() in item.description.lower()
                for item in results
            )
            coverage_factors.append(1.0 if material_covered else 0.5)
        
        # Power range coverage
        if intent.power_watts:
            power_covered = any(
                hasattr(item, 'power_watts') and item.power_watts and
                abs(item.power_watts - intent.power_watts) < intent.power_watts * 0.3
                for item in results
            )
            coverage_factors.append(1.0 if power_covered else 0.3)
        
        return sum(coverage_factors) / len(coverage_factors) if coverage_factors else 0.5
    
    def _calculate_diversity_score(self, results: List[RecommendationItem]) -> float:
        """Calculate diversity in the result set"""
        
        if len(results) < 2:
            return 1.0 if results else 0.0
        
        # Category diversity
        categories = set(item.category for item in results)
        category_diversity = len(categories) / min(len(results), 5)  # Max 5 categories expected
        
        # Manufacturer diversity  
        manufacturers = set(item.manufacturer for item in results if item.manufacturer)
        manufacturer_diversity = len(manufacturers) / min(len(results), 3) if manufacturers else 0.5
        
        # Price range diversity (if available)
        prices = [item.price for item in results if item.price]
        price_diversity = 1.0
        if len(prices) > 1:
            price_range = max(prices) - min(prices)
            avg_price = sum(prices) / len(prices)
            price_diversity = min(price_range / avg_price, 1.0) if avg_price > 0 else 0.5
        
        return (category_diversity * 0.4 + manufacturer_diversity * 0.3 + price_diversity * 0.3)
    
    def _estimate_query_confidence(self, intent: ExtractedIntent, query_type: QueryType) -> float:
        """Estimate confidence for a query type given the intent"""
        
        base_confidence = intent.confidence
        
        # Adjust based on query type suitability
        if query_type == QueryType.BASIC_PROPERTY and intent.welding_process:
            base_confidence += 0.1
        elif query_type == QueryType.RANGE_BASED and (intent.power_watts or intent.current_amps):
            base_confidence += 0.1
        elif query_type == QueryType.INDUSTRY_BASED and intent.industry:
            base_confidence += 0.1
        elif query_type == QueryType.SIMILAR_PURCHASE and intent.similar_to_customer:
            base_confidence += 0.2
        elif query_type == QueryType.TEXT_SEARCH and intent.confidence < 0.5:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _get_primary_category(self, intent: ExtractedIntent) -> str:
        """Determine primary product category to search"""
        
        # Default to PowerSource as the main component
        if intent.power_watts or intent.current_amps or intent.voltage:
            return "PowerSource"
        
        # Could be extended based on more specific intent analysis
        return "PowerSource"