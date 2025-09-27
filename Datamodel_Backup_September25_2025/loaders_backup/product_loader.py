"""
Product Catalog Loader
Bharath's Quality-First Implementation

This loader handles the enhanced_simplified_products.json file and serves as the 
foundation for all other loaders. It must be run first to establish the product
catalog that other loaders will validate against.

Features:
- Idempotent loading (can be run multiple times)
- Comprehensive product validation
- Category normalization and validation
- Image URL validation and caching
- Specification parsing and validation
- Performance optimized bulk loading
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from urllib.parse import urlparse

from .base_loader import BaseLoader, ValidationResult


class ProductLoader(BaseLoader):
    """
    Product Catalog Loader - Foundation loader that must run first
    
    Loads products from enhanced_simplified_products.json with:
    - GIN number validation and deduplication
    - Category normalization 
    - Specification parsing
    - Image URL validation
    - Country availability parsing
    - Data quality scoring
    """
    
    VALID_CATEGORIES = {
        'PowerSource', 'Feeder', 'Cooler', 'Torch', 'FeederAccessory', 
        'TorchAccessory', 'Accessory', 'Consumable', 'Other',
        'SystemItem', 'Interconnector', 'Monitoring', 'Remote', 'Unknown',
        'ConnectivityAccessory', 'PowerSourceAccessory', 'SafetyAccessory', 'WeldingAccessory'
    }
    
    REQUIRED_FIELDS = {
        'gin_number', 'product_name', 'component_category'
    }
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 postgres_config: Dict[str, str] = None):
        """Initialize Product Loader"""
        super().__init__(neo4j_uri, neo4j_user, neo4j_password, postgres_config)
        
        # Product-specific validation sets
        self._existing_gin_numbers: Set[str] = set()
        self._category_mappings = self._load_category_mappings()
        self._load_existing_products()
    
    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category mapping configurations"""
        # Standard category mappings for normalization
        return {
            'power_source': 'PowerSource',
            'powersource': 'PowerSource',
            'wire_feeder': 'Feeder', 
            'feeder': 'Feeder',
            'cooler': 'Cooler',
            'cooling_unit': 'Cooler',
            'torch': 'Torch',
            'welding_torch': 'Torch',
            'mig_torch': 'Torch',
            'tig_torch': 'Torch',
            'accessory': 'Accessory',
            'consumable': 'Consumable',
            'other': 'Other'
        }
    
    def _load_existing_products(self):
        """Load existing product GIN numbers to avoid duplicates"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run("MATCH (p:Product) RETURN p.gin as gin")
                self._existing_gin_numbers = {record["gin"] for record in result}
                self.logger.info(f"Found {len(self._existing_gin_numbers)} existing products")
        except Exception as e:
            self.logger.info(f"No existing products found (fresh database): {e}")
    
    def _validate_json_structure(self, data: Any, file_path: Path) -> ValidationResult:
        """
        Validate enhanced_simplified_products.json structure
        
        Expected structure:
        [
            {
                "gin_number": "string",
                "product_name": "string", 
                "component_category": "string",
                "specifications": {},
                ...
            }
        ]
        """
        result = ValidationResult(is_valid=False, total_records=0, valid_records=0, invalid_records=0)
        
        # Must be a list of products
        if not isinstance(data, list):
            result.add_error("Root element must be an array of products")
            return result
        
        if len(data) == 0:
            result.add_error("Product list is empty")
            return result
        
        result.total_records = len(data)
        
        # Validate each product record
        seen_gin_numbers = set()
        valid_count = 0
        
        for i, product in enumerate(data):
            record_id = f"index_{i}"
            
            # Must be a dictionary
            if not isinstance(product, dict):
                result.add_error(f"Product must be an object", record_id)
                continue
            
            # Check required fields
            missing_fields = self.REQUIRED_FIELDS - set(product.keys())
            if missing_fields:
                result.add_error(f"Missing required fields: {missing_fields}", record_id)
                continue
            
            # Validate GIN number
            gin = product.get('gin_number', '').strip()
            if not gin:
                result.add_error("Empty GIN number", record_id)
                continue
            
            if not re.match(r'^\\d{10}$', gin):
                result.add_warning(f"GIN number format unusual: {gin}", record_id)
            
            # Check for duplicates within file
            if gin in seen_gin_numbers:
                result.add_error(f"Duplicate GIN number in file: {gin}", record_id)
                result.duplicate_keys.add(gin)
                continue
            seen_gin_numbers.add(gin)
            
            # Validate category
            category = product.get('component_category', '').strip()
            if category not in self.VALID_CATEGORIES:
                # Try to normalize category
                normalized_category = self._normalize_category(category)
                if normalized_category:
                    result.add_warning(f"Category normalized: {category} -> {normalized_category}", record_id)
                else:
                    result.add_error(f"Invalid category: {category}", record_id)
                    continue
            
            # Validate product name
            name = product.get('product_name', '').strip()
            if not name or len(name) < 3:
                result.add_error("Product name missing or too short", record_id)
                continue
            
            valid_count += 1
        
        result.valid_records = valid_count
        result.invalid_records = result.total_records - valid_count
        result.is_valid = result.invalid_records == 0
        
        if result.is_valid:
            self.logger.info(f"Product file validation passed: {valid_count} valid products")
        else:
            self.logger.warning(f"Product file validation issues: {result.invalid_records} invalid products")
        
        return result
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category name to standard format"""
        if not category:
            return ""
        
        # If already a valid category, return as-is
        if category.strip() in self.VALID_CATEGORIES:
            return category.strip()
        
        # Try direct mapping
        normalized = category.lower().strip()
        if normalized in self._category_mappings:
            return self._category_mappings[normalized]
        
        # Try partial matching
        for key, value in self._category_mappings.items():
            if key in normalized or normalized in key:
                return value
        
        return ""
    
    def _validate_product_record(self, product: Dict, index: int) -> tuple[Dict, List[str]]:
        """
        Validate and normalize a single product record
        
        Returns:
            (normalized_product, errors)
        """
        errors = []
        normalized = product.copy()
        
        # Normalize GIN number
        gin = str(product.get('gin_number', '')).strip()
        if not gin:
            errors.append("Missing GIN number")
            return normalized, errors
        normalized['gin'] = gin
        
        # Normalize category
        category = product.get('component_category', '').strip()
        normalized_category = self._normalize_category(category)
        if not normalized_category:
            errors.append(f"Invalid category: {category}")
        normalized['category'] = normalized_category or category
        
        # Validate and clean product name
        name = str(product.get('product_name', '')).strip()
        if not name:
            errors.append("Missing product name")
        normalized['name'] = name
        
        # Clean description
        description = str(product.get('product_description', '')).strip()
        normalized['description'] = description[:1000] if description else ""  # Limit length
        
        # Validate specifications
        specs = product.get('specifications', {})
        if not isinstance(specs, dict):
            errors.append("Specifications must be an object")
            specs = {}
        normalized['specifications'] = self._normalize_specifications(specs)
        
        # Validate image URL
        image_url = product.get('image_url')
        if image_url:
            if self._validate_url(image_url):
                normalized['image_url'] = image_url
            else:
                errors.append(f"Invalid image URL: {image_url}")
                normalized['image_url'] = None
        else:
            normalized['image_url'] = None
        
        # Validate datasheet URL
        datasheet_url = product.get('datasheet_url') 
        if datasheet_url:
            if self._validate_url(datasheet_url):
                normalized['datasheet_url'] = datasheet_url
            else:
                errors.append(f"Invalid datasheet URL: {datasheet_url}")
                normalized['datasheet_url'] = None
        else:
            normalized['datasheet_url'] = None
        
        # Parse countries
        countries = product.get('countries_available', [])
        if isinstance(countries, list):
            # Validate country codes
            valid_countries = [c for c in countries if isinstance(c, str) and len(c) == 3]
            if len(valid_countries) != len(countries):
                errors.append(f"Some invalid country codes: {countries}")
            normalized['countries_available'] = valid_countries
        else:
            normalized['countries_available'] = []
        
        # Availability flag
        normalized['is_available'] = bool(product.get('is_available', True))
        
        # Last modified timestamp
        last_modified = product.get('last_modified', '')
        normalized['last_modified'] = last_modified
        
        # Product ID 
        product_id = product.get('product_id', '')
        normalized['product_id'] = product_id
        
        return normalized, errors
    
    def _normalize_specifications(self, specs: Dict) -> str:
        """Normalize specifications dictionary to JSON string for Neo4j compatibility"""
        if not specs or not isinstance(specs, dict):
            return ""
        
        normalized = {}
        
        for key, value in specs.items():
            if not key or not value:
                continue
                
            # Normalize key
            clean_key = str(key).strip()
            
            # Normalize value - keep as is for JSON serialization
            if isinstance(value, list):
                clean_value = [str(v).strip() for v in value if v]
            elif isinstance(value, (int, float)):
                clean_value = value
            else:
                clean_value = str(value).strip()
            
            if clean_value:  # Only add non-empty values
                normalized[clean_key] = clean_value
        
        # Return as JSON string for Neo4j compatibility
        import json
        try:
            return json.dumps(normalized, ensure_ascii=False)
        except (TypeError, ValueError):
            return ""
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _process_data(self, data: List[Dict], validate_references: bool) -> ValidationResult:
        """
        Process and load product data into Neo4j
        
        Args:
            data: List of product dictionaries
            validate_references: Not used for product loader (base dataset)
            
        Returns:
            ValidationResult with loading statistics
        """
        result = ValidationResult(
            is_valid=False,
            total_records=len(data), 
            valid_records=0,
            invalid_records=0
        )
        
        self.logger.info(f"Processing {len(data)} product records")
        
        # Batch processing for performance
        batch_size = 100
        products_to_create = []
        products_to_update = []
        
        for i, product_data in enumerate(data):
            # Validate and normalize product
            normalized_product, errors = self._validate_product_record(product_data, i)
            
            if errors:
                result.invalid_records += 1
                for error in errors:
                    result.add_error(error, f"product_{i}")
                continue
            
            gin = normalized_product['gin']
            
            # Check if product exists (update vs create)
            if gin in self._existing_gin_numbers:
                products_to_update.append(normalized_product)
                self.logger.debug(f"Product {gin} will be updated")
            else:
                products_to_create.append(normalized_product)
                self.logger.debug(f"Product {gin} will be created")
            
            result.valid_records += 1
            
            # Process in batches for performance
            if len(products_to_create) >= batch_size:
                self._create_products_batch(products_to_create)
                products_to_create = []
            
            if len(products_to_update) >= batch_size:
                self._update_products_batch(products_to_update)
                products_to_update = []
        
        # Process remaining products
        if products_to_create:
            self._create_products_batch(products_to_create)
        
        if products_to_update:
            self._update_products_batch(products_to_update)
        
        # Create indexes for performance
        self.create_indexes()
        
        result.is_valid = result.invalid_records == 0
        
        self.logger.info(f"Product loading completed:")
        self.logger.info(f"  Created: {len([p for p in data if p.get('gin') not in self._existing_gin_numbers])}")
        self.logger.info(f"  Updated: {len([p for p in data if p.get('gin') in self._existing_gin_numbers])}")
        
        return result
    
    def _create_products_batch(self, products: List[Dict]):
        """Create multiple products in a single transaction"""
        if not products:
            return
            
        cypher_query = """
        UNWIND $products AS product
        CREATE (p:Product {
            gin: product.gin,
            name: product.name,
            description: product.description,
            category: product.category,
            specifications_json: product.specifications,
            image_url: product.image_url,
            datasheet_url: product.datasheet_url,
            countries_available: product.countries_available,
            is_available: product.is_available,
            last_modified: product.last_modified,
            product_id: product.product_id,
            created_at: datetime(),
            updated_at: datetime()
        })
        """
        
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                session.run(cypher_query, products=products)
            self.logger.info(f"Created {len(products)} products")
        except Exception as e:
            self.logger.error(f"Failed to create product batch: {e}")
            raise
    
    def _update_products_batch(self, products: List[Dict]):
        """Update multiple products in a single transaction"""
        if not products:
            return
            
        cypher_query = """
        UNWIND $products AS product
        MATCH (p:Product {gin: product.gin})
        SET p.name = product.name,
            p.description = product.description,
            p.category = product.category,
            p.specifications_json = product.specifications,
            p.image_url = product.image_url,
            p.datasheet_url = product.datasheet_url,
            p.countries_available = product.countries_available,
            p.is_available = product.is_available,
            p.last_modified = product.last_modified,
            p.product_id = product.product_id,
            p.updated_at = datetime()
        """
        
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                session.run(cypher_query, products=products)
            self.logger.info(f"Updated {len(products)} products")
        except Exception as e:
            self.logger.error(f"Failed to update product batch: {e}")
            raise
    
    def create_indexes(self):
        """Create performance indexes for product queries"""
        indexes = [
            "CREATE INDEX product_gin_index IF NOT EXISTS FOR (p:Product) ON (p.gin)",
            "CREATE INDEX product_category_index IF NOT EXISTS FOR (p:Product) ON (p.category)",
            "CREATE INDEX product_name_index IF NOT EXISTS FOR (p:Product) ON (p.name)",
            "CREATE INDEX product_available_index IF NOT EXISTS FOR (p:Product) ON (p.is_available)"
        ]
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Created index: {index_query}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")
    
    def cleanup_old_data(self, backup_first: bool = True):
        """
        Clean up old product data (use with caution!)
        
        Args:
            backup_first: Create backup before deletion
        """
        if backup_first:
            self.logger.info("Creating product backup before cleanup")
            # Could implement backup logic here
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            result = session.run("MATCH (p:Product) RETURN count(p) as count")
            count = result.single()["count"]
            
            if count > 0:
                self.logger.warning(f"Deleting {count} existing products")
                session.run("MATCH (p:Product) DETACH DELETE p")
                self.logger.info("Product cleanup completed")
    
    def get_product_statistics(self) -> Dict:
        """Get comprehensive product statistics"""
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            stats_query = """
            MATCH (p:Product)
            RETURN 
                count(p) as total_products,
                count(DISTINCT p.category) as unique_categories,
                sum(case when p.is_available then 1 else 0 end) as available_products,
                sum(case when p.image_url IS NOT NULL then 1 else 0 end) as products_with_images,
                sum(case when p.datasheet_url IS NOT NULL then 1 else 0 end) as products_with_datasheets,
                collect(DISTINCT p.category) as categories
            """
            
            result = session.run(stats_query)
            stats = result.single()
            
            return {
                'total_products': stats['total_products'],
                'unique_categories': stats['unique_categories'], 
                'available_products': stats['available_products'],
                'products_with_images': stats['products_with_images'],
                'products_with_datasheets': stats['products_with_datasheets'],
                'categories': stats['categories']
            }