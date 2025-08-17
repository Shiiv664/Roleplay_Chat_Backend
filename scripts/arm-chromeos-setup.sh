#!/bin/bash

# ARM ChromeOS Environment Setup Script
# Handles IPv6 fix, Poetry installation, and environment preparation
# Usage: ./scripts/arm-chromeos-setup.sh [--check-only]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CHECK_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--check-only]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🔧 ARM ChromeOS Environment Setup${NC}"
echo "=================================="

cd "$PROJECT_ROOT"

# Function to check IPv6 status
check_ipv6() {
    echo -e "\n${BLUE}Checking IPv6 status...${NC}"
    
    if [[ -f /proc/sys/net/ipv6/conf/all/disable_ipv6 ]]; then
        ipv6_status=$(cat /proc/sys/net/ipv6/conf/all/disable_ipv6)
        if [[ "$ipv6_status" == "1" ]]; then
            echo -e "${GREEN}✓ IPv6 is disabled (ARM ChromeOS fix applied)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ IPv6 is enabled (may cause pip hanging issues)${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ Cannot check IPv6 status${NC}"
        return 1
    fi
}

# Function to apply IPv6 fix
apply_ipv6_fix() {
    echo -e "\n${BLUE}Applying IPv6 fix for ARM ChromeOS...${NC}"
    
    if $CHECK_ONLY; then
        echo -e "${YELLOW}Check-only mode: Would disable IPv6${NC}"
        return 0
    fi
    
    echo "Disabling IPv6 to prevent pip hanging issues..."
    
    # Apply temporary fix
    sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
    sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
    
    # Check if permanent fix exists
    if ! grep -q "net.ipv6.conf.all.disable_ipv6=1" /etc/sysctl.conf 2>/dev/null; then
        echo "Adding permanent IPv6 disable to /etc/sysctl.conf..."
        echo -e "\n# Disable IPv6 to fix pip hanging issue on ARM ChromeOS" | sudo tee -a /etc/sysctl.conf
        echo "net.ipv6.conf.all.disable_ipv6=1" | sudo tee -a /etc/sysctl.conf
        echo "net.ipv6.conf.default.disable_ipv6=1" | sudo tee -a /etc/sysctl.conf
        echo "net.ipv6.conf.lo.disable_ipv6=1" | sudo tee -a /etc/sysctl.conf
    fi
    
    echo -e "${GREEN}✓ IPv6 disabled successfully${NC}"
}

# Function to check Poetry installation
check_poetry() {
    echo -e "\n${BLUE}Checking Poetry installation...${NC}"
    
    if command -v poetry >/dev/null 2>&1; then
        poetry_version=$(poetry --version 2>/dev/null | cut -d' ' -f3 || echo "unknown")
        echo -e "${GREEN}✓ Poetry is installed (version: $poetry_version)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Poetry is not installed${NC}"
        return 1
    fi
}

# Function to install Poetry
install_poetry() {
    echo -e "\n${BLUE}Installing Poetry...${NC}"
    
    if $CHECK_ONLY; then
        echo -e "${YELLOW}Check-only mode: Would install Poetry${NC}"
        return 0
    fi
    
    echo "Downloading and installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    # Verify installation
    if command -v poetry >/dev/null 2>&1; then
        poetry_version=$(poetry --version | cut -d' ' -f3)
        echo -e "${GREEN}✓ Poetry installed successfully (version: $poetry_version)${NC}"
    else
        echo -e "${RED}✗ Poetry installation failed${NC}"
        echo "Please add $HOME/.local/bin to your PATH and restart your shell"
        exit 1
    fi
}

# Function to validate pyproject.toml
check_pyproject() {
    echo -e "\n${BLUE}Checking pyproject.toml configuration...${NC}"
    
    if [[ -f "pyproject.toml" ]]; then
        echo -e "${GREEN}✓ pyproject.toml found${NC}"
        
        # Check if Poetry dependencies are configured
        if grep -q "\[tool.poetry\]" pyproject.toml; then
            echo -e "${GREEN}✓ Poetry configuration found${NC}"
        else
            echo -e "${YELLOW}⚠ No Poetry configuration in pyproject.toml${NC}"
        fi
        
        # Check for main dependencies
        if grep -q "\[tool.poetry.dependencies\]" pyproject.toml; then
            echo -e "${GREEN}✓ Poetry dependencies section found${NC}"
        else
            echo -e "${YELLOW}⚠ No Poetry dependencies section${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ pyproject.toml not found${NC}"
        echo "This project may not be configured for Poetry"
    fi
}

# Function to test network connectivity
test_network() {
    echo -e "\n${BLUE}Testing network connectivity...${NC}"
    
    # Test PyPI connectivity (IPv4)
    if ping -4 -c 1 pypi.org >/dev/null 2>&1; then
        echo -e "${GREEN}✓ IPv4 connectivity to PyPI working${NC}"
    else
        echo -e "${YELLOW}⚠ IPv4 connectivity to PyPI failed${NC}"
    fi
    
    # Test npm registry connectivity
    if ping -4 -c 1 registry.npmjs.org >/dev/null 2>&1; then
        echo -e "${GREEN}✓ IPv4 connectivity to npm registry working${NC}"
    else
        echo -e "${YELLOW}⚠ IPv4 connectivity to npm registry failed${NC}"
    fi
    
    # Clear package manager caches if not in check-only mode
    if ! $CHECK_ONLY; then
        echo "Clearing package manager caches..."
        if command -v npm >/dev/null 2>&1; then
            npm cache clean --force 2>/dev/null || true
        fi
        if command -v pip >/dev/null 2>&1; then
            pip cache purge 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Package manager caches cleared${NC}"
    fi
}

# Function to configure npm for ARM ChromeOS
configure_npm() {
    echo -e "\n${BLUE}Configuring npm for ARM ChromeOS...${NC}"
    
    if ! command -v npm >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ npm not found, skipping npm configuration${NC}"
        return 0
    fi
    
    if $CHECK_ONLY; then
        echo -e "${YELLOW}Check-only mode: Would configure npm${NC}"
        return 0
    fi
    
    # Configure npm with ARM ChromeOS optimizations
    npm config set registry https://registry.npmjs.org/
    npm config set fetch-timeout 600000
    npm config set maxsockets 5
    npm config set fetch-retries 5
    
    echo -e "${GREEN}✓ npm configured for ARM ChromeOS${NC}"
}

# Function to configure pip
configure_pip() {
    echo -e "\n${BLUE}Configuring pip for ARM environment...${NC}"
    
    if ! command -v pip >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ pip not found, skipping pip configuration${NC}"
        return 0
    fi
    
    if $CHECK_ONLY; then
        echo -e "${YELLOW}Check-only mode: Would configure pip${NC}"
        return 0
    fi
    
    # Configure pip timeout
    pip config set global.timeout 600
    
    echo -e "${GREEN}✓ pip configured for ARM environment${NC}"
}

# Main execution flow
echo -e "${YELLOW}Mode: $(if $CHECK_ONLY; then echo "Check-only"; else echo "Setup and fix"; fi)${NC}"

# Step 1: Check and fix IPv6
if ! check_ipv6; then
    if $CHECK_ONLY; then
        echo -e "${YELLOW}IPv6 fix needed but not applied (check-only mode)${NC}"
    else
        apply_ipv6_fix
    fi
fi

# Step 2: Check and install Poetry
if ! check_poetry; then
    if $CHECK_ONLY; then
        echo -e "${YELLOW}Poetry installation needed but not performed (check-only mode)${NC}"
    else
        install_poetry
    fi
fi

# Step 3: Validate project configuration
check_pyproject

# Step 4: Test and configure network
test_network
configure_npm
configure_pip

# Step 5: Summary
echo -e "\n${BLUE}Setup Summary:${NC}"
echo "=============="

if check_ipv6 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ IPv6 fix applied${NC}"
else
    echo -e "${YELLOW}⚠ IPv6 fix needed${NC}"
fi

if check_poetry >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Poetry available${NC}"
else
    echo -e "${YELLOW}⚠ Poetry needs installation${NC}"
fi

if [[ -f "pyproject.toml" ]]; then
    echo -e "${GREEN}✓ Poetry project configured${NC}"
else
    echo -e "${YELLOW}⚠ Poetry project setup needed${NC}"
fi

if $CHECK_ONLY; then
    echo -e "\n${YELLOW}Check completed. Run without --check-only to apply fixes.${NC}"
else
    echo -e "\n${GREEN}🎉 ARM ChromeOS environment setup completed!${NC}"
    echo "Your system is now optimized for package installations and development."
fi

echo -e "\n${BLUE}Next steps:${NC}"
echo "  1. Run: poetry install --only=main"
echo "  2. Run: npm install (in frontend directory)"
echo "  3. Deploy: ./scripts/deploy.sh"