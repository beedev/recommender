#!/bin/bash

# PowerSource Data Extraction System - Quick Execution Script
# Usage: ./run_powersource_extraction.sh [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONFIG_FILE="powersource_config.json"
VERBOSE=false
SKIP_VALIDATION=false
NO_BACKUP=false

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
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}PowerSource Data Extraction${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --config FILE        PowerSource configuration file (default: powersource_config.json)"
    echo "  -p, --powersources LIST  Comma-separated PowerSource GINs (overrides config)"
    echo "  -a, --add-powersource GIN Add single PowerSource to existing config"
    echo "  -v, --verbose            Enable verbose logging"
    echo "  -s, --skip-validation    Skip validation checks (faster execution)"
    echo "  -n, --no-backup         Skip backup creation"
    echo "  --no-simplified         Skip simplified product generation"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Use default config"
    echo "  $0 --config my_config.json --verbose       # Custom config with verbose output"
    echo "  $0 --powersources \"0446200880,0465350883\"   # Specific PowerSources"
    echo "  $0 --add-powersource \"0445100880\"           # Add new PowerSource"
    echo "  $0 --skip-validation --no-backup           # Fast execution"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -p|--powersources)
            POWERSOURCES="$2"
            shift 2
            ;;
        -a|--add-powersource)
            ADD_POWERSOURCE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -s|--skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        -n|--no-backup)
            NO_BACKUP=true
            shift
            ;;
        --no-simplified)
            NO_SIMPLIFIED=true
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

# Print header
print_header

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "dt/powersource_orchestrator.py" ]]; then
    print_error "Please run this script from the AgenticAI/Recommender directory"
    exit 1
fi

# Build command
COMMAND="python dt/powersource_orchestrator.py"

# Add main argument (config, powersources, or add-powersource)
if [[ -n "$ADD_POWERSOURCE" ]]; then
    COMMAND="$COMMAND --add-powersource \"$ADD_POWERSOURCE\""
    print_status "Adding PowerSource: $ADD_POWERSOURCE"
elif [[ -n "$POWERSOURCES" ]]; then
    COMMAND="$COMMAND --powersources \"$POWERSOURCES\""
    print_status "Processing PowerSources: $POWERSOURCES"
else
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    COMMAND="$COMMAND --config \"$CONFIG_FILE\""
    print_status "Using configuration: $CONFIG_FILE"
fi

# Add optional flags
if [[ "$VERBOSE" == true ]]; then
    COMMAND="$COMMAND --verbose"
    print_status "Verbose logging enabled"
fi

if [[ "$SKIP_VALIDATION" == true ]]; then
    COMMAND="$COMMAND --skip-validation"
    print_warning "Skipping validation checks"
fi

if [[ "$NO_BACKUP" == true ]]; then
    COMMAND="$COMMAND --no-backup"
    print_warning "Backup creation disabled"
fi

if [[ "$NO_SIMPLIFIED" == true ]]; then
    COMMAND="$COMMAND --no-simplified"
    print_status "Simplified product generation disabled"
fi

# Show what we're about to run
print_status "Executing: $COMMAND"
echo ""

# Execute the command
eval $COMMAND

EXIT_CODE=$?

# Check execution result
if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    print_status "✅ PowerSource data extraction completed successfully!"
    print_status "Generated datasets are available in: neo4j_datasets/"
    echo ""
    echo -e "${GREEN}Generated Files:${NC}"
    echo "  📦 product_catalog.json        - Enhanced product catalog"
    echo "  🔗 compatibility_rules.json    - Extracted compatibility rules" 
    echo "  🏆 golden_packages.json        - Filtered golden packages"
    echo "  💰 sales_data.json            - Complete combo sales data"
    echo "  📊 generation_summary.json     - Processing metadata"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Review generated datasets in neo4j_datasets/"
    echo "  2. Load datasets into Neo4j using provided Cypher scripts"
    echo "  3. Test recommendation queries against loaded data"
else
    print_error "❌ PowerSource data extraction failed with exit code: $EXIT_CODE"
    echo ""
    echo -e "${YELLOW}Troubleshooting Tips:${NC}"
    echo "  • Check that all source files exist in Datasets/"
    echo "  • Verify PowerSource GINs are valid 10-character format"
    echo "  • Run with --verbose for detailed error information"
    echo "  • Use --skip-validation for faster debugging"
    exit $EXIT_CODE
fi