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
