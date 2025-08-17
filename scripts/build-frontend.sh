#!/bin/bash

# Build React frontend and copy to backend for production serving
# Usage: ./scripts/build-frontend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$(cd "$PROJECT_ROOT/../frontend" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏗️  Frontend Build and Integration${NC}"
echo "=================================="

# Check if frontend directory exists
if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Frontend directory: $FRONTEND_DIR${NC}"
echo -e "${YELLOW}Backend directory: $PROJECT_ROOT${NC}"

cd "$FRONTEND_DIR"

# Check if package.json exists
if [[ ! -f "package.json" ]]; then
    echo -e "${RED}Error: package.json not found in frontend directory${NC}"
    exit 1
fi

echo -e "\n${BLUE}Step 1: Installing frontend dependencies${NC}"
if command -v npm &> /dev/null; then
    npm install
else
    echo -e "${RED}Error: npm not found. Please install Node.js and npm${NC}"
    exit 1
fi

# Port validation function
validate_port_sync() {
    local backend_env="$PROJECT_ROOT/.env.production"
    local frontend_env="$FRONTEND_DIR/.env.production"
    
    # Check if both env files exist
    if [[ ! -f "$backend_env" ]]; then
        echo -e "${RED}Error: Backend .env.production not found at $backend_env${NC}"
        exit 1
    fi
    
    if [[ ! -f "$frontend_env" ]]; then
        echo -e "${YELLOW}Warning: Frontend .env.production not found, will use VITE_API_BASE_URL from build environment${NC}"
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
    
    echo -e "${GREEN}✓ Port configuration validated - Backend and frontend ports are synchronized${NC}"
    return 0
}

echo -e "\n${BLUE}Step 2: Port Configuration Validation${NC}"
validate_port_sync

echo -e "\n${BLUE}Step 3: Building frontend for production${NC}"
# Read Flask port from environment file
FLASK_PORT=$(grep "^FLASK_PORT=" "$PROJECT_ROOT/.env.production" | cut -d'=' -f2 || echo "5000")

# Set production mode and API base URL with correct port
export NODE_ENV=production
export VITE_API_BASE_URL="http://localhost:${FLASK_PORT}"

# Build the frontend
npm run build

# Check if build was successful
if [[ ! -d "dist" ]]; then
    echo -e "${RED}Error: Frontend build failed - dist directory not found${NC}"
    exit 1
fi

echo -e "\n${BLUE}Step 4: Copying build files to backend${NC}"
cd "$PROJECT_ROOT"

# Remove existing frontend_build directory
if [[ -d "frontend_build" ]]; then
    echo "Removing existing frontend_build directory..."
    rm -rf frontend_build
fi

# Copy dist files to backend
echo "Copying build files..."
cp -r "$FRONTEND_DIR/dist" frontend_build

# Verify copy was successful
if [[ ! -f "frontend_build/index.html" ]]; then
    echo -e "${RED}Error: Copy failed - index.html not found in frontend_build${NC}"
    exit 1
fi

echo -e "\n${BLUE}Step 5: Updating frontend API configuration${NC}"
# The frontend is built with VITE_API_BASE_URL pointing to the configured Flask port
echo "Frontend built with API URLs pointing to port ${FLASK_PORT}"

echo -e "\n${GREEN}✓ Frontend build completed successfully!${NC}"
echo -e "${GREEN}✓ Files copied to: $PROJECT_ROOT/frontend_build${NC}"

# Show build summary
echo -e "\n${BLUE}Build Summary:${NC}"
echo "Frontend files: $(find frontend_build -type f | wc -l) files"
echo "Total size: $(du -sh frontend_build | cut -f1)"

# List main files
echo -e "\nMain files:"
find frontend_build -maxdepth 1 -name "*.html" -o -name "*.js" -o -name "*.css" | head -10

echo -e "\n${YELLOW}Note: Run the backend with FLASK_ENV=production to serve these files${NC}"