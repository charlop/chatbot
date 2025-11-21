#!/bin/bash

################################################################################
# Contract Refund Eligibility System - Startup Script
#
# This script starts all required services for local development:
# - Docker services (PostgreSQL, Redis)
# - Backend API (FastAPI on port 8001)
# - Frontend (Next.js on port 3000)
#
# Usage:
#   ./start.sh              # Start all services
#   ./start.sh --seed       # Start all services and seed database
#   ./start.sh --help       # Show help
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
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Configuration
BACKEND_PORT=8001
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Parse command line arguments
SEED_DB=false
SKIP_FRONTEND=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --seed)
            SEED_DB=true
            shift
            ;;
        --backend-only)
            SKIP_FRONTEND=true
            shift
            ;;
        --help|-h)
            echo "Contract Refund Eligibility System - Startup Script"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --seed           Seed database with test data"
            echo "  --backend-only   Start backend only (skip frontend)"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Services:"
            echo "  PostgreSQL:  localhost:$POSTGRES_PORT"
            echo "  Redis:       localhost:$REDIS_PORT"
            echo "  Backend API: http://localhost:$BACKEND_PORT"
            echo "  Frontend:    http://localhost:$FRONTEND_PORT"
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

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    return 0
}

wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=0

    echo -n "Waiting for $service_name to be ready..."

    while ! nc -z "$host" "$port" 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            echo ""
            print_error "$service_name failed to start (timeout)"
            return 1
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    print_success "$service_name is ready"
    return 0
}

kill_process_on_port() {
    local port=$1
    local service_name=$2

    if lsof -ti:$port > /dev/null 2>&1; then
        print_warning "$service_name already running on port $port, killing..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        print_success "Killed existing $service_name process"
    fi
}

################################################################################
# Startup Sequence
################################################################################

print_header "Contract Refund Eligibility System"
echo "Starting all services..."
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! check_command "docker"; then
    print_error "Docker is required. Please install Docker Desktop."
    exit 1
fi

if ! check_command "docker-compose"; then
    print_error "Docker Compose is required. Please install Docker Compose."
    exit 1
fi

if ! check_command "uv"; then
    print_error "UV is required for backend. Install from: https://github.com/astral-sh/uv"
    exit 1
fi

if ! check_command "npm" && [ "$SKIP_FRONTEND" = false ]; then
    print_error "npm is required for frontend. Please install Node.js."
    exit 1
fi

if ! check_command "nc"; then
    print_warning "netcat (nc) not found, service health checks may not work"
fi

print_success "All prerequisites met"
echo ""

################################################################################
# Step 1: Start Docker Services
################################################################################

print_header "Step 1: Starting Docker Services"

cd "$BACKEND_DIR"

# Check if services are already running
if docker-compose ps | grep -q "Up"; then
    print_info "Docker services already running"
else
    print_info "Starting PostgreSQL and Redis..."
    docker-compose up -d
fi

# Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 3  # Give docker-compose time to start

# Check service health
if docker-compose ps | grep -q "postgres.*healthy"; then
    print_success "PostgreSQL is healthy"
else
    print_warning "PostgreSQL health check not confirmed"
fi

if docker-compose ps | grep -q "redis.*healthy"; then
    print_success "Redis is healthy"
else
    print_warning "Redis health check not confirmed"
fi

# Wait for ports to be available
wait_for_service localhost $POSTGRES_PORT "PostgreSQL" || exit 1
wait_for_service localhost $REDIS_PORT "Redis" || exit 1

echo ""

################################################################################
# Step 2: Seed Database (Optional)
################################################################################

if [ "$SEED_DB" = true ]; then
    print_header "Step 2: Seeding Database"

    print_info "Seeding database with test data..."
    cd "$BACKEND_DIR"
    uv run python scripts/seed_db.py --with-extractions

    print_success "Database seeded successfully"
    echo ""
else
    print_info "Skipping database seeding (use --seed to seed)"
    echo ""
fi

################################################################################
# Step 2.5: Setup S3 (LocalStack) with Test PDFs
################################################################################

if [ "$SEED_DB" = true ]; then
    print_header "Step 2.5: Setting up LocalStack S3"

    # Wait for LocalStack to be healthy
    print_info "Waiting for LocalStack S3 to be ready..."
    if wait_for_service localhost 4566 "LocalStack"; then
        print_success "LocalStack is ready"

        print_info "Creating S3 bucket and uploading test PDFs..."
        cd "$BACKEND_DIR"
        uv run python scripts/setup_s3.py --all

        print_success "S3 setup completed"
    else
        print_warning "LocalStack not available, skipping S3 setup"
        print_info "PDFs will not be available until S3 is set up"
    fi

    echo ""
fi

################################################################################
# Step 3: Start Backend API
################################################################################

print_header "Step 3: Starting Backend API"

# Kill existing backend processes
kill_process_on_port $BACKEND_PORT "Backend API"

print_info "Starting FastAPI server on port $BACKEND_PORT..."
cd "$BACKEND_DIR"

# Start backend in background with S3 environment variables for LocalStack
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=us-east-1 \
nohup uv run uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3
if wait_for_service localhost $BACKEND_PORT "Backend API"; then
    print_success "Backend API started successfully (PID: $BACKEND_PID)"
    echo -e "${GREEN}   📚 API Docs: http://localhost:$BACKEND_PORT/docs${NC}"
else
    print_error "Backend API failed to start"
    print_info "Check logs: tail -f /tmp/backend.log"
    exit 1
fi

echo ""

################################################################################
# Step 4: Start Frontend (Optional)
################################################################################

if [ "$SKIP_FRONTEND" = false ]; then
    print_header "Step 4: Starting Frontend"

    # Kill existing frontend processes
    kill_process_on_port $FRONTEND_PORT "Frontend"

    # Check if frontend dependencies are installed
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        print_warning "Frontend dependencies not found, installing..."
        cd "$FRONTEND_DIR"
        npm install
        print_success "Dependencies installed"
    fi

    print_info "Starting Next.js development server on port $FRONTEND_PORT..."
    cd "$FRONTEND_DIR"

    # Start frontend in background
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!

    # Wait for frontend to be ready
    sleep 5
    if wait_for_service localhost $FRONTEND_PORT "Frontend"; then
        print_success "Frontend started successfully (PID: $FRONTEND_PID)"
        echo -e "${GREEN}   🌐 Web UI: http://localhost:$FRONTEND_PORT${NC}"
    else
        print_error "Frontend failed to start"
        print_info "Check logs: tail -f /tmp/frontend.log"
        exit 1
    fi
else
    print_info "Skipping frontend (--backend-only flag set)"
fi

echo ""

################################################################################
# Summary
################################################################################

print_header "✅ All Services Started"

echo ""
echo -e "${CYAN}Service Status:${NC}"
echo -e "${GREEN}  ✅ PostgreSQL:${NC}   localhost:$POSTGRES_PORT"
echo -e "${GREEN}  ✅ Redis:${NC}        localhost:$REDIS_PORT"
echo -e "${GREEN}  ✅ Backend API:${NC}  http://localhost:$BACKEND_PORT"

if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${GREEN}  ✅ Frontend:${NC}     http://localhost:$FRONTEND_PORT"
fi

echo ""
echo -e "${CYAN}Useful Links:${NC}"
echo -e "  📚 API Documentation: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  🔍 ReDoc:            ${BLUE}http://localhost:$BACKEND_PORT/redoc${NC}"
echo -e "  ❤️  Health Check:     ${BLUE}http://localhost:$BACKEND_PORT/health${NC}"

if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "  🌐 Web Application:  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
fi

echo ""
echo -e "${CYAN}Logs:${NC}"
echo -e "  Backend:  ${YELLOW}tail -f /tmp/backend.log${NC}"

if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "  Frontend: ${YELLOW}tail -f /tmp/frontend.log${NC}"
fi

echo -e "  Docker:   ${YELLOW}docker-compose -f $BACKEND_DIR/docker-compose.yml logs -f${NC}"

echo ""
echo -e "${CYAN}Process Management:${NC}"
echo -e "  Backend PID:  $BACKEND_PID"

if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "  Frontend PID: $FRONTEND_PID"
fi

echo ""
echo -e "${CYAN}To stop services:${NC}"
echo -e "  1. Stop backend:  ${YELLOW}kill $BACKEND_PID${NC}"

if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "  2. Stop frontend: ${YELLOW}kill $FRONTEND_PID${NC}"
fi

echo -e "  3. Stop Docker:   ${YELLOW}cd $BACKEND_DIR && docker-compose down${NC}"

echo ""
echo -e "${CYAN}Quick test commands:${NC}"
echo -e "  ${YELLOW}curl http://localhost:$BACKEND_PORT/health${NC}"
echo -e "  ${YELLOW}curl -X POST http://localhost:$BACKEND_PORT/api/v1/contracts/search \\
    -H 'Content-Type: application/json' \\
    -d '{\"account_number\": \"ACC-TEST-00001\"}'${NC}"

echo ""
print_success "All services are running! Happy coding! 🚀"
echo ""

# Save PIDs to file for easy stopping later
cat > /tmp/project_pids.txt <<EOF
BACKEND_PID=$BACKEND_PID
FRONTEND_PID=$FRONTEND_PID
EOF

print_info "Service PIDs saved to /tmp/project_pids.txt"
