#!/bin/bash

# Stop production server
# Usage: ./scripts/prod-stop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Production Server${NC}"
echo "============================="

cd "$PROJECT_ROOT"

# Function to stop service by PID file
stop_production_service() {
    local pid_file="pids/production.pid"
    local log_file="production.log"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping production server (PID: $pid)...${NC}"
            
            # Try graceful shutdown first
            kill $pid
            
            # Wait for process to stop
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 15 ]; do
                echo "Waiting for graceful shutdown... ($count/15)"
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}Graceful shutdown timeout, force killing...${NC}"
                kill -9 $pid
                sleep 2
            fi
            
            if ! ps -p $pid > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Production server stopped${NC}"
            else
                echo -e "${RED}✗ Failed to stop production server${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}Production server process not found (stale PID file)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}Production server PID file not found${NC}"
        echo "Server may not be running or was started manually"
    fi
    
    # Archive log file with timestamp
    if [[ -f "$log_file" ]]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        local archived_log="${log_file}.${timestamp}"
        mv "$log_file" "$archived_log"
        echo -e "${BLUE}Log archived: $archived_log${NC}"
    fi
}

# Stop the production server
stop_production_service

# Additional cleanup - kill any remaining processes on production port
echo -e "\n${BLUE}Cleaning up production port...${NC}"

# Get production port
local port=8080
if [[ -f ".env.production" ]]; then
    port=$(grep "^FLASK_PORT=" .env.production | cut -d'=' -f2 || echo "8080")
fi

# Kill processes on production port
if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
    echo "Killing remaining processes on port $port..."
    lsof -Ti :$port | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Kill any remaining python processes related to our app in production mode
pkill -f "FLASK_ENV=production.*python app.py" 2>/dev/null || true
pkill -f "python app.py.*production" 2>/dev/null || true

echo -e "\n${GREEN}🎉 Production server stopped!${NC}"
echo "============================"

# Verification
echo -e "\n${BLUE}Cleanup verification:${NC}"
if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
    echo -e "${YELLOW}⚠ Port $port still in use:${NC}"
    lsof -Pi :$port -sTCP:LISTEN
    echo ""
    echo "You may need to manually kill the process:"
    echo "  sudo lsof -Ti :$port | xargs sudo kill -9"
else
    echo -e "${GREEN}✓ Port $port is now available${NC}"
fi

# Show status
if [[ -f "pids/production.pid" ]]; then
    echo -e "${YELLOW}⚠ PID file still exists (this shouldn't happen)${NC}"
else
    echo -e "${GREEN}✓ PID file cleaned up${NC}"
fi

echo -e "\n${BLUE}Tip: Use ./scripts/status.sh to verify the server is stopped${NC}"