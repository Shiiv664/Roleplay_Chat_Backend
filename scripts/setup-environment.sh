#!/bin/bash

# Environment setup and validation script
# Usage: ./scripts/setup-environment.sh [environment]
# Examples:
#   ./scripts/setup-environment.sh development
#   ./scripts/setup-environment.sh production
#   ./scripts/setup-environment.sh  # interactive mode

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Environment Setup and Validation${NC}"
echo "===================================="

# Function to validate and setup environment
setup_environment() {
    local env="$1"
    local env_file=".env.$env"
    local example_file=".env.example"
    
    echo -e "\n${YELLOW}Setting up environment: $env${NC}"
    
    # Check if example file exists
    if [[ ! -f "$example_file" ]]; then
        echo -e "${RED}Error: $example_file not found${NC}"
        echo "Cannot create environment file without template"
        exit 1
    fi
    
    # Create environment file if it doesn't exist
    if [[ ! -f "$env_file" ]]; then
        echo "Creating $env_file from template..."
        cp "$example_file" "$env_file"
        echo -e "${GREEN}✓ Created $env_file${NC}"
    else
        echo -e "${GREEN}✓ $env_file already exists${NC}"
    fi
    
    # Validate required variables
    echo "Validating environment variables..."
    
    local missing_vars=()
    local empty_vars=()
    
    # Required variables for all environments
    local required_vars=("FLASK_ENV" "FLASK_HOST" "FLASK_PORT" "DATABASE_URL")
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            missing_vars+=("$var")
        else
            value=$(grep "^$var=" "$env_file" | cut -d'=' -f2-)
            if [[ -z "$value" ]]; then
                empty_vars+=("$var")
            fi
        fi
    done
    
    # Check for SECRET_KEY and ENCRYPTION_KEY (can be empty initially)
    local key_vars=("SECRET_KEY" "ENCRYPTION_KEY")
    local empty_keys=()
    
    for var in "${key_vars[@]}"; do
        if grep -q "^$var=" "$env_file"; then
            value=$(grep "^$var=" "$env_file" | cut -d'=' -f2-)
            if [[ -z "$value" ]]; then
                empty_keys+=("$var")
            fi
        else
            # Add missing key variable
            echo "$var=" >> "$env_file"
            empty_keys+=("$var")
        fi
    done
    
    # Report validation results
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Missing required variables: ${missing_vars[*]}${NC}"
        exit 1
    fi
    
    if [[ ${#empty_vars[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Empty required variables: ${empty_vars[*]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All required variables present${NC}"
    
    # Handle empty keys
    if [[ ${#empty_keys[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Empty security keys detected: ${empty_keys[*]}${NC}"
        echo "Generating keys automatically..."
        "$SCRIPT_DIR/generate-encryption-key.sh" "$env"
    else
        echo -e "${GREEN}✓ All security keys present${NC}"
    fi
    
    # Environment-specific validation
    if [[ "$env" == "production" ]]; then
        echo "Performing production-specific validation..."
        
        # Check that debug is disabled
        flask_debug=$(grep "^FLASK_DEBUG=" "$env_file" | cut -d'=' -f2-)
        if [[ "$flask_debug" == "true" ]]; then
            echo -e "${YELLOW}⚠ Warning: FLASK_DEBUG=true in production environment${NC}"
        fi
        
        # Check that production database is configured
        db_url=$(grep "^DATABASE_URL=" "$env_file" | cut -d'=' -f2-)
        if [[ "$db_url" == "sqlite:///app.db" ]]; then
            echo -e "${YELLOW}⚠ Warning: Using development database in production${NC}"
        fi
        
        # Check host binding for production
        flask_host=$(grep "^FLASK_HOST=" "$env_file" | cut -d'=' -f2-)
        if [[ "$flask_host" == "127.0.0.1" ]]; then
            echo -e "${YELLOW}⚠ Warning: Production server bound to localhost only${NC}"
            echo "  Consider setting FLASK_HOST=0.0.0.0 for external access"
        fi
    fi
    
    echo -e "${GREEN}✓ Environment $env validation completed${NC}"
}

# Function to show current environment status
show_status() {
    echo -e "\n${BLUE}Current Environment Status:${NC}"
    echo "=========================="
    
    for env in "development" "production"; do
        env_file=".env.$env"
        if [[ -f "$env_file" ]]; then
            echo -e "${GREEN}✓ $env_file exists${NC}"
            
            # Check for important variables
            if grep -q "^SECRET_KEY=" "$env_file" && [[ -n $(grep "^SECRET_KEY=" "$env_file" | cut -d'=' -f2-) ]]; then
                echo "  ✓ SECRET_KEY configured"
            else
                echo -e "  ${YELLOW}⚠ SECRET_KEY missing/empty${NC}"
            fi
            
            if grep -q "^ENCRYPTION_KEY=" "$env_file" && [[ -n $(grep "^ENCRYPTION_KEY=" "$env_file" | cut -d'=' -f2-) ]]; then
                echo "  ✓ ENCRYPTION_KEY configured"
            else
                echo -e "  ${YELLOW}⚠ ENCRYPTION_KEY missing/empty${NC}"
            fi
        else
            echo -e "${RED}✗ $env_file missing${NC}"
        fi
    done
}

# Main logic
case "${1:-}" in
    "development"|"production")
        setup_environment "$1"
        ;;
    "status")
        show_status
        ;;
    "")
        # Interactive mode
        echo "Available actions:"
        echo "  1) Setup development environment"
        echo "  2) Setup production environment"
        echo "  3) Setup both environments"
        echo "  4) Show status"
        echo ""
        read -p "Select action (1-4): " choice
        
        case $choice in
            1)
                setup_environment "development"
                ;;
            2)
                setup_environment "production"
                ;;
            3)
                setup_environment "development"
                setup_environment "production"
                ;;
            4)
                show_status
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                exit 1
                ;;
        esac
        ;;
    *)
        echo -e "${RED}Usage: $0 [environment|status]${NC}"
        echo "Examples:"
        echo "  $0 development"
        echo "  $0 production"
        echo "  $0 status"
        echo "  $0  # interactive mode"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 Environment setup completed!${NC}"