#!/bin/bash

# Simple development server starter
# Usage: ./scripts/dev-start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/../frontend"

echo "🚀 Starting Development Servers"
echo "==============================="

# Check if frontend exists
if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo "❌ Frontend directory not found at: $FRONTEND_DIR"
    exit 1
fi

# Create directories
mkdir -p "$PROJECT_ROOT/pids"
mkdir -p "$FRONTEND_DIR/pids"

# Function to start backend
start_backend() {
    echo "Starting Flask backend..."
    cd "$PROJECT_ROOT"
    
    # Kill existing backend if running
    if [[ -f "pids/backend.pid" ]]; then
        local pid=$(cat pids/backend.pid)
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            sleep 2
        fi
        rm -f pids/backend.pid
    fi
    
    # Start backend
    export FLASK_ENV=development
    nohup poetry run python3 app.py > backend_dev.log 2>&1 &
    local backend_pid=$!
    echo $backend_pid > pids/backend.pid
    
    echo "✓ Backend started (PID: $backend_pid)"
    echo "  - URL: http://127.0.0.1:5000"
    echo "  - API Docs: http://127.0.0.1:5000/api/v1/docs"
}

# Function to start frontend  
start_frontend() {
    echo "Starting Vite frontend..."
    cd "$FRONTEND_DIR"
    
    # Kill existing frontend if running
    if [[ -f "pids/frontend.pid" ]]; then
        local pid=$(cat pids/frontend.pid)
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            sleep 2
        fi
        rm -f pids/frontend.pid
    fi
    
    # Start frontend
    nohup npm run dev > frontend_dev.log 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > pids/frontend.pid
    
    echo "✓ Frontend started (PID: $frontend_pid)"
    echo "  - URL: http://localhost:5173"
}

# Start services
start_backend
sleep 2
start_frontend
sleep 3

echo ""
echo "🎉 Both servers are running!"
echo "Backend:  http://127.0.0.1:5000"
echo "Frontend: http://localhost:5173"
echo ""
echo "To stop: ./scripts/dev-stop.sh"