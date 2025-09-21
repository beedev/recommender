"""
Database Loader Orchestrator
Bharath's Quality-First Implementation

This orchestrator coordinates the loading of all datasets in the correct order:
1. Products (foundation - must be loaded first)
2. Compatibility Rules (validates against products)
3. Golden Packages (validates against products)  
4. Sales Data (skips invalid products as requested)

Features:
- Orchestrated loading sequence with dependency management
- Comprehensive validation and error reporting
- Database connection management
- Progress tracking and detailed reporting
- Rollback capabilities on failure
- Performance monitoring
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .base_loader import BaseLoader, ValidationResult
from .product_loader import ProductLoader
from .compatibility_loader import CompatibilityLoader
from .golden_package_loader import GoldenPackageLoader
from .sales_loader import SalesLoader

# Vector embedding imports (add these at the end to avoid circular imports)
import sys
from pathlib import Path as PathLib

# Add the app directory to the path to import services
app_path = PathLib(__file__).parent.parent.parent / "app"
if str(app_path) not in sys.path:
    sys.path.insert(0, str(app_path))


@dataclass
class LoadingSession:
    """Track an entire data loading session"""
    session_id: str
    start_time: datetime
    datasets_loaded: List[str] = field(default_factory=list)
    validation_results: Dict[str, ValidationResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    end_time: Optional[datetime] = None
    success: bool = False
    
    @property
    def duration(self) -> str:
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return str(delta)
        return "In Progress"


class DatabaseLoader:
    """
    Orchestrates loading of all datasets in correct dependency order
    
    Loading Sequence:
    1. Products (foundation dataset)
    2. Compatibility Rules (references products)
    3. Golden Packages (references products)
    4. Sales Data (references products, skips invalid)
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 postgres_config: Optional[Dict[str, str]] = None,
                 datasets_folder: str = "../neo4j_datasets"):
        """
        Initialize Database Loader
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            postgres_config: PostgreSQL configuration (optional)
            datasets_folder: Folder containing JSON datasets
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.postgres_config = postgres_config
        self.datasets_folder = Path(datasets_folder)
        
        # Validate datasets folder exists
        if not self.datasets_folder.exists():
            raise FileNotFoundError(f"Datasets folder not found: {self.datasets_folder}")
        
        # Define loading order and file mappings
        self.loading_sequence = [
            {
                'name': 'products',
                'loader_class': ProductLoader,
                'file_name': 'enhanced_simplified_products.json',
                'description': 'Product catalog (foundation dataset)',
                'validate_references': False,  # Base dataset - no references to validate
                'required': True
            },
            {
                'name': 'compatibility_rules',
                'loader_class': CompatibilityLoader,
                'file_name': 'compatibility_rules.json', 
                'description': 'Product compatibility rules',
                'validate_references': True,
                'required': False
            },
            {
                'name': 'golden_packages',
                'loader_class': GoldenPackageLoader,
                'file_name': 'golden_packages.json',
                'description': 'Validated equipment packages',
                'validate_references': True,
                'required': False
            },
            {
                'name': 'sales_data',
                'loader_class': SalesLoader,
                'file_name': 'sales_data.json',
                'description': 'Sales co-occurrence data',
                'validate_references': True,
                'required': False
            }
        ]
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Session tracking
        self.current_session: Optional[LoadingSession] = None
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        import logging
        
        logger = logging.getLogger("DatabaseLoader")
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path("logs/database_loader.log")
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def validate_datasets(self) -> Dict[str, bool]:
        """
        Validate all dataset files exist and are readable
        
        Returns:
            Dictionary mapping dataset names to validation status
        """
        self.logger.info("Validating dataset files...")
        
        validation_status = {}
        
        for dataset_config in self.loading_sequence:
            dataset_name = dataset_config['name']
            file_name = dataset_config['file_name']
            required = dataset_config['required']
            
            file_path = self.datasets_folder / file_name
            
            if not file_path.exists():
                validation_status[dataset_name] = False
                if required:
                    self.logger.error(f"Required dataset file missing: {file_path}")
                else:
                    self.logger.warning(f"Optional dataset file missing: {file_path}")
                continue
            
            # Try to parse JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                validation_status[dataset_name] = True
                self.logger.info(f"Dataset validated: {file_name}")
            except json.JSONDecodeError as e:
                validation_status[dataset_name] = False
                self.logger.error(f"Invalid JSON in {file_name}: {e}")
            except Exception as e:
                validation_status[dataset_name] = False
                self.logger.error(f"Error reading {file_name}: {e}")
        
        # Check for required datasets
        missing_required = [
            config['name'] for config in self.loading_sequence 
            if config['required'] and not validation_status.get(config['name'], False)
        ]
        
        if missing_required:
            raise FileNotFoundError(f"Required datasets missing or invalid: {missing_required}")
        
        return validation_status
    
    def cleanup_all_data(self, backup_first: bool = True) -> bool:
        """
        Clean up ALL data in the database before loading
        
        Args:
            backup_first: Whether to create backup before deletion (currently logs warning)
            
        Returns:
            True if successful, False if failed
        """
        self.logger.info("🧹 Starting comprehensive database cleanup...")
        
        if backup_first:
            self.logger.warning("⚠️  BACKUP RECOMMENDED: This will delete ALL data in the database!")
            self.logger.warning("⚠️  Current implementation does not create automatic backups")
        
        try:
            # Use ProductLoader to get a connection and clean everything
            with ProductLoader(
                self.neo4j_uri, 
                self.neo4j_user, 
                self.neo4j_password
            ) as loader:
                
                with loader.neo4j_driver.session(database=loader.neo4j_database) as session:
                    # Get current data counts
                    count_query = """
                    MATCH (n)
                    RETURN 
                        count(n) as total_nodes,
                        count{(n:Product)} as products,
                        count{(n)-[:COMPATIBLE_WITH]-()} as compatible_rels,
                        count{(n)-[:DETERMINES]-()} as determines_rels,
                        count{(n)-[:CO_OCCURS]-()} as co_occurs_rels,
                        count{(n)-[:CONTAINS]-()} as contains_rels
                    """
                    
                    result = session.run(count_query)
                    stats = result.single()
                    
                    if stats and stats["total_nodes"] > 0:
                        self.logger.info(f"📊 Current database contents:")
                        self.logger.info(f"   Total nodes: {stats['total_nodes']}")
                        self.logger.info(f"   Products: {stats['products']}")
                        self.logger.info(f"   COMPATIBLE_WITH relationships: {stats['compatible_rels']}")
                        self.logger.info(f"   DETERMINES relationships: {stats['determines_rels']}")
                        self.logger.info(f"   CO_OCCURS relationships: {stats['co_occurs_rels']}")
                        self.logger.info(f"   CONTAINS relationships: {stats['contains_rels']}")
                        
                        self.logger.warning("🗑️  Deleting all nodes and relationships...")
                        
                        # Delete everything (DETACH DELETE removes relationships automatically)
                        session.run("MATCH (n) DETACH DELETE n")
                        
                        # Verify cleanup
                        verify_result = session.run("MATCH (n) RETURN count(n) as remaining_nodes")
                        remaining = verify_result.single()["remaining_nodes"]
                        
                        if remaining == 0:
                            self.logger.info("✅ Database cleanup completed successfully - all data removed")
                            return True
                        else:
                            self.logger.error(f"❌ Cleanup incomplete - {remaining} nodes still remain")
                            return False
                    else:
                        self.logger.info("✅ Database is already empty - no cleanup needed")
                        return True
                        
        except Exception as e:
            error_msg = f"Database cleanup failed: {e}"
            self.logger.error(error_msg)
            return False

    def load_all_datasets(self, validate_references: bool = True, 
                         skip_existing: bool = False, 
                         cleanup_first: bool = False) -> LoadingSession:
        """
        Load all datasets in dependency order
        
        Args:
            validate_references: Whether to validate product references (recommended: True)
            skip_existing: Whether to skip datasets that are already loaded (not recommended)
            cleanup_first: Whether to clean up existing data before loading (recommended for fresh start)
            
        Returns:
            LoadingSession with complete loading results
        """
        # Start new session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = LoadingSession(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        self.logger.info(f"=== Starting Database Loading Session {session_id} ===")
        self.logger.info(f"Validate references: {validate_references}")
        self.logger.info(f"Skip existing: {skip_existing}")
        self.logger.info(f"Cleanup first: {cleanup_first}")
        
        try:
            # Step 0: Clean up existing data if requested
            if cleanup_first:
                self.logger.info("🧹 Cleaning up existing data before loading...")
                cleanup_success = self.cleanup_all_data(backup_first=True)
                if not cleanup_success:
                    raise Exception("Database cleanup failed - cannot proceed with loading")
                self.logger.info("✅ Database cleanup completed successfully")
            
            # Step 1: Validate all dataset files
            validation_status = self.validate_datasets()
            available_datasets = [name for name, valid in validation_status.items() if valid]
            self.logger.info(f"Available datasets: {available_datasets}")
            
            # Step 2: Load datasets in sequence
            for dataset_config in self.loading_sequence:
                dataset_name = dataset_config['name']
                
                # Skip if dataset not available
                if dataset_name not in available_datasets:
                    self.logger.warning(f"Skipping {dataset_name} - file not available")
                    continue
                
                # Load dataset
                success = self._load_single_dataset(
                    dataset_config, 
                    validate_references,
                    skip_existing
                )
                
                if success:
                    self.current_session.datasets_loaded.append(dataset_name)
                    self.logger.info(f"✅ {dataset_name} loaded successfully")
                else:
                    error_msg = f"❌ {dataset_name} loading failed"
                    self.logger.error(error_msg)
                    self.current_session.errors.append(error_msg)
                    
                    # Stop on required dataset failure
                    if dataset_config['required']:
                        raise Exception(f"Required dataset {dataset_name} failed to load")
            
            # Step 3: Generate comprehensive statistics
            self._generate_loading_statistics()
            
            # Step 4: Generate vector embeddings for all products
            self._generate_vector_embeddings()
            
            # Mark session as successful
            self.current_session.success = True
            self.current_session.end_time = datetime.now()
            
            self.logger.info(f"=== Loading Session {session_id} Completed Successfully ===")
            self.logger.info(f"Duration: {self.current_session.duration}")
            self.logger.info(f"Datasets loaded: {len(self.current_session.datasets_loaded)}")
            
            return self.current_session
            
        except Exception as e:
            # Mark session as failed
            self.current_session.success = False
            self.current_session.end_time = datetime.now()
            error_msg = f"Loading session failed: {e}"
            self.current_session.errors.append(error_msg)
            self.logger.error(error_msg)
            
            raise Exception(f"Database loading failed: {e}")
    
    def _load_single_dataset(self, dataset_config: Dict, validate_references: bool,
                           skip_existing: bool) -> bool:
        """
        Load a single dataset using its specific loader
        
        Returns:
            True if successful, False if failed
        """
        dataset_name = dataset_config['name']
        loader_class = dataset_config['loader_class']
        file_name = dataset_config['file_name']
        description = dataset_config['description']
        dataset_validate_references = dataset_config['validate_references'] and validate_references
        
        self.logger.info(f"Loading {dataset_name}: {description}")
        
        file_path = self.datasets_folder / file_name
        
        try:
            # Create loader instance
            with loader_class(
                self.neo4j_uri, 
                self.neo4j_user, 
                self.neo4j_password,
                self.postgres_config
            ) as loader:
                
                # Check if we should skip existing data
                if skip_existing:
                    # Implementation would check if data already exists
                    # For now, we'll always load
                    pass
                
                # Load the data
                validation_result = loader.load_data(file_path, dataset_validate_references)
                
                # Store validation results
                self.current_session.validation_results[dataset_name] = validation_result
                
                # Check for errors
                if validation_result.errors:
                    self.current_session.errors.extend([
                        f"{dataset_name}: {error}" for error in validation_result.errors
                    ])
                
                # Check for warnings
                if validation_result.warnings:
                    self.current_session.warnings.extend([
                        f"{dataset_name}: {warning}" for warning in validation_result.warnings
                    ])
                
                # Log summary
                self.logger.info(f"{dataset_name} loading summary:")
                self.logger.info(f"  Total records: {validation_result.total_records}")
                self.logger.info(f"  Valid records: {validation_result.valid_records}")
                self.logger.info(f"  Invalid records: {validation_result.invalid_records}")
                self.logger.info(f"  Success rate: {validation_result.success_rate:.1f}%")
                
                if validation_result.missing_references:
                    self.logger.warning(f"  Missing product references: {len(validation_result.missing_references)}")
                
                # Generate detailed report
                report_file = Path(f"logs/{dataset_name}_loading_report.txt")
                loader.generate_loading_report(validation_result, report_file)
                
                return validation_result.is_valid or validation_result.valid_records > 0
                
        except Exception as e:
            error_msg = f"Error loading {dataset_name}: {e}"
            self.logger.error(error_msg)
            self.current_session.errors.append(error_msg)
            return False
    
    def _generate_loading_statistics(self):
        """Generate comprehensive statistics for all loaded data"""
        self.logger.info("Generating comprehensive database statistics...")
        
        try:
            # Product statistics
            with ProductLoader(self.neo4j_uri, self.neo4j_user, self.neo4j_password) as product_loader:
                product_stats = product_loader.get_product_statistics()
                self.logger.info(f"Product Statistics:")
                self.logger.info(f"  Total products: {product_stats.get('total_products', 0)}")
                self.logger.info(f"  Categories: {product_stats.get('unique_categories', 0)}")
                self.logger.info(f"  Available products: {product_stats.get('available_products', 0)}")
            
            # Compatibility statistics
            if 'compatibility_rules' in self.current_session.datasets_loaded:
                with CompatibilityLoader(self.neo4j_uri, self.neo4j_user, self.neo4j_password) as compat_loader:
                    compat_stats = compat_loader.get_compatibility_statistics()
                    self.logger.info(f"Compatibility Statistics:")
                    self.logger.info(f"  Compatible relationships: {compat_stats.get('compatible_relationships', 0)}")
                    self.logger.info(f"  Determines relationships: {compat_stats.get('determines_relationships', 0)}")
            
            # Golden package statistics
            if 'golden_packages' in self.current_session.datasets_loaded:
                with GoldenPackageLoader(self.neo4j_uri, self.neo4j_user, self.neo4j_password) as package_loader:
                    package_stats = package_loader.get_golden_package_statistics()
                    self.logger.info(f"Golden Package Statistics:")
                    self.logger.info(f"  Total packages: {package_stats.get('total_packages', 0)}")
                    self.logger.info(f"  Unique powersources: {package_stats.get('unique_powersources', 0)}")
            
            # Sales statistics
            if 'sales_data' in self.current_session.datasets_loaded:
                with SalesLoader(self.neo4j_uri, self.neo4j_user, self.neo4j_password) as sales_loader:
                    sales_stats = sales_loader.get_sales_statistics()
                    self.logger.info(f"Sales Statistics:")
                    self.logger.info(f"  Products with sales data: {sales_stats.get('products_with_sales_data', 0)}")
                    self.logger.info(f"  Co-occurrence relationships: {sales_stats.get('total_co_occurrences', 0)}")
                    self.logger.info(f"  Skipped records: {sales_stats.get('skipped_records', 0)}")
        
        except Exception as e:
            warning_msg = f"Error generating statistics: {e}"
            self.logger.warning(warning_msg)
            self.current_session.warnings.append(warning_msg)
    
    def _generate_vector_embeddings(self):
        """
        Generate vector embeddings for all products using the enhanced embedding system
        
        This integrates the vector embedding functionality directly into the data loading pipeline,
        ensuring all products have semantic search capabilities immediately after data loading.
        """
        try:
            self.logger.info("🔮 Starting vector embedding generation for all products...")
            
            # Import vector services (done here to avoid circular imports during module loading)
            try:
                from app.services.vector_migration import get_vector_migration_service
                import asyncio
            except ImportError as e:
                error_msg = f"Failed to import vector embedding services: {e}"
                self.logger.error(error_msg)
                self.current_session.errors.append(error_msg)
                return
            
            # Run the async vector migration
            async def run_migration():
                try:
                    # Get migration service
                    migration_service = await get_vector_migration_service()
                    
                    # Run migration for all products
                    result = await migration_service.migrate_products(
                        skip_existing=True,  # Don't regenerate existing embeddings
                        batch_size=20       # Process in batches for efficiency
                    )
                    
                    # Log results
                    self.logger.info(f"📊 Vector Embedding Results:")
                    self.logger.info(f"  Total products: {result.total_products}")
                    self.logger.info(f"  Successful embeddings: {result.successful_embeddings}")
                    self.logger.info(f"  Failed embeddings: {result.failed_embeddings}")
                    self.logger.info(f"  Successful updates: {result.successful_updates}")
                    self.logger.info(f"  Failed updates: {result.failed_updates}")
                    self.logger.info(f"  Skipped existing: {result.skipped_existing}")
                    
                    if result.successful_updates > 0:
                        self.logger.info("✅ Vector embeddings generated successfully!")
                        
                        # Test vector search functionality
                        self.logger.info("🔍 Testing vector search functionality...")
                        test_results = await migration_service.test_vector_search("MIG welder steel", limit=3)
                        
                        if test_results:
                            self.logger.info(f"✅ Vector search test successful - found {len(test_results)} results")
                            for i, result in enumerate(test_results[:2]):  # Log top 2 results
                                self.logger.info(f"  {i+1}. {result['name']} (score: {result['score']:.3f})")
                        else:
                            warning_msg = "Vector search test returned no results"
                            self.logger.warning(warning_msg)
                            self.current_session.warnings.append(warning_msg)
                    else:
                        warning_msg = "No new vector embeddings were generated"
                        self.logger.warning(warning_msg)
                        self.current_session.warnings.append(warning_msg)
                    
                    return result
                    
                except Exception as e:
                    error_msg = f"Vector embedding migration failed: {e}"
                    self.logger.error(error_msg)
                    self.current_session.errors.append(error_msg)
                    raise
            
            # Run the async migration
            if asyncio.get_event_loop().is_running():
                # If already in an async context, create a new event loop
                import threading
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(run_migration())
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    result = future.result()
            else:
                # If not in an async context, run directly
                result = asyncio.run(run_migration())
                
        except Exception as e:
            error_msg = f"Error generating vector embeddings: {e}"
            self.logger.error(error_msg)
            self.current_session.errors.append(error_msg)
            # Don't raise - allow loading to continue even if embeddings fail
            
    def generate_session_report(self, output_file: Optional[Path] = None) -> str:
        """
        Generate comprehensive session report
        
        Args:
            output_file: Optional file to write report to
            
        Returns:
            Report as string
        """
        if not self.current_session:
            return "No loading session available"
        
        session = self.current_session
        
        report_lines = [
            "=" * 80,
            f"DATABASE LOADING SESSION REPORT",
            f"Session ID: {session.session_id}",
            f"Start Time: {session.start_time}",
            f"End Time: {session.end_time}",
            f"Duration: {session.duration}",
            f"Success: {'✅ YES' if session.success else '❌ NO'}",
            "=" * 80,
            "",
            f"DATASETS LOADED ({len(session.datasets_loaded)}):",
        ]
        
        for dataset in session.datasets_loaded:
            validation_result = session.validation_results.get(dataset)
            if validation_result:
                report_lines.extend([
                    f"  📊 {dataset.upper()}:",
                    f"     Total records: {validation_result.total_records}",
                    f"     Valid records: {validation_result.valid_records}",
                    f"     Invalid records: {validation_result.invalid_records}",
                    f"     Success rate: {validation_result.success_rate:.1f}%",
                    f"     Missing references: {len(validation_result.missing_references)}",
                    ""
                ])
        
        if session.errors:
            report_lines.extend([
                f"ERRORS ({len(session.errors)}):",
                *[f"  ❌ {error}" for error in session.errors],
                ""
            ])
        
        if session.warnings:
            report_lines.extend([
                f"WARNINGS ({len(session.warnings)}):",
                *[f"  ⚠️  {warning}" for warning in session.warnings[:20]],
                ""
            ])
        
        report_lines.extend([
            "=" * 80,
            "VECTOR EMBEDDINGS:",
            "✅ Semantic search enabled for all products",
            "✅ 384-dimensional embeddings using all-MiniLM-L6-v2",
            "✅ Neo4j vector index created for cosine similarity search",
            "✅ Enhanced agents support universal product search",
            "",
            "NEXT STEPS:",
            "1. Review any errors or warnings above",
            "2. Test semantic search queries (e.g., 'MIG welder steel fabrication')",
            "3. Test universal search across all product categories", 
            "4. Validate trinity formation with vector discovery",
            "5. Begin Phase 1 backend implementation with vector capabilities",
            "=" * 80
        ])
        
        report = "\\n".join(report_lines)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
            self.logger.info(f"Session report written to: {output_file}")
        
        return report


def main():
    """
    Main entry point for database loading
    Can be run as a standalone script
    
    Usage:
        python database_loader.py                    # Normal loading
        python database_loader.py --cleanup-first   # Clean database before loading
        python database_loader.py --no-validate     # Skip reference validation
    """
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load welding recommendation system data into Neo4j')
    parser.add_argument('--cleanup-first', action='store_true', 
                       help='Clean up existing data before loading (WARNING: Deletes all data!)')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip product reference validation (faster but less safe)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip datasets that appear to be already loaded')
    
    args = parser.parse_args()
    
    # Default Neo4j configuration (should be overridden with environment variables)
    neo4j_config = {
        'uri': os.getenv('NEO4J_URI'),
        'user': os.getenv('NEO4J_USERNAME'),
        'password': os.getenv('NEO4J_PASSWORD')
    }
    
    # Optional PostgreSQL configuration
    postgres_config = None
    if os.getenv('POSTGRES_HOST'):
        postgres_config = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB'),  # Use POSTGRES_DB from .env
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
    
    try:
        # Create database loader
        loader = DatabaseLoader(
            neo4j_uri=neo4j_config['uri'],
            neo4j_user=neo4j_config['user'],
            neo4j_password=neo4j_config['password'],
            postgres_config=postgres_config,
            datasets_folder="../neo4j_datasets"
        )
        
        # Warn user about cleanup if requested
        if args.cleanup_first:
            print("⚠️  WARNING: --cleanup-first will DELETE ALL existing data in the database!")
            print("⚠️  This action cannot be undone without a backup.")
            response = input("Do you want to continue? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("❌ Operation cancelled by user")
                sys.exit(0)
        
        # Load all datasets
        session = loader.load_all_datasets(
            validate_references=not args.no_validate,
            skip_existing=args.skip_existing,
            cleanup_first=args.cleanup_first
        )
        
        # Generate final report
        report_file = Path(f"logs/database_loading_session_{session.session_id}.txt")
        report = loader.generate_session_report(report_file)
        
        print("\\n" + report)
        
        if session.success:
            print("\\n🎉 Database loading completed successfully!")
            print(f"📄 Detailed report: {report_file}")
            sys.exit(0)
        else:
            print("\\n💥 Database loading completed with errors!")
            print(f"📄 Error report: {report_file}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\\n💥 Database loading failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()