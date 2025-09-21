"""
Enhanced Neo4j Agent with Vector Search Capabilities

Combines traditional graph queries with vector embeddings for semantic search
while preserving the existing 2-agent architecture and trinity relationships.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .simple_intent_agent import SimpleWeldingIntent
from ..database.repositories import Neo4jRepository
from ..services.embedding_generator import ProductEmbeddingGenerator

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Enhanced search strategies"""
    VECTOR_ONLY = "vector"
    HYBRID = "hybrid"
    GRAPH_ONLY = "graph"
    AUTO = "auto"


@dataclass 
class EnhancedWeldingPackageComponent:
    """Enhanced component with vector scores"""
    gin: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    
    # Scoring metrics
    vector_score: float = 0.0
    compatibility_score: float = 0.0
    sales_frequency: int = 0
    hybrid_score: float = 0.0
    
    # Embedding data
    embedding_text: Optional[str] = None


@dataclass
class EnhancedWeldingPackage:
    """Enhanced welding package with vector scores"""
    power_source: Optional[EnhancedWeldingPackageComponent] = None
    feeders: List[EnhancedWeldingPackageComponent] = field(default_factory=list)
    coolers: List[EnhancedWeldingPackageComponent] = field(default_factory=list)
    consumables: List[EnhancedWeldingPackageComponent] = field(default_factory=list)
    accessories: List[EnhancedWeldingPackageComponent] = field(default_factory=list)
    
    # Package metrics
    total_price: float = 0.0
    vector_score: float = 0.0
    trinity_score: float = 0.0
    sales_score: float = 0.0
    hybrid_score: float = 0.0
    confidence: float = 0.0
    
    # Search metadata
    search_strategy: str = "hybrid"
    query_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "power_source": self.power_source.__dict__ if self.power_source else None,
            "feeders": [f.__dict__ for f in self.feeders],
            "coolers": [c.__dict__ for c in self.coolers],
            "consumables": [c.__dict__ for c in self.consumables],
            "accessories": [a.__dict__ for a in self.accessories],
            "total_price": self.total_price,
            "vector_score": self.vector_score,
            "trinity_score": self.trinity_score,
            "sales_score": self.sales_score,
            "hybrid_score": self.hybrid_score,
            "confidence": self.confidence,
            "search_strategy": self.search_strategy,
            "query_text": self.query_text
        }


class EnhancedNeo4jAgent:
    """
    Enhanced Neo4j Agent with Vector Search Capabilities
    
    Combines semantic vector search with graph relationship traversal
    for improved welding package recommendations while preserving
    the DETERMINES-based trinity formation logic.
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository, embedding_generator: ProductEmbeddingGenerator):
        """
        Initialize with Neo4j repository and embedding generator.
        
        Args:
            neo4j_repo: Neo4j repository instance
            embedding_generator: Product embedding generator
        """
        self.neo4j_repo = neo4j_repo
        self.embedding_generator = embedding_generator
    
    def _generate_search_text(self, intent: SimpleWeldingIntent) -> str:
        """
        Generate comprehensive search text from welding intent.
        
        Args:
            intent: Welding intent from SimpleIntentAgent
            
        Returns:
            Search text for embedding generation
        """
        search_parts = []
        
        # Add processes
        if intent.processes:
            search_parts.extend(intent.processes)
        
        # Add material information
        if intent.material:
            search_parts.append(intent.material)
        
        # Add thickness information
        if intent.thickness:
            search_parts.append(f"{intent.thickness} thickness")
        
        # Add industry/application context
        if intent.industry:
            search_parts.append(intent.industry)
        
        if intent.application:
            search_parts.append(intent.application)
        
        if intent.environment:
            search_parts.append(intent.environment)
        
        # Add power/voltage requirements if specified
        if intent.voltage:
            search_parts.append(f"{intent.voltage}V")
        
        if intent.amperage:
            search_parts.append(f"{intent.amperage}A")
        
        # Join all parts
        search_text = " ".join(search_parts)
        
        logger.debug(f"Generated search text: {search_text}")
        
        return search_text
    
    def _convert_search_result_to_component(self, result: Dict[str, Any]) -> EnhancedWeldingPackageComponent:
        """
        Convert search result to EnhancedWeldingPackageComponent.
        
        Args:
            result: Search result from Neo4j
            
        Returns:
            EnhancedWeldingPackageComponent object
        """
        # Handle different result structures
        if "product" in result:
            product = result["product"]
        elif "component" in result:
            product = result["component"]
        else:
            product = result
        
        return EnhancedWeldingPackageComponent(
            gin=product.get("gin", ""),
            product_name=product.get("name", "Unknown"),
            category=product.get("category", ""),
            subcategory=product.get("subcategory"),
            price=product.get("price"),
            description=product.get("description"),
            vector_score=result.get("vector_score", 0.0),
            compatibility_score=result.get("compatibility_score", 0.0),
            sales_frequency=result.get("sales_frequency", 0),
            hybrid_score=result.get("hybrid_score", 0.0),
            embedding_text=product.get("embedding_text")
        )
    
    async def find_power_sources_vector(self, intent: SimpleWeldingIntent, limit: int = 10) -> List[EnhancedWeldingPackageComponent]:
        """
        Find power sources using vector search.
        
        Args:
            intent: Welding intent
            limit: Maximum number of results
            
        Returns:
            List of power source components with vector scores
        """
        try:
            # Generate search text and embedding
            search_text = self._generate_search_text(intent)
            if not search_text:
                logger.warning("No search text generated for power source search")
                return []
            
            query_embedding = self.embedding_generator.query_embedding(search_text)
            
            # Perform hybrid search for power sources
            results = await self.neo4j_repo.hybrid_search_products(
                query_embedding=query_embedding,
                limit=limit,
                category_filter="PowerSource",
                include_sales_frequency=True,
                vector_weight=0.7,
                sales_weight=0.3
            )
            
            # Convert results to components
            power_sources = []
            for result in results:
                component = self._convert_search_result_to_component(result)
                power_sources.append(component)
            
            logger.info(f"Found {len(power_sources)} power sources using vector search")
            
            return power_sources
            
        except Exception as e:
            logger.error(f"Vector power source search failed: {e}")
            return []
    
    async def find_compatible_components_vector(
        self,
        power_source_gin: str,
        intent: SimpleWeldingIntent,
        component_category: str,
        limit: int = 5
    ) -> List[EnhancedWeldingPackageComponent]:
        """
        Find compatible components using vector search with relationship validation.
        
        Args:
            power_source_gin: Power source GIN number
            intent: Original welding intent
            component_category: Component category (Feeder, Cooler, etc.)
            limit: Maximum number of results
            
        Returns:
            List of compatible components
        """
        try:
            # Generate search text and embedding
            search_text = self._generate_search_text(intent)
            if not search_text:
                # Fallback to category-based search
                search_text = component_category
            
            query_embedding = self.embedding_generator.query_embedding(search_text)
            
            # Use the new vector-enabled compatible components search
            results = await self.neo4j_repo.find_compatible_components_vector(
                power_source_gin=power_source_gin,
                query_embedding=query_embedding,
                component_category=component_category,
                limit=limit
            )
            
            # Convert results to components
            components = []
            for result in results:
                component = self._convert_search_result_to_component(result)
                components.append(component)
            
            logger.info(f"Found {len(components)} compatible {component_category} components")
            
            return components
            
        except Exception as e:
            logger.error(f"Compatible {component_category} vector search failed: {e}")
            return []
    
    async def form_trinity_package_vector(self, intent: SimpleWeldingIntent) -> Optional[EnhancedWeldingPackage]:
        """
        Form trinity package using vector search with relationship validation.
        
        Args:
            intent: Welding intent
            
        Returns:
            Enhanced welding package or None
        """
        try:
            # Generate search text and embedding
            search_text = self._generate_search_text(intent)
            if not search_text:
                logger.warning("No search text generated for trinity formation")
                return None
            
            query_embedding = self.embedding_generator.query_embedding(search_text)
            
            # Use the new trinity formation vector search
            trinity_results = await self.neo4j_repo.trinity_formation_vector(
                query_embedding=query_embedding,
                limit=3  # Get top 3 trinity options
            )
            
            if not trinity_results:
                logger.warning("No trinity packages found with vector search")
                return None
            
            # Select the best trinity package
            best_trinity = trinity_results[0]
            
            # Convert to enhanced components
            power_source = self._convert_trinity_component(
                best_trinity["power_source"],
                best_trinity["scores"]["power_source_score"],
                best_trinity["sales_frequencies"]["power_source_sales"]
            )
            
            feeder = self._convert_trinity_component(
                best_trinity["feeder"],
                best_trinity["scores"]["feeder_score"],
                best_trinity["sales_frequencies"]["feeder_sales"]
            )
            
            cooler = self._convert_trinity_component(
                best_trinity["cooler"],
                best_trinity["scores"]["cooler_score"],
                best_trinity["sales_frequencies"]["cooler_sales"]
            )
            
            # Calculate total price
            total_price = 0.0
            for component in [power_source, feeder, cooler]:
                if component.price:
                    total_price += component.price
            
            # Create enhanced package
            package = EnhancedWeldingPackage(
                power_source=power_source,
                feeders=[feeder],
                coolers=[cooler],
                total_price=total_price,
                vector_score=best_trinity["scores"]["power_source_score"],
                trinity_score=best_trinity["scores"]["trinity_score"],
                sales_score=(
                    best_trinity["sales_frequencies"]["power_source_sales"] +
                    best_trinity["sales_frequencies"]["feeder_sales"] +
                    best_trinity["sales_frequencies"]["cooler_sales"]
                ) / 300.0,
                hybrid_score=best_trinity["scores"]["trinity_score"],
                confidence=intent.confidence * best_trinity["scores"]["trinity_score"],
                search_strategy="vector_trinity",
                query_text=search_text
            )
            
            logger.info(f"Formed trinity package with score: {package.trinity_score:.3f}")
            
            return package
            
        except Exception as e:
            logger.error(f"Trinity formation vector search failed: {e}")
            return None
    
    def _convert_trinity_component(self, product: Dict, vector_score: float, sales_frequency: int) -> EnhancedWeldingPackageComponent:
        """Convert trinity component to enhanced component."""
        return EnhancedWeldingPackageComponent(
            gin=product.get("gin", ""),
            product_name=product.get("name", "Unknown"),
            category=product.get("category", ""),
            subcategory=product.get("subcategory"),
            price=product.get("price"),
            description=product.get("description"),
            vector_score=vector_score,
            sales_frequency=sales_frequency,
            hybrid_score=vector_score * 0.7 + (sales_frequency / 100.0) * 0.3
        )
    
    async def universal_product_search(
        self,
        intent: SimpleWeldingIntent,
        category_filter: Optional[str] = None,
        limit: int = 20
    ) -> List[EnhancedWeldingPackageComponent]:
        """
        Universal product search across all categories using vector search.
        
        Args:
            intent: Welding intent
            category_filter: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of products from all relevant categories
        """
        try:
            # Generate search text and embedding
            search_text = self._generate_search_text(intent)
            if not search_text:
                logger.warning("No search text generated for universal search")
                return []
            
            query_embedding = self.embedding_generator.query_embedding(search_text)
            
            # Perform hybrid search across all products
            results = await self.neo4j_repo.hybrid_search_products(
                query_embedding=query_embedding,
                limit=limit,
                category_filter=category_filter,
                include_sales_frequency=True,
                vector_weight=0.6,
                sales_weight=0.4
            )
            
            # Convert results to components
            products = []
            for result in results:
                component = self._convert_search_result_to_component(result)
                products.append(component)
            
            logger.info(f"Universal search found {len(products)} products")
            
            return products
            
        except Exception as e:
            logger.error(f"Universal product search failed: {e}")
            return []
    
    async def form_welding_package_enhanced(
        self,
        intent: SimpleWeldingIntent,
        strategy: SearchStrategy = SearchStrategy.AUTO
    ) -> Optional[EnhancedWeldingPackage]:
        """
        Form welding package using enhanced vector + graph search.
        
        Args:
            intent: Welding intent
            strategy: Search strategy to use
            
        Returns:
            Enhanced welding package or None
        """
        try:
            logger.info(f"Forming welding package with strategy: {strategy.value}")
            
            # For AUTO strategy, prefer vector search
            if strategy == SearchStrategy.AUTO:
                strategy = SearchStrategy.HYBRID
            
            if strategy == SearchStrategy.VECTOR_ONLY or strategy == SearchStrategy.HYBRID:
                # Try vector-based trinity formation first
                package = await self.form_trinity_package_vector(intent)
                
                if package:
                    # Enhance with additional components using vector search
                    await self._enhance_package_with_accessories(package, intent)
                    return package
            
            # Fallback to traditional graph-based search
            logger.info("Falling back to traditional graph-based search")
            return await self._form_package_graph_fallback(intent)
            
        except Exception as e:
            logger.error(f"Enhanced package formation failed: {e}")
            return None
    
    async def _enhance_package_with_accessories(
        self,
        package: EnhancedWeldingPackage,
        intent: SimpleWeldingIntent
    ) -> None:
        """Add accessories and consumables to package using vector search."""
        try:
            # Find consumables
            consumables = await self.universal_product_search(
                intent,
                category_filter="Consumable",
                limit=3
            )
            package.consumables = consumables[:3]
            
            # Find accessories
            accessories = await self.universal_product_search(
                intent,
                category_filter="Accessory",
                limit=2
            )
            package.accessories = accessories[:2]
            
            # Update total price
            for comp in package.consumables + package.accessories:
                if comp.price:
                    package.total_price += comp.price
                    
        except Exception as e:
            logger.error(f"Failed to enhance package with accessories: {e}")
    
    async def _form_package_graph_fallback(self, intent: SimpleWeldingIntent) -> Optional[EnhancedWeldingPackage]:
        """Fallback to traditional graph-based package formation."""
        # This would implement the original SimpleNeo4jAgent logic
        # For now, return None to indicate fallback failed
        logger.warning("Graph-based fallback not yet implemented")
        return None