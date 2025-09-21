"""
Neo4j repository for graph database operations.

Provides safe, parameterized queries for product recommendations,
relationship traversals, and graph analysis operations.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from ..neo4j import Neo4jConnection, get_neo4j_connection

logger = logging.getLogger(__name__)


class Neo4jRepository:
    """
    Repository for Neo4j graph database operations.
    
    Handles all product, package, and relationship queries with
    parameterized queries for security and performance.
    """
    
    def __init__(self, connection: Neo4jConnection):
        """
        Initialize repository with Neo4j connection.
        
        Args:
            connection: Neo4j connection instance
        """
        self.connection = connection
    
    # =============================================================================
    # PRODUCT QUERIES
    # =============================================================================
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product by its unique ID.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product data or None if not found
        """
        query = """
        MATCH (p:Product {product_id: $product_id})
        RETURN p {
            .*, 
            labels: labels(p)
        } as product
        """
        
        result = await self.connection.execute_query(
            query, 
            parameters={"product_id": product_id}
        )
        
        return result[0]["product"] if result else None
    
    async def get_products_by_category(
        self,
        category: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get products by category with pagination.
        
        Args:
            category: Product category
            limit: Maximum number of products to return
            skip: Number of products to skip for pagination
            
        Returns:
            List of product data
        """
        query = """
        MATCH (p:Product)
        WHERE p.category = $category OR p.subcategory = $category
        RETURN p {
            .*, 
            labels: labels(p)
        } as product
        ORDER BY p.product_name
        SKIP $skip
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={
                "category": category,
                "limit": limit,
                "skip": skip
            }
        )
        
        return [record["product"] for record in result]
    
    async def search_products(
        self,
        search_term: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search products by name, description, or specifications.
        
        Args:
            search_term: Search term to match
            limit: Maximum number of products to return
            skip: Number of products to skip for pagination
            
        Returns:
            List of matching product data
        """
        query = """
        MATCH (p:Product)
        WHERE p.product_name CONTAINS $search_term
           OR p.description CONTAINS $search_term
           OR p.specifications CONTAINS $search_term
           OR p.category CONTAINS $search_term
           OR p.subcategory CONTAINS $search_term
        RETURN p {
            .*, 
            labels: labels(p)
        } as product
        ORDER BY 
            CASE 
                WHEN p.product_name CONTAINS $search_term THEN 1
                WHEN p.category CONTAINS $search_term THEN 2
                ELSE 3
            END,
            p.product_name
        SKIP $skip
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={
                "search_term": search_term,
                "limit": limit,
                "skip": skip
            }
        )
        
        return [record["product"] for record in result]
    
    async def get_all_categories(self) -> List[str]:
        """
        Get all unique product categories.
        
        Returns:
            List of category names
        """
        query = """
        MATCH (p:Product)
        RETURN DISTINCT p.category as category
        ORDER BY category
        """
        
        result = await self.connection.execute_query(query)
        return [record["category"] for record in result if record["category"]]
    
    async def get_all_subcategories(self, category: Optional[str] = None) -> List[str]:
        """
        Get all unique product subcategories, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of subcategory names
        """
        if category:
            query = """
            MATCH (p:Product {category: $category})
            RETURN DISTINCT p.subcategory as subcategory
            ORDER BY subcategory
            """
            parameters = {"category": category}
        else:
            query = """
            MATCH (p:Product)
            RETURN DISTINCT p.subcategory as subcategory
            ORDER BY subcategory
            """
            parameters = {}
        
        result = await self.connection.execute_query(query, parameters=parameters)
        return [record["subcategory"] for record in result if record["subcategory"]]
    
    # =============================================================================
    # PACKAGE QUERIES  
    # =============================================================================
    
    async def get_package_by_id(self, package_id: str) -> Optional[Dict[str, Any]]:
        """
        Get package by its unique ID.
        
        Args:
            package_id: Package identifier
            
        Returns:
            Package data or None if not found
        """
        query = """
        MATCH (pkg:Package {package_id: $package_id})
        RETURN pkg {
            .*, 
            labels: labels(pkg)
        } as package
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={"package_id": package_id}
        )
        
        return result[0]["package"] if result else None
    
    async def get_all_packages(
        self,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all packages with pagination.
        
        Args:
            limit: Maximum number of packages to return
            skip: Number of packages to skip for pagination
            
        Returns:
            List of package data
        """
        query = """
        MATCH (pkg:Package)
        RETURN pkg {
            .*, 
            labels: labels(pkg)
        } as package
        ORDER BY pkg.package_name
        SKIP $skip
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={"limit": limit, "skip": skip}
        )
        
        return [record["package"] for record in result]
    
    async def get_package_products(self, package_id: str) -> List[Dict[str, Any]]:
        """
        Get all products in a package with their relationships.
        
        Args:
            package_id: Package identifier
            
        Returns:
            List of products with relationship data
        """
        query = """
        MATCH (pkg:Package {package_id: $package_id})-[r]->(p:Product)
        RETURN p {
            .*, 
            labels: labels(p)
        } as product,
        r {
            .*, 
            type: type(r)
        } as relationship
        ORDER BY r.order, p.product_name
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={"package_id": package_id}
        )
        
        return [
            {
                "product": record["product"],
                "relationship": record["relationship"]
            }
            for record in result
        ]
    
    # =============================================================================
    # RECOMMENDATION QUERIES
    # =============================================================================
    
    async def get_similar_products(
        self,
        product_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get products similar to the given product based on relationships.
        
        Args:
            product_id: Source product identifier
            limit: Maximum number of similar products
            
        Returns:
            List of similar products with similarity scores
        """
        query = """
        MATCH (p1:Product {product_id: $product_id})
        MATCH (p1)-[r1]-(intermediate)-[r2]-(p2:Product)
        WHERE p1 <> p2
        WITH p2, count(*) as connection_count, 
             collect(DISTINCT type(r1)) as r1_types,
             collect(DISTINCT type(r2)) as r2_types
        RETURN p2 {
            .*, 
            labels: labels(p2)
        } as product,
        connection_count,
        r1_types,
        r2_types,
        connection_count as similarity_score
        ORDER BY similarity_score DESC, p2.product_name
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={
                "product_id": product_id,
                "limit": limit
            }
        )
        
        return [
            {
                "product": record["product"],
                "similarity_score": record["similarity_score"],
                "connection_count": record["connection_count"],
                "relationship_types": {
                    "r1_types": record["r1_types"],
                    "r2_types": record["r2_types"]
                }
            }
            for record in result
        ]
    
    async def get_complementary_products(
        self,
        product_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get products that complement the given product.
        
        Args:
            product_id: Source product identifier
            limit: Maximum number of complementary products
            
        Returns:
            List of complementary products
        """
        query = """
        MATCH (p1:Product {product_id: $product_id})
        MATCH (p1)-[:COMPLEMENTS|WORKS_WITH|PAIRS_WITH]->(p2:Product)
        RETURN p2 {
            .*, 
            labels: labels(p2)
        } as product
        ORDER BY p2.product_name
        LIMIT $limit
        
        UNION
        
        MATCH (p1:Product {product_id: $product_id})
        MATCH (p1)<-[:COMPLEMENTS|WORKS_WITH|PAIRS_WITH]-(p2:Product)
        RETURN p2 {
            .*, 
            labels: labels(p2)
        } as product
        ORDER BY p2.product_name
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={
                "product_id": product_id,
                "limit": limit
            }
        )
        
        return [dict(record["product"]) for record in result]  # Convert Neo4j Node to dictionary
    
    async def get_products_for_application(
        self,
        application: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products suitable for a specific application.
        
        Args:
            application: Application type or use case
            limit: Maximum number of products
            
        Returns:
            List of suitable products
        """
        query = """
        MATCH (p:Product)
        WHERE p.applications CONTAINS $application
           OR p.use_cases CONTAINS $application
           OR p.industry CONTAINS $application
        RETURN p {
            .*, 
            labels: labels(p)
        } as product
        ORDER BY p.product_name
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={
                "application": application,
                "limit": limit
            }
        )
        
        return [record["product"] for record in result]
    
    # =============================================================================
    # RELATIONSHIP QUERIES
    # =============================================================================
    
    async def get_product_relationships(
        self,
        product_id: str,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a product.
        
        Args:
            product_id: Product identifier
            relationship_types: Optional filter for relationship types
            
        Returns:
            List of relationships with connected nodes
        """
        if relationship_types:
            type_filter = "AND type(r) IN $relationship_types"
            parameters = {
                "product_id": product_id,
                "relationship_types": relationship_types
            }
        else:
            type_filter = ""
            parameters = {"product_id": product_id}
        
        query = f"""
        MATCH (p1:Product {{product_id: $product_id}})-[r]-(p2)
        WHERE p1 <> p2 {type_filter}
        RETURN p2 {{
            .*, 
            labels: labels(p2)
        }} as connected_node,
        r {{
            .*, 
            type: type(r)
        }} as relationship
        ORDER BY type(r), coalesce(p2.product_name, p2.package_name, p2.name)
        """
        
        result = await self.connection.execute_query(query, parameters=parameters)
        
        return [
            {
                "connected_node": record["connected_node"],
                "relationship": record["relationship"]
            }
            for record in result
        ]
    
    async def get_all_relationship_types(self) -> List[str]:
        """
        Get all relationship types in the graph.
        
        Returns:
            List of relationship type names
        """
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
        """
        
        result = await self.connection.execute_query(query)
        return [record["relationshipType"] for record in result]
    
    # =============================================================================
    # STATISTICS AND ANALYTICS
    # =============================================================================
    
    async def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        stats = {}
        
        # Node counts by label
        node_count_query = """
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        ORDER BY count DESC
        """
        node_results = await self.connection.execute_query(node_count_query)
        stats["node_counts"] = {
            str(record["labels"]): record["count"] 
            for record in node_results
        }
        
        # Relationship counts by type
        rel_count_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        rel_results = await self.connection.execute_query(rel_count_query)
        stats["relationship_counts"] = {
            record["type"]: record["count"]
            for record in rel_results
        }
        
        # Product statistics
        product_stats_query = """
        MATCH (p:Product)
        RETURN 
            count(p) as total_products,
            count(DISTINCT p.category) as unique_categories,
            count(DISTINCT p.subcategory) as unique_subcategories
        """
        product_results = await self.connection.execute_query(product_stats_query)
        if product_results:
            stats["product_statistics"] = product_results[0]
        
        # Package statistics
        package_stats_query = """
        MATCH (pkg:Package)
        OPTIONAL MATCH (pkg)-[r]->(p:Product)
        RETURN 
            count(DISTINCT pkg) as total_packages,
            avg(count(p)) as avg_products_per_package
        """
        package_results = await self.connection.execute_query(package_stats_query)
        if package_results:
            stats["package_statistics"] = package_results[0]
        
        return stats
    
    async def get_popular_products(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most connected products (highest relationship count).
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of popular products with connection counts
        """
        query = """
        MATCH (p:Product)-[r]-()
        RETURN p {
            .*, 
            labels: labels(p)
        } as product,
        count(r) as connection_count
        ORDER BY connection_count DESC, p.product_name
        LIMIT $limit
        """
        
        result = await self.connection.execute_query(
            query,
            parameters={"limit": limit}
        )
        
        return [
            {
                "product": record["product"],
                "connection_count": record["connection_count"]
            }
            for record in result
        ]
    
    async def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw Neo4j query with parameters.
        
        This is a generic method used by agent tools for custom queries.
        
        Args:
            query: Neo4j query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        result = await self.connection.execute_query(
            query, 
            parameters=parameters or {}
        )
        
        # Convert Neo4j records to dictionaries
        return [dict(record) for record in result]
    
    # =============================================================================
    # VECTOR SEARCH QUERIES
    # =============================================================================
    
    async def vector_search_products(
        self,
        query_embedding: List[float],
        limit: int = 10,
        category_filter: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on products.
        
        Args:
            query_embedding: Query embedding vector (384 dimensions)
            limit: Maximum number of results to return
            category_filter: Optional category filter
            min_score: Minimum similarity score threshold
            
        Returns:
            List of products with similarity scores
        """
        # Build the corrected query with named parameters
        vector_query = """
        CALL db.index.vector.queryNodes($indexName, $numberOfNearestNeighbours, $query)
        YIELD node as product, score
        WHERE score >= $min_score
        """
        
        # Add category filter if specified
        if category_filter:
            vector_query += " AND product.category = $category_filter"
        
        vector_query += """
        RETURN product {
            .*,
            labels: labels(product)
        } as product,
        score
        ORDER BY score DESC
        """
        
        vector_parameters = {
            "indexName": "product_embeddings",
            "numberOfNearestNeighbours": limit,
            "query": query_embedding,
            "min_score": min_score
        }
        
        if category_filter:
            vector_parameters["category_filter"] = category_filter
        
        try:
            result = await self.connection.execute_query(vector_query, parameters=vector_parameters)
            
            return [
                {
                    "product": record["product"],
                    "similarity_score": record["score"]
                }
                for record in result
            ]
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            # Fallback to empty results
            return []
    
    async def hybrid_search_products(
        self,
        query_embedding: List[float],
        limit: int = 10,
        category_filter: Optional[str] = None,
        include_sales_frequency: bool = True,
        vector_weight: float = 0.6,
        sales_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and sales frequency.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            category_filter: Optional category filter
            include_sales_frequency: Include sales frequency in scoring
            vector_weight: Weight for vector similarity score (0.0-1.0)
            sales_weight: Weight for sales frequency score (0.0-1.0)
            
        Returns:
            List of products with hybrid scores
        """
        # Build hybrid search query
        query_parts = [
            "CALL db.index.vector.queryNodes('product_embeddings', $query_embedding, $vector_limit)",
            "YIELD node as product, score as vector_score"
        ]
        
        parameters = {
            "query_embedding": query_embedding,
            "vector_limit": min(limit * 3, 50),  # Get more candidates for hybrid scoring
            "vector_weight": vector_weight,
            "sales_weight": sales_weight
        }
        
        # Add category filter if specified
        if category_filter:
            query_parts.append("WHERE product.category = $category_filter")
            parameters["category_filter"] = category_filter
        
        # Add sales frequency calculation if requested
        if include_sales_frequency:
            query_parts.extend([
                "OPTIONAL MATCH (product)<-[:CONTAINS]-(t:Transaction)",
                "WITH product, vector_score, COUNT(t) as sales_frequency",
                "WITH product, vector_score, sales_frequency,",
                "     CASE WHEN sales_frequency > 0 THEN",
                "          (toFloat(sales_frequency) / 100.0) * $sales_weight",
                "     ELSE 0.0 END as sales_score",
                "WITH product, vector_score, sales_frequency,",
                "     (vector_score * $vector_weight + sales_score) as hybrid_score"
            ])
        else:
            query_parts.extend([
                "WITH product, vector_score, 0 as sales_frequency,",
                "     vector_score as hybrid_score"
            ])
        
        # Add return and ordering
        query_parts.extend([
            "RETURN product {",
            "    .*,",
            "    labels: labels(product)",
            "} as product,",
            "vector_score,",
            "sales_frequency,",
            "hybrid_score",
            "ORDER BY hybrid_score DESC",
            "LIMIT $limit"
        ])
        
        parameters["limit"] = limit
        
        query = " ".join(query_parts)
        
        try:
            result = await self.connection.execute_query(query, parameters=parameters)
            
            return [
                {
                    "product": record["product"],
                    "vector_score": record["vector_score"],
                    "sales_frequency": record["sales_frequency"],
                    "hybrid_score": record["hybrid_score"]
                }
                for record in result
            ]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to regular vector search
            return await self.vector_search_products(query_embedding, limit, category_filter)
    
    async def find_compatible_components_vector(
        self,
        power_source_gin: str,
        query_embedding: List[float],
        component_category: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find compatible components using vector search with relationship validation.
        
        Args:
            power_source_gin: Power source GIN number
            query_embedding: Query embedding for semantic matching
            component_category: Component category (Feeder, Cooler, etc.)
            limit: Maximum number of results
            
        Returns:
            List of compatible components with scores
        """
        query = """
        // First find the power source
        MATCH (ps:Product {gin: $power_source_gin, category: 'PowerSource'})
        
        // Find compatible components via DETERMINES relationship
        MATCH (ps)-[:DETERMINES]->(comp:Product {category: $component_category})
        
        // Get vector similarity for semantic matching
        CALL db.index.vector.queryNodes('product_embeddings', $query_embedding, 20)
        YIELD node as vector_product, score as vector_score
        WHERE vector_product.gin = comp.gin
        
        // Optional: Get sales frequency
        OPTIONAL MATCH (comp)<-[:CONTAINS]-(t:Transaction)
        WITH comp, vector_score, COUNT(t) as sales_frequency
        
        // Calculate hybrid score
        WITH comp, vector_score, sales_frequency,
             (vector_score * 0.7 + (toFloat(sales_frequency) / 100.0) * 0.3) as compatibility_score
        
        RETURN comp {
            .*,
            labels: labels(comp)
        } as component,
        vector_score,
        sales_frequency,
        compatibility_score
        ORDER BY compatibility_score DESC
        LIMIT $limit
        """
        
        parameters = {
            "power_source_gin": power_source_gin,
            "query_embedding": query_embedding,
            "component_category": component_category,
            "limit": limit
        }
        
        try:
            result = await self.connection.execute_query(query, parameters=parameters)
            
            return [
                {
                    "component": record["component"],
                    "vector_score": record["vector_score"],
                    "sales_frequency": record["sales_frequency"],
                    "compatibility_score": record["compatibility_score"]
                }
                for record in result
            ]
            
        except Exception as e:
            logger.error(f"Compatible components vector search failed: {e}")
            return []
    
    async def trinity_formation_vector(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Form trinity packages using vector search with relationship validation.
        
        Args:
            query_embedding: Query embedding for semantic matching
            limit: Maximum number of trinity packages
            
        Returns:
            List of trinity packages with scores
        """
        query = """
        // Find power sources using vector search
        CALL db.index.vector.queryNodes('product_embeddings', $query_embedding, 15)
        YIELD node as ps, score as ps_score
        WHERE ps.category = 'PowerSource'
        
        // Find compatible feeders and coolers
        MATCH (ps)-[:DETERMINES]->(feeder:Product {category: 'Feeder'})
        MATCH (ps)-[:DETERMINES]->(cooler:Product {category: 'Cooler'})
        
        // Get vector scores for components if they have embeddings
        OPTIONAL MATCH (feeder) WHERE feeder.embedding IS NOT NULL
        CALL db.index.vector.queryNodes('product_embeddings', $query_embedding, 1) 
        YIELD node as feeder_vector, score as feeder_score
        WHERE feeder_vector.gin = feeder.gin
        
        OPTIONAL MATCH (cooler) WHERE cooler.embedding IS NOT NULL
        CALL db.index.vector.queryNodes('product_embeddings', $query_embedding, 1)
        YIELD node as cooler_vector, score as cooler_score  
        WHERE cooler_vector.gin = cooler.gin
        
        // Get sales frequencies
        OPTIONAL MATCH (ps)<-[:CONTAINS]-(t1:Transaction)
        OPTIONAL MATCH (feeder)<-[:CONTAINS]-(t2:Transaction)
        OPTIONAL MATCH (cooler)<-[:CONTAINS]-(t3:Transaction)
        
        WITH ps, feeder, cooler,
             ps_score,
             COALESCE(feeder_score, 0.5) as feeder_score,
             COALESCE(cooler_score, 0.5) as cooler_score,
             COUNT(t1) as ps_sales,
             COUNT(t2) as feeder_sales,
             COUNT(t3) as cooler_sales
        
        // Calculate trinity score
        WITH ps, feeder, cooler,
             ps_score, feeder_score, cooler_score,
             ps_sales, feeder_sales, cooler_sales,
             ((ps_score * 0.5 + feeder_score * 0.25 + cooler_score * 0.25) * 0.7 +
              ((ps_sales + feeder_sales + cooler_sales) / 300.0) * 0.3) as trinity_score
        
        RETURN {
            power_source: ps {.*, labels: labels(ps)},
            feeder: feeder {.*, labels: labels(feeder)}, 
            cooler: cooler {.*, labels: labels(cooler)},
            scores: {
                power_source_score: ps_score,
                feeder_score: feeder_score,
                cooler_score: cooler_score,
                trinity_score: trinity_score
            },
            sales_frequencies: {
                power_source_sales: ps_sales,
                feeder_sales: feeder_sales,
                cooler_sales: cooler_sales
            }
        } as trinity_package
        ORDER BY trinity_score DESC
        LIMIT $limit
        """
        
        parameters = {
            "query_embedding": query_embedding,
            "limit": limit
        }
        
        try:
            result = await self.connection.execute_query(query, parameters=parameters)
            
            return [record["trinity_package"] for record in result]
            
        except Exception as e:
            logger.error(f"Trinity formation vector search failed: {e}")
            return []


# Dependency for getting Neo4j repository
async def get_neo4j_repository() -> Neo4jRepository:
    """
    Factory function to get Neo4j repository instance.
    
    Returns:
        Neo4j repository with active connection
    """
    connection = await get_neo4j_connection()
    return Neo4jRepository(connection)