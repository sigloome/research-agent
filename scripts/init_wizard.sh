#!/bin/bash
# ============================================
# Velvet Research Setup Wizard
# This script helps new users set up the environment for Velvet Research.
# ============================================

cd "$(dirname "$0")/.."

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  Velvet Research - Project Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# ============================================
# 1. Check Prerequisites
# ============================================
echo -e "${YELLOW}Step 1: Checking Prerequisites...${NC}"

# Try to load NVM if node is not found
if ! command -v node &> /dev/null; then
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        echo "Node not found in PATH, attempting to load from NVM..."
        . "$NVM_DIR/nvm.sh"
    fi
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    success "Python $PYTHON_VERSION found"
else
    error "Python 3 is required but not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js $NODE_VERSION found"
else
    error "Node.js is required but not installed. Please install Node.js (v18+ recommended) and try again."
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    success "npm $NPM_VERSION found"
else
    error "npm is required but not installed. Please install npm and try again."
    exit 1
fi

echo ""

# ============================================
# 2. Backend Setup
# ============================================
echo -e "${YELLOW}Step 2: Setting up Backend...${NC}"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
    success "Virtual environment created"
else
    success "Virtual environment 'venv' already exists."
fi

echo "Installing backend dependencies..."
source venv/bin/activate
pip install -r requirements.txt
success "Backend dependencies installed"
echo ""

# ============================================
# 3. Frontend Setup
# ============================================
echo -e "${YELLOW}Step 3: Setting up Frontend...${NC}"
cd frontend

INSTALL_DEPS=true
if [ -d "node_modules" ]; then
    echo "Frontend dependencies appear to be installed (node_modules exists)."
    read -p "Do you want to reinstall them? (y/N) " reinstall
    if [[ ! "$reinstall" =~ ^[Yy]$ ]]; then
        INSTALL_DEPS=false
    fi
fi

if [ "$INSTALL_DEPS" = true ]; then
    echo "Installing frontend dependencies (this may take a while)..."
    npm install
    success "Frontend dependencies installed"
fi

cd ..
echo ""

# ============================================
# 4. MCP Integration Checks (Z-Library)
# ============================================
echo -e "${YELLOW}Step 4: Checking MCP Integrations...${NC}"

# Load existing .env if present
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

MCP_ROOT="${MCP_ROOT:-$HOME/code/mcp}"
ZLIBRARY_MCP_PATH="$MCP_ROOT/zlibrary-mcp"

if [ -d "$ZLIBRARY_MCP_PATH" ]; then
    success "Found zlibrary-mcp at $ZLIBRARY_MCP_PATH"
    
    # Check if built
    if [ -f "$ZLIBRARY_MCP_PATH/dist/index.js" ]; then
        success "zlibrary-mcp is built"
    else
        warning "zlibrary-mcp needs to be built"
        echo "  Run: cd $ZLIBRARY_MCP_PATH && npm install && npm run build"
    fi
    
    # Check Python environment
    if [ -d "$ZLIBRARY_MCP_PATH/.venv" ]; then
        success "zlibrary-mcp Python environment exists"
    else
        warning "zlibrary-mcp Python environment missing"
        echo "  Run: cd $ZLIBRARY_MCP_PATH && bash setup-uv.sh"
    fi
else
    # Only warn, don't fail, as it's optional
    warning "zlibrary-mcp not found at $ZLIBRARY_MCP_PATH (Optional)"
    echo "  To enable Z-Library integration:"
    echo "  1. git clone https://github.com/loganrooks/zlibrary-mcp.git $ZLIBRARY_MCP_PATH"
    echo "  2. cd $ZLIBRARY_MCP_PATH && bash setup-uv.sh && npm install && npm run build"
    echo "  3. Update MCP_ROOT in .env if different from $MCP_ROOT"
fi
echo ""

# ============================================
# 5. Configuration (.env)
# ============================================
echo -e "${YELLOW}Step 5: Configuration...${NC}"

if [ -f ".env" ]; then
    echo ".env file already exists."
    read -p "Do you want to overwrite it? (y/N) " overwrite_env
    if [[ ! "$overwrite_env" =~ ^[Yy]$ ]]; then
        echo "Skipping .env creation."
        # Jump to success
        overwrite_env="no"
    fi
else
    overwrite_env="yes"
fi

if [[ "$overwrite_env" =~ ^[Yy]$ ]]; then
    echo "Creating .env file..."
    echo "Please enter your Anthropic API Key:"
    read -s anthropic_key
    echo ""

    echo "Would you like to configure Z-Library now? (Optional) (y/N)"
    read config_zlib

    zlib_email=""
    zlib_pass=""

    if [[ "$config_zlib" =~ ^[Yy]$ ]]; then
        echo "Z-Library Email:"
        read zlib_email
        echo "Z-Library Password:"
        read -s zlib_pass
        echo ""
    fi

    cat > .env <<EOL
# Anthropic/Claude API Configuration
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_AUTH_TOKEN=${anthropic_key}
DISABLE_TELEMETRY=1

# MCP Configuration
MCP_ROOT=${MCP_ROOT}

# Z-Library Credentials (for zlibrary-mcp)
ZLIBRARY_EMAIL=${zlib_email}
ZLIBRARY_PASSWORD=${zlib_pass}
EOL

    success ".env file created."
fi
echo ""

# ============================================
# 6. Conclusion
# ============================================
chmod +x scripts/start.sh
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "You can now start the application using:"
echo -e "${YELLOW}./scripts/start.sh${NC}"
