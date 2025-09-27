"""
Compatibility Rules Loader
Bharath's Quality-First Implementation

This loader handles compatibility_rules.json and creates the COMPATIBLE_WITH
and DETERMINES relationships between products. It validates all product
references against the loaded product catalog.

Features:
- Product reference validation (flags missing products)
- Rule type validation and normalization
- Confidence score validation
- Bidirectional relationship creation
- Rule deduplication
- Performance optimized batch loading
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass

from .base_loader import BaseLoader, ValidationResult


@dataclass
class CompatibilityRule:
    """Structured compatibility rule with validation"""
    rule_id: str
    rule_type: str
    source_gin: str
    target_gin: str
    source_category: str
    target_category: str
    confidence: float = 0.95
    bidirectional: bool = False
    metadata: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = ""


class CompatibilityLoader(BaseLoader):
    """
    Compatibility Rules Loader
    
    Loads compatibility relationships from compatibility_rules.json with:
    - Product reference validation (must exist in catalog)
    - Rule type validation (COMPATIBLE_WITH, DETERMINES)
    - Confidence score validation (0.0 - 1.0)
    - Duplicate rule detection
    - Bidirectional relationship handling
    """
    
    VALID_RULE_TYPES = {
        'COMPATIBLE_WITH', 'DETERMINES', 'REQUIRES', 'EXCLUDES'
    }
    
    REQUIRED_FIELDS = {
        'rule_id', 'rule_type', 'source_gin', 'target_gin',
        'source_category', 'target_category'
    }
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 postgres_config: Dict[str, str] = None):
        """Initialize Compatibility Loader"""
        super().__init__(neo4j_uri, neo4j_user, neo4j_password, postgres_config)
        
        # Compatibility-specific tracking
        self._existing_rules: Set[str] = set()
        self._product_categories: Dict[str, str] = {}
        self._load_existing_rules()
        self._load_product_categories()
    
    def _load_existing_rules(self):
        """Load existing rule IDs to avoid duplicates"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run("""
                    MATCH (a:Product)-[r:COMPATIBLE_WITH|DETERMINES]->(b:Product)
                    RETURN r.rule_id as rule_id
                """)
                self._existing_rules = {record["rule_id"] for record in result if record["rule_id"]}
                self.logger.info(f"Found {len(self._existing_rules)} existing compatibility rules")
        except Exception as e:
            self.logger.info(f"No existing rules found (fresh database): {e}")
    
    def _load_product_categories(self):
        """Load product categories for validation"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run("MATCH (p:Product) RETURN p.gin as gin, p.category as category")
                self._product_categories = {
                    record["gin"]: record["category"] 
                    for record in result
                }
                self.logger.info(f"Loaded {len(self._product_categories)} product categories")
        except Exception as e:
            self.logger.warning(f"Could not load product categories: {e}")
    
    def _validate_json_structure(self, data: Any, file_path: Path) -> ValidationResult:
        """
        Validate compatibility_rules.json structure
        
        Expected structure:
        {
            "metadata": {...},
            "compatibility_rules": [
                {
                    "rule_id": "string",
                    "rule_type": "COMPATIBLE_WITH|DETERMINES",
                    "source_gin": "string",
                    "target_gin": "string", 
                    "source_category": "string",
                    "target_category": "string",
                    "confidence": float,
                    ...
                }
            ]
        }
        """
        result = ValidationResult(is_valid=False, total_records=0, valid_records=0, invalid_records=0)
        
        # Must be a dictionary with compatibility_rules
        if not isinstance(data, dict):
            result.add_error("Root element must be an object")
            return result
        
        if 'compatibility_rules' not in data:
            result.add_error("Missing 'compatibility_rules' key")
            return result
        
        rules = data['compatibility_rules']
        if not isinstance(rules, list):
            result.add_error("'compatibility_rules' must be an array")
            return result
        
        if len(rules) == 0:
            result.add_error("Compatibility rules list is empty")
            return result
        
        result.total_records = len(rules)
        
        # Validate each rule record
        seen_rule_ids = set()
        valid_count = 0
        
        for i, rule in enumerate(rules):
            record_id = f"rule_{i}"
            
            # Must be a dictionary
            if not isinstance(rule, dict):
                result.add_error("Rule must be an object", record_id)
                continue
            
            # Check required fields
            missing_fields = self.REQUIRED_FIELDS - set(rule.keys())
            if missing_fields:
                result.add_error(f"Missing required fields: {missing_fields}", record_id)
                continue
            
            # Validate rule ID
            rule_id = rule.get('rule_id', '').strip()
            if not rule_id:
                result.add_error("Empty rule_id", record_id)
                continue
            
            # Handle duplicates within file by generating unique IDs
            original_rule_id = rule_id
            counter = 1
            while rule_id in seen_rule_ids:
                rule_id = f"{original_rule_id}_{counter}"
                counter += 1
                result.add_warning(f"Duplicate rule_id found, renamed to: {rule_id}", record_id)
                result.duplicate_keys.add(original_rule_id)
            seen_rule_ids.add(rule_id)
            
            # Update rule with potentially new ID
            rule['rule_id'] = rule_id
            
            # Validate rule type
            rule_type = rule.get('rule_type', '').strip()
            if rule_type not in self.VALID_RULE_TYPES:
                result.add_error(f"Invalid rule_type: {rule_type}", record_id)
                continue
            
            # Validate GIN numbers
            source_gin = rule.get('source_gin', '').strip()
            target_gin = rule.get('target_gin', '').strip()
            
            if not source_gin or not target_gin:
                result.add_error("Missing source_gin or target_gin", record_id)
                continue
            
            if source_gin == target_gin:
                result.add_error("source_gin cannot equal target_gin", record_id)
                continue
            
            # Validate confidence score
            confidence = rule.get('confidence', 0.95)
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                result.add_warning(f"Invalid confidence score: {confidence}, using 0.95", record_id)
            
            valid_count += 1
        
        result.valid_records = valid_count
        result.invalid_records = result.total_records - valid_count
        result.is_valid = result.invalid_records == 0
        
        if result.is_valid:
            self.logger.info(f"Compatibility rules validation passed: {valid_count} valid rules")
        else:
            self.logger.warning(f"Compatibility rules validation issues: {result.invalid_records} invalid rules")
        
        return result
    
    def _validate_rule_record(self, rule_data: Dict, index: int, 
                            validate_references: bool) -> Tuple[CompatibilityRule, List[str]]:
        """
        Validate and normalize a single compatibility rule
        
        Returns:
            (compatibility_rule, errors)
        """
        errors = []
        
        # Extract and validate basic fields
        rule_id = str(rule_data.get('rule_id', '')).strip()
        if not rule_id:
            errors.append("Missing rule_id")
            return None, errors
        
        rule_type = str(rule_data.get('rule_type', '')).strip()
        if rule_type not in self.VALID_RULE_TYPES:
            errors.append(f"Invalid rule_type: {rule_type}")
            return None, errors
        
        source_gin = str(rule_data.get('source_gin', '')).strip()
        target_gin = str(rule_data.get('target_gin', '')).strip()
        
        if not source_gin or not target_gin:
            errors.append("Missing source_gin or target_gin")
            return None, errors
        
        if source_gin == target_gin:
            errors.append("source_gin cannot equal target_gin")
            return None, errors
        
        source_category = str(rule_data.get('source_category', '')).strip()
        target_category = str(rule_data.get('target_category', '')).strip()
        
        # Check product references if requested
        warnings = []
        skip_rule = False
        if validate_references:
            if source_gin not in self._product_catalog:
                warnings.append(f"Source product not found in catalog: {source_gin}")
                skip_rule = True
            
            if target_gin not in self._product_catalog:
                warnings.append(f"Target product not found in catalog: {target_gin}")
                skip_rule = True
        
        # If missing products, skip this rule but don't count as error
        if skip_rule:
            return None, []  # Empty errors = not an error, just skipped
            
        # Validate category consistency (treat as warnings, not errors)
        if validate_references:
            if source_gin in self._product_categories:
                actual_category = self._product_categories[source_gin]
                if source_category and actual_category != source_category:
                    warnings.append(f"Source category mismatch: rule says {source_category}, product is {actual_category}")
                    # Update rule to use actual category
                    source_category = actual_category
            
            if target_gin in self._product_categories:
                actual_category = self._product_categories[target_gin] 
                if target_category and actual_category != target_category:
                    warnings.append(f"Target category mismatch: rule says {target_category}, product is {actual_category}")
                    # Update rule to use actual category
                    target_category = actual_category
        
        # Validate confidence score
        confidence = rule_data.get('confidence', 0.95)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            errors.append(f"Invalid confidence score: {confidence}")
            confidence = 0.95  # Default fallback
        
        # Check for bidirectional flag
        bidirectional = bool(rule_data.get('bidirectional', False))
        
        # Extract metadata and serialize to JSON
        metadata = {}
        for key, value in rule_data.items():
            if key not in self.REQUIRED_FIELDS and key not in ['confidence', 'bidirectional']:
                metadata[key] = value
        
        # Serialize metadata to JSON string for Neo4j compatibility
        import json
        try:
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else ""
        except (TypeError, ValueError):
            metadata_json = ""
        
        if errors:
            return None, errors
        
        rule = CompatibilityRule(
            rule_id=rule_id,
            rule_type=rule_type,
            source_gin=source_gin,
            target_gin=target_gin,
            source_category=source_category,
            target_category=target_category,
            confidence=float(confidence),
            bidirectional=bidirectional,
            metadata=metadata_json
        )
        
        return rule, []
    
    def _process_data(self, data: Dict, validate_references: bool) -> ValidationResult:
        """
        Process and load compatibility rules into Neo4j
        
        Args:
            data: Dictionary containing compatibility rules
            validate_references: Whether to validate product references
            
        Returns:
            ValidationResult with loading statistics
        """
        rules_data = data.get('compatibility_rules', [])
        result = ValidationResult(
            is_valid=False,
            total_records=len(rules_data),
            valid_records=0,
            invalid_records=0
        )
        
        self.logger.info(f"Processing {len(rules_data)} compatibility rules")
        
        # Collect valid rules for batch processing
        rules_to_create = []
        rules_to_update = []
        
        for i, rule_data in enumerate(rules_data):
            # Validate and normalize rule
            rule, errors = self._validate_rule_record(rule_data, i, validate_references)
            
            if errors:
                result.invalid_records += 1
                for error in errors:
                    result.add_error(error, f"rule_{i}")
                
                # Track missing references
                for error in errors:
                    if "not found in catalog" in error:
                        gin = error.split(": ")[1] if ": " in error else ""
                        if gin:
                            result.missing_references.add(gin)
                continue
            
            # If rule is None (skipped due to missing products), don't count as error
            if rule is None:
                continue
            
            # Check if rule exists (update vs create)
            if rule.rule_id in self._existing_rules:
                rules_to_update.append(rule)
                self.logger.debug(f"Rule {rule.rule_id} will be updated")
            else:
                rules_to_create.append(rule)
                self.logger.debug(f"Rule {rule.rule_id} will be created")
            
            result.valid_records += 1
        
        # Process rules in batches
        if rules_to_create:
            self._create_rules_batch(rules_to_create)
        
        if rules_to_update:
            self._update_rules_batch(rules_to_update)
        
        # Create indexes for performance
        self.create_indexes()
        
        result.is_valid = result.invalid_records == 0
        
        self.logger.info(f"Compatibility rules loading completed:")
        self.logger.info(f"  Created: {len(rules_to_create)} rules")
        self.logger.info(f"  Updated: {len(rules_to_update)} rules")
        self.logger.info(f"  Missing product references: {len(result.missing_references)}")
        
        return result
    
    def _create_rules_batch(self, rules: List[CompatibilityRule]):
        """Create multiple compatibility rules in a single transaction"""
        if not rules:
            return
        
        # Group rules by type for optimized queries
        compatible_rules = [r for r in rules if r.rule_type == 'COMPATIBLE_WITH']
        determines_rules = [r for r in rules if r.rule_type == 'DETERMINES']
        other_rules = [r for r in rules if r.rule_type not in ['COMPATIBLE_WITH', 'DETERMINES']]
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            # Create COMPATIBLE_WITH relationships
            if compatible_rules:
                compatible_query = """
                UNWIND $rules AS rule
                MATCH (source:Product {gin: rule.source_gin})
                MATCH (target:Product {gin: rule.target_gin})
                CREATE (source)-[r:COMPATIBLE_WITH {
                    rule_id: rule.rule_id,
                    confidence: rule.confidence,
                    created_at: datetime(),
                    metadata_json: rule.metadata
                }]->(target)
                """
                
                rule_data = [{
                    'rule_id': r.rule_id,
                    'source_gin': r.source_gin,
                    'target_gin': r.target_gin,
                    'confidence': r.confidence,
                    'metadata': r.metadata
                } for r in compatible_rules]
                
                session.run(compatible_query, rules=rule_data)
                self.logger.info(f"Created {len(compatible_rules)} COMPATIBLE_WITH relationships")
                
                # Handle bidirectional relationships
                bidirectional_rules = [r for r in compatible_rules if r.bidirectional]
                if bidirectional_rules:
                    bidirectional_query = """
                    UNWIND $rules AS rule
                    MATCH (source:Product {gin: rule.source_gin})
                    MATCH (target:Product {gin: rule.target_gin})
                    CREATE (target)-[r:COMPATIBLE_WITH {
                        rule_id: rule.rule_id + '_reverse',
                        confidence: rule.confidence,
                        created_at: datetime(),
                        metadata_json: rule.metadata
                    }]->(source)
                    """
                    session.run(bidirectional_query, rules=rule_data)
                    self.logger.info(f"Created {len(bidirectional_rules)} bidirectional COMPATIBLE_WITH relationships")
            
            # Create DETERMINES relationships
            if determines_rules:
                determines_query = """
                UNWIND $rules AS rule
                MATCH (source:Product {gin: rule.source_gin})
                MATCH (target:Product {gin: rule.target_gin})
                CREATE (source)-[r:DETERMINES {
                    rule_id: rule.rule_id,
                    confidence: rule.confidence,
                    created_at: datetime(),
                    metadata: rule.metadata
                }]->(target)
                """
                
                rule_data = [{
                    'rule_id': r.rule_id,
                    'source_gin': r.source_gin,
                    'target_gin': r.target_gin,
                    'confidence': r.confidence,
                    'metadata': r.metadata
                } for r in determines_rules]
                
                session.run(determines_query, rules=rule_data)
                self.logger.info(f"Created {len(determines_rules)} DETERMINES relationships")
    
    def _update_rules_batch(self, rules: List[CompatibilityRule]):
        """Update existing compatibility rules"""
        if not rules:
            return
        
        # For now, we'll delete and recreate updated rules
        # This ensures consistency and handles rule type changes
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for rule in rules:
                # Delete existing rule
                delete_query = """
                MATCH ()-[r {rule_id: $rule_id}]-()
                DELETE r
                """
                session.run(delete_query, rule_id=rule.rule_id)
        
        # Recreate as new rules
        self._create_rules_batch(rules)
        self.logger.info(f"Updated {len(rules)} compatibility rules")
    
    def create_indexes(self):
        """Create performance indexes for compatibility queries"""
        indexes = [
            "CREATE INDEX compatible_rule_id_index IF NOT EXISTS FOR ()-[r:COMPATIBLE_WITH]-() ON (r.rule_id)",
            "CREATE INDEX determines_rule_id_index IF NOT EXISTS FOR ()-[r:DETERMINES]-() ON (r.rule_id)",
            "CREATE INDEX compatible_confidence_index IF NOT EXISTS FOR ()-[r:COMPATIBLE_WITH]-() ON (r.confidence)",
            "CREATE INDEX determines_confidence_index IF NOT EXISTS FOR ()-[r:DETERMINES]-() ON (r.confidence)"
        ]
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Created index: {index_query}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")
    
    def get_compatibility_statistics(self) -> Dict:
        """Get comprehensive compatibility statistics"""
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            stats_query = """
            MATCH (p:Product)
            OPTIONAL MATCH (p)-[c:COMPATIBLE_WITH]->()
            OPTIONAL MATCH (p)-[d:DETERMINES]->()
            RETURN 
                count(DISTINCT p) as total_products,
                count(c) as compatible_relationships,
                count(d) as determines_relationships,
                avg(c.confidence) as avg_compatible_confidence,
                avg(d.confidence) as avg_determines_confidence
            """
            
            result = session.run(stats_query)
            stats = result.single()
            
            return {
                'total_products': stats['total_products'],
                'compatible_relationships': stats['compatible_relationships'],
                'determines_relationships': stats['determines_relationships'],
                'avg_compatible_confidence': stats['avg_compatible_confidence'],
                'avg_determines_confidence': stats['avg_determines_confidence']
            }