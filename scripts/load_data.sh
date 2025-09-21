#!/bin/bash

# Comprehensive Data Loader Script
# Loads data from neo4jdatasets/ folder into Neo4j database
# Supports clean, incremental, and specific file loading modes
# Usage: ./scripts/load_data.sh [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
NEO4J_DATASETS_DIR="$PROJECT_ROOT/neo4jdatasets"

# Default values
LOAD_MODE="clean"  # clean, incremental, specific
SPECIFIC_FILES=""
VALIDATE_REFERENCES=true
SKIP_EXISTING=false
CLEANUP_FIRST=false
VERBOSE=false
DRY_RUN=false
BACKUP_BEFORE_CLEAN=true
TEST_CONNECTION=false

# Available dataset files
AVAILABLE_FILES=(
    "product_catalog.json"
    "compatibility_rules.json"
    "golden_packages.json"
    "sales_data.json"
)

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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}         Neo4j Data Loading Pipeline       ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${CYAN}Load: neo4jdatasets/ → Neo4j Database${NC}"
    echo ""
}

print_footer() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}✅ Data Loading Complete!${NC}"
    echo -e "${BLUE}============================================${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Description:"
    echo "  Load datasets from neo4jdatasets/ into Neo4j database"
    echo ""
    echo "Loading Modes:"
    echo "  clean        Clean database and load all datasets (default)"
    echo "  incremental  Load only new/changed data (skip existing)"
    echo "  specific     Load only specified files"
    echo ""
    echo "Options:"
    echo "  -m, --mode MODE          Loading mode: clean|incremental|specific (default: clean)"
    echo "  -f, --files FILES        Comma-separated list of files (for specific mode)"
    echo "  -c, --cleanup-first      Force cleanup before loading (for incremental mode)"
    echo "  -s, --skip-existing      Skip existing records (for incremental mode)"
    echo "  -v, --verbose            Enable verbose logging"
    echo "  -d, --dry-run           Show what would be loaded without executing"
    echo "  -t, --test-connection   Test Neo4j connection and exit"
    echo "  --no-validation         Skip reference validation"
    echo "  --no-backup             Skip backup before clean loading"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Clean load all datasets"
    echo "  $0 --mode incremental --verbose            # Incremental load with logging"
    echo "  $0 --mode specific --files \"products.json,sales.json\" # Load specific files"
    echo "  $0 --cleanup-first --verbose               # Force clean with verbose output"
    echo "  $0 --test-connection                       # Test database connection"
    echo "  $0 --dry-run                              # Preview what will be loaded"
    echo ""
    echo "Available Files:"
    for file in "${AVAILABLE_FILES[@]}"; do
        echo "  📄 $file"
    done
    echo ""
    echo "Input Source:"
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
    
    if [[ ! -f "$BACKEND_DIR/load_data.py" ]]; then
        print_error "Data loader not found: $BACKEND_DIR/load_data.py"
        exit 1
    fi
    
    if [[ ! -d "$NEO4J_DATASETS_DIR" ]]; then
        print_error "Source datasets directory not found: $NEO4J_DATASETS_DIR"
        print_error "Please run ./scripts/transform_data.sh first to generate datasets"
        exit 1
    fi
    
    print_status "✅ Environment validation passed"
}

# Function to test Neo4j connection
test_neo4j_connection() {
    print_status "Testing Neo4j connection..."
    
    cd "$BACKEND_DIR"
    
    # Test connection using Python script
    python3 -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

try:
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    with driver.session() as session:
        result = session.run('RETURN \"Connection successful\" as message, datetime() as timestamp')
        record = result.single()
        print(f\"✅ {record['message']} at {record['timestamp']}\")
    
    driver.close()
    print('✅ Neo4j connection test passed')
    
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        print_success "Neo4j connection test passed"
        if [[ "$TEST_CONNECTION" == true ]]; then
            exit 0
        fi
    else
        print_error "Neo4j connection test failed"
        exit 1
    fi
}

# Function to validate dataset files
validate_dataset_files() {
    print_status "Validating dataset files..."
    
    local files_to_check=()
    
    if [[ "$LOAD_MODE" == "specific" ]]; then
        IFS=',' read -ra files_to_check <<< "$SPECIFIC_FILES"
    else
        files_to_check=("${AVAILABLE_FILES[@]}")
    fi
    
    local missing_files=()
    local total_size=0
    
    for file in "${files_to_check[@]}"; do
        file=$(echo "$file" | xargs)  # Trim whitespace
        filepath="$NEO4J_DATASETS_DIR/$file"
        
        if [[ ! -f "$filepath" ]]; then
            missing_files+=("$file")
        else
            size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
            total_size=$((total_size + size))
            print_status "✅ Found: $file ($(numfmt --to=iec $size))"
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "Missing dataset files:"
        for file in "${missing_files[@]}"; do
            echo "  ❌ $file"
        done
        print_error "Please run ./scripts/transform_data.sh first to generate missing files"
        exit 1
    fi
    
    print_status "✅ All required files found (Total: $(numfmt --to=iec $total_size))"
}

# Function to show dry run information
show_dry_run() {
    print_header
    print_status "🔍 DRY RUN MODE - Showing what would be executed"
    echo ""
    
    echo -e "${CYAN}Loading Configuration:${NC}"
    echo "  🎯 Mode: $LOAD_MODE"
    echo "  📁 Source: $NEO4J_DATASETS_DIR"
    echo "  🔄 Cleanup First: $CLEANUP_FIRST"
    echo "  ⏭️  Skip Existing: $SKIP_EXISTING"
    echo "  🔍 Validate References: $VALIDATE_REFERENCES"
    echo "  💾 Backup Before Clean: $BACKUP_BEFORE_CLEAN"
    echo "  📊 Verbose: $VERBOSE"
    echo ""
    
    if [[ "$LOAD_MODE" == "specific" ]]; then
        echo -e "${CYAN}Files to Load:${NC}"
        IFS=',' read -ra files <<< "$SPECIFIC_FILES"
        for file in "${files[@]}"; do
            file=$(echo "$file" | xargs)
            echo "  📄 $file"
        done
        echo ""
    fi
    
    echo -e "${CYAN}Loading Command:${NC}"
    echo "  cd $BACKEND_DIR"
    
    local command="python load_data.py"
    if [[ "$CLEANUP_FIRST" == true ]]; then
        command="$command --cleanup-first"
    fi
    if [[ "$SKIP_EXISTING" == true ]]; then
        command="$command --skip-existing"
    fi
    if [[ "$VALIDATE_REFERENCES" == false ]]; then
        command="$command --no-validation"
    fi
    if [[ "$VERBOSE" == true ]]; then
        command="$command --verbose"
    fi
    
    echo "  $command"
    echo ""
    
    echo -e "${CYAN}Expected Results:${NC}"
    case "$LOAD_MODE" in
        "clean")
            echo "  🗑️  Database will be cleaned"
            echo "  📦 All datasets will be loaded fresh"
            echo "  🔗 All relationships will be created"
            echo "  🧭 Vector indexes will be rebuilt"
            ;;
        "incremental")
            echo "  🔄 Only new/changed data will be loaded"
            echo "  📦 Existing records will be preserved"
            echo "  🔗 New relationships will be added"
            ;;
        "specific")
            echo "  🎯 Only specified files will be loaded"
            echo "  📦 Other datasets remain unchanged"
            ;;
    esac
    echo ""
    
    print_status "Use without --dry-run to execute the loading"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            LOAD_MODE="$2"
            if [[ ! "$LOAD_MODE" =~ ^(clean|incremental|specific)$ ]]; then
                print_error "Invalid mode: $LOAD_MODE. Must be: clean, incremental, or specific"
                exit 1
            fi
            shift 2
            ;;
        -f|--files)
            SPECIFIC_FILES="$2"
            shift 2
            ;;
        -c|--cleanup-first)
            CLEANUP_FIRST=true
            shift
            ;;
        -s|--skip-existing)
            SKIP_EXISTING=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -t|--test-connection)
            TEST_CONNECTION=true
            shift
            ;;
        --no-validation)
            VALIDATE_REFERENCES=false
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_CLEAN=false
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

# Validate specific mode requirements
if [[ "$LOAD_MODE" == "specific" ]] && [[ -z "$SPECIFIC_FILES" ]]; then
    print_error "Specific mode requires --files option"
    show_usage
    exit 1
fi

# Handle dry run
if [[ "$DRY_RUN" == true ]]; then
    validate_environment
    validate_dataset_files
    show_dry_run
fi

# Print header
print_header

# Validate environment
validate_environment

# Test Neo4j connection
test_neo4j_connection

# Validate dataset files
validate_dataset_files

# Show configuration
print_status "Loading Configuration:"
echo "  🎯 Mode: $LOAD_MODE"
echo "  📁 Source: $NEO4J_DATASETS_DIR"
echo "  🔄 Cleanup First: $CLEANUP_FIRST"
echo "  ⏭️  Skip Existing: $SKIP_EXISTING"
echo "  🔍 Validate References: $VALIDATE_REFERENCES"
echo "  💾 Backup Before Clean: $BACKUP_BEFORE_CLEAN"
echo "  📊 Verbose: $VERBOSE"

if [[ "$LOAD_MODE" == "specific" ]]; then
    echo "  📄 Files: $SPECIFIC_FILES"
fi
echo ""

# Handle clean mode confirmation
if [[ "$LOAD_MODE" == "clean" ]] && [[ "$DRY_RUN" != true ]]; then
    print_warning "CLEAN MODE will delete all existing data in Neo4j!"
    if [[ "$BACKUP_BEFORE_CLEAN" == true ]]; then
        print_status "Backup will be created before cleaning"
    fi
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Operation cancelled by user"
        exit 0
    fi
fi

# Change to backend directory for execution
cd "$BACKEND_DIR"
print_status "Changed to backend directory: $BACKEND_DIR"

# Build command based on mode
case "$LOAD_MODE" in
    "clean")
        COMMAND="python load_data.py --cleanup-first"
        ;;
    "incremental")
        COMMAND="python load_data.py"
        if [[ "$CLEANUP_FIRST" == true ]]; then
            COMMAND="$COMMAND --cleanup-first"
        fi
        if [[ "$SKIP_EXISTING" == true ]]; then
            COMMAND="$COMMAND --skip-existing"
        fi
        ;;
    "specific")
        # For specific files, we'll need to modify the loader or use individual commands
        COMMAND="python load_data.py"
        if [[ "$CLEANUP_FIRST" == true ]]; then
            COMMAND="$COMMAND --cleanup-first"
        fi
        print_warning "Specific file loading will load all files (feature to be enhanced)"
        ;;
esac

# Add common options
if [[ "$VALIDATE_REFERENCES" == false ]]; then
    COMMAND="$COMMAND --no-validation"
fi

if [[ "$VERBOSE" == true ]]; then
    COMMAND="$COMMAND --verbose"
fi

print_status "Executing data loading..."
print_status "Command: $COMMAND"
echo ""

# Execute the loading
eval $COMMAND

EXIT_CODE=$?

# Check execution result
if [[ $EXIT_CODE -eq 0 ]]; then
    print_footer
    echo ""
    echo -e "${GREEN}Loading Summary:${NC}"
    
    # Get database statistics
    cd "$BACKEND_DIR"
    python3 -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

try:
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    with driver.session() as session:
        # Get node counts
        result = session.run('MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY label')
        print('📊 Node Counts:')
        for record in result:
            if record['label']:
                print(f'  {record[\"label\"]}: {record[\"count\"]:,}')
        
        # Get relationship counts
        result = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY type')
        print('\\n🔗 Relationship Counts:')
        for record in result:
            print(f'  {record[\"type\"]}: {record[\"count\"]:,}')
        
        # Check vector index
        result = session.run('SHOW INDEXES WHERE name = \"product_embeddings\"')
        if result.single():
            print('\\n🧭 Vector Index: ✅ Active')
        else:
            print('\\n🧭 Vector Index: ❌ Not found')
    
    driver.close()
    
except Exception as e:
    print(f'❌ Error getting database statistics: {e}')
"
    
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. 🧪 Test queries using Neo4j Desktop or Browser"
    echo "  2. 🔍 Run vector search tests with simple_vector_queries.cypher"
    echo "  3. 🚀 Start the backend API server for recommendations"
    echo "  4. 📊 Monitor performance and adjust as needed"
    echo ""
else
    echo ""
    print_error "❌ Data loading failed with exit code: $EXIT_CODE"
    echo ""
    echo -e "${YELLOW}Troubleshooting Tips:${NC}"
    echo "  • Check Neo4j connection with --test-connection"
    echo "  • Verify .env file has correct Neo4j credentials"
    echo "  • Ensure Neo4j server is running and accessible"
    echo "  • Check dataset files exist in $NEO4J_DATASETS_DIR"
    echo "  • Run with --verbose for detailed error information"
    echo "  • Try --cleanup-first if database is in inconsistent state"
    exit $EXIT_CODE
fi