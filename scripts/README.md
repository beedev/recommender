# Scripts Directory

Comprehensive scripts for managing data pipeline and testing the welding equipment recommendation system.

## 📁 Script Overview

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `transform_data.sh` | Transform raw datasets | `Datasets/` | `neo4jdatasets/` |
| `load_data.sh` | Load into Neo4j | `neo4jdatasets/` | Neo4j Database |
| `deploy_data.sh` | Full pipeline orchestrator | `Datasets/` | Neo4j Database |
| `test_recommendations.py` | Test enterprise recommendation system | REST API | Test results |

## 🚀 Quick Start

### Complete Pipeline (Recommended)
```bash
# Full pipeline: transform + load with clean database
./scripts/deploy_data.sh

# With verbose logging
./scripts/deploy_data.sh --verbose

# Preview what will be executed
./scripts/deploy_data.sh --dry-run
```

### Step-by-Step Execution
```bash
# Step 1: Transform data
./scripts/transform_data.sh --verbose

# Step 2: Load into Neo4j
./scripts/load_data.sh --mode clean --verbose
```

## 📋 Detailed Usage

### 1. Data Transformation (`transform_data.sh`)

Transforms raw datasets from `Datasets/` folder to Neo4j-ready format in `neo4jdatasets/`.

```bash
# Basic usage
./scripts/transform_data.sh

# Custom configuration
./scripts/transform_data.sh --config my_config.json --verbose

# Specific PowerSources
./scripts/transform_data.sh --powersources "0446200880,0465350883"

# Force overwrite existing output
./scripts/transform_data.sh --force --verbose

# Preview transformation
./scripts/transform_data.sh --dry-run
```

**Options:**
- `-c, --config FILE` - PowerSource configuration file
- `-p, --powersources LIST` - Comma-separated PowerSource GINs
- `-a, --add-powersource GIN` - Add single PowerSource
- `-v, --verbose` - Enable verbose logging
- `-s, --skip-validation` - Skip validation checks
- `-n, --no-backup` - Skip backup creation
- `-f, --force` - Force overwrite existing neo4jdatasets
- `-d, --dry-run` - Preview without executing

### 2. Data Loading (`load_data.sh`)

Loads transformed datasets from `neo4jdatasets/` into Neo4j database.

```bash
# Clean load (default - deletes all existing data)
./scripts/load_data.sh

# Incremental load (preserves existing data)
./scripts/load_data.sh --mode incremental

# Specific files only
./scripts/load_data.sh --mode specific --files "products.json,sales.json"

# Test connection only
./scripts/load_data.sh --test-connection

# Preview loading
./scripts/load_data.sh --dry-run
```

**Loading Modes:**
- `clean` - Delete all data and load fresh (default)
- `incremental` - Add new data, preserve existing
- `specific` - Load only specified files

**Options:**
- `-m, --mode MODE` - Loading mode: clean|incremental|specific
- `-f, --files FILES` - Comma-separated list of files (specific mode)
- `-c, --cleanup-first` - Force cleanup before loading
- `-s, --skip-existing` - Skip existing records
- `-v, --verbose` - Enable verbose logging
- `-d, --dry-run` - Preview without executing
- `-t, --test-connection` - Test Neo4j connection only
- `--no-validation` - Skip reference validation
- `--no-backup` - Skip backup before clean loading

### 3. Master Orchestrator (`deploy_data.sh`)

Coordinates complete pipeline: transformation + loading in one command.

```bash
# Full pipeline
./scripts/deploy_data.sh

# Transform only
./scripts/deploy_data.sh --transform-only

# Load only (requires existing neo4jdatasets)
./scripts/deploy_data.sh --load-only

# Custom PowerSources with incremental loading
./scripts/deploy_data.sh --powersources "0446200880" --load-mode incremental

# Preview entire pipeline
./scripts/deploy_data.sh --dry-run
```

**Pipeline Modes:**
- `full` - Transform + Load (default)
- `transform` - Transform only (`--transform-only`)
- `load` - Load only (`--load-only`)

**Options:**
- `--transform-only` - Run transformation step only
- `--load-only` - Run loading step only
- `--load-mode MODE` - Loading mode: clean|incremental
- `-c, --config FILE` - PowerSource configuration file
- `-p, --powersources LIST` - Comma-separated PowerSource GINs
- `-f, --force` - Force overwrite existing outputs
- `--skip-existing` - Skip existing records (incremental)
- `--no-validation` - Skip reference validation
- `--no-backup` - Skip backup before clean loading
- `-v, --verbose` - Enable verbose logging
- `-d, --dry-run` - Preview without executing
- `-t, --test-connection` - Test Neo4j connection only

## 📂 Directory Structure

```
Recommender/
├── Datasets/                    # Raw source data
├── neo4jdatasets/              # Transformed Neo4j-ready data
├── backend/
│   ├── data/dt/                # Transformation tools
│   └── load_data.py            # Python data loader
└── scripts/                    # Shell scripts (this folder)
    ├── transform_data.sh       # Data transformation
    ├── load_data.sh           # Data loading
    ├── deploy_data.sh         # Master orchestrator
    └── README.md              # This file
```

## 🔄 Data Flow

```
Datasets/ 
    ↓ (transform_data.sh)
neo4jdatasets/
    ↓ (load_data.sh)
Neo4j Database
```

## 🧪 Testing & Validation

### Test Neo4j Connection
```bash
./scripts/load_data.sh --test-connection
```

### Preview Operations (Dry Run)
```bash
# Preview transformation
./scripts/transform_data.sh --dry-run

# Preview loading
./scripts/load_data.sh --dry-run

# Preview complete pipeline
./scripts/deploy_data.sh --dry-run
```

### Verbose Logging
```bash
# Add --verbose to any script for detailed output
./scripts/deploy_data.sh --verbose
```

## 🚨 Important Notes

### Clean Mode Warning
```bash
# Clean mode DELETES ALL DATA in Neo4j!
./scripts/load_data.sh --mode clean

# Always creates backup unless --no-backup specified
./scripts/load_data.sh --mode clean --no-backup
```

### File Locations
- **Source data**: Must be in `Datasets/` folder in project root
- **Transformed data**: Generated in `neo4jdatasets/` folder
- **Backend tools**: Located in `backend/data/dt/`

### Prerequisites
- Python 3 with required dependencies
- Neo4j database running and accessible
- Valid `.env` file with Neo4j credentials
- Source datasets in `Datasets/` folder

## 📊 Generated Files

After transformation, `neo4jdatasets/` contains:

| File | Description | Usage |
|------|-------------|-------|
| `product_catalog.json` | Enhanced product catalog with embeddings | Products and specifications |
| `compatibility_rules.json` | Product compatibility relationships | COMPATIBLE_WITH relationships |
| `golden_packages.json` | Pre-configured product bundles | Golden package recommendations |
| `sales_data.json` | Historical sales and combinations | Sales analysis and trends |
| `generation_summary.json` | Processing metadata and statistics | Audit trail and debugging |

## 🔧 Troubleshooting

### Common Issues

**Connection Failed:**
```bash
# Test connection
./scripts/load_data.sh --test-connection

# Check .env file has correct credentials
cat backend/.env
```

**Missing Files:**
```bash
# Run transformation first
./scripts/transform_data.sh --verbose

# Check source data exists
ls -la Datasets/
```

**Permission Errors:**
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

**Python Errors:**
```bash
# Check Python environment
cd backend
python3 -c "import neo4j, pandas, numpy; print('Dependencies OK')"
```

### Debug Commands

```bash
# Verbose logging
./scripts/deploy_data.sh --verbose

# Skip validation for faster debugging
./scripts/transform_data.sh --skip-validation --verbose

# Force overwrite for clean slate
./scripts/transform_data.sh --force

# Test individual components
./scripts/transform_data.sh --dry-run
./scripts/load_data.sh --test-connection
```

## 📈 Performance Tips

- Use `--skip-validation` for faster development cycles
- Use `--incremental` mode for regular updates
- Use `--verbose` only when debugging (slower)
- Use `--dry-run` to verify before execution
- Monitor disk space for large datasets

## 🔄 Typical Workflows

### Initial Setup
```bash
./scripts/deploy_data.sh --verbose
```

### Development Updates
```bash
./scripts/deploy_data.sh --load-mode incremental --verbose
```

### Production Deployment
```bash
./scripts/deploy_data.sh --verbose --no-backup
```

### Debugging
```bash
./scripts/deploy_data.sh --dry-run
./scripts/transform_data.sh --verbose --skip-validation
./scripts/load_data.sh --test-connection
```

---

# 🧪 Recommendation System Testing

## Test Script (`test_recommendations.py`)

Comprehensive testing tool for the enterprise welding equipment recommendation system.

### Quick Start

```bash
# Test all scenarios
python3 scripts/test_recommendations.py

# Test specific scenario with verbose output
python3 scripts/test_recommendations.py --scenario mig_aluminum --verbose

# Export results to JSON
python3 scripts/test_recommendations.py --export results.json
```

### Test Scenarios

| Scenario | Description | Expected Output |
|----------|-------------|-----------------|
| `mig_aluminum` | MIG welding for aluminum, 300A | PowerSource + Feeder + Cooler |
| `tig_stainless` | TIG welding for stainless steel, 200A | PowerSource + Cooler + Torch |
| `stick_steel` | Stick welding for carbon steel, 400A | PowerSource + accessories |
| `high_current_mig` | High current MIG for thick steel, 500A | Heavy-duty package |
| `multi_process` | Multi-process requirement (MIG + TIG) | Versatile equipment |

### Usage Options

```bash
# Basic testing
python3 scripts/test_recommendations.py

# Verbose output with detailed package info
python3 scripts/test_recommendations.py --verbose

# Test single scenario
python3 scripts/test_recommendations.py --scenario mig_aluminum

# Export results for analysis
python3 scripts/test_recommendations.py --export test_results.json

# Help and available scenarios
python3 scripts/test_recommendations.py --help
```

### Test Validation

The script validates each recommendation against:

- ✅ **Package Generation**: System returns packages
- ✅ **Process Match**: Correct welding process (MIG/TIG/Stick)
- ✅ **Material Match**: Correct material type (aluminum/steel/stainless)
- ✅ **Current Range**: Current rating within expected range
- ✅ **Required Components**: Has minimum required components
- ✅ **Sales Evidence**: Includes sales history analysis
- ✅ **Complete Package**: 7-category package completion

### Example Output

```
============================================================
        Welding Equipment Recommendation System Test        
============================================================
ℹ️  Testing against: http://localhost:8000
ℹ️  Session ID: test_session_1758386912
✅ Server is running: healthy
✅ NEO4J database connected
✅ POSTGRES database connected

============================================================
           Testing: MIG Welding - Aluminum (300A)           
============================================================
ℹ️  Sending request: I need MIG welding equipment for aluminum, 300 amp...
✅ Received 1 package(s)

Validation Results:
  ✅ Has Packages
  ✅ Correct Process
  ✅ Correct Material
  ✅ Current In Range
  ✅ Has Required Components
  ✅ Has Sales Evidence
  ✅ Complete Package
Success Rate: 100.0% (7/7)
Response Time: 2.45s

Package Details:
Package ID: expert_mig_aluminum_300a_pkg_001
Total Price: $15,450.00
Confidence: 92.5%
Processes: MIG
Materials: aluminum
Current Rating: 300 A

Components (7 categories):
  PowerSource: Warrior 500i (W500i) - 500A - $8,500.00
  Feeder: ESP-150 Wire Feeder - $2,100.00
  Cooler: CoolMate 3 - $1,250.00
  Torch: MIG Torch 400A - $850.00
  FeederAccessory: Wire Drive Kit - $420.00
  PowerSourceAccessory: Remote Control - $330.00
  Interconnector: 25ft Cable Set - $1,000.00
Sales Evidence: This combination sold 47 times in automotive sector...

============================================================
                        Test Summary                        
============================================================
Total Tests Run: 5
Successful Tests: 5/5
Overall Success: 100.0%
Avg Validation Rate: 85.7%
Avg Response Time: 3.2s
Total Packages Generated: 5

🎉 System is performing well!
```

### Prerequisites

- Backend server running on port 8000
- Neo4j database loaded with product data
- Python 3 with `requests` library
- Network access to localhost:8000

### Troubleshooting

**Server Connection Issues:**
```bash
# Check if server is running
curl http://localhost:8000/api/v1/health

# Start backend server
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Test Failures:**
```bash
# Run with verbose output for debugging
python3 scripts/test_recommendations.py --verbose

# Test specific scenario that's failing
python3 scripts/test_recommendations.py --scenario mig_aluminum --verbose
```

**Low Validation Rates:**
- Check if Neo4j database has product data loaded
- Verify sales data and golden packages are present
- Review system logs for processing errors