#!/bin/bash

# Master Data Deployment Orchestrator
# Coordinates data transformation and loading in one pipeline
# Usage: ./scripts/deploy_data.sh [options]

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

# Default values
TRANSFORM_ONLY=false
LOAD_ONLY=false
LOAD_MODE="clean"
VERBOSE=false
DRY_RUN=false
SKIP_VALIDATION=false
NO_BACKUP=false
FORCE_OVERWRITE=false
CONFIG_FILE="powersource_config.json"
POWERSOURCES=""
TEST_CONNECTION=false

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

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}    Master Data Deployment Pipeline       ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${CYAN}Complete ETL: Datasets → neo4jdatasets → Neo4j${NC}"
    echo ""
}

print_footer() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}🎉 Data Deployment Complete!${NC}"
    echo -e "${BLUE}============================================${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Description:"
    echo "  Complete data deployment pipeline: transform and load datasets into Neo4j"
    echo ""
    echo "Pipeline Modes:"
    echo "  full         Transform datasets + Load into Neo4j (default)"
    echo "  transform    Transform datasets only"
    echo "  load         Load existing neo4jdatasets only"
    echo ""
    echo "Options:"
    echo "  Pipeline Control:"
    echo "    --transform-only        Run transformation step only"
    echo "    --load-only            Run loading step only"
    echo "    --load-mode MODE       Loading mode: clean|incremental (default: clean)"
    echo ""
    echo "  Transformation Options:"
    echo "    -c, --config FILE      PowerSource configuration file"
    echo "    -p, --powersources LIST Comma-separated PowerSource GINs"
    echo "    -f, --force           Force overwrite existing outputs"
    echo ""
    echo "  Loading Options:"
    echo "    --skip-existing       Skip existing records (incremental mode)"
    echo "    --no-validation       Skip reference validation"
    echo "    --no-backup          Skip backup before clean loading"
    echo ""
    echo "  General Options:"
    echo "    -v, --verbose         Enable verbose logging"
    echo "    -d, --dry-run        Show what would be done without executing"
    echo "    -t, --test-connection Test Neo4j connection and exit"
    echo "    -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Full pipeline with default config"
    echo "  $0 --verbose                         # Full pipeline with detailed logging"
    echo "  $0 --transform-only --force          # Transform only, overwrite existing"
    echo "  $0 --load-only --load-mode incremental # Load only, incremental mode"
    echo "  $0 --powersources \"0446200880,0465350883\" # Custom PowerSources"
    echo "  $0 --dry-run                        # Preview entire pipeline"
    echo "  $0 --test-connection                # Test database connection"
    echo ""
    echo "Pipeline Steps:"
    echo "  1. 🔄 Transform: Datasets/ → neo4jdatasets/"
    echo "  2. 📥 Load: neo4jdatasets/ → Neo4j Database"
    echo "  3. ✅ Validate: Test connections and data integrity"
}

# Function to validate environment
validate_environment() {
    print_status "Validating environment..."
    
    # Check scripts exist
    if [[ ! -f "$SCRIPT_DIR/transform_data.sh" ]]; then
        print_error "Transform script not found: $SCRIPT_DIR/transform_data.sh"
        exit 1
    fi
    
    if [[ ! -f "$SCRIPT_DIR/load_data.sh" ]]; then
        print_error "Load script not found: $SCRIPT_DIR/load_data.sh"
        exit 1
    fi
    
    # Check scripts are executable
    if [[ ! -x "$SCRIPT_DIR/transform_data.sh" ]]; then
        print_warning "Making transform script executable..."
        chmod +x "$SCRIPT_DIR/transform_data.sh"
    fi
    
    if [[ ! -x "$SCRIPT_DIR/load_data.sh" ]]; then
        print_warning "Making load script executable..."
        chmod +x "$SCRIPT_DIR/load_data.sh"
    fi
    
    print_status "✅ Environment validation passed"
}

# Function to show dry run information
show_dry_run() {
    print_header
    print_status "🔍 DRY RUN MODE - Showing complete pipeline execution plan"
    echo ""
    
    echo -e "${CYAN}Pipeline Configuration:${NC}"
    if [[ "$TRANSFORM_ONLY" == true ]]; then
        echo "  🎯 Mode: Transform Only"
    elif [[ "$LOAD_ONLY" == true ]]; then
        echo "  🎯 Mode: Load Only"
    else
        echo "  🎯 Mode: Full Pipeline (Transform + Load)"
    fi
    echo "  📊 Verbose: $VERBOSE"
    echo "  🔍 Skip Validation: $SKIP_VALIDATION"
    echo "  💾 No Backup: $NO_BACKUP"
    echo "  ⚡ Force Overwrite: $FORCE_OVERWRITE"
    echo ""
    
    if [[ "$TRANSFORM_ONLY" != true ]]; then
        echo -e "${CYAN}Loading Configuration:${NC}"
        echo "  🔄 Load Mode: $LOAD_MODE"
        echo ""
    fi
    
    echo -e "${CYAN}Execution Plan:${NC}"
    
    if [[ "$LOAD_ONLY" != true ]]; then
        echo -e "${PURPLE}Step 1: Data Transformation${NC}"
        echo "  📁 Source: $PROJECT_ROOT/Datasets/"
        echo "  📁 Output: $PROJECT_ROOT/neo4jdatasets/"
        
        transform_cmd=\"./scripts/transform_data.sh\"
        if [[ -n \"$CONFIG_FILE\" ]] && [[ \"$CONFIG_FILE\" != \"powersource_config.json\" ]]; then
            transform_cmd=\"\$transform_cmd --config \$CONFIG_FILE\"
        fi
        if [[ -n \"$POWERSOURCES\" ]]; then
            transform_cmd=\"\$transform_cmd --powersources \$POWERSOURCES\"
        fi
        if [[ \"$VERBOSE\" == true ]]; then
            transform_cmd=\"\$transform_cmd --verbose\"
        fi
        if [[ \"$SKIP_VALIDATION\" == true ]]; then
            transform_cmd=\"\$transform_cmd --skip-validation\"
        fi
        if [[ \"$NO_BACKUP\" == true ]]; then
            transform_cmd=\"\$transform_cmd --no-backup\"
        fi
        if [[ \"$FORCE_OVERWRITE\" == true ]]; then
            transform_cmd=\"\$transform_cmd --force\"
        fi
        
        echo \"  🔧 Command: \$transform_cmd\"
        echo \"\"
    fi
    
    if [[ \"$TRANSFORM_ONLY\" != true ]]; then
        echo -e \"${PURPLE}Step 2: Data Loading${NC}\"
        echo \"  📁 Source: \$PROJECT_ROOT/neo4jdatasets/\"
        echo \"  🎯 Target: Neo4j Database\"
        
        load_cmd=\"./scripts/load_data.sh --mode \$LOAD_MODE\"
        if [[ \"$VERBOSE\" == true ]]; then
            load_cmd=\"\$load_cmd --verbose\"
        fi
        if [[ \"$SKIP_VALIDATION\" == true ]]; then
            load_cmd=\"\$load_cmd --no-validation\"
        fi
        if [[ \"$NO_BACKUP\" == true ]]; then
            load_cmd=\"\$load_cmd --no-backup\"
        fi
        
        echo \"  🔧 Command: \$load_cmd\"
        echo \"\"
    fi
    
    echo -e \"${PURPLE}Step 3: Validation${NC}\"
    echo \"  🧪 Test Neo4j connection\"
    echo \"  📊 Verify data counts\"
    echo \"  🔍 Check vector indexes\"
    echo \"\"
    
    print_status \"Use without --dry-run to execute the complete pipeline\"
    exit 0
}

# Function to run transformation step
run_transformation() {
    print_step \"🔄 Starting Data Transformation...\"
    echo \"\"
    
    local transform_cmd=\"\$SCRIPT_DIR/transform_data.sh\"
    
    # Build transformation command
    local transform_args=()
    
    if [[ -n \"$CONFIG_FILE\" ]] && [[ \"$CONFIG_FILE\" != \"powersource_config.json\" ]]; then
        transform_args+=(\"--config\" \"$CONFIG_FILE\")
    fi
    
    if [[ -n \"$POWERSOURCES\" ]]; then
        transform_args+=(\"--powersources\" \"$POWERSOURCES\")
    fi
    
    if [[ \"$VERBOSE\" == true ]]; then
        transform_args+=(\"--verbose\")
    fi
    
    if [[ \"$SKIP_VALIDATION\" == true ]]; then
        transform_args+=(\"--skip-validation\")
    fi
    
    if [[ \"$NO_BACKUP\" == true ]]; then
        transform_args+=(\"--no-backup\")
    fi
    
    if [[ \"$FORCE_OVERWRITE\" == true ]]; then
        transform_args+=(\"--force\")
    fi
    
    # Execute transformation
    \"\$transform_cmd\" \"\${transform_args[@]}\"
    
    if [[ \$? -eq 0 ]]; then
        print_success \"✅ Data transformation completed successfully\"
        echo \"\"
    else
        print_error \"❌ Data transformation failed\"
        exit 1
    fi
}

# Function to run loading step
run_loading() {
    print_step \"📥 Starting Data Loading...\"
    echo \"\"
    
    local load_cmd=\"\$SCRIPT_DIR/load_data.sh\"
    
    # Build loading command
    local load_args=(\"--mode\" \"\$LOAD_MODE\")
    
    if [[ \"\$VERBOSE\" == true ]]; then
        load_args+=(\"--verbose\")
    fi
    
    if [[ \"\$SKIP_VALIDATION\" == true ]]; then
        load_args+=(\"--no-validation\")
    fi
    
    if [[ \"\$NO_BACKUP\" == true ]]; then
        load_args+=(\"--no-backup\")
    fi
    
    # Execute loading
    \"\$load_cmd\" \"\${load_args[@]}\"
    
    if [[ \$? -eq 0 ]]; then
        print_success \"✅ Data loading completed successfully\"
        echo \"\"
    else
        print_error \"❌ Data loading failed\"
        exit 1
    fi
}

# Function to run validation step
run_validation() {
    print_step \"✅ Running Final Validation...\"
    echo \"\"
    
    # Test connection and get summary
    \"\$SCRIPT_DIR/load_data.sh\" --test-connection
    
    if [[ \$? -eq 0 ]]; then
        print_success \"✅ Validation completed successfully\"
        echo \"\"
    else
        print_error \"❌ Validation failed\"
        exit 1
    fi
}

# Parse command line arguments
while [[ \$# -gt 0 ]]; do
    case \$1 in
        --transform-only)
            TRANSFORM_ONLY=true
            shift
            ;;
        --load-only)
            LOAD_ONLY=true
            shift
            ;;
        --load-mode)
            LOAD_MODE=\"\$2\"
            if [[ ! \"\$LOAD_MODE\" =~ ^(clean|incremental)\$ ]]; then
                print_error \"Invalid load mode: \$LOAD_MODE. Must be: clean or incremental\"
                exit 1
            fi
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE=\"\$2\"
            shift 2
            ;;
        -p|--powersources)
            POWERSOURCES=\"\$2\"
            shift 2
            ;;
        -f|--force)
            FORCE_OVERWRITE=true
            shift
            ;;
        --skip-existing)
            # This would be passed to load script
            shift
            ;;
        --no-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
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
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error \"Unknown option: \$1\"
            show_usage
            exit 1
            ;;
    esac
done

# Validate mutual exclusivity
if [[ \"\$TRANSFORM_ONLY\" == true ]] && [[ \"\$LOAD_ONLY\" == true ]]; then
    print_error \"Cannot specify both --transform-only and --load-only\"
    exit 1
fi

# Handle test connection
if [[ \"\$TEST_CONNECTION\" == true ]]; then
    \"\$SCRIPT_DIR/load_data.sh\" --test-connection
    exit \$?
fi

# Handle dry run
if [[ \"\$DRY_RUN\" == true ]]; then
    validate_environment
    show_dry_run
fi

# Print header
print_header

# Validate environment
validate_environment

# Show configuration
print_status \"Pipeline Configuration:\"
if [[ \"\$TRANSFORM_ONLY\" == true ]]; then
    echo \"  🎯 Mode: Transform Only\"
elif [[ \"\$LOAD_ONLY\" == true ]]; then
    echo \"  🎯 Mode: Load Only\"
else
    echo \"  🎯 Mode: Full Pipeline (Transform + Load)\"
fi
echo \"  📊 Verbose: \$VERBOSE\"
echo \"  🔄 Load Mode: \$LOAD_MODE\"
if [[ -n \"\$POWERSOURCES\" ]]; then
    echo \"  🎯 PowerSources: \$POWERSOURCES\"
elif [[ \"\$CONFIG_FILE\" != \"powersource_config.json\" ]]; then
    echo \"  ⚙️  Config: \$CONFIG_FILE\"
fi
echo \"\"

# Record start time
START_TIME=\$(date +%s)
print_status \"🚀 Starting pipeline execution at \$(date)\"
echo \"\"

# Execute pipeline steps
if [[ \"\$LOAD_ONLY\" != true ]]; then
    run_transformation
fi

if [[ \"\$TRANSFORM_ONLY\" != true ]]; then
    run_loading
    run_validation
fi

# Calculate execution time
END_TIME=\$(date +%s)
DURATION=\$((END_TIME - START_TIME))
MINUTES=\$((DURATION / 60))
SECONDS=\$((DURATION % 60))

# Print footer
print_footer
echo \"\"
echo -e \"\${GREEN}Pipeline Summary:\${NC}\"
echo \"  ⏱️  Total Duration: \${MINUTES}m \${SECONDS}s\"
echo \"  🎯 Mode: \$(if [[ \"\$TRANSFORM_ONLY\" == true ]]; then echo \"Transform Only\"; elif [[ \"\$LOAD_ONLY\" == true ]]; then echo \"Load Only\"; else echo \"Full Pipeline\"; fi)\"
echo \"  📊 Status: ✅ Success\"
echo \"\"
echo -e \"\${BLUE}Next Steps:\${NC}\"
echo \"  1. 🧪 Test queries using Neo4j Desktop or Browser\"
echo \"  2. 🔍 Run vector search tests with simple_vector_queries.cypher\"
echo \"  3. 🚀 Start the backend API server: cd backend && python -m uvicorn app.main:app --reload\"
echo \"  4. 📊 Monitor performance and adjust as needed\"
echo \"\"
echo -e \"\${CYAN}Useful Commands:\${NC}\"
echo \"  ./scripts/deploy_data.sh --dry-run           # Preview pipeline\"
echo \"  ./scripts/deploy_data.sh --load-mode incremental # Incremental updates\"
echo \"  ./scripts/deploy_data.sh --test-connection   # Test database\"
echo \"  ./scripts/transform_data.sh --help          # Transform options\"
echo \"  ./scripts/load_data.sh --help               # Loading options\"