#!/bin/bash

# Comprehensive Data Transformation Script
# Transforms data from Datasets/ folder to neo4jdatasets/ folder using data/dt tools
# Usage: ./scripts/transform_data.sh [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
DATA_DT_DIR="$BACKEND_DIR/data/dt"
DATASETS_DIR="$PROJECT_ROOT/Datasets"
NEO4J_DATASETS_DIR="$PROJECT_ROOT/neo4jdatasets"

# Default values
CONFIG_FILE="powersource_config.json"
VERBOSE=false
SKIP_VALIDATION=false
NO_BACKUP=false
FORCE_OVERWRITE=false
DRY_RUN=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}      Data Transformation Pipeline         ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${CYAN}Transform: Datasets/ → neo4jdatasets/${NC}"
    echo ""
}

print_footer() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}✅ Data Transformation Complete!${NC}"
    echo -e "${BLUE}============================================${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Description:"
    echo "  Transform raw datasets from Datasets/ to Neo4j-ready format in neo4jdatasets/"
    echo ""
    echo "Options:"
    echo "  -c, --config FILE        PowerSource configuration file (default: powersource_config.json)"
    echo "  -p, --powersources LIST  Comma-separated PowerSource GINs (overrides config)"
    echo "  -a, --add-powersource GIN Add single PowerSource to existing config"
    echo "  -v, --verbose            Enable verbose logging"
    echo "  -s, --skip-validation    Skip validation checks (faster execution)"
    echo "  -n, --no-backup         Skip backup creation"
    echo "  -f, --force             Force overwrite existing neo4jdatasets"
    echo "  -d, --dry-run           Show what would be done without executing"
    echo "  --no-simplified         Skip simplified product generation"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Use default config"
    echo "  $0 --config my_config.json --verbose       # Custom config with verbose output"
    echo "  $0 --powersources \"0446200880,0465350883\"   # Specific PowerSources"
    echo "  $0 --add-powersource \"0445100880\"           # Add new PowerSource"
    echo "  $0 --force --verbose                        # Force overwrite with logging"
    echo "  $0 --dry-run                               # Preview what will be done"
    echo ""
    echo "Input Sources:"
    echo "  📁 $DATASETS_DIR/"
    echo ""
    echo "Output Destination:"
    echo "  📁 $NEO4J_DATASETS_DIR/"
}

# Function to validate environment
validate_environment() {
    print_status "Validating environment..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if we're in the right directory structure
    if [[ ! -d "$BACKEND_DIR" ]]; then
        print_error "Backend directory not found: $BACKEND_DIR"
        print_error "Please run this script from the Recommender project root"
        exit 1
    fi
    
    if [[ ! -d "$DATA_DT_DIR" ]]; then
        print_error "Data transformation directory not found: $DATA_DT_DIR"
        exit 1
    fi
    
    if [[ ! -f "$DATA_DT_DIR/powersource_orchestrator.py" ]]; then
        print_error "PowerSource orchestrator not found: $DATA_DT_DIR/powersource_orchestrator.py"
        exit 1
    fi
    
    if [[ ! -d "$DATASETS_DIR" ]]; then
        print_error "Source datasets directory not found: $DATASETS_DIR"
        print_error "Please ensure Datasets/ folder exists in project root"
        exit 1
    fi
    
    print_status "✅ Environment validation passed"
}

# Function to check output directory
check_output_directory() {
    if [[ -d "$NEO4J_DATASETS_DIR" ]] && [[ "$FORCE_OVERWRITE" != true ]]; then
        print_warning "Output directory already exists: $NEO4J_DATASETS_DIR"
        echo -e "${YELLOW}Existing files may be overwritten. Use --force to proceed automatically.${NC}"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Operation cancelled by user"
            exit 0
        fi
    fi
    
    # Create output directory if it doesn't exist
    mkdir -p "$NEO4J_DATASETS_DIR"
    print_status "Output directory ready: $NEO4J_DATASETS_DIR"
}

# Function to show dry run information
show_dry_run() {
    print_header
    print_status "🔍 DRY RUN MODE - Showing what would be executed"
    echo ""
    
    echo -e "${CYAN}Source Directory:${NC}"
    echo "  📁 $DATASETS_DIR"
    echo ""
    
    echo -e "${CYAN}Output Directory:${NC}"
    echo "  📁 $NEO4J_DATASETS_DIR"
    echo ""
    
    echo -e "${CYAN}Transformation Command:${NC}"
    echo "  cd $BACKEND_DIR"
    echo "  python data/dt/powersource_orchestrator.py $*"
    echo ""
    
    echo -e "${CYAN}Expected Output Files:${NC}"
    echo "  📦 product_catalog.json        - Enhanced product catalog"
    echo "  🔗 compatibility_rules.json    - Extracted compatibility rules" 
    echo "  🏆 golden_packages.json        - Filtered golden packages"
    echo "  💰 sales_data.json            - Complete combo sales data"
    echo "  📊 generation_summary.json     - Processing metadata"
    echo ""
    
    print_status "Use without --dry-run to execute the transformation"
    exit 0
}

# Parse command line arguments
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            ARGS+=("--config" "$2")
            shift 2
            ;;
        -p|--powersources)
            POWERSOURCES="$2"
            ARGS+=("--powersources" "$2")
            shift 2
            ;;
        -a|--add-powersource)
            ADD_POWERSOURCE="$2"
            ARGS+=("--add-powersource" "$2")
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            ARGS+=("--verbose")
            shift
            ;;
        -s|--skip-validation)
            SKIP_VALIDATION=true
            ARGS+=("--skip-validation")
            shift
            ;;
        -n|--no-backup)
            NO_BACKUP=true
            ARGS+=("--no-backup")
            shift
            ;;
        -f|--force)
            FORCE_OVERWRITE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-simplified)
            ARGS+=("--no-simplified")
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Handle dry run
if [[ "$DRY_RUN" == true ]]; then
    show_dry_run "${ARGS[@]}"
fi

# Print header
print_header

# Validate environment
validate_environment

# Check output directory
check_output_directory

# Show configuration
print_status "Configuration:"
echo "  📁 Source: $DATASETS_DIR"
echo "  📁 Output: $NEO4J_DATASETS_DIR"
echo "  🔧 Backend: $BACKEND_DIR"
if [[ -n "$POWERSOURCES" ]]; then
    echo "  🎯 PowerSources: $POWERSOURCES"
elif [[ -n "$ADD_POWERSOURCE" ]]; then
    echo "  ➕ Adding PowerSource: $ADD_POWERSOURCE"
else
    echo "  ⚙️  Config: $CONFIG_FILE"
fi
echo "  📊 Verbose: $VERBOSE"
echo "  ⚡ Skip Validation: $SKIP_VALIDATION"
echo "  💾 No Backup: $NO_BACKUP"
echo ""

# Change to backend directory for execution
cd "$BACKEND_DIR"
print_status "Changed to backend directory: $BACKEND_DIR"

# Build and execute command
COMMAND="python data/dt/powersource_orchestrator.py"
for arg in "${ARGS[@]}"; do
    COMMAND="$COMMAND $arg"
done

print_status "Executing transformation..."
print_status "Command: $COMMAND"
echo ""

# Execute the transformation
eval $COMMAND

EXIT_CODE=$?

# Check execution result
if [[ $EXIT_CODE -eq 0 ]]; then
    print_footer
    echo ""
    echo -e "${GREEN}Generated Files in ${CYAN}$NEO4J_DATASETS_DIR${GREEN}:${NC}"
    if [[ -d "$NEO4J_DATASETS_DIR" ]]; then
        for file in "$NEO4J_DATASETS_DIR"/*.json; do
            if [[ -f "$file" ]]; then
                filename=$(basename "$file")
                size=$(ls -lh "$file" | awk '{print $5}')
                echo "  📄 $filename ($size)"
            fi
        done
    fi
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. 📋 Review generated datasets in neo4jdatasets/"
    echo "  2. 🔄 Run ./scripts/load_data.sh to load into Neo4j"
    echo "  3. 🧪 Test recommendation queries against loaded data"
    echo ""
else
    echo ""
    print_error "❌ Data transformation failed with exit code: $EXIT_CODE"
    echo ""
    echo -e "${YELLOW}Troubleshooting Tips:${NC}"
    echo "  • Check that all source files exist in $DATASETS_DIR"
    echo "  • Verify PowerSource GINs are valid 10-character format"
    echo "  • Run with --verbose for detailed error information"
    echo "  • Use --skip-validation for faster debugging"
    echo "  • Check Python dependencies are installed"
    exit $EXIT_CODE
fi