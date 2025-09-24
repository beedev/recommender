#!/bin/bash

# =============================================================================
# ESAB Agentic AI Welding Recommender - Server Startup Script
# =============================================================================
# Comprehensive script to start both frontend and backend servers
# Kills existing processes on ports 3000 and 8000 before starting
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} ESAB Agentic AI Recommender${NC}"
    echo -e "${BLUE} Server Startup Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    local service_name=$2
    
    print_status "Checking for existing $service_name processes on port $port..."
    
    # Find processes using the port
    local pids=$(lsof -ti tcp:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        print_warning "Found existing processes on port $port: $pids"
        print_status "Killing processes..."
        
        # Kill the processes forcefully
        for pid in $pids; do
            kill -9 "$pid" 2>/dev/null || true
        done
        
        # Wait a moment for cleanup
        sleep 3
        
        # Verify processes are killed
        local remaining_pids=$(lsof -ti tcp:$port 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            print_warning "Some processes still running on port $port: $remaining_pids"
            print_status "Attempting additional cleanup..."
            for pid in $remaining_pids; do
                kill -9 "$pid" 2>/dev/null || true
            done
            sleep 2
            
            # Final check
            remaining_pids=$(lsof -ti tcp:$port 2>/dev/null || true)
            if [ -n "$remaining_pids" ]; then
                print_error "Failed to kill all processes on port $port. Please manually kill: $remaining_pids"
                return 1
            fi
        fi
        print_success "Successfully killed processes on port $port"
    else
        print_status "Port $port is available"
    fi
}

# Function to check if required directories exist
check_directories() {
    print_status "Checking project directories..."
    
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found: $BACKEND_DIR"
        return 1
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        print_warning "Frontend directory not found: $FRONTEND_DIR"
        print_warning "Will only start backend server"
        return 0
    fi
    
    print_success "Project directories found"
}

# Function to check Python environment
check_python_env() {
    print_status "Checking Python environment..."
    
    cd "$BACKEND_DIR"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_status "Found Python virtual environment"
        source venv/bin/activate
    elif [ -d "../venv" ]; then
        print_status "Found Python virtual environment in parent directory"
        source ../venv/bin/activate
    else
        print_warning "No virtual environment found, using system Python"
    fi
    
    # Check if required packages are installed
    if ! python -c "import uvicorn, fastapi" 2>/dev/null; then
        print_error "Required Python packages not found. Please install requirements:"
        print_error "pip install -r requirements.txt"
        return 1
    fi
    
    print_success "Python environment ready"
}

# Function to check Node.js environment
check_node_env() {
    if [ ! -d "$FRONTEND_DIR" ]; then
        return 0
    fi
    
    print_status "Checking Node.js environment..."
    
    cd "$FRONTEND_DIR"
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js"
        return 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm"
        return 1
    fi
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules not found. Running npm install..."
        npm install
    fi
    
    print_success "Node.js environment ready"
}

# Function to start backend server
start_backend() {
    print_status "Starting backend server..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "Activated virtual environment: backend/venv"
    elif [ -d "../venv" ]; then
        source ../venv/bin/activate
        print_status "Activated virtual environment: venv"
    fi
    
    # Check if .env file exists
    if [ ! -f "../.env" ] && [ ! -f ".env" ]; then
        print_warning "No .env file found. Using default configuration."
    fi
    
    # Start the backend server in background with absolute path for log
    print_status "Launching FastAPI server on port $BACKEND_PORT..."
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$SCRIPT_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    # Wait for server to start
    print_status "Waiting for backend server to start..."
    sleep 8
    
    # Check if backend is running
    local max_retries=5
    local retry_count=0
    while [ $retry_count -lt $max_retries ]; do
        if curl -s http://localhost:$BACKEND_PORT/api/v1/health/ > /dev/null 2>&1; then
            print_success "Backend server started successfully on port $BACKEND_PORT (PID: $BACKEND_PID)"
            return 0
        fi
        retry_count=$((retry_count + 1))
        print_status "Waiting for backend to respond... (attempt $retry_count/$max_retries)"
        sleep 3
    done
    
    print_error "Backend server failed to start. Check $SCRIPT_DIR/backend.log for details."
    if [ -f "$SCRIPT_DIR/backend.log" ]; then
        print_status "Last few lines of backend.log:"
        tail -10 "$SCRIPT_DIR/backend.log" 2>/dev/null || true
    fi
    return 1
}

# Function to start frontend server
start_frontend() {
    if [ ! -d "$FRONTEND_DIR" ]; then
        print_warning "Skipping frontend server (directory not found)"
        return 0
    fi
    
    print_status "Starting frontend server..."
    
    cd "$FRONTEND_DIR"
    
    # Start the frontend server in background
    print_status "Launching development server on port $FRONTEND_PORT..."
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for server to start
    print_status "Waiting for frontend server to start..."
    sleep 8
    
    # Check if frontend is running
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        print_success "Frontend server started successfully on port $FRONTEND_PORT (PID: $FRONTEND_PID)"
    else
        print_warning "Frontend server may not be running. Check frontend.log for details."
    fi
}

# Function to start simple HTTP server for prototype
start_prototype_server() {
    print_status "Starting simple HTTP server for frontend prototype..."
    
    cd "$SCRIPT_DIR"
    
    # Start simple HTTP server for the prototype HTML file
    nohup python3 -m http.server $FRONTEND_PORT > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for server to start
    sleep 3
    
    print_success "Frontend prototype server started on port $FRONTEND_PORT (PID: $FRONTEND_PID)"
    print_status "Access the frontend at: http://localhost:$FRONTEND_PORT/frontend_prototype.html"
}

# Function to display running services
show_status() {
    echo
    print_header
    print_status "Server Status:"
    echo
    
    # Check backend
    if curl -s http://localhost:$BACKEND_PORT/api/v1/health/ > /dev/null 2>&1; then
        print_success "✓ Backend API: http://localhost:$BACKEND_PORT"
        print_success "  - Health Check: http://localhost:$BACKEND_PORT/api/v1/health/"
        print_success "  - API Documentation: http://localhost:$BACKEND_PORT/docs"
        print_success "  - Enterprise API: http://localhost:$BACKEND_PORT/api/v1/enterprise/recommendations"
        print_success "  - Vector Compatibility: http://localhost:$BACKEND_PORT/api/v1/vector-compatibility/compatibility-search"
    else
        print_error "✗ Backend API: Not running"
    fi
    
    echo
    
    # Check frontend
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        print_success "✓ Frontend: http://localhost:$FRONTEND_PORT"
        if [ -f "$SCRIPT_DIR/frontend_prototype.html" ]; then
            print_success "  - Prototype: http://localhost:$FRONTEND_PORT/frontend_prototype.html"
        fi
    else
        print_error "✗ Frontend: Not running"
    fi
    
    echo
    print_status "Log files:"
    print_status "  - Backend: $SCRIPT_DIR/backend.log"
    print_status "  - Frontend: $SCRIPT_DIR/frontend.log"
    echo
    print_status "To stop servers: ./stop_servers.sh or use 'kill' with the PIDs shown above"
    echo
}

# Function to create stop script
create_stop_script() {
    cat > "$SCRIPT_DIR/stop_servers.sh" << 'EOF'
#!/bin/bash

# Stop ESAB Agentic AI servers

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_status "Stopping ESAB Agentic AI servers..."

# Kill processes on port 8000 (backend)
backend_pids=$(lsof -ti tcp:8000 2>/dev/null || true)
if [ -n "$backend_pids" ]; then
    echo $backend_pids | xargs kill -9 2>/dev/null || true
    print_success "Backend server stopped"
fi

# Kill processes on port 3000 (frontend)
frontend_pids=$(lsof -ti tcp:3000 2>/dev/null || true)
if [ -n "$frontend_pids" ]; then
    echo $frontend_pids | xargs kill -9 2>/dev/null || true
    print_success "Frontend server stopped"
fi

print_status "All servers stopped"
EOF

    chmod +x "$SCRIPT_DIR/stop_servers.sh"
    print_success "Created stop script: ./stop_servers.sh"
}

# Main execution
main() {
    print_header
    
    # Kill existing processes
    kill_port $BACKEND_PORT "backend"
    kill_port $FRONTEND_PORT "frontend"
    
    # Check environments
    check_directories
    check_python_env
    check_node_env
    
    echo
    print_status "Starting servers..."
    echo
    
    # Start backend
    start_backend
    
    # Start frontend using simple HTTP server for prototype
    start_prototype_server
    
    # Create stop script
    create_stop_script
    
    # Show status
    show_status
}

# Handle script interruption
trap 'print_error "Script interrupted. Servers may still be running. Use ./stop_servers.sh to stop them."' INT

# Run main function
main "$@"