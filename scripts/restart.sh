#!/bin/bash

# Restart services
# Usage: ./scripts/restart.sh [service]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Service Restart${NC}"
echo "=================="

cd "$PROJECT_ROOT"

# Function to restart development services
restart_development() {
    echo -e "${YELLOW}Restarting development environment...${NC}"
    
    # Stop development services
    echo "Stopping development services..."
    "$SCRIPT_DIR/dev-stop.sh"
    
    # Wait a moment
    sleep 2
    
    # Start development services
    echo "Starting development services..."
    "$SCRIPT_DIR/dev-start.sh"
    
    echo -e "${GREEN}✓ Development environment restarted${NC}"
}

# Function to restart production service
restart_production() {
    echo -e "${YELLOW}Restarting production server...${NC}"
    
    # Stop production service
    echo "Stopping production server..."
    "$SCRIPT_DIR/prod-stop.sh"
    
    # Wait a moment
    sleep 2
    
    # Start production service
    echo "Starting production server..."
    "$SCRIPT_DIR/prod-start.sh"
    
    echo -e "${GREEN}✓ Production server restarted${NC}"
}

# Function to graceful restart (with health check)
graceful_restart_production() {
    echo -e "${YELLOW}Performing graceful production restart...${NC}"
    
    # Check if production is running
    if [[ ! -f "pids/production.pid" ]]; then
        echo -e "${YELLOW}Production server not running, starting...${NC}"
        "$SCRIPT_DIR/prod-start.sh"
        return
    fi
    
    local pid=$(cat pids/production.pid)
    if ! ps -p $pid > /dev/null 2>&1; then
        echo -e "${YELLOW}Production server not running (stale PID), starting...${NC}"
        rm -f pids/production.pid
        "$SCRIPT_DIR/prod-start.sh"
        return
    fi
    
    # Get current port
    local port=$(grep "^FLASK_PORT=" .env.production | cut -d'=' -f2 || echo "8080")
    
    # Health check before restart
    echo "Performing pre-restart health check..."
    if curl -s --max-time 5 "http://localhost:$port/" > /dev/null; then
        echo -e "${GREEN}✓ Server is healthy before restart${NC}"
    else
        echo -e "${YELLOW}⚠ Server not responding, forcing restart${NC}"
    fi
    
    # Stop with grace period
    echo "Stopping production server gracefully..."
    "$SCRIPT_DIR/prod-stop.sh"
    
    # Wait a bit longer for cleanup
    sleep 3
    
    # Start production service
    echo "Starting production server..."
    "$SCRIPT_DIR/prod-start.sh"
    
    # Post-restart health check
    echo "Performing post-restart health check..."
    sleep 5
    
    local attempts=0
    local max_attempts=12  # 60 seconds total
    
    while [ $attempts -lt $max_attempts ]; do
        if curl -s --max-time 5 "http://localhost:$port/" > /dev/null; then
            echo -e "${GREEN}✓ Server is healthy after restart${NC}"
            break
        fi
        
        attempts=$((attempts + 1))
        echo "  Waiting for server to respond... ($attempts/$max_attempts)"
        sleep 5
    done
    
    if [ $attempts -eq $max_attempts ]; then
        echo -e "${RED}✗ Server health check failed after restart${NC}"
        echo "Check logs: tail -f production.log"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Graceful production restart completed${NC}"
}

# Function to quick restart (just the process, no rebuild)
quick_restart_production() {
    echo -e "${YELLOW}Performing quick production restart (no rebuild)...${NC}"
    
    # Just restart the Python process without rebuilding frontend
    if [[ -f "pids/production.pid" ]]; then
        local pid=$(cat pids/production.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping production process..."
            kill $pid
            
            # Wait for process to stop
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
        fi
        rm -f pids/production.pid
    fi
    
    # Start just the Flask app
    echo "Starting production server..."
    export FLASK_ENV=production
    
    # Activate virtual environment if it exists
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
    
    nohup poetry run python app.py > production.log 2>&1 &
    local server_pid=$!
    echo $server_pid > pids/production.pid
    
    echo -e "${GREEN}✓ Quick restart completed (PID: $server_pid)${NC}"
}

# Main logic
case "${1:-}" in
    "dev"|"development")
        restart_development
        ;;
    "prod"|"production")
        restart_production
        ;;
    "graceful"|"graceful-prod")
        graceful_restart_production
        ;;
    "quick"|"quick-prod")
        quick_restart_production
        ;;
    "")
        # Interactive mode
        echo "Available restart options:"
        echo "  1) Development environment (stop + start)"
        echo "  2) Production server (stop + start)"
        echo "  3) Production graceful (with health checks)"
        echo "  4) Production quick (process only, no rebuild)"
        echo ""
        read -p "Select option (1-4): " choice
        
        case $choice in
            1)
                restart_development
                ;;
            2)
                restart_production
                ;;
            3)
                graceful_restart_production
                ;;
            4)
                quick_restart_production
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                exit 1
                ;;
        esac
        ;;
    *)
        echo -e "${RED}Usage: $0 [service]${NC}"
        echo "Services:"
        echo "  dev          Restart development environment"
        echo "  prod         Restart production server"
        echo "  graceful     Graceful production restart with health checks"
        echo "  quick        Quick production restart (no rebuild)"
        echo ""
        echo "Examples:"
        echo "  $0 dev       # Restart development servers"
        echo "  $0 prod      # Restart production server"
        echo "  $0 graceful  # Graceful production restart"
        echo "  $0           # Interactive mode"
        exit 1
        ;;
esac

echo -e "\n${BLUE}Restart completed! Use ./scripts/status.sh to verify services.${NC}"