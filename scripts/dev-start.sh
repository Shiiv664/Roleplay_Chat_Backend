#!/bin/bash

# Start development servers (Flask backend + Vite frontend)
# Usage: ./scripts/dev-start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$(cd "$PROJECT_ROOT/../Roleplay_Chat_Frontend" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Development Environment${NC}"
echo "=================================="

# Setup environment
echo -e "${YELLOW}Setting up development environment...${NC}"
export FLASK_ENV=development

# Setup backend environment if needed
cd "$PROJECT_ROOT"
if [[ ! -f ".env.development" ]]; then
    echo "Setting up backend environment..."
    "$SCRIPT_DIR/setup-environment.sh" development
fi

# Check if frontend directory exists
if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Setup frontend environment if needed
cd "$FRONTEND_DIR"
if [[ ! -f ".env.development" ]]; then
    echo "Setting up frontend environment..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env.development
        echo "Created .env.development from template"
    fi
fi

# Install dependencies if needed
echo -e "\n${BLUE}Checking dependencies...${NC}"

# Backend dependencies
cd "$PROJECT_ROOT"
if [[ ! -d "venv" ]] && [[ ! -d ".venv" ]]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt found"
else
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
fi

# Frontend dependencies
cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Create PID directory
mkdir -p "$PROJECT_ROOT/pids"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start backend
start_backend() {
    cd "$PROJECT_ROOT"
    
    # Check if backend is already running
    if [[ -f "pids/backend.pid" ]]; then
        local pid=$(cat pids/backend.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Backend already running (PID: $pid)${NC}"
            return
        else
            rm -f pids/backend.pid
        fi
    fi
    
    # Check if port 5000 is in use
    if check_port 5000; then
        echo -e "${YELLOW}Port 5000 is already in use by another process${NC}"
        echo "Attempting to start backend anyway..."
    fi
    
    echo -e "${BLUE}Starting Flask backend...${NC}"
    
    # Activate virtual environment if it exists
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
    
    # Start backend in background
    export FLASK_ENV=development
    nohup python app.py > backend_dev.log 2>&1 &
    local backend_pid=$!
    echo $backend_pid > pids/backend.pid
    
    echo -e "${GREEN}✓ Backend started (PID: $backend_pid)${NC}"
    echo "  - URL: http://127.0.0.1:5000"
    echo "  - API Docs: http://127.0.0.1:5000/api/v1/docs"
    echo "  - Logs: tail -f backend_dev.log"
}

# Function to start frontend
start_frontend() {
    cd "$FRONTEND_DIR"
    
    # Check if frontend is already running
    if [[ -f "pids/frontend.pid" ]]; then
        local pid=$(cat pids/frontend.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Frontend already running (PID: $pid)${NC}"
            return
        else
            rm -f pids/frontend.pid
        fi
    fi
    
    # Check if port 5173 is in use
    if check_port 5173; then
        echo -e "${YELLOW}Port 5173 is already in use by another process${NC}"
        echo "Attempting to start frontend anyway..."
    fi
    
    echo -e "${BLUE}Starting Vite frontend...${NC}"
    
    # Create pids directory in frontend
    mkdir -p pids
    
    # Start frontend in background
    export NODE_ENV=development
    nohup npm run dev > frontend_dev.log 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > pids/frontend.pid
    
    echo -e "${GREEN}✓ Frontend started (PID: $frontend_pid)${NC}"
    echo "  - URL: http://localhost:5173"
    echo "  - Network: http://0.0.0.0:5173"
    echo "  - Logs: tail -f frontend_dev.log"
}

# Start services
echo -e "\n${BLUE}Starting development servers...${NC}"

start_backend
sleep 2  # Give backend time to start

start_frontend
sleep 3  # Give frontend time to start

echo -e "\n${GREEN}🎉 Development environment started!${NC}"
echo "======================================"
echo -e "${BLUE}Services:${NC}"
echo "  Backend:  http://127.0.0.1:5000"
echo "  Frontend: http://localhost:5173"
echo ""
echo -e "${BLUE}Management:${NC}"
echo "  Stop all:     ./scripts/dev-stop.sh"
echo "  View logs:    ./scripts/logs.sh"
echo "  Check status: ./scripts/status.sh"
echo ""
echo -e "${YELLOW}Note: Services are running in background. Use dev-stop.sh to stop them.${NC}"