#!/usr/bin/env python3
"""
PowerSource Dataset Orchestrator
===============================

Comprehensive orchestrator that takes PowerSource GIN(s) as input and generates
complete Neo4j-ready datasets through the entire analysis pipeline.

Usage:
    python powersource_orchestrator.py --powersources 0465350883,0465350884
    python powersource_orchestrator.py --config powersources.json
    python powersource_orchestrator.py --add-powersource 0123456789
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import our analysis modules
from powersource_master_extractor import PowerSourceMasterExtractor
from product_catalog_transformer import create_enhanced_simplified_output, load_master_products_from_catalog
from category_consistency_analyzer import CategoryConsistencyAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class PowerSourceOrchestrator:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path("/Users/bharath/Desktop/AgenticAI/Recommender")
        self.datasets_path = self.base_path / "Datasets"
        self.output_path = self.base_path / "neo4j_datasets"
        self.config_file = self.base_path / "powersource_config.json"
        
        # Create output directory
        self.output_path.mkdir(exist_ok=True)
        
        logger.info(f"PowerSource Orchestrator initialized")
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Output path: {self.output_path}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        default_config = {
            "powersources": {
                "0465350883": "Warrior 500i",
                "0465350884": "Warrior 400i", 
                "0445555880": "Warrior 750i 380-460V, CE",
                "0445250880": "Renegade ES 300i with cables",
                "0446200880": "Aristo 500ix"
            },
            "validation_settings": {
                "run_category_consistency": True,
                "require_golden_package_presence": True,
                "min_gin_discovery_threshold": 10
            },
            "output_settings": {
                "generate_simplified_catalog": True,
                "include_synthetic_products": True,
                "create_backup": True
            },
            "last_updated": datetime.now().isoformat()
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except Exception as e:
                logger.warning(f"Error loading config: {e}. Using defaults.")
        
        # Save default config
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save orchestrator configuration"""
        try:
            config["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def validate_powersources(self, powersources: List[str]) -> List[str]:
        """Validate and normalize PowerSource GINs"""
        validated = []
        
        for ps in powersources:
            # Pad to 10 characters
            ps_padded = str(ps).strip().zfill(10)
            
            # Basic validation
            if len(ps_padded) != 10:
                logger.warning(f"Invalid PowerSource GIN format: {ps}")
                continue
            
            if not ps_padded.isdigit():
                logger.warning(f"PowerSource GIN must be numeric: {ps}")
                continue
            
            validated.append(ps_padded)
        
        logger.info(f"Validated {len(validated)} PowerSource GINs: {validated}")
        return validated
    
    def check_prerequisites(self) -> bool:
        """Check if all required source files exist"""
        required_files = [
            self.datasets_path / "ENG.json",
            self.datasets_path / "golden_pkg_format_V2.xlsx",
            self.datasets_path / "sales_data_cleaned.csv",
            self.datasets_path / "Ruleset"
        ]
        
        logger.info("Checking prerequisites...")
        missing_files = []
        
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            logger.error("Missing required files:")
            for file_path in missing_files:
                logger.error(f"  - {file_path}")
            return False
        
        # Check ruleset files
        ruleset_files = list((self.datasets_path / "Ruleset").glob("*.xlsx")) + \
                        list((self.datasets_path / "Ruleset").glob("*.xlsb"))
        
        if len(ruleset_files) == 0:
            logger.error("No ruleset files found in Ruleset directory")
            return False
        
        logger.info(f"✅ All prerequisites met. Found {len(ruleset_files)} ruleset files.")
        return True
    
    def run_category_consistency_check(self) -> bool:
        """Run category consistency analysis"""
        logger.info("🔍 Running category consistency analysis...")
        
        try:
            analyzer = CategoryConsistencyAnalyzer()
            results = analyzer.generate_report()
            
            if not results["can_proceed"]:
                logger.error("❌ Category inconsistencies found. Cannot proceed safely.")
                return False
            
            logger.info("✅ Category consistency verified.")
            return True
            
        except Exception as e:
            logger.error(f"Error in category consistency check: {e}")
            return False
    
    def extract_master_datasets(self, powersources: List[str]) -> bool:
        """Extract master datasets using PowerSource extractor"""
        logger.info("📦 Extracting master datasets...")
        
        try:
            extractor = PowerSourceMasterExtractor(powersources)
            results = extractor.generate_master_datasets()
            
            # Validate results
            if not results:
                logger.error("Master dataset extraction failed")
                return False
            
            total_gins = len(results.get('all_related_gins', []))
            if total_gins < 10:  # Minimum threshold
                logger.warning(f"Only {total_gins} GINs discovered. This seems low.")
            
            logger.info(f"✅ Master datasets extracted successfully")
            logger.info(f"   Discovered {total_gins} unique GINs")
            logger.info(f"   Golden packages: {len(results.get('golden_packages', []))}")
            logger.info(f"   Sales records: {results.get('sales_data', {}).get('metadata', {}).get('total_records', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in master dataset extraction: {e}")
            return False
    
    def generate_simplified_catalog(self) -> bool:
        """Generate simplified product catalog using new single-source approach"""
        logger.info("🔧 Generating simplified product catalog...")
        
        try:
            # Verify product catalog exists
            existing_gins, synthetic_products = load_master_products_from_catalog()
            
            if existing_gins is None:
                logger.error("Failed to load product catalog")
                return False
            
            # Generate simplified catalog (now processes everything from product_catalog.json)
            success = create_enhanced_simplified_output()
            if not success:
                logger.error("Failed to create simplified catalog")
                return False
            
            logger.info("✅ Simplified product catalog generated")
            return True
            
        except Exception as e:
            logger.error(f"Error generating simplified catalog: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create backup of previous datasets"""
        try:
            backup_dir = self.base_path / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy existing datasets to backup
            for file_path in self.output_path.glob("*.json"):
                backup_path = backup_dir / file_path.name
                backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
            
            logger.info(f"✅ Backup created at {backup_dir}")
            return True
            
        except Exception as e:
            logger.warning(f"Backup creation failed: {e}")
            return False
    
    def validate_outputs(self) -> bool:
        """Validate generated datasets"""
        logger.info("🔍 Validating generated datasets...")
        
        required_files = [
            "product_catalog.json",
            "golden_packages.json", 
            "sales_data.json",
            "compatibility_rules.json"
        ]
        
        validation_results = {}
        
        for filename in required_files:
            file_path = self.output_path / filename
            
            if not file_path.exists():
                logger.error(f"Missing output file: {filename}")
                validation_results[filename] = False
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Basic validation
                if 'metadata' not in data:
                    logger.warning(f"{filename}: Missing metadata section")
                    validation_results[filename] = False
                    continue
                
                # File-specific validation
                if filename == "product_catalog.json":
                    products = data.get('products', [])
                    if len(products) < 50:  # Minimum expected
                        logger.warning(f"{filename}: Only {len(products)} products found")
                    validation_results[filename] = len(products) > 0
                
                elif filename == "golden_packages.json":
                    packages = data.get('golden_packages', [])
                    validation_results[filename] = len(packages) > 0
                
                elif filename == "sales_data.json":
                    records = data.get('sales_records', [])
                    validation_results[filename] = len(records) > 0
                
                elif filename == "compatibility_rules.json":
                    # Rules file can be empty initially
                    validation_results[filename] = True
                
            except Exception as e:
                logger.error(f"Error validating {filename}: {e}")
                validation_results[filename] = False
        
        # Summary
        passed = sum(validation_results.values())
        total = len(validation_results)
        
        if passed == total:
            logger.info(f"✅ All {total} output files validated successfully")
            return True
        else:
            logger.error(f"❌ {total - passed} validation failures out of {total} files")
            return False
    
    def generate_summary_report(self, powersources: List[str]) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "powersources": powersources,
            "pipeline_stages": {},
            "dataset_summary": {},
            "validation_results": {},
            "next_steps": []
        }
        
        try:
            # Load dataset metadata
            for filename in ["product_catalog.json", "golden_packages.json", "sales_data.json"]:
                file_path = self.output_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        summary["dataset_summary"][filename] = data.get("metadata", {})
            
            # Add recommendations
            summary["next_steps"] = [
                "Review generated datasets in neo4j_datasets/ directory",
                "Load datasets into Neo4j using provided Cypher scripts",
                "Test recommendation queries against loaded data",
                "Consider implementing compatibility rules extraction"
            ]
            
            # Save summary
            summary_path = self.output_path / "generation_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Summary report saved to {summary_path}")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
        
        return summary
    
    def cleanup_output_directory(self):
        """Clean up neo4j_datasets directory before each run"""
        try:
            if self.output_path.exists():
                logger.info("🧹 Cleaning up neo4j_datasets directory...")
                import shutil
                shutil.rmtree(self.output_path)
                logger.info("✅ Cleaned up neo4j_datasets directory")
            
            # Recreate the directory
            self.output_path.mkdir(parents=True, exist_ok=True)
            logger.info("📁 Created fresh neo4j_datasets directory")
            
        except Exception as e:
            logger.error(f"Error cleaning up output directory: {e}")
            raise

    def orchestrate(self, powersources: List[str], config: Dict[str, Any] = None) -> bool:
        """Main orchestration method"""
        logger.info("=" * 80)
        logger.info("POWERSOURCE DATASET ORCHESTRATION PIPELINE")
        logger.info("=" * 80)
        
        if not config:
            config = self.load_config()
        
        # Stage 0: Cleanup
        self.cleanup_output_directory()
        
        # Stage 1: Validation
        logger.info("Stage 1: Prerequisites & Validation")
        if not self.check_prerequisites():
            return False
        
        powersources = self.validate_powersources(powersources)
        if not powersources:
            logger.error("No valid PowerSource GINs provided")
            return False
        
        # Stage 2: Backup (optional)
        if config.get("output_settings", {}).get("create_backup", True):
            logger.info("Stage 2: Creating Backup")
            self.create_backup()
        
        # Stage 3: Category Consistency (optional)
        if config.get("validation_settings", {}).get("run_category_consistency", True):
            logger.info("Stage 3: Category Consistency Check")
            if not self.run_category_consistency_check():
                return False
        
        # Stage 4: Master Dataset Extraction
        logger.info("Stage 4: Master Dataset Extraction")
        if not self.extract_master_datasets(powersources):
            return False
        
        # Stage 5: Simplified Catalog Generation (optional)
        if config.get("output_settings", {}).get("generate_simplified_catalog", True):
            logger.info("Stage 5: Simplified Catalog Generation")
            if not self.generate_simplified_catalog():
                return False
        
        # Stage 6: Output Validation
        logger.info("Stage 6: Output Validation")
        if not self.validate_outputs():
            logger.warning("Some validation failures detected, but continuing...")
        
        # Stage 7: Summary Report
        logger.info("Stage 7: Summary Report Generation")
        summary = self.generate_summary_report(powersources)
        
        # Update config with new PowerSources
        for ps in powersources:
            if ps not in config["powersources"]:
                config["powersources"][ps] = f"PowerSource {ps}"
        self.save_config(config)
        
        logger.info("=" * 80)
        logger.info("✅ ORCHESTRATION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Generated datasets available in: {self.output_path}")
        logger.info("Files created:")
        for file_path in self.output_path.glob("*.json"):
            logger.info(f"  - {file_path.name}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="PowerSource Dataset Orchestrator")
    
    # Input methods
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--powersources", type=str, 
                      help="Comma-separated list of PowerSource GINs (e.g., '0465350883,0465350884')")
    group.add_argument("--config", type=str,
                      help="Path to JSON config file with PowerSource list")
    group.add_argument("--add-powersource", type=str,
                      help="Add single PowerSource to existing config")
    
    # Options
    parser.add_argument("--base-path", type=str,
                       default="/Users/bharath/Desktop/AgenticAI/Recommender",
                       help="Base path for the recommender project")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip category consistency validation")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip backup creation")
    parser.add_argument("--no-simplified", action="store_true",
                       help="Skip simplified catalog generation")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = PowerSourceOrchestrator(args.base_path)
    
    # Load configuration
    config = orchestrator.load_config()
    
    # Override config with command line options
    if args.skip_validation:
        config["validation_settings"]["run_category_consistency"] = False
    if args.no_backup:
        config["output_settings"]["create_backup"] = False
    if args.no_simplified:
        config["output_settings"]["generate_simplified_catalog"] = False
    
    # Determine PowerSource list
    powersources = []
    
    if args.powersources:
        powersources = [ps.strip() for ps in args.powersources.split(",")]
    elif args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                powersources = list(config_data.get("powersources", {}).keys())
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            sys.exit(1)
    elif args.add_powersource:
        # Add to existing config
        powersources = list(config["powersources"].keys())
        powersources.append(args.add_powersource)
    
    if not powersources:
        logger.error("No PowerSource GINs provided")
        sys.exit(1)
    
    # Run orchestration
    success = orchestrator.orchestrate(powersources, config)
    
    if success:
        logger.info("🎉 PowerSource dataset generation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 PowerSource dataset generation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()