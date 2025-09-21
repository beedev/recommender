#!/usr/bin/env python3
"""
GIN Extraction Report Generator
Creates comprehensive report of all GINs extracted by Excel file and sheet
"""

import json
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GINExtractionReporter:
    def __init__(self, target_powersources: List[str]):
        self.base_path = Path("/Users/bharath/Desktop/AgenticAI/Recommender/Datasets")
        self.target_powersources = set(self.pad_gin(ps) for ps in target_powersources)
        
        # Load ENG.json to check which GINs exist
        self.eng_products = self.load_eng_products()
        
        # Storage for extraction details
        self.extraction_details = []
        self.gin_sources = defaultdict(list)
        self.gin_categories = {}
        
    def pad_gin(self, gin: str) -> str:
        """Pad GIN to 10 characters with leading zeros"""
        if not gin or pd.isna(gin):
            return ""
        gin_str = str(gin).strip()
        return gin_str.zfill(10)
    
    def load_eng_products(self) -> Dict[str, Dict]:
        """Load products from ENG.json"""
        try:
            eng_file = self.base_path / "ENG.json"
            with open(eng_file, 'r', encoding='utf-8') as f:
                eng_data = json.load(f)
            
            products = {}
            for product in eng_data:
                gin_raw = product.get('data', {}).get('attributes', {}).get('GIN', '')
                gin = self.pad_gin(gin_raw)
                if gin:
                    products[gin] = {
                        'name': product.get('data', {}).get('attributes', {}).get('GINName', ''),
                        'description': product.get('data', {}).get('attributes', {}).get('description', ''),
                        'available': product.get('data', {}).get('attributes', {}).get('Available', 'true') == 'true',
                        'original_data': product
                    }
            
            logger.info(f"Loaded {len(products)} products from ENG.json")
            return products
            
        except Exception as e:
            logger.error(f"Error loading ENG.json: {e}")
            return {}
    
    def find_matching_ruleset(self, powersource_gin: str) -> str:
        """Find ruleset file for PowerSource"""
        ruleset_dir = self.base_path / "Ruleset"
        if not ruleset_dir.exists():
            return None
        
        # Map PowerSource GINs to likely ruleset files
        ps_to_file = {
            '0446200880': 'HIP configurator_Aristo 500ix_08092025.xlsx',
            '0465350883': 'HIP configurator_Warrior_08092025.xlsx', 
            '0465350884': 'HIP configurator_Warrior_08092025.xlsx',
            '0445555880': 'HIP configurator_Warrior750_08092025.xlsb.xlsx',
            '0445250880': 'HIP configurator_Renegade ES300_08092025.xlsx',
        }
        
        filename = ps_to_file.get(powersource_gin)
        if filename:
            file_path = ruleset_dir / filename
            if file_path.exists():
                return str(file_path)
        
        return None
    
    def extract_gins_from_sheet(self, file_path: str, sheet_name: str, powersource_gin: str) -> List[Dict]:
        """Extract GINs from a specific sheet"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Column mapping for categories
            column_category_mapping = {
                'GIN Powersource': 'PowerSource',
                'GIN Feeder': 'Feeder',
                'GIN Cooler': 'Cooler', 
                'GIN Torches': 'Torch',
                'GIN Interconn': 'Interconnector',
                'GIN Remote': 'Remote',
                'GIN_powersource': 'PowerSource',
                'GIN_feeder': 'Feeder',
                'GIN_cooler': 'Cooler',
                'GIN_torches': 'Torch', 
                'GIN_interconn': 'Interconnector',
                'GIN_remote': 'Remote',
                'GIN Accessories': 'WeldingAccessory',
                'GIN_accessories': 'WeldingAccessory'
            }
            
            # Additional mappings for accessories
            accessory_mappings = {
                'GIN Power Acc': 'PowerSourceAccessory',
                'GIN_power_acc': 'PowerSourceAccessory',
                'GIN Feeder Acc': 'FeederAccessory', 
                'GIN_feeder_acc': 'FeederAccessory',
                'GIN Remote Acc': 'RemoteAccessory',
                'GIN_remote_acc': 'RemoteAccessory',
                'GIN Connectivity': 'ConnectivityAccessory',
                'GIN_connectivity': 'ConnectivityAccessory'
            }
            
            column_category_mapping.update(accessory_mappings)
            
            extracted_gins = []
            
            for col_name in df.columns:
                if col_name in column_category_mapping:
                    category = column_category_mapping[col_name]
                    
                    for idx, value in df[col_name].items():
                        if pd.isna(value) or not self.is_valid_gin(value):
                            continue
                        
                        gin = self.pad_gin(value)
                        if gin:
                            # Check if exists in ENG.json
                            exists_in_eng = gin in self.eng_products
                            product_name = self.eng_products.get(gin, {}).get('name', f'Unknown Product {gin}')
                            
                            gin_info = {
                                'gin': gin,
                                'category': category,
                                'product_name': product_name,
                                'exists_in_eng': exists_in_eng,
                                'source_type': 'catalog' if exists_in_eng else 'synthetic',
                                'excel_file': Path(file_path).name,
                                'sheet_name': sheet_name,
                                'column_name': col_name,
                                'powersource_gin': powersource_gin,
                                'row_index': idx
                            }
                            
                            extracted_gins.append(gin_info)
                            
                            # Store for category tracking
                            self.gin_categories[gin] = category
                            self.gin_sources[gin].append({
                                'file': Path(file_path).name,
                                'sheet': sheet_name,
                                'column': col_name,
                                'powersource': powersource_gin
                            })
            
            return extracted_gins
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}, sheet {sheet_name}: {e}")
            return []
    
    def is_valid_gin(self, value) -> bool:
        """Check if value looks like a valid GIN"""
        if pd.isna(value):
            return False
        
        value_str = str(value).strip()
        if not value_str:
            return False
        
        # Standard 10-digit GIN
        if re.match(r'^\d{8,12}$', value_str):
            return True
        
        # F-series synthetic GINs
        if re.match(r'^F\d{9}$', value_str):
            return True
        
        # Handle alphanumeric GINs
        if re.match(r'^[0-9A-Z]{8,12}$', value_str.upper()):
            return True
        
        return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive extraction report"""
        logger.info("=" * 80)
        logger.info("GENERATING COMPREHENSIVE GIN EXTRACTION REPORT")
        logger.info("=" * 80)
        
        # Process each target PowerSource
        for powersource_gin in self.target_powersources:
            logger.info(f"Processing PowerSource: {powersource_gin}")
            
            # Find and process ruleset
            ruleset_file = self.find_matching_ruleset(powersource_gin)
            if not ruleset_file:
                logger.warning(f"No ruleset found for PowerSource {powersource_gin}")
                continue
            
            logger.info(f"Processing ruleset: {Path(ruleset_file).name}")
            
            # Get all sheets in the Excel file
            try:
                excel_file = pd.ExcelFile(ruleset_file)
                for sheet_name in excel_file.sheet_names:
                    logger.info(f"  Processing sheet: {sheet_name}")
                    
                    sheet_gins = self.extract_gins_from_sheet(
                        ruleset_file, sheet_name, powersource_gin
                    )
                    
                    self.extraction_details.extend(sheet_gins)
                    logger.info(f"    Extracted {len(sheet_gins)} GINs from {sheet_name}")
                    
            except Exception as e:
                logger.error(f"Error processing {ruleset_file}: {e}")
        
        # Analyze inconsistencies
        inconsistencies = self.analyze_inconsistencies()
        
        # Generate summary statistics
        summary = self.generate_summary()
        
        report = {
            'metadata': {
                'total_gins_extracted': len(self.extraction_details),
                'unique_gins': len(set(g['gin'] for g in self.extraction_details)),
                'catalog_products': len([g for g in self.extraction_details if g['exists_in_eng']]),
                'synthetic_products': len([g for g in self.extraction_details if not g['exists_in_eng']]),
                'target_powersources': list(self.target_powersources),
                'files_processed': len(set(g['excel_file'] for g in self.extraction_details)),
                'sheets_processed': len(set(f"{g['excel_file']}:{g['sheet_name']}" for g in self.extraction_details))
            },
            'extraction_details': self.extraction_details,
            'inconsistencies': inconsistencies,
            'summary': summary
        }
        
        return report
    
    def analyze_inconsistencies(self) -> Dict[str, Any]:
        """Analyze data inconsistencies"""
        inconsistencies = {
            'category_conflicts': [],
            'missing_from_eng': [],
            'duplicate_gins': [],
            'suspicious_patterns': []
        }
        
        # Check for category conflicts (same GIN with different categories)
        gin_categories_multi = defaultdict(set)
        for detail in self.extraction_details:
            gin_categories_multi[detail['gin']].add(detail['category'])
        
        for gin, categories in gin_categories_multi.items():
            if len(categories) > 1:
                inconsistencies['category_conflicts'].append({
                    'gin': gin,
                    'categories': list(categories),
                    'sources': [d for d in self.extraction_details if d['gin'] == gin]
                })
        
        # Find missing from ENG.json (high-frequency synthetic products)
        gin_frequency = defaultdict(int)
        for detail in self.extraction_details:
            if not detail['exists_in_eng']:
                gin_frequency[detail['gin']] += 1
        
        high_freq_missing = {gin: freq for gin, freq in gin_frequency.items() if freq >= 3}
        inconsistencies['missing_from_eng'] = [
            {
                'gin': gin,
                'frequency': freq,
                'category': self.gin_categories.get(gin, 'Unknown'),
                'sources': [d for d in self.extraction_details if d['gin'] == gin][:3]  # First 3 sources
            }
            for gin, freq in high_freq_missing.items()
        ]
        
        # Find suspicious patterns (e.g., obvious product names that should exist)
        for detail in self.extraction_details:
            if not detail['exists_in_eng'] and not detail['gin'].startswith('F'):
                # Non-F synthetic GINs that might actually exist
                inconsistencies['suspicious_patterns'].append(detail)
        
        return inconsistencies
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        # Category breakdown
        category_stats = defaultdict(lambda: {'total': 0, 'catalog': 0, 'synthetic': 0})
        
        for detail in self.extraction_details:
            category = detail['category']
            category_stats[category]['total'] += 1
            if detail['exists_in_eng']:
                category_stats[category]['catalog'] += 1
            else:
                category_stats[category]['synthetic'] += 1
        
        # File breakdown
        file_stats = defaultdict(lambda: {'total_gins': 0, 'unique_gins': set(), 'sheets': set()})
        
        for detail in self.extraction_details:
            file_name = detail['excel_file']
            file_stats[file_name]['total_gins'] += 1
            file_stats[file_name]['unique_gins'].add(detail['gin'])
            file_stats[file_name]['sheets'].add(detail['sheet_name'])
        
        # Convert sets to counts for JSON serialization
        for file_name in file_stats:
            file_stats[file_name]['unique_gins'] = len(file_stats[file_name]['unique_gins'])
            file_stats[file_name]['sheets'] = len(file_stats[file_name]['sheets'])
        
        return {
            'category_breakdown': dict(category_stats),
            'file_breakdown': dict(file_stats),
            'top_missing_gins': sorted(
                [(gin, len(sources)) for gin, sources in self.gin_sources.items() 
                 if gin not in self.eng_products and not gin.startswith('F')],
                key=lambda x: x[1], reverse=True
            )[:10]
        }

def main():
    """Generate comprehensive GIN extraction report"""
    # Use the same target PowerSources from config
    target_powersources = ['0465350883', '0465350884', '0445555880', '0445250880', '0446200880']
    
    reporter = GINExtractionReporter(target_powersources)
    report = reporter.generate_report()
    
    # Save detailed report
    output_file = '/Users/bharath/Desktop/AgenticAI/Recommender/neo4j_datasets/gin_extraction_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Detailed report saved to: {output_file}")
    
    # Print summary to console
    print("\\n" + "=" * 80)
    print("GIN EXTRACTION REPORT SUMMARY")
    print("=" * 80)
    
    metadata = report['metadata']
    print(f"Total GINs Extracted: {metadata['total_gins_extracted']}")
    print(f"Unique GINs: {metadata['unique_gins']}")
    print(f"Catalog Products: {metadata['catalog_products']}")
    print(f"Synthetic Products: {metadata['synthetic_products']}")
    print(f"Files Processed: {metadata['files_processed']}")
    print(f"Sheets Processed: {metadata['sheets_processed']}")
    
    print("\\n" + "=" * 50)
    print("CATEGORY BREAKDOWN")
    print("=" * 50)
    for category, stats in report['summary']['category_breakdown'].items():
        print(f"{category:20} | Total: {stats['total']:3d} | Catalog: {stats['catalog']:3d} | Synthetic: {stats['synthetic']:3d}")
    
    print("\\n" + "=" * 50)
    print("INCONSISTENCIES FOUND")
    print("=" * 50)
    
    inconsistencies = report['inconsistencies']
    print(f"Category Conflicts: {len(inconsistencies['category_conflicts'])}")
    print(f"High-Frequency Missing from ENG: {len(inconsistencies['missing_from_eng'])}")
    print(f"Suspicious Patterns: {len(inconsistencies['suspicious_patterns'])}")
    
    if inconsistencies['category_conflicts']:
        print("\\nCategory Conflicts (first 5):")
        for conflict in inconsistencies['category_conflicts'][:5]:
            print(f"  {conflict['gin']}: {conflict['categories']}")
    
    if inconsistencies['missing_from_eng']:
        print("\\nHigh-Frequency Missing GINs (first 10):")
        for missing in inconsistencies['missing_from_eng'][:10]:
            print(f"  {missing['gin']} ({missing['category']}): appears {missing['frequency']} times")
    
    print(f"\\nFull detailed report available at: {output_file}")

if __name__ == "__main__":
    main()