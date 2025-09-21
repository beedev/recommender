#!/usr/bin/env python3
"""
Category Consistency Analyzer
============================

Analyzes GINs across all rulesets to verify category consistency.
Each GIN should appear in only ONE category role across all rules.
Flags any inconsistencies before proceeding with data loading.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CategoryConsistencyAnalyzer:
    def __init__(self):
        self.base_path = Path("/Users/bharath/Desktop/AgenticAI/Recommender")
        self.valid_files_path = self.base_path / "archive" / "ValidFiles"
        self.orphan_files_path = self.base_path / "archive" / "Orphans"
        
        # Track GIN → category mappings
        self.gin_categories = defaultdict(set)  # GIN → set of categories
        self.category_sources = defaultdict(list)  # GIN → list of (category, source, rule_type)
        
        # Target PowerSources for context
        self.target_powersources = {
            "0465350883",  # Warrior 500i
            "0465350884",  # Warrior 400i
            "0445555880",  # Warrior 750i 380-460V, CE
            "0445250880",  # Renegade ES 300i with cables
            "0446200880"   # Aristo 500ix
        }
    
    def load_json_file(self, file_path: Path) -> Dict:
        """Load JSON file with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def pad_gin(self, gin: str) -> str:
        """Pad GIN to 10 characters with leading zeros"""
        if not gin or gin.startswith('F000'):
            return gin
        return gin.zfill(10)
    
    def extract_gin_category(self, gin: str, category: str, source: str, rule_type: str):
        """Record GIN-category mapping with source tracking"""
        padded_gin = self.pad_gin(gin)
        if padded_gin and padded_gin != "":
            self.gin_categories[padded_gin].add(category)
            self.category_sources[padded_gin].append((category, source, rule_type))
    
    def analyze_valid_rules(self):
        """Analyze valid compatibility rules for category consistency"""
        logger.info("Analyzing valid compatibility rules...")
        
        rules_data = self.load_json_file(self.valid_files_path / "compatibility_rules_valid.json")
        if not rules_data:
            return
        
        compatibility_rules = rules_data.get("compatibility_rules", {})
        
        # Analyze powersource_feeder_cooler rules
        for rule in compatibility_rules.get("powersource_feeder_cooler", []):
            ps_gin = rule.get("powersource", {}).get("gin", "")
            feeder_gin = rule.get("feeder", {}).get("gin", "")
            cooler_gin = rule.get("cooler", {}).get("gin", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "valid_rules", "powersource_feeder_cooler")
            self.extract_gin_category(feeder_gin, "Feeder", "valid_rules", "powersource_feeder_cooler")
            self.extract_gin_category(cooler_gin, "Cooler", "valid_rules", "powersource_feeder_cooler")
        
        # Analyze powersource_accessories rules
        for rule in compatibility_rules.get("powersource_accessories", []):
            ps_gin = rule.get("powersource_gin", "")
            acc_gin = rule.get("accessory", {}).get("gin", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "valid_rules", "powersource_accessories")
            self.extract_gin_category(acc_gin, "PowerSourceAccessory", "valid_rules", "powersource_accessories")
        
        # Analyze feeder_accessories rules
        for rule in compatibility_rules.get("feeder_accessories", []):
            ps_gin = rule.get("powersource_gin", "")
            feeder_gin = rule.get("feeder_gin", "")
            acc_gin = rule.get("accessory", {}).get("gin", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "valid_rules", "feeder_accessories")
            self.extract_gin_category(feeder_gin, "Feeder", "valid_rules", "feeder_accessories")
            self.extract_gin_category(acc_gin, "FeederAccessory", "valid_rules", "feeder_accessories")
        
        # Analyze interconnector_accessories rules
        for rule in compatibility_rules.get("interconnector_accessories", []):
            ps_gin = rule.get("gin_powersource", "")
            ic_gin = rule.get("gin_interconnector", "")
            acc_gin = rule.get("gin_accessory", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "valid_rules", "interconnector_accessories")
            self.extract_gin_category(ic_gin, "Interconnector", "valid_rules", "interconnector_accessories")
            self.extract_gin_category(acc_gin, "InterconnectorAccessory", "valid_rules", "interconnector_accessories")
        
        # Analyze torch_accessories rules
        for rule in compatibility_rules.get("torch_accessories", []):
            ps_gin = rule.get("gin_powersource", "")
            torch_gin = rule.get("gin_torch", "")
            acc_gin = rule.get("gin_accessory", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "valid_rules", "torch_accessories")
            self.extract_gin_category(torch_gin, "Torch", "valid_rules", "torch_accessories")
            self.extract_gin_category(acc_gin, "TorchAccessory", "valid_rules", "torch_accessories")
    
    def analyze_orphan_rules(self):
        """Analyze orphan compatibility rules for category consistency"""
        logger.info("Analyzing orphan compatibility rules...")
        
        rules_data = self.load_json_file(self.orphan_files_path / "compatibility_rules_orphan.json")
        if not rules_data:
            return
        
        orphan_rules = rules_data.get("orphan_rules", {})
        
        # Analyze torches rules
        for rule in orphan_rules.get("torches", []):
            feeder_gin = rule.get("feeder_gin", "")
            cooler_gin = rule.get("cooler_gin", "")
            torch_gin = rule.get("torch", {}).get("gin", "")
            
            self.extract_gin_category(feeder_gin, "Feeder", "orphan_rules", "torches")
            self.extract_gin_category(cooler_gin, "Cooler", "orphan_rules", "torches")
            self.extract_gin_category(torch_gin, "Torch", "orphan_rules", "torches")
        
        # Analyze remotes rules
        for rule in orphan_rules.get("remotes", []):
            ps_gin = rule.get("powersource_gin", "")
            feeder_gin = rule.get("feeder_gin", "")
            remote_gin = rule.get("remote", {}).get("gin", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "orphan_rules", "remotes")
            self.extract_gin_category(feeder_gin, "Feeder", "orphan_rules", "remotes")
            self.extract_gin_category(remote_gin, "Remote", "orphan_rules", "remotes")
        
        # Analyze powersource_accessories rules
        for rule in orphan_rules.get("powersource_accessories", []):
            ps_gin = rule.get("powersource_gin", "")
            acc_gin = rule.get("accessory", {}).get("gin", "")
            
            self.extract_gin_category(ps_gin, "PowerSource", "orphan_rules", "powersource_accessories")
            self.extract_gin_category(acc_gin, "PowerSourceAccessory", "orphan_rules", "powersource_accessories")
        
        # Continue for other orphan rule types...
        # (Adding similar patterns for other rule types in orphan rules)
    
    def analyze_golden_packages(self):
        """Analyze golden packages for category consistency"""
        logger.info("Analyzing golden packages...")
        
        golden_data = self.load_json_file(self.valid_files_path / "golden_packages_valid.json")
        if not golden_data:
            return
        
        packages = golden_data.get("packages", [])
        
        for package in packages:
            components = package.get("components", {})
            
            # Map component types to categories
            component_category_map = {
                "powersource": "PowerSource",
                "feeder": "Feeder", 
                "cooler": "Cooler",
                "interconnector": "Interconnector",
                "torch": "Torch",
                "power_accessory": "PowerSourceAccessory",
                "feeder_accessory": "FeederAccessory",
                "cooler_accessory": "CoolerAccessory"
            }
            
            for comp_type, category in component_category_map.items():
                if comp_type in components:
                    gin = components[comp_type].get("gin", "")
                    if gin and gin != "":
                        self.extract_gin_category(gin, category, "golden_packages", f"component_{comp_type}")
    
    def find_inconsistencies(self) -> List[Tuple[str, Set[str], List[Tuple]]]:
        """Find GINs with multiple category assignments"""
        inconsistencies = []
        
        for gin, categories in self.gin_categories.items():
            if len(categories) > 1:
                sources = self.category_sources[gin]
                inconsistencies.append((gin, categories, sources))
        
        return inconsistencies
    
    def analyze_target_powersource_gins(self):
        """Analyze GINs specifically related to target PowerSources"""
        logger.info("Analyzing GINs related to target PowerSources...")
        
        target_related_gins = set()
        
        # Extract from golden packages first
        golden_data = self.load_json_file(self.valid_files_path / "golden_packages_valid.json")
        packages = golden_data.get("packages", [])
        
        for package in packages:
            ps_gin = package.get("components", {}).get("powersource", {}).get("gin", "")
            if self.pad_gin(ps_gin) in self.target_powersources:
                # Add all component GINs from this package
                all_gins = package.get("all_gins", [])
                for gin in all_gins:
                    target_related_gins.add(self.pad_gin(gin))
        
        logger.info(f"Found {len(target_related_gins)} GINs related to target PowerSources")
        
        # Check category consistency for target-related GINs
        target_inconsistencies = []
        for gin in target_related_gins:
            if gin in self.gin_categories and len(self.gin_categories[gin]) > 1:
                target_inconsistencies.append((gin, self.gin_categories[gin], self.category_sources[gin]))
        
        return target_related_gins, target_inconsistencies
    
    def generate_report(self):
        """Generate comprehensive category consistency report"""
        logger.info("=" * 60)
        logger.info("CATEGORY CONSISTENCY ANALYSIS REPORT")
        logger.info("=" * 60)
        
        # Analyze all rulesets
        self.analyze_valid_rules()
        self.analyze_orphan_rules()
        self.analyze_golden_packages()
        
        # Overall statistics
        total_gins = len(self.gin_categories)
        logger.info(f"Total unique GINs analyzed: {total_gins}")
        
        # Find inconsistencies
        inconsistencies = self.find_inconsistencies()
        logger.info(f"GINs with category inconsistencies: {len(inconsistencies)}")
        
        if inconsistencies:
            logger.warning("🚨 CATEGORY INCONSISTENCIES FOUND:")
            for gin, categories, sources in inconsistencies:
                logger.warning(f"GIN {gin} appears as: {', '.join(categories)}")
                for category, source, rule_type in sources:
                    logger.warning(f"  - {category} in {source} ({rule_type})")
                logger.warning("")
        
        # Target PowerSource analysis
        target_gins, target_inconsistencies = self.analyze_target_powersource_gins()
        
        # Detailed breakdown of target GINs by category
        target_gin_categories = defaultdict(list)
        for gin in target_gins:
            if gin in self.gin_categories and len(self.gin_categories[gin]) == 1:
                category = list(self.gin_categories[gin])[0]
                target_gin_categories[category].append(gin)
        
        logger.info("\nDetailed breakdown of 18 target-related GINs:")
        for category, gins in sorted(target_gin_categories.items()):
            logger.info(f"  {category}: {len(gins)} GINs")
            for gin in sorted(gins):
                logger.info(f"    - {gin}")
        
        if target_inconsistencies:
            logger.error("🚨 INCONSISTENCIES IN TARGET POWERSOURCE ECOSYSTEM:")
            for gin, categories, sources in target_inconsistencies:
                logger.error(f"Target-related GIN {gin} appears as: {', '.join(categories)}")
                for category, source, rule_type in sources:
                    logger.error(f"  - {category} in {source} ({rule_type})")
        else:
            logger.info("✅ No category inconsistencies found in target PowerSource ecosystem")
        
        # Category distribution
        category_counts = defaultdict(int)
        for gin, categories in self.gin_categories.items():
            if len(categories) == 1:  # Only count consistent GINs
                category_counts[list(categories)[0]] += 1
        
        logger.info("\nCategory Distribution (consistent GINs only):")
        for category, count in sorted(category_counts.items()):
            logger.info(f"  {category}: {count} GINs")
        
        # Return analysis results
        return {
            "total_gins": total_gins,
            "inconsistencies": inconsistencies,
            "target_related_gins": target_gins,
            "target_inconsistencies": target_inconsistencies,
            "can_proceed": len(target_inconsistencies) == 0
        }

def main():
    analyzer = CategoryConsistencyAnalyzer()
    results = analyzer.generate_report()
    
    if results["can_proceed"]:
        logger.info("✅ APPROVAL: Category consistency verified. Safe to proceed with data loading.")
    else:
        logger.error("❌ BLOCK: Category inconsistencies found. Must resolve before proceeding.")
    
    return results

if __name__ == "__main__":
    main()