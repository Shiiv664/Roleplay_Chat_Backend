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

echo -e "\n${BLUE}Step 2: Building frontend for production${NC}"
# Set production mode and empty API base URL (will use same server)
export NODE_ENV=production
export VITE_API_BASE_URL=""

# Build the frontend
npm run build

# Check if build was successful
if [[ ! -d "dist" ]]; then
    echo -e "${RED}Error: Frontend build failed - dist directory not found${NC}"
    exit 1
fi

echo -e "\n${BLUE}Step 3: Copying build files to backend${NC}"
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

echo -e "\n${BLUE}Step 4: Updating frontend API configuration${NC}"
# The frontend is built with empty VITE_API_BASE_URL, so it will use relative URLs
echo "Frontend built with relative API URLs for production"

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