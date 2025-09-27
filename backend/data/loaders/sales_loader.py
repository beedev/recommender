"""
Sales Data Loader  
Bharath's Quality-First Implementation

This loader handles sales_data.json and creates comprehensive sales data model:
1. Clean Order-based architecture with proper Trinity nodes
2. Multi-PowerSource order splitting with compatibility checking
3. Trinity semantic search with combined descriptions
4. CO_OCCURS relationships for recommendation performance

Creates the following Neo4j structure:
- Customer nodes: aggregated customer data with facilities, categories
- Order nodes: header nodes for grouped line items
- Transaction nodes: individual line items within orders
- Trinity nodes: PowerSource+Feeder+Cooler combinations with semantic descriptions
- Relationships: (Customer)-[:PLACED]->(Order)-[:CONTAINS]->(Product)
- Relationships: (Order)-[:PART_OF]->(Transaction)-[:LINE_ITEM]->(Product)
- Relationships: (Order)-[:FORMS_TRINITY]->(Trinity)-[:COMPRISES {component_type}]->(Product)

Features:
- Clean Order-based architecture with Trinity nodes
- Multi-PowerSource order splitting with compatibility logic
- Trinity semantic search with combined component descriptions
- Product reference validation (skips invalid GINs)
- Order-based co-occurrence calculation
- Customer aggregation and profiling foundation
- Performance optimized batch loading
- Comprehensive indexing for fast queries
- DETERMINES relationship compatibility checking
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import uuid

from .base_loader import BaseLoader, ValidationResult


@dataclass
class SalesRecord:
    """Structured sales record with validation"""
    order_id: str
    line_no: str
    gin: str
    description: str = ""
    customer: str = ""
    facility: str = ""
    warehouse: str = ""
    category: str = ""
    
    def __post_init__(self):
        # Normalize fields
        self.gin_number = self.gin  # For compatibility with existing logic


@dataclass
class CoOccurrence:
    """Product co-occurrence relationship"""
    product1_gin: str
    product2_gin: str
    frequency: int
    last_occurrence_date: date
    orders: List[str]
    confidence_score: float = 0.0


@dataclass
class OrderData:
    """Order header with line items"""
    original_order_id: str
    order_id: str  # May have suffix for split orders
    customer: str
    facility: str
    warehouse: str
    line_items: List[SalesRecord]
    powersources: List[str] = None  # GINs of PowerSources in this order
    
    def __post_init__(self):
        # Extract PowerSources from line items if not provided
        if self.powersources is None:
            self.powersources = [item.gin for item in self.line_items 
                               if getattr(item, 'category', '') == 'PowerSource']


@dataclass 
class TrinityData:
    """Trinity combination with semantic description"""
    trinity_id: str
    powersource_gin: str
    feeder_gin: str
    cooler_gin: str
    powersource_name: str
    feeder_name: str
    cooler_name: str
    combined_description: str
    orders: List[str]  # Orders that contain this Trinity
    
    def __post_init__(self):
        # Generate combined semantic description
        if not self.combined_description:
            self.combined_description = (
                f"Complete welding system: {self.powersource_name} power source "
                f"with {self.feeder_name} feeder and {self.cooler_name} cooler. "
                f"Optimized for professional welding applications requiring "
                f"power source, wire feeding, and cooling capabilities."
            )


class SalesLoader(BaseLoader):
    """
    Sales Data Loader - Comprehensive Sales Intelligence
    
    Loads sales data from sales_data.json and creates:
    
    1. **Customer Nodes**: Aggregated customer intelligence
       - Name, primary facility, all facilities/warehouses
       - Transaction count, product categories purchased
       - Foundation for future customer profile extension
    
    2. **Transaction Nodes**: Detailed sales records
       - Order ID, line number, product details
       - Customer, facility, warehouse, category
       - Individual transaction-level granularity
    
    3. **CO_OCCURS Relationships**: Product co-occurrence patterns
       - Frequency, confidence, order counts
       - Optimized for fast recommendation queries
    
    4. **Relationship Graph**:
       (Customer)-[:MADE]->(Transaction)-[:CONTAINS]->(Product)
       (Product)-[:CO_OCCURS]->(Product)
    
    Features:
    - Product reference validation (skips invalid products per requirement)
    - Batch processing for performance optimization
    - Comprehensive indexing for query speed
    - Extensible foundation for customer profiles and analytics
    - Dual-purpose: Fast recommendations + detailed customer intelligence
    """
    
    REQUIRED_FIELDS = {
        'order_id', 'line_no', 'gin'
    }
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 postgres_config: Dict[str, str] = None):
        """Initialize Sales Loader"""
        super().__init__(neo4j_uri, neo4j_user, neo4j_password, postgres_config)
        
        # Sales-specific tracking
        self._valid_orders: Dict[str, List[SalesRecord]] = defaultdict(list)
        self._split_orders: List[OrderData] = []
        self._trinity_combinations: List[TrinityData] = []
        self._invalid_gin_count = 0
        self._skipped_records = 0
    
    def _validate_json_structure(self, data: Any, file_path: Path) -> ValidationResult:
        """
        Validate sales_data.json structure
        
        Expected structure:
        {
            "metadata": {...},
            "sales_records": [
                {
                    "order_id": "string",
                    "line_no": "string", 
                    "gin_number": "string",
                    "quantity": int,
                    "unit_price": float,
                    "order_date": "string",
                    ...
                }
            ]
        }
        """
        result = ValidationResult(is_valid=False, total_records=0, valid_records=0, invalid_records=0)
        
        # Must be a dictionary with sales_records
        if not isinstance(data, dict):
            result.add_error("Root element must be an object")
            return result
        
        if 'sales_records' not in data:
            result.add_error("Missing 'sales_records' key")
            return result
        
        records = data['sales_records']
        if not isinstance(records, list):
            result.add_error("'sales_records' must be an array")
            return result
        
        if len(records) == 0:
            result.add_error("Sales records list is empty")
            return result
        
        result.total_records = len(records)
        
        # Validate each sales record
        valid_count = 0
        
        for i, record in enumerate(records):
            record_id = f"record_{i}"
            
            # Must be a dictionary
            if not isinstance(record, dict):
                result.add_error("Record must be an object", record_id)
                continue
            
            # Check required fields
            missing_fields = self.REQUIRED_FIELDS - set(record.keys())
            if missing_fields:
                result.add_error(f"Missing required fields: {missing_fields}", record_id)
                continue
            
            # Validate order_id and line_no
            order_id = str(record.get('order_id', '')).strip()
            line_no = str(record.get('line_no', '')).strip()
            
            if not order_id or not line_no:
                result.add_error("Missing order_id or line_no", record_id)
                continue
            
            # Validate GIN number
            gin = str(record.get('gin', '')).strip()
            if not gin:
                result.add_error("Missing gin", record_id)
                continue
            
            valid_count += 1
        
        result.valid_records = valid_count
        result.invalid_records = result.total_records - valid_count
        result.is_valid = result.invalid_records == 0
        
        if result.is_valid:
            self.logger.info(f"Sales data validation passed: {valid_count} valid records")
        else:
            self.logger.warning(f"Sales data validation issues: {result.invalid_records} invalid records")
        
        return result
    
    def _validate_sales_record(self, record_data: Dict, index: int,
                             validate_references: bool) -> Tuple[SalesRecord, List[str]]:
        """
        Validate and normalize a single sales record
        
        Returns:
            (sales_record, errors)
        """
        errors = []
        
        # Extract and validate basic fields
        order_id = str(record_data.get('order_id', '')).strip()
        line_no = str(record_data.get('line_no', '')).strip()
        gin = str(record_data.get('gin', '')).strip()
        
        if not order_id or not line_no or not gin:
            errors.append("Missing order_id, line_no, or gin")
            return None, errors
        
        # Validate product reference if requested - skip missing products but don't error
        if validate_references and gin not in self._product_catalog:
            # Skip this record but don't treat as error
            return None, []
        
        # Extract other available fields
        description = str(record_data.get('description', '')).strip()
        customer = str(record_data.get('customer', '')).strip()
        facility = str(record_data.get('facility', '')).strip()
        warehouse = str(record_data.get('warehouse', '')).strip()
        category = str(record_data.get('category', '')).strip()
        
        if errors:
            return None, errors
        
        # Create the sales record with available fields
        sales_record = SalesRecord(
            order_id=order_id,
            line_no=line_no,
            gin=gin,
            description=description,
            customer=customer,
            facility=facility,
            warehouse=warehouse,
            category=category
        )
        
        return sales_record, []
    
    def _process_data(self, data: Dict, validate_references: bool) -> ValidationResult:
        """
        Process and load sales data with new clean architecture:
        1. Group transactions into Order headers
        2. Split multi-PowerSource orders with compatibility checking
        3. Create Trinity nodes with semantic descriptions
        4. Create CO_OCCURS relationships
        
        Args:
            data: Dictionary containing sales records
            validate_references: Whether to validate product references (skip invalid)
            
        Returns:
            ValidationResult with loading statistics
        """
        records_data = data.get('sales_records', [])
        result = ValidationResult(
            is_valid=False,
            total_records=len(records_data),
            valid_records=0,
            invalid_records=0
        )
        
        self.logger.info(f"Processing {len(records_data)} sales records with new clean architecture")
        
        # Step 1: Validate and group records by original order
        valid_orders = defaultdict(list)
        
        for i, record_data in enumerate(records_data):
            # Validate and normalize record
            record, errors = self._validate_sales_record(record_data, i, validate_references)
            
            if errors:
                # Check if error is due to missing product reference
                if validate_references and any("not found in catalog" in error for error in errors):
                    # Skip this record as requested for missing product references
                    result.add_warning(f"Skipping record due to missing product: {errors[0]}", f"record_{i}")
                    self._skipped_records += 1
                    gin = record_data.get('gin_number', 'unknown')
                    if gin != 'unknown':
                        result.missing_references.add(gin)
                    continue
                else:
                    # Other validation errors count as invalid
                    result.invalid_records += 1
                    for error in errors:
                        result.add_error(error, f"record_{i}")
                    continue
            
            # Group valid records by order
            valid_orders[record.order_id].append(record)
            result.valid_records += 1
        
        self.logger.info(f"Grouped {result.valid_records} valid records into {len(valid_orders)} original orders")
        self.logger.info(f"Skipped {self._skipped_records} records due to missing product references")
        
        # Step 2: Split multi-PowerSource orders with compatibility checking
        enhanced_orders = self._enhance_orders_with_f_gin(valid_orders)
        split_orders = self._split_multi_powersource_orders(enhanced_orders)
        self.logger.info(f"Split into {len(split_orders)} final orders after multi-PowerSource processing")
        
        # Step 3: Create Trinity combinations with semantic descriptions
        trinity_combinations = self._create_trinity_combinations(split_orders)
        self.logger.info(f"Created {len(trinity_combinations)} Trinity combinations")
        
        # Step 4: Calculate co-occurrences from split orders
        co_occurrences = self._calculate_co_occurrences_from_orders(split_orders)
        self.logger.info(f"Calculated {len(co_occurrences)} product co-occurrences")
        
        # Step 5: Create the new graph structure in Neo4j
        self._create_customer_nodes_new(split_orders)
        self._create_order_nodes(split_orders)
        self._create_transaction_nodes_new(split_orders)
        self._create_trinity_nodes(trinity_combinations)
        
        # Step 6: Create relationships
        self._create_order_relationships(split_orders, trinity_combinations)
        
        # Step 7: Create CO_OCCURS relationships
        if co_occurrences:
            self._create_co_occurrence_relationships(co_occurrences)
        
        # Step 8: Create indexes for performance
        self.create_indexes()
        
        result.is_valid = True  # Always valid since we skip problematic records
        
        self.logger.info(f"Sales data loading completed:")
        self.logger.info(f"  Valid records: {result.valid_records}")
        self.logger.info(f"  Split orders: {len(split_orders)}")
        self.logger.info(f"  Trinity combinations: {len(trinity_combinations)}")
        self.logger.info(f"  Skipped records: {self._skipped_records}")
        self.logger.info(f"  Co-occurrence relationships: {len(co_occurrences)}")
        
        return result
    
    def _enhance_orders_with_f_gin(self, orders: Dict[str, List[SalesRecord]]) -> Dict[str, List[SalesRecord]]:
        """
        Enhance orders by adding F-gin products for Renegade PowerSource orders.
        This ensures co-occurrence relationships are created between Renegade and F-gin products.
        """
        enhanced_orders = {}
        renegade_orders_enhanced = 0
        f_gin_records_added = 0
        
        for order_id, records in orders.items():
            # Copy the original records
            enhanced_records = list(records)
            
            # Check if this order contains Renegade PowerSource (0445250880)
            has_renegade = any(record.gin == '0445250880' for record in records)
            
            if has_renegade:
                # Check if F-gin products are already present
                existing_gins = {record.gin for record in records}
                
                # Get sample record for customer/facility info
                sample_record = records[0]
                
                # Add F000000005 (No Cooler Available) if not present
                if 'F000000005' not in existing_gins:
                    f_gin_record = SalesRecord(
                        order_id=order_id,
                        line_no=f"F005_AUTO",
                        gin='F000000005',
                        description='No Cooler Available - All-in-one unit',
                        customer=sample_record.customer,
                        facility=sample_record.facility,
                        warehouse=sample_record.warehouse,
                        category='Cooler'
                    )
                    enhanced_records.append(f_gin_record)
                    f_gin_records_added += 1
                
                # Add F000000007 (No Feeder Available) if not present
                if 'F000000007' not in existing_gins:
                    f_gin_record = SalesRecord(
                        order_id=order_id,
                        line_no=f"F007_AUTO",
                        gin='F000000007',
                        description='No Feeder Available - All-in-one unit',
                        customer=sample_record.customer,
                        facility=sample_record.facility,
                        warehouse=sample_record.warehouse,
                        category='Feeder'
                    )
                    enhanced_records.append(f_gin_record)
                    f_gin_records_added += 1
                
                renegade_orders_enhanced += 1
            
            enhanced_orders[order_id] = enhanced_records
        
        self.logger.info(f"Enhanced {renegade_orders_enhanced} Renegade orders with {f_gin_records_added} F-gin records for co-occurrence analysis")
        
        return enhanced_orders
    
    def _split_multi_powersource_orders(self, orders: Dict[str, List[SalesRecord]]) -> List[OrderData]:
        """
        Split orders with multiple PowerSources into separate sub-orders.
        
        Algorithm:
        1. For each order, identify unique PowerSources (ignore duplicates)
        2. For each PowerSource, find compatible feeder and cooler from ALL order line items
        3. Only create sub-order if both compatible feeder AND cooler found
        4. Create sub-order with suffix: originalID-1, originalID-2, etc.
        5. Include compatible accessories from complete line item set
        
        Args:
            orders: Dictionary of order_id -> list of SalesRecords
            
        Returns:
            List of OrderData objects representing split orders
        """
        self.logger.info("Starting multi-PowerSource order splitting with compatibility checking...")
        
        # Load DETERMINES relationships for compatibility checking
        determines_relationships = self._load_determines_relationships()
        split_orders = []
        
        for original_order_id, records in orders.items():
            # Group line items by category
            products_by_category = defaultdict(list)
            for record in records:
                category = getattr(record, 'category', '')
                if category:
                    products_by_category[category].append(record)
            
            # Get unique PowerSources (ignore duplicate quantities)
            powersources = products_by_category.get('PowerSource', [])
            unique_powersources = {}
            for ps_record in powersources:
                if ps_record.gin not in unique_powersources:
                    unique_powersources[ps_record.gin] = ps_record
            
            # If single PowerSource, create single order
            if len(unique_powersources) <= 1:
                if unique_powersources:  # Has at least one PowerSource
                    # Create single order with all line items
                    order_data = OrderData(
                        original_order_id=original_order_id,
                        order_id=original_order_id,
                        customer=records[0].customer,
                        facility=records[0].facility,
                        warehouse=records[0].warehouse,
                        line_items=records
                    )
                    split_orders.append(order_data)
                continue
            
            # Multiple PowerSources - split into sub-orders
            all_feeders = [r.gin for r in products_by_category.get('Feeder', [])]
            all_coolers = [r.gin for r in products_by_category.get('Cooler', [])]
            all_accessories = products_by_category.get('Accessory', [])
            
            sub_order_count = 0
            
            for ps_gin, ps_record in unique_powersources.items():
                # Find compatible feeder from ALL order line items
                compatible_feeder_gin = self._find_compatible_component(
                    ps_gin, all_feeders, 'Feeder', determines_relationships
                )
                
                # Find compatible cooler from ALL order line items 
                compatible_cooler_gin = self._find_compatible_component(
                    ps_gin, all_coolers, 'Cooler', determines_relationships
                )
                
                # Only create sub-order if BOTH feeder and cooler found
                if compatible_feeder_gin and compatible_cooler_gin:
                    sub_order_count += 1
                    sub_order_id = f"{original_order_id}-{sub_order_count}"
                    
                    # Build line items for this sub-order
                    sub_order_line_items = [ps_record]  # Start with PowerSource
                    
                    # Add compatible feeder
                    feeder_record = next(
                        (r for r in products_by_category.get('Feeder', []) if r.gin == compatible_feeder_gin),
                        None
                    )
                    if feeder_record:
                        sub_order_line_items.append(feeder_record)
                    
                    # Add compatible cooler
                    cooler_record = next(
                        (r for r in products_by_category.get('Cooler', []) if r.gin == compatible_cooler_gin),
                        None
                    )
                    if cooler_record:
                        sub_order_line_items.append(cooler_record)
                    
                    # Add compatible accessories from complete line item set
                    # (For now, add all accessories - could enhance with compatibility logic)
                    sub_order_line_items.extend(all_accessories)
                    
                    # Create sub-order
                    sub_order = OrderData(
                        original_order_id=original_order_id,
                        order_id=sub_order_id,
                        customer=ps_record.customer,
                        facility=ps_record.facility,
                        warehouse=ps_record.warehouse,
                        line_items=sub_order_line_items
                    )
                    
                    split_orders.append(sub_order)
                    
                    self.logger.debug(
                        f"Created sub-order {sub_order_id} for PowerSource {ps_gin} "
                        f"with feeder {compatible_feeder_gin} and cooler {compatible_cooler_gin}"
                    )
                    
                else:
                    # Log skipped PowerSource
                    missing_components = []
                    if not compatible_feeder_gin:
                        missing_components.append('feeder')
                    if not compatible_cooler_gin:
                        missing_components.append('cooler')
                    
                    self.logger.warning(
                        f"Skipped PowerSource {ps_gin} in order {original_order_id}: "
                        f"missing compatible {', '.join(missing_components)}"
                    )
        
        self.logger.info(
            f"Order splitting completed: {len(orders)} original orders → {len(split_orders)} split orders"
        )
        
        return split_orders
    
    def _create_trinity_combinations(self, orders: List[OrderData]) -> List[TrinityData]:
        """
        Create Trinity combinations from split orders with semantic descriptions.
        Each order should have exactly one PowerSource with compatible feeder/cooler.
        
        Args:
            orders: List of OrderData objects (post-splitting)
            
        Returns:
            List of TrinityData objects with combined descriptions for semantic search
        """
        self.logger.info("Creating Trinity combinations with semantic descriptions...")
        
        trinity_combinations = []
        trinity_map = {}  # trinity_id -> TrinityData for deduplication
        
        for order in orders:
            # Group line items by category
            products_by_category = defaultdict(list)
            for item in order.line_items:
                category = getattr(item, 'category', '')
                if category in ['PowerSource', 'Feeder', 'Cooler']:
                    products_by_category[category].append(item)
            
            # Should have exactly one of each for split orders
            powersources = products_by_category.get('PowerSource', [])
            feeders = products_by_category.get('Feeder', [])
            coolers = products_by_category.get('Cooler', [])
            
            if len(powersources) == 1 and len(feeders) == 1 and len(coolers) == 1:
                ps_record = powersources[0]
                feeder_record = feeders[0]
                cooler_record = coolers[0]
                
                # Create Trinity ID
                trinity_id = f"{ps_record.gin}_{feeder_record.gin}_{cooler_record.gin}"
                
                if trinity_id not in trinity_map:
                    # Get product names from catalog
                    ps_name = self._get_product_name(ps_record.gin) or ps_record.description or ps_record.gin
                    feeder_name = self._get_product_name(feeder_record.gin) or feeder_record.description or feeder_record.gin
                    cooler_name = self._get_product_name(cooler_record.gin) or cooler_record.description or cooler_record.gin
                    
                    # Create Trinity with semantic description
                    trinity_data = TrinityData(
                        trinity_id=trinity_id,
                        powersource_gin=ps_record.gin,
                        feeder_gin=feeder_record.gin,
                        cooler_gin=cooler_record.gin,
                        powersource_name=ps_name,
                        feeder_name=feeder_name,
                        cooler_name=cooler_name,
                        combined_description="",  # Will be auto-generated
                        orders=[order.order_id]
                    )
                    
                    # Generate semantic description
                    trinity_data.combined_description = self._generate_trinity_description(
                        trinity_data
                    )
                    
                    trinity_map[trinity_id] = trinity_data
                    
                else:
                    # Add this order to existing Trinity
                    trinity_map[trinity_id].orders.append(order.order_id)
                
            else:
                # Log problematic orders
                self.logger.warning(
                    f"Order {order.order_id} does not have exactly 1 PowerSource, 1 Feeder, 1 Cooler: "
                    f"PS={len(powersources)}, F={len(feeders)}, C={len(coolers)}"
                )
        
        trinity_combinations = list(trinity_map.values())
        
        self.logger.info(
            f"Created {len(trinity_combinations)} unique Trinity combinations "
            f"from {len(orders)} split orders"
        )
        
        # Log sample Trinity descriptions for verification
        for i, trinity in enumerate(trinity_combinations[:3]):
            self.logger.info(
                f"Trinity {i+1} ({trinity.trinity_id}): {trinity.combined_description[:100]}..."
            )
        
        return trinity_combinations
    
    def _get_product_name(self, gin: str) -> str:
        """
        Get product name from catalog for Trinity description.
        Load product data from Neo4j since _product_catalog is just a set of GINs.
        
        Args:
            gin: Product GIN number
            
        Returns:
            Product name or None if not found
        """
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                query = "MATCH (p:Product {gin: $gin}) RETURN p.product_name as name, p.description as description"
                result = session.run(query, gin=gin)
                record = result.single()
                
                if record:
                    return record['name'] or record['description'] or gin
                else:
                    return gin
                    
        except Exception as e:
            self.logger.warning(f"Failed to get product name for {gin}: {e}")
            return gin
    
    def _generate_trinity_description(self, trinity: TrinityData) -> str:
        """
        Generate comprehensive semantic description for Trinity combination.
        
        Args:
            trinity: TrinityData object
            
        Returns:
            Combined semantic description for search
        """
        # Handle F-GIN products with special descriptions
        feeder_desc = trinity.feeder_name
        cooler_desc = trinity.cooler_name
        
        if trinity.feeder_gin == 'F000000007':
            feeder_desc = "integrated feeder (no separate feeder required)"
        if trinity.cooler_gin == 'F000000005':
            cooler_desc = "integrated cooling (no separate cooler required)"
        
        # Generate comprehensive description
        description = (
            f"Complete welding system featuring {trinity.powersource_name} power source "
            f"with {feeder_desc} and {cooler_desc}. "
            f"This welding package provides comprehensive power generation, wire feeding, "
            f"and cooling capabilities for professional welding applications. "
            f"Optimized for industrial use with {trinity.powersource_name} technology, "
            f"compatible feeder system, and appropriate cooling solution. "
            f"Suitable for {trinity.powersource_name.lower()} welding processes "
            f"requiring coordinated power, feeding, and thermal management."
        )
        
        return description
    
    def _calculate_co_occurrences_from_orders(self, orders: List[OrderData]) -> List[CoOccurrence]:
        """Calculate product co-occurrences from split OrderData objects"""
        co_occurrence_data = defaultdict(lambda: {
            'frequency': 0,
            'orders': set()
        })
        
        for order in orders:
            # Get unique products in this order
            products_in_order = list(set(record.gin for record in order.line_items))
            
            # Skip orders with only one product (no co-occurrence possible)
            if len(products_in_order) < 2:
                continue
            
            # Create co-occurrence pairs (bidirectional)
            for i, product1 in enumerate(products_in_order):
                for product2 in products_in_order[i+1:]:
                    # Create sorted pair key for consistency
                    pair_key = tuple(sorted([product1, product2]))
                    
                    co_occurrence_data[pair_key]['frequency'] += 1
                    co_occurrence_data[pair_key]['orders'].add(order.order_id)
        
        # Convert to CoOccurrence objects with confidence scoring
        co_occurrences = []
        max_frequency = max((data['frequency'] for data in co_occurrence_data.values()), default=1)
        
        for (product1, product2), data in co_occurrence_data.items():
            # Calculate confidence score based on frequency
            frequency_score = min(data['frequency'] / max_frequency, 1.0)
            confidence_score = frequency_score
            
            co_occurrence = CoOccurrence(
                product1_gin=product1,
                product2_gin=product2,
                frequency=data['frequency'],
                last_occurrence_date=date.today(),
                orders=list(data['orders']),
                confidence_score=confidence_score
            )
            
            co_occurrences.append(co_occurrence)
        
        # Sort by frequency (most frequent first)
        co_occurrences.sort(key=lambda x: x.frequency, reverse=True)
        
        return co_occurrences
    
    def _calculate_co_occurrences(self, orders: Dict[str, List[SalesRecord]]) -> List[CoOccurrence]:
        """Calculate product co-occurrences within orders"""
        co_occurrence_data = defaultdict(lambda: {
            'frequency': 0,
            'orders': set()
        })
        
        for order_id, records in orders.items():
            # Get unique products in this order
            products_in_order = list(set(record.gin_number for record in records))
            
            # Skip orders with only one product (no co-occurrence possible)
            if len(products_in_order) < 2:
                continue
            
            # Create co-occurrence pairs (bidirectional)
            for i, product1 in enumerate(products_in_order):
                for product2 in products_in_order[i+1:]:
                    # Create sorted pair key for consistency
                    pair_key = tuple(sorted([product1, product2]))
                    
                    co_occurrence_data[pair_key]['frequency'] += 1
                    co_occurrence_data[pair_key]['orders'].add(order_id)
        
        # Convert to CoOccurrence objects with confidence scoring
        co_occurrences = []
        max_frequency = max((data['frequency'] for data in co_occurrence_data.values()), default=1)
        
        for (product1, product2), data in co_occurrence_data.items():
            # Calculate confidence score based on frequency only (no date data available)
            frequency_score = min(data['frequency'] / max_frequency, 1.0)
            
            # Since we don't have order dates, use frequency-based scoring only
            confidence_score = frequency_score
            
            co_occurrence = CoOccurrence(
                product1_gin=product1,
                product2_gin=product2,
                frequency=data['frequency'],
                last_occurrence_date=date.today(),  # Use current date as placeholder
                orders=list(data['orders']),
                confidence_score=confidence_score
            )
            
            co_occurrences.append(co_occurrence)
        
        # Sort by frequency (most frequent first)
        co_occurrences.sort(key=lambda x: x.frequency, reverse=True)
        
        return co_occurrences
    
    def _create_customer_nodes_new(self, orders: List[OrderData]):
        """
        Create Customer nodes from split orders.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        # Collect customer data
        customers_data = defaultdict(lambda: {
            'facilities': set(),
            'warehouses': set(),
            'order_count': 0,
            'categories': set()
        })
        
        for order in orders:
            if order.customer:
                customer_key = order.customer.strip()
                if customer_key:
                    customers_data[customer_key]['facilities'].add(order.facility)
                    customers_data[customer_key]['warehouses'].add(order.warehouse)
                    customers_data[customer_key]['order_count'] += 1
                    
                    # Collect categories from line items
                    for item in order.line_items:
                        if hasattr(item, 'category') and item.category:
                            customers_data[customer_key]['categories'].add(item.category)
        
        # Convert sets to lists for Customer node creation
        customers_data_lists = {}
        for customer_name, data in customers_data.items():
            customers_data_lists[customer_name] = {
                'facilities': list(data['facilities']),
                'warehouses': list(data['warehouses']),
                'order_count': data['order_count'],  # Changed from transaction_count
                'categories': list(data['categories'])
            }
        
        # Create Customer nodes in batches
        self._create_customer_nodes(customers_data_lists)
        
        self.logger.info(f"Created {len(customers_data)} Customer nodes from {len(orders)} split orders")
    
    def _create_order_nodes(self, orders: List[OrderData]):
        """
        Create Order header nodes from split orders.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        batch_size = 100
        total_created = 0
        
        for i in range(0, len(orders), batch_size):
            batch = orders[i:i+batch_size]
            
            # Prepare batch data
            orders_batch = []
            for order in batch:
                order_node = {
                    'order_id': order.order_id,
                    'original_order_id': order.original_order_id,
                    'customer': order.customer,
                    'facility': order.facility,
                    'warehouse': order.warehouse,
                    'line_item_count': len(order.line_items),
                    'powersource_count': len(order.powersources),
                    'created_at': datetime.utcnow().isoformat()
                }
                orders_batch.append(order_node)
            
            # Create Order nodes
            cypher_query = """
            UNWIND $orders AS order
            CREATE (o:Order {
                order_id: order.order_id,
                original_order_id: order.original_order_id,
                customer: order.customer,
                facility: order.facility,
                warehouse: order.warehouse,
                line_item_count: order.line_item_count,
                powersource_count: order.powersource_count,
                created_at: order.created_at
            })
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, orders=orders_batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Order nodes (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Order batch: {e}")
                raise
        
        self.logger.info(f"Total Order nodes created: {total_created}")
    
    def _create_transaction_nodes_new(self, orders: List[OrderData]):
        """
        Create Transaction nodes (line items) from split orders.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        # Collect all line items
        all_transactions = []
        for order in orders:
            for item in order.line_items:
                transaction_data = {
                    'order_id': order.order_id,
                    'original_order_id': order.original_order_id,
                    'line_no': item.line_no,
                    'gin': item.gin,
                    'description': item.description,
                    'customer': order.customer,
                    'facility': order.facility,
                    'warehouse': order.warehouse,
                    'category': getattr(item, 'category', '')
                }
                all_transactions.append(transaction_data)
        
        # Create Transaction nodes in batches
        batch_size = 500
        total_created = 0
        
        for i in range(0, len(all_transactions), batch_size):
            batch = all_transactions[i:i+batch_size]
            
            # Prepare batch data
            transactions_batch = []
            for txn in batch:
                transaction_node = {
                    'order_id': txn['order_id'],
                    'original_order_id': txn['original_order_id'],
                    'line_no': txn['line_no'],
                    'gin': txn['gin'],
                    'description': txn['description'],
                    'customer': txn['customer'],
                    'facility': txn['facility'],
                    'warehouse': txn['warehouse'],
                    'category': txn['category'],
                    'created_at': datetime.utcnow().isoformat()
                }
                transactions_batch.append(transaction_node)
            
            # Create Transaction nodes
            cypher_query = """
            UNWIND $transactions AS txn
            CREATE (t:Transaction {
                order_id: txn.order_id,
                original_order_id: txn.original_order_id,
                line_no: txn.line_no,
                gin: txn.gin,
                description: txn.description,
                customer: txn.customer,
                facility: txn.facility,
                warehouse: txn.warehouse,
                category: txn.category,
                created_at: txn.created_at
            })
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, transactions=transactions_batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Transaction nodes (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Transaction batch: {e}")
                raise
        
        self.logger.info(f"Total Transaction nodes created: {total_created}")
    
    def _create_trinity_nodes(self, trinity_combinations: List[TrinityData]):
        """
        Create Trinity nodes with semantic descriptions for search.
        
        Args:
            trinity_combinations: List of TrinityData objects
        """
        if not trinity_combinations:
            return
        
        batch_size = 100
        total_created = 0
        
        for i in range(0, len(trinity_combinations), batch_size):
            batch = trinity_combinations[i:i+batch_size]
            
            # Prepare batch data
            trinity_batch = []
            for trinity in batch:
                trinity_node = {
                    'trinity_id': trinity.trinity_id,
                    'powersource_gin': trinity.powersource_gin,
                    'feeder_gin': trinity.feeder_gin,
                    'cooler_gin': trinity.cooler_gin,
                    'powersource_name': trinity.powersource_name,
                    'feeder_name': trinity.feeder_name,
                    'cooler_name': trinity.cooler_name,
                    'combined_description': trinity.combined_description,
                    'order_count': len(trinity.orders),
                    'sample_orders': trinity.orders[:5],  # First 5 orders as sample
                    'created_at': datetime.utcnow().isoformat()
                }
                trinity_batch.append(trinity_node)
            
            # Create Trinity nodes
            cypher_query = """
            UNWIND $trinity_batch AS trinity
            CREATE (tr:Trinity {
                trinity_id: trinity.trinity_id,
                powersource_gin: trinity.powersource_gin,
                feeder_gin: trinity.feeder_gin,
                cooler_gin: trinity.cooler_gin,
                powersource_name: trinity.powersource_name,
                feeder_name: trinity.feeder_name,
                cooler_name: trinity.cooler_name,
                combined_description: trinity.combined_description,
                order_count: trinity.order_count,
                sample_orders: trinity.sample_orders,
                created_at: trinity.created_at
            })
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, trinity_batch=trinity_batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Trinity nodes (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Trinity batch: {e}")
                raise
        
        self.logger.info(f"Total Trinity nodes created: {total_created}")
    
    def _create_order_relationships(self, orders: List[OrderData], trinity_combinations: List[TrinityData]):
        """
        Create all relationships in the new architecture:
        - (Customer)-[:PLACED]->(Order)
        - (Order)-[:PART_OF]->(Transaction)  
        - (Transaction)-[:LINE_ITEM]->(Product)
        - (Order)-[:CONTAINS]->(Product)
        - (Order)-[:FORMS_TRINITY]->(Trinity)
        - (Trinity)-[:COMPRISES {component_type}]->(Product)
        
        Args:
            orders: List of OrderData objects
            trinity_combinations: List of TrinityData objects
        """
        self.logger.info("Creating relationships for new architecture...")
        
        # Step 1: Create Customer-Order relationships
        self._create_customer_order_relationships(orders)
        
        # Step 2: Create Order-Transaction relationships  
        self._create_order_transaction_relationships(orders)
        
        # Step 3: Create Transaction-Product relationships
        self._create_transaction_product_relationships(orders)
        
        # Step 4: Create Order-Product relationships (summary level)
        self._create_order_product_relationships(orders)
        
        # Step 5: Create Order-Trinity relationships
        self._create_order_trinity_relationships(orders, trinity_combinations)
        
        # Step 6: Create Trinity-Product relationships
        self._create_trinity_product_relationships(trinity_combinations)
        
        self.logger.info("All relationships created successfully")
    
    def _create_customer_order_relationships(self, orders: List[OrderData]):
        """
        Create (Customer)-[:PLACED]->(Order) relationships.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        # Collect Customer-Order pairs
        customer_order_pairs = []
        for order in orders:
            if order.customer:
                customer_order_pairs.append({
                    'customer_name': order.customer,
                    'order_id': order.order_id
                })
        
        if not customer_order_pairs:
            return
        
        # Create relationships in batches
        batch_size = 500
        total_created = 0
        
        for i in range(0, len(customer_order_pairs), batch_size):
            batch = customer_order_pairs[i:i+batch_size]
            
            cypher_query = """
            UNWIND $pairs AS pair
            MATCH (c:Customer {name: pair.customer_name})
            MATCH (o:Order {order_id: pair.order_id})
            CREATE (c)-[:PLACED]->(o)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, pairs=batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Customer-Order relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Customer-Order relationships: {e}")
                raise
        
        self.logger.info(f"Total Customer-Order relationships created: {total_created}")
    
    def _create_order_transaction_relationships(self, orders: List[OrderData]):
        """
        Create (Order)-[:PART_OF]->(Transaction) relationships.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        # Collect Order-Transaction pairs
        order_transaction_pairs = []
        for order in orders:
            for item in order.line_items:
                order_transaction_pairs.append({
                    'order_id': order.order_id,
                    'line_no': item.line_no
                })
        
        # Create relationships in batches
        batch_size = 1000
        total_created = 0
        
        for i in range(0, len(order_transaction_pairs), batch_size):
            batch = order_transaction_pairs[i:i+batch_size]
            
            cypher_query = """
            UNWIND $pairs AS pair
            MATCH (o:Order {order_id: pair.order_id})
            MATCH (t:Transaction {order_id: pair.order_id, line_no: pair.line_no})
            CREATE (o)-[:PART_OF]->(t)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, pairs=batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Order-Transaction relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Order-Transaction relationships: {e}")
                raise
        
        self.logger.info(f"Total Order-Transaction relationships created: {total_created}")
    
    def _create_transaction_product_relationships(self, orders: List[OrderData]):
        """
        Create (Transaction)-[:LINE_ITEM]->(Product) relationships.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        # Collect Transaction-Product pairs
        transaction_product_pairs = []
        for order in orders:
            for item in order.line_items:
                transaction_product_pairs.append({
                    'order_id': order.order_id,
                    'line_no': item.line_no,
                    'gin': item.gin
                })
        
        # Create relationships in batches
        batch_size = 1000
        total_created = 0
        
        for i in range(0, len(transaction_product_pairs), batch_size):
            batch = transaction_product_pairs[i:i+batch_size]
            
            cypher_query = """
            UNWIND $pairs AS pair
            MATCH (t:Transaction {order_id: pair.order_id, line_no: pair.line_no})
            MATCH (p:Product {gin: pair.gin})
            CREATE (t)-[:LINE_ITEM]->(p)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, pairs=batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Transaction-Product relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Transaction-Product relationships: {e}")
                raise
        
        self.logger.info(f"Total Transaction-Product relationships created: {total_created}")
    
    def _create_order_product_relationships(self, orders: List[OrderData]):
        """
        Create (Order)-[:CONTAINS]->(Product) relationships for summary level access.
        
        Args:
            orders: List of OrderData objects
        """
        if not orders:
            return
        
        # Collect unique Order-Product pairs
        order_product_pairs = []
        for order in orders:
            unique_products = set()
            for item in order.line_items:
                if item.gin not in unique_products:
                    unique_products.add(item.gin)
                    order_product_pairs.append({
                        'order_id': order.order_id,
                        'gin': item.gin
                    })
        
        # Create relationships in batches
        batch_size = 1000
        total_created = 0
        
        for i in range(0, len(order_product_pairs), batch_size):
            batch = order_product_pairs[i:i+batch_size]
            
            cypher_query = """
            UNWIND $pairs AS pair
            MATCH (o:Order {order_id: pair.order_id})
            MATCH (p:Product {gin: pair.gin})
            CREATE (o)-[:CONTAINS]->(p)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, pairs=batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Order-Product relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Order-Product relationships: {e}")
                raise
        
        self.logger.info(f"Total Order-Product relationships created: {total_created}")
    
    def _create_order_trinity_relationships(self, orders: List[OrderData], trinity_combinations: List[TrinityData]):
        """
        Create (Order)-[:FORMS_TRINITY]->(Trinity) relationships.
        
        Args:
            orders: List of OrderData objects
            trinity_combinations: List of TrinityData objects
        """
        if not trinity_combinations:
            return
        
        # Create Trinity ID to Order mapping
        trinity_to_orders = {}
        for trinity in trinity_combinations:
            trinity_to_orders[trinity.trinity_id] = trinity.orders
        
        # Collect Order-Trinity pairs
        order_trinity_pairs = []
        for trinity_id, order_ids in trinity_to_orders.items():
            for order_id in order_ids:
                order_trinity_pairs.append({
                    'order_id': order_id,
                    'trinity_id': trinity_id
                })
        
        # Create relationships in batches
        batch_size = 500
        total_created = 0
        
        for i in range(0, len(order_trinity_pairs), batch_size):
            batch = order_trinity_pairs[i:i+batch_size]
            
            cypher_query = """
            UNWIND $pairs AS pair
            MATCH (o:Order {order_id: pair.order_id})
            MATCH (tr:Trinity {trinity_id: pair.trinity_id})
            CREATE (o)-[:FORMS_TRINITY]->(tr)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, pairs=batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Order-Trinity relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Order-Trinity relationships: {e}")
                raise
        
        self.logger.info(f"Total Order-Trinity relationships created: {total_created}")
    
    def _create_trinity_product_relationships(self, trinity_combinations: List[TrinityData]):
        """
        Create (Trinity)-[:COMPRISES {component_type}]->(Product) relationships.
        
        Args:
            trinity_combinations: List of TrinityData objects
        """
        if not trinity_combinations:
            return
        
        # Collect Trinity-Product relationships with component types
        trinity_product_pairs = []
        for trinity in trinity_combinations:
            # PowerSource relationship
            trinity_product_pairs.append({
                'trinity_id': trinity.trinity_id,
                'gin': trinity.powersource_gin,
                'component_type': 'PowerSource'
            })
            
            # Feeder relationship
            trinity_product_pairs.append({
                'trinity_id': trinity.trinity_id,
                'gin': trinity.feeder_gin,
                'component_type': 'Feeder'
            })
            
            # Cooler relationship
            trinity_product_pairs.append({
                'trinity_id': trinity.trinity_id,
                'gin': trinity.cooler_gin,
                'component_type': 'Cooler'
            })
        
        # Create relationships in batches
        batch_size = 1000
        total_created = 0
        
        for i in range(0, len(trinity_product_pairs), batch_size):
            batch = trinity_product_pairs[i:i+batch_size]
            
            cypher_query = """
            UNWIND $pairs AS pair
            MATCH (tr:Trinity {trinity_id: pair.trinity_id})
            MATCH (p:Product {gin: pair.gin})
            CREATE (tr)-[:COMPRISES {
                component_type: pair.component_type
            }]->(p)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, pairs=batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Trinity-Product relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Trinity-Product relationships: {e}")
                raise
        
        self.logger.info(f"Total Trinity-Product relationships created: {total_created}")
    
    def _create_co_occurrence_relationships(self, co_occurrences: List[CoOccurrence]):
        """Create CO_OCCURS relationships in Neo4j"""
        if not co_occurrences:
            return
        
        # Process in batches for performance
        batch_size = 500
        total_created = 0
        
        for i in range(0, len(co_occurrences), batch_size):
            batch = co_occurrences[i:i+batch_size]
            
            # Prepare batch data
            relationship_data = []
            for co_occ in batch:
                relationship_data.append({
                    'product1_gin': co_occ.product1_gin,
                    'product2_gin': co_occ.product2_gin,
                    'frequency': co_occ.frequency,
                    'last_occurrence_date': co_occ.last_occurrence_date.isoformat(),
                    'confidence_score': co_occ.confidence_score,
                    'orders_count': len(co_occ.orders),
                    'sample_orders': co_occ.orders[:5]  # Store first 5 orders as sample
                })
            
            # Create bidirectional CO_OCCURS relationships
            cypher_query = """
            UNWIND $relationships AS rel
            MATCH (p1:Product {gin: rel.product1_gin})
            MATCH (p2:Product {gin: rel.product2_gin})
            CREATE (p1)-[r1:CO_OCCURS {
                frequency: rel.frequency,
                last_occurrence_date: rel.last_occurrence_date,
                confidence_score: rel.confidence_score,
                orders_count: rel.orders_count,
                sample_orders: rel.sample_orders,
                created_at: datetime()
            }]->(p2)
            CREATE (p2)-[r2:CO_OCCURS {
                frequency: rel.frequency,
                last_occurrence_date: rel.last_occurrence_date,
                confidence_score: rel.confidence_score,
                orders_count: rel.orders_count,
                sample_orders: rel.sample_orders,
                created_at: datetime()
            }]->(p1)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, relationships=relationship_data)
                
                batch_created = len(batch) * 2  # Bidirectional relationships
                total_created += batch_created
                self.logger.info(f"Created {batch_created} CO_OCCURS relationships (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create co-occurrence batch: {e}")
                raise
        
        self.logger.info(f"Total CO_OCCURS relationships created: {total_created}")
    
    def _create_transaction_nodes(self, orders: Dict[str, List[SalesRecord]]):
        """
        Create Transaction and Customer nodes for detailed sales analytics.
        
        Creates:
        - Customer nodes with aggregated info
        - Transaction nodes for each sales record
        - Relationships: (Customer)-[:MADE]->(Transaction)-[:CONTAINS]->(Product)
        """
        if not orders:
            return
        
        self.logger.info(f"Creating Transaction and Customer nodes for {len(orders)} orders")
        
        # Step 1: Collect all transactions and group by customer
        all_transactions = []
        customers_data = defaultdict(lambda: {
            'facilities': set(),
            'warehouses': set(),
            'transaction_count': 0,
            'categories': set()
        })
        
        for order_id, records in orders.items():
            for record in records:
                # Collect transaction data
                transaction_data = {
                    'order_id': record.order_id,
                    'line_no': record.line_no,
                    'gin': record.gin,
                    'description': record.description,
                    'customer': record.customer,
                    'facility': record.facility,
                    'warehouse': record.warehouse,
                    'category': record.category
                }
                all_transactions.append(transaction_data)
                
                # Aggregate customer data for Customer nodes
                if record.customer:
                    customer_key = record.customer.strip()
                    if customer_key:
                        customers_data[customer_key]['facilities'].add(record.facility)
                        customers_data[customer_key]['warehouses'].add(record.warehouse)
                        customers_data[customer_key]['transaction_count'] += 1
                        customers_data[customer_key]['categories'].add(record.category)
        
        # Step 2: Create Customer nodes in batches
        self._create_customer_nodes(customers_data)
        
        # Step 3: Create Transaction nodes in batches
        self._create_transaction_records(all_transactions)
        
        self.logger.info(f"Created {len(customers_data)} Customer nodes and {len(all_transactions)} Transaction nodes")
    
    def _create_customer_nodes(self, customers_data: Dict[str, Dict]):
        """Create Customer nodes with aggregated information"""
        if not customers_data:
            return
        
        batch_size = 100
        customer_list = list(customers_data.items())
        total_created = 0
        
        for i in range(0, len(customer_list), batch_size):
            batch = customer_list[i:i+batch_size]
            
            # Prepare batch data
            customers_batch = []
            for customer_name, data in batch:
                customer_node = {
                    'name': customer_name,
                    'primary_facility': data['facilities'][0] if data['facilities'] else '',
                    'all_facilities': data['facilities'],
                    'all_warehouses': data['warehouses'],
                    'order_count': data['order_count'],
                    'product_categories': data['categories'],
                    'created_at': datetime.utcnow().isoformat()
                }
                customers_batch.append(customer_node)
            
            # Create Customer nodes
            cypher_query = """
            UNWIND $customers AS customer
            MERGE (c:Customer {name: customer.name})
            SET c.primary_facility = customer.primary_facility,
                c.all_facilities = customer.all_facilities,
                c.all_warehouses = customer.all_warehouses,
                c.order_count = customer.order_count,
                c.product_categories = customer.product_categories,
                c.created_at = customer.created_at,
                c.updated_at = datetime()
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, customers=customers_batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Customer nodes (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Customer batch: {e}")
                raise
        
        self.logger.info(f"Total Customer nodes created: {total_created}")
    
    def _add_f_gin_products(self, transactions: List[Dict]) -> List[Dict]:
        """
        Add F-gin dummy products to orders containing Renegade PowerSource
        
        Business Rule: When an order contains Renegade PowerSource (0445250880),
        automatically add F000000005 (No Cooler Available) and F000000007 (No Feeder Available)
        to represent that Renegade is all-in-one and doesn't need separate components.
        """
        enhanced_transactions = list(transactions)  # Copy original transactions
        
        # Group transactions by order_id
        orders_by_id = defaultdict(list)
        for txn in transactions:
            orders_by_id[txn['order_id']].append(txn)
        
        # Track orders that contain Renegade PowerSource
        renegade_orders = set()
        f_gin_added_count = 0
        
        for order_id, order_transactions in orders_by_id.items():
            # Check if this order contains Renegade PowerSource (0445250880)
            has_renegade = any(txn['gin'] == '0445250880' for txn in order_transactions)
            
            if has_renegade:
                renegade_orders.add(order_id)
                
                # Check if F-gin products are already present
                existing_gims = {txn['gin'] for txn in order_transactions}
                
                # Get customer info from existing transactions for consistency
                sample_txn = order_transactions[0]
                
                # Add F000000005 (No Cooler Available) if not present
                if 'F000000005' not in existing_gims:
                    f_gin_txn = {
                        'order_id': order_id,
                        'line_no': f"F005_{len(order_transactions) + 1}",  # Generate unique line number
                        'gin': 'F000000005',
                        'description': 'No Cooler Available - All-in-one unit (auto-added)',
                        'customer': sample_txn['customer'],
                        'facility': sample_txn['facility'],
                        'warehouse': sample_txn['warehouse'],
                        'category': 'Cooler'
                    }
                    enhanced_transactions.append(f_gin_txn)
                    f_gin_added_count += 1
                
                # Add F000000007 (No Feeder Available) if not present
                if 'F000000007' not in existing_gims:
                    f_gin_txn = {
                        'order_id': order_id,
                        'line_no': f"F007_{len(order_transactions) + 2}",  # Generate unique line number
                        'gin': 'F000000007',
                        'description': 'No Feeder Available - All-in-one unit (auto-added)',
                        'customer': sample_txn['customer'],
                        'facility': sample_txn['facility'],
                        'warehouse': sample_txn['warehouse'],
                        'category': 'Feeder'
                    }
                    enhanced_transactions.append(f_gin_txn)
                    f_gin_added_count += 1
        
        self.logger.info(f"Enhanced sales data: Added {f_gin_added_count} F-gin products to {len(renegade_orders)} Renegade orders")
        
        return enhanced_transactions
    
    def _load_determines_relationships(self):
        """Load DETERMINES relationships from database for compatibility checking"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                query = """
                MATCH (ps:Product)-[d:DETERMINES]->(comp:Product)
                WHERE ps.category = 'PowerSource'
                RETURN ps.gin as powersource_gin, 
                       comp.gin as component_gin,
                       comp.category as component_category
                """
                results = session.run(query).data()
                
                # Group by powersource -> category -> [components]
                determines_map = {}
                for record in results:
                    ps_gin = record['powersource_gin'] 
                    comp_gin = record['component_gin']
                    comp_category = record['component_category']
                    
                    if ps_gin not in determines_map:
                        determines_map[ps_gin] = {}
                    if comp_category not in determines_map[ps_gin]:
                        determines_map[ps_gin][comp_category] = []
                        
                    determines_map[ps_gin][comp_category].append(comp_gin)
                
                self.logger.info(f"Loaded DETERMINES relationships for {len(determines_map)} PowerSources")
                return determines_map
                
        except Exception as e:
            self.logger.error(f"Failed to load DETERMINES relationships: {e}")
            return {}

    def _find_compatible_component(self, powersource_gin, available_components, component_category, determines_relationships):
        """
        Find compatible component for PowerSource from available components in the order.
        
        Args:
            powersource_gin: PowerSource GIN to find compatible component for
            available_components: List of component GINs available in the order
            component_category: 'Feeder' or 'Cooler' 
            determines_relationships: Loaded DETERMINES relationships
            
        Returns:
            Compatible component GIN or None if no compatible component found
        """
        # Get components that this PowerSource DETERMINES
        ps_determines = determines_relationships.get(powersource_gin, {})
        required_components = ps_determines.get(component_category, [])
        
        # Find intersection between required and available
        compatible_components = [comp for comp in available_components if comp in required_components]
        
        if compatible_components:
            # Return first compatible component (could be enhanced with priority logic)
            return compatible_components[0]
        
        # No compatible component found
        return None
    
    def _create_transaction_records(self, transactions: List[Dict]):
        """Create Transaction nodes and connect to Customer and Product nodes"""
        if not transactions:
            return
        
        # Add F-gin dummy products for Renegade orders
        enhanced_transactions = self._add_f_gin_products(transactions)
        
        batch_size = 500
        total_created = 0
        
        for i in range(0, len(enhanced_transactions), batch_size):
            batch = enhanced_transactions[i:i+batch_size]
            
            # Prepare batch data
            transactions_batch = []
            for txn in batch:
                transaction_node = {
                    'order_id': txn['order_id'],
                    'line_no': txn['line_no'],
                    'gin': txn['gin'],
                    'description': txn['description'],
                    'customer_name': txn['customer'],
                    'facility': txn['facility'],
                    'warehouse': txn['warehouse'],
                    'category': txn['category'],
                    'created_at': datetime.utcnow().isoformat()
                }
                transactions_batch.append(transaction_node)
            
            # Create Transaction nodes and relationships
            cypher_query = """
            UNWIND $transactions AS txn
            
            // Create Transaction node
            CREATE (t:Transaction {
                order_id: txn.order_id,
                line_no: txn.line_no,
                description: txn.description,
                facility: txn.facility,
                warehouse: txn.warehouse,
                category: txn.category,
                created_at: txn.created_at
            })
            
            // Connect to Customer (if exists)
            WITH t, txn
            WHERE txn.customer_name IS NOT NULL AND txn.customer_name <> ''
            MATCH (c:Customer {name: txn.customer_name})
            CREATE (c)-[:MADE]->(t)
            
            // Connect to Product
            WITH t, txn
            MATCH (p:Product {gin: txn.gin})
            CREATE (t)-[:CONTAINS]->(p)
            """
            
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    session.run(cypher_query, transactions=transactions_batch)
                
                batch_created = len(batch)
                total_created += batch_created
                self.logger.info(f"Created {batch_created} Transaction nodes (batch {i//batch_size + 1})")
                
            except Exception as e:
                self.logger.error(f"Failed to create Transaction batch: {e}")
                # Continue with next batch rather than failing completely
                self.logger.warning(f"Skipping transaction batch {i//batch_size + 1} due to error")
        
        self.logger.info(f"Total Transaction nodes created: {total_created}")
    
    def create_indexes(self):
        """Create performance indexes for the new architecture"""
        indexes = [
            # CO_OCCURS relationship indexes
            "CREATE INDEX co_occurs_frequency_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.frequency)",
            "CREATE INDEX co_occurs_confidence_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.confidence_score)",
            "CREATE INDEX co_occurs_date_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.last_occurrence_date)",
            
            # Customer node indexes
            "CREATE INDEX customer_name_index IF NOT EXISTS FOR (c:Customer) ON (c.name)",
            "CREATE INDEX customer_facility_index IF NOT EXISTS FOR (c:Customer) ON (c.primary_facility)",
            "CREATE INDEX customer_order_count_index IF NOT EXISTS FOR (c:Customer) ON (c.order_count)",
            
            # Order node indexes
            "CREATE INDEX order_id_index IF NOT EXISTS FOR (o:Order) ON (o.order_id)",
            "CREATE INDEX order_original_id_index IF NOT EXISTS FOR (o:Order) ON (o.original_order_id)",
            "CREATE INDEX order_customer_index IF NOT EXISTS FOR (o:Order) ON (o.customer)",
            "CREATE INDEX order_facility_index IF NOT EXISTS FOR (o:Order) ON (o.facility)",
            
            # Transaction node indexes
            "CREATE INDEX transaction_order_index IF NOT EXISTS FOR (t:Transaction) ON (t.order_id)",
            "CREATE INDEX transaction_original_order_index IF NOT EXISTS FOR (t:Transaction) ON (t.original_order_id)",
            "CREATE INDEX transaction_gin_index IF NOT EXISTS FOR (t:Transaction) ON (t.gin)",
            "CREATE INDEX transaction_category_index IF NOT EXISTS FOR (t:Transaction) ON (t.category)",
            
            # Trinity node indexes
            "CREATE INDEX trinity_id_index IF NOT EXISTS FOR (tr:Trinity) ON (tr.trinity_id)",
            "CREATE INDEX trinity_powersource_index IF NOT EXISTS FOR (tr:Trinity) ON (tr.powersource_gin)",
            "CREATE INDEX trinity_feeder_index IF NOT EXISTS FOR (tr:Trinity) ON (tr.feeder_gin)",
            "CREATE INDEX trinity_cooler_index IF NOT EXISTS FOR (tr:Trinity) ON (tr.cooler_gin)",
            "CREATE FULLTEXT INDEX trinity_description_index IF NOT EXISTS FOR (tr:Trinity) ON (tr.combined_description)"
        ]
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Created index: {index_query}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")
    
    def get_sales_statistics(self) -> Dict:
        """Get comprehensive sales statistics for new architecture"""
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            # Node count statistics
            node_stats_query = """
            RETURN 
                apoc.meta.stats() AS meta_stats
            """
            
            # Basic statistics without APOC
            basic_stats_query = """
            MATCH (c:Customer) WITH count(c) as customers
            MATCH (o:Order) WITH customers, count(o) as orders
            MATCH (t:Transaction) WITH customers, orders, count(t) as transactions
            MATCH (tr:Trinity) WITH customers, orders, transactions, count(tr) as trinity_nodes
            MATCH (p:Product) WITH customers, orders, transactions, trinity_nodes, count(p) as products
            OPTIONAL MATCH ()-[co:CO_OCCURS]-() WITH customers, orders, transactions, trinity_nodes, products, count(co) as co_occurrences
            RETURN customers, orders, transactions, trinity_nodes, products, co_occurrences
            """
            
            result = session.run(basic_stats_query)
            stats = result.single()
            
            # Get Trinity statistics
            trinity_stats_query = """
            MATCH (tr:Trinity)
            RETURN 
                count(tr) as total_trinity_combinations,
                avg(tr.order_count) as avg_orders_per_trinity,
                max(tr.order_count) as max_orders_per_trinity
            """
            
            trinity_result = session.run(trinity_stats_query)
            trinity_stats = trinity_result.single()
            
            # Get top Trinity combinations
            top_trinity_query = """
            MATCH (tr:Trinity)
            RETURN tr.trinity_id as trinity_id, 
                   tr.powersource_name as powersource_name,
                   tr.feeder_name as feeder_name,
                   tr.cooler_name as cooler_name,
                   tr.order_count as order_count
            ORDER BY tr.order_count DESC
            LIMIT 5
            """
            
            top_trinity_result = session.run(top_trinity_query)
            top_trinity = [
                {
                    'trinity_id': record['trinity_id'],
                    'powersource_name': record['powersource_name'],
                    'feeder_name': record['feeder_name'],
                    'cooler_name': record['cooler_name'],
                    'order_count': record['order_count']
                }
                for record in top_trinity_result
            ]
            
            return {
                'architecture': 'Clean Order-based with Trinity nodes',
                'customers': stats['customers'] or 0,
                'orders': stats['orders'] or 0,
                'transactions': stats['transactions'] or 0,
                'products': stats['products'] or 0,
                'trinity_combinations': trinity_stats['total_trinity_combinations'] or 0,
                'avg_orders_per_trinity': trinity_stats['avg_orders_per_trinity'] or 0,
                'max_orders_per_trinity': trinity_stats['max_orders_per_trinity'] or 0,
                'co_occurrences': stats['co_occurrences'] or 0,
                'top_trinity_combinations': top_trinity,
                'skipped_records': self._skipped_records,
                'missing_product_references': len(getattr(self, '_missing_references', set()))
            }
    
    # Old Trinity relationship method removed - replaced with new architecture