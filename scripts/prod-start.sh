#!/bin/bash

# Start production server (single Flask server serving both API and React static files)
# Usage: ./scripts/prod-start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Production Server${NC}"
echo "=============================="

# Setup environment
echo -e "${YELLOW}Setting up production environment...${NC}"
export FLASK_ENV=production

cd "$PROJECT_ROOT"

# Setup environment if needed
if [[ ! -f ".env.production" ]]; then
    echo "Setting up production environment..."
    "$SCRIPT_DIR/setup-environment.sh" production
fi

# Check if frontend is built
if [[ ! -d "frontend_build" ]] || [[ ! -f "frontend_build/index.html" ]]; then
    echo -e "${YELLOW}Frontend not built. Building now...${NC}"
    "$SCRIPT_DIR/build-frontend.sh"
fi

# Activate virtual environment if it exists
if [[ -d "venv" ]]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Activated virtual environment${NC}"
elif [[ -d ".venv" ]]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Activated virtual environment${NC}"
else
    echo -e "${YELLOW}⚠ No virtual environment found${NC}"
fi

# Create PID directory
mkdir -p pids

# Function to check if port is in use
check_port() {
    port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check if production server is already running
if [[ -f "pids/production.pid" ]]; then
    pid=$(cat pids/production.pid)
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${YELLOW}Production server already running (PID: $pid)${NC}"
        
        # Check what port it's using
        port=$(grep "^FLASK_PORT=" .env.production | cut -d'=' -f2 || echo "8080")
        echo "  URL: http://localhost:$port"
        echo "  To restart: ./scripts/restart.sh production"
        echo "  To stop: ./scripts/prod-stop.sh"
        exit 0
    else
        rm -f pids/production.pid
    fi
fi

# Get production port
port=$(grep "^FLASK_PORT=" .env.production | cut -d'=' -f2 || echo "8080")

# Check if port is in use
if check_port $port; then
    echo -e "${RED}Error: Port $port is already in use${NC}"
    echo "Either stop the service using that port or change FLASK_PORT in .env.production"
    lsof -Pi :$port -sTCP:LISTEN
    exit 1
fi

echo -e "\n${BLUE}Starting production server...${NC}"

# Run pre-start checks
echo "Performing pre-start validation..."

# Check database
if poetry run python -c "from app.utils.db import check_db_connection; check_db_connection()" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${YELLOW}⚠ Database check failed, will initialize on start${NC}"
fi

# Check environment variables
if poetry run python -c "from app.config import get_config; config = get_config(); print('Config loaded successfully')" 2>/dev/null; then
    echo -e "${GREEN}✓ Configuration loaded successfully${NC}"
else
    echo -e "${RED}✗ Configuration failed to load${NC}"
    exit 1
fi

# Check frontend files
if [[ -f "frontend_build/index.html" ]]; then
    file_count=$(find frontend_build -type f | wc -l)
    echo -e "${GREEN}✓ Frontend files ready ($file_count files)${NC}"
else
    echo -e "${RED}✗ Frontend files missing${NC}"
    exit 1
fi

# Check database state and run migrations if needed
if [[ -f "alembic.ini" ]]; then
    echo "Checking database state..."
    if poetry run python -c "from app.utils.db import check_db_connection; check_db_connection()" 2>/dev/null; then
        echo -e "${GREEN}✓ Database is properly initialized${NC}"
    else
        echo "Database needs initialization, running migrations..."
        if poetry run alembic upgrade head 2>/dev/null; then
            echo -e "${GREEN}✓ Database migrations completed${NC}"
        else
            echo -e "${YELLOW}⚠ Database migrations failed${NC}"
        fi
    fi
fi

# Start the production server
echo -e "\n${BLUE}Launching Flask production server...${NC}"

# Use nohup for ARM ChromeOS VM compatibility
nohup env FLASK_ENV=production poetry run python app.py > production.log 2>&1 &
server_pid=$!
echo $server_pid > pids/production.pid

echo -e "${GREEN}✓ Production server started (PID: $server_pid)${NC}"

# Wait a moment and check if server started successfully
sleep 3

if ps -p $server_pid > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running successfully${NC}"
    
    # Show access information
    host=$(grep "^FLASK_HOST=" .env.production | cut -d'=' -f2 || echo "0.0.0.0")
    
    echo -e "\n${GREEN}🎉 Production server is ready!${NC}"
    echo "=============================="
    echo -e "${BLUE}Access URLs:${NC}"
    echo "  Local:    http://localhost:$port"
    if [[ "$host" == "0.0.0.0" ]]; then
        echo "  Network:  http://$(hostname -I | awk '{print $1}'):$port"
    fi
    echo ""
    echo -e "${BLUE}Features:${NC}"
    echo "  ✓ API endpoints at /api/v1/*"
    echo "  ✓ React frontend served from /"
    echo "  ✓ Single-server architecture"
    echo "  ✓ Production optimizations enabled"
    echo ""
    echo -e "${BLUE}Management:${NC}"
    echo "  Stop:     ./scripts/prod-stop.sh"
    echo "  Restart:  ./scripts/restart.sh production"
    echo "  Logs:     tail -f production.log"
    echo "  Status:   ./scripts/status.sh"
    
    # Health check
    sleep 2
    echo -e "\n${BLUE}Performing health check...${NC}"
    if curl -s "http://localhost:$port/" > /dev/null; then
        echo -e "${GREEN}✓ Server health check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Health check failed - server may still be starting${NC}"
    fi
    
else
    echo -e "${RED}✗ Server failed to start${NC}"
    echo "Check the logs: tail -f production.log"
    rm -f pids/production.pid
    exit 1
fi

echo -e "\n${YELLOW}Note: Server is running in background. Use prod-stop.sh to stop it.${NC}"