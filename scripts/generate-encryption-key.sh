#!/bin/bash

# Generate encryption keys for specific environments
# Usage: ./scripts/generate-encryption-key.sh [environment]
# Examples:
#   ./scripts/generate-encryption-key.sh development
#   ./scripts/generate-encryption-key.sh production
#   ./scripts/generate-encryption-key.sh  # interactive mode

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

echo -e "${BLUE}🔐 Encryption Key Generator${NC}"
echo "================================"

# Function to generate keys
generate_keys() {
    local env="$1"
    local env_file=".env.$env"
    
    echo -e "\n${YELLOW}Generating keys for environment: $env${NC}"
    
    # Check if environment file exists
    if [[ ! -f "$env_file" ]]; then
        echo -e "${RED}Error: Environment file $env_file not found${NC}"
        echo "Please create it from .env.example first"
        exit 1
    fi
    
    # Generate encryption key
    echo "Generating encryption key..."
    encryption_key=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Generate secret key
    echo "Generating Flask secret key..."
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update the environment file
    echo "Updating $env_file..."
    
    # Create backup
    cp "$env_file" "$env_file.backup"
    
    # Update keys in the file
    if grep -q "^ENCRYPTION_KEY=" "$env_file"; then
        # Replace existing empty encryption key
        sed -i "s/^ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$encryption_key/" "$env_file"
    else
        # Add encryption key
        echo "ENCRYPTION_KEY=$encryption_key" >> "$env_file"
    fi
    
    if grep -q "^SECRET_KEY=" "$env_file"; then
        # Replace existing empty secret key
        sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$secret_key/" "$env_file"
    else
        # Add secret key
        echo "SECRET_KEY=$secret_key" >> "$env_file"
    fi
    
    echo -e "${GREEN}✓ Keys generated and saved to $env_file${NC}"
    echo -e "${GREEN}✓ Backup created: $env_file.backup${NC}"
    
    # Verify the keys were added
    echo -e "\n${BLUE}Verification:${NC}"
    echo "ENCRYPTION_KEY: $(grep "^ENCRYPTION_KEY=" "$env_file" | cut -d'=' -f2 | head -c 20)..."
    echo "SECRET_KEY: $(grep "^SECRET_KEY=" "$env_file" | cut -d'=' -f2 | head -c 20)..."
}

# Main logic
if [[ $# -eq 1 ]]; then
    # Environment provided as argument
    ENV="$1"
    if [[ "$ENV" != "development" && "$ENV" != "production" ]]; then
        echo -e "${RED}Error: Environment must be 'development' or 'production'${NC}"
        exit 1
    fi
    generate_keys "$ENV"
elif [[ $# -eq 0 ]]; then
    # Interactive mode
    echo "Available environments:"
    echo "  1) development"
    echo "  2) production"
    echo "  3) both"
    echo ""
    read -p "Select environment (1-3): " choice
    
    case $choice in
        1)
            generate_keys "development"
            ;;
        2)
            generate_keys "production"
            ;;
        3)
            generate_keys "development"
            generate_keys "production"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
else
    echo -e "${RED}Usage: $0 [environment]${NC}"
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 production"
    echo "  $0  # interactive mode"
    exit 1
fi

echo -e "\n${GREEN}🎉 Key generation completed!${NC}"
echo -e "${YELLOW}Note: Make sure to restart your application to use the new keys${NC}"