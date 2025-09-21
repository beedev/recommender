"""
Vector Migration Service for Neo4j

Migrates existing products to include vector embeddings using the
enhanced ProductEmbeddingGenerator with comprehensive specification extraction.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..database.repositories import Neo4jRepository, get_neo4j_repository
from .embedding_generator import ProductEmbeddingGenerator, ProductEmbedding

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Migration result statistics"""
    total_products: int = 0
    successful_embeddings: int = 0
    failed_embeddings: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    skipped_existing: int = 0


class VectorMigrationService:
    """
    Service for migrating existing Neo4j products to include vector embeddings.
    
    Handles the complete migration process including:
    1. Fetching existing products from Neo4j
    2. Generating comprehensive embeddings
    3. Updating products with embedding properties
    4. Creating vector index for similarity search
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository, embedding_generator: ProductEmbeddingGenerator):
        """
        Initialize migration service.
        
        Args:
            neo4j_repo: Neo4j repository instance
            embedding_generator: Embedding generator instance
        """
        self.neo4j_repo = neo4j_repo
        self.embedding_generator = embedding_generator
    
    async def fetch_all_products(self) -> List[Dict]:
        """
        Fetch all products from Neo4j.
        
        Returns:
            List of product dictionaries
        """
        try:
            query = """
            MATCH (p:Product)
            RETURN p.gin as gin,
                   p.name as name,
                   p.category as category,
                   p.subcategory as subcategory,
                   p.description as description,
                   p.specifications_json as specifications_json,
                   p.embedding as existing_embedding
            ORDER BY p.gin
            """
            
            logger.info("Fetching all products from Neo4j")
            results = await self.neo4j_repo.execute_query(query)
            
            products = [dict(record) for record in results]
            logger.info(f"Fetched {len(products)} products from Neo4j")
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            raise
    
    async def check_vector_index_exists(self) -> bool:
        """
        Check if vector index already exists.
        
        Returns:
            True if index exists, False otherwise
        """
        try:
            query = "SHOW INDEXES YIELD name WHERE name = 'product_embeddings'"
            results = await self.neo4j_repo.execute_query(query)
            
            exists = len(results) > 0
            logger.info(f"Vector index exists: {exists}")
            
            return exists
            
        except Exception as e:
            logger.warning(f"Failed to check vector index: {e}")
            return False
    
    async def create_vector_index(self) -> bool:
        """
        Create vector index for product embeddings.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if index already exists
            if await self.check_vector_index_exists():
                logger.info("Vector index already exists, skipping creation")
                return True
            
            # Create vector index
            create_index_query = """
            CREATE VECTOR INDEX product_embeddings IF NOT EXISTS
            FOR (p:Product) ON (p.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
              }
            }
            """
            
            logger.info("Creating vector index for product embeddings")
            await self.neo4j_repo.execute_query(create_index_query)
            
            logger.info("Vector index created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return False
    
    async def update_product_embedding(self, embedding: ProductEmbedding) -> bool:
        """
        Update a single product with embedding data.
        
        Args:
            embedding: ProductEmbedding object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_query = """
            MATCH (p:Product {gin: $gin})
            SET p.embedding = $embedding,
                p.embedding_text = $embedding_text,
                p.embedding_model = $embedding_model,
                p.embedding_created_at = $embedding_created_at
            RETURN p.gin as updated_gin
            """
            
            parameters = {
                "gin": embedding.gin,
                "embedding": embedding.embedding,
                "embedding_text": embedding.embedding_text,
                "embedding_model": embedding.embedding_model,
                "embedding_created_at": embedding.embedding_created_at
            }
            
            results = await self.neo4j_repo.execute_query(update_query, parameters)
            
            if results:
                logger.debug(f"Updated embedding for product {embedding.gin}")
                return True
            else:
                logger.warning(f"Product {embedding.gin} not found for embedding update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update embedding for product {embedding.gin}: {e}")
            return False
    
    async def update_products_batch(self, embeddings: List[ProductEmbedding], batch_size: int = 10) -> Tuple[int, int]:
        """
        Update multiple products with embeddings in batches.
        
        Args:
            embeddings: List of ProductEmbedding objects
            batch_size: Number of products to update per batch
            
        Returns:
            Tuple of (successful_updates, failed_updates)
        """
        successful = 0
        failed = 0
        
        logger.info(f"Updating {len(embeddings)} products with embeddings (batch size: {batch_size})")
        
        for i in range(0, len(embeddings), batch_size):
            batch = embeddings[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(embeddings) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = [self.update_product_embedding(embedding) for embedding in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                elif result:
                    successful += 1
                else:
                    failed += 1
            
            # Small delay between batches to avoid overwhelming the database
            await asyncio.sleep(0.1)
        
        logger.info(f"Batch update complete: {successful} successful, {failed} failed")
        
        return successful, failed
    
    async def migrate_products(self, 
                             skip_existing: bool = True, 
                             batch_size: int = 10) -> MigrationResult:
        """
        Complete migration process for all products.
        
        Args:
            skip_existing: Skip products that already have embeddings
            batch_size: Number of products to process per batch
            
        Returns:
            MigrationResult with statistics
        """
        result = MigrationResult()
        
        try:
            logger.info("Starting vector migration for all products")
            
            # 1. Fetch all products
            products = await self.fetch_all_products()
            result.total_products = len(products)
            
            if not products:
                logger.warning("No products found for migration")
                return result
            
            # 2. Filter products if skipping existing embeddings
            products_to_process = []
            
            for product in products:
                if skip_existing and product.get('existing_embedding'):
                    result.skipped_existing += 1
                    logger.debug(f"Skipping product {product.get('gin')} - already has embedding")
                else:
                    products_to_process.append(product)
            
            logger.info(f"Processing {len(products_to_process)} products ({result.skipped_existing} skipped)")
            
            if not products_to_process:
                logger.info("No products need embedding generation")
                return result
            
            # 3. Generate embeddings
            logger.info("Generating embeddings for products")
            embeddings = self.embedding_generator.generate_embeddings_batch(products_to_process)
            
            result.successful_embeddings = len(embeddings)
            result.failed_embeddings = len(products_to_process) - len(embeddings)
            
            if not embeddings:
                logger.warning("No embeddings generated successfully")
                return result
            
            # 4. Create vector index if it doesn't exist
            index_created = await self.create_vector_index()
            if not index_created:
                logger.warning("Failed to create vector index, but continuing with migration")
            
            # 5. Update products with embeddings
            successful_updates, failed_updates = await self.update_products_batch(embeddings, batch_size)
            
            result.successful_updates = successful_updates
            result.failed_updates = failed_updates
            
            logger.info(f"Migration complete: {result.successful_updates}/{result.total_products} products updated")
            
            return result
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def test_vector_search(self, query_text: str, limit: int = 5) -> List[Dict]:
        """
        Test vector search functionality after migration.
        
        Args:
            query_text: Search query text
            limit: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.query_embedding(query_text)
            
            # Perform vector search with correct parameter names
            search_query = """
            CALL db.index.vector.queryNodes($indexName, $numberOfNearestNeighbours, $query)
            YIELD node as product, score
            RETURN product.gin as gin,
                   product.name as name,
                   product.category as category,
                   product.embedding_text as embedding_text,
                   score
            ORDER BY score DESC
            """
            
            parameters = {
                "indexName": "product_embeddings",
                "numberOfNearestNeighbours": limit,
                "query": query_embedding
            }
            
            results = await self.neo4j_repo.execute_query(search_query, parameters)
            
            search_results = [dict(record) for record in results]
            
            logger.info(f"Vector search test for '{query_text}' returned {len(search_results)} results")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search test failed: {e}")
            raise


# Factory function for dependency injection
async def get_vector_migration_service() -> VectorMigrationService:
    """
    Factory function to create VectorMigrationService instance.
    
    Returns:
        VectorMigrationService with dependencies
    """
    neo4j_repo = await get_neo4j_repository()
    embedding_generator = ProductEmbeddingGenerator()
    
    return VectorMigrationService(neo4j_repo, embedding_generator)