#!/bin/bash

# Deploy from GitHub repository
# Usage: ./scripts/deploy-from-git.sh [branch] [--backup] [--force]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 Git-based Deployment${NC}"
echo "======================="

# Default values
BRANCH="main"
BACKUP=false
FORCE=false
REPO_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup)
            BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --repo)
            REPO_URL="$2"
            shift 2
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [branch] [--backup] [--force] [--repo URL]"
            echo "  --backup  Create backup before deployment"
            echo "  --force   Force deployment even if there are local changes"
            echo "  --repo    Specify repository URL"
            exit 1
            ;;
        *)
            BRANCH="$1"
            shift
            ;;
    esac
done

cd "$PROJECT_ROOT"

echo -e "${YELLOW}Git deployment configuration:${NC}"
echo "  Branch: $BRANCH"
echo "  Backup: $BACKUP"
echo "  Force: $FORCE"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    if [[ -z "$REPO_URL" ]]; then
        echo -e "${RED}Error: Not in a git repository and no --repo URL provided${NC}"
        echo "Either:"
        echo "  1. Run this from a git repository"
        echo "  2. Provide repository URL with --repo"
        exit 1
    else
        echo -e "${YELLOW}Cloning repository...${NC}"
        # This would be for a fresh clone scenario
        echo "Fresh clone deployment not implemented in this script"
        echo "Please clone manually and run from the cloned directory"
        exit 1
    fi
fi

# Check for uncommitted changes
if ! $FORCE && [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Uncommitted changes detected${NC}"
    echo "Uncommitted files:"
    git status --porcelain
    echo ""
    echo "Options:"
    echo "  1. Commit your changes: git add -A && git commit -m 'Pre-deployment commit'"
    echo "  2. Stash your changes: git stash"
    echo "  3. Force deployment (will lose changes): $0 $BRANCH --force"
    exit 1
fi

# Create backup if requested
if $BACKUP; then
    echo -e "\n${BLUE}Creating backup...${NC}"
    
    BACKUP_DIR="../backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="deployment_backup_${TIMESTAMP}"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    # Create backup excluding common unneeded directories
    rsync -av --exclude='node_modules' --exclude='venv' --exclude='.venv' \
          --exclude='frontend_build' --exclude='*.log' --exclude='pids' \
          --exclude='uploads' --exclude='.git' \
          . "$BACKUP_PATH/"
    
    echo -e "${GREEN}✓ Backup created: $BACKUP_PATH${NC}"
fi

# Stop production server if running
echo -e "\n${BLUE}Stopping services...${NC}"
if [[ -f "pids/production.pid" ]]; then
    echo "Stopping production server..."
    "$SCRIPT_DIR/prod-stop.sh"
fi

# Stop development servers if running
if [[ -f "pids/backend.pid" ]]; then
    echo "Stopping development servers..."
    "$SCRIPT_DIR/dev-stop.sh"
fi

# Fetch latest changes
echo -e "\n${BLUE}Fetching latest changes...${NC}"
git fetch origin

# Check if branch exists
if ! git show-ref --verify --quiet refs/remotes/origin/$BRANCH; then
    echo -e "${RED}Error: Branch '$BRANCH' does not exist on remote${NC}"
    echo "Available branches:"
    git branch -r | grep -v HEAD
    exit 1
fi

# Get current commit for rollback info
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Current commit: $CURRENT_COMMIT"

# Checkout and pull the specified branch
echo -e "\n${BLUE}Updating to branch: $BRANCH${NC}"

# If we're not on the target branch, switch to it
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
    echo "Switching from $CURRENT_BRANCH to $BRANCH..."
    git checkout $BRANCH
fi

# Pull latest changes
git pull origin $BRANCH

NEW_COMMIT=$(git rev-parse HEAD)
echo "New commit: $NEW_COMMIT"

if [[ "$CURRENT_COMMIT" == "$NEW_COMMIT" ]]; then
    echo -e "${YELLOW}No new changes to deploy${NC}"
    if ! $FORCE; then
        echo "Use --force to redeploy anyway"
        exit 0
    fi
fi

# Show what changed
echo -e "\n${BLUE}Changes being deployed:${NC}"
if [[ "$CURRENT_COMMIT" != "$NEW_COMMIT" ]]; then
    git log --oneline $CURRENT_COMMIT..$NEW_COMMIT | head -10
    echo ""
    echo "Files changed:"
    git diff --name-only $CURRENT_COMMIT..$NEW_COMMIT | head -20
    if [[ $(git diff --name-only $CURRENT_COMMIT..$NEW_COMMIT | wc -l) -gt 20 ]]; then
        echo "... and $(( $(git diff --name-only $CURRENT_COMMIT..$NEW_COMMIT | wc -l) - 20 )) more files"
    fi
fi

# Check if dependencies need updating
echo -e "\n${BLUE}Checking for dependency updates...${NC}"

# Python dependencies
if git diff --name-only $CURRENT_COMMIT..$NEW_COMMIT | grep -q "requirements.txt\|pyproject.toml\|poetry.lock"; then
    echo -e "${YELLOW}Python dependencies may have changed${NC}"
    
    if [[ -d "venv" ]]; then
        source venv/bin/activate
        if [[ -f "requirements.txt" ]]; then
            echo "Updating Python dependencies..."
            pip install -r requirements.txt
        fi
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
        if [[ -f "requirements.txt" ]]; then
            echo "Updating Python dependencies..."
            pip install -r requirements.txt
        fi
    fi
    echo -e "${GREEN}✓ Python dependencies updated${NC}"
fi

# Frontend dependencies (if package.json changed)
FRONTEND_DIR="../Roleplay_Chat_Frontend"
if [[ -d "$FRONTEND_DIR" ]]; then
    cd "$FRONTEND_DIR"
    
    # Check if we're in a git repo and if package files changed
    if git rev-parse --git-dir > /dev/null 2>&1; then
        if git diff --name-only $CURRENT_COMMIT..$NEW_COMMIT | grep -q "package.json\|package-lock.json"; then
            echo -e "${YELLOW}Frontend dependencies may have changed${NC}"
            echo "Updating frontend dependencies..."
            npm install
            echo -e "${GREEN}✓ Frontend dependencies updated${NC}"
        fi
    fi
    
    cd "$PROJECT_ROOT"
fi

# Run database migrations if needed
echo -e "\n${BLUE}Checking for database migrations...${NC}"
if git diff --name-only $CURRENT_COMMIT..$NEW_COMMIT | grep -q "alembic/versions\|migrations"; then
    echo -e "${YELLOW}Database migrations detected${NC}"
    if [[ -f "alembic.ini" ]] && command -v alembic >/dev/null; then
        echo "Running database migrations..."
        alembic upgrade head
        echo -e "${GREEN}✓ Database migrations completed${NC}"
    else
        echo -e "${YELLOW}⚠ Alembic not available, skipping migrations${NC}"
    fi
fi

# Deploy the application
echo -e "\n${BLUE}Deploying application...${NC}"
"$SCRIPT_DIR/deploy.sh"

# Create rollback script
echo -e "\n${BLUE}Creating rollback script...${NC}"
ROLLBACK_SCRIPT="rollback_to_${CURRENT_COMMIT:0:8}.sh"

cat > "$ROLLBACK_SCRIPT" << EOF
#!/bin/bash
# Rollback script generated on $(date)
# This will rollback to commit: $CURRENT_COMMIT

echo "Rolling back to commit: $CURRENT_COMMIT"

# Stop current services
./scripts/prod-stop.sh || true
./scripts/dev-stop.sh || true

# Checkout previous commit
git checkout $CURRENT_COMMIT

# Redeploy
./scripts/deploy.sh

echo "Rollback completed"
EOF

chmod +x "$ROLLBACK_SCRIPT"
echo -e "${GREEN}✓ Rollback script created: $ROLLBACK_SCRIPT${NC}"

# Success summary
echo -e "\n${GREEN}🎉 Git deployment completed successfully!${NC}"
echo "========================================"
echo -e "${BLUE}Deployment Summary:${NC}"
echo "  Branch: $BRANCH"
echo "  From commit: ${CURRENT_COMMIT:0:8}"
echo "  To commit: ${NEW_COMMIT:0:8}"
if $BACKUP; then
    echo "  Backup: $BACKUP_PATH"
fi
echo "  Rollback: ./$ROLLBACK_SCRIPT"

echo -e "\n${BLUE}Post-deployment:${NC}"
echo "  Status: ./scripts/status.sh"
echo "  Logs: ./scripts/logs.sh"
echo "  Rollback: ./$ROLLBACK_SCRIPT"

# Health check
sleep 3
local port=$(grep "^FLASK_PORT=" .env.production 2>/dev/null | cut -d'=' -f2 || echo "8080")
if curl -s --max-time 5 "http://localhost:$port/" > /dev/null; then
    echo -e "\n${GREEN}✓ Deployment health check passed${NC}"
    echo "Application is running at: http://localhost:$port"
else
    echo -e "\n${YELLOW}⚠ Health check failed - check logs${NC}"
    echo "Check status: ./scripts/status.sh"
    echo "Check logs: ./scripts/logs.sh"
fi