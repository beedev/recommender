"""
Base Loader Infrastructure
Bharath's Quality-First Implementation

This module provides the foundation for all data loaders with:
- Idempotent loading (can run multiple times safely)
- Comprehensive validation and error reporting
- Transaction safety with rollback capabilities
- Detailed logging and progress tracking
- Reference validation between datasets
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from neo4j import GraphDatabase
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ValidationResult:
    """Comprehensive validation result with detailed error reporting"""
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skipped_records: List[Dict] = field(default_factory=list)
    missing_references: Set[str] = field(default_factory=set)
    duplicate_keys: Set[str] = field(default_factory=set)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.valid_records / self.total_records) * 100.0
    
    def add_error(self, message: str, record_id: str = None):
        """Add error with optional record context"""
        error_msg = f"Record {record_id}: {message}" if record_id else message
        self.errors.append(error_msg)
    
    def add_warning(self, message: str, record_id: str = None):
        """Add warning with optional record context"""
        warning_msg = f"Record {record_id}: {message}" if record_id else message
        self.warnings.append(warning_msg)


class BaseLoader(ABC):
    """
    Abstract base class for all data loaders
    
    Provides common functionality:
    - Database connections (Neo4j + PostgreSQL)
    - File handling and validation
    - Transaction management
    - Logging and error reporting
    - Reference validation
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 postgres_config: Dict[str, str] = None):
        """
        Initialize loader with database connections
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username  
            neo4j_password: Neo4j password
            postgres_config: PostgreSQL connection config (optional)
        """
        self.logger = self._setup_logging()
        
        # Neo4j connection - require explicit database configuration
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        self.neo4j_database = os.getenv('NEO4J_DATABASE')
        if not self.neo4j_database:
            raise ValueError("NEO4J_DATABASE environment variable is required but not set")
        
        # PostgreSQL connection (optional)
        self.postgres_conn = None
        if postgres_config:
            self.postgres_conn = psycopg2.connect(**postgres_config)
        
        # Product catalog cache for reference validation
        self._product_catalog: Set[str] = set()
        self._load_product_catalog_cache()
        
        # Statistics tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_processed': 0,
            'successful_loads': 0,
            'failed_loads': 0,
            'skipped_records': 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for the loader"""
        logger = logging.getLogger(f"{self.__class__.__name__}")
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
        log_file = Path(f"logs/{self.__class__.__name__.lower()}.log")
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_product_catalog_cache(self):
        """Load product catalog GINs for reference validation"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run("MATCH (p:Product) RETURN p.gin as gin")
                self._product_catalog = {record["gin"] for record in result}
                self.logger.info(f"Loaded {len(self._product_catalog)} products for reference validation")
        except Exception as e:
            self.logger.warning(f"Could not load product catalog cache: {e}")
            # Try to load from JSON file as fallback
            try:
                products_file = Path("neo4j_datasets/enhanced_simplified_products.json")
                if products_file.exists():
                    with open(products_file, 'r') as f:
                        products_data = json.load(f)
                        self._product_catalog = {
                            product['gin_number'] for product in products_data
                            if product.get('gin_number')
                        }
                    self.logger.info(f"Loaded {len(self._product_catalog)} products from JSON fallback")
            except Exception as fallback_error:
                self.logger.warning(f"Fallback product loading failed: {fallback_error}")
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate JSON file structure and basic requirements
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(is_valid=False, total_records=0, valid_records=0, invalid_records=0)
        
        if not file_path.exists():
            result.add_error(f"File not found: {file_path}")
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate JSON structure
            validation_result = self._validate_json_structure(data, file_path)
            return validation_result
            
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON format: {e}")
            return result
        except Exception as e:
            result.add_error(f"File validation error: {e}")
            return result
    
    @abstractmethod
    def _validate_json_structure(self, data: Any, file_path: Path) -> ValidationResult:
        """
        Validate the specific JSON structure for this loader type
        Must be implemented by each loader subclass
        """
        pass
    
    def validate_product_references(self, gin_numbers: List[str], 
                                  context: str = "") -> Tuple[List[str], List[str]]:
        """
        Validate that GIN numbers exist in product catalog
        
        Args:
            gin_numbers: List of GIN numbers to validate
            context: Context for error reporting
            
        Returns:
            Tuple of (valid_gins, invalid_gins)
        """
        valid_gins = []
        invalid_gins = []
        
        for gin in gin_numbers:
            if gin in self._product_catalog:
                valid_gins.append(gin)
            else:
                invalid_gins.append(gin)
                self.logger.warning(f"{context}: Invalid GIN reference: {gin}")
        
        return valid_gins, invalid_gins
    
    def load_data(self, file_path: Path, validate_references: bool = True) -> ValidationResult:
        """
        Main data loading method with comprehensive validation and error handling
        
        Args:
            file_path: Path to data file
            validate_references: Whether to validate product references
            
        Returns:
            ValidationResult with loading statistics
        """
        self.logger.info(f"Starting data load from: {file_path}")
        self.stats['start_time'] = datetime.now()
        
        # Step 1: Validate file
        validation_result = self.validate_file(file_path)
        if not validation_result.is_valid:
            self.logger.error(f"File validation failed: {validation_result.errors}")
            return validation_result
        
        # Step 2: Load and process data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Step 3: Execute loader-specific processing
            processing_result = self._process_data(data, validate_references)
            
            # Step 4: Log final statistics
            self.stats['end_time'] = datetime.now()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            self.logger.info(f"Data loading completed in {duration}")
            self.logger.info(f"Success rate: {processing_result.success_rate:.1f}%")
            self.logger.info(f"Valid records: {processing_result.valid_records}")
            self.logger.info(f"Invalid records: {processing_result.invalid_records}")
            
            if processing_result.errors:
                self.logger.error(f"Errors encountered: {len(processing_result.errors)}")
                for error in processing_result.errors[:10]:  # Log first 10 errors
                    self.logger.error(f"  - {error}")
            
            if processing_result.warnings:
                self.logger.warning(f"Warnings: {len(processing_result.warnings)}")
                for warning in processing_result.warnings[:5]:  # Log first 5 warnings
                    self.logger.warning(f"  - {warning}")
            
            return processing_result
            
        except Exception as e:
            self.logger.error(f"Data loading failed: {e}")
            validation_result.add_error(f"Loading failed: {e}")
            return validation_result
    
    @abstractmethod 
    def _process_data(self, data: Any, validate_references: bool) -> ValidationResult:
        """
        Process the loaded data - must be implemented by subclasses
        
        Args:
            data: Loaded JSON data
            validate_references: Whether to validate product references
            
        Returns:
            ValidationResult with processing statistics
        """
        pass
    
    def create_indexes(self):
        """Create database indexes for performance - implemented by subclasses if needed"""
        pass
    
    def cleanup_old_data(self, backup_first: bool = True):
        """Cleanup old data before loading - implemented by subclasses if needed"""
        pass
    
    def close_connections(self):
        """Close all database connections"""
        try:
            if self.neo4j_driver:
                self.neo4j_driver.close()
                self.logger.info("Neo4j connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Neo4j connection: {e}")
        
        try:
            if self.postgres_conn:
                self.postgres_conn.close()
                self.logger.info("PostgreSQL connection closed")
        except Exception as e:
            self.logger.error(f"Error closing PostgreSQL connection: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with connection cleanup"""
        self.close_connections()
        
        if exc_type is not None:
            self.logger.error(f"Exception during loading: {exc_type.__name__}: {exc_val}")
        
        return False  # Don't suppress exceptions
    
    def generate_loading_report(self, validation_result: ValidationResult, 
                              output_file: Optional[Path] = None) -> str:
        """
        Generate comprehensive loading report
        
        Args:
            validation_result: Result from data loading
            output_file: Optional file to write report to
            
        Returns:
            Report as string
        """
        report_lines = [
            f"=== {self.__class__.__name__} Loading Report ===",
            f"Timestamp: {datetime.now().isoformat()}",
            f"",
            f"SUMMARY:",
            f"  Total Records: {validation_result.total_records}",
            f"  Valid Records: {validation_result.valid_records}",
            f"  Invalid Records: {validation_result.invalid_records}",
            f"  Success Rate: {validation_result.success_rate:.1f}%",
            f"  Processing Time: {(self.stats.get('end_time') or datetime.now()) - (self.stats.get('start_time') or datetime.now())}",
            f""
        ]
        
        if validation_result.errors:
            report_lines.extend([
                f"ERRORS ({len(validation_result.errors)}):",
                *[f"  - {error}" for error in validation_result.errors],
                f""
            ])
        
        if validation_result.warnings:
            report_lines.extend([
                f"WARNINGS ({len(validation_result.warnings)}):",
                *[f"  - {warning}" for warning in validation_result.warnings[:20]],  # Limit warnings
                f""
            ])
        
        if validation_result.missing_references:
            report_lines.extend([
                f"MISSING PRODUCT REFERENCES ({len(validation_result.missing_references)}):",
                *[f"  - {gin}" for gin in sorted(validation_result.missing_references)],
                f""
            ])
        
        if validation_result.duplicate_keys:
            report_lines.extend([
                f"DUPLICATE KEYS ({len(validation_result.duplicate_keys)}):",
                *[f"  - {key}" for key in sorted(validation_result.duplicate_keys)],
                f""
            ])
        
        report = "\\n".join(report_lines)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
            self.logger.info(f"Loading report written to: {output_file}")
        
        return report