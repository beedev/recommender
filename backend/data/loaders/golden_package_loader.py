"""
Golden Package Loader
Bharath's Quality-First Implementation

This loader handles golden_packages.json and creates validated equipment
packages with all component references validated against the product catalog.

Features:
- Product reference validation (flags missing products)
- Package completeness validation
- Component role validation (PowerSource, Feeder, Cooler, etc.)
- Price calculation and validation
- Performance optimized loading
- Package recommendation scoring
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from decimal import Decimal

from .base_loader import BaseLoader, ValidationResult


@dataclass
class PackageComponent:
    """Individual component in a golden package"""
    gin: str
    name: str
    role: str  # 'powersource', 'feeder', 'cooler', 'torch', 'accessory'
    quantity: int = 1
    unit_price: float = 0.0


@dataclass
class GoldenPackage:
    """Complete validated golden package"""
    package_id: str
    powersource_gin: str
    powersource_name: str
    components: List[PackageComponent]
    total_price: float
    package_name: str = ""
    description: str = ""
    use_case: str = ""
    confidence_score: float = 1.0
    metadata: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = ""


class GoldenPackageLoader(BaseLoader):
    """
    Golden Package Loader
    
    Loads validated equipment packages from golden_packages.json with:
    - Product reference validation (all components must exist)
    - Package completeness validation (must have PowerSource + essential components)
    - Component role validation
    - Price calculation and validation
    - Package scoring based on component compatibility
    """
    
    REQUIRED_PACKAGE_FIELDS = {
        'package_id', 'powersource_gin', 'powersource_name', 'components'
    }
    
    REQUIRED_COMPONENT_ROLES = {'powersource'}  # PowerSource is mandatory
    OPTIONAL_COMPONENT_ROLES = {'feeder', 'cooler', 'torch', 'accessory'}
    ALL_COMPONENT_ROLES = REQUIRED_COMPONENT_ROLES | OPTIONAL_COMPONENT_ROLES
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 postgres_config: Dict[str, str] = None):
        """Initialize Golden Package Loader"""
        super().__init__(neo4j_uri, neo4j_user, neo4j_password, postgres_config)
        
        # Package-specific tracking
        self._existing_packages: Set[str] = set()
        self._product_prices: Dict[str, float] = {}
        self._load_existing_packages()
        self._load_product_prices()
    
    def _load_existing_packages(self):
        """Load existing package IDs to avoid duplicates"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run("MATCH (gp:GoldenPackage) RETURN gp.package_id as package_id")
                self._existing_packages = {record["package_id"] for record in result}
                self.logger.info(f"Found {len(self._existing_packages)} existing golden packages")
        except Exception as e:
            self.logger.info(f"No existing packages found (fresh database): {e}")
    
    def _load_product_prices(self):
        """Load product prices for package cost calculation"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run("""
                    MATCH (p:Product) 
                    WHERE p.specifications.price IS NOT NULL
                    RETURN p.gin as gin, p.specifications.price as price
                """)
                for record in result:
                    try:
                        price = float(record["price"])
                        self._product_prices[record["gin"]] = price
                    except (ValueError, TypeError):
                        continue
                
                self.logger.info(f"Loaded {len(self._product_prices)} product prices")
        except Exception as e:
            self.logger.warning(f"Could not load product prices: {e}")
    
    def _validate_json_structure(self, data: Any, file_path: Path) -> ValidationResult:
        """
        Validate golden_packages.json structure
        
        Expected structure:
        {
            "metadata": {...},
            "golden_packages": [
                {
                    "package_id": int,
                    "powersource_gin": "string",
                    "powersource_name": "string",
                    "components": {
                        "feeder": {...},
                        "cooler": {...},
                        ...
                    },
                    ...
                }
            ]
        }
        """
        result = ValidationResult(is_valid=False, total_records=0, valid_records=0, invalid_records=0)
        
        # Must be a dictionary with golden_packages
        if not isinstance(data, dict):
            result.add_error("Root element must be an object")
            return result
        
        if 'golden_packages' not in data:
            result.add_error("Missing 'golden_packages' key")
            return result
        
        packages = data['golden_packages']
        if not isinstance(packages, list):
            result.add_error("'golden_packages' must be an array")
            return result
        
        if len(packages) == 0:
            result.add_error("Golden packages list is empty")
            return result
        
        result.total_records = len(packages)
        
        # Validate each package record
        seen_package_ids = set()
        valid_count = 0
        
        for i, package in enumerate(packages):
            record_id = f"package_{i}"
            
            # Must be a dictionary
            if not isinstance(package, dict):
                result.add_error("Package must be an object", record_id)
                continue
            
            # Check required fields
            missing_fields = self.REQUIRED_PACKAGE_FIELDS - set(package.keys())
            if missing_fields:
                result.add_error(f"Missing required fields: {missing_fields}", record_id)
                continue
            
            # Validate package ID
            package_id = package.get('package_id')
            if package_id is None:
                result.add_error("Missing package_id", record_id)
                continue
            
            package_id_str = str(package_id)
            
            # Check for duplicates within file
            if package_id_str in seen_package_ids:
                result.add_error(f"Duplicate package_id in file: {package_id_str}", record_id)
                result.duplicate_keys.add(package_id_str)
                continue
            seen_package_ids.add(package_id_str)
            
            # Validate PowerSource GIN
            powersource_gin = str(package.get('powersource_gin', '')).strip()
            if not powersource_gin:
                result.add_error("Missing powersource_gin", record_id)
                continue
            
            # Validate components structure
            components = package.get('components')
            if not isinstance(components, dict):
                result.add_error("Components must be an object", record_id)
                continue
            
            if len(components) == 0:
                result.add_error("Package has no components", record_id)
                continue
            
            # Validate component structure
            component_errors = []
            for role, component_data in components.items():
                if not isinstance(component_data, dict):
                    component_errors.append(f"Component {role} must be an object")
                    continue
                
                if 'gin' not in component_data or 'name' not in component_data:
                    component_errors.append(f"Component {role} missing gin or name")
            
            if component_errors:
                for error in component_errors:
                    result.add_error(error, record_id)
                continue
            
            valid_count += 1
        
        result.valid_records = valid_count
        result.invalid_records = result.total_records - valid_count
        result.is_valid = result.invalid_records == 0
        
        if result.is_valid:
            self.logger.info(f"Golden packages validation passed: {valid_count} valid packages")
        else:
            self.logger.warning(f"Golden packages validation issues: {result.invalid_records} invalid packages")
        
        return result
    
    def _validate_package_record(self, package_data: Dict, index: int,
                                validate_references: bool) -> Tuple[GoldenPackage, List[str]]:
        """
        Validate and normalize a single golden package
        
        Returns:
            (golden_package, errors)
        """
        errors = []
        
        # Extract and validate basic fields
        package_id = str(package_data.get('package_id', ''))
        if not package_id:
            errors.append("Missing package_id")
            return None, errors
        
        powersource_gin = str(package_data.get('powersource_gin', '')).strip()
        powersource_name = str(package_data.get('powersource_name', '')).strip()
        
        if not powersource_gin or not powersource_name:
            errors.append("Missing powersource_gin or powersource_name")
            return None, errors
        
        # Validate PowerSource reference - skip package if powersource missing
        if validate_references and powersource_gin not in self._product_catalog:
            # Skip this package but don't treat as error
            return None, []
        
        # Parse and validate components
        components_data = package_data.get('components', {})
        if not isinstance(components_data, dict):
            errors.append("Components must be an object")
            return None, errors
        
        components = []
        component_errors = []
        total_price = 0.0
        
        # Add PowerSource as first component
        powersource_price = self._product_prices.get(powersource_gin, 0.0)
        powersource_component = PackageComponent(
            gin=powersource_gin,
            name=powersource_name,
            role='powersource',
            quantity=1,
            unit_price=powersource_price
        )
        components.append(powersource_component)
        total_price += powersource_price
        
        # Process other components
        for role, component_data in components_data.items():
            if role == 'powersource':
                continue  # Already handled above
            
            if not isinstance(component_data, dict):
                component_errors.append(f"Component {role} must be an object")
                continue
            
            gin = str(component_data.get('gin', '')).strip()
            name = str(component_data.get('name', '')).strip()
            
            if not gin or not name:
                component_errors.append(f"Component {role} missing gin or name")
                continue
            
            # Validate component reference - skip missing components but don't treat as error
            if validate_references and gin not in self._product_catalog:
                # Just skip this component, don't add to component_errors
                continue
            
            # Parse quantity and price
            quantity = int(component_data.get('quantity', 1))
            unit_price = self._product_prices.get(gin, 0.0)
            
            # Override with provided price if available
            if 'price' in component_data:
                try:
                    unit_price = float(component_data['price'])
                except (ValueError, TypeError):
                    component_errors.append(f"Invalid price for component {role}: {component_data['price']}")
            
            component = PackageComponent(
                gin=gin,
                name=name,
                role=role.lower(),
                quantity=quantity,
                unit_price=unit_price
            )
            components.append(component)
            total_price += unit_price * quantity
        
        if component_errors:
            errors.extend(component_errors)
            return None, errors
        
        # Validate package completeness (must have PowerSource + at least one other component)
        if len(components) < 2:
            errors.append("Package must have PowerSource + at least one additional component")
            return None, errors
        
        # Extract optional fields
        package_name = str(package_data.get('package_name', '')).strip()
        description = str(package_data.get('description', '')).strip()
        use_case = str(package_data.get('use_case', '')).strip()
        
        # Calculate confidence score based on component count and price availability
        base_confidence = 1.0
        price_availability = sum(1 for c in components if c.unit_price > 0) / len(components)
        component_completeness = min(len(components) / 5.0, 1.0)  # Ideal package has 5 components
        confidence_score = base_confidence * 0.5 + price_availability * 0.3 + component_completeness * 0.2
        
        # Extract metadata and serialize to JSON
        metadata = {}
        excluded_keys = self.REQUIRED_PACKAGE_FIELDS | {'package_name', 'description', 'use_case', 'components'}
        for key, value in package_data.items():
            if key not in excluded_keys:
                metadata[key] = value
        
        # Serialize metadata to JSON string for Neo4j compatibility
        import json
        try:
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else ""
        except (TypeError, ValueError):
            metadata_json = ""
        
        if errors:
            return None, errors
        
        golden_package = GoldenPackage(
            package_id=package_id,
            powersource_gin=powersource_gin,
            powersource_name=powersource_name,
            components=components,
            total_price=round(total_price, 2),
            package_name=package_name,
            description=description,
            use_case=use_case,
            confidence_score=round(confidence_score, 3),
            metadata=metadata_json
        )
        
        return golden_package, []
    
    def _process_data(self, data: Dict, validate_references: bool) -> ValidationResult:
        """
        Process and load golden packages into Neo4j
        
        Args:
            data: Dictionary containing golden packages
            validate_references: Whether to validate product references
            
        Returns:
            ValidationResult with loading statistics
        """
        packages_data = data.get('golden_packages', [])
        result = ValidationResult(
            is_valid=False,
            total_records=len(packages_data),
            valid_records=0,
            invalid_records=0
        )
        
        self.logger.info(f"Processing {len(packages_data)} golden packages")
        
        # Collect valid packages for batch processing
        packages_to_create = []
        packages_to_update = []
        
        for i, package_data in enumerate(packages_data):
            # Validate and normalize package
            package, errors = self._validate_package_record(package_data, i, validate_references)
            
            if errors:
                result.invalid_records += 1
                for error in errors:
                    result.add_error(error, f"package_{i}")
                
                # Track missing references
                for error in errors:
                    if "not found in catalog" in error:
                        gin = error.split(": ")[1].split(" ")[0] if ": " in error else ""
                        if gin:
                            result.missing_references.add(gin)
                continue
            
            # If package is None (skipped due to missing products), don't count as error
            if package is None:
                continue
            
            # Check if package exists (update vs create)
            if package.package_id in self._existing_packages:
                packages_to_update.append(package)
                self.logger.debug(f"Package {package.package_id} will be updated")
            else:
                packages_to_create.append(package)
                self.logger.debug(f"Package {package.package_id} will be created")
            
            result.valid_records += 1
        
        # Process packages in batches
        if packages_to_create:
            self._create_packages_batch(packages_to_create)
        
        if packages_to_update:
            self._update_packages_batch(packages_to_update)
        
        # Create indexes for performance
        self.create_indexes()
        
        result.is_valid = result.invalid_records == 0
        
        self.logger.info(f"Golden packages loading completed:")
        self.logger.info(f"  Created: {len(packages_to_create)} packages")
        self.logger.info(f"  Updated: {len(packages_to_update)} packages")
        self.logger.info(f"  Missing product references: {len(result.missing_references)}")
        
        return result
    
    def _create_packages_batch(self, packages: List[GoldenPackage]):
        """Create multiple golden packages in a single transaction"""
        if not packages:
            return
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for package in packages:
                # Create the golden package node
                create_package_query = """
                CREATE (gp:GoldenPackage {
                    package_id: $package_id,
                    powersource_gin: $powersource_gin,
                    powersource_name: $powersource_name,
                    total_price: $total_price,
                    package_name: $package_name,
                    description: $description,
                    use_case: $use_case,
                    confidence_score: $confidence_score,
                    created_at: datetime(),
                    metadata_json: $metadata
                })
                """
                
                session.run(create_package_query,
                    package_id=package.package_id,
                    powersource_gin=package.powersource_gin,
                    powersource_name=package.powersource_name,
                    total_price=package.total_price,
                    package_name=package.package_name,
                    description=package.description,
                    use_case=package.use_case,
                    confidence_score=package.confidence_score,
                    metadata=package.metadata
                )
                
                # Create relationships to component products
                for component in package.components:
                    create_component_query = """
                    MATCH (gp:GoldenPackage {package_id: $package_id})
                    MATCH (p:Product {gin: $component_gin})
                    CREATE (gp)-[r:CONTAINS {
                        role: $role,
                        quantity: $quantity,
                        unit_price: $unit_price,
                        total_price: $total_price
                    }]->(p)
                    """
                    
                    session.run(create_component_query,
                        package_id=package.package_id,
                        component_gin=component.gin,
                        role=component.role,
                        quantity=component.quantity,
                        unit_price=component.unit_price,
                        total_price=component.unit_price * component.quantity
                    )
                
                self.logger.debug(f"Created golden package {package.package_id} with {len(package.components)} components")
        
        self.logger.info(f"Created {len(packages)} golden packages")
    
    def _update_packages_batch(self, packages: List[GoldenPackage]):
        """Update existing golden packages"""
        if not packages:
            return
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for package in packages:
                # Update package properties
                update_package_query = """
                MATCH (gp:GoldenPackage {package_id: $package_id})
                SET gp.powersource_gin = $powersource_gin,
                    gp.powersource_name = $powersource_name,
                    gp.total_price = $total_price,
                    gp.package_name = $package_name,
                    gp.description = $description,
                    gp.use_case = $use_case,
                    gp.confidence_score = $confidence_score,
                    gp.updated_at = datetime(),
                    gp.metadata_json = $metadata
                """
                
                session.run(update_package_query,
                    package_id=package.package_id,
                    powersource_gin=package.powersource_gin,
                    powersource_name=package.powersource_name,
                    total_price=package.total_price,
                    package_name=package.package_name,
                    description=package.description,
                    use_case=package.use_case,
                    confidence_score=package.confidence_score,
                    metadata=package.metadata
                )
                
                # Delete existing component relationships
                session.run("""
                    MATCH (gp:GoldenPackage {package_id: $package_id})-[r:CONTAINS]->()
                    DELETE r
                """, package_id=package.package_id)
                
                # Recreate component relationships
                for component in package.components:
                    create_component_query = """
                    MATCH (gp:GoldenPackage {package_id: $package_id})
                    MATCH (p:Product {gin: $component_gin})
                    CREATE (gp)-[r:CONTAINS {
                        role: $role,
                        quantity: $quantity,
                        unit_price: $unit_price,
                        total_price: $total_price
                    }]->(p)
                    """
                    
                    session.run(create_component_query,
                        package_id=package.package_id,
                        component_gin=component.gin,
                        role=component.role,
                        quantity=component.quantity,
                        unit_price=component.unit_price,
                        total_price=component.unit_price * component.quantity
                    )
        
        self.logger.info(f"Updated {len(packages)} golden packages")
    
    def create_indexes(self):
        """Create performance indexes for golden package queries"""
        indexes = [
            "CREATE INDEX golden_package_id_index IF NOT EXISTS FOR (gp:GoldenPackage) ON (gp.package_id)",
            "CREATE INDEX golden_package_powersource_index IF NOT EXISTS FOR (gp:GoldenPackage) ON (gp.powersource_gin)",
            "CREATE INDEX golden_package_confidence_index IF NOT EXISTS FOR (gp:GoldenPackage) ON (gp.confidence_score)",
            "CREATE INDEX contains_role_index IF NOT EXISTS FOR ()-[r:CONTAINS]-() ON (r.role)"
        ]
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Created index: {index_query}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")
    
    def get_golden_package_statistics(self) -> Dict:
        """Get comprehensive golden package statistics"""
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            stats_query = """
            MATCH (gp:GoldenPackage)
            OPTIONAL MATCH (gp)-[c:CONTAINS]->(p:Product)
            RETURN 
                count(DISTINCT gp) as total_packages,
                count(c) as total_components,
                avg(gp.total_price) as avg_package_price,
                max(gp.total_price) as max_package_price,
                min(gp.total_price) as min_package_price,
                avg(gp.confidence_score) as avg_confidence_score,
                collect(DISTINCT gp.powersource_gin) as unique_powersources
            """
            
            result = session.run(stats_query)
            stats = result.single()
            
            # Get component role distribution
            roles_query = """
            MATCH ()-[c:CONTAINS]->()
            RETURN c.role as role, count(c) as count
            ORDER BY count DESC
            """
            
            roles_result = session.run(roles_query)
            role_distribution = {record['role']: record['count'] for record in roles_result}
            
            return {
                'total_packages': stats['total_packages'],
                'total_components': stats['total_components'],
                'avg_package_price': round(stats['avg_package_price'] or 0, 2),
                'max_package_price': stats['max_package_price'],
                'min_package_price': stats['min_package_price'],
                'avg_confidence_score': round(stats['avg_confidence_score'] or 0, 3),
                'unique_powersources': len(stats['unique_powersources'] or []),
                'component_role_distribution': role_distribution
            }