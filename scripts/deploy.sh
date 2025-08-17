#!/bin/bash

# Full deployment script (build frontend + start production)
# Usage: ./scripts/deploy.sh [--skip-build] [--force]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Full Deployment Script${NC}"
echo "=========================="

# Parse command line arguments
SKIP_BUILD=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--skip-build] [--force]"
            echo "  --skip-build  Skip frontend build (use existing build)"
            echo "  --force       Force deployment even if production server is running"
            exit 1
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Check if production server is already running
if [[ -f "pids/production.pid" ]] && ! $FORCE; then
    pid=$(cat pids/production.pid)
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${YELLOW}Production server is already running (PID: $pid)${NC}"
        echo "Options:"
        echo "  1. Stop and redeploy: ./scripts/restart.sh production"
        echo "  2. Force redeploy: $0 --force"
        echo "  3. Just rebuild frontend: ./scripts/build-frontend.sh"
        exit 0
    else
        # Clean up stale PID file
        rm -f pids/production.pid
    fi
fi

echo -e "${YELLOW}Starting deployment process...${NC}"

# Step 0: Check port availability early (before expensive operations)
echo -e "\n${BLUE}Step 0: Pre-deployment validation${NC}"
if [[ ! -f ".env.production" ]]; then
    echo -e "${RED}✗ .env.production not found${NC}"
    echo "Run: ./scripts/setup-environment.sh production"
    exit 1
fi

port=$(grep "^FLASK_PORT=" .env.production | cut -d'=' -f2 || echo "8080")
if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
    if $FORCE; then
        echo -e "${YELLOW}⚠ Port $port in use, will attempt to start anyway (--force)${NC}"
    else
        echo -e "${RED}✗ Port $port is already in use${NC}"
        echo -e "${YELLOW}Resolution options:${NC}"
        echo "  1. Stop the service: lsof -Pi :$port -sTCP:LISTEN -t | xargs kill"
        echo "  2. Change port in .env.production (edit FLASK_PORT=)"
        echo "  3. Force override: $0 --force"
        echo ""
        echo "Process using port $port:"
        lsof -Pi :$port -sTCP:LISTEN
        exit 1
    fi
else
    echo -e "${GREEN}✓ Port $port is available${NC}"

# Validate port synchronization between backend and frontend
validate_port_sync() {
    local backend_env=".env.production"
    local frontend_env="../frontend/.env.production"
    
    # Check if frontend env file exists
    if [[ ! -f "$frontend_env" ]]; then
        echo -e "${YELLOW}⚠ Frontend .env.production not found, will use environment variables during build${NC}"
        return 0
    fi
    
    # Extract ports
    local backend_port=$(grep "^FLASK_PORT=" "$backend_env" | cut -d'=' -f2 || echo "5000")
    local frontend_url=$(grep "^VITE_API_BASE_URL=" "$frontend_env" | cut -d'=' -f2 || echo "")
    local frontend_port=""
    
    if [[ -n "$frontend_url" ]]; then
        # Extract port from URL (handles http://127.0.0.1:8548 or http://localhost:8548)
        frontend_port=$(echo "$frontend_url" | sed -n 's/.*:\([0-9]\+\).*/\1/p')
    fi
    
    # Compare ports
    if [[ -n "$frontend_port" && "$backend_port" != "$frontend_port" ]]; then
        echo -e "${RED}✗ Port configuration mismatch detected!${NC}"
        echo -e "${YELLOW}Backend port (FLASK_PORT): $backend_port${NC}"
        echo -e "${YELLOW}Frontend port (VITE_API_BASE_URL): $frontend_port${NC}"
        echo -e "\n${BLUE}To fix this issue:${NC}"
        echo -e "1. Update frontend .env.production: VITE_API_BASE_URL=http://127.0.0.1:$backend_port"
        echo -e "2. Or update backend .env.production: FLASK_PORT=$frontend_port"
        echo -e "3. Then re-run this script"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Port configuration synchronized between backend and frontend${NC}"
    return 0
}

validate_port_sync
fi

# Step 1: ARM ChromeOS Environment Setup
echo -e "\n${BLUE}Step 1: ARM ChromeOS Environment Check${NC}"
if [[ -f "$SCRIPT_DIR/arm-chromeos-setup.sh" ]]; then
    "$SCRIPT_DIR/arm-chromeos-setup.sh" --check-only
    if [[ $? -ne 0 ]]; then
        echo -e "${YELLOW}ARM ChromeOS optimizations needed. Running setup...${NC}"
        "$SCRIPT_DIR/arm-chromeos-setup.sh"
    fi
else
    echo -e "${YELLOW}⚠ ARM ChromeOS setup script not found, continuing without optimizations${NC}"
fi

# Step 2: Setup production environment
echo -e "\n${BLUE}Step 2: Environment Setup${NC}"
if [[ ! -f ".env.production" ]]; then
    echo "Setting up production environment..."
    "$SCRIPT_DIR/setup-environment.sh" production
else
    echo -e "${GREEN}✓ Production environment exists${NC}"
fi

# Step 3: Build frontend (unless skipped)
if ! $SKIP_BUILD; then
    echo -e "\n${BLUE}Step 3: Building Frontend${NC}"
    "$SCRIPT_DIR/build-frontend.sh"
else
    echo -e "\n${BLUE}Step 3: Skipping Frontend Build${NC}"
    if [[ ! -d "frontend_build" ]] || [[ ! -f "frontend_build/index.html" ]]; then
        echo -e "${RED}Error: Frontend build not found and --skip-build specified${NC}"
        echo "Please run: ./scripts/build-frontend.sh"
        exit 1
    fi
    echo -e "${GREEN}✓ Using existing frontend build${NC}"
fi

# Step 4: Prepare production environment
echo -e "\n${BLUE}Step 4: Production Preparation${NC}"

# Install Python dependencies using Poetry (recommended) or pip fallback
if [[ -f "pyproject.toml" ]] && command -v poetry >/dev/null 2>&1; then
    echo "Installing Python dependencies with Poetry..."
    poetry install --only=main
    echo -e "${GREEN}✓ Poetry dependencies installed${NC}"
elif [[ -f "requirements.txt" ]]; then
    # Fallback to pip if Poetry not available
    if [[ -d "venv" ]]; then
        source venv/bin/activate
        echo "Checking Python dependencies with pip..."
        pip install -r requirements.txt --quiet
        echo -e "${GREEN}✓ Python dependencies updated${NC}"
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
        echo "Checking Python dependencies with pip..."
        pip install -r requirements.txt --quiet
        echo -e "${GREEN}✓ Python dependencies updated${NC}"
    else
        echo -e "${YELLOW}⚠ No virtual environment found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No pyproject.toml or requirements.txt found${NC}"
fi

# Run database migrations if using Alembic
if [[ -f "alembic.ini" ]]; then
    echo "Running database migrations..."
    if command -v poetry >/dev/null 2>&1; then
        poetry run alembic upgrade head
        echo -e "${GREEN}✓ Database migrations completed${NC}"
    elif command -v alembic >/dev/null; then
        alembic upgrade head
        echo -e "${GREEN}✓ Database migrations completed${NC}"
    else
        echo -e "${YELLOW}⚠ Alembic not found, skipping migrations${NC}"
    fi
fi

# Step 5: Pre-deployment validation
echo -e "\n${BLUE}Step 5: Pre-deployment Validation${NC}"

# Activate virtual environment for validation
if [[ -d "venv" ]]; then
    source venv/bin/activate
elif [[ -d ".venv" ]]; then
    source .venv/bin/activate
fi

# Validate configuration
if python -c "from app.config import get_config; config = get_config(); print('Production config valid')" 2>/dev/null; then
    echo -e "${GREEN}✓ Production configuration valid${NC}"
else
    echo -e "${RED}✗ Production configuration invalid${NC}"
    exit 1
fi

# Validate frontend build
if [[ -f "frontend_build/index.html" ]]; then
    file_count=$(find frontend_build -type f | wc -l)
    build_size=$(du -sh frontend_build | cut -f1)
    echo -e "${GREEN}✓ Frontend build valid ($file_count files, $build_size)${NC}"
else
    echo -e "${RED}✗ Frontend build invalid${NC}"
    exit 1
fi

# Step 6: Deploy production server
echo -e "\n${BLUE}Step 6: Starting Production Server${NC}"
"$SCRIPT_DIR/prod-start.sh"

# Step 7: Post-deployment verification
echo -e "\n${BLUE}Step 7: Post-deployment Verification${NC}"

sleep 5  # Give server time to fully start

# Health check
port=$(grep "^FLASK_PORT=" .env.production | cut -d'=' -f2 || echo "8080")
if curl -s "http://localhost:$port/" > /dev/null; then
    echo -e "${GREEN}✓ Server health check passed${NC}"
else
    echo -e "${YELLOW}⚠ Health check failed${NC}"
    echo "Check logs: tail -f production.log"
fi

# API check
if curl -s "http://localhost:$port/api/v1/" > /dev/null; then
    echo -e "${GREEN}✓ API endpoint check passed${NC}"
else
    echo -e "${YELLOW}⚠ API endpoint check failed${NC}"
fi

# Frontend check
if curl -s "http://localhost:$port/" | grep -q "<!DOCTYPE html>"; then
    echo -e "${GREEN}✓ Frontend serving check passed${NC}"
else
    echo -e "${YELLOW}⚠ Frontend serving check failed${NC}"
fi

echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo "======================================="

# Show deployment summary
echo -e "${BLUE}Deployment Summary:${NC}"
echo "  Environment: production"
echo "  Port: $port"
echo "  Frontend: $(find frontend_build -type f | wc -l) files"
echo "  Server PID: $(cat pids/production.pid 2>/dev/null || echo 'unknown')"
echo ""
echo -e "${BLUE}Access your application:${NC}"
echo "  http://localhost:$port"

host=$(grep "^FLASK_HOST=" .env.production | cut -d'=' -f2 || echo "0.0.0.0")
if [[ "$host" == "0.0.0.0" ]]; then
    echo "  http://$(hostname -I | awk '{print $1}'):$port"
fi

echo ""
echo -e "${BLUE}Management commands:${NC}"
echo "  Stop:     ./scripts/prod-stop.sh"
echo "  Restart:  ./scripts/restart.sh production"
echo "  Status:   ./scripts/status.sh"
echo "  Logs:     tail -f production.log"

echo -e "\n${YELLOW}🎯 Deployment complete! Your application is now running in production mode.${NC}"