#!/bin/bash

# Stop development servers (Flask backend + Vite frontend)
# Usage: ./scripts/dev-stop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Discover frontend directory with fallback logic
FRONTEND_DIR=""
if [[ -d "$PROJECT_ROOT/../frontend" ]]; then
    FRONTEND_DIR="$(cd "$PROJECT_ROOT/../frontend" && pwd)"
elif [[ -d "$PROJECT_ROOT/../Roleplay_Chat_Frontend" ]]; then
    FRONTEND_DIR="$(cd "$PROJECT_ROOT/../Roleplay_Chat_Frontend" && pwd)"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Development Environment${NC}"
echo "=================================="

# Function to stop service by PID file
stop_service() {
    local service_name="$1"
    local pid_file="$2"
    local log_file="$3"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
            kill $pid
            
            # Wait for process to stop
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}Process still running, force killing...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✓ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}$service_name process not found (stale PID file)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}$service_name PID file not found${NC}"
    fi
    
    # Optionally archive log file
    if [[ -f "$log_file" ]]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        mv "$log_file" "${log_file}.${timestamp}"
        echo "  Log archived: ${log_file}.${timestamp}"
    fi
}

# Stop backend
cd "$PROJECT_ROOT"
stop_service "Backend" "pids/backend.pid" "backend_dev.log"

# Stop frontend
if [[ -n "$FRONTEND_DIR" ]] && [[ -d "$FRONTEND_DIR" ]]; then
    cd "$FRONTEND_DIR"
    stop_service "Frontend" "pids/frontend.pid" "frontend_dev.log"
fi

# Additional cleanup - kill any remaining processes on development ports
echo -e "\n${BLUE}Cleaning up development ports...${NC}"

# Kill processes on port 5000 (backend)
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
    echo "Killing remaining processes on port 5000..."
    lsof -t -i :5000 | xargs kill -9 2>/dev/null || true
fi

# Kill processes on port 5173 (frontend)
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null; then
    echo "Killing remaining processes on port 5173..."
    lsof -t -i :5173 | xargs kill -9 2>/dev/null || true
fi

# Kill any remaining node processes related to vite
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

# Kill any remaining python processes related to our app
pkill -f "python app.py" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

echo -e "\n${GREEN}🎉 Development environment stopped!${NC}"
echo "==================================="

# Show any remaining processes that might be related
echo -e "\n${BLUE}Process cleanup verification:${NC}"
remaining_processes=false

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
    echo -e "${YELLOW}⚠ Port 5000 still in use:${NC}"
    lsof -Pi :5000 -sTCP:LISTEN
    remaining_processes=true
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null; then
    echo -e "${YELLOW}⚠ Port 5173 still in use:${NC}"
    lsof -Pi :5173 -sTCP:LISTEN
    remaining_processes=true
fi

if ! $remaining_processes; then
    echo -e "${GREEN}✓ All development ports are clear${NC}"
fi

echo -e "\n${BLUE}Tip: Use ./scripts/status.sh to verify services are stopped${NC}"