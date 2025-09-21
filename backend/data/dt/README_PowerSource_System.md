# PowerSource Data Extraction System

## Overview

The PowerSource Data Extraction System is a comprehensive Neo4j dataset generation pipeline that transforms raw welding equipment data into structured, relationship-rich datasets ready for graph database loading. The system takes PowerSource GIN(s) as input and automatically discovers, processes, and formats all related product, sales, package, and compatibility data.

## System Architecture

```
PowerSource Config → Orchestrator → [4 Master Datasets] → Neo4j
     ↓                    ↓
Source Files:        Processing:
- ENG.json           - GIN Discovery  
- Golden Packages    - Product Enhancement
- Sales Data         - Sales Filtering
- Ruleset Files      - Rule Extraction
```

## Core Components

### 1. PowerSource Orchestrator (`dt/powersource_orchestrator.py`)
- **Purpose**: Main coordination pipeline
- **Input**: PowerSource configuration file
- **Output**: 4 Neo4j-ready dataset files
- **Features**: Validation, backup, category consistency checking

### 2. Master Extractor (`dt/powersource_master_extractor.py`)
- **Purpose**: Core data processing engine
- **Features**: GIN discovery, synthetic product generation, compatibility rule extraction
- **Processing**: Transforms raw Excel/CSV data into structured JSON

### 3. Product Catalog Transformer (`dt/product_catalog_transformer.py`)
- **Purpose**: Product data enhancement and categorization
- **Features**: ERP filtering, synthetic product integration, category consistency

## File Structure

```
AgenticAI/Recommender/
├── dt/                              # Data Transformation Scripts
│   ├── powersource_orchestrator.py # Main orchestrator
│   ├── powersource_master_extractor.py # Core extraction engine
│   └── product_catalog_transformer.py # Product processing
├── Datasets/                        # Source Data
│   ├── ENG.json                    # Master product catalog
│   ├── golden_pkg_format_V2.xlsx   # Golden package configurations
│   ├── sales_data_cleaned.csv      # Historical sales data
│   └── Ruleset/                    # PowerSource compatibility rules
│       ├── HIP configurator_Aristo 500ix_08092025.xlsx
│       ├── HIP configurator_Warrior_08092025.xlsx
│       ├── HIP configurator_Warrior750_08092025.xlsb.xlsx
│       ├── HIP configurator_Renegade ES300_08092025.xlsx
│       └── [Additional PowerSource rulesets]
├── neo4j_datasets/                 # Generated Output
│   ├── product_catalog.json        # Enhanced product catalog
│   ├── compatibility_rules.json    # Extracted compatibility rules
│   ├── golden_packages.json        # Filtered golden packages
│   ├── sales_data.json            # Complete combo sales data
│   └── generation_summary.json     # Processing metadata
├── powersource_config.json         # PowerSource configuration
└── README_PowerSource_System.md    # This documentation
```

## Quick Start

### 1. Basic Execution
```bash
# Run with existing PowerSource configuration
python dt/powersource_orchestrator.py --config powersource_config.json

# Run with custom PowerSources
python dt/powersource_orchestrator.py --powersources "0446200880,0465350883"

# Add a new PowerSource to existing configuration
python dt/powersource_orchestrator.py --add-powersource "0445100880"
```

### 2. Configuration Options
```bash
# Skip validation (faster execution)
python dt/powersource_orchestrator.py --config powersource_config.json --skip-validation

# Disable backup creation
python dt/powersource_orchestrator.py --config powersource_config.json --no-backup

# Disable simplified product generation
python dt/powersource_orchestrator.py --config powersource_config.json --no-simplified

# Verbose logging
python dt/powersource_orchestrator.py --config powersource_config.json --verbose
```

## Adding New PowerSources

### Step 1: Update Configuration
```json
{
  "powersources": {
    "0465350883": "Warrior 500i",
    "0465350884": "Warrior 400i", 
    "0445555880": "Warrior 750i 380-460V, CE",
    "0445250880": "Renegade ES 300i with cables",
    "0446200880": "Aristo 500ix",
    "NEW_GIN": "New PowerSource Name"
  }
}
```

### Step 2: Prepare Source Files

#### Required Files:
1. **Golden Package Entry**: Add row in `golden_pkg_format_V2.xlsx`
2. **Sales Data**: Include records in `sales_data_cleaned.csv`
3. **Ruleset File**: Add `HIP configurator_NewPowerSourceName_MMDDYYYY.xlsx`
4. **Product Data**: Ensure products exist in `ENG.json` (or system will create synthetic)

#### Ruleset File Requirements:
The Excel ruleset must contain these sheets:
- **Init**: PowerSource → Feeder/Cooler determination rules
- **Torches**: Torch compatibility rules
- **Interconn**: Interconnector compatibility rules
- **Powersource Accessories**: Power accessory compatibility
- **Feeder Accessories**: Feeder accessory compatibility  
- **Remotes**: Remote control compatibility
- **Connectivity**: Connectivity accessory rules

### Step 3: Execute Pipeline
```bash
python dt/powersource_orchestrator.py --config powersource_config.json
```

## Generated Datasets

### 1. Product Catalog (`product_catalog.json`)
```json
{
  "metadata": {
    "total_products": 249,
    "existing_products": 192,
    "synthetic_products": 57,
    "target_powersources": ["0446200880", "0465350883", ...]
  },
  "products": [
    {
      "gin_number": "0446200880",
      "component_category": "PowerSource",
      "description": "Aristo 500ix",
      "is_synthetic": false
    }
  ]
}
```

### 2. Compatibility Rules (`compatibility_rules.json`)
```json
{
  "metadata": {
    "total_rules": 1029,
    "target_powersources": ["0446200880", "0465350883", ...]
  },
  "compatibility_rules": [
    {
      "rule_id": "0465350883_determines_feeder_0465250881",
      "rule_type": "DETERMINES",
      "source_gin": "0465350883",
      "target_gin": "0465250881",
      "source_category": "PowerSource",
      "target_category": "Feeder",
      "relationship": "determines",
      "priority": 1,
      "confidence": 1.0,
      "source_file": "Warrior 500i",
      "sheet_name": "Init"
    }
  ]
}
```

### 3. Golden Packages (`golden_packages.json`)
```json
{
  "metadata": {
    "total_packages": 7,
    "target_powersources": ["0446200880", "0465350883", ...]
  },
  "golden_packages": [
    {
      "package_id": 1,
      "powersource_gin": "0446200880",
      "powersource_name": "Aristo 500ix",
      "components": {
        "feeder": {"gin": "0445800894", "name": "RobustFeed Pulse..."},
        "cooler": {"gin": "0465427880", "name": "Cool 2"},
        "interconnector": {"gin": "0446255891", "name": "Intercon. RF..."},
        "torch": {"gin": "0700026415", "name": "EXEOR PSF 420W..."}
      }
    }
  ]
}
```

### 4. Sales Data (`sales_data.json`)
```json
{
  "metadata": {
    "total_records": 4108,
    "unique_orders": 644,
    "complete_combo_orders": 644,
    "filtering_rule": "Orders must contain PowerSource + Feeder + Cooler minimum combo"
  },
  "sales_records": [
    {
      "order_id": "ORD-001",
      "powersource_gin": "0446200880",
      "feeder_gin": "0445800894",
      "cooler_gin": "0465427880",
      "quantity": 1,
      "order_date": "2024-01-15"
    }
  ]
}
```

## Validation and Quality Checks

### Automatic Validations:
1. **Prerequisites Check**: Verifies all source files exist
2. **PowerSource GIN Validation**: Ensures valid 10-character format
3. **Category Consistency**: Checks component categorization across all sources
4. **Golden Package Presence**: Validates each PowerSource has golden packages
5. **GIN Discovery Threshold**: Ensures minimum GIN discovery (default: 10)

### Manual Validation Commands:
```bash
# Check category consistency only
python dt/category_consistency_analyzer.py

# Validate specific PowerSource
python dt/powersource_orchestrator.py --powersources "0446200880" --skip-validation
```

## Advanced Configuration

### PowerSource Config (`powersource_config.json`)
```json
{
  "powersources": {
    "GIN": "Name"
  },
  "validation_settings": {
    "run_category_consistency": true,
    "require_golden_package_presence": true,
    "min_gin_discovery_threshold": 10
  },
  "output_settings": {
    "generate_simplified_catalog": true,
    "include_synthetic_products": true,
    "create_backup": false
  }
}
```

### Environment Variables:
```bash
export POWERSOURCE_BASE_PATH="/custom/path/to/datasets"
export NEO4J_OUTPUT_PATH="/custom/neo4j/import"
```

## Troubleshooting

### Common Issues:

**1. Missing Ruleset File**
```
Error: No ruleset file found for: PowerSource Name
Solution: Add HIP configurator_PowerSourceName_MMDDYYYY.xlsx to Datasets/Ruleset/
```

**2. GIN Format Mismatch**
```
Error: Invalid GIN format
Solution: Ensure GINs are 10-character strings with leading zeros (e.g., "0446200880")
```

**3. Category Inconsistency**
```
Warning: Category inconsistencies found
Solution: Review component categorization in source files
```

**4. No Golden Packages Found**
```
Error: No golden packages found for PowerSource
Solution: Add entries to golden_pkg_format_V2.xlsx
```

### Debug Commands:
```bash
# Verbose logging
python dt/powersource_orchestrator.py --config powersource_config.json --verbose

# Skip problematic validations
python dt/powersource_orchestrator.py --config powersource_config.json --skip-validation

# Process single PowerSource for debugging
python dt/powersource_orchestrator.py --powersources "0446200880"
```

## Performance Optimization

### Large Dataset Handling:
- **Batch Processing**: System handles thousands of products efficiently
- **Memory Management**: Optimized for large Excel file processing
- **Incremental Updates**: Only processes new/changed PowerSources

### Execution Time Estimates:
- **5 PowerSources**: ~45 seconds
- **10 PowerSources**: ~90 seconds
- **20 PowerSources**: ~3 minutes

## Neo4j Loading

After generation, load datasets into Neo4j:

```cypher
// Load products
LOAD CSV WITH HEADERS FROM 'file:///product_catalog.json' AS row
CREATE (p:Product {
  gin_number: row.gin_number,
  category: row.component_category,
  description: row.description,
  is_synthetic: toBoolean(row.is_synthetic)
});

// Load compatibility rules
LOAD CSV WITH HEADERS FROM 'file:///compatibility_rules.json' AS row
MATCH (source:Product {gin_number: row.source_gin})
MATCH (target:Product {gin_number: row.target_gin})
CREATE (source)-[r:COMPATIBLE_WITH {
  rule_type: row.rule_type,
  relationship: row.relationship,
  priority: toInteger(row.priority),
  confidence: toFloat(row.confidence)
}]->(target);
```

## Support and Maintenance

### Log Files:
- Execution logs written to console with timestamps
- Error details included in orchestrator output
- Generation summary in `generation_summary.json`

### Backup Strategy:
- Automatic backup creation before major operations
- Backups stored in `backups/YYYYMMDD_HHMMSS/`
- Configurable via `create_backup` setting

### Updates and Maintenance:
- Source file updates processed automatically on next run
- Configuration changes take effect immediately
- No system restart required for new PowerSources

---

## Quick Reference Commands

```bash
# Basic execution
python dt/powersource_orchestrator.py --config powersource_config.json

# Add new PowerSource
python dt/powersource_orchestrator.py --add-powersource "NEW_GIN"

# Custom PowerSource list
python dt/powersource_orchestrator.py --powersources "GIN1,GIN2,GIN3"

# Fast execution (skip validation)
python dt/powersource_orchestrator.py --config powersource_config.json --skip-validation

# Debug mode
python dt/powersource_orchestrator.py --config powersource_config.json --verbose
```

This system provides a robust, scalable solution for welding equipment data extraction and Neo4j preparation with comprehensive validation, error handling, and documentation.