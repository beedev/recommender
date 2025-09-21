"""
Sales Data Loader  
Bharath's Quality-First Implementation

This loader handles sales_data.json and creates comprehensive sales data model:
1. CO_OCCURS relationships for recommendation performance
2. Transaction nodes for detailed sales analytics  
3. Customer nodes for customer intelligence (extensible for profiles)

Creates the following Neo4j structure:
- Customer nodes: aggregated customer data with facilities, categories
- Transaction nodes: individual sales records with order details
- CO_OCCURS relationships: product co-occurrence patterns for recommendations
- Relationships: (Customer)-[:MADE]->(Transaction)-[:CONTAINS]->(Product)

Features:
- Product reference validation (skips invalid GINs)
- Order-based co-occurrence calculation
- Customer aggregation and profiling foundation
- Transaction-level detail preservation
- Frequency tracking and normalization
- Performance optimized batch loading
- Comprehensive indexing for fast queries
- Extensible for future customer profile enhancements
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass

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
        Process and load sales data into Neo4j co-occurrence relationships
        
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
        
        self.logger.info(f"Processing {len(records_data)} sales records")
        
        # Step 1: Validate and group records by order
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
        
        self.logger.info(f"Grouped {result.valid_records} valid records into {len(valid_orders)} orders")
        self.logger.info(f"Skipped {self._skipped_records} records due to missing product references")
        
        # Step 2: Calculate co-occurrences within orders (including F-gin enhancements)
        enhanced_orders = self._enhance_orders_with_f_gin(valid_orders)
        co_occurrences = self._calculate_co_occurrences(enhanced_orders)
        self.logger.info(f"Calculated {len(co_occurrences)} product co-occurrences")
        
        # Step 3: Create Transaction and Customer nodes for detailed analysis
        self._create_transaction_nodes(valid_orders)
        
        # Step 4: Create CO_OCCURS relationships in Neo4j
        if co_occurrences:
            self._create_co_occurrence_relationships(co_occurrences)
        
        # Step 5: Create indexes for performance
        self.create_indexes()
        
        result.is_valid = True  # Always valid since we skip problematic records
        
        self.logger.info(f"Sales data loading completed:")
        self.logger.info(f"  Valid records: {result.valid_records}")
        self.logger.info(f"  Skipped records: {self._skipped_records}")
        self.logger.info(f"  Missing product references: {len(result.missing_references)}")
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
                    'primary_facility': list(data['facilities'])[0] if data['facilities'] else '',
                    'all_facilities': list(data['facilities']),
                    'all_warehouses': list(data['warehouses']),
                    'transaction_count': data['transaction_count'],
                    'product_categories': list(data['categories']),
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
                c.transaction_count = customer.transaction_count,
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
        """Create performance indexes for sales queries"""
        indexes = [
            # CO_OCCURS relationship indexes
            "CREATE INDEX co_occurs_frequency_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.frequency)",
            "CREATE INDEX co_occurs_confidence_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.confidence_score)",
            "CREATE INDEX co_occurs_date_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.last_occurrence_date)",
            
            # Customer node indexes
            "CREATE INDEX customer_name_index IF NOT EXISTS FOR (c:Customer) ON (c.name)",
            "CREATE INDEX customer_facility_index IF NOT EXISTS FOR (c:Customer) ON (c.primary_facility)",
            "CREATE INDEX customer_transaction_count_index IF NOT EXISTS FOR (c:Customer) ON (c.transaction_count)",
            
            # Transaction node indexes
            "CREATE INDEX transaction_order_index IF NOT EXISTS FOR (t:Transaction) ON (t.order_id)",
            "CREATE INDEX transaction_facility_index IF NOT EXISTS FOR (t:Transaction) ON (t.facility)",
            "CREATE INDEX transaction_warehouse_index IF NOT EXISTS FOR (t:Transaction) ON (t.warehouse)",
            "CREATE INDEX transaction_category_index IF NOT EXISTS FOR (t:Transaction) ON (t.category)"
        ]
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Created index: {index_query}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")
    
    def get_sales_statistics(self) -> Dict:
        """Get comprehensive sales statistics"""
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            stats_query = """
            MATCH (p:Product)
            OPTIONAL MATCH (p)-[c:CO_OCCURS]->()
            RETURN 
                count(DISTINCT p) as products_with_sales_data,
                count(c) as total_co_occurrences,
                avg(c.frequency) as avg_co_occurrence_frequency,
                max(c.frequency) as max_co_occurrence_frequency,
                avg(c.confidence_score) as avg_confidence_score
            """
            
            result = session.run(stats_query)
            stats = result.single()
            
            # Get top co-occurring products
            top_pairs_query = """
            MATCH (p1:Product)-[c:CO_OCCURS]->(p2:Product)
            WHERE p1.gin < p2.gin  // Avoid duplicates
            RETURN p1.gin as product1, p2.gin as product2, c.frequency as frequency
            ORDER BY c.frequency DESC
            LIMIT 10
            """
            
            top_pairs_result = session.run(top_pairs_query)
            top_pairs = [
                {
                    'product1': record['product1'],
                    'product2': record['product2'], 
                    'frequency': record['frequency']
                }
                for record in top_pairs_result
            ]
            
            return {
                'products_with_sales_data': stats['products_with_sales_data'],
                'total_co_occurrences': stats['total_co_occurrences'],
                'avg_co_occurrence_frequency': stats['avg_co_occurrence_frequency'],
                'max_co_occurrence_frequency': stats['max_co_occurrence_frequency'],
                'avg_confidence_score': stats['avg_confidence_score'],
                'top_co_occurring_pairs': top_pairs,
                'skipped_records': self._skipped_records,
                'missing_product_references': len(getattr(self, '_missing_references', set()))
            }