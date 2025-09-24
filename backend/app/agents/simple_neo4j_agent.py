"""
Simplified Neo4j Query Agent for 2-Agent Architecture
Converts welding intent into dynamic Cypher queries and forms packages
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import openai
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .simple_intent_agent import SimpleWeldingIntent
from ..database.repositories import Neo4jRepository
from ..services.embedding_generator import ProductEmbeddingGenerator
from ..utils.product_search_engine import ProductSearchEngine, SearchResult
from ..core.config import settings

logger = logging.getLogger(__name__)


class QueryStrategy(Enum):
    """Neo4j query strategies"""
    EXACT_MATCH = "exact"
    FUZZY_MATCH = "fuzzy"
    DESCRIPTION_SEARCH = "description"
    COMPATIBILITY_BASED = "compatibility"
    SALES_FREQUENCY = "sales"


@dataclass
class WeldingPackageComponent:
    """Component in a welding package"""
    product_id: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    price: Optional[float] = None
    compatibility_score: float = 0.0
    sales_frequency: Optional[int] = 0
    description: Optional[str] = None


@dataclass
class SimpleWeldingPackage:
    """Simplified welding package result"""
    power_source: Optional[WeldingPackageComponent] = None
    feeders: List[WeldingPackageComponent] = field(default_factory=list)
    coolers: List[WeldingPackageComponent] = field(default_factory=list)
    consumables: List[WeldingPackageComponent] = field(default_factory=list)
    accessories: List[WeldingPackageComponent] = field(default_factory=list)
    
    total_price: float = 0.0
    package_score: float = 0.0
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "power_source": self.power_source.__dict__ if self.power_source else None,
            "feeders": [f.__dict__ for f in self.feeders],
            "coolers": [c.__dict__ for c in self.coolers],
            "consumables": [c.__dict__ for c in self.consumables],
            "accessories": [a.__dict__ for a in self.accessories],
            "total_price": self.total_price,
            "package_score": self.package_score,
            "confidence": self.confidence
        }


class SimpleNeo4jAgent:
    """
    Simplified Neo4j Query Agent for the 2-agent architecture.
    
    Converts welding intent into dynamic Cypher queries,
    searches for components, and forms complete packages.
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        """Initialize with Neo4j repository"""
        self.neo4j_repo = neo4j_repo
        
        # Initialize LLM for category inference
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.2,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize OpenAI client for entity extraction
        self.llm_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize embedding generator for vector search
        self.embedding_generator = ProductEmbeddingGenerator()
        
        # Initialize product search engine
        self.search_engine = ProductSearchEngine(neo4j_repo)
        
        # Available product categories from database
        self.available_categories = [
            "PowerSource",
            "Feeder", 
            "Cooler",
            "Torch",
            "Accessory",
            "PowerSourceAccessory",
            "FeederAccessory", 
            "ConnectivityAccessory",
            "Interconnector",
            "Remote",
            "Unknown"
        ]
        
    def generate_power_source_query(self, intent: SimpleWeldingIntent) -> Tuple[str, Dict[str, Any]]:
        """
        Generate dynamic Cypher query for power source search
        
        Args:
            intent: Extracted welding intent
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        
        # Base query - using actual schema (Product nodes with PowerSource category)
        query_parts = ["MATCH (p:Product {category: 'PowerSource'})", "WHERE 1=1"]
        parameters = {}
        conditions = []
        
        # Process-based filtering (search in specifications_json or description)
        if intent.welding_process:
            process_conditions = []
            for i, process in enumerate(intent.welding_process):
                param_name = f"process_{i}"
                # Search in specifications_json and description
                process_conditions.append(f"(p.specifications_json CONTAINS ${param_name} OR p.description CONTAINS ${param_name})")
                parameters[param_name] = process
            
            if process_conditions:
                conditions.append(f"({' OR '.join(process_conditions)})")
        
        # Material-specific logic (search in description)
        if intent.material:
            conditions.append("p.description CONTAINS $material")
            parameters["material"] = intent.material
        
        # Industry/Application-based filtering
        if intent.industry:
            conditions.append("p.description CONTAINS $industry")
            parameters["industry"] = intent.industry
        
        if intent.application:
            conditions.append("p.description CONTAINS $application")
            parameters["application"] = intent.application
        
        if intent.environment:
            conditions.append("p.description CONTAINS $environment")
            parameters["environment"] = intent.environment
        
        # Combine conditions
        if conditions:
            query_parts.append("AND " + " AND ".join(conditions))
        
        # Add sales frequency and ordering
        query_parts.extend([
            "OPTIONAL MATCH (p)<-[:CONTAINS]-(t:Transaction)",
            "WITH p, COUNT(DISTINCT t.order_id) as sales_frequency",
            "RETURN p.product_id as product_id,",
            "       p.name as product_name,", 
            "       p.category as category,",
            "       p.description as description,",
            "       p.specifications_json as specifications,",
            "       p.gin as gin_number,",
            "       sales_frequency",
            "ORDER BY sales_frequency DESC, p.name ASC",
            "LIMIT 10"
        ])
        
        final_query = " ".join(query_parts)
        
        logger.debug(f"Generated power source query: {final_query}")
        logger.debug(f"Parameters: {parameters}")
        
        return final_query, parameters
    
    def generate_compatible_components_query(self, power_source_id: str, component_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generate query for compatible components (feeders, coolers, consumables)
        
        Args:
            power_source_id: Power source product ID
            component_type: Type of component (Wire_Feeder, Cooler, Consumable)
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        
        query = f"""
        MATCH (p:Product {{product_id: $power_source_id, category: 'PowerSource'}})
        MATCH (p)-[:DETERMINES]->(comp:Product {{category: $component_category}})
        OPTIONAL MATCH (comp)<-[:CONTAINS]-(t:Transaction)
        WITH comp, COUNT(DISTINCT t.order_id) as sales_frequency
        RETURN comp.product_id as product_id,
               comp.name as product_name,
               comp.category as category,
               comp.description as description,
               comp.specifications_json as specifications,
               sales_frequency
        ORDER BY sales_frequency DESC, comp.name ASC
        LIMIT 5
        """
        
        parameters = {
            "power_source_id": power_source_id,
            "component_category": component_type
        }
        
        return query, parameters
    
    def score_component_compatibility(self, component: Dict[str, Any], intent: SimpleWeldingIntent) -> float:
        """
        Score component compatibility with intent
        
        Args:
            component: Component data from Neo4j
            intent: Original welding intent
            
        Returns:
            Compatibility score 0.0-1.0
        """
        
        score = 0.5  # Base score
        
        # Process matching (search in specifications or description)
        if intent.welding_process and (component.get("specifications") or component.get("description")):
            specifications = component.get("specifications", "")
            description = component.get("description", "")
            for process in intent.welding_process:
                if (process.upper() in specifications.upper() or 
                    process.upper() in description.upper()):
                    score += 0.2
                    break
        
        # Material-specific bonus
        if intent.material and component.get("description"):
            if intent.material.lower() in component["description"].lower():
                score += 0.1
        
        # Sales frequency bonus
        sales_freq = component.get("sales_frequency", 0)
        if sales_freq > 10:
            score += 0.1
        elif sales_freq > 5:
            score += 0.05
        
        return min(score, 1.0)
    
    async def infer_required_categories(self, user_query: str) -> List[str]:
        """
        Use LLM to infer which product categories are needed based on user query
        
        Args:
            user_query: Original user query
            
        Returns:
            List of relevant product categories
        """
        
        try:
            categories_str = ", ".join(self.available_categories)
            
            system_prompt = f"""You are an expert welding equipment specialist. 
            
Given a user query about welding equipment, identify which product categories from our catalog are relevant.

Available categories:
{categories_str}

Category descriptions:
- PowerSource: Main welding power units (e.g., Aristo 500ix, Warrior 400i)
- Feeder: Wire feeding systems for MIG welding
- Cooler: Cooling systems for torches and equipment
- Torch: Welding torches and guns
- Accessory: General accessories and components
- PowerSourceAccessory: Accessories specifically for power sources (trolleys, wheels, stands)
- FeederAccessory: Accessories for wire feeders
- ConnectivityAccessory: Cables, connectors, interconnection components
- Interconnector: Connection components between equipment
- Remote: Remote controls for welding equipment
- Unknown: Unclassified products

Return ONLY a JSON array of relevant category names. Be specific and practical.

Examples:
- "I need an Aristo 500ix with a trolley" → ["PowerSource", "PowerSourceAccessory"]
- "MIG welding package with cooler" → ["PowerSource", "Feeder", "Cooler"]
- "Wire feeder for aluminum welding" → ["Feeder"]
- "Power source with interconnection cables" → ["PowerSource", "ConnectivityAccessory"]"""

            human_prompt = f"""User query: "{user_query}"

Identify which categories are needed:"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            response_text = response.content.strip()
            
            logger.info(f"LLM category inference response: {response_text}")
            
            # Parse JSON response
            try:
                categories = json.loads(response_text)
                if isinstance(categories, list):
                    # Validate categories exist in our available list
                    valid_categories = [cat for cat in categories if cat in self.available_categories]
                    logger.info(f"Inferred categories: {valid_categories}")
                    return valid_categories
                else:
                    logger.warning(f"LLM response was not a list: {response_text}")
                    return ["PowerSource"]  # Default fallback
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM category response as JSON: {e}")
                logger.error(f"Response was: {response_text}")
                return ["PowerSource"]  # Default fallback
                
        except Exception as e:
            logger.error(f"Error in category inference: {e}")
            return ["PowerSource"]  # Default fallback
    
    async def find_power_sources(self, intent: SimpleWeldingIntent) -> List[WeldingPackageComponent]:
        """
        Find compatible power sources based on intent using vector search first
        
        Args:
            intent: Welding intent from first agent
            
        Returns:
            List of power source components
        """
        
        try:
            # First, test basic Product query (actual schema)
            test_query = "MATCH (p:Product) RETURN COUNT(p) as total"
            test_results = await self.neo4j_repo.execute_query(test_query, {})
            logger.info(f"Total Product nodes in database: {test_results[0]['total'] if test_results else 0}")
            
            # Check PowerSource category specifically
            ps_query = "MATCH (p:Product {category: 'PowerSource'}) RETURN COUNT(p) as total"
            ps_results = await self.neo4j_repo.execute_query(ps_query, {})
            logger.info(f"Total PowerSource category products: {ps_results[0]['total'] if ps_results else 0}")
            
            power_sources = []
            
            # Strategy 1: Try vector search first if we have a specific product mentioned
            if hasattr(intent, 'original_query') and intent.original_query:
                vector_results = await self._search_power_sources_by_vector(intent.original_query)
                if vector_results:
                    logger.info(f"Vector search found {len(vector_results)} power sources")
                    power_sources.extend(vector_results)
            
            # Strategy 2: If vector search didn't find anything or we need more, use parameter-based search
            if not power_sources:
                logger.info("Using parameter-based power source search as fallback")
                parameter_results = await self._search_power_sources_by_parameters(intent)
                power_sources.extend(parameter_results)
            
            # Score and rank all found power sources
            for ps in power_sources:
                if hasattr(ps, '__dict__'):
                    ps.compatibility_score = self.score_component_compatibility(ps.__dict__, intent)
                else:
                    ps.compatibility_score = self.score_component_compatibility(ps, intent)
            
            # Sort by compatibility score and sales frequency (handle None values)
            power_sources.sort(key=lambda ps: (ps.compatibility_score, ps.sales_frequency or 0), reverse=True)
            
            logger.info(f"Found {len(power_sources)} power sources total")
            
            return power_sources[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Error finding power sources: {e}")
            return []
    
    async def _extract_welding_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract welding-specific entities using LLM for intelligent query formation.
        
        Args:
            query: User query text
            
        Returns:
            Dictionary with extracted entities by type
        """
        try:
            logger.info(f"[Entity Extraction] Starting LLM entity extraction for query: {query}")
            entity_extraction_prompt = f"""
            Extract welding-specific entities from this query: "{query}"
            
            Identify and extract:
            - Product names/models (e.g., "Aristo 500ix", "Warrior 400i", "PowerWave")
            - Welding processes (e.g., "MIG", "TIG", "STICK", "GMAW", "GTAW", "SMAW")
            - Materials (e.g., "aluminum", "steel", "stainless steel", "carbon steel")
            - Specifications (e.g., "500 amp", "400A", "230V", "three phase")
            - Applications (e.g., "automotive", "pipeline", "fabrication", "repair")
            - Equipment types (e.g., "feeder", "cooler", "torch", "cable")
            
            Return ONLY a JSON object with this exact format:
            {{
                "product_names": ["list", "of", "product", "names"],
                "processes": ["list", "of", "welding", "processes"],
                "materials": ["list", "of", "materials"],
                "specifications": ["list", "of", "specs"],
                "applications": ["list", "of", "applications"],
                "equipment_types": ["list", "of", "equipment", "types"]
            }}
            
            Example: "Create package with Aristo 500ix for aluminum MIG welding"
            Response: {{"product_names": ["Aristo 500ix"], "processes": ["MIG"], "materials": ["aluminum"], "specifications": [], "applications": [], "equipment_types": []}}
            """
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": entity_extraction_prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            import json
            entities = json.loads(response.choices[0].message.content.strip())
            logger.info(f"LLM extracted entities: {entities}")
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting welding entities: {e}")
            # Fallback to empty entities
            return {
                "product_names": [],
                "processes": [],
                "materials": [],
                "specifications": [],
                "applications": [],
                "equipment_types": []
            }
    

    async def _search_by_product_name(self, product_name: str, category: str) -> List[WeldingPackageComponent]:
        """
        Search for products using the optimized two-stage search engine.
        
        Args:
            product_name: Product name to search for
            category: Product category to filter by
            
        Returns:
            List of matching components
        """
        try:
            # Use the new search engine
            search_results = await self.search_engine.search_products(product_name, category)
            
            # Convert SearchResult objects to WeldingPackageComponent
            components = []
            for result in search_results:
                component = WeldingPackageComponent(
                    product_id=result.product_id,
                    product_name=result.product_name,
                    category=result.category,
                    subcategory=result.subcategory,
                    price=result.price,
                    sales_frequency=result.sales_frequency or 0,
                    description=result.description,
                    compatibility_score=result.match_score  # Use match score as compatibility
                )
                components.append(component)
            
            return components
            
        except Exception as e:
            logger.error(f"Error in product name search: {e}")
            return []
    
    async def _search_by_entities(self, entities: Dict[str, List[str]], category: str) -> List[WeldingPackageComponent]:
        """
        Search for products using extracted welding entities for intelligent matching.
        
        Args:
            entities: Dictionary of extracted welding entities
            category: Product category to filter by
            
        Returns:
            List of matching components
        """
        try:
            # Build dynamic query based on available entities
            query_parts = []
            parameters = {"category": category}
            param_counter = 0
            
            # Product name matching (highest priority)
            if entities.get("product_names"):
                name_conditions = []
                for product_name in entities["product_names"]:
                    param_name = f"product_name_{param_counter}"
                    name_conditions.append(f"toLower(p.name) CONTAINS toLower(${param_name})")
                    parameters[param_name] = product_name
                    param_counter += 1
                
                if name_conditions:
                    query_parts.append(f"({' OR '.join(name_conditions)})")
            
            # Welding process matching
            if entities.get("processes"):
                process_conditions = []
                for process in entities["processes"]:
                    param_name = f"process_{param_counter}"
                    process_conditions.append(f"(p.specifications_json CONTAINS ${param_name} OR p.description CONTAINS ${param_name})")
                    parameters[param_name] = process
                    param_counter += 1
                
                if process_conditions:
                    query_parts.append(f"({' OR '.join(process_conditions)})")
            
            # Material matching
            if entities.get("materials"):
                material_conditions = []
                for material in entities["materials"]:
                    param_name = f"material_{param_counter}"
                    material_conditions.append(f"(p.specifications_json CONTAINS ${param_name} OR p.description CONTAINS ${param_name})")
                    parameters[param_name] = material
                    param_counter += 1
                
                if material_conditions:
                    query_parts.append(f"({' OR '.join(material_conditions)})")
            
            # Specification matching
            if entities.get("specifications"):
                spec_conditions = []
                for spec in entities["specifications"]:
                    param_name = f"spec_{param_counter}"
                    spec_conditions.append(f"(p.specifications_json CONTAINS ${param_name} OR p.description CONTAINS ${param_name})")
                    parameters[param_name] = spec
                    param_counter += 1
                
                if spec_conditions:
                    query_parts.append(f"({' OR '.join(spec_conditions)})")
            
            # If no specific entities, fall back to basic category search
            if not query_parts:
                logger.info(f"No specific entities found, using basic category search for {category}")
                return []
            
            # Combine all conditions with AND logic (must match at least one condition from each type)
            where_conditions = " AND ".join(query_parts)
            
            entity_search_query = f"""
            MATCH (p:Product {{category: $category}})
            WHERE {where_conditions}
            RETURN p.product_id as product_id,
                   p.name as product_name,
                   p.category as category,
                   p.subcategory as subcategory,
                   p.description as description,
                   p.specifications_json as specifications,
                   p.price as price
            ORDER BY p.name
            LIMIT 10
            """
            
            logger.info(f"Entity-based search query: {entity_search_query}")
            logger.info(f"Parameters: {parameters}")
            
            results = await self.neo4j_repo.execute_query(entity_search_query, parameters)
            
            components = []
            for record in results:
                component = WeldingPackageComponent(
                    product_id=record.get("product_id", ""),
                    product_name=record.get("product_name", "Unknown"),
                    category=record.get("category", category),
                    subcategory=record.get("subcategory"),
                    price=record.get("price"),
                    sales_frequency=0,
                    description=record.get("description"),
                    compatibility_score=0.90  # High score for entity matches
                )
                components.append(component)
            
            logger.info(f"Entity-based search found {len(components)} matches for {category}")
            return components
            
        except Exception as e:
            logger.error(f"Error in entity-based search for {category}: {e}")
            return []
    
    async def _search_by_exact_name(self, product_name: str, category: str) -> List[WeldingPackageComponent]:
        """
        Search for products by exact name matching.
        
        Args:
            product_name: Specific product name to search for
            category: Product category to filter by
            
        Returns:
            List of matching components
        """
        try:
            # Use CONTAINS and case-insensitive matching for flexibility
            exact_search_query = """
            MATCH (p:Product {category: $category})
            WHERE toLower(p.name) CONTAINS toLower($product_name)
            RETURN p.product_id as product_id,
                   p.name as product_name,
                   p.category as category,
                   p.subcategory as subcategory,
                   p.description as description,
                   p.specifications_json as specifications,
                   p.price as price
            ORDER BY p.name
            LIMIT 5
            """
            
            parameters = {
                "product_name": product_name,
                "category": category
            }
            
            results = await self.neo4j_repo.execute_query(exact_search_query, parameters)
            
            components = []
            for record in results:
                component = WeldingPackageComponent(
                    product_id=record.get("product_id", ""),
                    product_name=record.get("product_name", "Unknown"),
                    category=record.get("category", category),
                    subcategory=record.get("subcategory"),
                    price=record.get("price"),
                    sales_frequency=0,
                    description=record.get("description"),
                    compatibility_score=0.95  # High score for exact matches
                )
                components.append(component)
            
            return components
            
        except Exception as e:
            logger.error(f"Error in exact name search for '{product_name}': {e}")
            return []
    
    async def _search_power_sources_by_vector(self, query: str) -> List[WeldingPackageComponent]:
        """
        Search for power sources using hybrid approach: exact name matching + semantic search
        
        Args:
            query: Original user query text
            
        Returns:
            List of power source components from hybrid search
        """
        try:
            # First, infer which categories are needed from the query
            required_categories = await self.infer_required_categories(query)
            logger.info(f"LLM inferred categories: {required_categories}")
            
            power_sources = []
            
            # STEP 1: Extract entities from the query
            entities = await self._extract_welding_entities(query)
            
            # Check for product-specific queries first (highest priority)
            if entities.get('product_names'):
                mentioned_product = entities['product_names'][0]  # Take first product name
                logger.info(f"Product-specific query detected, searching for: {mentioned_product}")
                product_matches = await self._search_by_product_name(mentioned_product, "PowerSource")
                power_sources.extend(product_matches)
                logger.info(f"Product name search found {len(product_matches)} matches")
            
            # STEP 2: If no product-specific matches, try entity-based search
            if not power_sources:
                if any(entities.values()):  # If any entities were found
                    logger.info(f"Using entity-based search with entities: {entities}")
                    entity_matches = await self._search_by_entities(entities, "PowerSource")
                    power_sources.extend(entity_matches)
                    logger.info(f"Entity-based search found {len(entity_matches)} matches")
                
                # STEP 3: If still no matches, use semantic/vector search
                if not power_sources:
                    logger.info("No product-specific matches found, using semantic vector search")
                
                # Create semantic search terms instead of using raw query
                # Vector search works better with functional descriptions than product names
                semantic_search_terms = []
                
                # Add welding process terms
                if "TIG" in query.upper() or "GTAW" in query.upper():
                    semantic_search_terms.append("TIG welder")
                if "MIG" in query.upper() or "GMAW" in query.upper():
                    semantic_search_terms.append("MIG welder")
                if "STICK" in query.upper() or "SMAW" in query.upper():
                    semantic_search_terms.append("stick welder")
                
                # Add generic power source terms
                semantic_search_terms.extend(["welding power source", "power supply"])
                
                # If no specific process mentioned, use the best semantic term
                if not semantic_search_terms:
                    semantic_search_terms = ["welding power source"]
                
                # Use the most specific term for vector search
                search_term = semantic_search_terms[0] if semantic_search_terms else "welding power source"
                logger.info(f"Using semantic search term: '{search_term}' instead of raw query")
                
                # Generate query embedding using the semantic search term
                query_embedding = self.embedding_generator.query_embedding(search_term)
                
                # Perform proper vector similarity search using Neo4j vector index
                vector_search_query = """
                CALL db.index.vector.queryNodes($indexName, $numberOfNearestNeighbours, $query)
                YIELD node as product, score
                WHERE product.category = 'PowerSource'
                RETURN product.product_id as product_id,
                       product.name as product_name,
                       product.category as category,
                       product.subcategory as subcategory,
                       product.description as description,
                       product.specifications_json as specifications,
                       product.price as price,
                       score
                ORDER BY score DESC
                """
                
                parameters = {
                    "indexName": "product_embeddings",
                    "numberOfNearestNeighbours": 20,  # Get more candidates to filter
                    "query": query_embedding
                }
                
                results = await self.neo4j_repo.execute_query(vector_search_query, parameters)
                
                logger.info(f"Vector search returned {len(results)} PowerSource candidates")
                
                for record in results:
                    # Only include if PowerSource is in required categories
                    if "PowerSource" in required_categories:
                        component = WeldingPackageComponent(
                            product_id=record.get("product_id", ""),
                            product_name=record.get("product_name", "Unknown"),
                            category=record.get("category", "PowerSource"),
                            subcategory=record.get("subcategory"),
                            price=record.get("price"),
                            sales_frequency=0,  # Will be updated with sales data if needed
                            description=record.get("description"),
                            compatibility_score=float(record.get("score", 0.0))  # Use vector similarity score
                        )
                        power_sources.append(component)
                
                logger.info(f"Vector search found {len(power_sources)} PowerSource products matching categories")
            
            # Return results from either exact matching or vector search
            logger.info(f"Total power sources found: {len(power_sources)}")
            return power_sources
            
        except Exception as e:
            logger.error(f"Error in vector search for power sources: {e}")
            return []
    
    async def _search_power_sources_by_parameters(self, intent: SimpleWeldingIntent) -> List[WeldingPackageComponent]:
        """
        Search for power sources using parameter-based query (fallback)
        
        Args:
            intent: Welding intent with extracted parameters
            
        Returns:
            List of power source components from parameter search
        """
        try:
            query, parameters = self.generate_power_source_query(intent)
            
            logger.info(f"Executing parameter-based query: {query}")
            logger.info(f"With parameters: {parameters}")
            
            results = await self.neo4j_repo.execute_query(query, parameters)
            
            logger.info(f"Parameter query returned {len(results)} results")
            
            power_sources = []
            
            for record in results:
                component = WeldingPackageComponent(
                    product_id=record.get("product_id", ""),
                    product_name=record.get("product_name", "Unknown"),
                    category=record.get("category", "PowerSource"),
                    subcategory=record.get("subcategory"),
                    price=record.get("price"),
                    sales_frequency=record.get("sales_frequency", 0),
                    description=record.get("description"),
                    compatibility_score=0.6  # Lower score for parameter search
                )
                
                power_sources.append(component)
            
            return power_sources
            
        except Exception as e:
            logger.error(f"Error in parameter-based power source search: {e}")
            return []
    
    async def find_compatible_components(self, power_source_id: str, intent: SimpleWeldingIntent) -> Dict[str, List[WeldingPackageComponent]]:
        """
        Find compatible feeders, coolers, and consumables
        
        Args:
            power_source_id: Selected power source ID
            intent: Original welding intent
            
        Returns:
            Dictionary with component lists
        """
        
        components = {
            "feeders": [],
            "coolers": [],
            "consumables": [],
            "accessories": []
        }
        
        component_mappings = {
            "feeders": "Feeder",
            "coolers": "Cooler", 
            "consumables": "Consumable",
            "accessories": "Accessory"
        }
        
        for component_key, component_type in component_mappings.items():
            try:
                query, parameters = self.generate_compatible_components_query(power_source_id, component_type)
                
                results = await self.neo4j_repo.execute_query(query, parameters)
                
                for record in results:
                    component = WeldingPackageComponent(
                        product_id=record.get("product_id", ""),
                        product_name=record.get("product_name", "Unknown"),
                        category=record.get("category", component_type),
                        subcategory=record.get("subcategory"),
                        price=record.get("price"),
                        sales_frequency=record.get("sales_frequency", 0),
                        description=record.get("description"),
                        compatibility_score=self.score_component_compatibility(record, intent)
                    )
                    
                    components[component_key].append(component)
                
                logger.info(f"Found {len(components[component_key])} {component_key}")
                
            except Exception as e:
                logger.error(f"Error finding {component_key}: {e}")
        
        return components
    
    async def find_components_by_categories(self, query: str, required_categories: List[str]) -> Dict[str, List[WeldingPackageComponent]]:
        """
        Find components for all required categories using entity-based and vector search
        
        Args:
            query: Original user query
            required_categories: List of categories inferred by LLM
            
        Returns:
            Dictionary mapping category names to component lists
        """
        
        components_by_category = {}
        
        try:
            # Check if this is a product-specific query and extract mentioned product
            mentioned_product = None
            if "aristo" in query.lower() or "warrior" in query.lower() or "renegade" in query.lower():
                # Simple extraction for known product names
                words = query.lower().split()
                for i, word in enumerate(words):
                    if word in ["aristo", "warrior", "renegade"]:
                        # Get the product name (current word + next word if it's a number/model)
                        if i + 1 < len(words) and any(char.isdigit() for char in words[i + 1]):
                            mentioned_product = f"{word} {words[i + 1]}"
                            if i + 2 < len(words) and words[i + 2] in ["ix", "i", "cc/cv"]:
                                mentioned_product = f"{mentioned_product} {words[i + 2]}"
                        break
                        
                if mentioned_product:
                    logger.info(f"Product-specific query detected: {mentioned_product}")
            
            # Extract welding entities once for all categories
            entities = await self._extract_welding_entities(query)
            logger.info(f"Using entities for category search: {entities}")
            
            # Perform search for each required category
            for category in required_categories:
                components_by_category[category] = []
                
                # STEP 1: Try product-specific search first (highest priority)
                if mentioned_product:
                    logger.info(f"Trying product-specific search for {category} with: {mentioned_product}")
                    product_matches = await self._search_by_product_name(mentioned_product, category)
                    components_by_category[category].extend(product_matches)
                    logger.info(f"Product-specific search for {category} found {len(product_matches)} matches")
                
                # STEP 2: Try entity-based search if no product-specific matches
                if not components_by_category[category] and any(entities.values()):
                    entity_matches = await self._search_by_entities(entities, category)
                    components_by_category[category].extend(entity_matches)
                    logger.info(f"Entity search for {category} found {len(entity_matches)} matches")
                
                # STEP 2: If no entity matches or need more, use semantic vector search
                if len(components_by_category[category]) < 3:  # Want at least 3 options per category
                    try:
                        # Create category-specific semantic search terms
                        def get_semantic_term_for_category(cat: str, original_query: str) -> str:
                            """Get appropriate semantic search term for each category"""
                            if cat == "PowerSource":
                                if "TIG" in original_query.upper() or "GTAW" in original_query.upper():
                                    return "TIG welder"
                                if "MIG" in original_query.upper() or "GMAW" in original_query.upper():
                                    return "MIG welder"
                                if "STICK" in original_query.upper() or "SMAW" in original_query.upper():
                                    return "stick welder"
                                return "welding power source"
                            elif cat == "Feeder":
                                return "wire feeder"
                            elif cat == "Cooler":
                                return "cooling system"
                            elif cat == "FeederAccessory":
                                return "feeder accessory"
                            else:
                                return f"{cat.lower()} welding"
                        
                        semantic_term = get_semantic_term_for_category(category, query)
                        logger.info(f"Vector search for {category} using semantic term: '{semantic_term}'")
                        
                        # Generate category-specific query embedding
                        category_query_embedding = self.embedding_generator.query_embedding(semantic_term)
                        
                        # Vector search filtered by category
                        vector_search_query = """
                        CALL db.index.vector.queryNodes($indexName, $numberOfNearestNeighbours, $query)
                    YIELD node as product, score
                    WHERE product.category = $category
                    RETURN product.product_id as product_id,
                           product.name as product_name,
                           product.category as category,
                           product.subcategory as subcategory,
                           product.description as description,
                           product.specifications_json as specifications,
                           product.price as price,
                           score
                    ORDER BY score DESC
                    LIMIT 5
                    """
                    
                        parameters = {
                            "indexName": "product_embeddings",
                            "numberOfNearestNeighbours": 10,  # Get top candidates for this category
                            "query": category_query_embedding,
                            "category": category
                        }
                        
                        results = await self.neo4j_repo.execute_query(vector_search_query, parameters)
                        
                        for record in results:
                            component = WeldingPackageComponent(
                                product_id=record.get("product_id", ""),
                                product_name=record.get("product_name", "Unknown"),
                                category=record.get("category", category),
                                subcategory=record.get("subcategory"),
                                price=record.get("price"),
                                sales_frequency=0,  # Would need separate query for this
                                description=record.get("description"),
                                compatibility_score=float(record.get("score", 0.0))  # Use vector similarity score
                            )
                            components_by_category[category].append(component)
                        
                        logger.info(f"Vector search found {len(components_by_category[category])} components for category {category}")
                        
                    except Exception as e:
                        logger.error(f"Vector search failed for category {category}: {e}")
                        components_by_category[category] = []
            
            return components_by_category
            
        except Exception as e:
            logger.error(f"Error finding components by categories: {e}")
            return components_by_category
    
    async def form_expert_mode_package(self, power_source: WeldingPackageComponent, intent: SimpleWeldingIntent) -> Optional[SimpleWeldingPackage]:
        """
        Form a comprehensive expert mode package using sales history and golden package fallback.
        
        Logic:
        1. Trinity Formation: PowerSource + Most Popular Compatible Feeder + Most Popular Compatible Cooler
        2. Sales History Analysis: Find most popular combo with this trinity from sales orders
        3. Category Consolidation: If multiple products in same category → choose most popular by frequency
        4. 7-Category Completion: If package < 7 products → use golden package fallback to fill missing categories
        
        Args:
            power_source: Already identified power source
            intent: Original welding intent
            
        Returns:
            Complete 7+ category welding package or None if insufficient data
        """
        try:
            logger.info(f"🎯 TRINITY-FIRST MODE: Forming package for user-selected PowerSource: {power_source.product_name}")
            
            # TRINITY-FIRST STEP 1: Generate all possible Trinity combinations
            trinity_combinations = await self._generate_trinity_combinations(power_source.product_id)
            logger.info(f"🔍 Generated {len(trinity_combinations)} possible Trinity combinations")
            
            # TRINITY-FIRST STEP 2: Calculate Trinity popularity (orders containing all 3 components)
            most_popular_trinity = await self._find_most_popular_trinity(trinity_combinations)
            if not most_popular_trinity:
                logger.warning("❌ No Trinity combinations found, falling back to individual components")
                return None
            
            logger.info(f"🏆 Most Popular Trinity: PS={power_source.product_name}, F={most_popular_trinity['feeder'].product_name}, C={most_popular_trinity['cooler'].product_name} ({most_popular_trinity['trinity_frequency']} orders)")
            
            # TRINITY-FIRST STEP 3: Find accessories purchased WITH this specific Trinity
            trinity_accessories = await self._find_trinity_based_accessories(
                power_source.product_id, 
                most_popular_trinity['feeder'].product_id,
                most_popular_trinity['cooler'].product_id
            )
            
            # Combine Trinity components with accessories
            combo_products = [
                power_source,  # User's explicitly selected PowerSource
                most_popular_trinity['feeder'],
                most_popular_trinity['cooler']
            ] + trinity_accessories
            logger.info(f"🎯 Trinity-Based Products: Found {len(combo_products)} products (3 Trinity + {len(trinity_accessories)} accessories)")
            
            # Step 5: Consolidate by category (choose most popular if multiple in same category)
            # TRINITY-FIRST: Pass user's selected PowerSource ID to prevent substitution
            consolidated_package = await self._consolidate_by_category_popularity(combo_products, power_source.product_id)
            logger.info(f"🔄 Consolidated: {len(consolidated_package)} unique categories")
            
            # Step 6: If less than 7 categories, use golden package fallback
            if len(consolidated_package) < 7:
                logger.info(f"📦 Golden Package: Current {len(consolidated_package)} < 7, using fallback")
                # Create trinity structure with power_source for golden package completion
                trinity_with_powersource = {
                    "power_source": power_source,
                    "feeder": most_popular_trinity['feeder'],
                    "cooler": most_popular_trinity['cooler']
                }
                final_package = await self._complete_with_golden_package(trinity_with_powersource, consolidated_package)
            else:
                final_package = consolidated_package
                
            logger.info(f"✅ Expert Mode: Final package has {len(final_package)} categories")
            
            # Step 7: Convert to SimpleWeldingPackage format
            return await self._convert_to_simple_package(final_package, intent)
            
        except Exception as e:
            logger.error(f"❌ Expert mode package formation failed: {e}")
            return None

    async def _find_most_popular_compatible_component(self, power_source_id: str, component_type: str) -> Optional[WeldingPackageComponent]:
        """Find the most popular compatible component by sales frequency"""
        try:
            query, parameters = self.generate_compatible_components_query(power_source_id, component_type)
            results = await self.neo4j_repo.execute_query(query, parameters)
            logger.info(f"🔍 Popular {component_type}: Found {len(results)} compatible components for PowerSource {power_source_id}")
            
            if results:
                top_result = results[0]  # Already sorted by sales_frequency DESC
                return WeldingPackageComponent(
                    product_id=top_result.get("product_id", ""),
                    product_name=top_result.get("product_name", "Unknown"),
                    category=top_result.get("category", component_type),
                    subcategory=top_result.get("subcategory"),
                    price=top_result.get("price"),
                    sales_frequency=top_result.get("sales_frequency", 0),
                    description=top_result.get("description"),
                    compatibility_score=1.0  # High compatibility since it's from COMPATIBLE_WITH relationship
                )
            return None
        except Exception as e:
            logger.error(f"Error finding most popular {component_type}: {e}")
            return None

    async def _find_sales_history_combo(self, trinity: Dict) -> List[WeldingPackageComponent]:
        """Find most popular combo from sales history with the given trinity"""
        try:
            # Get product IDs from trinity
            power_source_id = trinity["power_source"].product_id if trinity["power_source"] else ""
            feeder_id = trinity["feeder"].product_id if trinity["feeder"] else ""
            cooler_id = trinity["cooler"].product_id if trinity["cooler"] else ""
            
            logger.info(f"🔍 Sales History Analysis: Trinity IDs - PS: {power_source_id}, F: {feeder_id}, C: {cooler_id}")
            
            # First check if we have any Transaction data at all
            order_count_query = "MATCH (t:Transaction) RETURN count(DISTINCT t.order_id) as total_orders"
            order_count_result = await self.neo4j_repo.execute_query(order_count_query, {})
            total_orders = order_count_result[0]["total_orders"] if order_count_result else 0
            logger.info(f"🔍 Database Check: Total orders in database: {total_orders}")
            
            # Find orders that contain this trinity combination
            query = """
            MATCH (t1:Transaction)-[:CONTAINS]->(ps:Product {product_id: $power_source_id})
            MATCH (t2:Transaction)-[:CONTAINS]->(f:Product {product_id: $feeder_id})
            MATCH (t3:Transaction)-[:CONTAINS]->(c:Product {product_id: $cooler_id})
            MATCH (t_other:Transaction)-[:CONTAINS]->(other:Product)
            WHERE t1.order_id = t2.order_id AND t2.order_id = t3.order_id AND t3.order_id = t_other.order_id
              AND NOT other.product_id IN [$power_source_id, $feeder_id, $cooler_id]
            WITH other, COUNT(DISTINCT t_other.order_id) as purchase_frequency
            RETURN other.product_id as product_id,
                   other.name as product_name,
                   other.category as category,
                   other.subcategory as subcategory,
                   other.price as price,
                   other.description as description,
                   purchase_frequency
            ORDER BY purchase_frequency DESC, other.category ASC
            LIMIT 20
            """
            
            parameters = {
                "power_source_id": power_source_id,
                "feeder_id": feeder_id,
                "cooler_id": cooler_id
            }
            
            results = await self.neo4j_repo.execute_query(query, parameters)
            logger.info(f"🔍 Sales History: Found {len(results)} additional products from orders with this trinity")
            
            # Include trinity components in the result
            combo_products = [trinity["power_source"], trinity["feeder"], trinity["cooler"]]
            
            # Add other products from sales history
            for result in results:
                component = WeldingPackageComponent(
                    product_id=result.get("product_id", ""),
                    product_name=result.get("product_name", "Unknown"),
                    category=result.get("category", "Unknown"),
                    subcategory=result.get("subcategory"),
                    price=result.get("price"),
                    sales_frequency=result.get("purchase_frequency", 0),
                    description=result.get("description"),
                    compatibility_score=0.9  # High score since it's from actual sales history
                )
                combo_products.append(component)
            
            return combo_products
            
        except Exception as e:
            logger.error(f"Error finding sales history combo: {e}")
            # Return just the trinity if sales history fails
            return [comp for comp in [trinity["power_source"], trinity["feeder"], trinity["cooler"]] if comp]

    async def _consolidate_by_category_popularity(self, products: List[WeldingPackageComponent], user_selected_powersource_id: str = None) -> Dict[str, WeldingPackageComponent]:
        """Consolidate products by category, choosing most popular if multiple in same category
        RESPECTS USER INTENT: Never substitutes user-explicitly-selected PowerSource
        """
        try:
            category_products = {}
            
            for product in products:
                category = product.category
                
                if category not in category_products:
                    category_products[category] = product
                else:
                    # TRINITY-FIRST RULE: Respect user's explicit PowerSource choice
                    if category == "PowerSource" and user_selected_powersource_id and product.product_id == user_selected_powersource_id:
                        # Keep user's explicitly selected PowerSource regardless of sales frequency
                        category_products[category] = product
                        logger.info(f"✅ USER INTENT RESPECTED: Keeping user-selected PowerSource {product.product_name}")
                        continue
                    elif category == "PowerSource" and user_selected_powersource_id and category_products[category].product_id == user_selected_powersource_id:
                        # Don't replace user's explicitly selected PowerSource
                        logger.info(f"✅ USER INTENT PROTECTED: Not replacing user-selected PowerSource {category_products[category].product_name}")
                        continue
                    
                    # For all other categories, choose the one with higher sales frequency
                    current = category_products[category]
                    # Handle None values for sales_frequency comparison
                    product_sales = product.sales_frequency or 0
                    current_sales = current.sales_frequency or 0
                    if product_sales > current_sales:
                        category_products[category] = product
                        logger.info(f"📊 Replaced {current.product_name} with {product.product_name} (higher sales: {product_sales} vs {current_sales})")
            
            return category_products
            
        except Exception as e:
            logger.error(f"Error consolidating by category: {e}")
            return {}

    async def _complete_with_golden_package(self, trinity: Dict, current_package: Dict[str, WeldingPackageComponent]) -> Dict[str, WeldingPackageComponent]:
        """Complete package to 7+ categories using golden package fallback"""
        try:
            power_source_id = trinity["power_source"].product_id if trinity["power_source"] else ""
            
            # Find golden package with the same power source
            query = """
            MATCH (gp:GoldenPackage {powersource_gin: $power_source_id})
            MATCH (gp)-[:CONTAINS]->(product:Product)
            WHERE NOT product.category IN $existing_categories
            RETURN product.product_id as product_id,
                   product.name as product_name,
                   product.category as category,
                   product.subcategory as subcategory,
                   product.price as price,
                   product.description as description
            ORDER BY product.category ASC
            """
            
            existing_categories = list(current_package.keys())
            parameters = {
                "power_source_id": power_source_id,
                "existing_categories": existing_categories
            }
            
            results = await self.neo4j_repo.execute_query(query, parameters)
            
            # Add golden package products to fill missing categories
            final_package = current_package.copy()
            
            for result in results:
                category = result.get("category", "Unknown")
                if category not in final_package:
                    component = WeldingPackageComponent(
                        product_id=result.get("product_id", ""),
                        product_name=result.get("product_name", "Unknown"),
                        category=category,
                        subcategory=result.get("subcategory"),
                        price=result.get("price"),
                        sales_frequency=0,  # Golden package items don't have sales frequency
                        description=result.get("description"),
                        compatibility_score=0.8  # Good compatibility from golden package
                    )
                    final_package[category] = component
                    logger.info(f"📦 Added {component.product_name} from golden package to fill {category}")
            
            return final_package
            
        except Exception as e:
            logger.error(f"Error completing with golden package: {e}")
            return current_package

    async def _convert_to_simple_package(self, package_dict: Dict[str, WeldingPackageComponent], intent: SimpleWeldingIntent) -> SimpleWeldingPackage:
        """Convert category dictionary to SimpleWeldingPackage format"""
        try:
            # Extract components by category
            power_source = package_dict.get("PowerSource")
            feeders = [comp for cat, comp in package_dict.items() if "feeder" in cat.lower() and "accessory" not in cat.lower()]
            coolers = [comp for cat, comp in package_dict.items() if "cooler" in cat.lower() and "accessory" not in cat.lower()]
            consumables = [comp for cat, comp in package_dict.items() if "consumable" in cat.lower()]
            
            # All non-core components go to accessories (including Torch, Interconnector, and *Accessory components)
            core_categories = {"PowerSource"}
            feeder_categories = {cat for cat in package_dict.keys() if "feeder" in cat.lower() and "accessory" not in cat.lower()}
            cooler_categories = {cat for cat in package_dict.keys() if "cooler" in cat.lower() and "accessory" not in cat.lower()}
            consumable_categories = {cat for cat in package_dict.keys() if "consumable" in cat.lower()}
            
            excluded_categories = core_categories | feeder_categories | cooler_categories | consumable_categories
            accessories = [comp for cat, comp in package_dict.items() if cat not in excluded_categories]
            
            # Calculate total price
            total_price = sum(comp.price or 0.0 for comp in package_dict.values())
            
            # Calculate package score
            component_scores = [comp.compatibility_score for comp in package_dict.values()]
            avg_score = sum(component_scores) / len(component_scores) if component_scores else 0.5
            
            return SimpleWeldingPackage(
                power_source=power_source,
                feeders=feeders,
                coolers=coolers,
                consumables=consumables,
                accessories=accessories,
                total_price=total_price,
                package_score=avg_score,
                confidence=intent.confidence * avg_score
            )
            
        except Exception as e:
            logger.error(f"Error converting to simple package: {e}")
            return None

    async def form_welding_package(self, intent: SimpleWeldingIntent, expertise_mode: str = None) -> Optional[SimpleWeldingPackage]:
        """
        Form a complete welding package based on intent using category inference
        
        Args:
            intent: Welding intent from first agent
            
        Returns:
            Complete welding package or None if insufficient data
        """
        
        try:
            logger.info("Forming welding package from intent using category inference")
            logger.info(f"🔍 DEBUG: Expertise mode parameter: {expertise_mode}")
            
            # Get original query for category inference
            original_query = getattr(intent, 'original_query', '') or getattr(intent, 'processes', [''])
            if isinstance(original_query, list):
                original_query = ' '.join(original_query)
            
            logger.info(f"Using query for category inference: {original_query}")
            
            # Infer required categories from the original query
            required_categories = await self.infer_required_categories(original_query)
            
            if not required_categories:
                logger.warning("No categories inferred, falling back to standard approach")
                # Fallback to original approach
                power_sources = await self.find_power_sources(intent)
                if not power_sources:
                    logger.warning("No power sources found")
                    return None
                best_power_source = power_sources[0]
            else:
                logger.info(f"Using category-based search for categories: {required_categories}")
                
                # Find components for all required categories
                all_components = await self.find_components_by_categories(original_query, required_categories)
                logger.info(f"🔍 DEBUG: All components found: {list(all_components.keys()) if all_components else 'None'}")
                
                # Extract power source from results
                power_sources = all_components.get("PowerSource", [])
                logger.info(f"🔍 DEBUG: Power sources from category search: {len(power_sources) if power_sources else 0}")
                if not power_sources:
                    logger.warning("No power sources found in category search")
                    return None
                
                best_power_source = power_sources[0]  # Take the top result from vector search
                logger.info(f"🔍 DEBUG: Best power source selected: {best_power_source.product_id if best_power_source else 'None'}")
            
            logger.info(f"Selected power source: {best_power_source.product_id} - {best_power_source.description[:100] if best_power_source.description else 'No description'}")
            
            # Check if we should use expert mode comprehensive package generation
            logger.info(f"🔍 DEBUG: Expertise mode parameter: {expertise_mode}")
            logger.info(f"🔍 DEBUG: Expertise mode type: {type(expertise_mode)}")
            logger.info(f"🔍 DEBUG: Expertise mode truthy: {bool(expertise_mode)}")
            if expertise_mode:
                logger.info(f"🔍 DEBUG: Expertise mode upper: {str(expertise_mode).upper()}")
                logger.info(f"🔍 DEBUG: In allowed list: {str(expertise_mode).upper() in ['EXPERT', 'HYBRID']}")
            
            logger.info(f"🔍 DEBUG: About to check if condition...")
            if expertise_mode and str(expertise_mode).upper() in ['EXPERT', 'HYBRID']:
                logger.info(f"🎯 Using EXPERT MODE package generation for {expertise_mode}")
                return await self.form_expert_mode_package(best_power_source, intent)
            else:
                logger.info(f"🔍 DEBUG: If condition failed - expertise_mode: {expertise_mode}, condition result: {expertise_mode and str(expertise_mode).upper() in ['EXPERT', 'HYBRID']}")
            
            # Find compatible components using traditional compatibility approach
            # This ensures we get compatible feeders, coolers, etc. even if not explicitly mentioned
            compatible_components = await self.find_compatible_components(best_power_source.product_id, intent)
            
            # Merge category-based results with compatibility-based results
            if 'required_categories' in locals():
                category_components = await self.find_components_by_categories(original_query, required_categories)
                
                # Prioritize category-matched components over compatibility-matched ones
                if "Feeder" in category_components and category_components["Feeder"]:
                    compatible_components["feeders"] = category_components["Feeder"] + compatible_components["feeders"]
                if "Cooler" in category_components and category_components["Cooler"]:
                    compatible_components["coolers"] = category_components["Cooler"] + compatible_components["coolers"]
                if "PowerSourceAccessory" in category_components and category_components["PowerSourceAccessory"]:
                    compatible_components["accessories"] = category_components["PowerSourceAccessory"] + compatible_components["accessories"]
            
            # Calculate total price
            total_price = best_power_source.price or 0.0
            
            all_components = []
            all_components.extend(compatible_components["feeders"][:2])  # Top 2 feeders
            all_components.extend(compatible_components["coolers"][:1])  # Top 1 cooler
            all_components.extend(compatible_components["consumables"][:3])  # Top 3 consumables
            all_components.extend(compatible_components["accessories"][:2])  # Top 2 accessories
            
            for comp in all_components:
                if comp.price:
                    total_price += comp.price
            
            # Calculate package score
            component_scores = [comp.compatibility_score for comp in all_components]
            avg_component_score = sum(component_scores) / len(component_scores) if component_scores else 0.5
            
            package_score = (best_power_source.compatibility_score * 0.6 + avg_component_score * 0.4)
            
            # Create package
            package = SimpleWeldingPackage(
                power_source=best_power_source,
                feeders=compatible_components["feeders"][:2],
                coolers=compatible_components["coolers"][:1],
                consumables=compatible_components["consumables"][:3],
                accessories=compatible_components["accessories"][:2],
                total_price=total_price,
                package_score=package_score,
                confidence=intent.confidence * package_score
            )
            
            logger.info(f"Package formed with score: {package_score:.2f}, total price: ${total_price:.2f}")
            
            return package
            
        except Exception as e:
            logger.error(f"Error forming welding package: {e}")
            return None
    
    # ========================================
    # TRINITY-FIRST ARCHITECTURE METHODS
    # ========================================
    
    async def _generate_trinity_combinations(self, powersource_id: str) -> List[Dict]:
        """Generate all possible Trinity combinations for a PowerSource using DETERMINES relationships"""
        try:
            # Get all compatible feeders using DETERMINES relationships
            feeders_query = """
            MATCH (ps:Product {gin: $ps_id})-[:DETERMINES]->(f:Product)
            WHERE f.category = 'Feeder'
            RETURN f.gin as feeder_id, f.name as feeder_name
            ORDER BY f.name
            """
            
            # Get all compatible coolers using DETERMINES relationships
            coolers_query = """
            MATCH (ps:Product {gin: $ps_id})-[:DETERMINES]->(c:Product)
            WHERE c.category = 'Cooler'
            RETURN c.gin as cooler_id, c.name as cooler_name
            ORDER BY c.name
            """
            
            feeders = await self.neo4j_repo.execute_query(feeders_query, {"ps_id": powersource_id})
            coolers = await self.neo4j_repo.execute_query(coolers_query, {"ps_id": powersource_id})
            
            logger.info(f"🔧 Found {len(feeders)} compatible feeders and {len(coolers)} compatible coolers")
            
            # Generate all combinations
            combinations = []
            for feeder in feeders:
                for cooler in coolers:
                    combination = {
                        "powersource_id": powersource_id,
                        "feeder_id": feeder["feeder_id"],
                        "feeder_name": feeder["feeder_name"],
                        "cooler_id": cooler["cooler_id"],
                        "cooler_name": cooler["cooler_name"]
                    }
                    combinations.append(combination)
            
            return combinations
            
        except Exception as e:
            logger.error(f"Error generating Trinity combinations: {e}")
            return []
    
    async def _find_most_popular_trinity(self, trinity_combinations: List[Dict]) -> Optional[Dict]:
        """Find the Trinity combination with highest sales frequency using FORMS_TRINITY relationships
        Uses new Trinity-First architecture for fast queries
        """
        try:
            logger.info(f"🚀 TRINITY-FIRST: Using FORMS_TRINITY relationships for fast Trinity discovery")
            
            # Get PowerSource ID from first combination (they all have same PowerSource)
            if not trinity_combinations:
                return None
                
            powersource_id = trinity_combinations[0]["powersource_id"]
            
            # Fast Trinity popularity query using FORMS_TRINITY relationships
            trinity_popularity_query = """
            MATCH (t:Transaction)-[trinity:FORMS_TRINITY]->(ps:Product {gin: $powersource_id})
            MATCH (f:Product {gin: trinity.feeder_gin})
            MATCH (c:Product {gin: trinity.cooler_gin})
            RETURN trinity.feeder_gin as feeder_gin, 
                   trinity.cooler_gin as cooler_gin,
                   f.name as feeder_name,
                   c.name as cooler_name,
                   count(*) as trinity_frequency
            ORDER BY trinity_frequency DESC
            LIMIT 1
            """
            
            result = await self.neo4j_repo.execute_query(trinity_popularity_query, {
                "powersource_id": powersource_id
            })
            
            if not result or not result[0]:
                logger.warning("❌ No Trinity combinations found in FORMS_TRINITY relationships")
                return None
            
            top_trinity = result[0]
            frequency = top_trinity["trinity_frequency"]
            
            logger.info(f"🏆 Most Popular Trinity: F={top_trinity['feeder_name'][:30]}...+C={top_trinity['cooler_name'][:30]}... = {frequency} orders")
            
            # Create component objects for the best Trinity
            best_trinity = {
                "feeder": WeldingPackageComponent(
                    product_id=top_trinity["feeder_gin"],
                    product_name=top_trinity["feeder_name"],
                    category="Feeder",
                    sales_frequency=frequency,  # Trinity-based frequency
                    compatibility_score=1.0
                ),
                "cooler": WeldingPackageComponent(
                    product_id=top_trinity["cooler_gin"],
                    product_name=top_trinity["cooler_name"],
                    category="Cooler",
                    sales_frequency=frequency,  # Trinity-based frequency
                    compatibility_score=1.0
                ),
                "trinity_frequency": frequency
            }
            
            return best_trinity
            
        except Exception as e:
            logger.error(f"Error finding most popular Trinity: {e}")
            return None
    
    async def _find_trinity_based_accessories(self, powersource_id: str, feeder_id: str, cooler_id: str) -> List[WeldingPackageComponent]:
        """Find accessories that are purchased WITH this specific Trinity combination using FORMS_TRINITY relationships"""
        try:
            logger.info(f"🚀 TRINITY-FIRST: Finding accessories for Trinity using FORMS_TRINITY relationships")
            logger.info(f"🔍 DEBUG: Looking for accessories with Trinity PS={powersource_id}, F={feeder_id}, C={cooler_id}")
            
            # Fast Trinity-based accessories query using FORMS_TRINITY relationships
            trinity_accessories_query = """
            // Find Transaction nodes that have this specific Trinity
            MATCH (trinity_t:Transaction)-[trinity:FORMS_TRINITY]->(ps:Product {gin: $ps_id})
            WHERE trinity.feeder_gin = $feeder_id AND trinity.cooler_gin = $cooler_id
            
            // Find ALL Transaction nodes with the same order_id (since Transaction nodes are per-product)
            MATCH (all_t:Transaction {order_id: trinity_t.order_id})-[:CONTAINS]->(accessory:Product)
            WHERE accessory.gin <> $ps_id AND accessory.gin <> $feeder_id AND accessory.gin <> $cooler_id
            
            // Count co-occurrence with this Trinity
            WITH accessory, COUNT(DISTINCT trinity_t.order_id) as trinity_cooccurrence
            RETURN accessory.gin as product_id,
                   accessory.name as product_name,
                   accessory.category as category,
                   accessory.subcategory as subcategory,
                   accessory.price as price,
                   accessory.description as description,
                   trinity_cooccurrence
            ORDER BY trinity_cooccurrence DESC, accessory.category ASC
            LIMIT 15
            """
            
            results = await self.neo4j_repo.execute_query(trinity_accessories_query, {
                "ps_id": powersource_id,
                "feeder_id": feeder_id,
                "cooler_id": cooler_id
            })
            
            logger.info(f"🔍 DEBUG: Trinity accessories query returned {len(results)} results")
            
            # If no accessories found, debug the Trinity relationship
            if not results:
                debug_query = """
                MATCH (t:Transaction)-[trinity:FORMS_TRINITY]->(ps:Product {gin: $ps_id})
                WHERE trinity.feeder_gin = $feeder_id AND trinity.cooler_gin = $cooler_id
                RETURN count(t) as trinity_transactions, 
                       collect(DISTINCT t.order_id)[0..3] as sample_orders
                """
                debug_result = await self.neo4j_repo.execute_query(debug_query, {
                    "ps_id": powersource_id,
                    "feeder_id": feeder_id,
                    "cooler_id": cooler_id
                })
                if debug_result:
                    logger.info(f"🔍 DEBUG: Found {debug_result[0]['trinity_transactions']} transactions with this Trinity")
                    logger.info(f"🔍 DEBUG: Sample order IDs: {debug_result[0]['sample_orders']}")
                    
                    # Check what products exist in those orders
                    if debug_result[0]['trinity_transactions'] > 0:
                        products_query = """
                        MATCH (trinity_t:Transaction)-[trinity:FORMS_TRINITY]->(ps:Product {gin: $ps_id})
                        WHERE trinity.feeder_gin = $feeder_id AND trinity.cooler_gin = $cooler_id
                        WITH trinity_t LIMIT 1
                        MATCH (all_t:Transaction {order_id: trinity_t.order_id})-[:CONTAINS]->(p:Product)
                        RETURN p.gin, p.name, p.category
                        ORDER BY p.category
                        """
                        products_result = await self.neo4j_repo.execute_query(products_query, {
                            "ps_id": powersource_id,
                            "feeder_id": feeder_id,
                            "cooler_id": cooler_id
                        })
                        logger.info(f"🔍 DEBUG: Products in sample Trinity order: {[(r['p.gin'], r['p.name'], r['p.category']) for r in products_result]}")
            
            accessories = []
            for result in results:
                accessory = WeldingPackageComponent(
                    product_id=result["product_id"],
                    product_name=result["product_name"],
                    category=result["category"],
                    subcategory=result["subcategory"],
                    price=result["price"],
                    description=result["description"],
                    sales_frequency=result["trinity_cooccurrence"],  # Trinity-based co-occurrence
                    compatibility_score=0.9
                )
                accessories.append(accessory)
                logger.info(f"🔗 Trinity Accessory: {accessory.product_name} ({accessory.category}) = {accessory.sales_frequency} orders with Trinity")
            
            return accessories
            
        except Exception as e:
            logger.error(f"Error finding Trinity-based accessories: {e}")
            return []
    
    # =============================================================================
    # VECTOR COMPATIBILITY SEARCH WITH SMART FALLBACK
    # =============================================================================
    
    async def find_compatible_products_with_fallback(
        self,
        compatibility_query: str,
        target_product_id: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: int = 10
    ) -> Tuple[List[WeldingPackageComponent], str]:
        """
        Vector-first compatibility search with intelligent fallback.
        
        Args:
            compatibility_query: Natural language compatibility query
            target_product_id: Optional specific product to find compatibility for
            category_filter: Optional category to filter results
            limit: Maximum number of results
            
        Returns:
            Tuple of (results, method_used)
        """
        logger.info(f"🔍 Vector compatibility search: '{compatibility_query}' (threshold: {settings.VECTOR_CONFIDENCE_THRESHOLD})")
        
        try:
            # Step 1: Try vector similarity search first
            vector_results = await self._vector_compatibility_search(
                compatibility_query=compatibility_query,
                target_product_id=target_product_id,
                category_filter=category_filter,
                limit=settings.VECTOR_SEARCH_LIMIT
            )
            
            # Step 2: Filter by confidence threshold
            high_confidence_results = [
                result for result in vector_results 
                if result.compatibility_score >= settings.VECTOR_CONFIDENCE_THRESHOLD
            ]
            
            if high_confidence_results and len(high_confidence_results) >= min(3, limit):
                logger.info(f"✅ Vector search success: {len(high_confidence_results)} results above {settings.VECTOR_CONFIDENCE_THRESHOLD} threshold")
                return high_confidence_results[:limit], "vector_high_confidence"
            
            # Step 3: Fallback to rules-based search if vector confidence is low
            if settings.ENABLE_COMPATIBILITY_FALLBACK:
                logger.info(f"⚠️ Vector search low confidence ({len(high_confidence_results)} results), trying fallback...")
                
                fallback_results = await self._rules_based_compatibility_search(
                    compatibility_query=compatibility_query,
                    target_product_id=target_product_id,
                    category_filter=category_filter,
                    limit=limit
                )
                
                if fallback_results:
                    logger.info(f"✅ Fallback search success: {len(fallback_results)} results")
                    return fallback_results, "rules_fallback"
            
            # Step 4: Return vector results even if low confidence (better than nothing)
            if vector_results:
                logger.info(f"⚠️ Returning {len(vector_results)} vector results with mixed confidence")
                return vector_results[:limit], "vector_low_confidence" 
            
            logger.warning("❌ No compatibility results found with any method")
            return [], "no_results"
            
        except Exception as e:
            logger.error(f"Error in compatibility search: {e}")
            return [], "error"
    
    async def _vector_compatibility_search(
        self,
        compatibility_query: str,
        target_product_id: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: int = 20
    ) -> List[WeldingPackageComponent]:
        """
        Pure vector similarity search for compatibility.
        """
        try:
            # Enhance query with target product context if provided
            if target_product_id:
                target_product = await self._get_product_context(target_product_id)
                if target_product:
                    enhanced_query = f"{target_product['name']} compatible {compatibility_query}"
                else:
                    enhanced_query = f"compatible with product {target_product_id} {compatibility_query}"
            else:
                enhanced_query = f"compatible {compatibility_query}"
            
            logger.info(f"🎯 Enhanced vector query: '{enhanced_query}'")
            
            # Generate query embedding
            query_embedding = self.embedding_generator.query_embedding(enhanced_query)
            
            # Build vector search query
            vector_query = """
            CALL db.index.vector.queryNodes($indexName, $numberOfNearestNeighbours, $query)
            YIELD node as product, score
            WHERE 1=1
            """
            
            parameters = {
                "indexName": "product_embeddings",
                "numberOfNearestNeighbours": limit,
                "query": query_embedding
            }
            
            # Add category filter if specified
            if category_filter:
                vector_query += " AND product.category = $category_filter"
                parameters["category_filter"] = category_filter
            
            # Exclude target product if specified
            if target_product_id:
                vector_query += " AND product.product_id <> $target_product_id"
                parameters["target_product_id"] = target_product_id
            
            vector_query += """
            RETURN product.product_id as product_id,
                   product.name as product_name,
                   product.category as category,
                   product.subcategory as subcategory,
                   product.description as description,
                   product.specifications_json as specifications,
                   score as similarity_score
            ORDER BY score DESC
            """
            
            # Execute vector search
            results = await self.neo4j_repo.execute_query(vector_query, parameters)
            
            # Convert to WeldingPackageComponent objects
            components = []
            for result in results:
                component = WeldingPackageComponent(
                    product_id=result["product_id"],
                    product_name=result["product_name"],
                    category=result["category"],
                    subcategory=result["subcategory"],
                    description=result["description"],
                    compatibility_score=result["similarity_score"],
                    sales_frequency=0  # Could enhance with sales data later
                )
                components.append(component)
                logger.debug(f"🔍 Vector result: {component.product_name} (score: {component.compatibility_score:.3f})")
            
            return components
            
        except Exception as e:
            logger.error(f"Vector compatibility search error: {e}")
            return []
    
    async def _rules_based_compatibility_search(
        self,
        compatibility_query: str,
        target_product_id: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[WeldingPackageComponent]:
        """
        Fallback rules-based compatibility search using text matching.
        """
        try:
            logger.info("🔧 Using rules-based fallback search")
            
            # Extract key terms from query for text matching
            key_terms = self._extract_key_terms(compatibility_query)
            logger.info(f"🔑 Key terms extracted: {key_terms}")
            
            # Build text-based search query
            search_query = "MATCH (p:Product) WHERE 1=1"
            parameters = {}
            conditions = []
            
            # Add category filter
            if category_filter:
                conditions.append("p.category = $category_filter")
                parameters["category_filter"] = category_filter
            
            # Exclude target product
            if target_product_id:
                conditions.append("p.product_id <> $target_product_id")
                parameters["target_product_id"] = target_product_id
            
            # Add text matching conditions
            if key_terms:
                text_conditions = []
                for i, term in enumerate(key_terms):
                    param_name = f"term_{i}"
                    text_conditions.append(
                        f"(p.name CONTAINS ${param_name} OR p.description CONTAINS ${param_name} OR p.specifications_json CONTAINS ${param_name})"
                    )
                    parameters[param_name] = term
                
                if text_conditions:
                    conditions.append(f"({' OR '.join(text_conditions)})")
            
            # Apply conditions
            if conditions:
                search_query += " AND " + " AND ".join(conditions)
            
            search_query += """
            RETURN p.product_id as product_id,
                   p.name as product_name,
                   p.category as category,
                   p.subcategory as subcategory,
                   p.description as description,
                   p.specifications_json as specifications
            ORDER BY p.name
            LIMIT $limit
            """
            
            parameters["limit"] = limit
            
            # Execute search
            results = await self.neo4j_repo.execute_query(search_query, parameters)
            
            # Convert to components with basic compatibility scoring
            components = []
            for result in results:
                # Basic compatibility score based on term matches
                score = self._calculate_basic_compatibility_score(result, key_terms)
                
                component = WeldingPackageComponent(
                    product_id=result["product_id"],
                    product_name=result["product_name"],
                    category=result["category"],
                    subcategory=result["subcategory"],
                    description=result["description"],
                    compatibility_score=score,
                    sales_frequency=0
                )
                components.append(component)
            
            # Sort by compatibility score
            components.sort(key=lambda x: x.compatibility_score, reverse=True)
            
            return components
            
        except Exception as e:
            logger.error(f"Rules-based compatibility search error: {e}")
            return []
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from compatibility query for text matching."""
        # Simple keyword extraction - could be enhanced with NLP
        import re
        
        # Common welding terms to look for
        welding_terms = [
            "MIG", "TIG", "STICK", "GMAW", "GTAW", "SMAW", "FCAW",
            "aluminum", "steel", "stainless", "carbon",
            "marine", "outdoor", "indoor", "portable", "heavy", "duty",
            "feeder", "cooler", "torch", "wire", "electrode",
            "amperage", "voltage", "power", "current"
        ]
        
        query_lower = query.lower()
        found_terms = []
        
        for term in welding_terms:
            if term.lower() in query_lower:
                found_terms.append(term)
        
        # Also extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]+)"', query)
        found_terms.extend(quoted_phrases)
        
        return list(set(found_terms))  # Remove duplicates
    
    def _calculate_basic_compatibility_score(self, product_result: Dict, key_terms: List[str]) -> float:
        """Calculate basic compatibility score based on term matching."""
        if not key_terms:
            return 0.5  # Default score
        
        # Check how many terms match in product data
        product_text = " ".join([
            product_result.get("product_name", ""),
            product_result.get("description", ""),
            product_result.get("specifications", "")
        ]).lower()
        
        matches = sum(1 for term in key_terms if term.lower() in product_text)
        score = min(0.9, 0.3 + (matches / len(key_terms)) * 0.6)  # Scale to 0.3-0.9
        
        return score
    
    async def _get_product_context(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get basic product information for context enhancement."""
        try:
            query = """
            MATCH (p:Product {product_id: $product_id})
            RETURN p.name as name, p.category as category, p.description as description
            """
            
            result = await self.neo4j_repo.execute_query(query, {"product_id": product_id})
            return result[0] if result else None
            
        except Exception as e:
            logger.warning(f"Could not get product context for {product_id}: {e}")
            return None