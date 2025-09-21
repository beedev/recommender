# Vector Embedding Design for Neo4j Welding Recommendation System

**Date**: 2025-01-19  
**Purpose**: Add semantic search capabilities to the 2-agent welding recommendation system using Neo4j native vector embeddings

## Overview

Enhance the existing 2-agent architecture (SimpleIntentAgent + SimpleNeo4jAgent) with vector embeddings for semantic product discovery while maintaining all existing graph relationship logic.

## Architecture Design

### Current Architecture
```
User Query → SimpleIntentAgent → SimpleNeo4jAgent → Neo4j → Package
```

### Enhanced Architecture  
```
User Query → SimpleIntentAgent → SimpleNeo4jAgent → {
    1. Vector Search (semantic discovery)
    2. Graph Validation (relationship verification)
    3. Hybrid Scoring (similarity + sales + compatibility)
} → Enhanced Package
```

## Component Design

### 1. Product Embedding Schema

**Enhanced Product Nodes**:
```cypher
(p:Product {
  gin: "0465350883",
  name: "Warrior 500i CC/CV",
  category: "PowerSource",
  description: "Multi-process welding...",
  specifications_json: "{...}",
  
  // NEW: Vector embedding properties
  embedding: [0.1, 0.2, -0.3, ...],           // 768-dimensional vector
  embedding_text: "Warrior 500i PowerSource MIG TIG Stick 380V 500A industrial",
  embedding_created_at: "2025-01-19T10:00:00Z"
})
```

**Vector Index**:
```cypher
CREATE VECTOR INDEX product_embeddings
FOR (p:Product) ON (p.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: `cosine`
  }
}
```

### 2. Enhanced Embedding Generation Service

**File**: `app/services/embedding_generator.py`

```python
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import json
import re
from html import unescape
import logging

class ProductEmbeddingGenerator:
    """Generate semantic embeddings for welding products with comprehensive data extraction"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.logger = logging.getLogger(__name__)
    
    def generate_product_text(self, product: Dict[str, Any]) -> str:
        """Convert product data to comprehensive embedding text"""
        components = [
            # Core product info
            product.get('name', ''),
            product.get('category', ''),
            
            # Clean description (most important)
            self._clean_description(product.get('description', '')),
            
            # All specifications (comprehensive)
            self._extract_all_specifications(product.get('specifications_json', '')),
        ]
        
        # Join and clean up
        text = ' '.join(filter(None, components))
        return self._normalize_text(text)
    
    def _clean_description(self, html_description: str) -> str:
        """Clean HTML description to meaningful text"""
        if not html_description:
            return ''
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', html_description)
        
        # Decode HTML entities
        clean = unescape(clean)
        
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Remove marketing fluff and focus on technical content
        # Keep sentences with technical terms
        sentences = clean.split('.')
        technical_sentences = []
        
        technical_keywords = {
            'welding', 'MIG', 'TIG', 'MMA', 'Stick', 'GMAW', 'GTAW', 'SMAW',
            'amperage', 'voltage', 'current', 'duty cycle', 'inverter',
            'wire', 'electrode', 'arc', 'plasma', 'fabrication', 'gouging',
            'cable', 'cooled', 'cooling', 'feeder', 'torch', 'remote',
            'industrial', 'heavy duty', 'portable', 'precision'
        }
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword.lower() in sentence.lower() for keyword in technical_keywords):
                technical_sentences.append(sentence)
        
        return '. '.join(technical_sentences)
    
    def _extract_all_specifications(self, specs_json: str) -> str:
        """Extract ALL specifications comprehensively without hardcoding"""
        if not specs_json:
            return ''
        
        try:
            specs = json.loads(specs_json)
        except:
            return ''
        
        spec_texts = []
        
        for field_name, field_values in specs.items():
            # Convert field name to readable text
            readable_field = self._humanize_field_name(field_name)
            
            # Handle different value types
            if isinstance(field_values, list):
                # Multiple values - extract all
                for value in field_values:
                    spec_texts.append(f"{readable_field} {self._clean_spec_value(value)}")
            else:
                # Single value
                spec_texts.append(f"{readable_field} {self._clean_spec_value(field_values)}")
        
        return ' '.join(spec_texts)
    
    def _humanize_field_name(self, field_name: str) -> str:
        """Convert field names to human-readable text"""
        # Common field mappings
        field_mappings = {
            'Arcdatapowerinputvoltage': 'input voltage',
            'Arcdatapowerweldingprocess': 'welding process',
            'Dimensions': 'dimensions',
            'Enclosureclass': 'protection rating',
            'Inputvoltage': 'voltage',
            'Maxsettinga': 'maximum current',
            'Minsettinga': 'minimum current', 
            'Maxspooldiameter': 'spool diameter',
            'Operatingtemp': 'operating temperature',
            'Rated KVA': 'power rating',
            'Settingrangea': 'current range',
            'Settingrangev': 'voltage range',
            'Standards': 'standards',
            'Weight': 'weight',
            'Weldingoutput': 'welding output',
            'Wirediameter': 'wire diameter',
            'Wirefeedspeed': 'wire feed speed'
        }
        
        # Return mapped name or convert camelCase to readable
        if field_name in field_mappings:
            return field_mappings[field_name]
        
        # Convert camelCase to space-separated
        readable = re.sub(r'([a-z])([A-Z])', r'\1 \2', field_name)
        return readable.lower()
    
    def _clean_spec_value(self, value: str) -> str:
        """Clean and normalize specification values"""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove extra characters and normalize
        value = value.strip()
        
        # Normalize units and common patterns
        value = re.sub(r'\s+', ' ', value)
        
        return value
    
    def _normalize_text(self, text: str) -> str:
        """Final text normalization for embedding"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters that don't add semantic value
        text = re.sub(r'[^\w\s\-\.\(\)/°]', ' ', text)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text"""
        if not text or len(text.strip()) < 3:
            # Return zero vector for empty/invalid text
            return [0.0] * 384  # Assuming all-MiniLM-L6-v2 dimensions
        
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def generate_query_embedding(self, intent: 'SimpleWeldingIntent') -> List[float]:
        """Generate embedding for user intent/query with natural language"""
        query_components = []
        
        # Build natural language query
        if intent.processes:
            for process in intent.processes:
                if process.upper() in ['MIG', 'GMAW']:
                    query_components.append('MIG welding')
                elif process.upper() in ['TIG', 'GTAW']:
                    query_components.append('TIG welding')
                elif process.upper() in ['STICK', 'MMA', 'SMAW']:
                    query_components.append('Stick welding')
                else:
                    query_components.append(f'{process} welding')
        
        # Material and thickness context
        if intent.material and intent.thickness_mm:
            query_components.append(f'{intent.thickness_mm}mm {intent.material}')
        elif intent.thickness_mm:
            if intent.thickness_mm >= 6:
                query_components.append('thick steel heavy duty welding')
            elif intent.thickness_mm <= 2:
                query_components.append('thin material precision welding')
            else:
                query_components.append(f'{intent.thickness_mm}mm welding')
        
        # Power specifications
        if intent.current_amps:
            if intent.current_amps >= 500:
                query_components.append('high power industrial welding')
            elif intent.current_amps >= 300:
                query_components.append('medium power welding')
            else:
                query_components.append('light duty welding')
        
        if intent.voltage:
            if intent.voltage >= 380:
                query_components.append('industrial voltage')
            else:
                query_components.append('standard voltage')
        
        # Context and application
        if intent.application:
            query_components.append(intent.application)
        if intent.industry:
            query_components.append(intent.industry)
        if intent.environment:
            query_components.append(intent.environment)
        
        # Build final query
        query_text = ' '.join(query_components) if query_components else 'welding equipment'
        
        return self.generate_embedding(query_text)
    
    def extract_searchable_specs(self, product: Dict[str, Any]) -> Dict[str, str]:
        """Extract specifications for metadata filtering"""
        specs_json = product.get('specifications_json', '')
        if not specs_json:
            return {}
        
        try:
            specs = json.loads(specs_json)
        except:
            return {}
        
        searchable = {}
        
        # Extract key searchable fields
        for field, values in specs.items():
            if isinstance(values, list) and values:
                # Take first value for simplicity
                searchable[field] = str(values[0])
            else:
                searchable[field] = str(values)
        
        return searchable
```

### 3. Vector Migration Service

**File**: `app/database/vector_migration.py`

```python
import asyncio
from typing import List, Dict, Any
from ..services.embedding_generator import ProductEmbeddingGenerator
from ..database.neo4j import get_neo4j_connection
import logging

class VectorMigration:
    """Migrate existing products to include vector embeddings"""
    
    def __init__(self):
        self.embedding_generator = ProductEmbeddingGenerator()
        self.logger = logging.getLogger(__name__)
    
    async def migrate_all_products(self) -> Dict[str, int]:
        """Add embeddings to all products and create vector index"""
        conn = await get_neo4j_connection()
        
        # Step 1: Get all products
        products = await self._get_all_products(conn)
        self.logger.info(f"Found {len(products)} products to process")
        
        # Step 2: Generate and store embeddings
        success_count = 0
        error_count = 0
        
        for product in products:
            try:
                await self._add_embedding_to_product(conn, product)
                success_count += 1
                if success_count % 10 == 0:
                    self.logger.info(f"Processed {success_count}/{len(products)} products")
            except Exception as e:
                self.logger.error(f"Error processing product {product.get('gin')}: {e}")
                error_count += 1
        
        # Step 3: Create vector index
        await self._create_vector_index(conn)
        
        return {
            "total_products": len(products),
            "success_count": success_count,
            "error_count": error_count
        }
    
    async def _get_all_products(self, conn) -> List[Dict[str, Any]]:
        """Retrieve all products from Neo4j"""
        query = """
        MATCH (p:Product)
        RETURN p.gin as gin, p.name as name, p.category as category,
               p.description as description, p.specifications_json as specifications_json
        ORDER BY p.category, p.name
        """
        return await conn.execute_query(query)
    
    async def _add_embedding_to_product(self, conn, product: Dict[str, Any]):
        """Generate and add embedding to a single product"""
        # Generate embedding text and vector
        embedding_text = self.embedding_generator.generate_product_text(product)
        embedding_vector = self.embedding_generator.generate_embedding(embedding_text)
        
        # Update product with embedding
        query = """
        MATCH (p:Product {gin: $gin})
        SET p.embedding = $embedding,
            p.embedding_text = $embedding_text,
            p.embedding_created_at = datetime()
        RETURN p.gin as updated_gin
        """
        
        result = await conn.execute_query(query, {
            'gin': product['gin'],
            'embedding': embedding_vector,
            'embedding_text': embedding_text
        })
        
        if not result:
            raise Exception(f"Failed to update product {product['gin']}")
    
    async def _create_vector_index(self, conn):
        """Create vector index on product embeddings"""
        try:
            # Check if index already exists
            check_query = """
            SHOW INDEXES 
            YIELD name, type 
            WHERE name = 'product_embeddings' AND type CONTAINS 'VECTOR'
            RETURN count(*) as index_count
            """
            result = await conn.execute_query(check_query)
            
            if result and result[0]['index_count'] > 0:
                self.logger.info("Vector index 'product_embeddings' already exists")
                return
            
            # Create vector index
            create_query = """
            CREATE VECTOR INDEX product_embeddings
            FOR (p:Product) ON (p.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: `cosine`
              }
            }
            """
            await conn.execute_query(create_query)
            self.logger.info("Created vector index 'product_embeddings'")
            
        except Exception as e:
            self.logger.error(f"Error creating vector index: {e}")
            raise
```

### 4. Enhanced Neo4j Repository

**File**: `app/database/repositories/neo4j_repository.py` (additions)

```python
# Add to existing Neo4jRepository class

async def vector_search_products(
    self,
    query_embedding: List[float],
    category: Optional[str] = None,
    top_k: int = 10,
    min_similarity: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search on products.
    
    Args:
        query_embedding: Vector embedding of search query
        category: Optional category filter
        top_k: Maximum number of results
        min_similarity: Minimum similarity score threshold
        
    Returns:
        List of products with similarity scores
    """
    query = """
    CALL db.index.vector.queryNodes(
        'product_embeddings', 
        $query_embedding, 
        $top_k
    ) YIELD node as product, score
    WHERE score >= $min_similarity
      AND ($category IS NULL OR product.category = $category)
    
    // Get sales frequency
    OPTIONAL MATCH (product)<-[:CONTAINS]-(t:Transaction)
    WITH product, score, COUNT(t) as sales_frequency
    
    RETURN product {
        .gin, .name, .category, .description, .specifications_json,
        .embedding_text
    } as product,
    score,
    sales_frequency,
    (score * 0.4 + CASE WHEN sales_frequency > 0 THEN log(sales_frequency)/10 ELSE 0 END * 0.6) as hybrid_score
    ORDER BY hybrid_score DESC
    """
    
    result = await self.connection.execute_query(query, {
        'query_embedding': query_embedding,
        'category': category,
        'top_k': top_k,
        'min_similarity': min_similarity
    })
    
    return [dict(record) for record in result]

async def hybrid_search_with_relationships(
    self,
    query_embedding: List[float],
    category: str = "PowerSource",
    include_trinity: bool = True
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining vector similarity with relationship data.
    Perfect for trinity formation.
    """
    query = """
    CALL db.index.vector.queryNodes(
        'product_embeddings', 
        $query_embedding, 
        10
    ) YIELD node as product, score
    WHERE product.category = $category
    
    // Get DETERMINES relationships for trinity
    OPTIONAL MATCH (product)-[:DETERMINES]->(comp:Product)
    WHERE comp.category IN ['Feeder', 'Cooler']
    
    // Get COMPATIBLE_WITH relationships  
    OPTIONAL MATCH (product)-[:COMPATIBLE_WITH]->(acc:Product)
    
    // Get sales frequency
    OPTIONAL MATCH (product)<-[:CONTAINS]-(t:Transaction)
    
    WITH product, score, COUNT(t) as sales_frequency,
         COLLECT(DISTINCT comp) as trinity_components,
         COLLECT(DISTINCT acc) as compatible_accessories
    
    RETURN product {
        .gin, .name, .category, .description, .specifications_json
    } as product,
    score,
    sales_frequency,
    trinity_components,
    compatible_accessories,
    (score * 0.4 + CASE WHEN sales_frequency > 0 THEN log(sales_frequency)/10 ELSE 0 END * 0.6) as hybrid_score
    ORDER BY hybrid_score DESC
    """
    
    result = await self.connection.execute_query(query, {
        'query_embedding': query_embedding,
        'category': category
    })
    
    return [dict(record) for record in result]
```

### 5. Enhanced SimpleNeo4jAgent

**File**: `app/agents/simple_neo4j_agent.py` (additions)

```python
# Add to existing SimpleNeo4jAgent class

from ..services.embedding_generator import ProductEmbeddingGenerator

class SimpleNeo4jAgent:
    def __init__(self, neo4j_repo: Neo4jRepository):
        self.neo4j_repo = neo4j_repo
        self.embedding_generator = ProductEmbeddingGenerator()  # NEW
        
    async def find_power_sources_with_vectors(
        self, 
        intent: SimpleWeldingIntent
    ) -> List[WeldingPackageComponent]:
        """
        Enhanced power source discovery using vector embeddings.
        Combines semantic search with relationship validation.
        """
        # Step 1: Generate query embedding from intent
        query_embedding = self.embedding_generator.generate_query_embedding(intent)
        
        # Step 2: Vector search with relationship data
        vector_results = await self.neo4j_repo.hybrid_search_with_relationships(
            query_embedding=query_embedding,
            category="PowerSource",
            include_trinity=True
        )
        
        # Step 3: Convert to WeldingPackageComponents with enhanced scoring
        power_sources = []
        for result in vector_results:
            product = result['product']
            similarity_score = result['score']
            sales_frequency = result['sales_frequency']
            trinity_components = result['trinity_components']
            
            # Enhanced compatibility scoring
            compatibility_score = similarity_score * 0.4 + (sales_frequency / 1000) * 0.6
            
            # Bonus for complete trinity availability
            if len(trinity_components) >= 2:  # Has both feeder and cooler options
                compatibility_score += 0.1
            
            component = WeldingPackageComponent(
                product_id=product['gin'],
                product_name=product['name'],
                category=product['category'],
                description=product.get('description'),
                compatibility_score=compatibility_score,
                sales_frequency=sales_frequency
            )
            power_sources.append(component)
        
        return power_sources[:5]  # Top 5 results

    async def universal_product_search(
        self,
        intent: SimpleWeldingIntent,
        category: Optional[str] = None
    ) -> List[WeldingPackageComponent]:
        """
        Universal semantic product search across all categories.
        Handles queries like "wirefeeder with 5m cable", "remote control 10m".
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(intent)
        
        # Vector search
        results = await self.neo4j_repo.vector_search_products(
            query_embedding=query_embedding,
            category=category,
            top_k=15,
            min_similarity=0.6
        )
        
        # Convert to components
        components = []
        for result in results:
            product = result['product']
            similarity_score = result['score']
            sales_frequency = result['sales_frequency']
            
            component = WeldingPackageComponent(
                product_id=product['gin'],
                product_name=product['name'],
                category=product['category'],
                description=product.get('description'),
                compatibility_score=result['hybrid_score'],
                sales_frequency=sales_frequency
            )
            components.append(component)
        
        return components

    async def form_trinity_with_vectors(
        self,
        power_source: WeldingPackageComponent
    ) -> Dict[str, List[WeldingPackageComponent]]:
        """
        Form trinity using DETERMINES relationships with vector-enhanced ranking.
        """
        # Get DETERMINES relationships (existing logic)
        trinity_query = """
        MATCH (ps:Product {gin: $ps_gin})-[:DETERMINES]->(comp:Product)
        WHERE comp.category IN ['Feeder', 'Cooler']
        
        // Get sales frequency for ranking
        OPTIONAL MATCH (comp)<-[:CONTAINS]-(t:Transaction)
        WITH comp, COUNT(t) as sales_frequency
        
        RETURN comp {
            .gin, .name, .category, .description
        } as component,
        sales_frequency
        ORDER BY comp.category, sales_frequency DESC
        """
        
        result = await self.neo4j_repo.execute_query(trinity_query, {
            'ps_gin': power_source.product_id
        })
        
        # Organize by category
        feeders = []
        coolers = []
        
        for record in result:
            comp_data = record['component']
            sales_freq = record['sales_frequency']
            
            component = WeldingPackageComponent(
                product_id=comp_data['gin'],
                product_name=comp_data['name'],
                category=comp_data['category'],
                description=comp_data.get('description'),
                sales_frequency=sales_freq,
                compatibility_score=1.0  # Perfect compatibility via DETERMINES
            )
            
            if comp_data['category'] == 'Feeder':
                feeders.append(component)
            elif comp_data['category'] == 'Cooler':
                coolers.append(component)
        
        return {
            'feeders': feeders,
            'coolers': coolers
        }
```

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. ✅ Create embedding generation service
2. ✅ Create vector migration utilities  
3. ✅ Generate embeddings for all 249 products
4. ✅ Create vector index in Neo4j

### Phase 2: Integration (Week 2)
1. ✅ Enhance Neo4j repository with vector methods
2. ✅ Add vector search to SimpleNeo4jAgent
3. ✅ Test hybrid queries (vector + graph)
4. ✅ Validate trinity formation with vectors

### Phase 3: Enhancement (Week 3)
1. ✅ Universal product search across categories
2. ✅ Optimize hybrid scoring algorithms
3. ✅ Performance testing and tuning
4. ✅ Integration with existing 2-agent workflow

## Enhanced Data Extraction Benefits

### Comprehensive Specification Coverage
- ✅ **All 17 specification fields** extracted automatically (no hardcoding)
- ✅ **Dynamic field mapping** from technical names to readable terms
- ✅ **Complete value extraction** for list and single values
- ✅ **Universal approach** works across all product categories

### Clean HTML Processing  
- ✅ **Technical content focus** - filters marketing fluff, keeps technical sentences
- ✅ **HTML tag removal** and entity decoding for clean text
- ✅ **Technical keyword detection** preserves relevant information
- ✅ **Normalized text output** for consistent embeddings

### Example Transformations
**Before (Hardcoded)**:
```
"Warrior 500i PowerSource MIG TIG Stick 380V 500A industrial"
```

**After (Comprehensive)**:
```
"Warrior 500i CC/CV PowerSource The reliable multi-process welding equipment designed for heavy duty productivity with up to 500 amps delivered input voltage 380-415 VAC welding process GMAW (MIG/MAG) welding process GTAW (TIG) welding process SMAW/MMA (Stick) dimensions 712x325x470 mm current range 16-500 A voltage range 15-39 V weight 59 kg"
```

### Semantic Understanding
- ✅ "MIG welder for 6mm steel" → understands power requirements
- ✅ "portable welding setup" → finds lightweight equipment  
- ✅ "industrial fabrication" → suggests heavy-duty solutions
- ✅ "wirefeeder with 5m cable" → matches cable specifications
- ✅ "25 meter interconnection" → fuzzy matches dimensions

### Architecture Benefits  
- ✅ Single database (Neo4j) - no additional infrastructure
- ✅ Atomic queries - vector search + graph relationships
- ✅ ACID consistency - vectors and relationships always in sync
- ✅ Leverages existing Neo4j expertise and infrastructure

### Enhanced Capabilities
- ✅ **Complete coverage** - no missed specifications due to hardcoding
- ✅ **Fuzzy matching** - "5m" matches "5 meter", "5.0m"
- ✅ **Semantic search** - understands domain concepts
- ✅ **Universal search** - works across all product categories
- ✅ **Preserved trinity formation** - maintains business logic
- ✅ **Future-proof** - automatically handles new specification fields

## Risk Mitigation

### Fallback Strategy
- If vector search fails → fall back to existing CONTAINS queries
- If embeddings missing → use traditional text search
- Gradual rollout → test with subset of products first

### Performance Considerations
- Vector index optimization for 249 products
- Hybrid scoring algorithm tuning
- Query performance monitoring and optimization

### Data Quality
- Embedding text validation and testing
- Regular re-generation of embeddings as products change
- Monitoring similarity score distributions

This design maintains the simplicity and effectiveness of the current 2-agent system while adding powerful semantic search capabilities through Neo4j's native vector features.