#!/bin/bash

################################################################################
# Contract Refund Eligibility System - Stop Script
#
# This script stops all running services:
# - Backend API
# - Frontend
# - Docker services (optional)
#
# Usage:
#   ./stop.sh              # Stop backend and frontend only
#   ./stop.sh --all        # Stop everything including Docker
#   ./stop.sh --help       # Show help
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Configuration
STOP_DOCKER=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all|-a)
            STOP_DOCKER=true
            shift
            ;;
        --help|-h)
            echo "Contract Refund Eligibility System - Stop Script"
            echo ""
            echo "Usage: ./stop.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all, -a        Stop everything including Docker services"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Default behavior:"
            echo "  Stops backend and frontend, but leaves Docker running"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

kill_process_on_port() {
    local port=$1
    local service_name=$2

    if lsof -ti:$port > /dev/null 2>&1; then
        print_info "Stopping $service_name on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        print_success "$service_name stopped"
    else
        print_info "$service_name not running on port $port"
    fi
}

################################################################################
# Stop Sequence
################################################################################

print_header "Stopping Services"

# Stop Backend (port 8001)
kill_process_on_port 8001 "Backend API"

# Stop Frontend (port 3000)
kill_process_on_port 3000 "Frontend"

# Alternative: Stop by PID if available
if [ -f /tmp/project_pids.txt ]; then
    print_info "Found PID file, killing processes..."
    source /tmp/project_pids.txt

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_success "Backend process (PID: $BACKEND_PID) killed"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend process (PID: $FRONTEND_PID) killed"
    fi

    rm /tmp/project_pids.txt
    print_success "PID file cleaned up"
fi

# Stop any remaining uvicorn processes
if pgrep -f "uvicorn" > /dev/null 2>&1; then
    print_info "Stopping remaining uvicorn processes..."
    pkill -f "uvicorn" 2>/dev/null || true
    print_success "All uvicorn processes stopped"
fi

# Stop any remaining Next.js processes
if pgrep -f "next dev" > /dev/null 2>&1; then
    print_info "Stopping remaining Next.js processes..."
    pkill -f "next dev" 2>/dev/null || true
    print_success "All Next.js processes stopped"
fi

# Stop Docker services if requested
if [ "$STOP_DOCKER" = true ]; then
    print_header "Stopping Docker Services"

    cd "$BACKEND_DIR"

    if docker-compose ps | grep -q "Up"; then
        print_info "Stopping PostgreSQL and Redis..."
        docker-compose stop
        print_success "Docker services stopped"

        print_warning "Docker containers are stopped but not removed"
        print_info "To remove containers: cd $BACKEND_DIR && docker-compose down"
        print_info "To remove with volumes: cd $BACKEND_DIR && docker-compose down -v"
    else
        print_info "Docker services not running"
    fi
fi

# Clean up log files (optional)
print_header "Cleanup"

if [ -f /tmp/backend.log ]; then
    print_info "Backend logs available at: /tmp/backend.log"
fi

if [ -f /tmp/frontend.log ]; then
    print_info "Frontend logs available at: /tmp/frontend.log"
fi

echo ""
print_success "All services stopped"

if [ "$STOP_DOCKER" = false ]; then
    print_info "Docker services are still running (use --all to stop)"
fi

echo ""
