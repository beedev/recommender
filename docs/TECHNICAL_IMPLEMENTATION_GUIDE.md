# Technical Implementation Guide

**Detailed technical guide for implementing, operating, and maintaining the welding recommendation system's data pipeline and Neo4j infrastructure.**

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Data Transformation Implementation](#data-transformation-implementation)
3. [Neo4j Configuration](#neo4j-configuration)
4. [Loading Procedures](#loading-procedures)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Backup & Recovery](#backup--recovery)
8. [Performance Tuning](#performance-tuning)

---

## System Requirements

### **Infrastructure Requirements**

#### **Development Environment**
```yaml
Minimum Specifications:
  CPU: 4 cores, 2.5GHz
  RAM: 16GB
  Storage: 100GB SSD
  Network: 100Mbps

Recommended Specifications:
  CPU: 8 cores, 3.0GHz+
  RAM: 32GB
  Storage: 500GB NVMe SSD
  Network: 1Gbps
```

#### **Production Environment**
```yaml
Neo4j Server:
  CPU: 16+ cores
  RAM: 64GB+ (128GB recommended)
  Storage: 1TB+ NVMe SSD (RAID 10)
  Network: 10Gbps

Application Server:
  CPU: 8+ cores
  RAM: 32GB+
  Storage: 200GB SSD
  Network: 1Gbps
```

### **Software Dependencies**

#### **Core Dependencies**
```yaml
Python: 3.9+
Neo4j: 5.13+
Java: OpenJDK 17+
Node.js: 18+ (for frontend)

Python Packages:
  - neo4j==5.13.0
  - pandas==2.0.3
  - numpy==1.24.3
  - sentence-transformers==2.2.2
  - python-dotenv==1.0.0
  - beautifulsoup4==4.12.2
  - openpyxl==3.1.2
```

#### **System Libraries**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip python3-venv
sudo apt-get install -y build-essential libssl-dev libffi-dev
sudo apt-get install -y curl wget git

# macOS (via Homebrew)
brew install python@3.11 openjdk@17 git
```

---

## Data Transformation Implementation

### **Core Transformation Classes**

#### **1. PowerSource Master Extractor**

```python
class PowerSourceMasterExtractor:
    """
    Core transformation engine for PowerSource-centric data processing.
    
    Responsibilities:
    - Excel file parsing and validation
    - Product catalog enhancement
    - Compatibility rule extraction
    - Embedding generation coordination
    """
    
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.embedding_generator = EmbeddingGenerator()
        self.validator = DataValidator()
    
    def extract_product_catalog(self) -> List[Product]:
        """Extract and enhance product catalog"""
        
        # 1. Load base product data
        products = self.load_product_master()
        
        # 2. Enhance with specifications
        products = self.enhance_with_specifications(products)
        
        # 3. Generate embeddings
        products = self.embedding_generator.generate_embeddings(products)
        
        # 4. Validate data quality
        validation_report = self.validator.validate_products(products)
        
        if not validation_report.is_valid:
            raise ValidationError(f"Product validation failed: {validation_report.errors}")
        
        return products
    
    def extract_compatibility_rules(self, products: List[Product]) -> List[CompatibilityRule]:
        """Extract compatibility relationships from Excel matrices"""
        
        compatibility_rules = []
        
        for powersource_gin in self.config.powersource_gins:
            # Load PowerSource-specific compatibility matrix
            matrix_file = self.find_compatibility_matrix(powersource_gin)
            
            if matrix_file:
                rules = self.parse_compatibility_matrix(matrix_file, powersource_gin)
                
                # Enhance with confidence scoring
                rules = self.calculate_confidence_scores(rules)
                
                # Validate against product catalog
                rules = self.validate_product_references(rules, products)
                
                compatibility_rules.extend(rules)
        
        return compatibility_rules
```

#### **2. Embedding Generation System**

```python
class EmbeddingGenerator:
    """
    Manages semantic embedding generation for products.
    
    Features:
    - Batch processing for efficiency
    - Text preprocessing and cleaning
    - Model caching and optimization
    - Quality validation
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = 384
    
    def generate_embeddings(self, products: List[Product], batch_size: int = 32) -> List[Product]:
        """Generate embeddings for product catalog"""
        
        logger.info(f"Generating embeddings for {len(products)} products")
        
        # Process in batches for memory efficiency
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            # Prepare text for embedding
            texts = [self.prepare_embedding_text(product) for product in batch]
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            # Assign embeddings to products
            for product, embedding in zip(batch, embeddings):
                product.embedding = embedding.tolist()
                product.embedding_model = self.model_name
                product.embedding_dimension = self.dimension
        
        logger.info("Embedding generation completed")
        return products
    
    def prepare_embedding_text(self, product: Product) -> str:
        """Prepare comprehensive text for embedding generation"""
        
        components = []
        
        # Product name (highest semantic weight)
        if product.name:
            components.append(f"Product: {product.name}")
        
        # Category provides context
        if product.category:
            components.append(f"Category: {product.category}")
        
        # Clean and process description
        if product.description:
            cleaned_desc = self.clean_description(product.description)
            if len(cleaned_desc) > 50:  # Only include substantial descriptions
                components.append(cleaned_desc)
        
        # Extract key specifications
        if product.specifications_json:
            key_specs = self.extract_key_specifications(product.specifications_json)
            components.extend(key_specs)
        
        # Join with proper spacing
        full_text = ". ".join(components)
        
        # Ensure reasonable length (BERT models have token limits)
        if len(full_text) > 400:
            full_text = full_text[:400] + "..."
        
        return full_text
    
    def clean_description(self, description: str) -> str:
        """Clean HTML and normalize description text"""
        
        # Remove HTML tags
        soup = BeautifulSoup(description, 'html.parser')
        cleaned = soup.get_text()
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove special characters that don't add semantic value
        cleaned = re.sub(r'[^\w\s\-\.,;:()\[\]]', '', cleaned)
        
        return cleaned
    
    def extract_key_specifications(self, specs_json: str) -> List[str]:
        """Extract semantically meaningful specifications"""
        
        try:
            specs = json.loads(specs_json)
        except (json.JSONDecodeError, TypeError):
            return []
        
        key_spec_patterns = [
            'welding.*process',
            'input.*voltage',
            'output.*amp',
            'duty.*cycle',
            'weight',
            'dimensions',
            'enclosure.*class'
        ]
        
        key_specs = []
        
        for spec_name, spec_values in specs.items():
            # Check if this specification matches key patterns
            if any(re.search(pattern, spec_name.lower()) for pattern in key_spec_patterns):
                if isinstance(spec_values, list) and spec_values:
                    # Take the first value or combine meaningful ones
                    spec_text = f"{spec_name}: {', '.join(map(str, spec_values[:3]))}"
                    key_specs.append(spec_text)
                elif spec_values:
                    spec_text = f"{spec_name}: {spec_values}"
                    key_specs.append(spec_text)
        
        return key_specs[:5]  # Limit to most important specs
```

#### **3. Data Validation Framework**

```python
class DataValidator:
    """
    Comprehensive data validation for all transformation stages.
    
    Validation Categories:
    - Schema validation
    - Business rule validation
    - Reference integrity
    - Data quality checks
    """
    
    def validate_products(self, products: List[Product]) -> ValidationReport:
        """Comprehensive product validation"""
        
        errors = []
        warnings = []
        
        # Required field validation
        for product in products:
            if not product.product_id:
                errors.append(f"Missing product_id for product: {product.name}")
            
            if not product.gin or len(product.gin) != 10:
                errors.append(f"Invalid GIN format for {product.product_id}: {product.gin}")
            
            if not product.name or len(product.name.strip()) < 3:
                errors.append(f"Invalid name for {product.product_id}: {product.name}")
            
            if product.category not in VALID_CATEGORIES:
                warnings.append(f"Unknown category for {product.product_id}: {product.category}")
        
        # Duplicate detection
        gin_counts = {}
        product_id_counts = {}
        
        for product in products:
            gin_counts[product.gin] = gin_counts.get(product.gin, 0) + 1
            product_id_counts[product.product_id] = product_id_counts.get(product.product_id, 0) + 1
        
        # Check for duplicates
        for gin, count in gin_counts.items():
            if count > 1:
                errors.append(f"Duplicate GIN found: {gin} ({count} occurrences)")
        
        for product_id, count in product_id_counts.items():
            if count > 1:
                errors.append(f"Duplicate product_id found: {product_id} ({count} occurrences)")
        
        # Embedding validation
        embedding_errors = self.validate_embeddings(products)
        errors.extend(embedding_errors)
        
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_products=len(products),
            valid_products=len(products) - len([e for e in errors if "product_id" in e])
        )
    
    def validate_compatibility_rules(self, rules: List[CompatibilityRule], products: List[Product]) -> ValidationReport:
        """Validate compatibility rules against product catalog"""
        
        errors = []
        warnings = []
        
        # Build product lookup
        product_gins = {p.gin for p in products}
        
        for rule in rules:
            # Check source product exists
            if rule.source_gin not in product_gins:
                errors.append(f"Source GIN not found in catalog: {rule.source_gin}")
            
            # Check target product exists
            if rule.target_gin not in product_gins:
                errors.append(f"Target GIN not found in catalog: {rule.target_gin}")
            
            # Validate confidence score
            if not (0.0 <= rule.confidence <= 1.0):
                errors.append(f"Invalid confidence score: {rule.confidence} for rule {rule.rule_id}")
            
            # Check for self-references
            if rule.source_gin == rule.target_gin:
                warnings.append(f"Self-referencing compatibility rule: {rule.rule_id}")
        
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_rules=len(rules),
            valid_rules=len(rules) - len(errors)
        )
```

### **Configuration Management**

#### **Transformation Configuration**

```json
{
  "transformation_config": {
    "powersource_gins": [
      "0445100880",
      "0445250880",
      "0446200880"
    ],
    "input_sources": {
      "product_master": "Datasets/product_master.xlsx",
      "specifications": "Datasets/product_specifications.xlsx", 
      "compatibility_matrices": "Datasets/compatibility/",
      "golden_packages": "Datasets/golden_packages.xlsx",
      "sales_history": "Datasets/sales_history.xlsx"
    },
    "output_destination": "neo4jdatasets/",
    "embedding_config": {
      "model_name": "all-MiniLM-L6-v2",
      "batch_size": 32,
      "max_length": 400,
      "normalize": true
    },
    "validation_config": {
      "strict_mode": true,
      "max_errors": 10,
      "fail_on_warnings": false
    }
  }
}
```

---

## Neo4j Configuration

### **Database Setup**

#### **Neo4j Installation & Configuration**

```bash
# Download and install Neo4j
wget https://neo4j.com/artifact.php?name=neo4j-community-5.13.0-unix.tar.gz
tar -xzf neo4j-community-5.13.0-unix.tar.gz
cd neo4j-community-5.13.0

# Configure Neo4j
cp conf/neo4j.conf conf/neo4j.conf.backup
```

#### **Critical Configuration Settings**

```properties
# conf/neo4j.conf

# Server configuration
server.default_listen_address=0.0.0.0
server.bolt.listen_address=:7687
server.http.listen_address=:7474

# Memory settings (adjust based on available RAM)
server.memory.heap.initial_size=8g
server.memory.heap.max_size=16g
server.memory.pagecache.size=24g

# Performance settings
dbms.transaction.timeout=300s
dbms.query.timeout=300s
db.transaction.concurrent.maximum=1000

# Security settings
dbms.security.auth_enabled=true
dbms.security.procedures.unrestricted=apoc.*,gds.*

# Vector index settings (Neo4j 5.13+)
db.vector.enabled=true
db.vector.similarity.function=cosine

# Logging
dbms.logs.query.enabled=INFO
dbms.logs.query.threshold=1s
dbms.logs.query.parameter_logging_enabled=true
```

#### **Environment Variables**

```bash
# .env configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j

# Optional: Neo4j Aura Cloud
# NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=your_aura_password
```

### **Database Schema Setup**

#### **Constraints and Indexes Creation**

```cypher
-- Create unique constraints (primary keys)
CREATE CONSTRAINT product_id_unique 
FOR (p:Product) REQUIRE p.product_id IS UNIQUE;

CREATE CONSTRAINT package_id_unique 
FOR (g:GoldenPackage) REQUIRE g.package_id IS UNIQUE;

CREATE CONSTRAINT sale_id_unique 
FOR (s:Sale) REQUIRE s.sale_id IS UNIQUE;

-- Create business key indexes
CREATE INDEX product_gin_index 
FOR (p:Product) ON (p.gin);

CREATE INDEX product_name_index 
FOR (p:Product) ON (p.name);

CREATE INDEX product_category_index 
FOR (p:Product) ON (p.category);

-- Create composite indexes for common query patterns
CREATE INDEX product_category_availability 
FOR (p:Product) ON (p.category, p.is_available);

CREATE INDEX product_availability_country 
FOR (p:Product) ON (p.is_available, p.countries_available);

-- Create date indexes for time-based queries
CREATE INDEX sale_date_index 
FOR (s:Sale) ON (s.sale_date);

CREATE INDEX sale_region_date 
FOR (s:Sale) ON (s.region, s.sale_date);

-- Create relationship indexes
CREATE INDEX compatibility_confidence 
FOR ()-[r:COMPATIBLE_WITH]-() ON (r.confidence);

CREATE INDEX cooccurrence_frequency 
FOR ()-[r:CO_OCCURS]-() ON (r.frequency, r.confidence);
```

#### **Vector Index Creation**

```cypher
-- Create vector index for semantic search
CREATE VECTOR INDEX product_embeddings 
FOR (p:Product) ON (p.embedding) 
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};

-- Verify vector index creation
SHOW INDEXES YIELD name, labelsOrTypes, properties, type
WHERE type = "VECTOR"
RETURN name, labelsOrTypes, properties;
```

### **Database Optimization**

#### **Memory Configuration Calculation**

```python
def calculate_optimal_memory_settings(total_ram_gb: int, dataset_size_gb: int) -> dict:
    """Calculate optimal Neo4j memory settings"""
    
    # Reserve 25% for OS and other applications
    available_ram = total_ram_gb * 0.75
    
    # Page cache: Should fit the entire dataset + 50% buffer
    page_cache = min(dataset_size_gb * 1.5, available_ram * 0.6)
    
    # Heap: Remaining memory split between initial and max
    remaining = available_ram - page_cache
    heap_size = min(remaining * 0.8, 32)  # Max 32GB for heap
    
    return {
        "heap_initial": f"{int(heap_size * 0.5)}g",
        "heap_max": f"{int(heap_size)}g", 
        "page_cache": f"{int(page_cache)}g"
    }

# Example for 64GB server with 10GB dataset
settings = calculate_optimal_memory_settings(64, 10)
print(settings)
# {'heap_initial': '13g', 'heap_max': '26g', 'page_cache': '15g'}
```

---

## Loading Procedures

### **Data Loading Implementation**

#### **Core Loading Classes**

```python
class Neo4jDataLoader:
    """
    Comprehensive Neo4j data loading with transaction management.
    
    Features:
    - Batch processing for performance
    - Transaction safety
    - Progress tracking
    - Error recovery
    """
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.batch_size = 1000
        self.session_config = {"database": "neo4j"}
    
    def load_products(self, products: List[dict], mode: str = "merge") -> LoadingReport:
        """Load products with configurable merge strategy"""
        
        report = LoadingReport("products")
        
        try:
            # Process in batches
            for batch_start in range(0, len(products), self.batch_size):
                batch = products[batch_start:batch_start + self.batch_size]
                
                with self.driver.session(**self.session_config) as session:
                    if mode == "merge":
                        result = session.execute_write(self._merge_product_batch, batch)
                    elif mode == "create":
                        result = session.execute_write(self._create_product_batch, batch)
                    else:
                        raise ValueError(f"Unknown loading mode: {mode}")
                    
                    report.add_batch_result(result)
                
                # Progress reporting
                processed = min(batch_start + self.batch_size, len(products))
                progress = (processed / len(products)) * 100
                logger.info(f"Loaded {processed}/{len(products)} products ({progress:.1f}%)")
        
        except Exception as e:
            report.add_error(f"Product loading failed: {str(e)}")
            logger.error(f"Product loading error: {e}")
        
        return report
    
    def _merge_product_batch(self, tx, products: List[dict]) -> dict:
        """Merge product batch with conflict resolution"""
        
        query = """
        UNWIND $products AS product
        MERGE (p:Product {product_id: product.product_id})
        SET p.name = product.name,
            p.category = product.category,
            p.gin = product.gin,
            p.description = product.description,
            p.specifications_json = product.specifications_json,
            p.embedding = product.embedding,
            p.countries_available = product.countries_available,
            p.is_available = product.is_available,
            p.updated_at = datetime()
        ON CREATE SET 
            p.created_at = datetime()
        RETURN count(p) as created_count
        """
        
        result = tx.run(query, products=products)
        return {"created": result.single()["created_count"]}
    
    def load_compatibility_rules(self, rules: List[dict]) -> LoadingReport:
        """Load compatibility relationships with validation"""
        
        report = LoadingReport("compatibility_rules")
        
        try:
            for batch_start in range(0, len(rules), self.batch_size):
                batch = rules[batch_start:batch_start + self.batch_size]
                
                with self.driver.session(**self.session_config) as session:
                    result = session.execute_write(self._create_compatibility_batch, batch)
                    report.add_batch_result(result)
        
        except Exception as e:
            report.add_error(f"Compatibility loading failed: {str(e)}")
        
        return report
    
    def _create_compatibility_batch(self, tx, rules: List[dict]) -> dict:
        """Create compatibility relationships with validation"""
        
        query = """
        UNWIND $rules AS rule
        MATCH (source:Product {gin: rule.source_gin})
        MATCH (target:Product {gin: rule.target_gin})
        MERGE (source)-[r:COMPATIBLE_WITH]->(target)
        SET r.confidence = rule.confidence,
            r.rule_id = rule.rule_id,
            r.metadata_json = rule.metadata_json,
            r.created_at = datetime()
        RETURN count(r) as relationships_created
        """
        
        result = tx.run(query, rules=rules)
        return {"relationships": result.single()["relationships_created"]}
```

#### **Loading Order Management**

```python
class LoadingOrchestrator:
    """Manages loading order and dependencies"""
    
    LOADING_STAGES = [
        {
            "name": "products",
            "file": "product_catalog.json",
            "loader": "load_products",
            "dependencies": []
        },
        {
            "name": "compatibility",
            "file": "compatibility_rules.json", 
            "loader": "load_compatibility_rules",
            "dependencies": ["products"]
        },
        {
            "name": "golden_packages",
            "file": "golden_packages.json",
            "loader": "load_golden_packages", 
            "dependencies": ["products"]
        },
        {
            "name": "sales",
            "file": "sales_data.json",
            "loader": "load_sales_data",
            "dependencies": ["products"]
        }
    ]
    
    def execute_loading_pipeline(self, data_dir: str, mode: str = "clean") -> LoadingSession:
        """Execute complete loading pipeline with dependency management"""
        
        session = LoadingSession()
        
        if mode == "clean":
            self.cleanup_database()
        
        for stage in self.LOADING_STAGES:
            # Check dependencies
            if not self._dependencies_satisfied(stage["dependencies"], session):
                raise DependencyError(f"Dependencies not satisfied for {stage['name']}")
            
            # Load stage data
            data_file = os.path.join(data_dir, stage["file"])
            
            if os.path.exists(data_file):
                report = self._load_stage(stage, data_file, mode)
                session.add_stage_report(stage["name"], report)
            else:
                logger.warning(f"Data file not found: {data_file}")
        
        return session
```

### **Database Cleanup Procedures**

#### **Safe Cleanup Implementation**

```python
def cleanup_database_safely(driver, backup_first: bool = True) -> CleanupReport:
    """Safely clean database with optional backup"""
    
    report = CleanupReport()
    
    try:
        with driver.session() as session:
            # Get current statistics
            stats = session.run("""
                MATCH (n) 
                RETURN labels(n)[0] as label, count(n) as count 
                ORDER BY label
            """).data()
            
            report.pre_cleanup_stats = stats
            
            if backup_first:
                backup_path = create_database_backup(driver)
                report.backup_path = backup_path
            
            # Delete all relationships first (safer)
            result = session.run("MATCH ()-[r]-() DELETE r RETURN count(r) as deleted")
            report.relationships_deleted = result.single()["deleted"]
            
            # Delete all nodes
            result = session.run("MATCH (n) DELETE n RETURN count(n) as deleted")
            report.nodes_deleted = result.single()["deleted"]
            
            # Drop vector index (will be recreated)
            try:
                session.run("DROP INDEX product_embeddings IF EXISTS")
                report.indexes_dropped.append("product_embeddings")
            except Exception as e:
                logger.warning(f"Could not drop vector index: {e}")
            
            report.success = True
            logger.info(f"Database cleanup completed: {report.nodes_deleted} nodes, {report.relationships_deleted} relationships")
    
    except Exception as e:
        report.success = False
        report.error = str(e)
        logger.error(f"Database cleanup failed: {e}")
    
    return report
```

---

## Monitoring & Maintenance

### **Performance Monitoring**

#### **Query Performance Tracking**

```python
class Neo4jPerformanceMonitor:
    """Monitor Neo4j performance and query patterns"""
    
    def __init__(self, driver):
        self.driver = driver
        self.metrics = defaultdict(list)
    
    def get_query_performance_stats(self) -> dict:
        """Get query performance statistics"""
        
        with self.driver.session() as session:
            # Get slow queries
            slow_queries = session.run("""
                CALL dbms.listQueries() 
                YIELD queryId, query, elapsedTimeMillis, allocatedBytes
                WHERE elapsedTimeMillis > 1000
                RETURN query, elapsedTimeMillis, allocatedBytes
                ORDER BY elapsedTimeMillis DESC
                LIMIT 10
            """).data()
            
            # Get index usage
            index_usage = session.run("""
                CALL db.indexes() 
                YIELD name, labelsOrTypes, properties, state, populationPercent
                RETURN name, labelsOrTypes, properties, state, populationPercent
            """).data()
            
            # Get memory usage
            memory_stats = session.run("""
                CALL dbms.queryJmx('java.lang:type=Memory') 
                YIELD attributes
                RETURN attributes.HeapMemoryUsage as heap,
                       attributes.NonHeapMemoryUsage as nonHeap
            """).data()
            
            return {
                "slow_queries": slow_queries,
                "index_usage": index_usage,
                "memory_stats": memory_stats,
                "timestamp": datetime.now().isoformat()
            }
    
    def monitor_vector_index_performance(self) -> dict:
        """Monitor vector index query performance"""
        
        # Test vector query performance
        test_vector = [0.1] * 384  # Test vector
        
        with self.driver.session() as session:
            start_time = time.time()
            
            result = session.run("""
                CALL db.index.vector.queryNodes('product_embeddings', 10, $vector)
                YIELD node, score
                RETURN count(*) as result_count
            """, vector=test_vector)
            
            query_time = time.time() - start_time
            result_count = result.single()["result_count"]
            
            return {
                "vector_query_time_ms": query_time * 1000,
                "result_count": result_count,
                "index_status": "healthy" if query_time < 0.1 else "slow"
            }
```

#### **Database Health Checks**

```python
def perform_health_check(driver) -> HealthCheckReport:
    """Comprehensive database health check"""
    
    report = HealthCheckReport()
    
    try:
        with driver.session() as session:
            # Connection test
            session.run("RETURN 1").single()
            report.connection_status = "healthy"
            
            # Data integrity checks
            node_counts = session.run("""
                MATCH (n) 
                RETURN labels(n)[0] as label, count(n) as count
            """).data()
            report.node_counts = {item["label"]: item["count"] for item in node_counts}
            
            # Relationship integrity
            orphaned_relationships = session.run("""
                MATCH ()-[r:COMPATIBLE_WITH]->()
                WHERE NOT EXISTS {
                    MATCH (p1:Product)-[r]->(p2:Product)
                }
                RETURN count(r) as orphaned_count
            """).single()["orphaned_count"]
            
            report.orphaned_relationships = orphaned_relationships
            
            # Vector index health
            vector_index_exists = session.run("""
                SHOW INDEXES 
                WHERE name = 'product_embeddings'
                RETURN count(*) as count
            """).single()["count"] > 0
            
            report.vector_index_status = "exists" if vector_index_exists else "missing"
            
            # Query performance sample
            perf_sample = session.run("""
                MATCH (p:Product)
                WHERE p.is_available = true
                RETURN count(p) as available_products
            """)
            
            report.query_performance = "healthy"
            report.overall_status = "healthy"
    
    except Exception as e:
        report.overall_status = "error"
        report.error_details = str(e)
    
    return report
```

### **Maintenance Procedures**

#### **Index Maintenance**

```cypher
-- Rebuild vector index if performance degrades
DROP INDEX product_embeddings IF EXISTS;

CREATE VECTOR INDEX product_embeddings 
FOR (p:Product) ON (p.embedding) 
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};

-- Update database statistics
CALL db.stats.collect();

-- Check index status
CALL db.indexes() 
YIELD name, state, populationPercent
WHERE state <> 'ONLINE' OR populationPercent < 100.0
RETURN name, state, populationPercent;
```

#### **Database Optimization**

```cypher
-- Identify unused indexes
CALL db.indexes() 
YIELD name, labelsOrTypes, properties, uniqueness
RETURN name, labelsOrTypes, properties, uniqueness;

-- Check constraint violations
CALL db.constraints() 
YIELD name, labelsOrTypes, properties, type
RETURN name, labelsOrTypes, properties, type;

-- Analyze query patterns
CALL dbms.listQueries() 
YIELD queryId, query, elapsedTimeMillis, activeLockCount
WHERE elapsedTimeMillis > 100
RETURN query, elapsedTimeMillis, activeLockCount
ORDER BY elapsedTimeMillis DESC
LIMIT 20;
```

---

## Troubleshooting Guide

### **Common Issues & Solutions**

#### **1. Connection Issues**

**Problem**: Cannot connect to Neo4j database

**Diagnosis**:
```bash
# Test basic connectivity
curl http://localhost:7474

# Check Neo4j service status
neo4j status

# Verify configuration
cat neo4j.conf | grep -E "(listen_address|auth_enabled)"
```

**Solutions**:
```bash
# Start Neo4j service
neo4j start

# Reset password if needed
neo4j-admin dbms set-initial-password newpassword

# Check firewall rules
sudo ufw status
sudo ufw allow 7474
sudo ufw allow 7687
```

#### **2. Loading Performance Issues**

**Problem**: Data loading takes too long

**Diagnosis**:
```python
# Monitor loading progress
def diagnose_loading_performance(driver):
    with driver.session() as session:
        # Check active transactions
        result = session.run("CALL dbms.listTransactions()")
        
        # Check lock conflicts
        locks = session.run("CALL dbms.listQueries() YIELD activeLockCount")
        
        # Check memory usage
        memory = session.run("CALL dbms.queryJmx('java.lang:type=Memory')")
        
        return {
            "active_transactions": result.data(),
            "lock_conflicts": locks.data(),
            "memory_usage": memory.data()
        }
```

**Solutions**:
- Increase batch size for bulk operations
- Drop indexes during loading, recreate after
- Increase transaction timeout
- Monitor memory usage and adjust heap size

#### **3. Vector Index Issues**

**Problem**: Vector queries are slow or failing

**Diagnosis**:
```cypher
-- Check vector index status
SHOW INDEXES WHERE type = "VECTOR";

-- Test vector query
CALL db.index.vector.queryNodes('product_embeddings', 5, [0.1, 0.2, ...])
YIELD node, score
RETURN count(*);

-- Check embedding data
MATCH (p:Product) 
WHERE p.embedding IS NOT NULL
RETURN count(p) as products_with_embeddings, 
       size(p.embedding) as embedding_dimensions
LIMIT 1;
```

**Solutions**:
```cypher
-- Recreate vector index
DROP INDEX product_embeddings IF EXISTS;
CREATE VECTOR INDEX product_embeddings 
FOR (p:Product) ON (p.embedding) 
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};

-- Verify embedding consistency
MATCH (p:Product) 
WHERE p.embedding IS NOT NULL AND size(p.embedding) <> 384
RETURN p.product_id, size(p.embedding);
```

#### **4. Memory Issues**

**Problem**: OutOfMemory errors during operations

**Diagnosis**:
```bash
# Check system memory
free -h

# Check Neo4j heap usage
jstat -gc [neo4j_pid]

# Check page cache usage
neo4j-admin memrec --memory=64g
```

**Solutions**:
```properties
# Adjust Neo4j memory settings
server.memory.heap.initial_size=16g
server.memory.heap.max_size=32g
server.memory.pagecache.size=20g

# Reduce concurrent connections
db.transaction.concurrent.maximum=500
```

---

## Backup & Recovery

### **Backup Procedures**

#### **Automated Backup Script**

```bash
#!/bin/bash
# Neo4j backup automation script

NEO4J_HOME="/opt/neo4j"
BACKUP_DIR="/backup/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/neo4j_backup_$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop Neo4j for consistent backup
$NEO4J_HOME/bin/neo4j stop

# Create backup
$NEO4J_HOME/bin/neo4j-admin database backup neo4j \
  --to-path="$BACKUP_PATH" \
  --verbose

# Start Neo4j
$NEO4J_HOME/bin/neo4j start

# Compress backup
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "$(basename $BACKUP_PATH)"
rm -rf "$BACKUP_PATH"

# Keep only last 7 backups
find "$BACKUP_DIR" -name "neo4j_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_PATH.tar.gz"
```

#### **Online Backup (Enterprise)**

```bash
# Online backup for Neo4j Enterprise
neo4j-admin database backup neo4j \
  --from=bolt://localhost:7687 \
  --username=neo4j \
  --password=password \
  --to-path=/backup/online_backup_$(date +%Y%m%d)
```

### **Recovery Procedures**

#### **Full Database Restore**

```bash
#!/bin/bash
# Database restore procedure

BACKUP_FILE="$1"
NEO4J_HOME="/opt/neo4j"

if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop Neo4j
$NEO4J_HOME/bin/neo4j stop

# Extract backup
TEMP_DIR="/tmp/neo4j_restore"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restore database
$NEO4J_HOME/bin/neo4j-admin database restore neo4j \
  --from-path="$TEMP_DIR/$(basename $BACKUP_FILE .tar.gz)" \
  --overwrite-destination=true

# Clean up
rm -rf "$TEMP_DIR"

# Start Neo4j
$NEO4J_HOME/bin/neo4j start

echo "Database restored from $BACKUP_FILE"
```

#### **Point-in-Time Recovery**

```python
def restore_to_point_in_time(driver, target_timestamp: datetime):
    """Restore database to specific point in time using transaction logs"""
    
    with driver.session() as session:
        # Find transactions after target timestamp
        problematic_transactions = session.run("""
            MATCH (n)
            WHERE n.updated_at > $target_timestamp OR n.created_at > $target_timestamp
            RETURN count(n) as affected_nodes
        """, target_timestamp=target_timestamp).single()["affected_nodes"]
        
        if problematic_transactions > 0:
            logger.warning(f"Found {problematic_transactions} nodes created/modified after target time")
            
            # Option 1: Remove newer data
            confirmation = input(f"Remove {problematic_transactions} newer records? (y/N): ")
            if confirmation.lower() == 'y':
                session.run("""
                    MATCH (n)
                    WHERE n.updated_at > $target_timestamp OR n.created_at > $target_timestamp
                    DETACH DELETE n
                """, target_timestamp=target_timestamp)
        
        return {"restored": True, "affected_nodes": problematic_transactions}
```

---

## Performance Tuning

### **Query Optimization**

#### **Index Strategy**

```cypher
-- Create composite indexes for common query patterns
CREATE INDEX product_search_index 
FOR (p:Product) ON (p.category, p.is_available, p.countries_available);

-- Create text indexes for search
CREATE TEXT INDEX product_name_text 
FOR (p:Product) ON (p.name);

CREATE TEXT INDEX product_description_text 
FOR (p:Product) ON (p.description);
```

#### **Query Pattern Optimization**

```cypher
-- Optimized product search with filters
MATCH (p:Product)
WHERE p.category = $category 
  AND p.is_available = true
  AND ANY(country IN p.countries_available WHERE country = $target_country)
WITH p
ORDER BY p.name
SKIP $offset
LIMIT $limit
RETURN p;

-- Optimized compatibility query with confidence filtering
MATCH (ps:Product {gin: $powersource_gin})-[c:COMPATIBLE_WITH]->(compatible:Product)
WHERE compatible.is_available = true
  AND c.confidence >= $min_confidence
WITH compatible, c.confidence as confidence
ORDER BY confidence DESC
LIMIT $limit
RETURN compatible, confidence;

-- Optimized vector search with pre-filtering
MATCH (candidates:Product)
WHERE candidates.is_available = true 
  AND candidates.category IN $target_categories
WITH collect(candidates) as filtered_products

CALL db.index.vector.queryNodes('product_embeddings', $limit * 2, $query_vector)
YIELD node, score
WHERE node IN filtered_products
RETURN node, score
ORDER BY score DESC
LIMIT $limit;
```

### **System Optimization**

#### **Operating System Tuning**

```bash
# Increase file descriptor limits
echo "neo4j soft nofile 40000" >> /etc/security/limits.conf
echo "neo4j hard nofile 40000" >> /etc/security/limits.conf

# Optimize virtual memory
echo 'vm.swappiness=1' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=50' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=80' >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

#### **JVM Tuning**

```properties
# Additional JVM settings for Neo4j
dbms.jvm.additional=-XX:+UseG1GC
dbms.jvm.additional=-XX:+UnlockExperimentalVMOptions
dbms.jvm.additional=-XX:+TrustFinalNonStaticFields
dbms.jvm.additional=-XX:+DisableExplicitGC
dbms.jvm.additional=-XX:MaxGCPauseMillis=300
dbms.jvm.additional=-XX:+UseStringDeduplication
```

---

**Document Version**: 1.0  
**Last Updated**: September 2025  
**Next Review**: December 2025

This comprehensive technical guide provides the foundation for implementing, operating, and maintaining the welding recommendation system's data infrastructure. Regular updates and performance monitoring ensure optimal system performance and reliability.