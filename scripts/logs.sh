#!/bin/bash

# View real-time logs
# Usage: ./scripts/logs.sh [service] [--follow]

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

echo -e "${BLUE}📋 Log Viewer${NC}"
echo "=============="

cd "$PROJECT_ROOT"

# Parse arguments
SERVICE=""
FOLLOW=false
LINES=50

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        dev|development|backend|frontend|prod|production)
            SERVICE="$1"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [service] [--follow] [--lines N]"
            echo "Services: dev, backend, frontend, prod, production"
            echo "Options:"
            echo "  -f, --follow    Follow log output (like tail -f)"
            echo "  -n, --lines N   Number of lines to show (default: 50)"
            exit 1
            ;;
    esac
done

# Function to show log with colors and formatting
show_log() {
    local log_file="$1"
    local service_name="$2"
    local follow="$3"
    
    if [[ ! -f "$log_file" ]]; then
        echo -e "${YELLOW}No log file found: $log_file${NC}"
        return
    fi
    
    echo -e "\n${BLUE}=== $service_name ===${NC}"
    echo -e "${YELLOW}Log file: $log_file${NC}"
    echo -e "${YELLOW}Last modified: $(stat -c %y "$log_file" 2>/dev/null || echo 'unknown')${NC}"
    echo ""
    
    if $follow; then
        echo -e "${GREEN}Following log (Ctrl+C to stop)...${NC}"
        echo ""
        tail -f "$log_file"
    else
        echo -e "${GREEN}Last $LINES lines:${NC}"
        echo ""
        tail -n "$LINES" "$log_file"
    fi
}

# Function to show multiple logs with tail -f
follow_multiple_logs() {
    local log_files=()
    local log_names=()
    
    # Collect available log files
    if [[ -f "backend_dev.log" ]]; then
        log_files+=("backend_dev.log")
        log_names+=("DEV-BACKEND")
    fi
    
    if [[ -d "$FRONTEND_DIR" ]] && [[ -f "$FRONTEND_DIR/frontend_dev.log" ]]; then
        log_files+=("$FRONTEND_DIR/frontend_dev.log")
        log_names+=("DEV-FRONTEND")
    fi
    
    if [[ -f "production.log" ]]; then
        log_files+=("production.log")
        log_names+=("PRODUCTION")
    fi
    
    if [[ ${#log_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No log files found${NC}"
        return
    fi
    
    echo -e "${GREEN}Following ${#log_files[@]} log files (Ctrl+C to stop)...${NC}"
    echo "Files: ${log_names[*]}"
    echo ""
    
    # Use multitail if available, otherwise fall back to tail
    if command -v multitail >/dev/null 2>&1; then
        multitail "${log_files[@]}"
    else
        # Create a simple multi-tail using tail and awk to add prefixes
        for i in "${!log_files[@]}"; do
            tail -f "${log_files[$i]}" | awk -v prefix="[${log_names[$i]}]" '{print prefix " " $0}' &
        done
        
        echo -e "${YELLOW}Note: Install multitail for better multi-log viewing${NC}"
        echo "Press Ctrl+C to stop all log tails"
        
        # Wait for Ctrl+C
        trap 'kill $(jobs -p); exit' INT
        wait
    fi
}

# Main logic
case "$SERVICE" in
    "dev"|"development")
        if $FOLLOW; then
            follow_multiple_logs
        else
            show_log "backend_dev.log" "Development Backend" false
            if [[ -d "$FRONTEND_DIR" ]] && [[ -f "$FRONTEND_DIR/frontend_dev.log" ]]; then
                show_log "$FRONTEND_DIR/frontend_dev.log" "Development Frontend" false
            fi
        fi
        ;;
    "backend")
        show_log "backend_dev.log" "Development Backend" $FOLLOW
        ;;
    "frontend")
        if [[ -d "$FRONTEND_DIR" ]]; then
            show_log "$FRONTEND_DIR/frontend_dev.log" "Development Frontend" $FOLLOW
        else
            echo -e "${RED}Frontend directory not found${NC}"
        fi
        ;;
    "prod"|"production")
        show_log "production.log" "Production Server" $FOLLOW
        ;;
    "")
        # Show all logs
        if $FOLLOW; then
            follow_multiple_logs
        else
            echo -e "${YELLOW}Showing recent logs from all services...${NC}"
            
            show_log "backend_dev.log" "Development Backend" false
            
            if [[ -d "$FRONTEND_DIR" ]] && [[ -f "$FRONTEND_DIR/frontend_dev.log" ]]; then
                show_log "$FRONTEND_DIR/frontend_dev.log" "Development Frontend" false
            fi
            
            show_log "production.log" "Production Server" false
            
            # Show archived logs if any
            echo -e "\n${BLUE}=== Archived Logs ===${NC}"
            archived_logs=$(find . -name "*.log.*" -type f 2>/dev/null | head -5)
            if [[ -n "$archived_logs" ]]; then
                echo "Recent archived logs:"
                echo "$archived_logs"
            else
                echo "No archived logs found"
            fi
        fi
        ;;
    *)
        echo -e "${RED}Unknown service: $SERVICE${NC}"
        echo "Available services: dev, backend, frontend, prod, production"
        exit 1
        ;;
esac

# Show helpful commands at the end (only if not following)
if ! $FOLLOW; then
    echo -e "\n${BLUE}Log Commands:${NC}"
    echo "============="
    echo "  Follow all logs:      ./scripts/logs.sh --follow"
    echo "  Follow specific log:  ./scripts/logs.sh prod --follow"
    echo "  More lines:           ./scripts/logs.sh --lines 100"
    echo "  Clear old logs:       find . -name '*.log.*' -delete"
    echo ""
    echo -e "${BLUE}Log Files:${NC}"
    echo "  Development Backend:  backend_dev.log"
    echo "  Development Frontend: ../Roleplay_Chat_Frontend/frontend_dev.log"
    echo "  Production Server:    production.log"
fi