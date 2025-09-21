#!/usr/bin/env python3
"""
PowerSource Master Dataset Generator
===================================

Comprehensive system that takes PowerSource GIN(s) as input and generates
complete datasets ready for Neo4j loading:

1. Discovers ALL related GINs from Rulesets + Golden Packages
2. Creates master GIN list  
3. Filters all data sources by master GIN list
4. Creates synthetic products for missing GINs (SG- prefix in description)
5. Generates 4 JSON datasets ready for Neo4j import

Output: product_catalog.json, compatibility_rules.json, golden_packages.json, sales_data.json
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Set, List, Any, Tuple
from collections import defaultdict
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PowerSourceMasterExtractor:
    def __init__(self, target_powersources: List[str]):
        self.base_path = Path("/Users/bharath/Desktop/AgenticAI/Recommender/Datasets")
        
        # Target PowerSources (can be 1 or more)
        self.target_powersources = set(self.pad_gin(ps) for ps in target_powersources)
        
        # Master GIN discovery
        self.master_gin_list = set()
        self.gin_sources = defaultdict(list)  # Track where each GIN was discovered
        
        # Category inference from rulesets
        self.gin_categories = {}
        
        logger.info(f"Initializing PowerSource Master Extractor for: {self.target_powersources}")
    
    def pad_gin(self, gin: str) -> str:
        """Pad GIN to 10 characters with leading zeros"""
        if not gin or pd.isna(gin):
            return ""
        gin_str = str(gin).strip()
        if gin_str.startswith('F000') or gin_str == "":
            return gin_str
        return gin_str.zfill(10)
    
    def discover_gins_from_golden_packages(self):
        """Discover all GINs related to target PowerSources from golden packages"""
        logger.info("🔍 Discovering GINs from Golden Packages...")
        
        golden_file = self.base_path / "golden_pkg_format_V2.xlsx"
        
        try:
            df = pd.read_excel(golden_file, sheet_name='Sheet1')
            logger.info(f"Golden packages loaded: {df.shape}")
            
            # Find packages containing target PowerSources
            related_packages = []
            for idx, row in df.iterrows():
                ps_gin = self.pad_gin(row.get('powersource gin', ''))
                if ps_gin in self.target_powersources:
                    related_packages.append(row)
                    logger.info(f"Found package for PowerSource {ps_gin}: {row.get('powersource name', 'Unknown')}")
            
            # Extract ALL GINs from related packages
            column_mappings = {
                'powersource gin': 'PowerSource',
                'feeder gin': 'Feeder',
                'cooler gin': 'Cooler',
                'Interconn GIN': 'Interconnector',
                'torches gin': 'Torch',
                'power accessories gin': 'PowerSourceAccessory',
                'feeder accessories gin': 'FeederAccessory',
                'GIN Cooler Accessories': 'CoolerAccessory'
            }
            
            for package in related_packages:
                ps_gin = self.pad_gin(package.get('powersource gin', ''))
                for col_name, category in column_mappings.items():
                    gin_value = package.get(col_name, '')
                    if pd.notna(gin_value) and str(gin_value).strip():
                        gin = self.pad_gin(gin_value)
                        if gin:
                            self.master_gin_list.add(gin)
                            self.gin_sources[gin].append(f"golden_package_{ps_gin}")
                            if gin not in self.gin_categories:
                                self.gin_categories[gin] = category
                            logger.info(f"  Discovered {gin} ({category}) from golden package")
            
            logger.info(f"✅ Golden Packages: Discovered {len([g for g in self.master_gin_list if any('golden_package' in src for src in self.gin_sources[g])])} GINs")
            
        except Exception as e:
            logger.error(f"Error processing golden packages: {e}")
    
    def discover_gins_from_rulesets(self):
        """Discover GINs from ruleset Excel files for target PowerSources"""
        logger.info("🔍 Discovering GINs from Rulesets...")
        
        ruleset_dir = self.base_path / "Ruleset"
        
        # Map PowerSource to expected ruleset files
        powersource_file_mapping = {
            "0465350883": "HIP configurator_Warrior_08092025.xlsx",      # Warrior 500i
            "0465350884": "HIP configurator_Warrior_08092025.xlsx",      # Warrior 400i  
            "0445555880": "HIP configurator_Warrior750_08092025.xlsb.xlsx", # Warrior 750i
            "0445250880": "HIP configurator_Renegade ES300_08092025.xlsx",  # Renegade ES 300i
            "0446200880": "HIP configurator_Aristo 500ix_08092025.xlsx"     # Aristo 500ix
        }
        
        for ps_gin in self.target_powersources:
            if ps_gin in powersource_file_mapping:
                file_name = powersource_file_mapping[ps_gin]
                file_path = ruleset_dir / file_name
                
                logger.info(f"Processing ruleset for {ps_gin}: {file_name}")
                
                try:
                    self._extract_gins_from_ruleset_file(file_path, ps_gin)
                except Exception as e:
                    logger.error(f"Error processing {file_name}: {e}")
        
        ruleset_gins = len([g for g in self.master_gin_list if any('ruleset' in src for src in self.gin_sources[g])])
        logger.info(f"✅ Rulesets: Discovered {ruleset_gins} additional GINs")
    
    def _extract_gins_from_ruleset_file(self, file_path: Path, powersource_gin: str):
        """Extract GINs from a specific ruleset file"""
        if not file_path.exists():
            logger.warning(f"Ruleset file not found: {file_path}")
            return
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            # Define category mappings based on COLUMN NAMES (not sheet names)
            column_category_mapping = {
                # PowerSource columns
                'GIN Powersource': 'PowerSource',
                'Powersource Name': 'PowerSource',
                
                # Feeder columns  
                'GIN Feeder': 'Feeder',
                'Feeder Name': 'Feeder',
                'GIN Feeder Wears': 'FeederAccessory',
                'Feeder Wears Name': 'FeederAccessory',
                
                # Cooler columns
                'GIN Cooler': 'Cooler', 
                'Cooler Name': 'Cooler',
                
                # Torch columns
                'GIN Torches': 'Torch',
                'Torches Name': 'Torch',
                
                # Interconnector columns
                'GIN Interconn': 'Interconnector',
                'Interconn Name': 'Interconnector',
                
                # PowerSource Accessories
                'GIN Powersource Accessories': 'PowerSourceAccessory',
                'Powersource Accessories Name': 'PowerSourceAccessory',
                'GIN Powersource Conditional Accessories': 'PowerSourceAccessory',
                'Powersource Conditional Accessories Name': 'PowerSourceAccessory',
                
                # Feeder Accessories
                'GIN Feeder Accessories': 'FeederAccessory',
                'Feeder Accessories Name': 'FeederAccessory', 
                'GIN Feeder Conditional Accessories': 'FeederAccessory',
                'Feeder Conditional Accessories Name': 'FeederAccessory',
                
                # Remote columns
                'GIN Remotes': 'Remote',
                'Remotes Name': 'Remote',
                'GIN Remote Accessories': 'RemoteAccessory',
                'Remote Accessories Name': 'RemoteAccessory',
                'GIN Remote Conditional Accessories': 'RemoteAccessory', 
                'Remote Conditional Accessories Name': 'RemoteAccessory',
                
                # Connectivity columns
                'GIN Connectivity': 'ConnectivityAccessory',
                'Connectivity Name': 'ConnectivityAccessory',
            }
            
            for sheet_name in excel_file.sheet_names:
                if sheet_name in ['Description', 'Attributes']:
                    continue  # Skip description/attribute sheets
                
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if len(df) == 0:
                        continue
                    
                    # Extract GINs using COLUMN-BASED categorization
                    for idx, row in df.iterrows():
                        for col_name, value in row.items():
                            if pd.notna(value):
                                value_str = str(value).strip()
                                # Look for GIN patterns
                                if self._is_valid_gin_pattern(value_str):
                                    gin = self.pad_gin(value_str)
                                    if gin:
                                        # Determine category based on COLUMN NAME, not sheet name
                                        category = column_category_mapping.get(col_name, 'Unknown')
                                        
                                        # CRITICAL FIX: Only add PowerSource GINs that are in target_powersources
                                        # All other categories should be added without restriction
                                        if category == 'PowerSource':
                                            if gin in self.target_powersources:
                                                self.master_gin_list.add(gin)
                                                self.gin_sources[gin].append(f"ruleset_{powersource_gin}_{sheet_name}_{col_name}")
                                                if gin not in self.gin_categories:
                                                    self.gin_categories[gin] = category
                                                logger.info(f"    Added target PowerSource from ruleset: {gin}")
                                            else:
                                                logger.info(f"    Skipped non-target PowerSource: {gin} (not in config)")
                                        else:
                                            # Non-PowerSource components: add without restriction
                                            self.master_gin_list.add(gin)
                                            self.gin_sources[gin].append(f"ruleset_{powersource_gin}_{sheet_name}_{col_name}")
                                            if gin not in self.gin_categories:
                                                self.gin_categories[gin] = category
                
                except Exception as e:
                    logger.warning(f"Could not process sheet {sheet_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing ruleset file {file_path}: {e}")
    
    def _is_valid_gin_pattern(self, value: str) -> bool:
        """Check if value matches GIN pattern"""
        # GIN patterns: 10 digits, F000 series, or specific alphanumeric patterns
        if value.startswith('F000'):
            return True
        if value.isdigit() and len(value) >= 8:
            return True
        # Handle alphanumeric GINs like "114P381040"
        if re.match(r'^[0-9A-Z]{8,12}$', value.upper()):
            return True
        return False
    
    def create_enhanced_product_catalog(self):
        """Create enhanced product catalog with synthetic entries for missing GINs"""
        logger.info("📦 Creating Enhanced Product Catalog...")
        
        # Load existing product catalog
        eng_file = self.base_path / "ENG.json"
        existing_products = {}
        
        try:
            with open(eng_file, 'r', encoding='utf-8') as f:
                eng_data = json.load(f)
            
            for product in eng_data:
                # Handle ENG.json structure: product['data']['attributes']['GIN']
                gin_raw = product.get('data', {}).get('attributes', {}).get('GIN', '')
                gin = self.pad_gin(gin_raw)
                if gin:
                    existing_products[gin] = product
            
            logger.info(f"Loaded {len(existing_products)} existing products from ENG.json")
            
        except Exception as e:
            logger.error(f"Error loading ENG.json: {e}")
            existing_products = {}
        
        # Create enhanced catalog
        enhanced_catalog = []
        missing_count = 0
        
        for gin in sorted(self.master_gin_list):
            if gin in existing_products:
                # Use existing product from ENG.json structure
                eng_product = existing_products[gin]
                attrs = eng_product.get('data', {}).get('attributes', {})
                
                product = {
                    'gin': gin,  # Ensure padded format
                    'name': attrs.get('GINName', f'Product {gin}'),
                    'description': attrs.get('description', f'Product {gin}'),
                    'category': self.gin_categories.get(gin, 'Unknown'),
                    'available': attrs.get('Available', 'true') == 'true',
                    'source': 'catalog',
                    'original_data': eng_product
                }
                enhanced_catalog.append(product)
            else:
                # Create synthetic product
                synthetic_product = self._create_synthetic_product(gin)
                enhanced_catalog.append(synthetic_product)
                missing_count += 1
                logger.info(f"Created synthetic product for {gin}: {synthetic_product['name']}")
        
        logger.info(f"✅ Enhanced Catalog: {len(enhanced_catalog)} products ({len(existing_products)-missing_count} existing, {missing_count} synthetic)")
        
        return {
            "metadata": {
                "total_products": len(enhanced_catalog),
                "existing_products": len(enhanced_catalog) - missing_count,
                "synthetic_products": missing_count,
                "target_powersources": list(self.target_powersources),
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Enhanced catalog from ENG.json + synthetic products"
            },
            "products": enhanced_catalog
        }
    
    def _create_synthetic_product(self, gin: str) -> Dict[str, Any]:
        """Create enhanced synthetic product entry with ruleset context"""
        category = self.gin_categories.get(gin, 'Unknown')
        sources = self.gin_sources.get(gin, [])
        
        # Analyze sources to extract context
        context_info = self._extract_ruleset_context(gin, sources)
        
        # Generate enhanced name based on category and context
        if gin.startswith('F000'):
            name_map = {
                'F000000007': 'No Feeder Available',
                'F000000005': 'No Cooler Available', 
                'F000000002': 'No Cooler Available',
                'F000000003': 'No Torch Available',
                'F000000006': 'No Torch Available',
                'F000000008': 'No Interconnector Available',
                'F000000009': 'No Feeder Accessory Available',
                'F000000010': 'No Accessory Available',
                'F000000011': 'No Connectivity Available'
            }
            name = name_map.get(gin, f'No {category} Available')
            description = f"SG-Integrated component placeholder - {name}. {context_info['description']}"
        else:
            # Create detailed name from context
            name = self._generate_product_name(gin, category, context_info)
            description = f"SG-{category} product. {context_info['description']}"
        
        return {
            "gin": gin,
            "name": name,
            "description": description,
            "category": category,
            "source": "synthetic",
            "discovery_sources": sources,
            "is_available": gin.startswith('F000') == False,
            "ruleset_context": context_info,
            "compatible_powersources": context_info['powersources'],
            "usage_frequency": len(sources),
            "specifications": context_info['specs'],
            "image_url": None,
            "datasheet_url": None
        }
    
    def _extract_ruleset_context(self, gin: str, sources: List[str]) -> Dict[str, Any]:
        """Extract detailed context from ruleset sources"""
        context = {
            'description': '',
            'powersources': [],
            'rule_types': [],
            'sheet_types': [],
            'specs': {},
            'compatibility_info': ''
        }
        
        powersource_set = set()
        rule_types = set()
        sheet_types = set()
        
        for source in sources:
            # Parse source format: "ruleset_{powersource_gin}_{sheet_name}"
            if source.startswith('ruleset_'):
                parts = source.split('_', 2)
                if len(parts) >= 3:
                    ps_gin = parts[1]
                    sheet_name = parts[2]
                    
                    powersource_set.add(ps_gin)
                    sheet_types.add(sheet_name)
                    
                    # Map sheet names to rule types
                    if 'Accessories' in sheet_name:
                        rule_types.add('accessory_compatibility')
                    elif 'Torch' in sheet_name:
                        rule_types.add('torch_compatibility')
                    elif 'Feeder' in sheet_name:
                        rule_types.add('feeder_compatibility')
                    elif 'Remote' in sheet_name:
                        rule_types.add('remote_compatibility')
                    elif 'Connectivity' in sheet_name or 'Interconn' in sheet_name:
                        rule_types.add('connectivity_compatibility')
                    else:
                        rule_types.add('general_compatibility')
        
        context['powersources'] = list(powersource_set)
        context['rule_types'] = list(rule_types)
        context['sheet_types'] = list(sheet_types)
        
        # Generate description based on context
        context['description'] = self._generate_context_description(gin, context)
        
        # Add compatibility info
        context['compatibility_info'] = f"Compatible with PowerSources: {', '.join(powersource_set)}"
        
        return context
    
    def _generate_context_description(self, gin: str, context: Dict[str, Any]) -> str:
        """Generate descriptive text from ruleset context"""
        descriptions = []
        
        # PowerSource context
        if context['powersources']:
            ps_names = []
            for ps_gin in context['powersources']:
                ps_name = self.target_powersources_names.get(ps_gin, ps_gin)
                ps_names.append(ps_name)
            descriptions.append(f"Used with {', '.join(ps_names)}")
        
        # Rule type context
        if context['rule_types']:
            if 'accessory_compatibility' in context['rule_types']:
                descriptions.append("Compatible accessory component")
            if 'torch_compatibility' in context['rule_types']:
                descriptions.append("Torch system component")
            if 'feeder_compatibility' in context['rule_types']:
                descriptions.append("Wire feeder component")
            if 'connectivity_compatibility' in context['rule_types']:
                descriptions.append("Connectivity/interconnection component")
        
        # Usage frequency
        usage_count = len(context.get('sheet_types', []))
        if usage_count > 5:
            descriptions.append("Frequently used component")
        elif usage_count > 2:
            descriptions.append("Commonly used component")
        
        return '. '.join(descriptions) if descriptions else "Component discovered in compatibility rules"
    
    def _generate_product_name(self, gin: str, category: str, context: Dict[str, Any]) -> str:
        """Generate meaningful product name from context"""
        base_name = f"{category} {gin}"
        
        # Add descriptive suffixes based on context
        if category == 'Remote' and 'remote_compatibility' in context.get('rule_types', []):
            return f"Remote Control {gin}"
        elif category == 'Torch' and 'torch_compatibility' in context.get('rule_types', []):
            return f"Welding Torch {gin}"
        elif category == 'Feeder' and 'feeder_compatibility' in context.get('rule_types', []):
            return f"Wire Feeder {gin}"
        elif category == 'Interconnector' and 'connectivity_compatibility' in context.get('rule_types', []):
            return f"Interconnector Cable {gin}"
        elif 'Accessory' in category:
            return f"{category.replace('Accessory', ' Accessory')} {gin}"
        
        return base_name
    
    @property
    def target_powersources_names(self):
        """Map of PowerSource GINs to names"""
        return {
            "0465350883": "Warrior 500i",
            "0465350884": "Warrior 400i", 
            "0445555880": "Warrior 750i 380-460V CE",
            "0445250880": "Renegade ES 300i",
            "0446200880": "Aristo 500ix"
        }
    
    def create_filtered_sales_data(self):
        """Filter sales data for complete orders with PowerSource + Feeder + Cooler combo"""
        logger.info("💰 Filtering Sales Data for complete PowerSource + Feeder + Cooler orders...")
        
        sales_file = self.base_path / "sales_data_cleaned.csv"
        
        try:
            df = pd.read_csv(sales_file, dtype={'GIN': str, 'GIN with Zero': str})
            logger.info(f"Loaded sales data: {df.shape}")
            
            # Group by order to analyze complete orders
            orders_analysis = self._analyze_orders_for_complete_combos(df)
            
            # Filter for complete orders only
            complete_orders = []
            valid_order_ids = set()
            
            for order_id, order_info in orders_analysis.items():
                if order_info['is_complete_combo']:
                    valid_order_ids.add(order_id)
                    complete_orders.append(order_info)
            
            logger.info(f"Found {len(complete_orders)} complete PowerSource + Feeder + Cooler orders")
            
            # Extract all records from valid orders
            filtered_sales = []
            for _, row in df.iterrows():
                order_id = str(row.get('Ord_No', ''))
                if order_id in valid_order_ids:
                    gin_raw = str(row.get('GIN with Zero', '') or row.get('GIN', ''))
                    gin = self.pad_gin(gin_raw)
                    
                    # Only include GINs from our master list
                    if gin in self.master_gin_list:
                        sales_record = {
                            "order_id": order_id,
                            "line_no": str(row.get('Line_No', '')),
                            "gin": gin,
                            "description": str(row.get('Descr', '')),
                            "customer": str(row.get('Cust_nm', '')),
                            "facility": str(row.get('Facility', '')),
                            "warehouse": str(row.get('Whs', '')),
                            "category": self.gin_categories.get(gin, 'Unknown')
                        }
                        filtered_sales.append(sales_record)
            
            logger.info(f"✅ Sales Data: {len(filtered_sales)} records from {len(valid_order_ids)} complete orders")
            
            return {
                "metadata": {
                    "total_records": len(filtered_sales),
                    "unique_orders": len(valid_order_ids),
                    "complete_combo_orders": len(complete_orders),
                    "target_powersources": list(self.target_powersources),
                    "generated_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Filtered from sales_data_cleaned.csv - complete PowerSource+Feeder+Cooler orders only",
                    "filtering_rule": "Orders must contain PowerSource + Feeder + Cooler minimum combo"
                },
                "sales_records": filtered_sales
            }
            
        except Exception as e:
            logger.error(f"Error processing sales data: {e}")
            return {"metadata": {"total_records": 0}, "sales_records": []}
    
    def _analyze_orders_for_complete_combos(self, df) -> Dict[str, Dict[str, Any]]:
        """Analyze orders to find complete PowerSource + Feeder + Cooler combos"""
        from collections import defaultdict
        
        orders_analysis = defaultdict(lambda: {
            'powersources': set(),
            'feeders': set(), 
            'coolers': set(),
            'other_components': set(),
            'total_items': 0,
            'is_complete_combo': False
        })
        
        # Group by order ID and categorize components
        for _, row in df.iterrows():
            order_id = str(row.get('Ord_No', ''))
            if not order_id:
                continue
                
            gin_raw = str(row.get('GIN with Zero', '') or row.get('GIN', ''))
            gin = self.pad_gin(gin_raw)
            
            # Only process GINs from our master list
            if gin not in self.master_gin_list:
                continue
                
            category = self.gin_categories.get(gin, 'Unknown')
            orders_analysis[order_id]['total_items'] += 1
            
            # Categorize by component type
            if category == 'PowerSource':
                orders_analysis[order_id]['powersources'].add(gin)
            elif category == 'Feeder':
                orders_analysis[order_id]['feeders'].add(gin)
            elif category == 'Cooler':
                orders_analysis[order_id]['coolers'].add(gin)
            else:
                orders_analysis[order_id]['other_components'].add(gin)
        
        # Determine complete combos
        complete_count = 0
        for order_id, analysis in orders_analysis.items():
            # Check for complete combo: at least 1 PowerSource + 1 Feeder + 1 Cooler
            has_powersource = len(analysis['powersources']) > 0
            has_feeder = len(analysis['feeders']) > 0
            has_cooler = len(analysis['coolers']) > 0
            
            # Special handling for integrated PowerSources (like Renegade with F000 components)
            has_integrated_feeder = any(gin.startswith('F000') and self.gin_categories.get(gin) == 'Feeder' 
                                      for gin in analysis['other_components'])
            has_integrated_cooler = any(gin.startswith('F000') and self.gin_categories.get(gin) == 'Cooler' 
                                      for gin in analysis['other_components'])
            
            # Accept integrated components as valid
            if has_integrated_feeder:
                has_feeder = True
            if has_integrated_cooler:
                has_cooler = True
            
            analysis['is_complete_combo'] = has_powersource and has_feeder and has_cooler
            
            if analysis['is_complete_combo']:
                complete_count += 1
        
        logger.info(f"Order analysis: {len(orders_analysis)} total orders, {complete_count} complete combos")
        logger.info(f"Complete combo rate: {(complete_count/len(orders_analysis)*100):.1f}%")
        
        return dict(orders_analysis)
    
    def create_filtered_golden_packages(self):
        """Filter golden packages for target PowerSources"""
        logger.info("🏆 Filtering Golden Packages...")
        
        golden_file = self.base_path / "golden_pkg_format_V2.xlsx"
        
        try:
            df = pd.read_excel(golden_file, sheet_name='Sheet1')
            
            filtered_packages = []
            
            for idx, row in df.iterrows():
                ps_gin = self.pad_gin(row.get('powersource gin', ''))
                if ps_gin in self.target_powersources:
                    package = {
                        "package_id": idx + 1,
                        "powersource_gin": ps_gin,
                        "powersource_name": str(row.get('powersource name', '')),
                        "components": {}
                    }
                    
                    # Map all component columns
                    component_mappings = {
                        'feeder_gin': row.get('feeder gin', ''),
                        'feeder_name': row.get('feeder name', ''),
                        'cooler_gin': row.get('cooler gin', ''),
                        'cooler_name': row.get('cooler name', ''),
                        'interconnector_gin': row.get('Interconn GIN', ''),
                        'interconnector_name': row.get('Interconn name', ''),
                        'torch_gin': row.get('torches gin', ''),
                        'torch_name': row.get('torches name', ''),
                        'power_accessory_gin': row.get('power accessories gin', ''),
                        'power_accessory_name': row.get('power accessories name', ''),
                        'feeder_accessory_gin': row.get('feeder accessories gin', ''),
                        'feeder_accessory_name': row.get('feeder accessories name', ''),
                        'cooler_accessory_gin': row.get('GIN Cooler Accessories', ''),
                        'cooler_accessory_name': row.get('Cooler Accessories Name', '')
                    }
                    
                    for comp_type, value in component_mappings.items():
                        if pd.notna(value) and str(value).strip():
                            if comp_type.endswith('_gin'):
                                comp_name = comp_type.replace('_gin', '')
                                gin = self.pad_gin(value)
                                name = component_mappings.get(f"{comp_name}_name", "")
                                
                                if gin:
                                    package["components"][comp_name] = {
                                        "gin": gin,
                                        "name": str(name) if pd.notna(name) else ""
                                    }
                    
                    filtered_packages.append(package)
            
            logger.info(f"✅ Golden Packages: {len(filtered_packages)} packages for target PowerSources")
            
            return {
                "metadata": {
                    "total_packages": len(filtered_packages),
                    "target_powersources": list(self.target_powersources),
                    "generated_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Filtered from golden_pkg_format_V2.xlsx"
                },
                "golden_packages": filtered_packages
            }
            
        except Exception as e:
            logger.error(f"Error processing golden packages: {e}")
            return {"metadata": {"total_packages": 0}, "golden_packages": []}
    
    def create_filtered_compatibility_rules(self):
        """Create compatibility rules from ruleset analysis"""
        logger.info("🔗 Creating Compatibility Rules...")
        
        # Load PowerSource config to get names
        config_path = Path(__file__).parent.parent.parent.parent / "powersource_config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                powersource_names = config.get("powersources", {})
        except Exception as e:
            logger.error(f"Failed to load PowerSource config: {e}")
            return {
                "metadata": {"total_rules": 0, "target_powersources": list(self.target_powersources), 
                           "generated_date": datetime.now().strftime("%Y-%m-%d"), "source": "Error loading config"},
                "compatibility_rules": []
            }
        
        compatibility_rules = []
        total_rules = 0
        
        for powersource_gin in self.target_powersources:
            if powersource_gin in powersource_names:
                powersource_name = powersource_names[powersource_gin]
                logger.info(f"  Processing PowerSource: {powersource_gin} ({powersource_name})")
                
                # Find matching ruleset Excel file
                excel_file = self._find_ruleset_file(powersource_name)
                
                if excel_file:
                    logger.info(f"    Found ruleset file: {excel_file.name}")
                    rules = self._extract_rules_from_excel(excel_file, powersource_gin, powersource_name)
                    compatibility_rules.extend(rules)
                    total_rules += len(rules)
                    logger.info(f"    Extracted {len(rules)} rules")
                else:
                    logger.warning(f"    No ruleset file found for: {powersource_name}")
            else:
                logger.warning(f"  PowerSource GIN not found in config: {powersource_gin}")
        
        logger.info(f"🔗 Total compatibility rules extracted: {total_rules}")
        
        return {
            "metadata": {
                "total_rules": total_rules,
                "target_powersources": list(self.target_powersources),
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Extracted from ruleset Excel files"
            },
            "compatibility_rules": compatibility_rules
        }
    
    def _find_ruleset_file(self, powersource_name: str) -> Path:
        """Find the matching ruleset Excel file for a PowerSource name"""
        ruleset_dir = self.base_path / "Ruleset"
        
        # Create mapping patterns to match PowerSource names to filenames
        name_patterns = {
            "Aristo 500ix": ["Aristo 500ix"],
            "Warrior 500i": ["Warrior_", "Warrior."],  # Could be in general Warrior file
            "Warrior 400i": ["Warrior_", "Warrior."],  # Could be in general Warrior file  
            "Warrior 750i 380-460V, CE": ["Warrior750"],
            "Renegade ES 300i with cables": ["Renegade ES300"]
        }
        
        # Get all Excel files in Ruleset directory
        excel_files = list(ruleset_dir.glob("*.xlsx")) + list(ruleset_dir.glob("*.xlsb"))
        
        if powersource_name in name_patterns:
            patterns = name_patterns[powersource_name]
            for pattern in patterns:
                for excel_file in excel_files:
                    if pattern in excel_file.name:
                        return excel_file
        
        # Fallback: try to find by partial name match
        for excel_file in excel_files:
            # Extract key words from PowerSource name
            key_words = powersource_name.replace(" ", "").replace("i", "").replace(",", "").replace("-", "")
            if any(word in excel_file.name for word in key_words.split() if len(word) > 3):
                return excel_file
        
        return None
    
    def _extract_rules_from_excel(self, excel_file: Path, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Extract compatibility rules from Excel ruleset file"""
        rules = []
        
        try:
            # Process Init sheet (PowerSource -> Feeder/Cooler rules)
            try:
                init_df = pd.read_excel(excel_file, sheet_name='Init')
                init_rules = self._process_init_sheet(init_df, powersource_gin, powersource_name)
                rules.extend(init_rules)
                logger.info(f"      Init sheet: {len(init_rules)} rules")
            except Exception as e:
                logger.warning(f"      Could not process Init sheet: {e}")
            
            # Process other compatibility sheets
            sheet_processors = {
                'Interconn': self._process_interconn_sheet,
                'Torches': self._process_torch_sheet,
                'Powersource Accessories': self._process_power_accessory_sheet,
                'Feeder Accessories': self._process_feeder_accessory_sheet,
                'Remotes': self._process_remote_sheet,
                'Connectivity': self._process_connectivity_sheet
            }
            
            for sheet_name, processor in sheet_processors.items():
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    sheet_rules = processor(df, powersource_gin, powersource_name)
                    rules.extend(sheet_rules)
                    logger.info(f"      {sheet_name} sheet: {len(sheet_rules)} rules")
                except Exception as e:
                    logger.warning(f"      Could not process {sheet_name} sheet: {e}")
                    
        except Exception as e:
            logger.error(f"    Error reading Excel file {excel_file.name}: {e}")
        
        return rules
    
    def _process_init_sheet(self, init_df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Init sheet - PowerSource DETERMINES Feeder/Cooler"""
        rules = []
        
        for _, row in init_df.iterrows():
            try:
                power_gin = self.pad_gin(str(row['GIN Powersource']).strip())
                feeder_gin = self.pad_gin(str(row['GIN Feeder']).strip())
                cooler_gin = self.pad_gin(str(row['GIN Cooler']).strip())
                
                # Only include rules for our target PowerSource or if power_gin matches
                if power_gin == powersource_gin or power_gin == 'nan':
                    
                    # PowerSource -> Feeder rule
                    if self._is_valid_gin(feeder_gin):
                        rules.append({
                            "rule_id": f"{powersource_gin}_determines_feeder_{feeder_gin}",
                            "rule_type": "DETERMINES",
                            "source_gin": powersource_gin,
                            "target_gin": feeder_gin,
                            "source_category": "PowerSource", 
                            "target_category": "Feeder",
                            "relationship": "determines",
                            "priority": 1,
                            "confidence": 1.0,
                            "source_file": powersource_name,
                            "sheet_name": "Init"
                        })
                    
                    # PowerSource -> Cooler rule  
                    if self._is_valid_gin(cooler_gin):
                        rules.append({
                            "rule_id": f"{powersource_gin}_determines_cooler_{cooler_gin}",
                            "rule_type": "DETERMINES",
                            "source_gin": powersource_gin,
                            "target_gin": cooler_gin,
                            "source_category": "PowerSource",
                            "target_category": "Cooler", 
                            "relationship": "determines",
                            "priority": 1,
                            "confidence": 1.0,
                            "source_file": powersource_name,
                            "sheet_name": "Init"
                        })
                        
            except Exception as e:
                logger.warning(f"Error processing Init rule: {e}")
        
        return rules
    
    def _process_interconn_sheet(self, interconn_df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Interconn sheet - context-dependent interconnector compatibility"""
        rules = []
        
        for _, row in interconn_df.iterrows():
            try:
                power_gin = self.pad_gin(str(row['GIN Powersource']).strip())
                feeder_gin = self.pad_gin(str(row['GIN Feeder']).strip())
                cooler_gin = self.pad_gin(str(row['GIN Cooler']).strip())
                interconn_gin = self.pad_gin(str(row['GIN Interconn']).strip())
                priority = row.get('Priorities', 1)
                
                # Only include rules for our target PowerSource
                if power_gin == powersource_gin or power_gin == 'nan':
                    if self._is_valid_gin(interconn_gin):
                        rules.append({
                            "rule_id": f"{powersource_gin}_interconn_{interconn_gin}",
                            "rule_type": "COMPATIBLE_WITH",
                            "source_gin": interconn_gin,
                            "target_gin": powersource_gin,
                            "source_category": "Interconnector",
                            "target_category": "PowerSource",
                            "relationship": "compatible_with",
                            "priority": priority,
                            "confidence": 0.9,
                            "context": {
                                "requires_feeder": feeder_gin if self._is_valid_gin(feeder_gin) else None,
                                "requires_cooler": cooler_gin if self._is_valid_gin(cooler_gin) else None
                            },
                            "source_file": powersource_name,
                            "sheet_name": "Interconn"
                        })
                        
            except Exception as e:
                logger.warning(f"Error processing Interconn rule: {e}")
        
        return rules
    
    def _process_torch_sheet(self, torch_df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Torches sheet - torch compatibility"""
        rules = []
        
        for _, row in torch_df.iterrows():
            try:
                feeder_gin = self.pad_gin(str(row['GIN Feeder']).strip())
                cooler_gin = self.pad_gin(str(row['GIN Cooler']).strip()) 
                torch_gin = self.pad_gin(str(row['GIN Torches']).strip())
                priority = row.get('Priorities', 1)
                
                if self._is_valid_gin(torch_gin):
                    rules.append({
                        "rule_id": f"{powersource_gin}_torch_{torch_gin}",
                        "rule_type": "COMPATIBLE_WITH",
                        "source_gin": torch_gin,
                        "target_gin": powersource_gin,
                        "source_category": "Torch",
                        "target_category": "PowerSource", 
                        "relationship": "compatible_with",
                        "priority": priority,
                        "confidence": 0.8,
                        "context": {
                            "requires_feeder": feeder_gin if self._is_valid_gin(feeder_gin) else None,
                            "requires_cooler": cooler_gin if self._is_valid_gin(cooler_gin) else None
                        },
                        "source_file": powersource_name,
                        "sheet_name": "Torches"
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing Torch rule: {e}")
        
        return rules
    
    def _process_power_accessory_sheet(self, df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Power Source Accessories sheet"""
        rules = []
        
        for _, row in df.iterrows():
            try:
                power_gin = self.pad_gin(str(row['GIN Powersource']).strip())
                accessory_gin = self.pad_gin(str(row['GIN Powersource Accessories']).strip())
                priority = row.get('Priorities', 1)
                
                # Only include rules for our target PowerSource
                if (power_gin == powersource_gin or power_gin == 'nan') and self._is_valid_gin(accessory_gin):
                    rules.append({
                        "rule_id": f"{powersource_gin}_power_accessory_{accessory_gin}",
                        "rule_type": "COMPATIBLE_WITH",
                        "source_gin": powersource_gin,
                        "target_gin": accessory_gin,
                        "source_category": "PowerSource",
                        "target_category": "Power Accessory",
                        "relationship": "compatible_with",
                        "priority": priority,
                        "confidence": 0.7,
                        "source_file": powersource_name,
                        "sheet_name": "Powersource Accessories"
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing Power Accessory rule: {e}")
        
        return rules
    
    def _process_feeder_accessory_sheet(self, df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Feeder Accessories sheet"""
        rules = []
        
        for _, row in df.iterrows():
            try:
                feeder_gin = self.pad_gin(str(row['GIN Feeder']).strip())
                accessory_gin = self.pad_gin(str(row['GIN Feeder Accessories']).strip())
                priority = row.get('Priorities', 1) if 'Priorities' in row else 1
                
                if self._is_valid_gin(feeder_gin) and self._is_valid_gin(accessory_gin):
                    rules.append({
                        "rule_id": f"{feeder_gin}_feeder_accessory_{accessory_gin}",
                        "rule_type": "COMPATIBLE_WITH", 
                        "source_gin": feeder_gin,
                        "target_gin": accessory_gin,
                        "source_category": "Feeder",
                        "target_category": "Feeder Accessory",
                        "relationship": "compatible_with",
                        "priority": priority,
                        "confidence": 0.7,
                        "context": {"powersource_gin": powersource_gin},
                        "source_file": powersource_name,
                        "sheet_name": "Feeder Accessories"
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing Feeder Accessory rule: {e}")
        
        return rules
    
    def _process_remote_sheet(self, df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Remotes sheet"""
        rules = []
        
        for _, row in df.iterrows():
            try:
                power_gin = self.pad_gin(str(row['GIN Powersource']).strip())
                feeder_gin = self.pad_gin(str(row['GIN Feeder']).strip())
                remote_gin = self.pad_gin(str(row['GIN Remotes']).strip())
                priority = row.get('Priorities', 1)
                
                # Only include rules for our target PowerSource
                if (power_gin == powersource_gin or power_gin == 'nan') and self._is_valid_gin(remote_gin):
                    rules.append({
                        "rule_id": f"{powersource_gin}_remote_{remote_gin}",
                        "rule_type": "COMPATIBLE_WITH",
                        "source_gin": remote_gin,
                        "target_gin": powersource_gin,
                        "source_category": "Remote",
                        "target_category": "PowerSource",
                        "relationship": "compatible_with", 
                        "priority": priority,
                        "confidence": 0.7,
                        "context": {
                            "requires_feeder": feeder_gin if self._is_valid_gin(feeder_gin) else None
                        },
                        "source_file": powersource_name,
                        "sheet_name": "Remotes"
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing Remote rule: {e}")
        
        return rules
    
    def _process_connectivity_sheet(self, df: pd.DataFrame, powersource_gin: str, powersource_name: str) -> List[Dict]:
        """Process Connectivity sheet"""
        rules = []
        
        for _, row in df.iterrows():
            try:
                power_gin = self.pad_gin(str(row['GIN Powersource']).strip())
                feeder_gin = self.pad_gin(str(row['GIN Feeder']).strip())
                connectivity_gin = self.pad_gin(str(row['GIN Connectivity']).strip())
                
                # Only include rules for our target PowerSource
                if (power_gin == powersource_gin or power_gin == 'nan') and self._is_valid_gin(connectivity_gin):
                    rules.append({
                        "rule_id": f"{powersource_gin}_connectivity_{connectivity_gin}",
                        "rule_type": "COMPATIBLE_WITH",
                        "source_gin": connectivity_gin,
                        "target_gin": powersource_gin,
                        "source_category": "Connectivity",
                        "target_category": "PowerSource",
                        "relationship": "compatible_with",
                        "priority": 1,
                        "confidence": 0.6,
                        "context": {
                            "requires_feeder": feeder_gin if self._is_valid_gin(feeder_gin) else None
                        },
                        "source_file": powersource_name,
                        "sheet_name": "Connectivity"
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing Connectivity rule: {e}")
        
        return rules
    
    def _is_valid_gin(self, gin: str) -> bool:
        """Check if GIN is valid (not nan, empty, or null)"""
        return gin and gin != 'nan' and gin.strip() != '' and gin.lower() != 'none'
    
    def generate_master_datasets(self) -> Dict[str, Any]:
        """Generate all 4 master datasets"""
        logger.info("=" * 60)
        logger.info("POWERSOURCE MASTER DATASET GENERATION")
        logger.info("=" * 60)
        
        # Step 1: Discover all related GINs
        self.discover_gins_from_golden_packages()
        self.discover_gins_from_rulesets()
        
        logger.info(f"\\n🎯 Master GIN List: {len(self.master_gin_list)} unique GINs")
        logger.info("\\nGIN Sources Summary:")
        for gin in sorted(self.master_gin_list):
            sources = set(self.gin_sources[gin])
            category = self.gin_categories.get(gin, 'Unknown')
            logger.info(f"  {gin} ({category}): {len(sources)} sources")
        
        # Step 2: Generate datasets
        logger.info("\\n" + "=" * 60)
        logger.info("GENERATING DATASETS")
        logger.info("=" * 60)
        
        product_catalog = self.create_enhanced_product_catalog()
        sales_data = self.create_filtered_sales_data()
        golden_packages = self.create_filtered_golden_packages()
        compatibility_rules = self.create_filtered_compatibility_rules()
        
        # Step 3: Save datasets
        output_dir = self.base_path.parent / "neo4j_datasets"
        output_dir.mkdir(exist_ok=True)
        
        datasets = {
            "product_catalog.json": product_catalog,
            "sales_data.json": sales_data,
            "golden_packages.json": golden_packages,
            "compatibility_rules.json": compatibility_rules
        }
        
        for filename, data in datasets.items():
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved: {file_path}")
        
        # Summary
        logger.info("\\n" + "=" * 60)
        logger.info("GENERATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Target PowerSources: {len(self.target_powersources)}")
        logger.info(f"Master GIN List: {len(self.master_gin_list)} GINs")
        logger.info(f"Product Catalog: {product_catalog['metadata']['total_products']} products")
        logger.info(f"Sales Records: {sales_data['metadata']['total_records']} records")
        logger.info(f"Golden Packages: {golden_packages['metadata']['total_packages']} packages")
        logger.info(f"Output Directory: {output_dir}")
        
        return {
            "master_gin_list": list(self.master_gin_list),
            "gin_categories": self.gin_categories,
            "datasets": datasets,
            "output_directory": str(output_dir)
        }

def main():
    # Test with target PowerSources
    target_powersources = [
        "0465350883",  # Warrior 500i
        "0465350884",  # Warrior 400i
        "0445555880",  # Warrior 750i 380-460V, CE
        "0445250880",  # Renegade ES 300i with cables
        "0446200880"   # Aristo 500ix
    ]
    
    extractor = PowerSourceMasterExtractor(target_powersources)
    results = extractor.generate_master_datasets()
    
    return results

if __name__ == "__main__":
    main()