#!/usr/bin/env python3
"""
CSV Exporter for GIN Extraction Data
Creates clean CSV with Excel file, sheet, GIN, category, description, and compatibility info
"""

import json
import pandas as pd
import csv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_gin_extraction_csv():
    """Export GIN extraction data to CSV format"""
    
    # Load the detailed extraction report
    report_file = '/Users/bharath/Desktop/AgenticAI/Recommender/neo4j_datasets/gin_extraction_report.json'
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        logger.info(f"Loaded extraction report with {len(report['extraction_details'])} records")
        
    except Exception as e:
        logger.error(f"Error loading report: {e}")
        return False
    
    # Prepare CSV data
    csv_data = []
    
    for detail in report['extraction_details']:
        # Determine compatibility inference based on context
        compatibility_info = infer_compatibility(detail)
        
        # Get description (from ENG.json if available, otherwise generate)
        description = get_product_description(detail)
        
        csv_row = {
            'Excel_File': detail['excel_file'],
            'Sheet_Name': detail['sheet_name'],
            'GIN': detail['gin'],
            'Category': detail['category'],
            'Description': description,
            'Compatibility_Inferred': compatibility_info,
            'Source_Type': detail['source_type'],
            'Column_Name': detail['column_name'],
            'PowerSource_Context': detail['powersource_gin'],
            'Row_Index': detail['row_index'],
            'Exists_in_ENG': 'Yes' if detail['exists_in_eng'] else 'No'
        }
        
        csv_data.append(csv_row)
    
    # Create DataFrame
    df = pd.DataFrame(csv_data)
    
    # Sort by Excel file, sheet, then GIN for better organization
    df = df.sort_values(['Excel_File', 'Sheet_Name', 'GIN'])
    
    # Export to CSV
    output_file = '/Users/bharath/Desktop/AgenticAI/Recommender/neo4j_datasets/gin_extraction_details.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    logger.info(f"CSV exported to: {output_file}")
    logger.info(f"Total records: {len(df)}")
    
    # Print summary statistics
    print("\\n" + "=" * 60)
    print("CSV EXPORT SUMMARY")
    print("=" * 60)
    print(f"Total Records: {len(df):,}")
    print(f"Unique GINs: {df['GIN'].nunique():,}")
    print(f"Unique Excel Files: {df['Excel_File'].nunique()}")
    print(f"Unique Sheets: {df['Sheet_Name'].nunique()}")
    
    print("\\nRecords by Excel File:")
    file_counts = df['Excel_File'].value_counts()
    for file, count in file_counts.items():
        print(f"  {file}: {count:,} records")
    
    print("\\nRecords by Category:")
    category_counts = df['Category'].value_counts()
    for category, count in category_counts.items():
        print(f"  {category}: {count:,} records")
    
    print("\\nSource Type Distribution:")
    source_counts = df['Source_Type'].value_counts()
    for source, count in source_counts.items():
        print(f"  {source}: {count:,} records ({count/len(df)*100:.1f}%)")
    
    print(f"\\nCSV file saved to: {output_file}")
    
    return True

def infer_compatibility(detail):
    """Infer compatibility information based on context"""
    powersource = detail['powersource_gin']
    sheet_name = detail['sheet_name']
    category = detail['category']
    gin = detail['gin']
    
    # Map PowerSource GINs to names for readability
    ps_names = {
        '0446200880': 'Aristo 500ix',
        '0465350883': 'Warrior 500i', 
        '0465350884': 'Warrior 400i',
        '0445555880': 'Warrior 750i',
        '0445250880': 'Renegade ES300'
    }
    
    ps_name = ps_names.get(powersource, f'PowerSource {powersource}')
    
    # Base compatibility
    compatibility = f"Compatible with {ps_name}"
    
    # Add context based on sheet
    if 'Init' in sheet_name:
        if category == 'PowerSource':
            compatibility = f"Primary PowerSource for {ps_name}"
        else:
            compatibility = f"Core component for {ps_name}"
    elif 'Mandatory' in sheet_name:
        compatibility = f"Required component for {ps_name}"
    elif 'Conditional' in sheet_name or 'Cond' in sheet_name:
        compatibility = f"Optional component for {ps_name} (conditional)"
    elif 'Accessories' in sheet_name or 'Acc' in sheet_name:
        compatibility = f"Accessory for {ps_name}"
    elif 'Wears' in sheet_name:
        compatibility = f"Wear part for {ps_name}"
    
    # Add category-specific context
    if category in ['Feeder', 'Cooler', 'Torch', 'Interconnector']:
        compatibility += f" ({category.lower()} role)"
    elif 'Accessory' in category:
        compatibility += f" (accessory role)"
    elif category == 'Remote':
        compatibility += f" (remote control)"
    
    # Handle synthetic products
    if gin.startswith('F000'):
        compatibility = f"Placeholder - No {category.lower()} available for {ps_name}"
    
    return compatibility

def get_product_description(detail):
    """Get product description from ENG.json or generate one"""
    if detail['exists_in_eng']:
        # Would need to load ENG.json again to get description
        # For now, use the product name from the detail
        return detail['product_name']
    else:
        # Generate description for synthetic products
        gin = detail['gin']
        category = detail['category']
        
        if gin.startswith('F000'):
            # Handle special synthetic codes
            synthetic_descriptions = {
                'F000000002': 'No Cooler Available - Placeholder',
                'F000000003': 'No Torch Available - Placeholder', 
                'F000000005': 'No Cooler Available - Standalone',
                'F000000006': 'No Torch Available - Standalone',
                'F000000007': 'No Feeder Available - Placeholder',
                'F000000008': 'No Interconnector Available - Placeholder',
                'F000000009': 'No Feeder Accessory Available - Placeholder',
                'F000000010': 'No Accessory Available - Placeholder',
                'F000000011': 'No Connectivity Available - Placeholder'
            }
            return synthetic_descriptions.get(gin, f'Synthetic {category} {gin}')
        else:
            # Generate description for missing products
            if category == 'Interconnector':
                return f'Interconnector Cable {gin}'
            elif category == 'Feeder':
                return f'Wire Feeder {gin}'
            elif category == 'Cooler':
                return f'Cooling Unit {gin}'
            elif category == 'Torch':
                return f'Welding Torch {gin}'
            elif 'Accessory' in category:
                return f'{category} {gin}'
            else:
                return f'{category} Product {gin}'

def main():
    """Main export function"""
    print("Exporting GIN extraction data to CSV...")
    success = export_gin_extraction_csv()
    
    if success:
        print("✅ CSV export completed successfully!")
    else:
        print("❌ CSV export failed!")

if __name__ == "__main__":
    main()