#!/usr/bin/env python3
"""
Create Enhanced Simplified Product Output
Generate comprehensive simplified product catalog with proper categorization and specs
"""

import json
import re
from typing import Dict, List, Any, Optional

def pad_gin_number(gin: str) -> str:
    """Pad GIN number to 10 characters with leading zeros"""
    if gin is None:
        return ""
    gin_str = str(gin).strip()
    return gin_str.zfill(10)

def clean_html_description(description: str) -> str:
    """Clean HTML tags and extra whitespace from description"""
    if not description:
        return ""
    
    # Remove HTML tags
    clean_desc = re.sub(r'<[^>]+>', '', description)
    # Replace HTML entities
    clean_desc = clean_desc.replace('&nbsp;', ' ')
    clean_desc = clean_desc.replace('&lt;', '<')
    clean_desc = clean_desc.replace('&gt;', '>')
    clean_desc = clean_desc.replace('&amp;', '&')
    clean_desc = re.sub(r'&[^;]+;', ' ', clean_desc)
    # Clean extra whitespace and newlines
    clean_desc = ' '.join(clean_desc.split())
    
    return clean_desc

def extract_specs_and_features(specs_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract meaningful specs and features from the specs object"""
    if not specs_dict:
        return {}
    
    # Define meaningful spec fields
    meaningful_specs = {}
    
    for key, value in specs_dict.items():
        # Skip null/empty values
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            continue
        
        # Clean key names for readability
        clean_key = clean_spec_key(key)
        meaningful_specs[clean_key] = value
    
    return meaningful_specs

def clean_spec_key(key: str) -> str:
    """Convert camelCase/technical keys to readable format"""
    # Add spaces before capital letters
    key = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
    # Capitalize first letter and convert to title case
    key = key.replace('_', ' ').title()
    # Fix common technical terms
    key = key.replace('Kva', 'KVA')
    key = key.replace('Kvac', 'KVAC') 
    key = key.replace('Kv', 'KV')
    key = key.replace('Arc Data', 'ArcData')
    
    return key

# Removed duplicate function - using only the correct one below

def determine_enhanced_category(catalog_category: str, product_name: str, product_description: str, original_category: str = "") -> str:
    """Enhanced category determination with intelligent fallback for Unknown categories"""
    
    # If catalog category is not Unknown, use it
    if catalog_category and catalog_category != "Unknown":
        return catalog_category
    
    # Fallback: Analyze name and description for category keywords
    combined_text = f"{product_name} {product_description}".lower()
    
    category_keywords = {
        'Torch': ['torch', 'gouging', 'tig', 'mig', 'welding gun', 'electrode holder'],
        'Feeder': ['feeder', 'wire feed', 'spool', 'drive roll', 'push pull'],
        'PowerSource': ['welder', 'power source', 'welding machine', 'inverter'],
        'Cooler': ['cooler', 'cooling', 'water cool', 'coolant', 'radiator'],
        'Interconnector': ['cable', 'interconnect', 'connection', 'lead', 'welding cable'],
        'WeldingAccessory': ['accessory', 'consumable', 'replacement', 'spare', 'head'],
        'Remote': ['remote', 'control', 'pendant', 'foot control']
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            return category
    
    # Final fallback: try to extract from original ENG category
    if original_category:
        if "Torch" in original_category:
            return "Torch"
        elif "Feeder" in original_category:
            return "Feeder"
        elif "Accessories" in original_category:
            return "WeldingAccessory"
    
    return "Unknown"

def create_enhanced_simplified_output(master_gin_list: List[str] = None, synthetic_products: List[Dict] = None):
    """Create enhanced simplified product output using product_catalog.json as single source"""
    try:
        # Load product catalog as single source of truth
        catalog_file = '/Users/bharath/Desktop/AgenticAI/Recommender/neo4j_datasets/product_catalog.json'
        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)
        
        # Get products from product catalog
        catalog_products = catalog_data.get('products', [])
        print(f"Processing {len(catalog_products)} products from product catalog (single source)...")
        
        enhanced_products = []
        category_counts = {}
        
        for i, catalog_product in enumerate(catalog_products):
            try:
                # Extract primary data from catalog
                gin_number = pad_gin_number(catalog_product.get('gin', ''))
                product_name = catalog_product.get('name', f'Product {gin_number}')
                is_available = catalog_product.get('available', True)
                source = catalog_product.get('source', 'catalog')
                
                        # Handle description and additional data based on source
                if source == 'synthetic':
                    # For synthetic products: use ruleset_context data
                    ruleset_context = catalog_product.get('ruleset_context', {})
                    product_description = ruleset_context.get('description', catalog_product.get('description', f'Product {gin_number}'))
                    specifications = extract_specs_and_features(ruleset_context.get('specs', {}))
                    original_category = ruleset_context.get('compatibility_info', 'Synthetic Product')
                    image_url = None
                    datasheet_url = None
                    countries_available = []
                    last_modified = ''
                else:
                    # For catalog products: use original_data attributes
                    product_description = catalog_product.get('description', f'Product {gin_number}')
                    original_data_attrs = catalog_product.get('original_data', {}).get('data', {}).get('attributes', {})
                    specifications = extract_specs_and_features(original_data_attrs.get('specs', {}))
                    original_categories = original_data_attrs.get('category', [])
                    original_category = original_categories[0] if original_categories else 'Unknown'
                    image_url = original_data_attrs.get('Imageurl')
                    datasheet_url = original_data_attrs.get('datasheeturl')
                    countries_available = original_data_attrs.get('countrydisplay', [])
                    last_modified = catalog_product.get('original_data', {}).get('last_modified', '')
                
                # Enhanced category determination with intelligent fallback
                catalog_category = catalog_product.get('category', 'Unknown')
                component_category = determine_enhanced_category(
                    catalog_category, product_name, product_description, original_category
                )
                
                enhanced_product = {
                    'gin_number': gin_number,
                    'product_name': product_name,
                    'product_description': product_description,
                    'original_category': original_category,
                    'component_category': component_category,
                    'specifications': specifications,
                    'image_url': image_url,
                    'datasheet_url': datasheet_url,
                    'countries_available': countries_available,
                    'is_available': is_available,
                    'last_modified': last_modified,
                    'product_id': gin_number
                }
                
                enhanced_products.append(enhanced_product)
                category_counts[component_category] = category_counts.get(component_category, 0) + 1
                
                if (i + 1) % 50 == 0:
                    print(f"Processed {i + 1}/{len(catalog_products)} products...")
                    
            except Exception as e:
                print(f"Error processing product {i}: {e}")
        
        # Note: synthetic_products parameter maintained for compatibility but not used
        # All products (catalog and synthetic) are now processed from product_catalog.json
        
        # Save enhanced products
        output_file = '/Users/bharath/Desktop/AgenticAI/Recommender/neo4j_datasets/enhanced_simplified_products.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_products, f, indent=2, ensure_ascii=False)
        
        print(f"\nEnhanced products saved to: {output_file}")
        print(f"Total processed: {len(enhanced_products)} products")
        
        print("\n=== CATEGORY DISTRIBUTION ===")
        for category, count in sorted(category_counts.items()):
            print(f"{category}: {count}")
        
        # Show source breakdown from original catalog data
        source_counts = {}
        for catalog_product in catalog_products:
            source = catalog_product.get('source', 'catalog')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print("\n=== SOURCE BREAKDOWN ===")
        for source, count in source_counts.items():
            print(f"{source}: {count}")
        
        return True
        
    except Exception as e:
        print(f"Error creating enhanced output: {e}")
        return False

def load_master_products_from_catalog():
    """Load product catalog - simplified for new single-source approach"""
    try:
        catalog_file = '/Users/bharath/Desktop/AgenticAI/Recommender/neo4j_datasets/product_catalog.json'
        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)
        
        # Count products by source for reporting
        products = catalog_data.get('products', [])
        catalog_count = sum(1 for p in products if p.get('source') == 'catalog')
        synthetic_count = sum(1 for p in products if p.get('source') == 'synthetic')
        
        print(f"Loaded product catalog: {len(products)} total products ({catalog_count} catalog, {synthetic_count} synthetic)")
        
        # Return empty sets for compatibility - new approach processes everything in create_enhanced_simplified_output
        return set(), []
        
    except Exception as e:
        print(f"Error loading master products: {e}")
        return None, None

if __name__ == "__main__":
    # Load master GIN list from PowerSource extraction
    master_gins = load_master_gin_list_from_product_catalog()
    
    if master_gins:
        print("Creating enhanced simplified output with PowerSource-derived GIN filtering...")
        create_enhanced_simplified_output(master_gins)
    else:
        print("No master GIN list found, processing all products...")
        create_enhanced_simplified_output()