#!/bin/bash

# Check service status and health
# Usage: ./scripts/status.sh [service]

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

echo -e "${BLUE}📊 Service Status Report${NC}"
echo "========================"

cd "$PROJECT_ROOT"

# Function to check service status
check_service() {
    local service_name="$1"
    local pid_file="$2"
    local port="$3"
    local url="$4"
    
    echo -e "\n${BLUE}$service_name:${NC}"
    echo "==============="
    
    # Check PID file
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "  Status: ${GREEN}RUNNING${NC} (PID: $pid)"
            
            # Get process info
            local start_time=$(ps -p $pid -o lstart= | xargs)
            echo -e "  Started: $start_time"
            
            # Get memory usage
            local memory=$(ps -p $pid -o rss= | xargs)
            if [[ -n "$memory" ]]; then
                memory_mb=$((memory / 1024))
                echo -e "  Memory: ${memory_mb}MB"
            fi
            
        else
            echo -e "  Status: ${RED}STOPPED${NC} (stale PID file)"
            echo -e "  PID file: $pid_file (contains stale PID: $pid)"
        fi
    else
        echo -e "  Status: ${RED}STOPPED${NC} (no PID file)"
    fi
    
    # Check port
    if [[ -n "$port" ]]; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
            local port_pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            echo -e "  Port $port: ${GREEN}IN USE${NC} (PID: $port_pid)"
            
            # Check if it's our process
            if [[ -f "$pid_file" ]]; then
                local our_pid=$(cat "$pid_file")
                if [[ "$port_pid" == "$our_pid" ]]; then
                    echo -e "  Port match: ${GREEN}YES${NC} (our process)"
                else
                    echo -e "  Port match: ${YELLOW}NO${NC} (different process)"
                fi
            fi
        else
            echo -e "  Port $port: ${RED}FREE${NC}"
        fi
    fi
    
    # Check HTTP endpoint if URL provided
    if [[ -n "$url" ]]; then
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            echo -e "  HTTP check: ${GREEN}RESPONDING${NC}"
            
            # Get response time
            local response_time=$(curl -s -w "%{time_total}" --max-time 5 "$url" -o /dev/null 2>/dev/null || echo "timeout")
            if [[ "$response_time" != "timeout" ]]; then
                echo -e "  Response time: ${response_time}s"
            fi
        else
            echo -e "  HTTP check: ${RED}NOT RESPONDING${NC}"
        fi
    fi
}

# Function to show environment info
show_environment() {
    echo -e "\n${BLUE}Environment Information:${NC}"
    echo "========================"
    
    # Current Flask environment
    local current_env=$(grep "^FLASK_ENV=" .env.development 2>/dev/null | cut -d'=' -f2 || echo "not set")
    echo -e "  Current mode: $current_env"
    
    # Environment files
    for env in "development" "production"; do
        if [[ -f ".env.$env" ]]; then
            echo -e "  .env.$env: ${GREEN}EXISTS${NC}"
            
            # Check for important variables
            local secret_key=$(grep "^SECRET_KEY=" ".env.$env" | cut -d'=' -f2)
            local encryption_key=$(grep "^ENCRYPTION_KEY=" ".env.$env" | cut -d'=' -f2)
            
            if [[ -n "$secret_key" ]]; then
                echo -e "    SECRET_KEY: ${GREEN}SET${NC}"
            else
                echo -e "    SECRET_KEY: ${YELLOW}EMPTY${NC}"
            fi
            
            if [[ -n "$encryption_key" ]]; then
                echo -e "    ENCRYPTION_KEY: ${GREEN}SET${NC}"
            else
                echo -e "    ENCRYPTION_KEY: ${YELLOW}EMPTY${NC}"
            fi
        else
            echo -e "  .env.$env: ${RED}MISSING${NC}"
        fi
    done
    
    # Frontend build
    if [[ -d "frontend_build" ]]; then
        local file_count=$(find frontend_build -type f | wc -l)
        local build_size=$(du -sh frontend_build | cut -f1)
        echo -e "  Frontend build: ${GREEN}READY${NC} ($file_count files, $build_size)"
    else
        echo -e "  Frontend build: ${YELLOW}NOT BUILT${NC}"
    fi
}

# Function to show recent logs
show_recent_logs() {
    echo -e "\n${BLUE}Recent Log Activity:${NC}"
    echo "===================="
    
    # Development logs
    if [[ -f "backend_dev.log" ]]; then
        echo -e "\n${YELLOW}Development Backend (last 5 lines):${NC}"
        tail -5 backend_dev.log 2>/dev/null || echo "  No recent activity"
    fi
    
    if [[ -d "$FRONTEND_DIR" ]] && [[ -f "$FRONTEND_DIR/frontend_dev.log" ]]; then
        echo -e "\n${YELLOW}Development Frontend (last 5 lines):${NC}"
        tail -5 "$FRONTEND_DIR/frontend_dev.log" 2>/dev/null || echo "  No recent activity"
    fi
    
    # Production logs
    if [[ -f "production.log" ]]; then
        echo -e "\n${YELLOW}Production (last 5 lines):${NC}"
        tail -5 production.log 2>/dev/null || echo "  No recent activity"
    fi
}

# Main logic
case "${1:-}" in
    "dev"|"development")
        check_service "Development Backend" "pids/backend.pid" "5000" "http://localhost:5000"
        if [[ -n "$FRONTEND_DIR" ]] && [[ -d "$FRONTEND_DIR" ]]; then
            cd "$FRONTEND_DIR"
            check_service "Development Frontend" "pids/frontend.pid" "5173" "http://localhost:5173"
            cd "$PROJECT_ROOT"
        fi
        ;;
    "prod"|"production")
        port=$(grep "^FLASK_PORT=" .env.production 2>/dev/null | cut -d'=' -f2 || echo "8080")
        check_service "Production Server" "pids/production.pid" "$port" "http://localhost:$port"
        ;;
    "")
        # Show all services
        echo -e "${YELLOW}Checking all services...${NC}"
        
        # Development services
        check_service "Development Backend" "pids/backend.pid" "5000" "http://localhost:5000"
        
        if [[ -n "$FRONTEND_DIR" ]] && [[ -d "$FRONTEND_DIR" ]]; then
            cd "$FRONTEND_DIR"
            check_service "Development Frontend" "pids/frontend.pid" "5173" "http://localhost:5173"
            cd "$PROJECT_ROOT"
        fi
        
        # Production service
        port=$(grep "^FLASK_PORT=" .env.production 2>/dev/null | cut -d'=' -f2 || echo "8080")
        check_service "Production Server" "pids/production.pid" "$port" "http://localhost:$port"
        
        # Environment info
        show_environment
        
        # Recent logs
        show_recent_logs
        ;;
    *)
        echo -e "${RED}Usage: $0 [dev|prod]${NC}"
        echo "Examples:"
        echo "  $0        # Show all services"
        echo "  $0 dev    # Show development services only"
        echo "  $0 prod   # Show production service only"
        exit 1
        ;;
esac

echo -e "\n${BLUE}Quick Commands:${NC}"
echo "==============="
echo "  Start dev:  ./scripts/dev-start.sh"
echo "  Stop dev:   ./scripts/dev-stop.sh"
echo "  Start prod: ./scripts/prod-start.sh"
echo "  Stop prod:  ./scripts/prod-stop.sh"
echo "  Deploy:     ./scripts/deploy.sh"
echo "  Logs:       ./scripts/logs.sh"
echo "  Restart:    ./scripts/restart.sh [dev|prod]"